"""Fake 모델 — 휴리스틱 정책 (기획서 §9 추가①, 설계 §3.4).

프롬프트의 `<<CONTEXT_JSON>>` 블록을 읽어 규칙으로 답한다. 판단이 LLM 보다
단순할 뿐, 규칙·로그·인스펙터는 동일하다. 테스트·자동 대전(수백 판)·LLM 장애
폴백·API 키 없는 로컬 플레이가 전부 이것으로 돈다.

"너무 똑똑하지도 너무 멍청하지도" 않아야 실험이 의미 있다: 감독은 힐러 유무와
승산을 보고, 단원은 HP·스태미나·방침을 보고, 보스는 코드가 제안한 적응을 따른다.
"""

import json
from typing import Any

from apps.arena.app.use_cases.agents.prompts import CTX_CLOSE, CTX_OPEN
from apps.arena.domain.ports.ports import JsonSchema, Role
from apps.arena.domain.services.josa import with_josa

RANGED_CLASSES = {"archer", "bard"}


def parse_context(prompt: str) -> dict[str, Any]:
    start = prompt.rfind(CTX_OPEN)
    end = prompt.rfind(CTX_CLOSE)
    if start < 0 or end < 0:
        return {}
    return json.loads(prompt[start + len(CTX_OPEN) : end])


# 적이 이만큼 이상이면 광역이 지목보다 낫다. 전에는 지목을 먼저 골라 광역
# 기술이 단일 대상으로 바뀌었고, 행동당 타격이 2.43 → 1.19 로 떨어졌다.
# 감독 OFF 는 지목이 없어 우연히 광역을 골랐고, 그래서 E1 이 "감독은 해롭다"
# 고 말했다(QA 재검 2026-09-09 R21).
AOE_MIN_TARGETS = 3


class FakeModel:
    name = "fake"

    def decide(self, role: Role, prompt: str, schema: JsonSchema) -> dict[str, Any]:
        ctx = parse_context(prompt)
        if role == "orchestrator":
            return self._orchestrate(ctx)
        if role == "character":
            return self._act(ctx)
        if role == "boss":
            return self._boss(ctx)
        return {"narration": ctx.get("fallback", "")}

    # ─── 단장 ───────────────────────────────────────────────────────────
    def _orchestrate(self, ctx: dict[str, Any]) -> dict[str, Any]:
        names = ctx.get("names", {})
        units = ctx.get("units", [])
        enemies = ctx.get("enemies", [])
        odds = float(ctx.get("odds", 0.5))
        forced = bool(ctx.get("forced"))
        has_healer = any(u["can_heal"] for u in units)
        if not has_healer:
            strategy = "rush"
        elif odds >= 0.5:
            strategy = "attrition"
        else:
            strategy = "defensive"
        # 임계는 전략이 정한다. 속공은 "짧게 끝내자"는 약속이라 낮은 승산을 견디고,
        # 방어전은 오래 끄는 만큼 일찍 접는다. 힐러 없음에 +0.05 를 얹는 안은 실측
        # (30시드)에서 이길 판의 절반을 포기하게 만들어 버렸다.
        # 실측 보정(30시드, 전사 몰빵): 승산이 0.15~0.20 으로 읽힐 때 그대로 싸운
        # 판의 28% 가 이겼다. 임계 0.20 은 이길 판을 버리는 값이라 속공은 0.15 로
        # 내린다. 오래 끄는 작전일수록 일찍 접는다.
        threshold = {"rush": 0.15, "attrition": 0.25, "defensive": 0.30}[strategy]

        # 도주 성공률이 낮으면 후퇴가 더 비싸다 — 실패한 유닛은 턴을 잃고 그대로 맞는다.
        # 실측(30시드, 전사 몰빵): 느린 전사 파티에 후퇴를 명령하니 사망이 22→40 으로
        # 늘고 승률은 10/30 → 1/30 이 됐다. 도망칠 수 없다면 싸우는 편이 낫다.
        escape = float(ctx.get("escape_chance", 1.0))
        can_escape = escape >= 0.5

        # 승산은 휴리스틱이라 한 턴 크게 흔들린다. 한 번 낮게 찍혔다고 판을 접으면
        # 이길 판을 버린다 — 추세가 나빠지는 중일 때만 접는다. 강제 결정(연속
        # 재계획 상한 초과)일 때는 추세를 묻지 않는다(설계 §6.3).
        prev = ctx.get("previous_odds")
        worsening = prev is None or odds <= float(prev)

        # 후퇴는 이르게 하거나 하지 않는다.
        #
        # 사람이 쓰러진 뒤에 빼면 값이 두 배다: 이미 잃은 것은 못 돌리고, 남은
        # 이들은 등을 보이며 맞는다. 실측(30시드, 전사 몰빵)에서 늦은 후퇴는
        # 승률을 33%→13% 로 깎으면서 생존율은 76%→74% 로 그대로였다 — 아무것도
        # 사지 못하고 판만 버린 셈이다. 그래서 이미 잃은 뒤에는 승산이 임계의
        # 절반 아래로 무너졌을 때만 접는다.
        losses = int(ctx.get("losses", 0))
        bar = threshold if losses == 0 else threshold * 0.5
        give_up = can_escape and ((odds < bar and worsening) or (forced and odds < bar + 0.1))
        if give_up:
            return {
                "assessment": (
                    f"승산 {odds:.2f}. 전령관 {'있음' if has_healer else '없음'}. "
                    "더 싸우면 사람을 잃는다."
                ),
                "worth_fighting": False,
                "strategy": "retreat",
                "formation": {u["id"]: u["position"] for u in units},
                "focus_target": None,
                "per_unit_directive": {u["id"]: "후퇴한다. 생존 우선." for u in units},
                "retreat_threshold": round(threshold, 2),
                "rationale": (
                    f"싸울 가치가 없다. 도주 성공률 {escape:.0%} 면 뺄 수 있다. 생존 우선 철수."
                ),
            }

        # 편성: 원거리·치유자는 뒤, 근접은 앞. 그리고 **가장 잘 때리는 사람 하나를
        # 전열 뒤에 세운다.**
        #
        # 근접 적은 전열이 살아 있는 한 후열에 닿지 못한다(core/battle/resolve.py).
        # 그러니 전열은 방패고, 방패 뒤에서 계속 때리는 사람이 판을 끝낸다.
        # 실측(200시드, 전 근접 조합): 전원을 앞에 세우면 승률 1%, 최고 딜러
        # 하나를 뒤에 두면 26%. 그 하나가 끝까지 살아 피해를 넣기 때문이다.
        formation = {}
        for u in units:
            back = u["ranged"] or u["can_heal"]
            formation[u["id"]] = "back" if back else "front"

        front = [u for u in units if formation[u["id"]] == "front"]
        if len(front) >= 2:
            carry = max(front, key=lambda u: u.get("expected_damage", 0))
            formation[carry["id"]] = "back"
        elif units and not front:
            # 아무도 앞에 없으면 근접 적이 후열을 그대로 친다. 가장 단단한 사람이 선다.
            tank = max(units, key=lambda u: (u["weight_class"], u["hp_pct"]))
            formation[tank["id"]] = "front"

        # 집중 목표: 치유자 → 보스 → 가장 약한 적.
        #
        # 한때 "곧 죽일 수 있는 잡졸 먼저" 로 두었다. 20시드에서는 그럴듯해
        # 보였지만 150~200시드가 뒤집었다: 바르가스는 3턴마다 수하를 부르므로
        # 재계획마다 목표가 수하로 갈아타고(60판 집계 수하 314 / 보스 107),
        # 보스에게 가는 피해가 63%→44% 로 떨어져 보스 처치가 60판 중 47판에서
        # 8판이 됐다. 보스가 살아 있는 한 소환은 멈추지 않는다 — 잡졸을 치우는
        # 이득보다 보스를 늦게 죽이는 손해가 크다(QA 라운드 2).
        # **닿는 적 안에서만 지목한다.** 근접은 전열이 살아 있는 한 후열에 못
        # 닿는데(resolve.py 의 reachable) "가장 약한 적" 이 대개 후열의 투석수라,
        # 지목을 따르려던 근접 대원의 타격이 통째로 되돌려졌다 — 30시드 미션 7
        # 에서 264회. 그래서 감독 ON 이 파티 피해를 11,638 → 5,573 으로 **반토막**
        # 냈고, E1 이 "감독은 나쁜 조합에서 유의하게 해롭다" 고 말했다
        # (QA 재검 2026-09-09 R21, A/B: 완주 2% → 32%).
        focus = None
        if enemies:
            근접만 = not any(u["ranged"] for u in units)
            전열 = [e for e in enemies if e.get("position") == "front"]
            닿는_적 = 전열 if (근접만 and 전열) else enemies
            healers = [e for e in 닿는_적 if e["can_heal"]]
            bosses = [e for e in 닿는_적 if e["is_boss"]]
            weakest = min(닿는_적, key=lambda e: e.get("hp", 0))
            if healers and any(u["ranged"] for u in units):
                focus = healers[0]["id"]
            elif bosses:
                focus = bosses[0]["id"]
            else:
                focus = weakest["id"]

        focus_name = names.get(focus, focus) if focus else "적"
        directive = {}
        for u in units:
            if u["can_heal"]:
                directive[u["id"]] = "후열에서 다친 아군을 치유하고, 여유가 있으면 축복."
            elif formation[u["id"]] == "front":
                directive[u["id"]] = (
                    f"전열에서 {with_josa(focus_name, '을')} 집중 공격. 빈사면 방어."
                )
            else:
                directive[u["id"]] = (
                    f"후열에서 {with_josa(focus_name, '을')} 노린다. 근접당하면 물러선다."
                )

        stuck = "" if can_escape else f" 도주 성공률이 {escape:.0%}라 물러설 수도 없다."
        text = {
            "rush": "전령관이 없으니 오래 못 버틴다. 속공으로 짧게 끝낸다.",
            "attrition": "전령관이 있다. 전열이 버티고 후열이 갉아먹는다.",
            "defensive": "승산이 반반 아래다. 방어하며 기회를 본다.",
        }[strategy] + stuck
        return {
            "assessment": f"승산 {odds:.2f}. 전령관 {'있음' if has_healer else '없음'}. {text}",
            "worth_fighting": True,
            "strategy": strategy,
            "formation": formation,
            "focus_target": focus,
            "per_unit_directive": directive,
            "retreat_threshold": round(threshold, 2),
            "rationale": text,
        }

    # ─── 단원 ───────────────────────────────────────────────────────────
    def _act(self, ctx: dict[str, Any]) -> dict[str, Any]:
        me = ctx.get("self", {})
        available = ctx.get("available", [])
        verdict = ctx.get("verdict", "comply")
        focus = ctx.get("focus_target")
        visible = ctx.get("visible", {})
        names = ctx.get("names", {})
        skills = {s["name"]: s for s in ctx.get("skills", [])}
        hp = me.get("hp_pct", 100)
        stamina_ratio = me.get("stamina", 0) / max(1, me.get("stamina_max", 1))
        my_statuses = set((visible.get("self") or {}).get("statuses") or [])

        def nm(uid: str | None) -> str:
            return names.get(uid, uid) if uid else "적"

        def find(kind: str, **match: Any) -> dict[str, Any] | None:
            for a in available:
                if a["kind"] != kind:
                    continue
                if all(a.get(k) == v for k, v in match.items()):
                    return a
            return None

        def skill_actions(pred) -> list[dict[str, Any]]:
            out = []
            for a in available:
                if a["kind"] != "SKILL":
                    continue
                meta = skills.get(a.get("skill") or "")
                if meta and pred(meta):
                    out.append(a)
            return out

        def answer(a: dict[str, Any] | None, follows: bool, reason: str) -> dict[str, Any]:
            if a is None:
                a = {"kind": "WAIT", "target": None, "skill": None, "position": None}
            return {
                "action": a["kind"],
                "target": a.get("target"),
                "skill": a.get("skill"),
                "position": a.get("position"),
                "follows_plan": follows,
                "reason": reason,
            }

        if ctx.get("strategy") == "retreat" and find("FLEE"):
            return answer(find("FLEE"), True, "단장의 후퇴 명령이다. 물러난다.")

        if verdict == "deviate":
            # 두고 온 사람이 있을 때만 그 이야기를 한다. "가족 없음" 을 도주
            # 사유로 대는 건 말이 안 된다.
            life = (me.get("life") or "").strip()
            worry = f" {life}" if life and int(me.get("dependents", 0)) > 0 else ""
            if hp < 40 and find("FLEE"):
                return answer(find("FLEE"), False, f"여기서 죽을 수는 없다.{worry}")
            if find("DEFEND"):
                return answer(find("DEFEND"), False, f"방침은 알지만 지금은 몸을 지킨다.{worry}")
            return answer(find("WAIT"), False, f"발이 떨어지지 않는다.{worry}")

        # 순응 — 치유자가 먼저 본다. 사람이 죽으면 작전이 없다.
        if me.get("can_heal"):
            allies = visible.get("allies") or []
            hurt = sorted(
                [a for a in allies if a.get("hp_pct", 100) < 55], key=lambda a: a["hp_pct"]
            )
            if hp < 45:
                heal_self = find("SKILL", skill="치유", target=me["id"])
                if heal_self:
                    return answer(heal_self, True, "내가 쓰러지면 아무도 못 살린다.")
            for h in hurt:
                a = find("SKILL", skill="치유", target=h["id"])
                if a:
                    who = with_josa(h["name"], "이")
                    return answer(a, True, f"{who} 위험하다. 상처를 덮는다.")
            bless = skill_actions(lambda m: m["effect"] == "bless")
            if bless and stamina_ratio > 0.6 and "bless" not in my_statuses:
                return answer(bless[0], True, "다친 사람이 없다. 축복으로 아군의 손을 돕는다.")

        # 순응 — 빈사면 방어
        if hp < 30 and find("DEFEND"):
            return answer(find("DEFEND"), True, "빈사다. 방침대로 몸을 지킨다.")

        # 순응 — 방어 기술은 아직 안 걸려 있을 때 한 번만.
        #
        # 예전에는 "스킬 목록의 첫 번째" 를 골랐고, 전사 스킬 순서가
        # (방패 밀치기, 강타) 라 가렛이 40판 동안 자기 방어만 하고 총 피해가 0 이었다
        # (QA 라운드 1 P0-4). 기술이 무엇을 하는지는 ctx["skills"] 가 말해준다.
        guards = skill_actions(lambda m: m["effect"] == "guard")
        if (
            guards
            and "guard" not in my_statuses
            and stamina_ratio > 0.5
            and me.get("position") == "front"
        ):
            return answer(guards[0], True, "전열이다. 방패를 들어 뒤를 막는다.")

        # 순응 — 피해 기술. 집중 목표가 있으면 그쪽으로.
        offensive = skill_actions(lambda m: m["offensive"])
        if offensive and stamina_ratio >= 0.5:
            # **적이 셋 이상이면 광역이 지목보다 낫다.** 전에는 지목을 먼저 골라
            # 광역 기술이 단일 대상으로 바뀌었고, 행동당 타격이 2.43 → 1.10 으로
            # 떨어졌다(30시드 미션 7 실측). 지목은 적이 적을 때의 규칙이다.
            광역 = next((a for a in offensive if a.get("target") is None), None)
            # 단원 컨텍스트에는 적 목록이 없다(가시성 마스킹 때문이다). **지금
            # 칠 수 있는 적**의 수는 available 의 ATTACK 대상 수가 말해 준다.
            닿는_적 = {a.get("target") for a in available if a["kind"] == "ATTACK"}
            여럿 = len(닿는_적) >= AOE_MIN_TARGETS
            picked = 광역 if (여럿 and 광역) else None
            picked = picked or next((a for a in offensive if a.get("target") == focus), None)
            picked = picked or 광역
            picked = picked or offensive[0]
            where = nm(picked.get("target")) if picked.get("target") else "적 전체"
            skill = with_josa(picked["skill"], "으로")
            return answer(picked, True, f"{skill} {with_josa(where, '을')} 노린다.")

        # 순응 — 집중 목표 공격
        if focus and find("ATTACK", target=focus):
            target_name = with_josa(nm(focus), "을")
            return answer(find("ATTACK", target=focus), True, f"방침대로 {target_name} 친다.")
        any_attack = find("ATTACK")
        if any_attack:
            hit = with_josa(nm(any_attack["target"]), "을")
            return answer(any_attack, focus is None, f"{hit} 친다.")
        if find("DEFEND"):
            return answer(find("DEFEND"), True, "칠 수 없다. 방어한다.")
        return answer(find("WAIT"), True, "지쳤다. 숨을 고른다.")

    # ─── 보스 ───────────────────────────────────────────────────────────
    def _boss(self, ctx: dict[str, Any]) -> dict[str, Any]:
        available = ctx.get("available", [])
        enemies = ctx.get("enemies", [])
        focus = ctx.get("focus_override")
        adapt = ctx.get("adapt_suggestion")
        turn = int(ctx.get("turn", 0))

        target = focus
        if target is None and enemies:
            front = [e for e in enemies if e["position"] == "front"]
            pool = front or enemies
            target = min(pool, key=lambda e: e["hp_pct"])["id"]

        def find(kind: str, **match: Any) -> dict[str, Any] | None:
            for a in available:
                if a["kind"] == kind and all(a.get(k) == v for k, v in match.items()):
                    return a
            return None

        chosen = None
        if turn % 2 == 0:
            chosen = find("SKILL", skill="분쇄", target=target) or find("SKILL", skill="갱도 진동")
        if chosen is None:
            chosen = (
                find("ATTACK", target=target) or find("ATTACK") or find("DEFEND") or find("WAIT")
            )
        if chosen is None:
            chosen = {"kind": "WAIT", "target": None, "skill": None}
        names = ctx.get("names", {})
        target_name = names.get(target, target) if target else "적"
        adapt_ko = {
            "focus": " 저 자가 계속 나를 노렸다.",
            "breach": " 앞줄이 계속 막는다. 방패를 든 놈부터 부순다.",
            "target_healer": " 상처를 덮는 자를 먼저 부순다.",
            "summon_faster": " 잔해를 더 자주 불러 모은다.",
        }
        return {
            "action": chosen["kind"],
            "target": chosen.get("target"),
            "skill": chosen.get("skill"),
            "adapt": adapt,
            "reason": f"{with_josa(target_name, '을')} 노린다." + adapt_ko.get(adapt or "", ""),
        }

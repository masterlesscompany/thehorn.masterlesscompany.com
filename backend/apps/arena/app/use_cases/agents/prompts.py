"""프롬프트 조립 (설계 §6.1·§6.4).

두 부분으로 되어 있다:
1. 사람이 읽는 서술 — 실제 LLM 이 상황을 이해하는 부분.
2. `<<CONTEXT_JSON>> … <<END>>` — 같은 정보의 구조화본. Fake 모델이 규칙으로
   읽고, 실제 모델도 정확한 id 를 여기서 가져간다.

두 부분이 같은 정보를 담아야 한다. 서술에만 있고 JSON 에 없는 정보는 Fake 가
못 보고, 그 반대는 실제 모델이 놓친다.

MBTI 문자열은 절대 넣지 않는다(tests/test_prompts.py). 성향은 describe() 의
수치 서술로만 들어간다(기획서 §4.5).
"""

import json
from typing import Any

from apps.arena.domain.constants.balance import RETREAT_THRESHOLD_DEFAULT, RETREAT_THRESHOLD_RANGE
from apps.arena.domain.entities.types import Action, Plan, SkillDef
from apps.arena.domain.services.battle.state import Battle, UnitState, living
from apps.arena.domain.services.judgment.odds import unit_damage
from apps.arena.domain.services.rules.combat import flee_chance
from apps.arena.domain.services.rules.disposition import describe

CTX_OPEN = "<<CONTEXT_JSON>>"
CTX_CLOSE = "<<END>>"


def _ctx(d: dict[str, Any]) -> str:
    return f"\n{CTX_OPEN}\n{json.dumps(d, ensure_ascii=False)}\n{CTX_CLOSE}\n"


def _hp_bucket(u: UnitState) -> str:
    pct = u.hp / u.hp_max
    return "건재" if pct > 0.7 else ("상처" if pct > 0.3 else "빈사")


def build_orchestrator_prompt(
    battle: Battle,
    faction: str,
    odds_value: float,
    reason: str,
    forced: bool = False,
    previous: Plan | None = None,
    previous_odds: float | None = None,
) -> str:
    env = battle.environment
    mine = living(battle, faction)
    other = battle.enemy if faction == battle.party else battle.party
    foes = living(battle, other)
    lost = [u for u in battle.units.values() if u.faction == faction and not u.active]

    units_ctx = [
        {
            "id": u.id,
            "name": u.name,
            "class": u.char_class,
            "hp_pct": round(100 * u.hp / u.hp_max),
            "stamina_pct": round(100 * u.stamina / u.stamina_max),
            "agi": u.stats.agi,
            "weight_class": u.armor.weight_class,
            "ranged": u.weapon.ranged,
            "can_heal": any(s.effect == "heal" for s in u.skills),
            "position": u.position,
            # 누가 가장 잘 때리는가. 전열이 방패가 되는 전장에서 편성의 핵심은
            # "가장 잘 때리는 사람을 오래 살리는 것" 이다 — 단장이 그걸 알아야
            # 판단할 수 있다(QA 라운드 2, 200시드).
            "expected_damage": round(unit_damage(u, foes, env, battle)[0], 1),
            "disposition": u.disposition.as_dict() if u.disposition else None,
        }
        for u in mine
    ]
    foes_ctx = [
        {
            "id": f.id,
            "name": f.name,
            "hp_bucket": _hp_bucket(f),
            "hp": f.hp,
            "hp_pct": round(100 * f.hp / f.hp_max),
            "is_boss": f.is_boss,
            "position": f.position,
            "can_heal": any(s.effect == "heal" for s in f.skills),
        }
        for f in foes
    ]
    # 후퇴에도 비용이 있다(설계 §5.3) — 도망 판정에 실패한 유닛은 한 턴을 잃고 맞는다.
    # 느린 파티에게 후퇴 명령은 사형선고가 될 수 있으므로 단장이 이것을 보고 판단해야 한다.
    # 가장 느린 사람이 후퇴 가능 여부를 정한다 — 평균을 쓰면 빠른 둘이 빠지고
    # 느린 하나가 남아 맞아 죽는 판을 감독이 "뺄 수 있다" 로 읽는다.
    escapes = [flee_chance(u, foes)[0] for u in mine] or [0]
    escape_avg = round(min(escapes) / 100, 2)

    lines = [
        "당신은 용병단의 단장이다. 단주가 준 인원으로 최선을 다한다. 받은 패로 싸운다.",
        "먼저 '싸울 가치가 있는가'를 판단하고, 있다면 작전을 짠다.",
        f"가장 느린 단원의 도주 성공률: {escape_avg:.0%}. 낮으면 후퇴하다 더 크게 잃는다.",
        f"이미 잃은 인원: {len(lost)}명. 사람이 쓰러진 뒤의 후퇴는 늦다 — "
        "빼려면 온전할 때 빼야 값이 싸다.",
        f"환경: {env.name} — {env.description}",
        f"환경 수치: 중갑 속도 페널티 {env.speed_penalty_by_weight}, "
        f"스태미나 배수 {env.stamina_multiplier}, "
        f"후열 거리 페널티 {env.range_penalty}%, 어둠 {env.darkness}",
        f"현재 승산(코드 계산): {odds_value:.2f}",
        f"재계획 사유: {reason}",
    ]
    if forced:
        lines.append("경고: 재계획이 연속 3회를 넘었다. 이번에는 포기 여부를 반드시 결정하라.")
    if previous:
        lines.append(f"직전 작전: {previous.strategy} / {previous.assessment}")
    if previous_odds is not None:
        direction = "나빠지는 중" if odds_value < previous_odds else "버티는 중"
        lines.append(f"직전 승산 {previous_odds:.2f} → 지금 {odds_value:.2f} ({direction})")
    lines.append("출전 단원:")
    for u in units_ctx:
        d = u["disposition"]
        dd = ", ".join(describe_from_dict(d).values()) if d else "-"
        lines.append(
            f"- {u['name']}({u['id']}, {u['class']}) HP {u['hp_pct']}% "
            f"스태미나 {u['stamina_pct']}% 민첩 {u['agi']} 갑옷무게 {u['weight_class']} "
            f"원거리 {u['ranged']} 치유 {u['can_heal']} / 성향: {dd}"
        )
    lines.append("적:")
    for f in foes_ctx:
        lines.append(
            f"- {f['name']}({f['id']}) {f['hp_bucket']} 위치 {f['position']} 보스 {f['is_boss']}"
        )
    lines.append(
        "JSON 으로만 답하라: assessment, worth_fighting, "
        "strategy(rush|attrition|defensive|retreat), "
        "formation{unit_id: front|back}, focus_target, per_unit_directive{unit_id: 지시}, "
        f"retreat_threshold({RETREAT_THRESHOLD_RANGE[0]}..{RETREAT_THRESHOLD_RANGE[1]}, "
        f"기본 {RETREAT_THRESHOLD_DEFAULT}), rationale"
    )
    ctx = {
        "role": "orchestrator",
        "units": units_ctx,
        "enemies": foes_ctx,
        "odds": odds_value,
        "escape_chance": escape_avg,
        "previous_odds": previous_odds,
        "losses": len(lost),
        "reason": reason,
        "forced": forced,
        "environment": {
            "name": env.name,
            "speed_penalty_by_weight": {str(k): v for k, v in env.speed_penalty_by_weight.items()},
            "range_penalty": env.range_penalty,
        },
        "retreat_threshold_default": RETREAT_THRESHOLD_DEFAULT,
        "names": {u.id: u.name for u in [*mine, *foes]},
    }
    return "\n".join(lines) + _ctx(ctx)


def describe_from_dict(d: dict[str, int]) -> dict[str, str]:
    from apps.arena.domain.entities.types import Disposition

    return describe(Disposition(**d))


def build_character_prompt(
    unit: UnitState,
    visible: dict[str, Any],
    masked: list[str],
    plan: Plan | None,
    actions: list[Action],
    verdict: str,
    names: dict[str, str] | None = None,
) -> str:
    directive = plan.per_unit_directive.get(unit.id) if plan else None
    focus = plan.focus_target if plan else None
    d = unit.disposition
    lines = [
        f"당신은 {unit.name}, {unit.char_class} 다. {unit.voice}",
        f"신체: {unit.body.height_cm}cm · {unit.body.build} · {unit.body.weight_kg}kg. "
        f"무기 {unit.weapon.name}, 갑옷 {unit.armor.name}.",
        f"능력치: 힘 {unit.stats.str_} 민첩 {unit.stats.agi} 체력 {unit.stats.con} "
        f"지능 {unit.stats.int_} 지혜 {unit.stats.wis}",
    ]
    if d:
        lines.append("성향: " + ", ".join(describe(d).values()))
    if unit.life_note:
        lines.append(f"생애: {unit.life_note}")
    if plan:
        lines.append(
            f"단장의 방침: {directive or '(개별 지시 없음)'} / 집중 목표: {focus or '없음'}"
        )
    else:
        lines.append("단장이 없다. 방침도 없다. 스스로 판단한다.")
    if verdict == "deviate":
        lines.append(
            "당신은 이번 턴 단장의 방침을 따르지 않기로 했다. 살아남는 것이 먼저다. "
            "도망(FLEE)치거나 방침 밖 행동을 고르고, 이유를 말하라."
        )
    else:
        lines.append("방침 안에서 이번 턴 행동을 고른다.")
    lines.append("보이는 것: " + json.dumps(visible, ensure_ascii=False))
    if masked:
        lines.append("보이지 않는 것(판단력 한계): " + ", ".join(masked))
    if unit.skills:
        lines.append("가진 기술: " + ", ".join(_skill_text(s) for s in unit.skills))
    lines.append("가능한 행동: " + ", ".join(_action_text(a) for a in actions))
    lines.append(
        "JSON 으로만 답하라: action(ATTACK|DEFEND|SKILL|MOVE|FLEE|WAIT), target, skill, position, "
        "follows_plan(bool), reason(한 문장). 이름을 쓸 때는 id 가 아니라 표시 이름을 쓴다."
    )
    ctx = {
        "role": "character",
        "self": {
            "id": unit.id,
            "class": unit.char_class,
            "hp_pct": round(100 * unit.hp / unit.hp_max),
            "stamina": unit.stamina,
            "stamina_max": unit.stamina_max,
            "position": unit.position,
            "can_heal": any(s.effect == "heal" for s in unit.skills),
            # 이탈 사유에 생애가 나타나야 한다 — 기획서 §9 의 예시가
            # "생존 우선순위 상향, 가족 부양 책임" 이다.
            "life": unit.life_note,
            "dependents": unit.dependents,
        },
        "verdict": verdict,
        "directive": directive,
        "focus_target": focus,
        "strategy": plan.strategy if plan else None,
        "visible": visible,
        "masked": masked,
        "available": [_action_ctx(a) for a in actions],
        # 스킬이 무엇을 하는지 — 이게 없으면 읽는 쪽(모델이든 Fake 든)이 방패
        # 밀치기(자기 방어)와 강타(피해)를 구분하지 못한다(QA 라운드 1 P0-4).
        "skills": [_skill_ctx(s) for s in unit.skills],
        # id → 표시 이름. 모델이 쓰는 사유가 화면에 그대로 나가므로 id 를 쓰면 안 된다.
        "names": names or {},
    }
    return "\n".join(lines) + _ctx(ctx)


def _action_text(a: Action) -> str:
    if a.kind == "SKILL":
        return f"SKILL:{a.skill}" + (f"→{a.target}" if a.target else "")
    if a.kind == "ATTACK":
        return f"ATTACK→{a.target}"
    if a.kind == "MOVE":
        return f"MOVE→{a.position}"
    return a.kind


def _action_ctx(a: Action) -> dict[str, Any]:
    return {"kind": a.kind, "target": a.target, "skill": a.skill, "position": a.position}


_EFFECT_KO = {
    "damage": "피해",
    "snipe": "후열 저격",
    "crit": "치명 확률이 높은 피해",
    "double": "두 번 타격",
    "heal": "아군 치유",
    "guard": "자기 방어력 상승",
    "slow": "적 속도 감소",
    "blind": "적 명중 감소",
    "bless": "아군 명중 상승",
}


def _skill_text(s: SkillDef) -> str:
    return f"{s.name}({_EFFECT_KO.get(s.effect, s.effect)}, 스태미나 {s.cost})"


def _skill_ctx(s: SkillDef) -> dict[str, Any]:
    return {
        "name": s.name,
        "effect": s.effect,
        "target": s.target,
        "cost": s.cost,
        "base": s.base,
        # 피해를 내는 기술인가 — 이 한 비트가 방패 밀치기와 강타를 가른다.
        "offensive": s.effect in ("damage", "snipe", "crit", "double"),
    }


def build_boss_prompt(
    battle: Battle,
    unit: UnitState,
    actions: list[Action],
    adapt_suggestion: str | None,
    focus_override: str | None,
) -> str:
    names = {u.id: u.name for u in battle.units.values()}
    foes = [u for u in battle.units.values() if u.faction != unit.faction and u.active]
    foes_ctx = [
        {
            "id": f.id,
            "class": f.char_class,
            "hp_pct": round(100 * f.hp / f.hp_max),
            "position": f.position,
            "can_heal": any(s.effect == "heal" for s in f.skills),
        }
        for f in foes
    ]
    lines = [
        f"당신은 {unit.name}. 상대가 반복하는 것을 기억하고 대응한다.",
        f"HP {round(100 * unit.hp / unit.hp_max)}%, 스태미나 {unit.stamina}/{unit.stamina_max}.",
        "상대: " + json.dumps(foes_ctx, ensure_ascii=False),
    ]
    if adapt_suggestion:
        lines.append(f"관측된 패턴에 대한 대응 후보: {adapt_suggestion}")
    if focus_override:
        lines.append(f"우선 타격 대상: {focus_override}")
    lines.append("가능한 행동: " + ", ".join(_action_text(a) for a in actions))
    lines.append(
        "JSON 으로만 답하라: action, target, skill, "
        "adapt(focus|breach|target_healer|summon_faster|null), reason"
    )
    ctx = {
        "role": "boss",
        "self": {
            "id": unit.id,
            "hp_pct": round(100 * unit.hp / unit.hp_max),
            "stamina": unit.stamina,
        },
        "enemies": foes_ctx,
        "adapt_suggestion": adapt_suggestion,
        "focus_override": focus_override,
        "available": [_action_ctx(a) for a in actions],
        "skills": [_skill_ctx(s) for s in unit.skills],
        "names": names,
        "turn": battle.turn,
    }
    return "\n".join(lines) + _ctx(ctx)


def build_narration_prompt(kind: str, facts: dict[str, Any], fallback: str) -> str:
    lines = [
        "다음 사실을 한두 문장의 중세 용병단 서사로 쓴다. 사실을 바꾸지 않는다.",
        f"종류: {kind}",
        "사실: " + json.dumps(facts, ensure_ascii=False),
        "JSON 으로만 답하라: narration",
    ]
    return "\n".join(lines) + _ctx(
        {"role": "narrator", "kind": kind, "facts": facts, "fallback": fallback}
    )

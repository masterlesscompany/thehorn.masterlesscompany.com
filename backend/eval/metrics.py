"""트레이스 → 지표. 순수 함수 (설계 §10).

실험은 **후처리만으로** 계산되어야 한다 — 러너를 고쳐야 지표가 나오면 실험이
코어를 건드리게 되고, 그것이 기획서 §3.1 이 막으려는 것이다.
"""

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from apps.arena.domain.entities.trace_event import TraceEvent

# 「철수」는 벌점이 아니다(기획서 v3 §7.1b). 목표를 이룬 판만 "이겼다" 로 센다.
CLEARED_GRADES = ("full_success", "success")
GRADES = ("full_success", "success", "withdraw", "failure", "disaster")


@dataclass(frozen=True)
class MissionMetrics:
    """계약 안의 판 하나. 계약은 여러 판이고, 지표는 그 전부를 봐야 한다."""

    no: int
    outcome: str
    grade: str
    turns: int
    survivors: int
    injured: int
    taken: int
    dead: int
    fled: int
    calls: int
    plans: int
    abandoned: bool

    @property
    def cleared(self) -> bool:
        return self.grade in CLEARED_GRADES


@dataclass(frozen=True)
class RunMetrics:
    missions: tuple[MissionMetrics, ...]
    party_size: int
    deviations: int
    adaptations: int
    # 발동했지만 **상태가 안 바뀐** 적응. 승패로는 안 보이는 것을 여기서 본다 —
    # E2 가 "아무것도 재지 못한다" 는 것이 지표 탓인지 메커니즘 탓인지 갈린다
    # (QA 2026-09-09 V5).
    adaptations_no_change: int
    # 적응이 지목한 대상을 보스가 **실제로 때렸는가**. 상태는 바뀌는데 승패가
    # 안 움직이면 그 사이 어디가 끊겼는지 이 값이 말한다(QA 2026-09-09 V5).
    focus_strikes: int
    focus_followed: int
    replans: int
    fallbacks: int
    actions: dict[str, int]

    # ── 계약 단위 ────────────────────────────────────────────────────────
    @property
    def cleared(self) -> int:
        return sum(1 for m in self.missions if m.cleared)

    @property
    def contract_clear(self) -> bool:
        """계약을 끝까지 완주했는가. E1 의 헤드라인은 이것이다."""
        return bool(self.missions) and all(m.cleared for m in self.missions)

    @property
    def turns(self) -> int:
        return sum(m.turns for m in self.missions)

    @property
    def calls(self) -> int:
        return max((m.calls for m in self.missions), default=0)

    @property
    def plans(self) -> int:
        return sum(m.plans for m in self.missions)

    @property
    def abandoned(self) -> bool:
        return any(m.abandoned for m in self.missions)

    @property
    def dead(self) -> int:
        return sum(m.dead for m in self.missions)

    @property
    def taken(self) -> int:
        return sum(m.taken for m in self.missions)

    @property
    def injured(self) -> int:
        return sum(m.injured for m in self.missions)

    @property
    def fled(self) -> int:
        return sum(m.fled for m in self.missions)

    @property
    def everyone_home(self) -> bool:
        """아무도 죽지 않고 아무도 굴에 끌려가지 않았는가.

        기획서 §8.1 은 감독의 가치를 "나쁜 조합에서의 **회복력**" 이라고 쓴다.
        완주율만 보면 감독이 목표를 포기하고 전원을 데리고 나온 판이 벌점이 되어
        (「철수」는 벌점이 아니다 — v3 §7.1b) 자기 주장을 반증하게 된다.
        E1 은 두 축을 함께 낸다: 완주했는가, 그리고 데리고 나왔는가.
        """
        return all(m.dead == 0 and m.taken == 0 for m in self.missions)

    @property
    def survivors(self) -> int:
        """마지막 판에 서 있던 사람. 계약을 끝까지 걸어 나온 수다."""
        return self.missions[-1].survivors if self.missions else 0

    @property
    def survival_rate(self) -> float:
        return self.survivors / self.party_size if self.party_size else 0.0


def metrics_of(events: Sequence[TraceEvent]) -> RunMetrics:
    """한 판의 트레이스에서 지표를 뽑는다.

    **판마다 하나씩** 담는다. 마지막 판만 쓰면 1판의 참사가 통째로 사라지고,
    E1 은 감독이 아니라 직전 판의 끌려감 주사위를 재게 된다(QA 2026-09-09 V1) —
    감독이 판을 길게 끌면 쓰러진 사람이 늘고, 그가 끌려가면 다음 판을 둘로 간다.
    그 연쇄의 끝만 보면 "감독은 해롭다" 는 결론이 나온다.

    판단 횟수(이탈·적응·재계획)와 행동 분포는 **런 전체**에서 온다.
    party_size 는 출전 명단 전체다.
    """
    start = next(e for e in events if e.kind == "run_start")
    party_size = len(start.payload["lineup"])

    missions = tuple(
        MissionMetrics(
            no=int(e.payload["no"]),
            outcome=str(e.payload["outcome"]),
            # 등급은 v3 에서 왔다. 옛 트레이스에는 없으므로 승패에서 유추한다.
            grade=str(
                e.payload.get("grade")
                or ("full_success" if e.payload["outcome"] == "win" else "failure")
            ),
            turns=int(e.payload["turns"]),
            survivors=len(e.payload["survivors"]),
            injured=len(e.payload.get("injured") or []),
            taken=len(e.payload.get("taken") or []),
            dead=len(e.payload["dead"]),
            fled=len(e.payload["fled"]),
            calls=int(e.payload["calls_used"]),
            plans=int(e.payload["plans"]),
            abandoned=bool(e.payload["abandoned"]),
        )
        for e in events
        if e.kind == "mission_end"
    )

    # **파티의 행동만 센다.** 보스와 수하도 decision 을 내므로 전부 세면 적의
    # 행동이 섞인다 — 실측(시드 3, 균등)에서 decision 98개 중 40개(41%)가 적이었고
    # E3 의 "성향별 행동 분포" 가 그만큼 틀렸다(QA 라운드 2).
    party = set(start.payload["lineup"])
    actions: dict[str, int] = {}
    for e in events:
        if e.kind == "decision" and e.actor in party:
            label = str(e.payload["label"]).split(":")[0]
            actions[label] = actions.get(label, 0) + 1
    return RunMetrics(
        missions=missions,
        party_size=party_size,
        deviations=sum(
            1 for e in events if e.kind == "compliance" and e.payload["verdict"] == "deviate"
        ),
        adaptations=sum(1 for e in events if e.kind == "boss_adapt"),
        adaptations_no_change=sum(
            1
            for e in events
            if e.kind == "boss_adapt" and (e.payload.get("effect") or {}).get("no_change")
        ),
        **_focus_follow(events),
        replans=sum(1 for e in events if e.kind == "replan_trigger"),
        fallbacks=sum(
            1
            for e in events
            if e.kind in ("decision", "plan") and (e.payload.get("model") or {}).get("fallback")
        ),
        actions=actions,
    )


def _focus_follow(events: Sequence[TraceEvent]) -> dict[str, int]:
    """적응이 대상을 지목한 뒤, 보스의 타격이 그 대상에 갔는가.

    지목은 `boss_adapt` 의 effect.after 이고, 그 뒤 같은 보스의 `resolution`
    타격을 센다. 트레이스만 읽는다 — 러너를 고치지 않는다(기획서 §3.1).
    """
    focus: str | None = None
    boss: str | None = None
    strikes = followed = 0
    for e in events:
        if e.kind == "boss_adapt":
            # `field` 를 봐야 한다. `summon_faster` 의 effect 는
            # `{"field":"summon_every","after":2}` 라 `2` 가 truthy 로 "지목" 이
            # 되고, 이후 보스 타격이 전부 **절대 안 맞는** 지목으로 계수되며
            # 살아 있는 진짜 지목까지 지워졌다 — 방패병 몰빵에서 23% vs 참값 47%
            # (QA 재검 2026-09-09 R12).
            eff = e.payload.get("effect") or {}
            if eff.get("field") != "boss_focus":
                continue
            boss = e.actor
            focus = eff.get("after")
        elif e.kind == "mission_start":
            focus = boss = None  # 판이 바뀌면 지목도 사라진다
        elif e.kind == "resolution" and focus and e.actor == boss:
            for s in e.payload.get("strikes", []):
                strikes += 1
                followed += s.get("target") == focus
    return {"focus_strikes": strikes, "focus_followed": followed}


def aggregate(runs: Sequence[RunMetrics]) -> dict[str, Any]:
    """여러 판을 하나의 칸으로.

    두 층을 따로 낸다 — **판 단위**(win_rate 등)는 계약 안 모든 판을 세고,
    **계약 단위**(clear_rate)는 끝까지 완주한 계약의 비율이다. 둘을 섞으면
    1판을 말아먹고 2판을 이긴 계약이 두 판 다 이긴 계약과 같은 점수를 받는다.
    """
    n = len(runs)
    if n == 0:
        return {"games": 0}

    ms = [m for r in runs for m in r.missions]
    total = len(ms) or 1

    def rate(outcome: str) -> float:
        return round(sum(1 for m in ms if m.outcome == outcome) / total, 3)

    grades = Counter(m.grade for m in ms)
    action_total: dict[str, int] = {}
    for r in runs:
        for k, v in r.actions.items():
            action_total[k] = action_total.get(k, 0) + v
    acted = sum(action_total.values()) or 1
    return {
        "games": n,
        "missions": len(ms),
        # 판 단위.
        "win_rate": rate("win"),
        "retreat_rate": rate("retreat"),
        "loss_rate": rate("lose"),
        "draw_rate": rate("draw"),
        # v3 의 헤드라인은 승패가 아니라 5등급이다(기획서 v3 §7.1b).
        "grade_share": {g: round(grades[g] / total, 3) for g in GRADES},
        # 계약 단위.
        "clear_rate": round(sum(1 for r in runs if r.contract_clear) / n, 3),
        "home_rate": round(sum(1 for r in runs if r.everyone_home) / n, 3),
        "survival_rate": round(sum(r.survival_rate for r in runs) / n, 3),
        "abandon_rate": round(sum(1 for r in runs if r.abandoned) / n, 3),
        # 쓰러짐 3분기(기획서 v3 §6.0) — 계약 하나당 몇 명인가.
        "avg_injured": round(sum(r.injured for r in runs) / n, 2),
        "avg_taken": round(sum(r.taken for r in runs) / n, 2),
        "avg_dead": round(sum(r.dead for r in runs) / n, 2),
        "avg_turns": round(sum(r.turns for r in runs) / n, 1),
        # `calls` 는 **판 최댓값**이다(기획서 §7.1 의 "전투 1판 = 100~300"). 이름을
        # `avg_calls` 로 두면 계약 비용을 뜻하는 것처럼 읽힌다(QA 재검 R19).
        "avg_peak_mission_calls": round(sum(r.calls for r in runs) / n, 1),
        "max_calls": max(r.calls for r in runs),
        "avg_contract_calls": round(sum(sum(m.calls for m in r.missions) for r in runs) / n, 1),
        "avg_plans": round(sum(r.plans for r in runs) / n, 1),
        "avg_deviations": round(sum(r.deviations for r in runs) / n, 1),
        "avg_adaptations": round(sum(r.adaptations for r in runs) / n, 1),
        # 발동한 적응 중 상태를 못 바꾼 비율. 1.0 에 가까우면 적응은 로그에만 있다.
        "adapt_no_change_rate": round(
            sum(r.adaptations_no_change for r in runs) / max(1, sum(r.adaptations for r in runs)), 3
        ),
        # 지목한 대상을 실제로 때린 비율. 낮으면 적응이 상태만 바꾸고 행동에 못 닿은 것이다.
        "focus_follow_rate": round(
            sum(r.focus_followed for r in runs) / max(1, sum(r.focus_strikes for r in runs)), 3
        ),
        "fallbacks": sum(r.fallbacks for r in runs),
        # 성향별 행동 분포(E3)의 재료. 여기서 미리 비율로 만들어 둔다.
        "action_share": {k: round(v / acted, 3) for k, v in sorted(action_total.items())},
    }


def paired(
    on: Sequence["RunMetrics"],
    off: Sequence["RunMetrics"],
    criterion: "Callable[[RunMetrics], bool]",
    axis: str,
) -> dict[str, Any]:
    """같은 시드로 짝지은 비교 (McNemar).

    성공 기준을 **함수로 받는다.** bool 리스트를 호출자가 만들게 두었더니
    `paired(cleared["on"], home["off"])` 처럼 두 축을 섞어도 아무도 못 잡았고,
    결과 dict 에 축 이름이 없어 JSON 만 보고는 무엇을 짝지었는지도 알 수
    없었다(QA 재검 2026-09-09 R19). 이제 `axis` 가 결과에 남는다.

    기본 기준은 **계약 완주**다(`RunMetrics.contract_clear`). 마지막 판의 승패로
    짝을 지으면 앞판에서 누가 끌려갔는지가 결과를 지배한다(QA 2026-09-09 V1).

    ON/OFF 가 같은 시드를 쓰므로 짝을 살릴 수 있다. 비율만 보면 30판에서 3판
    차이가 잡음과 구별되지 않는다 — 짝지으면 같은 판 수로도 훨씬 잘 갈린다.
    p 는 이항 정확검정(양측)이고 외부 의존성 없이 계산한다.
    """
    쌍 = [(criterion(a), criterion(b)) for a, b in zip(on, off, strict=True)]
    only_on = sum(1 for a, b in 쌍 if a and not b)
    only_off = sum(1 for a, b in 쌍 if b and not a)
    return {
        "axis": axis,
        "games": len(on),
        "only_on_wins": only_on,
        "only_off_wins": only_off,
        "p_value": _binom_two_sided(only_on, only_on + only_off),
    }


def _binom_two_sided(k: int, n: int) -> float:
    """p=0.5 이항 양측검정. n 이 0 이면 차이가 없다는 뜻이라 1.0."""
    if n == 0:
        return 1.0
    from math import comb

    total = 2**n
    k = min(k, n - k)
    tail = sum(comb(n, i) for i in range(k + 1))
    return round(min(1.0, 2 * tail / total), 4)

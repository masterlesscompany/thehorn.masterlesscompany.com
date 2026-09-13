"""재계획 트리거 (기획서 §8.3, 설계 §6.3).

캐릭터 이탈 · 승산 붕괴 · 적응 감지 · 환경 변화. 한 턴에 재계획은 최대 1회이고,
연속 3회를 넘으면 감독에게 포기 여부를 강제로 묻는다(forced).
"""

from dataclasses import dataclass, field

from apps.arena.domain.constants.balance import (
    ODDS_COLLAPSE_STEP,
    REPLAN_DEVIATION_COOLDOWN,
    REPLAN_MAX_CONSECUTIVE,
)
from apps.arena.domain.entities.types import Plan


@dataclass(frozen=True)
class Trigger:
    kind: str  # deviation | odds_collapse | adaptation | environment
    detail: str


@dataclass
class ReplanState:
    """러너가 판 하나 동안 들고 다니는 상태. 순수 함수가 읽고 갱신한다."""

    collapse_level: float | None = None  # 마지막으로 트리거를 낸 승산 계단
    turn: int = 0
    last_deviation_replan: int = -99
    consecutive: int = 0
    total: int = 0
    triggered_this_turn: bool = False
    deviations: list[str] = field(default_factory=list)
    adaptations: list[str] = field(default_factory=list)
    environment_changes: list[str] = field(default_factory=list)

    def begin_turn(self, turn: int = 0) -> None:
        """턴 시작. 한 턴 1회 제한만 푼다.

        이탈·적응 신호는 여기서 지우지 않는다 — 그것들은 **직전 턴 안에서** 쌓이고
        이번 턴 시작에 읽혀야 한다. 예전에는 여기서 함께 비웠고, 그래서 기획서
        §8.3 의 트리거 4종 중 이탈·적응 두 종이 한 번도 발동하지 않았다
        (160판 계측: replan_trigger 가 전부 odds_collapse).
        """
        self.triggered_this_turn = False
        self.turn = turn

    def consume_signals(self) -> None:
        """트리거 판정이 끝났다. 읽은 신호를 비운다 — 다음 턴이 새로 쌓는다."""
        self.deviations.clear()
        self.adaptations.clear()
        self.environment_changes.clear()


ADAPT_KO = {
    "repeat_attacker": "같은 자의 반복 공격",
    "frontline_wall": "전열이 막고 있는 것",
    "healing": "반복된 치유",
    "turtle": "방어 일변도",
}


def replan_triggers(
    state: ReplanState, odds_value: float, plan: Plan | None, names: dict[str, str] | None = None
) -> list[Trigger]:
    """이번 턴에 재계획을 부를 이유들. 비어 있으면 그대로 간다."""
    if plan is None or state.triggered_this_turn:
        return []
    out: list[Trigger] = []
    if state.deviations and state.turn - state.last_deviation_replan >= REPLAN_DEVIATION_COOLDOWN:
        n = names or {}
        who = ", ".join(n.get(x, x) for x in dict.fromkeys(state.deviations))
        out.append(Trigger("deviation", f"{who} 가 방침을 이탈했다"))
    if odds_value <= plan.retreat_threshold:
        # 첫 진입은 1회, 이후 0.1 씩 더 내려갈 때마다.
        level = _floor_step(odds_value)
        if state.collapse_level is None or level < state.collapse_level:
            out.append(
                Trigger(
                    "odds_collapse", f"승산 {odds_value:.2f} ≤ 임계 {plan.retreat_threshold:.2f}"
                )
            )
    for what in state.adaptations:
        out.append(Trigger("adaptation", f"적이 읽었다: {ADAPT_KO.get(what, what)}"))
    for what in state.environment_changes:
        out.append(Trigger("environment", what))
    return out


def _floor_step(v: float) -> float:
    return round((v // ODDS_COLLAPSE_STEP) * ODDS_COLLAPSE_STEP, 2)


def mark_replanned(
    state: ReplanState, odds_value: float, plan: Plan | None, triggers: list[Trigger] | None = None
) -> bool:
    """재계획을 실행했다고 기록한다. 강제 결정(연속 상한 초과)이면 True."""
    state.triggered_this_turn = True
    if any(t.kind == "deviation" for t in triggers or ()):
        state.last_deviation_replan = state.turn
    state.total += 1
    state.consecutive += 1
    if plan is not None and odds_value <= plan.retreat_threshold:
        state.collapse_level = _floor_step(odds_value)
    return state.consecutive > REPLAN_MAX_CONSECUTIVE


def mark_quiet_turn(state: ReplanState) -> None:
    """재계획 없이 지나간 턴은 연속 카운트를 끊는다."""
    state.consecutive = 0

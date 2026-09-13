"""성장 포인트 (기획서 §5, 설계 §7.3).

유저가 찍은 포인트는 시스템이 절대 뺏지 않는다 — `Stats` 에 감소 경로가 없다.
은행 가능: 안 쓰면 남는다.
"""

from dataclasses import replace
from typing import Any

from apps.arena.domain.constants.balance import GROWTH_LOSE, GROWTH_WIN
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import STAT_LABELS, Character
from apps.arena.domain.services.rules.stats import allocate


def points_for(outcome: str) -> int:
    """승리 10 / 그 밖 6.

    패배·후퇴에도 주는 이유: 0 이면 후퇴 판단에 벌점이 되어 단장이 포기를
    회피하게 된다. 포기가 진짜 판단이려면 값이 싸지도 비싸지도 않아야 한다.
    """
    return GROWTH_WIN if outcome == "win" else GROWTH_LOSE


def grant(
    members: list[tuple[Character, Any, str]],
    outcome: str,
    allocations: dict[str, dict[str, int]],
    banked: dict[str, int],
    tracer: Tracer,
) -> tuple[list[tuple[Character, Any, str]], dict[str, int]]:
    """지급 → 유저 분배 적용 → 남은 것은 은행. (바뀐 멤버, 새 은행 잔고)."""
    granted = points_for(outcome)
    out = []
    new_bank = dict(banked)
    for c, build, voice in members:
        pool = new_bank.get(c.id, 0) + granted
        alloc = {k: v for k, v in (allocations.get(c.id) or {}).items() if v > 0}
        spent = sum(alloc.values())
        if spent > pool:
            raise ValueError(f"{c.name} 에게 준 포인트는 {pool} 인데 {spent} 를 찍으려 한다")
        # 상한(20) 검증은 allocate 가 한다. 모르는 능력치·음수·실수도 거기서 걸린다.
        stats = allocate(c.stats, alloc) if alloc else c.stats
        new_bank[c.id] = pool - spent
        out.append((replace(c, stats=stats), build, voice))
        tracer.emit(
            "growth_points",
            {
                "granted": granted,
                "outcome": outcome,
                "pool": pool,
                "spent": {STAT_LABELS[k]: v for k, v in alloc.items()},
                "banked": new_bank[c.id],
                "stats_after": stats.as_dict(),
            },
            actor=c.id,
        )
    return out, new_bank

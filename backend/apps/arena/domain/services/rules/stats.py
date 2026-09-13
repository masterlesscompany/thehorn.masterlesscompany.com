"""능력치 분배와 파생치 (기획서 §4.2 · 설계 §13)."""

from apps.arena.domain.constants.balance import (
    FREE_POINTS,
    HP_BASE,
    HP_PER_CON,
    STAMINA_BASE,
    STAMINA_PER_CON,
    STAT_BASE,
)
from apps.arena.domain.entities.types import STAT_LABELS, STAT_NAMES, Stats


def base_stats() -> Stats:
    return Stats(*([STAT_BASE] * 6))


def allocate(base: Stats, points: dict[str, int]) -> Stats:
    """유저의 자유 포인트 분배. 총량 ≤ FREE_POINTS, 음수 금지, 상한은 Stats 가 본다."""
    for name, p in points.items():
        if name not in STAT_NAMES:
            raise ValueError(f"모르는 능력치: {name}")
        # bool 은 int 의 하위 타입이라 True 가 1점으로 들어간다. 실수는 능력치를
        # 10.5 로 만들고 그 값이 HP 로 흘러 트레이스에 실린다(QA 라운드 1 P1-5).
        # 문자열·None 은 비교에서 TypeError 가 나 API 가 500 을 낸다 — 여기서 잡는다.
        if isinstance(p, bool) or not isinstance(p, int):
            raise ValueError(f"{STAT_LABELS[name]} 포인트는 정수여야 한다: {p!r}")
        if p < 0:
            raise ValueError(f"{STAT_LABELS[name]} 에 음수 포인트({p})를 줄 수 없다")
    total = sum(points.values())
    if total > FREE_POINTS:
        raise ValueError(f"포인트 총량 {total} 이 상한 {FREE_POINTS} 을 넘는다")
    return base.with_added(**points)


def hp_max(stats: Stats) -> int:
    return HP_BASE + stats.con * HP_PER_CON


def stamina_max(stats: Stats) -> int:
    return STAMINA_BASE + stats.con * STAMINA_PER_CON

"""회수 비용 (기획서 v3 §6.8).

**회수는 보장된 거래가 아니다.** 돈을 내도 실패할 수 있고, 실패하면 계약
진도까지 잃는다. 이것이 몸값과의 결정적 차이다.

A단계는 결정을 기록하는 데까지다. 회수 미션 개방과 출동 슬롯 소모는
B단계다(기획서 v3 §12).

은화가 아직 없어 **누적 투자를 성장 포인트로 센다.** 은화가 들어오면
invested_of 의 몸통만 바뀐다 — 비율과 호출부는 그대로다.
"""

from apps.arena.domain.constants.balance import RECOVERY_COST_RATIO, STAT_BASE
from apps.arena.domain.entities.types import Stats


def invested_of(stats: Stats) -> int:
    """기본값 위에 얹은 포인트의 합. 유저가 이 사람에게 쏟은 것이다."""
    return sum(max(0, v - STAT_BASE) for v in stats.as_dict().values())


def recovery_cost(invested: int) -> int:
    return round(invested * RECOVERY_COST_RATIO)

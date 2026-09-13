"""회수 결정 — 기획서 v3 §6.8.

몸값은 은화만 태우지만 회수는 은화와 출동 슬롯을 동시에 태운다. A단계는
**결정을 기록하는 데까지**다 — 회수 미션 개방은 B단계다(기획서 v3 §12).
"""

from apps.arena.domain.constants.balance import RECOVERY_COST_RATIO, STAT_BASE
from apps.arena.domain.services.rules.recovery import invested_of, recovery_cost
from apps.arena.domain.services.rules.stats import base_stats


def test_아무것도_안_찍었으면_투자가_0이다():
    assert invested_of(base_stats()) == 0


def test_찍은_만큼이_투자다():
    from dataclasses import replace

    s = replace(base_stats(), agi=STAT_BASE + 8, wis=STAT_BASE + 4)
    assert invested_of(s) == 12


def test_회수_비용은_누적_투자의_6할이다():
    assert recovery_cost(40) == round(40 * RECOVERY_COST_RATIO)
    assert recovery_cost(0) == 0


def test_비용은_투자에_비례해_커진다():
    """오래 키운 사람일수록 되찾는 값이 비싸다 — 그게 딜레마의 축이다."""
    assert recovery_cost(10) < recovery_cost(30) < recovery_cost(60)

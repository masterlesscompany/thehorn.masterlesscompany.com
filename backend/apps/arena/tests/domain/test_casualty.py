"""쓰러짐 3분기 — 기획서 v3 §6.0.

HP 0 이 곧 사망이 아니다. 전투 종료 시 부상 / 끌려감 / 사망으로 갈린다.
"""

import pytest

from apps.arena.adapter.outbound.strategies.dice import FixedDice, SeededDice
from apps.arena.domain.constants.balance import CASUALTY_TABLE
from apps.arena.domain.services.rules.casualty import resolve_casualty


def test_봄_구간은_사망이_0이다():
    """기획서 v3 §6.0 — 1~4 출동은 사망 0% 고정. 고블린은 죽이기보다 끌고 간다."""
    부상, 끌려감, 사망 = CASUALTY_TABLE["spring"]
    assert 사망 == 0
    # 100 번 굴려도 사망이 나오지 않는다.
    결과 = {resolve_casualty(FixedDice([r]), "spring").verdict for r in range(1, 101)}
    assert "dead" not in 결과
    assert 결과 == {"injured", "taken"}


def test_구간이_깊어질수록_사망이_늘어난다():
    사망률 = [CASUALTY_TABLE[t][2] for t in ("spring", "summer", "autumn")]
    assert 사망률 == sorted(사망률) and 사망률[0] < 사망률[-1]


def test_각_구간의_확률은_100_이다():
    for tier, (부상, 끌려감, 사망) in CASUALTY_TABLE.items():
        assert 부상 + 끌려감 + 사망 == 100, tier


@pytest.mark.parametrize("tier", sorted(CASUALTY_TABLE))
def test_굴림은_표의_경계를_그대로_따른다(tier):
    부상, 끌려감, _ = CASUALTY_TABLE[tier]
    if 부상:
        assert resolve_casualty(FixedDice([부상]), tier).verdict == "injured"
    if 끌려감:
        assert resolve_casualty(FixedDice([부상 + 끌려감]), tier).verdict == "taken"
    assert resolve_casualty(FixedDice([100]), tier).verdict == (
        "dead" if CASUALTY_TABLE[tier][2] else "taken"
    )


def test_같은_시드는_같은_판정을_낸다():
    a = [resolve_casualty(SeededDice(7), "summer") for _ in range(20)]
    b = [resolve_casualty(SeededDice(7), "summer") for _ in range(20)]
    assert a == b


def test_판정은_굴림과_경계를_함께_돌려준다():
    """QA 2026-09-09 J2·V10 — 가장 무거운 판정만 "왜" 를 못 댔다.

    인스펙터가 "84 를 굴렸고 부상은 85 까지다" 라고 말할 수 있어야 한다.
    결과만 남기면 이 판정은 그냥 랜덤과 구별되지 않는다.
    """
    r = resolve_casualty(FixedDice([84]), "boss_juvenile")
    assert r.verdict == "injured" and r.roll == 84
    # 누적 경계 — 부상 85, 끌려감 98, 사망 100.
    assert r.bounds == (("injured", 85), ("taken", 98), ("dead", 100))
    assert r.tier == "boss_juvenile"

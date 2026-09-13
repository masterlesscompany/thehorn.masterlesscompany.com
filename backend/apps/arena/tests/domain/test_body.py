from apps.arena.adapter.outbound.strategies.dice import FixedDice, SeededDice
from apps.arena.domain.services.rules.body import roll_body


def test_주사위가_키_체형_몸무게를_정한다():
    # d50=50 → 200cm, d6=6 → 건장, d5=5 → BMI 26+2=28 → 28×2.0² = 112
    body = roll_body(FixedDice([50, 6, 5]))
    assert (body.height_cm, body.build, body.weight_kg) == (200, "sturdy", 112)


def test_마른_체형():
    # d50=10 → 160, d6=1 → 마른, d5=3 → BMI 18 → 18×1.6² = 46.08 → 46
    body = roll_body(FixedDice([10, 1, 3]))
    assert (body.height_cm, body.build, body.weight_kg) == (160, "slim", 46)


def test_키는_151에서_200_사이다():
    heights = {roll_body(SeededDice(s)).height_cm for s in range(300)}
    assert min(heights) >= 151 and max(heights) <= 200
    assert len(heights) > 30, "주사위가 죽어 있다"


def test_세_체형이_모두_나온다():
    builds = {roll_body(SeededDice(s)).build for s in range(100)}
    assert builds == {"slim", "normal", "sturdy"}

from apps.arena.adapter.outbound.strategies.dice import FixedDice, SeededDice


def test_같은_시드는_같은_수열을_낸다():
    a, b = SeededDice(7), SeededDice(7)
    assert [a.roll(100) for _ in range(20)] == [b.roll(100) for _ in range(20)]
    assert a.uniform() == b.uniform()


def test_다른_시드는_다른_수열을_낸다():
    a, b = SeededDice(1), SeededDice(2)
    assert [a.roll(100) for _ in range(20)] != [b.roll(100) for _ in range(20)]


def test_굴림은_1과_면수_사이다():
    d = SeededDice(3)
    rolls = [d.roll(6) for _ in range(500)]
    assert min(rolls) == 1 and max(rolls) == 6


def test_고정_주사위는_순서대로_낸다():
    d = FixedDice([3, 50, 1], uniforms=[0.25])
    assert (d.roll(6), d.roll(100), d.roll(6)) == (3, 50, 1)
    assert d.uniform() == 0.25


def test_고정_주사위가_바닥나면_마지막_값을_반복한다():
    """테스트 픽스처가 굴림 수를 정확히 세지 않아도 되게 한다."""
    d = FixedDice([4])
    assert (d.roll(6), d.roll(6)) == (4, 4)

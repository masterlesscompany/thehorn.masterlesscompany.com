import pytest

from apps.arena.domain.entities.types import Body, Disposition, Stats


def test_능력치는_감소_경로가_없다():
    """기획서 §5 — 유저가 찍은 포인트를 시스템이 뺏지 않는다."""
    s = Stats(8, 8, 8, 8, 8, 8)
    with pytest.raises(ValueError):
        s.with_added(str_=-1)


def test_능력치는_상한을_넘지_못한다():
    with pytest.raises(ValueError):
        Stats(21, 8, 8, 8, 8, 8)
    with pytest.raises(ValueError):
        Stats(8, 8, 8, 8, 8, 8).with_added(agi=13)


def test_능력치_더하기는_새_객체를_돌려준다():
    s = Stats(8, 8, 8, 8, 8, 8)
    t = s.with_added(wis=5, con=2)
    assert (t.wis, t.con) == (13, 10)
    assert s.wis == 8


def test_체형이_무게등급을_정한다():
    assert Body(170, "slim", 55).weight_class == 1
    assert Body(170, "normal", 65).weight_class == 2
    assert Body(170, "sturdy", 80).weight_class == 3


def test_성향은_범위를_벗어나지_못한다():
    with pytest.raises(ValueError):
        Disposition(101, 0, 0, 0)
    with pytest.raises(ValueError):
        Disposition(0, -101, 0, 0)


def test_성향_이동은_범위_안으로_잘린다():
    """생애 이벤트의 파라미터 변경(기획서 §6.7)이 범위를 넘으면 잘라 둔다.

    예외로 막으면 이벤트 하나가 인터미션 전체를 죽인다.
    """
    d = Disposition(90, 0, 0, -95).shifted(risk=20, sacrifice=-20)
    assert (d.risk, d.sacrifice) == (100, -100)

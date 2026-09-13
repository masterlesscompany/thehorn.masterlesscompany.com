import pytest

from apps.arena.domain.services.rules.stats import allocate, base_stats, hp_max, stamina_max


def test_기본_능력치는_전부_8이다():
    assert base_stats().as_dict() == dict.fromkeys(["str_", "agi", "con", "int_", "wis", "luck"], 8)


def test_자유_포인트_18을_넘으면_거부한다():
    with pytest.raises(ValueError, match="18"):
        allocate(base_stats(), {"str_": 10, "agi": 9})


def test_한_능력치_몰빵은_허용된다():
    """ "한 명만 몰빵" 사회실험의 레버는 유저 포인트다(기획서 §5). 8+12=20."""
    s = allocate(base_stats(), {"str_": 12, "con": 6})
    assert (s.str_, s.con) == (20, 14)


def test_음수_포인트는_거부한다():
    with pytest.raises(ValueError):
        allocate(base_stats(), {"str_": -1, "agi": 5})


def test_모르는_능력치는_거부한다():
    with pytest.raises(ValueError):
        allocate(base_stats(), {"charisma": 3})


def test_파생치():
    s = base_stats().with_added(con=4)  # CON 12
    assert hp_max(s) == 40 + 12 * 6
    assert stamina_max(s) == 20 + 12 * 2


def test_실수와_bool_포인트는_거부한다():
    """QA 라운드 1 P1-5 — 2.5 가 통과해 능력치가 10.5 가 됐고 그 값이 HP 로 흘렀다."""
    import pytest

    for bad in ({"str_": 2.5}, {"str_": True}, {"str_": "5"}, {"str_": None}):
        with pytest.raises(ValueError, match="정수"):
            allocate(base_stats(), bad)

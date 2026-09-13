from apps.arena.domain.entities.types import Body, Equipment
from apps.arena.domain.services.rules.equipment import efficiency
from apps.arena.domain.services.rules.stats import base_stats

판금 = Equipment("판금 갑옷", weight_class=3, min_height=0, min_str=11, base_damage=0, armor=30)
장궁 = Equipment("장궁", weight_class=2, min_height=170, min_str=8, base_damage=9, is_long=True)
단검 = Equipment("단검", weight_class=1, min_height=0, min_str=4, base_damage=5)


def test_마른_몸에_판금은_명중과_속도_페널티():
    """장착 불가가 아니라 페널티(기획서 §4.3 효율 스펙트럼)."""
    m = efficiency(Body(165, "slim", 52), base_stats(), 판금)
    assert m.hit == -20
    assert m.speed == -2
    assert ("무게 미달", -20) in m.notes


def test_힘_미달은_스태미나_배수():
    m = efficiency(Body(180, "sturdy", 90), base_stats(), 판금)  # STR 8 vs 11
    assert m.stamina_mult == 1.3
    assert any(n == "힘 미달" for n, _ in m.notes)


def test_키_미달은_장궁에만():
    m = efficiency(Body(160, "normal", 60), base_stats(), 장궁)
    assert m.hit == -10  # (170-160)/5 × 5
    m2 = efficiency(Body(160, "normal", 60), base_stats(), 단검)
    assert m2.hit == 0


def test_적합하면_페널티가_없다():
    m = efficiency(Body(185, "sturdy", 95), base_stats().with_added(str_=6), 판금)
    assert (m.hit, m.speed, m.stamina_mult, m.notes) == (0, 0, 1.0, ())

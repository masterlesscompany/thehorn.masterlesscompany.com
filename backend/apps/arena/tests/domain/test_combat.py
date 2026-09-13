from dataclasses import replace

from apps.arena.adapter.outbound.strategies.dice import FixedDice
from apps.arena.domain.constants.balance import (
    FLEE_BASE,
    FLEE_PER_AGI_DIFF,
    HIT_BASE,
    HIT_PER_AGI_DIFF,
)
from apps.arena.domain.services.battle.order import turn_order
from apps.arena.domain.services.battle.state import Battle, unit_from_character, unit_from_enemy
from apps.arena.domain.services.rules.combat import damage, flee_chance, hit_chance, speed
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.environments import MINE, SWAMP
from content.monsters import JUVENILE_MINOTAUR
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def _char(cid: str, **stat_override):
    c = ROSTER_BY_ID[cid]
    c = replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))
    if stat_override:
        c = replace(c, stats=replace(c.stats, **stat_override))
    return c


def _battle(env=MINE, party=("martin", "gilles", "thoma"), **overrides):
    units = {}
    for cid in party:
        c = _char(cid, **overrides.get(cid, {}))
        units[cid] = unit_from_character(c, choose_build(c), "party", "front")
    for e in JUVENILE_MINOTAUR.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(seed=1, environment=env, units=units, enemy_def=JUVENILE_MINOTAUR)


def test_명중은_기본_60에_민첩차를_더한다():
    b = _battle()
    needed, bd = hit_chance(b.units["thoma"], b.units["minotaur"], MINE)
    # 수치를 박지 않는다 — 밸런스를 튜닝하면 같이 움직인다(QA 2026-09-09).
    # 마른 몸에 장궁(무게등급 2) 이라 무기 효율 페널티가 함께 붙는다.
    차 = (b.units["thoma"].stats.agi - b.units["minotaur"].stats.agi) * HIT_PER_AGI_DIFF
    assert ("민첩 차", 차) in bd and ("무기 효율", -10) in bd
    assert needed == HIT_BASE + 차 - 10


def test_후열_원거리는_폐광에서_거리_페널티를_받는다():
    b = _battle()
    전열, _ = hit_chance(b.units["thoma"], b.units["minotaur"], MINE)
    b.units["thoma"].position = "back"
    needed, bd = hit_chance(b.units["thoma"], b.units["minotaur"], MINE)
    assert ("환경 폐광 거리", -MINE.range_penalty) in bd
    assert needed == 전열 - MINE.range_penalty


def test_행운은_굴림에만_소폭_걸린다():
    """기획서 §4.2 — LCK 20 과 1 의 차는 (20-1)×0.5 ≈ 9~10%."""
    hi = _battle(thoma={"luck": 20})
    lo = _battle(thoma={"luck": 1})
    a, _ = hit_chance(hi.units["thoma"], hi.units["minotaur"], MINE)
    c, _ = hit_chance(lo.units["thoma"], lo.units["minotaur"], MINE)
    assert 9 <= a - c <= 10


def test_명중은_5와_95_사이로_잘린다():
    # 마르탱은 장창의 요구치를 다 넘어 효율 페널티가 없다 — 상한이 드러난다.
    b = _battle(martin={"agi": 20})
    b.units["minotaur"].stats = replace(b.units["minotaur"].stats, agi=1)
    needed, _ = hit_chance(b.units["martin"], b.units["minotaur"], MINE)  # 60 + 38 = 98 → 95
    assert needed == 95
    lo = _battle(thoma={"agi": 1})
    lo.units["minotaur"].stats = replace(lo.units["minotaur"].stats, agi=20)
    from apps.arena.domain.services.battle.state import Status

    lo.units["thoma"].statuses.append(Status("blind", 2, 15))
    # 60 - 38(민첩) - 15(연막) - 10(무기 효율) = -3 → 하한 5
    needed, _ = hit_chance(lo.units["thoma"], lo.units["minotaur"], MINE)
    assert needed == 5


def test_방어_태세는_피해를_절반으로():
    b = _battle()
    full, _ = damage(b.units["minotaur"], b.units["martin"], MINE, None, crit=False)
    b.units["martin"].defending = True
    half, bd = damage(b.units["minotaur"], b.units["martin"], MINE, None, crit=False)
    assert half == round(full * 0.5) or abs(half * 2 - full) <= 1
    assert ("방어 태세", 0.5) in bd


def test_환경은_더는_피해를_바꾸지_않는다():
    """기획서 v3 §0.2 — 피해 종류가 하나가 되면서 환경의 피해 배수도 사라졌다.

    환경은 이제 속도·스태미나·어둠·사거리로만 갈린다. 같은 타격이면
    늪지든 폐광이든 피해가 같다.
    """
    b = _battle(party=("martin", "aude", "thoma"))
    d_swamp, _ = damage(b.units["martin"], b.units["minotaur"], SWAMP, None, crit=False)
    d_mine, _ = damage(b.units["martin"], b.units["minotaur"], MINE, None, crit=False)
    assert d_swamp == d_mine


def test_치명타는_1_5배():
    b = _battle()
    n, _ = damage(b.units["martin"], b.units["minotaur"], MINE, None, crit=False)
    c, _ = damage(b.units["martin"], b.units["minotaur"], MINE, None, crit=True)
    assert abs(c - n * 1.5) <= 1


def test_늪지에서_중갑은_느려진다():
    b = _battle(env=SWAMP)
    v, bd = speed(b.units["martin"], SWAMP)
    assert ("환경 늪지", -2) in bd
    v2, _ = speed(b.units["martin"], MINE)
    assert v == v2 - 2


def test_행동_순서는_속도_내림차순이고_시드에_결정된다():
    b = _battle()
    o1 = [r[0] for r in turn_order(b, FixedDice([1]))]
    o2 = [r[0] for r in turn_order(b, FixedDice([1]))]
    assert o1 == o2
    assert o1[0] == "thoma"  # AGI 16


def test_도망_성공률은_적_최고_민첩과의_차다():
    b = _battle()
    needed, _ = flee_chance(b.units["thoma"], [b.units["minotaur"]])
    차 = b.units["thoma"].stats.agi - b.units["minotaur"].stats.agi
    assert needed == FLEE_BASE + 차 * FLEE_PER_AGI_DIFF

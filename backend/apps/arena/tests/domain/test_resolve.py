from dataclasses import replace

import pytest

from apps.arena.adapter.outbound.strategies.dice import FixedDice
from apps.arena.domain.entities.types import Action
from apps.arena.domain.services.battle.resolve import end_turn, resolve
from apps.arena.domain.services.battle.state import Battle, unit_from_character, unit_from_enemy
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.environments import MINE
from content.monsters import GNOLL_PACK, JUVENILE_MINOTAUR
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def _char(cid: str):
    c = ROSTER_BY_ID[cid]
    return replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))


def _battle(enemy=JUVENILE_MINOTAUR, party=("martin", "aude", "thoma"), positions=None):
    units = {}
    for cid in party:
        c = _char(cid)
        pos = (positions or {}).get(cid, "front")
        units[cid] = unit_from_character(c, choose_build(c), "party", pos)
    for e in enemy.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(seed=1, environment=MINE, units=units, enemy_def=enemy)


def test_명중_굴림이_성공하면_피해가_들어간다():
    b = _battle()
    hp0 = b.units["minotaur"].hp
    rec = resolve(b, "martin", Action("ATTACK", "minotaur"), FixedDice([1, 100]))  # 명중, 치명 아님
    assert rec.strikes[0].hit and not rec.strikes[0].crit
    assert b.units["minotaur"].hp == hp0 - rec.strikes[0].damage
    assert rec.stamina_cost > 0


def test_빗나가면_피해가_없다():
    b = _battle()
    hp0 = b.units["minotaur"].hp
    rec = resolve(b, "martin", Action("ATTACK", "minotaur"), FixedDice([100]))
    assert not rec.strikes[0].hit and b.units["minotaur"].hp == hp0


def test_치명타_굴림():
    b = _battle()
    rec = resolve(b, "martin", Action("ATTACK", "minotaur"), FixedDice([1, 1]))
    assert rec.strikes[0].crit and ("치명타", 1.5) in rec.strikes[0].damage_breakdown


def test_근접은_전열이_살아_있으면_후열을_못_노린다():
    b = _battle(enemy=GNOLL_PACK)
    rec = resolve(b, "martin", Action("ATTACK", "rotten_priest"), FixedDice([50, 100]))
    assert rec.target in tuple(u.id for u in GNOLL_PACK.units)
    assert rec.notes and "전열이 막음" in rec.notes[0]


def test_원거리는_후열을_노린다():
    # 놀은 둘 다 전열이다. 후열이 있는 고블린 무리(투석수)로 잰다.
    from content.monsters import GOBLIN_BAND

    b = _battle(enemy=GOBLIN_BAND)
    rec = resolve(b, "thoma", Action("ATTACK", "goblin_b"), FixedDice([50, 100]))
    assert rec.target == "goblin_b" and not rec.notes


def test_방어는_다음_피해를_절반으로_하고_스태미나를_돌려준다():
    b = _battle()
    g = b.units["martin"]
    g.stamina = 10
    resolve(b, "martin", Action("DEFEND"), FixedDice([1]))
    assert g.defending and g.stamina == 15
    rec = resolve(b, "minotaur", Action("ATTACK", "martin"), FixedDice([1, 100]))
    assert ("방어 태세", 0.5) in rec.strikes[0].damage_breakdown
    # 방어자가 다음 행동을 하면 태세가 풀린다
    resolve(b, "martin", Action("WAIT"), FixedDice([1]))
    assert not g.defending


def test_치유는_최대_HP_를_넘지_않는다():
    b = _battle()
    g = b.units["martin"]
    g.hp = g.hp_max - 5
    rec = resolve(b, "aude", Action("SKILL", target="martin", skill="치유"), FixedDice([1]))
    assert rec.healed == 5 and g.hp == g.hp_max


def test_스태미나_부족_스킬은_호출자_버그다():
    b = _battle()
    b.units["aude"].stamina = 1
    with pytest.raises(ValueError):
        resolve(b, "aude", Action("SKILL", target="martin", skill="치유"), FixedDice([1]))


def test_도망_성공은_전장에서_빠진다():
    b = _battle()
    rec = resolve(b, "thoma", Action("FLEE"), FixedDice([1]))
    assert rec.flee_success and b.units["thoma"].fled and not b.units["thoma"].active


def test_도망_실패는_턴만_잃는다():
    b = _battle()
    rec = resolve(b, "thoma", Action("FLEE"), FixedDice([100]))
    assert rec.flee_success is False and not b.units["thoma"].fled


def test_방패_밀치기는_방어_상태를_걸고_턴이_지나면_풀린다():
    b = _battle(party=("gilles", "aude", "thoma"))
    resolve(b, "gilles", Action("SKILL", skill="방패 밀치기"), FixedDice([1]))
    assert b.units["gilles"].status("guard") is not None
    end_turn(b)
    end_turn(b)
    assert b.units["gilles"].status("guard") is None


def test_턴_종료에_스태미나가_회복된다():
    b = _battle()
    k = b.units["thoma"]
    k.stamina = 0
    end_turn(b)
    assert k.stamina == round(3 + k.stats.con * 0.3)


def test_휩쓸기는_적_전원을_때린다():
    b = _battle(enemy=GNOLL_PACK, party=("martin", "aude", "thoma"))
    rec = resolve(b, "martin", Action("SKILL", skill="휩쓸기"), FixedDice([1, 100]))
    assert len(rec.strikes) == len(GNOLL_PACK.units)


def test_행동은_history_에_남는다():
    b = _battle()
    resolve(b, "martin", Action("ATTACK", "minotaur"), FixedDice([1, 100]))
    assert b.history[-1].actor == "martin" and b.history[-1].damage > 0


def test_효율_스펙트럼_페널티가_modifiers_에_이름으로_남는다():
    """마른 몸에 판금 — 트롤픽의 대가가 인스펙터에 보인다(기획서 §4.3)."""
    # 힘 8 인 사람에게 판금과 방패를 쥐여준다. 베른은 추천 배분으로 힘이 13 이라
    # 미달이 나지 않는다 — 트롤픽의 대가를 보려면 실제로 모자란 몸이어야 한다.
    c = replace(_char("aude"), char_class="warrior")
    c = replace(c, body=replace(c.body, height_cm=180, build="slim"))
    b = _battle()
    from apps.arena.domain.entities.types import BuildChoice
    from content.classes import ARMORS, WEAPONS

    build = BuildChoice(WEAPONS["방패와 검"], ARMORS["판금 갑옷"], (), "테스트")
    b.units["aude"] = unit_from_character(c, build, "party", "front")
    rec = resolve(b, "aude", Action("ATTACK", "minotaur"), FixedDice([100]))
    names = [n for n, _ in rec.modifiers]
    assert "무게 미달" in names and "힘 미달" in names

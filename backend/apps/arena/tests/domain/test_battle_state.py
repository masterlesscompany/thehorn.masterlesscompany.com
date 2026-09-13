from dataclasses import replace

from apps.arena.domain.entities.types import Action
from apps.arena.domain.services.battle.state import (
    Battle,
    available_actions,
    outcome,
    stamina_cost,
    unit_from_character,
    unit_from_enemy,
)
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.environments import MINE, SWAMP
from content.monsters import JUVENILE_MINOTAUR
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def _char(cid: str):
    c = ROSTER_BY_ID[cid]
    return replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))


def _battle(env=MINE, party=("martin", "gilles", "thoma")):
    units = {}
    for cid in party:
        c = _char(cid)
        units[cid] = unit_from_character(c, choose_build(c), "party", "front")
    for e in JUVENILE_MINOTAUR.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(seed=1, environment=env, units=units, enemy_def=JUVENILE_MINOTAUR)


def test_스태미나가_바닥이면_WAIT_만_남는다():
    b = _battle()
    b.units["martin"].stamina = 0
    assert [a.kind for a in available_actions(b, "martin")] == ["WAIT"]


def test_중갑은_늪지에서_스태미나를_더_쓴다():
    """기획서 §4.1 "무거운 갑옷 입으면 느리고 금방 지친다"."""
    b = _battle(env=SWAMP)
    g = b.units["martin"]  # 판금(무게 3)
    assert stamina_cost(g, Action("ATTACK", "minotaur"), SWAMP) > stamina_cost(
        g, Action("ATTACK", "minotaur"), MINE
    )
    k = b.units["thoma"]  # 가죽(무게 1)
    assert stamina_cost(k, Action("ATTACK", "minotaur"), SWAMP) == stamina_cost(
        k, Action("ATTACK", "minotaur"), MINE
    )


def test_적이_전멸하면_승리():
    b = _battle()
    b.units["minotaur"].alive = False
    assert outcome(b) == "win"


def test_후퇴_명령_없이_전원이_사라지면_패배_명령이_있으면_후퇴():
    b = _battle()
    for cid in ("martin", "gilles", "thoma"):
        b.units[cid].fled = True
    assert outcome(b) == "lose"
    b.retreat_ordered = True
    assert outcome(b) == "retreat"


def test_턴_상한은_턴_종료에서만_무승부다():
    """유닛 루프 안에서 함께 보면 30턴째 첫 행동 하나로 판이 잘린다(QA 라운드 1 P1-4)."""
    b = _battle()
    b.turn = 30
    assert outcome(b) is None
    assert outcome(b, end_of_turn=True) == "draw"


def test_치유_스킬은_자기와_아군을_대상으로_한다():
    b = _battle(party=("martin", "aude", "thoma"))
    targets = {a.target for a in available_actions(b, "aude") if a.skill == "치유"}
    assert targets == {"martin", "aude", "thoma"}


def test_유닛은_효율_스펙트럼을_들고_있다():
    b = _battle(party=("gilles", "aude", "thoma"))
    s = b.units["aude"]
    assert s.armor_mods.hit == 0  # 가죽 갑옷은 보통 몸에 맞는다

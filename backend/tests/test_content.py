from dataclasses import replace

from apps.arena.domain.constants.balance import FREE_POINTS
from apps.arena.domain.entities.types import Body, Disposition
from apps.arena.domain.services.rules.stats import allocate
from content.classes import CLASSES, SKILLS, choose_build
from content.environments import MINE, SWAMP
from content.monsters import JUVENILE_MINOTAUR
from content.roster import PRESET_ALLOCATIONS, PRESET_ROSTER, ROSTER_BY_ID


def test_프리셋_다섯은_id_가_유일하고_능력치는_전부_8이다():
    ids = [c.id for c in PRESET_ROSTER]
    assert len(ids) == 5 and len(set(ids)) == 5
    for c in PRESET_ROSTER:
        assert set(c.stats.as_dict().values()) == {8}


def test_프리셋_성향은_설계_표와_같다():
    assert ROSTER_BY_ID["agnes"].disposition == Disposition(-40, 10, 20, -50)
    assert ROSTER_BY_ID["thoma"].disposition == Disposition(20, 50, 0, 80)
    assert ROSTER_BY_ID["agnes"].life.dependents == 1
    assert ROSTER_BY_ID["aude"].disposition == Disposition(-20, 40, 80, 20)


def test_데모_성향_다섯이_모두_대응된다():
    """기획서 §7.4 — 희생형·가장형·수읽기형·보수 기준선·중갑 전사."""
    d = {c.id: c.disposition for c in PRESET_ROSTER}
    assert d["thoma"].sacrifice == 80  # 희생형
    assert d["agnes"].sacrifice == -50  # 가장형
    assert d["aude"].planning == 80  # 수읽기형
    assert d["gilles"].planning == 20 and d["gilles"].risk == 0  # 보수 기준선
    assert ROSTER_BY_ID["martin"].char_class == "warrior"  # 중갑


def test_추천_배분은_전원_18점이다():
    for cid, alloc in PRESET_ALLOCATIONS.items():
        assert sum(alloc.values()) == FREE_POINTS, cid
        allocate(ROSTER_BY_ID[cid].stats, alloc)  # 예외 없이 통과해야 한다


def test_클래스는_다섯이고_스킬은_둘씩이다():
    assert set(CLASSES) == {"defender", "warrior", "archer", "rogue", "bard"}
    for cls in CLASSES.values():
        assert len(cls.skills) == 2
        for k in cls.skills:
            assert k in SKILLS
    assert CLASSES["bard"].can_heal


def test_마법사와_성직자는_사라졌다():
    """클래스 개편(설계 2026-09-08) — 역할을 막는 쪽·때리는 쪽·살리는 쪽으로 갈랐다."""
    assert "mage" not in CLASSES and "cleric" not in CLASSES


def test_방패병은_때리지_않고_전사는_지키지_않는다():
    """방어/공격을 행동 금지가 아니라 수치로 가른다(기획서 §4.3)."""
    방패병 = [SKILLS[k] for k in CLASSES["defender"].skills]
    전사 = [SKILLS[k] for k in CLASSES["warrior"].skills]
    assert all(s.base == 0 for s in 방패병), "방패병 스킬이 피해를 낸다"
    assert all(s.effect in ("guard", "slow") for s in 방패병)
    assert all(s.effect == "damage" for s in 전사)
    assert all(s.base > 0 for s in 전사)


def test_방패병_무기는_전사_무기보다_약하다():
    from content.classes import WEAPONS

    가장_센_방패병 = max(WEAPONS[w].base_damage for w in CLASSES["defender"].weapons)
    가장_약한_전사 = min(WEAPONS[w].base_damage for w in CLASSES["warrior"].weapons)
    assert 가장_센_방패병 < 가장_약한_전사


def test_음유시인은_치유와_축복을_든다():
    """응원·사기는 bless 가 이미 "아군 전체 명중 상승" 이라 그대로 맞는다.

    이름을 바꾸지 않는 이유: boss.py 와 fake.py 가 "치유"·"축복" 문자열을
    하드코딩한다. 바꾸면 보스의 치유자 적응(E2)이 조용히 깨진다.
    """
    assert set(CLASSES["bard"].skills) == {"치유", "축복"}
    assert any(SKILLS[k].effect == "heal" for k in CLASSES["bard"].skills)
    assert any(SKILLS[k].effect == "bless" for k in CLASSES["bard"].skills)


def test_엔진이_아는_효과는_모두_누군가_쓴다():
    """효과를 지우면 resolve.py 의 분기가 조용히 죽는다."""
    쓰이는 = {SKILLS[k].effect for cls in CLASSES.values() for k in cls.skills}
    엔진_효과 = {"guard", "slow", "damage", "snipe", "double", "crit", "blind", "heal", "bless"}
    assert 엔진_효과 <= 쓰이는


def test_힘_센_방패병은_타워_실드를_든다():
    bern = ROSTER_BY_ID["gilles"]
    bern = replace(bern, stats=allocate(bern.stats, PRESET_ALLOCATIONS["gilles"]))
    b = choose_build(bern)
    assert b.weapon.name == "타워 실드" and b.armor.name == "판금 갑옷"


def test_키_큰_전사는_장창을_뻗는다():
    garret = ROSTER_BY_ID["martin"]
    garret = replace(garret, stats=allocate(garret.stats, PRESET_ALLOCATIONS["martin"]))
    assert choose_build(garret).weapon.name == "장창"


def test_키_작고_힘_센_전사는_워해머다():
    """기획서 §5 "키 작고 힘 센 전사 → 긴 창 비효율, 워해머"."""
    c = replace(
        ROSTER_BY_ID["martin"],
        body=Body(165, "normal", 66),
        stats=allocate(ROSTER_BY_ID["martin"].stats, {"str_": 8}),
    )
    assert choose_build(c).weapon.name == "워해머"


def test_마른_캐릭터를_전사로_키워도_막지_않는다():
    """트롤픽 허용(기획서 §4.1). 빌드가 나오고 이유가 붙는다."""
    c = replace(ROSTER_BY_ID["agnes"], char_class="warrior")
    b = choose_build(c)
    assert b.weapon and b.rationale


def test_환경_수치는_설계와_같다():
    assert SWAMP.speed_penalty_by_weight == {3: -2}
    assert SWAMP.stamina_multiplier == 1.5
    assert MINE.darkness and MINE.range_penalty == 10
    # 피해 배수 축은 사라졌다(기획서 v3 §0.2). 환경은 속도·스태미나·어둠·사거리로 갈린다.
    assert not hasattr(SWAMP, "damage_modifiers")


def test_보스는_유닛_하나와_소환_규칙이다():
    assert len(JUVENILE_MINOTAUR.units) == 1 and JUVENILE_MINOTAUR.units[0].is_boss
    assert JUVENILE_MINOTAUR.summon_every == 3 and JUVENILE_MINOTAUR.summon_max == 2


def test_출전은_1명부터_3명까지다():
    """기획서 §7.2 — A·B 단계 출전 1~3. 혼자 가는 것도 단주의 선택이다."""
    from content.missions import MISSIONS_A, MISSIONS_B

    for m in (*MISSIONS_A, *MISSIONS_B):
        assert (m.lineup_min, m.lineup_max) == (1, 3), m.name


def test_도적_무기는_행운이_아니라_민첩이_고른다():
    """기획서 §4.2 — 행운은 판단에 개입하지 않는다. 투척/단검은 사거리를 바꾼다."""
    from dataclasses import replace

    base = ROSTER_BY_ID["agnes"]
    빠름 = replace(base, stats=replace(base.stats, agi=14, luck=1))
    느림 = replace(base, stats=replace(base.stats, agi=8, luck=20))
    assert choose_build(빠름).weapon.ranged is True
    assert choose_build(느림).weapon.ranged is False

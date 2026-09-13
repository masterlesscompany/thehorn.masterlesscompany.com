from dataclasses import replace

import pytest

from apps.arena.adapter.outbound.strategies.dice import FixedDice
from apps.arena.domain.entities.types import Plan
from apps.arena.domain.services.battle.state import Battle, unit_from_character, unit_from_enemy
from apps.arena.domain.services.judgment.compliance import deviation_probability, judge_compliance
from apps.arena.domain.services.judgment.odds import odds
from apps.arena.domain.services.judgment.replan import (
    ReplanState,
    mark_quiet_turn,
    mark_replanned,
    replan_triggers,
)
from apps.arena.domain.services.judgment.visibility import visible_context, wis_tier
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


def _battle(env=SWAMP, party=("martin", "aude", "thoma"), **overrides):
    units = {}
    for cid in party:
        c = _char(cid, **overrides.get(cid, {}))
        units[cid] = unit_from_character(c, choose_build(c), "party", "front")
    for e in JUVENILE_MINOTAUR.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(seed=1, environment=env, units=units, enemy_def=JUVENILE_MINOTAUR)


PLAN = Plan("평가", True, "rush", {}, "minotaur", {}, 0.30, "이유")


# ─── 지혜 마스킹 ──────────────────────────────────────────────────────


def test_지혜_단계는_설계_표와_같다():
    assert [wis_tier(w, SWAMP) for w in (7, 8, 12, 13, 16, 17, 20)] == [0, 1, 1, 2, 2, 3, 3]


def test_어둠은_한_단계_내린다():
    assert wis_tier(13, MINE) == 1 and wis_tier(5, MINE) == 0


def test_지혜가_낮으면_아군_상태가_가려진다():
    b = _battle(thoma={"wis": 5})
    visible, masked, tier = visible_context(b, "thoma", PLAN, 0.6)
    assert tier == 0
    assert "allies" not in visible and "allies" in masked
    assert "enemy_pattern" in masked and "plan_intent" in masked and "odds" in masked
    assert visible["self"]["hp"] and visible["enemies_basic"][0]["id"] == "minotaur"
    assert "hp" not in visible["enemies_basic"][0]


def test_지혜가_높으면_전부_보인다():
    b = _battle(gilles={"wis": 18}, party=("martin", "aude", "gilles"))
    visible, masked, tier = visible_context(b, "gilles", PLAN, 0.6)
    assert tier == 3 and masked == []
    assert visible["plan_intent"]["strategy"] == "rush" and visible["odds"] == 0.6
    assert {a["id"] for a in visible["allies"]} == {"martin", "aude"}


def test_같은_상황_두_캐릭터의_입력이_다르다():
    """기획서 §15 "지혜 높으면 뭐가 달라져요" — 입력 컨텍스트 비교."""
    b = _battle(garret={"wis": 5}, elaine={"wis": 15})
    _, m1, _ = visible_context(b, "martin", PLAN, 0.5)
    _, m2, _ = visible_context(b, "aude", PLAN, 0.5)
    assert len(m1) > len(m2)


# ─── 승산 ─────────────────────────────────────────────────────────────


def test_승산은_범위_안이고_대칭이다():
    b = _battle()
    a, _ = odds(b, "party")
    e, _ = odds(b, "enemy")
    assert 0.05 <= a <= 0.95 and abs(a + e - 1) < 0.01


def test_전력이_없는_진영의_승산은_바닥이다():
    b = _battle()
    for cid in ("martin", "aude", "thoma"):
        b.units[cid].alive = False
    v, _ = odds(b, "party")
    assert v == 0.05


def test_힐러가_있으면_시너지가_붙는다():
    with_healer = _battle(party=("martin", "aude", "thoma"))
    without = _battle(party=("martin", "gilles", "thoma"))
    _, bd1 = odds(with_healer, "party")
    _, bd2 = odds(without, "party")
    assert bd1["mine"]["synergy"] == 1.15 and bd2["mine"]["synergy"] == 1.0


def test_HP_가_줄면_승산이_내려간다():
    b = _battle()
    full, _ = odds(b, "party")
    b.units["martin"].hp = 10
    hurt, _ = odds(b, "party")
    assert hurt < full


# ─── 순응 ─────────────────────────────────────────────────────────────


def test_HP_가_낮을수록_이탈_확률이_오른다():
    b = _battle()
    k = b.units["thoma"]
    ps = []
    for hp in (k.hp_max, k.hp_max // 2, k.hp_max // 5):
        k.hp = hp
        ps.append(deviation_probability(k, b)[0])
    assert ps[0] < ps[1] < ps[2]


def test_희생_수용도가_높을수록_이탈_확률이_내린다():
    b = _battle()
    # 토마는 희생 +80, 마르탱은 +10. 같은 HP 면 토마가 덜 이탈한다.
    희생형, 보통 = b.units["thoma"], b.units["martin"]
    희생형.hp = 보통.hp = 20
    assert deviation_probability(희생형, b)[0] < deviation_probability(보통, b)[0]


def test_가장형은_같은_HP_에서_이탈_압력이_높다():
    """아녜스: 두 살 딸(기획서 §9 예시). 생애 가중이 압력에 이름으로 남는다.

    희생 수용도가 그 항을 늘이고 줄인다 — 아녜스는 -50 이라 기본값보다 크다.
    """
    b = _battle(party=("agnes", "martin", "thoma"))
    _, bd = deviation_probability(b.units["agnes"], b)
    assert bd["pressure_breakdown"]["life"] > 0.2
    _, bd2 = deviation_probability(b.units["martin"], b)
    assert bd2["pressure_breakdown"]["life"] == 0.0


def test_성향_축은_서로_다른_항을_흔든다():
    """QA 라운드 2 — 세 축의 계수가 같으면 E3 가 같은 실험을 세 번 그린다."""
    from dataclasses import replace as _replace

    b = _battle()
    u = b.units["martin"]
    u.hp = u.hp_max // 2
    기준, _ = deviation_probability(u, b)

    u.disposition = _replace(u.disposition, risk=80)
    위험높음, bd = deviation_probability(u, b)
    assert bd["pressure_breakdown"]["hp"] < 0.25, "위험 감수형은 자기 상처를 작게 느낀다"

    u.disposition = _replace(b.units["martin"].disposition, risk=20, sacrifice=80)
    희생높음, bd2 = deviation_probability(u, b)
    # 아군 손실도 부양가족도 없는 상황이라 희생 축은 HP 항을 건드리지 않는다.
    assert bd2["pressure_breakdown"]["hp"] == pytest.approx(
        deviation_probability(b.units["martin"], b)[1]["pressure_breakdown"]["hp"]
    )
    assert 위험높음 != 희생높음 != 기준


def test_기획서_9장_시나리오():
    """HP 32%, 응급 담당 사망, 딸 둘 → 이탈 확률이 높다(기획서 §9 예시).

    가장형은 아녜스다 — 두 살 딸이 집에 있다.
    """
    b = _battle(party=("martin", "aude", "agnes"))
    k = b.units["agnes"]
    k.hp = round(k.hp_max * 0.32)
    b.units["aude"].alive = False
    p, _ = deviation_probability(k, b)
    assert 0.6 <= p <= 0.9


def test_판정은_시드_주사위로_결정된다():
    b = _battle()
    k = b.units["thoma"]
    k.hp = 5
    rec = judge_compliance(k, b, FixedDice([1], uniforms=[0.01]))
    assert rec.verdict == "deviate" and rec.roll == 0.01
    rec2 = judge_compliance(k, b, FixedDice([1], uniforms=[0.99]))
    assert rec2.verdict == "comply"


def test_적_유닛은_항상_순응한다():
    b = _battle()
    assert (
        judge_compliance(b.units["minotaur"], b, FixedDice([1], uniforms=[0.0])).verdict == "comply"
    )


# ─── 재계획 ───────────────────────────────────────────────────────────


def test_이탈은_재계획을_부른다():
    s = ReplanState()
    s.deviations.append("thoma")
    ts = replan_triggers(s, 0.6, PLAN)
    assert [t.kind for t in ts] == ["deviation"]


def test_승산_붕괴는_첫_진입과_계단마다_한_번씩():
    s = ReplanState()
    assert [t.kind for t in replan_triggers(s, 0.28, PLAN)] == ["odds_collapse"]
    mark_replanned(s, 0.28, PLAN)
    s.begin_turn()
    s.consume_signals()
    assert replan_triggers(s, 0.25, PLAN) == []  # 같은 계단(0.2)
    s.begin_turn()
    s.consume_signals()
    assert [t.kind for t in replan_triggers(s, 0.19, PLAN)] == ["odds_collapse"]  # 0.1 계단


def test_한_턴에_재계획은_한_번이다():
    s = ReplanState()
    mark_replanned(s, 0.6, PLAN)
    s.deviations.append("thoma")
    assert replan_triggers(s, 0.6, PLAN) == []


def test_감독_OFF_면_트리거가_없다():
    s = ReplanState()
    s.deviations.append("thoma")
    assert replan_triggers(s, 0.1, None) == []


def test_연속_재계획_상한을_넘으면_강제_결정():
    s = ReplanState()
    forced = [mark_replanned(s, 0.6, PLAN) for _ in range(4)]
    assert forced == [False, False, False, True]
    mark_quiet_turn(s)
    assert s.consecutive == 0

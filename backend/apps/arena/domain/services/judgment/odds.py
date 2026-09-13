"""승산 휴리스틱 — 계산은 코드, 판단은 모델 (기획서 §8.3, 설계 §6.2).

"누가 먼저 쓰러지는가" 로 잰다. 양쪽의 한 턴 기대 피해와 남은 HP 로 서로를
눕히는 데 걸리는 턴 수를 구하고, 그 비로 승산을 낸다.

예전에는 HP **비율**과 기대 피해만 곱했다. 그래서 HP 148 인 보스와 HP 60 인
수하가 만피면 같은 무게로 셌고, 전사 파티가 "승산 0.66" 이라는 말을 들으며
지는 판이 실측으로 나왔다(30시드).

행운을 읽지 않는다(hit_chance 에 include_luck=False). 행운이 승산에 들어가면
"그냥 랜덤 아니에요?"의 근거가 되고 성향 실험을 오염시킨다(기획서 §4.2).
"""

from typing import Any

from apps.arena.domain.constants.balance import HEAL_SYNERGY, ODDS_MAX, ODDS_MIN
from apps.arena.domain.entities.types import Environment
from apps.arena.domain.services.battle.state import Battle, UnitState, living
from apps.arena.domain.services.judgment.compliance import deviation_probability
from apps.arena.domain.services.rules.combat import damage, hit_chance


def unit_damage(
    u: UnitState, foes: list[UnitState], env: Environment, battle: Battle | None = None
) -> tuple[float, dict[str, Any]]:
    """한 턴 기대 피해. 적 전체에 대한 평균으로 잡는다 — 누구를 칠지는 작전이 정한다."""
    if not foes:
        return 0.0, {"reason": "적 없음"}
    exp = 0.0
    for f in foes:
        needed, _ = hit_chance(u, f, env, None, include_luck=False)
        dmg, _ = damage(u, f, env, None, crit=False)
        exp += dmg * needed / 100
    exp /= len(foes)

    # 스태미나가 바닥이면 행동을 못 한다. 그래도 0 은 아니다 — 회복이 있다.
    stamina = max(0.3, u.stamina / u.stamina_max)

    # 순응 기댓값. 방침을 자주 이탈하는 단원은 그만큼 덜 싸운다 — 이탈하면
    # 도망치거나 몸을 지키지, 적을 치지 않는다. 결정론적 수치이고 행운을 읽지
    # 않는다(기획서 §4.2·§5.1).
    comply = 1.0
    if battle is not None and u.disposition is not None:
        comply = 1 - deviation_probability(u, battle)[0]

    dps = exp * stamina * comply
    return dps, {
        "hp": u.hp,
        "expected_damage": round(exp, 1),
        "stamina": round(stamina, 2),
        "compliance": round(comply, 2),
        "dps": round(dps, 1),
    }


def faction_power(battle: Battle, faction: str) -> tuple[float, float, dict[str, Any]]:
    """(한 턴 기대 피해 합, 남은 HP 합, 내역)."""
    mine = living(battle, faction)
    other = battle.enemy if faction == battle.party else battle.party
    foes = living(battle, other)
    dps = 0.0
    hp = 0.0
    per_unit: dict[str, Any] = {}
    for u in mine:
        d, bd = unit_damage(u, foes, battle.environment, battle)
        dps += d
        hp += u.hp
        per_unit[u.id] = bd
    synergy = 1.0
    if any(s.effect == "heal" for u in mine for s in u.skills):
        # 치유는 실질 HP 를 늘린다. 피해가 아니라 버티는 시간에 붙인다.
        synergy = HEAL_SYNERGY
        hp *= synergy
    return (
        dps,
        hp,
        {
            "units": per_unit,
            "synergy": synergy,
            "dps": round(dps, 1),
            "effective_hp": round(hp),
        },
    )


def odds(battle: Battle, faction: str) -> tuple[float, dict[str, Any]]:
    """faction 의 승산 0.05..0.95. 서로를 눕히는 데 걸리는 턴 수의 비."""
    other = battle.enemy if faction == battle.party else battle.party
    # 한쪽이 비어 있으면 승부가 이미 났다.
    if not living(battle, faction):
        return ODDS_MIN, {"reason": "생존 유닛 없음"}
    if not living(battle, other):
        return ODDS_MAX, {"reason": "적 생존 유닛 없음"}

    my_dps, my_hp, bd_mine = faction_power(battle, faction)
    their_dps, their_hp, bd_theirs = faction_power(battle, other)

    # 우리가 버티는 턴 수 vs 적이 버티는 턴 수. 피해가 0 이면 영원히 안 죽는다 —
    # 무한 대신 큰 수를 써서 나눗셈이 터지지 않게 한다.
    big = 999.0
    my_turns = big if their_dps <= 0 else my_hp / their_dps
    their_turns = big if my_dps <= 0 else their_hp / my_dps

    value = my_turns / (my_turns + their_turns)
    value = max(ODDS_MIN, min(ODDS_MAX, value))
    bd_mine["survives_turns"] = round(my_turns, 1)
    bd_theirs["survives_turns"] = round(their_turns, 1)
    return round(value, 3), {"mine": bd_mine, "theirs": bd_theirs}

"""전투 판 세우기 — 배치 · 유닛 생성 · 소환 · 전령관 확인.

러너에서 갈라 나왔다(QA 2026-09-09 C6). "누가 어디에 서는가" 는 판을 굴리는
일과 다른 관심사다 — 러너는 판을 굴리고, 여기는 판을 세운다.
"""

from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import MissionSpec, PartyMember
from apps.arena.domain.services.battle.state import (
    Battle,
    unit_from_character,
    unit_from_enemy,
)


def default_positions(members: list[PartyMember]) -> dict[str, str]:
    """감독 OFF 의 고정 편성(설계 §6.1): AGI 최고 1명 후열, 나머지 전열.

    혼자 나가면 뒤에 설 수 없다 — 앞을 막아 줄 사람이 없다.
    """
    if not members:
        return {}
    if len(members) == 1:
        return {members[0][0].id: "front"}
    fastest = max(members, key=lambda m: m[0].stats.agi)[0].id
    return {m[0].id: ("back" if m[0].id == fastest else "front") for m in members}


def setup_battle(
    mission: MissionSpec,
    members: list[PartyMember],
    seed: int,
    adaptation_on: bool,
    boss_title: str | None = None,
) -> Battle:
    positions = default_positions(members)
    units = {}
    for c, build, voice in members:
        units[c.id] = unit_from_character(c, build, "party", positions[c.id], voice=voice)  # type: ignore[arg-type]
    for e in mission.enemy.units:
        unit = unit_from_enemy(e, "enemy")
        if boss_title and unit.is_boss:
            # 이름 없는 것이 이름을 얻는다. 유저마다 다르다.
            unit.name = boss_title
        units[e.id] = unit
    return Battle(
        seed=seed,
        environment=mission.environment,
        units=units,
        adaptation_on=adaptation_on and mission.adaptation_on,
        enemy_def=mission.enemy,
        summon_every=mission.enemy.summon_every,
        mission_no=mission.no,
    )


def maybe_summon(battle: Battle, tracer: Tracer) -> None:
    e = battle.enemy_def
    if e is None or not battle.summon_every or e.summon_template is None:
        return
    if battle.summoned >= e.summon_max or battle.turn % battle.summon_every != 0:
        return
    boss_alive = any(u.is_boss and u.active for u in battle.units.values())
    if not boss_alive:
        return
    battle.summoned += 1
    unit = unit_from_enemy(e.summon_template, "enemy", suffix=f"_{battle.summoned}")
    battle.units[unit.id] = unit
    tracer.emit(
        "summon", {"unit": unit.id, "name": unit.name, "count": battle.summoned}, actor=unit.id
    )


# 뿔피리를 부는 병과(기획서 v3 §8.2 — "뿔피리는 **전령관**이 분다").
HERALD_CLASS = "bard"


def herald_present(battle: Battle) -> bool:
    """전령관이 아직 서 있는가(기획서 v3 §8.2).

    **무기가 아니라 병과로 본다.** 나팔(`is_horn`)로 판정했더니, 전령관에게
    힘을 12 이상 찍으면 `choose_build` 가 「단검과 붕대」를 쥐여 주어 **육성이
    병과 능력을 빼앗았다** — 화면은 "전령관 있음" 이라 말하고 엔진은 아니라고
    했다(QA 재검 2026-09-09 P1-E). 기획서가 말하는 것은 역할이지 물건이 아니다.
    """
    return any(
        u.faction == battle.party and u.active and u.char_class == HERALD_CLASS
        for u in battle.units.values()
    )

"""지혜 → 정보 해상도 (기획서 §4.2, 설계 §4.6).

지능은 수치를 올리고, 지혜는 볼 수 있는 것을 늘린다. 구현은 프롬프트 조립 시
필드 마스킹이라 비용이 거의 없다. 인스펙터가 "본 것 / 못 본 것"을 나란히
보여줄 수 있도록 masked 필드 이름을 함께 돌려준다.
"""

from typing import Any

from apps.arena.domain.constants.balance import ADAPT_WINDOW, DARKNESS_TIER_PENALTY, WIS_TIERS
from apps.arena.domain.entities.types import Environment, Plan
from apps.arena.domain.services.battle.state import Battle, UnitState, allies_of, enemies_of

# 단계별로 열리는 필드. 0단계 필드는 항상 보인다.
TIER_FIELDS: dict[int, tuple[str, ...]] = {
    0: ("self", "enemies_basic"),
    1: ("allies",),
    2: ("enemy_pattern",),
    3: ("plan_intent", "odds"),
}
ALL_FIELDS: tuple[str, ...] = tuple(f for t in sorted(TIER_FIELDS) for f in TIER_FIELDS[t])


def wis_tier(wis: int, env: Environment) -> int:
    tier = 0
    for lo, hi, t in WIS_TIERS:
        if lo <= wis <= hi:
            tier = t
            break
    if env.darkness:
        tier = max(0, tier - DARKNESS_TIER_PENALTY)
    return tier


def _unit_view(u: UnitState, full: bool) -> dict[str, Any]:
    v: dict[str, Any] = {"id": u.id, "name": u.name, "position": u.position, "alive": u.alive}
    if full:
        v.update(
            hp=u.hp,
            hp_max=u.hp_max,
            hp_pct=round(100 * u.hp / u.hp_max),
            stamina=u.stamina,
            statuses=[s.name for s in u.statuses],
            defending=u.defending,
        )
    return v


def _enemy_pattern(battle: Battle, foes: list[UnitState]) -> dict[str, Any]:
    recent = [h for h in battle.history if h.turn > battle.turn - ADAPT_WINDOW]
    out: dict[str, Any] = {}
    for f in foes:
        acts = [h for h in recent if h.actor == f.id]
        out[f.id] = {
            "recent_actions": [f"{h.action}→{h.target}" for h in acts],
            "hp_estimate": _hp_bucket(f),
        }
    return out


def _hp_bucket(u: UnitState) -> str:
    pct = u.hp / u.hp_max
    if pct > 0.7:
        return "건재"
    if pct > 0.3:
        return "상처"
    return "빈사"


def visible_context(
    battle: Battle, actor_id: str, plan: Plan | None, odds_value: float | None
) -> tuple[dict[str, Any], list[str], int]:
    """(보이는 것, 가려진 필드 이름, 단계)."""
    me = battle.units[actor_id]
    tier = wis_tier(me.stats.wis, battle.environment)
    open_fields = {f for t, fs in TIER_FIELDS.items() if t <= tier for f in fs}

    foes = enemies_of(battle, actor_id)
    visible: dict[str, Any] = {
        "self": _unit_view(me, full=True),
        "enemies_basic": [_unit_view(f, full=False) for f in foes],
    }
    if "allies" in open_fields:
        visible["allies"] = [_unit_view(a, full=True) for a in allies_of(battle, actor_id)]
    if "enemy_pattern" in open_fields:
        visible["enemy_pattern"] = _enemy_pattern(battle, foes)
    if "plan_intent" in open_fields and plan is not None:
        visible["plan_intent"] = {
            "assessment": plan.assessment,
            "strategy": plan.strategy,
            "rationale": plan.rationale,
        }
    if "odds" in open_fields and odds_value is not None:
        visible["odds"] = round(odds_value, 2)

    masked = [f for f in ALL_FIELDS if f not in open_fields]
    return visible, masked, tier

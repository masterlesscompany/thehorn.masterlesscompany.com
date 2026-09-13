"""단장 — 전략 층 (기획서 §8, 설계 §6.1).

전투 시작과 재계획 때만 부른다. 편성·작전·후퇴 판단. "어떻게 이기는가" 이전에
"싸울 가치가 있는가". 승산 계산은 코드(odds), 판단은 모델.
"""

from typing import Any

from apps.arena.app.use_cases.agents.prompts import build_orchestrator_prompt
from apps.arena.app.use_cases.agents.schemas import ORCHESTRATOR_SCHEMA
from apps.arena.domain.constants.balance import RETREAT_THRESHOLD_DEFAULT, RETREAT_THRESHOLD_RANGE
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Plan
from apps.arena.domain.ports.ports import DecisionModel
from apps.arena.domain.services.battle.state import Battle, living
from apps.arena.domain.services.judgment.odds import odds


def plan_from(data: dict[str, Any], battle: Battle, faction: str) -> tuple[Plan, list[str]]:
    """모델 응답을 Plan 으로. 모르는 id·잘못된 위치는 버리고 그 사실을 남긴다."""
    notes: list[str] = []
    mine = {u.id for u in living(battle, faction)}
    other = battle.enemy if faction == battle.party else battle.party
    foes = {u.id for u in living(battle, other)}

    formation: dict[str, str] = {}
    for uid, pos in (data.get("formation") or {}).items():
        if uid not in mine:
            notes.append(f"편성에 모르는 유닛 {uid}")
            continue
        if pos not in ("front", "back"):
            notes.append(f"{uid} 위치 {pos} 는 front|back 이 아니다")
            continue
        formation[uid] = pos

    focus = data.get("focus_target")
    if focus is not None and focus not in foes:
        notes.append(f"집중 목표 {focus} 는 살아 있는 적이 아니다")
        focus = None

    lo, hi = RETREAT_THRESHOLD_RANGE
    threshold = data.get("retreat_threshold", RETREAT_THRESHOLD_DEFAULT)
    threshold = max(lo, min(hi, float(threshold)))

    strategy = data["strategy"]
    worth = bool(data["worth_fighting"])
    if not worth and strategy != "retreat":
        notes.append("싸울 가치가 없다면서 후퇴가 아닌 전략 — 후퇴로 고정")
        strategy = "retreat"

    directive = {k: str(v) for k, v in (data.get("per_unit_directive") or {}).items() if k in mine}
    plan = Plan(
        assessment=str(data.get("assessment", "")),
        worth_fighting=worth,
        strategy=strategy,
        formation=formation,  # type: ignore[arg-type]
        focus_target=focus,
        per_unit_directive=directive,
        retreat_threshold=round(threshold, 2),
        rationale=str(data.get("rationale", "")),
    )
    return plan, notes


def make_plan(
    battle: Battle,
    faction: str,
    model: DecisionModel,
    tracer: Tracer,
    reason: str,
    forced: bool = False,
) -> Plan:
    odds_value, odds_bd = odds(battle, faction)
    previous = battle.plans.get(faction)
    prompt = build_orchestrator_prompt(
        battle, faction, odds_value, reason, forced, previous, battle.last_plan_odds
    )
    battle.last_plan_odds = odds_value
    data = model.decide("orchestrator", prompt, ORCHESTRATOR_SCHEMA)
    plan, notes = plan_from(data, battle, faction)
    battle.plans[faction] = plan

    # 편성은 작전 지시다 — 즉시 반영된다. 이동 비용은 전투 중 MOVE 에만 있다.
    for uid, pos in plan.formation.items():
        battle.units[uid].position = pos  # type: ignore[assignment]

    tracer.emit(
        "plan",
        {
            "faction": faction,
            "reason": reason,
            "forced": forced,
            "odds": odds_value,
            "odds_breakdown": odds_bd,
            "plan": plan,
            "notes": notes,
            "model": data.get("_meta", {}),
            "timing": data.get("_timing", {}),
            "prompt": prompt,
            "raw": {k: v for k, v in data.items() if not k.startswith("_")},
        },
    )
    return plan

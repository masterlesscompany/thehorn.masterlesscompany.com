"""단원 — 전술 층 (기획서 §8.3, 설계 §6.4). 매 턴, 방침 이탈 가능.

순서가 곧 규칙이다:
1. 지혜 마스킹으로 보이는 것을 정한다 (context)
2. 코드가 순응 판정을 한다 (compliance) — 모델은 뒤집을 수 없다
3. 모델이 그 판정 안에서 행동을 고른다 (decision)
"""

from dataclasses import dataclass
from typing import Any

from apps.arena.app.use_cases.agents.prompts import build_character_prompt
from apps.arena.app.use_cases.agents.schemas import CHARACTER_SCHEMA
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Action, Plan
from apps.arena.domain.ports.ports import DecisionModel, Dice
from apps.arena.domain.services.battle.state import Battle, available_actions, display_names
from apps.arena.domain.services.judgment.compliance import ComplianceRecord, judge_compliance
from apps.arena.domain.services.judgment.visibility import visible_context


@dataclass(frozen=True)
class CharacterDecision:
    action: Action
    compliance: ComplianceRecord
    follows_plan: bool
    reason: str


def action_from(data: dict[str, Any], actions: list[Action]) -> tuple[Action, str | None]:
    """모델이 고른 행동을 가능한 목록에 맞춘다. 목록 밖이면 가장 가까운 것 + 기록."""
    kind = data.get("action")
    target = data.get("target")
    skill = data.get("skill")
    position = data.get("position")
    for a in actions:
        if a.kind == kind and a.target == target and a.skill == skill and a.position == position:
            return a, None
    # 같은 종류에서 대상만 다른 것
    same_kind = [a for a in actions if a.kind == kind and (kind != "SKILL" or a.skill == skill)]
    if same_kind:
        a = same_kind[0]
        return a, f"{kind}→{target or skill or position} 은 불가능 → {a.label()}→{a.target} 로 변경"
    return Action("WAIT"), f"{kind} 은 지금 할 수 없다 → WAIT"


def _without_plan_actions(actions: list[Action], plan: Plan | None, unit_id: str) -> list[Action]:
    """방침이 가리키는 행동을 뺀다. 전부 빠지면(달리 할 게 없으면) 그대로 둔다."""
    if plan is None:
        return actions
    focus = plan.focus_target
    left = [
        a for a in actions if not (focus and a.target == focus and a.kind in ("ATTACK", "SKILL"))
    ]
    return left or actions


def character_act(
    battle: Battle,
    unit_id: str,
    plan: Plan | None,
    model: DecisionModel,
    dice: Dice,
    tracer: Tracer,
    odds_value: float | None,
) -> CharacterDecision:
    unit = battle.units[unit_id]

    visible, masked, tier = visible_context(battle, unit_id, plan, odds_value)
    tracer.emit(
        "context",
        {"wis": unit.stats.wis, "wis_tier": tier, "visible": visible, "masked": masked},
        actor=unit_id,
    )

    comp = judge_compliance(unit, battle, dice)
    tracer.emit("compliance", comp.as_payload(), actor=unit_id)

    actions = available_actions(battle, unit_id)

    # 후퇴 명령은 선택지가 아니다(설계 §5.3). 예전에는 모델에게 물었고, 방침이
    # "후퇴" 인데 계속 싸우는 응답이 오면 트레이스에 abandon 만 남고 판은 이어졌다 —
    # 인스펙터가 거짓말을 했다. 모델을 부르지 않으므로 호출도 아낀다.
    if battle.retreat_ordered:
        flee = next((a for a in actions if a.kind == "FLEE"), None) or Action("WAIT")
        tracer.emit(
            "decision",
            {
                "action": flee,
                "label": flee.label(),
                "target": None,
                "follows_plan": True,
                "verdict": "retreat",
                "reason": "단장의 후퇴 명령이다. 물러난다.",
                "note": None if flee.kind == "FLEE" else "도망칠 힘이 없다",
                "model": {"model": "order", "fallback": False, "attempts": 0},
                "timing": {},
            },
            actor=unit_id,
        )
        return CharacterDecision(flee, comp, True, "단장의 후퇴 명령이다. 물러난다.")

    if comp.verdict == "deviate":
        # 이탈은 라벨이 아니라 선택지의 변화다(설계 §6.4). 방침이 시키는 행동을
        # 목록에서 빼야 "이탈했는데 방침대로 쳤다" 는 기록이 나오지 않는다.
        actions = _without_plan_actions(actions, plan, unit_id)

    prompt = build_character_prompt(
        unit, visible, masked, plan, actions, comp.verdict, display_names(battle)
    )
    data = model.decide("character", prompt, CHARACTER_SCHEMA)
    action, note = action_from(data, actions)

    # 모델이 "따랐다"고 해도 판정이 이탈이면 이탈이다 — 결정론적 확률의 의미.
    follows = bool(data.get("follows_plan")) and comp.verdict == "comply" and plan is not None
    reason = str(data.get("reason", ""))
    tracer.emit(
        "decision",
        {
            "action": action,
            "label": action.label(),
            "target": action.target,
            "follows_plan": follows,
            "verdict": comp.verdict,
            "reason": reason,
            "note": note,
            "model": data.get("_meta", {}),
            "timing": data.get("_timing", {}),
            "prompt": prompt,
            "raw": {k: v for k, v in data.items() if not k.startswith("_")},
        },
        actor=unit_id,
    )
    return CharacterDecision(action, comp, follows, reason)

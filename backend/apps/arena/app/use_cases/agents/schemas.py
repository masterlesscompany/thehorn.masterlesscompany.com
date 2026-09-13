"""모델 응답 JSON 스키마 (설계 §6.1·§6.4·§5.6). core 가 소유한다.

검증기(adapters/harness/validate.py)는 여기 쓰인 부분집합(type·enum·required·
properties·minimum·maximum·items)만 안다. 그 밖의 키워드를 쓰면 검증되지 않는다.
"""

from apps.arena.domain.constants.balance import RETREAT_THRESHOLD_RANGE
from apps.arena.domain.ports.ports import JsonSchema

ACTION_KINDS = ["ATTACK", "DEFEND", "SKILL", "MOVE", "FLEE", "WAIT"]
STRATEGIES = ["rush", "attrition", "defensive", "retreat"]
POSITIONS = ["front", "back"]
ADAPTATIONS = ["focus", "breach", "target_healer", "summon_faster"]

ORCHESTRATOR_SCHEMA: JsonSchema = {
    "type": "object",
    "required": [
        "assessment",
        "worth_fighting",
        "strategy",
        "formation",
        "focus_target",
        "per_unit_directive",
        "retreat_threshold",
        "rationale",
    ],
    "properties": {
        "assessment": {"type": "string"},
        "worth_fighting": {"type": "boolean"},
        "strategy": {"type": "string", "enum": STRATEGIES},
        "formation": {"type": "object"},
        "focus_target": {"type": ["string", "null"]},
        "per_unit_directive": {"type": "object"},
        "retreat_threshold": {
            "type": "number",
            "minimum": RETREAT_THRESHOLD_RANGE[0],
            "maximum": RETREAT_THRESHOLD_RANGE[1],
        },
        "rationale": {"type": "string"},
    },
}

CHARACTER_SCHEMA: JsonSchema = {
    "type": "object",
    "required": ["action", "follows_plan", "reason"],
    "properties": {
        "action": {"type": "string", "enum": ACTION_KINDS},
        "target": {"type": ["string", "null"]},
        "skill": {"type": ["string", "null"]},
        "position": {"type": ["string", "null"], "enum": [*POSITIONS, None]},
        "follows_plan": {"type": "boolean"},
        "reason": {"type": "string"},
    },
}

BOSS_SCHEMA: JsonSchema = {
    "type": "object",
    "required": ["action", "reason"],
    "properties": {
        "action": {"type": "string", "enum": ACTION_KINDS},
        "target": {"type": ["string", "null"]},
        "skill": {"type": ["string", "null"]},
        "adapt": {"type": ["string", "null"], "enum": [*ADAPTATIONS, None]},
        "reason": {"type": "string"},
    },
}

NARRATION_SCHEMA: JsonSchema = {
    "type": "object",
    "required": ["narration"],
    "properties": {"narration": {"type": "string"}},
}

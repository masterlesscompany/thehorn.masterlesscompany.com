"""육성 턴 — 유저는 카테고리를 지시하고, 캐릭터가 따를지 정한다 (기획서 §5.1).

거부하면 모델이 대체 행동의 서사 한 줄을 쓰고, 결과는 코드가 파라미터로 귀결한다.
"훈련 대신 술집에 갔다 왔습니다" 는 서사이고, 피로 -10 은 수치다.
"""

from dataclasses import replace
from typing import Any

from apps.arena.app.use_cases.agents.narration import life_event_subject
from apps.arena.app.use_cases.agents.prompts import build_narration_prompt
from apps.arena.app.use_cases.agents.schemas import NARRATION_SCHEMA
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Character
from apps.arena.domain.ports.ports import DecisionModel, Dice
from apps.arena.domain.services.judgment.training import (
    CATEGORY_KO,
    Category,
    execute_roll,
    judge_training,
    roll_mode,
)

# 카테고리별 효과. (숙련 증가, 피로 변화) — 실행 판정 d20 이 이 값을 스케일한다.
# 능력치는 여기서 손대지 않는다: 유저가 찍은 포인트는 시스템이 뺏지도 주지도 않고
# 성장 포인트로만 오른다(기획서 §5).
EFFECTS: dict[str, tuple[int, int]] = {
    "train": (3, 12),
    "study": (2, 8),
    "rest": (0, -25),
    "leisure": (0, -15),
}

# 거부했을 때 실제로 한 일. 서사는 모델이 쓰지만 결과는 여기 고정이다 —
# 모델이 수치를 정하면 같은 판이 매번 달라진다.
REFUSAL: dict[str, tuple[str, int, int]] = {
    "train": ("훈련장 대신 술집", 0, -8),
    "study": ("책을 덮고 산책", 0, -6),
    "rest": ("쉬라는데 몰래 훈련장", 2, 10),
    "leisure": ("여가를 마다하고 무기 손질", 1, 4),
}

FALLBACK: dict[str, str] = {
    "train": "훈련장에 가는 대신 술집에 앉아 있었다.",
    "study": "책을 덮고 성벽을 걸었다.",
    "rest": "쉬라는 말을 듣고도 몰래 훈련장에 갔다.",
    "leisure": "여가를 마다하고 무기를 손질했다.",
}


def run_training_turn(
    c: Character,
    category: Category,
    model: DecisionModel,
    dice: Dice,
    tracer: Tracer,
) -> tuple[Character, dict[str, Any]]:
    """(바뀐 캐릭터, 결과 요약).

    트레이스에 directive · train_compliance · train_result 를 남긴다.
    """
    tracer.emit("directive", {"category": category, "label": CATEGORY_KO[category]}, actor=c.id)

    comp = judge_training(c, dice)
    tracer.emit("train_compliance", {**comp.as_payload(), "fatigue": c.fatigue}, actor=c.id)

    mode, mode_reason = roll_mode(c)
    value, rolls = execute_roll(mode, dice)

    if comp.verdict == "refuse":
        what, skill_gain, fatigue_delta = REFUSAL[category]
        narration = _narrate(model, c, category, what, tracer)
    else:
        what = CATEGORY_KO[category]
        skill_gain, fatigue_delta = EFFECTS[category]
        if comp.verdict == "partial":
            skill_gain = skill_gain // 2
            fatigue_delta = round(fatigue_delta * 0.5)
        # 실행 판정: d20 이 낮으면 절반, 높으면 그대로 + 1.
        if value <= 7:
            skill_gain = skill_gain // 2
        elif value >= 16:
            skill_gain += 1
        narration = f"{c.name}은(는) {what}에 하루를 썼다."

    fatigue = max(0, min(100, c.fatigue + fatigue_delta))
    after = replace(c, fatigue=fatigue)
    result = {
        "category": category,
        "verdict": comp.verdict,
        "what": what,
        "roll_mode": mode,
        "roll_mode_reason": mode_reason,
        "rolls": rolls,
        "roll": value,
        "effect": {"skill": skill_gain, "fatigue": fatigue_delta},
        "fatigue_before": c.fatigue,
        "fatigue_after": fatigue,
        "narration": narration,
    }
    tracer.emit("train_result", result, actor=c.id)
    return after, result


def _narrate(model: DecisionModel, c: Character, category: str, what: str, tracer: Tracer) -> str:
    """거부 장면의 서사 한 줄. 사실은 코드가 정하고 문장만 모델이 쓴다."""
    fallback = FALLBACK[category]
    facts = {
        "who": life_event_subject(c),
        "ordered": CATEGORY_KO[category],
        "did": what,
        "personality": c.disposition.as_dict(),
        "fatigue": c.fatigue,
    }
    prompt = build_narration_prompt("training_refusal", facts, fallback)
    try:
        data = model.decide("narrator", prompt, NARRATION_SCHEMA)
    except Exception:  # noqa: BLE001 — 서사가 실패해도 인터미션은 계속된다
        return fallback
    text = str(data.get("narration") or "").strip()
    return text or fallback

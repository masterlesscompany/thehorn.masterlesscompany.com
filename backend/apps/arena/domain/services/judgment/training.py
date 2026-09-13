"""육성 턴의 순응·실행 판정 (기획서 §5.1, 설계 §7.1).

전투의 순응 판정과 같은 원칙이다: 코드가 결정론적 확률을 계산하고 시드 주사위가
정한다. 모델은 거부했을 때 **무엇을 했는지**만 쓴다("훈련장 대신 술집").

유저에겐 결과만 통보되고 시스템은 전부 기록한다 — 관찰가능성 문제의 축소판이다.
"""

from dataclasses import dataclass
from typing import Any, Literal

from apps.arena.domain.constants.balance import (
    DILIGENT_PLANNING,
    TIRED_FATIGUE,
    TRAIN_BASE,
    TRAIN_COOPERATION_COEF,
    TRAIN_FATIGUE_COEF,
    TRAIN_MAX,
    TRAIN_MIN,
    TRAIN_PARTIAL_BAND,
    TRAIN_PLANNING_COEF,
)
from apps.arena.domain.entities.types import Character
from apps.arena.domain.ports.ports import Dice

Category = Literal["train", "rest", "study", "leisure"]
Verdict = Literal["comply", "partial", "refuse"]
RollMode = Literal["advantage", "normal", "disadvantage"]

CATEGORY_KO: dict[str, str] = {
    "train": "훈련",
    "rest": "휴식",
    "study": "교육",
    "leisure": "여가",
}


@dataclass(frozen=True)
class TrainingCompliance:
    probability: float
    breakdown: dict[str, float]
    roll: float
    verdict: Verdict

    def as_payload(self) -> dict[str, Any]:
        return {
            "probability": self.probability,
            "breakdown": self.breakdown,
            "roll": self.roll,
            "verdict": self.verdict,
        }


def compliance_probability(c: Character) -> tuple[float, dict[str, float]]:
    """순응 확률. 계획적이고 협동적일수록 오르고, 피로할수록 내린다."""
    bd = {
        "base": TRAIN_BASE,
        "planning": round(TRAIN_PLANNING_COEF * c.disposition.planning, 3),
        "cooperation": round(TRAIN_COOPERATION_COEF * c.disposition.cooperation, 3),
        "fatigue": round(-TRAIN_FATIGUE_COEF * c.fatigue, 3),
    }
    p = max(TRAIN_MIN, min(TRAIN_MAX, sum(bd.values())))
    return round(p, 3), bd


def judge_training(c: Character, dice: Dice) -> TrainingCompliance:
    """순응 / 부분 순응 / 거부.

    부분 순응은 순응 확률 바로 아래 좁은 띠다 — "하긴 했는데 대충 했다".
    """
    p, bd = compliance_probability(c)
    roll = round(dice.uniform(), 3)
    if roll <= p:
        verdict: Verdict = "comply"
    elif roll <= p + TRAIN_PARTIAL_BAND:
        verdict = "partial"
    else:
        verdict = "refuse"
    return TrainingCompliance(p, bd, roll, verdict)


def roll_mode(c: Character) -> tuple[RollMode, str]:
    """실행 판정의 굴림 방식 (기획서 §5.1: 성실→advantage, 피로→disadvantage)."""
    if c.fatigue > TIRED_FATIGUE:
        return "disadvantage", f"피로 {c.fatigue}"
    if c.disposition.planning > DILIGENT_PLANNING:
        return "advantage", f"계획 성향 {c.disposition.planning:+d}"
    return "normal", ""


def execute_roll(mode: RollMode, dice: Dice) -> tuple[int, list[int]]:
    """(쓰인 값, 굴린 값들). advantage 는 두 번 굴려 높은 것, disadvantage 는 낮은 것."""
    if mode == "normal":
        v = dice.roll(20)
        return v, [v]
    a, b = dice.roll(20), dice.roll(20)
    return (max(a, b) if mode == "advantage" else min(a, b)), [a, b]

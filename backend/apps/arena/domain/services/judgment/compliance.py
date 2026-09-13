"""순응 판정 — 성격 가중치 기반 결정론적 확률 (기획서 §5.1·§9, 설계 §6.4).

모델이 순응 여부를 뒤집을 수 없다. 코드가 확률을 계산하고 시드 주사위가
판정하며, 모델에게는 결과만 준다("당신은 방침을 따르지 않기로 했다").
그래야 인스펙터의 "순응 판정: 방침 이탈 확률 71% → 이탈 발생" 이 재현된다.

행운을 읽지 않는다(tests/test_boundaries.py).
"""

import math
from dataclasses import dataclass
from typing import Any

from apps.arena.domain.constants.balance import (
    ADJUST_COOPERATION,
    ADJUST_RISK,
    ADJUST_SACRIFICE,
    DEVIATION_MAX,
    DEVIATION_MIN,
    DEVIATION_SIGMOID_GAIN,
    DEVIATION_SIGMOID_SHIFT,
    PRESSURE_HP_WEIGHT,
    PRESSURE_LIFE_WEIGHT,
    PRESSURE_LOSS_WEIGHT,
    PRESSURE_SCALE_DIVISOR,
)
from apps.arena.domain.ports.ports import Dice
from apps.arena.domain.services.battle.state import Battle, UnitState

Verdict = str  # "comply" | "deviate"


@dataclass(frozen=True)
class ComplianceRecord:
    pressure: float
    pressure_breakdown: dict[str, float]
    adjust: float
    adjust_breakdown: dict[str, float]
    probability: float
    roll: float
    verdict: Verdict

    def as_payload(self) -> dict[str, Any]:
        return {
            "pressure": self.pressure,
            "pressure_breakdown": self.pressure_breakdown,
            "disposition_adjust": self.adjust,
            "adjust_breakdown": self.adjust_breakdown,
            "probability": self.probability,
            "roll": self.roll,
            "verdict": self.verdict,
        }


def allies_lost_ratio(battle: Battle, unit: UnitState) -> float:
    same = [u for u in battle.units.values() if u.faction == unit.faction]
    lost = [u for u in same if not u.active]
    return len(lost) / len(same) if same else 0.0


def deviation_pressure(unit: UnitState, battle: Battle) -> tuple[float, dict[str, float]]:
    """이탈 압력. 성향이 각 항을 **다르게** 늘이고 줄인다.

    위험을 감수하는 사람은 자기 상처를 작게 느끼고, 희생을 받아들이는 사람은
    동료가 쓰러진 것과 두고 온 가족을 견딘다. 세 축이 같은 계수로 한 스칼라에
    합쳐지면 축이 구별되지 않는다(QA 라운드 2).
    """
    d = unit.disposition
    risk_scale = 1 - (d.risk / PRESSURE_SCALE_DIVISOR if d else 0)
    sac_scale = 1 - (d.sacrifice / PRESSURE_SCALE_DIVISOR if d else 0)

    hp_term = PRESSURE_HP_WEIGHT * (1 - unit.hp / unit.hp_max) * risk_scale
    loss_term = PRESSURE_LOSS_WEIGHT * allies_lost_ratio(battle, unit) * sac_scale
    life_term = PRESSURE_LIFE_WEIGHT * (1.0 if unit.dependents > 0 else 0.0) * sac_scale
    bd = {"hp": round(hp_term, 3), "allies_lost": round(loss_term, 3), "life": round(life_term, 3)}
    return round(hp_term + loss_term + life_term, 3), bd


def disposition_adjust(unit: UnitState) -> tuple[float, dict[str, float]]:
    d = unit.disposition
    if d is None:
        return 0.0, {}
    bd = {
        "risk": round(ADJUST_RISK * d.risk, 3),
        "sacrifice": round(ADJUST_SACRIFICE * d.sacrifice, 3),
        "cooperation": round(ADJUST_COOPERATION * d.cooperation, 3),
    }
    return round(sum(bd.values()), 3), bd


def deviation_probability(unit: UnitState, battle: Battle) -> tuple[float, dict[str, Any]]:
    pressure, p_bd = deviation_pressure(unit, battle)
    adjust, a_bd = disposition_adjust(unit)
    x = DEVIATION_SIGMOID_GAIN * (pressure + adjust) - DEVIATION_SIGMOID_SHIFT
    p = 1 / (1 + math.exp(-x))
    p = max(DEVIATION_MIN, min(DEVIATION_MAX, p))
    return round(p, 3), {
        "pressure": pressure,
        "pressure_breakdown": p_bd,
        "adjust": adjust,
        "adjust_breakdown": a_bd,
    }


def judge_compliance(unit: UnitState, battle: Battle, dice: Dice) -> ComplianceRecord:
    """적 유닛(성향 없음)은 항상 순응한다 — 고정 정책 진영이다."""
    if unit.disposition is None:
        return ComplianceRecord(0.0, {}, 0.0, {}, 0.0, 1.0, "comply")
    p, bd = deviation_probability(unit, battle)
    roll = round(dice.uniform(), 3)
    verdict = "deviate" if roll < p else "comply"
    return ComplianceRecord(
        pressure=bd["pressure"],
        pressure_breakdown=bd["pressure_breakdown"],
        adjust=bd["adjust"],
        adjust_breakdown=bd["adjust_breakdown"],
        probability=p,
        roll=roll,
        verdict=verdict,
    )

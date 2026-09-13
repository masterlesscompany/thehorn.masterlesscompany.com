"""신체 주사위 — 탄생 1회(기획서 §4.1). 식은 설계 §4.1."""

from apps.arena.domain.constants.balance import (
    BMI_BY_BUILD,
    BMI_JITTER_DIE,
    BUILD_BY_D6,
    HEIGHT_BASE,
    HEIGHT_DIE,
)
from apps.arena.domain.entities.types import Body
from apps.arena.domain.ports.ports import Dice


def roll_body(dice: Dice) -> Body:
    height = HEIGHT_BASE + dice.roll(HEIGHT_DIE)
    build = BUILD_BY_D6[dice.roll(6)]
    bmi = BMI_BY_BUILD[build] + (dice.roll(BMI_JITTER_DIE) - 3)
    weight = round(bmi * (height / 100) ** 2)
    return Body(height_cm=height, build=build, weight_kg=weight)  # type: ignore[arg-type]

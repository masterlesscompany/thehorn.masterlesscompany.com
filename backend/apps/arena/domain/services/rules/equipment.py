"""효율 스펙트럼 — "장착 불가" 대신 페널티 (기획서 §4.3, 설계 §4.3).

금지가 없어야 판단할 것이 생긴다. 마른 캐릭터에 판금을 입히면 입혀지고,
대신 명중·속도·스태미나로 값을 치른다. 그 값이 인스펙터에 이름과 함께 남는다.
"""

from dataclasses import dataclass

from apps.arena.domain.constants.balance import (
    HEIGHT_PENALTY_PER_5CM,
    MISMATCH_HIT_PENALTY,
    MISMATCH_SPEED_PENALTY,
    MISMATCH_STAMINA_PER_5STR,
)
from apps.arena.domain.entities.types import Body, Equipment, Stats


@dataclass(frozen=True)
class Modifiers:
    hit: int = 0
    speed: int = 0
    stamina_mult: float = 1.0
    # (이유, 값) — 트레이스 resolution.modifiers 에 그대로 실린다
    notes: tuple[tuple[str, float], ...] = ()

    def merged(self, other: "Modifiers") -> "Modifiers":
        return Modifiers(
            hit=self.hit + other.hit,
            speed=self.speed + other.speed,
            stamina_mult=round(self.stamina_mult * other.stamina_mult, 3),
            notes=self.notes + other.notes,
        )


def efficiency(body: Body, stats: Stats, equipment: Equipment) -> Modifiers:
    hit = 0
    speed = 0
    stamina_mult = 1.0
    notes: list[tuple[str, float]] = []

    weight_gap = max(0, equipment.weight_class - body.weight_class)
    if weight_gap:
        hit -= MISMATCH_HIT_PENALTY * weight_gap
        speed -= MISMATCH_SPEED_PENALTY * weight_gap
        notes.append(("무게 미달", -MISMATCH_HIT_PENALTY * weight_gap))

    str_gap = max(0, equipment.min_str - stats.str_)
    if str_gap:
        stamina_mult = round(1 + MISMATCH_STAMINA_PER_5STR * str_gap / 5, 3)
        notes.append(("힘 미달", stamina_mult))

    if equipment.is_long and equipment.min_height and body.height_cm < equipment.min_height:
        height_gap = equipment.min_height - body.height_cm
        penalty = HEIGHT_PENALTY_PER_5CM * (height_gap // 5)
        if penalty:
            hit -= penalty
            notes.append(("키 미달", -penalty))

    return Modifiers(hit=hit, speed=speed, stamina_mult=stamina_mult, notes=tuple(notes))

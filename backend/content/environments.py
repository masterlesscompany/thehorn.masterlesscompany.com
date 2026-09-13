"""환경 — 규칙 엔진의 수정자 (설계 §2.4·§5.5). 서술은 감독 프롬프트에 그대로 들어간다."""

from apps.arena.domain.entities.types import Environment

SWAMP = Environment(
    name="늪지",
    description=(
        "발목까지 잠기는 검은 물. 무거운 갑옷은 발이 빠지고, 젖은 공기에 불이 잘 붙지 않는다."
    ),
    speed_penalty_by_weight={3: -2},
    stamina_multiplier=1.5,
    range_penalty=0,
    darkness=False,
)

MINE = Environment(
    name="폐광",
    description=(
        "무너진 갱도. 천장이 낮아 활은 거리를 못 살리고, 횃불 하나로는 아군의 얼굴도 잘 안 보인다. "
        "갱도의 마른 가스에 불이 잘 붙는다."
    ),
    speed_penalty_by_weight={},
    stamina_multiplier=1.0,
    range_penalty=10,
    darkness=True,
)

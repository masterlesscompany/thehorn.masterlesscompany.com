"""인터미션 — 전투와 전투 사이 (기획서 §5.1·§6.2·§7.1, 설계 §7).

한 번의 인터미션에서 일어나는 일:
  1. 성장 포인트 지급 + 유저 분배
  2. 육성 턴 1회 — 유저가 카테고리를 지시하고 캐릭터가 따를지 정한다
  3. 생애 이벤트 1회 — 성향이 바뀌고, 그것이 다음 판의 판단을 바꾼다

인터미션이 있어야 육성·거부·생애 이벤트가 존재하고, 그 뒤에 전투가 있어야
"이벤트 → 판단 변화" 의 인과가 닫힌다(기획서 §2).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from apps.arena.app.use_cases.intermission.growth import grant
from apps.arena.app.use_cases.intermission.life_event import EventLike, apply_life_event, pick
from apps.arena.app.use_cases.intermission.training import run_training_turn
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Character
from apps.arena.domain.ports.ports import DecisionModel, Dice
from apps.arena.domain.services.judgment.training import Category

PartyMember = tuple[Character, Any, str]
# 캐릭터 id → 그에게 일어날 수 있는 사건들. content 가 만들어 준다.
EventPool = Callable[[Character], list[EventLike]]


@dataclass
class IntermissionInput:
    """유저의 지시. 없으면 기본값으로 간다 — 화면이 응답하지 않아도 판은 이어진다."""

    directives: dict[str, Category] = field(default_factory=dict)
    growth: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class IntermissionState:
    """판 사이에 남는 것. 은행에 쌓인 성장 포인트."""

    banked: dict[str, int] = field(default_factory=dict)


def run_intermission(
    members: list[PartyMember],
    outcome: str,
    user_input: IntermissionInput,
    event_pool: EventPool,
    model: DecisionModel,
    dice: Dice,
    tracer: Tracer,
    state: IntermissionState,
) -> list[PartyMember]:
    tracer.emit(
        "intermission_start", {"after_outcome": outcome, "party": [c.id for c, _, _ in members]}
    )

    members, state.banked = grant(members, outcome, user_input.growth, state.banked, tracer)

    trained: list[PartyMember] = []
    for c, build, voice in members:
        category = user_input.directives.get(c.id, "train")
        after, _ = run_training_turn(c, category, model, dice, tracer)
        trained.append((after, build, voice))

    # 사건은 한 번만 일어난다. 후보 순서는 출전 순서 — dict 순회에 기대지 않는다.
    candidates = {c.id: event_pool(c) for c, _, _ in trained}
    picked = pick(candidates, dice)
    if picked is not None:
        cid, event = picked
        final: list[PartyMember] = []
        for c, build, voice in trained:
            if c.id == cid:
                changed, _ = apply_life_event(c, event, model, tracer)
                final.append((changed, build, voice))
            else:
                final.append((c, build, voice))
        return final
    return trained

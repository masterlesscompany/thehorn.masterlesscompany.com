"""생애 이벤트 — 인터미션마다 한 번 (기획서 §6.2, 설계 §7.2).

effect 는 `param_change` 하나만 쓴다. 이탈·충원·복귀·사망은 C단계이고
타입만 선언돼 있다(`apps.arena.domain.entities.types.EventEffectKind`).

성향이 바뀌면 다음 판의 순응 판정이 달라진다 — "이벤트 → 판단 변화" 의 인과가
여기서 닫힌다(기획서 §2 "A→B의 핵심 차이").
"""

from dataclasses import replace
from typing import Any, Protocol

from apps.arena.app.use_cases.agents.narration import life_event_subject
from apps.arena.app.use_cases.agents.prompts import build_narration_prompt
from apps.arena.app.use_cases.agents.schemas import NARRATION_SCHEMA
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Character
from apps.arena.domain.ports.ports import DecisionModel, Dice


class EventLike(Protocol):
    key: str
    category: str
    title: str
    fact: str
    shift: dict[str, int]
    fatigue: int


def pick(
    candidates_by_character: dict[str, list[EventLike]], dice: Dice
) -> tuple[str, EventLike] | None:
    """누구에게 무슨 일이 일어나는가. 시드가 정한다.

    후보가 있는 캐릭터만 대상이고, 순서는 호출자가 준 순서 그대로다 —
    dict 순회 순서에 기대지 않으려면 호출자가 정렬해서 준다.
    """
    eligible = [(cid, evs) for cid, evs in candidates_by_character.items() if evs]
    if not eligible:
        return None
    cid, evs = eligible[dice.roll(len(eligible)) - 1]
    return cid, evs[dice.roll(len(evs)) - 1]


def apply_life_event(
    c: Character, event: EventLike, model: DecisionModel, tracer: Tracer
) -> tuple[Character, dict[str, Any]]:
    """(바뀐 캐릭터, 파라미터 diff). life_event 와 param_diff 를 남긴다."""
    narration = _narrate(model, c, event)
    tracer.emit(
        "life_event",
        {
            "key": event.key,
            "category": event.category,
            "title": event.title,
            "fact": event.fact,
            "effect": "param_change",
            "narration": narration,
        },
        actor=c.id,
    )

    before = c.disposition.as_dict()
    after_disp = c.disposition.shifted(**event.shift)
    after = after_disp.as_dict()
    fatigue = max(0, min(100, c.fatigue + event.fatigue))
    changed = replace(c, disposition=after_disp, fatigue=fatigue)

    diff = {
        "before": {**before, "fatigue": c.fatigue},
        "after": {**after, "fatigue": fatigue},
        "delta": {
            **{k: after[k] - before[k] for k in after if after[k] != before[k]},
            **({"fatigue": fatigue - c.fatigue} if fatigue != c.fatigue else {}),
        },
        "cause": event.title,
    }
    tracer.emit("param_diff", diff, actor=c.id)
    return changed, diff


def _narrate(model: DecisionModel, c: Character, event: EventLike) -> str:
    fallback = event.fact
    facts = {
        "who": life_event_subject(c),
        "title": event.title,
        "fact": event.fact,
        "life": c.life.note,
        "personality": c.disposition.as_dict(),
    }
    prompt = build_narration_prompt("life_event", facts, fallback)
    try:
        data = model.decide("narrator", prompt, NARRATION_SCHEMA)
    except Exception:  # noqa: BLE001 — 서사가 실패해도 인터미션은 계속된다
        return fallback
    return str(data.get("narration") or "").strip() or fallback

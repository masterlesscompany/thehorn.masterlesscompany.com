"""학습 카드 — 보스전 앞에서 뽑고, 보스전 시작에 펼친다 (기획서 v3 §8.4).

러너에서 갈라 나왔다(QA 2026-09-09 C6). 집계·매칭은 도메인
(`domain/services/judgment/cards.py`)이 하고, 여기는 **언제 뽑고 무엇에
거는가** 만 정한다.
"""

from typing import Any

from apps.arena.domain.constants.balance import CARD_SLOTS
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import MissionSpec, PartyMember
from apps.arena.domain.services.battle.state import ActionRecord, Battle, Status
from apps.arena.domain.services.judgment.cards import choose_cards


def cards_for(
    mission: MissionSpec,
    forsaken: tuple[tuple[str, str, int], ...],
    history: list[ActionRecord],
    pool: tuple[Any, ...],
    members: list[PartyMember],
) -> list[tuple[Any, dict[str, Any]]]:
    """보스전 앞에서만 카드를 뽑는다. 일반전은 카드를 안 쓴다.

    슬롯은 형태가 자랄수록 는다 — 3형태는 진화 트리가 아니라 유저의 실패
    기록이다(기획서 v3 §8.4).
    """
    slots = CARD_SLOTS.get(mission.casualty_tier, 0)
    if not slots or not pool:
        return []
    # 실제 원거리 대원을 센다. 예전에는 빈 집합을 박아 둬서 「사거리」 카드가
    # 영원히 안 나왔다 — 카드 풀 3장 중 1장이 죽은 코드였다(QA 2026-09-09 C1·J4).
    ranged = {c.id for c, build, _ in members if build.weapon.ranged}
    return choose_cards(history, ranged, forsaken, slots, pool)


def apply_cards(battle: Battle, cards: list[tuple[Any, dict[str, Any]]], tracer: Tracer) -> None:
    """보스전 시작에 카드가 펼쳐진다(기획서 v3 §8.4).

    실효는 기존 메커니즘으로만 낸다 — focus 는 이미 있는 boss_focus 를 쓰고,
    ranged_block 은 blind 상태를 건다. 새 효과를 만들지 않는다.
    """
    펼친_것 = []
    for card, why in cards:
        applied: dict[str, Any] = {}
        if card.effect == "focus":
            대상 = why.get("member")
            if 대상 not in battle.units and why.get("char_class"):
                # 굴에 두고 온 사람은 정의상 이 판에 없다. 그것이 배운 것은 그
                # 사람 자체가 아니라 **그 병과를 상대하는 법**이다 — 지금 그
                # 자리에 선 사람을 노린다(QA 2026-09-09 J5·T5).
                같은_병과 = [
                    u.id
                    for u in battle.units.values()
                    if u.faction == battle.party and u.char_class == why["char_class"] and u.alive
                ]
                if 같은_병과:
                    대상 = 같은_병과[0]
                    applied = {"inherited_from": why.get("member")}
            if 대상 in battle.units:
                battle.boss_focus = 대상
                applied = {**applied, "field": "boss_focus", "after": 대상}
        elif card.effect == "ranged_block":
            맞은_사람 = [
                u.id for u in battle.units.values() if u.faction == battle.party and u.weapon.ranged
            ]
            for uid in 맞은_사람:
                battle.units[uid].statuses.append(
                    Status("blind", battle.turn_limit, card.magnitude)
                )
            applied = {"field": "blind", "value": card.magnitude, "units": 맞은_사람}
        펼친_것.append(
            {
                "key": card.key,
                "name": card.name,
                "source": card.source,
                # 출처 라운드·인물·종 셋이 다 링크돼야 한다(기획서 v3 §11).
                # 라운드가 없으면 "판을 넘는 학습" 이 아니라 그냥 표시다.
                "round": why.get("round", 0),
                "observation": card.observation.format(**why),
                "evidence": why,
                "applied": applied,
            }
        )
    tracer.emit("cards", {"cards": 펼친_것})

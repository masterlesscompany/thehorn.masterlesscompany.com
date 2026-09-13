"""쓰러짐 3분기 판정 (기획서 v3 §6.0).

HP 가 0 이 된 대원은 그 자리에서 죽지 않는다. 전투가 끝난 뒤에야
부상 · 끌려감 · 사망으로 갈린다. 굴림은 Dice 포트를 지난다 — 같은 시드가
같은 사상자 명부를 만들어야 리플레이와 실험이 성립한다.
"""

from dataclasses import dataclass
from typing import Literal

from apps.arena.domain.constants.balance import CASUALTY_TABLE
from apps.arena.domain.ports.ports import Dice

Casualty = Literal["injured", "taken", "dead"]


@dataclass(frozen=True)
class CasualtyRoll:
    """판정 하나와 그 근거.

    굴림과 경계를 함께 들고 나온다 — 이 판의 가장 무거운 판정이 결과만
    남기면 인스펙터가 "왜" 를 못 댄다(QA 2026-09-09 J2·V10).
    """

    verdict: Casualty
    roll: int
    tier: str
    # 누적 상한. ("injured", 85) 는 "85 까지가 부상" 이다.
    bounds: tuple[tuple[Casualty, int], ...]


def casualty_bounds(tier: str) -> tuple[tuple[Casualty, int], ...]:
    """표의 비율을 누적 상한으로. 순수 함수 — 굴리지 않는다."""
    injured, taken, _dead = CASUALTY_TABLE[tier]
    return (("injured", injured), ("taken", injured + taken), ("dead", 100))


def resolve_casualty(dice: Dice, tier: str) -> CasualtyRoll:
    """1..100 굴림을 표의 누적 경계에 대본다.

    경계를 포함으로 읽는다 — 부상 97 이면 97 까지가 부상이다. 사망이 0% 인
    구간에서는 100 을 굴려도 끌려감에서 멈춘다.
    """
    bounds = casualty_bounds(tier)
    roll = dice.roll(100)
    verdict = next((k for k, upper in bounds if roll <= upper), "dead")
    return CasualtyRoll(verdict=verdict, roll=roll, tier=tier, bounds=bounds)

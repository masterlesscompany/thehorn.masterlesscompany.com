"""성향 4축 — 주사위 · MBTI 표기 · 한국어 서술 (기획서 §4.5).

MBTI 는 유저가 알아보기 쉽게 붙인 이름표다. 프롬프트에는 describe() 의
수치 서술만 들어간다. mbti_label() 의 결과가 프롬프트에 들어가면
tests/test_prompts.py 가 잡는다.
"""

from apps.arena.domain.constants.balance import DISPOSITION_MAX, DISPOSITION_MIN
from apps.arena.domain.entities.types import Disposition
from apps.arena.domain.ports.ports import Dice


def roll_disposition(dice: Dice) -> Disposition:
    span = DISPOSITION_MAX - DISPOSITION_MIN + 1
    return Disposition(
        *(DISPOSITION_MIN + dice.roll(span) - 1 for _ in range(4)),
    )


def mbti_label(d: Disposition) -> str:
    """가중치 테이블(방식 B). 각 축의 부호가 한 글자를 정한다."""
    return (
        ("E" if d.cooperation >= 0 else "I")
        + ("N" if d.risk >= 0 else "S")
        + ("F" if d.sacrifice >= 0 else "T")
        + ("J" if d.planning >= 0 else "P")
    )


_축_서술 = {
    "risk": ("위험을 감수하는 편", "위험을 피하는 편"),
    "cooperation": ("협동을 중시하는 편", "혼자 움직이는 편"),
    "planning": ("계획대로 움직이는 편", "즉흥적인 편"),
    "sacrifice": ("남을 위해 희생하는 편", "자기 보존이 우선인 편"),
}


def _강도(v: int) -> str:
    a = abs(v)
    if a >= 60:
        return "매우 "
    if a >= 25:
        return ""
    return "약간 "


def describe(d: Disposition) -> dict[str, str]:
    """축별 한국어 서술 + 수치. 예: "위험을 감수하는 편 (+40)"."""
    out = {}
    for axis, (pos, neg) in _축_서술.items():
        v = getattr(d, axis)
        word = pos if v >= 0 else neg
        out[axis] = f"{_강도(v)}{word} ({v:+d})"
    return out

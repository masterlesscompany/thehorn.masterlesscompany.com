import re

from apps.arena.adapter.outbound.strategies.dice import SeededDice
from apps.arena.domain.entities.types import Disposition
from apps.arena.domain.services.rules.disposition import describe, mbti_label, roll_disposition

MBTI = re.compile(r"\b[EI][NS][TF][JP]\b")


def test_MBTI_표기는_가중치_테이블로만_정해진다():
    """기획서 §4.5 방식 B. 협동→E/I, 위험→N/S, 희생→F/T, 계획→J/P."""
    assert mbti_label(Disposition(risk=10, cooperation=50, planning=30, sacrifice=-5)) == "ENTJ"
    assert mbti_label(Disposition(risk=-30, cooperation=-20, planning=-10, sacrifice=40)) == "ISFP"
    assert mbti_label(Disposition(0, 0, 0, 0)) == "ENFJ"


def test_서술에는_MBTI_문자가_없다():
    """프롬프트에 MBTI 를 넣지 않는다 — 고정관념 판단이 되고 재현이 안 된다."""
    d = Disposition(40, -20, 80, 0)
    text = " ".join(describe(d).values())
    assert not MBTI.search(text)
    assert "+40" in text or "40" in text


def test_서술은_네_축을_모두_다룬다():
    축 = {"risk", "cooperation", "planning", "sacrifice"}
    assert set(describe(Disposition(0, 0, 0, 0))) == 축


def test_성향_주사위는_범위_안이고_시드에_결정된다():
    a, b = roll_disposition(SeededDice(11)), roll_disposition(SeededDice(11))
    assert a == b
    for v in a.as_dict().values():
        assert -100 <= v <= 100

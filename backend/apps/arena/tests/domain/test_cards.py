"""학습 카드 선택 — 기획서 v3 §8.4.

집계도 매칭도 결정론이다. 같은 기록이면 같은 카드가 나온다 — 그러지 않으면
"보스가 배웠다" 가 아니라 "보스가 굴렸다" 가 된다.
"""

from apps.arena.domain.services.battle.state import ActionRecord
from apps.arena.domain.services.judgment.cards import choose_cards, pattern_metrics
from content.cards import CARDS


def _hist(pairs):
    return [ActionRecord(1, a, "party", "ATTACK", "minotaur", d, 0) for a, d in pairs]


def test_기여도_최상위를_찾는다():
    m = pattern_metrics(_hist([("thoma", 40), ("martin", 10), ("aude", 0)]), ranged_ids=set())
    assert m["top_contributor"] == "thoma"
    assert m["top_ratio"] == 0.8


def test_아무도_때리지_않았으면_최상위가_없다():
    m = pattern_metrics([], ranged_ids=set())
    assert m["top_contributor"] is None and m["top_ratio"] == 0.0


def test_원거리_인원을_센다():
    m = pattern_metrics([], ranged_ids={"thoma", "agnes"})
    assert m["ranged_count"] == 2


def test_같은_기록이면_같은_카드가_나온다():
    h = _hist([("thoma", 40), ("martin", 10)])
    a = choose_cards(h, ranged_ids={"thoma"}, forsaken=(), slots=3, pool=CARDS)
    b = choose_cards(h, ranged_ids={"thoma"}, forsaken=(), slots=3, pool=CARDS)
    assert [c.key for c, _ in a] == [c.key for c, _ in b]


def test_굴에_두고_온_사람이_있으면_섭식_카드가_먼저_온다():
    """미회수의 대가가 카드가 되어 눈앞에 있다(기획서 v3 §8.4)."""
    h = _hist([("thoma", 40), ("martin", 10)])
    cards = choose_cards(
        h, ranged_ids={"thoma"}, forsaken=(("martin", "warrior", 7),), slots=3, pool=CARDS
    )
    assert cards[0][0].key == "devoured"
    assert cards[0][1]["member"] == "martin" and cards[0][1]["char_class"] == "warrior"


def test_슬롯을_넘지_않는다():
    h = _hist([("thoma", 40), ("martin", 10)])
    assert (
        len(
            choose_cards(
                h, ranged_ids={"thoma"}, forsaken=(("martin", "warrior", 7),), slots=1, pool=CARDS
            )
        )
        == 1
    )


def test_재료가_없으면_카드도_없다():
    assert choose_cards([], ranged_ids=set(), forsaken=(), slots=3, pool=CARDS) == []

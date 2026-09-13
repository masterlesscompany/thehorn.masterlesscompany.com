"""속도 어댑터 — 판이 사람 눈에 보이는 속도로 흐른다."""

import time

from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.adapter.outbound.strategies.llm.paced import PacedModel
from apps.arena.domain.ports.ports import DecisionModel


def test_포트를_그대로_만족한다():
    assert isinstance(PacedModel(FakeModel(), 0.0), DecisionModel)


def test_지연이_0이면_느려지지_않는다():
    m = PacedModel(FakeModel(), 0.0)
    t0 = time.perf_counter()
    for _ in range(20):
        m.decide("character", "{}", {"type": "object"})
    assert time.perf_counter() - t0 < 0.5


def test_지연을_주면_그만큼_쉰다():
    m = PacedModel(FakeModel(), 0.02)
    t0 = time.perf_counter()
    for _ in range(5):
        m.decide("character", "{}", {"type": "object"})
    assert time.perf_counter() - t0 >= 0.1


def test_이름과_속성은_안쪽_것을_그대로_쓴다():
    inner = FakeModel()
    m = PacedModel(inner, 0.0)
    assert m.name == inner.name

import pytest

from apps.arena.adapter.outbound.sinks.list_sink import ListSink
from apps.arena.domain.entities.trace_event import KINDS, TraceEvent, Tracer, from_json, to_json


def test_모르는_kind_는_거부한다():
    with pytest.raises(ValueError):
        TraceEvent("r", 1, "t", 1, 1, "banana", None, {})


def test_왕복_직렬화():
    e = TraceEvent(
        "r", 1, "2026-09-07T00:00:00", 1, 3, "decision", "thoma", {"a": [1, 2], "b": "한글"}
    )
    assert from_json(to_json(e)) == e


def test_tracer_는_seq_를_단조_증가시키고_mission_turn_을_붙인다():
    sink = ListSink()
    t = Tracer("run1", sink, clock=lambda: "T")
    t.mission, t.turn = 1, 2
    a = t.emit("turn_start", {"order": []})
    b = t.emit("odds", {"value": 0.5}, actor=None)
    assert (a.seq, b.seq) == (1, 2)
    assert (b.mission, b.turn, b.ts) == (1, 2, "T")
    assert sink.of_kind("odds") == [b]


def test_페이로드의_dataclass_와_tuple_은_직렬화된다():
    from apps.arena.domain.entities.types import Action

    t = Tracer("r", ListSink(), clock=lambda: "T")
    e = t.emit("decision", {"action": Action("ATTACK", "minotaur"), "pair": (1, "x")})
    assert e.payload["action"]["kind"] == "ATTACK"
    assert e.payload["pair"] == [1, "x"]


def test_싱크_실패는_판을_멈추지_않는다():
    class 깨진싱크:
        def emit(self, e):
            raise OSError("디스크 없음")

    t = Tracer("r", 깨진싱크(), clock=lambda: "T")
    assert t.emit("odds", {}).seq == 1


def test_설계_8장의_kind_가_전부_있다():
    필수 = {
        "run_start",
        "plan",
        "odds",
        "context",
        "compliance",
        "decision",
        "resolution",
        "boss_adapt",
        "replan_trigger",
        "abandon",
        "flee",
        "mission_end",
        "run_end",
        "intermission_start",
        "directive",
        "train_compliance",
        "train_result",
        "life_event",
        "param_diff",
        "growth_points",
        "advice",
    }
    assert 필수 <= KINDS

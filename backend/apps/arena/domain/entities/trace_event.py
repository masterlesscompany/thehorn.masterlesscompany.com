"""트레이스 이벤트 스키마 v1 — 첫 이틀의 계약 (기획서 §3.3, 설계 §8).

코어는 쓰고, 평가와 프론트는 읽는다. frontend/lib/trace.ts 가 이 kind 목록을
미러링하고, 양쪽이 docs/trace-samples/one-run.jsonl 을 같이 읽어 계약이
갈라지지 않게 한다(tests/test_trace_contract.py · lib/trace.test.ts).
"""

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from apps.arena.domain.ports.ports import TraceSink

KINDS: frozenset[str] = frozenset(
    {
        "run_start",
        "mission_start",
        "plan",
        "odds",
        "turn_start",
        "context",
        "compliance",
        "decision",
        "resolution",
        "cards",
        "boss_adapt",
        "replan_trigger",
        "abandon",
        "flee",
        "summon",
        "horn",
        "casualty",
        "boss_named",
        "recovery",
        "mission_end",
        "intermission_start",
        "directive",
        "train_compliance",
        "train_result",
        "life_event",
        "param_diff",
        "growth_points",
        "advice",
        "run_end",
    }
)


@dataclass(frozen=True)
class TraceEvent:
    run_id: str
    seq: int
    ts: str
    mission: int
    turn: int
    kind: str
    actor: str | None
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"모르는 이벤트 종류: {self.kind}")


def to_json(e: TraceEvent) -> str:
    return json.dumps(asdict(e), ensure_ascii=False, default=_jsonable)


def from_json(s: str) -> TraceEvent:
    return TraceEvent(**json.loads(s))


def _jsonable(o: Any) -> Any:
    """dataclass · tuple · set 을 JSON 으로. 모르는 것은 문자열로 — 로그가 판을 죽이면 안 된다."""
    if hasattr(o, "__dataclass_fields__"):
        return asdict(o)
    if isinstance(o, set | frozenset):
        return sorted(o)
    return str(o)


# 결정론 비교에서 빼는 필드. 측정한 시각과 걸린 시간은 매번 다르고, 판단이 아니다.
NON_DETERMINISTIC = ("ts", "timing")


def judgment_view(e: "TraceEvent") -> dict[str, Any]:
    """ "같은 시드 = 같은 판" 을 비교하는 정본(설계 §3.4).

    테스트마다 각자 필드를 빼면 결정론의 정의가 갈라진다 — 실제로 갈라져 있었고
    한쪽은 항상 빨갛고 한쪽은 통과했다(QA 라운드 1 P0-2). 여기 하나만 쓴다.
    """
    d = {k: v for k, v in asdict(e).items() if k not in NON_DETERMINISTIC}
    d["payload"] = {k: v for k, v in d["payload"].items() if k not in NON_DETERMINISTIC}
    return d


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class Tracer:
    """seq 를 매기고 mission/turn 을 들고 다닌다. clock 주입은 결정론 테스트용."""

    def __init__(self, run_id: str, sink: TraceSink, clock: Callable[[], str] = _now) -> None:
        self.run_id = run_id
        self._sink = sink
        self._clock = clock
        self.seq = 0
        self.mission = 0
        self.turn = 0

    def emit(self, kind: str, payload: dict[str, Any], actor: str | None = None) -> TraceEvent:
        self.seq += 1
        e = TraceEvent(
            run_id=self.run_id,
            seq=self.seq,
            ts=self._clock(),
            mission=self.mission,
            turn=self.turn,
            kind=kind,
            actor=actor,
            # 직렬화 가능한 형태로 미리 바꿔 둔다 — 싱크가 무엇이든 같은 것을 받는다.
            payload=json.loads(json.dumps(payload, ensure_ascii=False, default=_jsonable)),
        )
        try:
            self._sink.emit(e)
        except Exception:  # noqa: BLE001 — 기록 실패가 판을 멈추면 안 된다
            pass
        return e

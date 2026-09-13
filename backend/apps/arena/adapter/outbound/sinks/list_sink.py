"""메모리 싱크. 파일·큐 싱크는 adapters/ 에 있다."""

from apps.arena.domain.entities.trace_event import TraceEvent


class ListSink:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)

    def of_kind(self, kind: str) -> list[TraceEvent]:
        return [e for e in self.events if e.kind == kind]

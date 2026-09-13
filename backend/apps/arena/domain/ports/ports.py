"""경계 인터페이스.

안쪽 계층이 인터페이스를 소유하고 바깥 계층이 구현한다. 그래야 의존성이
항상 안쪽을 향한다 — adapters/ 는 core 를 알지만 core 는 google-genai 도
anthropic 도 모른다.

여기 선언된 Protocol 은 전부 최소 두 구현을 갖는다(설계 §3.4):
DecisionModel 은 Fake · Replay · Gemini · Anthropic, Dice 는 Seeded · Fixed,
TraceSink 는 List · Queue · Jsonl, RunStore 는 Jsonl · InMemory.
"""

from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["orchestrator", "character", "boss", "narrator"]
JsonSchema = dict[str, Any]


@runtime_checkable
class Dice(Protocol):
    """시드 고정 난수. 같은 시드는 같은 판을 만든다 — 리플레이·실험의 전제."""

    def roll(self, sides: int) -> int:
        """1..sides."""
        ...

    def uniform(self) -> float:
        """[0, 1)."""
        ...


@runtime_checkable
class DecisionModel(Protocol):
    """LLM 포트. 역할과 프롬프트, 응답 JSON 스키마를 받고 dict 를 돌려준다.

    스키마 검증·재시도·폴백은 여기가 아니라 adapters/harness 가 한다 —
    포트는 "모델이 답한다" 만 약속한다.
    """

    @property
    def name(self) -> str: ...

    def decide(self, role: Role, prompt: str, schema: JsonSchema) -> dict[str, Any]: ...


@runtime_checkable
class TraceSink(Protocol):
    def emit(self, event: Any) -> None:
        """TraceEvent 를 받는다. 실패가 판을 멈추면 안 된다 — 호출자가 예외를 삼킨다."""
        ...


@runtime_checkable
class RunStore(Protocol):
    def save(self, run: Any) -> None: ...

    def load(self, run_id: str) -> Any | None: ...

    def list_recent(self, limit: int) -> list[Any]: ...

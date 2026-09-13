"""Replay 모델 — 녹화된 판단을 순서대로 돌려준다 (기획서 §9 추가①, 설계 §3.4).

데모 빨리감기와 LLM 장애 폴백에 쓴다. 녹화된 트레이스의 plan/decision 이벤트에서
raw 응답을 역할별로 꺼내 준다. 같은 시드·같은 설정이면 규칙 엔진이 같은 질문을
같은 순서로 하므로 답이 맞아떨어진다. 녹화가 바닥나면(설정이 달라졌다면) 폴백.
"""

from collections import deque
from typing import Any

from apps.arena.domain.entities.trace_event import TraceEvent
from apps.arena.domain.ports.ports import DecisionModel, JsonSchema, Role


class ReplayModel:
    name = "replay"

    def __init__(self, events: list[TraceEvent], fallback: DecisionModel) -> None:
        self._queues: dict[str, deque[dict[str, Any]]] = {
            "orchestrator": deque(),
            "character": deque(),
            "boss": deque(),
            "narrator": deque(),
        }
        for e in events:
            if e.kind == "plan":
                self._queues["orchestrator"].append(e.payload["raw"])
            elif e.kind == "decision" and "raw" in e.payload:
                role = "boss" if e.payload.get("verdict") == "policy" else "character"
                self._queues[role].append(e.payload["raw"])
            elif e.kind in ("train_result", "life_event") and "raw" in e.payload:
                self._queues["narrator"].append(e.payload["raw"])
        self._fallback = fallback
        self.exhausted = 0

    def decide(self, role: Role, prompt: str, schema: JsonSchema) -> dict[str, Any]:
        q = self._queues.get(role)
        if q:
            return dict(q.popleft())
        self.exhausted += 1
        return self._fallback.decide(role, prompt, schema)

"""속도 어댑터 — 판이 사람 눈에 보이는 속도로 흐르게 한다.

Fake 모델은 한 판을 수백 ms 에 끝낸다. 그러면 서사가 한꺼번에 쏟아지고,
**뿔피리를 누를 시간이 없다**(기획서 v3 §8.2). 유저의 유일한 전투 중 개입이
물리적으로 불가능해지면 그 기능은 없는 것과 같다.

core 를 재우지 않는다. 포트를 감싼 어댑터가 잔다 — 규칙 엔진은 시간을 모른다.
실모델은 이미 느리므로 지연을 0 으로 둔다.
"""

import time
from typing import Any

from apps.arena.domain.ports.ports import DecisionModel, JsonSchema, Role


class PacedModel:
    """decide() 한 번에 delay_s 만큼 쉰다. 0 이면 아무것도 하지 않는다."""

    def __init__(self, inner: DecisionModel, delay_s: float) -> None:
        self._inner = inner
        self._delay = max(0.0, delay_s)

    @property
    def name(self) -> str:
        return self._inner.name

    def __getattr__(self, item: str) -> Any:
        # calls_used · fallbacks 처럼 하네스가 노출하는 것을 그대로 통과시킨다.
        return getattr(self._inner, item)

    def decide(self, role: Role, prompt: str, schema: JsonSchema) -> dict[str, Any]:
        out = self._inner.decide(role, prompt, schema)
        if self._delay:
            time.sleep(self._delay)
        return out

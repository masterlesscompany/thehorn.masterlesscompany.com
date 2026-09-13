"""환경변수로 모델을 고른다 (설계 §3.4). RPG_MODEL=fake|replay|gemini|anthropic. 기본 fake.

실모델 어댑터는 선택 의존성이라 여기서 지연 import 한다 — 설치돼 있지 않아도
fake 로는 돌아야 한다.
"""

import os

from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.adapter.outbound.strategies.llm.paced import PacedModel
from apps.arena.domain.constants.balance import MAX_CALLS
from apps.arena.domain.ports.ports import DecisionModel


def model_name_from_env() -> str:
    return os.environ.get("RPG_MODEL", "fake").lower()


def build_model(name: str | None = None) -> DecisionModel:
    name = name or model_name_from_env()
    if name == "fake":
        return FakeModel()
    if name == "gemini":
        from apps.arena.adapter.outbound.strategies.llm.gemini import GeminiModel

        return GeminiModel()
    if name == "anthropic":
        from apps.arena.adapter.outbound.strategies.llm.anthropic import AnthropicModel

        return AnthropicModel()
    raise ValueError(f"모르는 모델: {name} (fake|gemini|anthropic)")


# Fake 로 도는 판의 기본 박자(초/판단). 0 이면 2판 계약이 0.11초에 끝나
# **뿔피리를 물리적으로 누를 수 없다** — 3턴에 요청하면 409 「전투 중이 아니다」가
# 온다(QA 재검 2026-09-09, 실측 전투 창 0.04초). 로스터 화면은 굵은 글씨로
# "당신이 할 수 있는 일은 뿔피리뿐이다" 라고 말한다. 기본값이 그 말을 거짓말로
# 만들면 안 된다. 실모델은 이미 느리므로 0 이다.
FAKE_PACE_S = 0.2


def pace_seconds(model_name: str = "fake") -> float:
    """RPG_PACE_S — decide() 한 번마다 쉬는 시간(초).

    환경변수가 있으면 그것이 이긴다. 없으면 Fake 만 박자를 받는다.
    """
    raw = os.environ.get("RPG_PACE_S")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            return 0.0
    return FAKE_PACE_S if model_name == "fake" else 0.0


def build_harness(
    missions: int = 1,
    name: str | None = None,
    max_calls: int | None = None,
    pace: float | None = None,
) -> Harness:
    """모든 경로가 하네스를 거친다 — 스키마 검증·재시도·폴백·호출 계수.

    `MAX_CALLS` 는 **전투 한 판**의 상한이다(기획서 §7.1). 하네스는 런 하나를
    끝까지 함께 가므로 예산도 계약 길이만큼 잡는다 — 그러지 않으면 18출동에서
    8회차부터 모든 판단이 조용히 Fake 로 떨어진다(QA 2026-09-09 V2).
    """
    per_mission = max_calls or int(os.environ.get("RPG_MAX_CALLS", MAX_CALLS))
    limit = per_mission * max(1, missions)
    name = name or model_name_from_env()
    model = build_model(name)
    # 박자는 **화면**의 것이다 — 실험 러너는 수백 판을 돌리므로 0 이어야 한다.
    pace = pace_seconds(name) if pace is None else pace
    if pace:
        model = PacedModel(model, pace)
    return Harness(model, FakeModel(), max_calls=limit)

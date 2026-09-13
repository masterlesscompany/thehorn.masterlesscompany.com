"""HTTP 요청/응답 스키마. 도메인 검증(포인트 총량·출전 인원)은 core/content 가 한다 —
여기는 모양만 본다."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateRunRequest(BaseModel):
    """출정 요청.

    모르는 필드를 막는다. `{"orchestrater": false}` 오타가 200 을 받고 감독이
    **켜진 채** 돌면, A/B 토글이 조용히 반대 팔로 도는 것이라 실험 신뢰성이
    무너진다(§3.1). "게임은 막지 않는다" 는 전략 얘기지 오타 얘기가 아니다
    (QA 재검 2026-09-09 R18).
    """

    model_config = ConfigDict(extra="forbid")

    lineup: list[str] = Field(min_length=1, max_length=5)
    allocations: dict[str, dict[str, int]] = Field(default_factory=dict)
    classes: dict[str, str] = Field(default_factory=dict)
    genders: dict[str, Literal["female", "male"]] = Field(default_factory=dict)
    orchestrator: bool = True
    adaptation: bool = True
    seed: int | None = None
    missions: Literal[1, 2] = 1


class CreateRunResponse(BaseModel):
    run_id: str
    seed: int
    model: str


class DirectivesRequest(BaseModel):
    """인터미션 입력(B단계). 지시 카테고리 + 성장 포인트 분배."""

    directives: dict[str, Literal["train", "rest", "study", "leisure"]] = Field(
        default_factory=dict
    )
    growth: dict[str, dict[str, int]] = Field(default_factory=dict)


class RecoveryRequest(BaseModel):
    """회수 결정 — 지불할 대원 id 목록(기획서 v3 §6.8). 빈 목록은 전원 미지불이다.

    `pay` 는 **필수**다. 기본값을 두면 `{"payy": [...]}` 같은 오타가 200 을 받고
    큐를 소비해 전원 영구 상실로 확정된다 — 진짜 결정은 409 를 받고, 되돌릴
    방법이 없다(QA 2026-09-09 T7). "게임은 막지 않는다" 는 전략 얘기지
    오타 얘기가 아니다. 모르는 필드도 막는다.
    """

    model_config = ConfigDict(extra="forbid")

    pay: list[str]

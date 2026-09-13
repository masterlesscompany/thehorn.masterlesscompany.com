import pytest

from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.harness.validate import validate
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.app.use_cases.agents.schemas import CHARACTER_SCHEMA


def test_검증기는_타입_필수_enum_범위를_잡는다():
    schema = {
        "type": "object",
        "required": ["a", "b"],
        "properties": {
            "a": {"type": "string", "enum": ["x", "y"]},
            "b": {"type": "number", "minimum": 0, "maximum": 1},
            "c": {"type": ["string", "null"]},
        },
    }
    assert validate({"a": "x", "b": 0.5, "c": None}, schema) == []
    errs = validate({"a": "z", "b": 2}, schema)
    assert len(errs) == 2 and "enum" not in errs[0]  # 사람이 읽는 문장
    assert validate({"a": "x"}, schema) == ["$: 필수 필드 b 가 없다"]
    assert validate({"a": "x", "b": True}, schema)  # bool 은 number 가 아니다


class 대본모델:
    """정해둔 응답을 순서대로 낸다. 바닥나면 마지막 것을 반복한다."""

    name = "script"

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts: list[str] = []

    def decide(self, role, prompt, schema):
        self.prompts.append(prompt)
        r = self.responses[min(len(self.prompts) - 1, len(self.responses) - 1)]
        if isinstance(r, Exception):
            raise r
        return dict(r)


좋은_응답 = {"action": "DEFEND", "follows_plan": True, "reason": "ok"}
_CTX = '{"role":"character","self":{"hp_pct":100},"available":[{"kind":"DEFEND"}]}'
PROMPT = f"...\n<<CONTEXT_JSON>>\n{_CTX}\n<<END>>\n"


def test_깨진_응답은_오류를_붙여_다시_묻고_통과하면_attempts_가_남는다():
    m = 대본모델([{"action": "JUMP"}, {"action": "DEFEND"}, 좋은_응답])
    h = Harness(m, FakeModel())
    out = h.decide("character", PROMPT, CHARACTER_SCHEMA)
    assert out["action"] == "DEFEND" and out["_meta"]["attempts"] == 3
    assert out["_meta"]["fallback"] is False
    assert "형식에 맞지 않았다" in m.prompts[1] and "필수 필드" in m.prompts[1]


def test_세_번_실패하면_폴백으로_답하고_기록한다():
    m = 대본모델([{"action": "JUMP"}])
    h = Harness(m, FakeModel())
    out = h.decide("character", PROMPT, CHARACTER_SCHEMA)
    assert out["_meta"]["fallback"] is True and out["_meta"]["model"] == "fake"
    assert out["action"] == "DEFEND" and h.fallbacks == 1 and h.calls_used == 3


def test_모델_예외도_폴백으로_흡수한다():
    m = 대본모델([RuntimeError("timeout")])
    out = Harness(m, FakeModel()).decide("character", PROMPT, CHARACTER_SCHEMA)
    assert out["_meta"]["fallback"] and "timeout" in out["_meta"]["fallback_reason"]


def test_호출_상한을_넘으면_모델을_부르지_않는다():
    m = 대본모델([좋은_응답])
    h = Harness(m, FakeModel(), max_calls=1)
    h.decide("character", PROMPT, CHARACTER_SCHEMA)
    out = h.decide("character", PROMPT, CHARACTER_SCHEMA)
    assert out["_meta"]["fallback_reason"] == "budget" and len(m.prompts) == 1


@pytest.mark.parametrize("role,schema", [("character", CHARACTER_SCHEMA)])
def test_Fake_는_항상_스키마를_통과한다(role, schema):
    out = FakeModel().decide(role, PROMPT, schema)
    assert validate(out, schema) == []

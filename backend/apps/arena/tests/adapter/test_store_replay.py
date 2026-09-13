import json
from pathlib import Path

from apps.arena.adapter.outbound.repositories.jsonl_run_repository import JsonlRunStore
from apps.arena.adapter.outbound.strategies.dice import SeededDice
from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.adapter.outbound.strategies.llm.replay import ReplayModel
from apps.arena.adapter.outbound.strategies.llm.select import build_harness, build_model
from apps.arena.app.use_cases.runner import run
from apps.arena.domain.entities.trace_event import KINDS, from_json, judgment_view
from apps.arena.domain.entities.types import RunConfig
from content.missions import MISSIONS_A
from content.party import build_party

# apps/arena/tests/adapter/ → 저장소 루트까지 다섯 단계다.
SAMPLE = Path(__file__).resolve().parents[5] / "docs" / "trace-samples" / "one-run.jsonl"


def _cfg(seed=3):
    return RunConfig(
        seed=seed,
        lineup=("agnes", "thoma", "gilles"),
        allocations={},
        classes={},
        genders={},
        orchestrator_on=True,
        adaptation_on=True,
        missions=MISSIONS_A,
        intermission=False,
    )


def _run(cfg, model_factory=lambda _n: Harness(FakeModel(), FakeModel())):
    return run("r1", cfg, build_party(cfg), model_factory, SeededDice, clock=lambda: "T")


def _strip(events):
    return [judgment_view(e) for e in events]


def _strip_model(events):
    """판단 내용만 본다 — 누가 답했는지(fake vs replay)는 뺀다.

    결정론 비교(_strip)와 다른 질문이다: "리플레이가 같은 판단을 냈는가".
    """
    out = []
    for d in _strip(events):
        d["payload"] = {k: v for k, v in d["payload"].items() if k != "model"}
        out.append(d)
    return out


def test_저장_후_불러오면_같다(tmp_path):
    store = JsonlRunStore(tmp_path)
    rec = _run(_cfg())
    store.save(rec)
    loaded = store.load("r1")
    assert loaded is not None
    assert _strip(loaded.events) == _strip(rec.events)
    assert loaded.results[0].outcome == rec.results[0].outcome
    assert loaded.config["seed"] == 3


def test_없는_런은_None_이고_이상한_id_는_거부한다(tmp_path):
    store = JsonlRunStore(tmp_path)
    assert store.load("nope") is None
    import pytest

    with pytest.raises(ValueError):
        store.load("../etc/passwd")


def test_최근_목록은_요약만_읽는다(tmp_path):
    store = JsonlRunStore(tmp_path)
    store.save(_run(_cfg(1)))
    rows = store.list_recent(5)
    assert rows[0]["run_id"] == "r1" and rows[0]["lineup"] == ["agnes", "thoma", "gilles"]


def test_리플레이는_모델_호출_없이_같은_판을_재생한다():
    """기획서 §11.3 — 데모에서 AI 를 안 부르고 안정적으로 보여준다."""
    original = _run(_cfg())

    class 부르면안됨:
        name = "boom"

        def decide(self, *a):
            raise AssertionError("리플레이 중에 모델을 불렀다")

    replay = ReplayModel(original.events, fallback=부르면안됨())
    again = _run(_cfg(), model_factory=lambda _n: Harness(replay, 부르면안됨()))
    assert _strip_model(again.events) == _strip_model(original.events)
    assert replay.exhausted == 0


def test_녹화가_바닥나면_폴백으로_간다():
    original = _run(_cfg())
    replay = ReplayModel(original.events, fallback=FakeModel())
    other = _run(_cfg(seed=9), model_factory=lambda _n: Harness(replay, FakeModel()))
    assert other.results[0].outcome in ("win", "lose", "retreat", "draw")


def test_기본_모델은_fake_이고_하네스를_거친다(monkeypatch):
    monkeypatch.delenv("RPG_MODEL", raising=False)
    assert build_model().name == "fake"
    h = build_harness()
    assert h.name == "fake" and h.calls_used == 0


def test_샘플_트레이스는_계약을_지킨다():
    """docs/trace-samples/one-run.jsonl — 프론트 lib/trace.test.ts 가 같은 파일을 읽는다."""
    assert SAMPLE.exists(), "scripts/make_trace_sample.py 를 돌려 샘플을 만든다"
    lines = SAMPLE.read_text(encoding="utf-8").splitlines()
    events = [from_json(line) for line in lines]
    assert events[0].kind == "run_start" and events[-1].kind == "run_end"
    assert {e.kind for e in events} <= KINDS
    assert [e.seq for e in events] == list(range(1, len(events) + 1))
    # 데모 하이라이트가 샘플에 있어야 화면 개발이 된다
    kinds = {e.kind for e in events}
    assert {"plan", "context", "compliance", "decision", "resolution", "odds"} <= kinds
    assert {"abandon", "replan_trigger", "boss_adapt", "flee"} <= kinds
    assert any(e.kind == "compliance" and e.payload["verdict"] == "deviate" for e in events)
    # v3 의 심장도 샘플에 있어야 프론트가 화면을 만들 수 있다.
    assert {"cards", "casualty", "recovery", "boss_named", "horn"} <= kinds
    # 샘플이 못 덮는 것은 **명시한다.** 부분집합만 보면 무엇이 왜 빠졌는지
    # 아무도 모른다(QA 재검 2026-09-09 R17).
    인터미션 = {
        "intermission_start",
        "directive",
        "train_compliance",
        "train_result",
        "life_event",
        "param_diff",
        "growth_points",
        "advice",
    }
    빠진 = KINDS - kinds - 인터미션
    assert not 빠진, f"샘플이 이 종류를 한 번도 안 담는다: {sorted(빠진)}"


def test_샘플_트레이스가_낡지_않았다():
    """QA 2026-09-09 C10·V11 — 미션 번호를 바꾼 커밋이 샘플을 안 만들어 두는 바람에
    재생성하면 359줄 중 358줄이 바뀌는 상태였다. **낡았는지 묻는 검사가 양쪽 어디에도
    없었다.** 프론트가 이 파일로 계약을 확인하므로 낡은 샘플은 거짓 초록을 만든다.

    지금 코드가 만드는 판정 뷰와 커밋된 파일이 같은지 본다(ts·timing 은 판단이 아니라 뺀다).
    """
    import subprocess
    import sys

    script = SAMPLE.parents[2] / "scripts" / "make_trace_sample.py"
    out = subprocess.run(
        [sys.executable, str(script), "--stdout"],
        capture_output=True,
        text=True,
        check=True,
        cwd=SAMPLE.parents[2] / "backend",
    ).stdout.splitlines()
    committed = [
        json.dumps(judgment_view(from_json(line)), ensure_ascii=False, sort_keys=True)
        for line in SAMPLE.read_text(encoding="utf-8").splitlines()
    ]
    assert out == committed, (
        f"샘플이 낡았다 — `uv run python ../scripts/make_trace_sample.py` 를 돌린다 "
        f"(지금 {len(out)}줄 vs 커밋된 {len(committed)}줄)"
    )


def test_Fake_는_기본으로_박자를_받는다():
    """QA 재검 2026-09-09 — 기본 박자가 0 이라 2판 계약이 0.11초에 끝났다.

    3턴에 뿔피리를 요청하면 409 「전투 중이 아니다」가 온다 — 로스터 화면이
    굵은 글씨로 광고하는 유일한 개입 수단을 **물리적으로 누를 수 없었다.**
    실모델은 이미 느리므로 박자를 안 받는다.
    """
    import os

    from apps.arena.adapter.outbound.strategies.llm.select import FAKE_PACE_S, pace_seconds

    있던 = os.environ.pop("RPG_PACE_S", None)
    try:
        assert pace_seconds("fake") == FAKE_PACE_S > 0
        assert pace_seconds("anthropic") == 0.0
        os.environ["RPG_PACE_S"] = "0"  # 환경변수가 이긴다 — 테스트·CI 는 0 으로 돈다
        assert pace_seconds("fake") == 0.0
    finally:
        os.environ.pop("RPG_PACE_S", None)
        if 있던 is not None:
            os.environ["RPG_PACE_S"] = 있던

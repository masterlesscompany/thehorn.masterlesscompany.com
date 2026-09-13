import json
import time

import pytest
from fastapi.testclient import TestClient

from apps.arena.adapter.inbound.api.v1.arena_router import build_app
from apps.arena.adapter.outbound.repositories.jsonl_run_repository import JsonlRunStore
from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel


@pytest.fixture
def paced_client(tmp_path):
    """판단마다 조금 쉬는 클라이언트 — 전투 창이 열려 있는 동안 HTTP 로 끼어들 수 있다.

    기본 클라이언트는 2판 계약을 0.1초에 끝내서, 뿔피리 HTTP 테스트가 **한 번도
    200 을 못 받고** `남은 == []` 로 공허 통과했다(20회 반복 실측 0/20).
    그래서 `blow_horn → horn_signal → 러너` 왕복을 어떤 테스트도 안 지났다
    (QA 재검 2026-09-09 R14).
    """
    from apps.arena.adapter.outbound.strategies.llm.paced import PacedModel

    app = build_app(
        store=JsonlRunStore(tmp_path),
        model_factory=lambda _n: Harness(PacedModel(FakeModel(), 0.02), FakeModel()),
    )
    return TestClient(app)


def _wait_kind(client, run_id, kind, timeout=10.0):
    """그 종류의 이벤트가 나올 때까지 기다린다. 없으면 None."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        body = client.get(f"/runs/{run_id}").json()
        hit = next((e for e in body["events"] if e["kind"] == kind), None)
        if hit is not None:
            return hit
        if body["done"]:
            return None
        time.sleep(0.01)
    return None


@pytest.fixture
def client(tmp_path):
    app = build_app(
        store=JsonlRunStore(tmp_path), model_factory=lambda _n: Harness(FakeModel(), FakeModel())
    )
    return TestClient(app)


def _parse_sse(text: str) -> list[dict]:
    out = []
    for block in text.strip().split("\n\n"):
        kind = data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                kind = line[7:]
            elif line.startswith("data: "):
                data = line[6:]
        if kind and data is not None:
            out.append({"event": kind, "data": json.loads(data)})
    return out


def _wait_done(client, run_id, timeout=10.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get(f"/runs/{run_id}")
        if r.status_code == 200 and r.json()["done"]:
            return r.json()
        time.sleep(0.05)
    raise AssertionError("런이 끝나지 않는다")


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["model"] == "fake"


def test_프리셋_로스터_다섯(client):
    r = client.get("/roster/preset")
    body = r.json()
    assert len(body["roster"]) == 5 and body["free_points"] == 18 and body["lineup_size"] == 3
    가장형 = next(c for c in body["roster"] if c["id"] == "agnes")
    assert 가장형["mbti"] and "딸" in 가장형["life"] and 가장형["build_preview"]["weapon"]
    assert sum(가장형["recommended"].values()) == 18


def test_출전_인원_상한을_넘으면_422(client):
    r = client.post("/runs", json={"lineup": ["martin", "aude", "thoma", "agnes"], "seed": 1})
    assert r.status_code == 422 and "1~3명" in r.json()["detail"]


def test_혼자_출전해도_받아준다(client):
    """기획서 §8.1 — 게임은 막지 않는다. 결과가 따라올 뿐이다."""
    assert client.post("/runs", json={"lineup": ["martin"], "seed": 1}).status_code == 200


def test_포인트_초과는_422(client):
    r = client.post(
        "/runs",
        json={
            "lineup": ["martin", "aude", "thoma"],
            "allocations": {"martin": {"str_": 19}},
            "seed": 1,
        },
    )
    assert r.status_code == 422 and "18" in r.json()["detail"]


def test_없는_캐릭터는_422(client):
    r = client.post("/runs", json={"lineup": ["martin", "aude", "ghost"], "seed": 1})
    assert r.status_code == 422


def test_런_생성_후_스트림은_run_start_로_시작해_done_으로_끝난다(client):
    r = client.post("/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 8})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    with client.stream("GET", f"/runs/{run_id}/stream") as s:
        text = "".join(s.iter_text())
    events = _parse_sse(text)
    assert events[0]["event"] == "run_start" and events[-1]["event"] == "done"
    assert events[-2]["event"] == "run_end"
    kinds = {e["event"] for e in events}
    assert {"plan", "decision", "resolution", "mission_end"} <= kinds


def test_완료된_런은_저장되고_다시_읽힌다(client):
    run_id = client.post("/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 8}).json()[
        "run_id"
    ]
    body = _wait_done(client, run_id)
    assert body["events"][0]["kind"] == "run_start"
    # 저장소에서도 읽힌다
    assert client.get("/runs").json()["runs"][0]["run_id"] == run_id


def test_리플레이는_같은_판을_다시_돌린다(client):
    run_id = client.post("/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 8}).json()[
        "run_id"
    ]
    first = _wait_done(client, run_id)
    r = client.post(f"/runs/{run_id}/replay")
    assert r.status_code == 200 and r.json()["model"] == "replay"
    second = _wait_done(client, r.json()["run_id"])
    labels1 = [e["payload"].get("label") for e in first["events"] if e["kind"] == "decision"]
    labels2 = [e["payload"].get("label") for e in second["events"] if e["kind"] == "decision"]
    assert labels1 == labels2 and len(labels1) > 10


def test_없는_런은_404(client):
    assert client.get("/runs/zzz").status_code == 404


def test_시크릿이_설정되면_헤더_없이는_401(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKEND_SHARED_SECRET", "s3cret")
    app = build_app(
        store=JsonlRunStore(tmp_path), model_factory=lambda _n: Harness(FakeModel(), FakeModel())
    )
    c = TestClient(app)
    assert c.get("/roster/preset").status_code == 401
    assert c.get("/roster/preset", headers={"X-Backend-Secret": "s3cret"}).status_code == 200
    assert c.get("/healthz").status_code == 200  # healthz 는 열려 있다


def test_실험_결과가_없으면_404_이고_목록은_빈다(client):
    assert client.get("/experiments/e1").status_code == 404
    assert client.get("/experiments").json()["available"] == []
    assert client.get("/experiments/e9").status_code == 404


def test_실험_결과가_있으면_그대로_내려준다(tmp_path):
    import json as _json

    out = tmp_path / "out"
    out.mkdir()
    (out / "e1.json").write_text(_json.dumps({"experiment": "e1", "compositions": []}), "utf-8")
    app = build_app(
        store=JsonlRunStore(tmp_path),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        experiments_dir=out,
    )
    c = TestClient(app)
    assert c.get("/experiments").json()["available"] == ["e1"]
    assert c.get("/experiments/e1").json()["experiment"] == "e1"


# ─── B단계 인터미션 ────────────────────────────────────────────────────


def _two_mission_client(tmp_path, timeout=5.0):
    app = build_app(
        store=JsonlRunStore(tmp_path),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        directive_timeout=timeout,
    )
    return TestClient(app)


def test_두_판이면_인터미션에서_입력을_기다린다(tmp_path):
    """기획서 §7.1 — 1판 → 인터미션 → 2판. 인터미션이 있어야 인과가 닫힌다."""
    c = _two_mission_client(tmp_path)
    run_id = c.post(
        "/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 3, "missions": 2}
    ).json()["run_id"]

    # 인터미션에 닿을 때까지 기다렸다가 지시를 보낸다.
    t0 = time.time()
    while time.time() - t0 < 10:
        events = c.get(f"/runs/{run_id}").json()["events"]
        if any(e["kind"] == "intermission_start" for e in events):
            break
        time.sleep(0.05)
    r = c.post(
        f"/runs/{run_id}/directives",
        json={"directives": {"thoma": "rest", "martin": "train"}, "growth": {"thoma": {"agi": 3}}},
    )
    assert r.status_code == 200

    body = _wait_done(c, run_id)
    kinds = [e["kind"] for e in body["events"]]
    assert kinds.count("mission_start") == 2, "2판이 시작되지 않았다"
    assert "train_result" in kinds and "growth_points" in kinds
    지시 = [e["payload"]["category"] for e in body["events"] if e["kind"] == "directive"]
    assert "rest" in 지시


def test_인터미션이_아닐_때의_지시는_409(tmp_path):
    c = _two_mission_client(tmp_path)
    run_id = c.post("/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 8}).json()[
        "run_id"
    ]
    r = c.post(f"/runs/{run_id}/directives", json={"directives": {}})
    assert r.status_code in (409, 404)


def test_응답이_없어도_기본값으로_판이_이어진다(tmp_path):
    """화면이 죽어도 스트림이 영원히 열려 있으면 안 된다."""
    c = _two_mission_client(tmp_path, timeout=0.3)
    run_id = c.post(
        "/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 3, "missions": 2}
    ).json()["run_id"]
    body = _wait_done(c, run_id, timeout=20)
    kinds = [e["kind"] for e in body["events"]]
    assert kinds.count("mission_start") == 2
    지시 = {e["payload"]["category"] for e in body["events"] if e["kind"] == "directive"}
    assert 지시 == {"train"}, "기본값은 전원 훈련이어야 한다"


def test_잘못된_성장_분배는_판을_죽이지_않는다(tmp_path):
    c = _two_mission_client(tmp_path)
    run_id = c.post(
        "/runs", json={"lineup": ["martin", "aude", "thoma"], "seed": 3, "missions": 2}
    ).json()["run_id"]
    t0 = time.time()
    while time.time() - t0 < 10:
        if any(
            e["kind"] == "intermission_start" for e in c.get(f"/runs/{run_id}").json()["events"]
        ):
            break
        time.sleep(0.05)
    c.post(f"/runs/{run_id}/directives", json={"growth": {"thoma": {"agi": 99}}})
    body = _wait_done(c, run_id, timeout=20)
    assert body["error"] is None
    rejected = [
        e
        for e in body["events"]
        if e["kind"] == "intermission_start" and e["payload"].get("rejected")
    ]
    assert rejected and "찍으려 한다" in rejected[0]["payload"]["rejected"]


def test_동시_런_상한을_넘으면_429(tmp_path):
    """배포하면 누구나 POST /runs 를 반복할 수 있다 — 런마다 스레드가 생긴다."""
    app = build_app(
        store=JsonlRunStore(tmp_path),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        max_active_runs=1,
        directive_timeout=30,
    )
    c = TestClient(app)
    body = {"lineup": ["martin", "aude", "thoma"], "seed": 3, "missions": 2}
    first = c.post("/runs", json=body)
    assert first.status_code == 200
    second = c.post("/runs", json=body)
    # 첫 런이 인터미션에서 입력을 기다리는 동안 두 번째는 거절된다.
    if second.status_code == 200:
        _wait_done(c, first.json()["run_id"], timeout=40)
        return
    assert second.status_code == 429 and "동시에" in second.json()["detail"]


def test_완료된_런은_상한을_먹지_않는다(tmp_path):
    app = build_app(
        store=JsonlRunStore(tmp_path),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        max_active_runs=1,
    )
    c = TestClient(app)
    body = {"lineup": ["martin", "aude", "thoma"], "seed": 8}
    run_id = c.post("/runs", json=body).json()["run_id"]
    _wait_done(c, run_id)
    assert c.post("/runs", json=body).status_code == 200


# ─── 뿔피리 (기획서 v3 §8.2) ────────────────────────────────────────────


def test_HTTP_로_분_뿔피리가_실제로_판을_끝낸다(paced_client):
    """`blow_horn → horn_signal → 러너` 왕복을 지나는 유일한 테스트.

    QA 재검 2026-09-09 R14: 전에는 이 자리의 테스트 둘이 **100% 공허**였다 —
    판이 0.1초에 끝나 첫 요청이 20회 중 0회만 200 을 받았고, `남은 == []` 이면
    `[] == []` 로 통과했다. 그래서 판 시작 창의 신호 증발(R2)이 살아남았다.
    """
    client = paced_client
    run_id = client.post("/runs", json={"lineup": ["martin", "aude", "agnes"], "seed": 5}).json()[
        "run_id"
    ]
    assert _wait_kind(client, run_id, "mission_start"), "판이 시작되지 않았다"

    r = client.post(f"/runs/{run_id}/horn")
    assert r.status_code == 200, r.text
    assert r.json()["horn_left"] == 2, "충전이 안 닳았다"

    # 이미 울린 신호가 안 닿았으면 또 받지 않는다 — 횟수만 닳고 효과는 하나다.
    두번째 = client.post(f"/runs/{run_id}/horn")
    assert 두번째.status_code == 409 and "이미" in 두번째.json()["detail"]

    horn = _wait_kind(client, run_id, "horn")
    assert horn is not None, "200 을 받았는데 뿔피리가 울리지 않았다"
    assert horn["payload"]["delivered"] is True
    _wait_done(client, run_id)
    끝 = [e for e in client.get(f"/runs/{run_id}").json()["events"] if e["kind"] == "mission_end"]
    assert 끝[0]["payload"]["grade"] == "withdraw", "뿔피리로 끝난 판은 「철수」다"


def test_없는_런에_뿔피리를_불면_404(client):
    assert client.post("/runs/nope/horn").status_code == 404


# ─── 회수 결정 (기획서 v3 §6.8) ─────────────────────────────────────────


def test_회수_결정을_안_받을_때_보내면_409(client):
    run_id = client.post("/runs", json={"lineup": ["martin", "aude", "agnes"], "seed": 5}).json()[
        "run_id"
    ]
    r = client.post(f"/runs/{run_id}/recovery", json={"pay": ["thoma"]})
    assert r.status_code in (409, 404)


def test_없는_런에_회수_결정을_보내면_404(client):
    assert client.post("/runs/nope/recovery", json={"pay": []}).status_code == 404


def test_전투_중이_아니면_뿔피리를_받지_않는다(client):
    """QA 2026-09-09 T1 — 인터미션 훅이 플래그를 먼저 지우고 LLM 을 돌려
    그 사이 창으로 들어온 신호가 다음 판 1턴에 터졌다(재현 2회).

    이제 판 경계를 러너가 알려 준다(BattleGateFn). 판이 끝난 뒤엔 못 분다.
    """
    run_id = client.post("/runs", json={"lineup": ["martin", "aude", "agnes"], "seed": 5}).json()[
        "run_id"
    ]
    _wait_done(client, run_id)
    r = client.post(f"/runs/{run_id}/horn")
    assert r.status_code == 409
    assert "끝난" in r.json()["detail"] or "전투 중이 아니다" in r.json()["detail"]


def test_뿔피리_세_번을_쓰면_네_번째는_거부된다():
    """QA 2026-09-09 C5 — HTTP 로는 한 판에 한 번밖에 못 불어 상한 분기를
    어떤 테스트도 지나지 않았다. 세션을 직접 돌려 단위로 잰다.
    """
    from apps.arena.adapter.inbound.api.v1.arena_router import RunSession
    from apps.arena.domain.constants.balance import HORN_CHARGES

    s = RunSession("r", None)  # type: ignore[arg-type]
    s.in_battle.set()
    for i in range(HORN_CHARGES):
        assert s.horn_left == HORN_CHARGES - i
        s.blow_horn()
        assert s.horn_signal(6, 5) is True  # 판 중간 턴 — 신호가 닿는다
    assert s.horn_left == 0
    # 네 번째. 라우터가 이 문장을 그대로 409 로 실어 보낸다.
    assert s.horn_refusal() == "뿔피리를 다 썼다"


def test_뿔피리_거절_사유_넷을_모두_지난다():
    """QA 2026-09-09 C5 — 거절 분기가 라우터 안에 있어 HTTP 로는 한 판에 한 번밖에
    못 불어(불면 판이 끝난다) 어떤 테스트도 지나지 못했다. 세션이 판단하므로
    이제 넷을 다 지난다.
    """
    from apps.arena.adapter.inbound.api.v1.arena_router import RunSession

    s = RunSession("r", None)  # type: ignore[arg-type]
    assert s.horn_refusal() == "지금은 전투 중이 아니다"

    s.in_battle.set()
    assert s.horn_refusal() is None

    s.blow_horn()
    assert s.horn_refusal() == "이미 뿔피리가 울렸다"

    s.horn_signal(6, 5)  # 신호가 닿았다
    s.horn_left = 0
    assert s.horn_refusal() == "뿔피리를 다 썼다"

    s.horn_left = 3
    s.done.set()
    assert s.horn_refusal() == "이미 끝난 판이다"


def test_판이_끝나면_안_닿은_신호를_버린다():
    """묵은 신호는 **판 경계**에서 버린다 — 게이트가 그 자리를 정확히 안다.

    전에는 "1턴이면 버린다" 였는데, `gate(True)` 가 `make_plan`(모델 호출) 앞에서
    열리므로 그 사이에 들어온 **정상** 신호까지 먹었다 — 200 을 받고 충전이
    닳는데 아무 일도 안 일어났다(QA 재검 2026-09-09 P1-C).
    """
    from apps.arena.adapter.inbound.api.v1.arena_router import RunSession

    s = RunSession("r", None)  # type: ignore[arg-type]
    s.in_battle.set()
    s.blow_horn()
    s.close_battle()
    assert s.horn_signal(6, 1) is False, "묵은 신호가 다음 판에 터졌다"

    # 판이 열린 채 1턴이면 그건 **정상 입력**이다. 먹지 않는다.
    s.in_battle.set()
    s.blow_horn()
    assert s.horn_signal(6, 1) is True, "판 시작 창의 정상 신호를 먹었다"


def test_회수_요청의_오타는_거절된다(client):
    """QA 2026-09-09 T7 — `pay` 에 기본값이 있어 `{"payy": [...]}` 오타가 200 을
    받고 큐를 소비했다. 전원 영구 상실로 확정되고 **되돌릴 방법이 없었다.**
    """
    run_id = client.post("/runs", json={"lineup": ["martin", "aude"], "seed": 5}).json()["run_id"]
    assert client.post(f"/runs/{run_id}/recovery", json={"payy": ["aude"]}).status_code == 422
    assert client.post(f"/runs/{run_id}/recovery", json={}).status_code == 422


def test_리플레이_런에서는_뿔피리를_받지_않는다():
    """QA 재검 2026-09-09 P1-D — 리플레이는 `session.horn_signal` 을 아무도 부르지
    않는데 `horn_refusal()` 이 수락했다. 소비자가 없어 신호가 영원히 남고 이후
    모든 요청이 409 「이미 뿔피리가 울렸다」로 막혔다 — 200 을 받고 충전이 닳은 뒤에.
    """
    from apps.arena.adapter.inbound.api.v1.arena_router import RunSession

    s = RunSession("r", None)  # type: ignore[arg-type]
    s.in_battle.set()
    s.replaying = True
    assert s.horn_refusal() == "리플레이는 다시 불 수 없다 — 녹화된 판을 그대로 되감는다"


@pytest.mark.parametrize(
    "body",
    [
        {"lineup": ["martin"], "orchestrater": False},  # 감독이 켜진 채 돈다
        {"lineup": ["martin"], "adaption": False},
        {"lineup": ["martin"], "mission": 2},  # 1판만 돈다
        {"lineup": ["martin"], "allocation": {"martin": {"str_": 4}}},  # 배분이 무시된다
    ],
    ids=["orchestrater", "adaption", "mission", "allocation"],
)
def test_출정_요청의_오타는_거절된다(client, body):
    """QA 재검 2026-09-09 R18 — 오타가 200 을 받고 **반대 팔로** 돌았다.
    A/B 토글이 조용히 뒤집히면 실험이 재는 것이 무엇인지 알 수 없다(기획서 §3.1).
    """
    assert client.post("/runs", json=body).status_code == 422

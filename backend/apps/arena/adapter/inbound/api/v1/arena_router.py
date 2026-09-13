"""FastAPI 앱 — 얇은 HTTP 계층 (설계 §11.1). 도메인 판단을 하지 않는다.

런은 백그라운드 스레드에서 돌고 이벤트를 큐에 넣는다. /runs/{id}/stream 이 큐를
SSE 로 흘리고, 끝나면 저장소에 남긴다. 완료된 런의 스트림은 저장된 이벤트를
한 번에 흘린다 — 새로고침해도 같은 화면이 나온다.
"""

import json
import logging
import queue
import secrets
import threading
import time
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from apps.arena.adapter.inbound.api.schemas.arena_schema import (
    CreateRunRequest,
    CreateRunResponse,
    DirectivesRequest,
    RecoveryRequest,
)
from apps.arena.adapter.outbound.strategies.dice import SeededDice
from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.adapter.outbound.strategies.llm.paced import PacedModel
from apps.arena.adapter.outbound.strategies.llm.replay import ReplayModel
from apps.arena.adapter.outbound.strategies.llm.select import pace_seconds
from apps.arena.app.use_cases.intermission import (
    IntermissionInput,
    IntermissionState,
    run_intermission,
)
from apps.arena.app.use_cases.runner import ModelFactory, RunRecord, run
from apps.arena.domain.constants.balance import (
    FREE_POINTS,
    HORN_CHARGES,
    MAX_CALLS,
    STAT_BASE,
    STAT_MAX,
)
from apps.arena.domain.entities.trace_event import TraceEvent, Tracer
from apps.arena.domain.entities.types import RunConfig
from apps.arena.domain.ports.ports import RunStore
from apps.arena.domain.services.rules.disposition import describe, mbti_label
from content.cards import CARDS
from content.classes import CLASSES, choose_build
from content.events import pool_for
from content.missions import MISSIONS_A, MISSIONS_SINGLE
from content.party import apply_direction, build_party
from content.roster import PRESET_ALLOCATIONS, PRESET_ROSTER
from core.security import 시크릿_검사

logger = logging.getLogger("rpg.api")

_DONE = object()


class RunSession:
    """진행 중인 런 하나. 이벤트 큐 + 완료 플래그 + 인터미션 입력 대기."""

    def __init__(self, run_id: str, config: RunConfig) -> None:
        self.run_id = run_id
        self.config = config
        self.events: list[TraceEvent] = []
        self.queue: queue.Queue[Any] = queue.Queue()
        self.done = threading.Event()
        self.error: str | None = None
        # 인터미션에서 유저 입력을 기다리는 자리. 화면이 응답하지 않아도 판은
        # 이어져야 하므로 대기에 상한을 둔다(설계 §11.1).
        self.directives: queue.Queue[DirectivesRequest] = queue.Queue()
        self.awaiting_input = threading.Event()
        # 뿔피리 — 유저의 유일한 전투 중 개입(기획서 v3 §8.2). 계약 기간 3회.
        # 잔여 횟수는 여기가 센다. core 는 "지금 울렸나" 만 답받는다.
        self.horn_left = HORN_CHARGES
        self.horn_pending = threading.Event()
        # 뿔피리는 **판 안에서만** 유효하다(기획서 v3 §8.2). 세션 플래그만으로는
        # mission_end↔인터미션 훅 사이, 그리고 훅이 플래그를 지운 뒤 LLM 이 도는
        # 몇 초 동안 창이 열린다 — 그때 받은 신호가 다음 판 1턴에 터진다
        # (QA 2026-09-09 T1·C3·J14, 재현 2회).
        self.in_battle = threading.Event()
        # 리플레이 런은 유저 입력을 **녹화에서** 재생한다. 세션 훅을 아무도
        # 부르지 않으므로 여기서 받은 신호는 소비자가 없어 영원히 남고, 이후
        # 모든 요청이 "이미 뿔피리가 울렸다" 로 막힌다(QA 재검 2026-09-09 P1-D).
        self.replaying = False
        # 회수 결정 — 끌려간 대원을 다시 데려올 것인가(기획서 v3 §6.8).
        # 화면이 답하지 않으면 미지불이다. 기한을 넘기면 자동 미지불이라는
        # 규칙이 그대로 기본값이 된다.
        self.recovery: queue.Queue[set[str]] = queue.Queue()
        self.awaiting_recovery = threading.Event()
        self.finished_at: float | None = None

    def horn_refusal(self) -> str | None:
        """지금 뿔피리를 받을 수 없다면 그 이유. 받을 수 있으면 None.

        라우터가 아니라 세션이 판단한다 — HTTP 로는 한 판에 한 번밖에 못 불어
        (불면 그 판이 끝난다) 상한·중복 분기를 어떤 테스트도 지나지 못했다
        (QA 2026-09-09 C5). 판단이 세션에 있으면 단위로 전부 지날 수 있다.
        """
        if self.done.is_set():
            return "이미 끝난 판이다"
        if self.replaying:
            return "리플레이는 다시 불 수 없다 — 녹화된 판을 그대로 되감는다"
        if self.horn_left <= 0:
            return "뿔피리를 다 썼다"
        # 이미 울린 신호가 아직 안 닿았다. 또 받으면 횟수만 닳고 효과는 하나다.
        if self.horn_pending.is_set():
            return "이미 뿔피리가 울렸다"
        # 전투 중 개입이다(기획서 v3 §8.2). 인터미션이나 회수 결정 중에 받으면
        # 신호가 다음 판 첫 턴까지 묵혀 있다가 엉뚱한 자리에서 터진다.
        if not self.in_battle.is_set():
            return "지금은 전투 중이 아니다"
        return None

    def blow_horn(self) -> None:
        self.horn_left -= 1
        self.horn_pending.set()

    def close_battle(self) -> None:
        """판이 끝났다. 아직 안 닿은 신호를 여기서 버린다.

        묵은 신호를 "1턴이면 버린다" 로 막던 때가 있었는데, `gate(True)` 가
        `make_plan`(모델 호출) **앞에서** 열리므로 그 사이에 들어온 **정상**
        신호까지 먹었다 — 200 을 받고 충전이 닳는데 아무 일도 안 일어났다
        (QA 재검 2026-09-09 P1-C). 판 경계는 게이트가 정확히 안다.
        """
        self.in_battle.clear()
        self.horn_pending.clear()

    def horn_signal(self, mission: int, turn: int) -> bool:
        """턴 시작에 core 가 묻는다. 울렸으면 한 번만 참을 준다.

        회차는 리플레이 훅이 쓴다 — 세션은 "지금 판" 만 알면 되므로 안 본다.
        """
        if self.horn_pending.is_set():
            self.horn_pending.clear()
            return True
        return False

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
        self.queue.put(event)


# 인터미션에서 유저 지시를 기다리는 상한(초). 넘으면 기본값(전원 훈련·분배 없음)
# 으로 간다 — 판이 멈춘 채로 남으면 스트림이 영원히 열려 있다.
DIRECTIVE_TIMEOUT = 60.0

# 동시에 도는 런의 상한. 배포하면 누구나 POST /runs 를 반복할 수 있고, 런마다
# 스레드 하나와 이벤트 전량이 메모리에 남는다. MAX_CALLS 는 런 **하나 안의**
# 호출만 막는다(QA 라운드 2).
MAX_ACTIVE_RUNS = 8
# 완료된 런을 세션에 남겨 두는 시간(초). 스트림이 끝을 읽고 화면이 결과로
# 넘어갈 시간만 있으면 된다 — 기록은 저장소에 있다.
SESSION_TTL = 120.0


def build_app(
    store: RunStore,
    model_factory: ModelFactory,
    model_name: str = "fake",
    experiments_dir: Path | None = None,
    directive_timeout: float = DIRECTIVE_TIMEOUT,
    max_active_runs: int = MAX_ACTIVE_RUNS,
) -> FastAPI:
    app = FastAPI(title="rpg-arena", docs_url=None, redoc_url=None, openapi_url=None)
    sessions: dict[str, RunSession] = {}
    guard = [Depends(시크릿_검사)]

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "model": model_name,
            "max_calls": MAX_CALLS,
            "active_runs": len(sessions),
        }

    @app.get("/roster/preset", dependencies=guard)
    def roster_preset() -> dict[str, Any]:
        out = []
        for c in PRESET_ROSTER:
            alloc = PRESET_ALLOCATIONS[c.id]
            cfg = _config(
                seed=0,
                lineup=(c.id,),
                allocations={c.id: alloc},
                classes={},
                genders={},
                orchestrator=True,
                adaptation=True,
                missions=MISSIONS_SINGLE,
            )
            directed = apply_direction(cfg, c.id)
            build = choose_build(directed)
            out.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "gender": c.gender,
                    "body": asdict(c.body),
                    "weight_class": c.body.weight_class,
                    "base_stats": c.stats.as_dict(),
                    "recommended": alloc,
                    "class": c.char_class,
                    "disposition": c.disposition.as_dict(),
                    "disposition_text": describe(c.disposition),
                    "mbti": mbti_label(c.disposition),
                    "life": c.life.note,
                    "backstory": c.backstory,
                    "build_preview": {
                        "weapon": build.weapon.name,
                        "armor": build.armor.name,
                        "rationale": build.rationale,
                    },
                }
            )
        return {
            "roster": out,
            "classes": [
                {"key": k, "label": v.label, "primary": v.primary} for k, v in CLASSES.items()
            ],
            "free_points": FREE_POINTS,
            "stat_base": STAT_BASE,
            # 상한도 서버가 준다 — 화면이 20 을 하드코딩하고 있었다(수치 단일 출처).
            "stat_max": STAT_MAX,
            "lineup_size": MISSIONS_A[0].lineup_max,
            "horn_charges": HORN_CHARGES,
            # 화면이 미션 이름을 하드코딩하면 콘텐츠가 바뀔 때 조용히 거짓말한다
            # (QA 2026-09-09 U1·T3 — 로스터가 삭제된 "폐광의 군주" 를 광고했다).
            "missions": {
                1: [{"no": m.no, "name": m.name, "enemy": m.enemy.name} for m in MISSIONS_SINGLE],
                2: [{"no": m.no, "name": m.name, "enemy": m.enemy.name} for m in MISSIONS_A],
            },
        }

    @app.post("/runs", response_model=CreateRunResponse, dependencies=guard)
    def create_run(req: CreateRunRequest) -> CreateRunResponse:
        seed = req.seed if req.seed is not None else secrets.randbelow(1_000_000)
        cfg = _config(
            seed=seed,
            lineup=tuple(req.lineup),
            allocations=req.allocations,
            classes=req.classes,
            genders=req.genders,
            orchestrator=req.orchestrator,
            adaptation=req.adaptation,
            missions=MISSIONS_A if req.missions == 2 else MISSIONS_SINGLE,
        )
        try:
            members = build_party(cfg)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        _reap_sessions()
        active = sum(1 for s in sessions.values() if not s.done.is_set())
        if active >= max_active_runs:
            raise HTTPException(
                status_code=429,
                detail=f"지금 {active}판이 동시에 돌고 있다. 잠시 뒤 다시 시도한다",
            )
        run_id = secrets.token_hex(6)
        session = RunSession(run_id, cfg)
        sessions[run_id] = session
        _start(session, members, model_factory)
        return CreateRunResponse(run_id=run_id, seed=seed, model=model_name)

    @app.get("/runs/{run_id}/stream", dependencies=guard)
    def stream(run_id: str) -> StreamingResponse:
        session = sessions.get(run_id)
        if session is not None:
            return StreamingResponse(
                _sse_live(session),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        record = _load(run_id)
        return StreamingResponse(_sse_static(record.events), media_type="text/event-stream")

    @app.get("/runs/{run_id}", dependencies=guard)
    def get_run(run_id: str) -> dict[str, Any]:
        session = sessions.get(run_id)
        if session is not None:
            return {
                "run_id": run_id,
                "done": session.done.is_set(),
                "error": session.error,
                "events": [asdict(e) for e in session.events],
            }
        record = _load(run_id)
        return {
            "run_id": run_id,
            "done": True,
            "error": None,
            "events": [asdict(e) for e in record.events],
        }

    @app.post("/runs/{run_id}/replay", response_model=CreateRunResponse, dependencies=guard)
    def replay(run_id: str) -> CreateRunResponse:
        """녹화된 판을 Replay 모델로 다시 돌린다 — 모델 호출 0(기획서 §11.3)."""
        record = _load(run_id)
        cfg = _config_from_payload(record.config)
        members = build_party(cfg)
        new_id = secrets.token_hex(6)
        session = RunSession(new_id, cfg)
        sessions[new_id] = session
        events = list(record.events)
        # 리플레이도 같은 속도로 흐른다 — 데모에서 판을 눈으로 따라갈 수 있어야
        # 한다. 다만 뿔피리는 받지 않는다(녹화를 되감는 중이다 — `replaying`).
        pace = pace_seconds("fake")

        # **유저 입력도 재생한다**(QA 2026-09-09 J1). 모델 판단만 되감고 뿔피리·회수를
        # 비워 두면 원본이 「철수」로 끝난 판이 리플레이에서는 「패배」로 끝난다 —
        # "같은 시드 = 같은 판" 이 유저 입력이 낀 판에서 깨진다.
        # 재료는 이미 트레이스에 있다: horn 은 turn, recovery 는 member·paid.
        # **원래 분 턴**으로 되돌린다. `turn` 은 신호가 **닿은** 턴이라, 전령관이
        # 없는 편성에서는 리플레이가 이미 늦춰진 턴에 다시 불고 러너가 또 한 턴을
        # 민다 — 왕복할 때마다 1턴씩 밀린다(QA 재검 2026-09-09 P0-B).
        # 회차도 함께 맞춘다: 안 그러면 6회차에 분 것이 7회차에서 터진다(P0-A).
        horn_turns = {
            (e.mission, e.payload.get("delayed_from") or e.payload.get("turn"))
            for e in events
            if e.kind == "horn"
        }
        paid_members = {
            e.payload.get("member")
            for e in events
            if e.kind == "recovery" and e.payload.get("paid")
        }
        fired: set[tuple[int, int]] = set()

        def replay_horn(mission: int, turn: int) -> bool:
            if (mission, turn) in horn_turns and (mission, turn) not in fired:
                fired.add((mission, turn))
                return True
            return False

        def replay_recovery(ids: list[str], _costs: dict[str, int], _t: Tracer) -> set[str]:
            return {i for i in ids if i in paid_members}

        session.replaying = True
        _start(
            session,
            members,
            lambda _n: Harness(
                PacedModel(ReplayModel(events, FakeModel()), pace)
                if pace
                else ReplayModel(events, FakeModel()),
                FakeModel(),
            ),
            horn=replay_horn,
            recovery_fn=replay_recovery,
        )
        return CreateRunResponse(run_id=new_id, seed=cfg.seed, model="replay")

    @app.post("/runs/{run_id}/directives", dependencies=guard)
    def directives(run_id: str, req: DirectivesRequest) -> dict[str, Any]:
        """인터미션 입력 — 육성 지시 + 성장 포인트 분배(기획서 §5·§5.1)."""
        session = sessions.get(run_id)
        if session is None:
            raise HTTPException(status_code=404, detail="진행 중인 런이 아니다")
        if not session.awaiting_input.is_set():
            raise HTTPException(status_code=409, detail="지금은 인터미션이 아니다")
        session.directives.put(req)
        return {"status": "accepted"}

    @app.post("/runs/{run_id}/recovery", dependencies=guard)
    def recovery(run_id: str, req: RecoveryRequest) -> dict[str, Any]:
        """회수 결정 — 지불할 대원 목록(기획서 v3 §6.8).

        A단계는 결정을 기록하는 데까지다. 회수 미션 개방은 B단계다.
        """
        session = sessions.get(run_id)
        if session is None:
            raise HTTPException(status_code=404, detail="진행 중인 런이 아니다")
        if not session.awaiting_recovery.is_set():
            raise HTTPException(status_code=409, detail="지금은 회수 결정을 받지 않는다")
        session.recovery.put(set(req.pay))
        return {"status": "accepted"}

    @app.post("/runs/{run_id}/horn", dependencies=guard)
    def horn(run_id: str) -> dict[str, Any]:
        """뿔피리 — 즉시 이탈(기획서 v3 §8.2). 계약 기간 3회.

        전멸은 피하지만 목표는 실패하고 보수는 없다. 부는 것은 전령관이다 —
        나팔을 든 사람이 서 있지 않으면 신호가 한 턴 늦는다.
        지연은 러너가 판단한다(`runner.herald_present`).
        """
        session = sessions.get(run_id)
        if session is None:
            raise HTTPException(status_code=404, detail="진행 중인 런이 아니다")
        거절 = session.horn_refusal()
        if 거절:
            raise HTTPException(status_code=409, detail=거절)
        session.blow_horn()
        return {"status": "accepted", "horn_left": session.horn_left}

    @app.get("/runs", dependencies=guard)
    def recent(limit: int = 20) -> dict[str, Any]:
        return {"runs": store.list_recent(min(limit, 50))}

    @app.get("/experiments", dependencies=guard)
    def experiments() -> dict[str, Any]:
        """돌아 있는 실험 목록. 화면이 무엇을 그릴 수 있는지 먼저 묻는다."""
        if experiments_dir is None or not experiments_dir.exists():
            return {"available": []}
        return {"available": sorted(p.stem for p in experiments_dir.glob("*.json"))}

    @app.get("/experiments/{name}", dependencies=guard)
    def experiment(name: str) -> dict[str, Any]:
        if name not in ("e1", "e2", "e3", "e4"):
            raise HTTPException(status_code=404, detail=f"모르는 실험: {name}")
        # experiments_dir 가 없으면 "실험 결과가 없다" 다. 상대 경로로 기본값을 두면
        # 테스트가 프로세스의 작업 디렉토리에 따라 결과를 주웠다 놓쳤다 한다.
        path = (experiments_dir / f"{name}.json") if experiments_dir else None
        if path is None or not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"{name.upper()} 결과가 아직 없다. "
                f"backend 에서 `uv run python -m eval.run -e {name}` 을 돌린다",
            )
        return json.loads(path.read_text(encoding="utf-8"))

    # ─── 내부 ──────────────────────────────────────────────────────────

    def _reap_sessions() -> None:
        """끝난 지 오래된 세션을 치운다.

        예전에는 완료마다 threading.Timer 를 하나씩 띄웠다 — 런이 끝나지 않으면
        영영 남았고, 타이머 스레드도 함께 늘었다. 새 런을 만들 때 훑는다.
        """
        now = time.monotonic()
        for rid, s in list(sessions.items()):
            if s.done.is_set() and s.finished_at and now - s.finished_at > SESSION_TTL:
                sessions.pop(rid, None)

    def _load(run_id: str) -> RunRecord:
        try:
            record = store.load(run_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if record is None:
            raise HTTPException(status_code=404, detail="그런 런이 없다")
        return record

    def _start(
        session: RunSession,
        members: Any,
        factory: ModelFactory,
        horn: Any = None,
        recovery_fn: Any = None,
    ) -> None:
        def work() -> None:
            try:
                intermission = _intermission_for(session)
                record = run(
                    session.run_id,
                    session.config,
                    members,
                    factory,
                    SeededDice,
                    sink=session,
                    intermission=intermission,
                    horn=horn or session.horn_signal,
                    recovery=recovery_fn or _recovery_for(session),
                    card_pool=CARDS,
                    gate=lambda on, s=session: s.in_battle.set() if on else s.close_battle(),
                )
                try:
                    store.save(record)
                except Exception as e:  # noqa: BLE001 — 저장 실패가 화면을 끊으면 안 된다
                    logger.exception("런 저장 실패 %s", session.run_id)
                    # 스트림은 정상으로 끝나는데 세션이 지워지면 방금 본 판이
                    # 사라진다. 그 사실을 화면에 알린다(QA 라운드 2).
                    session.error = f"기록을 저장하지 못했다: {type(e).__name__}: {e}"
            except Exception as e:  # noqa: BLE001
                logger.exception("런 실패 %s", session.run_id)
                session.error = f"{type(e).__name__}: {e}"
            finally:
                session.done.set()
                session.finished_at = time.monotonic()
                session.queue.put(_DONE)

        threading.Thread(target=work, name=f"run-{session.run_id}", daemon=True).start()

    def _recovery_for(session: RunSession) -> Any:
        """회수 결정 훅. 화면의 답을 기다렸다가 지불 목록을 돌려준다."""

        def hook(ids: list[str], costs: dict[str, int], tracer: Tracer) -> set[str]:
            session.awaiting_recovery.set()
            # **값을 보여주고 묻는다.** 전에는 비용을 받아 그대로 버려서, 유저가
            # 얼마인지 모른 채 결정했다(QA 2026-09-09 L·U8). 남은 시간도 함께
            # 준다 — 답하지 않으면 자동 미지불이라 기한이 곧 결정이다.
            tracer.emit(
                "recovery",
                {
                    "awaiting_input": True,
                    "members": list(ids),
                    "costs": dict(costs),
                    "timeout_s": directive_timeout,
                },
            )
            try:
                return session.recovery.get(timeout=directive_timeout)
            except queue.Empty:
                return set()  # 기한을 넘기면 자동 미지불(기획서 v3 §6.8)
            finally:
                session.awaiting_recovery.clear()

        return hook

    def _intermission_for(session: RunSession) -> Any:
        """인터미션 훅. 유저 입력을 기다렸다가 core 의 인터미션을 돌린다."""
        state = IntermissionState()

        def hook(members, result, model, dice, tracer):  # type: ignore[no-untyped-def]
            session.awaiting_input.set()
            # 화면에게 "지금 입력받는다" 를 알린다. 이 이벤트가 없으면 스트림을
            # 보는 쪽은 판이 멈춘 이유를 알 수 없다.
            tracer.emit(
                "intermission_start",
                {
                    "awaiting_input": True,
                    "after_outcome": result.outcome,
                    "party": [c.id for c, _, _ in members],
                    "timeout_s": directive_timeout,
                },
            )
            try:
                req = session.directives.get(timeout=directive_timeout)
                user = IntermissionInput(directives=dict(req.directives), growth=dict(req.growth))
            except queue.Empty:
                user = IntermissionInput()
            finally:
                session.awaiting_input.clear()
            try:
                return run_intermission(
                    members, result.outcome, user, pool_for, model, dice, tracer, state
                )
            except ValueError as e:
                # 유저 입력이 규칙을 어겼다(포인트 초과 등). 판을 죽이지 않고
                # 기본값으로 간다 — 그 사실을 트레이스에 남긴다.
                logger.warning("인터미션 입력 거부 %s: %s", session.run_id, e)
                tracer.emit("intermission_start", {"rejected": str(e), "fallback": True})
                return run_intermission(
                    members,
                    result.outcome,
                    IntermissionInput(),
                    pool_for,
                    model,
                    dice,
                    tracer,
                    state,
                )

        return hook

    return app


def _sse(event: TraceEvent) -> str:
    return f"event: {event.kind}\ndata: {json.dumps(asdict(event), ensure_ascii=False)}\n\n"


def _sse_live(session: RunSession) -> Iterator[str]:
    # 이미 지나간 이벤트부터 — 중간에 접속해도 처음부터 본다.
    sent = 0
    idle = 0
    while True:
        while sent < len(session.events):
            yield _sse(session.events[sent])
            sent += 1
        if session.done.is_set() and sent >= len(session.events):
            break
        try:
            # 짧게 기다린다. 종료는 done 플래그가 판정하고 큐는 깨우는 신호일
            # 뿐이다 — 센티널을 한 명만 집어가서 둘째 구독자의 done 이 15초
            # 늦던 문제를 없앤다(QA 라운드 2).
            item = session.queue.get(timeout=1.0)
        except queue.Empty:
            idle += 1
            if idle >= 15:
                idle = 0
                yield ": keepalive\n\n"
            continue
        idle = 0
        if item is _DONE:
            # 센티널을 다시 넣어 다른 구독자도 즉시 깨어나게 한다.
            session.queue.put(_DONE)
            while sent < len(session.events):
                yield _sse(session.events[sent])
                sent += 1
            break
    if session.error:
        yield f"event: error\ndata: {json.dumps({'error': session.error}, ensure_ascii=False)}\n\n"
    yield "event: done\ndata: {}\n\n"


def _sse_static(events: list[TraceEvent]) -> Iterator[str]:
    for e in events:
        yield _sse(e)
    yield "event: done\ndata: {}\n\n"


def _config(
    seed: int,
    lineup: tuple[str, ...],
    allocations: dict,
    classes: dict,
    genders: dict,
    orchestrator: bool,
    adaptation: bool,
    missions: tuple,
) -> RunConfig:
    return RunConfig(
        seed=seed,
        lineup=lineup,
        allocations=allocations,
        classes=classes,
        genders=genders,
        orchestrator_on=orchestrator,
        adaptation_on=adaptation,
        missions=missions,
        intermission=len(missions) > 1,
    )


def _config_from_payload(p: dict[str, Any]) -> RunConfig:
    """run_start payload → RunConfig. 리플레이는 같은 설정이어야 같은 질문이 나온다.

    설정을 역산하지 않는다 — run_start 가 유저의 방향 결정을 그대로 싣는다.
    """
    return _config(
        seed=int(p["seed"]),
        lineup=tuple(p["lineup"]),
        allocations={k: dict(v) for k, v in (p.get("allocations") or {}).items()},
        classes=dict(p.get("classes") or {}),
        genders=dict(p.get("genders") or {}),
        orchestrator=bool(p["orchestrator_on"]),
        adaptation=bool(p["adaptation_on"]),
        missions=MISSIONS_A if p.get("mission_count", 1) == 2 else MISSIONS_SINGLE,
    )


def create_app() -> FastAPI:
    """uvicorn 진입점.

    `uv run uvicorn apps.arena.adapter.inbound.api.v1.arena_router:create_app --factory`
    """
    import os

    from apps.arena.adapter.outbound.repositories.jsonl_run_repository import JsonlRunStore
    from apps.arena.adapter.outbound.strategies.llm.select import build_harness, model_name_from_env

    runs_dir = Path(os.environ.get("RPG_RUNS_DIR", "runs"))
    return build_app(
        store=JsonlRunStore(runs_dir),
        model_factory=build_harness,
        model_name=model_name_from_env(),
        experiments_dir=Path(os.environ.get("RPG_EXPERIMENTS_DIR", "eval/out")),
    )

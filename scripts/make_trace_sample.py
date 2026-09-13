#!/usr/bin/env python3
"""docs/trace-samples/one-run.jsonl 을 만든다 — 파이썬과 프론트가 같이 읽는 계약 샘플.

backend/ 에서: uv run python ../scripts/make_trace_sample.py
시드·조합을 고정해 두어 다시 만들어도 같은 파일이 나온다(ts 제외).
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from apps.arena.adapter.outbound.strategies.harness.harness import Harness  # noqa: E402
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel  # noqa: E402
from content.cards import CARDS  # noqa: E402
from content.missions import MISSIONS_A  # noqa: E402
from content.party import build_party  # noqa: E402
from apps.arena.adapter.outbound.strategies.dice import SeededDice  # noqa: E402
from apps.arena.app.use_cases.runner import run  # noqa: E402
from apps.arena.domain.entities.trace_event import judgment_view  # noqa: E402
from apps.arena.domain.entities.types import RunConfig  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "trace-samples" / "one-run.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser(description="트레이스 계약 샘플 생성")
    # CI 가 프로세스 간 결정론을 재는 데 쓴다 — 파일을 건드리지 않고 표준출력으로.
    ap.add_argument(
        "--stdout",
        action="store_true",
        help="파일 대신 표준출력으로 판정 뷰를 낸다 (CI 의 프로세스 간 결정론 비교용)",
    )
    args = ap.parse_args()

    # 편성: 마르탱(중장병) · 오드(전령관) · 아녜스(약탈병). 아녜스에게 딸이 있어
    # 이탈 장면의 재료가 된다.
    #
    # 시드 8 은 v3 의 하이라이트가 **한 판에 다 나온다**: abandon · flee ·
    # replan_trigger · boss_adapt · summon · cards · casualty · recovery ·
    # boss_named · 방침 이탈. 밸런스를 튜닝하면 이 시드도 다시 골라야 한다
    # (`scripts/make_trace_sample.py` 를 돌리면 계약 테스트가 말해 준다).
    cfg = RunConfig(
        seed=8,
        lineup=("martin", "aude", "agnes"),
        allocations={},
        classes={},
        genders={},
        orchestrator_on=True,
        adaptation_on=True,
        missions=MISSIONS_A,
        intermission=False,
    )
    rec = run(
        "sample-one-run",
        cfg,
        build_party(cfg),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        dice_factory=SeededDice,
        clock=lambda: "2026-09-07T00:00:00.000+00:00",
        card_pool=CARDS,
        # 회수 결정도 샘플에 넣는다 — 아무도 안 되찾는 쪽이 v3 의 기본값이고,
        # 그래야 recovery·boss_named·「섭식」 카드가 한 파일에 다 들어온다.
        recovery=lambda ids, costs, tracer: set(),
        # 뿔피리도 샘플에 넣는다. 없으면 프론트의 뿔피리 서사·인스펙터 분기가
        # 계약 검사를 한 줄도 안 받는다(QA 재검 2026-09-09 R17).
        # 7회차(야습) 12턴. 그 앞에서 이미 쓰러진 사람이 있어
        # casualty·recovery·boss_named 가 남고, 보스전은 끝까지 굴러
        # abandon·flee·boss_adapt·자기 대상 기술까지 한 파일에 들어온다.
        horn=lambda mission, turn: mission == MISSIONS_A[0].no and turn == 12,
    )
    if args.stdout:
        # 판정 뷰만 낸다 — ts 와 timing 은 매번 다르고 판단이 아니다(설계 §3.4).
        for e in rec.events:
            view = json.dumps(judgment_view(e), ensure_ascii=False, sort_keys=True)
            sys.stdout.write(view + "\n")
        return

    # 파일은 픽스처다. 측정한 시간을 0 으로 눕혀 다시 만들어도 같은 바이트가
    # 나오게 한다 — 그러지 않으면 재생성할 때마다 git diff 가 소음으로 찬다.
    body = ""
    for e in rec.events:
        d = asdict(e)
        if isinstance(d["payload"].get("timing"), dict):
            d["payload"]["timing"] = {"latency_ms": 0.0}
        body += json.dumps(d, ensure_ascii=False) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding="utf-8")
    kinds = sorted({e.kind for e in rec.events})
    print(f"{OUT}: {len(rec.events)} events, outcome={rec.results[0].outcome}, kinds={kinds}")


if __name__ == "__main__":
    main()

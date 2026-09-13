"""JSONL 런 저장소 (설계 §1.4 — A·B 단계에 DB 는 없다).

runs/<run_id>.jsonl 한 파일에 이벤트가 한 줄씩. 첫 줄이 run_start 라 요약을
읽을 때 파일 전체를 파싱하지 않아도 된다.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from apps.arena.app.use_cases.runner import RunRecord
from apps.arena.domain.entities.trace_event import TraceEvent, from_json, to_json


class JsonlRunStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        if not run_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"run_id 에 허용되지 않는 문자: {run_id}")
        return self.root / f"{run_id}.jsonl"

    def save(self, run: RunRecord) -> None:
        path = self._path(run.run_id)
        tmp = path.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for e in run.events:
                f.write(to_json(e) + "\n")
        tmp.replace(path)  # 반쯤 쓰인 파일이 목록에 보이지 않게

    def load(self, run_id: str) -> RunRecord | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        events = [from_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        return record_from_events(run_id, events)

    def list_recent(self, limit: int) -> list[dict[str, Any]]:
        files = sorted(self.root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        out = []
        for p in files[:limit]:
            with p.open(encoding="utf-8") as f:
                first = f.readline()
            if not first:
                continue
            head = json.loads(first)
            out.append(
                {
                    "run_id": p.stem,
                    "ts": head.get("ts"),
                    "lineup": head.get("payload", {}).get("lineup"),
                    "orchestrator_on": head.get("payload", {}).get("orchestrator_on"),
                }
            )
        return out


def record_from_events(run_id: str, events: list[TraceEvent]) -> RunRecord:
    from apps.arena.app.use_cases.runner import MissionResult

    config = events[0].payload if events and events[0].kind == "run_start" else {}
    results = []
    for e in events:
        if e.kind == "mission_end":
            results.append(MissionResult(**{k: _tuple_if_list(v) for k, v in e.payload.items()}))
    return RunRecord(run_id=run_id, config=config, events=events, results=results)


def _tuple_if_list(v: Any) -> Any:
    return tuple(v) if isinstance(v, list) else v


def events_payload(run: RunRecord) -> list[dict[str, Any]]:
    return [asdict(e) for e in run.events]

#!/usr/bin/env python3
"""커밋 하나를 개발 로그 한 건으로 옮긴다.

PostToolUse 훅이 `git commit` 성공 직후 호출한다. 커밋 메시지에 이미
"무엇을 왜 했는가"가 들어 있으므로 LLM 없이 그대로 가공한다 — 훅이
느려지거나 비용이 들거나, 같은 커밋에서 매번 다른 문장이 나오는 일이 없다.

secu-agent 의 같은 이름 스크립트를 이식했다. 거기서는 Jekyll 사이트
(`jekyll/_logs/`)에 썼고, 여기는 사이트가 없어 `docs/devlog/` 에 쓴다.

만들어진 파일은 커밋하지 않고 워킹트리에 남긴다. 훅 안에서 커밋하면
그 커밋이 다시 훅을 부르고, 로그가 로그를 기록하게 된다.
"""

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

# 경로는 스크립트 위치에서 푼다 — 훅이 어느 디렉토리에서 불릴지 알 수 없다.
REPO = Path(__file__).resolve().parent.parent
LOGS = REPO / "docs" / "devlog"

# 저장소 디렉토리 → 작업 영역. 이 프로젝트의 계층(설계 문서 3.2)을 따른다.
AREA_RULES: list[tuple[str, str]] = [
    ("backend/apps/arena/domain/", "core"),
    ("backend/apps/arena/app/", "core"),
    ("backend/apps/arena/adapter/inbound/", "api"),
    ("backend/apps/arena/adapter/", "adapter"),
    ("backend/content/", "content"),
    ("backend/eval/", "eval"),
    ("backend/core/", "api"),
    ("backend/", "api"),
    ("frontend/", "web"),
    ("docs/qa/", "qa"),
    ("docs/", "docs"),
    (".claude/", "infra"),
    ("scripts/", "infra"),
    (".github/", "infra"),
]
DEFAULT_AREA = "infra"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True, cwd=REPO
    ).stdout.strip()


def area_for(paths: list[str]) -> str:
    """변경 파일들의 다수결로 영역을 정한다."""
    hits = Counter()
    for p in paths:
        for prefix, area in AREA_RULES:
            if p.startswith(prefix):
                hits[area] += 1
                break
        else:
            hits[DEFAULT_AREA] += 1
    return hits.most_common(1)[0][0] if hits else DEFAULT_AREA


def next_seq(day: str) -> int:
    existing = [
        int(m.group(1))
        for f in LOGS.glob(f"{day}-*.md")
        if (m := re.match(rf"{day}-(\d+)-", f.name))
    ]
    return max(existing, default=0) + 1


def to_bullets(subject: str, body: str) -> str:
    """커밋 제목을 굵은 리드로, 본문은 원래 줄 구조를 지킨 채 들여쓴다."""
    out = [f"- **{subject}**"]
    kept: list[str] = []
    for raw in body.strip().splitlines():
        line = raw.rstrip()
        # 트레일러(Co-Authored-By:, Claude-Session: 등)는 로그에 남기지 않는다.
        if re.match(r"^[A-Za-z][A-Za-z-]*:\s", line):
            continue
        kept.append(line)
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    for line in kept:
        out.append(f"  {line}" if line.strip() else "")
    return "\n".join(out)


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass

    LOGS.mkdir(parents=True, exist_ok=True)
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

    try:
        sha = _git("rev-parse", "--short", ref)
        subject = _git("log", "-1", "--pretty=%s", ref)
        body = _git("log", "-1", "--pretty=%b", ref)
        changed = [p for p in _git("show", "--name-only", "--pretty=", ref).splitlines() if p]
    except subprocess.CalledProcessError:
        return 0

    if not changed:
        return 0
    if all(p.startswith("docs/devlog/") for p in changed):
        return 0

    # 훅은 한 커밋에 여러 번 불릴 수 있다. 멱등성은 여기서 만든다.
    marker = f"커밋 `{sha}`"
    for existing in LOGS.glob("*.md"):
        if marker in existing.read_text(encoding="utf-8"):
            return 0

    day = date.today().isoformat()
    area = area_for(changed)
    seq = next_seq(day)
    path = LOGS / f"{day}-{seq:02d}-{area}.md"
    path.write_text(
        f"---\ndate: {day}\narea: {area}\nseq: {seq}\n---\n\n"
        f"{to_bullets(subject, body)}\n\n"
        f"- 커밋 `{sha}` · 파일 {len(changed)}개\n",
        encoding="utf-8",
    )
    print(json.dumps({"systemMessage": f"개발 로그를 남겼다 → {path}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

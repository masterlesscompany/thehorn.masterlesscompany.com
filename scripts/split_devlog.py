#!/usr/bin/env python3
"""팀 개발일지 원본 하나를 사이트의 개발 로그로 쪼갠다.

원본은 `devlog/devlog.md` 한 파일이다 — 팀이 날마다 `## YYYY-MM-DD` 절을 이어 쓴다.
이 스크립트가 날짜 절마다 `jekyll/_logs/<날짜>-team.md` 한 편을 만들고,
머리말(프로젝트·팀)과 날짜가 아닌 절(한눈에 보는 마일스톤)은 `/log/` 머리에 넣을
include 로 뺀다.

산출물은 커밋하지 않는다(.gitignore). 배포 워크플로와 밤 11시 로컬 반영이 빌드 직전에
돌린다 — 원본만 고치면 그날 밤 사이트에 들어간다(설계 2026-09-13 §2.4 · §3).

표준 라이브러리만 쓴다. 같은 원본이면 몇 번을 돌려도 산출물이 같다.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "devlog" / "devlog.md"
LOGS = REPO / "jekyll" / "_logs"
INCLUDES = REPO / "jekyll" / "_includes"
SUFFIX = "-team.md"
DATE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")


def strip_front_matter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """(머리말, [(## 제목, 본문)]). 제목 없는 첫 덩어리가 머리말이다."""
    head, out, title, buf = [], [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if title is not None:
                out.append((title, "\n".join(buf)))
            title, buf = line, []
        elif title is None:
            head.append(line)
        else:
            buf.append(line)
    if title is not None:
        out.append((title, "\n".join(buf)))
    return "\n".join(head), out


def tidy(body: str) -> str:
    # 절 사이 구분선(---)은 원본에서만 의미가 있다. 사이트에서는 편마다 카드로 나뉜다.
    lines = body.strip().splitlines()
    while lines and lines[-1].strip() in ("---", ""):
        lines.pop()
    return "\n".join(lines).strip() + "\n"


def write(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    head, secs = sections(strip_front_matter(SRC.read_text(encoding="utf-8")))
    head = re.sub(r"^# .*\n?", "", head.strip() + "\n", count=1)
    LOGS.mkdir(parents=True, exist_ok=True)

    wanted, extra = set(), []
    for title, body in secs:
        m = DATE.match(title)
        if not m:
            extra.append(f"### {title[3:].strip()}\n\n{tidy(body)}")
            continue
        day = m.group(1)
        path = LOGS / f"{day}{SUFFIX}"
        wanted.add(path)
        write(path, f"---\ndate: {day}\narea: team\nseq: 0\n---\n\n{tidy(body)}")

    # 원본에서 사라진 날짜는 로그에서도 지운다 — 남겨 두면 원본에 없는 기록이 사이트에 산다.
    for stale in LOGS.glob(f"*{SUFFIX}"):
        if stale not in wanted:
            stale.unlink()

    write(INCLUDES / "devlog_head.md", tidy(head))
    write(INCLUDES / "devlog_extra.md", "\n".join(extra) if extra else "")
    print(f"개발일지 {len(wanted)}편 · 부록 {len(extra)}절 ← {SRC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

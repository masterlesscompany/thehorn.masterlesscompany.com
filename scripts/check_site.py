#!/usr/bin/env python3
"""사이트판 경계 테스트 — 기획서의 약속을 빌드 산출물에서 검사한다.

RPG 저장소의 `tests/test_boundaries.py` 가 AST 로 계층 규칙을 강제하듯, 이 스크립트는
사이트가 원문의 "하지 않는다"를 어기지 않았는지를 `jekyll/_site` 에서 확인한다.
의견이 아니라 검사다 — 규칙을 바꾸려면 기획서를 먼저 바꾼다(CLAUDE.md "사이트가 굳힌 규칙").

표준 라이브러리만 쓴다. CI 에서 파이썬 의존성 설치 없이 돈다.

    cd jekyll && bundle exec jekyll build && cd .. && python3 scripts/check_site.py
    cd jekyll && bundle exec jekyll build --baseurl /thehorn && cd .. && python3 scripts/check_site.py --baseurl /thehorn
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "jekyll"

# Visual Guide §35 · 기획서 §46: 대외 문구에 특정 상용 게임명을 쓰지 않는다.
# 내부 레퍼런스 후보와 흔한 비교 대상을 넓게 둔다. 원문 페이지(/docs/*)는 검사하지 않는다 —
# 원문은 손대지 않는 것이 규칙이고, 원문도 게임명을 쓰지 않는다.
BANNED_GAMES = [
    "브라운더스트", "브라운 더스트", "Brown Dust", "BrownDust", "브더2",
    "다키스트 던전", "Darkest Dungeon", "배틀 브라더스", "Battle Brothers",
    "명일방주", "Arknights", "에픽세븐", "Epic Seven", "AFK 아레나", "AFK Arena",
    "킹덤 러쉬", "Kingdom Rush", "슬레이 더 스파이어", "Slay the Spire",
    "니케", "블루 아카이브", "Blue Archive", "로드 오브 히어로즈",
]
# 기획서 §34 · Visual Guide §16: 뿔피리는 Resource 가 아니다. 남은 개수 표기 금지.
BANNED_HORN = [
    re.compile(r"Horn\s*remaining", re.I),
    re.compile(r"Horn\s*[×x]\s*\d", re.I),
    re.compile(r"뿔피리\s*[×x]\s*\d"),
    # "뿔피리 3개 / 3회 / 3번" 처럼 개수로 세는 표현도 Resource 취급이다(QA R1 frontend).
    re.compile(r"뿔피리\s*\d+\s*[개회번]"),
    re.compile(r"Horn\s*\d+\s*(?:uses?|left|remaining)", re.I),
]


class Page(HTMLParser):
    """링크·id 를 모으고, 목업 figure 를 잘라낸다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.results: list[str] = []  # data-result 요소의 글자
        self._in_result = 0
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])
        if "data-result" in a:
            self._in_result += 1
            self._buf = []

    def handle_endtag(self, tag):
        if self._in_result and tag == "span":
            self._in_result -= 1
            self.results.append("".join(self._buf).strip())

    def handle_data(self, data):
        if self._in_result:
            self._buf.append(data)


def figures(html: str, mock: str | None = None) -> list[str]:
    """<figure class="mock" …> … </figure> 조각들. 목업 안에 figure 를 중첩하지 않는다는 전제."""
    # class 에 다른 이름이 섞여도(class="mock tour") 잡아야 한다 — 예전 정규식은 class="mock" 만
    # 맞아서, 클래스를 하나 더 붙이면 배지 검사를 통째로 빠져나갔다(QA R1 frontend).
    pat = (
        r'<figure\b(?=[^>]*\bclass="[^"]*\bmock\b)'
        + (rf'(?=[^>]*\bdata-mock="{mock}")' if mock else "")
        + r"[^>]*>.*?</figure>"
    )
    return re.findall(pat, html, re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(SRC / "_site"))
    ap.add_argument("--baseurl", default="")
    args = ap.parse_args()
    site = Path(args.site)
    base = args.baseurl.rstrip("/")
    if not (site / "index.html").exists():
        print(f"✗ 빌드 산출물이 없다: {site} — 먼저 `bundle exec jekyll build`")
        return 2

    pages = {p: p.read_text(encoding="utf-8") for p in site.rglob("*.html")}
    rel = lambda p: "/" + p.relative_to(site).as_posix()  # noqa: E731
    ours = {p: h for p, h in pages.items() if not rel(p).startswith("/docs/") or rel(p) == "/docs/index.html"}
    fails: dict[str, list[str]] = {}

    def fail(check: str, msg: str) -> None:
        fails.setdefault(check, []).append(msg)

    # 1. 상용 게임명
    for p, h in ours.items():
        for g in BANNED_GAMES:
            if g in h:
                fail("상용 게임명 금지 (Visual §35)", f"{rel(p)}: '{g}'")

    # 2. 뿔피리 개수
    for p, h in ours.items():
        for pat in BANNED_HORN:
            if m := pat.search(h):
                fail("뿔피리 개수 표기 금지 (기획서 §34)", f"{rel(p)}: '{m.group(0)}'")

    # 3. MOCK 배지 — 모든 목업 figure
    n_fig = 0
    for p, h in pages.items():
        for f in figures(h):
            n_fig += 1
            if "badge-mock" not in f:
                name = re.search(r'data-mock="([^"]+)"', f)
                fail("목업마다 MOCK 배지 (Visual §29.8)", f"{rel(p)}: {name.group(1) if name else '?'}")
    if n_fig == 0:
        fail("목업마다 MOCK 배지 (Visual §29.8)", "목업이 하나도 없다 — 검사가 빈 집합을 통과하고 있다")

    # 4. 평가 대시보드 — 결과 칸은 NOT RUN 뿐, 영문 판정어 없음
    n_eval = 0
    for p, h in pages.items():
        for f in figures(h, "evaluation"):
            n_eval += 1
            pp = Page()
            pp.feed(f)
            if not pp.results:
                fail("평가 결과는 NOT RUN (PART 1 §42)", f"{rel(p)}: data-result 칸이 없다")
            for r in pp.results:
                if r != "NOT RUN":
                    fail("평가 결과는 NOT RUN (PART 1 §42)", f"{rel(p)}: 결과 칸에 '{r}'")
            text = re.sub(r"<[^>]+>", " ", f)
            if m := re.search(r"\b(PASS|FAIL|PASSED|FAILED)\b", text):
                fail("평가 결과는 NOT RUN (PART 1 §42)", f"{rel(p)}: 판정어 '{m.group(0)}'")
            if m := re.search(r"\d+(\.\d+)?\s*%", text):
                fail("평가 결과는 NOT RUN (PART 1 §42)", f"{rel(p)}: 퍼센트 수치 '{m.group(0)}'")
    if n_eval == 0:
        fail("평가 결과는 NOT RUN (PART 1 §42)", "평가 대시보드 목업이 없다")
    # 주석 줄은 뺀다 — 파일 머리 설명이 "status: NOT RUN 이고" 처럼 규칙 자체를 인용한다.
    eval_yml = "\n".join(
        ln for ln in (SRC / "_data" / "eval.yml").read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")
    )
    for m in re.finditer(r"status:\s*([^,}\n]+)", eval_yml):
        if m.group(1).strip() != "NOT RUN":
            fail("평가 결과는 NOT RUN (PART 1 §42)", f"_data/eval.yml: status: {m.group(1).strip()}")

    # 5. 원시 내부 경로 금지 — 소스 템플릿에서. 산출물에서는 baseurl 이 비면 구별이 안 된다.
    for f in list(SRC.glob("*.html")) + list(SRC.glob("_layouts/*.html")) + list(SRC.rglob("_includes/**/*.html")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r'(?:href|src)="/(?!/)', line):
                fail("내부 링크는 relative_url (배포 baseurl)", f"{f.relative_to(REPO)}:{i}")

    # 6. 내부 링크가 산출물 안에서 풀리는가 (앵커 포함)
    parsed: dict[Path, Page] = {}
    for p, h in pages.items():
        pp = Page()
        pp.feed(h)
        parsed[p] = pp
    for p, pp in parsed.items():
        for link in pp.links:
            u = urlsplit(link)
            if u.scheme or link.startswith("//") or link.startswith("mailto:") or link.startswith("data:"):
                continue
            path, frag = unquote(u.path), unquote(u.fragment)
            if not path:
                target = p
            else:
                if base and not path.startswith(base + "/") and path != base:
                    fail("내부 링크 해소", f"{rel(p)}: '{link}' — baseurl '{base}' 없이 나갔다(relative_url 누락)")
                    continue
                path = path[len(base):] if base else path
                t = site / path.lstrip("/")
                target = t / "index.html" if (path.endswith("/") or t.is_dir()) else t
                if not target.exists():
                    fail("내부 링크 해소", f"{rel(p)}: '{link}' → 없음")
                    continue
            if frag and target.suffix == ".html":
                ids = parsed[target].ids if target in parsed else set()
                if frag not in ids:
                    fail("내부 링크 해소", f"{rel(p)}: '#{frag}' 앵커 없음 ({rel(target)})")

    # 7. 구현 현황이 v4 기준임을 밝히는가
    idx = pages.get(site / "index.html", "")
    sec = re.search(r'<section class="chap[^"]*" id="status">.*?</section>', idx, re.S)
    if not sec or "v5.2 기능이 아닙니다" not in sec.group(0):
        fail("구현 현황은 v4 기준 명시", "index.html #status 에 경고 문구가 없다")

    checks = [
        "상용 게임명 금지 (Visual §35)", "뿔피리 개수 표기 금지 (기획서 §34)", "목업마다 MOCK 배지 (Visual §29.8)",
        "평가 결과는 NOT RUN (PART 1 §42)", "내부 링크는 relative_url (배포 baseurl)", "내부 링크 해소", "구현 현황은 v4 기준 명시",
    ]
    for c in checks:
        if c in fails:
            print(f"✗ {c}")
            for m in fails[c][:20]:
                print(f"    {m}")
            if len(fails[c]) > 20:
                print(f"    … 외 {len(fails[c]) - 20}건")
        else:
            print(f"✓ {c}")
    print(f"\n페이지 {len(pages)} · 목업 {n_fig} · 평가 목업 {n_eval} · baseurl '{base or '(빈 값)'}'")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

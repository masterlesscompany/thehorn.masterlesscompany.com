"""계층 경계를 CI 가 강제한다.

설계 §3.3 의 규칙을 문서가 아니라 테스트로 만든다. secu-agent 의 같은 이름
테스트를 이식했고, 이 프로젝트 고유의 격리 셋(성별 · 행운)을 더했다.

클린 아키텍처 재배치 후로는 계층이 셋이다 — domain(최내) → app → adapter(최외).
화살표는 안쪽으로만 간다. content · eval · core(전역 인프라)는 BC 밖이다.
"""

import ast
import re
from pathlib import Path

import pytest

DOMAIN = Path("apps/arena/domain")
APP = Path("apps/arena/app")
ADAPTER = Path("apps/arena/adapter")

인프라_프레임워크 = (
    "fastapi",
    "google",
    "langchain",
    "langchain_core",
    "langgraph",
    "anthropic",
    "pydantic",
    "httpx",
    "yaml",
    "uvicorn",
)


def _모듈_이름들_추출(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def _import_모듈들(py: Path) -> list[str]:
    """전체 점 표기 모듈명. 계층이 apps.arena.* 아래로 들어가 최상위 이름만으로는
    구분되지 않는다 — 접두사로 판별한다."""
    return _모듈_이름들_추출(ast.parse(py.read_text(encoding="utf-8")))


def _파일들(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _속성_접근_파일들(root: str, attr: str) -> set[str]:
    """root 아래에서 `.attr` 속성을 읽는 파일 집합."""
    hits: set[str] = set()
    for py in _파일들(Path(root)):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == attr:
                hits.add(str(py))
    return hits


def _금지_접두사(py: Path, 금지: tuple[str, ...]) -> None:
    for name in _import_모듈들(py):
        for 접두 in 금지:
            assert not (name == 접두 or name.startswith(접두 + ".")), (
                f"{py} 가 {name} 을 import 한다 — 계층 역전"
            )


def test_각_계층에_검사할_파일이_있다():
    assert _파일들(DOMAIN), "domain/ 에 파이썬 파일이 없다"
    assert _파일들(APP), "app/ 에 파이썬 파일이 없다"
    assert _파일들(ADAPTER), "adapter/ 에 파이썬 파일이 없다"


@pytest.mark.parametrize("py", _파일들(DOMAIN), ids=str)
def test_domain_은_바깥_계층을_import_하지_않는다(py):
    """최내층. app · adapter 도, BC 밖(content · eval · core)도 모른다."""
    _금지_접두사(py, ("apps.arena.app", "apps.arena.adapter", "content", "eval", "core", "tests"))


@pytest.mark.parametrize("py", _파일들(APP), ids=str)
def test_app_은_adapter_를_import_하지_않는다(py):
    """유스케이스는 domain 만 안다. 어댑터 선택은 조립 지점(dependencies)의 일이다."""
    _금지_접두사(py, ("apps.arena.adapter", "content", "eval", "tests"))


@pytest.mark.parametrize("py", _파일들(Path("content")), ids=str)
def test_content_는_유스케이스를_import_하지_않는다(py):
    """세계관 데이터가 유스케이스에 묶이면 밸런스 튠이 코드 수정이 된다(설계 §3.3).

    이 규칙이 **없어서** `content/party.py` 가 `app/use_cases/agents/narration`
    을 import 하는 것을 CI 가 통과시켰다(QA 재검 2026-09-09 R15).
    CLAUDE.md 의 의존 그림에는 그 화살표가 없다.
    """
    _금지_접두사(py, ("apps.arena.app", "apps.arena.adapter", "eval", "tests"))


@pytest.mark.parametrize("py", _파일들(DOMAIN) + _파일들(APP), ids=str)
def test_안쪽_계층은_인프라_프레임워크를_import_하지_않는다(py):
    for name in _import_모듈들(py):
        assert name.split(".")[0] not in 인프라_프레임워크, f"{py} 가 {name} 을 import 한다"


@pytest.mark.parametrize("py", _파일들(DOMAIN) + _파일들(APP), ids=str)
def test_안쪽_계층은_random_을_직접_쓰지_않는다(py):
    """난수는 전부 Dice 포트를 통한다 — 같은 시드 = 같은 판(설계 §3.4).

    SeededDice 는 adapter/outbound/strategies/dice.py 로 나갔다. 재배치 전에는
    core 안에 있어 파일 이름으로 예외를 뒀지만, 이제 예외가 필요 없다.
    """
    for name in _import_모듈들(py):
        assert name.split(".")[0] != "random", f"{py} 가 random 을 직접 import 한다"


def test_성별은_엔진에_닿지_않는다():
    """기획서 §4.4 "전투·능력치·판단 엔진에 영향 0" 을 테스트로 만든다."""
    # narration 은 표기를 만들고, runner 는 그 값을 트레이스에 실어 리플레이가
    # 같은 설정을 복원하게 한다. 둘 다 판단이 아니다 — 규칙·전투·판단 층은 못 읽는다.
    허용 = {
        "apps/arena/app/use_cases/agents/narration.py",
        "apps/arena/app/use_cases/runner.py",
    }
    hits = _속성_접근_파일들("apps/arena/domain", "gender") | _속성_접근_파일들(
        "apps/arena/app", "gender"
    )
    assert hits <= 허용, f"서사 표기 밖에서 gender 를 읽는다: {hits - 허용}"
    금지 = (
        "apps/arena/domain/services/rules",
        "apps/arena/domain/services/battle",
        "apps/arena/domain/services/judgment",
        "apps/arena/app/use_cases/intermission",
    )
    for root in 금지:
        assert not _속성_접근_파일들(root, "gender"), f"{root} 가 gender 를 읽는다"


def test_행운은_판단에_개입하지_않는다():
    """기획서 §4.2 — 행운은 굴림에만. 판단 층은 luck 을 읽지 않는다."""
    # 굴림에만 쓴다 — 판단 층(judgment)도, 프롬프트 조립(agents)도 읽지 않는다.
    # 콘텐츠의 빌드 선택도 판단이므로 함께 막는다(QA 라운드 1 P1-6).
    허용 = {"apps/arena/domain/services/rules/combat.py"}
    hits = (
        _속성_접근_파일들("apps/arena/domain", "luck")
        | _속성_접근_파일들("apps/arena/app", "luck")
        | _속성_접근_파일들("content", "luck")
    )
    assert hits <= 허용, f"굴림 밖에서 luck 을 읽는다: {hits - 허용}"


def _코드_어휘(py: Path) -> list[str]:
    """식별자와 문자열 리터럴만 모은다. **주석과 독스트링은 뺀다.**

    주석은 "왜 마법을 뺐는가" 를 적는 자리다. 원문을 통째로 훑으면 그 이력을
    적을 수 없어 주석이 흐려진다 — 실제로 v3 개편 diff 에서 그 일이 일어났다
    (QA 2026-09-09 C7). 막아야 하는 것은 **코드**에 남은 마법이다.
    """
    tree = ast.parse(py.read_text(encoding="utf-8"))
    말: list[str] = []
    독스트링 = {
        n
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        for n in [ast.get_docstring(node, clean=False)]
        if n
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            말.append(node.id)
        elif isinstance(node, ast.Attribute):
            말.append(node.attr)
        elif isinstance(node, ast.arg):
            말.append(node.arg)
        elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            말.append(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in 독스트링:
                말.append(node.value)
    return 말


def _낱말로_있다(원문: str, 낱말: str) -> bool:
    """영문은 낱말 경계로, 한글은 그대로 — `reward` 의 `ward` 를 잡지 않는다."""
    if 낱말.isascii():
        return re.search(rf"(?<![A-Za-z]){re.escape(낱말)}(?![A-Za-z])", 원문) is not None
    return 낱말 in 원문


def test_마법은_어디에도_남아_있지_않다():
    """기획서 v3 §0.2 — 회복 주문도, 적 마법사도, 언데드도 없다.

    힐러를 넣는 순간 사망률 곡선(§6.0)과 자원 딜레마(§5.0)가 동시에 무너진다.
    설정이 아니라 설계라서 테스트로 굳힌다.
    """
    금지어 = ("magic", "마법", "ward", "마도서", "지팡이")
    뿌리 = [Path("apps/arena"), Path("content"), Path("eval")]
    hits: list[str] = []
    for root in 뿌리:
        for py in _파일들(root):
            for 이름 in _코드_어휘(py):
                for 낱말 in 금지어:
                    # 부분 문자열이면 `reward`·`forward` 가 걸린다(QA 2026-09-09 C7).
                    if _낱말로_있다(이름, 낱말):
                        hits.append(f"{py}: {이름}")
    assert not hits, "마법 흔적이 남았다: " + ", ".join(hits)

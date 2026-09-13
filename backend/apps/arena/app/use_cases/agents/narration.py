"""서사 표기 — 성별을 읽는 유일한 core 파일 (기획서 §4.4, 설계 §3.3).

성별은 이름·대사 톤·생애 이벤트 사유 문구에만 관여한다. 여기서 만든
문자열이 UnitState.voice 로 실려 프롬프트에 들어가지만, 규칙·판단 엔진은
그 문자열을 읽지 않는다. tests/test_boundaries.py 가 `.gender` 접근을
이 파일로 제한한다.
"""

from apps.arena.domain.entities.types import Character


def pronoun(c: Character) -> str:
    return "그녀" if c.gender == "female" else "그"


def life_event_subject(c: Character) -> str:
    """생애 이벤트 서사에서 쓰는 주어. 사유 목록이 성별별로 달라질 수 있는 자리(§6.2)."""
    return f"{c.name}({pronoun(c)})"

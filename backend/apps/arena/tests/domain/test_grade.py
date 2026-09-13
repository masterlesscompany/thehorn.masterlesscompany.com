"""결과 5등급 — 기획서 v3 §7.1b.

「철수」가 벌점이 아닌 것이 핵심이다. 승산 붕괴를 읽고 물러난 판은 실패가
아니다. 포기 판단을 시스템이 처벌하면 §8.3 이 죽는다.
"""

from apps.arena.domain.services.rules.grade import GRADES, grade_of


def test_등급은_다섯이다():
    assert GRADES == ("full_success", "success", "withdraw", "failure", "disaster")


def test_사망이_있으면_이겼어도_참사다():
    assert grade_of("win", dead=("thoma",), taken=(), injured=()) == "disaster"


def test_무손실_승리는_완전_성공이다():
    assert grade_of("win", dead=(), taken=(), injured=()) == "full_success"


def test_다치고_이기면_성공이다():
    assert grade_of("win", dead=(), taken=(), injured=("thoma",)) == "success"


def test_전원_생환한_후퇴는_철수지_실패가_아니다():
    """뿔피리를 불었거나 중대장이 스스로 물러난 판(기획서 v3 §8.2)."""
    assert grade_of("retreat", dead=(), taken=(), injured=("thoma",)) == "withdraw"


def test_끌려간_사람이_있으면_후퇴여도_실패다():
    """전원 생환이 철수의 조건이다. 굴에 두고 온 사람이 있으면 아니다."""
    assert grade_of("retreat", dead=(), taken=("thoma",), injured=()) == "failure"


def test_패배와_무승부는_실패다():
    assert grade_of("lose", dead=(), taken=(), injured=()) == "failure"
    assert grade_of("draw", dead=(), taken=(), injured=()) == "failure"


def test_철수는_실패보다_나쁘지_않다():
    """등급 순서가 곧 서열이다 — 철수가 실패 앞에 온다."""
    assert GRADES.index("withdraw") < GRADES.index("failure")

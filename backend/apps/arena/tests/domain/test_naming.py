"""보스 호칭 — 기획서 v3 §8.5.

미노타우루스는 고유명을 갖고 시작하지 않는다. 대원들은 그것이 **처음 데려간
사람의 이름**으로 그것을 부른다. 유저마다 보스 이름이 다르다.
"""

from apps.arena.domain.services.naming import boss_title


def test_받침이_없으면_를_붙는다():
    assert boss_title("토마") == "토마를 데려간 것"


def test_받침이_있으면_을_붙는다():
    assert boss_title("마르탱") == "마르탱을 데려간 것"


def test_받침_없는_이름은_를_로_읽는다():
    """QA 2026-09-09 C14 — 이름이 단언과 반대였다. "스" 는 받침이 없어 「를」이 맞다."""
    assert boss_title("아녜스") == "아녜스를 데려간 것"

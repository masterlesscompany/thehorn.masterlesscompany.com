from apps.arena.domain.services.josa import has_final, josa, with_josa


def test_받침이_있으면_은_을_과():
    assert josa("가렛 발렌", "은") == "은"
    assert josa("바르가스", "을") == "를"  # '스' 는 받침 없음
    assert josa("일레인 모어", "은") == "는"
    assert josa("카일 브란트", "이") == "가"  # 트: 받침 없음


def test_받침_판정():
    assert has_final("칼") is True
    assert has_final("나") is False
    assert has_final("thoma") is None
    assert has_final("") is None


def test_한글이_아니면_병기한다():
    """로마자·숫자의 받침은 읽는 사람마다 달라 틀리게 붙이는 것보다 병기가 낫다."""
    assert josa("thoma", "은") == "은(는)"
    assert with_josa("minotaur", "을") == "minotaur을(를)"


def test_ㄹ_받침은_로():
    assert josa("서울", "으로") == "로"
    assert josa("칼", "으로") == "로"
    assert josa("손", "으로") == "으로"


def test_붙여서_돌려준다():
    assert with_josa("가렛 발렌", "은") == "가렛 발렌은"
    assert with_josa("일레인 모어", "가") == "일레인 모어가"

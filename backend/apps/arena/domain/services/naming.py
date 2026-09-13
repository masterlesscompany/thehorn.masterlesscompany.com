"""그것에게는 이름이 없다 (기획서 v3 §8.5).

미노타우루스는 고유명을 갖고 시작하지 않는다. 첫 「끌려감」이 발생한 대원의
이름이 그대로 보스 호칭이 되고, 계약이 끝날 때까지(18출동) UI 에 남는다.

**회수에 성공했더라도 호칭은 남는다**(2026-09-08 팀 결정 ③) — 대원들은 잊지
않는다. 유저마다 보스 이름이 다르고, 로그에서 생성되므로 구현 비용은
문자열 하나다.
"""

from apps.arena.domain.services.josa import with_josa


def boss_title(member_name: str) -> str:
    """ "토마를 데려간 것". 받침을 보고 을/를 을 고른다."""
    return f"{with_josa(member_name, '를')} 데려간 것"

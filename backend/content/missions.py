"""미션 정의. 에피소드 길이는 파라미터다(기획서 §7.1) — 리스트 길이가 N 이다.

계약은 **18출동**이다 — 일반 5 + 보스 1 을 세 번(기획서 v3 §7.1, 2026-09-09 개정).
사이클 하나 안에서 생애주기가 한 바퀴 돌아야 해서 4판을 5판으로 늘렸다.

A단계(9/20)는 그중 두 판이다(2026-09-08 팀 결정 ①):
  7회차 야습 대응 — 놀 등장. 뿔피리 순간과 끌려감이 여기서 나온다
  6회차 성장기 미노타우루스 — 첫 보스 대치

**회차 번호가 순서와 어긋나는 것은 의도다.** 18출동 중 어느 판을 잘라 냈는지가
보이는 편이 낫다. 놀은 여름(7~11)에 등장하고 성장기 보스는 봄 끝(6)이라,
"끌려감이 나오는 판" 과 "첫 보스" 를 둘 다 넣으면 번호가 뒤집힌다.
"""

from apps.arena.domain.entities.types import MissionSpec
from content.environments import MINE, SWAMP
from content.monsters import GNOLL_PACK, JUVENILE_MINOTAUR

# 7회차 — 여름. 놀이 처음 나온다. 밤·시야 제한.
# "누굴 뒤에 두는가" 가 처음 문제가 되는 자리다(통합시나리오 §5).
MISSION_NIGHT_RAID = MissionSpec(
    no=7,
    name="야습 대응",
    enemy=GNOLL_PACK,
    environment=SWAMP,
    lineup_min=1,
    lineup_max=3,
    adaptation_on=False,
    casualty_tier="summer",
)

# 6회차 — 굴 입구. 그것이 처음 온다. 이 판은 이긴다. 그것은 물러난다.
MISSION_JUVENILE_BOSS = MissionSpec(
    no=6,
    name="굴 입구",
    enemy=JUVENILE_MINOTAUR,
    environment=MINE,
    lineup_min=1,
    lineup_max=3,
    adaptation_on=True,
    casualty_tier="boss_juvenile",
)

# A단계 제출본: 야습 → 보스전 두 판. **18출동 중 두 판을 잘라 낸 것**이다.
#
# 나머지 16판을 지금 채우지 않는 이유(QA 2026-09-09 V2 처리): 적 편성이 둘뿐이라
# 16판이 거의 같은 판이 된다 — 숫자만 참이고 판은 거짓이 된다. 계약 길이는
# 리스트 길이라 콘텐츠가 늘면 코드를 안 고치고 늘어난다. 호출 예산은 이미
# 계약 길이만큼 잡으므로(`select.build_harness(missions=…)`) 18판도 지금 돈다 —
# `test_긴_계약도_판마다_예산을_받는다` 가 실제로 18판을 돌려 확인한다.
MISSIONS_A: tuple[MissionSpec, ...] = (MISSION_NIGHT_RAID, MISSION_JUVENILE_BOSS)

# B단계: 같은 두 판 사이에 인터미션이 들어간다(러너가 intermission 플래그로 켠다).
MISSIONS_B: tuple[MissionSpec, ...] = MISSIONS_A

# 한 판만 도는 경로. 인터미션 없이 보스전만 본다 — 투표 유저의 첫 접속용이고,
# 실험 러너도 이걸 쓴다. 판 수는 파라미터라는 원칙이 여기서 지켜진다(기획서 §7.1).
MISSIONS_SINGLE: tuple[MissionSpec, ...] = (MISSION_JUVENILE_BOSS,)

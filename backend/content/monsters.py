"""숲 뒤편의 것들 (기획서 v3 §7.1a). 진영 대칭 엔진의 B 진영 정의.

**전부 살과 뼈다.** 언데드·악마·이형·주술사를 넣지 않는다 — 취향이 아니라
에셋 문제다(v3 §2.3). 상태 스프라이트가 배증하고, 비정형 실루엣은 64×64 에서
판독이 안 되며, 주문 연출은 애니메이션이라 스코프 밖이다.

각 종은 4슬롯 골격 중 하나를 부순다:
  고블린 → 소탕 (다수·매복, 열세면 도주)
  놀     → 호위 (부상자와 낙오자부터 문다)
  미노타우루스 → 전부. 3형태로 자란다
"""

from apps.arena.domain.entities.types import (
    Body,
    EnemyDef,
    EnemyUnitDef,
    Equipment,
    SkillDef,
    Stats,
)
from content.classes import ARMORS

녹슨_단검 = Equipment("녹슨 단검", 1, 0, 1, 7)
투석 = Equipment("투석", 1, 0, 1, 6, ranged=True)
갈고리 = Equipment("갈고리 창", 2, 0, 1, 11)
뿔 = Equipment("굽은 뿔", 3, 0, 1, 16)

물어뜯기 = SkillDef("물어뜯기", 9, 13, "enemy", "damage")
들이받기 = SkillDef("들이받기", 12, 18, "enemy", "damage")
포효 = SkillDef("포효", 10, 0, "all_enemies", "slow", 2)

# ─── 고블린 — 봄(1~4). 다수 약체. 죽이기보다 끌고 간다 ────────────────
_고블린 = EnemyUnitDef(
    "goblin_c",
    "고블린",
    Stats(8, 11, 7, 4, 4, 6),
    Body(140, "slim", 38),
    녹슨_단검,
    ARMORS["가죽 갑옷"],
    (),
    "front",
)

GOBLIN_BAND = EnemyDef(
    name="고블린 무리",
    description=(
        "길 뒤편에서 몰려 나온다. 하나하나는 약하고 셋이 붙으면 성가시다. "
        "열세를 감지하면 흩어져 달아났다가 다시 모인다."
    ),
    units=(
        EnemyUnitDef(
            "goblin_a",
            "고블린 두목",
            Stats(10, 11, 9, 5, 5, 6),
            Body(148, "normal", 45),
            갈고리,
            ARMORS["가죽 갑옷"],
            (),
            "front",
        ),
        EnemyUnitDef(
            "goblin_b",
            "고블린 투석수",
            Stats(7, 12, 6, 4, 5, 7),
            Body(138, "slim", 36),
            투석,
            ARMORS["가죽 갑옷"],
            (),
            "back",
        ),
        _고블린,
    ),
)

# ─── 놀 — 여름(6~9). 부상자와 낙오자부터 문다 ────────────────────────
GNOLL_PACK = EnemyDef(
    name="놀 무리",
    description=(
        "밤에 움직이고 측면으로 돈다. 성한 사람을 피하고 부상자와 낙오자부터 "
        "문다. 누구를 뒤에 두는가가 여기서 처음 문제가 된다. "
        # 여름은 두 종이 함께 온다(기획서 v3 §2.2). 서술은 화면과 프롬프트에
        # 그대로 나가므로 조항 번호는 주석에 둔다.
        "고블린이 뒤에서 돌을 던진다 — 여름은 두 종이 함께 온다."
    ),
    units=(
        EnemyUnitDef(
            "gnoll_a",
            "놀 사냥꾼",
            Stats(15, 14, 13, 5, 6, 5),
            Body(182, "normal", 78),
            갈고리,
            ARMORS["가죽 갑옷"],
            (물어뜯기,),
            "front",
        ),
        EnemyUnitDef(
            "gnoll_b",
            "놀 추적자",
            Stats(13, 16, 12, 5, 7, 6),
            Body(176, "slim", 68),
            갈고리,
            ARMORS["가죽 갑옷"],
            (물어뜯기,),
            "front",
        ),
        _고블린,
        EnemyUnitDef(
            "goblin_slinger",
            "고블린 투석수",
            Stats(7, 12, 6, 4, 5, 7),
            Body(138, "slim", 36),
            투석,
            ARMORS["가죽 갑옷"],
            (),
            "back",
        ),
    ),
)

# ─── 미노타우루스 성장기 — 5회차. 아직 이름이 없다 ────────────────────
JUVENILE_MINOTAUR = EnemyDef(
    name="굴의 그것",
    description=(
        "고블린 무리 뒤에 뭔가 서 있다. 아직 이름이 없다 — 대원들은 그것이 처음 "
        # 첫 끌려감이 그것의 이름을 만든다(기획서 v3 §8.5).
        "데려간 사람의 이름으로 그것을 부르게 된다. "
        "우리가 활 쏠 자리를 아는 것처럼 서 있다."
    ),
    units=(
        EnemyUnitDef(
            "minotaur",
            "굴의 그것",
            Stats(17, 10, 19, 6, 8, 6),
            Body(230, "sturdy", 190),
            뿔,
            ARMORS["판금 갑옷"],
            (들이받기, 포효),
            "front",
            is_boss=True,
        ),
    ),
    summon_every=3,
    summon_max=2,
    summon_template=_고블린,
)

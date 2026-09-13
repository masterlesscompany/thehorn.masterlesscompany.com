"""프리셋 로스터 5명 — 통합시나리오 §3 의 시드 프로필.

신체·성향은 지급 시 이미 굴려진 상태다. **성향은 유저가 못 정한다**(기획서 v3 §4.5) —
성격은 태어나는 것이고, 유저가 정하면 실험 변수가 오염된다.

데모 장면별 요구 성향(희생형·가장형·수읽기형·보수 기준선·중갑)에 한 명씩
대응한다(기획서 §7.4). 능력치는 전부 기본 8 이고 PRESET_ALLOCATIONS 가
"추천 배분" 이다 — 유저가 재분배한다.
"""

from apps.arena.domain.entities.types import Body, Character, Disposition, LifeContext
from apps.arena.domain.services.rules.stats import base_stats

PRESET_ROSTER: tuple[Character, ...] = (
    Character(
        id="thoma",
        name="토마",
        gender="male",
        body=Body(186, "slim", 68),
        stats=base_stats(),
        # 희생형 — 남을 위해 먼저 선다. 자기보존이 낮아 위험을 감수한다.
        disposition=Disposition(risk=20, cooperation=50, planning=0, sacrifice=80),
        char_class="archer",
        life=LifeContext(0, "고향에 남은 사람이 없다."),
        backstory="마르고 크다. 활을 당기기 위해 태어난 몸이라는 말을 듣고 자랐다.",
    ),
    Character(
        id="martin",
        name="마르탱",
        gender="male",
        body=Body(178, "sturdy", 88),
        stats=base_stats(),
        # 중갑 — 전투광. 위험을 반기고 대열을 잘 안 맞춘다.
        disposition=Disposition(risk=70, cooperation=-40, planning=-20, sacrifice=10),
        char_class="warrior",
        life=LifeContext(0, "브레티니 전까지 정규군이었다."),
        backstory="휴전이 그를 실직시켰다. 싸우지 않는 계절을 견디지 못한다.",
    ),
    Character(
        id="aude",
        name="오드",
        gender="female",
        body=Body(161, "normal", 55),
        stats=base_stats(),
        # 수읽기형 — 계획이 높고 지혜가 최고다. 복선 대사의 화자.
        disposition=Disposition(risk=-20, cooperation=40, planning=80, sacrifice=20),
        char_class="bard",
        life=LifeContext(0, "종군 이발사의 딸."),
        backstory="사상자를 세는 법을 아버지에게 배웠다. 뿔피리를 부는 것은 그의 몫이다.",
    ),
    Character(
        id="gilles",
        name="질",
        gender="male",
        body=Body(172, "sturdy", 86),
        stats=base_stats(),
        # 보수 기준선 — 모든 축이 중간이다. 비교군.
        disposition=Disposition(risk=0, cooperation=10, planning=20, sacrifice=0),
        char_class="defender",
        life=LifeContext(0, "성문 수비대에서 십 년."),
        backstory="어디가 먼저 뚫릴지 보고 그 자리에 선다. 그것 말고는 하는 일이 없다.",
    ),
    Character(
        id="agnes",
        name="아녜스",
        gender="female",
        body=Body(167, "slim", 56),
        stats=base_stats(),
        # 가장형 — 자기보존이 높다. 위험이 오면 먼저 집을 생각한다.
        disposition=Disposition(risk=-40, cooperation=10, planning=20, sacrifice=-50),
        char_class="rogue",
        life=LifeContext(1, "두 살 딸이 집에 있다."),
        backstory="척후로 먹고산다. 돌아갈 이유가 하나 있어 늘 먼저 물러선다.",
    ),
)

# 추천 배분(합 18). "추천 배분 수락" 버튼의 값이다(기획서 §5) — 조언 시스템과 무관.
PRESET_ALLOCATIONS: dict[str, dict[str, int]] = {
    # 장궁의 최소 힘 9 를 맞춘다. 무게등급 미달(마른 몸 vs 등급 2)은 남는다 —
    # 시나리오가 정한 체형이고, 그것이 효율 스펙트럼이다(기획서 §4.3).
    "thoma": {"agi": 8, "str_": 1, "wis": 4, "con": 4, "luck": 1},
    "martin": {"str_": 8, "con": 6, "agi": 4},
    "aude": {"wis": 10, "int_": 5, "con": 3},
    "gilles": {"con": 8, "str_": 5, "wis": 5},
    "agnes": {"agi": 8, "luck": 5, "wis": 5},
}

ROSTER_BY_ID: dict[str, Character] = {c.id: c for c in PRESET_ROSTER}

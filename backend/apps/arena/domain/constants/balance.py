"""밸런스 수치의 단일 출처. 근거는 설계 문서 13장.

다른 곳에 리터럴을 쓰지 않는다. 튠할 때 여기만 바꾼다.
"""

# ─── 능력치 (설계 §4.2·§13) ────────────────────────────────────────────
STAT_MIN = 1
STAT_MAX = 20
STAT_BASE = 8
FREE_POINTS = 18  # 한 능력치 몰빵(8+12=20)이 가능해야 "몰빵 실험"이 성립한다

# ─── 성향 (설계 §4.5) ─────────────────────────────────────────────────
DISPOSITION_MIN = -100
DISPOSITION_MAX = 100

# ─── 신체 (설계 §4.1) ─────────────────────────────────────────────────
HEIGHT_BASE = 150  # 키 = 150 + d50
HEIGHT_DIE = 50
BUILD_BY_D6 = {1: "slim", 2: "slim", 3: "normal", 4: "normal", 5: "sturdy", 6: "sturdy"}
BMI_BY_BUILD = {"slim": 18, "normal": 22, "sturdy": 26}
BMI_JITTER_DIE = 5  # BMI += d5 - 3
WEIGHT_CLASS = {"slim": 1, "normal": 2, "sturdy": 3}

# ─── 파생치 ──────────────────────────────────────────────────────────
HP_BASE = 40
HP_PER_CON = 6
STAMINA_BASE = 20
STAMINA_PER_CON = 2
STAMINA_REGEN_BASE = 3
STAMINA_REGEN_PER_CON = 0.3  # 턴당 회복 = 3 + CON×0.3
DEFEND_STAMINA_BONUS = 5

# ─── 판정 (설계 §5.4) ─────────────────────────────────────────────────
HIT_BASE = 60
HIT_PER_AGI_DIFF = 2
CRIT_BASE = 5
CRIT_MULT = 1.5
LUCK_ROLL_BONUS = 0.5  # (LCK - 10) × 0.5 %. 굴림에만 — 판단에는 개입 금지
LUCK_NEUTRAL = 10
STR_DAMAGE_COEF = 0.8
ARMOR_SCALE = 100  # 방어 감쇄 = 100 / (100 + 방어력)
DEFEND_MULT = 0.5
FLEE_BASE = 50
FLEE_PER_AGI_DIFF = 3
HIT_MIN = 5
HIT_MAX = 95

STAMINA_COST = {"ATTACK": 5, "DEFEND": 0, "MOVE": 3, "FLEE": 4, "WAIT": 0}


# ─── 효율 스펙트럼 (설계 §4.3) ────────────────────────────────────────
MISMATCH_HIT_PENALTY = 10  # 무게등급 미달 1당 명중 -10%
MISMATCH_SPEED_PENALTY = 1
MISMATCH_STAMINA_PER_5STR = 0.5  # STR 미달 5당 스태미나 ×(1+0.5)
HEIGHT_PENALTY_PER_5CM = 5  # 장궁·장창류 키 미달 5cm 당 명중 -5%

# ─── 전투 ────────────────────────────────────────────────────────────
TURN_LIMIT = 30
HEAL_SYNERGY = 1.15  # 치유 가능 진영의 전력 보정(설계 §6.2)

# ─── 승산 · 재계획 (설계 §6.2·§6.3) ──────────────────────────────────
ODDS_MIN = 0.05
ODDS_MAX = 0.95
RETREAT_THRESHOLD_DEFAULT = 0.30
RETREAT_THRESHOLD_RANGE = (0.15, 0.45)
ODDS_COLLAPSE_STEP = 0.10  # 재진입 트리거는 0.1 씩 더 내려갈 때마다
REPLAN_MAX_CONSECUTIVE = 3
# 이탈은 자주 일어난다(성향이 그렇게 생긴 단원이 있다). 이탈마다 감독을 부르면
# 23턴에 14번을 불러 호출 예산(기획서 §7.1: 100~300)을 먹고 로그가 재계획으로 덮인다.
# 승산 붕괴·적응은 쿨다운 없이 즉시 부른다.
REPLAN_DEVIATION_COOLDOWN = 3

# ─── 순응 판정 (설계 §6.4) ────────────────────────────────────────────
PRESSURE_HP_WEIGHT = 0.5
PRESSURE_LOSS_WEIGHT = 0.3
PRESSURE_LIFE_WEIGHT = 0.2
# 성향이 이탈 확률에 들어가는 방식.
#
# 세 축에 같은 계수를 주면 축이 수학적으로 구별되지 않는다 — E3 의 "성향별
# 행동 분포" 가 같은 숫자를 세 번 그리게 된다(QA 라운드 2). 축마다 **무엇을**
# 흔드는지가 달라야 한다:
#   위험 성향  → 자기 상처를 얼마나 크게 느끼는가 (HP 항의 배수)
#   희생 수용도 → 남이 쓰러진 것과 두고 온 가족을 얼마나 크게 느끼는가
#   협동 성향  → 전체적으로 자리를 지키는가 (평탄한 보정)
ADJUST_RISK = -0.0015
ADJUST_SACRIFICE = -0.0015
ADJUST_COOPERATION = -0.002
# 성향이 압력 항을 얼마나 늘이고 줄이는가. ±80 이면 ×0.6 ~ ×1.4.
PRESSURE_SCALE_DIVISOR = 200
DEVIATION_SIGMOID_GAIN = 4.0
DEVIATION_SIGMOID_SHIFT = 2.5
DEVIATION_MIN = 0.02
DEVIATION_MAX = 0.95

# ─── 지혜 마스킹 (설계 §4.6) — (하한, 상한, 단계) ────────────────────
WIS_TIERS = ((1, 7, 0), (8, 12, 1), (13, 16, 2), (17, 20, 3))
DARKNESS_TIER_PENALTY = 1

# ─── 보스 적응 (설계 §5.6) ────────────────────────────────────────────
ADAPT_WINDOW = 3  # 최근 3턴 관측
# 「전열이 벽이다」의 기준 — 전열이 **자기 최대 HP 의 이만큼을 맞고도 서 있으면** 벽이다.
#
# 전에는 "보스 피해의 60% 이상이 전열에 갔는가" 였다. 근접은 전열이 살아 있는 한
# 후열에 닿지 않으므로 이 비율은 구조적으로 항상 1.0 이었다 — 관측이 아니라
# 동어반복(QA 2026-09-09 J3, 실측 `{1.0: 134}`). 지금 값은 40시드 319개 관측 창
# 실측으로 골랐다: 창 내내 앞줄을 때린 창 91개 중 41개에서 발동한다.
ADAPT_WALL_HP_RATIO = 0.6
ADAPT_HEAL_COUNT = 2
ADAPT_DEFEND_RATIO = 0.5

# ─── 하네스 ──────────────────────────────────────────────────────────
MAX_CALLS = 300
HARNESS_RETRIES = 2

# ─── 인터미션 (설계 §7) ───────────────────────────────────────────────
GROWTH_WIN = 10
GROWTH_LOSE = 6
TRAIN_BASE = 0.5
TRAIN_PLANNING_COEF = 0.003
TRAIN_COOPERATION_COEF = 0.002
TRAIN_FATIGUE_COEF = 0.004
TRAIN_MIN = 0.10
TRAIN_MAX = 0.95
TRAIN_PARTIAL_BAND = 0.15  # 순응 확률 바로 아래 이 폭은 "부분 순응"
DILIGENT_PLANNING = 30  # planning > 30 → advantage
TIRED_FATIGUE = 60  # fatigue > 60 → disadvantage

# ─── 조언 (설계 §6.5) ─────────────────────────────────────────────────
ADVICE_MIN_MISSION = 2
ADVICE_ODDS_BELOW = 0.35
ADVICE_PROBABILITY = 0.25

# ─── 쓰러짐 3분기 (기획서 v3 §6.0) ────────────────────────────────────
# HP 0 은 사망이 아니다. 전투 종료 시 (부상, 끌려감, 사망) 백분율로 갈린다.
# 1~4 출동의 사망 0% 는 고정이다 — 튜토리얼 구간에서 아무도 잃지 않고
# 부상과 피로 관리만 배운다. 첫 상실은 여름의 「끌려감」으로, 죽음이 아니라
# 회수 여부라는 선택으로 온다.
CASUALTY_TABLE: dict[str, tuple[int, int, int]] = {
    "spring": (97, 3, 0),  # 1~4 · 고블린
    "boss_juvenile": (85, 13, 2),  # 5 · 성장기 미노타우루스
    "summer": (70, 22, 8),  # 6~9 · 놀 등장
    "boss_adult": (60, 25, 15),  # 10 · 성체
    "autumn": (55, 25, 20),  # 11~14 · 오크 등장
    "boss_king": (50, 25, 25),  # 15 · 킹
}

# ─── 뿔피리 (기획서 v3 §8.2) ──────────────────────────────────────────
# 계약 기간 3회. 무한이면 유저가 조종하는 게임이 되고(§0.1 위반), 0 이면
# 관전이 된다. 셋이면 매 판 "지금인가" 를 묻게 된다.
HORN_CHARGES = 3

# ─── 회수 (기획서 v3 §6.8) ────────────────────────────────────────────
# 대원의 누적 투자 × 0.6 (안내인·횃불·사냥개). 오래 키운 사람일수록 되찾는
# 값이 비싸다 — 그것이 딜레마의 축이다. 출동 슬롯 1 은 B단계에서 붙는다.
RECOVERY_COST_RATIO = 0.6

# ─── 학습 카드 (기획서 v3 §8.4) ───────────────────────────────────────
# 형태가 자랄수록 슬롯이 는다. 3형태는 진화 트리가 아니라 유저의 실패 기록이다.
CARD_SLOTS: dict[str, int] = {
    "boss_juvenile": 3,
    "boss_adult": 5,
    "boss_king": 7,
}

"""도메인 엔티티와 값 객체.

표준 라이브러리만 쓴다. 프레임워크도 콘텐츠도 모른다 —
그 사실을 tests/test_boundaries.py 가 강제한다.

용어: 단주(유저) · 단장(오케스트레이터) · 단원(캐릭터 에이전트).
"""

from dataclasses import dataclass, field, replace
from typing import Literal

from apps.arena.domain.constants.balance import (
    DISPOSITION_MAX,
    DISPOSITION_MIN,
    STAT_MAX,
    STAT_MIN,
    WEIGHT_CLASS,
)

Build = Literal["slim", "normal", "sturdy"]
Gender = Literal["female", "male"]
Position = Literal["front", "back"]

STAT_NAMES: tuple[str, ...] = ("str_", "agi", "con", "int_", "wis", "luck")
# 화면·API 가 쓰는 이름. 파이썬 예약어(str·int) 때문에 필드명에 밑줄이 붙었다.
STAT_LABELS: dict[str, str] = {
    "str_": "힘",
    "agi": "민첩",
    "con": "체력",
    "int_": "지능",
    "wis": "지혜",
    "luck": "행운",
}


@dataclass(frozen=True)
class Body:
    """신체 — 탄생 주사위 1회, 불변(기획서 §4.1·§4.3).

    변경 메서드가 없다. 유일한 예외인 부상(장애)은 C단계이고 Injury 타입만 있다.
    """

    height_cm: int
    build: Build
    weight_kg: int

    @property
    def weight_class(self) -> int:
        """장비 효율 계산의 입력. 마른 1 / 보통 2 / 건장 3 (설계 §4.1)."""
        return WEIGHT_CLASS[self.build]


@dataclass(frozen=True)
class Stats:
    """능력치 6종 (기획서 §4.2). 값은 1..20.

    감소 경로가 없다 — 유저가 찍은 포인트를 시스템이 뺏지 않는다(기획서 §5).
    역성장은 숙련·컨디션(Character.fatigue)에만 걸린다.
    """

    str_: int
    agi: int
    con: int
    int_: int
    wis: int
    luck: int

    def __post_init__(self) -> None:
        for name in STAT_NAMES:
            v = getattr(self, name)
            if not STAT_MIN <= v <= STAT_MAX:
                raise ValueError(f"{STAT_LABELS[name]} 은 {STAT_MIN}..{STAT_MAX} 이어야 한다: {v}")

    def with_added(self, **delta: int) -> "Stats":
        """포인트를 더한 새 Stats. 음수는 거부한다 — 감소 경로를 만들지 않는다."""
        for name, d in delta.items():
            if name not in STAT_NAMES:
                raise ValueError(f"모르는 능력치: {name}")
            if d < 0:
                raise ValueError(f"{STAT_LABELS[name]} 을 줄일 수 없다 ({d})")
        return replace(self, **{k: getattr(self, k) + v for k, v in delta.items()})

    def as_dict(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in STAT_NAMES}


@dataclass(frozen=True)
class Disposition:
    """성향 4축 (기획서 §4.5). 각 -100..100. 내부는 수치, 외부 표기만 MBTI.

    지급 시 시드로 결정되고 유저는 손대지 못한다. 바뀌는 경로는 생애 이벤트의
    파라미터 변경뿐이다(shifted).
    """

    risk: int
    cooperation: int
    planning: int
    sacrifice: int

    def __post_init__(self) -> None:
        for name in ("risk", "cooperation", "planning", "sacrifice"):
            v = getattr(self, name)
            if not DISPOSITION_MIN <= v <= DISPOSITION_MAX:
                raise ValueError(f"성향 {name} 은 {DISPOSITION_MIN}..{DISPOSITION_MAX}: {v}")

    def shifted(self, **delta: int) -> "Disposition":
        """이벤트 효과. 범위를 넘으면 잘라 둔다 — 예외로 막으면 이벤트 하나가
        인터미션 전체를 죽인다."""
        out = {}
        for name in ("risk", "cooperation", "planning", "sacrifice"):
            v = getattr(self, name) + delta.get(name, 0)
            out[name] = max(DISPOSITION_MIN, min(DISPOSITION_MAX, v))
        return Disposition(**out)

    def as_dict(self) -> dict[str, int]:
        return {
            "risk": self.risk,
            "cooperation": self.cooperation,
            "planning": self.planning,
            "sacrifice": self.sacrifice,
        }


@dataclass(frozen=True)
class LifeContext:
    """생애 컨텍스트. 캐릭터 프롬프트와 순응 판정의 입력(설계 §6.4).

    dependents: 부양가족 수. "딸 2세" 가 곧 이 값 1 이다.
    """

    dependents: int
    note: str


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    gender: Gender
    body: Body
    stats: Stats
    disposition: Disposition
    char_class: str
    life: LifeContext
    backstory: str
    # 컨디션. 0..100. 인터미션 훈련 순응 판정의 입력. 역성장이 걸리는 유일한 축.
    fatigue: int = 0


@dataclass(frozen=True)
class Equipment:
    """장비 — 효율 스펙트럼의 입력(설계 §4.3). 요구치 미달은 금지가 아니라 페널티다."""

    name: str
    weight_class: int  # 요구 무게등급 1..3
    min_height: int  # 0 이면 무관. 장궁·장창류만 값이 있다
    min_str: int
    base_damage: int
    armor: int = 0
    is_long: bool = False  # 키 미달 페널티 대상
    ranged: bool = False  # 후열에서도 아무나 노린다. 근접은 전열이 살아 있으면 전열만


@dataclass(frozen=True)
class SkillDef:
    name: str
    cost: int
    base: int
    target: Literal["enemy", "ally", "self", "all_enemies", "all_allies"]
    # heal | damage | guard(전열 보호) | slow | blind | bless | snipe | double | crit
    effect: str
    magnitude: int = 0


@dataclass(frozen=True)
class CardDef:
    """학습 카드 (기획서 v3 §8.4). 그것은 당신이 남긴 것을 먹고 자란다.

    실효는 기존 메커니즘으로만 낸다 — 새 효과를 만들지 않는다.
      focus        : 지목한 대원을 우선 타격한다(battle.boss_focus)
      ranged_block : 원거리 대원의 명중을 깎는다(blind 상태)
    """

    key: str
    name: str
    source: Literal["scout", "flight", "loot", "feeding"]
    observation: str  # 무엇을 보고 배웠는가. {값} 자리는 선택 시점에 채운다
    effect: Literal["focus", "ranged_block"]
    magnitude: int = 0


@dataclass(frozen=True)
class BuildChoice:
    """AI 세부 층의 결과(기획서 §5 "세부" 층). 무기·갑옷·스킬은 유저가 정하지 않는다."""

    weapon: Equipment
    armor: Equipment
    skills: tuple[SkillDef, ...]
    rationale: str


# 출전 한 사람 = (캐릭터, 빌드, 말투). app·content·adapter 가 같이 쓰는 어휘라
# 도메인이 소유한다 — 러너에 두면 content 가 유스케이스를 import 하게 된다.
PartyMember = tuple[Character, BuildChoice, str]


@dataclass(frozen=True)
class Environment:
    """규칙 엔진의 수정자(설계 §5.5). 편성 장면에서 서술과 수치가 함께 프롬프트에 들어간다."""

    name: str
    description: str
    speed_penalty_by_weight: dict[int, int]  # 무게등급 → 속도 페널티
    stamina_multiplier: float
    range_penalty: int  # 후열 원거리 명중 페널티(%)
    darkness: bool  # 지혜 마스킹 한 단계 강화


@dataclass(frozen=True)
class EnemyUnitDef:
    id: str
    name: str
    stats: Stats
    body: Body
    weapon: Equipment
    armor: Equipment
    skills: tuple[SkillDef, ...]
    position: Position
    is_boss: bool = False


@dataclass(frozen=True)
class EnemyDef:
    name: str
    description: str
    units: tuple[EnemyUnitDef, ...]
    # 수하 소환 주기(턴). 0 이면 없음. 보스 적응 "turtle" 이 이것을 줄인다.
    summon_every: int = 0
    summon_max: int = 0
    summon_template: EnemyUnitDef | None = None


@dataclass(frozen=True)
class MissionSpec:
    no: int
    name: str
    enemy: EnemyDef
    environment: Environment
    lineup_min: int
    lineup_max: int
    adaptation_on: bool
    # 쓰러짐 3분기 확률표의 행(기획서 v3 §6.0). CASUALTY_TABLE 의 키다.
    casualty_tier: str = "spring"


Strategy = Literal["rush", "attrition", "defensive", "retreat"]


@dataclass(frozen=True)
class Plan:
    """단장의 작전(설계 §6.1)."""

    assessment: str
    worth_fighting: bool
    strategy: Strategy
    formation: dict[str, Position]
    focus_target: str | None
    per_unit_directive: dict[str, str]
    retreat_threshold: float
    rationale: str


ActionKind = Literal["ATTACK", "DEFEND", "SKILL", "MOVE", "FLEE", "WAIT"]


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    target: str | None = None
    skill: str | None = None
    position: Position | None = None

    def label(self) -> str:
        if self.kind == "SKILL":
            return f"SKILL:{self.skill}"
        if self.kind == "MOVE":
            return f"MOVE:{self.position}"
        return self.kind


@dataclass(frozen=True)
class RunConfig:
    seed: int
    lineup: tuple[str, ...]
    allocations: dict[str, dict[str, int]]
    classes: dict[str, str]
    genders: dict[str, Gender]
    orchestrator_on: bool
    adaptation_on: bool
    missions: tuple[MissionSpec, ...]
    intermission: bool
    model_name: str = "fake"


# ─── C단계 — 타입만 선언한다 (기획서 §6·§12 "스키마만") ─────────────────

SlotOccupantKind = Literal["original", "veteran_substitute", "rookie"]
LeaveKind = Literal["returning", "permanent"]


@dataclass(frozen=True)
class Injury:
    """부상(장애) — 신체 불변의 유일한 예외. 구현하지 않는다."""

    description: str
    stat_penalty: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Slot:
    """로스터의 한 자리(기획서 §6.1). 사람이 바뀌어도 자리는 그대로다."""

    index: int
    occupant_id: str
    occupant_kind: SlotOccupantKind
    on_leave_owner_id: str | None = None


EventEffectKind = Literal[
    "param_change",
    "absence",
    "leave",
    "recruit",
    "return",
    "death",
]

"""진영 대칭 전투 상태 (설계 §5.1).

보스전도 PvP 도 같은 코드다 — 보스는 "유닛 1(+수하) + 고정 정책 진영"이다.
UnitState 와 Battle 은 제자리에서 갱신된다(mutable). 한 판 안에서 상태가
수천 번 바뀌는데 매번 복사하면 느리고 읽기도 나쁘다. 불변이 필요한 것
(Character · Body · Stats)은 이미 불변이다.
"""

from dataclasses import dataclass, field

from apps.arena.domain.constants.balance import (
    STAMINA_COST,
    TURN_LIMIT,
)
from apps.arena.domain.entities.types import (
    Action,
    Body,
    BuildChoice,
    Character,
    Disposition,
    EnemyDef,
    EnemyUnitDef,
    Environment,
    Equipment,
    Plan,
    Position,
    SkillDef,
    Stats,
)
from apps.arena.domain.services.rules.equipment import Modifiers, efficiency
from apps.arena.domain.services.rules.stats import hp_max, stamina_max


@dataclass
class Status:
    """지속 효과. name: guard | slow | blind | bless. turns 가 0 이 되면 사라진다."""

    name: str
    turns: int
    value: float


@dataclass
class UnitState:
    id: str
    name: str
    faction: str
    stats: Stats
    body: Body
    weapon: Equipment
    armor: Equipment
    skills: tuple[SkillDef, ...]
    hp: int
    hp_max: int
    stamina: int
    stamina_max: int
    position: Position
    char_class: str
    weapon_mods: Modifiers
    armor_mods: Modifiers
    # 캐릭터 에이전트에만 있는 것. 적 유닛은 None / 0.
    disposition: Disposition | None = None
    dependents: int = 0
    life_note: str = ""
    # 말투 지시 한 줄. narration.voice() 가 만든다. 엔진은 읽지 않는다.
    voice: str = ""
    is_boss: bool = False
    alive: bool = True
    fled: bool = False
    defending: bool = False
    statuses: list[Status] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.alive and not self.fled

    def status(self, name: str) -> Status | None:
        for s in self.statuses:
            if s.name == name:
                return s
        return None

    def has_skill(self, name: str) -> SkillDef | None:
        for s in self.skills:
            if s.name == name:
                return s
        return None


@dataclass(frozen=True)
class ActionRecord:
    """history 한 줄. 보스 적응(설계 §5.6)과 지혜 2단계 "적 패턴"의 입력."""

    turn: int
    actor: str
    faction: str
    action: str  # Action.label()
    target: str | None
    damage: int
    healed: int
    # 몇 회차의 기록인가. 학습 카드가 "출처 라운드" 를 짚는 재료다
    # (기획서 v3 §11, QA 2026-09-09 J9). 기록은 판을 넘어 쌓인다.
    mission: int = 0


@dataclass
class Battle:
    seed: int
    environment: Environment
    units: dict[str, UnitState]
    factions: tuple[str, str] = ("party", "enemy")
    turn: int = 0
    plans: dict[str, Plan | None] = field(default_factory=dict)
    history: list[ActionRecord] = field(default_factory=list)
    adaptation_on: bool = False
    boss_adaptations: list[tuple[int, str]] = field(default_factory=list)  # (턴, 패턴)
    boss_focus: str | None = None  # 적응 "focus"·"target_healer" 의 우선 타격 대상
    enemy_def: EnemyDef | None = None
    summoned: int = 0
    summon_every: int = 0
    retreat_ordered: bool = False
    mission_no: int = 0  # 이 전투가 몇 회차인가 — history 에 찍혀 판을 넘어 남는다
    # 직전 작전 때의 승산. 감독이 추세를 본다 — 한 번 낮게 찍혔다고 판을 접지 않는다.
    last_plan_odds: float | None = None
    turn_limit: int = TURN_LIMIT

    @property
    def party(self) -> str:
        return self.factions[0]

    @property
    def enemy(self) -> str:
        return self.factions[1]


def unit_from_character(
    c: Character, build: BuildChoice, faction: str, position: Position, voice: str = ""
) -> UnitState:
    return UnitState(
        id=c.id,
        name=c.name,
        faction=faction,
        stats=c.stats,
        body=c.body,
        weapon=build.weapon,
        armor=build.armor,
        skills=build.skills,
        hp=hp_max(c.stats),
        hp_max=hp_max(c.stats),
        stamina=stamina_max(c.stats),
        stamina_max=stamina_max(c.stats),
        position=position,
        char_class=c.char_class,
        weapon_mods=efficiency(c.body, c.stats, build.weapon),
        armor_mods=efficiency(c.body, c.stats, build.armor),
        disposition=c.disposition,
        dependents=c.life.dependents,
        life_note=c.life.note,
        voice=voice,
    )


# 소환된 유닛의 이름. 숫자로 끝나면 한국어 조사를 고를 수 없어 화면에
# "잔해 수하 1이(가)" 가 찍힌다(QA 라운드 2). 한글 서수를 쓴다.
ORDINALS = ("첫째", "둘째", "셋째", "넷째", "다섯째")


def unit_from_enemy(e: EnemyUnitDef, faction: str, suffix: str = "") -> UnitState:
    uid = e.id + suffix
    ordinal = ""
    if suffix:
        n = suffix.strip("_")
        ordinal = (
            f" {ORDINALS[int(n) - 1]}" if n.isdigit() and 0 < int(n) <= len(ORDINALS) else f" {n}"
        )
    return UnitState(
        id=uid,
        name=e.name + ordinal,
        faction=faction,
        stats=e.stats,
        body=e.body,
        weapon=e.weapon,
        armor=e.armor,
        skills=e.skills,
        hp=hp_max(e.stats),
        hp_max=hp_max(e.stats),
        stamina=stamina_max(e.stats),
        stamina_max=stamina_max(e.stats),
        position=e.position,
        char_class="monster",
        weapon_mods=efficiency(e.body, e.stats, e.weapon),
        armor_mods=efficiency(e.body, e.stats, e.armor),
        is_boss=e.is_boss,
    )


def display_names(battle: Battle) -> dict[str, str]:
    """id → 표시 이름. 프롬프트와 서사가 id 를 쓰지 않게 하는 단일 출처."""
    return {u.id: u.name for u in battle.units.values()}


def living(battle: Battle, faction: str) -> list[UnitState]:
    return [u for u in battle.units.values() if u.faction == faction and u.active]


def enemies_of(battle: Battle, unit_id: str) -> list[UnitState]:
    me = battle.units[unit_id]
    return [u for u in battle.units.values() if u.faction != me.faction and u.active]


def allies_of(battle: Battle, unit_id: str) -> list[UnitState]:
    me = battle.units[unit_id]
    return [
        u for u in battle.units.values() if u.faction == me.faction and u.active and u.id != unit_id
    ]


def stamina_cost(unit: UnitState, action: Action, env: Environment) -> int:
    """행동 비용. 장비 미달 배수 × 환경 배수(중갑만). "무거운 갑옷 입으면 금방 지친다" 의 실체."""
    if action.kind == "SKILL":
        skill = unit.has_skill(action.skill or "")
        base = skill.cost if skill else 0
    else:
        base = STAMINA_COST[action.kind]
    mult = unit.weapon_mods.stamina_mult * unit.armor_mods.stamina_mult
    if unit.armor.weight_class == 3:
        mult *= env.stamina_multiplier
    return round(base * mult)


def available_actions(battle: Battle, unit_id: str) -> list[Action]:
    """스태미나로 걸러진 행동 목록. 스태미나가 바닥이면 WAIT 만 남는다."""
    u = battle.units[unit_id]
    env = battle.environment
    # 스태미나 0 은 "지쳐서 아무것도 못 한다" 다. 비용 0 인 방어도 못 한다(설계 §5.4).
    if u.stamina <= 0:
        return [Action("WAIT")]
    out: list[Action] = []
    foes = enemies_of(battle, unit_id)
    friends = allies_of(battle, unit_id)

    def ok(a: Action) -> bool:
        return stamina_cost(u, a, env) <= u.stamina

    for f in foes:
        a = Action("ATTACK", target=f.id)
        if ok(a):
            out.append(a)
    if ok(Action("DEFEND")):
        out.append(Action("DEFEND"))
    for s in u.skills:
        if s.target == "enemy":
            for f in foes:
                a = Action("SKILL", target=f.id, skill=s.name)
                if ok(a):
                    out.append(a)
        elif s.target == "ally":
            for fr in [u, *friends]:
                a = Action("SKILL", target=fr.id, skill=s.name)
                if ok(a):
                    out.append(a)
        else:
            a = Action("SKILL", skill=s.name)
            if ok(a):
                out.append(a)
    other: Position = "back" if u.position == "front" else "front"
    if ok(Action("MOVE", position=other)):
        out.append(Action("MOVE", position=other))
    if foes and ok(Action("FLEE")):
        out.append(Action("FLEE"))
    out.append(Action("WAIT"))
    return out


def outcome(battle: Battle, end_of_turn: bool = False) -> str | None:
    """A진영(party) 기준. None 이면 계속.

    후퇴 명령 뒤에 파티가 전장에서 사라지면 "retreat", 명령 없이 사라지면 "lose".
    턴 상한은 무승부 — 승산으로 판정하지 않는다. 판정하면 실험이 오염된다(설계 §5.2).

    **턴 상한은 end_of_turn 에서만 본다.** 유닛 루프 안에서 함께 보면 30턴째의
    첫 행동 하나만 해석되고 나머지 유닛의 턴이 통째로 사라진다(설계 §5.2 의
    루프 순서: 유닛별 행동 → 턴 종료 → 승리 조건).
    """
    if not living(battle, battle.enemy):
        return "win"
    if not living(battle, battle.party):
        # 후퇴 명령을 내렸어도 한 명도 빠져나오지 못했으면 그건 전멸이다 —
        # 차트에서 후퇴색으로 칠해지면 "빠져나왔다" 로 읽힌다(QA 라운드 2).
        escaped = any(u.faction == battle.party and u.fled for u in battle.units.values())
        return "retreat" if battle.retreat_ordered and escaped else "lose"
    if end_of_turn and battle.turn >= battle.turn_limit:
        return "draw"
    return None

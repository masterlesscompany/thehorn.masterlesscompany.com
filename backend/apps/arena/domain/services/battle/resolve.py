"""행동 해석 — 상태를 제자리에서 바꾸고 판정 내역을 돌려준다 (설계 §5.3·§5.4).

에이전트의 판단은 흐릿할 수 있다(전열이 막는 후열을 노린다든지). 그런 행동은
예외로 죽이지 않고 가장 가까운 유효한 행동으로 바꾸고 그 사실을 기록한다.
스태미나 부족만 예외다 — available_actions 가 걸러 준 목록 밖이라 호출자 버그다.
"""

from dataclasses import dataclass, field

from apps.arena.domain.constants.balance import (
    DEFEND_STAMINA_BONUS,
    STAMINA_REGEN_BASE,
    STAMINA_REGEN_PER_CON,
)
from apps.arena.domain.entities.types import Action, SkillDef
from apps.arena.domain.ports.ports import Dice
from apps.arena.domain.services.battle.state import (
    ActionRecord,
    Battle,
    Status,
    UnitState,
    allies_of,
    enemies_of,
    stamina_cost,
)
from apps.arena.domain.services.josa import with_josa
from apps.arena.domain.services.rules.combat import crit_chance, damage, flee_chance, hit_chance

Breakdown = list[tuple[str, float]]


@dataclass
class Strike:
    target: str
    hit_roll: int
    needed: int
    hit: bool
    crit_roll: int | None
    crit_needed: int | None
    crit: bool
    damage: int
    killed: bool
    hit_breakdown: Breakdown
    damage_breakdown: Breakdown


@dataclass
class ResolutionRecord:
    actor: str
    action: str
    target: str | None
    stamina_cost: int
    strikes: list[Strike] = field(default_factory=list)
    healed: int = 0
    flee_roll: int | None = None
    flee_needed: int | None = None
    flee_success: bool | None = None
    # (이름, 값) — 효율 스펙트럼·환경·상태 보정. 인스펙터가 표로 보여준다.
    modifiers: Breakdown = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def total_damage(self) -> int:
        return sum(s.damage for s in self.strikes)


def _valid_enemy_target(
    battle: Battle, actor: UnitState, target_id: str | None, skill: SkillDef | None
) -> tuple[str, str | None]:
    """근접 무기는 전열이 살아 있으면 전열만 노린다. 원거리·저격은 제한 없다."""
    foes = enemies_of(battle, actor.id)
    if not foes:
        raise ValueError("공격할 적이 없다")
    ranged = actor.weapon.ranged or (skill is not None and skill.effect == "snipe")
    front = [f for f in foes if f.position == "front"]
    reachable = foes if (ranged or not front) else front
    if target_id in {f.id for f in reachable}:
        return target_id, None
    fallback = min(reachable, key=lambda f: f.hp)
    if target_id is None:
        return fallback.id, None
    blocked = battle.units[target_id].name if target_id in battle.units else target_id
    to = with_josa(fallback.name, "으로")
    note = f"{with_josa(blocked, '은')} 노릴 수 없다(전열이 막음) → {to} 변경"
    return fallback.id, note


def _strike(
    battle: Battle, actor: UnitState, target: UnitState, dice: Dice, skill: SkillDef | None
) -> Strike:
    needed, hit_bd = hit_chance(actor, target, battle.environment, skill)
    roll = dice.roll(100)
    hit = roll <= needed
    crit_roll = crit_needed = None
    crit = False
    dmg = 0
    dmg_bd: Breakdown = []
    killed = False
    if hit:
        crit_needed, _ = crit_chance(actor, skill)
        crit_roll = dice.roll(100)
        crit = crit_roll <= crit_needed
        dmg, dmg_bd = damage(actor, target, battle.environment, skill, crit)
        target.hp = max(0, target.hp - dmg)
        if target.hp == 0:
            target.alive = False
            killed = True
    return Strike(
        target.id, roll, needed, hit, crit_roll, crit_needed, crit, dmg, killed, hit_bd, dmg_bd
    )


def resolve(battle: Battle, actor_id: str, action: Action, dice: Dice) -> ResolutionRecord:
    actor = battle.units[actor_id]
    env = battle.environment
    cost = stamina_cost(actor, action, env)
    if cost > actor.stamina:
        raise ValueError(
            f"{actor.name} 의 스태미나 {actor.stamina} 로 {action.label()}({cost}) 을 할 수 없다"
        )
    actor.stamina -= cost
    # 방어 태세는 다음 행동을 시작하는 순간 풀린다.
    actor.defending = False

    rec = ResolutionRecord(
        actor=actor_id, action=action.label(), target=action.target, stamina_cost=cost
    )
    rec.modifiers.extend(actor.weapon_mods.notes)
    rec.modifiers.extend(actor.armor_mods.notes)
    if actor.armor.weight_class == 3 and env.stamina_multiplier != 1.0:
        rec.modifiers.append((f"환경 {env.name} 스태미나", env.stamina_multiplier))

    skill = actor.has_skill(action.skill or "") if action.kind == "SKILL" else None
    kind = action.kind
    healed = 0

    if kind == "ATTACK":
        tid, note = _valid_enemy_target(battle, actor, action.target, None)
        if note:
            rec.notes.append(note)
        rec.target = tid
        rec.strikes.append(_strike(battle, actor, battle.units[tid], dice, None))

    elif kind == "DEFEND":
        actor.defending = True
        actor.stamina = min(actor.stamina_max, actor.stamina + DEFEND_STAMINA_BONUS)

    elif kind == "SKILL":
        if skill is None:
            raise ValueError(f"{actor.name} 에게 스킬 {action.skill} 이 없다")
        if skill.effect in ("damage", "snipe", "crit", "double"):
            if skill.target == "all_enemies":
                for f in list(enemies_of(battle, actor_id)):
                    rec.strikes.append(_strike(battle, actor, f, dice, skill))
            else:
                tid, note = _valid_enemy_target(battle, actor, action.target, skill)
                if note:
                    rec.notes.append(note)
                rec.target = tid
                hits = 2 if skill.effect == "double" else 1
                for _ in range(hits):
                    tgt = battle.units[tid]
                    if not tgt.active:
                        break
                    rec.strikes.append(_strike(battle, actor, tgt, dice, skill))
        elif skill.effect == "heal":
            tid = action.target or actor_id
            tgt = battle.units.get(tid)
            if tgt is None or tgt.faction != actor.faction or not tgt.active:
                tgt = min([actor, *allies_of(battle, actor_id)], key=lambda u: u.hp / u.hp_max)
                rec.notes.append(f"치유 대상 변경 → {tgt.name}")
            rec.target = tgt.id
            before = tgt.hp
            tgt.hp = min(tgt.hp_max, tgt.hp + skill.magnitude)
            healed = tgt.hp - before
            rec.healed = healed
        elif skill.effect == "guard":
            _set_status(actor, "guard", skill.magnitude, 20)
            rec.target = actor_id
        elif skill.effect == "slow":
            for f in enemies_of(battle, actor_id):
                _set_status(f, "slow", skill.magnitude, 2)
        elif skill.effect == "blind":
            for f in enemies_of(battle, actor_id):
                _set_status(f, "blind", skill.magnitude, 15)
        elif skill.effect == "bless":
            for a in [actor, *allies_of(battle, actor_id)]:
                _set_status(a, "bless", skill.magnitude, 10)
        else:
            raise ValueError(f"모르는 스킬 효과: {skill.effect}")

    elif kind == "MOVE":
        actor.position = action.position or ("back" if actor.position == "front" else "front")
        rec.target = actor.position

    elif kind == "FLEE":
        needed, bd = flee_chance(actor, enemies_of(battle, actor_id))
        roll = dice.roll(100)
        rec.flee_roll, rec.flee_needed = roll, needed
        rec.flee_success = roll <= needed
        rec.modifiers.extend(bd)
        if rec.flee_success:
            actor.fled = True

    elif kind == "WAIT":
        pass
    else:
        raise ValueError(f"모르는 행동: {kind}")

    battle.history.append(
        ActionRecord(
            turn=battle.turn,
            actor=actor_id,
            faction=actor.faction,
            action=action.label(),
            target=rec.target,
            damage=rec.total_damage,
            healed=healed,
            mission=battle.mission_no,
        )
    )
    return rec


def _set_status(u: UnitState, name: str, turns: int, value: float) -> None:
    existing = u.status(name)
    if existing:
        existing.turns = max(existing.turns, turns)
        existing.value = value
    else:
        u.statuses.append(Status(name, turns, value))


def end_turn(battle: Battle) -> None:
    """턴 종료 — 스태미나 회복(CON), 지속 상태 감쇄 (설계 §5.2 4단계)."""
    for u in battle.units.values():
        if not u.active:
            continue
        regen = round(STAMINA_REGEN_BASE + u.stats.con * STAMINA_REGEN_PER_CON)
        u.stamina = min(u.stamina_max, u.stamina + regen)
        for s in u.statuses:
            s.turns -= 1
        u.statuses = [s for s in u.statuses if s.turns > 0]

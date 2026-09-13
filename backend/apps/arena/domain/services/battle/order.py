"""행동 순서 — 민첩 + 속도 보정 내림차순, 동률은 주사위 (설계 §5.2)."""

from apps.arena.domain.ports.ports import Dice
from apps.arena.domain.services.battle.state import Battle
from apps.arena.domain.services.rules.combat import speed


def turn_order(battle: Battle, dice: Dice) -> list[tuple[str, int, list[tuple[str, float]]]]:
    """[(unit_id, 속도, 내역)] — 트레이스 turn_start.order 에 그대로 실린다."""
    rows = []
    for u in battle.units.values():
        if not u.active:
            continue
        v, bd = speed(u, battle.environment)
        rows.append((u.id, v, bd))
    # 동률 타이브레이크. 시드가 같으면 같은 순서다.
    tiebreak = {r[0]: dice.roll(1000) for r in rows}
    rows.sort(key=lambda r: (-r[1], -tiebreak[r[0]]))
    return rows

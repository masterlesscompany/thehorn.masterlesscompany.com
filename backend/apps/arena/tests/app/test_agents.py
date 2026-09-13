from dataclasses import replace

from apps.arena.adapter.outbound.sinks.list_sink import ListSink
from apps.arena.adapter.outbound.strategies.dice import FixedDice
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.app.use_cases.agents.boss import boss_act, detect_adaptation, minion_act
from apps.arena.app.use_cases.agents.character import action_from, character_act
from apps.arena.app.use_cases.agents.orchestrator import make_plan
from apps.arena.domain.constants.balance import ADAPT_WALL_HP_RATIO
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.entities.types import Action
from apps.arena.domain.services.battle.state import (
    ActionRecord,
    Battle,
    unit_from_character,
    unit_from_enemy,
)
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.environments import MINE
from content.monsters import JUVENILE_MINOTAUR
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def _char(cid):
    c = ROSTER_BY_ID[cid]
    return replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))


def _battle(party=("martin", "aude", "thoma"), adaptation=True):
    units = {}
    for cid in party:
        c = _char(cid)
        units[cid] = unit_from_character(c, choose_build(c), "party", "front")
    for e in JUVENILE_MINOTAUR.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(
        seed=1, environment=MINE, units=units, enemy_def=JUVENILE_MINOTAUR, adaptation_on=adaptation
    )


def _tracer():
    sink = ListSink()
    return Tracer("t", sink, clock=lambda: "T"), sink


class 고정모델:
    name = "fixed"

    def __init__(self, data):
        self.data = data

    def decide(self, role, prompt, schema):
        return dict(self.data)


# ─── 단장 ─────────────────────────────────────────────────────────────


def test_감독은_힐러가_없으면_속공을_고르고_편성을_반영한다():
    b = _battle(party=("martin", "gilles", "thoma"))
    tracer, sink = _tracer()
    plan = make_plan(b, "party", FakeModel(), tracer, "initial")
    assert plan.strategy == "rush" and plan.worth_fighting
    # 방패병이 전열을 잡고 전사는 그 뒤에서 때린다 — 근접 적은 전열이 살아 있는
    # 한 후열에 닿지 못한다(resolve.py 의 reachable). 클래스 개편 뒤의 편성이다.
    assert b.units["gilles"].position == "front"
    assert b.units["martin"].position == "back" and b.units["thoma"].position == "back"
    assert sink.of_kind("plan")[0].payload["reason"] == "initial"


def test_싸울_가치가_없다면서_다른_전략을_내면_후퇴로_고정한다():
    b = _battle()
    tracer, sink = _tracer()
    m = 고정모델(
        {
            "assessment": "x",
            "worth_fighting": False,
            "strategy": "rush",
            "formation": {"nobody": "front"},
            "focus_target": "ghost",
            "per_unit_directive": {},
            "retreat_threshold": 0.9,
            "rationale": "r",
        }
    )
    plan = make_plan(b, "party", m, tracer, "initial")
    assert (
        plan.strategy == "retreat" and plan.retreat_threshold == 0.45 and plan.focus_target is None
    )
    notes = sink.of_kind("plan")[0].payload["notes"]
    assert len(notes) == 3


# ─── 단원 ─────────────────────────────────────────────────────────────


def test_이탈_판정이면_모델이_따랐다고_해도_이탈이다():
    """설계 §6.4 — 모델이 순응 여부를 뒤집을 수 없다."""
    b = _battle()
    tracer, sink = _tracer()
    b.units["thoma"].hp = 3
    m = 고정모델(
        {"action": "ATTACK", "target": "minotaur", "follows_plan": True, "reason": "싸운다"}
    )
    d = character_act(b, "thoma", None, m, FixedDice([1], uniforms=[0.0]), tracer, 0.5)
    assert d.compliance.verdict == "deviate" and d.follows_plan is False
    kinds = [e.kind for e in sink.events]
    assert kinds == ["context", "compliance", "decision"]


def test_모델이_불가능한_행동을_고르면_가장_가까운_것으로_바꾸고_기록한다():
    actions = [Action("ATTACK", "minotaur"), Action("DEFEND"), Action("WAIT")]
    a, note = action_from({"action": "ATTACK", "target": "ghost"}, actions)
    assert a == Action("ATTACK", "minotaur") and note
    a, note = action_from({"action": "SKILL", "skill": "화염구"}, actions)
    assert a == Action("WAIT") and note


def test_감독_OFF_에서도_단원은_행동한다():
    b = _battle()
    tracer, _ = _tracer()
    d = character_act(b, "martin", None, FakeModel(), FixedDice([1], uniforms=[0.99]), tracer, None)
    assert d.action.kind in ("ATTACK", "SKILL")
    assert d.follows_plan is False  # 방침이 없으니 "따랐다"도 없다


def test_Fake_단원은_방침의_집중_목표를_친다():
    b = _battle()
    tracer, _ = _tracer()
    plan = make_plan(b, "party", FakeModel(), tracer, "initial")
    d = character_act(b, "martin", plan, FakeModel(), FixedDice([1], uniforms=[0.99]), tracer, 0.5)
    assert d.action.target == plan.focus_target or d.action.kind == "SKILL"
    assert d.follows_plan


# ─── 보스 ─────────────────────────────────────────────────────────────


def _history(
    b, actor, turns, target="minotaur", dmg=10, action="ATTACK", healed=0, faction="party"
):
    for t in turns:
        b.history.append(ActionRecord(t, actor, faction, action, target, dmg, healed))


def test_같은_아군이_3턴_연속_공격하면_집중_타격_적응():
    b = _battle()
    b.turn = 4
    _history(b, "martin", [1, 2, 3])
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    pattern, ev = detect_adaptation(b, "minotaur")
    assert pattern == "repeat_attacker" and ev["actor"] == "martin"


def _앞줄만(b, front="gilles"):
    for u in b.units.values():
        if u.faction == "party":
            u.position = "front" if u.id == front else "back"


def test_전열이_맞고도_버티면_전열_붕괴_적응():
    """기획서 v3 §8.4 — 앞줄이 **버틴다**는 것이 신호다.

    QA 2026-09-09 J3: 전에는 "내 피해의 60% 이상이 앞줄에 갔는가" 를 봤다.
    근접은 전열이 살아 있는 한 후열에 닿지 않으므로(resolve.py 의 reachable)
    이 비율은 **구조적으로 항상 1.0** 이었다 — 실측 `{1.0: 134}`. 관측이 아니라
    동어반복이었다.

    지금 보는 것은 둘이다: 창 내내 앞줄을 때렸는가, 그런데도 그가 서 있는가.
    """
    b = _battle(party=("gilles", "martin", "thoma"))
    b.turn = 4
    _앞줄만(b)
    벽 = b.units["gilles"]
    # 최대 HP 의 절반 넘게 맞고도 서 있다.
    _history(b, "minotaur", [1, 2, 3], target="gilles", dmg=벽.hp_max // 3 + 1, faction="enemy")
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    pattern, ev = detect_adaptation(b, "minotaur")
    assert pattern == "frontline_wall" and ev["blocker"] == "gilles"
    assert ev["absorbed"] > 0 and ev["ratio"] >= ADAPT_WALL_HP_RATIO


def test_긁기만_해서는_전열이_벽이_아니다():
    """맞았다고 다 벽이 아니다 — 창이 지나도록 **긁기만** 했으면 관측이 없다.

    이 테스트가 실패하면 규칙이 다시 동어반복으로 돌아간 것이다.
    """
    b = _battle(party=("gilles", "martin", "thoma"))
    b.turn = 4
    _앞줄만(b)
    _history(b, "minotaur", [1, 2, 3], target="gilles", dmg=1, faction="enemy")
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    assert detect_adaptation(b, "minotaur")[0] != "frontline_wall"


def test_앞줄을_부수면_벽이_아니다():
    """때려서 쓰러뜨렸으면 막힌 게 아니다 — 뒤가 열렸다."""
    b = _battle(party=("gilles", "martin", "thoma"))
    b.turn = 4
    _앞줄만(b)
    벽 = b.units["gilles"]
    _history(b, "minotaur", [1, 2, 3], target="gilles", dmg=벽.hp_max, faction="enemy")
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    벽.hp, 벽.alive = 0, False
    assert detect_adaptation(b, "minotaur")[0] != "frontline_wall"


def test_치유_2회면_치유자_타격_적응():
    b = _battle()
    b.turn = 4
    _history(b, "aude", [1, 2], target="martin", dmg=0, action="SKILL:치유", healed=20)
    _history(b, "martin", [3], dmg=5)
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    assert detect_adaptation(b, "minotaur")[0] == "healing"


def test_방어_위주면_소환_가속_적응():
    b = _battle()
    b.turn = 4
    _history(b, "martin", [1, 2, 3], dmg=0, action="DEFEND")
    _history(b, "thoma", [1, 2, 3], dmg=0, action="DEFEND")
    assert detect_adaptation(b, "minotaur")[0] == "turtle"


def test_적응_OFF_면_적응하지_않고_ON_이면_boss_adapt_가_남는다():
    for on in (False, True):
        b = _battle(adaptation=on)
        b.turn = 4
        b.summon_every = 3
        _history(b, "martin", [1, 2, 3])
        tracer, sink = _tracer()
        action, pattern = boss_act(b, "minotaur", FakeModel(), tracer)
        assert (pattern is not None) == on
        assert (len(sink.of_kind("boss_adapt")) == 1) == on
        if on:
            assert b.boss_focus == "martin" and action.target == "martin"


def test_같은_패턴은_창_안에서_한_번만():
    b = _battle()
    b.turn = 4
    _history(b, "martin", [1, 2, 3])
    b.boss_adaptations.append((3, "repeat_attacker"))
    assert detect_adaptation(b, "minotaur")[0] is None


def test_수하는_모델_없이_가장_약한_적을_친다():
    b = _battle()
    b.units["thoma"].hp = 5
    tracer, sink = _tracer()
    a = minion_act(b, "minotaur", tracer)  # 보스를 수하 정책으로 돌려도 동작한다
    assert a.target == "thoma" and a.kind in ("ATTACK", "SKILL")
    assert sink.of_kind("decision")[0].payload["model"]["model"] == "policy"


# ─── QA 라운드 1 회귀 ──────────────────────────────────────────────────


def test_후퇴_명령은_모델에게_묻지_않는다():
    """설계 §5.3 — 후퇴는 선택지가 아니라 명령이다. 모델이 계속 싸우겠다고 해도 뺀다."""
    b = _battle()
    b.retreat_ordered = True
    tracer, sink = _tracer()
    m = 고정모델(
        {"action": "ATTACK", "target": "minotaur", "follows_plan": True, "reason": "싸운다"}
    )
    d = character_act(b, "thoma", None, m, FixedDice([1], uniforms=[0.99]), tracer, 0.1)
    assert d.action.kind == "FLEE"
    dec = sink.of_kind("decision")[0].payload
    assert dec["verdict"] == "retreat" and dec["model"]["model"] == "order"


def test_이탈이면_방침_행동이_선택지에서_빠진다():
    """설계 §6.4 — 이탈은 라벨이 아니라 선택지의 변화다."""
    from apps.arena.domain.entities.types import Plan

    b = _battle()
    b.units["thoma"].hp = 3
    plan = Plan("x", True, "rush", {}, "minotaur", {"thoma": "vargas 공격"}, 0.3, "r")
    tracer, sink = _tracer()
    m = 고정모델(
        {"action": "ATTACK", "target": "minotaur", "follows_plan": True, "reason": "싸운다"}
    )
    d = character_act(b, "thoma", plan, m, FixedDice([1], uniforms=[0.0]), tracer, 0.5)
    assert d.compliance.verdict == "deviate"
    assert not (d.action.kind == "ATTACK" and d.action.target == "minotaur")


def test_적응은_실제로_바뀐_것을_남긴다():
    """QA 라운드 1 P1-9 — 같은 적응을 세 번 기록하면서 상태가 그대로면 로그가 거짓말한다."""
    b = _battle()
    b.turn = 4
    _history(b, "martin", [1, 2, 3])
    tracer, sink = _tracer()
    boss_act(b, "minotaur", FakeModel(), tracer)
    eff = sink.of_kind("boss_adapt")[0].payload["effect"]
    assert eff["field"] == "boss_focus" and eff["after"] == "martin" and eff["no_change"] is False


def test_보스_적응_대상은_해시_순서에_기대지_않는다():
    """QA 라운드 1 P0-3 — set 순회는 PYTHONHASHSEED 마다 다른 판을 만든다."""
    b = _battle()
    b.turn = 4
    _history(b, "thoma", [1, 2, 3])  # 카일이 먼저 치기 시작했다
    _history(b, "martin", [1, 2, 3])
    assert detect_adaptation(b, "minotaur")[1]["actor"] == "thoma"

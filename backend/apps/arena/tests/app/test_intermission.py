from dataclasses import replace

import pytest

from apps.arena.adapter.outbound.sinks.list_sink import ListSink
from apps.arena.adapter.outbound.strategies.dice import FixedDice, SeededDice
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.app.use_cases.intermission import (
    IntermissionInput,
    IntermissionState,
    run_intermission,
)
from apps.arena.app.use_cases.intermission.growth import grant, points_for
from apps.arena.app.use_cases.intermission.life_event import apply_life_event, pick
from apps.arena.app.use_cases.intermission.training import run_training_turn
from apps.arena.domain.entities.trace_event import Tracer
from apps.arena.domain.services.judgment.training import (
    compliance_probability,
    execute_roll,
    judge_training,
    roll_mode,
)
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.events import LIFE_EVENTS, eligible, pool_for
from content.party import voice
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def _char(cid="thoma", **over):
    c = ROSTER_BY_ID[cid]
    c = replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))
    return replace(c, **over) if over else c


def _member(cid="thoma", **over):
    c = _char(cid, **over)
    return (c, choose_build(c), voice(c))


def _tracer():
    sink = ListSink()
    return Tracer("t", sink, clock=lambda: "T"), sink


# ─── 순응 판정 (기획서 §5.1) ────────────────────────────────────────────


def test_계획적일수록_순응하고_피로할수록_거부한다():
    성실 = _char("aude")  # 계획 +80
    지친 = replace(성실, fatigue=80)
    p1, _ = compliance_probability(성실)
    p2, _ = compliance_probability(지친)
    assert p2 < p1


def test_순응_확률은_범위_안이다():
    극단 = replace(_char("aude"), fatigue=100)
    p, bd = compliance_probability(극단)
    assert 0.10 <= p <= 0.95
    assert set(bd) == {"base", "planning", "cooperation", "fatigue"}


def test_판정은_순응_부분순응_거부로_갈린다():
    c = _char("agnes")
    p, _ = compliance_probability(c)
    assert judge_training(c, FixedDice([1], uniforms=[p - 0.01])).verdict == "comply"
    assert judge_training(c, FixedDice([1], uniforms=[p + 0.05])).verdict == "partial"
    assert judge_training(c, FixedDice([1], uniforms=[0.999])).verdict == "refuse"


def test_성실하면_advantage_피로하면_disadvantage():
    """기획서 §5.1 — 성실→advantage, 피로→disadvantage."""
    assert roll_mode(_char("aude"))[0] == "advantage"  # 계획 +80
    assert roll_mode(replace(_char("aude"), fatigue=80))[0] == "disadvantage"
    assert roll_mode(_char("martin"))[0] == "normal"  # 계획 -20


def test_advantage_는_두_번_굴려_높은_것():
    assert execute_roll("advantage", FixedDice([3, 17])) == (17, [3, 17])
    assert execute_roll("disadvantage", FixedDice([3, 17])) == (3, [3, 17])
    assert execute_roll("normal", FixedDice([11])) == (11, [11])


# ─── 육성 턴 ────────────────────────────────────────────────────────────


def test_거부하면_술집에_간다():
    """기획서 §5.1 — 훈련 지시를 거부하면 대체 행동의 서사가 붙고 결과도 파라미터로 귀결한다."""
    tracer, sink = _tracer()
    c = _char("aude")
    after, r = run_training_turn(c, "train", FakeModel(), FixedDice([10], uniforms=[0.999]), tracer)
    assert r["verdict"] == "refuse"
    assert "술집" in r["what"] and r["narration"]
    assert after.fatigue < c.fatigue or c.fatigue == 0
    assert [e.kind for e in sink.events] == ["directive", "train_compliance", "train_result"]


def test_훈련하면_피로가_쌓이고_쉬면_풀린다():
    tracer, _ = _tracer()
    c = replace(_char("agnes"), fatigue=40)
    훈련, _ = run_training_turn(c, "train", FakeModel(), FixedDice([18], uniforms=[0.0]), tracer)
    휴식, _ = run_training_turn(c, "rest", FakeModel(), FixedDice([18], uniforms=[0.0]), tracer)
    assert 훈련.fatigue > c.fatigue > 휴식.fatigue


def test_피로는_0과_100_사이로_잘린다():
    tracer, _ = _tracer()
    c = replace(_char("agnes"), fatigue=2)
    after, _ = run_training_turn(c, "rest", FakeModel(), FixedDice([18], uniforms=[0.0]), tracer)
    assert after.fatigue == 0


def test_육성_턴은_능력치를_건드리지_않는다():
    """기획서 §5 — 유저가 찍은 포인트는 시스템이 뺏지도 주지도 않는다."""
    tracer, _ = _tracer()
    c = _char("thoma")
    for cat in ("train", "rest", "study", "leisure"):
        after, _ = run_training_turn(c, cat, FakeModel(), SeededDice(1), tracer)
        assert after.stats == c.stats


# ─── 생애 이벤트 ────────────────────────────────────────────────────────


def test_부양가족이_없으면_아이_사건이_후보에_없다():
    딸이_있다 = eligible(LIFE_EVENTS, "female", dependents=1)
    없다 = eligible(LIFE_EVENTS, "female", dependents=0)
    assert any(e.key == "child_sick" for e in 딸이_있다)
    assert not any(e.key == "child_sick" for e in 없다)


def test_사건은_성향을_바꾸고_diff_가_남는다():
    """기획서 §2 — 이벤트 뒤에 전투가 있어야 "이벤트 → 판단 변화" 인과가 닫힌다."""
    tracer, sink = _tracer()
    c = _char("thoma")
    event = next(e for e in LIFE_EVENTS if e.key == "child_sick")
    after, diff = apply_life_event(c, event, FakeModel(), tracer)
    assert after.disposition.risk == c.disposition.risk - 20
    assert diff["delta"]["risk"] == -20 and diff["cause"] == event.title
    assert [e.kind for e in sink.events] == ["life_event", "param_diff"]


def test_성향_변화는_범위를_넘지_않는다():
    tracer, _ = _tracer()
    c = replace(_char("aude"), disposition=replace(_char("aude").disposition, sacrifice=95))
    event = next(e for e in LIFE_EVENTS if e.key == "comrade_debt")  # sacrifice +20
    after, _ = apply_life_event(c, event, FakeModel(), tracer)
    assert after.disposition.sacrifice == 100


def test_사건은_시드가_고르고_후보가_없으면_안_일어난다():
    a = pick({"thoma": list(LIFE_EVENTS)}, SeededDice(1))
    b = pick({"thoma": list(LIFE_EVENTS)}, SeededDice(1))
    assert a == b and a is not None
    assert pick({"thoma": []}, SeededDice(1)) is None


# ─── 성장 포인트 ────────────────────────────────────────────────────────


def test_승리는_10점_그_밖은_6점():
    assert points_for("win") == 10
    assert points_for("retreat") == points_for("lose") == points_for("draw") == 6


def test_안_쓴_포인트는_은행에_쌓인다():
    tracer, _ = _tracer()
    members = [_member("thoma")]
    m1, bank = grant(members, "win", {"thoma": {"agi": 4}}, {}, tracer)
    assert bank["thoma"] == 6 and m1[0][0].stats.agi == _char("thoma").stats.agi + 4
    _, bank2 = grant(m1, "lose", {}, bank, tracer)
    assert bank2["thoma"] == 12


def test_가진_것보다_많이_찍으면_거부한다():
    tracer, _ = _tracer()
    with pytest.raises(ValueError, match="찍으려 한다"):
        grant([_member("thoma")], "win", {"thoma": {"agi": 11}}, {}, tracer)


def test_성장_포인트도_상한_20을_넘지_못한다():
    tracer, _ = _tracer()
    c = replace(_char("thoma"), stats=replace(_char("thoma").stats, agi=19))
    with pytest.raises(ValueError, match="20"):
        grant([(c, choose_build(c), "")], "win", {"thoma": {"agi": 3}}, {}, tracer)


# ─── 인터미션 전체 ──────────────────────────────────────────────────────


def test_인터미션은_세_가지를_한_번씩_한다():
    tracer, sink = _tracer()
    members = [_member("martin"), _member("aude"), _member("thoma")]
    out = run_intermission(
        members,
        "win",
        IntermissionInput(directives={"thoma": "rest"}),
        pool_for,
        FakeModel(),
        SeededDice(5),
        tracer,
        IntermissionState(),
    )
    kinds = [e.kind for e in sink.events]
    assert kinds[0] == "intermission_start"
    assert kinds.count("growth_points") == 3
    assert kinds.count("directive") == 3 and kinds.count("train_result") == 3
    assert kinds.count("life_event") == 1 and kinds.count("param_diff") == 1
    assert len(out) == 3
    지시 = [e.payload["category"] for e in sink.events if e.kind == "directive"]
    assert 지시.count("rest") == 1 and 지시.count("train") == 2  # 기본값은 train


def test_인터미션은_시드에_결정된다():
    def once():
        tracer, sink = _tracer()
        run_intermission(
            [_member("martin"), _member("thoma")],
            "lose",
            IntermissionInput(),
            pool_for,
            FakeModel(),
            SeededDice(9),
            tracer,
            IntermissionState(),
        )
        return [(e.kind, e.actor, e.payload) for e in sink.events]

    assert once() == once()

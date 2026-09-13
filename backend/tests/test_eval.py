"""평가 하네스는 회귀 안전망이다(기획서 §10.1). 이 테스트가 그 안전망을 지킨다."""

import json
from dataclasses import replace

from apps.arena.domain.constants.balance import MAX_CALLS
from apps.arena.domain.entities.trace_event import TraceEvent
from eval.experiments import COMPOSITIONS, _run_once, e1, e3
from eval.metrics import aggregate, metrics_of


def test_지표는_트레이스_후처리만으로_나온다():
    """러너를 고쳐야 지표가 나오면 실험이 코어를 건드리게 된다(기획서 §3.1)."""
    m = _run_once(1, ("martin", "aude", "thoma"), {}, orchestrator=True, adaptation=True)
    assert m.missions and all(x.outcome in ("win", "lose", "retreat", "draw") for x in m.missions)
    assert m.party_size == 3 and 0 <= m.survivors <= 3
    assert m.turns > 0 and m.calls > 0
    assert sum(m.actions.values()) > 0


def test_집계는_비율과_평균을_낸다():
    runs = [
        _run_once(s, ("martin", "aude", "thoma"), {}, orchestrator=True, adaptation=True)
        for s in range(1, 4)
    ]
    a = aggregate(runs)
    assert a["games"] == 3
    for k in ("win_rate", "retreat_rate", "loss_rate", "draw_rate", "survival_rate"):
        assert 0.0 <= a[k] <= 1.0
    # 판 단위 네 비율은 합이 1 이다(3자리 반올림 오차만큼 벌어진다).
    assert abs(a["win_rate"] + a["retreat_rate"] + a["loss_rate"] + a["draw_rate"] - 1.0) < 0.005
    assert abs(sum(a["grade_share"].values()) - 1.0) < 0.005
    # 상한은 **판당** MAX_CALLS 다(기획서 §7.1). 리터럴 300 을 쓰면 단일 출처
    # 밖이고, 계약이 길어지면 뜻까지 틀린다(QA 재검 2026-09-09 R13).
    assert a["max_calls"] <= MAX_CALLS, "판당 호출 상한을 넘었다"


def test_E1_은_같은_시드로_같은_결과를_낸다():
    """실험이 재현되지 않으면 차트가 근거가 되지 못한다(설계 §3.4)."""
    a = e1(seeds=2)
    b = e1(seeds=2)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_E1_은_조합_넷과_ON_OFF_를_모두_담는다():
    r = e1(seeds=2)
    assert {c["key"] for c in r["compositions"]} == {c.key for c in COMPOSITIONS}
    for c in r["compositions"]:
        assert c["on"]["games"] == 2 and c["off"]["games"] == 2
        assert c["off"]["avg_plans"] == 0, "감독 OFF 인데 작전이 수립됐다"
        assert c["on"]["avg_plans"] > 0, "감독 ON 인데 작전이 없다"


def test_E1_은_완주와_생환_두_축을_함께_낸다():
    """QA 2026-09-09 V1 — 완주율만 내면 감독이 목표를 포기하고 전원을 데리고
    나온 판이 벌점이 되어, E1 이 기획서 §8.1("나쁜 조합에서의 회복력")을
    스스로 반증한다. 「철수」는 벌점이 아니다(v3 §7.1b).
    """
    r = e1(seeds=3)
    for c in r["compositions"]:
        assert c["paired"]["games"] == 3 and c["paired_home"]["games"] == 3
        for side in ("on", "off"):
            assert 0.0 <= c[side]["clear_rate"] <= 1.0
            assert 0.0 <= c[side]["home_rate"] <= 1.0


def test_E3_은_성향_수치만_바꾼다():
    r = e3(seeds=2)
    axes = {a["axis"] for a in r["axes"]}
    assert axes == {"risk", "sacrifice", "cooperation"}
    for a in r["axes"]:
        assert [row["level"] for row in a["levels"]] == [-80, 0, 80]


def test_희생_수용도가_높으면_이탈이_줄어든다():
    """기획서 §5.1 "항상 순응하는 캐릭터가 최강인가" 의 재료 — 축이 실제로 듣는가."""
    r = e3(seeds=4)
    sac = next(a for a in r["axes"] if a["axis"] == "sacrifice")
    낮음 = next(x for x in sac["levels"] if x["level"] == -80)["avg_deviations"]
    높음 = next(x for x in sac["levels"] if x["level"] == 80)["avg_deviations"]
    assert 높음 < 낮음, f"희생 수용도가 이탈에 영향이 없다: {낮음} → {높음}"


# ─── 계약 전체를 재는가 (QA 2026-09-09 V1) ──────────────────────────────


def _ev(seq, mission, kind, payload):
    return TraceEvent("r", seq, "T", mission, 0, kind, None, payload)


def _two_mission_trace(first: str, second: str) -> list[TraceEvent]:
    """1판 등급 `first`, 2판 등급 `second` 인 최소 트레이스."""

    def end(seq, no, grade):
        win = grade in ("full_success", "success")
        return _ev(
            seq,
            no,
            "mission_end",
            {
                "no": no,
                "outcome": "win" if win else "lose",
                "grade": grade,
                "turns": 5,
                "survivors": ["a", "b"] if win else [],
                "fled": [],
                "dead": [],
                "injured": [] if win else ["a", "b"],
                "taken": [],
                "calls_used": 10,
                "plans": 1,
                "abandoned": False,
            },
        )

    return [
        _ev(0, 0, "run_start", {"lineup": ["a", "b", "c"]}),
        end(1, 7, first),
        end(2, 6, second),
    ]


def test_지표는_마지막_판이_아니라_계약_전체를_잰다():
    """QA 2026-09-09 V1 — E1 이 감독이 아니라 **직전 판 끌려감 주사위**를 재고 있었다.

    마지막 미션의 승패만 승률로 쓰면 1판의 참사가 통째로 사라진다. 1판을
    말아먹고 2판을 이긴 계약과, 두 판 다 이긴 계약이 같은 점수를 받았다.
    """
    말아먹고_이김 = metrics_of(_two_mission_trace("disaster", "full_success"))
    둘_다_이김 = metrics_of(_two_mission_trace("full_success", "full_success"))

    assert len(말아먹고_이김.missions) == 2, "1판이 지표에서 사라졌다"
    assert not 말아먹고_이김.contract_clear
    assert 둘_다_이김.contract_clear
    assert 말아먹고_이김.cleared == 1 and 둘_다_이김.cleared == 2
    assert 말아먹고_이김.turns == 10, "턴은 계약 전체의 합이다"


def test_집계는_판_단위_승률과_계약_단위_완주율을_따로_낸다():
    runs = [
        metrics_of(_two_mission_trace("disaster", "full_success")),
        metrics_of(_two_mission_trace("full_success", "full_success")),
    ]
    a = aggregate(runs)
    assert a["win_rate"] == 0.75, "판 4개 중 3개를 이겼다"
    assert a["clear_rate"] == 0.5, "계약 2개 중 1개만 완주했다"
    assert a["grade_share"]["full_success"] == 0.75
    assert a["grade_share"]["disaster"] == 0.25


def test_지목_추적은_소환_가속을_지목으로_읽지_않는다():
    """QA 재검 2026-09-09 R12 — `summon_faster` 의 `effect.after` 는 소환 주기(정수)다.
    `field` 를 안 보면 `2` 가 truthy 라 "지목" 이 되고, 이후 보스 타격이 전부
    안 맞는 지목으로 계수되며 **살아 있는 진짜 지목까지 지워진다.**
    """
    from eval.metrics import _focus_follow

    events = [
        _ev(0, 6, "boss_adapt", {"effect": {"field": "boss_focus", "after": "thoma"}}),
        _ev(1, 6, "resolution", {"strikes": [{"target": "thoma"}, {"target": "martin"}]}),
        # 소환 가속 — 지목이 아니다. 앞의 지목이 살아 있어야 한다.
        _ev(2, 6, "boss_adapt", {"effect": {"field": "summon_every", "before": 3, "after": 2}}),
        _ev(3, 6, "resolution", {"strikes": [{"target": "thoma"}]}),
    ]
    events = [replace(e, actor="minotaur") for e in events]
    out = _focus_follow(events)
    assert out == {"focus_strikes": 3, "focus_followed": 2}

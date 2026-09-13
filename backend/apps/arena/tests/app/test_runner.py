import pytest

from apps.arena.adapter.outbound.strategies.dice import SeededDice
from apps.arena.adapter.outbound.strategies.harness.harness import Harness
from apps.arena.adapter.outbound.strategies.llm.fake import FakeModel
from apps.arena.app.use_cases.runner import run
from apps.arena.domain.entities.trace_event import judgment_view
from apps.arena.domain.entities.types import RunConfig
from content.missions import MISSIONS_A
from content.party import build_party


def _config(
    seed=1, lineup=("martin", "aude", "thoma"), orchestrator=True, adaptation=True, classes=None
):
    return RunConfig(
        seed=seed,
        lineup=tuple(lineup),
        allocations={},
        classes=classes or {},
        genders={},
        orchestrator_on=orchestrator,
        adaptation_on=adaptation,
        missions=MISSIONS_A,
        intermission=False,
    )


def _run(config, run_id="r", horn=None, recovery=None):
    return run(
        run_id,
        config,
        build_party(config),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        dice_factory=SeededDice,
        clock=lambda: "T",
        horn=horn,
        recovery=recovery,
    )


def _strip_ts(events):
    return [judgment_view(e) for e in events]


def test_A단계_한_판이_30턴_안에_끝난다():
    rec = _run(_config())
    res = rec.results[0]
    assert res.outcome in ("win", "lose", "retreat", "draw") and res.turns <= 30
    kinds = [e.kind for e in rec.events]
    assert kinds[0] == "run_start" and kinds[-1] == "run_end"
    assert "mission_start" in kinds and "mission_end" in kinds and "plan" in kinds


def test_같은_시드는_같은_트레이스를_만든다():
    """리플레이·실험의 전제(설계 §3.4). ts 만 빼고 바이트 단위로 같다."""
    a = _run(_config(seed=7))
    b = _run(_config(seed=7))
    assert _strip_ts(a.events) == _strip_ts(b.events)


def test_다른_시드는_다른_판을_만든다():
    outcomes = {(_run(_config(seed=s)).results[0].turns) for s in range(1, 8)}
    assert len(outcomes) > 1


def test_감독_OFF_면_plan_이벤트가_없다():
    rec = _run(_config(orchestrator=False))
    assert not [e for e in rec.events if e.kind == "plan"]
    assert rec.results[0].plans == 0


def test_호출_수는_상한_안이고_mission_end_에_남는다():
    rec = _run(_config())
    end = [e for e in rec.events if e.kind == "mission_end"][0]
    assert 0 < end.payload["calls_used"] <= 300


@pytest.mark.parametrize("seed", range(1, 41))
def test_어느_시드든_예외_없이_끝난다(seed):
    rec = _run(_config(seed=seed, lineup=("martin", "gilles", "agnes")))
    assert rec.results[0].outcome in ("win", "lose", "retreat", "draw")


def test_후퇴가_실제로_발생하는_시드가_있다():
    """기획서 §5 — 무조건 싸우는 게임이 아니다. 포기 판단이 트레이스에 남아야 한다."""
    found = None
    for seed in range(1, 120):
        # 지원 둘만 보내면 화력이 없어 승산이 무너진다 — 조합은 유저의 시험 문제다(§8.1).
        rec = _run(_config(seed=seed, lineup=("aude", "agnes")))
        if any(r.abandoned for r in rec.results):
            found = rec
            break
    assert found is not None, (
        "120개 시드에서 후퇴가 한 번도 없다 — 승산 붕괴가 감독에게 닿지 않는다"
    )
    kinds = [e.kind for e in found.events]
    assert "abandon" in kinds and "replan_trigger" in kinds
    assert all(r.outcome in ("retreat", "lose", "draw", "win") for r in found.results)


def test_출전_인원_상한을_넘으면_거부한다():
    """하한은 1 이다 — 혼자 가는 것도 단주의 선택(기획서 §7.2·§8.1)."""
    build_party(_config(lineup=("martin",)))
    build_party(_config(lineup=("martin", "aude")))
    with pytest.raises(ValueError, match="1~3명"):
        build_party(_config(lineup=("martin", "aude", "thoma", "agnes")))


def test_같은_캐릭터_중복_출전은_거부한다():
    with pytest.raises(ValueError):
        build_party(_config(lineup=("martin", "martin", "thoma")))


def test_트롤픽_전사_셋도_돈다():
    cfg = _config(
        lineup=("gilles", "aude", "agnes"),
        classes={"gilles": "warrior", "aude": "warrior", "agnes": "warrior"},
    )
    rec = _run(cfg)
    assert rec.results[0].outcome in ("win", "lose", "retreat", "draw")
    start = rec.events[0].payload
    assert all(r["class"] == "warrior" for r in start["roster"])


# ─── QA 라운드 1 회귀 ──────────────────────────────────────────────────


def test_이탈과_적응이_실제로_재계획을_부른다():
    """기획서 §8.3 의 트리거 4종 중 둘이 죽어 있었다(QA 라운드 1 P0-1).

    신호는 턴 안에서 쌓이고 다음 턴 시작에 읽힌다 — 읽기 전에 비우면 안 된다.
    """
    kinds = set()
    for seed in range(1, 12):
        rec = _run(_config(seed=seed))
        kinds |= {e.payload["trigger"] for e in rec.events if e.kind == "replan_trigger"}
    assert "deviation" in kinds, "이탈이 재계획을 부르지 않는다"
    assert "adaptation" in kinds, "보스 적응이 재계획을 부르지 않는다"


def test_30턴까지_모든_유닛이_행동한다():
    """QA 라운드 1 P1-4 — 턴 상한을 유닛 루프 안에서 보면 마지막 턴이 잘린다."""
    for seed in range(1, 200):
        rec = _run(_config(seed=seed))
        if rec.results[0].outcome != "draw":
            continue
        last = max(e.turn for e in rec.events)
        order = [e for e in rec.events if e.kind == "turn_start" and e.turn == last][0]
        차례 = [o["unit"] for o in order.payload["order"]]
        acted = {e.actor for e in rec.events if e.kind == "resolution" and e.turn == last}
        # 자기 차례 전에 쓰러지거나 빠져나간 유닛은 행동하지 못한다 — 그건 정상이다.
        사라짐: set[str] = set()
        for e in rec.events:
            if e.turn != last:
                continue
            if e.kind == "resolution":
                for st in e.payload["strikes"]:
                    if st["killed"]:
                        사라짐.add(st["target"])
                if e.payload.get("flee_success"):
                    사라짐.add(e.actor)
        기대 = [u for u in 차례 if u not in 사라짐 - acted]
        assert acted >= set(기대) - 사라짐, f"seed {seed}: 마지막 턴이 잘렸다"
        assert len(acted) >= len(차례) - len(사라짐), f"seed {seed}: 마지막 턴이 잘렸다"
        return
    raise AssertionError("무승부 시드를 찾지 못했다 — 이 테스트가 아무것도 재지 않는다")


def test_전사는_실제로_적을_친다():
    """QA 라운드 1 P0-4 — Fake 가 스킬 목록 첫 번째를 골라 자기 방어만 했다."""
    total = 0
    for seed in range(1, 6):
        rec = _run(_config(seed=seed))
        total += sum(
            s["damage"]
            for e in rec.events
            if e.kind == "resolution" and e.actor == "martin"
            for s in e.payload["strikes"]
        )
    assert total > 0, "전사가 다섯 판 동안 아무에게도 피해를 주지 못했다"


def test_봄에는_아무도_죽지_않는다():
    """기획서 v3 §6.0 — 1~4 출동 사망 0%. 고블린은 죽이기보다 끌고 간다.

    A단계 미션은 6·5회차라 봄이 아니다(2026-09-08 팀 결정 ①). 봄 구간을
    직접 만들어 확률표의 0% 가 실제로 지켜지는지 잰다.
    """
    from dataclasses import replace as _replace

    from content.environments import SWAMP
    from content.missions import MISSION_NIGHT_RAID
    from content.monsters import GOBLIN_BAND

    봄 = (
        _replace(
            MISSION_NIGHT_RAID,
            no=1,
            name="마을 방어",
            enemy=GOBLIN_BAND,
            environment=SWAMP,
            casualty_tier="spring",
        ),
    )
    쓰러진_적_있다 = False
    for seed in range(1, 40):
        cfg = _replace(_config(seed=seed, lineup=("thoma", "aude")), missions=봄)
        rec = _run(cfg)
        for res in rec.results:
            assert not res.dead, f"seed {seed}: 봄인데 {res.dead} 가 죽었다"
            쓰러진_적_있다 = 쓰러진_적_있다 or bool(res.injured or res.taken)
    assert 쓰러진_적_있다, "아무도 쓰러지지 않아 이 테스트가 아무것도 재지 않는다"


def test_사망하거나_끌려간_단원은_다음_판에_나오지_않는다():
    """사망은 소멸이고(기획서 §6.6), 끌려간 사람은 굴에 있다(v3 §6.8)."""
    from dataclasses import replace as _replace

    from content.missions import MISSIONS_B

    # 가을 구간(사망 20%)으로 바꿔 실제로 잃는 판을 만든다.
    가을 = tuple(_replace(m, casualty_tier="autumn") for m in MISSIONS_B)
    for seed in range(1, 60):
        cfg = _replace(_config(seed=seed, lineup=("thoma", "aude")), missions=가을)
        rec = _run(cfg)
        빠진_사람 = set(rec.results[0].dead) | set(rec.results[0].taken)
        if len(rec.results) < 2 or not 빠진_사람:
            continue
        second = [e for e in rec.events if e.kind == "mission_start"][1]
        나온_사람 = {p["id"] for p in second.payload["party"]}
        assert not (빠진_사람 & 나온_사람), (
            f"seed {seed}: {빠진_사람 & 나온_사람} 이(가) 2판에 섰다"
        )
        return
    raise AssertionError(
        "1판에 사망·끌려감이 나오는 시드를 찾지 못했다 — 이 테스트가 아무것도 재지 않는다"
    )


# ─── 뿔피리 (기획서 v3 §8.2) ────────────────────────────────────────────


def _horn_at(turn: int):
    """지정한 턴에 한 번만 울리는 뿔피리. 세션의 큐를 흉내낸다."""
    state = {"blown": False}

    def horn(_mission: int, battle_turn: int) -> bool:
        if battle_turn >= turn and not state["blown"]:
            state["blown"] = True
            return True
        return False

    return horn


def test_뿔피리를_불면_그_자리에서_판이_끝난다():
    """기획서 v3 §8.2 — 즉시 이탈. 전멸은 피하지만 목표는 실패하고 보수는 없다."""
    rec = _run(_config(seed=3), horn=_horn_at(2))
    res = rec.results[0]
    assert res.outcome == "retreat"
    assert res.turns <= 3, "뿔피리를 불었는데 판이 계속됐다"
    assert [e.kind for e in rec.events].count("horn") == 1


def test_뿔피리로_끝난_판은_철수지_실패가_아니다():
    """「철수」가 벌점이 아닌 것이 핵심이다(기획서 v3 §7.1b)."""
    rec = _run(_config(seed=3), horn=_horn_at(2))
    assert rec.results[0].grade == "withdraw"


def test_뿔피리를_불지_않으면_판이_그대로_돈다():
    없음 = _run(_config(seed=3))
    불었다 = _run(_config(seed=3), horn=_horn_at(2))
    assert 없음.results[0].turns > 불었다.results[0].turns


def test_뿔피리는_전원을_살려_내보낸다():
    rec = _run(_config(seed=3), horn=_horn_at(2))
    res = rec.results[0]
    assert not res.dead and not res.taken, "뿔피리를 불었는데 사람을 잃었다"
    assert len(res.fled) == 3


# ─── 보스 호칭 (기획서 v3 §8.5) ─────────────────────────────────────────


def test_첫_끌려감이_보스의_이름이_된다():
    """대원들은 그것이 처음 데려간 사람의 이름으로 그것을 부른다."""
    from dataclasses import replace as _replace

    from content.missions import MISSIONS_A

    # 지원 둘만 보내면 화력이 없어 실제로 쓰러진다 — 조합은 유저의 시험 문제다.
    여름 = tuple(_replace(m, casualty_tier="summer") for m in MISSIONS_A)
    for seed in range(1, 80):
        cfg = _replace(_config(seed=seed, lineup=("aude", "agnes")), missions=여름)
        rec = _run(cfg)
        끌려간 = [t for r in rec.results for t in r.taken]
        if not 끌려간:
            continue
        named = [e for e in rec.events if e.kind == "boss_named"]
        assert len(named) == 1, "호칭은 첫 끌려감에 한 번만 붙는다"
        assert named[0].payload["after"].endswith("데려간 것")
        assert named[0].payload["member"] == 끌려간[0]
        assert rec.boss_title == named[0].payload["after"]
        return
    raise AssertionError("끌려감이 나오는 시드를 찾지 못했다 — 이 테스트가 아무것도 재지 않는다")


def test_호칭이_붙으면_보스가_그_이름으로_선다():
    """호칭이 실제로 유닛에 입혀지는지 본다.

    "1판에서 끌려가고 2판이 도는" 시드를 찾는 방식은 쓰지 않는다 — 야습이
    충분히 쉬워 그런 시드가 없고, 있더라도 밸런스가 바뀌면 테스트가 조용히
    공허해진다. 적용 자체를 직접 잰다.
    """
    from apps.arena.app.use_cases.battle_setup import setup_battle
    from content.missions import MISSION_JUVENILE_BOSS

    members = build_party(_config())
    호칭 = "토마를 데려간 것"
    b = setup_battle(MISSION_JUVENILE_BOSS, members, seed=1, adaptation_on=True, boss_title=호칭)
    보스 = [u for u in b.units.values() if u.is_boss]
    assert len(보스) == 1 and 보스[0].name == 호칭

    # 호칭이 없으면 원래 이름 그대로다.
    b2 = setup_battle(MISSION_JUVENILE_BOSS, members, seed=1, adaptation_on=True)
    assert [u for u in b2.units.values() if u.is_boss][0].name == "굴의 그것"


# ─── 회수 결정 (기획서 v3 §6.8) ─────────────────────────────────────────


def _taken_run(decide=None, seeds=range(1, 80)):
    """끌려감이 실제로 나오는 판 하나를 찾아 돌린다."""
    from dataclasses import replace as _replace

    from content.missions import MISSIONS_A

    여름 = tuple(_replace(m, casualty_tier="summer") for m in MISSIONS_A)
    for seed in seeds:
        cfg = _replace(_config(seed=seed, lineup=("aude", "agnes")), missions=여름)
        rec = _run(cfg, recovery=decide)
        if any(r.taken for r in rec.results):
            return rec
    raise AssertionError("끌려감이 나오는 시드를 찾지 못했다 — 이 테스트가 아무것도 재지 않는다")


def test_결정하지_않으면_미지불로_영구_상실이다():
    """기한을 넘기면 자동 미지불이다(기획서 v3 §6.8)."""
    rec = _taken_run()
    res = next(r for r in rec.results if r.taken)
    assert res.recovery_unpaid == res.taken and res.recovery_paid == ()
    두고_온 = {m for m, _, _ in rec.forsaken}
    assert 두고_온 == set(res.taken), "미지불이 「섭식」 대상으로 남지 않았다"


def test_지불하면_섭식_대상에서_빠진다():
    """지불의 값이 여기서 생긴다 — 보스가 그 사람에게서 배우지 못한다(§8.4)."""
    rec = _taken_run(decide=lambda ids, costs, _t: set(ids))
    res = next(r for r in rec.results if r.taken)
    assert res.recovery_paid == res.taken and res.recovery_unpaid == ()
    assert rec.forsaken == ()


def test_회수_결정이_비용과_함께_트레이스에_남는다():
    rec = _taken_run()
    ev = [e for e in rec.events if e.kind == "recovery"]
    assert ev, "회수 결정이 트레이스에 없다"
    p = ev[0].payload
    assert p["member"] and p["paid"] is False and isinstance(p["cost"], int)


# ─── 학습 카드 (기획서 v3 §8.4) ─────────────────────────────────────────


def _card_run(seed=3, **over):
    from content.cards import CARDS

    return run(
        "r",
        _config(seed=seed, **over),
        build_party(_config(seed=seed, **over)),
        model_factory=lambda _n: Harness(FakeModel(), FakeModel()),
        dice_factory=SeededDice,
        clock=lambda: "T",
        card_pool=CARDS,
    )


def test_보스전에서만_카드가_펼쳐진다():
    """일반전은 카드를 안 쓴다. 슬롯이 보스 형태에만 있다."""
    rec = _card_run()
    카드들 = [e for e in rec.events if e.kind == "cards"]
    assert len(카드들) == 1, "카드가 보스전 말고 다른 데서도 펼쳐졌다"
    보스_시작 = [e for e in rec.events if e.kind == "mission_start"][1]
    assert 카드들[0].seq > 보스_시작.seq


def test_카드는_출처와_관측을_들고_온다():
    """인스펙터가 출처를 가리킬 수 있어야 한다 — 그러지 않으면 그냥 표시다."""
    rec = _card_run()
    cards = [e for e in rec.events if e.kind == "cards"][0].payload["cards"]
    assert cards, "보스전인데 카드가 하나도 없다"
    for c in cards:
        assert c["source"] in ("scout", "flight", "loot", "feeding")
        assert c["observation"] and "{" not in c["observation"], c
        assert c["applied"], f"카드가 아무것도 안 했다: {c}"


def test_카드는_슬롯을_넘지_않는다():
    from apps.arena.domain.constants.balance import CARD_SLOTS

    rec = _card_run()
    cards = [e for e in rec.events if e.kind == "cards"][0].payload["cards"]
    assert len(cards) <= CARD_SLOTS["boss_juvenile"]


def test_같은_시드는_같은_카드를_낸다():
    a = [e for e in _card_run().events if e.kind == "cards"][0].payload["cards"]
    b = [e for e in _card_run().events if e.kind == "cards"][0].payload["cards"]
    assert [c["key"] for c in a] == [c["key"] for c in b]


def test_원거리_편성이면_사거리_카드가_나온다():
    """QA 2026-09-09 C1·J4 — `ranged_ids` 에 빈 집합이 박혀 있어 「사거리」가
    영원히 안 나왔다. 단위 테스트는 인자를 직접 넘겨서 못 잡았다.

    러너를 **통과하는** 경로로 잰다.
    """
    from content.classes import WEAPONS

    # 토마(장궁)·오드(나팔) 가 원거리다. 다만 앞판에서 누가 끌려가면 보스전에
    # 서는 원거리 수가 줄어든다 — 기대값을 **보스전에 실제로 선 사람**에게서
    # 뽑는다. 그래야 밸런스 튜닝이 이 테스트를 깨뜨리지 않는다.
    rec = _card_run(seed=3, lineup=("thoma", "aude", "martin"))
    보스_시작 = [e for e in rec.events if e.kind == "mission_start"][1]
    선_원거리 = [u["id"] for u in 보스_시작.payload["party"] if WEAPONS[u["weapon"]].ranged]
    assert 선_원거리, "원거리가 보스전에 하나도 안 섰다 — 다른 시드로 재야 한다"

    cards = [e for e in rec.events if e.kind == "cards"][0].payload["cards"]
    keys = {c["key"] for c in cards}
    assert "range" in keys, f"원거리를 내보냈는데 「사거리」가 없다: {keys}"
    사거리 = next(c for c in cards if c["key"] == "range")
    assert 사거리["evidence"]["count"] == len(선_원거리)
    assert 사거리["applied"]["units"] == 선_원거리, "「사거리」가 원거리 아닌 사람을 겨눴다"


def test_섭식_카드는_두고_온_사람의_병과를_지금_사람에게_건다():
    """QA 2026-09-09 J5·T5 — `forsaken` 은 정의상 이 판에 없는 사람이라
    `대상 in battle.units` 가 항상 거짓이었다. 100% 무효인데 화면은
    "배웠다" 고 단언했다.

    그것이 배운 것은 사람이 아니라 **그 병과를 상대하는 법**이다.
    """
    from apps.arena.adapter.outbound.sinks.list_sink import ListSink
    from apps.arena.app.use_cases.battle_setup import setup_battle
    from apps.arena.app.use_cases.learning_cards import apply_cards
    from apps.arena.domain.entities.trace_event import Tracer
    from apps.arena.domain.services.judgment.cards import choose_cards
    from content.cards import CARDS
    from content.missions import MISSION_JUVENILE_BOSS

    members = build_party(_config(lineup=("thoma", "aude", "martin")))
    b = setup_battle(MISSION_JUVENILE_BOSS, members, seed=1, adaptation_on=True)
    sink = ListSink()
    tracer = Tracer("t", sink, clock=lambda: "T")
    # 굴에 두고 온 장궁병 — 이 판에 없다. 그런데 토마가 같은 병과로 서 있다.
    cards = choose_cards([], set(), (("someone", "archer", 7),), 3, CARDS)
    apply_cards(b, cards, tracer)
    펼친 = sink.events[-1].payload["cards"]
    섭식 = next(c for c in 펼친 if c["key"] == "devoured")
    assert 섭식["applied"], "섭식이 여전히 무효다"
    assert 섭식["applied"]["after"] == "thoma"
    assert 섭식["applied"]["inherited_from"] == "someone"


# ─── 계약 길이와 호출 예산 (QA 2026-09-09 V2) ───────────────────────────


def test_긴_계약도_판마다_예산을_받는다():
    """QA 2026-09-09 V2 — `MAX_CALLS` 가 **런당 하나**의 하네스에 걸려 있어,
    18출동을 흉내 내면 8회차부터 모든 판단이 조용히 Fake 로 떨어졌다.
    게다가 예산이 바닥나면 하네스가 호출을 세지 않아 `calls_used` 가 0 이 되고,
    "호출 300 이하" 검사가 **모델을 아예 안 쓴 판에서 가장 예쁘게 통과**했다.

    예산은 기획서 §7.1 대로 **전투 한 판당** 이다 — 계약이 길어지면 같이 늘어난다.
    """
    from apps.arena.adapter.outbound.strategies.llm.select import build_harness
    from apps.arena.domain.constants.balance import MAX_CALLS
    from content.missions import MISSION_JUVENILE_BOSS, MISSION_NIGHT_RAID

    # **예산이 계약 길이에 비례하는가** 를 직접 잰다. 러너를 도는 것만으로는
    # 못 잡는다 — 전에 쓰던 편성(seed=1)은 11판째 전멸해 합계 293 호출로
    # 끝나서 옛 상한 300 에 **닿지도 못했다.** 고친 코드와 버그 코드가 바이트
    # 단위로 같은 결과를 냈고 테스트는 초록이었다(QA 재검 2026-09-09 R11).
    assert build_harness(missions=18)._max_calls == MAX_CALLS * 18
    assert build_harness(missions=1)._max_calls == MAX_CALLS

    긴_계약 = (MISSION_NIGHT_RAID, MISSION_JUVENILE_BOSS) * 9  # 18출동
    # 18판을 **완주하는** 편성이라야 옛 상한을 넘겨 폴백이 드러난다.
    cfg = _config(seed=7, lineup=("martin", "aude", "agnes"))
    cfg = RunConfig(**{**cfg.__dict__, "missions": 긴_계약})
    rec = run(
        "long",
        cfg,
        build_party(cfg),
        model_factory=build_harness,
        dice_factory=SeededDice,
        clock=lambda: "T",
    )
    끝 = [e for e in rec.events if e.kind == "mission_end"]
    assert len(끝) == 18, f"18판을 완주하는 편성이라야 예산에 닿는다: {len(끝)}판"
    assert sum(e.payload["calls_used"] for e in 끝) > MAX_CALLS, (
        "옛 상한(런당 하나)을 넘기지 못하면 이 테스트는 버그를 되돌려도 초록이다"
    )
    for e in 끝:
        assert e.payload["fallbacks"] == 0, (
            f"{e.payload['no']}회차에서 조용히 폴백했다: {e.payload['fallbacks']}회"
        )
        assert 0 < e.payload["calls_used"] <= MAX_CALLS, (
            f"{e.payload['no']}회차의 호출 수가 이상하다: {e.payload['calls_used']}"
        )


def test_예산을_넘긴_폴백도_호출로_센다():
    """예산이 바닥났다고 계수를 멈추면 `calls_used` 가 거짓말을 한다 —
    "모델을 안 썼다" 가 "싸게 돌았다" 로 보인다.
    """
    from apps.arena.adapter.outbound.strategies.harness.harness import Harness as H
    from apps.arena.app.use_cases.agents.schemas import CHARACTER_SCHEMA

    h = H(FakeModel(), FakeModel(), max_calls=1)
    for _ in range(3):
        h.decide("character", "p", CHARACTER_SCHEMA)
    assert h.calls_used == 3, "예산 밖 호출이 계수에서 빠졌다"
    assert h.fallbacks == 2 and h.budget_skips == 2


def test_mission_end_는_회수_결정을_담고_나온다():
    """QA 2026-09-09 V3·K — emit 이 회수 결정보다 **먼저**라 `recovery_paid` 가
    영원히 빈 배열이었다. 같은 dataclass 가 트레이스에선 빈 값, `run_end` 에선
    채운 값으로 두 번 나왔다 — **빠진 필드가 아니라 거짓말하는 필드**다.
    저장된 런을 다시 읽으면 회수 정보가 통째로 사라졌다.
    """
    낸다 = []

    def recovery(ids, costs, _tracer):
        낸다.extend(ids)
        return set(ids)  # 전부 회수한다

    rec = _run(_config(seed=10, lineup=("thoma", "aude", "martin")), recovery=recovery)
    assert 낸다, "이 시드에서 끌려간 사람이 없다 — 테스트가 아무것도 안 재고 있다"

    끌려간_판 = [e for e in rec.events if e.kind == "mission_end" and e.payload["taken"]]
    assert 끌려간_판, "끌려간 사람이 있는데 mission_end 가 그걸 모른다"
    for e in 끌려간_판:
        assert e.payload["recovery_paid"], f"회수 결정이 안 실렸다: {e.payload}"

    # 순서: 사상자 판정 → 회수 결정 → 판 집계. 집계가 결정보다 먼저면 거짓말한다.
    kinds = [e.kind for e in rec.events]
    첫_회수 = kinds.index("recovery")
    assert kinds.index("casualty") < 첫_회수 < kinds.index("mission_end")


def test_회수를_묻기_전에_비용이_화면으로_간다():
    """QA 2026-09-09 L·C2·U8 — 유저가 **값을 모른 채** 결정하고 있었다.
    비용은 러너가 계산해 놓고 훅에 넘긴 뒤 그대로 버려졌다(`_ = costs`).

    훅이 트레이스를 받으므로 물어보기 전에 값을 화면에 띄울 수 있다.
    """
    본_비용 = {}

    def recovery(ids, costs, tracer):
        본_비용.update(costs)
        tracer.emit("recovery", {"awaiting_input": True, "costs": costs, "timeout_s": 60})
        return set()

    rec = _run(_config(seed=10, lineup=("thoma", "aude", "martin")), recovery=recovery)
    assert 본_비용 and all(v > 0 for v in 본_비용.values()), f"비용이 안 왔다: {본_비용}"

    물음 = [e for e in rec.events if e.kind == "recovery" and e.payload.get("awaiting_input")]
    결정 = [e for e in rec.events if e.kind == "recovery" and not e.payload.get("awaiting_input")]
    assert 물음 and 결정, "묻는 이벤트와 답하는 이벤트가 둘 다 있어야 한다"
    assert 물음[0].seq < 결정[0].seq, "값을 보여주기 전에 결정을 기록했다"


# ─── 전령관 부재 시 신호 지연 (기획서 v3 §8.2) ──────────────────────────


def _horn_turns(rec):
    return [e.payload["turn"] for e in rec.events if e.kind == "horn"]


def test_전령관이_없으면_신호가_한_턴_늦는다():
    """QA 2026-09-09 T·J8 — 주석은 "그 지연은 core 가 판단한다" 고 말했지만
    core 에는 그 코드가 없었다. 기획서 v3 §8.2 의 병과 가치가 통째로 비어 있었다.

    뿔피리는 전령관이 분다. 없으면 누군가 대신 부느라 한 턴을 잃는다.
    """
    울린_턴 = 3

    def once():
        울린 = []

        def horn(_mission, turn):
            if turn == 울린_턴 and not 울린:
                울린.append(turn)
                return True
            return False

        return horn

    있음 = _run(_config(lineup=("thoma", "aude", "martin")), horn=once())  # 오드가 전령관
    없음 = _run(_config(lineup=("thoma", "gilles", "martin")), horn=once())  # 전령관 없음

    assert _horn_turns(있음)[0] == 울린_턴, "전령관이 있는데 신호가 늦었다"
    assert _horn_turns(없음)[0] == 울린_턴 + 1, "전령관이 없는데 신호가 제때 닿았다"


def test_지연된_신호도_한_번만_터진다():
    """묵혀 둔 신호가 매 턴 다시 울리면 뿔피리가 무한이 된다.

    그리고 `horn` 이벤트는 **닿은 턴에 하나뿐**이어야 한다 — 지연을 따로
    이벤트로 내면 리플레이가 그 턴에도 뿔피리를 분다(J1 회귀).
    """
    울린 = []

    def once(_mission, turn):
        if turn == 2 and not 울린:
            울린.append(turn)
            return True
        return False

    rec = _run(_config(lineup=("thoma", "gilles", "martin")), horn=once)
    turns = _horn_turns(rec)
    assert turns == [3], f"신호가 한 번만, 늦게 닿아야 한다: {turns}"
    e = next(x for x in rec.events if x.kind == "horn")
    assert e.payload["delayed_from"] == 2


def test_전령관이_쓰러지면_그_판은_지연을_받는다():
    """부는 사람이 서 있어야 제때 분다 — 나팔은 쓰러진 사람이 불지 못한다."""
    from apps.arena.app.use_cases.battle_setup import herald_present, setup_battle
    from content.missions import MISSION_JUVENILE_BOSS

    members = build_party(_config(lineup=("thoma", "aude", "martin")))
    b = setup_battle(MISSION_JUVENILE_BOSS, members, seed=1, adaptation_on=True)
    assert herald_present(b)
    b.units["aude"].alive = False
    assert not herald_present(b)


def test_카드는_출처_라운드를_들고_온다():
    """QA 2026-09-09 V(J9) — 기획서 v3 §11 은 카드마다 **출처 라운드·인물·종**을
    링크하라고 한다. 종과 인물은 있었지만 라운드가 없었다 — "몇 회차에 그것이
    이걸 봤는가" 를 못 짚으면 판을 넘는 학습이 아니라 그냥 표시다.
    """
    rec = _card_run(seed=3, lineup=("thoma", "aude", "martin"))
    cards = [e for e in rec.events if e.kind == "cards"][0].payload["cards"]
    회차 = [e.payload["no"] for e in rec.events if e.kind == "mission_start"]
    assert cards
    for c in cards:
        assert c["round"] in 회차, f"출처 라운드가 없거나 이 계약의 회차가 아니다: {c}"


# ─── 원본 → 리플레이 왕복 (QA 재검 2026-09-09 P0-A·P0-B) ────────────────


def _replay_horn(events):
    """라우터의 리플레이 훅과 **같은 규칙**으로 유저 입력을 복원한다.

    라우터가 이 규칙을 갖고 있었지만 그것을 지나는 테스트가 저장소에 하나도
    없었다 — 그래서 "같은 시드 = 같은 판" 이 뿔피리가 낀 판에서 깨진 채
    "고쳤다" 로 닫혔다. 규칙을 여기서 다시 적어 네 조합 전부를 지난다.
    """
    horn_turns = {
        (e.mission, e.payload.get("delayed_from") or e.payload.get("turn"))
        for e in events
        if e.kind == "horn"
    }
    fired: set[tuple[int, int]] = set()

    def horn(mission: int, turn: int) -> bool:
        if (mission, turn) in horn_turns and (mission, turn) not in fired:
            fired.add((mission, turn))
            return True
        return False

    return horn


def _판정(rec):
    return (
        [r.outcome for r in rec.results],
        [r.grade for r in rec.results],
        [
            (e.mission, e.payload["turn"], e.payload.get("delayed_from"))
            for e in rec.events
            if e.kind == "horn"
        ],
        len(rec.events),
    )


@pytest.mark.parametrize(
    "lineup",
    [("thoma", "aude", "martin"), ("thoma", "gilles", "martin")],
    ids=["전령관있음", "전령관없음"],
)
@pytest.mark.parametrize("판", [1, 2], ids=["1판에불기", "2판에불기"])
def test_뿔피리가_낀_판도_리플레이가_같은_판을_낸다(lineup, 판):
    """설계 §3.4 — 같은 시드 + 같은 트레이스 = 같은 판.

    QA 재검 2026-09-09 P0-A·P0-B: 네 조합 중 **하나만** 일치했고 나머지 셋은
    등급까지 갈렸다. 원인 둘 — 리플레이가 회차를 안 봐서 6회차 뿔피리가
    7회차에서 터졌고, `delayed_from` 이 아니라 **닿은** 턴을 읽어 왕복마다
    1턴씩 밀렸다. 리플레이 버튼은 데모에서 "그냥 랜덤 아니에요?" 에
    답하는 버튼이다.
    """
    회차 = MISSIONS_A[판 - 1].no
    잰다 = {"blown": False}

    def 원본_뿔피리(mission: int, turn: int) -> bool:
        if mission == 회차 and turn == 3 and not 잰다["blown"]:
            잰다["blown"] = True
            return True
        return False

    cfg = _config(seed=11, lineup=lineup)
    원본 = _run(cfg, run_id="orig", horn=원본_뿔피리)
    assert any(e.kind == "horn" for e in 원본.events), "이 조합에서 뿔피리가 안 울렸다"

    리플레이 = _run(cfg, run_id="replay", horn=_replay_horn(원본.events))
    assert _판정(리플레이) == _판정(원본)


def test_섭식은_기본_편성에서_걸_대상이_없으면_그렇게_기록한다():
    """QA 재검 2026-09-09 R20 — 계승 분기가 **같은 병과가 지금 판에 있을 때만**
    발동한다. 기본 로스터는 5명 5병과이고 출전은 3명이라 중복 병과가 구조적으로
    불가능하다 — 80시드에서 계승 0회였다. 「무효」가 「도달 불가능한 조건에서만
    유효」로 옮겼을 뿐이다.

    지금 고치는 것은 **정직함**이다: 걸 대상이 없으면 `applied` 가 비고,
    화면이 "아직 쓰지 못한다" 고 말한다(`boss_adapt` 의 `no_change` 와 같은 원칙).
    """
    from apps.arena.adapter.outbound.sinks.list_sink import ListSink
    from apps.arena.app.use_cases.battle_setup import setup_battle
    from apps.arena.app.use_cases.learning_cards import apply_cards
    from apps.arena.domain.entities.trace_event import Tracer
    from apps.arena.domain.services.judgment.cards import choose_cards
    from content.cards import CARDS
    from content.missions import MISSION_JUVENILE_BOSS

    members = build_party(_config(lineup=("thoma", "aude", "martin")))
    b = setup_battle(MISSION_JUVENILE_BOSS, members, seed=1, adaptation_on=True)
    sink = ListSink()
    apply_cards(
        b,
        choose_cards([], set(), (("someone", "defender", 7),), 3, CARDS),
        Tracer("t", sink, clock=lambda: "T"),
    )
    섭식 = next(c for c in sink.events[-1].payload["cards"] if c["key"] == "devoured")
    # 방패병은 이 편성에 없다 — 걸 데가 없다. 그 사실이 payload 에 남아야 한다.
    assert 섭식["applied"] == {}, "없는 병과에 카드를 걸었다"
    assert 섭식["round"] == 7 and 섭식["evidence"]["char_class"] == "defender"

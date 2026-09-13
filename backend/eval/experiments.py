"""실험 러너 — 같은 러너를 시드만 바꿔 돌린다 (기획서 §10, 설계 §10).

E1: 조합별 감독 ON/OFF. "감독의 가치는 좋은 조합에서의 승률이 아니라
    나쁜 조합에서의 회복력" (기획서 §8.1).
E2: 보스 적응 ON/OFF.
E3: 성향별 행동 분포 — 같은 전투, 성향 수치만 교체.

전부 Fake 모델로 돈다. 사람도 API 키도 없이 돌아가는 것이 자동 대전의 요점이다
(기획서 §7.3 "평가 도구로는 A단계부터").
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from typing import Any

from apps.arena.adapter.outbound.sinks.list_sink import ListSink
from apps.arena.adapter.outbound.strategies.dice import SeededDice
from apps.arena.adapter.outbound.strategies.llm.select import build_harness
from apps.arena.app.use_cases.runner import run
from apps.arena.domain.entities.types import Disposition, MissionSpec, RunConfig
from content.missions import MISSIONS_A
from content.party import build_party
from content.roster import ROSTER_BY_ID
from eval.metrics import aggregate, metrics_of, paired


@dataclass(frozen=True)
class Composition:
    key: str
    label: str
    lineup: tuple[str, ...]
    classes: dict[str, str]
    # 클래스를 바꿨으면 배분도 바꿔야 한다. 프리셋 배분을 그대로 두면 "방패병
    # 몰빵" 의 방패병 둘이 힘 8 인 채로 판금을 못 입는 궁수가 되고, 실험이 재는
    # 것이 조합인지 장비 페널티인지 갈라지지 않는다(QA 라운드 2).
    allocations: dict[str, dict[str, int]] = field(default_factory=dict)


_WARRIOR = {"str_": 8, "con": 8, "wis": 2}
_DEFENDER = {"con": 8, "str_": 6, "wis": 4}

# 기획서 §10.1 의 조합 4종.
COMPOSITIONS: tuple[Composition, ...] = (
    Composition(
        "warriors",
        "중장병 몰빵",
        ("martin", "thoma", "agnes"),
        {"thoma": "warrior", "agnes": "warrior"},
        {"thoma": _WARRIOR, "agnes": _WARRIOR},
    ),
    Composition("balanced", "균등", ("martin", "aude", "gilles"), {}),
    Composition(
        # 옛 "마법사 몰빵" 조합을 대체한다(v3 개편, 2026-09-08 — 마법 전면 배제).
        # 전원이 방어형이라 적을
        # 못 죽인다 — "이길 수 없는 조합에서 단장이 무엇을 하는가" 가 더 선명하다.
        "defenders",
        "방패병 몰빵",
        ("gilles", "thoma", "agnes"),
        {"thoma": "defender", "agnes": "defender"},
        {"thoma": _DEFENDER, "agnes": _DEFENDER},
    ),
    Composition("no_healer", "전령관 없음", ("martin", "gilles", "agnes"), {}),
)


def _run_once(
    seed: int,
    lineup: tuple[str, ...],
    classes: dict[str, str],
    orchestrator: bool,
    adaptation: bool,
    missions: tuple[MissionSpec, ...] = MISSIONS_A,
    dispositions: dict[str, Disposition] | None = None,
    allocations: dict[str, dict[str, int]] | None = None,
) -> Any:
    cfg = RunConfig(
        seed=seed,
        lineup=lineup,
        allocations=allocations or {},
        classes=classes,
        genders={},
        orchestrator_on=orchestrator,
        adaptation_on=adaptation,
        missions=missions,
        intermission=False,
    )
    members = build_party(cfg)
    if dispositions:
        members = [
            (replace(c, disposition=dispositions.get(c.id, c.disposition)), b, v)
            for c, b, v in members
        ]
    sink = ListSink()
    run(
        f"eval-{seed}",
        cfg,
        members,
        # 제품과 같은 조립 경로를 쓴다. 전에는 여기가 `Harness(...)` 직결이라
        # "예산은 계약 길이만큼" 이 정작 그 숫자를 **재서 보고하는** 곳에서만
        # 안 먹었다(QA 재검 2026-09-09 R13).
        # 박자 0 — 실험은 수백 판을 돌린다. 데모 기본값(0.2초/판단)이 여기 걸리면
        # E1 한 번이 수십 분이 된다(QA 재검 2026-09-09 R13 후속).
        model_factory=lambda n: build_harness(missions=n, name="fake", pace=0.0),
        dice_factory=SeededDice,
        sink=sink,
        clock=lambda: "T",
    )
    return metrics_of(sink.events)


Progress = Callable[[str], None]


def e1(seeds: int, progress: Progress | None = None) -> dict[str, Any]:
    """조합 4종 × 감독 ON/OFF × 시드 N."""
    out = []
    for comp in COMPOSITIONS:
        cell: dict[str, Any] = {}
        # 짝비교의 성공 판정은 **계약 완주**다 — 마지막 판의 승패로 짝을 지으면
        # 앞판에서 누가 끌려갔는지가 결과를 지배한다(QA 2026-09-09 V1).
        runs_by_side: dict[str, list[Any]] = {}
        for side, on in (("on", True), ("off", False)):
            runs = [
                _run_once(
                    s,
                    comp.lineup,
                    comp.classes,
                    orchestrator=on,
                    adaptation=True,
                    allocations=comp.allocations,
                )
                for s in range(1, seeds + 1)
            ]
            runs_by_side[side] = runs
            cell[side] = aggregate(runs)
            if progress:
                progress(
                    f"E1 {comp.label} 감독 {side.upper()}: "
                    f"완주 {cell[side]['clear_rate']:.0%} · 판 승률 {cell[side]['win_rate']:.0%}"
                )
        out.append(
            {
                "key": comp.key,
                "label": comp.label,
                "lineup": [ROSTER_BY_ID[i].name for i in comp.lineup],
                **cell,
                # ON/OFF 가 같은 시드를 쓰므로 짝지어 비교할 수 있다. 비율만 남기면
                # 그 짝을 잃고, 30판에서 3판 차이는 잡음과 구별되지 않는다(QA 라운드 2).
                "paired": paired(
                    runs_by_side["on"], runs_by_side["off"], lambda r: r.contract_clear, "완주"
                ),
                # 기획서 §8.1 의 주장은 승률이 아니라 회복력이다 — 데리고 나왔는가.
                "paired_home": paired(
                    runs_by_side["on"], runs_by_side["off"], lambda r: r.everyone_home, "생환"
                ),
            }
        )
    return {"experiment": "e1", "seeds": seeds, "model": "fake", "compositions": out}


def e2(seeds: int, progress: Progress | None = None) -> dict[str, Any]:
    """보스 적응 ON/OFF. 같은 시드·같은 조합이라 차이는 적응 하나에서 온다."""
    out = []
    for comp in COMPOSITIONS:
        cell: dict[str, Any] = {}
        # 짝비교의 성공 판정은 **계약 완주**다 — 마지막 판의 승패로 짝을 지으면
        # 앞판에서 누가 끌려갔는지가 결과를 지배한다(QA 2026-09-09 V1).
        runs_by_side: dict[str, list[Any]] = {}
        for side, on in (("on", True), ("off", False)):
            runs = [
                _run_once(
                    s,
                    comp.lineup,
                    comp.classes,
                    orchestrator=True,
                    adaptation=on,
                    allocations=comp.allocations,
                )
                for s in range(1, seeds + 1)
            ]
            runs_by_side[side] = runs
            cell[side] = aggregate(runs)
            if progress:
                progress(
                    f"E2 {comp.label} 적응 {side.upper()}: "
                    f"완주 {cell[side]['clear_rate']:.0%} · "
                    f"발동 {cell[side]['avg_adaptations']}회/판 · "
                    f"그중 무효 {cell[side]['adapt_no_change_rate']:.0%}"
                )
        out.append(
            {
                "key": comp.key,
                "label": comp.label,
                **cell,
                "paired": paired(
                    runs_by_side["on"], runs_by_side["off"], lambda r: r.contract_clear, "완주"
                ),
                # 기획서 §8.1 의 주장은 승률이 아니라 회복력이다 — 데리고 나왔는가.
                "paired_home": paired(
                    runs_by_side["on"], runs_by_side["off"], lambda r: r.everyone_home, "생환"
                ),
            }
        )
    return {"experiment": "e2", "seeds": seeds, "model": "fake", "compositions": out}


# 성향 축 하나만 극단으로 바꾼다. 나머지 축은 0 으로 고정해 축의 효과를 분리한다.
E3_LEVELS = (-80, 0, 80)


def e3(seeds: int, progress: Progress | None = None) -> dict[str, Any]:
    """성향별 행동 분포 — 같은 전투, 성향 수치만 교체(기획서 §10.1 E3)."""
    comp = COMPOSITIONS[1]  # 균등
    out = []
    for axis in ("risk", "sacrifice", "cooperation"):
        rows = []
        for level in E3_LEVELS:
            disp = {
                cid: Disposition(
                    **{
                        **dict.fromkeys(("risk", "cooperation", "planning", "sacrifice"), 0),
                        axis: level,
                    }
                )
                for cid in comp.lineup
            }
            runs = [
                _run_once(
                    s,
                    comp.lineup,
                    comp.classes,
                    orchestrator=True,
                    adaptation=True,
                    dispositions=disp,
                    allocations=comp.allocations,
                )
                for s in range(1, seeds + 1)
            ]
            agg = aggregate(runs)
            rows.append({"level": level, **agg})
            if progress:
                progress(
                    f"E3 {axis}={level:+}: 이탈 {agg['avg_deviations']}회/판 "
                    f"FLEE {agg['action_share'].get('FLEE', 0):.0%}"
                )
        out.append({"axis": axis, "levels": rows})
    return {"experiment": "e3", "seeds": seeds, "model": "fake", "axes": out}


EXPERIMENTS: dict[str, Callable[..., dict[str, Any]]] = {"e1": e1, "e2": e2, "e3": e3}


def available() -> Iterable[str]:
    return EXPERIMENTS.keys()

"""생애 이벤트 카테고리 (기획서 §6.2·§6.7, 설계 §2.5).

카테고리 스키마는 고정하고 effect 범위를 제한한다 — 자유도는 서사에, 안정성은
스키마에. B단계에서 쓰는 effect 는 `param_change` 하나뿐이고, 나머지(이탈·충원·
복귀·사망)는 타입만 선언돼 있다(`apps.arena.domain.entities.types.EventEffectKind`).

성별은 **사유 목록**에만 관여한다. 어느 사유로 빠지느냐가 다를 뿐이고, 이번
단계에서 성별이 바꾸는 것은 서사 문구뿐이다(기획서 §4.4).
"""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class LifeEvent:
    key: str
    category: str
    # 표시 제목. 유저가 카드로 본다.
    title: str
    # 사실. 모델이 이 사실로 한두 문장을 쓴다.
    fact: str
    # 성향 4축 변화. 이것이 다음 판의 판단을 바꾼다 — 인과가 닫히는 지점이다.
    shift: dict[str, int]
    fatigue: int = 0
    gender: Literal["female", "male", "any"] = "any"
    # 부양가족이 있는 캐릭터에게만 / 없는 캐릭터에게만
    requires_dependents: bool | None = None


LIFE_EVENTS: tuple[LifeEvent, ...] = (
    LifeEvent(
        key="child_sick",
        category="가족",
        title="아이가 앓는다",
        fact="집에서 전갈이 왔다. 아이가 사흘째 열이 내리지 않는다.",
        shift={"risk": -20, "sacrifice": -20},
        fatigue=10,
        requires_dependents=True,
    ),
    LifeEvent(
        key="letter_home",
        category="가족",
        title="집에서 온 편지",
        fact="집에서 편지가 왔다. 다들 무사하고, 돌아오기만 기다린다고 적혀 있다.",
        shift={"risk": -10, "cooperation": 10},
        requires_dependents=True,
    ),
    LifeEvent(
        key="monastery_rebuilt",
        category="가족",
        title="수도원 재건 소식",
        fact="무너진 수도원을 다시 세운다는 소식이 왔다. 돌아오라는 말도 함께.",
        shift={"sacrifice": 15, "planning": -10},
    ),
    LifeEvent(
        key="old_wound",
        category="부상",
        title="옛 상처가 쑤신다",
        fact="지난 전투에서 얻은 상처가 밤마다 쑤신다. 팔이 예전 같지 않다.",
        shift={"risk": -15},
        fatigue=15,
    ),
    LifeEvent(
        key="first_blood",
        category="각성",
        title="처음으로 살아 돌아왔다",
        fact="처음으로 제 발로 전장을 걸어 나왔다. 손이 떨리지 않는다.",
        shift={"risk": 15, "planning": 10},
        fatigue=-5,
    ),
    LifeEvent(
        key="comrade_debt",
        category="각성",
        title="빚진 목숨",
        fact="누군가 대신 맞아 주지 않았다면 지금 여기 없다. 그 사실이 계속 걸린다.",
        shift={"cooperation": 20, "sacrifice": 20},
    ),
    LifeEvent(
        key="tavern_rumor",
        category="가족",
        title="주점의 소문",
        fact="주점에서 변경 너머의 이야기를 들었다. 왕실이 이 땅을 버렸다는 말.",
        shift={"cooperation": -15, "planning": 10},
    ),
)


def eligible(events: tuple[LifeEvent, ...], gender: str, dependents: int) -> list[LifeEvent]:
    """이 캐릭터에게 일어날 수 있는 사건. 순서는 정의 순서 그대로 — 주사위가 고른다."""
    out = []
    for e in events:
        if e.gender != "any" and e.gender != gender:
            continue
        if e.requires_dependents is True and dependents == 0:
            continue
        if e.requires_dependents is False and dependents > 0:
            continue
        out.append(e)
    return out


def pool_for(c: Any) -> list[LifeEvent]:
    """core/intermission 이 받는 EventPool. 캐릭터에게 일어날 수 있는 사건 목록."""
    return eligible(LIFE_EVENTS, c.gender, c.life.dependents)

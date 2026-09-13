"""로스터 → 출전 파티 조립. 유저의 방향 결정(능력치·클래스·성별)을 적용한다 (기획서 §4.1)."""

from dataclasses import replace

from apps.arena.domain.entities.types import Character, PartyMember, RunConfig
from apps.arena.domain.services.rules.stats import allocate
from content.classes import CLASSES, choose_build
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID


def voice(c: Character) -> str:
    """캐릭터 프롬프트의 말투 지시 한 줄.

    전에는 `app/use_cases/agents/narration.py` 에 있었고, 성별로 갈리는 척하는
    **죽은 분기**(두 갈래가 같은 문자열)를 품고 있었다. 그 분기 하나 때문에
    narration 이 성별 허용 목록에 들어가 있었고, 이 파일이 그걸 쓰느라
    **content → app** 화살표가 생겼다(QA 재검 2026-09-09 R15).

    말투는 세계관 텍스트다 — 콘텐츠가 소유한다.
    """
    return f"{c.name}. 짧고 담백하게 말한다. 자신을 '나'로 부른다."


def apply_direction(config: RunConfig, cid: str) -> Character:
    base = ROSTER_BY_ID[cid]
    alloc = config.allocations.get(cid, PRESET_ALLOCATIONS[cid])
    cls = config.classes.get(cid, base.char_class)
    if cls not in CLASSES:
        raise ValueError(f"모르는 클래스: {cls}")
    gender = config.genders.get(cid, base.gender)
    if gender not in ("female", "male"):
        raise ValueError(f"모르는 성별: {gender}")
    return replace(base, stats=allocate(base.stats, alloc), char_class=cls, gender=gender)


def build_party(config: RunConfig) -> list[PartyMember]:
    """출전 인원 검증은 여기서 한다 — 미션마다 허용 인원이 다르다(기획서 §7.2)."""
    for m in config.missions:
        if not m.lineup_min <= len(config.lineup) <= m.lineup_max:
            raise ValueError(
                f"미션 '{m.name}' 은 {m.lineup_min}~{m.lineup_max}명 출전인데 "
                f"{len(config.lineup)}명이다"
            )
    if len(set(config.lineup)) != len(config.lineup):
        raise ValueError("같은 캐릭터를 두 번 내보낼 수 없다")
    members: list[PartyMember] = []
    for cid in config.lineup:
        if cid not in ROSTER_BY_ID:
            raise ValueError(f"로스터에 없는 캐릭터: {cid}")
        c = apply_direction(config, cid)
        members.append((c, choose_build(c), voice(c)))
    return members

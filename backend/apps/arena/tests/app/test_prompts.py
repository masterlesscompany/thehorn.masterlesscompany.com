import re
from dataclasses import replace

from apps.arena.app.use_cases.agents.prompts import (
    build_boss_prompt,
    build_character_prompt,
    build_orchestrator_prompt,
)
from apps.arena.domain.entities.types import Plan
from apps.arena.domain.services.battle.state import (
    Battle,
    available_actions,
    unit_from_character,
    unit_from_enemy,
)
from apps.arena.domain.services.judgment.visibility import visible_context
from apps.arena.domain.services.rules.stats import allocate
from content.classes import choose_build
from content.environments import MINE
from content.monsters import JUVENILE_MINOTAUR
from content.party import voice
from content.roster import PRESET_ALLOCATIONS, ROSTER_BY_ID

MBTI = re.compile(r"\b[EI][NS][TF][JP]\b")


def _char(cid):
    c = ROSTER_BY_ID[cid]
    return replace(c, stats=allocate(c.stats, PRESET_ALLOCATIONS[cid]))


def _battle(party=("martin", "aude", "thoma")):
    units = {}
    for cid in party:
        c = _char(cid)
        units[cid] = unit_from_character(c, choose_build(c), "party", "front", voice=voice(c))
    for e in JUVENILE_MINOTAUR.units:
        units[e.id] = unit_from_enemy(e, "enemy")
    return Battle(seed=1, environment=MINE, units=units, enemy_def=JUVENILE_MINOTAUR)


PLAN = Plan(
    "평가",
    True,
    "rush",
    {"thoma": "back", "agnes": "back"},
    "minotaur",
    {"thoma": "후열에서 저격", "agnes": "측면으로 돌아 급소를 노려"},
    0.3,
    "속공",
)


def test_캐릭터_프롬프트에_MBTI_가_없다():
    """기획서 §4.5 — 모델이 MBTI 로 판단하면 고정관념이 되고 재현이 안 된다."""
    b = _battle()
    visible, masked, _ = visible_context(b, "thoma", PLAN, 0.5)
    p = build_character_prompt(
        b.units["thoma"], visible, masked, PLAN, available_actions(b, "thoma"), "comply"
    )
    assert not MBTI.search(p)
    # 수치를 하드코딩하지 않는다 — 로스터가 바뀌면 같이 바뀐다.
    위험 = ROSTER_BY_ID["thoma"].disposition.risk
    assert f"({위험:+d})" in p, "성향 수치가 프롬프트에 없다"


def test_아녜스_프롬프트에는_딸이_있다():
    b = _battle(party=("agnes", "martin", "thoma"))
    visible, masked, _ = visible_context(b, "agnes", PLAN, 0.5)
    p = build_character_prompt(
        b.units["agnes"], visible, masked, PLAN, available_actions(b, "agnes"), "comply"
    )
    assert "딸" in p and "측면으로 돌아" in p


def test_이탈_판정이면_방침을_따르지_않는다는_문장이_들어간다():
    b = _battle()
    visible, masked, _ = visible_context(b, "thoma", PLAN, 0.5)
    p = build_character_prompt(
        b.units["thoma"], visible, masked, PLAN, available_actions(b, "thoma"), "deviate"
    )
    assert "따르지 않기로" in p


def test_가려진_필드의_값은_프롬프트에_없다():
    b = _battle()
    k = b.units["thoma"]  # WIS 12, 어둠 → 0단계
    visible, masked, tier = visible_context(b, "thoma", PLAN, 0.42)
    assert tier == 0
    p = build_character_prompt(k, visible, masked, PLAN, available_actions(b, "thoma"), "comply")
    assert "0.42" not in p  # 승산은 3단계에서만
    assert '"allies":' not in p  # 키로는 없다(masked 목록의 값으로만)


def test_감독_프롬프트에_환경_수치와_성향_수치가_있다():
    b = _battle()
    p = build_orchestrator_prompt(b, "party", 0.55, "initial")
    assert "폐광" in p and "후열 거리 페널티 10%" in p and "0.55" in p
    협동 = ROSTER_BY_ID["martin"].disposition.cooperation
    assert f"({협동:+d})" in p, "마르탱의 협동 수치가 감독 프롬프트에 없다"
    assert not MBTI.search(p)


def test_보스_프롬프트에_적응_제안이_실린다():
    b = _battle()
    p = build_boss_prompt(
        b, b.units["minotaur"], available_actions(b, "minotaur"), "focus", "martin"
    )
    assert '"adapt_suggestion": "focus"' in p and "martin" in p

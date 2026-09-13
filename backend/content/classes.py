"""클래스 5종 · 무기 · 갑옷 · 스킬 · AI 세부 층의 빌드 선택 (설계 §2.3).

역할을 막는 쪽(방패병) · 때리는 쪽(전사 · 궁수 · 도적) · 살리는 쪽(음유시인)으로
가른다(설계 2026-09-08). 음유시인이 치유를 갖는 이유: E1 의 "힐러 없음" 조합이
성립하려면 힐러가 있어야 한다.

방어/공격은 행동 금지가 아니라 수치로 가른다 — 기획서 §4.3 "'장착 불가' 대신
페널티" 와 같은 원칙이다. 방패병에게 도끼를 쥐여주는 트롤픽도 막지 않는다.

choose_build 는 기획서 §5 "세부" 층이다 — 무기·스킬은 유저가 정하지 않고
캐릭터의 신체·능력치·클래스를 보고 정해진다. A단계는 코드 휴리스틱이고
그 이유가 rationale 로 인스펙터에 남는다.
"""

from dataclasses import dataclass

from apps.arena.domain.entities.types import BuildChoice, Character, Equipment, SkillDef

# ─── 무기 ─────────────────────────────────────────────────────────────
WEAPONS: dict[str, Equipment] = {
    # 방패병 — 피해는 낮고 방어가 붙는다
    "타워 실드": Equipment("타워 실드", 3, 0, 12, 4, armor=20),
    "방패와 검": Equipment("방패와 검", 3, 0, 10, 10, armor=10),
    # 전사 — 피해가 높고 방어가 없다
    "장창": Equipment("장창", 2, 175, 9, 13, is_long=True),
    "대검": Equipment("대검", 3, 0, 14, 15),
    "전투 도끼": Equipment("전투 도끼", 3, 0, 13, 14),
    "워해머": Equipment("워해머", 2, 0, 14, 16),
    # 음유시인 — 소리가 무기다. 피해는 곁다리고 역할은 지원이다
    "나팔": Equipment("나팔", 1, 0, 3, 4, ranged=True),
    "단검과 붕대": Equipment("단검과 붕대", 1, 0, 3, 5),
    "장궁": Equipment("장궁", 2, 170, 9, 11, is_long=True, ranged=True),
    "단궁": Equipment("단궁", 1, 0, 6, 8, ranged=True),
    "석궁": Equipment("석궁", 2, 0, 12, 13, ranged=True),
    "단검": Equipment("단검", 1, 0, 4, 7),
    "투척 나이프": Equipment("투척 나이프", 1, 0, 5, 6, ranged=True),
    "성표": Equipment("성표", 1, 0, 3, 5, ranged=True),
}

ARMORS: dict[str, Equipment] = {
    "판금 갑옷": Equipment("판금 갑옷", 3, 0, 11, 0, armor=30),
    "사슬 갑옷": Equipment("사슬 갑옷", 2, 0, 8, 0, armor=18),
    "가죽 갑옷": Equipment("가죽 갑옷", 1, 0, 4, 0, armor=8),
    "로브": Equipment("로브", 1, 0, 1, 0, armor=3),
}

# ─── 스킬 ─────────────────────────────────────────────────────────────
SKILLS: dict[str, SkillDef] = {
    # 피해가 0 이다 — 방패병은 막는 사람이다. guard 는 base 를 읽지 않는다.
    "방패 밀치기": SkillDef("방패 밀치기", 8, 0, "self", "guard", 2),
    "전열 압박": SkillDef("전열 압박", 10, 0, "all_enemies", "slow", 2),
    "강타": SkillDef("강타", 10, 14, "enemy", "damage"),
    "휩쓸기": SkillDef("휩쓸기", 12, 10, "all_enemies", "damage"),
    "조준 사격": SkillDef("조준 사격", 9, 12, "enemy", "snipe"),
    "연사": SkillDef("연사", 10, 6, "enemy", "double"),
    "급소 찌르기": SkillDef("급소 찌르기", 9, 9, "enemy", "crit", 30),
    "연막": SkillDef("연막", 8, 0, "all_enemies", "blind", 2),
    "치유": SkillDef("치유", 10, 0, "ally", "heal", 25),
    "축복": SkillDef("축복", 8, 0, "all_allies", "bless", 2),
}


@dataclass(frozen=True)
class ClassDef:
    key: str
    label: str
    primary: tuple[str, ...]
    ideal_build: tuple[str, ...]
    ideal_min_height: int
    weapons: tuple[str, ...]
    skills: tuple[str, ...]
    can_heal: bool = False


CLASSES: dict[str, ClassDef] = {
    "defender": ClassDef(
        "defender",
        "방패병",
        ("con", "str_"),
        ("sturdy",),
        175,
        ("타워 실드", "방패와 검"),
        ("방패 밀치기", "전열 압박"),
    ),
    "warrior": ClassDef(
        "warrior",
        "중장병",
        ("str_", "agi"),
        ("sturdy", "normal"),
        0,
        ("장창", "대검", "전투 도끼", "워해머"),
        ("강타", "휩쓸기"),
    ),
    "archer": ClassDef(
        "archer",
        "장궁병",
        ("agi",),
        ("slim", "normal"),
        165,
        ("장궁", "단궁", "석궁"),
        ("조준 사격", "연사"),
    ),
    "rogue": ClassDef(
        "rogue",
        "약탈병",
        ("agi", "luck"),
        ("slim",),
        0,
        ("단검", "투척 나이프"),
        ("급소 찌르기", "연막"),
    ),
    "bard": ClassDef(
        "bard",
        "전령관",
        ("wis", "int_"),
        ("slim", "normal", "sturdy"),
        0,
        ("나팔", "단검과 붕대"),
        ("치유", "축복"),
        can_heal=True,
    ),
}


def choose_build(c: Character) -> BuildChoice:
    """신체·능력치를 보고 무기·갑옷을 고른다. 이유를 문장으로 남긴다."""
    cls = CLASSES[c.char_class]
    b, s = c.body, c.stats
    skills = tuple(SKILLS[k] for k in cls.skills)

    if cls.key == "defender":
        # 방패병은 막는 사람이다. 힘이 받쳐 주면 더 두꺼운 방패를 든다.
        if s.str_ >= 12:
            w, why = WEAPONS["타워 실드"], "힘이 받친다. 타워 실드로 전열을 통째로 막는다."
        else:
            w, why = WEAPONS["방패와 검"], "타워 실드는 무겁다. 방패와 검으로 버틴다."
        a = ARMORS["판금 갑옷"] if s.str_ >= 11 else ARMORS["사슬 갑옷"]
        return BuildChoice(w, a, skills, why)

    if cls.key == "warrior":
        # 전사는 때리는 사람이다. 방패를 들지 않는다.
        if b.height_cm >= 175:
            return BuildChoice(
                WEAPONS["장창"],
                ARMORS["판금 갑옷"] if s.str_ >= 11 else ARMORS["사슬 갑옷"],
                skills,
                "키가 커서 장창을 제대로 뻗는다.",
            )
        if s.str_ >= 14:
            # 기획서 §5 "키 작고 힘 센 전사 → 긴 창 비효율, 워해머".
            return BuildChoice(
                WEAPONS["워해머"],
                ARMORS["사슬 갑옷"],
                skills,
                "키가 작고 힘이 세다. 긴 무기는 비효율 — 워해머로 짧게 세게 친다.",
            )
        if b.build == "sturdy":
            return BuildChoice(
                WEAPONS["전투 도끼"],
                ARMORS["사슬 갑옷"],
                skills,
                "몸이 두껍다. 도끼로 무겁게 내리친다.",
            )
        return BuildChoice(
            WEAPONS["대검"],
            ARMORS["사슬 갑옷"],
            skills,
            "특별한 강점이 없다. 대검으로 무난하게 벤다.",
        )

    if cls.key == "archer":
        if b.height_cm >= 170:
            return BuildChoice(
                WEAPONS["장궁"], ARMORS["가죽 갑옷"], skills, "키가 커서 장궁을 제대로 당긴다."
            )
        if s.str_ >= 12:
            return BuildChoice(
                WEAPONS["석궁"],
                ARMORS["가죽 갑옷"],
                skills,
                "키는 작지만 힘이 있다. 석궁이 맞는다.",
            )
        return BuildChoice(
            WEAPONS["단궁"],
            ARMORS["가죽 갑옷"],
            skills,
            "키가 작아 장궁은 비효율. 단궁으로 빠르게 쏜다.",
        )
    if cls.key == "rogue":
        # 행운으로 무기를 고르면 안 된다 — 투척은 원거리라 사거리·편성·거리
        # 페널티가 함께 바뀌고, 그것이 곧 판단이다(기획서 §4.2 "행운은 판단에
        # 개입하지 않는다"). 민첩으로 고른다.
        w = WEAPONS["투척 나이프"] if s.agi >= 12 else WEAPONS["단검"]
        return BuildChoice(
            w, ARMORS["가죽 갑옷"], skills, "가볍게 움직여야 한다. 손이 빠르면 투척, 아니면 단검."
        )
    # bard — 살리는 사람이다. 북으로 박자를 잡고, 지혜가 받치면 곡을 끌고 간다.
    if s.str_ >= 12:
        w, why = WEAPONS["단검과 붕대"], "몸이 받친다. 앞에 붙어 지혈하고 봉합한다."
    else:
        w, why = WEAPONS["나팔"], "먼저 신호가 서야 한다. 나팔로 대열의 박자를 잡는다."
    return BuildChoice(w, ARMORS["가죽 갑옷"], skills, why)

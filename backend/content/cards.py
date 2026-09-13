"""학습 카드 풀 (기획서 v3 §8.4).

**판타지 초능력이 아니다. 그것은 당신이 남긴 것을 먹고 자란다.**

네 출처가 각각 한 종에게 붙는다. 유저가 학습을 억제하는 수단이 전부 자원
결정과 연결된다 — 은화를 회수에 쓸 것인가 훈련에 쓸 것인가, 지친 대원을
쉬게 할 것인가 내보낼 것인가. 그 선택들이 곧 다음 보스의 강함이다.

A단계는 카드 풀과 결정론적 선택까지다. 카운터 카드 10~12장 전량과
패턴 지표 7종은 B단계다(기획서 v3 §14).
"""

from apps.arena.domain.entities.types import CardDef

SOURCE_KO: dict[str, str] = {
    "scout": "고블린의 척후 관찰",
    "flight": "놀의 탈주 추적",
    "loot": "오크의 전리품",
    "feeding": "섭식",
}


CARDS: tuple[CardDef, ...] = (
    CardDef(
        "pillar",
        "기둥",
        "flight",
        "기여도 {ratio}% 가 한 사람에게 있었다",
        "focus",
    ),
    CardDef(
        "range",
        "사거리",
        "scout",
        "원거리 대원이 {count}명이었다",
        "ranged_block",
        magnitude=15,
    ),
    CardDef(
        "devoured",
        "섭식",
        "feeding",
        "굴에 두고 온 사람에게서 배웠다",
        "focus",
    ),
)

CARDS_BY_KEY: dict[str, CardDef] = {c.key: c for c in CARDS}

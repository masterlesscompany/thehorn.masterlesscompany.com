"""한국어 조사 선택 — 받침을 보고 고른다.

이름이 화면에 그대로 나가므로 "가렛 발렌은(는)" 같은 문장을 두지 않는다.
한글이 아닌 글자로 끝나면 병기형("은(는)")으로 물러선다 — 로마자·숫자의
받침 여부는 읽는 사람마다 다르고, 틀리게 붙이는 것보다 병기가 낫다.
"""

# (받침 있음, 받침 없음)
PAIRS: dict[str, tuple[str, str]] = {
    "은": ("은", "는"),
    "는": ("은", "는"),
    "이": ("이", "가"),
    "가": ("이", "가"),
    "을": ("을", "를"),
    "를": ("을", "를"),
    "과": ("과", "와"),
    "와": ("과", "와"),
    "으로": ("으로", "로"),
    "로": ("으로", "로"),
}

_HANGUL_START = 0xAC00
_HANGUL_END = 0xD7A3


def has_final(word: str) -> bool | None:
    """마지막 글자에 받침이 있는가. 한글이 아니면 None."""
    if not word:
        return None
    ch = word[-1]
    code = ord(ch)
    if not (_HANGUL_START <= code <= _HANGUL_END):
        return None
    # '로' 는 ㄹ 받침을 받침 없음처럼 다룬다 — "서울로", "칼로".
    return (code - _HANGUL_START) % 28 != 0


def josa(word: str, kind: str) -> str:
    """조사 하나. 판단할 수 없으면 병기형."""
    with_final, without = PAIRS[kind]
    final = has_final(word)
    if final is None:
        return f"{with_final}({without})"
    if kind in ("으로", "로") and final and word[-1] and (ord(word[-1]) - _HANGUL_START) % 28 == 8:
        return "로"  # ㄹ 받침
    return with_final if final else without


def with_josa(word: str, kind: str) -> str:
    return f"{word}{josa(word, kind)}"

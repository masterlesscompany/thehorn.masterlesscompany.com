"""Dice 포트 구현 두 가지.

core 에서 random 을 직접 쓰는 유일한 파일이다(tests/test_boundaries.py 예외).
"""

import random
from collections.abc import Sequence


class SeededDice:
    """시드 고정 난수. 같은 시드 = 같은 판(설계 §3.4)."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)
        self.seed = seed

    def roll(self, sides: int) -> int:
        return self._rng.randint(1, sides)

    def uniform(self) -> float:
        return self._rng.random()


class FixedDice:
    """정해둔 값을 순서대로 낸다. 바닥나면 마지막 값을 반복한다 — 픽스처가
    굴림 수를 정확히 세지 않아도 된다."""

    def __init__(self, rolls: Sequence[int], uniforms: Sequence[float] = ()) -> None:
        self._rolls = list(rolls)
        self._uniforms = list(uniforms) or [0.5]
        self._i = 0
        self._j = 0

    def roll(self, sides: int) -> int:
        v = self._rolls[min(self._i, len(self._rolls) - 1)]
        self._i += 1
        return v

    def uniform(self) -> float:
        v = self._uniforms[min(self._j, len(self._uniforms) - 1)]
        self._j += 1
        return v

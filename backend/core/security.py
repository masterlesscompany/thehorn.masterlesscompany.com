"""공유 시크릿 — secu-agent 와 같은 방식. 프론트 BFF 만 백엔드를 부른다.

BACKEND_SHARED_SECRET 이 비어 있으면 검사하지 않는다(로컬). 배포에서는 반드시 채운다.
비ASCII 시크릿은 hmac.compare_digest 가 TypeError 로 죽으므로 시작 시점에 거른다.
"""

import hmac
import os

from fastapi import Header, HTTPException

HEADER = "X-Backend-Secret"


def configured_secret() -> str:
    s = os.environ.get("BACKEND_SHARED_SECRET", "")
    if s and not s.isascii():
        raise RuntimeError("BACKEND_SHARED_SECRET 은 ASCII 여야 한다")
    return s


def 시크릿_검사(x_backend_secret: str | None = Header(default=None)) -> None:
    expected = configured_secret()
    if not expected:
        return
    given = x_backend_secret or ""
    if not given.isascii() or not hmac.compare_digest(given, expected):
        raise HTTPException(status_code=401, detail="시크릿이 맞지 않는다")

"""결과 5등급 (기획서 v3 §7.1b).

전투의 승패(win/lose/retreat/draw)와 사상자를 함께 보고 한 등급으로 접는다.

**「철수」가 벌점이 아닌 것이 핵심이다.** 승산 붕괴를 읽고 물러난 판은 실패가
아니다. 포기 판단을 시스템이 처벌하면 "싸울 가치가 있는가" 를 묻는 §8.3 이
죽고, 중대장은 무조건 싸우는 쪽이 이득이 된다.
"""

from typing import Literal

Grade = Literal["full_success", "success", "withdraw", "failure", "disaster"]

# 좋은 순서다. 인덱스가 곧 서열이라 결산 리포트가 이 순서로 줄을 세운다.
GRADES: tuple[Grade, ...] = ("full_success", "success", "withdraw", "failure", "disaster")


def grade_of(
    outcome: str,
    dead: tuple[str, ...],
    taken: tuple[str, ...],
    injured: tuple[str, ...],
) -> Grade:
    """사망이 하나라도 있으면 무엇을 이겼든 참사다.

    부가 목표(시신·장비 회수, 굴 위치 확보)는 아직 없다. 그래서 지금의
    「완전 성공」은 "이기고 아무도 안 다쳤다" 다 — 부가 목표가 생기면 이
    함수의 첫 분기만 늘어난다.
    """
    if dead:
        return "disaster"
    if outcome == "win":
        return "success" if (taken or injured) else "full_success"
    if outcome == "retreat" and not taken:
        # 전원 생환. 목표는 못 이뤘지만 사람을 잃지 않았다.
        #
        # **부상자가 있어도 「철수」다** — 2026-09-09 팀 결정 #13(기획서 v3 §14).
        # 기획서 §7.1b 표가 "실패 = 퇴각, 부상·끌려감 발생" 이라 두 해석이 다
        # 근거가 있었고, 코드가 조용히 한쪽을 고른 상태였다(QA J15).
        # 부상 때문에 「실패」가 되면 "철수는 벌점이 아니다" 가 무의미해진다.
        return "withdraw"
    return "failure"

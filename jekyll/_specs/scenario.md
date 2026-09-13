---
title: "통합 시나리오 v3.2"
short: "고정 배역 없는 20년 캠페인의 서사 규칙."
order: 2
source: "자유중대_통합시나리오_v3.2_2026-09-10.md"
permalink: /docs/scenario/
render_with_liquid: false
---

# 「자유중대 (Free Company)」 통합 시나리오 v3.2 — Procedural Campaign

> 기준일: 2026-09-10  
> 본 문서는 **고정 캐릭터의 대본이 아니라, 매 플레이에서 다른 캐릭터의 이야기를 생성하는 캠페인 시나리오 정본**이다.  
> 이름·신체·MBTI·나이·Life Seed·Class·Build는 플레이에 따라 달라진다.  
> 고정되는 것은 세계, 미션 구조, 시간의 흐름, 시스템적 사건과 서사 규칙이다.

---

## 0. 시나리오의 원칙

기존처럼 “토마는 장궁병”, “오드는 전령관” 같은 고정 배역을 두지 않는다.

핵심 원칙:

> **스토리는 캐릭터를 미리 쓰는 것이 아니라, 시스템이 만든 캐릭터의 선택을 기억하고 의미를 붙인다.**

역할 분담:

- **Scenario Director AI** = 작가
- **Character AI** = 배우
- **Orchestrator** = 감독
- **Rule Engine** = 세계의 물리법칙
- **User** = 용병단 운영자

---

## 1. 세계관

1360년대.

오랜 전쟁 뒤 휴전이 왔다.

왕들은 서명했지만 길과 숲과 국경은 안전해지지 않았다.

정규군에 남지 못한 사람, 고향으로 돌아갈 수 없는 사람, 가족에게 돈을 보내야 하는 사람, 싸우는 것밖에 모르는 사람들은 자유중대에 들어간다.

유저는 그중 작은 용병단의 **서기 겸 계약 관리자**다.

유저는 직접 칼을 들지 않는다.

하는 일:

- 계약 수주
- 로스터 운영
- 출전 인원 선택
- Camp 지침
- Rescue 비용 지불 여부
- 신규 충원
- 뿔피리

전장에서 캐릭터는 스스로 판단한다.

---

## 2. 프롤로그 — 빈 10자리

게임 시작 시 장부에는 열 개의 빈 Slot이 있다.

모병관이 열 명을 데려온다.

각 캐릭터는 순서대로 생성된다.

### 2.1 Physical

주사위:

- 키
- 체형
- 몸무게

### 2.2 Age

Life Dice:

- 20~40세
- Roll 높음 → 젊음
- Roll 낮음 → 나이 많음

### 2.3 MBTI

16종 Roulette.

### 2.4 Gender

User 선택.

### 2.5 Name / Life Seed

Scenario Director 생성.

예:

> “29세. 북쪽 국경 마을의 목수 집안 출신. 가족에게 돈을 보내기 위해 자유중대에 들어왔다.”

### 2.6 Class / Initial Stats

User 결정.

### 2.7 Initial Build

Character AI 결정.

예:

```text
188cm / Lean / 74kg
MBTI ISTP
Warrior
AGI 중심

AI → Spear
```

다른 Run에서는 같은 조건에서도 다른 합리적 Build가 나올 수 있다.

---

## 3. 20년 캠페인 구조

전체 Campaign:

```text
Cycle 1: M1 M2 M3 M4 M5(Boss)
Cycle 2: M6 M7 M8 M9 M10(Boss)
Cycle 3: M11 M12 M13 M14 M15(Boss)
Cycle 4: M16 M17 M18 M19 M20(Final Boss)
```

각 Boss 후:

```text
Reward
↓
Recruitment Dice
↓
Age +5
↓
Life Event Check
↓
Roster 갱신
```

총 20년이 흐른다.

---

# CYCLE 1 — 서로를 알아가는 5년

## 4. Mission 1 — 첫 계약 / 3명

출전: **3명**

초반 Troll Guard:

- 최소 2개 Class

불가능:

```text
Warrior 3
Bard 3
```

가능:

```text
Warrior 2 + Bard 1
```

### 서사

가까운 농가와 도로에 소규모 습격이 발생했다.

첫 계약은 작다.

유저는 10명 중 3명을 고른다.

이 미션에서 중요한 것은 승패보다:

> **“이 캐릭터들이 실제로 어떤 방식으로 싸우는가?”**

를 보는 것이다.

Trace에 처음으로 다음이 기록된다.

- Weapon
- 행동
- 협동
- 위치
- 피해
- 지원
- 첫 판단

초반 Death는 거의 없고 Injury/Taken 중심으로 설계한다.

---

## 5. Mission 2 — 방어 계약 / 5명

출전: **5명**

초반 Troll Guard:

- 최소 2개 Class

첫 표준 파티.

M1에서 경험을 얻은 캐릭터를 다시 보낼지, 아직 출전하지 않은 캐릭터를 넣을지 유저가 결정한다.

### 시나리오 목적

- 5인 협업
- Bard/Guardian/Archer 등 역할차
- 첫 MVP 경쟁
- 첫 Taken 가능성
- 로테이션 판단

---

## 6. Mission 3 — 대규모 호위 / 7명

출전: **7명**

M3부터 Class 조합 제한 없음.

가능:

```text
7 Warrior
7 Bard
```

### 시스템적 의미

- 많은 캐릭터 경험
- 전체 피로 상승
- 다수 Agent 협업
- 첫 Camp 직전 압력

M3 종료 후 Camp I.

---

## 7. CAMP I — 첫 5턴

유저는 Camp 동안 5개의 전체 지침을 선택한다.

예:

```text
Turn1 REST
Turn2 TRAIN
Turn3 TRAIN
Turn4 EDUCATE
Turn5 LEISURE
```

10명 모두 같은 지침을 받는다.

하지만 실제 행동은 각 Character AI가 결정한다.

입력:

- MBTI
- Life Seed
- Fatigue
- Injury
- Mental Fatigue
- 최근 실패
- 최근 MVP
- Build

예:

```text
User: REST

A → REST
B → TRAIN
C → LEISURE
D → EDUCATE
...
```

Scenario Director는 이 차이를 이야기로 만든다.

첫 Camp에서 유저는 깨닫는다.

> **“나는 환경을 만들 수 있지만 사람을 직접 조종할 수는 없다.”**

---

## 8. Mission 4 — 소수 정예 / 2명

출전: **2명**

### 의미

- 집중 육성
- 두 Character AI의 협업/독립 행동
- MVP 집중
- Boss 전 마지막 일반전

오래 키우고 싶은 핵심 둘을 보낼 수도 있고, 경험이 적은 사람에게 기회를 줄 수도 있다.

---

## 9. Mission 5 — 첫 Boss / 5명

출전: **5명**

M5 Boss는 **Baseline Boss**다.

아직 충분한 과거 플레이 데이터가 없다.

### 전투 종료 후

시스템이 Behavior Fingerprint를 저장한다.

예:

```text
Class composition
Weapon distribution
Range preference
Formation
Target preference
Support dependency
Retreat behavior
Action distribution
```

이 기록은 M10 Boss의 학습 재료가 된다.

### 보상

- Gold
- 높은 Growth
- Recruitment Dice ×1

---

## 10. YEAR +5 — 첫 Life Checkpoint

모든 재적 캐릭터:

```text
Age +5
```

Rule Engine은 Life Event 후보를 만든다.

Scenario Director는 주요 사건을 서사화한다.

가능:

- 결혼
- 임신/출산
- 육아
- 가족 부양
- 고향 소식
- 만성 부상
- 다른 계약 제안

Checkpoint당 큰 사건은 기본 1~2개 정도.

일시 이탈/영구 이탈이 발생할 수 있다.

빈 자리가 생기면 Recruitment.

---

# CYCLE 2 — 적도 우리를 기억하기 시작한다

## 11. Mission 6 — 새로운 시대 첫 전투 / 4명

출전: **4명**

5년이 지났다.

기존 10명이 그대로일 수도 있고:

- 누군가 떠났거나
- Rookie가 들어왔거나
- Veteran이 합류했거나
- Temporary Leave가 발생했을 수도 있다.

이 미션은 변화한 팀의 첫 실제 검증이다.

---

## 12. Mission 7 — 대규모 작전 / 6명

출전: **6명**

피로와 Injury 압력이 높아진다.

미션 종료 후 Camp II.

---

## 13. CAMP II — 달라진 사람들

이제 캐릭터들은 첫 Camp와 다르다.

가지고 있는 것:

- Boss 경험
- 5년의 세월
- Life Event
- 새 동료
- 기존 상실
- 다른 Build
- 누적 Fatigue

같은 `TRAIN` 지시도 처음과 다르게 받아들일 수 있다.

예:

> 예전에는 훈련을 거부하던 사람이 가족이 생긴 뒤 더 불안해져 혼자 훈련할 수 있다.

Scenario Director는 History를 활용해 서사화한다.

---

## 14. Mission 8 — 소규모 계약 / 3명

출전: **3명**

새 Build를 시험하기 좋은 구간.

M5 Boss 이후 Character AI가 성장 방향을 어떻게 바꿨는지 관찰한다.

---

## 15. Mission 9 — 표준 전투 / 5명

출전: **5명**

M10 Boss 직전.

M5와 같은 인물을 보낼 수도 있고 완전히 다른 조합을 쓸 수도 있다.

---

## 16. Mission 10 — 첫 Adaptive Boss / 5명

출전: **5명**

Boss는 M5와 Cycle 1~2의 행동 로그를 가진다.

현재 파티 Fingerprint와 과거 Fingerprint를 비교한다.

### 예시 A — 비슷한 방법 반복

M5:

```text
Warrior 다수
Axe/Hammer
정면 돌파
Bard 의존 높음
```

M10도 비슷하면:

- 정면 돌파 견제
- Support 압박
- 특정 Range 대응

강화.

### 예시 B — 같은 Class, 다른 방법

M5:

```text
Warrior 5
Axe 중심
정면
```

M10:

```text
Warrior 5
Spear 중심
거리 유지
측면
```

Class 조합은 같지만 Fingerprint는 달라야 한다.

Inspector:

> “이 Counter는 M5에서 반복된 정면 돌파 행동 때문에 선택되었습니다.”

### 보상

- Recruitment Dice ×1
- Gold
- Growth

---

## 17. YEAR +10 — 두 번째 Life Checkpoint

초기 30~40대 캐릭터의 삶에 변화가 커진다.

가능:

- 육아
- 가족 간병
- 직업 고민
- 부상 은퇴
- 가업
- 복귀
- 영구 이탈

Scenario Director는 이야기만 만든다.

실제 Effect는 Rule Engine 범위 안.

---

# CYCLE 3 — 성장과 세대교체

## 18. Mission 11 — 2명

출전: **2명**

중반 소수 정예.

오래 키운 핵심 둘을 보낼지, 새로 들어온 Rookie/Veteran을 키울지 선택.

---

## 19. Mission 12 — 6명

출전: **6명**

대규모 전투.

Camp III 직전.

---

## 20. CAMP III — 중년의 변화

세 번째 Camp.

캐릭터마다:

- Stats
- Weapon
- Proficiency
- Life Event
- Age
- 동료 상실
- Taken 경험
- MVP 경험

이 다르다.

같은 Directive라도 과거와 다른 Actual Action이 나오는 것이 자연스럽다.

---

## 21. Mission 13 — 4명

출전: **4명**

M15 전까지 팀 구성을 정비하고 새 Build를 검증한다.

---

## 22. Mission 14 — 7명

출전: **7명**

두 번째 최대 규모.

후반부라 Taken/Death 위험이 높아진다.

많은 사람에게 성장 기회를 주지만 위험 노출도 크다.

---

## 23. Mission 15 — 누적 Adaptive Boss / 5명

출전: **5명**

Boss는 과거 두 번의 Fingerprint와 최근 Cycle을 함께 본다.

핵심 문장:

> **“적은 당신의 Class를 기억하는 것이 아니라, 싸우는 습관을 기억한다.”**

Character AI가 성장해 다른 전술을 만들었다면 과거 Counter가 정확히 맞지 않을 수 있다.

### 보상

- Recruitment Dice ×1
- Gold
- Growth

---

## 24. YEAR +15 — 세 번째 Life Checkpoint

초기 40세 캐릭터는 55세.

이제 노화와 은퇴가 본격적으로 의미를 가진다.

가능:

- 은퇴
- 장기 부상
- 고향 복귀
- 가족 우선
- 마지막 계약 의지
- 후방 역할 전환

Rookie로 들어온 젊은 세대와의 차이가 커진다.

---

# CYCLE 4 — 마지막 세대와 최종 적응

## 25. Mission 16 — 3명

출전: **3명**

Final Cycle 시작.

세대교체가 있었다면 새로운 핵심 멤버가 등장한다.

---

## 26. Mission 17 — 6명

출전: **6명**

마지막 Camp 직전 대규모 미션.

---

## 27. CAMP IV — 마지막 준비

마지막 5턴 Camp.

유저는 5번의 환경 지침을 내린다.

캐릭터는:

- 나이
- 상처
- 경험
- MBTI
- Life Seed
- 최근 실패
- Final Boss 압박

을 가지고 다르게 반응한다.

이 Camp는 “전원 버프 시간”이 아니다.

일부는 훈련하고, 일부는 쉬고, 일부는 여가를 보내고, 일부는 교육을 택할 수 있다.

---

## 28. Mission 18 — 2명

출전: **2명**

Final 전 소수 임무.

가장 믿는 둘을 보낼지, 마지막 성장 기회를 줄지 선택.

---

## 29. Mission 19 — 4명

출전: **4명**

Final Boss 직전 마지막 일반 계약.

이 미션 후 Character AI의 최종 Growth가 반영된다.

---

## 30. Mission 20 — Final Boss / 5명

출전: **5명**

Boss는 네 시대 동안 누적된 플레이 습관을 알고 있다.

하지만 Character AI도 20년 동안 변했다.

최종 질문:

> **“당신의 캐릭터는 적이 학습한 것보다 더 많이 변했는가?”**

고정 스펙으로 찍어누르는 전투가 아니다.

반복하던 습관을 버리고 다른 방법을 만들 수 있는지가 중요하다.

---

## 31. FINAL YEAR +20

Final Boss 종료 후:

- Reward
- Recruitment Dice
- Age +5
- Final Life Check
- Campaign Report

M20 이후 Recruitment는 다음 Campaign Carry-over를 고려할 수 있다.

---

## 32. Campaign Report

캐릭터별 20년 History:

- 시작 나이
- 현재 나이
- MBTI
- Life Seed
- Initial Class
- Initial Stats
- 첫 Weapon
- Weapon 변화
- Stat Growth
- MVP 횟수
- Camp 순응/거부
- Injury
- Taken
- Rescue
- Death/Lost
- Recruitment
- Temporary Leave
- Return
- Retirement
- Boss 참여
- 최종 상태

---

## 33. Taken 장면

Taken은 Boss 학습 재료가 아니다.

미션 종료:

> “{character_name}이 돌아오지 못했습니다.”

다음:

```text
외부 용병단 구조비: {cost} Gold

[파견한다]
[포기한다]
```

파견:

- 즉시 성공
- 즉시 복귀

포기:

- 영구 상실
- Recruitment

구조기한 없음.

---

## 34. Recruitment 장면

빈 Slot 발생.

### Dice 없음/미사용

> 20세 Rookie가 지원한다.

User:

- Gender
- Class
- Initial Stats

Scenario AI:

- 이름
- Life

Character AI:

- Build

### Dice 사용

높음:

> Veteran

이미 Class/Stats/Weapon/Proficiency 형성.

낮음:

> Rookie

---

## 35. 뿔피리 장면

전장에서 User가 직접 개입할 수 있는 제한적 수단.

Bard가 출전:

> 신호 즉시 전달.

Bard 없음:

> 신호 1턴 지연.

그 한 턴이 Injury/Taken/Death를 만들 수 있다.

Bard의 본질은 Support이며 Horn은 여러 지원 기능 중 하나다.

---

## 36. Dynamic Binding

고정 이름 대신 현재 Run의 캐릭터를 바인딩한다.

예:

```text
{recent_mvp}
{highest_wisdom_member}
{oldest_member}
{taken_member}
{recently_returned_member}
{most_fatigued_member}
```

Scenario Director는 실제 History를 읽고 대사를 만든다.

---

## 37. Scenario Director가 기억할 History

- 생성
- MBTI
- Life
- MVP
- Weapon 변화
- Growth
- Camp 거부
- Taken
- Rescue
- Death
- Replacement
- Life Event
- Boss 참여
- Fingerprint

하지만 실제 판정은 만들지 않는다.

---

## 38. 시나리오의 감정 곡선

### M1~5

> “이 사람들이 누구인지 알아가는 단계.”

### M6~10

> “이들은 성장했고, 적도 우리를 기억한다.”

### M11~15

> “누군가는 떠나고, 새로운 사람이 들어오고, 팀의 세대가 바뀐다.”

### M16~20

> “처음의 10명이 그대로 남아 있지 않을 수 있다. 그래도 용병단에는 20년의 History가 남아 있다.”

---

## 39. 마지막 문장

> **“장부의 첫 장에는 열 명의 낯선 사람이 있었다. 마지막 장에는 스무 해 동안 스스로 달라진 사람들의 기록이 남아 있었다.”**

이후 Evaluation 화면으로 전환한다.

> **“이 변화가 정말 AI의 자율성이었는지, 모델을 줄여도 유지되는지 이제 숫자로 확인합니다.”**


---

## 40. 시나리오와 Screen Flow의 결합

시나리오는 텍스트 대본만이 아니라 실제 Screen State와 연결된다.

일반 미션의 화면 진행은 다음으로 고정한다.

```text
Campaign Map
↓
Mission Node 선택
↓
Mission Detail
↓
Party Select
↓
Auto Formation
↓
2D Battle
↓
Result
↓
MVP / Reward
↓
Casualty
↓
Taken? → Rescue Decision
↓
AI Growth Report
↓
Campaign Map
```

스토리 이벤트는 이 흐름을 깨지 않고 사이에 삽입한다.

---

## 41. Campaign Map의 시간 표현

20 Mission은 네 개 Cycle로 보인다.

- Cycle 1: 초창기
- Cycle 2: 성장기
- Cycle 3: 세대교체
- Cycle 4: 마지막 시대

지도 색감과 환경도 시간의 흐름을 반영한다.

예:

```text
M1~5   봄/초기
M6~10  여름/확장
M11~15 가을/노후
M16~20 겨울/마지막 시대
```

정확한 계절은 연출 메타포이며 Rule에는 영향하지 않는다.

---

## 42. 전투 장면의 시나리오 규칙

전투 화면은 2D Auto Battle이다.

고정 Named Character가 없으므로 대사는 다음 Dynamic Binding을 사용한다.

```text
{recent_mvp}
{highest_wisdom_member}
{oldest_member}
{most_fatigued_member}
{taken_member}
{recently_returned_member}
```

전투에서 Character AI가 선택한 Weapon은 실제 Sprite Variant로 보인다.

Physical 차이는 Battle Sprite 크기로 표현하지 않고 Detail Screen의 정보로 남긴다.

---

## 43. Result가 시나리오의 핵심 연결점

미션 종료 후 이야기는 Result 화면에서 이어진다.

순서:

```text
Mission Result
↓
MVP Reveal
↓
Gold / Growth
↓
Injury / Taken / Dead
↓
Taken Rescue Decision
↓
AI Growth Decision
↓
Narrative Update
```

즉 “AI가 성장했다”는 내용을 대사로만 말하지 않고 **Growth Report Screen**에서 직접 보여준다.

---

## 44. Camp Screen의 시나리오 연출

Camp에서는 User가 5번 전체 지침을 선택한다.

각 Turn:

```text
User Directive
↓
10 Character AI Decision
↓
10 Result Card
↓
Scenario Director Narrative
```

예:

```text
REST 지시

A REST
B TRAIN
C LEISURE
...
```

지시와 다른 행동에는 `!` 등 간단한 시각 표시를 붙이고, 클릭하면 Inspector에서 이유를 확인한다.

Camp는 캐릭터 자율성을 전투보다 더 직접적으로 보여주는 장면이다.

---

## 45. Boss Fingerprint Reveal

기존 Learning Card 방식 대신 Boss 전후에 **Behavior Fingerprint**를 보여준다.

M10/M15/M20에서:

```text
과거 행동
↓
현재 유사도
↓
Boss Counter
```

를 카드/장부 형태로 표시한다.

예:

```text
M5 정면 공격 비중 68%
Bard 의존도 41%
현재 유사도 82%

→ Frontline Pressure
→ Support Disruption
```

화면에 나타난 수치는 Trace 집계 결과여야 하며 Scenario Director가 임의로 생성하지 않는다.

---

## 46. +5 Years Screen

Boss 종료 후 즉시:

```text
1361
↓
1366

5 YEARS HAVE PASSED
```

와 같은 짧은 연출을 보여준다.

그 뒤 Life Event Card가 열린다.

캐릭터의 실제 이름과 나이는 현재 Run에서 바인딩한다.

이 장면은 20 Mission을 단순한 20판이 아니라 **20년의 캠페인**으로 인식시키는 핵심 화면이다.

---

## 47. 마지막 UI 전환

M20 종료 후 Campaign Report를 보여준 뒤 Evaluation으로 이동할 수 있다.

```text
20-Year Campaign Report
↓
Character Histories
↓
Boss Adaptation History
↓
Evaluation
```

최종 문장:

> **“이 스무 해의 변화가 정말 AI의 자율성이었는지, 그리고 더 작은 모델에서도 유지되는지 이제 비교합니다.”**


---

## 48. 20 Mission과 Visual Asset은 1:1이 아니다

시나리오는 20 Mission을 유지한다.

하지만 각 Mission마다 새로운 Background와 Enemy를 요구하지 않는다.

예:

```text
M1 / M3 / M8
→ Forest/Road 계열 Background 재사용

M2 / M6 / M13
→ Village/Palisade 계열 재사용
```

다른 점은:

- 적 조합
- 출전 인원
- Mission Objective
- Weather/Lighting Overlay
- AI State
- Boss Fingerprint Context

이다.

따라서 시나리오 콘텐츠의 다양성과 Asset 수를 분리한다.

---

## 49. Hackathon Demo Mission Selection

해커톤 빌드에서 20 Mission 전체를 같은 수준의 Visual로 제작할 필요는 없다.

P0 Demo는 다음 유형을 반드시 포함하는 것을 권장한다.

1. 일반전 1개 — Character AI 기본 판단
2. Camp가 연결되는 Mission — Camp Autonomy
3. Boss / Adaptive Scenario — Fingerprint
4. Evaluation Replay용 고정 Scenario

나머지 Mission은 Campaign Map과 System Data로 존재할 수 있고, 이후 P1/P2에서 Visual을 확장한다.

이것은 20 Mission 구조를 축소하는 것이 아니라 **데모에서 실제 렌더링하는 범위를 우선순위화하는 것**이다.

---

## 50. Evaluation으로 이어지는 시나리오

최종 데모의 서사적 종착점은 Boss 승리만이 아니다.

예시 Demo Flow:

```text
Mission
↓
Character AI가 서로 다른 행동
↓
Growth
↓
Camp에서 지시와 다른 선택
↓
Boss가 반복 행동을 Counter
↓
Evaluation Dashboard
```

Evaluation에서 같은 Scenario를 다른 모델로 Replay한다.

심사위원에게 보여주는 질문:

> **“같은 캐릭터와 같은 상황에서 모델만 줄였을 때 이 자율성이 어디서 무너지는가?”**

따라서 Evaluation은 게임 밖의 부록이 아니라, 시나리오가 기술적 검증으로 이어지는 마지막 Act다.

---

## 51. Horn Scene

뿔피리는 소모성 Inventory가 아니다.

전투 중 유저가 선택하면:

```text
Horn
↓
Retreat Signal
```

이 발생한다.

Bard가 있으면 즉시, 없으면 1 Turn 지연된다.

철수 절차가 시작되기 때문에 “남은 뿔피리 개수”를 시나리오에서 관리하지 않는다.

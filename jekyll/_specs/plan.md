---
title: "기획서 확정본 v5.2"
short: "프로젝트 기획 정본(SSOT). 모든 조항의 최종 권위."
order: 1
source: "자유중대_기획서_확정본_v5.2_2026-09-10.md"
permalink: /docs/plan/
render_with_liquid: false
---

# Wanted AI Championship 2026 — 「자유중대 (Free Company)」 프로젝트 기획서 확정본 v5.2

> 기준일: 2026-09-10  
> 문서 지위: **프로젝트 기획 정본(SSOT)**  
> 프로젝트명: **자유중대 (Free Company)**  
> 장르 표현: 자율 캐릭터 멀티에이전트 성장·자동전투 시뮬레이션  
> 기술적 정의: **AI 캐릭터가 주어진 신체·성격·초기 방향 안에서 스스로 성장하고 판단하는 과정을 게임이라는 재현 가능한 환경에서 평가하는 Agent Testbed**  
> UI/비주얼 정본: `자유중대_Visual_UI_Asset_Guide_v1.0_2026-09-10.md`

---

## 0. 이 프로젝트는 왜 존재하는가

### 0.1 출발 질문

프로젝트의 출발점은 단순하다.

> **“AI로 게임을 만들 수 있을까?”**

하지만 여기서 말하는 “AI로 게임을 만든다”는 배경 이미지나 대사를 생성하는 수준을 뜻하지 않는다.  
우리가 알고 싶었던 것은 **게임 안의 캐릭터에게 실제 성장과 판단의 자유를 넘겼을 때, AI가 캐릭터를 ‘키울’ 수 있는가**다.

그래서 두 번째 질문이 생긴다.

> **“캐릭터의 성장과 판단을 AI에게 어디까지 맡길 수 있을까?”**

본 프로젝트에서 유저는 캐릭터를 직접 조종하지 않는다.  
캐릭터가 태어날 때의 신체와 성격은 유저가 통제하지 못한다. 유저는 그 캐릭터가 어떤 클래스와 초기 능력치로 출발할지만 정한다.

그 이후의 다음 항목은 Character AI의 몫이다.

- 어떤 무기를 선택할 것인가
- 성장 포인트를 어디에 배분할 것인가
- 어떤 숙련과 전투 스타일을 발전시킬 것인가
- 유저의 훈련·휴식 지시에 따를 것인가
- 상황이 바뀌었을 때 기존 계획을 유지할 것인가 바꿀 것인가
- 동료를 보호할 것인가 목표를 우선할 것인가
- 싸움을 계속할 것인가 철수할 것인가

즉, **유저는 출발 방향과 환경을 만들고, 캐릭터는 자기 삶을 스스로 전개한다.**

### 0.2 현실적인 문제

대형 API 모델을 사용하면 높은 추론 능력과 풍부한 행동 다양성을 기대할 수 있다. 그러나 게임처럼 반복 호출이 발생하는 환경에서는 다음 문제가 커진다.

- 호출 비용
- 네트워크 의존성
- 지연시간
- 서비스 장애
- 장기적으로 누적되는 운영비

반대로 로컬 모델은 비용과 네트워크 의존성을 낮출 수 있지만 다음 제약을 가진다.

- GPU VRAM
- 시스템 RAM
- 모델 크기
- 추론 속도
- context 길이
- structured output 안정성
- 장기 계획 및 Tool-use 능력

그래서 프로젝트의 세 번째 질문이 나온다.

> **“캐릭터의 자유도를 얼마나 유지하면서 모델을 줄일 수 있을까?”**

### 0.3 프로젝트의 연구 질문

동일한 세계, 동일한 캐릭터 조건, 동일한 미션, 동일한 Seed, 동일한 Harness에서 **모델만 단계적으로 줄인다.**

그리고 다음을 측정한다.

- 성장 방식이 유지되는가
- 캐릭터의 MBTI 기반 행동 특성이 유지되는가
- 같은 클래스라도 신체·스탯에 따라 다른 빌드가 나오는가
- 경험에 따라 성장 방향이 달라지는가
- 계획한 행동을 실제로 수행하는가
- 위험해졌을 때 Re-plan하는가
- 싸울 가치가 없을 때 철수할 수 있는가
- VRAM과 Latency는 얼마나 줄어드는가

최종 목표는 다음과 같다.

> **“가장 큰 모델을 쓰는 것이 아니라, 필요한 자율성을 만족하는 가장 작은 모델을 찾는다.”**

---

## 1. 핵심 설계 원칙

### 1.1 유저는 캐릭터를 조종하지 않는다

유저가 하는 일은 세 층이다.

1. **초기 방향 결정**
   - 성별
   - 클래스
   - 초기 능력치

2. **환경 결정**
   - 누굴 미션에 보낼지
   - Camp에서 Training / Rest / Education / Leisure 중 무엇을 지시할지
   - Taken 캐릭터를 돈을 내고 구조할지
   - 전투 중 뿔피리를 불어 강제 철수할지

3. **결과 관찰**
   - 왜 그렇게 성장했는지
   - 왜 지시를 따르거나 거부했는지
   - 왜 특정 무기를 골랐는지
   - 왜 전술을 바꿨는지
   - 왜 싸움을 계속하거나 포기했는지

유저가 하지 않는 일:

- 전투 중 개별 캐릭터 이동
- 개별 공격 명령
- 무기 직접 장착
- 성장 포인트 직접 배분
- 스킬 직접 선택
- 전투 스타일 직접 지정

### 1.2 자유도는 AI에게, 세계 법칙은 Rule Engine에게

```text
Character AI / Orchestrator
→ “무엇을 할 것인가?”

Rule Engine
→ “그 행동이 실제로 어떤 결과를 내는가?”
```

AI가 공격력을 만들어내거나, 사망을 선언하거나, 규칙 밖 행동을 성공시킬 수 없다.

### 1.3 CLASS ≠ BUILD

클래스는 완성된 직업이나 고정 무기를 뜻하지 않는다.

**클래스는 AI가 선택할 수 있는 행동·무기·전술의 가능 공간(Affordance Set)을 정의한다.**

### 1.4 좋은 아이템을 먹어 강해지는 게임이 아니다

무기 사이의 기본 공격력은 동일 수준으로 둔다.

차이는 다음과 같은 전술적 특성이다.

- Reach
- 행동 속도
- 방어 돌파
- 기동성
- 연속 행동
- 사거리
- 지원 범위

캐릭터는 더 좋은 숫자의 장비를 찾는 것이 아니라 **자기 신체·스탯·성격·경험에 맞는 싸우는 방법을 찾아간다.**

### 1.5 같은 조합을 벌주는 보스가 아니다

보스는 실제 행동 로그에서 **Behavior Fingerprint**를 만든다.

- 클래스 구성
- 무기 분포
- 거리 선호
- 진형
- 행동 분포
- 타깃 선호
- 지원 의존도
- 철수 경향
- 반복 전술

핵심 원칙:

> **“같은 조합을 쓰는 것을 벌주는 것이 아니라, 같은 방법을 반복하는 것을 벌준다.”**

---

## 2. 캐릭터 탄생 시스템

초기 로스터는 **10명**이다.

고정 이름, 고정 신체, 고정 클래스, 고정 성격을 가진 Named Character는 없다.

### 2.1 생성 순서

```text
① Physical Dice
② Age/Life Dice
③ MBTI Roulette
④ Gender — User
⑤ Scenario Director AI
   - 이름
   - Life Seed
⑥ User
   - Class
   - Initial Stats
⑦ USER HANDS OFF
⑧ Character AI
   - Initial Build
   - Weapon
   - 성장
   - 전술
```

---

## 3. Physical Dice

Physical은 타고난 조건이다.

항목:

- 키
- 체형: 마름 / 보통 / 건장
- 몸무게

원칙:

- 생성 시 한 번만 결정
- 성장 포인트로 바꾸지 않음
- 부상·노화로 효율 보정 가능
- 큰 몸이 무조건 좋은 것이 아님
- 신체와 클래스/스탯/빌드의 정합성이 중요

예:

```text
마른 체형 + 무거운 무기
→ 장착 가능
→ 피로 증가 / 행동 비용 증가

큰 키 + 창
→ Reach 활용 가능

가벼운 체형 + 민첩
→ 이동/회피 효율 증가
```

---

## 4. Age / Life Dice

초기 로스터 10명은 20~40세 사이에서 시작한다.

- Roll이 높을수록 젊다.
- Roll이 낮을수록 나이가 많다.
- 최솟값 20세
- 최댓값 40세

20 Mission 동안 5 Mission마다 5년이 흐른다.

- 20세 시작 → 최종 40세
- 40세 시작 → 최종 60세

이 축을 통해 다음 Life Event를 다룬다.

- 결혼
- 임신/출산
- 육아
- 가족 간병
- 가업
- 다른 직업 제안
- 부상 후 은퇴 고민
- 고향 복귀
- 노화
- 정년 은퇴

---

## 5. MBTI Roulette — 8개 행동 규칙

MBTI는 심리 진단이 아니라 **게임 행동 Rule Schema**다.

유저는 16종 중 하나를 룰렛으로 받는다.

### E — Extraversion

- 동료와 가까이 행동
- 협동/지원 행동 선호
- 집단 전술 적극 참여
- 동료 상태 변화에 빠르게 반응
- Leisure에서 공동 활동 선호

> “혼자 해결하기보다 팀과 함께 해결하려 한다.”

### I — Introversion

- 자기 역할 독립 수행
- 불필요한 지원 이동 감소
- 단독 미션 적응
- 혼자 집중하는 훈련/휴식 선호
- 집단 압력보다 자기 판단 유지

> “팀 안에서도 자기 역할을 독립적으로 완수하려 한다.”

### S — Sensing

- 현재 관측 정보 중시
- 검증된 전술 반복
- 과거 성공한 무기/행동 유지
- 명확한 위협부터 처리
- 익숙한 숙련 강화 선호

> “지금 보이는 사실과 검증된 경험을 믿는다.”

### N — Intuition

- 반복 패턴 추론
- 새로운 전술 시도
- Build 변경 가능성 증가
- 적의 다음 행동 가설 고려
- 새로운 조합 탐색

> “현재의 단서에서 다음 상황을 추론한다.”

### T — Thinking

- 승산·목표·효율 중시
- 전체 기대손실 고려
- Focus fire
- 팀 전체 결과가 좋아진다면 개인 위험 감수 가능
- Rescue/Retreat에서 비용 대비 효과 고려

> “전체 결과를 가장 좋게 만드는 선택은 무엇인가?”

### F — Feeling

- 동료 보호
- 부상자 구조
- 관계·사기 고려
- 특정 동료 희생 회피
- 동료 상태 때문에 기존 작전 수정 가능

> “이 선택이 사람들에게 어떤 결과를 만드는가?”

### J — Judging

- 계획 유지
- 기존 Build 관성
- 진형·역할 유지
- 지시 순응 가능성 증가
- Re-plan 빈도 낮지만 결정 후 강하게 실행

> “계획을 세웠으면 실행한다.”

### P — Perceiving

- 상황 변화에 즉각 수정
- Build/Weapon 변경 가능성 증가
- 기회 행동 선호
- 현장 판단에 따라 지시를 다르게 해석
- Re-plan 적극적

> “상황이 바뀌면 계획도 바뀌어야 한다.”

16 Type은 별도 Script가 아니다.

예:

```text
ISTJ = I + S + T + J
ENFP = E + N + F + P
```

---

## 6. Gender와 Scenario Director AI

Gender는 유저가 선택한다.

Gender는:

- 이름
- Life Seed
- 가능한 Life Event 사유

에 관여한다.

Gender는 다음에 영향 0:

- 기본 공격력
- HP
- 능력치
- 클래스 적합도
- 전투 판정

---

## 7. Scenario Director AI

Scenario Director는 이야기를 만든다.

입력:

- 시대/세계관
- 현재 나이
- Gender
- MBTI
- Physical
- Campaign Year
- 기존 Life Event

출력:

- 이름
- Life Seed narrative
- Life Seed tags
- Camp 행동 서사
- Life Event 표현
- 관계/상실/복귀 서사
- 미션 서사 연결

예:

```yaml
name: "생성 이름"
life_seed:
  narrative: "가족에게 돈을 보내기 위해 용병단에 들어왔다."
  motives:
    - FAMILY_DUTY
    - MONEY_PRESSURE
  history:
    - RURAL_ORIGIN
```

Scenario Director는 Class/Stats/Weapon/전투결과/사망/Growth를 결정하지 않는다.

---

## 8. 클래스 5종

1. **Warrior**
2. **Guardian**
3. **Archer**
4. **Bard**
5. **Rogue**

중복 제한 없음.

### Warrior

Weapon Pool:

- Long Sword
- Short Sword
- Hammer
- Axe
- Dual Axe
- Spear

### Guardian

- Shield 고정 Affordance
- Short Sword
- Mace
- Axe

### Archer

- Short Bow
- Long Bow
- Combat Bow

### Bard

- 사기 고양
- 정신피로 완화
- 응급처치/붕대
- 부상자 보조
- 짐/전리품 운반
- 전장 신호/Horn

### Rogue

- Short Dagger
- Throwing Dagger
- Obstacle
- Trap / Disruption
- 정찰/측면

---

## 9. 무기와 장비 철학

무기의 Base Attack은 동일 수준.

차이는 전술.

| 무기 | 기본 공격력 | 핵심 차이 |
|---|---:|---|
| Long Sword | 동일 | 균형 |
| Short Sword | 동일 | 빠른 행동 |
| Hammer | 동일 | 방어 돌파 |
| Axe | 동일 | 큰 행동비용 / 압박 |
| Dual Axe | 동일 | 연속 행동 / 방어 불리 |
| Spear | 동일 | Reach |
| Short Bow | 동일 | 기동 |
| Long Bow | 동일 | 긴 사거리 / 준비 |
| Combat Bow | 동일 | 균형 |

강해지는 이유는 Stat, 숙련, 경험, 판단, 협업, 전술이다.

---

## 10. 초기 능력치와 이후 성장

유저는 생성 시:

- Class
- Initial Stats

만 정한다.

이후 Growth Point를 Character AI가 배분한다.

AI 판단 대상:

- 어떤 Stat을 올릴지
- Weapon 유지/변경
- 숙련
- Combat Style
- Build 유지/변경

Build 변경에는 관성이 있다.

고려:

- 현재 숙련
- 누적 성공
- 최근 실패
- 신체 적합성
- Stats
- 미션 환경
- MBTI
- Life Seed

---

## 11. 미션 구조 — 20 Mission

```text
Cycle 1: M1 M2 M3 M4 M5(Boss)
Cycle 2: M6 M7 M8 M9 M10(Boss)
Cycle 3: M11 M12 M13 M14 M15(Boss)
Cycle 4: M16 M17 M18 M19 M20(Final Boss)
```

---

## 12. 미션별 고정 출전 인원

| Mission | 출전 인원 |
|---:|---:|
| M1 | 3 |
| M2 | 5 |
| M3 | 7 |
| M4 | 2 |
| M5 Boss | 5 |
| M6 | 4 |
| M7 | 6 |
| M8 | 3 |
| M9 | 5 |
| M10 Boss | 5 |
| M11 | 2 |
| M12 | 6 |
| M13 | 4 |
| M14 | 7 |
| M15 Boss | 5 |
| M16 | 3 |
| M17 | 6 |
| M18 | 2 |
| M19 | 4 |
| M20 Final Boss | 5 |

설계 이유:

- 2명: 소수 정예/집중 육성
- 3~4명: 조합 판단
- 5명: 표준 파티
- 6~7명: 대규모 출전·피로
- Boss 5명 고정: Fingerprint 비교 안정화

---

## 13. 초반 Troll Guard

### M1

- 3명
- 최소 2개 Class

### M2

- 5명
- 최소 2개 Class

M3부터 조합 제한 없음.

5 Bard, 5 Warrior 등 허용.

---

## 14. 초반 사망 완충

HP 0 이후:

```text
DOWNED
↓
Injured / Taken / Dead
```

초반:

- Death 매우 낮음
- Injury 높음
- Taken 중간

후반:

- Death 점진 증가
- Taken 유지
- Injury 감소

확률 수치는 `balance.py` 단일 출처.

---

## 15. Taken — 즉시 경제 의사결정

미션 종료 직후:

```text
Character Taken
↓
구조 비용 표시
↓
[용병단 파견]
YES / NO
```

YES:

- Gold 즉시 차감
- 외부 용병단 구조
- 구조 성공 확정
- 즉시 로스터 복귀
- Rescue Mission 없음
- 구조 기한 없음

NO:

- 영구 상실
- 즉시 빈 Slot 충원

---

## 16. Rescue Cost와 시작 자금

Cost Tier:

| Cycle | Mission | 기본배율 |
|---|---|---:|
| 1 | 1~5 | ×1.0 |
| 2 | 6~10 | ×1.5 |
| 3 | 11~15 | ×2.25 |
| 4 | 16~20 | ×3.0 |

시작 Gold는 Cycle 1 Taken 2명을 구조할 수 있는 금액.

예:

```text
Tier1 Rescue = 100
Start Gold = 200
```

정확한 숫자는 Pilot에서 튜닝.

---

## 17. 미션 보상

Normal:

- Gold
- Growth
- MVP

Boss:

- 더 많은 Gold
- 더 많은 Growth
- Recruitment Dice 1개

---

## 18. MVP

MVP는 Trace 기반 Contribution Score로 결정.

평가 요소:

- Objective contribution
- Damage
- Damage prevented
- Support
- First aid
- Morale
- Control
- Cover
- Rescue

초기 Growth 지급안:

Normal:

```text
참가 생환자 +1
MVP 추가 +2
```

Boss:

```text
참가 생환자 +2
MVP 추가 +3
```

Growth Point는 Character AI가 배분.

---

## 19. Camp Phase

발생:

```text
After M3
After M7
After M12
After M17
```

각 Camp = 5 Turn.

---

## 20. Camp에서 유저가 하는 일

각 Turn마다 부대 전체에게 하나의 지침:

- Training
- Rest
- Education
- Leisure

예:

```text
Turn1 REST
Turn2 TRAIN
Turn3 TRAIN
Turn4 EDUCATE
Turn5 LEISURE
```

10명에게 개별 명령하지 않는다.

---

## 21. Camp에서 Character AI가 하는 일

각 캐릭터가 실제 행동을 결정.

입력:

1. User Directive
2. MBTI
3. Life Seed
4. Current State

Current State:

- Fatigue
- Injury
- Mental Fatigue
- 최근 MVP
- 최근 실패
- Taken 목격
- Age
- Life Event
- Build

내부 행동 Category:

- TRAIN
- REST
- EDUCATE
- LEISURE

서사는 Scenario Director가 다양하게 표현.

---

## 22. Camp 순응/거부 예

휴식 지시:

```text
MBTI: ISTJ
Life: 가족 부양
Recent: 직전 미션 실수
Mental: 불안 높음

Actual: TRAIN
```

Narrative:

> “다시는 같은 실수를 하지 않겠다며 혼자 훈련장으로 갔다.”

훈련 지시:

```text
MBTI: ENFP
Life: 전쟁이 끝나면 술집을 열고 싶다
Fatigue: 매우 높음

Actual: LEISURE
```

Narrative:

> “훈련장에 얼굴만 비추고 동료들과 술집으로 사라졌다.”

---

## 23. Camp 효과

### TRAIN

- Growth opportunity
- Weapon/Proficiency 발전
- Stat 성장
- Fatigue 증가

### REST

- Fatigue 감소
- Injury 회복
- Mental 부담 감소

### EDUCATE

- WIS/INT 계열 성장 후보
- 전술 숙련
- 새로운 전략/Build 탐색

### LEISURE

- Mental Fatigue 감소
- 사기
- 관계
- Life pressure 완화

결과 수치는 Rule Engine.

---

## 24. 세월 — 5 Mission마다 5년

순서:

```text
Boss
↓
Reward
↓
Recruitment Dice
↓
Age +5
↓
Life Event Check
↓
Roster 갱신
↓
다음 Cycle
```

M5, M10, M15, M20 이후.

---

## 25. Life Event

종류:

- 결혼
- 임신/출산
- 육아
- 가족 간병
- 가업
- 다른 용병단 제안
- 고향 복귀
- 만성 부상
- 노화
- 은퇴/정년
- 임시 이탈
- 영구 이탈

Checkpoint마다 주요 사건 1~2개 정도를 기본으로 한다.

성별 특이 사건은 허용하되 기대 이탈 비용은 성별 간 대칭을 목표로 튜닝한다.

---

## 26. Temporary Leave와 Replacement

일시 이탈:

- 원 캐릭터는 복귀 가능 상태
- 빈 전력은 Replacement
- 다음 Life Checkpoint에서 복귀 여부 판단
- 복귀 시 대체자 퇴장 기본

---

## 27. Permanent Loss / Recruitment

빈 Slot 발생 조건:

- Dead
- Taken 미구조
- 영구 이탈
- Retirement

즉시 충원.

---

## 28. Recruitment Dice

Boss M5/M10/M15/M20에서 1개.

빈 Slot이 생길 때 유저가 사용 여부 결정.

사용 안 함:

- Rookie

사용:

- 높은 Roll → Veteran
- 낮은 Roll → Rookie

---

## 29. Rookie

- 현재 시점 20세 고정
- Physical Dice
- MBTI Roulette
- Gender(User)
- Name/Life(Scenario AI)
- Class(User)
- Initial Stats(User)
- 이후 AI 성장

---

## 30. Veteran

이미 형성된 상태:

- Physical
- Age
- MBTI
- Name/Life
- Class
- Stats
- Weapon
- Proficiency
- Build

추천 현재 나이 25~40세.

강하지만 이미 자기 방식이 있는 사람.

---

## 31. Fatigue와 로테이션

출전 캐릭터:

- Fatigue 증가
- 부상/Taken 위험 노출
- Growth 기회

비출전:

- 자연 회복

미션 고정 인원이 다르기 때문에 10명 로스터를 어떻게 돌릴지 판단이 생긴다.

---

## 32. Orchestrator — 단장

역할:

- 미션 시작 전략
- 출전 조합 분석
- 전황 판단
- Re-plan
- Boss 적응 감지
- 싸움 가치 판단
- 자율 철수

캐릭터 개인 성장/Weapon은 결정하지 않는다.

---

## 33. Character AI

역할:

- Weapon
- Stat Growth
- Proficiency
- Build
- Camp 행동
- 전투 행동
- 지시 순응/거부
- 동료 보호
- 자기보존
- 전술

---

## 34. 뿔피리

유저의 전투 중 **강제 철수 입력 수단**이다.

현재 정본에서는 뿔피리를 별도 소모성 Resource로 관리하지 않는다.

```text
Horn Input
↓
Retreat Sequence 시작
```

한 번 뿔피리를 불면 전투가 철수 절차로 전환되므로 같은 전투에서 “남은 횟수”를 관리할 이유가 없다.

- 사용 시 Mission Objective 실패 가능
- 생존 가능성을 높이는 Emergency Override
- Bard가 출전 중이면 신호 즉시 전달
- Bard가 없으면 신호 전달이 1 Turn 지연
- HQ 상단에 `Horn remaining`을 표시하지 않음
- UI에는 전투 중 `Horn / Retreat` Action만 표시

Bard는 나팔수 전용 Class가 아니라 Support Class이며, Horn은 지원 기능 중 하나다.

---

## 35. Boss Adaptation — Behavior Fingerprint

Fingerprint:

- Class composition
- Weapon distribution
- Range distribution
- Formation
- Action distribution
- Target preference
- Support dependency
- Retreat pattern

Boss 단계:

- M5: Baseline / 첫 Fingerprint
- M10: 첫 적응
- M15: 누적 적응
- M20: 최종 적응

같은 5 Warrior라도 전술이 달라지면 다른 Fingerprint가 될 수 있어야 한다.

---

## 36. Boss 학습 구현

```text
Trace
↓
Fingerprint 집계 — 코드
↓
과거와 Similarity — 코드
↓
Counter 후보 — 코드
↓
언제/어떻게 Counter 실행 — LLM
```

Inspector는 근거가 된 과거 행동을 보여준다.

---

## 37. 전체 Timeline

```text
M1 3
M2 5
M3 7
[CAMP 5T]
M4 2
M5 BOSS 5
[+5Y / LIFE / DICE]

M6 4
M7 6
[CAMP 5T]
M8 3
M9 5
M10 BOSS 5
[+5Y / LIFE / DICE]

M11 2
M12 6
[CAMP 5T]
M13 4
M14 7
M15 BOSS 5
[+5Y / LIFE / DICE]

M16 3
M17 6
[CAMP 5T]
M18 2
M19 4
M20 FINAL BOSS 5
[+5Y / FINAL LIFE CHECK]
```

---

## 38. UI — Growth History

캐릭터별 History 예:

```text
M1
Warrior
AI chose Spear

M3
Growth +3
AI → AGI +2 / CON +1

Camp1
User REST
Character TRAIN

M5
Spear 유지

M8
좁은 지형 반복
AI Spear → Short Sword
```

---

## 39. Inspector

모든 핵심 행동은 설명 가능해야 한다.

Weapon:
- Physical
- Stats
- Proficiency
- Mission
- Choice

Growth:
- Point
- Recent experience
- Allocation

Camp:
- Directive
- MBTI
- Life Seed
- State
- Actual action

Retreat:
- odds
- casualty
- objective value
- decision

---

## 40. Trace

필수 이벤트 예:

- character_created
- mbti_assigned
- life_seed_generated
- class_assigned
- initial_stats
- build_chosen
- weapon_changed
- growth_allocated
- camp_directive
- camp_decision
- camp_result
- mission_start
- character_action
- orchestrator_plan
- replan
- horn
- casualty
- taken_decision
- recruitment
- life_checkpoint
- life_event
- boss_fingerprint
- boss_counter
- mission_end

---

## 41. Evaluation

### E1

Orchestrator가 나쁜 조합에서 도움이 되는가.

### E2

Boss Fingerprint 적응이 실제 Counter를 만드는가.

### E3

MBTI 8축이 행동 차이로 나타나는가.

### E4 — 핵심

동일:

- Physical
- Age
- MBTI
- Gender
- Life Seed
- Class
- Initial Stats
- Mission
- Dice
- Harness

모델만 변경.

측정:

- Build Coherence
- Growth Coherence
- Camp Autonomy
- MBTI Retention
- Plan→Action
- Re-plan
- Retreat
- VRAM
- Latency

---

## 42. 대회 스코프

### A — 제출본 / Hackathon Ship Scope

제출본은 **비주얼의 질을 낮춘 Prototype**이 아니라, 핵심 장면의 완성도를 집중하는 방식으로 만든다.

반드시 포함:

- 실제 배포 가능한 Web Build
- 10명 Procedural Character 생성
- Campaign → Mission → Party Select
- **Character-first 2D Auto Battle의 완성된 Vertical Slice**
- Result / MVP / AI Growth
- Trace / Inspector
- Character Detail
- **Evaluation Dashboard P0**
- 최소 `Anchor + 1 Candidate`의 실제 Smoke/DEV 결과
- Model Ladder / Task Heatmap / Quality×VRAM 중 실제 데이터가 확보된 Chart

즉 “게임처럼 보이는 화면”과 “AI가 실제로 평가되었다는 화면”이 제출본부터 함께 존재해야 한다.

### B — 데모데이

A를 기반으로 다음을 확장한다.

- 실제 Local Model Ladder
- Autonomous Growth
- Camp
- MBTI 행동 차이
- Boss Behavior Fingerprint
- Re-plan / Retreat
- E4 핵심 Chart 5종
- Failure Drill-down / Replay
- Selected P1 Visual Polish

### C — 전체 제품 비전

- 20 Mission 전체
- 20년 Campaign
- Life Event
- Taken / Recruitment
- Temporary Leave / Return
- 4 Boss Cycle
- 전체 Campaign 결산
- 장기 Model Benchmark
- 확장 Asset Universe

**중요:** C 전체 제품 비전이 해커톤 제출 시점의 제작 의무를 뜻하지 않는다.

---

## 43. 아키텍처 원칙

- Domain Rule은 LLM을 모른다.
- Decision Model은 Port.
- Fake/Replay/Local/API 동일 Interface.
- Trace는 Frontend와 Eval의 계약.
- 같은 Seed + Replay는 같은 판 재현.
- Scenario/Content는 Domain Rule을 바꾸지 않는다.
- Balance 숫자는 단일 출처.

---

## 44. 제거되는 기존 설계

- 고정 Named 5명
- 토마/오드/마르탱 등 고정 역할
- 중장병/방패병/전령관/약탈병/장궁병
- 유저의 반복 Stat 배분
- 아이템 수치 성장
- 섭식 기반 Boss 학습
- 18 Mission
- 3형태 미노타우루스 성장
- 고정 캐릭터-아이템 인과

---

## 45. 유지되는 기존 설계

- 중세 자유중대 세계관
- 서기형 유저
- 직접 조작하지 않는 전투
- Orchestrator
- Character Agent
- 지혜=정보 해상도
- 행운=실행 굴림
- 뿔피리
- Taken
- Injury/Death
- Trace/Inspector
- Replay
- Seed 재현
- Boss 적응
- 철수 판단
- Troll Pick 허용
- Rule Engine / LLM 분리

---


## 46. Visual / UI 제품 방향

자유중대의 화면 목표는 **Competition-grade Character-first 2D Auto Battle Demo**다.

대외 발표에서는 특정 상용 게임과의 비교 표현을 사용하지 않는다.

외부 설명 문구:

> **Character-first 2D auto-battle UI with campaign-based mission progression**

핵심 Interaction Grammar:

- Campaign Node Map
- Mission Detail
- Party Select
- Character-first 2D Auto Battle
- Result / MVP / Reward
- Character Growth Report
- Boss 단계 진행

자유중대 고유 요소:

- 10명 Procedural Roster
- AI Autonomous Growth
- MBTI / Life Seed
- Camp 5턴
- Taken 즉시 Rescue 결정
- +5 Years / Life Event
- Recruitment Dice
- Boss Behavior Fingerprint
- Inspector Drawer
- **Evaluation Dashboard**

비주얼 목표는 “많은 종류의 적과 배경”이 아니라 **핵심 AI 루프가 실제 게임처럼 읽히는 것**이다.

---

## 47. 기본 Screen Flow

게임의 기본 Loop는 다음으로 고정한다.

```text
Mercenary HQ
↓
Campaign Map
↓
Mission Detail
↓
Party Select
↓
Auto Formation
↓
2D Auto Battle
↓
Mission Result
↓
MVP / Gold / Casualty
↓
Taken? → Rescue Decision
↓
AI Growth Report
↓
Campaign Map
```

특수 구간:

```text
M3 / M7 / M12 / M17
→ Camp 5턴
→ Camp Result

M5 / M10 / M15 / M20
→ Boss
→ Behavior Fingerprint
→ Recruitment Dice
→ +5 Years
→ Life Event
```

이 흐름은 게임 로직과 UI 양쪽에서 동일한 상태 전이로 취급한다.

---

## 48. 캐릭터의 시각적 단순화

실제 캐릭터 데이터는 서로 다르지만 전투 Sprite는 모든 Physical 차이를 개별 에셋으로 만들지 않는다.

전투 외형을 결정하는 축:

```text
Gender
×
Class
×
Weapon
```

따라서 기본 캐릭터는:

```text
2 Gender × 5 Class = 10 Base Character
```

Physical Dice의:

- Height
- Weight
- Body Type

그리고:

- Age
- MBTI
- Life Seed
- 세부 Stats

는 Character Detail에서 확인한다.

즉 포켓몬처럼 **같은 종/클래스의 외형을 공유하지만 내부 개체값은 다르다.**

이 단순화는 비주얼 표현의 제한일 뿐, Rule Engine과 Character AI는 실제 Physical/Stats 데이터를 그대로 사용한다.

---

## 49. 무기와 성장의 시각화

같은 Class의 캐릭터라도 AI가 선택한 Weapon은 전투 화면에서 반드시 보여야 한다.

무기별 Combat Variant:

- Warrior: 6종
- Guardian: 3종
- Archer: 3종
- Bard: 1종
- Rogue: 2종

Gender를 포함하면 총:

> **30 Combat Character Variants**

무기는 공격력 수치 상승용 아이템이 아니라 Tactical Affordance이므로, 시각적으로 다음이 읽혀야 한다.

- Spear와 Axe의 전투 거리 차이
- Guardian의 Shield Block
- Archer Bow Type
- Bard Support Action
- Rogue Throw / Trap

Character Detail에서는 AI가 Weapon을 왜 선택했고 언제 바꿨는지 History를 보여준다.

---

## 50. 전투 화면

전투는 **2D Standing Combat + Short Motion**을 기준으로 한다.

캐릭터는 전장을 자유롭게 마우스로 조작하지 않는다.

Orchestrator와 Character AI가 배치와 행동을 결정한다.

표현 방식:

- Idle
- 짧은 Move Tween
- Attack
- Hit
- Injured
- Down
- Retreat
- Class/Weapon Special Pose
- Projectile / Particle / Micro Shake / Hit Stop

최대 출전 7명을 고려해 2-depth Formation을 사용한다.

Inspector는 기본적으로 닫힌 Drawer이며, Battle 화면의 캐릭터 가독성을 침범하지 않는다.

---

## 51. Character Detail / Inspector의 역할

Roster 카드에는 최소 정보만 보여준다.

- Portrait
- Name
- Class
- Age
- MBTI
- HP
- Fatigue
- Status

Character Detail에서만 다음을 펼친다.

- Height / Weight / Body
- Initial Stats
- Current Stats
- Current Weapon
- Weapon History
- Growth History
- Camp History
- MVP History
- Life Seed
- Life Events

Inspector는 “왜?”를 설명한다.

```text
행동
↓
Human-readable reason
↓
Structured reason code / metric
↓
필요 시 raw trace
```

Raw JSON이 게임의 첫 화면이 되어서는 안 된다.

---

## 52. Competition-grade Visual Target

비주얼 품질과 제작 범위를 분리한다.

### 52.1 Visual Quality Target

해커톤에서 실제 노출되는 P0 화면은 상용 게임 데모처럼 읽힐 정도의 완성도를 목표로 한다.

- 캐릭터 Silhouette 명확
- Weapon 차이 가독
- 짧은 Motion
- Hit feedback
- Result / MVP 연출
- Camp 결과
- Evaluation Chart
- Inspector Drill-down

### 52.2 Hackathon P0 Asset Scope

P0는 **약 130~150 Source Visual Assets**를 목표 범위로 한다.

핵심 구조:

- Base Character Master 10
- Class/Gender Pose Family
- Weapon/Tool Overlay 15
- 실제 Demo Enemy 3종
- Demo Boss 1종
- 핵심 Background 6장 내외
- VFX 12종 내외
- UI Frame / SVG Icon 핵심 세트

중요:

> 30 Weapon Variant × 6 Pose를 전부 완성한 뒤 시작하지 않는다.

Character Master와 Pose Family를 먼저 Lock하고, Demo에서 실제 사용하는 Variant를 우선 제작한다.

### 52.3 P1 — Demo Day Polish

여유가 생긴 경우:

- 추가 Enemy
- 두 번째 Boss Visual
- 추가 Background
- Tired / Injured Portrait
- Life / Recruitment 연출
- 추가 Weapon-specific Pose

### 52.4 P2 — Asset Universe

전체 시스템을 완전 확장하면 약 **400~450 Source Assets** 규모가 될 수 있다.

이 수치는:

- 장기 확장 구조
- 디렉터리/파일명 설계
- 미래 Asset Budget

를 위한 **Asset Universe**이며 해커톤 Ship Scope가 아니다.

따라서 `약 424개`는 제작 목표 숫자로 사용하지 않는다.

### 52.5 생성 도구와 QA

GPT 기반 이미지 생성은 제작 가속 수단으로 사용한다.

그러나 다음은 수동 QA 대상이다.

- 얼굴 Drift
- Class Costume Drift
- 손/Weapon 오류
- Perspective 차이
- Foot line
- Transparent Edge
- Weapon anchor

생성 속도가 빨라도 Consistency QA가 병목이라는 전제를 일정에 반영한다.

---


## 53. Evaluation Dashboard — P0 Product Screen

Evaluation은 부록 화면이 아니라 **Battle과 동급의 P0 핵심 화면**이다.

최소 Screen 구성:

### A. Experiment Header

- Spec Version
- Model
- Quantization
- Hardware
- Seed Set
- Dataset Split
- Run Status

### B. Model Descent

```text
8B  PASS
4B  PASS
2B  PASS
1B  FAIL
```

Gate 통과/실패 지점을 즉시 보여준다.

### C. Task Heatmap

열:

- Model

행:

- Build
- Growth
- MBTI
- Camp
- Plan→Action
- Re-plan
- Retreat

### D. Quality × VRAM

X = Peak VRAM  
Y = Agent Quality / Critical Gate Summary

최소 자원으로 Gate를 통과한 후보를 표시한다.

### E. Camp Autonomy

같은 Directive에서 모델별 실제 행동 분포와 Counterfactual을 보여준다.

예:

```text
Directive = REST

8B: REST 55 / TRAIN 20 / EDUCATE 10 / LEISURE 15
4B: ...
2B: ...
```

### F. Persona Retention

E/I, S/N, T/F, J/P 축 효과가 모델 축소에 따라 얼마나 유지되는지 보여준다.

### G. Failure Drill-down

Chart Cell 클릭:

```text
Scenario
↓
State
↓
Decision
↓
Reason Code
↓
Outcome
↓
Trace / Replay
```

실험하지 않은 값은 채워 넣지 않고 `NOT RUN`으로 표시한다.

---

## 54. UI와 AI의 경계


UI는 AI 판단을 보여주는 표현 계층이다.

다음 원칙을 지킨다.

- Battle Animation은 Rule Engine 결과를 표현할 뿐 판정을 바꾸지 않는다.
- Inspector는 Trace를 읽을 뿐 새로운 판단을 만들지 않는다.
- Physical이 전투 Sprite에서 동일하게 보이더라도 Character AI에는 실제 Physical Data가 전달된다.
- Animation delay가 AI Turn timing이나 Evaluation 결과를 변경해서는 안 된다.
- Evaluation에서는 Visual Layer가 모델 비교의 입력 변수가 되어서는 안 된다.
- 동일 Trace는 동일 Game Event를 재현해야 한다.

---

## 55. FINAL PRINCIPLE


> **유저는 캐릭터의 출발점과 환경을 만든다.  
> Character AI는 그 안에서 자기 성장과 행동을 결정한다.  
> 게임은 그 과정을 기록하고 검증한다.  
> 그리고 우리는 그 자율성을 유지하는 가장 작은 모델을 찾는다.**

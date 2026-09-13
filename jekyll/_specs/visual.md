---
title: "Visual / UI / Asset Guide v1.1"
short: "비주얼·UI·에셋 제작 정본."
order: 6
source: "자유중대_Visual_UI_Asset_Guide_v1.1_FINAL_2026-09-10.md"
permalink: /docs/visual/
render_with_liquid: false
---

# 자유중대 (Free Company) — Visual / UI / Asset Guide v1.1 FINAL
## Character-first 2D Auto-Battle / Competition Demo Production Guide

> 기준일: 2026-09-10  
> 문서 지위: **비주얼·UI·에셋 제작 정본(SSOT)**  
> 대상: 해커톤 제출본 + 데모데이  
> 핵심 원칙: **Competition-grade Quality on Demo-critical Screens, Controlled Asset Breadth**  
> 내부 참고: 특정 상용 2D 자동전투 게임의 Campaign/Team Select/Battle 문법을 참고할 수 있으나, **대외 발표·슬라이드·데모 문구에서는 해당 게임명을 사용하지 않는다.**

---

# 0. v1.1에서 해결한 5개 문제

## 문제 1 — 424개 에셋을 해커톤 의무 범위로 잡았던 문제

수정:

- `약 400~450개`는 **Asset Universe**로 격하
- 해커톤 P0 목표는 **약 130~150 Source Visual Assets**
- 전체 Variant/Pose 생산을 시작 조건으로 두지 않음
- GPT 이미지 생성은 가속 도구로 사용하지만 Consistency QA 시간을 별도 Workstream으로 인정

## 문제 2 — 비주얼에 일정이 쏠리고 Evaluation이 약했던 문제

수정:

- Evaluation Dashboard를 **Battle과 동급 P0 Screen**으로 승격
- Model Descent / Heatmap / Quality×VRAM / Persona / Camp Autonomy / Failure Drill-down 스펙을 본 문서에 포함
- Battle Vertical Slice와 Evaluation Vertical Slice를 병렬 개발

## 문제 3 — Enemy 8종 × Pose, Background 18장의 과도한 P0 범위

수정:

- P0 일반 Enemy **3종**
- P0 Boss **1종**
- P0 핵심 Background **약 6장**
- 20 Mission은 Art 20세트가 아니라 Scenario/Data/Composition으로 다양화

## 문제 4 — `Horn remaining` 불일치

수정:

- HQ Resource에서 Horn 삭제
- Horn은 전투 중 Retreat Action
- 사용하면 Retreat Sequence가 시작되므로 남은 횟수 개념 없음
- Bard 없음 → 전달 1 Turn 지연

## 문제 5 — 대외적으로 특정 레퍼런스 게임을 전면에 내세우던 문제

수정:

대외 용어는 다음으로 통일한다.

> **Character-first 2D auto-battle UI**  
> **Campaign-based mission progression**  
> **Lightweight 2D combat presentation**

---

# 1. 비주얼 목표

## 1.1 한 문장

> **처음 3초에 실제 게임으로 읽히고, 30초 안에 AI가 캐릭터를 대신 판단한다는 것이 보이며, 3분 안에 그 판단을 Evaluation으로 검증할 수 있어야 한다.**

---

## 1.2 Art Direction

| 항목 | 기준 |
|---|---|
| 장르 | Medieval Low Fantasy |
| 시대감 | 1360년대 유럽 자유중대 모티프 |
| 현실/판타지 | 현실 80 / 판타지 20 |
| 캐릭터 | Stylized Realistic 2D |
| 분위기 | 거칠고 낡았지만 Horror 아님 |
| 소재 | 철 / 가죽 / 천 / 목재 / 양피지 |
| 광원 | 흐린 자연광 / 횃불 / 달빛 |
| UI | 양피지 / 먹 / 철제 리벳 / 가죽 |
| VFX | 짧고 읽기 쉬운 Combat Feedback |
| 금지 | Neon / 과도한 마법광 / 과장 갑옷 / 과금형 UI |

---

# 2. 기술·제작 원칙

## 2.1 기준 해상도

- Desktop First
- 1920 × 1080
- 16:9

## 2.2 완성 화면을 이미지 한 장으로 만들지 않는다

AI 생성:

- Character
- Enemy
- Background
- Equipment
- VFX source
- Frame
- Illustration

Frontend:

- Text
- HP
- Buttons
- Chart
- Status
- Layout
- SVG
- Tween

## 2.3 Key Pose + Frontend Motion

Full Sprite Animation 수십 Frame을 기본 전략으로 사용하지 않는다.

```text
Key Pose
↓
Tween / Transform
↓
Projectile
↓
Particle
↓
Hit Stop / Shake
```

---

# 3. Character Visual Model

## 3.1 Physical은 Data, Class/Gender는 Visual

실제 Character:

- Height
- Weight
- Body
- Age
- MBTI
- Life Seed
- Stats

전투 화면:

- Gender
- Class
- Weapon

만 Visual Variant에 반영한다.

같은 Male Warrior 두 명이 같은 Base Sprite를 써도 실제 Physical/Stats는 다르다.

---

## 3.2 Base Character — 10

```text
2 Gender × 5 Class = 10
```

Class:

- Warrior
- Guardian
- Archer
- Bard
- Rogue

각 Base는 Canonical Master 1장을 가진다.

---

# 4. Master Consistency Lock

각 Master에서 고정:

## Identity

- 얼굴
- 헤어
- 피부 톤
- Class별 기본 연령감

## Costume

- 의상
- Armor
- Material
- Palette

## Equipment Slot

- Main hand
- Off hand
- Shield
- Quiver
- Bard bag/horn
- Rogue pouch

## Camera

- Side 3/4
- Foot line
- Scale
- Facing

GPT로 Variant를 생성할 때 **새 캐릭터로 재디자인하지 않는다.**

---

# 5. Weapon System — Asset Architecture

전체 Weapon Universe:

### Warrior — 6

- Long Sword
- Short Sword
- Hammer
- Axe
- Dual Axe
- Spear

### Guardian — 3

- Shield + Short Sword
- Shield + Mace
- Shield + Axe

### Archer — 3

- Short Bow
- Long Bow
- Combat Bow

### Bard — 1 Tool Kit

- Horn
- Bandage
- Bag

### Rogue — 2

- Short Dagger
- Throwing Dagger

총 Weapon/Tool Visual Family:

> **15개**

전체를 캐릭터×포즈로 미리 굽지 않는다.

---

# 6. P0 Character Asset Strategy

## 6.1 목표

P0는 “30 Variant × 6 Pose = 180” 방식으로 시작하지 않는다.

대신:

```text
Base Master
+
Pose Family
+
Weapon/Tool Overlay
+
Frontend Motion
```

을 사용한다.

---

## 6.2 P0 Character Source 예상

### Master

10

### Core Pose

Base 10명 기준:

- IDLE
- HIT
- DOWN

`10 × 3 = 30`

### Attack / Special Pose Family

Weapon별이 아니라 Motion Family 기준.

#### Warrior

Gender별:

- Slash
- Thrust
- Heavy

= 6

#### Guardian

Gender별:

- Strike
- Block

= 4

#### Archer

Gender별:

- Aim
- Shoot

= 4

#### Bard

Gender별:

- Bandage
- Horn

= 4

#### Rogue

Gender별:

- Stab
- Throw
- Trap Set

= 6

합계:

> 24

### Weapon / Tool Overlay

15

### Portrait

Master에서 Crop한 NORMAL Portrait는 Derived Asset으로 처리.

추가 생성은 P1.

### P0 Player Source

```text
Master 10
Core Pose 30
Attack/Special 24
Weapon/Tool 15
----------------
79
```

목표:

> **약 79 Player Source Assets**

---

# 7. P0 Enemy / Boss

심사위원은 적 종류를 세지 않는다.

P0는 실제 Demo Scenario에 필요한 것만 만든다.

## 일반 Enemy — 3종

추천:

1. Goblin Raider — 기본 근접
2. Gnoll Charger — 빠른 압박
3. Orc Shieldbearer — 방어/전열

각:

- Idle
- Attack/Special
- Hit
- Down

```text
3 × 4 = 12
```

## Boss — 1종

Boss 1 Visual로 Behavior Adaptation을 보여줄 수 있다.

Pose:

- Idle
- Attack
- Heavy
- Defend
- Observe/Adapt
- Hit/Defeat

> 6

Enemy/Boss P0:

> **18 Source Assets**

---

# 8. P0 Background — 약 6장

1. Mercenary HQ
2. Campaign Map
3. Camp
4. General Battle A — Road/Forest
5. General Battle B — Village/Palisade
6. Boss Arena

20 Mission이라고 20 Background를 만들지 않는다.

미션 차이는 다음으로 만든다.

- Enemy composition
- Objective
- Lighting overlay
- Weather overlay
- Props
- Formation
- AI State
- Narrative

---

# 9. P0 VFX — 12

1. Slash
2. Pierce
3. Blunt
4. Shield Block
5. Arrow
6. Projectile Hit
7. Dodge Dust
8. Down Dust
9. Bandage
10. Morale
11. Horn/Retreat Signal
12. MVP/Growth Highlight

---

# 10. P0 UI Icon / Frame

## Icon — 약 20~24

- 6 Stats
- 5 Class
- HP
- Fatigue
- Injury
- Gold
- Recruitment Dice
- Growth
- Camp 4 actions
- Inspector
- Boss/Fingerprint

SVG 우선.

## Frame — 약 8

- Character
- Mission
- Inspector
- Result
- Camp
- Life
- Evaluation
- Modal

---

# 11. P0 Source Asset Budget

대략:

| 구분 | 수량 |
|---|---:|
| Player | 79 |
| Enemy/Boss | 18 |
| Background | 6 |
| VFX | 12 |
| Icon | 20~24 |
| Frame | 8 |
| **TOTAL** | **143~147** |

따라서 해커톤 P0는:

> **약 130~150 Source Visual Assets**

범위로 관리한다.

정확한 숫자보다 **Visual QA 통과 개수**가 중요하다.

---

# 12. P1 — Demo Day Polish

P0 이후에만 착수.

추천:

- Tired Portrait 10
- Injured Portrait 10
- Enemy 1~2종 추가
- Boss Visual 1종 추가
- Background 2~3장
- Weapon-specific Alt Attack
- Life Event Illustration
- Rookie/Veteran Illustration
- Boss Fingerprint Reveal Polish
- Sound/VFX Polish

---

# 13. P2 — Asset Universe

전체 제품을 확장하면:

- 30 Fully-baked Combat Variants
- Pose Pack 확장
- 일반 Enemy 8종 이상
- Boss 4개 Cycle
- Background 18장 수준
- Portrait State 확장
- UI/System Illustration 확장

이론상 **400~450 Source Asset** 규모가 될 수 있다.

하지만:

> **이 숫자는 해커톤 제작 약속이 아니다.**

용도:

- 장기 디렉터리 설계
- 확장 예산
- Post-hackathon roadmap

`424개`를 KPI나 완료 조건으로 사용하지 않는다.

---

# 14. Production Gate

## Gate A — Visual Bible

1 Male Warrior / 1 Female Bard / 1 Enemy / 1 Background.

확인:

- Style
- Scale
- Foot line
- Tween
- Hit feedback
- Transparent edge

## Gate B — Evaluation Slice

Visual 확장 전에 반드시:

- Evaluation Runner 실행
- Anchor 결과
- Candidate 결과
- 실제 Chart 최소 1개

를 확보한다.

## Gate C — P0 Battle Slice

- Party Select
- Battle
- Result
- AI Growth
- Inspector

연결.

## Gate D — P1 허용

다음 둘이 모두 Ready일 때만 추가 Art 확장:

```text
Battle Slice Ready
AND
Evaluation Slice Ready
```

---

# 15. Screen Architecture

P0 핵심 Screen:

1. Landing / HQ
2. Campaign
3. Character Creation
4. Roster
5. Character Detail
6. Mission Detail
7. Party Select
8. Battle
9. Inspector Drawer
10. Result / MVP
11. AI Growth
12. Taken / Rescue
13. Camp
14. Camp Result
15. Boss Fingerprint
16. Evaluation Dashboard

P1:

- +5 Years
- Life Event
- Recruitment
- Campaign Summary
- Long-term History

---

# 16. HQ

상단 Resource:

- Gold
- Recruitment Dice
- Campaign Year

표시하지 않음:

- Horn remaining

Horn은 Inventory가 아니다.

---

# 17. Roster

카드:

- Portrait
- Name
- Class
- Age
- MBTI
- HP
- Fatigue
- Status

Physical 세부값은 숨긴다.

---

# 18. Character Detail

표시:

- Height
- Weight
- Body
- Age
- MBTI
- Life Seed
- Initial Stats
- Current Stats
- Current Weapon
- Weapon History
- Growth History
- Camp History
- MVP
- Life Event

핵심:

> **같은 전투 외형을 공유해도 이 Character는 고유한 Agent다.**

---

# 19. Campaign

20 Mission Node는 유지.

하지만 P0 Demo에서 실제 Battle Scene을 모두 개별 제작하지 않는다.

Node 유형:

- Normal
- Boss
- Camp
- Life Check
- Cleared
- Current
- Locked

---

# 20. Party Select

Mission이 정확한 인원을 요구.

```text
Required: 5
Selected: 5 / 5
```

M1/M2 Troll Guard만 UI 안내.

---

# 21. Battle

캐릭터가 화면의 중심.

최대 7명을 위해 2-depth Formation.

표현:

- Idle micro motion
- Attack movement
- Projectile
- Hit
- Down
- Retreat
- Status effect

UI는 캐릭터를 가리지 않는다.

---

# 22. Floating Decision Tag

예:

- PROTECT
- FLANK
- HOLD
- SUPPORT
- REPLAN
- RETREAT

1초 전후.

Inspector 진입점.

---

# 23. Inspector

기본 Closed Drawer.

열면:

```text
ACTION
PROTECT

STATE
Ally HP 18
Self HP 63

REASON CODES
F_ALLY_PROTECTION
E_COOPERATION

OUTCOME
Damage prevented 14

MODEL
2B Q4
```

사후 LLM이 “그럴듯한 이유”를 새로 쓰면 안 된다.

Trace 기반만 표시.

---

# 24. Result

순서:

```text
Result
↓
Reward
↓
MVP
↓
Casualty
↓
Taken?
↓
AI Growth
```

MVP는 Damage만으로 선정하지 않는다.

---

# 25. Taken / Rescue

표시:

- Character
- Current Gold
- Rescue Cost

선택:

- Rescue
- Give up

Rescue:

- 즉시 성공
- 즉시 복귀

없음:

- Countdown
- 실패 확률
- 별도 Rescue Mission

---

# 26. Horn / Retreat UI

Battle Action:

> **RETREAT SIGNAL**

세계관 표현으로 Horn Icon을 사용할 수 있다.

Bard 있음:

- 즉시 전달

Bard 없음:

- 1 Turn delay

별도 사용횟수 / Inventory 없음.

---

# 27. Camp

5 Turn.

User:

- Train
- Rest
- Educate
- Leisure

전체 10명에게 Directive.

결과:

```text
A REST ✓
B TRAIN !
C LEISURE !
...
```

`!` 클릭 → Inspector.

---

# 28. Boss Fingerprint

Learning Card/섭식 UI를 사용하지 않는다.

표시:

```text
PAST PATTERN
Frontline 68
Support dependence 41
Retreat low

CURRENT SIMILARITY
82

COUNTER
Frontline Pressure
Support Disruption
```

수치는 Trace 집계 결과.

---

# 29. Evaluation Dashboard — P0

Evaluation은 #16의 “한 줄 메뉴”가 아니다.

**Battle과 동급의 핵심 Product Surface**다.

---

## 29.1 Experiment Header

상단:

```text
SPEC      v2.2
MODEL     2B Q4
HARDWARE  RTX ...
SPLIT     HOLDOUT
SEEDS     160
STATUS    COMPLETE
```

---

## 29.2 Model Descent

```text
8B   PASS
4B   PASS
2B   PASS
1B   FAIL
```

FAIL 클릭 → 실패 Task 표시.

---

## 29.3 Task Heatmap

```text
             8B   4B   2B   1B
Build
Growth
MBTI
Camp
Plan→Action
Re-plan
Retreat
```

Color에만 의존하지 않고 숫자/Pass 표시 병행.

---

## 29.4 Quality × VRAM

Scatter.

X:

- Peak VRAM

Y:

- Agent Quality

표시:

- Gate pass/fail
- Pareto candidate
- Minimum Viable Model

---

## 29.5 MBTI Retention

4축:

- E/I
- S/N
- T/F
- J/P

모델 축소에 따른 Directional Effect 유지.

---

## 29.6 Camp Autonomy

같은 Directive:

```text
REST
```

에서 Model별:

- REST
- TRAIN
- EDUCATE
- LEISURE

분포 비교.

추가:

- Justified Refusal
- Mechanical Compliance Collapse

---

## 29.7 Failure Drill-down

Chart 클릭:

```text
Scenario
↓
Character State
↓
Decision
↓
Reason Codes
↓
Outcome
↓
Trace
↓
Replay
```

---

## 29.8 실제 데이터만 사용

실험하지 않은 Cell:

> `NOT RUN`

개발 Mock:

> `MOCK`

발표 Build에서 Mock/Real 혼합 금지.

---

# 30. Evaluation과 Art 일정

금지:

```text
캐릭터 Variant 계속 제작
↓
Evaluation은 마지막 주
```

권장:

```text
Week/Phase A
Visual Bible
+
Evaluation Runner

Week/Phase B
Battle Slice
+
Smoke/DEV Chart

Week/Phase C
P0 Polish
+
E4 Ladder
```

---

# 31. GPT Image Generation Workflow

GPT는 Asset production accelerator로 적극 사용한다.

하지만 한 번 생성한 이미지를 바로 승인하지 않는다.

파이프라인:

```text
Master
↓
Variant request
↓
Visual QA
↓
Reject / Approve
↓
Background cleanup
↓
Runtime export
```

---

# 32. Consistency QA

각 Character Asset:

```text
[ ] Face matches Master
[ ] Hair matches
[ ] Costume matches
[ ] Palette matches
[ ] Weapon correct
[ ] Hands plausible
[ ] Camera matches
[ ] Foot line matches
[ ] Scale matches
[ ] Transparent edge clean
[ ] No text
```

GPT 생산성의 병목은 “생성 버튼”이 아니라 이 QA다.

---

# 33. Prompt Template

```text
[PROJECT]

Free Company.
1360s grounded medieval mercenary game.
Character-first 2D auto-battle presentation.
Low fantasy.
No magical glow.
No text.

[MASTER LOCK]

Use the canonical reference.
Preserve:
face,
hair,
costume,
class silhouette,
palette,
body proportions.

[ASSET]

Gender:
Class:
Pose family:
Weapon/tool:

[CAMERA]

Full body.
Side three-quarter.
Consistent foot line.
Consistent scale.
Facing right.

[OUTPUT]

Transparent background.
No environment.
No text.
```

---

# 34. Directory

```text
assets/
├── characters/
│   ├── master/
│   ├── pose/
│   ├── equipment/
│   └── portrait/
├── enemies/
├── boss/
├── backgrounds/
├── ui/
│   ├── frames/
│   └── icons/
├── vfx/
└── evaluation/
```

---

# 35. 외부 발표 표현

사용:

> **Character-first 2D auto-battle**

> **Campaign-based mission progression**

> **Autonomous character growth**

> **Traceable agent decisions**

> **Minimum Viable Gaming Agent**

사용하지 않음:

- “OO게임급”
- “OO게임 복제”
- 특정 상용 게임의 브랜드명을 전면 비교 대상으로 쓰는 표현

레퍼런스는 내부 제작 언어일 뿐 제품 정체성이 아니다.

---

# 36. 최종 성공 기준

## 게임

첫 3초:

> 게임으로 보인다.

## Character

30초:

> Class/Weapon/행동 차이가 읽힌다.

## Agent

1분:

> 유저가 직접 조작하지 않는데 Character가 다르게 판단한다.

## Explainability

2분:

> 왜 행동했는지 Inspector에서 확인된다.

## Evaluation

3분:

> 모델을 줄였을 때 어디서 Agent 품질이 무너지는지 Chart와 Trace로 확인된다.

---

# 37. FINAL PRINCIPLE

> **우리는 400개의 이미지를 만드는 프로젝트가 아니다.  
> 게임처럼 보이는 핵심 장면을 만들고, 그 장면에서 작동하는 Character AI를 실제 데이터로 검증하는 프로젝트다.**

> **GPT는 비주얼 제작 속도를 높인다.  
> 그래서 절약된 시간은 더 많은 Variant가 아니라 Evaluation과 Product Polish에 우선 투자한다.**

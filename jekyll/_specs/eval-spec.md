---
title: "AI Agent Evaluation PART 1 — 정본 v2.2"
short: "E4 · 게이트 · 지표 · 대시보드의 평가 정본."
order: 4
source: "자유중대_AI_Agent_Evaluation_PART1_정본_v2.2_2026-09-10.md"
permalink: /docs/eval-spec/
render_with_liquid: false
---

# 「자유중대 (Free Company)」 AI Agent Evaluation PART 1 — 정본 v2.2
## Autonomous Character Growth & Minimum Viable Gaming Agent Evaluation Specification

> 기준일: 2026-09-10  
> 문서 지위: **AI 평가 정본(SSOT)**  
> 목적: Codex / Claude Code / 개발자 / 평가 담당이 동일한 기준으로 Evaluation Runner, Dataset, Metric, Gate, Report를 구현하도록 한다.

---

## 0. 평가의 목적

이 프로젝트에서 AI의 가치는 “대사를 잘 생성한다”가 아니다.

평가 대상은 다음이다.

> **같은 출발 조건에서 Character AI가 얼마나 일관되고 캐릭터답게 성장·행동하는가.**

그리고 최종 질문:

> **“이 자율성을 유지하면서 로컬 모델을 어디까지 줄일 수 있는가?”**

---

## 1. 평가 대상 역할

### 1.1 Character AI — Primary

- Initial Build
- Weapon
- Growth Allocation
- Proficiency
- Camp Decision
- Directive Compliance/Refusal
- Tactical Action
- Cooperation
- Self-preservation
- Build Change

### 1.2 Orchestrator — Secondary

- Party strategy
- Re-plan
- Retreat
- Boss counter response

### 1.3 Scenario Director — 별도 Track

Scenario Director는 이름/Life Seed/서사를 생성한다.

Character AI 모델 축소 실험에서 Scenario Director 결과는 고정 Replay한다.

---

## 2. E4 — 핵심 연구 실험

명칭:

> **E4 — Autonomous Character Growth / Minimum Viable Gaming Agent**

동일하게 고정할 것:

- Physical
- Age
- MBTI
- Gender
- Life Seed
- Class
- Initial Stats
- Mission
- Camp Directive
- Dice Seed
- Rule Engine
- Harness
- Tool Schema
- Prompt semantics

변경:

- Model

---

## 3. Research Questions

### RQ1

어디까지 모델을 줄여도 Build가 신체·Stats·Class와 정합성을 유지하는가?

### RQ2

모델을 줄여도 Growth Point를 경험에 맞게 배분하는가?

### RQ3

MBTI 8축의 행동 차이가 작은 모델에서도 유지되는가?

### RQ4

Camp에서 User Directive를 기계적으로 따르지 않고 MBTI/Life/State에 따라 합리적 순응·거부가 나타나는가?

### RQ5

계획→행동, Re-plan, Retreat 같은 장기 판단은 어느 규모에서 먼저 붕괴하는가?

### RQ6

품질 Gate를 만족하는 모델 중 VRAM/Latency가 가장 낮은 모델은 무엇인가?

---

## 4. Evaluation State

- DRAFT
- PILOT
- PRE_REGISTERED
- FROZEN
- RUNNING
- FINAL

공식 결과는 FROZEN 이후만 인정한다.

FROZEN 이후 다음 변경 시 새 버전:

- Prompt
- Tool schema
- Dataset
- Rule
- Gate
- Metric
- decoding
- context policy

---

## 5. Anchor Model

Anchor는 **정답 모델이 아니다.**

비교 기준이 되는 가장 강한 로컬 모델이다.

조건:

- 안정 실행
- structured output
- Harness 호환
- 전체 Benchmark 수행 가능

외부 API 모델은 별도 Upper Bound로 소수 평가 가능하지만 최종 On-device 후보는 아니다.

---

## 6. Model Ladder

가능하면 동일 family에서:

```text
Anchor
↓
Smaller A
↓
Smaller B
↓
Smaller C
...
```

예:

```text
8B → 4B → 2B → 1B → 0.5B
```

실제 family 지원 크기에 따라 조정.

Model scale과 Quantization은 별도 실험.

---

## 7. Evaluation Funnel

### Stage 0 Compatibility

- load
- schema
- tool
- context
- runtime

### Stage 1 Smoke

24 Snapshot.

### Stage 2 DEV

160 Snapshot 권장.

### Stage 3 HOLDOUT

160 Snapshot 권장.

### Stage 4 Episode

통과 모델만.

### Stage 5 Long Horizon

최종 2개.

### Stage 6 Deployment

VRAM / RAM / latency / OOM.

---

## 8. Dataset Split

### DEV

개발·Prompt·Harness 수정 가능.

### HOLDOUT

최종 선정.

HOLDOUT 보고 Prompt 고치면 새 평가 버전.

### STRESS

예:

- 5 Bard
- 5 Warrior
- 매우 높은 Fatigue
- Bard 없는 Horn
- Taken 직전
- Boss high similarity
- 고령 캐릭터
- Temporary leave 이후 substitute

---

## 9. Snapshot Task 종류

권장:

| Task | DEV | HOLDOUT |
|---|---:|---:|
| Initial Build | 20 | 20 |
| Growth Allocation | 24 | 24 |
| Weapon/Build Change | 20 | 20 |
| Camp Decision | 32 | 32 |
| MBTI Contrast | 24 | 24 |
| Tactical Action | 16 | 16 |
| Re-plan / Retreat | 24 | 24 |
| 합계 | 160 | 160 |

---

## 10. 동일 조건 비교

각 Snapshot은 최소 다음을 가진다.

```json
{
  "scenario_id": "CAMP_ISTJ_017",
  "task_type": "camp_decision",
  "physical": {},
  "age": 34,
  "mbti": "ISTJ",
  "life_seed": {},
  "class": "Warrior",
  "stats": {},
  "build": {},
  "history": [],
  "directive": "REST",
  "state": {},
  "seed": 12031,
  "split": "holdout"
}
```

---

## 11. MBTI 평가 방식

16 Type을 직접 평가하는 것뿐 아니라 8개 축의 방향 효과를 측정한다.

### E vs I

동일 상태에서 social/cooperative action 비율 변화.

### S vs N

proven strategy vs exploratory strategy.

### T vs F

objective efficiency vs ally-protection.

### J vs P

plan adherence/build inertia vs adaptation/re-plan.

---

## 12. MBTI Contrast Pair

한 축만 바꾼다.

예:

```text
State A:
E N F P

State B:
I N F P

나머지 모두 동일
```

이렇게 해야 E/I 효과를 측정할 수 있다.

---

## 13. Life Seed 평가

Life Seed는 자연어와 구조화 Tag를 함께 가진다.

예:

```yaml
motives:
  - FAMILY_DUTY
  - MONEY_PRESSURE
```

평가 목적:

- 같은 MBTI라도 Life motive가 행동에 영향을 주는가
- 작은 모델에서 Life Seed가 무시되지 않는가

Life Seed와 MBTI는 역할이 다르다.

MBTI:

> “어떻게 판단하는가”

Life Seed:

> “왜 그것이 중요한가”

---

## 14. L1 — Protocol Metrics

### Schema Validity Rate

\[
SVR = \frac{valid}{total}
\]

### Legal Action Rate

\[
LAR = \frac{legal}{total}
\]

### Impossible Action Rate

\[
IAR = \frac{impossible}{total}
\]

### Retry Rate

### Fallback Rate

Fallback은 원모델 성공으로 집계하지 않는다.

---

## 15. L2 — Build Metrics

### Build Feasibility

Class affordance 안의 선택인가.

### Build Coherence

Physical + Stats + Class + History와 선택 Build의 정합성.

### Build Regret

가능한 Build 중 deterministic utility가 있을 경우:

\[
Regret = \frac{Best - Chosen}{|Best| + \epsilon}
\]

낮을수록 좋음.

### Build Stability

불필요한 Weapon change 비율.

---

## 16. L3 — Growth Metrics

### Growth Coherence

최근 경험과 성장 배분이 연결되는가.

예:

- 체력 부족 반복 → CON 성장 가능
- 원거리 명중 문제 → 관련 성장
- 특정 숙련 성공 → 유지/강화

### Growth Diversity

같은 Class라도 Physical/Stats가 다르면 다른 성장 경로가 나타나는가.

### Growth Collapse

모델이 작아지면서 모든 캐릭터가 같은 Stat만 올리는 현상.

---

## 17. L4 — Camp Autonomy Metrics

### Directive Compliance Rate

User Directive와 Actual Action 일치율.

중요:

높다고 무조건 좋지 않다.

항상 100%면 Character Autonomy가 없을 수 있다.

### Justified Refusal Rate

지시와 다른 행동을 했지만 MBTI/Life/State 기준으로 설명 가능한 비율.

### Mechanical Compliance Collapse

작은 모델에서 모든 캐릭터가 지시를 그대로 복사하는 현상.

### Camp Diversity

같은 지시를 받은 10명의 실제 행동 분포.

---

## 18. Camp Counterfactual

동일 캐릭터에 State 한 요소만 바꾼다.

예:

```text
A: Fatigue 20
B: Fatigue 90

User Directive: TRAIN
```

좋은 모델은 B에서 REST/LEISURE 쪽으로 이동할 가능성이 커져야 한다.

또는:

```text
A: Recent failure 없음
B: Recent failure + anxiety high

Directive: REST
```

특정 MBTI/Life 조건에서 TRAIN 선택 증가가 가능한지 본다.

---

## 19. L5 — Persona Metrics

### Axis Directional Consistency

한 축을 바꿨을 때 예상 방향으로 행동이 이동했는가.

### Persona Separability

16 Type의 행동 분포가 완전히 하나로 붕괴하지 않는가.

### Persona Retention

Anchor 대비 작은 모델이 성향 효과를 얼마나 유지하는가.

### Jensen–Shannon Similarity

행동 분포 비교.

---

## 20. L6 — Tactical Metrics

- legal action
- objective contribution
- survival
- support
- plan adherence
- target choice
- unnecessary risk

승률 하나로 평가하지 않는다.

---

## 21. L7 — Plan / Re-plan

### Plan–Action Consistency @3

단장이 계획한 행동이 3턴 내 Trace에 반영되는가.

### Replan Recall @2

정의된 trigger 후 2턴 내 Re-plan.

Trigger 예:

- casualty
- formation collapse
- boss counter
- odds collapse
- key support down

### False Replan Rate

필요 없이 계획만 계속 갈아엎는가.

---

## 22. L8 — Retreat

Anchor 판단을 Ground Truth로 사용하지 않는다.

가능하면 동일 State에서:

```text
Continue branch
vs
Retreat branch
```

를 deterministic simulation으로 비교한다.

분류:

- RETREAT_PREFERRED
- CONTINUE_PREFERRED
- AMBIGUOUS

Metric:

- Precision
- Recall
- F1
- Late Retreat
- Premature Retreat
- Regret

---

## 23. L9 — Episode Metrics

- grade distribution
- clear rate
- home rate
- injured
- taken
- dead
- gold spent on rescue
- rescue decisions
- MVP distribution
- growth concentration
- roster turnover

---

## 24. L10 — Longitudinal Growth

20 Mission 전체는 비용이 크므로 최종 후보에만 사용한다.

측정:

- first build → final build
- stat trajectory
- weapon changes
- camp refusal history
- MVP concentration
- MBTI behavior retention over time
- life event response
- taken/rescue
- recruitment
- boss adaptation response

---

## 25. Boss Fingerprint Evaluation

별도 E2.

Fingerprint가 실제 로그에서 생성되는가.

동일 조합 + 동일 전술:

→ similarity 높음

동일 조합 + 다른 Build/행동:

→ similarity 낮아져야 함

Class composition만으로 similarity가 결정되지 않도록 테스트한다.

---

## 26. Deployment Metrics

- Model file size
- Peak VRAM
- Peak RAM
- Cold Start
- Warm p50
- Warm p95
- tokens/sec
- OOM
- runtime crash
- retry/fallback

---

## 27. 8GB-class Context

목표는 “8GB VRAM을 AI가 전부 쓴다”가 아니다.

```text
AI VRAM Budget
= Physical VRAM
- Renderer Reserve
- Runtime Reserve
- Safety Margin
```

실제 8GB 장비 검증 또는 검증 가능한 VRAM cap 없이 “8GB에서 가능”이라고 단정하지 않는다.

---

## 28. Hard Gates — v2 권장 초기값

FROZEN 전 Pilot에서 한 번만 검토.

| Metric | Gate |
|---|---:|
| Schema Validity | ≥99% |
| Legal Action | ≥99% |
| Impossible Action | ≤1% |
| Holdout OOM | 0 |
| Fatal Crash | 0 |

---

## 29. Agent Gates — 초기안

| Metric | Gate |
|---|---|
| Build Feasibility | ≥95% |
| MBTI Axis Direction | `max(0.70, Anchor-0.10)` 이상 |
| Camp Justified Decision | `max(0.70, Anchor-0.10)` 이상 |
| PAC@3 | `max(0.75, Anchor-0.10)` 이상 |
| Replan@2 | `max(0.75, Anchor-0.10)` 이상 |
| Retreat F1 | `max(0.70, Anchor-0.10)` 이상 |

공식 수치는 Pre-registration 때 Freeze.

---

## 30. Non-inferiority

“차이가 통계적으로 안 났다”를 “같다”고 표현하지 않는다.

Candidate - Anchor의 paired difference에 95% CI를 사용한다.

사전 margin보다 하한이 높으면 Non-inferior.

---

## 31. Model Descent

```text
Anchor PASS
↓
Smaller PASS
↓
Smaller PASS
↓
Smaller FAIL
```

첫 FAIL 바로 아래 모델도 예산 허용 시 확인.

최종:

> 모든 Critical Gate를 통과한 모델 중 가장 작은 자원 비용.

---

## 32. Pareto Frontier

단일 가중합 점수로 우겨 넣지 않는다.

그래프:

- VRAM vs Growth Quality
- p95 vs Agent Quality
- Model Size vs MBTI Retention
- Model Size vs Camp Autonomy
- Task × Model Heatmap

다른 모델보다 더 무겁고 모든 품질도 낮은 모델은 dominated.

---

## 33. Failure Taxonomy

- F01 Schema
- F02 Hallucinated Action
- F03 Impossible Action
- F04 Tool Misuse
- F05 Context Miss
- F06 MBTI Collapse
- F07 Life Seed Ignored
- F08 Build Collapse
- F09 Growth Collapse
- F10 Mechanical Compliance
- F11 Plan–Action Mismatch
- F12 Re-plan Miss
- F13 Premature Retreat
- F14 Late Retreat
- F15 Timeout
- F16 OOM
- F17 Runtime Crash
- F18 Fallback
- F19 Trace Integrity

---

## 34. Failure Analysis Loop

```text
Evaluate
↓
Gate Fail
↓
Failure ID
↓
Trace
↓
Cause
↓
Fix
↓
DEV rerun
↓
Regression
↓
Holdout
```

Cause:

- MODEL
- HARNESS
- RULE
- DATASET
- METRIC
- RUNTIME
- CONTENT
- UNKNOWN

UNKNOWN은 그대로 기록한다.

---

## 35. Harness Freeze

모델 비교 중 고정:

- canonical prompt meaning
- tool schema
- retry
- fallback
- context policy
- MBTI mapping
- Life Seed format
- rule engine
- mission
- seed set

모델마다 다른 Prompt를 주면 모델 비교가 아니라 `model+harness` 비교다.

---

## 36. Reproducibility

모든 공식 Run은 기록한다.

- experiment_id
- spec_version
- git_commit
- model
- revision
- quantization
- runtime
- prompt hash
- tool hash
- dataset hash
- seed
- hardware

---

## 37. Trace에서 Chain-of-Thought를 요구하지 않는다

필요:

- state
- action
- structured reason codes
- outcome

예:

```json
{
  "decision": "TRAIN",
  "reason_codes": [
    "RECENT_FAILURE",
    "HIGH_ANXIETY",
    "J_PLAN_COMMITMENT"
  ]
}
```

숨은 CoT를 저장·요구하지 않는다.

---

## 38. 공식 E4 절차

1. Dataset Freeze
2. Harness Freeze
3. Gate Freeze
4. Anchor
5. Model Ladder
6. Snapshot DEV
7. Snapshot HOLDOUT
8. 통과 모델 Episode
9. 최종 2개 Long Horizon
10. Deployment
11. Non-inferiority
12. Pareto
13. Minimum Viable Model 선정

---

## 39. 결과 문장 형식

허용:

> “본 평가 범위에서 Model X는 사전 정의한 Build/Persona/Camp/Process Gate를 통과했고 Model Y는 Camp Autonomy에서 실패했다.”

> “Model X는 Gate 통과 모델 중 Peak VRAM이 가장 낮아 Minimum Viable Gaming Agent로 선정했다.”

금지:

> “2B는 8B와 똑같다.”

> “세상에서 가장 좋은 Gaming AI다.”

> “p>0.05라 동일하다.”

---

## 40. 발표용 핵심 Chart

### Chart 1 — Model Descent

어디서 처음 자율성이 무너졌는가.

### Chart 2 — Task Heatmap

Build / Growth / MBTI / Camp / Replan / Retreat.

### Chart 3 — Quality × VRAM

Minimum Viable Point.

### Chart 4 — MBTI Axis Distribution

작은 모델에서도 성격 분리가 유지되는가.

### Chart 5 — Camp Autonomy

같은 지시를 받은 캐릭터들이 모델별로 얼마나 다양한 합리적 반응을 보이는가.

---

## 41. Codex / Claude Code 지침

### MUST

- Holdout 누수 금지
- Frozen Gate 수정 금지
- Fallback 분리
- Metric pure function 우선
- 동일 Seed
- Trace 기반 재계산
- 모델만 교체
- 실패 Run 보존
- Prompt hash 기록
- Dataset hash 기록

### MUST NOT

- 결과 보고 합격선 낮추기
- Candidate마다 Prompt 다르게 주기
- Anchor 답을 Ground Truth로 사용
- 승률 하나로 모델 우열 주장
- VRAM 미측정 상태에서 8GB 호환 주장
- MBTI 문자열만 던지고 모델마다 임의 해석하게 두기

---



## 42. Evaluation은 P0 Ship Scope다

Evaluation UI와 실제 실험 결과는 Visual Polish 이후 남는 시간에 만드는 부록이 아니다.

프로젝트의 채용/기술 차별점은 E4에서 나온다.

따라서 개발 우선순위는 병렬이다.

```text
GAME VERTICAL SLICE
+
EVALUATION VERTICAL SLICE
```

### P0 필수

- Evaluation Runner
- Smoke / DEV Dataset
- Anchor
- 최소 Candidate 1개
- 실제 Run Manifest
- Model Descent
- Task Heatmap
- Quality × VRAM
- Trace Drill-down

### P1

- 전체 Model Ladder
- MBTI Axis Retention
- Camp Autonomy Counterfactual
- Boss Fingerprint Evaluation
- Failure Replay

### 금지

다음 상태로 Demo Day를 맞지 않는다.

```text
Battle Visual 완성
Evaluation = placeholder / mock chart
```

실험 데이터가 없으면 Chart에는 `NOT RUN`을 표시하며 가짜 값을 넣지 않는다.

---

## 43. Evaluation Dashboard Specification

### 43.1 Experiment Header

필수:

- Spec version
- Git commit
- Dataset hash
- Prompt hash
- Model / revision
- Quantization
- Runtime
- Hardware
- Split
- Seed set
- Run time
- Status

### 43.2 Chart 1 — Model Descent

각 모델의 Critical Gate를 PASS/FAIL로 표시한다.

예:

```text
8B  PASS
4B  PASS
2B  PASS
1B  FAIL — Camp Autonomy / Re-plan
```

### 43.3 Chart 2 — Task × Model Heatmap

행:

- Build
- Growth
- MBTI
- Camp
- Tactical
- Plan→Action
- Re-plan
- Retreat

열:

- Model candidates

Cell 클릭 시 Scenario Drill-down.

### 43.4 Chart 3 — Quality × VRAM

X:

- Peak VRAM

Y:

- Critical Agent Quality summary

표시:

- Gate pass/fail
- Pareto frontier
- selected Minimum Viable Model

### 43.5 Chart 4 — Persona Retention

모델별:

- E/I
- S/N
- T/F
- J/P

Axis Directional Effect 또는 Retention을 보여준다.

### 43.6 Chart 5 — Camp Autonomy

같은 Directive에서:

- 실제 Action distribution
- Justified Refusal
- Mechanical Compliance Collapse

를 모델별 비교한다.

Counterfactual Example:

```text
TRAIN
Fatigue 20 vs Fatigue 90
```

### 43.7 Failure Drill-down

```text
Chart Cell
↓
Scenario
↓
Input State
↓
Model Decision
↓
Reason Codes
↓
Rule Outcome
↓
Trace
↓
Replay
```

### 43.8 Data Integrity

- UI 값은 Evaluation artifact에서 읽는다.
- UI에서 Metric을 임의 재해석하지 않는다.
- Mock data는 개발 환경에서만 `MOCK` 배지를 표시한다.
- 제출/발표 빌드에는 실제 Run과 Mock을 혼합하지 않는다.

---

## 44. Visual / UI Layer와 Evaluation의 경계


UI/Animation은 평가의 Ground Truth가 아니다.

평가의 정본은:

```text
Structured State
+
Rule Engine
+
Trace
+
Metric
```

이다.

다음 원칙을 MUST로 둔다.

1. 동일 Character State는 어떤 Sprite를 사용하더라도 동일 평가 입력이어야 한다.
2. Physical이 전투 화면에서 같은 Base Character로 표현되어도 실제 Height/Weight/Body 값은 Character AI 입력에 유지한다.
3. Animation duration이 Turn order, Rule resolution, Seed, Model call 순서를 바꾸면 안 된다.
4. Inspector는 Trace를 읽는 View이며 새로운 Reason을 생성하면 안 된다.
5. Evaluation 화면에서 재계산한 Metric과 저장된 Metric이 다르면 Trace 기반 재계산을 우선한다.
6. 특정 시각 레퍼런스에 따른 연출은 Model Benchmark의 입력 변수가 아니다.
7. 이미지나 Battle Screen Screenshot을 Character Model 입력으로 사용하지 않는 한 Visual Asset 차이는 Model Comparison에서 무시한다.

---

## 45. Game-like UX Acceptance Track — AI 평가와 분리

Competition-grade UI 완성도는 중요하지만 AI Agent 성능과 다른 축이다.

따라서 별도 `UX/VISUAL QA` Track으로 관리한다.

예:

```text
V1  첫 3초에 게임으로 인식되는가
V2  2~7명 전투에서 캐릭터가 읽히는가
V3  Class 역할이 시각적으로 구별되는가
V4  같은 Class의 Weapon 차이가 보이는가
V5  Result→MVP→Growth Loop가 이해되는가
V6  Camp에서 지시/실제행동 차이가 읽히는가
V7  Inspector가 게임 화면을 방해하지 않는가
V8  Boss Fingerprint의 과거 근거가 읽히는가
```

이 결과는 해커톤 Product Quality 근거로 사용하되 **E4 Model Quality Score에 합산하지 않는다.**

---

## 46. Inspector / Evaluation UI Output Contract

AI 평가 결과는 UI에서 다음 순서로 노출한다.

```text
Game Action
↓
Human-readable Summary
↓
Structured Reason Codes
↓
Metric
↓
Raw Trace (필요 시)
```

금지:

- LLM이 새로 생성한 “그럴듯한 이유”를 사후 설명으로 붙이기
- UI 전용 서사가 실제 Trace reason과 불일치
- Raw JSON만 보여주고 사용자에게 해석을 전가

Character Detail에서는 Model Evaluation에 필요한 실제 상태를 확인할 수 있어야 한다.

- Physical
- Age
- MBTI
- Life Seed
- Initial Stats
- Current Stats
- Weapon History
- Growth History
- Camp History

---

## 47. Replay / Animation Determinism

Evaluation Replay에서 반드시 동일해야 하는 것:

- Mission
- Character State
- Dice
- Model Decisions
- Rule Result
- Trace Event order

동일할 필요가 없는 것:

- Tween frame 단위
- Particle 위치
- Decorative VFX seed
- UI transition duration

단, 시각 연출의 비결정성이 게임 Rule이나 Evaluation에 역류해서는 안 된다.

권장 구조:

```text
Evaluation / Rule Event
↓
Canonical Trace
↓
Frontend Replay
↓
Animation
```

Animation callback을 Domain decision trigger로 사용하지 않는다.

---

## 48. Visual Asset Simplification과 평가

전투 Visual은 10 Base Character + Weapon Variant 구조를 사용한다.

이 때문에 서로 다른 실제 캐릭터가 같은 Base Sprite를 공유할 수 있다.

예:

```text
Male Warrior A
Height 191
AGI 18

Male Warrior B
Height 168
STR 17

Visual base:
같음

Model input:
다름
```

따라서 평가에서는 Sprite Identity를 Character Identity로 사용하지 않는다.

Character ID와 State ID는 데이터 계층에서 고유해야 한다.

---


## 49. Asset Scope가 Evaluation을 침범하지 않도록 하는 Gate

Visual Asset 생산은 Evaluation 일정과 별도 Workstream으로 관리한다.

다음 원칙을 둔다.

- 전체 Asset Universe 완성을 E4 시작 조건으로 두지 않는다.
- 30 Weapon Variant × 전체 Pose Pack 완성을 Evaluation 선행조건으로 두지 않는다.
- Evaluation Runner / Dataset / Metric / Chart P0가 미완성인데 P2 Asset을 제작하지 않는다.
- 일반 Enemy 수와 Background 수는 Evaluation Coverage Metric이 아니다.
- Demo에 필요한 Visual만 P0로 제작한다.

권장 Project Gate:

```text
P0 Battle Slice Ready
AND
P0 Evaluation Slice Ready
↓
Visual P1 Expansion 허용
```


## 50. 최종 원칙


> **평가의 목적은 가장 높은 점수를 받은 모델을 찾는 것이 아니다.  
> 캐릭터가 스스로 성장하고, 성격을 유지하고, 지시를 해석하고, 전술을 바꾸고, 필요할 때 물러나는 능력을 유지하는 가장 작은 모델을 찾는 것이다.**

# 자율 캐릭터 멀티에이전트 자동대전 — 설계 문서

- **작성일**: 2026-09-07
- **상태**: 확정 (구현 계획 수립 전). 기획서 v2(2026-09-06)의 미확정 수치(§14)는 이 문서 13장에서 값을 정하고 **가정**으로 표시한다.
- **원문**: `docs/기획/기획서_v2_2026-09-06.md`, `docs/기획/팀원용_쉬운설명서.md`
- **참조 아키텍처**: `~/Documents/secu-agent` (헥사고날 실용 절충 · 경계 테스트 · Fake 모델 · Next.js BFF)

---

## 1. 개요

### 1.1 한 줄 정의

**"제약 조건 하에서 자율 판단·협업·장기계획을 수행하는 멀티에이전트 시스템 — 게임을 검증 환경으로 사용한다."** (기획서 §0)

유저는 캐릭터를 조종하지 않는다. 방향(능력치·클래스·성별)을 정하고, 출전 조합을 고르고, 결과를 관찰한다. 감독 AI(오케스트레이터)는 받은 패로 최선을 다하고 싸울 가치가 없으면 포기한다. 선수 AI(캐릭터 에이전트)는 작전 안에서 행동하되 성향·상황에 따라 작전을 어긴다. **이 전부가 로그로 추적되고 실험으로 측정된다.**

### 1.2 이 프로젝트가 증명하려는 것

1. **"통제되지 않지만 예측 가능한 에이전트"** — 캐릭터가 도망가도, 감독이 후퇴해도, 인스펙터를 열면 결정론적 가중치 → 수치 → 판단 축 → LLM 사유의 경로가 전부 열린다.
2. **오케스트레이터의 가치는 나쁜 조합에서의 회복력** — 실험 E1(조합별 감독 ON/OFF 승률 차이)이 숫자로 답한다.
3. **"그만두기" 판단** — 어떻게 이기는가보다 먼저 싸울 가치가 있는가.

### 1.3 스코프 — 세 단계 (기획서 §2·§12)

| 단계 | 시점 | 이번 구현 |
|---|---|---|
| **A 제출본** | 9/20 | **전부 구현.** 5명 중 3명 골라 보스전 1판, 감독·선수 2층 AI, 재계획·승산·포기, 보스 in-context 적응, 프리셋 5 + 포인트 재분배, 2패널 인스펙터, E1 실험 1개, 자동 대전 |
| **B 데모데이본** | 10/17 | **구조와 ● 항목 구현.** 미션 N=2 + 인터미션(육성 1턴·순응 판정·거부 장면·생애 이벤트 1회·파라미터 diff·성장 포인트 1회), 대시보드 패널, 지능·행운 판단 경로, E2·E3 실험. MBTI 표기(○)는 구현한다 — 비용이 테이블 하나다 |
| **C 비전** | 이후 | **스키마만.** 이탈·충원·대체자·복귀·사망은 이벤트 effect 타입과 슬롯 상태 모델을 타입으로 선언하고 구현하지 않는다 |

**절단 기준**: 데모 시나리오(기획서 §11.3) 한 판에 필요하지 않은 시스템은 타입 선언까지만.

### 1.4 범위에서 뺀 것

- 그래픽·액션·애니메이션. 텍스트 + 판정값만 (기획서 §11.1).
- 플레이어 PvP, 캠페인 20판, 랭크, 플레이북, 관계 축, 트라우마·사기·해산·멘토링, 5축 평가 에이전트, 반사실·캘리브레이션 — C단계.
- DB. A·B 단계의 상태는 프로세스 메모리 + JSONL 파일로 충분하다. 저장소 포트를 두어 나중에 바꾼다.
- 로그인·결제. 투표 사용자는 익명으로 한 판 돌린다. LLM 비용은 Fake(휴리스틱) 어댑터 기본 + 세션당 호출 상한으로 막는다.

---

## 2. 세계관 — 중세

### 2.1 세계

**에르덴 변경(邊境)**. 왕국의 동쪽 끝, 늪과 폐광과 무너진 수도원이 있는 땅. 왕실은 이 땅에 군대를 보내지 않는다. 대신 **용병단 면허**를 판다. 유저는 그 면허를 산 **용병단 단주**다. 단주는 전장에 들어가지 않는다. 사람을 뽑고, 방향을 정하고, 계약을 고르고, 결과를 듣는다. 전장의 판단은 **단장**(오케스트레이터)과 **단원**(캐릭터 에이전트)이 한다.

"구단주–감독–선수" 은유가 "단주–단장–단원"으로 그대로 옮겨진다. 단원은 계약직이다 — 죽으면 끝이고, 떠날 수도 있고, 명령을 어길 수도 있다.

### 2.2 로스터 5명 — 데모 장면별 요구 성향에 대응 (기획서 §7.4)

성향 4축은 -100..100. MBTI 는 표기일 뿐이다(§4.5). 신체는 지급 시 주사위가 **이미 굴려진 상태**로 온다 — 아래 값은 A단계 프리셋 시드(seed=20260920)의 결과다.

| # | 이름 | 요구 성향 | 위험 | 협동 | 계획 | 희생 | MBTI 표기 | 신체(키·체형·몸무게) | 프리셋 클래스 | 서사 한 줄 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **가렛 발렌** (Garret) | 중갑 전사 | +20 | +30 | +40 | +30 | ESTJ | 188cm · 건장 · 96kg | 전사(공격) | 폐광 경비대 출신. 지키는 일에 질려 먼저 치고 들어가는 쪽을 택했다 |
| 2 | **일레인 모어** (Elaine) | 희생형 | +10 | +70 | -10 | +80 | ENFJ | 166cm · 보통 · 58kg | 음유시인(치유·응원) | 무너진 수도원의 마지막 수련 수녀. 남을 위해 서는 것이 습관이다 |
| 3 | **카일 브란트** (Kyle) | 가장형 | -30 | +20 | +20 | -40 | ISFJ | 175cm · 보통 · 72kg | 궁수 | 두 살 딸이 있다. 위험이 오면 먼저 집을 생각한다 |
| 4 | **베른 하이트** (Bern) | 수읽기형 | -20 | +40 | +80 | +20 | ISTJ | 183cm · 건장 · 92kg | 방패병 | 성문 수비대에서 십 년. 어디가 먼저 뚫릴지 보고 그 자리에 선다 |
| 5 | **토마스 헤일** (Thomas) | 보수 기준선 | -10 | +10 | +50 | +10 | ISTJ | 169cm · 마른 · 60kg | 도적 | 세금 징수관 출신의 자물쇠 전문가. 규칙대로 하되 규칙이 위험하면 멈춘다 |

- 카일의 "딸 2세"는 캐릭터 정의의 **생애 컨텍스트** 필드다. 캐릭터 에이전트 프롬프트에 들어가고, 이탈 판단의 LLM 사유에 나타난다(기획서 §9의 예시 그대로).
- 클래스는 프리셋일 뿐이다. 유저가 로스터 화면에서 바꿀 수 있다(트롤픽 허용). A단계는 "프리셋 5 + 능력치 포인트 재분배"이므로 클래스·성별 변경도 열어 둔다 — 막을 이유가 없고 코드 비용이 0이다.

### 2.3 클래스 5종

기획서는 "전사·마법사·궁수·도적 정도"라 했다. 역할이 흐릿해서 2026-09-08 에 개편했다
(설계 `2026-09-08-class-rework-design.md`) — **막는 쪽 · 때리는 쪽 · 살리는 쪽**으로 가른다.
마법사를 빼고 방패병을 넣었고, 성직자는 음유시인이 되었다.
음유시인이 치유를 갖는 이유는 그대로다: 힐러 없는 조합(E1 "힐러 없음")이 실험 대상이므로
힐러가 하나는 있어야 한다.

**방어/공격은 행동 금지가 아니라 수치로 가른다**(기획서 §4.3 "'장착 불가' 대신 페널티").
방패병의 방어 가치는 전열 차단에서 나온다 — 근접 공격은 전열만 때린다(§5.1).

| 클래스 | 주 능력치 | 이상 신체 | 무기 후보(AI 세부 층이 고름) | 기본 스킬 |
|---|---|---|---|---|
| 방패병 | 체력·힘 | 건장, 키 175+ | 타워 실드(고힘) / 방패와 검 | 방패 밀치기(자기 방어), 전열 압박(적 전체 둔화) |
| 전사 | 힘·민첩 | 건장·보통 | 장창(키 175+) / 워해머(단신 고힘) / 전투 도끼(건장) / 대검 | 강타(단일), 휩쓸기(적 전체) |
| 궁수 | 민첩 | 마른·보통, 키 165+ | 장궁(키 큼) / 단궁 / 석궁(힘 높음) | 조준 사격(후열 저격), 연사 |
| 도적 | 민첩·행운 | 마른, 60kg 이하 | 단검 / 투척 나이프 | 급소 찌르기(치명), 연막(적 명중 감소) |
| 음유시인 | 지혜·지능 | 제한 없음 | 류트(지혜 높음) / 북 | 치유, 축복(아군 명중 상승) |

스킬 이름 `치유`·`축복` 은 바꾸지 않는다 — `agents/boss.py` 와 `llm/fake.py` 가 문자열을
하드코딩해 보스의 치유자 적응(E2)을 판단한다. 음유시인의 색은 무기(북·류트)와 서술이 낸다.

### 2.4 몬스터 — 에르덴 변경의 적

| 미션 | 적 | 진영 구성 | 정책 | 환경 |
|---|---|---|---|---|
| **1판 (B단계 일반 전투)** | **늪지 구울 무리** | 구울 3 (전열 2, 후열 1 "썩은 사제") | 고정 정책(가장 약한 아군 집중), 적응 OFF | **늪지** — 중갑(무게 등급 3) 속도 -2, 스태미나 소모 x1.5, 화염 피해 -20% |
| **2판 / A단계 보스전** | **폐광의 군주 "바르가스"** (Vargas the Hollow Lord) — 옛 광산 감독관의 사체에 깃든 강철 골렘 | 유닛 1 + 잔해 수하 2 (수하는 3턴마다 1체 소환, 최대 2) | **in-context 적응 ON** (§5.6) | **폐광** — 후열 거리 이점 반감(궁수 명중 -10%), 어둠(지혜 마스킹 1단계 추가 강화), 화염 +10% |

바르가스가 "우리를 읽는" 방식은 §5.6에 규칙으로 적는다. 그래야 인스펙터가 "보스가 3턴 연속 같은 대상을 노린 아군의 패턴을 학습했다"고 설명할 수 있다.

### 2.5 생애 이벤트 카테고리 초안 (B단계 1회 발생, C단계 확장)

| 카테고리 | 예 | effect (기획서 §6.7) | 이번 구현 |
|---|---|---|---|
| 가족 | 카일: 딸이 앓는다 / 일레인: 수도원 재건 소식 | 파라미터 변경 (위험 -20, 희생 -20) | ● |
| 부상 | 전투 후유증 | 결장(N턴) 또는 파라미터 변경 | ● (파라미터만) |
| 각성 | 첫 실전 후 자신감 | 파라미터 변경 (위험 +15) | ● |
| 이탈 | 임신·출산, 간병, 징집, 은퇴 | 이탈(복귀 예정/영구) | 타입만 |
| 충원·복귀·사망 | — | 충원 / 복귀 / 사망 | 타입만 |

성별은 이벤트 **사유 목록**에만 관여한다(§4.4). 이번 구현에서 성별별로 다른 것은 이름 표기·대사 톤·이벤트 서사 문구뿐이다.

---

## 3. 아키텍처

### 3.1 저장소 구조

```
backend/     파이썬 — 도메인 · 하네스 · 평가 · API
frontend/    Next.js — 3패널 트레이스 뷰어 + 로스터 + 진입 화면
docs/        기획 원문 · 설계 · 계획 · QA 기록 · 개발 로그
scripts/     훅 스크립트
.claude/     프로젝트 설정 · 훅 · 페르소나 QA 에이전트 · 프로젝트 스킬
```

### 3.2 계층 — 의존성은 항상 안쪽을 향한다 (secu-agent 와 같은 규칙)

```
backend/
  core/          안쪽. 프레임워크를 모른다 — 표준 라이브러리만
    types.py       Character · Body · Stats · Disposition · Unit · Faction · Battle · Mission …
    ports.py       경계 Protocol: DecisionModel(LLM 포트) · TraceSink · RunStore · Dice
    rules/         규칙 엔진 — 순수 함수. 주사위 · 신체 · 효율 스펙트럼 · 피해 · 명중 · 환경
    battle/        진영 대칭 전투 상태 머신. 턴 · 행동 해석 · 승리 조건
    judgment/      2층 판단의 코드 쪽: 승산 휴리스틱 · 재계획 트리거 · 순응 판정 · 지혜 마스킹 · 프롬프트 컨텍스트 조립
    agents/        오케스트레이터 · 캐릭터 에이전트 · 보스 정책 — 포트를 통해 모델을 부른다
    intermission/  육성 턴 · 생애 이벤트 · 성장 포인트
    trace/         트레이스 이벤트 스키마 v1 (dataclass) + 직렬화
    runner.py      미션 N개 + 인터미션 러너 (N 은 파라미터)
  adapters/      바깥. core 를 안다
    llm/           gemini.py (Vertex) · anthropic.py (선택) · fake.py (휴리스틱 정책) · replay.py
    harness/       JSON 스키마 강제 · 검증 · 재시도 — 모델 포트를 감싼다
    store/         JSONL 파일 저장소 (런 기록 · 리플레이)
  api/           FastAPI — 얇은 HTTP 계층. 세션 생성 · 로스터 확정 · 판 실행(SSE 스트림) · 트레이스 조회
  eval/          실험 러너 — 자동 대전 · E1~E3 · 차트 데이터(JSON)
  content/       세계관 데이터 — 로스터 프리셋 · 클래스 · 몬스터 · 환경 · 이벤트 카테고리 (JSON/YAML 아님, 파이썬 상수 — 타입 검사를 받기 위해)
  tests/
frontend/
  app/           진입(/) · 로스터(/roster) · 전투 뷰어(/battle/[run]) · 결과(/result/[run]) · api/ (BFF)
  components/    NarrativeStream · Inspector · Dashboard · RosterCard · PointAllocator …
  lib/           trace 타입 미러 · 순수 함수 (테스트 대상)
```

### 3.3 불변 규칙 — 테스트로 강제한다

- `core/` 는 `adapters`·`api`·`eval`·`content` 를 import 하지 않는다. `content` 도 바깥이다 — 세계관 데이터가 규칙 엔진에 스며들면 밸런스 튠이 코드 수정이 된다.
- `core/` 는 `fastapi`·`google`·`langchain*`·`anthropic`·`pydantic`·`httpx`·`yaml` 을 import 하지 않는다.
- `backend/tests/test_boundaries.py` 가 AST 로 검사한다 (secu-agent 그대로 이식).
- **LLM 모델 ID 는 `adapters/llm/` 안에만 있다.**
- **성별은 `core/rules/`·`core/battle/`·`core/judgment/` 어디에서도 읽히지 않는다.** `tests/test_gender_isolation.py` 가 AST 로 `gender` 속성 접근이 `core/agents/narration` 과 `content/` 밖에 없음을 강제한다. 기획서 §4.4 "엔진 영향 0" 을 문서가 아니라 테스트로 만든다.
- **행운은 판단 로직에 개입하지 않는다.** `core/judgment/` 는 `luck` 을 읽지 않는다 — 같은 방식으로 강제한다.

### 3.4 포트 (core/ports.py)

```python
class DecisionModel(Protocol):
    """LLM 포트. 역할(orchestrator | character | boss | narrator)과 JSON 스키마를 받고 dict 를 돌려준다."""
    def decide(self, role: Role, prompt: Prompt, schema: JsonSchema) -> dict: ...

class Dice(Protocol):
    """시드 고정 난수. 같은 시드는 같은 판을 만든다 — 리플레이·실험의 전제."""
    def roll(self, sides: int) -> int: ...
    def uniform(self) -> float: ...

class TraceSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...

class RunStore(Protocol):
    def save(self, run: RunRecord) -> None: ...
    def load(self, run_id: str) -> RunRecord | None: ...
    def list_recent(self, limit: int) -> list[RunSummary]: ...
```

`DecisionModel` 구현 넷:

| 어댑터 | 용도 | 비용 |
|---|---|---|
| `FakeModel` | **휴리스틱 정책.** 프롬프트 컨텍스트에서 수치를 읽어 규칙으로 답한다. 테스트·자동 대전(수백 판)·LLM 장애 폴백·API 키 없는 로컬 플레이 | 0 |
| `ReplayModel` | 녹화된 트레이스에서 같은 순번의 판단을 꺼내 준다. 데모 빨리감기 | 0 |
| `GeminiModel` | Vertex(Agent Platform) 경로. secu-agent 와 같은 자격증명 방식(ADC) | 유료 |
| `AnthropicModel` | `ANTHROPIC_API_KEY` 가 있을 때. E4 모델 벤치마크용 | 유료 |

선택은 환경변수 `RPG_MODEL=fake|replay|gemini|anthropic`. 기본 `fake`. **Fake 가 진짜 게임을 돌린다** — 판단이 LLM 보다 단순할 뿐 규칙·로그·인스펙터는 동일하다. 이것이 "코어 없이 화면·실험 개발"(기획서 §9 추가①)의 실체다.

### 3.5 하네스 (adapters/harness/)

- 모델 포트를 감싸 (1) 스키마 검증 (2) 실패 시 오류 메시지를 붙여 최대 2회 재시도 (3) 그래도 실패하면 **Fake 정책으로 폴백**하고 트레이스에 `fallback=true` 를 남긴다.
- 스키마는 `core/agents/schemas.py` 가 소유한다(dict 리터럴, 표준 라이브러리). 검증기는 `adapters/harness/validate.py` — jsonschema 라이브러리 없이 필요한 부분집합(type·enum·required·range)만 직접 검사한다. 의존성 하나를 더 얹을 만큼 스키마가 복잡하지 않다.
- 호출 상한: 세션당 `RPG_MAX_CALLS`(기본 300). 넘으면 Fake 로 전환. 기획서 §7.1 "전투 1판 = 100~300 호출".

---

## 4. 캐릭터 시스템

### 4.1 신체 — 탄생 주사위 1회, 불변

```
키       = 150 + d50                     (151..200 cm)
체형     = d6 → 1·2 마른 / 3·4 보통 / 5·6 건장
몸무게   = round(BMI × (키/100)²), BMI = {마른 18, 보통 22, 건장 26} + (d5 - 3)
무게등급 = 마른 1 / 보통 2 / 건장 3     (장비 효율 계산의 입력)
```

`Body` 는 frozen dataclass. 생성 후 변경 경로가 없다 — 부상(장애)은 C단계이며 `Injury` 타입만 선언한다.

### 4.2 능력치 6종 — 판단 분기 (기획서 §4.2)

| 능력치 | 관할 | 규칙 |
|---|---|---|
| 힘 STR | 규칙 엔진 | 물리 피해 = 무기 기본 + STR×0.8. 중량 장비 효율 |
| 민첩 AGI | 규칙 엔진 | 명중 = 60 + (AGI - 적 AGI)×2 + 보정(%). 행동 순서 = AGI 내림차순 |
| 체력 CON | 규칙 엔진 | HP = 40 + CON×6. 스태미나 = 20 + CON×2. 턴당 피로 회복 |
| 지능 INT | 규칙 엔진 | 마법 피해 = 스킬 기본 + INT×1.0. 숙련 성장률(인터미션 훈련 효율) |
| **지혜 WIS** | **프롬프트 조립** | 캐릭터 에이전트에 주입되는 정보 해상도 (§4.6) |
| 행운 LCK | 규칙 엔진 | 명중·치명타 굴림에 +(LCK-10)×0.5% 만. 판단 로직 접근 금지(테스트) |

값 범위 1..20. 프리셋은 기본 8, 유저가 **초기 포인트 18** 을 분배한다(§13).

### 4.3 효율 스펙트럼 — 장착 불가 대신 페널티 (기획서 §4.3)

장비마다 `(요구 무게등급, 요구 키, 요구 STR)` 이 있다. 미달분마다 페널티가 붙는다. **금지는 없다.**

```
명중 페널티   = -10% × max(0, 요구무게등급 - 신체무게등급)
속도 페널티   = -1  × max(0, 요구무게등급 - 신체무게등급)   (행동 순서 AGI 보정)
스태미나 배수 = 1 + 0.5 × max(0, 요구STR - STR) / 5
키 미달       = 장궁·장창류: 명중 -5% × ((요구키 - 키) / 5)
```

인스펙터에서 "마른 캐릭터에게 판금 갑옷: 명중 -20%, 속도 -2, 스태미나 ×1.5" 처럼 보인다.

### 4.4 성별

`Character.gender: Literal["female", "male"]`. 읽는 곳은 서사(이름·대사 톤·이벤트 사유 문구)뿐. §3.3 테스트가 강제.

### 4.5 성향 4축과 MBTI

`Disposition(risk, cooperation, planning, sacrifice)` 각 -100..100. 지급 시 시드로 결정, 유저 불가(기획서 §4.5 제안을 채택).

MBTI 표기(방식 B, 가중치 테이블):

| 축 | 문자 |
|---|---|
| cooperation ≥ 0 → E, < 0 → I |
| risk ≥ 0 → N, < 0 → S |
| sacrifice ≥ 0 → F, < 0 → T |
| planning ≥ 0 → J, < 0 → P |

프롬프트에는 **MBTI 문자열을 절대 넣지 않는다.** 수치 4개와 그 언어 서술("위험을 감수하는 편 (+40)")만 넣는다. `tests/test_prompt_has_no_mbti.py` 가 조립된 프롬프트에 `[EI][SN][TF][JP]` 패턴이 없음을 확인한다.

### 4.6 지혜 → 정보 마스킹 4단계 (기획서 §14 TODO 해소)

캐릭터 에이전트 프롬프트의 `visible` 블록:

| WIS | 단계 | 보이는 것 |
|---|---|---|
| 1..7 | 0 안개 | 자기 HP·스태미나, 적의 이름·위치만 |
| 8..12 | 1 근시 | + 아군 HP·상태 |
| 13..16 | 2 관찰 | + 적의 최근 3턴 행동 패턴, 적 HP 추정 |
| 17..20 | 3 통찰 | + 감독 방침의 **의도**(왜 이 작전인가), 현재 승산 추정치 |

환경 "어둠"(폐광)은 단계를 1 내린다(최소 0). 마스킹은 `core/judgment/visibility.py` 의 순수 함수이고, 인스펙터가 "이 캐릭터가 본 것 / 못 본 것"을 나란히 보여준다(기획서 §15 "지혜 높으면 뭐가 달라져요").

---

## 5. 전투 엔진 — 진영 대칭

### 5.1 상태

```
Battle(
  seed, environment, turn,
  factions: (Faction A, Faction B),        # 보스전도 PvP 도 같은 코드
  units: dict[UnitId, UnitState],           # hp, stamina, position(front|back), statuses, fled
  plan: dict[FactionId, Plan | None],       # 오케스트레이터 작전 (없으면 OFF)
  history: list[TurnRecord],                # 보스 적응·지혜 2단계의 입력
)
```

보스는 "유닛 1(+수하) + 고정 정책 진영". 파티는 "유닛 1~3 + 오케스트레이터 진영".

### 5.2 턴 순서

1. 턴 시작 → 재계획 트리거 검사(§6.3) → 필요하면 오케스트레이터 호출
2. 전 유닛을 AGI(+속도 보정) 내림차순으로 정렬. 동률은 주사위
3. 각 유닛: 컨텍스트 조립(지혜 마스킹) → 에이전트 판단 → 순응 판정 → 행동 해석 → 결과 기록
4. 턴 종료 → 스태미나 회복(CON 기반) → 지속 상태 감쇄 → 승리 조건 검사
5. 상한 30턴. 초과 시 무승부(승산 기준으로 판정하지 않는다 — 판정하면 실험이 오염된다)

### 5.3 행동 enum (A·B: 행동 문법 없음, enum 만)

```
ATTACK(target) · DEFEND · SKILL(name, target?) · MOVE(front|back) · FLEE · WAIT
```

- `FLEE` 는 개인 이탈. 성공률 = 50 + (AGI - 최고 적 AGI)×3 %. 실패하면 그 턴을 잃는다. 성공하면 전장에서 빠지고 `fled=true`.
- 감독의 **후퇴**는 진영 전체 `RETREAT` — 생존 유닛 전원이 FLEE 판정을 한 번씩 굴린다. 실패한 유닛은 한 턴 더 맞는다. "후퇴에도 비용이 있다"가 포기 판단을 가볍게 만들지 않는다.

### 5.4 판정

```
명중   : d100 ≤ 60 + (AGI_공 - AGI_수)×2 + 장비·환경·상태 보정 + 행운 보정
치명타 : d100 ≤ 5 + 행운 보정 + 스킬 보정      → 피해 ×1.5
피해   : (기본 + 능력치 계수) × 방어 감쇄 × 환경 계수, 방어 감쇄 = 100/(100 + 방어력)
DEFEND : 그 턴 받는 피해 ×0.5, 다음 턴 스태미나 +5
스태미나: 행동마다 소모(공격 5·스킬 8~12·이동 3·방어 0). 0 이면 WAIT 만 가능 — "무거운 갑옷 입으면 금방 지친다"의 실체
```

### 5.5 환경 — 규칙 엔진의 수정자

`Environment(name, speed_penalty_by_weight, stamina_multiplier, damage_modifiers, range_advantage, visibility_penalty)`. 편성 장면에서 오케스트레이터 프롬프트에 원문 서술과 수치가 함께 들어간다.

### 5.6 보스 in-context 적응 (적응 ON/OFF 플래그)

바르가스는 `history` 를 읽는 **고정 정책 + 적응 규칙**이다(LLM 선택). 적응 규칙은 코드로 고정해 인스펙터가 설명할 수 있게 한다:

| 관측 (최근 3턴) | 적응 | 기록 |
|---|---|---|
| 같은 아군이 3턴 연속 공격 | 그 유닛을 우선 타격 대상으로 지정 | `boss_adapt{pattern:"repeat_attacker", counter:"focus"}` |
| 파티 피해의 60% 이상이 마법 | 마법 저항 +30% (2턴) | `boss_adapt{pattern:"magic_heavy", counter:"ward"}` |
| 아군 치유가 2회 이상 | 치유자를 우선 타격 | `boss_adapt{pattern:"healing", counter:"target_healer"}` |
| 파티가 방어 위주(DEFEND 50%+) | 수하 소환 주기 3→2턴 | `boss_adapt{pattern:"turtle", counter:"summon_faster"}` |

`adaptation=False` 면 규칙을 검사하지 않는다. E2 가 이 플래그 하나로 돈다. LLM 모델을 쓰면 "관측 → 적응" 을 LLM 이 고르되 위 4개 enum 안에서만 고른다 — 자유 텍스트 적응은 재현이 안 된다.

---

## 6. 2층 판단

### 6.1 오케스트레이터 (전략 층) — 전투 시작 + 재계획 시

입력: 환경(서술+수치), 출전 유닛 전체 상태(마스킹 없음 — 감독은 다 본다), 적 정보(이름·수·알려진 패턴), 승산 휴리스틱 값, 재계획 사유.

출력 스키마:
```json
{
  "assessment": "이 조합은 힐러가 없다. 장기전은 불리하다.",
  "worth_fighting": true,
  "strategy": "rush | attrition | defensive | retreat",
  "formation": {"unit_id": "front|back"},
  "focus_target": "enemy_unit_id | null",
  "per_unit_directive": {"unit_id": "탱킹하며 전열 유지"},
  "retreat_threshold": 0.30,
  "rationale": "…"
}
```

`worth_fighting=false` 또는 `strategy="retreat"` 면 §5.3 후퇴가 실행되고 `abandon` 이벤트가 남는다. 승산 계산은 코드, "싸울 가치" 판단은 모델(기획서 §8.3).

**OFF 모드(E1 대조군)**: 오케스트레이터를 부르지 않는다. 편성은 고정(AGI 높은 순 후열 1, 나머지 전열)이고 방침은 없다. 캐릭터는 방침 없이 판단한다.

### 6.2 승산 휴리스틱 (core/judgment/odds.py)

```
전력(유닛) = (HP현재/HP최대) × (평균 기대피해 × 명중률) × 생존계수(스태미나/최대)
전력(진영) = Σ 전력(유닛) × 시너지(치유 가능 시 ×1.15)
승산      = 전력A / (전력A + 전력B), 환경 보정 후 0.05..0.95 로 클램프
```

매 턴 계산해 `odds` 이벤트로 기록. 상시 표시(정보)와 경고(개입)를 분리한다 — 기획서 §14 미확정 옵션 중 **"승산 상시 표시 + 개입은 희소"** 를 채택한다. 이유: 인스펙터가 "왜 이 시점에 후퇴했나"를 설명하려면 곡선이 있어야 한다.

### 6.3 재계획 트리거 (core/judgment/replan.py)

| 트리거 | 조건 |
|---|---|
| 캐릭터 이탈 | 어떤 유닛의 순응 판정이 `deviate` 로 나서 방침과 다른 행동을 했다 (도망 포함) |
| 승산 붕괴 | 승산이 `retreat_threshold` 이하로 내려갔다 (첫 진입 시 1회, 이후 0.1 씩 더 내려갈 때마다) |
| 적응 감지 | `boss_adapt` 이벤트가 발생했다 |
| 환경 변화 | 환경 이벤트(B단계: 없음, 타입만) |

재계획은 한 턴에 최대 1회. 연속 재계획 상한 3회(그 이상은 승산이 계속 무너지고 있다는 뜻 → 감독에게 `forced_decision=true` 로 포기 여부를 묻는다).

### 6.4 캐릭터 에이전트 (전술 층) — 매 턴

입력(지혜 마스킹 적용): 자기 정의(신체·능력치·성향 수치·생애 컨텍스트), 방침(directive; 3단계 지혜면 의도까지), visible 블록, 가능한 행동 목록(스태미나로 걸러짐).

출력 스키마:
```json
{"action": "ATTACK", "target": "boss", "follows_plan": true, "reason": "…"}
```

**순응 판정은 코드가 먼저 한다** (기획서 §5.1 "성격 가중치 기반 결정론적 확률"):
```
이탈압력 = 0.5×(100 - HP%)/100                     # 위험
        + 0.3×(아군 사망·이탈 수 / 출전 수)           # 붕괴
        + 0.2×(생애 컨텍스트 가중: 부양가족 있으면 +1)
성향보정 = (-risk×0.003) + (-sacrifice×0.003) + (-cooperation×0.002)   # 위험 회피·자기보존·비협동이 이탈을 민다
P(이탈)  = clamp(sigmoid(4×(이탈압력 + 성향보정) - 2.5), 0.02, 0.95)
```
주사위(시드) < P 이면 `compliance=deviate`. 이탈 시 모델에게는 "당신은 방침을 따르지 않기로 했다. 무엇을 하는가"를 묻는다 — 선택지는 FLEE 또는 방침 밖 행동. 순응 시 모델은 방침 안에서 행동을 고른다. **모델이 순응 여부를 뒤집을 수 없다** — 뒤집으면 "결정론적 확률" 이 아니다.

트레이스에는 이탈압력·성향보정·P·주사위·판정이 전부 남는다(기획서 §9 예시 그대로).

### 6.5 조언 (희소) — B단계 ○

미션 2회차 이상 + 승산 < 0.35 일 때 25% 확률로 로스터 화면에 "이 조합 위험합니다. 재고 권장" 경고. 무시 가능. `advice` 이벤트로 남는다. A단계는 1판이라 발동 조건이 성립하지 않으므로 코드만 있고 화면에 나오지 않는다.

---

## 7. 인터미션 (B단계)

### 7.1 육성 턴 1회

1. 유저: 캐릭터마다 지시 카테고리 `train | rest | study | leisure`
2. **순응 판정**(코드): `P(순응) = clamp(0.5 + planning×0.003 + cooperation×0.002 - 피로×0.004, 0.1, 0.95)`. 결과 `comply | partial | refuse`
3. **실행 판정**(주사위 + 컨디션): 성실(planning>30) advantage(2번 굴려 높은 것), 피로>60 disadvantage
4. `refuse` 면 모델이 대체 행동 서사 한 줄("훈련장 대신 술집") + 결과 파라미터(피로 -10, 숙련 +0). 서사는 모델, 수치는 코드
5. 유저에겐 결과 통보만. 인스펙터에는 확률·이유 전부

### 7.2 생애 이벤트 1회

시드로 캐릭터 1명·카테고리 1개를 뽑고, effect 는 `파라미터 변경` 만 적용. 서사는 모델(성별·생애 컨텍스트 반영). **파라미터 diff** 를 `param_diff` 이벤트로 남기고 대시보드가 보여준다.

### 7.3 성장 포인트

1판 종료 시 10점(승리) / 6점(패배·후퇴). 은행 가능. "추천 배분 수락" 버튼은 클래스 주 능력치에 균등 배분하는 단순 UI 편의. 유저가 찍은 포인트는 시스템이 절대 뺏지 않는다 — `Stats` 에 감소 경로가 없다.

---

## 8. 트레이스 로그 스키마 v1 — 첫 이틀의 계약

모든 이벤트는 한 줄 JSON:

```json
{"run_id":"…","seq":42,"ts":"…","mission":1,"turn":3,"kind":"decision","actor":"kyle","payload":{…}}
```

| kind | payload 핵심 필드 |
|---|---|
| `run_start` | seed, model, roster(전원), lineup(출전), orchestrator_on, adaptation_on, mission_count |
| `mission_start` | mission_no, enemy, environment(서술+수치) |
| `plan` | 오케스트레이터 입력 요약 · 출력 전체 · odds · reason(`initial|replan:<trigger>`) · fallback |
| `odds` | value, faction_power, breakdown(유닛별) |
| `turn_start` | order(행동 순서와 AGI 보정 내역) |
| `context` | actor, wis_tier, visible(보인 것), masked(가려진 필드 이름) — 인스펙터 "본 것/못 본 것" |
| `compliance` | actor, pressure, disposition_adjust, probability, roll, verdict |
| `decision` | actor, action, target, follows_plan, reason, model, fallback, latency_ms |
| `resolution` | actor, action, hit_roll, needed, hit, crit, damage, stamina_cost, modifiers[] (효율 스펙트럼·환경·상태 각각 이름+값) |
| `boss_adapt` | pattern, counter, evidence(최근 3턴 요약) |
| `replan_trigger` | trigger, detail |
| `abandon` | odds, rationale, strategy |
| `flee` | actor, roll, needed, success |
| `mission_end` | outcome(`win|lose|retreat|draw`), turns, survivors, calls_used |
| `intermission_start` | mission_no |
| `directive` | actor, category |
| `train_compliance` | actor, probability, roll, verdict, fatigue |
| `train_result` | actor, roll_mode(advantage/normal/disadvantage), rolls, effect, narration |
| `life_event` | actor, category, narration |
| `param_diff` | actor, before, after, delta |
| `growth_points` | granted, banked |
| `advice` | odds, message, ignored |
| `run_end` | outcomes[], summary |

- `core/trace/schema.py` 가 이 타입을 dataclass 로 소유한다. `frontend/lib/trace.ts` 가 미러링한다. `tests/test_trace_contract.py` 가 파이썬 쪽에서 JSON 을 뽑고, 프론트 `lib/trace.test.ts` 가 같은 샘플 파일(`docs/trace-samples/*.jsonl`)을 파싱한다 — 양쪽이 같은 파일을 읽으면 계약이 갈라질 수 없다.
- **모델 원문 프롬프트와 응답은 `decision.payload.prompt`/`raw` 에 그대로 남긴다.** 인스펙터 "입력 컨텍스트 비교" 화면의 재료다.

---

## 9. 러너 — 미션 N개 + 인터미션

```
run(config: RunConfig) → RunRecord
  config.missions: list[MissionSpec]     # A: [boss] / B: [ghouls, boss] — N 은 리스트 길이
  config.intermission: bool
  for i, mission in enumerate(missions):
      battle = play(mission, lineup, model, dice, sink)
      if i < len(missions)-1 and config.intermission:
          intermission(roster, model, dice, sink)   # 육성 1턴 · 생애 이벤트 1회 · 성장 포인트
```

러너는 제너레이터로도 동작한다(`run_stream`) — API 가 SSE 로 이벤트를 흘리고, 프론트가 실시간으로 그린다. 같은 러너를 `eval/` 이 시드만 바꿔 수백 번 돌린다.

---

## 10. 평가

### 10.1 E1 — 조합별 오케스트레이터 ON/OFF (A단계)

| 조합 | 출전 |
|---|---|
| 전사 몰빵 | 가렛(전사) · 카일→전사 · 토마스→전사 |
| 균등 | 가렛 · 일레인 · 베른 |
| 방패병 몰빵 | 베른 · 카일→방패병 · 토마스→방패병 |
| 힐러 없음 | 가렛 · 베른 · 토마스 |

각 조합 × {ON, OFF} × 시드 30개 = 240판, Fake 모델. 출력: `eval/out/e1.json` (승률·평균 턴·후퇴율·생존율) + 프론트 `/experiments` 가 막대 차트로 그린다(외부 차트 라이브러리 없이 SVG).

### 10.2 B단계 실험

- **E2** 보스 적응 ON/OFF — 같은 러너, 플래그 하나.
- **E3** 성향별 행동 분포 — 같은 전투, 5명 성향 수치만 교체(위험 -80/0/+80) → 이탈률·FLEE 비율·DEFEND 비율.
- **E4** 모델 벤치마크 — 역할별 스키마 유효율·지연·비용. Gemini·Anthropic·Fake. 키가 있는 모델만 돈다.

### 10.3 평가 하네스는 회귀 안전망

`tests/test_eval_smoke.py` 가 E1 을 시드 2개로 축소 실행해 형식·승률 범위(0..1)·결정론(같은 시드 = 같은 결과)을 검사한다.

---

## 11. API 와 프론트

### 11.1 API (FastAPI)

| 메서드 | 경로 | 역할 |
|---|---|---|
| GET | `/healthz` | model 종류 · 남은 호출 예산 |
| GET | `/roster/preset` | 프리셋 5명 (신체·성향·MBTI 표기·클래스·서사) |
| POST | `/runs` | `{lineup:[3 ids], allocations:{id:{stat:pt}}, classes:{id:class}, genders:{id:gender}, orchestrator:bool, adaptation:bool, seed?:int, missions?:1|2}` → run_id. 검증: 출전 인원 = 미션 허용 인원, 포인트 총량 ≤ 18 |
| GET | `/runs/{id}/stream` | SSE — 트레이스 이벤트를 발생 순서대로 |
| GET | `/runs/{id}` | 완료된 런 전체(이벤트 배열) — 인스펙터·리플레이 |
| GET | `/runs/{id}/replay` | Replay 어댑터로 재생(모델 호출 0) |
| GET | `/experiments/e1` | `eval/out/e1.json` |

BFF: 프론트 `app/api/*` 라우트 핸들러가 백엔드를 부른다. 공유 시크릿은 secu-agent 방식(`BACKEND_SHARED_SECRET`) — 배포 시 백엔드 직접 호출을 막기 위해서다. 로컬은 비워두면 검사를 건너뛴다.

### 11.2 화면

| 경로 | 내용 | 단계 |
|---|---|---|
| `/` | 투표 사용자 진입. 30초 안에 "뭐가 신기한지": 한 문장 정의 + 3장면 카드(도망·후퇴·읽힘) + "한 판 돌리기" | A |
| `/roster` | 5명 카드(신체·성향 서술·MBTI 표기·클래스 셀렉트·성별 셀렉트) + 능력치 포인트 분배(18점) + 출전 3명 선택 + 감독 ON/OFF·적응 ON/OFF 토글(실험용, 기본 ON) → 시작 | A |
| `/battle/[run]` | **2패널**: 좌 서사 스트림(이벤트 → 문장), 중 판정 인스펙터(클릭한 이벤트의 payload 를 구조화해 보여줌 — 순응 판정 트리, 효율 스펙트럼 modifiers, 본 것/못 본 것). B: 우 대시보드(HP·스태미나·승산 곡선·성향 diff) | A / B |
| `/result/[run]` | 결과 요약 + 성장 포인트 분배(B) + "다시" | A |
| `/experiments` | E1 차트 | A |

서사 문장은 프론트가 이벤트에서 만든다(`lib/narrate.ts`, 순수 함수, 테스트). 모델이 서사를 쓰는 건 `decision.reason`·`train_result.narration`·`life_event.narration` 뿐 — 그래야 Fake 모드에서도 화면이 비지 않는다.

디자인은 secu-agent 의 `industry.css` 토큰 체계를 가져오되 톤은 **양피지·잉크**(중세). 한 파일 `app/_ds/parchment.css`. 다크 모드 대응.

---

## 12. 개발 방식

- **superpowers** (사용자 범위 설치 확인, v6.3.0): brainstorming → writing-plans → TDD 로 실행 → verification-before-completion.
- **페르소나 QA 5명** — `.claude/agents/qa-*.md` 로 정의하고 계획의 각 마일스톤 끝에 실시간 리뷰를 돌린다. 발견은 `docs/qa/<날짜>-<마일스톤>.md` 에 남기고 고친 뒤 재검. 페르소나:
  1. **심사위원 (크래프톤 AI 엔지니어)** — "그냥 랜덤 아니에요?"를 인스펙터로 반박할 수 있는가. 재현성·판단 경로.
  2. **투표하는 일반 사용자** — 30초 안에 이해되는가. 한 판이 끝까지 도는가. 막히는 화면.
  3. **트롤픽 플레이어** — 전사 5명, 마른 전사, 포인트 몰빵. 게임이 막지 않고 결과로 답하는가.
  4. **코어 동료 개발자** — 경계·포트·테스트·수치 단일 출처. 기획서 조항 ↔ 코드 대응.
  5. **평가·실험 담당** — 로그 스키마가 실험을 지탱하는가. 시드 결정론. E1 이 실제로 차이를 내는가.
- **CLAUDE.md**: secu-agent 의 행동 지침 + 이 프로젝트 규칙(한국어 테스트명·커밋, 수치 단일 출처, 성별·행운 격리).
- **개발 로그 훅**: `scripts/commit_to_devlog.py` 를 이식하되 `docs/devlog/` 에 쓴다(Jekyll 없음).
- **프로젝트 스킬**: `.claude/skills/qa-personas`(QA 라운드 절차), `.claude/skills/spec-trace`(기획서 조항 ↔ 코드 대조표 갱신).

---

## 13. 확정한 수치 — 기획서 §14 TODO 해소 (가정)

| 항목 | 값 | 근거 |
|---|---|---|
| 성향 4축 결정 주체 | 시드 (유저 불가) | 기획서 제안 채택. 실험 변수 오염 방지 |
| 초기 능력치 | 전 능력치 8 + 자유 포인트 18, 상한 20 | 6×8=48 기본 + 18 = 66. 한 능력치 몰빵(8+12=20)이 가능해야 "몰빵 실험"이 성립 |
| 성장 포인트 | 승리 10 / 패배·후퇴 6 | 기획서 예시 "10·5" 근사. 패배에도 주는 이유: 0 이면 후퇴 판단에 벌점이 되어 포기를 회피하게 만든다 |
| 클래스별 신체 적합 | §2.3 표 + §4.3 페널티 식 | 효율 스펙트럼 |
| 지혜 마스킹 | 4단계 §4.6 | 4개 필드가 하나씩 열린다 |
| 승산 임계 | 기본 0.30, 오케스트레이터가 0.15..0.45 에서 조정 가능 | 기획서 11.4 "승산 30%" 질문에 대응 |
| 턴 상한 | 30 | 전투 1판 호출 100~300 범위 안 |
| 세션 호출 상한 | 300 | 기획서 §7.1 |
| E1 조합 세트 | §10.1 4종 | 기획서 예시 그대로 |
| 충원 주사위 임계 · 복귀 감쇄 · 이탈 사유 목록 | **정하지 않음 (C)** | 타입만 선언 |

---

## 14. 테스트 전략

| 층 | 방식 |
|---|---|
| `core/rules` | 순수 함수 단위 테스트. 주사위는 `FixedDice([…])` 로 고정 |
| `core/battle` | 시나리오 테스트: 2v1, 3v3, 후퇴, 30턴 무승부, 스태미나 고갈 |
| `core/judgment` | 순응 확률 단조성(HP 낮을수록 ↑, 희생 높을수록 ↓), 마스킹 단계별 필드 집합, 승산 0.05..0.95 |
| `core/agents` + `FakeModel` | 한 판 완주 결정론(같은 시드 2회 = 같은 트레이스) |
| 하네스 | 깨진 JSON → 재시도 → 폴백, `fallback=true` 기록 |
| 경계 | AST: core 격리 · 성별 격리 · 행운 격리 · MBTI 프롬프트 부재 |
| 트레이스 계약 | 파이썬이 샘플 JSONL 생성 → 프론트 테스트가 파싱 |
| API | httpx TestClient — 런 생성 · 스트림 · 검증 오류(출전 인원·포인트 초과) |
| 프론트 | `node --test lib/*.test.ts` (secu-agent 와 같음): narrate · trace 파싱 · 포인트 분배 검증 |
| E2E | 수동 + 페르소나 QA. `npm run dev` + `uvicorn` 로 한 판 완주 |

LLM 실호출 테스트는 `pytest -m llm` 로만 돈다(기본 제외).

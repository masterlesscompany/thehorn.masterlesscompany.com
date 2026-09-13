# CLAUDE.md — Backend

`backend/` 작업 시 루트 `CLAUDE.md`(Part I·II)와 함께 로드됩니다.

---

## [Backend] Part III — Backend Architecture

### 6. 왜 계층인가

바운디드 컨텍스트가 하나(`arena`)라 BC 를 여러 개 쪼개지 않는다. 대신 **BC 안을 클린 아키텍처 3층**으로 나눈다.
분할선은 "도메인이 다르다"가 아니라 **"안쪽이냐 바깥이냐"** 다.

```
안쪽 ←────────────────────────────────────────────────→ 바깥
domain/              app/                  adapter/
표준 라이브러리만      유스케이스 조립         LLM · HTTP · 파일
엔티티·규칙·포트       러너·에이전트·인터미션    어댑터 구현
```

| 층 | 무엇이 사는가 | 무엇을 모르는가 |
|---|---|---|
| `domain/` | `entities/`(types · trace_event) · `constants/`(balance) · `ports/` · `services/`(rules · battle · judgment · josa) | app · adapter · content · eval · core · 모든 프레임워크 |
| `app/` | `use_cases/`(runner · agents · intermission) | adapter · content · eval · 모든 프레임워크 |
| `adapter/` | `inbound/api/`(router · schema) · `outbound/`(repositories · sinks · strategies) | — 전부 안다 |

**왜 이렇게 나누는가:**
- `domain/` 전체가 한 컨텍스트 윈도우에 들어간다 — AI 위임의 단위.
- 의존성 규칙이 하나다: 비즈니스 로직은 인프라를 모른다.
- 모든 협력점이 포트를 지난다 — 타입이 있고, 이름이 있고, 독립적으로 테스트된다.
- AI 가 실수해도 피해가 한 층 안에 갇힌다.
- 어느 BC 를 더해도 같은 형태다 — 패턴 하나만 익히면 전체를 구현할 수 있다.

**계산과 판단을 분리한다.** `domain/services/judgment/odds.py` 가 승산을 계산하고, 그 값을 받아 결정하는 것은 모델이다.
계산은 코드, 판단은 모델 — 이 경계가 인스펙터에 보여줄 "왜 그랬는가"를 만든다.
계산부를 모델 안에 넣으면 재현할 수 없고, 판단부를 코드로 내리면 자율성이 사라진다.

```
사람이 정한다:                    AI 가 구현한다:
├── 포트(domain/ports)            ├── 어댑터(adapter/outbound)
├── 도메인 규칙(불변식)            ├── 규칙 함수(domain/services)
├── 밸런스 수치(domain/constants)  ├── 프롬프트 조립(app/use_cases/agents)
└── TDD 시나리오                  └── 스키마 · 라우터(adapter/inbound)
```

### 7. Hexagonal Architecture (Alistair Cockburn)

**The application is the center. The world outside is a plugin.**

애플리케이션은 누가 자기를 부르는지도, 자기가 무엇을 부르는지도 몰라야 한다.
UI · 파일 · LLM · CLI · 테스트는 전부 동등한 외부 액터다.

**Port** — 애플리케이션이 **자기 언어로** 정의한 인터페이스. 안쪽이 소유한다.
**Adapter** — 하나의 포트를 하나의 외부 기술에 잇는 구현. 바깥이 소유한다.

이 저장소의 Driven Port 는 넷이고 전부 `apps/arena/domain/ports/ports.py` 에 있다.

| 포트 | 무엇을 약속하는가 | 구현 |
|---|---|---|
| `Dice` | 시드 고정 난수 — 같은 시드 = 같은 판 | `adapter/outbound/strategies/dice.py` : `SeededDice` · `FixedDice` |
| `DecisionModel` | "모델이 답한다" **만**. 검증·재시도·폴백은 약속하지 않는다 | `.../strategies/llm/fake.py:FakeModel` · `.../llm/replay.py:ReplayModel` · `.../harness/harness.py:Harness`(포트를 감싸 포트를 구현하는 데코레이터) |
| `TraceSink` | 트레이스 이벤트를 받는다. 싱크 실패가 판을 멈추면 안 된다 | `adapter/outbound/sinks/list_sink.py:ListSink` · `adapter/inbound/api/v1/arena_router.py:RunSession`(SSE 큐) |
| `RunStore` | 런 저장 · 조회 | `adapter/outbound/repositories/jsonl_run_repository.py:JsonlRunStore` |

`random` 을 직접 import 하는 파일은 `adapter/outbound/strategies/dice.py` 하나다.
난수가 어댑터로 나가 있어 `domain/` · `app/` 은 결정론을 깰 방법이 아예 없다 — `tests/test_boundaries.py` 가 예외 없이 강제한다.

**Driving Port 는 두지 않는다.** 진입점이 `app/use_cases/runner.py:run()` 하나이고 구현도 하나다 — 한 번 쓰는 추상화는 만들지 않는다(루트 §2).
러너를 호출하는 Driving Adapter 는 셋이다: `adapter/inbound/api/v1/arena_router.py`(HTTP), `eval/run.py`(실험 CLI), `tests/`(테스트 드라이버).
셋 다 러너에게는 구분되지 않는다.

**Rules:**
- 비즈니스 로직은 포트를 import 한다. 어댑터를 import 하지 않는다.
- 어댑터 하나를 갈아끼워도 다른 계층은 건드리지 않는다 — `adapter/outbound/strategies/llm/select.py` 의 `RPG_MODEL` 분기가 그 자리다.
  (현재 실제로 존재하는 어댑터는 `fake` 와 `replay` 뿐이다. `gemini`·`anthropic` 분기는 파일이 아직 없어 지연 import 시점에 실패한다 — §12 의 "새 LLM 제공자" 절차대로 채운다.)
- 테스트는 또 하나의 Driving Adapter 일 뿐이다. 애플리케이션은 차이를 모른다.
- 포트 하나에 어댑터는 여럿, 어댑터 하나에 포트는 정확히 하나.
- **포트는 구현이 둘 이상일 때만 만든다.** 위 넷은 전부 이 조건을 만족한다.

### 8. SOLID (Uncle Bob)

**Write code that is easy to change, not just code that works.**

- **S** — One class, one reason to change. If you need "and" to describe it, split it.
- **O** — Add new behavior by adding new code, not by editing existing code.
- **L** — A subtype must honor every contract the base type promises. If overriding changes expected behavior, inheritance is wrong.
- **I** — Prefer many small, role-specific interfaces over one large general-purpose one.
- **D** — Business logic must not import concrete infrastructure. Dependencies point inward only.

### 9. Clean Architecture (Uncle Bob)

**Dependencies must point inward. Inner layers know nothing about outer layers.**

```
Frameworks & Drivers  →  Interface Adapters  →  Use Cases  →  Entities
     (outermost)                                              (innermost)
```

- **Entities**: pure domain logic. No external dependencies.
- **Use Cases**: orchestrate entities. Must not depend on UI, DB, or transport.
- **Interface Adapters**: convert between domain format and external format. Controllers, Presenters, Gateways.
- **Frameworks & Drivers**: all infrastructure detail lives here. Swappable without touching inner layers.

**Rules:**
- Don't pass framework types (ORM models, HTTP request objects) into use cases.
- Define interfaces in the inner layer; implement them in the outer layer.
- Only the composition root (main / IoC container) is allowed to wire everything together.

### 10. DDD + TDD + AOP

```
┌─────────────────────────────────────────────┐
│  DDD  "What to build" — domain model        │
│  ┌───────────────────────────────────────┐  │
│  │  TDD  "How to build it" — practice   │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AOP  "Where to put extras"     │  │  │
│  │  │       cross-cutting concerns    │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

| | DDD | TDD | AOP |
|---|---|---|---|
| **Purpose** | Domain modeling | Quality assurance | Concern separation |
| **Stage** | Design | Development | Implementation / Runtime |
| **Core value** | Business alignment | Testability | Modularity |

**DDD — Domain-Driven Design (Eric Evans)**

- Use the same terms in code and conversation. If the term drifts, the model drifts.
- Identify the **Core Domain** — invest here. Generic subdomains can be built simply or outsourced.
- **Bounded Context**: one consistent model per boundary. Use an ACL at the seam to prevent external models from polluting yours.
- **Entity**: identity-based. Mutate state only from inside.
- **Value Object**: attribute-based, immutable. Replace rather than mutate.
- **Aggregate**: one Root is the only entry point. Enforce invariants inside. Reference other Aggregates by ID only.
- **Repository**: one per Aggregate Root. Interface in domain layer; implementation in infrastructure.
- **Application Service**: thin orchestrator only — load, call domain, save, publish. No business rules here.
- If logic spans entities and doesn't fit in one, extract a **Domain Service**.

**TDD — Test-Driven Development (Kent Beck)**

- **Red → Green → Refactor.** Never write production code without a failing test.
- Red: smallest failing test. One behavior, one assertion. Confirm it fails for the right reason.
- Green: minimum code to pass. Fake it if needed. Do not refactor yet.
- Refactor: remove duplication, clarify names. All tests stay green. Clean test code too.
- One behavior per test. Arrange → Act → Assert.
- Test behavior, not implementation — tests must survive internal refactoring.
- Only mock system boundaries: network, filesystem, clock. Not internal collaborators.
- Hard-to-test code signals a design problem — too many dependencies or wrong responsibilities.

**AOP — Aspect-Oriented Programming**

- Cross-cutting concerns (logging, auth, transactions, caching, retry, auditing) belong in one Aspect each.
- Keep Advice thin — if it grows complex, business logic is hiding inside it.
- Apply via annotations or config, never by calling Aspect code directly.
- Keep Pointcuts narrow — an overly broad Pointcut silently intercepts code you didn't intend.
- Never use AOP to compensate for bad design. Fix the coupling first.

| Concern | Advice type |
|---|---|
| Logging | Around |
| Authorization | Before |
| Transaction | Around |
| Cache | Around |
| Retry | Around |
| Audit | After Returning |
| Exception translation | After Throwing |

---

## [Backend] Part IV — Backend Project Structure Rules

### 11. 계층 구조

`~/Documents/cloud.whoareryu/fastapi/apps/dumb_and_dumber` 의 클린 아키텍처 스켈레톤을 따른다.
단일 프로세스 · 바운디드 컨텍스트 하나(`arena`). **DB 도 ORM 도 없다** — A·B 단계의 저장소는 JSONL 파일이다(설계 §1.4).
그래서 템플릿의 `adapter/outbound/orm/` · `adapter/inbound/{mcp,grpc,websocket}/` 은 만들지 않았다. 필요해지면 그때 만든다(루트 §2).

```
backend/
├── core/                    BC 밖 전역 인프라 — security.py(공유 시크릿)
├── content/                 BC 밖 세계관 데이터 — roster · classes · monsters · environments · missions · events · party
├── eval/                    BC 밖 실험 러너 — experiments(E1~E3) · metrics · run(CLI)
├── tests/                   BC 밖 테스트 — test_boundaries · test_content · test_eval
└── apps/
    └── arena/               BC #1 — 에르덴 용병단 자동대전
        ├── domain/                          최내층. 표준 라이브러리만
        │   ├── entities/  types · trace_event
        │   ├── constants/ balance.py         밸런스 수치의 단일 출처
        │   ├── ports/     ports.py           Dice · DecisionModel · TraceSink · RunStore
        │   └── services/  josa
        │       ├── rules/     body · combat · disposition · equipment · stats · casualty · grade · recovery
        │       ├── battle/    state · order · resolve
        │       └── judgment/  compliance · odds · replan · visibility · training
        ├── app/                             유스케이스. domain 만 안다
        │   └── use_cases/ runner · battle_setup · learning_cards
        │       ├── agents/       orchestrator · character · boss · prompts · schemas · narration
        │       └── intermission/ training · life_event · growth
        ├── adapter/                         최외층. 안쪽을 전부 안다
        │   ├── inbound/api/v1/       arena_router.py   (FastAPI · create_app)
        │   ├── inbound/api/schemas/  arena_schema.py
        │   └── outbound/
        │       ├── repositories/ jsonl_run_repository.py
        │       ├── sinks/        list_sink.py
        │       └── strategies/   dice.py · llm/{fake,replay,select} · harness/{harness,validate}
        └── tests/  domain/ · app/ · adapter/
```

**의존성 방향 — 화살표는 안쪽으로만 간다.**

```
adapter ──→ app ──→ domain
   │                  ↑
   └── content · core ─┘ (BC 밖. 어댑터만 만진다)

eval ──→ app · adapter   (러너를 부르는 Driving Adapter)
```

- `domain/` 은 `app` · `adapter` 도, BC 밖(`content` · `eval` · `core`)도 **import 하지 않는다**.
- `app/` 은 `adapter` 를 import 하지 않는다. 어댑터 선택은 조립 지점의 일이다.
- `domain/` · `app/` 은 인프라 프레임워크를 import 하지 않는다 — fastapi · pydantic · httpx · anthropic · google · langchain · langgraph · uvicorn · yaml.
- `content/` 는 BC 밖이다. 세계관 데이터가 규칙 엔진에 스며들면 밸런스 튠이 코드 수정이 된다(설계 §3.3).
- `adapter/inbound/api/` 는 얇다. HTTP 스키마 검증만 하고, 도메인 검증(포인트 총량 · 출전 인원)은 `domain`/`content` 가 한다.

**포트가 `domain/ports/` 에 있는 이유:** `Dice` 는 `domain/services/` 가, `TraceSink` 는 `domain/entities/trace_event.py` 가 의존한다.
인터페이스는 안쪽이 소유하고 바깥이 구현한다(§9) — 그래서 템플릿의 `app/ports/output/` 이 아니라 최내층에 둔다.
Driving Port(`app/ports/input/`)는 두지 않았다. 진입점이 `runner.run()` 하나이고 구현도 하나다(루트 §2).

**`tests/test_boundaries.py` 가 AST 로 강제하는 것 (문서가 아니라 CI 다):**

| 테스트 | 무엇을 막는가 |
|---|---|
| `test_domain_은_바깥_계층을_import_하지_않는다` | 최내층의 의존성 역전 |
| `test_app_은_adapter_를_import_하지_않는다` | 유스케이스가 기술을 고르는 것 |
| `test_안쪽_계층은_인프라_프레임워크를_import_하지_않는다` | 프레임워크가 도메인에 새는 것 |
| `test_안쪽_계층은_random_을_직접_쓰지_않는다` | 결정론 파괴 — `SeededDice` 가 `adapter` 로 나가 이제 예외가 없다 |
| `test_성별은_엔진에_닿지_않는다` | 기획서 §4.4 위반 (허용: `agents/narration.py` · `use_cases/runner.py`) |
| `test_행운은_판단에_개입하지_않는다` | 기획서 §4.2 위반 (허용: `domain/services/rules/combat.py`) |

경계를 바꿔야 한다면 **테스트를 먼저 고친다.** 테스트를 우회하지 않는다.

**import 는 `apps.arena.` 를 전부 적는다.** `sys.path` 를 건드리지 않는다 —
`from apps.arena.domain.services.rules.combat import hit_chance`. pytest·uvicorn·스크립트가 모두 `backend/` 를 루트로 본다.

---

### 12. 새 코드를 어디에 두는가

**1 파일 = 1 책임.** 표를 보고 위치를 정한다. 애매하면 "이것이 없어도 판이 돌아가는가"를 묻는다 — 돌아가면 바깥이다.

| 무엇을 추가하는가 | 어디에 | 함께 해야 할 것 |
|---|---|---|
| 새 판정 공식 (명중·피해·도주) | `domain/services/rules/combat.py` | 계수는 `domain/constants/balance.py` 에. 함수는 **순수** — 주사위를 굴리지 않고 "필요한 값"과 내역을 돌려준다 |
| 새 밸런스 수치 | `domain/constants/balance.py` **만** | 설계 문서 13장에 근거를 남긴다. 다른 파일에 리터럴 금지 |
| 새 전투 행동 | `domain/services/battle/resolve.py` + `balance.STAMINA_COST` | `app/use_cases/agents/schemas.py` 의 응답 스키마 enum 도 함께 |
| 새 판단 계산 (승산·순응·가시성) | `domain/services/judgment/` | 순수 함수 + 내역 dict. **결정은 하지 않는다** — 계산만 하고 모델에 넘긴다 |
| 새 프롬프트 | `app/use_cases/agents/prompts.py` | 응답 스키마는 `app/use_cases/agents/schemas.py` |
| 새 세계관 데이터 (몬스터·클래스·미션) | `content/` | 규칙 코드를 고치지 않고 데이터만 늘어야 한다 |
| 새 LLM 제공자 | `adapter/outbound/strategies/llm/<provider>.py` + `select.py` 분기 | 모델 ID 문자열은 이 디렉터리 **밖으로 나가지 않는다** |
| 새 HTTP 엔드포인트 | `adapter/inbound/api/v1/arena_router.py` + `.../api/schemas/arena_schema.py` | 도메인 판단을 넣지 않는다. 러너를 부르고 결과를 실어 보낼 뿐 |
| 새 실험 | `eval/experiments.py` + `eval/metrics.py` | 지표는 순수 함수. 트레이스만 읽는다 |
| 새 트레이스 이벤트 | `domain/entities/trace_event.py` 의 `KINDS` | §13 참조 — 프론트 미러링을 함께 고친다 |

**포트를 새로 만들 때 — 조건은 하나다: 구현이 둘 이상인가.**

1. `apps/arena/domain/ports/ports.py` 에 `Protocol` 을 선언한다. 안쪽 언어로 쓴다.
2. 구현 최소 둘 — 실제 것 하나, 테스트용 가짜 하나. 하나뿐이면 포트를 만들지 않는다.
3. 조립은 진입점에서만 한다 (`arena_router.py:create_app` · `eval/run.py` · 테스트). 안쪽에서 구현을 고르지 않는다.

**모든 모델 호출은 하네스를 지난다.**
`adapter/outbound/strategies/harness/harness.py:Harness` 가 스키마 강제 · 검증 · 재시도 · 폴백 · 호출 계수를 맡는다.
`DecisionModel` 을 직접 부르지 않는다 — 전투 1판이 100~300 호출이고(기획서 §7.1), 비용 상한과 실패 격리가 여기에 있다.
`adapter/outbound/strategies/llm/select.py:build_harness()` 를 쓴다.

**Boundary Gate (경계 톨게이트):**
- **Inbound**: `adapter/inbound/api/schemas/arena_schema.py` 가 HTTP 형식 ↔ 도메인 타입을 가른다. Router → Runner 경계.
- **Outbound**: `adapter/outbound/repositories/jsonl_run_repository.py` 가 `TraceEvent` ↔ JSON 을 가른다. Runner → 파일 경계.
- `domain/` · `app/` 에서는 FastAPI · pydantic 등 외부 프레임워크를 import할 수 없다.

---

### 13. 트레이스 — 이 프로젝트의 데이터 계약

DB 가 없으므로 ERD 도 없다. 대신 **트레이스 이벤트 스키마가 계약**이다 (`apps/arena/domain/entities/trace_event.py`, 기획서 §3.3 · 설계 §8).
"그냥 랜덤 아니에요?" 에 답하는 근거가 전부 여기서 나온다.

```
domain (쓴다) ─→  TraceEvent  ──→  eval/metrics.py     (읽는다 — 실험 지표)
                              ──→  arena_router.py SSE (읽는다 — 실시간 인스펙터)
                              ──→  jsonl_run_repository (읽는다 — runs/<run_id>.jsonl)
                              ──→  frontend/lib/trace.ts (읽는다 — kind 목록 미러링)
```

**이벤트 형태** — `run_id · seq · ts · mission · turn · kind · actor · payload`.
`kind` 는 `KINDS` frozenset 밖의 값을 쓰면 생성 시점에 터진다. 오타가 조용히 지나가지 않는다.

**규칙:**
- **`kind` 는 추가만 한다.** 이름을 바꾸거나 지우면 프론트와 실험이 동시에 깨진다.
- `payload` 에는 **판단의 입력과 내역을 전부 싣는다.** 결과만 남기면 인스펙터가 "왜"를 보여줄 수 없다 — 이탈 압력이면 각 항의 값과 합을 함께 남긴다.
- 싱크 실패가 판을 멈추면 안 된다. 호출자가 예외를 삼킨다.
- 저장은 `runs/<run_id>.jsonl`, 한 줄에 이벤트 하나. 첫 줄이 `run_start` 라 요약을 읽을 때 전체를 파싱하지 않아도 된다.
- 새 `kind` 를 더하면 `frontend/lib/trace.ts` 의 미러와 `docs/trace-samples/one-run.jsonl` 샘플을 함께 갱신한다. 양쪽이 같은 샘플을 읽어 계약이 갈라지지 않게 한다.

**재현의 전제:** 같은 시드 + 같은 트레이스 = 같은 판. `RPG_MODEL=replay` 가 녹화된 판단을 순서대로 돌려주고,
`SeededDice` 가 같은 굴림을 낸다. 이 둘이 깨지면 실험(E1~E3)의 비교가 무의미해진다.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## [Shared] Part II — GoF Design Patterns

### 5. GoF Patterns (Gang of Four)

**`if/else` = the caller knows the branching → caller must change when behavior changes.**
**GoF pattern = the object knows its own branching → OCP achieved naturally.**

Telling AI "use Strategy here" compresses 10 lines of `if/elif/else` intent into one word.
Prefer `@abstractmethod` and polymorphism over any conditional that dispatches on type or state.

### Conditional → Pattern Mapping

| Bad code (conditional) | GoF Pattern | Category |
|---|---|---|
| `if type == "A": ... elif type == "B":` | **Strategy** | Behavioral |
| `if state == "PENDING": ... elif state == "PAID":` | **State** | Behavioral |
| `if format == "JSON": ... elif format == "XML":` | **Factory / Abstract Factory** | Creational |
| `if a: do_a(); if b: do_b();` | **Chain of Responsibility** | Behavioral |
| `if event == "click": ... elif event == "hover":` | **Observer / Command** | Behavioral |
| `for item in list: item.do()` | **Iterator + Visitor** | Behavioral |
| `obj = ClassA() if x else ClassB()` | **Factory Method** | Creational |
| `if cache: return cache; else: fetch()` | **Proxy** | Structural |
| `obj.a(); obj.b(); obj.c();` fixed order | **Template Method** | Behavioral |
| `if A and B and C: do()` complex condition | **Specification** | Behavioral |
| `result = step1(step2(step3(x)))` nested calls | **Decorator** | Structural |
| `global_var = None; if not global_var: init()` | **Singleton** | Creational |
| `try: ... except TypeA: ... except TypeB:` | **Command + Handler** | Behavioral |
| `if legacy_api: adapt(); else: use_new()` | **Adapter** | Structural |
| `obj1.notify(obj2); obj1.notify(obj3);` manual propagation | **Observer** | Behavioral |
| `if flag: do_extra()` feature toggle | **Decorator** | Structural |
| `if subsystem_a: ...; if subsystem_b: ...` | **Facade** | Structural |
| `copy = deepcopy(obj)` manual copy | **Prototype** | Creational |
| `for`-loop directly traversing a tree | **Composite + Iterator** | Structural + Behavioral |
| `if obj_type == "remote": ... elif "local":` | **Bridge** | Structural |

### GoF 23 Pattern Reference

```
Creational (5)
├── Singleton       ← global variable + if None check
├── Factory Method  ← if/else object creation
├── Abstract Factory← platform-specific if/else
├── Builder         ← telescoping constructor (too many __init__ args)
└── Prototype       ← manual deepcopy

Structural (7)
├── Adapter         ← if legacy / new API
├── Bridge          ← if remote / local
├── Composite       ← tree traversed directly with for
├── Decorator       ← nested function calls, flag-toggled features
├── Facade          ← complex subsystem if-chain
├── Flyweight       ← repeated object creation for identical data
└── Proxy           ← if cache / if auth / if lazy-load

Behavioral (11)
├── Chain of Responsibility ← if a: do_a; if b: do_b
├── Command         ← direct method call with no undo/queue
├── Iterator        ← direct for-loop over internals
├── Mediator        ← objects holding direct references to each other
├── Memento         ← state saved manually in dict/list
├── Observer        ← manual notify calls listed in sequence
├── State           ← if state == "X": elif state == "Y":
├── Strategy        ← if type == "A": elif type == "B":
├── Template Method ← fixed-order procedural calls
├── Visitor         ← for + if isinstance() dispatch
└── Interpreter     ← string parsing with if/elif chains
```

**Rules:**
- Replace any `if/elif` that dispatches on **type or state** with Strategy or State.
- Replace any object creation `if/else` with Factory Method or Abstract Factory.
- Replace any `for + if isinstance()` with Visitor.
- Use `@abstractmethod` to enforce contracts. Never check `isinstance` in business logic.
- When AI is asked to implement branching logic, default to the pattern — not the conditional.

---

## 이 프로젝트의 규칙

이 저장소는 **자율 캐릭터 멀티에이전트 자동대전 시스템**(Wanted AI Championship 2026 출품작, 코드네임 "에르덴 용병단")이다.
유저는 캐릭터를 조종하지 않고 고용한다. 전장에서는 단장 AI 가 작전을 짜고 단원 AI 가 매 턴 판단하며, 때로는 방침을 어긴다.
**게임은 목적이 아니라 에이전트 검증 환경(testbed)이다** — 자율성이 관측 가능하고 재현 가능한지를 보이는 것이 핵심이다.

Part I·II 는 범용 지침이다. 충돌하면 **이 절과 기획서가 이긴다**.

### 문서 위치

| 무엇 | 어디 |
|---|---|
| 기획 원문 (최종 권위) | `docs/기획/기획서_v4_2026-09-09.md` — 조항 번호는 v3 를 물려받았다 |
| 계약 서사·시드 시나리오 | `docs/기획/통합시나리오_v2_2026-09-09.md` |
| 팀원용 요약 | `docs/기획/팀원용_쉬운설명서.md` |
| 설계 | `docs/superpowers/specs/` |
| 구현 계획 | `docs/superpowers/plans/` |
| 기획서 조항 ↔ 설계 ↔ 코드/테스트 대응표 | `docs/spec-trace.md` |
| 페르소나 QA 발견 | `docs/qa/` |
| 개발 일지 | `docs/devlog/` |

아키텍처와 코드 규약은 `~/Documents/secu-agent` 를 따른다.

### 저장소 파일 구조

```
RPG/
├── CLAUDE.md                이 파일 — Part I·II(범용 지침) + 이 절(프로젝트 규칙)
├── README.md
├── docker-compose.yml · .env.example
├── backend/                 Python 3.12 · FastAPI · uv
│   ├── CLAUDE.md            Part III(백엔드 아키텍처) + Part IV(백엔드 구조 규칙)
│   ├── pyproject.toml · Dockerfile
│   ├── apps/arena/          BC #1 — domain/ · app/ · adapter/ · tests/
│   ├── core/                BC 밖 전역 인프라 (security)
│   ├── content/ eval/ tests/   BC 밖 — 세계관 데이터 · 실험 러너 · 경계 테스트
│   └── runs/                JSONL 런 저장소 (런타임 산출물)
├── frontend/                Next.js 16 App Router · TypeScript
│   ├── CLAUDE.md            → AGENTS.md 위임 (AGENTS.md 는 `next dev` 가 자동 생성)
│   ├── app/                 페이지 + BFF 라우트 (app/api/**)
│   ├── components/          Dashboard · Inspector · NarrativeStream · PointAllocator 등
│   ├── lib/                 allocation · josa · trace · narrate · backend (+ *.test.ts)
│   └── Dockerfile
├── docs/
│   ├── 기획/ superpowers/{specs,plans}/ qa/ devlog/ trace-samples/
│   └── spec-trace.md
├── scripts/                 commit_to_devlog.py · make_trace_sample.py
├── .claude/
│   ├── agents/              페르소나 QA 5인 (qa-judge·qa-voter·qa-troll·qa-core-dev·qa-evaluator)
│   └── skills/              qa-personas · spec-trace
└── .github/workflows/ci.yml
```

### 계층 (backend/)

클린 아키텍처 3층이다. 화살표는 **안쪽으로만** 간다.

```
apps/arena/         바운디드 컨텍스트 #1
  domain/           최내층. 표준 라이브러리만. app·adapter·content·eval·core 를 모른다
  app/              유스케이스. domain 만 안다 — adapter 를 모른다
  adapter/          최외층. LLM · HTTP · 파일. 모델 ID 는 outbound/strategies/llm/ 에만
core/               BC 밖 전역 인프라 (공유 시크릿)
content/            BC 밖 세계관 데이터(로스터·클래스·몬스터·환경·미션·생애이벤트)
eval/               BC 밖 실험 러너 (E1~E3)
```

`content/` 가 BC 밖인 이유: 세계관 데이터가 규칙 엔진에 스며들면 밸런스 튠이 코드 수정이 된다(설계 §3.3).
구조의 원본은 `~/Documents/cloud.whoareryu/fastapi/apps/dumb_and_dumber` 스켈레톤이다.
자세한 배치 규칙은 `backend/CLAUDE.md` Part IV.

**`backend/tests/test_boundaries.py` 가 AST 로 강제한다** — 문서가 아니라 테스트다.

### 기획서가 테스트로 굳혀진 것

이 다섯은 의견이 아니라 CI 다. 바꾸려면 기획서를 먼저 바꾼다.

| 규칙 | 근거 | 강제 방식 |
|---|---|---|
| **성별은 엔진 영향 0** | 기획서 §4.4 | `domain/services/{rules,battle,judgment}`·`app/use_cases/intermission` 이 `gender` 를 읽지 않는다. 허용은 `app/use_cases/agents/narration.py`(서사 표기)와 `app/use_cases/runner.py`(리플레이용 트레이스 기록)뿐 — 둘 다 판정이 아니다 |
| **행운은 판단에 개입하지 않는다** | 기획서 §4.2 | `domain/services/judgment` 가 `luck` 을 읽지 않는다. 행운은 굴림 보정(`LUCK_ROLL_BONUS`)에만 쓴다 |
| **MBTI 는 표기일 뿐** | 기획서 §4.5 | 프롬프트에 MBTI 문자열이 없다. 판단에 들어가는 것은 성향 4축 수치다 |
| **유저 포인트는 뺏지 않는다** | 기획서 §5 | `Stats` 에 감소 경로가 없다 |
| **같은 시드 = 같은 판** | 설계 §3.4 | 난수는 전부 `Dice` 포트를 통한다. `random` 을 아는 파일은 `adapter/outbound/strategies/dice.py` 하나뿐 |

마지막 항목이 이 프로젝트의 반박 근거다 — 심사위원의 "그냥 랜덤 아니에요?" 에는 시드 재현과 트레이스로 답한다.

### 수치 단일 출처

밸런스 수치(주사위 식·페널티 계수·승산 임계·마스킹 단계·포인트 총량·턴 상한)는 **`apps/arena/domain/constants/balance.py` 한 곳**에 있다.
다른 곳에 리터럴을 쓰지 않는다. 근거는 설계 문서 13장. 튠할 때 여기만 바꾼다.

### 코드 규약

- 테스트 함수 이름은 **한국어** (`test_지혜가_낮으면_아군_상태가_가려진다`).
- 주석은 "무엇"이 아니라 **"왜"**. 기획서·설계 조항 번호를 인용한다 (`(기획서 §4.2, 설계 §4.6)`).
- 커밋 메시지는 **한국어 평서형**(`~했다`). 제목 한 줄 + 본문에 이유.
- 파이썬 명령은 `backend/` 에서 `uv run …`. 프론트는 `frontend/` 에서 `npm …`.
- 도메인 용어는 고정한다 — **단주**(유저) · **단장**(오케스트레이터) · **단원**(캐릭터 에이전트) · **인스펙터** · **트레이스**.
  코드·UI·문서·대화에서 같은 말을 쓴다. 용어가 흔들리면 모델이 흔들린다(Part III §10 DDD).

### 검증 명령

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest -q
cd frontend && npm test && npx tsc --noEmit
```

완료를 말하기 전에 실제로 돌리고 출력을 본다(§4).

### 페르소나 QA

마일스톤이 끝날 때마다 `.claude/agents/qa-*.md` 다섯 페르소나로 리뷰를 돌린다 (`/qa-personas`).
발견은 `docs/qa/` 에 남기고, 고치고, 재검한다. **발견을 무시하고 넘어가지 않는다.**

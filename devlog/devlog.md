---
layout: post
title: 개발 일지
permalink: /docs/devlog.html
date: 2026-09-11
categories: devlog
---

# 개발 일지

> 프로젝트: Masterless Company (용병단명: 뿔피리 / Company of the Horn) — 캐릭터가 스스로 판단하는 AI Agent 기반 2D 오토배틀
> 연구 질문: **자율성을 유지하는 최소 모델은 무엇인가**
> 팀: BeyondFacade — 류준(Team Lead · Agent Harness) · 장민석(Evaluation) · 신채연(Game Frontend · Rule Engine) · **이은상(QA)** · 김충식(Scenario · Content)
> 제출: 2026-09-20 (예선) · 2026-10-17 데모데이 (본선)

## 2026-09-10

저장소 초기화 첫날. 코드는 아직 없고, **뼈대와 규칙과 로컬 인프라**를 확정한 날이다.
첫 커밋은 `900ee3e Create CLAUDE.md` (14:55) 하나뿐이며, 이후 작업은 아직 미커밋 상태다.

### 1. 포트 할당 — 3700 / 8700 / 5436

다른 프로젝트 6종이 이미 로컬 포트를 점유하고 있어, 충돌하지 않는 대역을 새로 잡았다.

| 서비스 | 포트 | 비고 |
|---|---|---|
| frontend | 3700 | `http://localhost:3700` |
| backend | 8700 | `http://localhost:8700` |
| postgres | 5436 | `127.0.0.1` 바인딩 전용 |

- Postgres 포트는 순번제로 배정. **5432** foodopsagent · **5433** lifetutorial · **5434** beyondfacade · **5435** pigfarm 이 사용 중이라 **5436** 이 다음 자리였다.
- 할당 직전 `ss -ltn`으로 3700 · 8700 · 5436 세 포트가 모두 비어 있음을 확인했다.
- 값의 단일 출처는 루트 `.env` (`FRONTEND_PORT` / `BACKEND_PORT` / `POSTGRES_PORT`)이고, `docker-compose.yml`이 이를 참조한다. 단독 실행용으로 `backend/.env` · `frontend/.env.local`에 같은 값을 둔다.

### 2. Claude Code 플러그인 3종 — 프로젝트 스코프 고정

팀원이 클론하면 동일한 도구 세트를 받도록 `.claude/settings.json`에 **project 스코프**로 박았다.

| 플러그인 | 마켓플레이스 | 버전 | 용도 |
|---|---|---|---|
| `superpowers` | claude-plugins-official | 6.3.0 | 브레인스토밍 · 서브에이전트 주도 개발 · 체계적 디버깅 · red/green TDD |
| `browser-use` | claude-plugins-official | a25f0a26 | 실제 브라우저 조작. MCP `browser_exec` / `browser_screenshot` |
| `humanize-korean` | im-not-ai | 2.3.2 | AI 티 나는 한글 문서 윤문 (제출 문서·발표 자료용) |

- `superpowers`는 사용자 전역 설정에서 `false`였는데, **프로젝트 설정이 전역을 덮어쓴다**는 점을 `claude plugin list`로 확인했다 (`Disabled in ~/.claude/settings.json but still loads — project settings enable it`).
- `im-not-ai` 마켓플레이스 출처(`epoko77-ai/im-not-ai`)도 같은 파일의 `extraKnownMarketplaces`에 함께 기록해, 클론한 사람이 마켓플레이스를 따로 등록하지 않아도 해결되게 했다.
- **Claude in Chrome은 플러그인이 아니다** — Chrome 확장 기반 내장 MCP라 설치 대상이 아니었다. `browser-use`는 `uvx browser-use@latest --cli-mcp`로 뜨므로 `uv`가 필요하고, 이미 `~/.local/bin/uv`에 있어 추가 설치는 없었다.

### 3. 지침 문서 6종 재작성 — 총 826줄

이전 프로젝트에서 복사돼 온 보일러플레이트를 전부 이 프로젝트 기준으로 다시 썼다.

| 파일 | 줄수 | 성격 |
|---|---|---|
| `CLAUDE.md` | 247 | 전역 — Part 0(프로젝트) · I(작업 원칙) · II(GoF) |
| `AGENTS.md` | 67 | 전역 (Codex용) |
| `backend/apps/docs/CLAUDE.md` | 294 | Part III(아키텍처) · IV(구조 규칙) |
| `backend/apps/docs/AGENTS.md` | 101 | 백엔드 (Codex용) |
| `frontend/docs/CLAUDE.md` | 71 | Part V(프론트엔드) |
| `frontend/docs/AGENTS.md` | 46 | 프론트엔드 (Codex용) |

**제거한 이전 프로젝트 잔재**: `apps/foodopsagent/`, `core/matrix/grid_oracle_database_manager.py`, `/play` 라우트 가정, `frontend/tests/*.cjs` 존재 가정, JPA·Kafka·SMTP 어댑터 예시.

**주입한 이 프로젝트 고유 제약**:

- **자율성 원칙(HANDS OFF)** — 캐릭터의 판단을 코드로 대신 내리지 않는다. LLM이 제안하고 코드는 확정만 한다.
- **결정론** — Rule Engine·Trace·Replay는 Seed가 고정되면 같은 결과를 낸다. 렌더 경로 포함해 `Math.random()`·실제 시각 금지.
- **LLM Port** — 연구 질문이 "최소 모델"이므로 Ollama / Fake / Cloud 어댑터 교체만으로 모델을 갈아끼울 수 있어야 한다. 도메인이 LLM SDK를 import하는 순간 Model Descent 실험이 불가능해진다.
- **유비쿼터스 언어** — 뿔피리(Horn) · Camp · Life Seed · Reason Code · Trace · Snapshot · Compliance / Justified Refusal · DOWNED 는 코드에서 번역·축약하지 않는다.
- **계약 소유권 표** — Trace 스키마 · Rule Engine API · Snapshot 포맷 · Reason Code enum의 소유자와 소비자를 명시. Trace는 append-only.

프론트엔드 문서에는 브라우저 자동화 사고를 막는 규칙 7항을 이관했다 — 서버 기동이 곧 브라우저를 열라는 뜻이 아니라는 것, 준비 확인은 HTTP 요청으로, 탭은 하나만 소유, 실패 시 새 탭·재기동으로 재시도 금지, 자기가 만든 것만 닫기.

### 4. 백엔드 스캐폴드 재배치 — Fractal 11-File Set 정합

문서가 규정한 11개 경로와 실제 `backend/apps/dummy/` 디렉터리가 5곳에서 어긋나 있었다. **문서를 정본으로 잡고 디렉터리를 옮겼다.**

| 이전 | 이후 |
|---|---|
| `app/use_case/` | `app/use_cases/` |
| `app/ports/` | `app/ports/input/` · `app/ports/output/` (ISP 분리) |
| `adapter/outbound/mappers/` | `adapter/outbound/orm_mappers/` |
| `adapter/outbound/orm/` | `adapter/outbound/orms/` |
| — | `adapter/inbound/mappers/` (신설) |
| — | `adapter/outbound/repositories/` (신설) |

결과: **디렉터리 21개 / `__init__.py` 21개**. 모든 파일이 0바이트라 이동 손실은 없었다.

`{name}` 테이블 하나당 11개 파일이 대응한다 — router · use_case(input port) · interactor · port(output port) · repository · schema · dto · orm · entity · mapper · orm_mapper. 라우터를 새로 만들 때는 비즈니스 로직보다 **`GET /{prefix}/myself`를 먼저** 붙여 DI 배선이 200을 반환하는지부터 확인한다.

**Bounded Context 이름은 아직 미정.** 후보 축은 Game API(신채연) · Rule Engine(신채연) · Agent Harness(류준) · Evaluation(장민석) 넷이며, 확정 전까지 `dummy/`는 구조 템플릿으로만 쓰고 임의로 BC를 만들지 않기로 문서에 못 박았다.

### 5. `.gitignore` 3종 — 159줄

| 파일 | 줄수 | 범위 |
|---|---|---|
| `.gitignore` | 62 | 환경변수 · 시크릿 · OS · 에디터 · Claude Code · 로그 · Docker · 산출물 · `/docs/` |
| `backend/.gitignore` | 46 | Python 캐시 · venv · 패키징 · pytest/mypy/ruff · 로컬 DB · `/apps/docs/` |
| `frontend/.gitignore` | 51 | node_modules · `.next`/`dist` 양쪽 · turbo/swc · Playwright 산출물 · `.vercel` · `/docs/` |

판단이 필요했던 지점 셋:

- **`.vscode/`는 통째로 무시하지 않았다.** 프론트엔드 지침이 `settings.json`의 `onAutoForward: silent` 포트 속성을 유지 대상으로 규정하고 있어, 파일을 무시하면 규칙이 성립하지 않는다. `settings.json` · `extensions.json` · `launch.json`만 예외로 뒀다.
- **`.claude/settings.json`은 커밋, `settings.local.json`은 무시** — 전자는 팀 공용 플러그인 설정이다.
- **`.env`를 무시하면 포트 설정이 저장소에서 사라진다.** `.env.example` 3종을 만들고 `!.env.example`로 되살렸다.

docs 디렉터리는 파일별로 앵커(`/docs/`)를 걸었다. 앵커 없이 `docs/`로 쓰면 하위 트리의 모든 `docs`에 걸려 루트 규칙 하나가 나머지 둘을 덮어버린다.

`git check-ignore`로 검증한 결과: `.env` 3종 ignored / `.env.example` 3종 tracked / `__pycache__` · `.venv` · `*.db` · `node_modules` · `.next` · `playwright-report` · `.DS_Store` · `*.log` 전부 ignored.

### 6. 로컬 DB — pgvector pg17 기동 확인

다른 저장소 6곳(`kr.co.foodrm`, `cloud.beyondfacade`, `com.lifetutorial`, `demo.pigfarm`, `com.foodopenlab`, `rpg-agent`)의 compose 구성을 읽고 공통 관례를 그대로 따랐다.

**확인한 관례**: 이미지 `pgvector/pgvector:pg17` · 포트 `127.0.0.1:54XX:5432` (LAN 노출 차단) · 컨테이너명 `{프로젝트}-db`/`-api`/`-web` · 계정은 user·db = 프로젝트명, 비번 `{프로젝트}-dev` · named volume + `pg_isready` healthcheck · 백엔드는 `depends_on: condition: service_healthy`.

작성한 파일:

- **`docker-compose.yml`** — `db` 서비스 신설. `masterless-db`, `127.0.0.1:5436:5432`, healthcheck(interval 5s / timeout 3s / retries 10), named volume `masterless_pgdata`, 적재용 `./data:/data:ro` 마운트.
- **`backend/Dockerfile`** — `python:3.13-slim`, `EXPOSE 8700`. CMD는 `alembic.ini`가 있을 때만 `alembic upgrade head`를 돌린 뒤 uvicorn을 띄운다. alembic 스캐폴드 전이라 무조건 실행하면 컨테이너가 죽는다.
- **`backend/.env`** — `DATABASE_URL=postgresql+psycopg://masterless:masterless-dev@127.0.0.1:5436/masterless` (호스트용). 컨테이너 안에서는 compose가 `db:5432`로 덮어쓴다.
- **`backend/requirements.txt`** — fastapi · uvicorn[standard] · SQLAlchemy>=2.0 · psycopg[binary] · pgvector · alembic · pydantic · pydantic-settings · python-dotenv · httpx · pytest (11개).

**`frontend` 서비스는 `profiles: ["frontend"]`로 뺐다.** `frontend/Dockerfile`도 `package.json`도 없는 상태라 그대로 두면 `docker compose up`이 프론트 빌드에서 즉시 깨진다. `cloud.beyondfacade`도 같은 이유로 프로파일을 쓰고 있었다.

**기동 검증**:

```
health: healthy (기동 후 11분 경과 시점)
PostgreSQL 17.10 (Debian 17.10-1.pgdg12+1) on x86_64-pc-linux-gnu
extname | extversion
plpgsql | 1.0
vector  | 0.8.5        ← pgvector 사용 가능
/data 마운트 OK (읽기 전용)
이미지 크기 627MB
```

`create extension if not exists vector`가 통과해 벡터 검색을 쓸 준비가 됐다.

### 7. 다음 작업

- [ ] `backend/main.py` 작성 — 현재 0바이트라 `backend` 컨테이너는 뜨지 않는다. `docker compose up -d db`로 DB만 사용 중
- [ ] `alembic init` — 마이그레이션 방식 확정 후. Dockerfile CMD는 이미 대응해 둠
- [ ] Bounded Context 이름 확정 → `apps/` 아래 첫 BC 생성 (`dummy/` 복제)
- [ ] ERD 초안 — 테이블 1개 = Fractal 11-File Set 1개
- [ ] 프론트엔드 스택 확정 (Next.js / Vite) → `frontend/Dockerfile` · `package.json` → compose 프로파일 해제
- [ ] `contracts/` — Trace 스키마 · Rule Engine API · Snapshot 포맷
- [ ] `docs/adr/` 개설 (최소 3건 목표)
- [ ] `core/` 매니저 네이밍 접두사 확정 (첫 매니저 작성 시)

---

## 2026-09-11

첫 코드가 들어온 날이다. 계약 4종을 쓰고, 그 계약 위에 결정 유즈케이스와 Trace 어댑터를 세우고, 테스트 72건까지 붙였다.
동시에 설계 정본 2건을 고쳤고, 축 B 장비에서 Qwen3.5 사다리를 실측했다.

**커밋은 0건이다.** 전부 `main` 작업 트리에만 있다 — "커밋하지 말고 파일만"이라는 지시에 따라 브랜치도 커밋도 만들지 않았다.
`git status --short` 기준 추적 파일 3개 수정(+213 / -12), 미추적 디렉터리 6개(`backend/apps/agent` · `backend/apps/game` · `backend/contracts` · `backend/eval` · `backend/tests` · `docs/superpowers`) + `backend/pytest.ini`.

### 1. 설계 정본 2건 갱신 — `thinking`을 고정값에서 평가 축으로

`backend/apps/docs/` 아래 두 문서를 고쳤다. 둘 다 어제 쓴 정본이고, 오늘 미결로 남아 있던 항목을 닫았다.

| 문서 | 변경 규모 | 내용 |
|---|---:|---|
| `Masterless_Company_Model_Selection_v1.0_2026-09-10.md` | +123 / -12 | §4.6 신설 — `thinking` on/off 평가 축 승격 |
| `Masterless_Company_Harness_First_Build_Strategy_v1.0_2026-09-10.md` | +89 / -0 | §4.9 신설 — Reason Code 어휘의 Pilot 유도 방식 |

**`thinking`을 어느 한쪽으로 고정하지 않기로 했다.** 어제까지는 "Decoding 고정 목록에 빠져 있으니 넣자"였는데, 고정하면 양방향으로 편향이 생긴다 — OFF로 고정하면 `2b`·`0.8b`가 thinking으로 살아날 여지를 실험이 원천 차단하고(과소평가), ON으로 고정하면 지연시간과 토큰 수를 thinking 길이가 지배해 축 B가 무의미해진다. EVAL §37이 금지하는 것은 CoT의 *요구·저장*이지 모델이 내부적으로 생각하는 것 자체가 아니므로, 이건 문서가 정할 값이 아니라 실험이 답할 질문이다.

사다리 4단 × 2설정 = **8구성**. 제3의 축이 아니라 같은 사다리의 두 번째 설정이며, 기존 2축 위에서 잰다. 판정 규칙 4가지를 못 박았다.

1. Anchor는 같은 `thinking` 상태끼리 비교한다 — `9b-ON ↔ 4b/2b/0.8b-ON`, `9b-OFF ↔ …-OFF`. 섞으면 §30 paired difference가 성립하지 않는다.
2. Minimum Viable 선언에 `thinking` 상태를 반드시 명시한다. 빼고 "2B로 충분하다"고 말하면 재현 불가능한 주장이 된다.
3. 축 B 수치는 상태별로 분리 보고한다. 풀링 금지 — "thinking의 대가 = VRAM +N GB, p95 +M ms"라는 증가분 자체가 산출물이다.
4. 두 상태를 하나의 승률로 합치지 않는다. best-of(둘 중 하나만 통과하면 PASS)도 금지.

§41 "모델만 교체"와 충돌하지 않는다 — `sweep.yaml`에 선언된 축이고 전 모델에 동일 적용되므로 요인설계이지 변수 오염이 아니다. 판별 기준은 "어떤 두 셀을 비교하든 정확히 하나의 축만 달라야 한다"로 표에 박았다. §10.1 결론표도 5행 → 9행(모델 × thinking)으로 늘렸다.

비용은 실험량 2배다. P0(`thinking OFF` 전 사다리) 09-13~09-15 → P1(`ON` 축소 격자) 09-15~09-17 → P2(`ON` 전 격자) 09-20 이후로 우선순위를 잘랐다. **제출 요건은 OFF만으로 충족되므로 시간이 부족하면 ON의 격자를 줄이되 축 자체는 없애지 않는다.**

> **편집자 주 (사이트)** — 같은 날 §9 실측에서 `2b` 기준 ON 비용은 2배가 아니라 **78배**로 나왔다. 본문은 그날 적은 그대로 둔다.

### 2. Reason Code 어휘 — 주관식은 설계에만 쓰고 측정에는 안 쓴다

Reason Code는 4개 계약 중 유일하게 내용을 미리 알 수 없는 항목이다. 나머지 셋은 구조를 정하는 일이지만 이건 "모델이 어떤 이유를 대는가"라는 경험적 질문이다. 손으로 추측하면 빠지고, 데이터로만 유도하면 측정 도구가 오염된다.

순수 주관식(자유 서술 이유)이 안 되는 이유 셋을 근거와 함께 적었다.

| # | 문제 | 근거 |
|---|---|---|
| 1 | §37 충돌 — 자유 서술 이유 필드는 정의상 CoT를 요구·저장한다 | EVAL §37 · PLAN §34 |
| 2 | 비교 가능성 붕괴 — 임베딩 거리가 *판단 차이*인지 *문장력 차이*인지 안 갈린다. 사실상 "작문이 유지되는 최소 모델"을 재게 된다 | EVAL §19 L5 |
| 3 | 순환 논리 — 모델이 말한 것에서만 코드를 유도하면 아무도 언급 안 한 이유는 어휘에 없다. "Life Seed를 고려하지 못했다"를 영원히 탐지 못 한다 | EVAL §33 F07 |

그래서 혼합안을 택했다. 도메인 문서에서 v0.9 시드 작성 → Pilot Run에서 객관식 `reason_codes` 필수 + 주관식 `reason_note` 병기 → `reason_note` 임베딩·클러스터링 → 누락/뭉툭/미사용 세 결함 교정 → v1.0 FREEZE 때 `reason_note`를 스키마에서 제거 → 공식 Run은 순수 객관식.

**핵심은 `pinned` 규칙이다.** 안 쓰였다고 다 지우지 않는다.

| 종류 | 예 | 미사용 시 |
|---|---|---|
| `pinned` (설계 의도) | MBTI 축 8개, `L_*` Life Seed 4개 | **남긴다.** 아무도 `L_MOTIVE_CONFLICT`를 안 골랐다면 어휘 결함이 아니라 F07 Life Seed Ignored 그 자체다. 지우면 실패가 안 보이게 된다 |
| `descriptive` (관측 서술) | 상태 코드, `B_*` 전술 근거 | 정리 대상 |

Pilot 설계는 `9b` **와** `2b` 두 단(강한 모델과 작은 모델이 말하고 싶어하는 이유가 다르다), Seed 1개, 결정 유형별 40건 내외, 임베딩은 로컬 보유 `bge-m3`, 저장은 `127.0.0.1:5436`의 pgvector `0.8.5`. 클러스터 명명은 사람이 한다 — Reason Code는 유비쿼터스 언어라 자동 생성 이름을 쓰면 코드와 대화의 용어가 갈라진다. `reason_note`의 언어도 프롬프트에서 고정한다. 한글·영어가 섞이면 클러스터가 내용이 아니라 언어로 갈린다.

일정: **09-12 Pilot Run → 09-12 오후 클러스터링·명명 → 09-13 FREEZE.**

계약 파일 목록도 4개 → 5개로 늘렸다. `reason_codes.v1.0.json`을 **별도 파일로 분리**한 이유는 버전 범프가 다른 계약의 해시를 건드리지 않게 하기 위해서다.

**미결정 2건을 남겼다.** `OTHER` 탈출구를 넣을지(넣으면 "어휘의 부족함"이 보이지 않는 문제에서 측정되는 지표로 바뀌지만, 작은 모델이 어려울 때마다 도피할 수 있어 사용률 상한 게이트가 같이 필요하다), 그리고 `thinking ON` 격자를 얼마나 줄일지. 둘 다 Freeze 전에 정한다.

### 3. `backend/contracts/` — 계약 4종 작성

| 파일 | 줄수 | 소유 |
|---|---:|---|
| `decision_io.schema.json` | 68 | 류준 |
| `trace.schema.json` | 48 | 류준 |
| `rule_engine.api.md` | 61 | 신채연 |
| `snapshot.format.md` | 64 | 장민석 |
| `reason_codes.v0.9.json` (09-10 작성) | 109 | 류준 · 김충식 |

전부 `v0.9 DRAFT`다. Freeze 대상이 아니며 Pilot 결과로 v1.0을 확정한 뒤 얼린다.

**Trace 스키마는 C9(숨은 CoT 금지)를 관례가 아니라 스키마로 강제한다.** `$defs/record`에 부정 조건을 박았다.

```json
"not": {"anyOf": [{"required": ["thinking"]}, {"required": ["chain_of_thought"]}]}
```

최상위는 `additionalProperties: false`이고 필수 10필드(`seq · run_id · mission · turn · event_type · actor · state · action · reason_codes · outcome`). `event_type`은 PLAN §40 목록 중 1단계에서 쓰는 12종만 열거했다. 결정 이벤트 4종(`build_chosen` · `weapon_changed` · `growth_allocated` · `character_action`)은 `if/then`으로 `fallback`(boolean)과 `retry`(integer ≥0)를 필수로 만들었다 — EVAL §14가 Fallback률과 Retry률을 요구하기 때문이다.

`decision_io.schema.json`은 input 7필드 필수, `mbti`는 `^[EI][SN][TF][JP]$`, `age` 20~60, `class` 5종, `decision_scope` 5종. output의 `reason_codes`는 1~4개(v0.9 권장 2~4를 감싸는 범위 — 상한은 미결정). `physical` · `stats` · `build` · `state`의 내부 키는 아직 미결정이라 EVAL §10처럼 빈 `object`로 뒀다. `reason_note`는 Pilot 한정 필드로 명시했다.

Reason Code는 전체 **62개**지만 한 호출에 노출되는 선택지는 **25~28개**다. `decision_scopes` 표로 scope별 접두사를 제한한다 — `0.8b`의 Schema Validity를 지키기 위한 설계다. 접두사에서 MBTI 축 문자(`E I S N T F J P`)를 피한 것도 의도적이다. 그래야 PLAN §34의 `H_*`와 EVAL §37의 `J_PLAN_COMMITMENT`가 둘 다 원문 그대로 살아남는다. 전술 근거를 `T_`가 아니라 `B_`로 쓴 이유가 이것이다.

### 4. `apps/agent` · `apps/game` — 첫 Bounded Context 둘

`dummy/` 템플릿 구조를 따라 BC 두 개를 세웠다. 디렉터리 42개.

| BC | 파일 | 줄수 | 내용 |
|---|---:|---:|---|
| `apps/agent` | 24 | 394 | 결정 유즈케이스 — 계약 검증 · Retry · Fallback |
| `apps/game` | 11 | 63 | Trace 기록 — JSONL append-only 어댑터 |

LLM은 Output Port(`LLMPort.complete(prompt, output_schema, seed, thinking)`) 뒤에 있고, 오늘 붙인 어댑터는 `FakeAdapter` 하나다. 도메인은 LLM SDK를 import하지 않는다 — 이 경계가 깨지면 Model Descent 실험 자체가 불가능해진다.

**HANDS OFF 경계는 `fallback` 플래그로 드러낸다.** Fallback은 코드가 캐릭터 대신 내린 결정이므로 반드시 `fallback=True`로 표시한다. 판정 로직은 이렇다.

| 상황 | 코드 | 처리 |
|---|---|---|
| JSON 파싱 실패 · 스키마 위반 · 어휘 밖 코드 | F01 | Retry 1회 후 Fallback |
| `decision`/`target`/`weapon`이 Legal Action 밖 | F02 | **Retry 없이 즉시** Fallback |
| LLM 타임아웃 | F15 | 즉시 Fallback |

F02에 Retry를 안 주는 건 오늘 판정이 갈렸던 지점이다. 계획서 Task 6 표는 "retry once"였는데 설계 spec §6은 "Legal Action 밖 행동 → Rule Engine이 거부 → Fallback"으로 Retry가 없었다. **spec을 구속력 있는 쪽으로 보고 코드를 고쳤다** — 틀렸다면 한 브랜치 되돌리면 되고, 그대로 뒀으면 Retry Rate의 의미가 달라진다.

Fallback 값은 scope별로 `ATTACK|PROTECT|HOLD → HOLD`, `RETREAT|CONTINUE → CONTINUE`, `BUILD_CHANGE|GROWTH → GROWTH + {}`. **5개 scope 중 3개만 채웠다.** `HORN_RESPONSE`와 Camp(`TRAIN|REST|EDUCATE|LEISURE`)는 1단계에서 안 쓰이므로 비워 뒀고, 뿔피리·Camp가 다음 계획에 들어올 때 채운다.

`JsonlTraceAdapter`는 append-only다. 기존 파일이 0바이트가 아니면 쓰기를 거부한다.

### 5. `eval/reproducibility.py` — 계약 해시와 stale 표시

54줄. 계약 5종의 SHA-256을 떠서 Run마다 기록한다(EVAL §36 · HARNESS C4). `ReproducibilityRecord`는 15필드 — `experiment_id · spec_version · git_commit · model · revision · quantization · runtime · prompt_hash · tool_hash · dataset_hash · seed · hardware · thinking · contract_hashes · status`. `thinking`이 필드로 들어간 건 §4.6 판정규칙 ②의 귀결이다.

`is_stale()`은 해시가 하나라도 다르면 `True`다. 계약이 바뀌면 이전 결과가 자동으로 stale로 표시되고, 조용히 재해석되지 않는다.

`prompt_hash()`가 렌더 설정까지 덮도록 보강했다. `json.dumps`의 `ensure_ascii` · `sort_keys` · `indent`를 `RENDER` 상수로 뽑아 해시 재료에 넣었다 — **이 값이 바뀌면 모델이 받는 문장이 바뀌는데 해시는 그대로였다.** Pilot Run 전에 고쳐야 하는 항목이라 Minor지만 이번에 처리했다. 아직 기록된 Run이 없으므로 stale이 될 것도 없다.

### 6. 테스트 72건 · 643줄

| 파일 | 줄수 | `def test_` |
|---|---:|---:|
| `tests/agent/test_decision_interactor.py` | 159 | 16 |
| `tests/contracts/test_decision_io_schema.py` | 84 | 10 |
| `tests/game/test_jsonl_trace_adapter.py` | 72 | 6 |
| `tests/agent/test_domain_value_objects.py` | 57 | 7 |
| `tests/contracts/test_trace_schema.py` | 55 | 8 |
| `tests/agent/test_decision_prompt.py` | 50 | 8 |
| `tests/eval/test_reproducibility.py` | 47 | 4 |
| `tests/agent/test_fake_adapter.py` | 42 | 5 |
| `tests/agent/conftest.py` | 35 | — |
| `tests/conftest.py` | 30 | — |
| `tests/agent/test_decision_dependencies.py` | 12 | 1 |
| **합계** | **643** | **65** |

`def test_` 65개이고 `parametrize` 전개를 포함한 수집 건수가 72다.

`backend/pytest.ini`(4줄)를 새로 뒀다 — `testpaths = tests` · `pythonpath = .` · `addopts = --import-mode=importlib`. `requirements.txt`에는 `jsonschema` 한 줄만 추가해 11개 → 12개가 됐다. 계약 검증에 필요하다.

> **확인 범위 주의.** 오늘 이 세션에서는 `pytest`를 직접 재실행하지 못했다(비대화 세션 권한 거부). 표의 줄수와 `def test_` 65개는 방금 정적으로 센 값이고, **`72 passed in 0.10s`는 fix wave 리포트와 재리뷰어 실행 기록에 남은 값**이다. 커밋 전에 한 번 직접 돌려 확인할 것.

### 7. SDD 실행 — Task 9개, 최종 리뷰 0 Critical

구현은 서브에이전트 주도로 돌렸다. 계획서 2,095줄과 설계 spec 434줄을 `docs/superpowers/` 아래 남겼다.

모델 배치: **구현자 haiku**(계획서에 코드 전문이 있어 받아쓰기 + 테스트) · **Task 리뷰어 sonnet** · **최종 리뷰 opus**.

Task별 누적 통과 건수 — 20 → 20 → 31 → 37 → 42 → 56 → 57 → 63 → 67 → (fix wave) **72**.

최종 리뷰 결과는 **0 Critical · 4 Important · 11 Minor**. Important 4건의 처리는 이렇게 갈랐다.

| # | 내용 | 처리 |
|---|---|---|
| 1 | `DecisionResult`가 마지막 실패/출력만 보관 → 혼합 시퀀스에서 L1 재구성 불가 | 다음 계획으로 이월. 시도를 Trace에 어떻게 적을지는 계약 결정이라 먼저 손대면 추측이 된다 |
| 2 | CoT 가드가 한 단계만 깊다 — 거부된 원문에 CoT가 실릴 수 있다 | 계약 소유자(류준) 질문으로 이월 |
| 3 | 적 행동과 모델 성공이 구분 안 된다 — actor 종류 미정의 | 〃 |
| 4 | 실패 코드 필수 필드가 없어 Trace가 Snapshot-ready 보장 안 됨 | 〃 |

2~4번을 임의로 고치지 않은 근거는 CLAUDE.md §5 "계약 우선 — 임의로 바꾸지 말고 변경이 필요하면 먼저 말한다"다. 계약 변경이 한 계획 늦게 들어오는 비용을 감수했다.

fix wave로 4건을 한 번에 처리했다 — F02 즉시 Fallback, 비객체 JSON이 F01인지 확인하는 테스트, 프롬프트가 `decision`에 null을 허용하던 문구, `prompt_hash`의 RENDER 누락. 전부 Pilot Run 전에 들어가야 하는 것들이다. 재리뷰는 clean.

부수적으로 `.git/info/exclude`에 `.superpowers/` 한 줄을 넣었다. 로컬 전용이라 추적되는 `.gitignore`는 건드리지 않았다. 커밋이 없어 `.superpowers/sdd/` 폴더가 리뷰 기록의 유일한 사본이라 마무리 때 지우지 않고 보존했다.

### 8. 축 B 실측 — Qwen3.5 사다리 지연시간·VRAM

**이 개발 머신이 Model Selection §3의 축 B 측정 노드다**(RTX 5060 Ti). 사다리 4단이 전부 로컬에 적재돼 있어 추정 없이 바로 쟀다.

측정 조건: §1.4 고정 입출력 JSON · 프롬프트 1,370토큰 · `temperature 0` / `seed 12031` · warm 상태 · 각 3회(편차 거의 없음).

> **편집자 주 (사이트)** — §9 는 같은 프롬프트를 **1,368토큰**으로 적었다(`8192 - 1,368 = 6,824`). 두 값 중 어느 쪽이 실측인지 원문에 없다.

| 모델 | OFF 1건 | ON 1건 | tok/s | 로드 후 VRAM |
|---|---:|---:|---:|---:|
| `0.8b` | 0.45초 | 미종료 | 280 | 1,559 MiB |
| `2b` | 0.63초 | 48.9초 (32K ctx) | 155 | 3,329 MiB |
| `4b` | 0.92초 | 미종료 | 111 | 4,189 MiB |
| `9b` | 1.34초 | 15.7초 | 71 | 6,815 MiB |

콜드 스타트 3.0~3.7초, 이후 0.17초. prefill은 0.07~0.5초라 총시간에 영향이 없다.

구성 1개 = 344 Snapshot(EVAL §7: Smoke 24 + DEV 160 + HOLDOUT 160) 기준 벽시계 추정:

- **P0 제출 최소선(`9b`+`4b`, OFF, 688건) = 13분.** Seed 5개면 1시간
- OFF 전 사다리 4단(1,376건) = 19분
- ON 2단(`9b`·`2b`)만 = 6시간 10분

**"평가 실험량이 많아 시간이 부족하다"는 전제가 실측으로 깨졌다.** OFF 격자 전체가 20분이다. 실제 임계경로는 GPU가 아니라 ① Snapshot 320개 저작 + §29 게이트용 기대 라벨 ② `thinking ON` 격자 ③ Harness 구축이다. 일정 논의에서 "격자를 줄이자"가 나오면 줄일 대상은 ON이지 OFF가 아니다.

### 9. `thinking ON`의 함정 — 게이트 실패가 아니라 컨텍스트 예산 부족

측정 중에 한 번 밟았고, 안 밟았으면 잘못된 수치를 정본에 적을 뻔했다.

`num_ctx 8192`로 `thinking ON`을 돌리면 `0.8b` · `2b` · `4b`가 **셋 다 유효 JSON을 못 낸다.** 생성 토큰이 정확히 **6,824**에서 끊기는데 이건 `8192 - 1,368(프롬프트)`다 — thinking이 종료되지 않고 컨텍스트를 전부 태운 것이다. `9b`만 thinking 3,648자에서 스스로 멈추고 정상 JSON을 냈다.

`2b`를 `num_ctx 32768`로 재실행하니 종료됐다 — thinking 28,593자(≈7,100토큰), 48.9초, 스키마 정상.

이 상태로 그냥 기록했다면 **"`2b`는 thinking ON에서 §28 Schema Validity FAIL"이라는 틀린 결론**이 정본에 박힌다. 게이트 실패가 아니라 측정 설정 실패다. 그래서 ON 셀은 `num_ctx` 32768 이상으로 잡고, 컨텍스트 소진으로 인한 스키마 실패를 게이트 FAIL로 분류하지 않기로 했다.

부산물로 §4.6의 비용 가정이 틀린 것도 드러났다. 문서는 ON 추가 비용을 "실험량 2배"로 적었지만 실측은 `2b` 기준 **78배**(0.63초 → 48.9초)다. ON의 진짜 대가도 지연시간이 아니라 **32K 강제에 따른 KV cache 증가**이고, 이게 §27의 8GB 예산선을 직접 때린다 — §4.6 판정규칙 ③이 요구하는 "thinking의 대가 = VRAM +N GB"의 N이 여기서 나온다. **P1/P2 일정 가정은 78배 위에서 다시 계산해야 한다.**

### 10. 인프라 — 변경 없음

```
NAME            IMAGE                    SERVICE   STATUS                  PORTS
masterless-db   pgvector/pgvector:pg17   db        Up 29 hours (healthy)   127.0.0.1:5436->5432/tcp
```

어제 띄운 그대로다. `backend` 컨테이너는 여전히 안 띄웠다 — `backend/main.py`가 0바이트라서 `docker compose up -d db`로 DB만 쓰고 있다.

### 11. 다음 작업

오늘 새로 생긴 것:

- [ ] **커밋.** 오늘 작업 전량이 미커밋 상태다. 브랜치를 따서 올릴지 `main`에 직접 올릴지 결정 필요
- [ ] **`pytest` 직접 재실행 확인** — 72건은 리포트 기록값이다. 커밋 전에 한 번 돌린다
- [ ] **09-12 Reason Code Pilot Run** — `9b`·`2b`, Seed 1개, 결정 유형별 40건. 임베딩 `bge-m3` → pgvector
- [ ] **09-13 Reason Code v1.0 FREEZE** — `reason_note` 필드 제거. 이후 변경은 버전 범프로만
- [ ] **미결정 2건 확정** — `OTHER` 탈출구 채택 여부·상한 / `thinking ON` 격자 축소 규모. 둘 다 Freeze 전
- [ ] **계약 소유자(류준) 확인 4건** — CoT 가드 깊이 · actor 종류 정의 · 실패 코드 필수 필드 · `life_seed.text` 명명
- [ ] **`DecisionResult` 재설계** — 시도별 실패/출력을 Trace에 어떻게 남길지 정한 뒤
- [ ] **Fallback 미구현 scope 2개** — `HORN_RESPONSE` · `TRAIN|REST|EDUCATE|LEISURE`. 뿔피리·Camp가 들어올 때
- [ ] **벤치마크 스크립트·원시 측정 데이터 보존** — 현재 세션 스크래치에만 있어 세션 종료 시 사라진다. `backend/eval/`로 옮길지 판단
- [ ] **P1/P2 일정 재계산** — `thinking ON` 78배 실측 반영

09-10에서 이월:

- [ ] `backend/main.py` 작성 — 여전히 0바이트
- [ ] `alembic init` — 마이그레이션 방식 확정 후
- [ ] ERD 초안 — 테이블 1개 = Fractal 11-File Set 1개
- [ ] 프론트엔드 스택 확정(Next.js / Vite) → `frontend/Dockerfile` · `package.json` → compose 프로파일 해제
- [ ] `docs/adr/` 개설 (최소 3건 목표). 오늘 `thinking` 축 승격과 Reason Code Pilot 유도는 ADR 후보다
- [ ] `core/` 매니저 네이밍 접두사 확정

해소됨: `contracts/` 3종 작성 · Bounded Context 이름 확정(`agent` · `game`)

> **편집자 주 (사이트)** — §3 은 계약 **4종**(+ 09-10 의 `reason_codes` 로 5종)을 적었다. 「3종」은 09-10 체크리스트의 개수(Trace · Rule Engine API · Snapshot)다.

---

## 한눈에 보는 마일스톤

| 일자 | 내용 |
|---|---|
| 2026-09-10 | 저장소 초기화 — 포트(3700/8700/5436) · 지침 6종 826줄 · 스캐폴드 정합 · pgvector DB 기동 |
| 2026-09-11 | 첫 코드 — 계약 4종 241줄 · BC 2개(`agent`·`game`) 457줄 · 테스트 72건 · `thinking` 평가 축 승격 · Qwen3.5 사다리 실측 |
| 2026-09-20 | 예선 제출 |
| 2026-10-17 | 데모데이 (본선) |

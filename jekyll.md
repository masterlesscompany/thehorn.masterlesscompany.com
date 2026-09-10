---
layout: post
title: 개발 일지
permalink: /docs/devlog.html
date: 2026-09-10
categories: devlog
---

# 개발 일지

> 프로젝트: Masterless Company (용병단명: 뿔피리 / Company of the Horn) — 캐릭터가 스스로 판단하는 AI Agent 기반 2D 오토배틀
> 연구 질문: **자율성을 유지하는 최소 모델은 무엇인가**
> 팀: BeyondFacade — 류준 · 장민석 · 신채연 · 이은상 · 김충식
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

## 한눈에 보는 마일스톤

| 일자 | 내용 |
|---|---|
| 2026-09-10 | 저장소 초기화 — 포트(3700/8700/5436) · 지침 6종 826줄 · 스캐폴드 정합 · pgvector DB 기동 |
| 2026-09-20 | 예선 제출 |
| 2026-10-17 | 데모데이 (본선) |

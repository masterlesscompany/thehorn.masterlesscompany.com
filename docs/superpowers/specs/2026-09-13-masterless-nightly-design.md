# Masterless Company 기준 전환 + 밤 11시 자동 반영 — 설계

작성 2026-09-13 · 선행 설계 `2026-09-11-thehorn-site-design.md`

## 0. 왜

유저가 준 팀 개발일지(09-10 · 09-11)와 사이트를 대조하니 사이트가 **다른 프로젝트**를 보여주고 있었다.

| # | 발견 | 위치 |
|---|---|---|
| A1 | 이름이 「자유중대」 — 팀은 **Masterless Company**(용병단명 뿔피리 / Company of the Horn) | `_config.yml` · 푸터 · README |
| A2 | XII장이 개인 저장소 `~/Documents/RPG`(v4 · 487건)를 잰다 — 팀 저장소는 09-10 시작 · 72건 | `_data/status.yml` |
| A3 | 칸반이 v4 익명 역할(코어 A/B…) — 팀은 실명 5인 | `_data/kanban.yml` |
| B1 | `/log/` 에 팀 일지가 없다 | `_logs/` |
| B2 | 계약 5종 · 소유자, Qwen3.5 사다리 실측, Fallback 판정, Reason Code Pilot→FREEZE 가 없다 | XII장 |
| C1 | 일지 머리말(`layout: post`, `/docs/devlog.html`)이 사이트와 안 맞는다 | — |
| C2 | 일지 내부 불일치 3건 — 프롬프트 1,370 vs 1,368 / 계약 4종 vs 「3종」 / thinking ON 비용 2배 vs 실측 78배 | 일지 본문 |
| C3 | `72 passed` 는 재실행 안 한 리포트 기록값 | 일지 09-11 §6 |
| C4 | 09-12 Pilot Run · 09-13 FREEZE 예정인데 기록 없음 | 일지 §11 |

## 1. 결정 (유저 확정)

1. 사이트 기준 = **개발일지의 팀 저장소**. RPG v4 수치는 사이트에서 뺀다.
2. 이름 = **Masterless Company** 로 통일. 문서 서가 원문 6편은 본문 무수정, 서가에 "원문 표기는 「자유중대」" 한 줄.
3. 이은상 = **프론트엔드 — 게임 클라이언트 Flutter 전환**. 일지의 "프론트 스택 확정(Next.js/Vite)" 은 Flutter 로 닫는다. 이 Jekyll 사이트는 Flutter 로 옮기지 않는다.
4. 방식 = **1안(데이터 파일로 나눈다)**.
5. 반영 시각 = **매일 23:00**. 대상 셋 — 로컬 화면 · GitHub Pages 배포 · 개발 로그.
6. 로그 출처 = thehorn 안의 **일지 원본 파일 하나**. 팀이 이어 쓰면 23:00 에 날짜별로 쪼갠다.
7. 원격 = **설정만**. `whoareryu/thehorn`(비어 있는 public) 연결·push·Pages 켜기는 내용 확인 뒤 따로.

## 2. 콘텐츠

### 2.1 이름
- `_config.yml` `title: Masterless Company` · `title_en: Company of the Horn` · tagline 유지.
- `base.html` 푸터 문구, README 제목·설명, 「게임 본체」 링크(`RPG-agnet` — 팀 저장소 아님) → 링크 제거, "팀 저장소 비공개" 로.
- `docs.html` 서가 머리에 원문 표기 안내 한 줄.

### 2.2 XII장 「지금까지 한 것」 — `_data/status.yml` 재작성
- 머리 경고: "팀 개발일지 2026-09-11 기준 · 커밋 0건(작업 트리) · 수치는 일지에 적힌 값".
- 타일: 작업 2일 · 테스트 72건(**리포트 기록값**) · 계약 5종 · BC 2개(`agent` · `game`).
- 표 ① 계약 5종 × 줄수 · 소유자 · 상태(v0.9 DRAFT).
- 표 ② 모델 사다리 실측 — `0.8b/2b/4b/9b` × OFF 1건 · ON 1건 · tok/s · VRAM. ON 미종료 셋은 "**컨텍스트 소진 — 측정 설정 실패, 게이트 FAIL 아님**".
- 표 ③ 코드가 대신 내린 결정(Fallback) — F01 · F02 · F15.
- 한 줄 요약: "OFF 전 사다리 19분 — 임계경로는 GPU 가 아니라 Snapshot 저작 · thinking ON · Harness".
- 뺀다: 487/22/47/14.6k 타일, E1 표, v4→v5.2 격차 표, `guards` 표(팀 저장소에 대응 테스트가 스키마 CoT 금지 하나뿐 — 표 ③ 옆 한 줄로).
- X장의 사다리 예시(8B→0.5B, 원문)는 그대로. 실측은 XII장에만.

### 2.3 칸반 — `_data/kanban.yml` 재작성
- 줄 = 류준 · 신채연 · 장민석 · 김충식 · 이은상 · **담당 미정**.
- 칸 = 완료 · 다음 · 이월 · 결정 필요.
- 카드 출처 = 일지 09-10 §7 · 09-11 §11 체크리스트 + 본문의 소유 표. 카드마다 `src: "09-11 §11"` 형식.
- 이은상 줄 대표 카드 = "게임 클라이언트 Flutter 전환 — Dockerfile · compose 프로파일 해제".
- 담당이 적히지 않은 카드(ERD · ADR · `main.py` · alembic · `core/` 접두사 등)는 **담당 미정** 줄. 추측 배정 안 한다.
- 09-12 Pilot Run · 09-13 FREEZE 카드에 "기록 없음" 표시.
- 페이지 경고 문구를 "v4 기준" → "팀 개발일지 기준 · 갱신일" 로.

### 2.4 개발 로그
- 원본 = `devlog/devlog.md` (저장소 루트 — Jekyll 소스 밖이라 렌더링 안 됨). 유저가 준 글 그대로 + 머리말 제거.
- 불일치 C2 3건은 본문을 고치지 않고 해당 줄 아래 `> 편집자 주:` 로 드러낸다.
- 쪼개기 결과 = `jekyll/_logs/<날짜>-team.md` (`date` · `area: team` · `seq: 0`). `## 한눈에 보는 마일스톤` 은 `jekyll/_includes/milestones.md` 로 빼서 `/log/` 머리에 넣는다.
- 기존 `_logs/2026-09-11-01-site.md` 는 남긴다(`area: site`).
- `log.html` — 일지 본문에는 h3 · 표 · 코드블록이 있다. `.logbody` 에 h3 · table(가로 스크롤) · pre 스타일 추가. 한 편이 길어 날짜별 `<details>` 로 접는다(최신 날짜만 펼침).

## 3. 밤 11시 자동 반영

### 3.1 흐름 (매일 23:00, 이 맥)

```
launchd com.whoareryu.thehorn.nightly  (StartCalendarInterval 23:00)
  └─ scripts/nightly.sh
       1. split_devlog.py      devlog/devlog.md → jekyll/_logs/*-team.md · _includes/milestones.md
       2. jekyll build -d 임시  (baseurl 빈 값)
       3. check_site.py --site 임시  ── 실패 → 여기서 멈춤. 어제 화면 유지, 로그에 사유
       4. rsync --delete 임시 → .live/          (로컬 화면이 읽는 폴더)
       5. origin 이 있을 때만: git commit -- <생성 파일만> → push → gh workflow run pages.yml
          (변경 있을 때만. 다른 미커밋 작업은 안 건드린다)
          없으면 커밋도 하지 않고 "원격 없음 — 배포 건너뜀" 기록
  로그: ~/Library/Logs/thehorn-nightly.log

launchd com.whoareryu.thehorn.serve  (KeepAlive)
  └─ /usr/bin/python3 -m http.server 4000 -b 127.0.0.1 -d .live
```

- 낮에는 파일을 고쳐도 `http://127.0.0.1:4000` 이 안 바뀐다. 지금 떠 있는 `jekyll serve`(라이브 리로드)는 내린다.
- 편집 중 미리보기가 필요하면 손으로 `bundle exec jekyll serve --port 4001` — 4000 과 겹치지 않는다.
- 맥이 **잠자기**면 깨어난 뒤 한 번 돈다. **전원이 꺼져** 있으면 그날은 건너뛴다(launchd 동작).
- launchd 는 PATH 가 비어 있다 — 스크립트가 rbenv shim 경로를 직접 잡는다.
- 설치·제거는 `scripts/nightly_install.sh` / `--uninstall`. plist 는 저장소 `ops/launchd/` 에 두고 설치 시 `~/Library/LaunchAgents` 로 복사한다.

### 3.2 GitHub Pages
- `pages.yml` — `on.push` 제거, `workflow_dispatch` 만 남긴다. 23:00 작업이 push 뒤 직접 호출하므로 로그가 **그날 밤** 배포된다(schedule 을 쓰면 로그 커밋보다 먼저 돌 수 있고 GitHub cron 은 수십 분 늦는다).
- `ci.yml` 은 그대로(push 마다 검사 — 배포 아님).
- 원격 연결 전까지 5단계(커밋·push·배포)는 건너뛴다 — 밤마다 아무도 요청하지 않은 커밋이 쌓이지 않게.

### 3.3 커밋 훅
- `.claude/settings.json` 의 `git commit` → 로그 훅 제거. `scripts/commit_to_devlog.py` 삭제(이 변경으로 고아가 된다).
- `log.html` 머리 문구 "커밋마다 한 편" → "팀 개발일지를 매일 23:00 에 옮긴다".
- `CLAUDE.md` · README 의 훅 설명 갱신.

## 4. 검사
- `check_site.py` #7 "v4 기준 명시" → "XII장이 출처(일지 날짜)와 리포트 기록값을 밝히는가".
- 신규 #8 — 칸반 카드 `role` 이 전부 정의된 줄에 있는가, 로그의 `area: team` 편 수 = 원본의 `## 날짜` 수.
- `split_devlog.py` 는 멱등 — 두 번 돌려도 산출물 동일(검증: 두 번 돌리고 `git diff --stat` 0).
- 수동: `nightly.sh` 한 번 즉시 실행 → `.live` 반영·로그 확인 → 브라우저 확인.
- 끝나면 페르소나 QA(사이트 `.claude/agents/qa-*`) 를 범용 에이전트로 돌려 `docs/qa/` 에 남긴다.

## 5. 하지 않는 것
- 원격 연결 · push · Pages 활성화 (결정 7).
- 팀 저장소 자동 읽기 (접근 경로 없음).
- 칸반 · XII장 자동 생성 — 사람이 `_data` 를 고치고, 반영만 23:00.
- 문서 서가 원문 6편 수정.

## 6. 구현하며 바뀐 것 (2026-09-13 오후)

설계를 쓴 뒤 사이트가 팀 저장소 `masterlesscompany/thehorn.masterlesscompany.com`(사용자 도메인
thehorn.masterlesscompany.com)로 들어갔다. 그래서 위 §3 의 일부가 더 단순해졌다. **이 절이 이긴다.**

| 설계 | 구현 | 이유 |
|---|---|---|
| 이은상 = 프론트 Flutter 전환 | **이은상 = QA**, Flutter 전환 카드는 **신채연(Game Frontend)** | 팀 개발일지 머리말이 역할을 명시했다 |
| 23:00 로컬 작업이 로그 커밋 → push → `gh workflow run` | **커밋하지 않는다.** `pages.yml` 이 `schedule: 0 14 * * *`(KST 23:00)로 돌며 빌드 직전에 `split_devlog.py` 를 부른다 | 원본이 이미 main 에 있으니 산출물을 커밋할 이유가 없다. 로그 산출물은 .gitignore |
| 로컬 작업이 저장소 클론에서 빌드 · `.live/` | **`~/.local/share/thehorn/`** 전용 클론에서 GitHub main 을 받아 빌드 · `live/` | macOS 는 launchd 프로세스가 `~/Documents` 를 읽지 못하게 막는다(`Operation not permitted` 실측). 사람이 작업하는 클론은 건드리지 않는다 |
| 원격 연결 전 5단계 건너뜀 | 해당 없음 | 원격이 생겼다 |
| `commit_to_devlog.py` · 커밋 훅 제거 | 이 저장소에는 thehorn 판이 없다. 루트의 같은 이름 파일은 게임(RPG) 쪽이라 손대지 않았다 | 범위 밖 |
| `_includes/milestones.md` | `_includes/devlog_head.md`(머리말) · `devlog_extra.md`(날짜 아닌 절) | 머리말(팀·제출일)도 로그 머리에 필요했다 |

추가로 발견해 막은 것: `_data` 키 `on:` · `off:` 가 YAML 1.1 불리언이 되어 사다리 표의 OFF/ON 칸이
비었다(`no:` 와 같은 함정). 키를 `think_on` · `think_off` 로 바꾸고, `check_site.py` #7 에 "구현 현황에
빈 표 칸이 없다" 를 더했다. #7 빈 칸 · #8 칸반 줄 · #8 로그 편 수는 전부 돌연변이를 넣어 빨개지는 것을 확인했다.

설치: `scripts/nightly_install.sh` (제거 `--uninstall`). 로그 `~/Library/Logs/thehorn-nightly.log`.

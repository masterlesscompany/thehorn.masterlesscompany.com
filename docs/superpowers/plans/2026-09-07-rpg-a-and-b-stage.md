# 자율 캐릭터 자동대전 — A·B 단계 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 유저가 5명 중 3명을 골라 보스전 한 판을 돌리고, 단장(오케스트레이터)이 왜 그렇게 편성하고 왜 후퇴했는지 인스펙터로 열어볼 수 있는 배포 가능한 서비스(A단계)를 만들고, 그 위에 2판 + 인터미션(B단계)을 얹는다.

**Architecture:** 파이썬 `core/`(표준 라이브러리만)에 규칙 엔진·진영 대칭 전투·2층 판단·트레이스 스키마·러너를 두고, `adapters/`가 모델(Fake·Replay·Gemini·Anthropic)·하네스·JSONL 저장소를 구현한다. FastAPI 가 SSE 로 트레이스를 흘리고 Next.js 가 서사 스트림 + 인스펙터(+대시보드)로 그린다. 같은 러너를 `eval/`이 시드만 바꿔 수백 번 돌려 E1~E3 차트를 낸다.

**Tech Stack:** Python 3.12 · uv · FastAPI · pytest · ruff / Next.js 16 · TypeScript · `node --test` / superpowers · 페르소나 QA 에이전트 5

**Spec:** `docs/superpowers/specs/2026-09-07-rpg-autonomous-party-design.md` (이하 "설계 §n")

## Global Constraints

- `backend/core/` 는 `adapters`·`api`·`eval`·`content` 와 `fastapi`·`google`·`langchain*`·`anthropic`·`pydantic`·`httpx`·`yaml` 을 import 하지 않는다 (설계 §3.3).
- 성별(`gender`)은 `core/rules`·`core/battle`·`core/judgment` 에서 읽히지 않는다. 행운(`luck`)은 `core/judgment` 에서 읽히지 않는다. 프롬프트에 MBTI 문자열이 없다 (설계 §3.3·§4.5).
- 난수는 전부 `Dice` 포트를 통한다. `random` 직접 호출 금지. 같은 시드 = 같은 트레이스.
- 밸런스 수치는 `core/rules/constants.py` 단일 출처 (설계 §13).
- `Stats` 에 감소 경로가 없다 (설계 §7.3).
- 테스트 함수 이름 한국어, 커밋 한국어 평서형, 주석은 "왜" + 기획서/설계 조항 인용.
- 파이썬 명령은 `backend/` 에서 `uv run …`. 프론트는 `frontend/` 에서 `npm …`.
- 마일스톤 끝: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` 초록 → `/qa-personas` 라운드 → 발견 처리 → 커밋.

---

## 파일 구조

```
backend/
  core/
    __init__.py
    types.py            Body · Stats · Disposition · LifeContext · Character · Equipment · UnitState · Faction · Environment · Plan · Action · RunConfig · MissionSpec
    ports.py            Dice · DecisionModel · TraceSink · RunStore · Role · JsonSchema
    rules/
      constants.py      모든 수치
      dice.py           SeededDice(표준 random.Random 을 감싼 Dice 구현) · FixedDice(테스트)
      body.py           roll_body(dice) -> Body
      stats.py          allocate(base, points) 검증 · derived(hp_max, stamina_max)
      disposition.py    roll_disposition(dice) · mbti_label(d) · describe(d) (수치 → 한국어 서술)
      equipment.py      efficiency(body, stats, equipment) -> Modifiers (효율 스펙트럼)
      combat.py         hit_chance · crit_chance · damage · flee_chance — 순수 함수, Modifiers 입력
    battle/
      state.py          Battle · UnitState 생성 · 승리 조건 · 행동 가능 목록
      order.py          turn_order(battle) — AGI + 속도 보정, 동률 주사위
      resolve.py        resolve(battle, actor, action, dice) -> (Battle, ResolutionRecord)
      environment.py    환경 수정자 적용 도우미
    judgment/
      visibility.py     wis_tier(wis, env) · visible_context(battle, actor) -> (visible, masked)
      odds.py           faction_power · odds(battle, faction)
      compliance.py     deviation_pressure · disposition_adjust · deviation_probability · judge(...)
      replan.py         replan_triggers(battle, last_turn_events) -> list[Trigger]
      training.py       (B) train_compliance_probability · execution_roll_mode
    agents/
      schemas.py        ORCHESTRATOR_SCHEMA · CHARACTER_SCHEMA · BOSS_SCHEMA · NARRATION_SCHEMA
      prompts.py        build_orchestrator_prompt · build_character_prompt · build_boss_prompt (성별은 narration 에서만)
      narration.py      캐릭터 표기(이름·호칭·말투) — gender 를 읽는 유일한 core 파일
      orchestrator.py   plan(battle, model, ...) -> Plan · decide_abandon
      character.py      act(battle, actor, plan, model, dice, sink) -> Action
      boss.py           boss_policy(battle, history, adaptation_on, model?) -> Action · adapt(...)
    trace/
      schema.py         TraceEvent(run_id, seq, ts, mission, turn, kind, actor, payload) · KINDS
      sink.py           ListSink · (JSONL 은 adapters)
    intermission/
      training.py       (B) run_training_turn
      life_event.py     (B) roll_life_event · apply_param_diff
      growth.py         (B) grant_points
    runner.py           run(config, model, dice_factory, sink) · run_stream(...) 제너레이터
  adapters/
    llm/fake.py         FakeModel — 휴리스틱 정책
    llm/replay.py       ReplayModel
    llm/gemini.py       GeminiModel (google-genai, Vertex ADC)
    llm/anthropic.py    AnthropicModel
    llm/select.py       from_env() -> DecisionModel
    harness/validate.py validate(data, schema) -> list[str]
    harness/harness.py  Harness(model, fallback, max_calls) — 검증·재시도·폴백·호출 계수
    store/jsonl.py      JsonlRunStore(dir)
  content/
    roster.py           PRESET_ROSTER (5명, 설계 §2.2)
    classes.py          CLASSES · WEAPONS · SKILLS (설계 §2.3)
    monsters.py         GHOUL_PACK · VARGAS (설계 §2.4)
    environments.py     SWAMP · MINE
    missions.py         MISSION_A · MISSIONS_B
    events.py           LIFE_EVENT_CATEGORIES (설계 §2.5)
  api/
    main.py             build_app(...)
    schemas.py          pydantic 요청/응답
    security.py         공유 시크릿 (비어 있으면 통과)
  eval/
    run.py              CLI: --experiment e1|e2|e3 --seeds N --out
    e1.py · e2.py · e3.py
    metrics.py          트레이스 → 지표 (순수 함수)
  tests/                아래 각 Task 참조
frontend/
  app/_ds/parchment.css
  app/layout.tsx · app/page.tsx (진입)
  app/roster/page.tsx · RosterClient.tsx
  app/battle/[run]/page.tsx · BattleClient.tsx
  app/result/[run]/page.tsx
  app/experiments/page.tsx
  app/api/{preset,runs,runs/[id],runs/[id]/stream,experiments/e1}/route.ts
  components/{RosterCard,PointAllocator,NarrativeStream,Inspector,Dashboard,OddsChart}.tsx
  lib/trace.ts · lib/narrate.ts · lib/allocation.ts · lib/backend.ts (+ *.test.ts)
docs/trace-samples/one-run.jsonl   파이썬이 생성, 프론트 테스트가 읽는다
```

---

## 마일스톤 1 — 규칙 엔진 기초 (설계 §4)

### Task 1.1: 타입 · 포트 · 상수 · 경계 테스트

**Files:** Create `core/types.py`, `core/ports.py`, `core/rules/constants.py`, `tests/test_boundaries.py`, `tests/test_types.py`

**Produces:**
```python
@dataclass(frozen=True) class Body: height_cm:int; build:Literal["slim","normal","sturdy"]; weight_kg:int
  @property weight_class -> int  # slim 1 / normal 2 / sturdy 3
@dataclass(frozen=True) class Stats: str_:int; agi:int; con:int; int_:int; wis:int; luck:int   # 1..20
  def with_added(self, **delta) -> Stats   # 음수 delta 는 ValueError — 감소 경로 없음
@dataclass(frozen=True) class Disposition: risk:int; cooperation:int; planning:int; sacrifice:int  # -100..100
@dataclass(frozen=True) class LifeContext: dependents:int; note:str
@dataclass(frozen=True) class Character: id:str; name:str; gender:Literal["female","male"]; body:Body; stats:Stats; disposition:Disposition; char_class:str; life:LifeContext; backstory:str; fatigue:int=0
@dataclass(frozen=True) class Equipment: name:str; weight_class:int; min_height:int; min_str:int; base_damage:int; kind:Literal["physical","magic"]; armor:int
@dataclass(frozen=True) class Environment: name:str; description:str; speed_penalty_by_weight:dict[int,int]; stamina_multiplier:float; damage_modifiers:dict[str,float]; range_penalty:int; darkness:bool
class Role = Literal["orchestrator","character","boss","narrator"]
class Dice(Protocol): roll(sides)->int; uniform()->float
class DecisionModel(Protocol): decide(role, prompt:str, schema:dict)->dict
class TraceSink(Protocol): emit(event)->None
class RunStore(Protocol): save(run)->None; load(run_id)->RunRecord|None; list_recent(limit)->list
```
constants: `STAT_MIN=1 STAT_MAX=20 STAT_BASE=8 FREE_POINTS=18 HP_BASE=40 HP_PER_CON=6 STAMINA_BASE=20 STAMINA_PER_CON=2 HIT_BASE=60 HIT_PER_AGI_DIFF=2 CRIT_BASE=5 LUCK_ROLL_BONUS=0.5 DEFEND_MULT=0.5 TURN_LIMIT=30 ODDS_MIN=0.05 ODDS_MAX=0.95 RETREAT_THRESHOLD_DEFAULT=0.30 RETREAT_THRESHOLD_RANGE=(0.15,0.45) MAX_CALLS=300 GROWTH_WIN=10 GROWTH_LOSE=6 MISMATCH_HIT_PENALTY=10 MISMATCH_SPEED_PENALTY=1 STAMINA_COST={...} WIS_TIERS=((1,7,0),(8,12,1),(13,16,2),(17,20,3))` 등.

- [ ] test_boundaries (secu-agent 이식, 금지 목록 = 설계 §3.3) + `test_gender_isolation`·`test_luck_isolation` (AST: `.gender`/`.luck` 속성 접근 파일 집합 검사)
- [ ] test_types: `Stats.with_added(str_=-1)` 가 ValueError, `Stats(21,…)` ValueError, `Body.weight_class`
- [ ] 구현 · `uv run pytest -q` · 커밋

### Task 1.2: 주사위 · 신체 · 성향 · MBTI

**Files:** Create `core/rules/dice.py`, `core/rules/body.py`, `core/rules/disposition.py`, `tests/test_dice.py`, `tests/test_body.py`, `tests/test_disposition.py`

**Produces:** `SeededDice(seed:int)`, `FixedDice(rolls:list[int], uniforms:list[float]=())`, `roll_body(dice)->Body`, `roll_disposition(dice)->Disposition`, `mbti_label(d)->str`, `describe(d)->dict[str,str]` (축별 한국어 서술, MBTI 문자 없음).

- [ ] 테스트: 같은 시드 두 SeededDice 가 같은 수열 / `roll_body(FixedDice([50,6,5]))` = 200cm·sturdy·몸무게 식 그대로 / 키 범위 151..200 (시드 200개) / `mbti_label(Disposition(10,50,30,-5))=="ENTJ"` … / describe 출력에 `[EI][SN][TF][JP]` 4글자 없음
- [ ] 구현 · 커밋

### Task 1.3: 능력치 분배 · 파생치 · 효율 스펙트럼

**Files:** Create `core/rules/stats.py`, `core/rules/equipment.py`, `tests/test_stats.py`, `tests/test_equipment.py`

**Produces:** `allocate(base:Stats, points:dict[str,int]) -> Stats` (총량 ≤ FREE_POINTS, 음수·상한 검증, ValueError 메시지 한국어), `hp_max(stats)`, `stamina_max(stats)`, `@dataclass Modifiers: hit:int; speed:int; stamina_mult:float; notes:tuple[tuple[str,float],...]`, `efficiency(body, stats, equipment) -> Modifiers` (설계 §4.3 식).

- [ ] 테스트: 마른(1)+판금(3) → hit -20, speed -2, notes 에 ("무게 미달", -20) / STR 6 vs 요구 11 → stamina_mult 1.5 / 적합하면 전부 0 · 1.0 / allocate 19점 → ValueError / 한 능력치 8+12=20 허용
- [ ] 구현 · 커밋

### Task 1.4: 콘텐츠 — 로스터 · 클래스 · 무기 · 몬스터 · 환경

**Files:** Create `content/roster.py`, `content/classes.py`, `content/monsters.py`, `content/environments.py`, `tests/test_content.py`

**Produces:** `PRESET_ROSTER: tuple[Character,...]` (설계 §2.2 값 그대로), `CLASSES: dict[str, ClassDef(primary:tuple[str,...], ideal_build, ideal_min_height, weapons:tuple[str,...], skills:tuple[str,...])]`, `WEAPONS: dict[str,Equipment]`, `ARMORS`, `SKILLS: dict[str, SkillDef(name, cost, kind, base, target:"enemy|ally|self|all_enemies", effect)]`, `choose_build(character) -> Build(weapon, armor, skills)` — **AI 세부 층의 코드 휴리스틱** (키·힘·체형 보고 무기 고름, 설계 §2.3 표), `GHOUL_PACK`, `VARGAS` (`EnemyDef(units, policy, summon_every)`), `SWAMP`, `MINE`.

- [ ] 테스트: 프리셋 5명 id 유일·능력치 전부 8·성향이 설계 표와 같음 / `choose_build(가렛)` = 방패+검, `choose_build(키 165 STR 16 전사)` = 워해머 / 5클래스 전부 스킬 2개 / 환경 수치가 설계 §2.4 와 같음
- [ ] 구현 · 커밋

---

## 마일스톤 2 — 진영 대칭 전투 엔진 (설계 §5)

### Task 2.1: 전투 상태 · 유닛 생성 · 승리 조건

**Files:** Create `core/battle/state.py`, `tests/test_battle_state.py`

**Produces:**
```python
@dataclass(frozen=True) class UnitState: id; name; faction; stats; body; build; hp; hp_max; stamina; stamina_max; position:"front"|"back"; statuses:tuple[Status,...]; alive:bool; fled:bool; is_boss:bool; char_class
@dataclass class Battle: seed; environment; turn; factions:(str,str); units:dict[str,UnitState]; plans:dict[str,Plan|None]; history:list[TurnRecord]; adaptation_on:bool; boss_adaptations:list
unit_from_character(c, faction, position) -> UnitState
unit_from_enemy(e, faction) -> UnitState
available_actions(battle, unit_id) -> list[Action]     # 스태미나 0 → [WAIT]
outcome(battle) -> "win"|"lose"|"draw"|None            # A진영 기준. fled 는 alive 지만 전투 밖
living(battle, faction) -> list[UnitState]
```
- [ ] 테스트: 스태미나 0 이면 WAIT 만 / 전원 fled+dead → lose / 30턴 → draw / 적 전멸 → win
- [ ] 구현 · 커밋

### Task 2.2: 판정 함수 · 행동 순서 · 행동 해석

**Files:** Create `core/rules/combat.py`, `core/battle/order.py`, `core/battle/resolve.py`, `tests/test_combat.py`, `tests/test_resolve.py`

**Produces:** `hit_chance(attacker, defender, mods, env) -> (needed:int, breakdown:list[(str,int)])`, `crit_chance`, `damage(attacker, defender, skill|None, mods, env, crit) -> (int, breakdown)`, `flee_chance(unit, enemies) -> int`, `turn_order(battle, dice) -> list[str]`, `resolve(battle, actor_id, action, dice) -> ResolutionRecord` (battle 을 제자리 갱신; 레코드에 `hit_roll, needed, hit, crit, damage, stamina_cost, modifiers:list[(name,value)]` — 설계 §8 `resolution`).

- [ ] 테스트: FixedDice 로 명중/빗나감/치명 각각 / DEFEND 후 피해 절반 / 늪지에서 무게 3 유닛 speed -2 가 순서에 반영 / FLEE 성공 시 fled / 스킬 스태미나 부족 시 ValueError / 치유 스킬은 hp_max 넘지 않음 / 행운 20 vs 1 의 needed 차이가 정확히 9~10 (LUCK_ROLL_BONUS)
- [ ] 구현 · 커밋

---

## 마일스톤 3 — 2층 판단 · 트레이스 · Fake 모델 (설계 §4.6·§6·§8)

### Task 3.1: 트레이스 스키마 · 싱크

**Files:** Create `core/trace/schema.py`, `core/trace/sink.py`, `tests/test_trace.py`

**Produces:** `KINDS: frozenset[str]` (설계 §8 표 전체), `TraceEvent(run_id, seq, ts, mission, turn, kind, actor, payload)`, `to_json(event)->str`, `from_json(s)->TraceEvent`, `ListSink`, `Tracer(run_id, sink)` — `emit(kind, payload, actor=None)` 이 seq 를 매기고 mission/turn 을 들고 있음. ts 는 `Tracer(clock=…)` 주입(결정론 테스트에서 고정).

- [ ] 테스트: 모르는 kind → ValueError / 왕복 직렬화 / seq 단조 증가
- [ ] 구현 · 커밋

### Task 3.2: 지혜 마스킹 · 승산 · 순응 · 재계획 트리거

**Files:** Create `core/judgment/visibility.py`, `odds.py`, `compliance.py`, `replan.py`, tests 4개

**Produces:** `wis_tier(wis, env)->int`, `visible_context(battle, actor_id, plan)->(visible:dict, masked:list[str])` (필드 이름: `self`, `enemies_basic`, `allies`, `enemy_pattern`, `plan_intent`, `odds`), `odds(battle, faction)->(float, breakdown)`, `deviation_probability(unit, battle, allies_lost_ratio)->(p, breakdown)` (설계 §6.4 식, luck 미참조), `judge_compliance(unit, battle, dice)->ComplianceRecord(pressure, adjust, probability, roll, verdict)`, `replan_triggers(battle, turn_events, plan)->list[Trigger]`.

- [ ] 테스트: WIS 7/10/15/18 의 masked 집합이 설계 §4.6 표와 같음, 어둠에서 한 단계 내려감 / odds 0.05..0.95 클램프, 전력 0 진영 / HP 낮을수록 p 증가(단조), sacrifice 높을수록 감소 / 트리거: deviate 1건 → ["deviation"], odds 0.25 < 0.30 → ["odds_collapse"], 연속 재진입은 0.1 단위로만
- [ ] 구현 · 커밋

### Task 3.3: 스키마 · 프롬프트 · 서사 표기

**Files:** Create `core/agents/schemas.py`, `core/agents/prompts.py`, `core/agents/narration.py`, `tests/test_prompts.py`

**Produces:** 스키마 dict 3개(설계 §6.1·§6.4 + boss `{"target":…, "action":…, "adapt": enum|null}`), `build_orchestrator_prompt(battle, faction, odds, reason, env)->str`, `build_character_prompt(unit, visible, masked, directive, actions, life)->str` (성향은 `describe()` 서술 + 수치), `build_boss_prompt(...)`, `display_name(character)`, `honorific(character)` — gender 를 읽는 유일한 core 파일.

- [ ] 테스트: 캐릭터 프롬프트에 MBTI 패턴 없음 / 카일 프롬프트에 "딸" 이 있음 / masked 필드 이름이 프롬프트 본문에 값으로 등장하지 않음 / 감독 프롬프트에 환경 수치 포함
- [ ] 구현 · 커밋

### Task 3.4: 하네스 검증기 · Fake 모델

**Files:** Create `adapters/harness/validate.py`, `adapters/harness/harness.py`, `adapters/llm/fake.py`, `tests/test_harness.py`, `tests/test_fake_model.py`

**Produces:** `validate(data, schema)->list[str]` (type·enum·required·min/max·properties 부분집합), `Harness(model, fallback:DecisionModel, max_calls:int, sink?)` — `decide()` 가 검증 실패 시 오류를 프롬프트에 덧붙여 2회 재시도 후 fallback, 결과 dict 에 `_meta={"model":..., "fallback":bool, "attempts":int, "latency_ms":..}` 붙임; `calls_used` 속성. `FakeModel` — 프롬프트 안의 `<<CONTEXT_JSON>>…<<END>>` 블록을 파싱해 규칙으로 답한다: 감독 = 힐러 없으면 rush, 승산<임계면 retreat, 무게 3 은 front, AGI 최고 back; 캐릭터 = 순응이면 directive 의 focus 공격 / HP<30% 이고 힐러 있으면 DEFEND / 이탈이면 FLEE; 보스 = 가장 HP 낮은 전열, 적응 규칙에 따라 target 변경.

- [ ] 테스트: 깨진 dict 2회 후 통과 → attempts=3 / 3회 실패 → fallback=true, fallback 모델 호출 / max_calls 초과 → 모델 안 부르고 fallback / Fake 결정론 / Fake 가 스키마를 항상 통과
- [ ] 구현 · 커밋

### Task 3.5: 오케스트레이터 · 캐릭터 에이전트 · 보스 정책

**Files:** Create `core/agents/orchestrator.py`, `core/agents/character.py`, `core/agents/boss.py`, `tests/test_orchestrator.py`, `tests/test_character_agent.py`, `tests/test_boss.py`

**Produces:** `make_plan(battle, faction, model, tracer, reason)->Plan` (플랜 이벤트 emit, worth_fighting False → strategy retreat), `character_act(battle, unit_id, plan|None, model, dice, tracer)->Action` (context → compliance → decision 이벤트 3개 emit, 이탈 시 프롬프트에 "방침을 따르지 않기로 했다"), `boss_act(battle, unit_id, model|None, dice, tracer)->Action` + `detect_adaptation(history)->Adaptation|None` (설계 §5.6 4규칙, `boss_adapt` emit).

- [ ] 테스트: 순응 판정이 deviate 면 모델이 follows_plan=true 를 줘도 기록은 deviate (모델이 뒤집지 못함) / 같은 아군 3턴 공격 → focus 적응 / adaptation_on=False 면 적응 없음 / OFF 모드(plan None)에서도 캐릭터가 행동함
- [ ] 구현 · 커밋

---

## 마일스톤 4 — 러너 · 한 판 완주 · 저장소 · 리플레이 (설계 §9) → **QA 라운드 1**

### Task 4.1: 전투 루프 · 미션 러너

**Files:** Create `core/runner.py`, `content/missions.py`, `tests/test_runner.py`

**Produces:** `RunConfig(seed, lineup:list[str], allocations, classes, genders, orchestrator_on, adaptation_on, missions:list[MissionSpec], intermission:bool, model_name)`, `MissionSpec(no, name, enemy, environment, lineup_size:(min,max), adaptation_on)`, `play_mission(mission, party:list[Character], model, dice, tracer)->MissionResult(outcome, turns, survivors, calls_used)`, `run(config, model_factory, tracer)->RunRecord`, `run_stream(config, model_factory, sink)->Iterator[TraceEvent]`, `MISSION_A`(바르가스·폐광·출전 3).

- [ ] 테스트: Fake 로 A 한 판이 30턴 안에 끝남 / 같은 시드 2회 → ts 제외 이벤트 동일 / 오케스트레이터 OFF 에서 plan 이벤트 0개 / 감독이 retreat 하면 abandon 이벤트 + mission_end.outcome=="retreat" (승산이 무너지는 시드를 찾아 고정) / calls_used ≤ 300
- [ ] 구현 · 커밋

### Task 4.2: JSONL 저장소 · Replay 모델 · 샘플 생성 스크립트

**Files:** Create `adapters/store/jsonl.py`, `adapters/llm/replay.py`, `adapters/llm/select.py`, `scripts/make_trace_sample.py`, `docs/trace-samples/one-run.jsonl`, `tests/test_store.py`, `tests/test_replay.py`

- [ ] 테스트: save→load 왕복 / list_recent 정렬 / Replay 가 녹화된 decision 을 순서대로 돌려주고 모델 호출 0 / 녹화가 끝나면 Fake 폴백
- [ ] `uv run python scripts/make_trace_sample.py` → `docs/trace-samples/one-run.jsonl` 커밋
- [ ] **QA 라운드 1** (`/qa-personas`, 범위: 마일스톤 1~4) → `docs/qa/2026-09-07-m4-one-run.md` → 수정 → 커밋

---

## 마일스톤 5 — API (설계 §11.1)

### Task 5.1: FastAPI 앱 · SSE

**Files:** Create `api/main.py`, `api/schemas.py`, `api/security.py`, `tests/test_api.py`

- [ ] 엔드포인트 7개(설계 §11.1). `/runs` 는 백그라운드 스레드로 러너를 돌리고 이벤트를 큐에 넣는다; `/runs/{id}/stream` 이 큐를 SSE 로 흘리고, 끝나면 `run_end` 후 닫는다. 완료 런은 RunStore 에 저장.
- [ ] 테스트(httpx): preset 5명 / 출전 2명 → 422 / 포인트 19 → 422 / 정상 생성 → stream 이 run_start 로 시작해 run_end 로 끝남 / 시크릿 설정 시 헤더 없으면 401, 미설정 시 통과
- [ ] 커밋

---

## 마일스톤 6 — 프론트 2패널 (설계 §11.2) → **QA 라운드 2**

### Task 6.1: 디자인 토큰 · 레이아웃 · 진입 화면
- [ ] `app/_ds/parchment.css` (secu-agent industry.css 토큰 구조, 양피지·잉크, `prefers-color-scheme` 대응), `app/layout.tsx`, `app/page.tsx` (한 문장 + 3장면 카드 + "한 판 돌리기" → /roster). 백엔드 다운 시 안내 카드.
- [ ] `lib/backend.ts` (BFF 공용 fetch, 시크릿 헤더), `lib/trace.ts` (kind 유니온·타입), `lib/trace.test.ts` 가 `docs/trace-samples/one-run.jsonl` 을 읽어 모든 줄이 알려진 kind 인지 검사
- [ ] `package.json` scripts.test = `node --test lib/*.test.ts`, 커밋

### Task 6.2: 로스터 화면
- [ ] `lib/allocation.ts`(순수: 총량·상한 검증, 추천 배분) + 테스트 / `RosterCard`(신체·성향 서술·MBTI 표기·클래스/성별 셀렉트·서사) / `PointAllocator` / 출전 3명 선택 / 감독·적응 토글 / POST → `/battle/[run]`
- [ ] 커밋

### Task 6.3: 전투 뷰어 — 서사 스트림 + 인스펙터
- [ ] `lib/narrate.ts`(모든 kind → 한국어 문장) + 테스트(샘플 파일의 모든 이벤트가 빈 문자열이 아님) / `NarrativeStream`(EventSource 구독, 클릭 → 선택) / `Inspector`(kind 별 뷰: compliance 트리, resolution modifiers 표, context 본 것/못 본 것, plan 전문, boss_adapt 증거, abandon) / `app/battle/[run]` 2패널 그리드, 390px 에서 세로 스택
- [ ] `app/result/[run]` 요약 + 다시 / 커밋
- [ ] **QA 라운드 2** (범위: 마일스톤 5~6, `qa-voter`·`qa-troll` 중심) → `docs/qa/…-m6-viewer.md` → 수정 → 커밋

---

## 마일스톤 7 — 평가 E1 (설계 §10.1) → **QA 라운드 3**

### Task 7.1: 지표 · E1 러너 · CLI · 차트 페이지
- [ ] `eval/metrics.py`(트레이스 → win/turns/retreat/survival, 순수) + 테스트 / `eval/e1.py`(조합 4 × ON/OFF × 시드 N) / `eval/run.py` CLI / `tests/test_eval_smoke.py`(시드 2, 결정론, 범위)
- [ ] `uv run python -m eval.run --experiment e1 --seeds 30` 실행, `eval/out/e1.json` 은 gitignore, 결과 표를 README 에 붙임 / API `/experiments/e1` / `app/experiments` SVG 막대
- [ ] **QA 라운드 3** (`qa-evaluator`·`qa-judge` 중심: ON 이 나쁜 조합에서 실제로 나은가) → 수정 → 커밋

---

## 마일스톤 8 — B단계: 인터미션 · 2판 · 대시보드 · E2/E3 (설계 §7·§10.2) → **QA 라운드 4**

### Task 8.1: 육성 턴 · 생애 이벤트 · 성장 포인트
- [ ] `core/judgment/training.py` + `core/intermission/*` + `content/events.py` + 테스트(순응 확률 단조성 · advantage 2회 굴림 · refuse 시 narration 존재 · param_diff before/after · Stats 감소 없음)
- [ ] 러너: `missions=[GHOUL, VARGAS]`, 사이에 `intermission()`; `MISSIONS_B`; 이벤트 kind 7종 emit / 테스트: B 완주 결정론 · 인터미션 이벤트 순서
- [ ] API: `/runs` 에 `missions: 1|2`, `POST /runs/{id}/directives` (육성 지시 + 성장 포인트 분배 — 스트림이 `intermission_start` 에서 멈추고 입력을 기다린다; 60초 무응답 시 기본값 `train` + 추천 배분) / 테스트
- [ ] 커밋

### Task 8.2: 대시보드 · 인터미션 화면 · 조언
- [ ] `Dashboard`(HP/스태미나 바 · `OddsChart` SVG 승산 곡선 · 성향 diff) 3번째 패널 / `app/battle/[run]` 인터미션 상태 UI(지시 4종 · 포인트 분배 · 결과 통보) / `advice` 이벤트 표시(희소 조건 §6.5)
- [ ] 커밋

### Task 8.3: E2 · E3
- [ ] `eval/e2.py`(적응 ON/OFF), `eval/e3.py`(성향 -80/0/+80 × 축) + 스모크 / `/experiments` 에 차트 추가
- [ ] **QA 라운드 4** (다섯 전원, 범위: 전체) → 수정 → 커밋

---

## 마일스톤 9 — 실모델 어댑터 · 배포 준비 · 문서

### Task 9.1: Gemini · Anthropic 어댑터
- [ ] `adapters/llm/gemini.py`(google-genai, Vertex ADC, JSON 응답 모드, 타임아웃 60s), `adapters/llm/anthropic.py`, `select.from_env()`; `tests/test_llm_live.py` `@pytest.mark.llm` / `.env.example`(secu-agent 양식)
- [ ] `eval/e4.py` 모델 벤치마크(키 있는 모델만)
### Task 9.2: 배포 · CI · README · 조항 추적
- [ ] `backend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`(secu-agent 양식: ruff · pytest · npm test · tsc · build), `frontend/.env.example`
- [ ] `README.md`(무엇이 다른가 · 구조 · 실행 · E1 결과 표 · 인스펙터 캡처) / `docs/spec-trace.md`(`/spec-trace`)
- [ ] 최종 검증: 전체 테스트 · 한 판 수동 완주 · 커밋

---

## 자기 검토

- **스펙 커버리지**: §2 콘텐츠(1.4·4.1·8.1) · §3 아키텍처/격리(1.1) · §4 캐릭터(1.2·1.3·3.2·3.3) · §5 전투/적응(2.x·3.5) · §6 판단/재계획/포기/조언(3.2·3.5·4.1·8.2) · §7 인터미션(8.1) · §8 로그(3.1·4.2·6.1) · §9 러너(4.1) · §10 평가(7.1·8.3·9.1) · §11 API/화면(5.1·6.x·8.2) · §12 개발 방식(QA 라운드 4회) · §13 수치(1.1) · §14 테스트(각 Task). 누락 없음.
- **타입 일관성**: `Tracer.emit(kind, payload, actor)` · `Harness.decide(role, prompt, schema)` · `resolve(battle, actor_id, action, dice)` · `visible_context(battle, actor_id, plan)` 이름을 전 Task 가 공유한다.

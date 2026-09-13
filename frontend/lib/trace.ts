// 트레이스 이벤트 스키마 v1 — backend/apps/arena/domain/entities/trace_event.py 의 미러 (설계 §8).
// KINDS 가 파이썬 쪽과 같은지 lib/trace.test.ts 가 docs/trace-samples/one-run.jsonl 로 확인한다.

export const KINDS = [
  "run_start",
  "mission_start",
  "plan",
  "odds",
  "turn_start",
  "context",
  "compliance",
  "decision",
  "resolution",
  "cards",
  "boss_adapt",
  "replan_trigger",
  "abandon",
  "flee",
  "summon",
  "horn",
  "casualty",
  "boss_named",
  "recovery",
  "mission_end",
  "intermission_start",
  "directive",
  "train_compliance",
  "train_result",
  "life_event",
  "param_diff",
  "growth_points",
  "advice",
  "run_end",
] as const;

export type Kind = (typeof KINDS)[number];

export type TraceEvent = {
  run_id: string;
  seq: number;
  ts: string;
  mission: number;
  turn: number;
  kind: Kind;
  actor: string | null;
  // 종류별 payload 는 아래 타입으로 좁혀 쓴다. 전부 타이핑하지 않는다 — 인스펙터는
  // 모르는 필드도 그대로 보여주는 것이 일이다.
  payload: Record<string, unknown>;
};

export type RosterEntry = {
  id: string;
  name: string;
  class: string;
  body: { height_cm: number; build: string; weight_kg: number };
  stats: Record<string, number>;
  disposition: Record<string, number>;
  life: string;
  weapon: string;
  armor: string;
  build_rationale: string;
};

export type Strike = {
  target: string;
  hit_roll: number;
  needed: number;
  hit: boolean;
  crit: boolean;
  damage: number;
  killed: boolean;
  hit_breakdown: [string, number][];
  damage_breakdown: [string, number][];
};

export type Resolution = {
  actor: string;
  action: string;
  target: string | null;
  stamina_cost: number;
  strikes: Strike[];
  healed: number;
  flee_roll: number | null;
  flee_needed: number | null;
  flee_success: boolean | null;
  modifiers: [string, number][];
  notes: string[];
};

export type MissionResult = {
  no: number;
  outcome: "win" | "lose" | "retreat" | "draw";
  turns: number;
  survivors: string[];
  fled: string[];
  dead: string[];
  calls_used: number;
  plans: number;
  abandoned: boolean;
  // v3 — 쓰러짐 3분기(§6.0) · 결과 5등급(§7.1b) · 회수 결정(§6.8).
  injured?: string[];
  taken?: string[];
  grade?: Grade;
  recovery_paid?: string[];
  recovery_unpaid?: string[];
  // 폴백 횟수. calls_used 만 보면 예산이 바닥나 모델을 안 쓴 판이 "싸게
  // 돌았다" 로 보인다(QA 2026-09-09 V2).
  fallbacks?: number;
};

/** 결과 5등급 — 「철수」가 벌점이 아닌 것이 핵심이다(기획서 v3 §7.1b). */
export type Grade = "full_success" | "success" | "withdraw" | "failure" | "disaster";

export const GRADE_KO: Record<Grade, string> = {
  full_success: "완전 성공",
  success: "성공",
  withdraw: "철수",
  failure: "실패",
  disaster: "참사",
};

export function isKind(k: string): k is Kind {
  return (KINDS as readonly string[]).includes(k);
}

export function parseLine(line: string): TraceEvent {
  const e = JSON.parse(line) as TraceEvent;
  if (!isKind(e.kind)) throw new Error(`모르는 이벤트 종류: ${e.kind}`);
  return e;
}

/** id → 표시 이름. run_start 의 로스터, mission_start 의 적, summon 에서 모은다. */
export function buildNameMap(events: TraceEvent[]): Record<string, string> {
  const names: Record<string, string> = {};
  for (const e of events) {
    if (e.kind === "run_start") {
      for (const r of (e.payload.roster as RosterEntry[]) ?? []) names[r.id] = r.name;
    } else if (e.kind === "mission_start") {
      const enemy = e.payload.enemy as { units?: { id: string; name: string }[] } | undefined;
      for (const u of enemy?.units ?? []) names[u.id] = u.name;
    } else if (e.kind === "summon") {
      names[String(e.payload.unit)] = String(e.payload.name);
    }
  }
  return names;
}

export const OUTCOME_KO: Record<MissionResult["outcome"], string> = {
  win: "승리",
  lose: "패배",
  retreat: "후퇴",
  draw: "무승부",
};

export const STAT_KO: Record<string, string> = {
  str_: "힘",
  agi: "민첩",
  con: "체력",
  int_: "지능",
  wis: "지혜",
  luck: "행운",
};

export const AXIS_KO: Record<string, string> = {
  risk: "위험",
  cooperation: "협동",
  planning: "계획",
  sacrifice: "희생",
};

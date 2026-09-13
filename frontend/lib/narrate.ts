// 이벤트 → 서사 문장 (설계 §11.2). 순수 함수. 모델이 쓰는 문장은 decision.reason 뿐이고
// 나머지는 전부 여기서 만든다 — 그래야 Fake 모드에서도 화면이 비지 않는다.
//
// 원칙: 왼쪽(서사)에서 일어나는 모든 일이 가운데(인스펙터)에서 설명 가능해야 한다.
// 그러니 서사는 사실만 말하고, 수치는 인스펙터에 맡긴다.

import { withJosa } from "./josa.ts";
import type { MissionResult, Resolution, TraceEvent } from "./trace.ts";
import { AXIS_KO, OUTCOME_KO } from "./trace.ts";

type Names = Record<string, string>;

const ACTION_KO: Record<string, string> = {
  ATTACK: "공격한다",
  DEFEND: "방어 태세를 취한다",
  FLEE: "전장에서 빠져나가려 한다",
  WAIT: "숨을 고른다",
};

const TRIGGER_KO: Record<string, string> = {
  deviation: "단원의 이탈",
  odds_collapse: "승산 붕괴",
  adaptation: "적의 적응",
  environment: "환경 변화",
};

const ADAPT_KO: Record<string, string> = {
  repeat_attacker: "같은 자가 세 턴 연속 자신을 노린 것",
  frontline_wall: "앞줄이 계속 막고 있는 것",
  healing: "치유가 반복되는 것",
  turtle: "상대가 방어만 하는 것",
};
const COUNTER_KO: Record<string, string> = {
  focus: "그를 우선 노리기로 한다",
  breach: "앞줄의 방패부터 부순다",
  target_healer: "치유자를 먼저 노린다",
  summon_faster: "잔해를 더 자주 불러 모은다",
};

const MASKED_KO: Record<string, string> = {
  allies: "아군 상태",
  enemies_basic: "적의 위치",
  enemy_pattern: "적의 행동 패턴",
  plan_intent: "단장의 의도",
  odds: "승산",
  self: "자기 상태",
};

const STRATEGY_KO: Record<string, string> = {
  rush: "속공",
  attrition: "지구전",
  defensive: "방어전",
  retreat: "후퇴",
};

export function nameOf(id: string | null | undefined, names: Names): string {
  if (!id) return "누군가";
  return names[id] ?? id;
}

/** 자유 텍스트(모델 사유·트리거 설명·보정 메모)에 남은 id 를 이름으로 바꾼다.
 *
 * 같은 문자열이 왼쪽(서사)에선 id, 가운데(인스펙터)에선 이름으로 보이면 안 된다. */
export function withNames(text: string, names: Names): string {
  let out = text;
  for (const [id, name] of Object.entries(names)) {
    out = out.replace(new RegExp(`\\b${id}\\b`, "g"), name);
  }
  return out;
}

export function narrate(e: TraceEvent, names: Names): string {
  const p = e.payload;
  const who = nameOf(e.actor, names);
  switch (e.kind) {
    case "run_start": {
      const lineup = (p.lineup as string[]).map((id) => nameOf(id, names)).join(", ");
      return `단주가 출전 명단을 확정했다 — ${lineup}. ${p.orchestrator_on ? "단장이 지휘한다." : "단장 없이 각자 판단한다."}`;
    }
    case "mission_start": {
      const enemy = p.enemy as { name: string; description: string };
      const env = p.environment as { name: string; description: string };
      return `${env.name}. ${env.description} 상대는 ${enemy.name}. ${enemy.description}`;
    }
    case "plan": {
      const plan = p.plan as { assessment: string; strategy: string; worth_fighting: boolean; focus_target: string | null };
      const reason = String(p.reason);
      const lead = reason === "initial" ? "단장이 전장을 읽는다" : "단장이 작전을 다시 짠다";
      if (!plan.worth_fighting) return `${lead}: "${plan.assessment}" — 싸울 가치가 없다고 판단했다.`;
      const focus = plan.focus_target ? ` 목표는 ${nameOf(plan.focus_target, names)}.` : "";
      return `${lead}: "${plan.assessment}" 작전은 ${STRATEGY_KO[plan.strategy] ?? plan.strategy}.${focus}`;
    }
    case "odds": {
      const v = Math.round(Number(p.value) * 100);
      return `승산 ${v}%.`;
    }
    case "turn_start": {
      const order = (p.order as { unit: string }[]).map((o) => nameOf(o.unit, names));
      return `${e.turn}턴. 움직이는 순서: ${order.join(" → ")}.`;
    }
    case "context": {
      const masked = (p.masked as string[]) ?? [];
      const subject = withJosa(who, "는");
      if (masked.length === 0) return `${subject} 전장을 전부 본다 (지혜 ${p.wis}).`;
      const hidden = masked.map((m) => MASKED_KO[m] ?? m).join(", ");
      return `${subject} 전장의 일부만 본다 — ${withJosa(hidden, "이")} 안 보인다 (지혜 ${p.wis}).`;
    }
    case "compliance": {
      const pct = Math.round(Number(p.probability) * 100);
      if (p.verdict === "deviate") return `${who}의 마음이 방침에서 떠난다 (이탈 확률 ${pct}%).`;
      return `${withJosa(who, "는")} 방침을 따르기로 한다 (이탈 확률 ${pct}%).`;
    }
    case "decision": {
      const label = String(p.label);
      const target = p.target ? nameOf(String(p.target), names) : null;
      const reason = p.reason ? ` "${withNames(String(p.reason), names)}"` : "";
      const note = p.note ? ` (${withNames(String(p.note), names)})` : "";
      const subject = withJosa(who, "가");
      if (label.startsWith("SKILL:")) {
        const skill = label.slice(6);
        // 자기에게 거는 기술은 "적 전체" 로 읽히면 안 된다.
        const onSelf = p.target === e.actor;
        const where = onSelf ? "자신에게" : target ? `${withJosa(target, "에게")}` : "";
        return `${subject} ${where ? where + " " : ""}${withJosa(skill, "을")} 쓴다.${reason}${note}`;
      }
      if (label.startsWith("MOVE:"))
        return `${subject} ${label.endsWith("back") ? "후열로" : "전열로"} 움직인다.${reason}`;
      if (label === "ATTACK")
        return `${subject} ${withJosa(target ?? "적", "을")} ${ACTION_KO.ATTACK}.${reason}${note}`;
      return `${subject} ${ACTION_KO[label] ?? label}.${reason}`;
    }
    case "resolution": {
      const r = p as unknown as Resolution;
      return narrateResolution(r, names);
    }
    case "boss_adapt": {
      const what = ADAPT_KO[String(p.pattern)] ?? String(p.pattern);
      const counter = COUNTER_KO[String(p.counter)] ?? String(p.counter);
      const effect = p.effect as { no_change?: boolean } | undefined;
      // 아무것도 안 바뀐 적응을 같은 문장으로 세 번 내면 로그가 거짓말이 된다.
      if (effect?.no_change) return `${withJosa(who, "가")} 다시 ${what}을 확인한다 — 방침 그대로.`;
      return `${withJosa(who, "가")} ${what}을 읽었다 — ${counter}.`;
    }
    case "replan_trigger":
      return `${TRIGGER_KO[String(p.trigger)] ?? String(p.trigger)} — ${withNames(String(p.detail), names)}. 단장이 판을 다시 본다.`;
    case "abandon": {
      const v = Math.round(Number(p.odds) * 100);
      return `단장이 결정한다: "${p.rationale}" (승산 ${v}%). 전원 철수.`;
    }
    case "recovery":
      // 기획서 v3 §6.8 — 회수는 보장된 거래가 아니다. 미지불은 영구 상실이다.
      if (p.awaiting_input) {
        // 값을 물어보는 쪽 이벤트다. 결정이 아니라 질문이다(QA 2026-09-09 L).
        const ms = (p.members as string[]) ?? [];
        return `굴에 끌려간 ${ms.map((m) => names[m] ?? m).join(", ")} — 되찾을 것인가.`;
      }
      return p.paid
        ? `${withJosa(who, "를")} 되찾기로 한다. 은화 ${p.cost}.`
        : `${withJosa(who, "를")} 굴에 둔다. 되찾는 값은 은화 ${p.cost}였다.`;
    case "cards": {
      // 기획서 v3 §8.4 — 그것은 당신이 남긴 것을 먹고 자란다.
      const cs = (p.cards as { name: string }[]) ?? [];
      return `그것이 배운 것이 펼쳐진다 — ${cs.map((c) => `「${c.name}」`).join(" ")}.`;
    }
    case "boss_named":
      // 기획서 v3 §8.5 — 그것에게는 이름이 없다. 첫 끌려감이 붙인다.
      return `대원들은 그것을 「${p.after}」이라 부르기 시작했다.`;
    case "horn":
      // 기획서 v3 §8.2 — 유저의 유일한 전투 중 개입. 즉시 이탈, 보수 0.
      // 전령관이 없으면 신호가 한 턴 늦는다 — 그 한 턴이 사람을 잃는 자리다.
      return p.delayed_from
        ? `${p.delayed_from}턴에 부른 뿔피리가 이제야 닿는다 — 전령관이 없다. 대열이 물러선다: ${(p.withdrew as string[] ?? []).length}명.`
        : `후방에서 뿔피리가 울린다. 대열이 물러선다 — ${(p.withdrew as string[] ?? []).length}명 전원.`;
    case "casualty": {
      // 기획서 v3 §6.0 — HP 0 은 사망이 아니다. 전투가 끝난 뒤에 갈린다.
      const verdict = String(p.verdict);
      if (verdict === "injured") return `${withJosa(who, "가")} 실려 나왔다. 살아 있다.`;
      if (verdict === "taken") return `${withJosa(who, "가")} 굴로 끌려갔다. 아직 살아 있다.`;
      return `${withJosa(who, "가")} 돌아오지 못했다.`;
    }
    case "flee":
      return p.success
        ? `${withJosa(who, "가")} 전장을 벗어났다.`
        : `${withJosa(who, "가")} 빠져나가지 못했다.`;
    case "summon":
      return `갱도가 흔들리고 ${withJosa(String(p.name), "이")} 일어선다.`;
    case "mission_end": {
      const r = p as unknown as MissionResult;
      const outcome = OUTCOME_KO[r.outcome] ?? r.outcome;
      const dead = r.dead.length ? ` 쓰러진 자: ${r.dead.map((d) => nameOf(d, names)).join(", ")}.` : "";
      const fled = r.fled.length ? ` 빠져나온 자: ${r.fled.map((d) => nameOf(d, names)).join(", ")}.` : "";
      return `${r.turns}턴 만에 ${outcome}.${dead}${fled}`;
    }
    case "intermission_start":
      if (p.rejected) return `지시를 받아들이지 못했다 (${String(p.rejected)}). 기본 지시로 간다.`;
      if (p.awaiting_input) return "야영지. 단주의 지시를 기다린다.";
      return "전투가 끝났다. 용병단은 야영지로 돌아온다.";
    case "directive":
      return `단주가 ${who}에게 지시한다: ${String(p.label ?? p.category)}.`;
    case "train_compliance": {
      const pct = Math.round(Number(p.probability) * 100);
      return p.verdict === "refuse"
        ? `${who}는 지시를 따르지 않는다 (순응 확률 ${pct}%).`
        : `${who}는 지시를 ${p.verdict === "partial" ? "절반만 " : ""}따른다 (순응 확률 ${pct}%).`;
    }
    case "train_result":
      return String(p.narration ?? `${who}의 하루가 지났다.`);
    case "life_event":
      return String(p.narration ?? `${who}에게 일이 생겼다.`);
    case "param_diff": {
      const delta = p.delta as Record<string, number>;
      const parts = Object.entries(delta).map(
        ([k, v]) => `${AXIS_KO[k] ?? (k === "fatigue" ? "피로" : k)} ${v > 0 ? "+" : ""}${v}`,
      );
      return `${withJosa(who, "가")} 변했다 — ${String(p.cause ?? "")}: ${parts.join(", ")}.`;
    }
    case "growth_points":
      return `단주가 성장 포인트 ${p.granted}점을 받았다.`;
    case "advice":
      return `단장의 경고: "${p.message}"`;
    case "run_end": {
      const outcomes = (p.outcomes as string[]).map((o) => OUTCOME_KO[o as MissionResult["outcome"]] ?? o);
      return `계약이 끝났다. 결과: ${outcomes.join(" · ")}.`;
    }
    default:
      return `${e.kind}`;
  }
}

function narrateResolution(r: Resolution, names: Names): string {
  const who = nameOf(r.actor, names);
  const subject = withJosa(who, "가");
  if (r.action === "FLEE") return r.flee_success ? `${subject} 몸을 돌려 달아났다.` : `${who}의 발이 잡혔다.`;
  if (r.action === "DEFEND") return `${subject} 몸을 낮춘다.`;
  if (r.action === "WAIT") return `${subject} 숨을 고른다.`;
  if (r.action.startsWith("MOVE")) return `${subject} 자리를 옮긴다.`;
  if (r.healed > 0)
    return `${who}의 손길에 ${nameOf(r.target, names)}의 상처가 ${r.healed}만큼 아문다.`;
  if (r.strikes.length === 0) {
    const skill = r.action.startsWith("SKILL:") ? r.action.slice(6) : r.action;
    // 자기에게 거는 기술(방패 밀치기 등)을 광역기처럼 쓰면 거짓말이 된다.
    if (r.target === r.actor) return `${subject} ${withJosa(skill, "을")} 스스로에게 건다.`;
    return `${who}의 ${withJosa(skill, "이")} 전장에 퍼진다.`;
  }
  const parts = r.strikes.map((s) => {
    const t = nameOf(s.target, names);
    if (!s.hit) return `${withJosa(t, "에게")}는 빗나갔다`;
    const crit = s.crit ? " 급소를 찔러" : "";
    const killed = s.killed ? ` — ${withJosa(t, "이")} 쓰러진다` : "";
    return `${withJosa(t, "에게")}${crit} ${s.damage}의 피해${killed}`;
  });
  const note = r.notes.length ? ` (${withNames(r.notes[0], names)})` : "";
  return `${who}: ${parts.join(", ")}.${note}`;
}

"use client";

import { useState } from "react";
import { nameOf } from "@/lib/narrate";
import { AXIS_KO, GRADE_KO, type MissionResult, type Resolution, type RosterEntry, type TraceEvent } from "@/lib/trace";

// 쓰러짐 3분기(기획서 v3 §6.0).
const CASUALTY_KO: Record<string, string> = { injured: "부상", taken: "끌려감", dead: "사망" };

type Names = Record<string, string>;

// 판정 인스펙터(기획서 §9). 행동을 클릭하면 "왜"가 열린다.
// 종류별로 구조화해 보여주고, 모르는 종류는 JSON 그대로 — 숨기는 것이 없어야 한다.
export default function Inspector({ event, names, events }: { event: TraceEvent | null; names: Names; events: TraceEvent[] }) {
  if (!event) {
    return (
      <p className="small faint">
        왼쪽에서 한 줄을 클릭하면 그 판정의 입력·확률·주사위·사유가 여기 열린다.
        <br />
        이탈(빨간 줄)·작전(붉은 줄)·적응(노란 줄)이 볼 만하다.
      </p>
    );
  }
  const p = event.payload;
  return (
    <div className="stack" style={{ gap: 12 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="row">
          <span className="tag tag-steel">{event.kind}</span>
          {event.actor && <span className="tag">{nameOf(event.actor, names)}</span>}
          <span className="faint small mono">
            #{event.seq} · {event.mission}판 {event.turn}턴
          </span>
        </div>
      </div>
      <Body event={event} names={names} events={events} />
      <Collapsible title="원본 payload">
        <pre className="json">{JSON.stringify(p, null, 2)}</pre>
      </Collapsible>
    </div>
  );
}

function Body({ event, names, events }: { event: TraceEvent; names: Names; events: TraceEvent[] }) {
  const p = event.payload as Record<string, unknown>;
  switch (event.kind) {
    case "compliance":
      return <ComplianceView p={p} />;
    case "context":
      return <ContextView p={p} names={names} />;
    case "decision":
      return <DecisionView p={p} names={names} events={events} seq={event.seq} />;
    case "resolution":
      return <ResolutionView r={p as unknown as Resolution} names={names} />;
    case "plan":
      return <PlanView p={p} names={names} />;
    case "boss_adapt":
      return (
        <KV
          rows={[
            ["관측 패턴", String(p.pattern)],
            ["대응", String(p.counter)],
            ["실제 변화", effectLine(p.effect as Record<string, unknown> | undefined, names)],
            ["증거", <pre key="e" className="json">{JSON.stringify(withNames(p.evidence, names), null, 2)}</pre>],
          ]}
        />
      );
    case "odds":
      return <OddsView p={p} names={names} />;
    case "turn_start":
      return (
        <table className="kv">
          <tbody>
            {(p.order as { unit: string; speed: number; breakdown: [string, number][] }[]).map((o) => (
              <tr key={o.unit}>
                <th>{nameOf(o.unit, names)}</th>
                <td>
                  속도 {o.speed} = {o.breakdown.map(([k, v]) => `${k} ${fmt(v)}`).join(" ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    case "abandon":
      return <KV rows={[["승산", pct(p.odds)], ["전략", String(p.strategy)], ["평가", String(p.assessment)], ["사유", String(p.rationale)]]} />;
    case "replan_trigger":
      return <KV rows={[["트리거", String(p.trigger)], ["내용", String(p.detail)]]} />;
    case "flee":
      return <KV rows={[["주사위", `${p.roll} (≤ ${p.needed} 이면 성공)`], ["결과", p.success ? "성공" : "실패"]]} />;
    case "horn":
      // 서사에서 가장 눌러 보고 싶은 줄인데 날 JSON 이었다(QA 재검 2026-09-09).
      return (
        <KV
          rows={[
            ["닿은 턴", String(p.turn)],
            [
              "부른 턴",
              p.delayed_from ? `${p.delayed_from} → 전령관이 없어 한 턴 늦었다` : "즉시 닿았다",
            ],
            ["물러난 사람", (p.withdrew as string[] ?? []).map((s) => nameOf(s, names)).join(", ") || "없음"],
            ["도착", p.delivered === false ? "닿기 전에 판이 끝났다" : "닿았다"],
          ]}
        />
      );
    case "boss_named":
      return (
        <KV
          rows={[
            ["누구를 데려갔나", nameOf(String(p.member), names)],
            ["전", p.before ? String(p.before) : "이름이 없었다"],
            ["후", String(p.after)],
          ]}
        />
      );
    case "recovery":
      // 물음과 결정이 같은 종류로 온다 — payload 가 어느 쪽인지 말한다.
      return p.awaiting_input ? (
        <KV
          rows={[
            ["묻는 중", "굴에 끌려간 대원을 되찾을 것인가"],
            [
              "값",
              Object.entries((p.costs as Record<string, number>) ?? {})
                .map(([id, c]) => `${nameOf(id, names)} ${c}`)
                .join(" · ") || "없음",
            ],
            ["기한", `${p.timeout_s}초 — 답하지 않으면 전원 미지불`],
          ]}
        />
      ) : (
        <KV
          rows={[
            ["대원", nameOf(String(p.member), names)],
            ["값", String(p.cost)],
            ["결정", p.paid ? "값을 치렀다 (회수 출동은 다음 계약)" : "굴에 두고 왔다 — 영구 상실"],
          ]}
        />
      );
    case "casualty":
      // 이 판의 가장 무거운 판정이다. 굴림과 경계를 보여주지 않으면 그냥
      // 랜덤과 구별되지 않는다(QA 2026-09-09 J2).
      return (
        <KV
          rows={[
            ["판정", CASUALTY_KO[String(p.verdict)] ?? String(p.verdict)],
            ["구간", String(p.tier)],
            [
              "주사위",
              p.roll === undefined
                ? "기록 없음"
                : `${p.roll} / 100 → ${((p.bounds as [string, number][]) ?? [])
                    .map(([k, upper]) => `${CASUALTY_KO[k] ?? k} ≤${upper}`)
                    .join(" · ")}`,
            ],
          ]}
        />
      );
    case "mission_end": {
      const r = p as unknown as MissionResult;
      return (
        <KV
          rows={[
            ["등급", r.grade ? GRADE_KO[r.grade] : r.outcome],
            ["턴", String(r.turns)],
            ["생존", r.survivors.map((s) => nameOf(s, names)).join(", ") || "없음"],
            ["이탈", r.fled.map((s) => nameOf(s, names)).join(", ") || "없음"],
            ["부상", (r.injured ?? []).map((s) => nameOf(s, names)).join(", ") || "없음"],
            ["끌려감", (r.taken ?? []).map((s) => nameOf(s, names)).join(", ") || "없음"],
            ["사망", r.dead.map((s) => nameOf(s, names)).join(", ") || "없음"],
            [
              "회수",
              (r.taken ?? []).length === 0
                ? "해당 없음"
                : `값을 치름 ${(r.recovery_paid ?? []).map((s) => nameOf(s, names)).join(", ") || "없음"}` +
                  ` · 두고 옴 ${(r.recovery_unpaid ?? []).map((s) => nameOf(s, names)).join(", ") || "없음"}`,
            ],
            // 폴백이 섞인 판은 "모델이 판단했다" 가 아니다(QA 2026-09-09 V2).
            ["모델 호출", `${r.calls_used}${r.fallbacks ? ` (폴백 ${r.fallbacks}회)` : ""}`],
            ["작전 수립", String(r.plans)],
            ["포기 여부", r.abandoned ? "단장이 포기를 결정" : "끝까지"],
          ]}
        />
      );
    }
    case "run_start":
      return <RosterView roster={p.roster as RosterEntry[]} p={p} />;
    default:
      return <pre className="json">{JSON.stringify(p, null, 2)}</pre>;
  }
}

function ComplianceView({ p }: { p: Record<string, unknown> }) {
  const pb = p.pressure_breakdown as Record<string, number>;
  const ab = p.adjust_breakdown as Record<string, number>;
  const deviate = p.verdict === "deviate";
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row">
        <span className={`tag ${deviate ? "tag-accent" : "tag-ok"}`}>{deviate ? "방침 이탈" : "순응"}</span>
        <span className="small">
          이탈 확률 <b>{pct(p.probability)}</b> · 주사위 {Number(p.roll).toFixed(3)} {deviate ? "< 확률 → 이탈" : "≥ 확률 → 순응"}
        </span>
      </div>
      <table className="kv">
        <tbody>
          <tr>
            <th>이탈 압력 {fmt(p.pressure)}</th>
            <td>
              {pb && Object.entries(pb).map(([k, v]) => (
                <div key={k}>
                  {({ hp: "HP 손실", allies_lost: "아군 이탈·사망", life: "부양가족" } as Record<string, string>)[k] ?? k}: {fmt(v)}
                </div>
              ))}
            </td>
          </tr>
          <tr>
            <th>성향 보정 {fmt(p.disposition_adjust)}</th>
            <td>
              {ab && Object.keys(ab).length === 0 && <span className="faint">성향 없음(고정 정책)</span>}
              {ab && Object.entries(ab).map(([k, v]) => (
                <div key={k}>
                  {AXIS_KO[k] ?? k}: {fmt(v)}
                </div>
              ))}
            </td>
          </tr>
          <tr>
            <th>식</th>
            <td className="mono small">P = clamp(σ(4 × (압력 + 보정) − 2.5), 0.02, 0.95)</td>
          </tr>
        </tbody>
      </table>
      <p className="small faint">모델은 이 판정을 뒤집을 수 없다. 코드가 확률을 계산하고 시드 주사위가 정한다. 행운은 여기 없다.</p>
    </div>
  );
}

function ContextView({ p, names }: { p: Record<string, unknown>; names: Names }) {
  const masked = (p.masked as string[]) ?? [];
  const labels: Record<string, string> = {
    self: "자기 상태",
    enemies_basic: "적의 이름·위치",
    allies: "아군 HP·상태",
    enemy_pattern: "적의 최근 행동 패턴",
    plan_intent: "단장 방침의 의도",
    odds: "현재 승산",
  };
  const visible = p.visible as Record<string, unknown>;
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row">
        <span className="tag tag-steel">지혜 {String(p.wis)} → {String(p.wis_tier)}단계</span>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <div className="stack" style={{ gap: 4 }}>
          <div className="card-kicker">본 것</div>
          {Object.keys(visible).map((k) => (
            <span key={k} className="tag tag-ok" style={{ alignSelf: "flex-start" }}>
              {labels[k] ?? k}
            </span>
          ))}
        </div>
        <div className="stack" style={{ gap: 4 }}>
          <div className="card-kicker">못 본 것</div>
          {masked.length === 0 && <span className="faint small">없음 — 전부 본다</span>}
          {masked.map((k) => (
            <span key={k} className="tag tag-outline" style={{ alignSelf: "flex-start", textDecoration: "line-through" }}>
              {labels[k] ?? k}
            </span>
          ))}
        </div>
      </div>
      <pre className="json">{JSON.stringify(withNames(visible, names), null, 2)}</pre>
    </div>
  );
}

function DecisionView({ p, names, events, seq }: { p: Record<string, unknown>; names: Names; events: TraceEvent[]; seq: number }) {
  const compliance = [...events].reverse().find((e) => e.kind === "compliance" && e.seq < seq && e.actor === (events.find((x) => x.seq === seq)?.actor ?? ""));
  return (
    <div className="stack" style={{ gap: 8 }}>
      <KV
        rows={[
          ["행동", `${String(p.label)}${p.target ? ` → ${nameOf(String(p.target), names)}` : ""}`],
          ["방침 준수", p.follows_plan ? "따랐다" : String(p.verdict) === "deviate" ? "이탈" : String(p.verdict) === "policy" ? "고정 정책" : "방침 없음"],
          ["사유", `"${String(p.reason ?? "")}"`],
          ...(p.note ? [["보정", String(p.note)] as [string, string]] : []),
          ["모델", modelLine(p)],
        ]}
      />
      {compliance && (
        <p className="small faint">직전 순응 판정 #{compliance.seq}: 이탈 확률 {pct(compliance.payload.probability)} → {String(compliance.payload.verdict)}</p>
      )}
      {typeof p.prompt === "string" && (
        <Collapsible title="모델에 들어간 프롬프트 (입력 컨텍스트)">
          <pre className="json">{p.prompt}</pre>
        </Collapsible>
      )}
      {p.raw != null && (
        <Collapsible title="모델 원 응답">
          <pre className="json">{JSON.stringify(p.raw, null, 2)}</pre>
        </Collapsible>
      )}
    </div>
  );
}

function ResolutionView({ r, names }: { r: Resolution; names: Names }) {
  return (
    <div className="stack" style={{ gap: 8 }}>
      <KV rows={[["행동", `${r.action}${r.target ? ` → ${nameOf(r.target, names)}` : ""}`], ["스태미나 소모", String(r.stamina_cost)]]} />
      {r.strikes.map((s, i) => (
        <div key={i} className="stack" style={{ gap: 4, padding: 8, background: "var(--color-surface-2)", borderRadius: 6 }}>
          <div className="row small">
            <b>{nameOf(s.target, names)}</b>
            <span>
              명중 굴림 {s.hit_roll} ≤ {s.needed}? → {s.hit ? "명중" : "빗나감"}
            </span>
            {s.hit && <span>{s.crit ? "치명타" : "치명 아님"} · 피해 {s.damage}</span>}
            {s.killed && <span className="tag tag-accent">쓰러짐</span>}
          </div>
          <div className="small faint">명중: {s.hit_breakdown.map(([k, v]) => `${k} ${fmt(v)}`).join(" · ")}</div>
          {s.hit && <div className="small faint">피해: {s.damage_breakdown.map(([k, v]) => `${k} ${fmt(v)}`).join(" · ")}</div>}
        </div>
      ))}
      {r.healed > 0 && <p className="small">치유 {r.healed}</p>}
      {r.flee_roll != null && (
        <p className="small">
          도망 굴림 {r.flee_roll} ≤ {r.flee_needed}? → {r.flee_success ? "성공" : "실패"}
        </p>
      )}
      {r.modifiers.length > 0 && (
        <table className="kv">
          <tbody>
            {r.modifiers.map(([k, v], i) => (
              <tr key={i}>
                <th>{k}</th>
                <td>{fmt(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {r.notes.map((n) => (
        <p key={n} className="small faint">
          {withNamesText(n, names)}
        </p>
      ))}
    </div>
  );
}

function PlanView({ p, names }: { p: Record<string, unknown>; names: Names }) {
  const plan = p.plan as Record<string, unknown>;
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row">
        <span className={`tag ${plan.worth_fighting ? "tag-ok" : "tag-accent"}`}>{plan.worth_fighting ? "싸울 가치 있음" : "싸울 가치 없음 → 후퇴"}</span>
        <span className="tag tag-steel">{String(plan.strategy)}</span>
        <span className="small">승산 {pct(p.odds)} · 후퇴 임계 {pct(plan.retreat_threshold)}</span>
      </div>
      <KV
        rows={[
          ["사유", String(p.reason)],
          ["평가", String(plan.assessment)],
          ["근거", String(plan.rationale)],
          ["집중 목표", plan.focus_target ? nameOf(String(plan.focus_target), names) : "없음"],
          ["편성", Object.entries((plan.formation as Record<string, string>) ?? {}).map(([k, v]) => `${nameOf(k, names)} ${v === "front" ? "전열" : "후열"}`).join(" · ")],
        ]}
      />
      <table className="kv">
        <tbody>
          {Object.entries((plan.per_unit_directive as Record<string, string>) ?? {}).map(([k, v]) => (
            <tr key={k}>
              <th>{nameOf(k, names)}</th>
              <td>{withNamesText(v, names)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {(p.notes as string[])?.length > 0 && <p className="small faint">보정: {(p.notes as string[]).join(" / ")}</p>}
      <p className="small faint">모델 {modelLine(p)}</p>
      {typeof p.prompt === "string" && (
        <Collapsible title="단장에게 들어간 프롬프트">
          <pre className="json">{p.prompt}</pre>
        </Collapsible>
      )}
    </div>
  );
}

function OddsView({ p, names }: { p: Record<string, unknown>; names: Names }) {
  type Side = {
    units?: Record<string, Record<string, number>>;
    synergy?: number;
    dps?: number;
    effective_hp?: number;
    survives_turns?: number;
  };
  const bd = p.breakdown as { mine?: Side; theirs?: Side } | undefined;
  const rows = (side: "mine" | "theirs") =>
    Object.entries(bd?.[side]?.units ?? {}).map(([id, u]) => (
      <tr key={id}>
        <th>{nameOf(id, names)}</th>
        <td className="small">
          HP {u.hp} · 기대피해 {u.expected_damage} × 스태미나 {u.stamina} × 순응 {u.compliance} ={" "}
          <b>{u.dps}</b>
        </td>
      </tr>
    ));
  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row">
        <span className="tag tag-steel">승산 {pct(p.value)}</span>
        {p.threshold != null && <span className="small">후퇴 임계 {pct(p.threshold)}</span>}
      </div>
      <table className="kv">
        <tbody>
          <tr>
            <th colSpan={2}>
              우리 — 한 턴 {bd?.mine?.dps} 피해 · 실질 HP {bd?.mine?.effective_hp}
              {bd?.mine?.synergy !== 1 && ` (치유 ×${bd?.mine?.synergy})`} → {bd?.mine?.survives_turns}턴 버팀
            </th>
          </tr>
          {rows("mine")}
          <tr>
            <th colSpan={2}>
              적 — 한 턴 {bd?.theirs?.dps} 피해 · HP {bd?.theirs?.effective_hp} →{" "}
              {bd?.theirs?.survives_turns}턴 버팀
            </th>
          </tr>
          {rows("theirs")}
        </tbody>
      </table>
      <p className="small faint mono">
        승산 = 우리가 버티는 턴 / (우리 + 적). 행운은 계산에 없다.
      </p>
    </div>
  );
}

function RosterView({ roster, p }: { roster: RosterEntry[]; p: Record<string, unknown> }) {
  return (
    <div className="stack" style={{ gap: 8 }}>
      <KV rows={[["시드", String(p.seed)], ["모델", String(p.model)], ["단장", p.orchestrator_on ? "ON" : "OFF"], ["보스 적응", p.adaptation_on ? "ON" : "OFF"]]} />
      {roster?.map((r) => (
        <div key={r.id} className="stack small" style={{ gap: 2, padding: 8, background: "var(--color-surface-2)", borderRadius: 6 }}>
          <b>
            {r.name} · {r.class}
          </b>
          <span className="faint">
            {r.body.height_cm}cm {r.body.build} {r.body.weight_kg}kg · {r.weapon} · {r.armor}
          </span>
          <span className="faint">&ldquo;{r.build_rationale}&rdquo;</span>
          <span className="mono faint">
            {Object.entries(r.stats).map(([k, v]) => `${k}${v}`).join(" ")} · {Object.entries(r.disposition).map(([k, v]) => `${AXIS_KO[k] ?? k}${v > 0 ? "+" : ""}${v}`).join(" ")}
          </span>
        </div>
      ))}
    </div>
  );
}

function KV({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <table className="kv">
      <tbody>
        {rows.map(([k, v], i) => (
          <tr key={i}>
            <th>{k}</th>
            <td>{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Collapsible({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="stack" style={{ gap: 4 }}>
      <button className="btn btn-sm btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => setOpen((o) => !o)}>
        {open ? "▾" : "▸"} {title}
      </button>
      {open && children}
    </div>
  );
}

/** 모델 한 줄. latency 는 payload.timing 에 있다 — payload.model 에서 찾으면 undefined 다. */
function modelLine(p: Record<string, unknown>): string {
  const meta = (p.model as Record<string, unknown>) ?? {};
  const timing = (p.timing as Record<string, unknown>) ?? {};
  const ms = timing.latency_ms;
  return (
    `${String(meta.model ?? "?")}${meta.fallback ? " (폴백)" : ""}` +
    ` · 시도 ${String(meta.attempts ?? 0)}` +
    (ms == null ? "" : ` · ${String(ms)}ms`)
  );
}

function pct(v: unknown): string {
  return `${Math.round(Number(v) * 100)}%`;
}
function fmt(v: unknown): string {
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return Number.isInteger(n) ? (n > 0 ? `+${n}` : `${n}`) : n.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function effectLine(effect: Record<string, unknown> | undefined, names: Names): string {
  if (!effect) return "기록 없음";
  if (effect.no_change) return "없음 — 이미 그 상태다";
  const f = String(effect.field);
  const before = effect.before == null ? "없음" : nameOf(String(effect.before), names);
  const after = effect.after == null ? "없음" : nameOf(String(effect.after), names);
  return `${f}: ${before} → ${after}`;
}

/** payload 안의 id 문자열을 표시 이름으로 바꾼다 — 인스펙터는 사람이 읽는다. */
function withNames(v: unknown, names: Names): unknown {
  if (typeof v === "string") return names[v] ?? v;
  if (Array.isArray(v)) return v.map((x) => withNames(x, names));
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v as Record<string, unknown>).map(([k, x]) => [names[k] ?? k, withNames(x, names)]));
  return v;
}
function withNamesText(s: string, names: Names): string {
  return Object.entries(names).reduce((acc, [id, name]) => acc.replace(new RegExp(`\\b${id}\\b`, "g"), name), s);
}

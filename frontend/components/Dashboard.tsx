"use client";

import { useMemo } from "react";
import { nameOf } from "@/lib/narrate";
import { AXIS_KO, type TraceEvent } from "@/lib/trace";

// 상태 대시보드(기획서 §11.2, B단계). HP·스태미나·승산 곡선·성향 diff.
// 트레이스만 읽는다 — 화면이 따로 상태를 들고 있으면 두 벌이 되고 어긋난다.

type Unit = {
  id: string;
  hp: number;
  hpMax: number;
  stamina: number;
  staminaMax: number;
  alive: boolean;
  fled: boolean;
  position: string;
  statuses: string[];
};

function unitsFrom(events: TraceEvent[]): Unit[] {
  const units = new Map<string, Unit>();
  for (const e of events) {
    if (e.kind === "mission_start") {
      units.clear();
      for (const p of (e.payload.party as { id: string; hp_max: number; position: string }[]) ?? []) {
        units.set(p.id, {
          id: p.id,
          hp: p.hp_max,
          hpMax: p.hp_max,
          stamina: 1,
          staminaMax: 1,
          alive: true,
          fled: false,
          position: p.position,
          statuses: [],
        });
      }
    }
    // context 이벤트가 매 턴 자기 상태를 싣는다 — 가장 촘촘한 소스다.
    if (e.kind === "context" && e.actor) {
      const self = (e.payload.visible as { self?: Record<string, unknown> })?.self;
      const u = units.get(e.actor);
      if (u && self) {
        u.hp = Number(self.hp ?? u.hp);
        u.hpMax = Number(self.hp_max ?? u.hpMax);
        u.stamina = Number(self.stamina ?? u.stamina);
        u.position = String(self.position ?? u.position);
        u.statuses = (self.statuses as string[]) ?? [];
        u.staminaMax = Math.max(u.staminaMax, u.stamina);
      }
    }
    if (e.kind === "flee" && e.actor && e.payload.success) {
      const u = units.get(e.actor);
      if (u) u.fled = true;
    }
    if (e.kind === "mission_end") {
      for (const id of (e.payload.dead as string[]) ?? []) {
        const u = units.get(id);
        if (u) {
          u.alive = false;
          u.hp = 0;
        }
      }
    }
  }
  return [...units.values()];
}

const STATUS_KO: Record<string, string> = {
  guard: "방어 태세",
  bless: "축복",
  blind: "실명",
  slow: "둔화",
};

export default function Dashboard({ events, names }: { events: TraceEvent[]; names: Record<string, string> }) {
  const units = useMemo(() => unitsFrom(events), [events]);
  const odds = useMemo(
    () => events.filter((e) => e.kind === "odds").map((e) => Number(e.payload.value)),
    [events],
  );
  const threshold = useMemo(() => {
    const last = [...events].reverse().find((e) => e.kind === "odds" && e.payload.threshold != null);
    return last ? Number(last.payload.threshold) : null;
  }, [events]);
  const diffs = useMemo(() => events.filter((e) => e.kind === "param_diff"), [events]);

  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="stack" style={{ gap: 8 }}>
        <div className="card-kicker">단원</div>
        {units.length === 0 && <p className="small faint">아직 편성되지 않았다.</p>}
        {units.map((u) => (
          <div key={u.id} className="stack" style={{ gap: 3 }}>
            <div className="row small" style={{ justifyContent: "space-between" }}>
              <span style={{ fontWeight: 600, opacity: u.alive && !u.fled ? 1 : 0.5 }}>
                {nameOf(u.id, names)}
                {!u.alive && " (쓰러짐)"}
                {u.fled && " (이탈)"}
              </span>
              <span className="faint mono">
                {u.hp}/{u.hpMax} · {u.position === "front" ? "전열" : "후열"}
              </span>
            </div>
            <div className="bar bar-hp">
              <span style={{ width: `${Math.max(0, (100 * u.hp) / u.hpMax)}%` }} />
            </div>
            <div className="bar bar-stamina" style={{ height: 4 }}>
              <span style={{ width: `${Math.max(0, (100 * u.stamina) / u.staminaMax)}%` }} />
            </div>
            {u.statuses.length > 0 && (
              <div className="row" style={{ gap: 3 }}>
                {u.statuses.map((s) => (
                  <span key={s} className="tag" style={{ fontSize: 10.5, padding: "1px 6px" }}>
                    {STATUS_KO[s] ?? s}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {odds.length > 1 && <OddsChart values={odds} threshold={threshold} />}

      {diffs.length > 0 && (
        <div className="stack" style={{ gap: 6 }}>
          <div className="card-kicker">성향이 바뀐 순간</div>
          {diffs.map((e) => (
            <div key={e.seq} className="small stack" style={{ gap: 2 }}>
              <b>
                {nameOf(e.actor, names)} — {String(e.payload.cause)}
              </b>
              <span className="faint mono">
                {Object.entries((e.payload.delta as Record<string, number>) ?? {})
                  .map(([k, v]) => `${AXIS_KO[k] ?? k} ${v > 0 ? "+" : ""}${v}`)
                  .join(" · ")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OddsChart({ values, threshold }: { values: number[]; threshold: number | null }) {
  const W = 260;
  const H = 64;
  const step = values.length > 1 ? W / (values.length - 1) : W;
  const path = values.map((v, i) => `${i === 0 ? "M" : "L"} ${i * step} ${H - v * H}`).join(" ");
  const last = values[values.length - 1];
  return (
    <div className="stack" style={{ gap: 4 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="card-kicker">승산</div>
        <span className="small mono">{Math.round(last * 100)}%</span>
      </div>
      <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="승산 곡선">
        <line x1={0} y1={H / 2} x2={W} y2={H / 2} stroke="var(--color-divider)" strokeDasharray="3 3" />
        {threshold != null && (
          <line
            x1={0}
            y1={H - threshold * H}
            x2={W}
            y2={H - threshold * H}
            stroke="var(--color-accent)"
            strokeDasharray="4 3"
            strokeWidth={1}
          />
        )}
        <path d={path} fill="none" stroke="var(--color-accent-2)" strokeWidth={2} />
      </svg>
      {threshold != null && (
        <span className="small faint">붉은 선이 단장의 후퇴 임계 {Math.round(threshold * 100)}%</span>
      )}
    </div>
  );
}

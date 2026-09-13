"use client";

import { useState } from "react";
import { nameOf } from "@/lib/narrate";
import { STAT_KO, type TraceEvent } from "@/lib/trace";

// 인터미션 입력(기획서 §5·§5.1). 유저는 카테고리 지시와 성장 포인트 분배만 한다.
// 캐릭터가 따를지는 캐릭터가 정한다 — 그래서 여기 "훈련시키기" 버튼은 없고
// "훈련하라고 말하기" 만 있다.

const CATEGORIES = [
  { key: "train", label: "훈련", hint: "숙련이 오르고 피로가 쌓인다" },
  { key: "study", label: "교육", hint: "지식이 늘고 피로가 조금" },
  { key: "rest", label: "휴식", hint: "피로가 크게 풀린다" },
  { key: "leisure", label: "여가", hint: "피로가 풀리고 기분이 산다" },
] as const;

type Category = (typeof CATEGORIES)[number]["key"];

const STAT_KEYS = ["str_", "agi", "con", "int_", "wis", "luck"] as const;

export default function IntermissionPanel({
  runId,
  events,
  names,
  timeoutS,
  onSent,
}: {
  runId: string;
  events: TraceEvent[];
  names: Record<string, string>;
  timeoutS: number;
  onSent: () => void;
}) {
  const party = ((events.find((e) => e.kind === "intermission_start")?.payload.party as string[]) ?? []).filter(
    Boolean,
  );
  const [directives, setDirectives] = useState<Record<string, Category>>({});
  const [growth, setGrowth] = useState<Record<string, Record<string, number>>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const granted = 10; // 승리 10 / 그 밖 6 — 서버가 실제 값을 정한다. 여기선 상한 표시용.

  function bump(id: string, stat: string, d: 1 | -1) {
    setGrowth((cur) => {
      const mine = { ...(cur[id] ?? {}) };
      const next = (mine[stat] ?? 0) + d;
      if (next < 0) return cur;
      const total = Object.values({ ...mine, [stat]: next }).reduce((a, b) => a + b, 0);
      if (total > granted) return cur;
      mine[stat] = next;
      return { ...cur, [id]: mine };
    });
  }

  async function send() {
    setBusy(true);
    setError(null);
    const body = {
      directives,
      growth: Object.fromEntries(
        Object.entries(growth).map(([id, m]) => [
          id,
          Object.fromEntries(Object.entries(m).filter(([, v]) => v > 0)),
        ]),
      ),
    };
    const r = await fetch(`/api/runs/${encodeURIComponent(runId)}/directives`, {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      setError(typeof d.detail === "string" ? d.detail : "보내지 못했다");
      setBusy(false);
      return;
    }
    onSent();
  }

  return (
    <div className="card" style={{ gap: 12, borderColor: "var(--color-accent)" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="stack" style={{ gap: 2 }}>
          <div className="card-kicker">인터미션 · 야영지</div>
          <b>다음 계약 전에 무엇을 시킬 것인가</b>
        </div>
        <span className="tag tag-warn">{timeoutS}초 안에 답하지 않으면 전원 훈련</span>
      </div>
      <p className="small muted">
        당신이 정하는 것은 방향뿐이다. 따를지는 단원이 정한다 — 게으르고 지친 단원은 훈련장 대신 술집에 갈 수 있고,
        당신은 결과만 통보받는다.
      </p>

      {party.map((id) => (
        <div key={id} className="stack" style={{ gap: 6, paddingTop: 8, borderTop: "1px solid var(--color-divider)" }}>
          <b className="small">{nameOf(id, names)}</b>
          <div className="row" style={{ gap: 4 }}>
            {CATEGORIES.map((c) => (
              <button
                key={c.key}
                title={c.hint}
                className={`btn btn-sm ${(directives[id] ?? "train") === c.key ? "btn-primary" : ""}`}
                onClick={() => setDirectives((cur) => ({ ...cur, [id]: c.key }))}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="row small" style={{ gap: 6, flexWrap: "wrap" }}>
            <span className="faint">성장 포인트</span>
            {STAT_KEYS.map((k) => {
              const v = growth[id]?.[k] ?? 0;
              return (
                <span key={k} className="row" style={{ gap: 2 }}>
                  <button className="btn btn-sm" style={{ padding: "0 6px" }} onClick={() => bump(id, k, -1)}>
                    −
                  </button>
                  <span className="mono" style={{ minWidth: 42, textAlign: "center" }}>
                    {STAT_KO[k]} {v > 0 ? `+${v}` : "·"}
                  </span>
                  <button className="btn btn-sm" style={{ padding: "0 6px" }} onClick={() => bump(id, k, 1)}>
                    +
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      ))}

      {error && (
        <p className="small" style={{ color: "var(--color-danger)" }}>
          {error}
        </p>
      )}
      <button className="btn btn-primary" disabled={busy} onClick={send}>
        {busy ? "보내는 중…" : "지시하고 다음 계약으로 →"}
      </button>
    </div>
  );
}

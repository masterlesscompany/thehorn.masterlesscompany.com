"use client";

import { useEffect, useState } from "react";
import type { TraceEvent } from "@/lib/trace";

type Props = {
  runId: string;
  ask: TraceEvent; // kind === "recovery" && payload.awaiting_input
  names: Record<string, string>;
  onSent: () => void;
};

/**
 * 회수 결정 — 굴에 끌려간 대원을 다시 데려올 것인가(기획서 v3 §6.8).
 *
 * 몸값은 은화만 태우지만 회수는 은화와 출동 슬롯을 동시에 태운다.
 * **회수는 보장된 거래가 아니다** — 돈을 내도 실패할 수 있다.
 * 그리고 두고 오면 그것이 그 사람에게서 배운다(§8.4 「섭식」).
 *
 * 값과 남은 시간은 백엔드가 물어보는 이벤트에 실어 보낸다 — 전에는 유저가
 * 얼마인지도, 얼마나 남았는지도 모른 채 결정했다(QA 2026-09-09 L·U8).
 */
export default function RecoveryPanel({ runId, ask, names, onSent }: Props) {
  const members = (ask.payload.members as string[]) ?? [];
  const costs = (ask.payload.costs as Record<string, number>) ?? {};
  const timeoutS = Number(ask.payload.timeout_s ?? 60);

  const [pay, setPay] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [left, setLeft] = useState(timeoutS);

  // 답하지 않으면 자동 미지불이다 — 기한이 곧 결정이라 남은 시간을 보여준다.
  useEffect(() => {
    setLeft(timeoutS);
    const t = setInterval(() => setLeft((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [timeoutS, ask.seq]);

  const toggle = (id: string) =>
    setPay((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));

  const total = pay.reduce((sum, id) => sum + (costs[id] ?? 0), 0);

  const send = async () => {
    setBusy(true);
    setErr(null);
    try {
      const r = await fetch(`/api/runs/${encodeURIComponent(runId)}/recovery`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pay }),
      });
      if (!r.ok) {
        const b = await r.json().catch(() => ({}));
        setErr(String(b.detail ?? "결정을 보내지 못했다"));
        return;
      }
      onSent();
    } catch {
      setErr("결정을 보내지 못했다");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card stack" style={{ gap: 10, borderColor: "var(--color-warn)" }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="card-kicker">회수 결정 — 굴에 두고 올 것인가</div>
        <span className="mono small" style={{ color: left <= 10 ? "var(--color-danger)" : undefined }}>
          {left}초 뒤 자동 미지불
        </span>
      </div>
      <p className="small" style={{ margin: 0 }}>
        값은 <strong>그 사람에게 쏟은 성장 포인트</strong>에 비례한다 — 아낀 사람일수록 비싸다.{" "}
        <strong>돈을 내도 실패할 수 있다.</strong> 두고 오면 그것이 그 사람에게서 배워 다음에 돌아온다.
      </p>
      <ul className="stack" style={{ gap: 6, listStyle: "none", padding: 0, margin: 0 }}>
        {members.map((id) => (
          <li key={id} className="row" style={{ gap: 8, alignItems: "center" }}>
            <label className="row" style={{ gap: 6, alignItems: "center" }}>
              <input type="checkbox" checked={pay.includes(id)} onChange={() => toggle(id)} />
              <strong>{names[id] ?? id}</strong>
            </label>
            <span className="mono small">{costs[id] ?? 0}</span>
            <span className="faint small">굴로 끌려갔다</span>
          </li>
        ))}
      </ul>
      {/* 값을 치러도 이번 계약에 돌아오지는 않는다. 그 사실을 결정 전에 말한다 —
          말하지 않으면 "돈을 냈는데 아무 일도 안 일어났다" 가 된다(QA 2026-09-09 P·U9). */}
      <p className="small faint" style={{ margin: 0 }}>
        지금 정하는 것은 <strong>회수를 시도할지</strong>다. 회수 출동은 다음 계약에 열린다(기획서 v3 §12) — 값을 치러도 이번 계약의 남은
        판에는 나오지 않는다. 두고 온 사람만 「섭식」 카드가 된다.
      </p>
      {err && (
        <p className="small" style={{ margin: 0, color: "var(--color-danger)" }}>
          {err}
        </p>
      )}
      <div className="row" style={{ gap: 6 }}>
        <button className="btn btn-sm btn-primary" disabled={busy} onClick={send}>
          {pay.length ? `${pay.length}명을 되찾는다 (${total})` : "아무도 되찾지 않는다"}
        </button>
        <span className="faint small">답하지 않으면 전원 미지불로 처리된다</span>
      </div>
    </section>
  );
}

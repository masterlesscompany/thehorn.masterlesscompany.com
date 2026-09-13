"use client";

import { useState } from "react";

// 잔여 횟수의 기본값. 서버가 `/roster/preset.horn_charges` 로 내려주는 값이
// 진짜이고(수치 단일 출처), 이건 그것이 아직 안 왔을 때의 자리다.
const CHARGES = 3;

/**
 * 뿔피리 — 유저가 전투 중에 할 수 있는 유일한 일(기획서 v3 §8.2).
 *
 * 불면 즉시 이탈이다. 전멸은 피하지만 목표는 실패하고 보수는 없다.
 * 불지 않으면 단장이 스스로 판단한다 — 물러날 줄 아는가, 그것이 이
 * 단장이 증명해야 하는 것이다.
 *
 * 세 번인 이유는 설정이 아니라 설계다. 무한이면 유저가 조종하는 게임이 되고,
 * 0 이면 관전이 된다. 세 번이면 매 판 "지금인가" 를 묻게 된다.
 */
export default function HornButton({
  runId,
  live,
  charges = CHARGES,
  reason,
}: {
  runId: string;
  live: boolean;
  charges?: number;
  /** 지금 못 부는 이유. 있으면 버튼이 잠기고 그대로 보여 준다. */
  reason?: string | null;
}) {
  const [left, setLeft] = useState(charges);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const blow = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await fetch(`/api/runs/${encodeURIComponent(runId)}/horn`, { method: "POST" });
      const body = await r.json().catch(() => ({}));
      if (r.ok) {
        setLeft(Number(body.horn_left ?? left - 1));
        // 200 은 "신호를 보냈다" 까지다. 실제로 닿았는지는 `horn` 트레이스
        // 이벤트가 말한다 — 전령관이 없으면 한 턴 늦고, 그 사이 판이 끝나면
        // 아예 안 닿는다. 여기서 단언하면 화면이 거짓말한다(QA 재검 P2-K).
        setNote("신호를 보냈다. 전령관이 받으면 대열이 물러선다.");
      } else {
        setNote(String(body.detail ?? "지금은 부를 수 없다"));
      }
    } catch {
      setNote("신호가 닿지 않았다");
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  const spent = left <= 0;
  const 잠김 = !live || spent || Boolean(reason);
  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="row" style={{ gap: 8, alignItems: "center" }}>
        <span className="card-kicker" style={{ margin: 0 }}>뿔피리</span>
        <span className="mono small" aria-label={`남은 횟수 ${left}회`}>
          {"●".repeat(Math.max(0, left))}
          <span className="faint">{"○".repeat(Math.max(0, CHARGES - left))}</span>
        </span>
      </div>

      {!confirming ? (
        <button
          className="btn btn-sm"
          disabled={잠김 || busy}
          onClick={() => setConfirming(true)}
          title={
            spent
              ? "세 번을 다 썼다"
              : "불면 즉시 이탈한다. 전멸은 피하지만 목표는 실패하고 보수는 없다"
          }
        >
          {spent ? "다 썼다" : reason ? "지금은 못 분다" : "뿔피리를 분다"}
        </button>
      ) : (
        <div className="stack" style={{ gap: 6 }}>
          <p className="small" style={{ margin: 0 }}>
            지금 불면 <strong>즉시 이탈</strong>이다. 목표는 실패하고 보수는 없다.
            불지 않으면 단장이 스스로 판단한다.
          </p>
          <div className="row" style={{ gap: 6 }}>
            <button className="btn btn-sm btn-primary" disabled={busy} onClick={blow}>
              분다
            </button>
            <button className="btn btn-sm" disabled={busy} onClick={() => setConfirming(false)}>
              기다린다
            </button>
          </div>
        </div>
      )}

      {/* 툴팁은 모바일에 없다. 상시 캡션으로 둔다(QA 2026-09-09 U5). */}
      <p className="small faint" style={{ margin: 0, maxWidth: 220 }}>
        {reason ?? "불면 전원 생환 · 목표 실패 · 보수 없음"}
      </p>
      {note && (
        <p className="small faint" style={{ margin: 0 }} role="status">
          {note}
        </p>
      )}
    </div>
  );
}

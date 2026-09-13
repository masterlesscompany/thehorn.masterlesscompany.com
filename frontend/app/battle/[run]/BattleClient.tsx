"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import CardsPanel from "@/components/CardsPanel";
import Dashboard from "@/components/Dashboard";
import HornButton from "@/components/HornButton";
import RecoveryPanel from "@/components/RecoveryPanel";
import Inspector from "@/components/Inspector";
import IntermissionPanel from "@/components/IntermissionPanel";
import NarrativeStream from "@/components/NarrativeStream";
import { buildNameMap, isKind, KINDS, type TraceEvent } from "@/lib/trace";

type Status = "connecting" | "live" | "done" | "error";

// 2패널 트레이스 뷰어(기획서 §11.2): 왼쪽 서사 스트림, 가운데 판정 인스펙터.
// 원칙: 왼쪽에서 일어나는 모든 일이 가운데에서 설명 가능하다.
export default function BattleClient({ runId }: { runId: string }) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<Status>("connecting");
  const [error, setError] = useState<string | null>(null);
  const [selectedSeq, setSelectedSeq] = useState<number | null>(null);
  const [follow, setFollow] = useState(true);
  const [showQuiet, setShowQuiet] = useState(false);
  const [sentFor, setSentFor] = useState<number[]>([]);
  const [recoverySentFor, setRecoverySentFor] = useState<number[]>([]);
  const seen = useRef(new Set<number>());

  useEffect(() => {
    const es = new EventSource(`/api/runs/${encodeURIComponent(runId)}/stream`);
    const onEvent = (raw: MessageEvent) => {
      try {
        const e = JSON.parse(raw.data) as TraceEvent;
        if (!isKind(e.kind) || seen.current.has(e.seq)) return;
        seen.current.add(e.seq);
        setEvents((cur) => [...cur, e]);
        setStatus("live");
      } catch {
        /* keepalive 등 */
      }
    };
    es.onmessage = onEvent;
    // 서버가 event: <kind> 로 보내므로 종류별로 붙인다.
    for (const k of KINDS) es.addEventListener(k, onEvent as EventListener);
    es.addEventListener("done", () => {
      setStatus("done");
      es.close();
    });
    es.addEventListener("error", (ev) => {
      const me = ev as MessageEvent;
      if (me.data) {
        try {
          setError(JSON.parse(me.data).error);
        } catch {
          setError(String(me.data));
        }
        setStatus("error");
        es.close();
      } else if (es.readyState === EventSource.CLOSED) {
        setStatus((s) => (s === "done" ? s : "error"));
      }
    });
    return () => es.close();
  }, [runId]);

  const names = useMemo(() => buildNameMap(events), [events]);
  const selected = useMemo(() => events.find((e) => e.seq === selectedSeq) ?? null, [events, selectedSeq]);
  const runEnd = events.find((e) => e.kind === "run_end");
  // 인터미션이 입력을 기다리는 중인가 — 그 뒤에 다른 이벤트가 오면 이미 지나갔다.
  const awaiting = useMemo(() => {
    const idx = events.findLastIndex(
      (e) => e.kind === "intermission_start" && e.payload.awaiting_input,
    );
    if (idx < 0 || sentFor.includes(events[idx].seq)) return null;
    return idx === events.length - 1 ? events[idx] : null;
  }, [events, sentFor]);
  // 리플레이 런은 유저 입력을 녹화에서 재생한다 — 여기서 부는 신호는 소비자가
  // 없어 충전만 닳고 이후 요청이 전부 409 가 된다(QA 재검 2026-09-09 P1-D).
  const replaying = useMemo(
    () => events.find((e) => e.kind === "run_start")?.payload.model === "replay",
    [events],
  );
  const missionStart = events.find((e) => e.kind === "mission_start");
  const title = missionStart ? String((missionStart.payload.name as string) ?? "") : "";

  // 그것에게 이름이 붙었나(기획서 v3 §8.5). 붙으면 계약이 끝날 때까지 남는다.
  const bossName = useMemo(() => {
    const named = events.findLast((e) => e.kind === "boss_named");
    return named ? String(named.payload.after ?? "") : null;
  }, [events]);

  // 굴로 끌려간 사람들 — 회수 결정을 받아야 한다(기획서 v3 §6.8).
  //
  // 조건이 까다로운 이유(QA 2026-09-09 U7·T8·U14): 끝난 런을 다시 열면 정적
  // 스트림이 casualty 를 다시 흘려 패널이 되살아나고, 눌러도 409/404 인 막다른
  // 곳이 된다. 그리고 결정은 **판마다** 받으므로 런 단위 불리언으로는 2판째
  // 끌려감을 물어보지 못한다.
  const lastMission = useMemo(
    () => events.findLast((e) => e.kind === "mission_start")?.mission ?? null,
    [events],
  );
  // 백엔드가 값과 남은 시간을 실어 물어본다(QA 2026-09-09 L). 화면이 끌려간
  // 사람을 casualty 에서 짜맞추지 않는다 — 물어보는 쪽이 명단을 준다.
  const recoveryAsk = useMemo(
    () =>
      events.findLast(
        (e) => e.kind === "recovery" && e.payload.awaiting_input && e.mission === lastMission,
      ) ?? null,
    [events, lastMission],
  );
  // 백엔드가 결정을 기록했으면(물음이 아닌 recovery 이벤트) 더는 묻지 않는다 —
  // 재열람·리플레이가 이걸로 해결된다.
  const decided = useMemo(
    () =>
      events.some(
        (e) => e.kind === "recovery" && !e.payload.awaiting_input && e.mission === lastMission,
      ),
    [events, lastMission],
  );
  const askRecovery =
    status === "live" &&
    recoveryAsk !== null &&
    !decided &&
    lastMission !== null &&
    !recoverySentFor.includes(lastMission);

  // 보스전 시작에 펼쳐진 학습 카드(기획서 v3 §8.4). 마지막 것이 지금 판의 것이다.
  const cards = useMemo(() => events.findLast((e) => e.kind === "cards") ?? null, [events]);

  return (
    <main className="page stack" style={{ gap: 14 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="stack" style={{ gap: 2 }}>
          <div className="card-kicker">전투 · {title || "…"}</div>
          <h2>
            {status === "connecting" && "전장에 연결하는 중…"}
            {status === "live" && "진행 중"}
            {status === "done" && "끝났다"}
            {status === "error" && "끊겼다"}
            <span className="faint small mono" style={{ marginLeft: 10 }}>
              {runId}
            </span>
          </h2>
        </div>
        <div className="row small">
          <label className="row" style={{ gap: 4 }}>
            <input type="checkbox" checked={follow} onChange={(e) => setFollow(e.target.checked)} />
            따라가기
          </label>
          <label className="row" style={{ gap: 4 }} title="승산·순응·행동 순서까지 전부 보여준다">
            <input type="checkbox" checked={showQuiet} onChange={(e) => setShowQuiet(e.target.checked)} />
            전부 보기
          </label>
          <HornButton
            runId={runId}
            live={status === "live"}
            // 인터미션·회수 대기 중에는 백엔드가 거절한다. 눌러 보고 튕기기
            // 전에 이유를 보여 준다(QA 2026-09-09 U6).
            reason={
              replaying
                ? "되감는 중이다 — 녹화된 판은 다시 부를 수 없다"
                : awaiting
                  ? "야영지다 — 전투 중에만 분다"
                  : askRecovery
                    ? "회수를 먼저 정한다"
                    : null
            }
          />
          {runEnd && (
            <Link className="btn btn-sm btn-primary" href={`/result/${runId}`}>
              결과 보기 →
            </Link>
          )}
          <Link className="btn btn-sm" href="/roster">
            다시 편성
          </Link>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: "var(--color-danger)" }}>
          <p className="small" style={{ color: "var(--color-danger)" }}>
            런이 실패했다: {error}
          </p>
        </div>
      )}

      {bossName && (
        <p className="small" style={{ margin: 0 }}>
          대원들은 그것을 <strong>「{bossName}」</strong>이라 부른다.
        </p>
      )}

      {cards && <CardsPanel event={cards} names={names} />}

      {askRecovery && recoveryAsk && (
        <RecoveryPanel
          runId={runId}
          ask={recoveryAsk}
          names={names}
          onSent={() =>
            setRecoverySentFor((cur) => (lastMission === null ? cur : [...cur, lastMission]))
          }
        />
      )}

      {awaiting && (
        <IntermissionPanel
          runId={runId}
          events={events}
          names={names}
          timeoutS={Number(awaiting.payload.timeout_s ?? 60)}
          onSent={() => setSentFor((cur) => [...cur, awaiting.seq])}
        />
      )}

      <div className="panels three">
        <section className="card panel panel-tall" style={{ gap: 8 }}>
          <div className="card-kicker">서사 스트림 · 클릭하면 판정이 열린다</div>
          <NarrativeStream
            events={events}
            names={names}
            selectedSeq={selectedSeq}
            onSelect={(s) => {
              setSelectedSeq(s);
              setFollow(false);
              // 좁은 화면에서는 인스펙터가 아래에 있다 — 눌렀는데 아무 일도
              // 안 일어난 것처럼 보이면 안 된다.
              if (typeof window !== "undefined" && window.innerWidth <= 900) {
                document.getElementById("inspector")?.scrollIntoView({ behavior: "smooth", block: "start" });
              }
            }}
            follow={follow}
            showQuiet={showQuiet}
          />
        </section>
        <section id="inspector" className="card panel" style={{ gap: 8 }}>
          <div className="card-kicker">판정 인스펙터</div>
          <Inspector event={selected} names={names} events={events} />
        </section>
        <section className="card panel" style={{ gap: 8 }}>
          <div className="card-kicker">상태</div>
          <Dashboard events={events} names={names} />
        </section>
      </div>
    </main>
  );
}

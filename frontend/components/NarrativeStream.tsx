"use client";

import { useEffect, useRef } from "react";
import { narrate } from "@/lib/narrate";
import type { TraceEvent } from "@/lib/trace";

// 기본으로 접는 종류. 24턴이 400줄이 되면 아무도 읽지 않는다.
//
// 단, **가려진 것이 있는 context 는 접지 않는다** — 지혜 마스킹은 이 프로젝트가
// 파는 것 중 하나인데, 접어 두면 화면에서 확인할 방법이 0 이 된다(QA 라운드 2).
const QUIET = new Set(["odds", "turn_start", "context"]);

function isQuiet(e: TraceEvent): boolean {
  if (e.kind === "context") return ((e.payload.masked as string[]) ?? []).length === 0;
  if (e.kind === "compliance") return e.payload.verdict === "comply";
  return QUIET.has(e.kind);
}

type Props = {
  events: TraceEvent[];
  names: Record<string, string>;
  selectedSeq: number | null;
  onSelect: (seq: number) => void;
  follow: boolean;
  showQuiet?: boolean;
};

export default function NarrativeStream({ events, names, selectedSeq, onSelect, follow, showQuiet = false }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (follow) endRef.current?.scrollIntoView({ block: "end" });
  }, [events.length, follow]);

  return (
    <div className="stream">
      {events.map((e) => {
        if (!showQuiet && e.kind !== "turn_start" && isQuiet(e)) return null;
        const cls = [
          "stream-item",
          `k-${e.kind}`,
          e.kind === "compliance" && e.payload.verdict === "deviate" ? "deviate" : "",
          e.seq === selectedSeq ? "selected" : "",
        ].join(" ");
        return (
          <div key={e.seq} className={cls} onClick={() => onSelect(e.seq)}>
            <span className="seq">#{e.seq}</span>
            {narrate(e, names)}
          </div>
        );
      })}
      {events.length === 0 && <p className="small faint">아직 아무 일도 일어나지 않았다.</p>}
      <div ref={endRef} />
    </div>
  );
}

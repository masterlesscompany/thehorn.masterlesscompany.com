"use client";

import type { PresetCharacter } from "@/app/roster/RosterClient";
import PointAllocator from "@/components/PointAllocator";
import type { Allocation } from "@/lib/allocation";
import { AXIS_KO } from "@/lib/trace";

const BUILD_KO: Record<string, string> = { slim: "마른", normal: "보통", sturdy: "건장" };

type Props = {
  c: PresetCharacter;
  classes: { key: string; label: string; primary: string[] }[];
  statBase: number;
  statMax: number;
  freePoints: number;
  alloc: Allocation;
  onAlloc: (a: Allocation) => void;
  cls: string;
  onClass: (k: string) => void;
  gender: "female" | "male";
  onGender: (g: "female" | "male") => void;
  selected: boolean;
  selectable: boolean;
  onToggle: () => void;
};

export default function RosterCard(p: Props) {
  const { c } = p;
  return (
    <div className="card" style={{ gap: 12, borderColor: p.selected ? "var(--color-accent)" : undefined }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <div className="stack" style={{ gap: 2 }}>
          <div className="card-title">{c.name}</div>
          <div className="row small muted" style={{ gap: 6 }}>
            <span>
              {c.body.height_cm}cm · {BUILD_KO[c.body.build] ?? c.body.build} · {c.body.weight_kg}kg
            </span>
            <span className="tag tag-outline" title="성향 4축을 알아보기 쉽게 붙인 이름표. AI 는 이 글자를 보지 않는다.">
              {c.mbti}
            </span>
          </div>
        </div>
        <button className={`btn btn-sm ${p.selected ? "btn-primary" : ""}`} disabled={!p.selectable} onClick={p.onToggle}>
          {p.selected ? "출전 ✓" : "출전"}
        </button>
      </div>

      <p className="small muted">{c.backstory}</p>
      <p className="small faint">생애: {c.life}</p>

      <div className="row small" style={{ gap: 10 }}>
        <label className="row" style={{ gap: 4 }}>
          클래스
          <select value={p.cls} onChange={(e) => p.onClass(e.target.value)}>
            {p.classes.map((k) => (
              <option key={k.key} value={k.key}>
                {k.label}
              </option>
            ))}
          </select>
        </label>
        <label className="row" style={{ gap: 4 }}>
          성별
          <select value={p.gender} onChange={(e) => p.onGender(e.target.value as "female" | "male")}>
            <option value="female">여성</option>
            <option value="male">남성</option>
          </select>
        </label>
      </div>

      <PointAllocator base={c.base_stats} alloc={p.alloc} statBase={p.statBase} statMax={p.statMax} freePoints={p.freePoints} recommended={c.recommended} onChange={p.onAlloc} />

      <div className="stack" style={{ gap: 4 }}>
        <div className="card-kicker">성향 (타고남 · 변경 불가)</div>
        <div className="row small muted" style={{ gap: 8 }}>
          {Object.entries(c.disposition_text).map(([axis, text]) => (
            <span key={axis} title={AXIS_KO[axis]}>
              {text}
            </span>
          ))}
        </div>
      </div>

      <div className="small faint">
        단원의 선택(프리셋 기준): {c.build_preview.weapon} · {c.build_preview.armor} — &ldquo;{c.build_preview.rationale}&rdquo;
      </div>
    </div>
  );
}

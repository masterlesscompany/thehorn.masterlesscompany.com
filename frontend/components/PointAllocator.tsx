"use client";

import { bump, remaining, STAT_KEYS, type Allocation, type StatKey } from "@/lib/allocation";
import { STAT_KO } from "@/lib/trace";

const HINT: Record<StatKey, string> = {
  str_: "물리 피해 · 중량 장비 효율",
  agi: "명중 · 회피 · 행동 순서",
  con: "HP · 스태미나 · 회복",
  int_: "전술 이해 · 훈련 효율",
  wis: "전장에서 보이는 정보의 양",
  luck: "주사위에만 소폭. 판단엔 개입 없음",
};

type Props = {
  base: Record<string, number>;
  alloc: Allocation;
  statBase: number;
  statMax: number;
  freePoints: number;
  recommended: Record<string, number>;
  onChange: (a: Allocation) => void;
};

export default function PointAllocator({ base, alloc, statBase, statMax, freePoints, recommended, onChange }: Props) {
  const left = remaining(alloc, freePoints);
  return (
    <div className="stack" style={{ gap: 6 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="card-kicker">능력치 · 남은 포인트 {left}</div>
        <div className="row" style={{ gap: 4 }}>
          <button className="btn btn-sm btn-ghost" onClick={() => onChange({ ...recommended })}>
            추천 배분
          </button>
          <button className="btn btn-sm btn-ghost" onClick={() => onChange({})}>
            초기화
          </button>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 4 }}>
        {STAT_KEYS.map((k) => {
          const v = base[k] + (alloc[k] ?? 0);
          return (
            <div key={k} className="row small" style={{ justifyContent: "space-between", gap: 6 }} title={HINT[k]}>
              <span style={{ width: 34 }}>{STAT_KO[k]}</span>
              <div className="bar" style={{ flex: 1 }}>
                <span style={{ width: `${(v / 20) * 100}%` }} />
              </div>
              <span className="mono" style={{ width: 22, textAlign: "right" }}>
                {v}
              </span>
              <span className="row" style={{ gap: 2 }}>
                <button className="btn btn-sm" style={{ padding: "0 7px" }} onClick={() => onChange(bump(alloc, k, -1, statBase, freePoints, statMax))}>
                  −
                </button>
                <button className="btn btn-sm" style={{ padding: "0 7px" }} onClick={() => onChange(bump(alloc, k, 1, statBase, freePoints, statMax))}>
                  +
                </button>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

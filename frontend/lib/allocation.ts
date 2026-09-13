// 능력치 포인트 분배 — 순수 함수.
// backend/apps/arena/domain/services/rules/stats.py 의 allocate() 와 같은 규칙.
// 화면이 먼저 막고, 백엔드가 다시 막는다(422). 화면 검증은 편의이고 백엔드 검증이 진실이다.

export const STAT_KEYS = ["str_", "agi", "con", "int_", "wis", "luck"] as const;
export type StatKey = (typeof STAT_KEYS)[number];
export type Allocation = Partial<Record<StatKey, number>>;

// 상한은 서버가 준다(`/roster/preset.stat_max`). 이 값은 그것이 아직 안 왔을
// 때의 자리다 — 20 을 하드코딩하던 것을 걷어낸 흔적(수치 단일 출처).
export const STAT_MAX_FALLBACK = 20;

export function total(a: Allocation): number {
  return STAT_KEYS.reduce((s, k) => s + (a[k] ?? 0), 0);
}

export function remaining(a: Allocation, freePoints: number): number {
  return freePoints - total(a);
}

/** 한 능력치에 1 더한다. 총량·상한을 넘으면 그대로 돌려준다. */
export function bump(
  a: Allocation,
  key: StatKey,
  delta: 1 | -1,
  base: number,
  freePoints: number,
  statMax: number = STAT_MAX_FALLBACK,
): Allocation {
  const cur = a[key] ?? 0;
  const next = cur + delta;
  if (next < 0) return a;
  if (base + next > statMax) return a;
  if (delta > 0 && total(a) + 1 > freePoints) return a;
  return { ...a, [key]: next };
}

export function validate(
  a: Allocation,
  base: number,
  freePoints: number,
  statMax: number = STAT_MAX_FALLBACK,
): string | null {
  for (const k of STAT_KEYS) {
    const v = a[k] ?? 0;
    if (v < 0) return `${k} 에 음수 포인트`;
    if (base + v > statMax) return `${k} 이 상한 ${statMax} 을 넘는다`;
  }
  if (total(a) > freePoints) return `포인트 총량 ${total(a)} 이 ${freePoints} 을 넘는다`;
  return null;
}

/** 0 인 항목을 뺀다 — 백엔드에 보낼 모양. */
export function compact(a: Allocation): Record<string, number> {
  const out: Record<string, number> = {};
  for (const k of STAT_KEYS) if ((a[k] ?? 0) > 0) out[k] = a[k]!;
  return out;
}

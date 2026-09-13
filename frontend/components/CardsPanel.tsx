"use client";

import type { TraceEvent } from "@/lib/trace";

const SOURCE_KO: Record<string, string> = {
  scout: "고블린의 척후 관찰",
  flight: "놀의 탈주 추적",
  loot: "오크의 전리품",
  feeding: "섭식",
};

type Card = {
  key: string;
  name: string;
  source: string;
  // 기획서 v3 §11 — 카드마다 출처 라운드·인물·종이 링크된다.
  round?: number;
  observation: string;
  evidence: Record<string, unknown>;
  applied: Record<string, unknown>;
};

/** 카드가 이 판에서 실제로 무엇을 걸었나. 비면 걸 대상이 없었던 것이다. */
function 효과(c: Card, names: Record<string, string>): string {
  const a = c.applied ?? {};
  if (!a || Object.keys(a).length === 0) return "관측만 남았다 — 이 판에 걸 대상이 없다";
  if (a.field === "boss_focus") {
    const 계승 = a.inherited_from ? ` (${names[String(a.inherited_from)] ?? a.inherited_from}에게서 배운 것)` : "";
    return `${names[String(a.after)] ?? a.after}를 노린다${계승}`;
  }
  if (a.field === "blind") {
    const who = ((a.units as string[]) ?? []).map((u) => names[u] ?? u).join(", ");
    return `${who} 의 사거리를 −${a.value}`;
  }
  return JSON.stringify(a);
}

/**
 * 학습 카드 패널 — 보스전 시작에 펼쳐진다(기획서 v3 §8.4).
 *
 * 여기가 이 시나리오의 심장이다. 보스 적응이 기술 차트가 아니라 **죄책감**으로
 * 전달된다 — 유저가 안 한 것(회수)이 카드가 되어 눈앞에 있다.
 */
export default function CardsPanel({
  event,
  names,
}: {
  event: TraceEvent;
  names: Record<string, string>;
}) {
  const cards = (event.payload.cards as Card[]) ?? [];
  if (!cards.length) return null;

  return (
    <section className="card stack" style={{ gap: 10, borderColor: "var(--color-accent)" }}>
      <div className="card-kicker">그것이 배운 것</div>
      <ul className="stack" style={{ gap: 10, listStyle: "none", padding: 0, margin: 0 }}>
        {cards.map((c) => {
          const who = c.evidence?.member ? String(c.evidence.member) : null;
          return (
            <li key={c.key} className="stack" style={{ gap: 3 }}>
              <div className="row" style={{ gap: 8, alignItems: "baseline" }}>
                <strong>「{c.name}」</strong>
                <span className="faint small">
                  출처: {SOURCE_KO[c.source] ?? c.source}
                  {c.round ? ` · ${c.round}회차` : ""}
                </span>
              </div>
              <p className="small" style={{ margin: 0 }}>
                관측: {c.observation}
              </p>
              {/* 걸린 것을 그대로 말한다. `applied` 가 비었는데 "배웠습니다" 라고
                  단언하면 화면이 거짓말한다 — `boss_adapt` 의 `no_change` 와 같은
                  원칙이다(QA 재검 2026-09-09 R20). */}
              <p className="small faint" style={{ margin: 0 }}>
                걸린 것: {효과(c, names)}
              </p>
              {c.source === "feeding" && who && (
                <p className="small" style={{ margin: 0, color: "var(--color-accent)" }}>
                  {Object.keys(c.applied ?? {}).length > 0
                    ? `이 보스는 ${c.round ? `${c.round}회차에 ` : ""}당신이 굴에 두고 온 ${names[who] ?? who}에게서 이걸 배웠습니다.`
                    : `그것은 ${c.round ? `${c.round}회차에 ` : ""}${names[who] ?? who}에게서 배웠다 — 이 판에는 그 병과가 없어 아직 쓰지 못한다.`}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

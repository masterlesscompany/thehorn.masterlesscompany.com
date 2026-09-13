import { backendFetch } from "@/lib/backend";
import AbChart, { E3Chart, type AbResult, type E3Result } from "@/components/ExperimentChart";

export const dynamic = "force-dynamic";

const INTRO: Record<string, { title: string; body: string }> = {
  e1: {
    title: "E1 · 조합별 단장 ON / OFF",
    body: "단장이 실제로 도움이 되는가 — 좋은 조합의 승률이 아니라 나쁜 조합에서의 회복력으로 잰다. 같은 시드를 두 번 돌리므로 차이는 단장 하나에서 온다.",
  },
  e2: {
    title: "E2 · 보스 적응 ON / OFF",
    body: "굴의 그것이 우리를 읽는 것이 판을 바꾸는가. 관측 네 가지(같은 자의 반복 공격·전열이 버팀·반복된 치유·방어 일변도)에 대응 네 가지가 붙는다.",
  },
  e3: {
    title: "E3 · 성향별 행동 분포",
    body: "성향 수치만 바꾼 같은 전투. 다양성이 말이 아니라 검증된 판단 분기라는 것을 보여준다. 축 하나만 극단으로 두고 나머지는 0 으로 고정했다.",
  },
};

// 백엔드가 꺼진 것과 실험을 아직 안 돌린 것은 다르다. 둘 다 null 로 만들면
// 화면이 "아직 결과가 없다" 고 거짓말한다(QA 2026-09-09 U15).
type Load<T> = { data: T | null; down: boolean };

async function load<T>(name: string): Promise<Load<T>> {
  try {
    const r = await backendFetch(`/experiments/${name}`);
    return { data: r.ok ? ((await r.json()) as T) : null, down: false };
  } catch {
    return { data: null, down: true };
  }
}

export default async function ExperimentsPage() {
  const [r1, r2, r3] = await Promise.all([
    load<AbResult>("e1"),
    load<AbResult>("e2"),
    load<E3Result>("e3"),
  ]);
  const [e1, e2, e3] = [r1.data, r2.data, r3.data];
  const down = r1.down && r2.down && r3.down;
  const none = !down && !e1 && !e2 && !e3;

  return (
    <main className="page page-narrow stack" style={{ gap: 18 }}>
      <div className="card-kicker">실험</div>
      <h1>말이 아니라 숫자로</h1>
      <p className="muted small">
        전부 Fake 모델(휴리스틱)로 돌린 자동 대전이다. 사람도 API 키도 없이 돌아가고, 같은 시드는 같은 판을 만든다.
        실제 모델로 다시 돌리면 같은 표에 다른 숫자가 들어간다.
      </p>

      {down && (
        <div className="card" style={{ borderColor: "var(--color-danger)" }}>
          <p className="small" style={{ color: "var(--color-danger)", margin: 0 }}>
            백엔드에 닿지 못했다. 결과가 없는 것이 아니라 <strong>물어보지 못한 것</strong>이다 — 백엔드를 띄우고 새로고침한다.
          </p>
        </div>
      )}
      {none && (
        <div className="card">
          <p className="small muted">
            아직 결과가 없다. 백엔드에서 <code>uv run python -m eval.run -e e1 -n 30</code> 을 돌리면 이 화면이 채워진다.
          </p>
        </div>
      )}

      {e1 && (
        <section className="stack" style={{ gap: 8 }}>
          <h2>{INTRO.e1.title}</h2>
          <p className="muted small">{INTRO.e1.body}</p>
          <AbChart data={e1} flag="단장" />
        </section>
      )}
      {e2 && (
        <section className="stack" style={{ gap: 8 }}>
          <h2>{INTRO.e2.title}</h2>
          <p className="muted small">{INTRO.e2.body}</p>
          <AbChart data={e2} flag="적응" />
        </section>
      )}
      {e3 && (
        <section className="stack" style={{ gap: 8 }}>
          <h2>{INTRO.e3.title}</h2>
          <p className="muted small">{INTRO.e3.body}</p>
          <E3Chart data={e3} />
        </section>
      )}
    </main>
  );
}

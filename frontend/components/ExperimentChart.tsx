// 실험 차트 — 외부 라이브러리 없이 SVG. eval/ 의 출력 형태를 그대로 받는다.
// 색은 app/_ds/parchment.css 의 토큰만 쓴다.

export type Cell = {
  games: number;
  // 판 단위(missions 개) 비율과 계약 단위(games 개) 비율이 따로 온다 —
  // 마지막 판만 세면 앞판의 참사가 사라진다(QA 2026-09-09 V1).
  missions: number;
  clear_rate: number;
  home_rate: number;
  grade_share: Record<string, number>;
  avg_injured: number;
  avg_taken: number;
  avg_dead: number;
  win_rate: number;
  retreat_rate: number;
  loss_rate: number;
  draw_rate: number;
  survival_rate: number;
  abandon_rate: number;
  avg_turns: number;
  avg_peak_mission_calls: number;
  avg_contract_calls: number;
  max_calls: number;
  avg_plans: number;
  avg_deviations: number;
  avg_adaptations: number;
  // 적응이 상태를 바꿨는가, 그리고 그 지목을 보스가 실제로 때렸는가.
  // 승패가 안 움직일 때 어디가 끊겼는지 이 둘이 말한다(QA 2026-09-09 V5).
  adapt_no_change_rate: number;
  focus_follow_rate: number;
  action_share: Record<string, number>;
};

export type Paired = {
  axis: string;
  games: number;
  only_on_wins: number;
  only_off_wins: number;
  p_value: number;
};

export type AbResult = {
  experiment: "e1" | "e2";
  seeds: number;
  model: string;
  compositions: {
    key: string;
    label: string;
    lineup?: string[];
    on: Cell;
    off: Cell;
    paired?: Paired;
    paired_home?: Paired;
  }[];
};

export type E3Result = {
  experiment: "e3";
  seeds: number;
  model: string;
  axes: { axis: string; levels: ({ level: number } & Cell)[] }[];
};

const SEGMENTS: { key: keyof Cell; label: string; color: string }[] = [
  { key: "win_rate", label: "승리", color: "var(--color-ok)" },
  { key: "retreat_rate", label: "후퇴", color: "var(--color-warn)" },
  { key: "loss_rate", label: "패배", color: "var(--color-accent)" },
  { key: "draw_rate", label: "무승부", color: "var(--color-text-faint)" },
];

const W = 320;

function Bar({ cell }: { cell: Cell }) {
  let x = 0;
  return (
    <svg
      width="100%"
      height={12}
      viewBox={`0 0 ${W} 12`}
      preserveAspectRatio="none"
      role="img"
      aria-label="결과 분포"
      style={{ minWidth: 120, flex: 1 }}
    >
      <rect x={0} y={1} width={W} height={10} rx={3} fill="var(--color-surface-2)" />
      {SEGMENTS.map((s) => {
        const w = W * (cell[s.key] as number);
        const el = <rect key={s.key} x={x} y={1} width={w} height={10} fill={s.color} />;
        x += w;
        return el;
      })}
    </svg>
  );
}

function Legend({ extra }: { extra?: string }) {
  return (
    <div className="row small faint" style={{ gap: 10 }}>
      {SEGMENTS.map((s) => (
        <span key={s.key} className="row" style={{ gap: 4 }}>
          <span style={{ width: 9, height: 9, borderRadius: 2, background: s.color, display: "inline-block" }} />
          {s.label}
        </span>
      ))}
      {extra && <span>· {extra}</span>}
    </div>
  );
}

/** E1·E2 — 조합별 ON/OFF 비교. 같은 시드라 차이는 플래그 하나에서 온다. */
export default function AbChart({ data, flag }: { data: AbResult; flag: string }) {
  return (
    <div className="card" style={{ gap: 14 }}>
      <div className="row small faint" style={{ justifyContent: "space-between" }}>
        <span>
          조합당 시드 {data.seeds}개 · 모델 {data.model}
        </span>
        <Legend extra="막대는 판 단위 결과 · 「완주」는 계약을 끝까지 이룬 비율" />
      </div>
      {data.compositions.map((c) => {
        // 두 축을 함께 보여준다. 완주만 보면 감독이 목표를 포기하고 전원을
        // 데리고 나온 판이 벌점이 되어, 기획서 §8.1 의 "회복력" 주장을 스스로
        // 반증한다 — 「철수」는 벌점이 아니다(v3 §7.1b).
        const delta = c.on.clear_rate - c.off.clear_rate;
        const homeDelta = c.on.home_rate - c.off.home_rate;
        return (
          <div key={c.key} className="stack" style={{ gap: 4 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <b>{c.label}</b>
              <span className="row" style={{ gap: 6 }}>
                <span className={`tag ${delta > 0 ? "tag-ok" : delta < 0 ? "tag-accent" : ""}`}>
                  {flag} 켜면 완주 {delta > 0 ? "+" : ""}
                  {Math.round(delta * 100)}p
                </span>
                <span className={`tag ${homeDelta > 0 ? "tag-ok" : homeDelta < 0 ? "tag-accent" : ""}`}>
                  생환 {homeDelta > 0 ? "+" : ""}
                  {Math.round(homeDelta * 100)}p
                </span>
              </span>
            </div>
            {(["on", "off"] as const).map((side) => (
              <div key={side} className="row small" style={{ gap: 8 }}>
                <span className="faint" style={{ width: 52 }}>
                  {flag} {side === "on" ? "ON" : "OFF"}
                </span>
                <Bar cell={c[side]} />
                <span className="mono faint">
                  완주 {Math.round(c[side].clear_rate * 100)}% · 생환 {Math.round(c[side].home_rate * 100)}% · 판 승{" "}
                  {Math.round(c[side].win_rate * 100)}% · 끌려감 {c[side].avg_taken} · {c[side].avg_turns}턴
                </span>
              </div>
            ))}
            {data.experiment === "e2" && c.on.avg_adaptations > 0 && (
              <div className="small faint mono">
                적응 {c.on.avg_adaptations}회/판 · 무효 {Math.round(c.on.adapt_no_change_rate * 100)}% · 지목 명중{" "}
                {Math.round(c.on.focus_follow_rate * 100)}%
              </div>
            )}
            {(
              [
                ["완주", c.paired],
                ["생환", c.paired_home],
              ] as const
            ).map(([label, pr]) =>
              pr ? (
                <div key={label} className="small faint mono">
                  {label} 짝비교 · ON만 {pr.only_on_wins} / OFF만 {pr.only_off_wins} · p={pr.p_value.toFixed(4)}{" "}
                  {pr.p_value < 0.05 ? "(유의)" : "(잡음과 구별 안 됨)"}
                </div>
              ) : null,
            )}
          </div>
        );
      })}
    </div>
  );
}

const AXIS_KO: Record<string, string> = {
  risk: "위험 성향",
  sacrifice: "희생 수용도",
  cooperation: "협동 성향",
  planning: "계획 성향",
};

/** E3 — 성향 수치만 바꾼 같은 전투. 축이 실제로 행동을 가르는지 본다. */
export function E3Chart({ data }: { data: E3Result }) {
  return (
    <div className="card" style={{ gap: 14 }}>
      <div className="small faint">
        수준당 시드 {data.seeds}개 · 모델 {data.model} · 다른 축은 0 으로 고정
      </div>
      {data.axes.map((a) => (
        <div key={a.axis} className="stack" style={{ gap: 4 }}>
          <b>{AXIS_KO[a.axis] ?? a.axis}</b>
          <table className="kv">
            <thead>
              <tr>
                <th>수준</th>
                <th>이탈 / 판</th>
                <th>도망 비율</th>
                <th>방어 비율</th>
                <th>승률</th>
              </tr>
            </thead>
            <tbody>
              {a.levels.map((l) => (
                <tr key={l.level}>
                  <td className="mono">
                    {l.level > 0 ? "+" : ""}
                    {l.level}
                  </td>
                  <td className="mono">{l.avg_deviations}</td>
                  <td className="mono">{Math.round((l.action_share.FLEE ?? 0) * 100)}%</td>
                  <td className="mono">{Math.round((l.action_share.DEFEND ?? 0) * 100)}%</td>
                  <td className="mono">{Math.round(l.win_rate * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

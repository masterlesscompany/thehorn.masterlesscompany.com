import Link from "next/link";
import BackendDown from "@/components/BackendDown";
import { backendFetch, BackendDown as BackendDownError } from "@/lib/backend";
import { buildNameMap, GRADE_KO, OUTCOME_KO, type MissionResult, type TraceEvent } from "@/lib/trace";

export const dynamic = "force-dynamic";

export default async function ResultPage({ params }: { params: Promise<{ run: string }> }) {
  const { run } = await params;
  let events: TraceEvent[];
  try {
    const r = await backendFetch(`/runs/${encodeURIComponent(run)}`);
    if (r.status === 404) return <NotFound run={run} />;
    if (!r.ok) return <BackendDown detail={`GET /runs/${run} → ${r.status}`} />;
    events = ((await r.json()) as { events: TraceEvent[] }).events;
  } catch (e) {
    return <BackendDown detail={e instanceof BackendDownError ? e.message : String(e)} />;
  }
  const names = buildNameMap(events);
  const results = events.filter((e) => e.kind === "mission_end").map((e) => e.payload as unknown as MissionResult);
  const runEnd = events.find((e) => e.kind === "run_end");
  const abandons = events.filter((e) => e.kind === "abandon").length;
  const deviations = events.filter((e) => e.kind === "compliance" && e.payload.verdict === "deviate").length;
  const adapts = events.filter((e) => e.kind === "boss_adapt").length;
  const plans = events.filter((e) => e.kind === "plan").length;
  const fallbacks = events.filter((e) => e.kind === "decision" && (e.payload.model as { fallback?: boolean })?.fallback).length;

  return (
    <main className="page page-narrow stack" style={{ gap: 16 }}>
      <div className="card-kicker">결산</div>
      {/* 제목은 등급뿐이다. 호칭 문장은 아래에 한 번만 — 전에는 같은 IIFE 가
          h1 안팎에 두 벌 있어 `<p>` 가 제목 안에 박히고 등급이 둘째 줄로 밀렸다
          (QA 재검 2026-09-09, U2 수정 때 들어온 복붙 사고). */}
      <h1>
        {results.map((r) => (r.grade ? GRADE_KO[r.grade] : OUTCOME_KO[r.outcome])).join(" · ") ||
          "진행 중"}
      </h1>
      {(() => {
        const named = events.findLast((e) => e.kind === "boss_named");
        return named ? (
          <p className="small" style={{ margin: 0 }}>
            대원들은 그것을 <strong>「{String(named.payload.after)}」</strong>이라 부른다.
          </p>
        ) : null;
      })()}
      {results.map((r) => (
        <div key={r.no} className="card" style={{ gap: 8 }}>
          <div className="row">
            <span
              className={`tag ${
                r.grade === "full_success" || r.grade === "success"
                  ? "tag-ok"
                  : r.grade === "withdraw"
                    ? "tag-warn"
                    : "tag-accent"
              }`}
            >
              {r.grade ? GRADE_KO[r.grade] : OUTCOME_KO[r.outcome]}
            </span>
            <span className="small">{r.turns}턴</span>
            {r.abandoned && <span className="tag tag-outline">단장이 포기를 결정</span>}
            {events.some((e) => e.kind === "horn" && e.mission === r.no) && (
              <span className="tag tag-outline">단주가 뿔피리를 불었다</span>
            )}
            {r.grade === "withdraw" && (
              <span className="faint small">물러난 판은 실패가 아니다</span>
            )}
          </div>
          <table className="kv">
            <tbody>
              <tr>
                <th>생존</th>
                <td>{r.survivors.map((s) => names[s] ?? s).join(", ") || "없음"}</td>
              </tr>
              <tr>
                <th>빠져나옴</th>
                <td>{r.fled.map((s) => names[s] ?? s).join(", ") || "없음"}</td>
              </tr>
              <tr>
                <th>부상</th>
                <td>{(r.injured ?? []).map((s) => names[s] ?? s).join(", ") || "없음"}</td>
              </tr>
              <tr>
                <th>굴에 끌려감</th>
                <td>
                  {(r.taken ?? []).length === 0
                    ? "없음"
                    : (r.taken ?? []).map((s) => names[s] ?? s).join(", ")}
                </td>
              </tr>
              <tr>
                <th>사망</th>
                <td>{r.dead.map((s) => names[s] ?? s).join(", ") || "없음"}</td>
              </tr>
              {((r.recovery_paid ?? []).length > 0 || (r.recovery_unpaid ?? []).length > 0) && (
                <tr>
                  <th>회수 결정</th>
                  <td>
                    {(r.recovery_paid ?? []).length > 0 && (
                      <>되찾기로 함: {(r.recovery_paid ?? []).map((s) => names[s] ?? s).join(", ")} </>
                    )}
                    {(r.recovery_unpaid ?? []).length > 0 && (
                      <>굴에 두고 옴: {(r.recovery_unpaid ?? []).map((s) => names[s] ?? s).join(", ")}</>
                    )}
                    <div className="faint small">되찾기는 다음 계약에서 처리된다(B단계)</div>
                  </td>
                </tr>
              )}
              <tr>
                <th>모델 호출</th>
                <td>
                  {r.calls_used} (판당 상한 300)
                  {/* 폴백이 섞였으면 "모델이 판단했다" 가 아니다(QA 2026-09-09 V2). */}
                  {r.fallbacks ? <span className="faint"> · 폴백 {r.fallbacks}회</span> : null}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}
      <div className="card" style={{ gap: 6 }}>
        <div className="card-kicker">이 판에서 일어난 판단</div>
        <div className="row small">
          <span className="tag">작전 수립 {plans}회</span>
          <span className="tag">방침 이탈 {deviations}회</span>
          <span className="tag">보스 적응 {adapts}회</span>
          <span className="tag">포기 {abandons}회</span>
          {fallbacks > 0 && <span className="tag tag-warn">폴백 {fallbacks}회</span>}
        </div>
        {runEnd && <p className="small faint">전체 모델 호출 {String(runEnd.payload.calls_used)}회</p>}
      </div>
      <div className="row">
        <Link href={`/battle/${run}`} className="btn">
          트레이스 다시 보기
        </Link>
        <ReplayButton run={run} />
        <Link href="/roster" className="btn btn-primary">
          다시 편성 →
        </Link>
      </div>
    </main>
  );
}

function NotFound({ run }: { run: string }) {
  return (
    <main className="page page-narrow">
      <div className="card">
        <div className="card-title">그런 런이 없다</div>
        <p className="small faint mono">{run}</p>
        <Link href="/roster">로스터로</Link>
      </div>
    </main>
  );
}

async function ReplayButton({ run }: { run: string }) {
  async function replay() {
    "use server";
    const { redirect } = await import("next/navigation");
    const r = await backendFetch(`/runs/${encodeURIComponent(run)}/replay`, { method: "POST" });
    if (!r.ok) return;
    const data = (await r.json()) as { run_id: string };
    redirect(`/battle/${data.run_id}`);
  }
  return (
    <form action={replay}>
      <button className="btn" type="submit" title="녹화된 판단을 그대로 재생한다. 모델 호출 0.">
        리플레이 (모델 호출 0)
      </button>
    </form>
  );
}

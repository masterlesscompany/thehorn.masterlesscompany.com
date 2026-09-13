// 백엔드에 닿지 못했을 때의 첫 화면. 서버 예외를 그대로 뱉지 않는다(secu-agent 와 같은 원칙).
export default function BackendDown({ detail }: { detail?: string }) {
  return (
    <main className="page page-narrow">
      <div className="card" style={{ borderColor: "var(--color-accent)" }}>
        <div className="row">
          <span className="tag tag-outline">502</span>
          <span className="card-title">백엔드에 닿지 못했습니다</span>
        </div>
        <p className="small muted">
          런을 돌리는 서버가 꺼져 있습니다. 로컬이라면 <code>cd backend && uv run uvicorn apps.arena.adapter.inbound.api.v1.arena_router:create_app --factory --port 8000</code>{" "}
          으로 켜고 새로고침하세요.
        </p>
        {detail && <p className="small faint mono">{detail}</p>}
        <p className="small muted">
          <a href="/">진입 화면</a>은 백엔드 없이 열립니다.
        </p>
      </div>
    </main>
  );
}

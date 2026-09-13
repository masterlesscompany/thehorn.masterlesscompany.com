// BFF 공용 — 브라우저는 백엔드를 직접 부르지 않는다. 라우트 핸들러가 시크릿을 달고 부른다.
// secu-agent 와 같은 모양. 시크릿은 서버 환경변수에만 있고 브라우저로 내려가지 않는다.

const BASE = process.env.BACKEND_URL ?? "http://localhost:8000";
const SECRET = process.env.BACKEND_SHARED_SECRET ?? "";

export class BackendDown extends Error {
  constructor(msg: string) {
    super(msg);
    this.name = "BackendDown";
  }
}

export function backendHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  if (SECRET) h["X-Backend-Secret"] = SECRET;
  return h;
}

export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(`${BASE}${path}`, {
      ...init,
      headers: backendHeaders({ ...(init.headers as Record<string, string> | undefined) }),
      cache: "no-store",
    });
  } catch (e) {
    throw new BackendDown(`백엔드(${BASE})에 닿지 못했다: ${(e as Error).message}`);
  }
}

/** JSON 응답을 그대로 넘긴다. 백엔드의 상태 코드와 본문을 보존한다 — 422 메시지가 화면에 필요하다. */
export async function proxyJson(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    const r = await backendFetch(path, init);
    const text = await r.text();
    return new Response(text, { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch (e) {
    if (e instanceof BackendDown) return Response.json({ detail: e.message }, { status: 502 });
    throw e;
  }
}

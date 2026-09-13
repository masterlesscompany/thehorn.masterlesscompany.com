import { backendFetch, BackendDown } from "@/lib/backend";

// SSE 를 그대로 흘린다. 버퍼링하면 실시간이 아니다 — body 스트림을 통째로 넘긴다.
export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  try {
    const r = await backendFetch(`/runs/${encodeURIComponent(id)}/stream`);
    if (!r.ok || !r.body) {
      // EventSource 는 HTTP 오류를 data 없는 error 로만 알려줘서 화면이 이유를
      // 못 보여준다. 사유를 SSE 로 흘려 준다(QA 라운드 2).
      const detail = await r.text();
      const body = `event: error\ndata: ${JSON.stringify({ error: detail, status: r.status })}\n\nevent: done\ndata: {}\n\n`;
      return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
    }
    return new Response(r.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (e) {
    if (e instanceof BackendDown) return Response.json({ detail: e.message }, { status: 502 });
    throw e;
  }
}

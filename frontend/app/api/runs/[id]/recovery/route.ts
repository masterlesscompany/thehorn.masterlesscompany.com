import { proxyJson } from "@/lib/backend";

// 회수 결정 — 끌려간 대원을 다시 데려올 것인가(기획서 v3 §6.8).
export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const body = await req.text();
  return proxyJson(`/runs/${encodeURIComponent(id)}/recovery`, {
    method: "POST",
    body,
    headers: { "Content-Type": "application/json" },
  });
}

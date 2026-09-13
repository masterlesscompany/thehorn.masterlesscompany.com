import { proxyJson } from "@/lib/backend";

// 뿔피리 — 유저의 유일한 전투 중 개입(기획서 v3 §8.2). 계약 기간 3회.
export async function POST(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  return proxyJson(`/runs/${encodeURIComponent(id)}/horn`, { method: "POST" });
}

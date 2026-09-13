import { proxyJson } from "@/lib/backend";

export async function POST(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  return proxyJson(`/runs/${encodeURIComponent(id)}/replay`, { method: "POST" });
}

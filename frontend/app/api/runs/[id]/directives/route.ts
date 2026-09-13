import { proxyJson } from "@/lib/backend";

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const body = await req.text();
  return proxyJson(`/runs/${encodeURIComponent(id)}/directives`, {
    method: "POST",
    body,
    headers: { "Content-Type": "application/json" },
  });
}

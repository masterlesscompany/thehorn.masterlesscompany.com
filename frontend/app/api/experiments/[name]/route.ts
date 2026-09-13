import { proxyJson } from "@/lib/backend";

export async function GET(_req: Request, ctx: { params: Promise<{ name: string }> }) {
  const { name } = await ctx.params;
  return proxyJson(`/experiments/${encodeURIComponent(name)}`);
}

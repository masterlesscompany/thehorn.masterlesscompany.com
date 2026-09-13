import { proxyJson } from "@/lib/backend";

export async function POST(req: Request) {
  const body = await req.text();
  return proxyJson("/runs", { method: "POST", body, headers: { "Content-Type": "application/json" } });
}

export async function GET() {
  return proxyJson("/runs");
}

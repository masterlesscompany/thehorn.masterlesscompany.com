import BattleClient from "./BattleClient";

export const dynamic = "force-dynamic";

export default async function BattlePage({ params }: { params: Promise<{ run: string }> }) {
  const { run } = await params;
  return <BattleClient runId={run} />;
}

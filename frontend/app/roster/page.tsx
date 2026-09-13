import { backendFetch, BackendDown as BackendDownError } from "@/lib/backend";
import BackendDown from "@/components/BackendDown";
import RosterClient, { type PresetResponse } from "./RosterClient";

export const dynamic = "force-dynamic";

export default async function RosterPage() {
  let preset: PresetResponse;
  try {
    const r = await backendFetch("/roster/preset");
    if (!r.ok) return <BackendDown detail={`GET /roster/preset → ${r.status}`} />;
    preset = (await r.json()) as PresetResponse;
  } catch (e) {
    return <BackendDown detail={e instanceof BackendDownError ? e.message : String(e)} />;
  }
  return <RosterClient preset={preset} />;
}

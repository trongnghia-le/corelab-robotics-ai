import { getStore } from "@/lib/storage";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    checkLocalRequest(request);
    return new Response(JSON.stringify(getStore().export(), null, 2), {
      headers: {
        "Content-Type": "application/json",
        "Content-Disposition": 'attachment; filename="corelab-backup.json"',
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    return failure(e);
  }
}

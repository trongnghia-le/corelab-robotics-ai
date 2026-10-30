import { getStore } from "@/lib/storage";
import { allMastery, recommend } from "@/lib/engine";
import { lessonIds } from "@/lib/content";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    checkLocalRequest(request);
    const progress = getStore().read();
    const ids = lessonIds();
    return Response.json(
      {
        progress,
        mastery: allMastery(progress),
        recommendations: recommend(progress, ids),
        lessonIds: ids,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    return failure(e);
  }
}

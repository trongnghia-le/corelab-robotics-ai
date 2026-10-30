import { deriveWeaknesses } from "@/lib/weaknesses";
import { getStore } from "@/lib/storage";
import { allMastery, recommend } from "@/lib/engine";
import { lessonIds, getAssessmentCatalog } from "@/lib/content";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    checkLocalRequest(request);
    const progress = getStore().read();
    const ids = lessonIds();
    const weaknesses = deriveWeaknesses(progress, getAssessmentCatalog());
    return Response.json(
      {
        progress,
        weaknesses,
        mastery: allMastery(progress),
        recommendations: recommend(progress, ids, new Date(), weaknesses),
        lessonIds: ids,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    return failure(e);
  }
}

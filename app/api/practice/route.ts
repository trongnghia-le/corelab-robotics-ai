import { getStore } from "@/lib/storage";
import {
  getAssessmentCatalog,
  practiceSkills,
  publicAssessment,
} from "@/lib/content";
import { selectTargetedPlan } from "@/lib/weaknesses";
import { topicMap } from "@/lib/curriculum";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    checkLocalRequest(request);
    const params = new URL(request.url).searchParams;
    const topicId = params.get("topic") ?? "";
    if (!Object.hasOwn(topicMap, topicId)) throw new Error("Unknown topic");
    const skills = practiceSkills(topicId);
    const tag = params.get("skill") ?? skills[0]?.tag ?? "";
    const plan = selectTargetedPlan(
      getStore().read(),
      getAssessmentCatalog(),
      topicId,
      tag,
    );
    return Response.json(
      {
        skills,
        plan: { ...plan, assessment: publicAssessment(plan.assessment) },
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    return failure(e);
  }
}

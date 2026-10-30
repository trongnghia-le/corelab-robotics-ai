import { mediaFor } from "@/lib/media";
import {
  getLesson,
  getOverview,
  getAssessment,
  publicAssessment,
  practiceSkills,
} from "@/lib/content";
import { topicMap } from "@/lib/curriculum";
import { failure, checkLocalRequest } from "@/lib/http";
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    checkLocalRequest(request);
    const { id } = await params;
    if (!topicMap[id])
      return Response.json({ error: "Unknown topic" }, { status: 404 });
    return Response.json({
      lesson: getLesson(id),
      media: mediaFor(id),
      overview: getOverview(id),
      assessment: publicAssessment(getAssessment(id)),
      practiceSkills: practiceSkills(id),
    });
  } catch (e) {
    return failure(e);
  }
}

import { mediaFor } from "@/lib/media";
import { cookies } from "next/headers";
import { LANG_COOKIE, parseLang } from "@/lib/lang";
import {
  getLocalizedLesson,
  localizeAssessment,
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
    const lang = parseLang(
      new URL(request.url).searchParams.get("lang") ??
        (await cookies()).get(LANG_COOKIE)?.value,
    );
    return Response.json({
      lang,
      lesson: getLocalizedLesson(id, lang),
      media: mediaFor(id),
      overview: getOverview(id),
      assessment: publicAssessment(
        localizeAssessment(getAssessment(id), "assessments", lang),
      ),
      practiceSkills: practiceSkills(id),
    });
  } catch (e) {
    return failure(e);
  }
}

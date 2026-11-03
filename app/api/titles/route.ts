import { cookies } from "next/headers";
import { LANG_COOKIE, parseLang } from "@/lib/lang";
import { translatedTitles } from "@/lib/content";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    checkLocalRequest(request);
    const lang = parseLang(
      new URL(request.url).searchParams.get("lang") ??
        (await cookies()).get(LANG_COOKIE)?.value,
    );
    return Response.json(
      { lang, titles: lang === "vi" ? translatedTitles() : {} },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (e) {
    return failure(e);
  }
}

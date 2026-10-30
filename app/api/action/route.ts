import { getStore } from "@/lib/storage";
import { applyAction } from "@/lib/actions";
import { checkLocalRequest, failure } from "@/lib/http";
export const dynamic = "force-dynamic";
export async function POST(request: Request) {
  try {
    checkLocalRequest(request);
    if (!request.headers.get("content-type")?.includes("application/json"))
      throw new Error("Expected application/json");
    const body = await request.text();
    if (body.length > 8_000_000) throw new Error("Request too large");
    return Response.json(applyAction(getStore(), JSON.parse(body)));
  } catch (e) {
    return failure(e);
  }
}

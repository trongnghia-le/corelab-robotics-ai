import { validateBackup } from "@/lib/storage";
import { checkLocalRequest, failure } from "@/lib/http";
export async function POST(request: Request) {
  try {
    checkLocalRequest(request);
    const text = await request.text();
    if (text.length > 8_000_000) throw new Error("Backup too large");
    const p = validateBackup(JSON.parse(text));
    return Response.json({
      attempts: p.attempts.length,
      sessions: p.sessions.length,
      labs: p.labs.length,
    });
  } catch (e) {
    return failure(e);
  }
}

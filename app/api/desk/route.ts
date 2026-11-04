import { z } from "zod";
import { checkDeskRequest, failure } from "@/lib/http";
import {
  deleteDeskFile,
  readDesk,
  runDeskFile,
  writeDeskFile,
} from "@/lib/desk";
export const dynamic = "force-dynamic";
const topic = z.string().regex(/^[A-Z]+\d+$/);
const body = z.discriminatedUnion("op", [
  z.object({
    op: z.literal("write"),
    topic,
    file: z.string(),
    content: z.string(),
  }),
  z.object({ op: z.literal("delete"), topic, file: z.string() }),
  z.object({
    op: z.literal("run"),
    topic,
    file: z.string(),
    timeoutMs: z.number().int().optional(),
  }),
]);
export async function GET(request: Request) {
  try {
    checkDeskRequest(request);
    const id = topic.parse(new URL(request.url).searchParams.get("topic"));
    return Response.json(readDesk(id));
  } catch (e) {
    return failure(e);
  }
}
export async function POST(request: Request) {
  try {
    checkDeskRequest(request);
    if (!request.headers.get("content-type")?.includes("application/json"))
      throw new Error("Expected application/json");
    const text = await request.text();
    if (text.length > 1_000_000) throw new Error("Request too large");
    const b = body.parse(JSON.parse(text));
    if (b.op === "write") {
      writeDeskFile(b.topic, b.file, b.content);
      return Response.json({ ok: true });
    }
    if (b.op === "delete") {
      deleteDeskFile(b.topic, b.file);
      return Response.json({ ok: true });
    }
    return Response.json(await runDeskFile(b.topic, b.file, b.timeoutMs));
  } catch (e) {
    return failure(e);
  }
}

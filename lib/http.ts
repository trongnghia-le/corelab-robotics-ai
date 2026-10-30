import { NextResponse } from "next/server";
import { ZodError } from "zod";
export function failure(error: unknown) {
  const message =
    error instanceof ZodError
      ? error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ")
      : error instanceof Error
        ? error.message
        : "Unexpected error";
  return NextResponse.json({ error: message }, { status: 400 });
}
export function checkLocalRequest(request: Request) {
  const url = new URL(request.url);
  const header = request.headers.get("host");
  const host = header ? new URL(`http://${header}`).hostname : undefined;
  if (!host || !["127.0.0.1", "localhost", "[::1]"].includes(host))
    throw new Error("CoreLab accepts localhost requests only");
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(`${url.protocol}//${header}`).origin)
    throw new Error("Cross-origin request blocked");
  if (Number(request.headers.get("content-length") ?? 0) > 8_000_000)
    throw new Error("Request too large");
}

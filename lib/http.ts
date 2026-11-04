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
export function checkLocalRequest(
  request: Request,
  options: { maxBytes?: number } = {},
) {
  const url = new URL(request.url);
  const header = request.headers.get("host");
  const host = header ? new URL(`http://${header}`).hostname : undefined;
  if (!host || !["127.0.0.1", "localhost", "[::1]"].includes(host))
    throw new Error("CoreLab accepts localhost requests only");
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(`${url.protocol}//${header}`).origin)
    throw new Error("Cross-origin request blocked");
  if (
    Number(request.headers.get("content-length") ?? 0) >
    (options.maxBytes ?? 8_000_000)
  )
    throw new Error("Request too large");
}
/**
 * Stricter guard for the study desk, which can run code: the request must come
 * from a CoreLab page itself (same Origin, same-site fetch metadata) and carry
 * a custom header, which a cross-origin page cannot send without a preflight.
 */
export function checkDeskRequest(request: Request, maxBytes = 1_000_000) {
  checkLocalRequest(request, { maxBytes });
  if (request.method === "GET") return;
  if (!request.headers.get("origin"))
    throw new Error("Desk requests need an Origin header");
  if (request.headers.get("x-corelab-desk") !== "1")
    throw new Error("Missing desk header");
  const site = request.headers.get("sec-fetch-site");
  if (site && site !== "same-origin")
    throw new Error("Cross-site desk request blocked");
}

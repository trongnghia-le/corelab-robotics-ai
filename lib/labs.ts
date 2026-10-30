import { verify, createPublicKey } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
export const reportSchema = z
  .object({
    schema: z.literal("corelab-lab/1"),
    runner: z.literal("corelab-fixed-tests/1"),
    topicId: z.enum(["M02", "PY01"]),
    at: z.iso.datetime(),
    assistance: z.enum(["A0", "A1", "A2", "A3"]),
    sourceHash: z.string().regex(/^[a-f0-9]{64}$/),
    passed: z.literal(true),
    checks: z.number().int().min(6),
    publicKey: z.string().max(500),
    signature: z.string().max(500),
  })
  .strict();
export function validateLab(input: unknown, requireLocalKey = false) {
  const report = reportSchema.parse(input);
  const { signature, ...payload } = report;
  if (createPublicKey(report.publicKey).asymmetricKeyType !== "ed25519")
    throw new Error("Expected Ed25519 lab signature");
  if (requireLocalKey) {
    let localKey: string;
    try {
      localKey = readFileSync(
        path.join(process.cwd(), ".local", "lab-public.pem"),
        "utf8",
      );
    } catch {
      throw new Error(
        "Run the local fixed verifier before importing a lab report.",
      );
    }
    if (localKey !== report.publicKey)
      throw new Error(
        "Report is not signed by this workspace. Run the local verifier here.",
      );
  }
  const expected = report.topicId === "M02" ? 8 : 6;
  if (report.checks !== expected) throw new Error("Unexpected test contract");
  if (Date.parse(report.at) > Date.now() + 60000)
    throw new Error("Lab date is in the future");
  if (
    !verify(
      null,
      Buffer.from(JSON.stringify(payload)),
      report.publicKey,
      Buffer.from(signature, "base64"),
    )
  )
    throw new Error("Lab signature does not match");
  return report;
}

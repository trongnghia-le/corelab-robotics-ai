import { randomUUID } from "node:crypto";
import { z } from "zod";
import { attemptRow, type Attempt } from "./state";
import { strictJSON, V2Error } from "./contracts";
import { insert, nextSequence, type DB } from "./db";
export function attemptById(db: DB, id: string): Attempt {
  const row = db.prepare("SELECT * FROM v2_attempts WHERE id=?").get(id);
  if (!row) throw new V2Error("not_found", "Attempt not found", 404);
  return attemptRow.parse(row);
}
export function expose(
  db: DB,
  a: Attempt,
  kind: "issued" | "hint1" | "hint2" | "solution" | "feedback" | "kit_download",
  at = new Date().toISOString(),
) {
  if (Date.parse(at) < Date.parse(a.issued_at))
    throw new V2Error(
      "clock_regression",
      "The local clock moved backwards; no exposure was saved",
      409,
    );
  const fps = z.array(z.string()).parse(strictJSON(a.fingerprints));
  for (const fp of fps)
    insert(db, "v2_exposures", {
      id: randomUUID(),
      at,
      event_seq: nextSequence(db),
      fingerprint: fp,
      attempt_id: a.id,
      kind,
    });
}

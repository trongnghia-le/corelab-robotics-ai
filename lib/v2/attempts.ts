import { randomUUID } from "node:crypto";
import { z } from "zod";
import type { Store } from "../storage";
import {
  canonical,
  digest,
  id,
  level,
  purpose,
  strictJSON,
  V2Error,
} from "./contracts";
import {
  family,
  familyHash,
  gradeItem,
  itemFingerprint,
  itemSchema,
  normalizedAnswers,
  publicItem,
} from "./content";
import { attemptRow, type Attempt } from "./state";
import {
  checkpoint,
  insert,
  meta,
  needsAcknowledgement,
  nextSequence,
  revisionToken,
  setMeta,
  write,
  type DB,
} from "./db";

export const issueSchema = z
  .object({
    purpose,
    source: id.optional(),
    objectiveId: id.optional(),
    route: id.optional(),
    difficulty: z.number().int().min(1).max(5).optional(),
    resumeAttemptId: id.optional(),
  })
  .strict();
export const submitSchema = z
  .object({
    answers: z.record(z.string().regex(/^\d{1,2}$/), z.string().max(200)),
    declaredAssistance: level,
  })
  .strict();
export function attemptById(db: DB, id: string): Attempt {
  const row = db.prepare("SELECT * FROM v2_attempts WHERE id=?").get(id);
  if (!row) throw new V2Error("not_found", "Attempt not found", 404);
  return attemptRow.parse(row);
}
function sourceItem(a: Attempt) {
  const item = itemSchema.parse(strictJSON(a.instance_json)),
    f = family(a.source_id);
  const original = f?.items.find((i) => i.id === item.id);
  if (
    !f ||
    a.source_version !== f.version ||
    familyHash(f) !== a.source_hash ||
    !original ||
    digest(original) !== digest(item)
  )
    throw new V2Error(
      "source_unavailable",
      "Original source version is unavailable; retained history cannot be regraded.",
      503,
    );
  return { item, f };
}
function result(a: Attempt) {
  if (a.status !== "submitted" || !a.submission_json) return null;
  try {
    const { item } = sourceItem(a),
      answers = z
        .record(z.string(), z.string())
        .parse(strictJSON(a.submission_json));
    return {
      ...gradeItem(item, answers),
      effectiveAssistance: Math.max(a.observed_level, a.declared_level ?? 0),
      claim: "Practice only; independent content review pending",
    };
  } catch {
    return {
      unverifiable: true,
      claim: "Retained history; original source unavailable",
    };
  }
}
export function publicAttempt(db: DB, id: string) {
  const a = attemptById(db, id),
    item = itemSchema.parse(strictJSON(a.instance_json));
  const repeat =
    (
      db
        .prepare(
          "SELECT count(*) n FROM v2_exposures WHERE fingerprint=? AND event_seq<?",
        )
        .get(itemFingerprint(item), a.issued_seq) as { n: number }
    ).n > 0;
  return {
    id: a.id,
    purpose: a.purpose,
    status: a.status,
    source: a.source_id,
    sourceVersion: a.source_version,
    item: publicItem(item),
    observedAssistance: a.observed_level,
    issuedAt: a.issued_at,
    submittedAt: a.submitted_at,
    repeat,
    result: result(a),
    reviewStatus: "Independent review pending",
    verifiedI: "unavailable",
  };
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
export function issue(store: Store, input: unknown) {
  const request = issueSchema.parse(input);
  if (request.resumeAttemptId)
    return publicAttempt(store.db, request.resumeAttemptId);
  if (request.purpose !== "practice" && request.purpose !== "placement")
    throw new V2Error(
      "review_gate",
      "C/M verification and retention require independently reviewed forms. Verified I and transfer are unavailable.",
      503,
    );
  const f = family(request.source ?? "");
  if (!f)
    throw new V2Error("source_required", "Choose an authored exercise family");
  return write(store.db, () => {
    const available = f.items.filter(
      (i) =>
        (!request.route || i.route === request.route) &&
        (!request.objectiveId || i.objectiveId === request.objectiveId) &&
        (!request.difficulty || i.difficulty === request.difficulty),
    );
    if (!available.length)
      throw new V2Error(
        "not_available",
        "No authored item matches these choices",
        404,
      );
    const exposures = new Set(
      (
        store.db
          .prepare("SELECT DISTINCT fingerprint FROM v2_exposures")
          .all() as { fingerprint: string }[]
      ).map((e) => e.fingerprint),
    );
    const item =
      available.find((i) => !exposures.has(itemFingerprint(i))) ?? available[0];
    const at = new Date().toISOString();
    const a: Attempt = {
      id: randomUUID(),
      purpose: request.purpose,
      objective_refs: canonical([{ id: item.objectiveId, version: 1 }]),
      source_kind: "family",
      source_id: f.id,
      source_version: f.version,
      source_hash: familyHash(f),
      route: item.route,
      policy_version: 1,
      instance_json: canonical(item),
      fingerprints: canonical([itemFingerprint(item)]),
      status: "issued",
      issued_at: at,
      submitted_at: null,
      issued_seq: nextSequence(store.db),
      closed_seq: null,
      observed_level: 0,
      declared_level: null,
      submission_json: null,
      submission_hash: null,
      grade_json: null,
      history_epoch: Number(meta(store.db, "current_history_epoch")),
    };
    insert(store.db, "v2_attempts", a);
    expose(store.db, a, "issued", at);
    return publicAttempt(store.db, a.id);
  });
}
export function assist(store: Store, id: string, input: unknown) {
  const req = z
    .object({ level: level.refine((n) => n > 0) })
    .strict()
    .parse(input);
  return write(store.db, () => {
    const a = attemptById(store.db, id);
    if (a.status !== "issued")
      throw new V2Error(
        "attempt_closed",
        "This attempt is closed. Open another practice attempt for help.",
        409,
      );
    const { item } = sourceItem(a),
      next = Math.max(a.observed_level, req.level);
    store.db
      .prepare("UPDATE v2_attempts SET observed_level=? WHERE id=?")
      .run(next, id);
    expose(
      store.db,
      a,
      req.level === 1 ? "hint1" : req.level === 2 ? "hint2" : "solution",
    );
    return { level: next, content: item.hints[req.level - 1] };
  });
}
export function submit(store: Store, id: string, input: unknown) {
  const req = submitSchema.parse(input);
  return write(store.db, () => {
    const a = attemptById(store.db, id),
      { item } = sourceItem(a);
    const normalized = normalizedAnswers(item, req.answers);
    const submissionHash = digest({
      answers: normalized,
      declaredAssistance: req.declaredAssistance,
    });
    if (a.status === "submitted") {
      if (a.submission_hash !== submissionHash)
        throw new V2Error(
          "attempt_closed",
          "This attempt already has a different submission",
          409,
        );
      return publicAttempt(store.db, id);
    }
    const grade = gradeItem(item, req.answers),
      at = new Date().toISOString();
    if (Date.parse(at) < Date.parse(a.issued_at))
      throw new V2Error(
        "clock_regression",
        "The local clock moved backwards; retry when time is consistent",
        409,
      );
    store.db
      .prepare(
        "UPDATE v2_attempts SET status='submitted',submitted_at=?,closed_seq=?,declared_level=?,submission_json=?,submission_hash=?,grade_json=? WHERE id=?",
      )
      .run(
        at,
        nextSequence(store.db),
        req.declaredAssistance,
        canonical(req.answers),
        submissionHash,
        canonical(grade),
        id,
      );
    expose(store.db, a, "feedback", at);
    return publicAttempt(store.db, id);
  });
}
export function history(store: Store, limit = 25, cursor?: string) {
  const n = Math.min(50, Math.max(1, limit));
  const list = store.db
    .prepare(
      "SELECT id,issued_seq FROM v2_attempts WHERE issued_seq<? ORDER BY issued_seq DESC LIMIT ?",
    )
    .all(cursor ? Number(cursor) : Number.MAX_SAFE_INTEGER, n) as {
    id: string;
    issued_seq: number;
  }[];
  return {
    items: list.map((a) => publicAttempt(store.db, a.id)),
    nextCursor: list.length === n ? String(list.at(-1)!.issued_seq) : null,
  };
}
export function acknowledge(store: Store, token: string) {
  if (!needsAcknowledgement(store.db))
    return { acknowledged: true, token: revisionToken(store.db) };
  return write(
    store.db,
    () => {
      if (token !== revisionToken(store.db))
        throw new V2Error(
          "history_changed",
          "History changed again; refresh before acknowledging",
          409,
        );
      const id = (
        store.db
          .prepare("SELECT coalesce(max(id),0)+1 n FROM v2_history_epochs")
          .get() as { n: number }
      ).n;
      if (!Number.isSafeInteger(id)) throw new Error("Epoch counter exhausted");
      const cp = checkpoint(store.db);
      insert(store.db, "v2_history_epochs", {
        id,
        origin_workspace_id: meta(store.db, "workspace_id"),
        at: new Date().toISOString(),
        reason: "legacy_history_acknowledged",
        checkpoint_hash: cp.hash,
        checkpoint_count: cp.count,
      });
      setMeta(store.db, "current_history_epoch", id);
      setMeta(store.db, "history_pending", 0);
      return { acknowledged: true };
    },
    true,
  );
}

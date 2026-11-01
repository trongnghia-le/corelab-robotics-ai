import { randomUUID } from "node:crypto";
import { z } from "zod";
import type { Store } from "../storage";
import { canonical, digest, strictJSON, V2Error } from "./contracts";
import { attemptById, expose } from "./records";
import { insert, meta, nextSequence, write, type DB } from "./db";
import {
  attemptRow,
  evidenceRow,
  exposureRow,
  reviewRow,
  type Attempt,
  type Evidence,
  type Exposure,
  type Review,
} from "./state";
import {
  cmSources,
  compositeItem,
  fingerprintCandidates,
  freezeVariant,
  frozenSchema,
  gradeCM,
  independentlyReviewed,
  normalizeCM,
  resolveCM,
  type CMSource,
  type Frozen,
  type SourceResolver,
  type Variant,
} from "./assessments";
import { itemFingerprint } from "./content";
import {
  admitCM,
  fresh,
  initialReview,
  reviewToken,
  reviewTransition,
  sameGrade,
  type Decision,
} from "./policy";

export function knownCM(a: Attempt, resolve: SourceResolver = resolveCM) {
  const source = resolve(a.source_id, a.source_version);
  if (!source || source.hash !== a.source_hash || source.kind !== a.source_kind)
    throw new V2Error(
      "source_unavailable",
      "Original assessment contract unavailable",
      503,
    );
  const frozen = frozenSchema.parse(strictJSON(a.instance_json)),
    variant = source.variants.find((v) => v.id === frozen.variant);
  if (!variant)
    throw new V2Error(
      "source_unavailable",
      "Original variant unavailable",
      503,
    );
  const { basis: _basis, ...base } = frozen;
  if (canonical(base) !== canonical(freezeVariant(variant, source.kind)))
    throw new V2Error(
      "instance_mismatch",
      "Frozen instance does not match its immutable source",
    );
  return { source, variant, frozen };
}
export function savedSubmission(a: Attempt) {
  return z
    .object({
      answers: z.record(z.string(), z.string()),
      artifact: z.string().max(8000),
    })
    .strict()
    .parse(strictJSON(a.submission_json ?? "null"));
}
export function relevantExposures(db: DB, variant: Variant): Exposure[] {
  const fps = [
    ...new Set(variant.items.flatMap((c) => fingerprintCandidates(c.task))),
  ];
  if (!fps.length) return [];
  return db
    .prepare(
      "SELECT * FROM v2_exposures WHERE fingerprint IN (" +
        fps.map(() => "?").join(",") +
        ")",
    )
    .all(...fps)
    .map((e) => exposureRow.parse(e));
}
function references(variant: Variant) {
  return [
    ...new Map(
      variant.items.map((c) => [
        c.task.objectiveId + "/" + c.dimension,
        { id: c.task.objectiveId, version: 1, dimension: c.dimension },
      ]),
    ).values(),
  ];
}
export function publicCM(
  db: DB,
  a: Attempt,
  resolve: SourceResolver = resolveCM,
) {
  const frozen = frozenSchema.parse(strictJSON(a.instance_json));
  let result:
    | null
    | { unverifiable: true; claim: string }
    | (ReturnType<typeof gradeCM> & {
        artifact: string;
        effectiveAssistance: number;
        claim: string;
        scopes: {
          objective: string;
          dimension: string;
          outcome: string;
          reason: string;
        }[];
      }) = null;
  if (a.status === "submitted") {
    try {
      const { source, variant } = knownCM(a, resolve),
        saved = savedSubmission(a);
      const grade = gradeCM(variant, saved.answers);
      const matches = sameGrade(a.grade_json, grade);
      const decisions =
        a.purpose === "verify"
          ? admitCM(
              a,
              source,
              variant,
              saved.answers,
              relevantExposures(db, variant),
            )
          : [];
      const records = db
        .prepare(
          "SELECT * FROM v2_evidence WHERE attempt_id=? ORDER BY objective_id,dimension",
        )
        .all(a.id)
        .map((e) => evidenceRow.parse(e));
      result = {
        ...grade,
        artifact: saved.artifact,
        effectiveAssistance: Math.max(a.observed_level, a.declared_level ?? 0),
        claim:
          a.purpose === "verify"
            ? "Objective-scoped C/M check; never a whole-topic mastery award"
            : "Due review; retention is separate from unfamiliar transfer",
        scopes: records.map((e) => {
          const d = decisions.find(
            (d) =>
              d.objective === e.objective_id && d.dimension === e.dimension,
          );
          return {
            objective: e.objective_id,
            dimension: e.dimension,
            outcome: !independentlyReviewed(source)
              ? "unverifiable"
              : !matches
                ? "not_admitted"
                : (d?.outcome ?? e.outcome),
            reason: !matches
              ? "recompute_mismatch"
              : (d?.reason ?? e.reason_code),
          };
        }),
      };
    } catch {
      result = {
        unverifiable: true,
        claim: "Retained assessment history; source/policy unavailable",
      };
    }
  }
  return {
    id: a.id,
    purpose: a.purpose,
    status: a.status,
    source: a.source_id,
    sourceVersion: a.source_version,
    item: compositeItem(frozen, a.source_id),
    observedAssistance: a.observed_level,
    issuedAt: a.issued_at,
    submittedAt: a.submitted_at,
    repeat: false,
    result,
    reviewStatus: "Source-specific independent review required",
    verifiedI: "unavailable",
  };
}
export function issueCM(
  store: Store,
  req: {
    purpose: "verify" | "review";
    source?: string;
    objectiveId?: string;
    dimension?: "C" | "M";
  },
  resolve: SourceResolver = resolveCM,
) {
  return write(store.db, () => {
    const sources = req.source
      ? [resolve(req.source, 1)].filter((s): s is CMSource => !!s)
      : cmSources();
    const source = sources.find(
      (s) =>
        s.kind === (req.purpose === "verify" ? "form" : "review_pool") &&
        (!req.objectiveId ||
          s.variants.some((v) =>
            v.items.some((c) => c.task.objectiveId === req.objectiveId),
          )),
    );
    if (!source || !independentlyReviewed(source))
      throw new V2Error(
        "review_gate",
        "C/M verification and retention require independently reviewed forms; no assessment attempt was issued.",
        503,
      );
    let basis: Frozen["basis"], review: Review | undefined;
    if (req.purpose === "review") {
      if (!req.objectiveId || !req.dimension)
        throw new V2Error(
          "review_scope",
          "Choose an objective and C/M review dimension",
        );
      const row = store.db
        .prepare(
          "SELECT * FROM v2_objective_reviews WHERE objective_id=? AND objective_version=1 AND dimension=?",
        )
        .get(req.objectiveId, req.dimension);
      if (!row)
        throw new V2Error(
          "not_due",
          "No admitted review basis; use practice instead",
          409,
        );
      review = reviewRow.parse(row);
      if (review.state !== "active" || Date.parse(review.due) > Date.now())
        throw new V2Error(
          "not_due",
          "This review is not due; use practice without advancing retention",
          409,
        );
      basis = {
        evidenceId: review.basis_evidence_id,
        dimension: review.dimension,
        token: reviewToken(review),
      };
    }
    const variants = source.variants.filter(
      (v) =>
        req.purpose !== "review" ||
        v.items.every(
          (c) =>
            c.task.objectiveId === req.objectiveId &&
            c.dimension === req.dimension,
        ),
    );
    const temporary: Attempt = {
      id: "unissued",
      purpose: req.purpose,
      objective_refs: "[]",
      source_kind: source.kind,
      source_id: source.id,
      source_version: source.version,
      source_hash: source.hash,
      route: null,
      policy_version: 1,
      instance_json: "{}",
      fingerprints: "[]",
      status: "issued",
      issued_at: new Date().toISOString(),
      submitted_at: null,
      issued_seq: Number.MAX_SAFE_INTEGER,
      closed_seq: null,
      observed_level: 0,
      declared_level: null,
      submission_json: null,
      submission_hash: null,
      grade_json: null,
      history_epoch: 1,
    };
    const variant = variants.find((v) =>
      fresh(
        v,
        temporary,
        relevantExposures(store.db, v),
        Number.MAX_SAFE_INTEGER,
      ),
    );
    if (!variant)
      throw new V2Error(
        req.purpose === "review" ? "no_unexposed_review" : "no_unexposed_form",
        "No fresh reviewed variant remains. Repeated practice stays available.",
        409,
      );
    const frozen = {
      ...freezeVariant(variant, source.kind),
      ...(basis ? { basis } : {}),
    };
    if (Buffer.byteLength(canonical(frozen)) > 16384)
      throw new Error("Frozen form exceeds its byte budget");
    const a: Attempt = {
      ...temporary,
      id: randomUUID(),
      objective_refs: canonical(references(variant)),
      route: variant.id,
      instance_json: canonical(frozen),
      fingerprints: canonical(
        variant.items.map((c) => itemFingerprint(c.task)),
      ),
      issued_seq: nextSequence(store.db),
      history_epoch: Number(meta(store.db, "current_history_epoch")),
    };
    insert(store.db, "v2_attempts", a);
    expose(store.db, a, "issued", a.issued_at);
    return publicCM(store.db, a, resolve);
  });
}
export function assistCM(
  store: Store,
  id: string,
  level: number,
  resolve: SourceResolver = resolveCM,
) {
  return write(store.db, () => {
    const a = attemptById(store.db, id);
    if (a.status !== "issued")
      throw new V2Error("attempt_closed", "This attempt is closed", 409);
    const { variant } = knownCM(a, resolve),
      next = Math.max(a.observed_level, level);
    store.db
      .prepare("UPDATE v2_attempts SET observed_level=? WHERE id=?")
      .run(next, id);
    expose(
      store.db,
      a,
      level === 1 ? "hint1" : level === 2 ? "hint2" : "solution",
    );
    return {
      level: next,
      content: variant.items
        .map((c, i) => i + 1 + ". " + c.task.hints[level - 1])
        .join("\n\n"),
    };
  });
}
export function appendEvidence(
  db: DB,
  a: Attempt,
  d: Decision,
  dimension: Evidence["dimension"] = d.dimension,
) {
  const e: Evidence = {
    id: randomUUID(),
    at: a.submitted_at!,
    objective_id: d.objective,
    objective_version: 1,
    dimension,
    attempt_id: a.id,
    source_kind: a.source_kind === "form" ? "form" : "review_pool",
    source_id: a.source_id,
    source_version: a.source_version,
    source_hash: a.source_hash,
    pathway: "numerical",
    mode: "analytic",
    effective_assistance: Math.max(a.observed_level, a.declared_level ?? 3),
    outcome: d.outcome,
    reason_code: d.reason,
    recorded_json: canonical({
      attempt: a.id,
      at: a.submitted_at,
      objective: d.objective,
      dimension,
      outcome: d.outcome,
      reason: d.reason,
      source: {
        id: a.source_id,
        version: a.source_version,
        hash: a.source_hash,
      },
      assistance: Math.max(a.observed_level, a.declared_level ?? 3),
    }),
    validation_json: canonical({
      policy: 1,
      outcome: d.outcome,
      reason: d.reason,
    }),
    policy_version: 1,
    provenance: "local",
  };
  insert(db, "v2_evidence", e);
  return e;
}
function saveReview(db: DB, row: Review) {
  db.prepare(
    "DELETE FROM v2_objective_reviews WHERE objective_id=? AND objective_version=? AND dimension=?",
  ).run(row.objective_id, row.objective_version, row.dimension);
  insert(db, "v2_objective_reviews", row);
}
export function applyInitial(db: DB, e: Evidence) {
  if (e.outcome !== "admitted" || (e.dimension !== "C" && e.dimension !== "M"))
    return;
  const previous = db
    .prepare(
      "SELECT state FROM v2_objective_reviews WHERE objective_id=? AND objective_version=? AND dimension=?",
    )
    .get(e.objective_id, e.objective_version, e.dimension) as
    { state: string } | undefined;
  if (!previous || previous.state === "suspended")
    saveReview(db, initialReview({ ...e, dimension: e.dimension }));
}
export function closeReview(
  db: DB,
  a: Attempt,
  source: CMSource,
  variant: Variant,
  frozen: Frozen,
  answers: Record<string, string>,
  resolve: SourceResolver = resolveCM,
  emit: typeof appendEvidence = appendEvidence,
) {
  const check = variant.items[0],
    objective = check.task.objectiveId,
    dimension = check.dimension;
  const raw = db
    .prepare(
      "SELECT * FROM v2_objective_reviews WHERE objective_id=? AND objective_version=1 AND dimension=?",
    )
    .get(objective, dimension);
  const stale = () =>
    emit(
      db,
      a,
      { objective, dimension, outcome: "not_admitted", reason: "stale_review" },
      "retention",
    );
  if (!independentlyReviewed(source) || a.policy_version !== 1)
    return emit(
      db,
      a,
      {
        objective,
        dimension,
        outcome: "unverifiable",
        reason: "review_or_policy_unavailable",
      },
      "retention",
    );
  if (!raw || !frozen.basis || frozen.basis.dimension !== dimension)
    return stale();
  const review = reviewRow.parse(raw);
  const basisRaw = db
    .prepare("SELECT * FROM v2_evidence WHERE id=?")
    .get(review.basis_evidence_id);
  if (!basisRaw) return stale();
  const basis = evidenceRow.parse(basisRaw),
    basisSource = resolve(basis.source_id, basis.source_version);
  const basisAttempt = basis.attempt_id
    ? attemptById(db, basis.attempt_id)
    : null;
  if (
    review.state !== "active" ||
    reviewToken(review) !== frozen.basis.token ||
    review.basis_evidence_id !== frozen.basis.evidenceId ||
    basis.dimension !== dimension ||
    basis.objective_id !== objective ||
    basis.outcome !== "admitted" ||
    !basisAttempt?.closed_seq ||
    basisAttempt.closed_seq >= a.issued_seq ||
    !basisSource ||
    !independentlyReviewed(basisSource) ||
    basisSource.hash !== basis.source_hash ||
    Date.parse(a.issued_at) < Date.parse(basis.at) ||
    Date.parse(a.issued_at) < Date.parse(review.due)
  )
    return stale();
  const exposures = relevantExposures(db, variant);
  if (
    !fresh(variant, a, exposures, a.issued_seq) ||
    !fresh(variant, a, exposures, a.closed_seq!)
  )
    return emit(
      db,
      a,
      { objective, dimension, outcome: "not_admitted", reason: "exposed" },
      "retention",
    );
  const correct = gradeCM(variant, answers).passed,
    eligible =
      a.observed_level === 0 &&
      a.declared_level === 0 &&
      independentlyReviewed(source);
  saveReview(db, reviewTransition(review, a, correct, eligible));
  const delay = Date.parse(a.submitted_at!) - Date.parse(basis.at);
  if (!correct)
    return emit(
      db,
      a,
      { objective, dimension, outcome: "not_admitted", reason: "incorrect" },
      "retention",
    );
  if (eligible && delay >= 7 * 86400000)
    return emit(
      db,
      a,
      {
        objective,
        dimension,
        outcome: "admitted",
        reason: "delayed_fresh_retrieval",
      },
      "retention",
    );
  return null;
}
export function submitCM(
  store: Store,
  id: string,
  req: {
    answers: Record<string, string>;
    declaredAssistance: number;
    artifact?: string;
  },
  resolve: SourceResolver = resolveCM,
) {
  return write(store.db, () => {
    const a = attemptById(store.db, id),
      { source, variant, frozen } = knownCM(a, resolve);
    const normalized = normalizeCM(variant, req.answers),
      submissionHash = digest({
        answers: normalized,
        declaredAssistance: req.declaredAssistance,
        artifact: req.artifact ?? "",
      });
    if (a.status === "submitted") {
      if (a.submission_hash !== submissionHash)
        throw new V2Error(
          "attempt_closed",
          "This attempt already has a different submission",
          409,
        );
      return publicCM(store.db, a, resolve);
    }
    const grade = gradeCM(variant, req.answers),
      at = new Date().toISOString();
    if (Date.parse(at) < Date.parse(a.issued_at))
      throw new V2Error(
        "clock_regression",
        "Clock moved backwards; no assessment was closed",
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
        canonical({ answers: req.answers, artifact: req.artifact ?? "" }),
        submissionHash,
        canonical(grade),
        id,
      );
    const closed = attemptRow.parse(
      store.db.prepare("SELECT * FROM v2_attempts WHERE id=?").get(id),
    );
    if (a.purpose === "verify") {
      for (const d of admitCM(
        closed,
        source,
        variant,
        req.answers,
        relevantExposures(store.db, variant),
      ))
        applyInitial(store.db, appendEvidence(store.db, closed, d));
    } else if (a.purpose === "review")
      closeReview(
        store.db,
        closed,
        source,
        variant,
        frozen,
        req.answers,
        resolve,
      );
    expose(store.db, closed, "feedback", at);
    return publicCM(store.db, closed, resolve);
  });
}

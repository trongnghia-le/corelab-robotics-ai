import { z } from "zod";
import { id, level, purpose, time } from "./contracts";
import { COLLECTION_LIMITS } from "./budget";
const integer = z
  .number()
  .int()
  .nonnegative()
  .max(Number.MAX_SAFE_INTEGER - 1);
const version = integer.min(1);
const sha = z.string().regex(/^[a-f0-9]{64}$/);
const json = z.string().max(65536);
export const attemptRow = z
  .object({
    id,
    purpose,
    objective_refs: json,
    source_kind: z.enum(["family", "form", "review_pool", "kit"]),
    source_id: id,
    source_version: version,
    source_hash: sha,
    route: id.nullable(),
    policy_version: version,
    instance_json: json.max(16384),
    fingerprints: json,
    status: z.enum(["issued", "submitted"]),
    issued_at: time,
    submitted_at: time.nullable(),
    issued_seq: version,
    closed_seq: version.nullable(),
    observed_level: level,
    declared_level: level.nullable(),
    submission_json: json.max(16384).nullable(),
    submission_hash: sha.nullable(),
    grade_json: json.max(16384).nullable(),
    history_epoch: version,
  })
  .strict();
export type Attempt = z.infer<typeof attemptRow>;
export const exposureRow = z
  .object({
    id,
    at: time,
    event_seq: version,
    fingerprint: sha,
    attempt_id: id,
    kind: z.enum([
      "issued",
      "hint1",
      "hint2",
      "solution",
      "feedback",
      "kit_download",
    ]),
  })
  .strict();
export type Exposure = z.infer<typeof exposureRow>;
export const evidenceRow = z
  .object({
    id,
    at: time,
    objective_id: id,
    objective_version: version,
    dimension: z.enum(["C", "M", "I", "retention", "transfer_reviewed"]),
    attempt_id: id.nullable(),
    source_kind: z.enum(["form", "review_pool", "contract", "reviewer"]),
    source_id: id,
    source_version: version,
    source_hash: sha,
    pathway: id,
    mode: id,
    effective_assistance: level,
    outcome: z.enum(["admitted", "not_admitted", "unreviewed", "unverifiable"]),
    reason_code: z.string().max(200),
    recorded_json: json,
    validation_json: json.max(16384),
    policy_version: version,
    provenance: z.enum([
      "local",
      "restored_same_workspace",
      "restored_foreign",
    ]),
  })
  .strict();
export type Evidence = z.infer<typeof evidenceRow>;
export const reviewRow = z
  .object({
    objective_id: id,
    objective_version: version,
    dimension: z.enum(["C", "M"]),
    stage: integer.max(3),
    due: time,
    basis_evidence_id: id,
    last_ref_kind: z.enum(["evidence", "attempt"]),
    last_ref_id: id,
    state: z.enum(["active", "suspended"]),
  })
  .strict();
export type Review = z.infer<typeof reviewRow>;
export const epochRow = z
  .object({
    id: version,
    origin_workspace_id: z.uuid(),
    at: time,
    reason: z.string().max(200),
    checkpoint_hash: sha,
    checkpoint_count: integer,
  })
  .strict();
// Local restore provenance, not an exported learning epoch until another
// learning mutation occurs. Owner-approved D11 refinement, 2026-11-02.
export const deferredEpochRow = epochRow.omit({ id: true }).extend({
  reason: z.enum(["full_restore", "legacy_restore"]),
});
export const prefsRow = z
  .object({
    key: z.enum(["goal", "mode", "objective", "route"]),
    value_json: z.string().max(1000),
  })
  .strict();
export const backup3 = z
  .object({
    schema: z.literal("corelab-backup/3"),
    exportedAt: time,
    workspaceId: z.uuid(),
    sidecarSchemaVersion: z.literal(1),
    contentManifestHash: sha,
    legacy: z.unknown(),
    v2: z
      .object({
        attempts: z.array(attemptRow).max(COLLECTION_LIMITS.attempts),
        exposures: z.array(exposureRow).max(COLLECTION_LIMITS.exposures),
        evidence: z.array(evidenceRow).max(COLLECTION_LIMITS.evidence),
        objectiveReviews: z
          .array(reviewRow)
          .max(COLLECTION_LIMITS.objectiveReviews),
        historyEpochs: z.array(epochRow).max(COLLECTION_LIMITS.historyEpochs),
        prefs: z.array(prefsRow).max(COLLECTION_LIMITS.prefs),
      })
      .strict(),
    counts: z
      .object({
        attempts: integer,
        exposures: integer,
        evidence: integer,
        objectiveReviews: integer,
        historyEpochs: integer,
        prefs: integer,
      })
      .strict(),
    contentHash: sha,
  })
  .strict();
export type Backup = z.infer<typeof backup3>;

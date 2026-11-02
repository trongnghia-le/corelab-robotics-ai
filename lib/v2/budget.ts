import { bytes, canonical } from "./contracts";
import type { Backup, Evidence } from "./state";
export const LEARNING_TABLES = {
  attempts: "v2_attempts",
  exposures: "v2_exposures",
  evidence: "v2_evidence",
  objectiveReviews: "v2_objective_reviews",
  historyEpochs: "v2_history_epochs",
  prefs: "v2_prefs",
} as const;
export const COLLECTION_LIMITS = {
  attempts: 100000,
  exposures: 1000000,
  evidence: 500000,
  objectiveReviews: 10000,
  historyEpochs: 10000,
  prefs: 4,
} as const;
export type CollectionSizes = Record<
  keyof typeof LEARNING_TABLES,
  { bytes: number; count: number }
>;
export const PROJECTION_ROW_BYTES = 1024;
export const EVIDENCE_PROJECTION_FIELDS = [
  "outcome",
  "reason_code",
  "validation_json",
  "provenance",
] as const;
export function evidenceProjectionBytes(evidence: Evidence) {
  return bytes(
    Object.fromEntries(
      EVIDENCE_PROJECTION_FIELDS.map((key) => [key, evidence[key]]),
    ),
  );
}
export function projectedCollectionSizes(data: Backup["v2"]): CollectionSizes {
  const sizes = Object.fromEntries(
    Object.entries(data).map(([key, rows]) => [
      key,
      {
        count: rows.length,
        bytes: rows.reduce((sum, row) => sum + bytes(row), 0),
      },
    ]),
  ) as CollectionSizes;
  sizes.evidence.bytes += data.evidence.reduce(
    (sum, row) =>
      sum + Math.max(0, PROJECTION_ROW_BYTES - evidenceProjectionBytes(row)),
    0,
  );
  // A replay may rebuild a missing C/M review cache. Reserve the complete row
  // per scope, not another fixed allowance after each restore. Oversized inert
  // caches retain enough room for the longer suspended-state spelling.
  const key = (r: {
    objective_id: string;
    objective_version: number;
    dimension: string;
  }) => canonical([r.objective_id, r.objective_version, r.dimension]);
  const reviews = new Map(
    data.evidence
      .filter((e) => e.dimension === "C" || e.dimension === "M")
      .map((e) => [key(e), PROJECTION_ROW_BYTES]),
  );
  for (const review of data.objectiveReviews)
    reviews.set(
      key(review),
      Math.max(PROJECTION_ROW_BYTES, bytes({ ...review, state: "suspended" })),
    );
  sizes.objectiveReviews = {
    count: reviews.size,
    bytes: [...reviews.values()].reduce((sum, n) => sum + n, 0),
  };
  return sizes;
}
// Same complete wire envelope as backup/3, with fixed-length server-generated
// UUID, SHA and UTC fields. Arrays are replaced by their measured row bytes.
export function encodedBackupBytes(
  progressBytes: number,
  collections: CollectionSizes,
) {
  const at = "2000-01-01T00:00:00.000Z",
    sha = "0".repeat(64);
  const skeleton = {
    schema: "corelab-backup/3",
    exportedAt: at,
    workspaceId: "00000000-0000-4000-8000-000000000000",
    sidecarSchemaVersion: 1,
    contentManifestHash: sha,
    legacy: {
      schema: "corelab-backup/2",
      curriculumVersion: "1.0",
      exportedAt: at,
      progress: null,
    },
    v2: Object.fromEntries(Object.keys(LEARNING_TABLES).map((k) => [k, []])),
    counts: Object.fromEntries(
      Object.entries(collections).map(([key, v]) => [key, v.count]),
    ),
    contentHash: sha,
  };
  return (
    bytes(skeleton) -
    4 +
    progressBytes +
    Object.values(collections).reduce(
      (sum, c) => sum + c.bytes + Math.max(0, c.count - 1),
      0,
    )
  );
}
export const budgetBytes = (encodedBytes: number) => encodedBytes + 32768;

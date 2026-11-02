import { randomUUID } from "node:crypto";
import { z } from "zod";
import { validateBackup, type Store } from "../storage";
import {
  BACKUP_LIMIT,
  bytes,
  canonical,
  digest,
  strictJSON,
  V2Error,
} from "./contracts";
import { contentManifestHash } from "./content";
import { replay } from "./replay";
import { resolveCM, type SourceResolver } from "./assessments";
import { backup3, type Backup, type Exposure } from "./state";
import {
  LEARNING_TABLES,
  COLLECTION_LIMITS,
  budgetBytes,
  encodedBackupBytes,
  projectedCollectionSizes,
} from "./budget";
import {
  learningData,
  learningTables,
  insert,
  meta,
  revisionToken,
  rows,
  setMeta,
  write,
  type DB,
  type Row,
  ensureHeadroom,
  deferRestoreEpoch,
} from "./db";

const mapping = LEARNING_TABLES;
function counts(data: Backup["v2"]) {
  return Object.fromEntries(
    Object.entries(data).map(([k, v]) => [k, v.length]),
  ) as Backup["counts"];
}
function capture(store: Store): Backup {
  const data = learningData(store.db);
  const v2 = Object.fromEntries(
    Object.entries(mapping).map(([key, table]) => [key, data[table]]),
  ) as unknown as Backup["v2"];
  const core = {
    schema: "corelab-backup/3" as const,
    exportedAt: new Date().toISOString(),
    workspaceId: meta(store.db, "workspace_id"),
    sidecarSchemaVersion: 1 as const,
    contentManifestHash: contentManifestHash(),
    legacy: store.export(),
    v2,
    counts: counts(v2),
  };
  return { ...core, contentHash: digest(core) };
}
function limited(backup: Backup) {
  const sizes = projectedCollectionSizes(backup.v2);
  const size = budgetBytes(
    encodedBackupBytes(
      bytes((backup.legacy as { progress: unknown }).progress),
      sizes,
    ),
  );
  if (sizes.objectiveReviews.count > COLLECTION_LIMITS.objectiveReviews)
    throw new V2Error(
      "capacity_limit",
      "Restored objective review scopes exceed the supported count",
      503,
    );
  if (size > BACKUP_LIMIT)
    throw new V2Error(
      "backup_limit",
      "Full backup exceeds the supported budget. Use a current local recovery copy.",
      413,
    );
  return size;
}
export function exportBackup(store: Store) {
  store.db.exec("BEGIN");
  try {
    const data = capture(store);
    limited(data);
    validateFull(data);
    store.db.exec("COMMIT");
    return data;
  } catch (e) {
    if (store.db.isTransaction) store.db.exec("ROLLBACK");
    throw e;
  }
}
function unique<T>(items: T[], key: (v: T) => string | number) {
  const seen = new Set();
  for (const item of items) {
    const k = key(item);
    if (seen.has(k)) throw new Error("Duplicate record ID/key");
    seen.add(k);
  }
}
export function validateFull(input: unknown) {
  if (bytes(input) > BACKUP_LIMIT)
    throw new V2Error("backup_limit", "Backup exceeds supported bytes", 413);
  const b = backup3.parse(structuredClone(input)),
    { contentHash, ...core } = b;
  if (digest(core) !== contentHash)
    throw new Error("Backup content hash mismatch");
  if (canonical(counts(b.v2)) !== canonical(b.counts))
    throw new Error("Backup counts mismatch");
  const legacy = validateBackup(structuredClone(b.legacy));
  const aMap = new Map(b.v2.attempts.map((a) => [a.id, a])),
    eMap = new Map(b.v2.evidence.map((e) => [e.id, e]));
  const epochSet = new Set(b.v2.historyEpochs.map((e) => e.id));
  unique(b.v2.attempts, (a) => a.id);
  unique(b.v2.exposures, (e) => e.id);
  unique(b.v2.evidence, (e) => e.id);
  unique(
    b.v2.evidence.filter((e) => e.attempt_id !== null),
    (e) =>
      canonical([
        e.attempt_id,
        e.objective_id,
        e.objective_version,
        e.dimension,
      ]),
  );
  unique(b.v2.historyEpochs, (e) => e.id);
  unique(b.v2.prefs, (p) => p.key);
  unique(b.v2.objectiveReviews, (r) =>
    canonical([r.objective_id, r.objective_version, r.dimension]),
  );
  const seq = new Set<number>();
  const fingerprintsByAttempt = new Map<string, Set<string>>();
  const exposuresByAttempt = new Map<string, Exposure[]>();
  const addSeq = (s: number) => {
    if (s >= Number.MAX_SAFE_INTEGER - 1)
      throw new Error("No safe event sequence remains after restore");
    if (seq.has(s)) throw new Error("Duplicate event sequence");
    seq.add(s);
  };
  for (const a of b.v2.attempts) {
    addSeq(a.issued_seq);
    if (a.closed_seq !== null) addSeq(a.closed_seq);
    if (!epochSet.has(a.history_epoch))
      throw new Error("Missing history epoch");
    if (Date.parse(a.issued_at) > Date.now() + 60000)
      throw new Error("Attempt is in the future");
    if (a.status === "submitted") {
      if (
        !a.closed_seq ||
        a.closed_seq <= a.issued_seq ||
        !a.submitted_at ||
        Date.parse(a.submitted_at) < Date.parse(a.issued_at) ||
        Date.parse(a.submitted_at) > Date.now() + 60000 ||
        a.declared_level === null ||
        !a.submission_json ||
        !a.submission_hash ||
        !a.grade_json
      )
        throw new Error("Invalid closed attempt");
    } else if (
      a.closed_seq !== null ||
      a.submitted_at !== null ||
      a.declared_level !== null ||
      a.submission_json !== null ||
      a.submission_hash !== null ||
      a.grade_json !== null
    )
      throw new Error("Invalid open attempt");
    for (const field of [
      a.objective_refs,
      a.instance_json,
      a.fingerprints,
      a.submission_json,
      a.grade_json,
    ])
      if (field !== null) {
        strictJSON(field);
        if (Buffer.byteLength(field, "utf8") > 16384)
          throw new Error("Attempt field exceeds its byte budget");
      }
    const fps = z
      .array(z.string().regex(/^[a-f0-9]{64}$/))
      .min(1)
      .max(100)
      .parse(strictJSON(a.fingerprints));
    if (new Set(fps).size !== fps.length)
      throw new Error("Duplicate item fingerprint");
    fingerprintsByAttempt.set(a.id, new Set(fps));
    z.array(
      z
        .object({
          id: z.string().min(1).max(120),
          version: z.number().int().positive(),
          dimension: z.enum(["C", "M"]).optional(),
        })
        .strict(),
    )
      .min(1)
      .max(100)
      .parse(strictJSON(a.objective_refs));
  }
  for (const e of b.v2.exposures) {
    addSeq(e.event_seq);
    const a = aMap.get(e.attempt_id);
    if (
      !a ||
      e.event_seq <= a.issued_seq ||
      Date.parse(e.at) < Date.parse(a.issued_at)
    )
      throw new Error("Dangling or invalid exposure");
    if (!fingerprintsByAttempt.get(a.id)?.has(e.fingerprint))
      throw new Error("Exposure does not belong to the frozen instance");
    if (
      e.kind === "feedback" &&
      (a.closed_seq === null || e.event_seq <= a.closed_seq)
    )
      throw new Error("Feedback precedes close");
    const group = exposuresByAttempt.get(a.id) ?? [];
    group.push(e);
    exposuresByAttempt.set(a.id, group);
    if (["hint1", "hint2", "solution"].includes(e.kind)) {
      const observed = e.kind === "hint1" ? 1 : e.kind === "hint2" ? 2 : 3;
      if (
        a.observed_level < observed ||
        (a.closed_seq !== null && e.event_seq >= a.closed_seq)
      )
        throw new Error("Assistance contradicts attempt history");
    }
  }
  for (const a of b.v2.attempts) {
    const fps = fingerprintsByAttempt.get(a.id)!;
    for (const fp of fps)
      if (
        (exposuresByAttempt.get(a.id) ?? []).filter(
          (e) =>
            e.attempt_id === a.id &&
            e.fingerprint === fp &&
            e.kind === "issued" &&
            (a.closed_seq === null || e.event_seq < a.closed_seq),
        ).length !== 1
      )
        throw new Error("Missing issue exposure");
  }
  for (const e of b.v2.evidence) {
    if (e.attempt_id !== null && !aMap.has(e.attempt_id))
      throw new Error("Dangling evidence attempt");
    strictJSON(e.recorded_json);
    strictJSON(e.validation_json);
    if (
      Buffer.byteLength(e.recorded_json) > 65536 ||
      Buffer.byteLength(e.validation_json) > 16384
    )
      throw new Error("Evidence field exceeds its byte budget");
    if (e.attempt_id !== null) {
      const a = aMap.get(e.attempt_id)!;
      if (a.status !== "submitted" || !["verify", "review"].includes(a.purpose))
        throw new Error("Evidence references an ineligible attempt");
    }
  }
  for (const r of b.v2.objectiveReviews) {
    const basis = eMap.get(r.basis_evidence_id);
    if (
      !basis ||
      basis.objective_id !== r.objective_id ||
      basis.objective_version !== r.objective_version ||
      basis.dimension !== r.dimension
    )
      throw new Error("Invalid review basis");
    if (
      r.last_ref_kind === "attempt"
        ? !aMap.has(r.last_ref_id)
        : !eMap.has(r.last_ref_id)
    )
      throw new Error("Dangling review reference");
    if (r.last_ref_kind === "evidence") {
      const last = eMap.get(r.last_ref_id)!;
      if (
        last.objective_id !== r.objective_id ||
        last.objective_version !== r.objective_version ||
        last.dimension !== r.dimension
      )
        throw new Error(
          "Review evidence reference has the wrong objective scope",
        );
    } else {
      const last = aMap.get(r.last_ref_id)!;
      const refs = strictJSON(last.objective_refs) as {
        id: string;
        version: number;
        dimension?: string;
      }[];
      if (
        last.status !== "submitted" ||
        !["verify", "review"].includes(last.purpose) ||
        !refs.some(
          (ref) =>
            ref.id === r.objective_id &&
            ref.version === r.objective_version &&
            (!ref.dimension || ref.dimension === r.dimension),
        )
      )
        throw new Error(
          "Review attempt reference has the wrong objective scope",
        );
    }
  }
  if (b.v2.historyEpochs.some((e) => e.id >= Number.MAX_SAFE_INTEGER - 1))
    throw new Error("No safe history epoch remains after restore");
  for (const p of b.v2.prefs)
    z.string().max(200).parse(strictJSON(p.value_json));
  limited(b);
  return { backup: b, legacy };
}
function project(db: DB, b: Backup, resolve: SourceResolver = resolveCM) {
  return replay(
    b,
    b.workspaceId === meta(db, "workspace_id")
      ? "restored_same_workspace"
      : "restored_foreign",
    resolve,
  );
}
// Validate normalized legacy/provenance projections before confirmation. Empty
// restore epochs are deferred by the owner-approved D11 refinement; no existing
// epoch is removed and no new learning row is created merely by restoring.
function restoredCapacity(
  backup: Backup,
  legacy: ReturnType<typeof validateBackup>,
  v2: Backup["v2"],
) {
  const data = v2;
  for (const key of Object.keys(mapping) as (keyof typeof mapping)[])
    if (data[key].length > COLLECTION_LIMITS[key])
      throw new V2Error(
        "capacity_limit",
        "Restored profile exceeds the supported " +
          key +
          " count; use a current local recovery copy.",
        503,
      );
  limited({
    ...backup,
    legacy: { ...(backup.legacy as object), progress: legacy },
    v2: data,
    counts: counts(data),
  });
}
export function preview(
  store: Store,
  input: unknown,
  resolve: SourceResolver = resolveCM,
) {
  const schema = (input as { schema?: unknown })?.schema;
  if (schema !== "corelab-backup/3") {
    const p = validateBackup(structuredClone(input));
    const current = capture(store);
    restoredCapacity(current, p, current.v2);
    return {
      digest: digest(input),
      token: revisionToken(store.db),
      scope: "legacy-only",
      counts: {
        attempts: p.attempts.length,
        sessions: p.sessions.length,
        labs: p.labs.length,
      },
      warnings: [
        "Objective history stays in place. A full local snapshot is taken before replacement.",
      ],
    };
  }
  const { backup, legacy } = validateFull(input);
  const projection = project(store.db, backup, resolve);
  restoredCapacity(backup, legacy, projection);
  return {
    digest: digest(input),
    token: revisionToken(store.db),
    scope: "full",
    counts: backup.counts,
    evidence: {
      admitted: projection.evidence.filter((e) => e.outcome === "admitted")
        .length,
      notAdmitted: projection.evidence.filter(
        (e) => e.outcome === "not_admitted",
      ).length,
      unverifiable: projection.evidence.filter(
        (e) => e.outcome === "unverifiable",
      ).length,
    },
    warnings: [
      ...(backup.workspaceId !== meta(store.db, "workspace_id")
        ? [
            "Foreign origin; local identity and issuer trust will not be imported.",
          ]
        : []),
      ...(backup.v2.evidence.length
        ? [
            "Evidence is recomputed from recognized sources, assistance and historical exposure. Unknown or unreviewed claims remain inert.",
          ]
        : []),
    ],
  };
}
export function restore(
  store: Store,
  input: unknown,
  expected: { digest: string; token: string; confirm: boolean },
  fault?: (stage: "after_snapshot" | "after_replace" | "after_prune") => void,
  resolve: SourceResolver = resolveCM,
) {
  const checked = preview(store, input, resolve);
  if (!expected.confirm || expected.digest !== checked.digest)
    throw new V2Error(
      "confirmation_required",
      "Confirm the exact previewed backup",
      409,
    );
  const full =
    (input as { schema?: unknown })?.schema === "corelab-backup/3"
      ? validateFull(input)
      : null;
  const legacy = full?.legacy ?? validateBackup(structuredClone(input));
  const projected = full ? project(store.db, full.backup, resolve) : null;
  return write(
    store.db,
    () => {
      if (revisionToken(store.db) !== expected.token)
        throw new V2Error(
          "restore_preview_stale",
          "Local data changed; preview this backup again",
          409,
        );
      const before = capture(store),
        snapshot = canonical({
          backup: before,
          meta: rows(store.db, "v2_meta"),
          issuers: rows(store.db, "v2_issuers"),
        });
      if (Buffer.byteLength(snapshot) > 512 * 1024 * 1024)
        throw new Error(
          "Insufficient supported snapshot capacity; create a recovery copy first",
        );
      // Conservative preflight for snapshot, replacement and journal pages.
      // SQLite's own disk-full errors still roll back the entire transaction.
      ensureHeadroom(
        store.db,
        Buffer.byteLength(snapshot) * 3 + bytes(input) * 2 + 1048576,
      );
      insert(store.db, "v2_restore_snapshots", {
        id: randomUUID(),
        at: new Date().toISOString(),
        sidecar_version: 1,
        hash: digest(strictJSON(snapshot)),
        snapshot_json: snapshot,
      });
      fault?.("after_snapshot");
      if (full) {
        const data = projected!;
        for (const t of [...learningTables].reverse())
          store.db.exec("DELETE FROM " + t);
        for (const key of [
          "historyEpochs",
          "attempts",
          "exposures",
          "evidence",
          "objectiveReviews",
          "prefs",
        ] as const)
          for (const row of data[key])
            insert(store.db, mapping[key], row as Row);
      }
      store.db
        .prepare("UPDATE state SET json=? WHERE id=1")
        .run(JSON.stringify(legacy));
      const maxEpoch = (
        store.db
          .prepare("SELECT coalesce(max(id),0) n FROM v2_history_epochs")
          .get() as { n: number }
      ).n;
      if (
        !Number.isSafeInteger(maxEpoch) ||
        maxEpoch >= Number.MAX_SAFE_INTEGER
      )
        throw new Error("Epoch counter exhausted");
      setMeta(store.db, "current_history_epoch", Math.max(1, maxEpoch));
      deferRestoreEpoch(store.db, full ? "full_restore" : "legacy_restore");
      setMeta(store.db, "history_pending", 0);
      const maxSeq = (
        store.db
          .prepare(
            "SELECT max(n) n FROM (SELECT coalesce(max(issued_seq),0) n FROM v2_attempts UNION ALL SELECT coalesce(max(closed_seq),0) FROM v2_attempts UNION ALL SELECT coalesce(max(event_seq),0) FROM v2_exposures)",
          )
          .get() as { n: number }
      ).n;
      setMeta(store.db, "next_event_seq", maxSeq + 1);
      fault?.("after_replace");
      const snapshots = rows(store.db, "v2_restore_snapshots").sort(
        (a, b) =>
          String(a.at).localeCompare(String(b.at)) ||
          String(a.id).localeCompare(String(b.id)),
      );
      let total = snapshots.reduce(
        (n, s) => n + Buffer.byteLength(String(s.snapshot_json)),
        0,
      );
      while (snapshots.length > 5 || total > 512 * 1024 * 1024) {
        const old = snapshots.shift()!;
        total -= Buffer.byteLength(String(old.snapshot_json));
        store.db
          .prepare("DELETE FROM v2_restore_snapshots WHERE id=?")
          .run(old.id);
      }
      fault?.("after_prune");
      return { restored: true, scope: checked.scope };
    },
    { allowPending: true, learningMutation: false },
  );
}
export function snapshots(db: DB) {
  return db
    .prepare(
      "SELECT id,at,sidecar_version,hash FROM v2_restore_snapshots ORDER BY at DESC,id DESC",
    )
    .all();
}
export function snapshotBackup(db: DB, id: string) {
  const row = db
    .prepare("SELECT snapshot_json,hash FROM v2_restore_snapshots WHERE id=?")
    .get(id) as { snapshot_json: string; hash: string } | undefined;
  if (!row) throw new V2Error("not_found", "Snapshot not found", 404);
  const parsed = strictJSON(row.snapshot_json) as { backup: Backup };
  if (digest(parsed) !== row.hash)
    throw new Error("Snapshot integrity check failed");
  return parsed.backup;
}

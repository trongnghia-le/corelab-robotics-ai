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
import { catalog } from "./content";
import { backup3, type Backup, type Exposure } from "./state";
import {
  checkpoint,
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
} from "./db";

const mapping = {
  attempts: "v2_attempts",
  exposures: "v2_exposures",
  evidence: "v2_evidence",
  objectiveReviews: "v2_objective_reviews",
  historyEpochs: "v2_history_epochs",
  prefs: "v2_prefs",
} as const;
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
    contentManifestHash: catalog().hash,
    legacy: store.export(),
    v2,
    counts: counts(v2),
  };
  return { ...core, contentHash: digest(core) };
}
function limited(backup: Backup) {
  const size = bytes(backup) + 32768 + backup.v2.evidence.length * 512;
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
    store.db.exec("COMMIT");
    return data;
  } catch (e) {
    store.db.exec("ROLLBACK");
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
  unique(b.v2.historyEpochs, (e) => e.id);
  unique(b.v2.prefs, (p) => p.key);
  unique(b.v2.objectiveReviews, (r) =>
    canonical([r.objective_id, r.objective_version, r.dimension]),
  );
  const seq = new Set<number>();
  const fingerprintsByAttempt = new Map<string, Set<string>>();
  const exposuresByAttempt = new Map<string, Exposure[]>();
  const addSeq = (s: number) => {
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
  }
  for (const p of b.v2.prefs)
    z.string().max(200).parse(strictJSON(p.value_json));
  limited(b);
  return { backup: b, legacy };
}
// Until an approved assessment source/policy is installed, incoming claims stay
// inert. Numeric grade agreement is deliberately not a trust/admission shortcut.
function project(db: DB, b: Backup) {
  const provenance =
    b.workspaceId === meta(db, "workspace_id")
      ? "restored_same_workspace"
      : "restored_foreign";
  const data = structuredClone(b.v2);
  for (const e of data.evidence) {
    e.provenance = provenance;
    e.outcome = "unverifiable";
    e.reason_code = "source_or_review_unavailable";
    e.validation_json = canonical({
      policy: 1,
      status: "unverifiable",
      reason: e.reason_code,
    });
    if (e.attempt_id !== null) {
      const a = data.attempts.find((a) => a.id === e.attempt_id);
      if (
        !a ||
        a.status !== "submitted" ||
        !["verify", "review"].includes(a.purpose)
      )
        e.attempt_id = null;
    }
  }
  for (const r of data.objectiveReviews) r.state = "suspended";
  return data;
}
export function preview(store: Store, input: unknown) {
  const schema = (input as { schema?: unknown })?.schema;
  if (schema !== "corelab-backup/3") {
    const p = validateBackup(structuredClone(input));
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
  const { backup } = validateFull(input);
  return {
    digest: digest(input),
    token: revisionToken(store.db),
    scope: "full",
    counts: backup.counts,
    warnings: [
      ...(backup.workspaceId !== meta(store.db, "workspace_id")
        ? [
            "Foreign origin; local identity and issuer trust will not be imported.",
          ]
        : []),
      ...(backup.v2.evidence.length
        ? [
            "Evidence is retained as unverified history until its independent review and policy gates are available.",
          ]
        : []),
    ],
  };
}
export function restore(
  store: Store,
  input: unknown,
  expected: { digest: string; token: string; confirm: boolean },
  fault?: () => void,
) {
  const checked = preview(store, input);
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
      insert(store.db, "v2_restore_snapshots", {
        id: randomUUID(),
        at: new Date().toISOString(),
        sidecar_version: 1,
        hash: digest(strictJSON(snapshot)),
        snapshot_json: snapshot,
      });
      if (full) {
        const data = project(store.db, full.backup);
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
      const epoch = maxEpoch + 1;
      if (!Number.isSafeInteger(epoch))
        throw new Error("Epoch counter exhausted");
      const cp = checkpoint(store.db);
      insert(store.db, "v2_history_epochs", {
        id: epoch,
        at: new Date().toISOString(),
        origin_workspace_id: meta(store.db, "workspace_id"),
        reason: full ? "full_restore" : "legacy_restore",
        checkpoint_hash: cp.hash,
        checkpoint_count: cp.count,
      });
      setMeta(store.db, "current_history_epoch", epoch);
      setMeta(store.db, "history_pending", 0);
      const maxSeq = (
        store.db
          .prepare(
            "SELECT max(n) n FROM (SELECT coalesce(max(issued_seq),0) n FROM v2_attempts UNION ALL SELECT coalesce(max(closed_seq),0) FROM v2_attempts UNION ALL SELECT coalesce(max(event_seq),0) FROM v2_exposures)",
          )
          .get() as { n: number }
      ).n;
      setMeta(store.db, "next_event_seq", maxSeq + 1);
      fault?.();
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
      return { restored: true, scope: checked.scope };
    },
    true,
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

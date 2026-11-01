import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import { randomUUID } from "node:crypto";
import { mkdirSync, rmSync, statfsSync, statSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import { BACKUP_LIMIT, digest, enabled, hash, V2Error } from "./contracts";

export type DB = DatabaseSync;
export type Row = Record<string, SQLInputValue>;
export const learningTables = [
  "v2_history_epochs",
  "v2_attempts",
  "v2_exposures",
  "v2_evidence",
  "v2_objective_reviews",
  "v2_prefs",
] as const;
export const schemaSQL = `
CREATE TABLE v2_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE v2_migrations (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL);
CREATE TABLE v2_history_epochs (id INTEGER PRIMARY KEY, origin_workspace_id TEXT NOT NULL, at TEXT NOT NULL, reason TEXT NOT NULL, checkpoint_hash TEXT NOT NULL, checkpoint_count INTEGER NOT NULL);
CREATE TABLE v2_attempts (
 id TEXT PRIMARY KEY, purpose TEXT NOT NULL CHECK(purpose IN ('practice','placement','verify','review')),
 objective_refs TEXT NOT NULL, source_kind TEXT NOT NULL CHECK(source_kind IN ('family','form','review_pool','kit')),
 source_id TEXT NOT NULL, source_version INTEGER NOT NULL, source_hash TEXT NOT NULL, route TEXT,
 policy_version INTEGER NOT NULL, instance_json TEXT NOT NULL, fingerprints TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('issued','submitted')), issued_at TEXT NOT NULL, submitted_at TEXT,
 issued_seq INTEGER NOT NULL UNIQUE, closed_seq INTEGER UNIQUE,
 observed_level INTEGER NOT NULL CHECK(observed_level BETWEEN 0 AND 3), declared_level INTEGER CHECK(declared_level BETWEEN 0 AND 3),
 submission_json TEXT, submission_hash TEXT, grade_json TEXT,
 history_epoch INTEGER NOT NULL REFERENCES v2_history_epochs(id),
 CHECK((status='issued' AND closed_seq IS NULL AND submitted_at IS NULL) OR
       (status='submitted' AND closed_seq>issued_seq AND submitted_at IS NOT NULL AND declared_level IS NOT NULL))
);
CREATE INDEX v2_attempts_source ON v2_attempts(source_id,source_version,issued_at);
CREATE INDEX v2_attempts_status ON v2_attempts(status,purpose,issued_at,id);
CREATE TABLE v2_exposures (
 id TEXT PRIMARY KEY, at TEXT NOT NULL, event_seq INTEGER NOT NULL UNIQUE, fingerprint TEXT NOT NULL,
 attempt_id TEXT NOT NULL REFERENCES v2_attempts(id),
 kind TEXT NOT NULL CHECK(kind IN ('issued','hint1','hint2','solution','feedback','kit_download'))
);
CREATE INDEX v2_exposures_fp ON v2_exposures(fingerprint,event_seq);
CREATE TABLE v2_evidence (
 id TEXT PRIMARY KEY, at TEXT NOT NULL, objective_id TEXT NOT NULL, objective_version INTEGER NOT NULL,
 dimension TEXT NOT NULL CHECK(dimension IN ('C','M','I','retention','transfer_reviewed')),
 attempt_id TEXT REFERENCES v2_attempts(id),
 source_kind TEXT NOT NULL CHECK(source_kind IN ('form','review_pool','contract','reviewer')),
 source_id TEXT NOT NULL, source_version INTEGER NOT NULL, source_hash TEXT NOT NULL,
 pathway TEXT NOT NULL, mode TEXT NOT NULL, effective_assistance INTEGER NOT NULL CHECK(effective_assistance BETWEEN 0 AND 3),
 outcome TEXT NOT NULL CHECK(outcome IN ('admitted','not_admitted','unreviewed','unverifiable')),
 reason_code TEXT NOT NULL, recorded_json TEXT NOT NULL, validation_json TEXT NOT NULL, policy_version INTEGER NOT NULL,
 provenance TEXT NOT NULL CHECK(provenance IN ('local','restored_same_workspace','restored_foreign')),
 UNIQUE(attempt_id,objective_id,objective_version,dimension)
);
CREATE INDEX v2_evidence_obj ON v2_evidence(objective_id,objective_version,dimension,at);
CREATE TRIGGER v2_evidence_admission_guard BEFORE INSERT ON v2_evidence
WHEN (NEW.attempt_id IS NOT NULL AND NOT EXISTS(
 SELECT 1 FROM v2_attempts a WHERE a.id=NEW.attempt_id AND a.status='submitted' AND a.purpose IN ('verify','review')
)) OR (NEW.outcome='admitted' AND (
 NEW.dimension IN ('I','transfer_reviewed') OR NEW.attempt_id IS NULL OR NEW.effective_assistance<>0 OR NOT EXISTS(
 SELECT 1 FROM v2_attempts a WHERE a.id=NEW.attempt_id AND a.status='submitted'
 AND a.observed_level=0 AND a.declared_level=0
 AND a.source_id=NEW.source_id AND a.source_version=NEW.source_version AND a.source_hash=NEW.source_hash
 AND ((NEW.dimension IN ('C','M') AND a.purpose='verify' AND a.source_kind='form' AND NEW.source_kind='form')
 OR (NEW.dimension='retention' AND a.purpose='review' AND a.source_kind='review_pool' AND NEW.source_kind='review_pool'))
))) BEGIN SELECT RAISE(ABORT,'inadmissible evidence'); END;
CREATE TABLE v2_objective_reviews (
 objective_id TEXT NOT NULL, objective_version INTEGER NOT NULL, dimension TEXT NOT NULL CHECK(dimension IN ('C','M')),
 stage INTEGER NOT NULL CHECK(stage BETWEEN 0 AND 3), due TEXT NOT NULL,
 basis_evidence_id TEXT NOT NULL REFERENCES v2_evidence(id),
 last_ref_kind TEXT NOT NULL CHECK(last_ref_kind IN ('attempt','evidence')), last_ref_id TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('active','suspended')),
 PRIMARY KEY(objective_id,objective_version,dimension)
);
CREATE TABLE v2_prefs (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE v2_issuers (key_id TEXT PRIMARY KEY, public_key TEXT NOT NULL, status TEXT NOT NULL, enrolled_at TEXT NOT NULL);
CREATE TABLE v2_restore_snapshots (id TEXT PRIMARY KEY, at TEXT NOT NULL, sidecar_version INTEGER NOT NULL, hash TEXT NOT NULL, snapshot_json TEXT NOT NULL);
`;
export const migrationHash = hash(schemaSQL);
export function rows(db: DB, table: string): Row[] {
  if (
    ![
      ...learningTables,
      "v2_meta",
      "v2_migrations",
      "v2_issuers",
      "v2_restore_snapshots",
    ].includes(table)
  )
    throw new Error("Unknown table");
  return (
    db.prepare("SELECT * FROM " + table + " ORDER BY 1").all() as Row[]
  ).map((row) => ({ ...row }));
}
export function insert(db: DB, table: string, row: Row) {
  if (![...learningTables, "v2_restore_snapshots"].includes(table))
    throw new Error("Unknown table");
  if (Object.keys(row).some((k) => !/^[a-z_]+$/.test(k)))
    throw new Error("Invalid column");
  db.prepare(
    "INSERT INTO " +
      table +
      " (" +
      Object.keys(row).join(",") +
      ") VALUES (" +
      Object.keys(row)
        .map(() => "?")
        .join(",") +
      ")",
  ).run(...Object.values(row));
}
export function meta(db: DB, key: string): string {
  return (
    (
      db.prepare("SELECT value FROM v2_meta WHERE key=?").get(key) as
        { value: string } | undefined
    )?.value ?? ""
  );
}
export function setMeta(db: DB, key: string, value: string | number) {
  db.prepare(
    "INSERT INTO v2_meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
  ).run(key, String(value));
}
export function status(db: DB): "absent" | "supported" | "unsupported" {
  const tables = db
    .prepare(
      "SELECT name FROM sqlite_schema WHERE type='table' AND name GLOB 'v2_*'",
    )
    .all() as { name: string }[];
  if (!tables.length) return "absent";
  const expected = [
    "v2_meta",
    "v2_migrations",
    "v2_issuers",
    "v2_restore_snapshots",
    ...learningTables,
  ];
  if (
    tables.length !== expected.length ||
    expected.some((n) => !tables.some((t) => t.name === n))
  )
    return "unsupported";
  try {
    const record = db
      .prepare("SELECT checksum FROM v2_migrations WHERE version=1")
      .get() as { checksum: string } | undefined;
    const safeCounter = (key: string, minimum = 0) => {
      const raw = meta(db, key),
        n = Number(raw);
      return (
        /^(0|[1-9]\d*)$/.test(raw) &&
        Number.isSafeInteger(n) &&
        n >= minimum &&
        n < Number.MAX_SAFE_INTEGER
      );
    };
    if (
      !z.uuid().safeParse(meta(db, "workspace_id")).success ||
      !/^[a-f0-9]{64}$/.test(meta(db, "legacy_state_hash")) ||
      !z.iso.datetime().safeParse(meta(db, "legacy_checkpoint_at")).success ||
      !["0", "1"].includes(meta(db, "history_pending")) ||
      !safeCounter("current_history_epoch", 1) ||
      !safeCounter("next_event_seq", 1) ||
      !safeCounter("data_revision") ||
      !safeCounter("legacy_snapshot_count") ||
      (
        db.prepare("SELECT count(*) n FROM v2_migrations").get() as {
          n: number;
        }
      ).n !== 1
    )
      return "unsupported";
    return meta(db, "sidecar_schema_version") === "1" &&
      record?.checksum === migrationHash
      ? "supported"
      : "unsupported";
  } catch {
    return "unsupported";
  }
}
export function checkpoint(db: DB) {
  const row = db.prepare("SELECT json FROM state WHERE id=1").get() as {
    json: string;
  };
  const count = (
    db.prepare("SELECT count(*) n FROM restore_snapshots").get() as {
      n: number;
    }
  ).n;
  return { hash: hash(row.json), count };
}
export function refreshCheckpoint(db: DB) {
  const c = checkpoint(db);
  setMeta(db, "legacy_state_hash", c.hash);
  setMeta(db, "legacy_snapshot_count", c.count);
  setMeta(db, "legacy_checkpoint_at", new Date().toISOString());
}
export function needsAcknowledgement(db: DB) {
  const c = checkpoint(db);
  return (
    meta(db, "history_pending") === "1" ||
    c.hash !== meta(db, "legacy_state_hash") ||
    String(c.count) !== meta(db, "legacy_snapshot_count")
  );
}
export function revisionToken(db: DB) {
  return digest({
    revision: meta(db, "data_revision"),
    checkpoint: checkpoint(db),
    pending: meta(db, "history_pending"),
  });
}
export function nextSequence(db: DB) {
  const seq = Number(meta(db, "next_event_seq"));
  if (!Number.isSafeInteger(seq) || seq < 1 || seq >= Number.MAX_SAFE_INTEGER)
    throw new V2Error(
      "counter_limit",
      "Event counter exhausted; keep a recovery copy",
      503,
    );
  setMeta(db, "next_event_seq", seq + 1);
  return seq;
}
export function learningData(db: DB) {
  return Object.fromEntries(
    learningTables.map((t) => [t, rows(db, t)]),
  ) as Record<(typeof learningTables)[number], Row[]>;
}
export function checkCapacity(db: DB) {
  const legacyBytes = (
    db
      .prepare("SELECT length(CAST(json AS BLOB)) n FROM state WHERE id=1")
      .get() as { n: number }
  ).n;
  const count = (
    db.prepare("SELECT count(*) n FROM v2_attempts").get() as { n: number }
  ).n;
  let rowBytes = 0,
    evidenceCount = 0;
  // Aggregate exact JSON row bytes inside SQLite. Do not materialize every
  // historical artifact into JavaScript for each small learning mutation.
  for (const table of learningTables) {
    const columns = (
      db.prepare("PRAGMA table_info(" + table + ")").all() as { name: string }[]
    ).map((r) => r.name);
    if (columns.some((c) => !/^[a-z_]+$/.test(c)))
      throw new Error("Unsupported capacity schema");
    const args = columns.flatMap((c) => ["'" + c + "'", c]).join(",");
    const totals = db
      .prepare(
        "SELECT coalesce(sum(length(CAST(json_object(" +
          args +
          ") AS BLOB))),0) n,count(*) count FROM " +
          table,
      )
      .get() as { n: number; count: number };
    rowBytes += totals.n + totals.count; // comma allowance between rows
    if (table === "v2_evidence") evidenceCount = totals.count;
  }
  // Covers envelope, restore epoch, projected provenance and validation overhead.
  const size = legacyBytes + rowBytes + 32768 + evidenceCount * 512;
  if (!Number.isSafeInteger(size) || count > 100000 || size > BACKUP_LIMIT)
    throw new V2Error(
      "capacity_limit",
      "Profile exceeds the supported backup budget. No new data was saved. Make a current local recovery copy.",
      503,
    );
  return {
    bytes: size,
    limit: BACKUP_LIMIT,
    warning: size > BACKUP_LIMIT * 0.8,
  };
}
export function bump(db: DB) {
  const n = Number(meta(db, "data_revision"));
  if (!Number.isSafeInteger(n) || n >= Number.MAX_SAFE_INTEGER)
    throw new Error("Revision counter exhausted");
  setMeta(db, "data_revision", n + 1);
}
export function copyDatabase(db: DB) {
  const file = (
    db.prepare("PRAGMA database_list").all() as { name: string; file: string }[]
  ).find((x) => x.name === "main")?.file;
  if (!file) return null; // Explicit in-memory test databases have no durable file.
  ensureHeadroom(db, statSync(file).size * 2 + 1048576);
  const dir = path.join(path.dirname(file), "v2-recovery");
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const target = path.join(
    dir,
    new Date().toISOString().replace(/[^0-9TZ]/g, "") +
      "-" +
      randomUUID() +
      ".sqlite",
  );
  const reader = new DatabaseSync(file, { readOnly: true });
  try {
    reader.prepare("VACUUM INTO ?").run(target);
    const check = new DatabaseSync(target, { readOnly: true });
    try {
      const integrity = check.prepare("PRAGMA integrity_check").get() as {
        integrity_check: string;
      };
      if (integrity.integrity_check !== "ok")
        throw new Error("Recovery copy integrity check failed");
    } finally {
      check.close();
    }
    return target;
  } catch (e) {
    rmSync(target, { force: true });
    throw e;
  } finally {
    reader.close();
  }
}
export function initialize(db: DB) {
  const current = status(db);
  if (current === "supported") return;
  if (current !== "absent")
    throw new V2Error(
      "schema_unsupported",
      "V2 schema is unsupported. Legacy view remains available.",
      503,
    );
  db.exec("BEGIN IMMEDIATE");
  try {
    if (status(db) !== "absent")
      throw new Error("Schema changed during initialization");
    copyDatabase(db);
    db.exec(schemaSQL);
    const at = new Date().toISOString(),
      workspace = randomUUID();
    db.prepare("INSERT INTO v2_migrations VALUES (1,?,?)").run(
      migrationHash,
      at,
    );
    for (const [k, v] of Object.entries({
      sidecar_schema_version: "1",
      workspace_id: workspace,
      current_history_epoch: "1",
      data_revision: "0",
      next_event_seq: "1",
      history_pending: "0",
    }))
      setMeta(db, k, v);
    refreshCheckpoint(db);
    try {
      setMeta(db, "capacity_bytes", checkCapacity(db).bytes);
    } catch (e) {
      if (!(e instanceof V2Error) || e.code !== "capacity_limit") throw e;
      setMeta(db, "capacity_bytes", "over_limit");
    }
    const cp = checkpoint(db);
    insert(db, "v2_history_epochs", {
      id: 1,
      origin_workspace_id: workspace,
      at,
      reason: "initialized",
      checkpoint_hash: cp.hash,
      checkpoint_count: cp.count,
    });
    db.exec("COMMIT");
  } catch (e) {
    db.exec("ROLLBACK");
    throw e;
  }
}
export function ensureHeadroom(db: DB, required: number) {
  const file = (
    db.prepare("PRAGMA database_list").all() as { name: string; file: string }[]
  ).find((r) => r.name === "main")?.file;
  if (!file) return;
  if (!Number.isSafeInteger(required) || required < 0)
    throw new Error("Invalid recovery space budget");
  const disk = statfsSync(path.dirname(file), { bigint: true });
  if (disk.bavail * disk.bsize < BigInt(required))
    throw new V2Error(
      "disk_headroom",
      "Insufficient free disk space for safe recovery; no learning history was replaced",
      503,
    );
}
export function write<T>(db: DB, fn: () => T, allowPending = false): T {
  db.exec("BEGIN IMMEDIATE");
  try {
    if (status(db) !== "supported")
      throw new V2Error(
        "schema_unsupported",
        "Unsupported V2 schema; no V2 writes permitted",
        503,
      );
    if (!allowPending && needsAcknowledgement(db))
      throw new V2Error(
        "history_changed",
        "Legacy history changed outside V2. Acknowledge it before continuing.",
        409,
      );
    const changesBefore = (
      db.prepare("SELECT total_changes() n").get() as { n: number }
    ).n;
    const result = fn();
    if (status(db) !== "supported")
      throw new V2Error(
        "schema_unsupported",
        "Schema changed during the write; nothing was saved",
        503,
      );
    if (
      (db.prepare("SELECT total_changes() n").get() as { n: number }).n ===
      changesBefore
    ) {
      db.exec("COMMIT");
      return result;
    }
    const capacity = checkCapacity(db);
    setMeta(db, "capacity_bytes", capacity.bytes);
    refreshCheckpoint(db);
    bump(db);
    db.exec("COMMIT");
    return result;
  } catch (e) {
    db.exec("ROLLBACK");
    throw e;
  }
}
export function legacyPrecommit(
  db: DB,
  before: { hash: string; count: number },
) {
  if (!enabled() || status(db) !== "supported") return;
  if (
    before.hash !== meta(db, "legacy_state_hash") ||
    String(before.count) !== meta(db, "legacy_snapshot_count")
  )
    setMeta(db, "history_pending", "1");
  setMeta(db, "capacity_bytes", checkCapacity(db).bytes);
  refreshCheckpoint(db);
  bump(db);
}

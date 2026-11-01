import { afterEach, expect, it } from "vitest";
import { Store } from "../../lib/storage";
import {
  exportBackup,
  preview,
  restore,
  snapshots,
  snapshotBackup,
  validateFull,
} from "../../lib/v2/backup";
import {
  initialize,
  learningData,
  meta,
  revisionToken,
  write,
  checkCapacity,
} from "../../lib/v2/db";
import { issue, assist, submit } from "../../lib/v2/attempts";
import { digest, bytes } from "../../lib/v2/contracts";
import { family } from "../../lib/v2/content";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => stores.splice(0).forEach((s) => s.close()));
it("round-trips frozen attempts/exposure while keeping local identity and a full recovery snapshot", () => {
  const from = fresh(),
    a = issue(from, { purpose: "practice", source: "X10" });
  assist(from, a.id, { level: 2 });
  const b = exportBackup(from),
    to = fresh(),
    local = meta(to.db, "workspace_id"),
    before = to.read();
  const p = preview(to, b);
  restore(to, b, { ...p, confirm: true });
  expect(meta(to.db, "workspace_id")).toBe(local);
  expect(learningData(to.db).v2_attempts).toEqual(
    learningData(from.db).v2_attempts,
  );
  expect(learningData(to.db).v2_exposures).toEqual(
    learningData(from.db).v2_exposures,
  );
  expect(snapshots(to.db)).toHaveLength(1);
  const snapshot = snapshotBackup(
    to.db,
    String((snapshots(to.db)[0] as { id: string }).id),
  );
  expect((snapshot.legacy as { progress: unknown }).progress).toEqual(before);
  expect(validateFull(exportBackup(to)).backup.v2.historyEpochs).toHaveLength(
    2,
  );
});
it("keeps the SQLite row-byte capacity bound above a non-ASCII escaped full export", () => {
  const s = fresh(),
    a = issue(s, { purpose: "practice", source: "X01" }),
    item = family("X01")!.items.find((i) => i.id === a.item.id)!;
  submit(s, a.id, {
    answers: Object.fromEntries(
      item.fields.map((f, i) => [String(i), Number(f.answer).toFixed(9)]),
    ),
    declaredAssistance: 0,
    artifact: '😀\u0000\\"'.repeat(100),
  });
  const capacity = checkCapacity(s.db),
    actual = bytes(exportBackup(s));
  expect(capacity.bytes).toBeGreaterThan(actual);
  expect(capacity.bytes - actual).toBeLessThan(32768);
  expect(Number(meta(s.db, "capacity_bytes"))).toBe(capacity.bytes);
});
it("rejects stale preview and rolls back replacement and snapshot on injected failure", () => {
  const s = fresh(),
    b = exportBackup(s),
    p = preview(s, b);
  issue(s, { purpose: "practice", source: "X01" });
  expect(() => restore(s, b, { ...p, confirm: true })).toThrow("changed");
  const before = learningData(s.db),
    token = revisionToken(s.db),
    p2 = preview(s, b);
  expect(() =>
    restore(s, b, { ...p2, confirm: true }, () => {
      throw Error("injected");
    }),
  ).toThrow("injected");
  expect(learningData(s.db)).toEqual(before);
  expect(revisionToken(s.db)).toBe(token);
  expect(snapshots(s.db)).toHaveLength(0);
});
it("rejects duplicate IDs and contradictory counts/hash before live writes", () => {
  const s = fresh();
  issue(s, { purpose: "practice", source: "X01" });
  const b = exportBackup(s);
  b.v2.attempts.push({ ...b.v2.attempts[0] });
  b.counts.attempts++;
  const { contentHash: _old, ...core } = b;
  b.contentHash = digest(core);
  expect(() => validateFull(b)).toThrow("Duplicate");
  const bad = exportBackup(s);
  bad.counts.exposures = 0;
  const { contentHash: _hash, ...rest } = bad;
  bad.contentHash = digest(rest);
  expect(() => validateFull(bad)).toThrow("counts");
});
it("partial legacy restore preserves sidecar learning and creates an epoch", () => {
  const s = fresh();
  issue(s, { purpose: "practice", source: "X01" });
  const before = learningData(s.db).v2_attempts;
  const b = s.export(),
    p = preview(s, b);
  expect(p.scope).toBe("legacy-only");
  restore(s, b, { ...p, confirm: true });
  expect(learningData(s.db).v2_attempts).toEqual(before);
});
it("retains at most five nonrecursive snapshots and never exports issuer pins", () => {
  const s = fresh();
  for (let i = 0; i < 7; i++) {
    const b = exportBackup(s);
    restore(s, b, { ...preview(s, b), confirm: true });
  }
  expect(snapshots(s.db)).toHaveLength(5);
  const b = exportBackup(s);
  expect(JSON.stringify(b)).not.toContain("v2_restore_snapshots");
  expect(JSON.stringify(b)).not.toContain("v2_issuers");
});
it("foreign serialized I claims never gain pilot admission", () => {
  const s = fresh(),
    b = exportBackup(s);
  b.v2.evidence.push({
    id: "inert",
    at: new Date().toISOString(),
    objective_id: "R04.planar-fk",
    objective_version: 1,
    dimension: "I",
    attempt_id: null,
    source_kind: "contract",
    source_id: "L02.planar",
    source_version: 1,
    source_hash: "a".repeat(64),
    pathway: "numerical",
    mode: "analytic",
    effective_assistance: 0,
    outcome: "admitted",
    reason_code: "forged",
    recorded_json: '{"original":"preserve me"}',
    validation_json: "{}",
    policy_version: 1,
    provenance: "local",
  });
  b.counts.evidence = 1;
  const { contentHash: _old, ...core } = b;
  b.contentHash = digest(core);
  restore(s, b, { ...preview(s, b), confirm: true });
  expect(learningData(s.db).v2_evidence[0]).toMatchObject({
    outcome: "unverifiable",
    recorded_json: '{"original":"preserve me"}',
  });
  expect(() =>
    write(s.db, () =>
      s.db
        .prepare(
          "UPDATE v2_meta SET value='2' WHERE key='sidecar_schema_version'",
        )
        .run(),
    ),
  ).toThrow("Schema changed");
});

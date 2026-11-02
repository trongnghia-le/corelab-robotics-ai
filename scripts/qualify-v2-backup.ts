// Explicit high-memory qualification on new temporary databases only.
// No configured learner database, signing keys or network service is used.
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir, platform, arch, cpus } from "node:os";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { Store } from "../lib/storage";
import { issue, submit } from "../lib/v2/attempts";
import { initialize, checkCapacity, learningData, meta } from "../lib/v2/db";
import { exportBackup, preview, restore, snapshots } from "../lib/v2/backup";
import { BACKUP_LIMIT, bytes, digest } from "../lib/v2/contracts";
import type { Session } from "../lib/types";

if (process.argv.slice(2).join(" ") !== "--full-budget")
  throw new Error(
    "Explicit opt-in required: tsx scripts/qualify-v2-backup.ts --full-budget (large temporary files and several GiB of memory may be needed)",
  );
const directory = mkdtempSync(path.join(tmpdir(), "corelab backup λ-"));
const stores: Store[] = [];
const started = performance.now();
const stages: Record<string, number> = {};
function mark(label: string) {
  stages[label] = Math.round(performance.now() - started);
  console.log(JSON.stringify({ stage: label, elapsedMs: stages[label] }));
}
function fresh(name: string) {
  const store = new Store(path.join(directory, name + ".sqlite"));
  stores.push(store);
  initialize(store.db);
  return store;
}
try {
  process.env.CORELAB_V2 = "1";
  const source = fresh("source"),
    target = fresh("target");
  const a = issue(source, { purpose: "practice", source: "XB1" });
  submit(source, a.id, { answers: { "0": "0" }, declaredAssistance: 0 });
  const notes: Session[] = [],
    at = new Date().toISOString(),
    text = 'Original synthetic note: λ漢🙂\\"\n'.repeat(300);
  const base = checkCapacity(source.db).bytes;
  let projected = base;
  // Leave 256 KiB explicitly unused. This is a large-profile mechanism check,
  // not the still-open exact-boundary/epoch policy acceptance criterion.
  while (true) {
    const note: Session = {
      id: "synthetic-" + notes.length,
      topicId: "R04",
      at,
      kind: "note",
      minutes: 1,
      text,
    };
    const next = projected + bytes(note) + (notes.length ? 1 : 0);
    if (next > BACKUP_LIMIT - 262144) break;
    notes.push(note);
    projected = next;
  }
  source.update((p) => p.sessions.push(...notes));
  const capacityBefore = checkCapacity(source.db);
  assert.equal(capacityBefore.bytes, projected);
  const legacyHash = digest(source.read()),
    historyHash = digest(learningData(source.db).v2_attempts),
    exposureHash = digest(learningData(source.db).v2_exposures);
  mark("fixture-written");
  const backup = exportBackup(source),
    wireBytes = bytes(backup);
  assert(wireBytes > BACKUP_LIMIT * 0.99);
  mark("full-export-validated");
  const confirmation = preview(target, backup);
  mark("restore-preview-validated");
  const targetIdentity = meta(target.db, "workspace_id");
  restore(target, backup, { ...confirmation, confirm: true });
  mark("atomic-restore-committed");
  assert.equal(digest(target.read()), legacyHash);
  assert.equal(digest(learningData(target.db).v2_attempts), historyHash);
  assert.equal(digest(learningData(target.db).v2_exposures), exposureHash);
  assert.equal(meta(target.db, "workspace_id"), targetIdentity);
  assert.equal(snapshots(target.db).length, 1);
  const restoredExport = exportBackup(target);
  assert.equal(digest(restoredExport.v2.attempts), historyHash);
  assert.equal(digest(restoredExport.v2.exposures), exposureHash);
  assert.equal(
    restoredExport.v2.historyEpochs.length,
    backup.v2.historyEpochs.length,
  );
  mark("restored-export-validated");
  console.log(
    JSON.stringify({
      passed: true,
      fixture:
        "Disk-backed non-ASCII legacy notes plus a closed V2 practice attempt; 256 KiB unused headroom",
      node: process.version,
      os: platform(),
      arch: arch(),
      cpu: cpus()[0]?.model,
      notes: notes.length,
      wireBytes,
      capacityBefore,
      capacityAfter: checkCapacity(target.db),
      stagesMs: stages,
      maxRssBytes: process.resourceUsage().maxRSS * 1024,
      limit:
        "One Linux mechanism run, not exact-boundary, reviewed-evidence projection, repeated-restore or other-OS qualification",
    }),
  );
} finally {
  stores.reverse().forEach((store) => store.close());
  rmSync(directory, { recursive: true, force: true });
}

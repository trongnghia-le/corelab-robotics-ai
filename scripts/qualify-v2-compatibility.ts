// Explicit historical-source probe. Does not open the configured learner DB.
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import path from "node:path";
import { tmpdir } from "node:os";
import assert from "node:assert/strict";
import { Store } from "../lib/storage";
import {
  initialize,
  needsAcknowledgement,
  revisionToken,
  learningData,
  status,
} from "../lib/v2/db";
import { issue, acknowledge } from "../lib/v2/attempts";
const baseline = process.argv[2];
if (!baseline)
  throw new Error(
    "Usage: tsx scripts/qualify-v2-compatibility.ts /absolute/trusted/baseline/source",
  );
const dir = mkdtempSync(path.join(tmpdir(), "corelab-real-v1-")),
  file = path.join(dir, "test.sqlite");
let store = new Store(file);
try {
  initialize(store.db);
  issue(store, { purpose: "practice", source: "X01" });
  const original = learningData(store.db),
    legacy = store.read();
  store.close();
  const run = spawnSync(
    process.execPath,
    [
      "--import",
      "tsx",
      "tests/fixtures/legacy-reopen.ts",
      path.resolve(baseline),
      file,
    ],
    { encoding: "utf8", timeout: 15000, shell: false, windowsHide: true },
  );
  assert.equal(run.status, 0, run.stderr);
  const old = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1)!);
  assert.equal(old.restored, true);
  assert.equal(old.sidecarRows, 1);
  assert.equal(old.version, 2);
  store = new Store(file);
  assert.equal(status(store.db), "supported");
  assert.deepEqual(store.read(), legacy);
  assert.deepEqual(learningData(store.db), original);
  assert.equal(needsAcknowledgement(store.db), true);
  acknowledge(store, revisionToken(store.db));
  assert.equal(needsAcknowledgement(store.db), false);
  issue(store, { purpose: "practice", source: "X04" });
  assert.equal(learningData(store.db).v2_attempts.length, 2);
  console.log(
    JSON.stringify({
      passed: true,
      baseline: path.resolve(baseline),
      probe:
        "V2 → actual V1 open/edit/restore → V2 acknowledgement and new practice",
      legacyProgressPreserved: true,
      sidecarRowsPreserved: true,
      userVersion: 2,
      node: process.version,
    }),
  );
} finally {
  try {
    store.close();
  } catch {}
  rmSync(dir, { recursive: true, force: true });
}

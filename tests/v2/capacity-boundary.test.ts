import { afterEach, expect, it, vi } from "vitest";
vi.mock("../../lib/v2/contracts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/v2/contracts")>()),
  BACKUP_LIMIT: 131072,
}));
import { Store } from "../../lib/storage";
import { initialize, checkCapacity, insert, write } from "../../lib/v2/db";
import { exportBackup, preview, restore } from "../../lib/v2/backup";
import { BACKUP_LIMIT } from "../../lib/v2/contracts";
import { cmSources, type SourceResolver } from "../../lib/v2/assessments";
import { issueCM, submitCM } from "../../lib/v2/verification";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => {
  stores.splice(0).forEach((s) => s.close());
  vi.unstubAllEnvs();
});
function fillToBoundary(s: Store) {
  const note = (id: string, text: string) => ({
    id,
    topicId: "M01",
    at: new Date().toISOString(),
    kind: "note" as const,
    text,
    minutes: 1,
  });
  while (checkCapacity(s.db).bytes < BACKUP_LIMIT - 11000)
    s.update((p) => {
      p.sessions.push(note("fixed-" + p.sessions.length, "a".repeat(10000)));
    });
  s.update((p) => {
    p.sessions.push(note("fill", ""));
  });
  let low = 0,
    high = 20000;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    try {
      s.update((p) => {
        p.sessions.at(-1)!.text = "b".repeat(mid);
      });
      low = mid;
    } catch (e) {
      expect((e as Error).message).toContain("budget");
      high = mid - 1;
    }
  }
  s.update((p) => {
    p.sessions.at(-1)!.text = "b".repeat(low);
  });
  expect(checkCapacity(s.db).bytes).toBe(BACKUP_LIMIT);
}
it.each([false, true])(
  "keeps the last accepted bounded write exportable and restorable at a reduced test budget (inert evidence: %s)",
  (withEvidence) => {
    vi.stubEnv("CORELAB_V2", "1");
    const s = fresh();
    if (withEvidence)
      write(s.db, () =>
        insert(s.db, "v2_evidence", {
          id: "retained-claim",
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
          outcome: "unverifiable",
          reason_code: "unknown",
          recorded_json: '{"original":"untouched"}',
          validation_json: "{}",
          policy_version: 1,
          provenance: "local",
        }),
      );
    fillToBoundary(s);
    const backup = exportBackup(s),
      target = fresh(),
      p = preview(target, backup);
    restore(target, backup, {
      digest: p.digest,
      token: p.token,
      confirm: true,
    });
    expect(target.read()).toEqual(s.read());
    for (let i = 0; i < 4; i++) {
      const next = exportBackup(target),
        again = preview(target, next);
      restore(target, next, { ...again, confirm: true });
    }
    expect(exportBackup(target).v2.historyEpochs).toEqual(
      backup.v2.historyEpochs,
    );
  },
);

it("can rebuild missing review caches at the last accepted write boundary without consuming another projection allowance", () => {
  vi.stubEnv("CORELAB_V2", "1");
  const s = fresh(),
    sources = structuredClone(cmSources()).map((source) => ({
      ...source,
      review: {
        status: "approved" as const,
        reviewer: "Synthetic capacity fixture, not independent sign-off",
        date: "2020-01-01",
      },
    }));
  const resolve: SourceResolver = (id, version) =>
    sources.find((source) => source.id === id && source.version === version);
  const source = resolve("F-R04", 1)!,
    opened = issueCM(s, { purpose: "verify", source: source.id }, resolve);
  const variant = source.variants.find((v) => v.id === opened.item.route)!;
  const answers = Object.fromEntries(
    variant.items.flatMap((item, i) =>
      item.task.fields.map((f, j) => [
        i + "." + j,
        f.kind === "choice" ? f.answer : Number(f.answer).toFixed(9),
      ]),
    ),
  );
  submitCM(s, opened.id, { answers, declaredAssistance: 0 }, resolve);
  write(s.db, () => s.db.exec("DELETE FROM v2_objective_reviews"));
  fillToBoundary(s);
  const backup = exportBackup(s),
    target = fresh();
  const p = preview(target, backup, resolve);
  restore(target, backup, { ...p, confirm: true }, undefined, resolve);
  expect(checkCapacity(target.db).bytes).toBe(BACKUP_LIMIT);
  expect(exportBackup(target).v2.objectiveReviews).toHaveLength(2);
  expect(
    exportBackup(target).v2.evidence.every((e) => e.outcome === "admitted"),
  ).toBe(true);
  const before = checkCapacity(target.db).bytes;
  const again = exportBackup(target);
  restore(
    target,
    again,
    { ...preview(target, again, resolve), confirm: true },
    undefined,
    resolve,
  );
  expect(checkCapacity(target.db).bytes).toBe(before);
});

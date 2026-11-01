import { afterEach, expect, it, vi } from "vitest";
import { Store } from "../../lib/storage";
import { initialize, learningData } from "../../lib/v2/db";
import {
  cmSources,
  fingerprintCandidates,
  gradeCM,
  independentlyReviewed,
  type CMSource,
  type SourceResolver,
} from "../../lib/v2/assessments";
import { itemFingerprint, catalog } from "../../lib/v2/content";
import {
  assistCM,
  issueCM,
  submitCM,
  knownCM,
} from "../../lib/v2/verification";
import { attemptById } from "../../lib/v2/records";
import { admitCM } from "../../lib/v2/policy";
import type { Exposure } from "../../lib/v2/state";
import { exportBackup, preview, restore } from "../../lib/v2/backup";
import { canonical, digest } from "../../lib/v2/contracts";

// Synthetic approvals exercise the engine without modifying release metadata.
// These fixtures are NOT independent reviewer sign-off.
function resolver(): SourceResolver {
  const sources = structuredClone(cmSources()).map((s) => ({
    ...s,
    review: {
      status: "approved" as const,
      reviewer: "Synthetic test fixture (not an independent review)",
      date: "2020-01-01",
    },
  }));
  return (id, version) =>
    sources.find((s) => s.id === id && s.version === version);
}
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => {
  stores.splice(0).forEach((s) => s.close());
  vi.useRealTimers();
});
function answers(source: CMSource, variantId: string) {
  return Object.fromEntries(
    source.variants
      .find((v) => v.id === variantId)!
      .items.flatMap((c, i) =>
        c.task.fields.map((f, j) => [
          i + "." + j,
          f.kind === "choice" ? f.answer : Number(f.answer).toFixed(9),
        ]),
      ),
  );
}
it("keeps real approvals pending and validates disjoint authored form/review pools", () => {
  const sources = cmSources();
  expect(sources.every((s) => !independentlyReviewed(s))).toBe(true);
  const seen = new Set<string>();
  const practice = new Set(
    catalog().families.flatMap((f) => f.items.map(itemFingerprint)),
  );
  for (const s of sources)
    for (const variant of s.variants)
      for (const check of variant.items) {
        const aliases = fingerprintCandidates(check.task);
        expect(
          aliases.some((fp) => seen.has(fp) || practice.has(fp)),
          check.task.id,
        ).toBe(false);
        aliases.forEach((fp) => seen.add(fp));
      }
});
it("admits passing scopes independently and rejects a 1/2 scope despite a passing global score", () => {
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-FRAMES", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  const raw = attemptById(store.db, opened.id),
    { variant } = knownCM(raw, resolve),
    a = answers(source, variant.id);
  const q = variant.items[1].task.fields[0];
  a["1.0"] = q.options!.find((o) => o !== q.answer)!;
  expect(
    gradeCM(variant, a).correct / gradeCM(variant, a).total,
  ).toBeGreaterThan(0.8);
  submitCM(store, opened.id, { answers: a, declaredAssistance: 0 }, resolve);
  const evidence = learningData(store.db).v2_evidence;
  expect(evidence).toHaveLength(7);
  expect(evidence.filter((e) => e.outcome === "admitted")).toHaveLength(6);
  expect(
    evidence.find((e) => e.objective_id === "M12.frame-labels"),
  ).toMatchObject({ outcome: "not_admitted", reason_code: "below_threshold" });
  expect(store.read().attempts).toHaveLength(0);
  expect(store.read().labs).toHaveLength(0);
});
it("records help durably, is idempotent, and never admits assisted checks", () => {
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
      store,
      { purpose: "verify", source: source.id },
      resolve,
    ),
    a = answers(source, opened.item.route);
  assistCM(store, opened.id, 1, resolve);
  const result = submitCM(
    store,
    opened.id,
    { answers: a, declaredAssistance: 0 },
    resolve,
  );
  const before = learningData(store.db);
  expect(
    before.v2_evidence.every(
      (e) => e.outcome === "not_admitted" && e.reason_code === "assisted",
    ),
  ).toBe(true);
  expect(
    submitCM(store, opened.id, { answers: a, declaredAssistance: 0 }, resolve),
  ).toEqual(result);
  expect(learningData(store.db)).toEqual(before);
  expect(() =>
    submitCM(store, opened.id, { answers: a, declaredAssistance: 1 }, resolve),
  ).toThrow("different submission");
});
it("checks cross-tab exposure at close and ignores later feedback", () => {
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  const a = attemptById(store.db, opened.id),
    { variant } = knownCM(a, resolve),
    exposures = learningData(store.db).v2_exposures as unknown as Exposure[];
  expect(
    admitCM(a, source, variant, answers(source, variant.id), exposures).every(
      (d) => d.outcome === "admitted",
    ),
  ).toBe(true);
  const matching: Exposure = {
    id: "synthetic-exposure",
    at: a.submitted_at!,
    event_seq: a.closed_seq! - 1,
    fingerprint: itemFingerprint(variant.items[0].task),
    attempt_id: "other-attempt",
    kind: "solution",
  };
  expect(
    admitCM(a, source, variant, answers(source, variant.id), [
      ...exposures,
      matching,
    ]).every((d) => d.reason === "exposed"),
  ).toBe(true);
  matching.event_seq = a.closed_seq! + 100;
  expect(
    admitCM(a, source, variant, answers(source, variant.id), [
      ...exposures,
      matching,
    ]).every((d) => d.outcome === "admitted"),
  ).toBe(true);
});
it("advances relative reviews and grants retention only after a due fresh A0 check delayed at least seven days", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-11-01T00:00:00Z"));
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  for (const [date, stage] of [
    ["2026-11-02", 1],
    ["2026-11-05", 2],
    ["2026-11-12", 3],
  ] as const) {
    vi.setSystemTime(new Date(date + "T00:00:00Z"));
    const review = issueCM(
      store,
      {
        purpose: "review",
        source: "RV-R04",
        objectiveId: "R04.planar-fk",
        dimension: "M",
      },
      resolve,
    );
    submitCM(
      store,
      review.id,
      {
        answers: answers(resolve("RV-R04", 1)!, review.item.route),
        declaredAssistance: 0,
      },
      resolve,
    );
    expect(
      learningData(store.db).v2_objective_reviews.find(
        (r) => r.dimension === "M",
      )?.stage,
    ).toBe(stage);
  }
  const retained = learningData(store.db).v2_evidence.filter(
    (e) => e.dimension === "retention" && e.outcome === "admitted",
  );
  expect(retained).toHaveLength(1);
  expect(retained[0].at).toBe("2026-11-12T00:00:00.000Z");
  expect(
    learningData(store.db).v2_objective_reviews.find((r) => r.dimension === "M")
      ?.due,
  ).toBe("2026-12-03T00:00:00.000Z");
});
it("two due-review attempts cannot advance the same obligation twice", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-11-01T00:00:00Z"));
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  vi.setSystemTime(new Date("2026-11-02T00:00:00Z"));
  const r1 = issueCM(
    store,
    {
      purpose: "review",
      source: "RV-R04",
      objectiveId: "R04.planar-fk",
      dimension: "M",
    },
    resolve,
  );
  const r2 = issueCM(
    store,
    {
      purpose: "review",
      source: "RV-R04",
      objectiveId: "R04.planar-fk",
      dimension: "M",
    },
    resolve,
  );
  for (const r of [r1, r2])
    submitCM(
      store,
      r.id,
      {
        answers: answers(resolve("RV-R04", 1)!, r.item.route),
        declaredAssistance: 0,
      },
      resolve,
    );
  expect(
    learningData(store.db).v2_objective_reviews.find((r) => r.dimension === "M")
      ?.stage,
  ).toBe(1);
  expect(
    learningData(store.db).v2_evidence.find((e) => e.attempt_id === r2.id)
      ?.reason_code,
  ).toBe("stale_review");
});

it("replays C/M and delayed reviews on foreign restore without trusting serialized admission or due caches", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-11-01T00:00:00Z"));
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  vi.setSystemTime(new Date("2026-11-09T00:00:00Z"));
  const due = issueCM(
    store,
    {
      purpose: "review",
      source: "RV-R04",
      objectiveId: "R04.planar-fk",
      dimension: "M",
    },
    resolve,
  );
  submitCM(
    store,
    due.id,
    {
      answers: answers(resolve("RV-R04", 1)!, due.item.route),
      declaredAssistance: 0,
    },
    resolve,
  );
  const backup = exportBackup(store),
    target = fresh();
  const originalClaims = backup.v2.evidence.map((e) => e.recorded_json);
  backup.v2.objectiveReviews.forEach((r) => {
    r.stage = 0;
    r.due = "2020-01-01T00:00:00.000Z";
  });
  const { contentHash: _hash, ...core } = backup;
  backup.contentHash = digest(core);
  const p = preview(target, backup, resolve);
  expect(p.evidence).toEqual({ admitted: 3, notAdmitted: 0, unverifiable: 0 });
  restore(
    target,
    backup,
    { digest: p.digest, token: p.token, confirm: true },
    undefined,
    resolve,
  );
  const restored = exportBackup(target);
  expect(restored.v2.evidence.map((e) => e.recorded_json)).toEqual(
    originalClaims,
  );
  expect(
    restored.v2.evidence.every((e) => e.provenance === "restored_foreign"),
  ).toBe(true);
  expect(
    restored.v2.objectiveReviews.find((r) => r.dimension === "M"),
  ).toMatchObject({
    stage: 1,
    due: "2026-11-12T00:00:00.000Z",
    state: "active",
  });
  expect(restored.workspaceId).not.toBe(backup.workspaceId);
});

it("does not readmit a forged grade, suspends its reviews, and keeps unreviewed source history inert", () => {
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  const backup = exportBackup(store),
    target = fresh();
  const grade = JSON.parse(backup.v2.attempts[0].grade_json!);
  grade.correct = 0;
  backup.v2.attempts[0].grade_json = canonical(grade);
  const { contentHash: _hash, ...core } = backup;
  backup.contentHash = digest(core);
  const p = preview(target, backup, resolve);
  expect(p.evidence?.notAdmitted).toBe(2);
  restore(
    target,
    backup,
    { digest: p.digest, token: p.token, confirm: true },
    undefined,
    resolve,
  );
  expect(
    exportBackup(target).v2.objectiveReviews.every(
      (r) => r.state === "suspended",
    ),
  ).toBe(true);
  expect(
    exportBackup(target).v2.evidence.every(
      (e) => e.reason_code === "recompute_mismatch",
    ),
  ).toBe(true);
  const pending = preview(target, backup);
  expect(pending.evidence?.unverifiable).toBe(2);
});

it("rejects changed submission hashes and missing known-scope evidence before restore writes", () => {
  const store = fresh(),
    resolve = resolver(),
    source = resolve("F-R04", 1)!;
  const opened = issueCM(
    store,
    { purpose: "verify", source: source.id },
    resolve,
  );
  submitCM(
    store,
    opened.id,
    { answers: answers(source, opened.item.route), declaredAssistance: 0 },
    resolve,
  );
  const backup = exportBackup(store),
    target = fresh();
  const before = learningData(target.db);
  const changed = structuredClone(backup);
  changed.v2.attempts[0].submission_hash = "0".repeat(64);
  const { contentHash: _h, ...core } = changed;
  changed.contentHash = digest(core);
  expect(() => preview(target, changed, resolve)).toThrow("submission hash");
  const missing = structuredClone(backup);
  missing.v2.evidence.pop();
  missing.counts.evidence--;
  missing.v2.objectiveReviews = [];
  missing.counts.objectiveReviews = 0;
  const { contentHash: _h2, ...c2 } = missing;
  missing.contentHash = digest(c2);
  expect(() => preview(target, missing, resolve)).toThrow("Missing scoped");
  expect(learningData(target.db)).toEqual(before);
});

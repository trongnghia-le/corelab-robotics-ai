import { afterEach, expect, it } from "vitest";
import { Store } from "../../lib/storage";
import { initialize, learningData } from "../../lib/v2/db";
import {
  downloadKit,
  selfReportKit,
  kitFingerprints,
  kits,
} from "../../lib/v2/kits";
import { exportBackup, preview, restore } from "../../lib/v2/backup";
import { submit } from "../../lib/v2/attempts";
import { cmSources, fingerprintCandidates } from "../../lib/v2/assessments";
const stores: Store[] = [];
afterEach(() => stores.splice(0).forEach((s) => s.close()));
function store() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
it("records download exposure and idempotent manual self-report without grades or evidence", () => {
  const s = store(),
    kit = downloadKit(s, "L02-planar");
  expect(kit.content).toContain("NotImplementedError");
  expect(
    learningData(s.db).v2_exposures.some((e) => e.kind === "kit_download"),
  ).toBe(true);
  const req = { attemptId: kit.attemptId, ran: true, declaredAssistance: 2 };
  expect(selfReportKit(s, kit.id, req).verifiedI).toBe("unavailable");
  const before = learningData(s.db);
  expect(selfReportKit(s, kit.id, req).recorded).toBe(true);
  expect(learningData(s.db)).toEqual(before);
  expect(before.v2_evidence).toEqual([]);
  expect(() => selfReportKit(s, kit.id, { ...req, passed: true })).toThrow();
  expect(() =>
    submit(s, kit.attemptId, { answers: {}, declaredAssistance: 0 }),
  ).toThrow("self-report");
  const b = exportBackup(s);
  restore(s, b, { ...preview(s, b), confirm: true });
  expect(learningData(s.db).v2_attempts[0].submission_json).toBe(
    before.v2_attempts[0].submission_json,
  );
});
it("serves the odometry kit with its own sample file and per-kit identity", () => {
  expect(kits().map((k) => k.id)).toEqual([
    "L01-SE2",
    "L02-planar",
    "L03-odometry",
  ]);
  const s = store(),
    kit = downloadKit(s, "L03-odometry");
  expect(kit.filename).toBe("L03-odometry.v1.py");
  expect(kit.content).toContain("NotImplementedError");
  expect(kit.samples.length).toBeGreaterThan(20);
  expect(kit.objectives).toEqual(["R02.exact-arc"]);
  const odometry = new Set(kitFingerprints("L03-odometry"));
  for (const other of ["L01-SE2", "L02-planar"])
    expect(kitFingerprints(other).some((fp) => odometry.has(fp))).toBe(false);
});
it("has disjoint authored kit sample exposure and C/M pools", () => {
  const samples = new Set(kits().flatMap((k) => kitFingerprints(k.id)));
  for (const s of cmSources())
    for (const v of s.variants)
      for (const c of v.items)
        expect(
          fingerprintCandidates(c.task).some((fp) => samples.has(fp)),
          c.task.id,
        ).toBe(false);
});

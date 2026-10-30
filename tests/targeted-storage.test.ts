import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { tmpdir } from "node:os";
import { Store, validateBackup } from "../lib/storage";
import { applyAction } from "../lib/actions";
import { getAssessment, getAssessmentCatalog } from "../lib/content";
import { isObjective } from "../lib/assessment";
import { gradeAssessment, masteryFor } from "../lib/engine";
import { deriveWeaknesses, selectTargetedPlan } from "../lib/weaknesses";
const catalog = getAssessmentCatalog();
const correct = () =>
  Object.fromEntries(
    getAssessment("M05")!
      .questions.filter(isObjective)
      .map((q) => [q.id, q.answer!]),
  );
function fail(s: Store) {
  s.attempt("M05", { ...correct(), q3: "99" }, "A0");
}
function submit(s: Store, assistance = "A0", skill = "chain-rule") {
  const plan = selectTargetedPlan(s.read(), catalog, "M05", skill);
  return applyAction(s, {
    type: "targeted_attempt",
    topicId: "M05",
    skillTag: skill,
    questionIds: plan.assessment.questions.map((q) => q.id),
    assessmentVersion: plan.assessment.version,
    answers: Object.fromEntries(
      plan.assessment.questions.map((q) => [
        q.id,
        q.answer ?? "My independently written justification",
      ]),
    ),
    assistance,
  });
}
describe("targeted persistence and backup compatibility", () => {
  it("stores objective correction through the action boundary without granting mastery", () => {
    const s = new Store(":memory:");
    fail(s);
    submit(s);
    const p = s.read();
    expect(p.attempts[1]).toMatchObject({
      purpose: "targeted",
      skillTag: "chain-rule",
      assessmentVersion: 1,
    });
    expect(deriveWeaknesses(p, catalog)[0].status).toBe(
      "independently_corrected",
    );
    expect(masteryFor("M05", p).level).toBe(0);
    expect(p.reviews).toHaveLength(1);
    s.close();
  });
  it("preserves old diagnostic evidence and numerical gates when metadata is added", () => {
    const s = new Store(":memory:");
    const raw = JSON.parse(
      fs.readFileSync("content/assessments/M05.v1.json", "utf8"),
    );
    const expected = gradeAssessment(raw, correct());
    const a = s.attempt("M05", correct(), "A0");
    expect(a.grade).toEqual(expected);
    const before = structuredClone(a);
    submit(s);
    expect(s.read().attempts[0]).toEqual(before);
    expect(masteryFor("M05", s.read()).level).toBe(1);
    s.close();
  });
  it("persists targeted attempts across restart without a destructive database migration", () => {
    const dir = fs.mkdtempSync(path.join(tmpdir(), "corelab-targeted-"));
    try {
      let s = new Store(path.join(dir, "progress.sqlite"));
      fail(s);
      submit(s);
      const before = s.read();
      s.close();
      s = new Store(path.join(dir, "progress.sqlite"));
      expect(s.read()).toEqual(before);
      expect(s.db.prepare("PRAGMA user_version").get()).toMatchObject({
        user_version: 2,
      });
      s.close();
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
  it("round-trips new v2 backups with selected questions and derived mistake history", () => {
    const a = new Store(":memory:");
    fail(a);
    submit(a, "A3");
    const backup = a.export();
    expect(backup.schema).toBe("corelab-backup/2");
    const b = new Store(":memory:");
    b.restore(backup, true);
    expect(b.read()).toEqual(a.read());
    expect(deriveWeaknesses(b.read(), catalog)).toEqual(
      deriveWeaknesses(a.read(), catalog),
    );
    a.close();
    b.close();
  });
  it("restores a historical v1 export without any new optional fields", () => {
    const a = new Store(":memory:");
    fail(a);
    const backup = { ...a.export(), schema: "corelab-backup/1" };
    expect(backup.progress.attempts[0].purpose).toBeUndefined();
    const p = validateBackup(backup);
    expect(p.attempts[0].grade).toEqual(a.read().attempts[0].grade);
    expect(deriveWeaknesses(p, catalog)[0].failureCount).toBe(1);
    a.close();
  });
  it("rejects new targeted fields disguised as a legacy backup", () => {
    const a = new Store(":memory:");
    submit(a);
    expect(() =>
      validateBackup({ ...a.export(), schema: "corelab-backup/1" }),
    ).toThrow("schema v2");
    a.close();
  });
  it("regrades a tampered targeted score using the retained bank version", () => {
    const a = new Store(":memory:");
    submit(a);
    const backup = a.export();
    backup.progress.attempts[0].answers[
      backup.progress.attempts[0].questionIds![0]
    ] = "wrong";
    backup.progress.attempts[0].grade.passed = true;
    const p = validateBackup(backup);
    expect(p.attempts[0].grade.passed).toBe(false);
    expect(masteryFor("M05", p).level).toBe(0);
    a.close();
  });
  it("rejects invalid practice provenance before replacing any progress", () => {
    const a = new Store(":memory:");
    fail(a);
    submit(a);
    const before = a.read();
    for (const edit of [
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts[1].questionIds = ["not-authored"];
      },
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts[1].assessmentVersion = 99;
      },
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts[1].skillTag = "unrelated";
      },
    ]) {
      const b = structuredClone(a.export());
      edit(b);
      expect(() => a.restore(b, true)).toThrow();
      expect(a.read()).toEqual(before);
    }
    a.close();
  });
  it("refuses stale submissions and never records a duplicate partial set", () => {
    const a = new Store(":memory:");
    const plan = selectTargetedPlan(a.read(), catalog, "M05", "chain-rule");
    submit(a);
    expect(() =>
      a.targetedAttempt(
        "M05",
        "chain-rule",
        plan.assessment.questions.map((q) => q.id),
        {},
        "A0",
        1,
      ),
    ).toThrow("stale");
    expect(a.read().attempts).toHaveLength(1);
    a.close();
  });
  it("requires complete answers and excludes questions outside the selected set", () => {
    const a = new Store(":memory:");
    const plan = selectTargetedPlan(a.read(), catalog, "M05", "chain-rule");
    const ids = plan.assessment.questions.map((q) => q.id);
    expect(() =>
      a.targetedAttempt("M05", "chain-rule", ids, {}, "A0", 1),
    ).toThrow("Complete");
    expect(() =>
      a.targetedAttempt("M05", "chain-rule", ids, { q99: "claim" }, "A0", 1),
    ).toThrow("outside");
    expect(a.read().attempts).toHaveLength(0);
    a.close();
  });
  it("does not schedule failure or create weaknesses for rubric-only design work", () => {
    const a = new Store(":memory:");
    submit(a, "A0", "design-decisions");
    expect(a.read().reviews).toEqual([]);
    expect(deriveWeaknesses(a.read(), catalog)).toEqual([]);
    expect(masteryFor("M05", a.read()).level).toBe(0);
    a.close();
  });
  it("A3 focused practice preserves the independent gate and unresolved weakness", () => {
    const a = new Store(":memory:");
    fail(a);
    submit(a, "A3");
    expect(deriveWeaknesses(a.read(), catalog)[0].status).toBe(
      "practiced_with_assistance",
    );
    expect(masteryFor("M05", a.read()).level).toBe(0);
    a.close();
  });
});

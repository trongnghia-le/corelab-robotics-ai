import { describe, it, expect } from "vitest";
import { validateGraph, topics, ancestors } from "../lib/curriculum";
import source from "../corelab/curriculum_graph_v1.json";
import {
  allMastery,
  masteryFor,
  gradeAssessment,
  recommend,
  contextFor,
} from "../lib/engine";
import { emptyProgress, type Assessment, type Progress } from "../lib/types";
import {
  getAssessment,
  lessonIds,
  getLesson,
  publicAssessment,
} from "../lib/content";
const correct = (id: string) =>
  Object.fromEntries(
    getAssessment(id)!
      .questions.filter((q) => q.kind !== "short")
      .map((q) => [q.id, q.answer!]),
  );
function pass(
  p: Progress,
  id: string,
  at = "2026-01-01T00:00:00.000Z",
  assistance: "A0" | "A3" = "A0",
) {
  p.attempts.push({
    id: crypto.randomUUID(),
    topicId: id,
    at,
    assistance,
    assessmentVersion: 1,
    answers: correct(id),
    grade: gradeAssessment(getAssessment(id)!, correct(id)),
  });
}
describe("curriculum integrity", () => {
  it("imports every supplied ID and preserves the source", () =>
    expect(validateGraph(source).map((t) => t.id)).toEqual(
      source.modules.map((t) => t.id),
    ));
  it("rejects duplicate IDs", () =>
    expect(() =>
      validateGraph({
        ...source,
        modules: [...source.modules, source.modules[0]],
      }),
    ).toThrow("Duplicate"));
  it("rejects dangling prerequisites", () =>
    expect(() =>
      validateGraph({
        ...source,
        modules: source.modules.map((t, i) =>
          i ? t : { ...t, prerequisites: ["NOPE"] },
        ),
      }),
    ).toThrow("Dangling"));
  it("rejects cycles", () =>
    expect(() =>
      validateGraph({
        ...source,
        modules: source.modules.map((t, i) =>
          i ? t : { ...t, prerequisites: ["M02"] },
        ),
      }),
    ).toThrow("cycle"));
  it("rejects invalid priorities", () =>
    expect(() =>
      validateGraph({
        ...source,
        modules: [{ ...source.modules[0], priority: "P9" }],
      }),
    ).toThrow());
  it("expands transitive ancestors without duplicates", () => {
    const ids = ancestors("R04");
    expect(ids).toContain("M01");
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).not.toContain("R04");
  });
});
describe("objective grading and mastery gates", () => {
  it("starts at unassessed for every topic", () => {
    const m = allMastery(emptyProgress());
    expect(Object.keys(m)).toHaveLength(topics.length);
    expect(
      Object.values(m).every((x) => x.status === "unassessed" && x.level === 0),
    ).toBe(true);
  });
  it("reading, notes, practice and AI feedback never verify mastery", () => {
    const p = emptyProgress();
    for (const kind of ["reading", "note", "practice", "ai_feedback"] as const)
      p.sessions.push({
        id: kind,
        topicId: "M01",
        at: new Date().toISOString(),
        kind,
        text: "I understand it",
        minutes: 15,
      });
    expect(masteryFor("M01", p).level).toBe(0);
  });
  it("keeps self-assessment provisional", () => {
    const p = emptyProgress();
    p.sessions.push({
      id: "self",
      topicId: "M01",
      at: new Date().toISOString(),
      kind: "self_assessment",
      text: "My own estimate",
      minutes: 0,
      provisionalLevel: 4,
    });
    expect(masteryFor("M01", p)).toMatchObject({
      level: 0,
      provisionalLevel: 4,
      status: "provisional",
    });
  });
  it("critical failure blocks verification even above 80%", () => {
    const a: Assessment = {
      id: "test",
      topicId: "M01",
      version: 1,
      questions: Array.from({ length: 6 }, (_, i) => ({
        id: String(i),
        kind: "choice",
        options: ["right", "wrong"],
        prompt: "test",
        answer: "0",
        dimension: "C",
        critical: i === 0,
        explanation: "reason",
      })),
    };
    const grade = gradeAssessment(a, {
      "0": "1",
      "1": "0",
      "2": "0",
      "3": "0",
      "4": "0",
      "5": "0",
    });
    expect(grade.score).toBe(83);
    expect(grade.passed).toBe(false);
    expect(grade.dimensions.C).toBe(false);
  });
  it("numerical checks use tolerance and reject blank/NaN", () => {
    const a: Assessment = {
      id: "n",
      topicId: "M01",
      version: 1,
      questions: [
        {
          id: "n",
          kind: "number",
          prompt: "test",
          answer: "1",
          dimension: "M",
          critical: false,
          tolerance: 0.001,
          explanation: "reason",
        },
      ],
    };
    expect(gradeAssessment(a, { n: "1.0005" }).passed).toBe(true);
    for (const answer of ["", "NaN", "Infinity", "1.01"])
      expect(gradeAssessment(a, { n: answer }).passed).toBe(false);
  });
  it("does not auto-grade a rubric response", () => {
    const a = getAssessment("M01")!;
    const g = gradeAssessment(a, {
      ...correct("M01"),
      explain: "I am an expert",
    });
    expect(g.items.at(-1)?.correct).toBeNull();
    expect(g.dimensions.T).toBeUndefined();
  });
  it("independent passing attempt yields L1 and separate C/M evidence", () => {
    const p = emptyProgress();
    pass(p, "M01");
    expect(masteryFor("M01", p)).toMatchObject({
      level: 1,
      dimensions: { C: 1, M: 1, I: 0, T: 0 },
    });
  });
  it("A3 passing attempts never verify", () => {
    const p = emptyProgress();
    pass(p, "M01", undefined, "A3");
    expect(masteryFor("M01", p).level).toBe(0);
  });
  it("A0 retest after assisted practice can verify", () => {
    const p = emptyProgress();
    pass(p, "M01", undefined, "A3");
    pass(p, "M01");
    expect(masteryFor("M01", p).level).toBe(1);
  });
  it("only trusted A0 lab evidence can satisfy implementation gate", () => {
    const p = emptyProgress();
    pass(p, "M02");
    p.labs.push({
      id: "lab",
      topicId: "M02",
      at: new Date().toISOString(),
      assistance: "A3",
      sourceHash: "a".repeat(64),
      report: "{}",
      signature: "signature",
      trusted: true,
    });
    expect(masteryFor("M02", p).level).toBe(1);
    p.labs[0].assistance = "A0";
    p.labs[0].trusted = false;
    expect(masteryFor("M02", p).level).toBe(1);
    p.labs[0].trusted = true;
    expect(masteryFor("M02", p).level).toBe(2);
  });
  it("retention requires a real seven-day interval and never claims novel transfer", () => {
    const p = emptyProgress();
    pass(p, "M01", "2026-01-01T00:00:00.000Z");
    pass(p, "M01", "2026-01-02T00:00:00.000Z");
    expect(masteryFor("M01", p).dimensions.T).toBe(0);
    pass(p, "M01", "2026-01-08T00:00:00.000Z");
    expect(masteryFor("M01", p).dimensions.T).toBe(1);
    expect(masteryFor("M01", p).level).toBe(1);
  });
  it("failed review creates a gap without deleting historical evidence", () => {
    const p = emptyProgress();
    pass(p, "M01");
    p.attempts.push({
      ...p.attempts[0],
      id: "fail",
      at: "2026-01-02T00:00:00.000Z",
      answers: {},
      grade: gradeAssessment(getAssessment("M01")!, {}),
    });
    expect(masteryFor("M01", p)).toMatchObject({ level: 1, gap: true });
  });
});
describe("deterministic recommendations", () => {
  it("begins with mathematical basics without fictitious progress", () =>
    expect(recommend(emptyProgress(), lessonIds())[0].topicId).toBe("M01"));
  it("does not recommend unmet prerequisites", () => {
    const p = emptyProgress();
    expect(
      recommend(p, lessonIds()).every((r) => r.prerequisites.length === 0),
    ).toBe(true);
  });
  it("unlocks the vector branch after verified basics", () => {
    const p = emptyProgress();
    pass(p, "M01");
    expect(recommend(p, lessonIds()).map((r) => r.topicId)).toContain("M02");
  });
  it("self-assessment does not unlock dependent topics", () => {
    const p = emptyProgress();
    p.sessions.push({
      id: "self",
      topicId: "M01",
      kind: "self_assessment",
      text: "estimate",
      at: new Date().toISOString(),
      minutes: 0,
      provisionalLevel: 4,
    });
    expect(recommend(p, lessonIds()).some((r) => r.topicId === "M02")).toBe(
      false,
    );
  });
  it("prioritizes a due review with an explanation", () => {
    const p = emptyProgress();
    pass(p, "M01");
    p.reviews.push({
      topicId: "M01",
      due: "2026-01-02T00:00:00.000Z",
      stage: 0,
      lastAttemptId: p.attempts[0].id,
    });
    const r = recommend(p, lessonIds(), new Date("2026-01-03"));
    expect(r[0]).toMatchObject({ topicId: "M01", kind: "review" });
    expect(r[0].reason).toContain("Review due");
  });
  it("lets a project focus prioritize missing foundational ancestors", () => {
    const p = emptyProgress();
    p.focusTopic = "E12";
    p.focusReason = "project";
    const r = recommend(p, lessonIds());
    expect(r.some((x) => ancestors("E12").includes(x.topicId))).toBe(true);
    expect(r).toEqual(recommend(p, lessonIds()));
  });
  it("never recommends an unauthored lesson", () =>
    expect(recommend(emptyProgress(), ["PY01"]).map((r) => r.topicId)).toEqual([
      "PY01",
    ]));
  it("limits suggestions to three", () =>
    expect(recommend(emptyProgress(), lessonIds()).length).toBeLessThanOrEqual(
      3,
    ));
});
describe("lesson and tutor boundaries", () => {
  it("keeps answer keys server-side", () => {
    const a = publicAssessment(getAssessment("M01"))!;
    expect(
      a.questions.every(
        (q) => !("answer" in q) && !("tolerance" in q) && q.explanation === "",
      ),
    ).toBe(true);
  });
  it("generates parseable handoff without question keys", () => {
    const p = emptyProgress();
    pass(p, "M01");
    const c = contextFor(
      "M01",
      p,
      getLesson("M01")!.meta.objectives,
      "debugging",
      "Why did my test fail?",
    );
    const data = JSON.parse(c);
    expect(data.topic.id).toBe("M01");
    expect(data.verifiedEvidence.level).toBe(1);
    expect(data.questions).toContain("test");
    expect(c).not.toContain('"q1"');
    expect(c).not.toContain('"answer"');
  });
});

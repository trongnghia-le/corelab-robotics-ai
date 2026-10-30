import { describe, it, expect } from "vitest";
import {
  getAssessment,
  getAssessmentCatalog,
  getPracticeAssessment,
  lessonIds,
  publicAssessment,
} from "../lib/content";
import {
  knowledgeTypeFor,
  knowledgeTypes,
  knowledgeTypeInfo,
  isObjective,
  assessmentSchema,
  resolveAttempt,
} from "../lib/assessment";
import {
  deriveWeaknesses,
  selectTargetedPlan,
  assertTargetedSubmission,
} from "../lib/weaknesses";
import { gradeAssessment, masteryFor, recommend } from "../lib/engine";
import {
  emptyProgress,
  type Progress,
  type Attempt,
  type Assistance,
  type Question,
} from "../lib/types";
import { scheduleReview } from "../lib/reviews";
const catalog = getAssessmentCatalog();
const now = new Date("2026-10-20T12:00:00.000Z");
const correct = (topic: string) =>
  Object.fromEntries(
    getAssessment(topic)!
      .questions.filter(isObjective)
      .map((q) => [q.id, q.answer!]),
  );
function diagnostic(
  p: Progress,
  topic = "M05",
  wrong: string[] = [],
  help: Assistance = "A0",
  at = "2026-10-10T12:00:00.000Z",
) {
  const answers = correct(topic);
  for (const id of wrong) answers[id] = "wrong";
  const a: Attempt = {
    id: crypto.randomUUID(),
    topicId: topic,
    assessmentVersion: 1,
    at,
    assistance: help,
    answers,
    grade: gradeAssessment(getAssessment(topic)!, answers),
  };
  p.attempts.push(a);
  return a;
}
function focused(
  p: Progress,
  tag = "chain-rule",
  help: Assistance = "A0",
  at = "2026-10-11T12:00:00.000Z",
  wrong: string[] = [],
  topic = "M05",
) {
  const plan = selectTargetedPlan(p, catalog, topic, tag, new Date(at));
  const answers = Object.fromEntries(
    plan.assessment.questions.map((q) => [
      q.id,
      q.answer ?? "My justified response",
    ]),
  );
  for (const id of wrong) answers[id] = "wrong";
  const a: Attempt = {
    id: crypto.randomUUID(),
    topicId: topic,
    assessmentVersion: 1,
    purpose: "targeted",
    skillTag: tag,
    questionIds: plan.assessment.questions.map((q) => q.id),
    at,
    assistance: help,
    answers,
    grade: gradeAssessment(plan.assessment, answers),
  };
  p.attempts.push(a);
  return a;
}
describe("objective mistake history", () => {
  it("records topic, contract, question, skill, category and timestamps from wrong answers", () => {
    const p = emptyProgress();
    const a = diagnostic(p, "M05", ["q3"]);
    const w = deriveWeaknesses(p, catalog, now)[0];
    expect(w).toMatchObject({
      topicId: "M05",
      skillTag: "chain-rule",
      failureCount: 1,
      failedAttempts: 1,
      lastFailedAt: a.at,
      lastAttemptAt: a.at,
      status: "active",
      latestResult: "incorrect",
      classificationSource: "authored",
    });
    expect(w.categories).toContain("mathematical");
    expect(w.questionRefs).toEqual([
      { questionId: "q3", version: 1, purpose: "diagnostic" },
    ]);
    expect(w.prerequisites).toEqual(["M01"]);
  });
  it("groups repeated question errors by authored skill and counts failed submissions separately", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1", "q3"]);
    diagnostic(p, "M05", ["q3"], "A0", "2026-10-11T12:00:00.000Z");
    const w = deriveWeaknesses(p, catalog, now).find(
      (w) => w.skillTag === "chain-rule",
    )!;
    expect(w.failureCount).toBe(3);
    expect(w.failedAttempts).toBe(2);
    expect(w.questionRefs).toHaveLength(2);
  });
  it("never classifies ungraded answers as incorrect", () => {
    const p = emptyProgress();
    diagnostic(p);
    p.attempts[0].answers.explain = "A fluent answer containing every keyword";
    expect(deriveWeaknesses(p, catalog, now)).toEqual([]);
    focused(p, "design-decisions");
    expect(deriveWeaknesses(p, catalog, now)).toEqual([]);
  });
  it("does not resolve a skill when the same submission also fails that skill", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    const plan = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    focused(p, "chain-rule", "A0", "2026-10-11T12:00:00.000Z", [
      plan.assessment.questions[0].id,
    ]);
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe("active");
  });
  it("opening or noting an explanation does not resolve an error", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    p.sessions.push({
      id: "reading",
      topicId: "M05",
      kind: "reading",
      at: now.toISOString(),
      text: "Read explanation",
      minutes: 0,
    });
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe("active");
  });
  it("assisted correctness is distinct from independent correction", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    focused(p, "chain-rule", "A3");
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe(
      "practiced_with_assistance",
    );
    focused(p, "chain-rule", "A0", "2026-10-12T12:00:00.000Z");
    expect(deriveWeaknesses(p, catalog, now)[0]).toMatchObject({
      status: "independently_corrected",
      latestResult: "independent_correct",
    });
  });
  it("a fresh A0 equivalent question repairs a skill but never grants diagnostic mastery", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    focused(p);
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe(
      "independently_corrected",
    );
    expect(masteryFor("M05", p, now).level).toBe(0);
    expect(masteryFor("M05", p, now).dimensions).toEqual({
      C: 0,
      M: 0,
      I: 0,
      T: 0,
    });
  });
  it("keeps resolved failure history and reopens on a later error", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q3"]);
    focused(p);
    diagnostic(p, "M05", ["q3"], "A0", "2026-10-12T12:00:00.000Z");
    const w = deriveWeaknesses(p, catalog, now)[0];
    expect(w.status).toBe("active");
    expect(w.failureCount).toBe(2);
    expect(w.lastCorrectedAt).not.toBeNull();
  });
  it("classifies delayed independent recall failure as retention, separately from mastery", () => {
    const p = emptyProgress();
    diagnostic(p);
    diagnostic(p, "M05", ["q3"], "A0", "2026-10-18T12:00:00.000Z");
    const w = deriveWeaknesses(p, catalog, now)[0];
    expect(w.categories).toContain("retention");
    expect(masteryFor("M05", p, now).level).toBe(1);
  });
  it("does not call a delayed assisted error a verified retention failure", () => {
    const p = emptyProgress();
    diagnostic(p);
    diagnostic(p, "M05", ["q3"], "A3", "2026-10-18T12:00:00.000Z");
    expect(deriveWeaknesses(p, catalog, now)[0].categories).not.toContain(
      "retention",
    );
  });
  it("uses conservative fallback tags for historical contracts without metadata", () => {
    const p = emptyProgress();
    diagnostic(p, "M01", ["q2"]);
    const w = deriveWeaknesses(p, catalog, now)[0];
    expect(w.classificationSource).toBe("legacy-inferred");
    expect(w.skillTag).toBe("m01-q2");
  });
  it("returns consistent history for an unsorted imported attempt array", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q3"]);
    focused(p);
    const before = deriveWeaknesses(p, catalog, now);
    p.attempts.reverse();
    expect(deriveWeaknesses(p, catalog, now)).toEqual(before);
  });
  it("derivation is pure and does not erase original attempts", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    focused(p);
    const snapshot = structuredClone(p);
    deriveWeaknesses(p, catalog, now);
    expect(p).toEqual(snapshot);
  });
  it("maps authored procedural and implementation/debugging categories without an LLM", () => {
    const p = emptyProgress();
    diagnostic(p, "R04", ["q2"]);
    diagnostic(p, "PY01", ["q1"]);
    const ws = deriveWeaknesses(p, catalog, now);
    expect(ws.find((w) => w.topicId === "R04")?.categories).toContain(
      "procedural",
    );
    expect(ws.find((w) => w.topicId === "PY01")?.categories).toContain(
      "implementation",
    );
  });
  it("a relevant newer trusted A0 lab can repair only its explicitly mapped skill", () => {
    const p = emptyProgress();
    diagnostic(p, "M02", ["q1", "q3"]);
    p.labs.push({
      id: "lab",
      topicId: "M02",
      at: "2026-10-12T12:00:00.000Z",
      assistance: "A0",
      trusted: true,
      sourceHash: "a".repeat(64),
      signature: "fixture",
      report: "fixture",
    });
    const ws = deriveWeaknesses(p, catalog, now);
    expect(
      ws.find((w) => w.skillTag === "vector-dot-product")?.latestResult,
    ).toBe("verified_lab");
    expect(ws.find((w) => w.skillTag === "dot-product-concept")?.status).toBe(
      "active",
    );
  });
  it("assisted or older lab evidence cannot erase a fresh error", () => {
    const p = emptyProgress();
    diagnostic(p, "M02", ["q3"]);
    p.labs.push({
      id: "lab",
      topicId: "M02",
      at: "2026-10-12T12:00:00.000Z",
      assistance: "A3",
      trusted: true,
      sourceHash: "a".repeat(64),
      signature: "fixture",
      report: "fixture",
    });
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe("active");
    p.labs[0].assistance = "A0";
    p.labs[0].at = "2026-10-01T00:00:00.000Z";
    expect(deriveWeaknesses(p, catalog, now)[0].status).toBe("active");
  });
});
describe("focused selection and availability", () => {
  it("selects fresh, equivalent authored questions deterministically for a failed skill", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q3"]);
    const a = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    expect(a.assessment.questions).toHaveLength(3);
    expect(
      a.assessment.questions.every(
        (q) =>
          q.skillTags?.includes("chain-rule") && q.equivalentTo?.includes("q3"),
      ),
    ).toBe(true);
    expect(a).toEqual(selectTargetedPlan(p, catalog, "M05", "chain-rule", now));
  });
  it("does not immediately recycle questions after assisted exposure", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q3"]);
    const seen = focused(p, "chain-rule", "A3").questionIds!;
    const next = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    expect(next.assessment.questions.every((q) => !seen.includes(q.id))).toBe(
      true,
    );
  });
  it("reports an honest exhausted state instead of endless immediate repeats", () => {
    const p = emptyProgress();
    focused(p);
    focused(p, "chain-rule", "A0", "2026-10-12T12:00:00.000Z");
    const plan = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    expect(plan.assessment.questions).toHaveLength(0);
    expect(plan.message).toContain("No fresh variants");
  });
  it("permits one delayed reuse only when the shared review is due", () => {
    const p = emptyProgress();
    const first = focused(p);
    focused(p, "chain-rule", "A0", "2026-10-12T12:00:00.000Z");
    p.reviews.push({
      topicId: "M05",
      due: "2026-10-19T00:00:00.000Z",
      stage: 0,
      lastAttemptId: first.id,
    });
    const due = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    expect(due.assessment.questions.length).toBeGreaterThan(0);
    expect(
      due.assessment.questions.every(
        (q) => first.questionIds!.includes(q.id) || q.id === "chain-values-2",
      ),
    ).toBe(true);
    focused(p, "chain-rule", "A0", now.toISOString());
    focused(p, "chain-rule", "A0", "2026-10-21T12:00:00.000Z");
    expect(
      selectTargetedPlan(
        p,
        catalog,
        "M05",
        "chain-rule",
        new Date("2026-11-01"),
      ).assessment.questions,
    ).toHaveLength(0);
  });
  it("does not use an early review to repeat a just-seen question", () => {
    const p = emptyProgress();
    focused(p);
    focused(p, "chain-rule", "A0", "2026-10-12T12:00:00.000Z");
    p.reviews.push({
      topicId: "M05",
      due: "2026-10-12T00:00:00.000Z",
      stage: 0,
      lastAttemptId: p.attempts[0].id,
    });
    expect(
      selectTargetedPlan(
        p,
        catalog,
        "M05",
        "chain-rule",
        new Date("2026-10-12T13:00:00Z"),
      ).assessment.questions,
    ).toHaveLength(0);
  });
  it("suggests an actual prerequisite after repeated failures without inventing graph edges", () => {
    const p = emptyProgress();
    for (let i = 0; i < 3; i++)
      diagnostic(p, "M05", ["q3"], "A0", `2026-10-${10 + i}T12:00:00.000Z`);
    const plan = selectTargetedPlan(p, catalog, "M05", "chain-rule", now);
    expect(plan.prerequisiteActivities.map((a) => a.topicId)).toEqual(["M01"]);
    diagnostic(p, "M01", [], "A0", "2026-10-13T12:00:00.000Z");
    expect(
      selectTargetedPlan(p, catalog, "M05", "chain-rule", now)
        .prerequisiteActivities,
    ).toEqual([]);
  });
  it("does not invent questions for an unavailable topic or unsupported weak skill", () => {
    for (const [topic, tag] of [
      ["M01", "m01-q2"],
      ["E15", "world-models"],
      ["M05", "polynomial-derivative"],
    ]) {
      const plan = selectTargetedPlan(
        emptyProgress(),
        catalog,
        topic,
        tag,
        now,
      );
      expect(plan.assessment.questions).toHaveLength(0);
      expect(plan.message).toContain("No authored variants");
    }
  });
  it("rejects stale, duplicate, substituted or empty submitted sets", () => {
    const plan = selectTargetedPlan(
      emptyProgress(),
      catalog,
      "M05",
      "chain-rule",
      now,
    );
    for (const ids of [
      [],
      ["q1"],
      [
        plan.assessment.questions[0].id,
        plan.assessment.questions[0].id,
        plan.assessment.questions[0].id,
      ],
    ])
      expect(() => assertTargetedSubmission(plan, ids)).toThrow();
  });
  it("directs recommendations toward remaining weak skills", () => {
    const p = emptyProgress();
    diagnostic(p, "M01");
    diagnostic(p, "M05", ["q1"]);
    const ws = deriveWeaknesses(p, catalog, now);
    const recommendation = recommend(p, lessonIds(), now, ws).find(
      (r) => r.topicId === "M05",
    );
    expect(recommendation).toMatchObject({
      kind: "practice",
      weaknessKey: "M05:chain-rule",
    });
    expect(recommendation?.reason).toContain("Differentiating composite");
  });
});
describe("knowledge type and competency integrity", () => {
  it("supports all four type-aware methods independently of C/M/I/T", () => {
    expect(knowledgeTypes).toEqual([
      "concept",
      "procedure",
      "implementation",
      "design",
    ]);
    for (const type of knowledgeTypes)
      expect(knowledgeTypeInfo[type].method.length).toBeGreaterThan(20);
    expect(knowledgeTypeFor({ kind: "number" } as Question)).toBe("procedure");
    expect(knowledgeTypeFor({ kind: "choice" } as Question)).toBe("concept");
    expect(
      knowledgeTypeFor(
        getPracticeAssessment("M05")!.questions.find(
          (q) => q.id === "design-scenario-1",
        )!,
      ),
    ).toBe("design");
  });
  it("does not auto-grade open design decisions by keywords", () => {
    const bank = getPracticeAssessment("M05")!;
    const q = bank.questions.find((q) => q.knowledgeType === "design")!;
    const grade = gradeAssessment(
      { ...bank, questions: [q] },
      { [q.id]: q.rubric!.join(" ") + " analytical finite differences noise" },
    );
    expect(grade).toMatchObject({ passed: false, score: 0, dimensions: {} });
    expect(grade.items[0].correct).toBeNull();
  });
  it("unsupported implementation/design objective formats do not create verified evidence", () => {
    for (const type of ["design", "implementation"] as const) {
      const q: Question = {
        id: "q",
        kind: "choice",
        prompt: "test",
        options: ["right", "wrong"],
        answer: "0",
        critical: true,
        dimension: "I",
        knowledgeType: type,
        explanation: "test",
      };
      const grade = gradeAssessment(
        { id: "test", topicId: "PY01", version: 1, questions: [q] },
        { q: "0" },
      );
      expect(grade.items[0].correct).toBeNull();
      expect(grade.passed).toBe(false);
      expect(grade.dimensions.I).toBeUndefined();
    }
  });
  it("focused A0 passes separated by a week do not manufacture retention or C/M mastery", () => {
    const p = emptyProgress();
    focused(p);
    focused(p, "chain-rule", "A0", "2026-10-19T12:00:00.000Z");
    expect(masteryFor("M05", p, now).dimensions).toEqual({
      C: 0,
      M: 0,
      I: 0,
      T: 0,
    });
  });
  it("rubric-only practice does not create a review failure", () => {
    const p = emptyProgress();
    const a = focused(p, "design-decisions");
    scheduleReview(p, a);
    expect(p.reviews).toEqual([]);
    expect(masteryFor("M05", p, now).gap).toBe(false);
  });
  it("assisted passes cannot satisfy any independent diagnostic gate", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", [], "A3");
    focused(p, "chain-rule", "A3");
    expect(masteryFor("M05", p, now).level).toBe(0);
  });
  it("the shared scheduler retains one topic review and resets failures to remediation", () => {
    const p = emptyProgress();
    const bad = diagnostic(p, "M05", ["q1"]);
    scheduleReview(p, bad);
    focused(p, "chain-rule", "A3");
    scheduleReview(p, p.attempts.at(-1)!);
    expect(p.reviews).toHaveLength(1);
    expect(p.reviews[0].stage).toBe(0);
    expect(
      Date.parse(p.reviews[0].due) - Date.parse(p.attempts.at(-1)!.at),
    ).toBe(86400000);
  });
  it("independent correction becomes due without erasing correction or increasing mastery", () => {
    const p = emptyProgress();
    diagnostic(p, "M05", ["q1"]);
    const a = focused(p);
    scheduleReview(p, a);
    const w = deriveWeaknesses(p, catalog, new Date("2026-10-13"))[0];
    expect(w.status).toBe("due_for_retention_review");
    expect(w.lastCorrectedAt).toBe(a.at);
    expect(masteryFor("M05", p, now).level).toBe(0);
  });
  it("a practice attempt resolves against its immutable selected-question contract", () => {
    const p = emptyProgress();
    const a = focused(p);
    const c = resolveAttempt(a, catalog)!;
    expect(c.questions.map((q) => q.id)).toEqual(a.questionIds);
    expect(
      resolveAttempt({ ...a, questionIds: ["not-authored"] }, catalog),
    ).toBeNull();
  });
  it("redacts practice answers, numeric tolerances and explanations before rendering", () => {
    const publicBank = publicAssessment(getPracticeAssessment("M05"))!;
    expect(
      publicBank.questions.every(
        (q) =>
          q.answer === undefined &&
          q.tolerance === undefined &&
          q.explanation === "",
      ),
    ).toBe(true);
  });
  it("rejects malformed type/answer metadata", () => {
    const a = getPracticeAssessment("M05")!;
    expect(() =>
      assessmentSchema.parse({
        ...a,
        questions: [{ ...a.questions[0], knowledgeType: "magic" }],
      }),
    ).toThrow();
    expect(() =>
      assessmentSchema.parse({
        ...a,
        questions: [{ ...a.questions[0], answer: "9" }],
      }),
    ).toThrow();
  });
});

describe("authored variant answer checks", () => {
  it("matches independent calculations for every numerical variant", () => {
    const checks: [string, string, number][] = [
      ["M02", "dot-calculation-1", 2 * 3 - 1 * 4],
      ["M02", "dot-calculation-2", -2 * 4 + 5 * 1],
      ["M05", "chain-values-1", 3 * (2 * 1 - 1) ** 2 * 2],
      ["M05", "chain-values-2", 2 * (4 * 0 + 2) * 4],
      ["PY01", "mean-values-1", (-2 + 4 + 10) / 3],
      ["PY01", "mean-values-2", (1 + 2 + 6) / 3],
      ["R04", "fk-values-1", 2 * Math.cos(0) + Math.cos(Math.PI / 2)],
      ["R04", "fk-values-2", 2 * Math.sin(Math.PI / 2) + Math.sin(Math.PI / 2)],
      ["ML05", "neuron-values-1", (2 * 3 + 0 - 4) * 3],
      ["ML05", "neuron-values-2", 1 * 2 + 1 - 5],
      ["V01", "pixel-count-1", 3 * 5],
      ["V01", "pixel-count-2", 2 * 4 * 6],
      ["RL02", "bellman-values-1", 2 / (1 - 0.5)],
      ["RL02", "bellman-values-2", 1 / (1 - 0.75)],
    ];
    for (const [topic, id, expected] of checks) {
      const q = getPracticeAssessment(topic)!.questions.find(
        (q) => q.id === id,
      )!;
      expect(Number(q.answer)).toBeCloseTo(expected, 6);
    }
  });
  it("supports authored method-selection classification without grading open judgment", () => {
    const local = structuredClone(catalog);
    local["diagnostic:V01:1"].questions[0].mistakeCategory = "method_selection";
    const p = emptyProgress();
    diagnostic(p, "V01", ["q1"]);
    expect(deriveWeaknesses(p, local, now)[0].categories).toContain(
      "method_selection",
    );
  });
});

it("retains a shared due date until the other due skills have fresh evidence", () => {
  const p = emptyProgress();
  diagnostic(p, "M05", ["q3", "q4"]);
  const repaired = diagnostic(p, "M05", [], "A0", "2026-10-11T12:00:00.000Z");
  p.reviews.push({
    topicId: "M05",
    due: "2026-10-19T12:00:00.000Z",
    stage: 1,
    lastAttemptId: repaired.id,
  });
  const a = focused(p, "chain-rule", "A0", now.toISOString());
  const ws = deriveWeaknesses(p, catalog, now);
  expect(ws.find((w) => w.skillTag === "chain-rule")?.status).toBe(
    "independently_corrected",
  );
  expect(ws.find((w) => w.skillTag === "local-linearization")?.status).toBe(
    "due_for_retention_review",
  );
  const due = p.reviews[0].due;
  scheduleReview(p, a, true);
  expect(p.reviews[0].due).toBe(due);
  expect(p.reviews[0].stage).toBe(1);
  expect(
    deriveWeaknesses(p, catalog, now).find(
      (w) => w.skillTag === "local-linearization",
    )?.status,
  ).toBe("due_for_retention_review");
});

it("still suggests a previously verified prerequisite when its latest review exposed a gap", () => {
  const p = emptyProgress();
  diagnostic(p, "M01", [], "A0", "2026-10-01T12:00:00.000Z");
  diagnostic(p, "M01", ["q1"], "A0", "2026-10-09T12:00:00.000Z");
  for (let i = 0; i < 3; i++)
    diagnostic(p, "M05", ["q3"], "A0", `2026-10-${10 + i}T12:00:00.000Z`);
  expect(masteryFor("M01", p, now).level).toBe(1);
  expect(
    selectTargetedPlan(
      p,
      catalog,
      "M05",
      "chain-rule",
      now,
    ).prerequisiteActivities.map((a) => a.topicId),
  ).toEqual(["M01"]);
});

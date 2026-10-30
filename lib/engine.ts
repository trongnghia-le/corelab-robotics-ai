import { ancestors, topicMap, topics } from "./curriculum";
import {
  dimensions,
  type Assessment,
  type Answers,
  type Grade,
  type Mastery,
  type Progress,
  type Recommendation,
} from "./types";
export function gradeAssessment(
  assessment: Assessment,
  answers: Answers,
): Grade {
  const objective = assessment.questions.filter((q) => q.kind !== "short");
  const items = assessment.questions.map((q) => {
    if (q.kind === "short")
      return {
        id: q.id,
        correct: null,
        feedback: `Review against the rubric; unverified. ${q.rubric?.join(" • ")}`,
      };
    const raw = (answers[q.id] ?? "").trim();
    const numeric = Number(raw);
    const correct =
      q.kind === "number"
        ? raw !== "" &&
          Number.isFinite(numeric) &&
          Math.abs(numeric - Number(q.answer)) <= (q.tolerance ?? 1e-6)
        : raw === q.answer;
    return { id: q.id, correct, feedback: q.explanation };
  });
  const score = objective.length
    ? Math.round(
        (100 * items.filter((i) => i.correct === true).length) /
          objective.length,
      )
    : 0;
  const byDimension: Grade["dimensions"] = {};
  for (const d of dimensions) {
    const qs = objective.filter((q) => q.dimension === d);
    if (qs.length)
      byDimension[d] =
        qs.filter((q) => items.find((i) => i.id === q.id)?.correct).length /
          qs.length >=
          0.8 &&
        qs
          .filter((q) => q.critical)
          .every((q) => items.find((i) => i.id === q.id)?.correct);
  }
  return {
    score,
    passed:
      score >= 80 &&
      objective
        .filter((q) => q.critical)
        .every((q) => items.find((i) => i.id === q.id)?.correct),
    dimensions: byDimension,
    items,
  };
}
export function masteryFor(
  topicId: string,
  p: Progress,
  now = new Date(),
): Mastery {
  const attempts = p.attempts.filter((a) => a.topicId === topicId),
    sessions = p.sessions.filter((s) => s.topicId === topicId);
  const dims: Mastery["dimensions"] = { C: 0, M: 0, I: 0, T: 0 };
  // A1+ is useful practice; only a fresh A0 attempt satisfies independent gates.
  for (const a of attempts)
    if (a.assistance === "A0" && a.grade.passed) {
      if (a.grade.dimensions.C) dims.C = 1;
      if (a.grade.dimensions.M) dims.M = 1;
    }
  const labs = p.labs.filter(
    (l) => l.topicId === topicId && l.trusted && l.assistance === "A0",
  );
  if (labs.length) dims.I = 2;
  const passed = attempts.filter(
    (a) => a.assistance === "A0" && a.grade.passed,
  );
  if (
    passed.some((a) =>
      passed.some((b) => Date.parse(a.at) - Date.parse(b.at) >= 7 * 86400000),
    )
  )
    dims.T = 1;
  // L3/L4 need reviewed novel transfer/research evidence; quizzes never claim those levels.
  const level = dims.C ? (dims.I >= 2 && dims.M >= 1 ? 2 : 1) : 0;
  const provisionalLevel = Math.max(
    0,
    ...sessions.map((s) => s.provisionalLevel ?? 0),
  );
  const latest = attempts.at(-1);
  return {
    level,
    dimensions: dims,
    provisionalLevel,
    status: level
      ? "verified"
      : provisionalLevel
        ? "provisional"
        : attempts.length || sessions.length || labs.length
          ? "in_progress"
          : "unassessed",
    reviewDue: p.reviews.some(
      (r) => r.topicId === topicId && Date.parse(r.due) <= now.getTime(),
    ),
    gap: !!latest && !latest.grade.passed,
  };
}
export function allMastery(p: Progress, now = new Date()) {
  return Object.fromEntries(
    topics.map((t) => [t.id, masteryFor(t.id, p, now)]),
  );
}
export function recommend(
  p: Progress,
  available: string[],
  now = new Date(),
): Recommendation[] {
  const m = allMastery(p, now),
    availableSet = new Set(available);
  const goalTopics = topics.filter((t) => t.domain === p.goal).map((t) => t.id);
  const relevant = new Set(goalTopics.flatMap((id) => [id, ...ancestors(id)]));
  const pinned = p.focusTopic
    ? new Set([p.focusTopic, ...ancestors(p.focusTopic)])
    : new Set<string>();
  return topics
    .filter((t) => availableSet.has(t.id) && t.priority !== "P2")
    .flatMap((t) => {
      const missing = t.prerequisites.filter((id) => m[id].level < 1);
      if (missing.length) return [];
      const state = m[t.id];
      if (
        state.level >= 1 &&
        !state.reviewDue &&
        !state.gap &&
        state.dimensions.I >= 2
      )
        return [];
      const read = p.sessions.some(
        (s) => s.topicId === t.id && s.kind === "reading",
      );
      const kind: Recommendation["kind"] = state.reviewDue
        ? "review"
        : state.gap
          ? "assess"
          : state.level >= 1
            ? "practice"
            : read
              ? "assess"
              : "learn";
      const dependents = topics.filter((x) =>
        x.prerequisites.includes(t.id),
      ).length;
      let rank =
        (t.priority === "P0" ? 30 : 0) +
        Math.min(dependents, 10) +
        (relevant.has(t.id) ? 25 : 0) +
        (pinned.has(t.id) ? 65 : 0) +
        (state.gap ? 50 : 0) +
        (state.reviewDue ? 70 : 0) +
        (t.id === "M01" ? 20 : 0) +
        (t.id === "PY01" ? 10 : 0) +
        (["M02", "M03"].includes(t.id) ? 20 : 0) +
        (t.id === "M05" ? 8 : 0);
      // Give the next missing foundation priority over repeating a passed quiz.
      if (state.level >= 1 && !state.reviewDue && !state.gap) rank -= 55;
      const reason = state.reviewDue
        ? "Review due: check retention without viewing the solution."
        : state.gap
          ? "The latest attempt revealed a gap; read the feedback and try again independently."
          : state.level >= 1
            ? "Conceptual evidence is available; next, implement independently and test your work."
            : pinned.has(t.id)
              ? `A foundation needed for your pinned goal ${p.focusTopic}; its prerequisites now have L1 evidence.`
              : t.prerequisites.length
                ? "Prerequisites have L1 evidence. This is the next step in building your foundations."
                : "No evidence yet. Start with a foundation that has no prerequisites.";
      return [
        {
          topicId: t.id,
          kind,
          rank,
          reason,
          prerequisites: t.prerequisites,
          exercise:
            kind === "practice"
              ? "Implement the assignment independently, run local tests, and import the report."
              : "Try an A0 diagnostic first; study and address gaps after your attempt.",
        },
      ];
    })
    .sort(
      (a, b) =>
        b.rank - a.rank ||
        topics.findIndex((t) => t.id === a.topicId) -
          topics.findIndex((t) => t.id === b.topicId),
    )
    .slice(0, 3);
}
export function contextFor(
  topicId: string,
  p: Progress,
  objectives: string[],
  kind: string,
  question = "",
) {
  const t = topicMap[topicId],
    m = masteryFor(topicId, p);
  const evidence = p.attempts
    .filter((a) => a.topicId === topicId)
    .map((a) => ({
      at: a.at,
      score: a.grade.score,
      passed: a.grade.passed,
      assistance: a.assistance,
      assessmentVersion: a.assessmentVersion,
    }));
  return JSON.stringify(
    {
      schema: "corelab-handoff/1",
      kind,
      topic: {
        id: t.id,
        title: t.title,
        objectives,
        prerequisites: t.prerequisites,
      },
      verifiedEvidence: {
        level: m.level,
        dimensions: m.dimensions,
        attempts: evidence,
        labs: p.labs
          .filter((l) => l.topicId === topicId)
          .map((l) => ({
            at: l.at,
            trusted: l.trusted,
            assistance: l.assistance,
            sourceHash: l.sourceHash,
          })),
      },
      attemptedExercises: p.sessions
        .filter((s) => s.topicId === topicId && s.kind === "practice")
        .map((s) => s.text),
      knownDifficulties: p.sessions
        .filter((s) => s.topicId === topicId && s.kind === "difficulty")
        .map((s) => s.text),
      notes: p.sessions
        .filter(
          (s) =>
            s.topicId === topicId && ["note", "ai_feedback"].includes(s.kind),
        )
        .map((s) => ({ kind: s.kind, text: s.text })),
      questions: question,
      sessionSummary:
        kind === "summary"
          ? p.sessions
              .filter((s) => s.topicId === topicId)
              .map((s) => ({
                at: s.at,
                kind: s.kind,
                minutes: s.minutes,
                text: s.text,
              }))
          : undefined,
      policy:
        'Start with a diagnostic. Ask me to derive and implement before giving solutions. AI feedback is provisional, never verified mastery. Return {"schema":"corelab-feedback/1","topicId":"' +
        topicId +
        '","summary":"...","difficulties":["..."],"nextSteps":["..."]}. No answer keys included.',
    },
    null,
    2,
  );
}

import type { Attempt, Progress } from "./types";
// One shared topic-level scheduler for diagnostics and focused objective practice.
export function scheduleReview(
  p: Progress,
  attempt: Attempt,
  remainingWeakness = false,
) {
  if (!attempt.grade.items.some((i) => i.correct !== null)) return;
  const topic = attempt.topicId,
    old = p.reviews.find((r) => r.topicId === topic);
  // A correct partial set must not postpone other skills that still need work.
  if (
    attempt.grade.passed &&
    attempt.assistance === "A0" &&
    remainingWeakness &&
    old
  )
    return;
  const independentPass =
    attempt.grade.passed && attempt.assistance === "A0" && !remainingWeakness;
  const isDue = old && Date.parse(old.due) <= Date.parse(attempt.at);
  const stage = independentPass
    ? Math.min(3, old && isDue ? old.stage + 1 : (old?.stage ?? 0))
    : 0;
  const days = independentPass ? [1, 3, 7, 21][stage] : 1;
  const due = new Date(Date.parse(attempt.at) + days * 86400000).toISOString();
  if (!old || !independentPass || isDue) {
    p.reviews = p.reviews.filter((r) => r.topicId !== topic);
    p.reviews.push({ topicId: topic, due, stage, lastAttemptId: attempt.id });
  }
}

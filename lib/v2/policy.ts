import { canonical, digest } from "./contracts";
import {
  fingerprintCandidates,
  gradeCM,
  independentlyReviewed,
  type CMSource,
  type Variant,
} from "./assessments";
import type { Attempt, Exposure, Review } from "./state";
export type Decision = {
  objective: string;
  dimension: "C" | "M";
  outcome: "admitted" | "not_admitted" | "unverifiable";
  reason: string;
};
export function fresh(
  variant: Variant,
  attempt: Attempt,
  exposures: Exposure[],
  cut: number,
) {
  const candidates = new Set(
    variant.items.flatMap((c) => fingerprintCandidates(c.task)),
  );
  return !exposures.some(
    (e) =>
      e.event_seq < cut &&
      candidates.has(e.fingerprint) &&
      !(e.attempt_id === attempt.id && e.kind === "issued"),
  );
}
export function admitCM(
  attempt: Attempt,
  source: CMSource,
  variant: Variant,
  answers: Record<string, string>,
  exposures: Exposure[],
): Decision[] {
  const grade = gradeCM(variant, answers),
    scopes = new Map<
      string,
      {
        objective: string;
        dimension: "C" | "M";
        correct: boolean;
        critical: boolean;
      }[]
    >();
  const recognized = source.variants.some(
    (v) => v.id === variant.id && canonical(v) === canonical(variant),
  );
  const expectedRefs = [
    ...new Map(
      variant.items.map((c) => [
        c.task.objectiveId + "/" + c.dimension,
        { id: c.task.objectiveId, version: 1, dimension: c.dimension },
      ]),
    ).values(),
  ];
  let covered = false;
  try {
    const refs = JSON.parse(attempt.objective_refs) as typeof expectedRefs;
    covered =
      canonical(
        [...refs].sort((a, b) =>
          (a.id + a.dimension).localeCompare(b.id + b.dimension),
        ),
      ) ===
      canonical(
        [...expectedRefs].sort((a, b) =>
          (a.id + a.dimension).localeCompare(b.id + b.dimension),
        ),
      );
  } catch {
    /* malformed references never authorize scope */
  }
  for (const [index, check] of variant.items.entries()) {
    const group =
      scopes.get(check.task.objectiveId + "/" + check.dimension) ?? [];
    const fields = grade.fields.filter((f) => f.id.startsWith(index + "."));
    group.push({
      objective: check.task.objectiveId,
      dimension: check.dimension,
      correct: fields.every((f) => f.correct),
      critical: check.critical,
    });
    scopes.set(check.task.objectiveId + "/" + check.dimension, group);
  }
  return [...scopes.values()].map((group) => {
    let outcome: Decision["outcome"] = "not_admitted",
      reason = "below_threshold";
    if (!independentlyReviewed(source) || attempt.policy_version !== 1) {
      outcome = "unverifiable";
      reason = "review_or_policy_unavailable";
    } else if (!recognized || !covered) {
      outcome = "unverifiable";
      reason = "variant_or_coverage_mismatch";
    } else if (
      attempt.purpose !== "verify" ||
      attempt.source_kind !== "form" ||
      attempt.status !== "submitted" ||
      attempt.closed_seq === null
    ) {
      reason = "wrong_purpose";
    } else if (
      attempt.source_hash !== source.hash ||
      attempt.source_id !== source.id ||
      attempt.source_version !== source.version
    ) {
      outcome = "unverifiable";
      reason = "source_mismatch";
    } else if (attempt.observed_level !== 0 || attempt.declared_level !== 0) {
      reason = "assisted";
    } else if (
      !fresh(variant, attempt, exposures, attempt.issued_seq) ||
      !fresh(variant, attempt, exposures, attempt.closed_seq)
    ) {
      reason = "exposed";
    } else if (group.some((g) => g.critical && !g.correct)) {
      reason = "critical_failed";
    } else if (
      group.filter((g) => g.correct).length >= Math.ceil(group.length * 0.8)
    ) {
      outcome = "admitted";
      reason = "scoped_pass";
    }
    return {
      objective: group[0].objective,
      dimension: group[0].dimension,
      outcome,
      reason,
    };
  });
}
const day = 86400000;
export const reviewToken = (review: Review) => digest(review);
export function initialReview(e: {
  id: string;
  at: string;
  objective_id: string;
  objective_version: number;
  dimension: "C" | "M";
}): Review {
  return {
    objective_id: e.objective_id,
    objective_version: e.objective_version,
    dimension: e.dimension,
    stage: 0,
    due: new Date(Date.parse(e.at) + day).toISOString(),
    basis_evidence_id: e.id,
    last_ref_kind: "evidence",
    last_ref_id: e.id,
    state: "active",
  };
}
export function reviewTransition(
  review: Review,
  attempt: Attempt,
  correct: boolean,
  eligible: boolean,
): Review {
  if (!attempt.submitted_at) throw new Error("Review is not closed");
  const next = {
    ...review,
    last_ref_kind: "attempt" as const,
    last_ref_id: attempt.id,
  };
  if (correct && eligible) {
    next.stage = Math.min(3, review.stage + 1);
    next.due = new Date(
      Date.parse(attempt.submitted_at) + [1, 3, 7, 21][next.stage] * day,
    ).toISOString();
  } else {
    if (!correct) next.stage = 0;
    next.due = new Date(Date.parse(attempt.submitted_at) + day).toISOString();
  }
  return next;
}
export function sameGrade(
  stored: string | null,
  grade: ReturnType<typeof gradeCM>,
) {
  try {
    return !!stored && canonical(JSON.parse(stored)) === canonical(grade);
  } catch {
    return false;
  }
}

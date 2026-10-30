import { topicMap } from "./curriculum";
import {
  knowledgeTypeFor,
  isObjective,
  skillTagsFor,
  resolveAttempt,
  contractKey,
  type ContractIndex,
} from "./assessment";
import type {
  Progress,
  Weakness,
  TargetedPlan,
  MistakeCategory,
} from "./types";
import { masteryFor } from "./engine";
export function weaknessUrl(topicId?: string, skillTag?: string) {
  const params = new URLSearchParams({ tab: "weaknesses" });
  if (topicId) params.set("topic", topicId);
  if (skillTag) params.set("skill", skillTag);
  return `/practice?${params}`;
}
export function deriveWeaknesses(
  p: Progress,
  catalog: ContractIndex,
  now = new Date(),
): Weakness[] {
  const groups = new Map<string, Weakness>();
  const lastIndependent = new Map<string, string>();
  const failures = new Map<string, Set<string>>();
  const ordered = p.attempts
    .map((a, index) => ({ a, index }))
    .sort((a, b) => a.a.at.localeCompare(b.a.at) || a.index - b.index);
  for (const { a } of ordered) {
    const contract = resolveAttempt(a, catalog);
    if (!contract) continue;
    const failedSkills = new Set(
      a.grade.items
        .filter((i) => i.correct === false)
        .flatMap((i) => {
          const q = contract.questions.find((q) => q.id === i.id);
          return q && isObjective(q) ? skillTagsFor(a.topicId, q) : [];
        }),
    );
    for (const item of a.grade.items) {
      const q = contract.questions.find((q) => q.id === item.id);
      if (!q || !isObjective(q) || item.correct === null) continue;
      for (const tag of skillTagsFor(a.topicId, q)) {
        const key = `${a.topicId}:${tag}`;
        let w = groups.get(key);
        if (item.correct === false) {
          const prior = lastIndependent.get(key);
          const category: MistakeCategory =
            a.assistance === "A0" &&
            prior &&
            Date.parse(a.at) - Date.parse(prior) >= 7 * 86400000
              ? "retention"
              : (q.mistakeCategory ??
                (q.dimension === "I"
                  ? "implementation"
                  : q.kind === "number"
                    ? "mathematical"
                    : "conceptual"));
          if (!w) {
            w = {
              key,
              topicId: a.topicId,
              skillTag: tag,
              skillLabel:
                q.skillLabel ?? `${topicMap[a.topicId].title} · ${q.id}`,
              knowledgeType: knowledgeTypeFor(q),
              failedAttempts: 0,
              failureCount: 0,
              questionRefs: [],
              categories: [],
              classificationSource:
                q.mistakeCategory || q.skillTags
                  ? "authored"
                  : "legacy-inferred",
              lastAttemptAt: a.at,
              lastFailedAt: a.at,
              lastCorrectedAt: null,
              latestResult: "incorrect",
              status: "active",
              reviewDueAt: null,
              prerequisites:
                q.relatedPrerequisites ?? topicMap[a.topicId].prerequisites,
              remediation: q.remediationRefs ?? [
                { label: "Review the concept", href: `/lessons/${a.topicId}` },
              ],
              priority: 0,
            };
            groups.set(key, w);
            failures.set(key, new Set());
          }
          failures.get(key)!.add(a.id);
          w.failedAttempts = failures.get(key)!.size;
          w.failureCount++;
          w.lastFailedAt = a.at;
          w.lastAttemptAt = a.at;
          w.latestResult = "incorrect";
          w.status = "active";
          if (!w.categories.includes(category)) w.categories.push(category);
          if (
            !w.questionRefs.some(
              (r) =>
                r.questionId === q.id &&
                r.version === a.assessmentVersion &&
                r.purpose === (a.purpose ?? "diagnostic"),
            )
          )
            w.questionRefs.push({
              questionId: q.id,
              version: a.assessmentVersion,
              purpose: a.purpose ?? "diagnostic",
            });
        } else if (item.correct === true && !failedSkills.has(tag)) {
          if (a.assistance === "A0") lastIndependent.set(key, a.at);
          if (w) {
            w.lastAttemptAt = a.at;
            w.latestResult =
              a.assistance === "A0"
                ? "independent_correct"
                : "assisted_correct";
            if (a.assistance === "A0") {
              w.status = "independently_corrected";
              w.lastCorrectedAt = a.at;
            } else if (w.status !== "independently_corrected")
              w.status = "practiced_with_assistance";
          }
        }
      }
    }
  }
  for (const w of groups.values()) {
    const relevant =
      catalog[contractKey(w.topicId, 1)]?.questions.filter(
        (q) =>
          q.verifiedLabTopicId === w.topicId &&
          skillTagsFor(w.topicId, q).includes(w.skillTag),
      ) ?? [];
    const lab = relevant.length
      ? p.labs
          .filter(
            (l) =>
              l.topicId === w.topicId &&
              l.trusted &&
              l.assistance === "A0" &&
              Date.parse(l.at) > Date.parse(w.lastFailedAt),
          )
          .sort((a, b) => b.at.localeCompare(a.at))[0]
      : undefined;
    if (lab) {
      w.status = "independently_corrected";
      w.latestResult = "verified_lab";
      w.lastCorrectedAt =
        w.lastCorrectedAt && w.lastCorrectedAt > lab.at
          ? w.lastCorrectedAt
          : lab.at;
      w.lastAttemptAt = w.lastAttemptAt > lab.at ? w.lastAttemptAt : lab.at;
    }
    w.reviewDueAt = p.reviews.find((r) => r.topicId === w.topicId)?.due ?? null;
    if (
      w.status === "independently_corrected" &&
      w.reviewDueAt &&
      w.lastCorrectedAt &&
      Date.parse(w.lastCorrectedAt) < Date.parse(w.reviewDueAt) &&
      Date.parse(w.reviewDueAt) <= now.getTime()
    )
      w.status = "due_for_retention_review";
    w.priority =
      (w.status === "due_for_retention_review"
        ? 90
        : w.status === "active"
          ? 70
          : w.status === "practiced_with_assistance"
            ? 60
            : 0) +
      Math.min(w.failureCount, 10) * 2 +
      (w.categories.includes("retention") ? 10 : 0);
  }
  return [...groups.values()].sort(
    (a, b) =>
      b.priority - a.priority ||
      b.lastAttemptAt.localeCompare(a.lastAttemptAt) ||
      a.key.localeCompare(b.key),
  );
}
export function selectTargetedPlan(
  p: Progress,
  catalog: ContractIndex,
  topicId: string,
  skillTag: string,
  now = new Date(),
): TargetedPlan {
  const bank = catalog[contractKey(topicId, 1, "targeted")];
  const weaknesses = deriveWeaknesses(p, catalog, now);
  const weakness =
    weaknesses.find((w) => w.topicId === topicId && w.skillTag === skillTag) ??
    null;
  const candidates =
    bank?.questions.filter((q) =>
      skillTagsFor(topicId, q).includes(skillTag),
    ) ?? [];
  const due = p.reviews.some(
    (r) => r.topicId === topicId && Date.parse(r.due) <= now.getTime(),
  );
  const questions = candidates
    .map((q, index) => {
      const seen = p.attempts.filter(
        (a) =>
          a.topicId === topicId &&
          a.purpose === "targeted" &&
          a.assessmentVersion === bank!.version &&
          a.questionIds?.includes(q.id),
      );
      const last = seen
        .map((a) => a.at)
        .sort()
        .at(-1);
      const eligible =
        !seen.length ||
        (due &&
          seen.length < 2 &&
          last &&
          now.getTime() - Date.parse(last) >= 7 * 86400000);
      const associated = weakness?.questionRefs.some((r) =>
        q.equivalentTo?.includes(r.questionId),
      );
      return {
        q,
        index,
        eligible,
        rank:
          (associated ? 100 : 0) +
          (due && last ? 40 : 0) +
          (!seen.length ? 20 : 0),
      };
    })
    .filter((x) => x.eligible)
    .sort((a, b) => b.rank - a.rank || a.index - b.index)
    .slice(0, 3)
    .map((x) => x.q);
  const prerequisites =
    weakness && weakness.failedAttempts >= 3
      ? weakness.prerequisites.filter((id) => {
          const m = masteryFor(id, p, now);
          return (
            m.level < 1 ||
            m.gap ||
            weaknesses.some(
              (w) => w.topicId === id && w.status !== "independently_corrected",
            )
          );
        })
      : [];
  return {
    topicId,
    skillTag,
    skillLabel: weakness?.skillLabel ?? candidates[0]?.skillLabel ?? skillTag,
    assessment: {
      id: bank?.id ?? `${topicId}-practice-unavailable`,
      topicId,
      version: bank?.version ?? 1,
      questions,
    },
    weakness,
    message: questions.length
      ? "An authored, focused set. Correct A0 answers can repair this skill; this set never satisfies full diagnostic mastery gates."
      : candidates.length
        ? "No fresh variants remain. A due question can be reused once after seven days; beyond that, review feedback or take the full diagnostic. New variants must be authored."
        : "No authored variants exist for this skill yet. Review the linked concept or retry the diagnostic; no replacement questions are invented.",
    prerequisiteActivities: prerequisites.map((id) => ({
      topicId: id,
      reason:
        "Repeated mistakes suggest checking this unverified foundation; this is a recommendation, not proof of a prerequisite deficit.",
      href: `/assessments/${id}`,
    })),
  };
}
export function assertTargetedSubmission(plan: TargetedPlan, ids: string[]) {
  if (
    !ids.length ||
    ids.length !== plan.assessment.questions.length ||
    ids.some((id, i) => id !== plan.assessment.questions[i].id)
  )
    throw new Error(
      "This practice set is stale or unavailable. Reload the set before submitting.",
    );
}
export function mistakeCategoryLabel(category: MistakeCategory) {
  return {
    conceptual: "Conceptual misunderstanding",
    mathematical: "Mathematical reasoning error",
    procedural: "Procedural error",
    implementation: "Implementation/debugging error",
    method_selection: "Incorrect method selection",
    retention: "Retention failure",
  }[category];
}

import { DatabaseSync } from "node:sqlite";
import { canonical, digest } from "./contracts";
import { insert, rows, schemaSQL } from "./db";
import { itemFingerprint } from "./content";
import {
  independentlyReviewed,
  gradeCM,
  normalizeCM,
  resolveCM,
  type SourceResolver,
} from "./assessments";
import { admitCM, sameGrade, type Decision } from "./policy";
import {
  applyInitial,
  closeReview,
  knownCM,
  relevantExposures,
  savedSubmission,
} from "./verification";
import { evidenceRow, reviewRow, type Backup, type Evidence } from "./state";

// Replay happens in a disposable database, before any active database write.
// Original claims/answers/IDs are retained; only the effective projection changes.
export function replay(
  backup: Backup,
  provenance: Evidence["provenance"],
  resolve: SourceResolver = resolveCM,
): Backup["v2"] {
  const stage = new DatabaseSync(":memory:");
  stage.exec("PRAGMA foreign_keys=ON");
  stage.exec(schemaSQL);
  const projected = new Map<string, Evidence>();
  const byAttempt = new Map<string, Evidence[]>();
  const inert = (
    e: Evidence,
    reason = "source_or_review_unavailable",
  ): Evidence => ({
    ...e,
    provenance,
    outcome: "unverifiable",
    reason_code: reason,
    validation_json: canonical({ policy: 1, outcome: "unverifiable", reason }),
  });
  for (const e of backup.v2.evidence) {
    if (e.attempt_id) {
      const group = byAttempt.get(e.attempt_id) ?? [];
      group.push(e);
      byAttempt.set(e.attempt_id, group);
    }
  }
  try {
    for (const row of backup.v2.historyEpochs)
      insert(stage, "v2_history_epochs", row);
    for (const row of backup.v2.attempts) insert(stage, "v2_attempts", row);
    for (const row of backup.v2.exposures) insert(stage, "v2_exposures", row);
    const closed = backup.v2.attempts
      .filter((a) => a.status === "submitted")
      .sort((a, b) => a.closed_seq! - b.closed_seq!);
    for (const a of closed) {
      const incoming = byAttempt.get(a.id) ?? [];
      const source = resolve(a.source_id, a.source_version);
      if (
        !source ||
        source.hash !== a.source_hash ||
        source.kind !== a.source_kind
      )
        continue;
      const { variant, frozen } = knownCM(a, resolve);
      if (
        canonical(variant.items.map((c) => itemFingerprint(c.task))) !==
        a.fingerprints
      )
        throw new Error("Assessment fingerprints contradict the frozen source");
      const saved = savedSubmission(a);
      const normalized = normalizeCM(variant, saved.answers);
      if (
        digest({
          answers: normalized,
          declaredAssistance: a.declared_level,
          artifact: saved.artifact,
        }) !== a.submission_hash
      )
        throw new Error("Assessment submission hash mismatch");
      if (!independentlyReviewed(source) || a.policy_version !== 1) continue;
      const grade = gradeCM(variant, saved.answers),
        matches = sameGrade(a.grade_json, grade);
      const consumed = new Set<string>();
      const emit = (
        _db: DatabaseSync,
        _attempt: typeof a,
        d: Decision,
        dimension: Evidence["dimension"] = d.dimension,
      ): Evidence => {
        const original = incoming.find(
          (e) =>
            e.objective_id === d.objective &&
            e.objective_version === 1 &&
            e.dimension === dimension,
        );
        if (!original) throw new Error("Missing scoped assessment result");
        if (consumed.has(original.id))
          throw new Error("Duplicate assessment result");
        consumed.add(original.id);
        if (
          original.source_id !== a.source_id ||
          original.source_version !== a.source_version ||
          original.source_hash !== a.source_hash ||
          original.source_kind !== source.kind ||
          original.at !== a.submitted_at ||
          original.policy_version !== a.policy_version
        )
          throw new Error("Evidence contradicts its source attempt");
        const decision = matches
          ? d
          : {
              ...d,
              outcome: "not_admitted" as const,
              reason: "recompute_mismatch",
            };
        const e: Evidence = {
          ...original,
          provenance,
          effective_assistance: Math.max(a.observed_level, a.declared_level!),
          outcome: decision.outcome,
          reason_code: decision.reason,
          validation_json: canonical({
            policy: 1,
            outcome: decision.outcome,
            reason: decision.reason,
          }),
        };
        insert(stage, "v2_evidence", e);
        projected.set(e.id, e);
        return e;
      };
      if (a.purpose === "verify") {
        for (const d of admitCM(
          a,
          source,
          variant,
          saved.answers,
          relevantExposures(stage, variant),
        ))
          applyInitial(stage, emit(stage, a, d));
      } else if (a.purpose === "review") {
        // If a restored basis lost admission, retain its dependent history inert.
        const currentBasis =
          frozen.basis && projected.get(frozen.basis.evidenceId);
        if (!currentBasis || currentBasis.outcome !== "admitted") continue;
        // A mismatched grade cannot advance even an early review's scheduler.
        if (matches)
          closeReview(
            stage,
            a,
            source,
            variant,
            frozen,
            saved.answers,
            resolve,
            emit,
          );
        else
          for (const e of incoming)
            projected.set(e.id, {
              ...inert(e, "recompute_mismatch"),
              outcome: "not_admitted",
              validation_json: canonical({
                policy: 1,
                outcome: "not_admitted",
                reason: "recompute_mismatch",
              }),
            });
      }
      if (matches && incoming.some((e) => !consumed.has(e.id)))
        throw new Error("Assessment contains an unsupported evidence scope");
    }
    const evidence = backup.v2.evidence.map(
      (e) => projected.get(e.id) ?? inert(e),
    );
    const activeReviews = rows(stage, "v2_objective_reviews").map((r) =>
      reviewRow.parse(r),
    );
    const key = (r: {
      objective_id: string;
      objective_version: number;
      dimension: string;
    }) => r.objective_id + "@" + r.objective_version + "/" + r.dimension;
    const activeKeys = new Set(activeReviews.map(key));
    return {
      ...backup.v2,
      evidence: evidence.map((e) => evidenceRow.parse(e)),
      objectiveReviews: [
        ...activeReviews,
        ...backup.v2.objectiveReviews
          .filter((r) => !activeKeys.has(key(r)))
          .map((r) => ({ ...r, state: "suspended" as const })),
      ],
    };
  } finally {
    stage.close();
  }
}

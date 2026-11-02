import { z } from "zod";
import type { Store } from "../storage";
import { catalog } from "./content";
import { meta, needsAcknowledgement, revisionToken } from "./db";
import { canonical, V2Error, BACKUP_LIMIT } from "./contracts";
import { objectives, bridgeText } from "./objectives";
import { kits } from "./kits";
import { cmSources, independentlyReviewed, resolveCM } from "./assessments";
import { CM_RELEASED } from "./release";
import { videoRegistry } from "../media";
import { labRoadmap } from "./roadmap";
const names: Record<string, string> = {
  "M12.frame-labels": "Identify source and destination frames",
  "M12.point-vs-direction": "Distinguish points from directions",
  "R03.rotation-validity": "Recognize a proper rotation",
  "R03.compose-invert-se2": "Compose planar frame transformations",
  "R04.planar-fk": "Compute a planar 2R arm pose",
};
// Review pool that issues an objective's retention check, or null when no
// approved pool covers it.
export function reviewSourceFor(objectiveId: string) {
  return (
    cmSources().find(
      (s) =>
        s.kind === "review_pool" &&
        independentlyReviewed(s) &&
        s.variants.some((v) =>
          v.items.some((c) => c.task.objectiveId === objectiveId),
        ),
    )?.id ?? null
  );
}
export function summaries(store: Store) {
  const registry = objectives();
  const counts = new Map(
    (
      store.db
        .prepare(
          "SELECT source_id,count(*) attempts,sum(status='submitted') completed FROM v2_attempts GROUP BY source_id",
        )
        .all() as { source_id: string; attempts: number; completed: number }[]
    ).map((r) => [r.source_id, r]),
  );
  const c = catalog();
  const families = c.families.map(({ items, ...f }) => ({
    ...f,
    itemCount: items.length,
    attempts: counts.get(f.id)?.attempts ?? 0,
    completed: counts.get(f.id)?.completed ?? 0,
    objectives: [...new Set(items.map((i) => i.objectiveId))].map((id) => ({
      id,
      title: names[id] ?? f.title,
    })),
    verification: {
      C: "Independent form review required",
      M: "Independent form review required",
      I: "Unavailable: reviewed isolation required",
      transfer: "Unavailable: qualified human review required",
    },
  }));
  let capacity:
    | { bytes: number; limit: number; warning: boolean }
    | { warning: boolean; message: string };
  try {
    const estimated = Number(meta(store.db, "capacity_bytes"));
    if (
      !meta(store.db, "capacity_bytes") ||
      !Number.isSafeInteger(estimated) ||
      estimated < 0
    )
      throw new Error(
        "Capacity requires a current export check; writes remain bounded.",
      );
    capacity = {
      bytes: estimated,
      limit: BACKUP_LIMIT,
      warning: estimated > BACKUP_LIMIT * 0.8,
    };
  } catch (e) {
    capacity = {
      warning: true,
      message: e instanceof Error ? e.message : "Recovery required",
    };
  }
  return {
    families,
    manualActivities: c.manualActivities,
    totals: {
      families: families.length,
      items: families.reduce((n, f) => n + f.itemCount, 0),
      attempts: families.reduce((n, f) => n + f.attempts, 0),
    },
    historyAcknowledgement: needsAcknowledgement(store.db)
      ? revisionToken(store.db)
      : null,
    capacity,
    reviewStatus:
      "Original content, author-tested and checked by an owner-assigned AI review (not a human expert review). Verified I and transfer remain unavailable.",
    workspace: { revision: meta(store.db, "data_revision") },
    objectives: registry.objectives.map((o) => ({
      ...o,
      learn: o.learn.map((ref) => ({
        ...ref,
        href:
          ref.type === "video"
            ? videoRegistry.videos.find((v) => v.id === ref.id)!.watchUrl
            : ref.type === "bridge"
              ? "/objectives/" + o.id
              : "/lessons/" + ref.topic,
      })),
    })),
    paths: registry.paths,
    labRoadmap: labRoadmap(),
    kits: kits(),
    forms: cmSources()
      .filter((s) => s.kind === "form")
      .map((s) => ({
        id: s.id,
        title: s.title,
        available: CM_RELEASED && independentlyReviewed(s),
        objectives: [
          ...new Set(
            s.variants.flatMap((v) => v.items.map((c) => c.task.objectiveId)),
          ),
        ],
        reason: "Requires an approved review record for this form",
      })),
    reviews: (
      store.db
        .prepare(
          "SELECT r.* FROM v2_objective_reviews r JOIN v2_evidence e ON e.id=r.basis_evidence_id WHERE r.state='active' AND e.outcome='admitted' ORDER BY r.due,r.objective_id,r.dimension LIMIT 50",
        )
        .all() as {
        objective_id: string;
        dimension: "C" | "M";
        due: string;
        stage: number;
        basis_evidence_id: string;
      }[]
    ).map((r) => ({
      objective: r.objective_id,
      dimension: r.dimension,
      due: r.due,
      stage: r.stage,
      dueNow: Date.parse(r.due) <= Date.now(),
      sourceId: reviewSourceFor(r.objective_id),
      available: CM_RELEASED,
    })),
    evidence: (
      store.db
        .prepare(
          "SELECT objective_id,dimension,source_id,source_version,source_hash FROM v2_evidence WHERE outcome='admitted' AND objective_version=1 AND dimension IN ('C','M') GROUP BY objective_id,dimension,source_id,source_version,source_hash",
        )
        .all() as {
        objective_id: string;
        dimension: "C" | "M";
        source_id: string;
        source_version: number;
        source_hash: string;
      }[]
    )
      .filter((e) => {
        const s = resolveCM(e.source_id, e.source_version);
        return s && independentlyReviewed(s) && s.hash === e.source_hash;
      })
      .map((e) => ({ objective: e.objective_id, dimension: e.dimension })),
  };
}
export function select(store: Store, params: URLSearchParams) {
  const req = z
    .object({
      mode: z.enum(["recommended", "explore", "more"]).default("recommended"),
      objective: z.string().max(120).optional(),
      domain: z.string().max(100).optional(),
      goal: z.string().max(120).optional(),
      limit: z.coerce.number().int().min(1).max(10).default(5),
    })
    .strict()
    .parse(Object.fromEntries(params));
  const summary = summaries(store),
    registry = objectives();
  const goal = registry.paths.find((p) => p.id === req.goal);
  if (req.goal && !goal)
    throw new V2Error("unknown_goal", "Choose an authored optional goal");
  let list = summary.families.filter(
    (f) =>
      (!req.objective || f.objectives.some((o) => o.id === req.objective)) &&
      (!req.domain || f.domain === req.domain),
  );
  const latest = store.db
    .prepare(
      "SELECT a.source_id,a.grade_json,a.observed_level,a.declared_level FROM v2_attempts a JOIN (SELECT source_id,max(closed_seq) closed_seq FROM v2_attempts WHERE status='submitted' AND source_kind='family' AND observed_level=0 AND declared_level=0 GROUP BY source_id) last ON a.source_id=last.source_id AND a.closed_seq=last.closed_seq",
    )
    .all() as {
    source_id: string;
    grade_json: string;
    observed_level: number;
    declared_level: number;
  }[];
  const failures = new Set(
    latest
      .filter((a) => {
        try {
          return (
            a.observed_level === 0 &&
            a.declared_level === 0 &&
            JSON.parse(a.grade_json).passed === false
          );
        } catch {
          return false;
        }
      })
      .map((a) => a.source_id),
  );
  const readiness = new Set(
    goal?.objectives.flatMap(
      (id) =>
        registry.objectives
          .find((o) => o.id === id)
          ?.readiness.map((r) => r.objective) ?? [],
    ) ?? [],
  );
  const attained = new Set(summary.evidence.map((e) => e.objective));
  const rank = (f: (typeof list)[number]) => {
    const due = summary.reviews.filter(
      (r) => r.dueNow && f.objectives.some((o) => o.id === r.objective),
    );
    if (
      failures.has(f.id) &&
      (!goal || f.objectives.some((o) => readiness.has(o.id)))
    )
      return {
        priority: 0,
        due: "",
        reason:
          "Your latest independent practice exposed a gap. Try a smaller example, another route or an optional prerequisite.",
      };
    if (due.length)
      return {
        priority: 1,
        due: due.map((r) => r.due).sort()[0],
        reason:
          "An objective review is due. Early/repeated practice never substitutes for fresh delayed retention.",
      };
    const next =
      goal &&
      goal.objectives.find(
        (id) =>
          !attained.has(id) &&
          (registry.objectives
            .find((o) => o.id === id)
            ?.readiness.every((r) => attained.has(r.objective)) ??
            false),
      );
    if (next && f.objectives.some((o) => o.id === next))
      return {
        priority: 3,
        due: "",
        reason:
          "Next readiness-aligned objective on your optional goal. You can choose any other activity.",
      };
    if (f.attempts > 0)
      return {
        priority: 4,
        due: "",
        reason:
          "Mix in an earlier activity, choose another route or revisit an observed gap.",
      };
    return {
      priority: 5,
      due: "",
      reason: "Optional application you have not practiced in this workspace.",
    };
  };
  if (req.mode !== "explore")
    list = [...list].sort((a, b) => {
      const x = rank(a),
        y = rank(b);
      return (
        x.priority - y.priority ||
        x.due.localeCompare(y.due) ||
        a.attempts - b.attempts ||
        a.objectiveId.localeCompare(b.objectiveId) ||
        a.id.localeCompare(b.id)
      );
    });
  return {
    items: list.slice(0, req.limit).map((f) => ({
      ...f,
      reason: rank(f).reason,
    })),
  };
}
export function objectiveDetail(store: Store, id: string) {
  const result = summaries(store),
    families = result.families.filter((f) =>
      f.objectives.some((o) => o.id === id),
    );
  if (!families.length)
    throw new V2Error(
      "not_found",
      "No authored objective exists with this ID",
      404,
    );
  return {
    ...result,
    families,
    bridge: (() => {
      const ref = objectives()
        .objectives.find((o) => o.id === id)
        ?.learn.find((r) => r.type === "bridge");
      return ref?.type === "bridge" ? bridgeText(ref.id) : null;
    })(),
  };
}
export function savePreference(store: Store, input: unknown) {
  const req = z
    .object({
      key: z.enum(["goal", "mode", "objective", "route"]),
      value: z.string().max(200),
    })
    .strict()
    .parse(input);
  store.db
    .prepare(
      "INSERT INTO v2_prefs VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
    )
    .run(req.key, canonical(req.value));
  return { saved: true };
}

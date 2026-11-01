import { z } from "zod";
import type { Store } from "../storage";
import { catalog } from "./content";
import { checkCapacity, meta, needsAcknowledgement, revisionToken } from "./db";
import { canonical, V2Error } from "./contracts";
const names: Record<string, string> = {
  "M12.frame-labels": "Identify source and destination frames",
  "M12.point-vs-direction": "Distinguish points from directions",
  "R03.rotation-validity": "Recognize a proper rotation",
  "R03.compose-invert-se2": "Compose planar frame transformations",
  "R04.planar-fk": "Compute a planar 2R arm pose",
};
export function summaries(store: Store) {
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
    capacity = checkCapacity(store.db);
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
      "Development preview. Original content is author-tested; independent review and release gates remain pending.",
    workspace: { revision: meta(store.db, "data_revision") },
  };
}
export function select(store: Store, params: URLSearchParams) {
  const req = z
    .object({
      mode: z.enum(["recommended", "explore", "more"]).default("recommended"),
      objective: z.string().max(120).optional(),
      domain: z.string().max(100).optional(),
      limit: z.coerce.number().int().min(1).max(10).default(5),
    })
    .strict()
    .parse(Object.fromEntries(params));
  let list = summaries(store).families.filter(
    (f) =>
      (!req.objective || f.objectives.some((o) => o.id === req.objective)) &&
      (!req.domain || f.domain === req.domain),
  );
  if (req.mode !== "explore")
    list = list.sort(
      (a, b) => a.attempts - b.attempts || a.id.localeCompare(b.id),
    );
  return {
    items: list
      .slice(0, req.limit)
      .map((f) => ({
        ...f,
        reason:
          f.attempts === 0
            ? "Not yet practiced in this workspace"
            : "Choose a new route or review a previous mistake; recommendations are optional.",
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
  return { ...result, families };
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

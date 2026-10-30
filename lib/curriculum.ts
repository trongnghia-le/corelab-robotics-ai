import { z } from "zod";
import source from "../corelab/curriculum_graph_v1.json";
export const topicSchema = z.object({
  id: z.string().regex(/^[A-Z]+\d+$/),
  title: z.string().min(1),
  domain: z.string().min(1),
  priority: z.enum(["P0", "P1", "P2"]),
  prerequisites: z.array(z.string()),
  target_level: z.number().int().min(1).max(4),
  baseline_status: z.literal("unassessed"),
  type: z.literal("module"),
});
export type Topic = z.infer<typeof topicSchema>;
export function validateGraph(input: unknown): Topic[] {
  const data = z
    .object({ schema_version: z.literal("1.0"), modules: z.array(topicSchema) })
    .parse(input);
  const ids = new Map<string, Topic>();
  for (const t of data.modules) {
    if (ids.has(t.id)) throw new Error(`Duplicate topic ID: ${t.id}`);
    ids.set(t.id, t);
  }
  const active = new Set<string>(),
    done = new Set<string>();
  function visit(id: string) {
    if (active.has(id)) throw new Error(`Prerequisite cycle at ${id}`);
    if (done.has(id)) return;
    active.add(id);
    for (const p of ids.get(id)!.prerequisites) {
      if (!ids.has(p)) throw new Error(`Dangling prerequisite ${p} in ${id}`);
      visit(p);
    }
    active.delete(id);
    done.add(id);
  }
  for (const id of ids.keys()) visit(id);
  return data.modules;
}
export const topics = validateGraph(source);
export const topicMap = Object.fromEntries(topics.map((t) => [t.id, t]));
export const domains = [...new Set(topics.map((t) => t.domain))];
export function ancestors(id: string): string[] {
  const result = new Set<string>();
  function visit(k: string) {
    for (const p of topicMap[k]?.prerequisites ?? []) {
      if (!result.has(p)) {
        result.add(p);
        visit(p);
      }
    }
  }
  visit(id);
  return [...result];
}

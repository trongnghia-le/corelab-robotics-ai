import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import { topicMap } from "../curriculum";
import { illustrationIds, visualizationIds, videoRegistry } from "../media";
import { getLesson } from "../content";
import { catalog } from "./content";
import { id, strictJSON } from "./contracts";
import { kits } from "./kits";
const ref = z.discriminatedUnion("type", [
  z.object({ type: z.literal("lesson"), topic: id }).strict(),
  z.object({ type: z.literal("bridge"), id }).strict(),
  z
    .object({
      type: z.literal("visualization"),
      id: z.enum(visualizationIds),
      topic: id,
    })
    .strict(),
  z
    .object({
      type: z.literal("illustration"),
      id: z.enum(illustrationIds),
      topic: id,
    })
    .strict(),
  z.object({ type: z.literal("video"), id }).strict(),
]);
const objectiveSchema = z
  .object({
    id,
    version: z.literal(1),
    topicId: id,
    title: z.string().min(1).max(200),
    statement: z.string().min(1).max(2000),
    excludes: z.array(z.string().min(1).max(500)).min(1).max(20),
    readiness: z
      .array(
        z
          .object({
            objective: id,
            version: z.literal(1),
            strength: z.enum(["recommended", "for-route"]),
            route: id.optional(),
          })
          .strict(),
      )
      .max(20),
    learn: z.array(ref).min(1).max(20),
    practice: z.array(id).min(1).max(10),
    kits: z.array(id).max(5),
    specializations: z.array(z.string().max(100)).max(10),
  })
  .strict();
export const registrySchema = z
  .object({
    schema: z.literal("corelab-objectives/1"),
    objectives: z.array(objectiveSchema).min(1).max(500),
    paths: z
      .array(
        z
          .object({
            id,
            title: z.string().max(200),
            objectives: z.array(id).min(1).max(100),
          })
          .strict(),
      )
      .max(20),
  })
  .strict();
export type Objective = z.infer<typeof objectiveSchema>;
export function validateObjectives(input: unknown) {
  const registry = registrySchema.parse(input),
    c = catalog();
  const ids = new Set(registry.objectives.map((o) => o.id));
  if (ids.size !== registry.objectives.length)
    throw new Error("Duplicate objective ID");
  const kitIds = new Set(kits().map((k) => String(k.id)));
  for (const o of registry.objectives) {
    if (!topicMap[o.topicId]) throw new Error("Unknown objective topic");
    const routes = new Set(
      o.practice.flatMap(
        (id) => c.families.find((f) => f.id === id)?.routes ?? [],
      ),
    );
    if (
      new Set(o.readiness.map((r) => r.objective)).size !== o.readiness.length
    )
      throw new Error("Duplicate readiness reference");
    for (const r of o.readiness)
      if (
        !ids.has(r.objective) ||
        (r.strength === "for-route" && (!r.route || !routes.has(r.route)))
      )
        throw new Error("Dangling readiness or route");
    for (const family of o.practice)
      if (
        !c.families
          .find((f) => f.id === family)
          ?.items.some((i) => i.objectiveId === o.id)
      )
        throw new Error("Dangling practice reference");
    for (const kit of o.kits)
      if (!kitIds.has(kit)) throw new Error("Dangling kit reference");
    for (const ref of o.learn) {
      if (ref.type === "lesson" && !topicMap[ref.topic])
        throw new Error("Dangling lesson topic");
      if (
        ref.type === "bridge" &&
        !existsSync(path.join(process.cwd(), bridgeFile(ref.id)))
      )
        throw new Error("Dangling bridge");
      if (
        (ref.type === "visualization" || ref.type === "illustration") &&
        !getLesson(ref.topic)
      )
        throw new Error("Media needs an existing lesson");
      if (
        ref.type === "video" &&
        !videoRegistry.videos.some((v) => v.id === ref.id)
      )
        throw new Error("Dangling video");
    }
  }
  const active = new Set<string>(),
    done = new Set<string>();
  const byId = new Map(registry.objectives.map((o) => [o.id, o]));
  function visit(id: string) {
    if (active.has(id)) throw new Error("Readiness cycle");
    if (done.has(id)) return;
    active.add(id);
    for (const r of byId.get(id)!.readiness) visit(r.objective);
    active.delete(id);
    done.add(id);
  }
  for (const id of ids) visit(id);
  for (const p of registry.paths) {
    if (
      new Set(p.objectives).size !== p.objectives.length ||
      p.objectives.some((id) => !ids.has(id))
    )
      throw new Error("Invalid optional path");
  }
  return registry;
}
let cached: ReturnType<typeof validateObjectives> | undefined;
export function objectives() {
  return (cached ??= validateObjectives(
    strictJSON(
      readFileSync(
        path.join(process.cwd(), "content/v2/objectives.v1.json"),
        "utf8",
      ),
    ),
  ));
}
// Original V2 teaching bridges live at content/v2/bridges/<id>.v1.md.
export function bridgeFile(bridgeId: string) {
  if (!id.safeParse(bridgeId).success) throw new Error("Invalid bridge id");
  return "content/v2/bridges/" + bridgeId + ".v1.md";
}
export function bridgeText(bridgeId = "radians-trig") {
  return readFileSync(path.join(process.cwd(), bridgeFile(bridgeId)), "utf8");
}
export function bridgeIds() {
  return [
    ...new Set(
      objectives().objectives.flatMap((o) =>
        o.learn.flatMap((r) => (r.type === "bridge" ? [r.id] : [])),
      ),
    ),
  ];
}
export function curriculumPreview() {
  // Advisory projection only. Never feeds v1 mastery, recommendations or evidence.
  const raw = z
    .object({
      schema: z.literal("corelab-curriculum-preview/1"),
      status: z.literal("advisory-planning-only"),
      sourceHash: z.string().length(64),
      nodes: z
        .array(z.object({ id, prerequisites: z.array(id) }).strict())
        .length(176),
    })
    .strict()
    .parse(
      strictJSON(
        readFileSync(
          path.join(process.cwd(), "content/v2/curriculum-planning.v1.json"),
          "utf8",
        ),
      ),
    );
  const ids = new Set(raw.nodes.map((n) => n.id));
  if (
    ids.size !== raw.nodes.length ||
    Object.keys(topicMap).some((id) => !ids.has(id))
  )
    throw new Error("Curriculum identities missing");
  const visited = new Set<string>(),
    visiting = new Set<string>(),
    byId = new Map(raw.nodes.map((n) => [n.id, n]));
  function visit(id: string) {
    if (visiting.has(id)) throw new Error("Curriculum preview cycle");
    if (visited.has(id)) return;
    const n = byId.get(id);
    if (!n) throw new Error("Dangling curriculum prerequisite");
    visiting.add(id);
    n.prerequisites.forEach(visit);
    visiting.delete(id);
    visited.add(id);
  }
  ids.forEach(visit);
  return raw;
}

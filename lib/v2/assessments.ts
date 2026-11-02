import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import {
  itemSchema,
  gradeItem,
  normalizedAnswers,
  publicItem,
  type Item,
  catalog,
  itemFingerprint,
  archivedFamilies,
  canonicalInputs,
} from "./content";
import {
  canonical,
  hash,
  id,
  strictJSON,
  V2Error,
  fingerprint,
} from "./contracts";

const checkSchema = z
  .object({
    task: itemSchema,
    dimension: z.enum(["C", "M"]),
    critical: z.boolean(),
  })
  .strict();
const variantSchema = z
  .object({ id, items: z.array(checkSchema).min(1).max(20) })
  .strict();
const sourceSchema = z
  .object({
    id,
    version: z.literal(1),
    kind: z.enum(["form", "review_pool"]),
    variants: z.array(variantSchema).min(1).max(100),
    rights: z
      .object({
        status: z.literal("original"),
        author: z.string(),
        license: z.literal("CC-BY-4.0"),
      })
      .strict(),
  })
  .strict();
const approval = z
  .object({
    status: z.enum(["pending", "approved"]),
    reviewer: z.string().min(1).nullable(),
    date: z.iso.date().nullable(),
  })
  .strict();
const indexSchema = z
  .object({
    schema: z.literal("corelab-verify-catalog/1"),
    sources: z
      .array(
        z
          .object({
            id,
            version: z.literal(1),
            title: z.string().min(1).max(120).optional(),
            review: approval,
          })
          .strict(),
      )
      .max(100),
  })
  .strict();
export type Variant = z.infer<typeof variantSchema>;
export type CMSource = z.infer<typeof sourceSchema> & {
  hash: string;
  review: z.infer<typeof approval>;
  title: string;
};
export type SourceResolver = (
  id: string,
  version: number,
) => CMSource | undefined;
let cached: CMSource[] | undefined;
export function cmSources() {
  if (cached) return cached;
  const index = indexSchema.parse(
    strictJSON(
      readFileSync(
        path.join(process.cwd(), "content/v2/assessments.v1.json"),
        "utf8",
      ),
    ),
  );
  cached = index.sources.map((entry) => {
    const raw = readFileSync(
      path.join(process.cwd(), "content/verify", entry.id + ".v1.json"),
      "utf8",
    );
    const source = sourceSchema.parse(strictJSON(raw));
    if (source.id !== entry.id)
      throw new Error("Assessment source identity mismatch");
    const variantIds = new Set(source.variants.map((v) => v.id));
    if (variantIds.size !== source.variants.length)
      throw new Error("Duplicate form variant");
    for (const variant of source.variants) {
      if (source.kind === "review_pool" && variant.items.length !== 1)
        throw new Error("A retrieval variant contains exactly one item");
      if (
        Buffer.byteLength(canonical(freezeVariant(variant, source.kind))) >
        16384
      )
        throw new Error("Frozen form exceeds 16 KiB");
    }
    return {
      ...source,
      hash: hash(raw),
      review: entry.review,
      title: entry.title ?? source.id,
    };
  });
  return cached;
}
export const resolveCM: SourceResolver = (id, version) =>
  cmSources().find((s) => s.id === id && s.version === version);
export function independentlyReviewed(source: CMSource) {
  return (
    source.review.status === "approved" &&
    !!source.review.reviewer &&
    !!source.review.date &&
    source.review.date <= new Date().toISOString().slice(0, 10)
  );
}
export function freezeVariant(variant: Variant, kind: "form" | "review_pool") {
  return {
    kind,
    variant: variant.id,
    items: variant.items.map((c) => ({
      ...publicItem(c.task),
      dimension: c.dimension,
      critical: c.critical,
    })),
  };
}
export const frozenSchema = z
  .object({
    kind: z.enum(["form", "review_pool"]),
    variant: id,
    items: z
      .array(
        z
          .object({
            id,
            route: id,
            difficulty: z.number().int().min(1).max(5),
            objectiveId: id,
            prompt: z.string().max(6000),
            fields: z
              .array(
                z
                  .object({
                    id: z.string(),
                    label: z.string().max(200),
                    kind: z.enum(["number", "angle", "choice"]),
                    options: z.array(z.string()).optional(),
                    tolerance: z.number().finite().positive(),
                  })
                  .strict(),
              )
              .min(1)
              .max(16),
            dimension: z.enum(["C", "M"]),
            critical: z.boolean(),
          })
          .strict(),
      )
      .min(1)
      .max(20),
    basis: z
      .object({
        evidenceId: id,
        dimension: z.enum(["C", "M"]),
        token: z.string().length(64),
      })
      .strict()
      .optional(),
  })
  .strict();
export type Frozen = z.infer<typeof frozenSchema>;
export function compositeItem(frozen: Frozen, sourceId: string) {
  return {
    id: sourceId + "." + frozen.variant,
    route: frozen.variant,
    difficulty: 2,
    objectiveId:
      frozen.items.length === 1
        ? frozen.items[0].objectiveId
        : "Multiple objective scopes",
    prompt: frozen.items.map((c, i) => i + 1 + ". " + c.prompt).join("\n\n"),
    fields: frozen.items.flatMap((c, i) =>
      c.fields.map((f) => ({
        ...f,
        id: i + "." + f.id,
        label: i + 1 + ". " + f.label + " · " + c.dimension,
      })),
    ),
  };
}
export function answersFor(answers: Record<string, string>, index: number) {
  return Object.fromEntries(
    Object.entries(answers)
      .filter(([key]) => key.startsWith(index + "."))
      .map(([key, value]) => [key.slice(key.indexOf(".") + 1), value]),
  );
}
export function normalizeCM(variant: Variant, answers: Record<string, string>) {
  const expected = new Set(
    variant.items.flatMap((c, i) => c.task.fields.map((_, j) => i + "." + j)),
  );
  if (
    Object.keys(answers).length !== expected.size ||
    Object.keys(answers).some((k) => !expected.has(k))
  )
    throw new V2Error(
      "answer_format",
      "Complete exactly the requested form fields",
    );
  return variant.items.map((c, i) =>
    normalizedAnswers(c.task, answersFor(answers, i)),
  );
}
export function gradeCM(variant: Variant, answers: Record<string, string>) {
  normalizeCM(variant, answers);
  const questions = variant.items.map((c, i) => ({
    check: c,
    grade: gradeItem(c.task, answersFor(answers, i)),
  }));
  const fields = questions.flatMap((q, i) =>
    q.grade.fields.map((f) => ({
      ...f,
      id: i + "." + f.id,
      label: i + 1 + ". " + f.label,
    })),
  );
  return {
    fields,
    correct: fields.filter((f) => f.correct).length,
    total: fields.length,
    passed: questions.every((q) => q.grade.passed),
    solution: questions
      .map((q, i) => i + 1 + ". " + q.grade.solution)
      .join("\n\n"),
    remediation:
      "Review the specific objective gaps; a global form score does not grant any failed scope.",
  };
}
// Explicit aliases for the first draft's operator IDs. Cosmetic variant IDs and
// source names cannot reset exact mathematical exposure.
let semanticIndex: Map<string, Set<string>> | undefined;
function semanticKey(item: Item) {
  let structure = item.structure,
    inputs = item.inputs;
  if (structure.startsWith("X11.R04.planar-fk."))
    structure = "planar-2r.pose@1";
  if (structure === "planar-2r.transform@1") structure = "planar-2r.pose@1";
  if (structure.startsWith("X10.R03.compose-invert-se2."))
    structure = "se2.compose.translation@1";
  if (structure.startsWith("X10.R03.rotation-validity."))
    structure = "rotation.proper@1";
  if (structure.startsWith("X10.M12.frame-labels.")) {
    structure = "frame.labels." + String(inputs.query) + "@1";
    inputs = { query: inputs.query };
  }
  if (
    structure.startsWith("X10.M12.point-vs-direction.") ||
    structure === "point-direction.apply@1"
  ) {
    structure = "point-direction.apply@1";
    inputs = {
      theta: inputs.theta,
      translation: inputs.translation,
      vector: inputs.vector ?? inputs.point,
    };
  }
  return canonical({ structure, inputs: canonicalInputs(inputs) });
}
export function fingerprintCandidates(item: Item) {
  if (!semanticIndex) {
    semanticIndex = new Map();
    const items = [
      ...catalog().families.flatMap((f) => f.items),
      ...archivedFamilies().flatMap((f) => f.items),
      ...cmSources().flatMap((s) =>
        s.variants.flatMap((v) => v.items.map((c) => c.task)),
      ),
    ];
    for (const candidate of items) {
      const key = semanticKey(candidate),
        group = semanticIndex.get(key) ?? new Set<string>();
      group.add(itemFingerprint(candidate));
      group.add(fingerprint(candidate.structure, candidate.inputs));
      semanticIndex.set(key, group);
    }
  }
  return [
    ...new Set([
      itemFingerprint(item),
      fingerprint(item.structure, item.inputs),
      ...(semanticIndex.get(semanticKey(item)) ?? []),
    ]),
  ];
}

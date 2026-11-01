import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import { topicMap } from "../curriculum";
import {
  canonical,
  fingerprint,
  hash,
  id,
  numberAnswer,
  V2Error,
} from "./contracts";

const fieldSchema = z
  .object({
    label: z.string().min(1).max(200),
    kind: z.enum(["number", "angle", "choice"]),
    answer: z.string().min(1).max(200),
    tolerance: z.number().finite().positive().max(0.01),
    options: z.array(z.string().min(1).max(200)).min(2).max(8).optional(),
  })
  .strict();
export const itemSchema = z
  .object({
    id,
    route: id,
    difficulty: z.number().int().min(1).max(5),
    structure: id,
    inputs: z.record(z.string(), z.unknown()),
    objectiveId: id,
    prompt: z.string().min(10).max(6000),
    fields: z.array(fieldSchema).min(1).max(16),
    solution: z.string().min(1).max(6000),
    hints: z.array(z.string().min(1).max(6000)).length(3),
    remediation: z.string().max(2000),
  })
  .strict();
const familySchema = z
  .object({
    id,
    version: z.literal(1),
    title: z.string().max(200),
    domain: z.string().max(100),
    topicId: id,
    objectiveId: id,
    routes: z.array(id).min(2).max(6),
    scope: z.string().max(1000),
    labIds: z.array(id),
    items: z.array(itemSchema).min(2).max(200),
    review: z
      .object({
        status: z.enum(["pending", "approved"]),
        reviewer: z.string().min(1).nullable(),
        date: z.iso.date().nullable(),
      })
      .strict(),
    rights: z
      .object({
        status: z.literal("original"),
        author: z.string(),
        license: z.literal("CC-BY-4.0"),
        sources: z.array(z.string()),
      })
      .strict(),
  })
  .strict();
const catalogSchema = z
  .object({
    schema: z.literal("corelab-exercise/1"),
    version: z.literal(1),
    reviewStatus: z.string(),
    families: z
      .array(
        z
          .object({
            id,
            version: z.literal(1),
            review: familySchema.shape.review,
          })
          .strict(),
      )
      .min(1)
      .max(50),
    manualActivities: z.array(
      z
        .object({
          id,
          topicId: id,
          title: z.string(),
          instructions: z.string(),
          status: z.literal("manual-unverified"),
        })
        .strict(),
    ),
  })
  .strict();
export type Item = z.infer<typeof itemSchema>;
export type Family = z.infer<typeof familySchema>;
let cached:
  | {
      families: Family[];
      manualActivities: z.infer<typeof catalogSchema>["manualActivities"];
      hash: string;
      sourceHashes: Record<string, string>;
    }
  | undefined;
export function catalog() {
  if (cached) return cached;
  const raw = readFileSync(
    path.join(process.cwd(), "content/v2/catalog.v1.json"),
    "utf8",
  );
  const parsed = catalogSchema.parse(JSON.parse(raw));
  const sourceHashes: Record<string, string> = {};
  const families = parsed.families.map((entry) => {
    const source = readFileSync(
      path.join(process.cwd(), "content/exercises", entry.id + ".v1.json"),
      "utf8",
    );
    sourceHashes[entry.id] = hash(source);
    const contract = familySchema
      .omit({ review: true })
      .parse(JSON.parse(source));
    if (contract.id !== entry.id || contract.version !== entry.version)
      throw new Error("Source identity mismatch");
    return { ...contract, review: entry.review };
  });
  const ids = new Set<string>();
  for (const f of families) {
    if (!topicMap[f.topicId])
      throw new Error("Unknown catalog topic " + f.topicId);
    if (
      f.review.status === "approved" &&
      (!f.review.reviewer || !f.review.date)
    )
      throw new Error("Missing independent review record");
    for (const item of f.items) {
      if (ids.has(item.id) || !f.routes.includes(item.route))
        throw new Error("Duplicate item or unknown route");
      ids.add(item.id);
      canonical(item.inputs);
      for (const field of item.fields) {
        if (field.kind === "choice") {
          if (
            !field.options?.includes(field.answer) ||
            new Set(field.options).size !== field.options.length
          )
            throw new Error("Invalid choice contract");
        } else if (!Number.isFinite(Number(field.answer)))
          throw new Error("Invalid numeric oracle");
      }
    }
  }
  cached = {
    families,
    manualActivities: parsed.manualActivities,
    hash: hash(raw),
    sourceHashes,
  };
  return cached;
}
export function family(id: string) {
  return catalog().families.find((f) => f.id === id);
}
export function familyHash(f: Family) {
  return catalog().sourceHashes[f.id];
}
export function itemFingerprint(item: Item) {
  return fingerprint(item.structure, item.inputs);
}
export function publicItem(item: Item) {
  return {
    id: item.id,
    route: item.route,
    difficulty: item.difficulty,
    objectiveId: item.objectiveId,
    prompt: item.prompt,
    fields: item.fields.map(({ label, kind, options, tolerance }, i) => ({
      id: String(i),
      label,
      kind,
      ...(options ? { options } : {}),
      tolerance,
    })),
  };
}
export function normalizedAnswers(item: Item, answers: Record<string, string>) {
  if (
    Object.keys(answers).length !== item.fields.length ||
    Object.keys(answers).some(
      (k) => !item.fields[Number(k)] || String(Number(k)) !== k,
    )
  )
    throw new V2Error(
      "answer_format",
      "Complete exactly the requested answer fields",
    );
  return item.fields.map((f, i) => {
    const a = answers[String(i)]?.trim();
    if (!a || a.length > 200)
      throw new V2Error("answer_format", "Complete " + f.label);
    if (f.kind === "choice") {
      if (!f.options?.includes(a))
        throw new V2Error("answer_format", "Choose a listed option");
      return a;
    }
    const { n, d } = numberAnswer(a);
    return { n, d };
  });
}
export function gradeItem(item: Item, answers: Record<string, string>) {
  normalizedAnswers(item, answers);
  const fields = item.fields.map((f, i) => {
    const answer = answers[String(i)].trim();
    let correct = false;
    if (f.kind === "choice") correct = answer === f.answer;
    else {
      const actual = numberAnswer(answer).value,
        expected = Number(f.answer);
      const error =
        f.kind === "angle"
          ? Math.abs(
              Math.atan2(
                Math.sin(actual - expected),
                Math.cos(actual - expected),
              ),
            )
          : Math.abs(actual - expected);
      correct = error <= f.tolerance;
    }
    return { id: String(i), label: f.label, correct, expected: f.answer };
  });
  return {
    fields,
    correct: fields.filter((f) => f.correct).length,
    total: fields.length,
    passed: fields.every((f) => f.correct),
    solution: item.solution,
    remediation: item.remediation,
  };
}

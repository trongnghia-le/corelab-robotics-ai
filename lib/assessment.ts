import { z } from "zod";
import type { Assessment, Attempt, Question, KnowledgeType } from "./types";
export const knowledgeTypes = [
  "concept",
  "procedure",
  "implementation",
  "design",
] as const;
export const mistakeCategories = [
  "conceptual",
  "mathematical",
  "procedural",
  "implementation",
  "method_selection",
  "retention",
] as const;
export const knowledgeTypeInfo = {
  concept: {
    label: "CONCEPT",
    goal: "Understand the principle",
    method: "Explain, identify assumptions, and distinguish misconceptions.",
  },
  procedure: {
    label: "PROCEDURE",
    goal: "Perform the calculation",
    method: "Calculate, show the steps, and verify the numerical result.",
  },
  implementation: {
    label: "IMPLEMENTATION",
    goal: "Build and verify",
    method: "Implement independently and run the supported local tests.",
  },
  design: {
    label: "DESIGN",
    goal: "Choose and justify",
    method:
      "Analyze a scenario, compare alternatives, and justify trade-offs with a rubric.",
  },
} as const;
const ref = z
  .object({
    label: z.string().min(1),
    href: z
      .string()
      .refine(
        (s) =>
          /^\/lessons\/[A-Z]+\d+(?:#[a-z0-9-]+)?$/.test(s) ||
          /^https:\/\//.test(s),
        "Expected a lesson link or HTTPS resource",
      ),
  })
  .strict();
export const questionMetadataSchema = z
  .object({
    knowledgeType: z.enum(knowledgeTypes).optional(),
    skillTags: z
      .array(z.string().regex(/^[a-z0-9][a-z0-9-]*$/))
      .min(1)
      .optional(),
    skillLabel: z.string().min(1).optional(),
    relatedPrerequisites: z.array(z.string()).optional(),
    mistakeCategory: z.enum(mistakeCategories).optional(),
    recommendedMethod: z.string().min(1).optional(),
    remediationRefs: z.array(ref).optional(),
    verifiedLabTopicId: z.enum(["M02", "PY01"]).optional(),
    equivalentTo: z.array(z.string()).optional(),
  })
  .strict();
export const assessmentSchema = z
  .object({
    id: z.string().min(1),
    topicId: z.string().min(1),
    version: z.number().int().positive(),
    questions: z
      .array(
        z.object({
          id: z.string().min(1),
          prompt: z.string().min(1),
          kind: z.enum(["choice", "number", "short"]),
          dimension: z.enum(["C", "M", "I", "T"]),
          critical: z.boolean(),
          options: z.array(z.string()).optional(),
          answer: z.string().optional(),
          tolerance: z.number().nonnegative().optional(),
          explanation: z.string(),
          rubric: z.array(z.string()).optional(),
          ...questionMetadataSchema.shape,
        }),
      )
      .min(1),
  })
  .superRefine((a, ctx) => {
    const seen = new Set<string>();
    for (const q of a.questions) {
      if (seen.has(q.id))
        ctx.addIssue({ code: "custom", message: `Duplicate question ${q.id}` });
      seen.add(q.id);
      if (
        q.kind === "choice" &&
        (!q.options ||
          q.options.length < 2 ||
          !/^\d+$/.test(q.answer ?? "") ||
          Number(q.answer) >= q.options.length)
      )
        ctx.addIssue({
          code: "custom",
          message: `Invalid choice contract ${q.id}`,
        });
      if (
        q.kind === "number" &&
        (!q.answer?.trim() || !Number.isFinite(Number(q.answer)))
      )
        ctx.addIssue({
          code: "custom",
          message: `Invalid numeric contract ${q.id}`,
        });
      if (q.kind === "short" && !q.rubric?.length)
        ctx.addIssue({ code: "custom", message: `Missing rubric ${q.id}` });
    }
  });
export function knowledgeTypeFor(q: Question): KnowledgeType {
  return (
    q.knowledgeType ??
    (q.kind === "number"
      ? "procedure"
      : q.kind === "short" && q.dimension === "T"
        ? "design"
        : "concept")
  );
}
export function isObjective(q: Question) {
  return (
    q.kind !== "short" &&
    !["implementation", "design"].includes(knowledgeTypeFor(q))
  );
}
export function skillTagsFor(topicId: string, q: Question) {
  return q.skillTags ?? [`${topicId.toLowerCase()}-${q.id}`];
}
export type ContractIndex = Record<string, Assessment>;
export function contractKey(
  topicId: string,
  version: number,
  purpose = "diagnostic",
) {
  return `${purpose}:${topicId}:${version}`;
}
export function resolveAttempt(
  a: Attempt,
  catalog: ContractIndex,
): Assessment | null {
  const contract =
    catalog[contractKey(a.topicId, a.assessmentVersion, a.purpose)];
  if (!contract) return null;
  if (a.purpose !== "targeted") return contract;
  if (
    !a.skillTag ||
    !a.questionIds?.length ||
    new Set(a.questionIds).size !== a.questionIds.length
  )
    return null;
  const qs = a.questionIds.map((id) =>
    contract.questions.find((q) => q.id === id),
  );
  if (qs.some((q) => !q || !skillTagsFor(a.topicId, q).includes(a.skillTag!)))
    return null;
  return { ...contract, questions: qs as Question[] };
}

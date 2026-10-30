import { lessonMediaRegistry } from "./media";
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import { topicMap } from "./curriculum";
import type { Assessment, Lesson, Overview, PracticeSkill } from "./types";
import {
  assessmentSchema,
  questionMetadataSchema,
  knowledgeTypeFor,
  skillTagsFor,
  contractKey,
  type ContractIndex,
} from "./assessment";
const root = path.join(process.cwd(), "content");
const metaSchema = z.object({
  id: z.string(),
  module_id: z.string(),
  title: z.string(),
  summary: z.string(),
  estimated_minutes: z.number().positive(),
  prerequisites: z.array(z.string()),
  source_refs: z.array(z.object({ title: z.string(), url: z.url() })),
  objectives: z.array(z.string()).min(2),
  core_theory: z.array(z.string()),
  labs: z.array(z.string()),
  assessment_refs: z.array(z.string()),
  review_prompts: z.array(z.string()),
  extension_refs: z.array(z.string()),
});
export function lessonIds(): string[] {
  return fs
    .readdirSync(path.join(root, "lessons"))
    .filter((f) => f.endsWith(".md"))
    .map((f) => f.slice(0, -3));
}
export function getLesson(id: string): Lesson | null {
  if (!topicMap[id]) return null;
  const file = path.join(root, "lessons", `${id}.md`);
  if (!fs.existsSync(file)) return null;
  const parsed = matter(fs.readFileSync(file, "utf8"));
  return {
    meta: {
      ...metaSchema.parse(parsed.data),
      ...lessonMediaRegistry.lessons[id],
    },
    body: parsed.content,
  };
}
export function getAssessment(id: string, version = 1): Assessment | null {
  if (!topicMap[id]) return null;
  const file = path.join(root, "assessments", `${id}.v${version}.json`);
  if (!fs.existsSync(file)) return null;
  const raw = assessmentSchema.parse(JSON.parse(fs.readFileSync(file, "utf8")));
  const metadata = JSON.parse(
    fs.readFileSync(path.join(root, "assessment-metadata.v1.json"), "utf8"),
  ).contracts as Record<string, Record<string, unknown>>;
  return {
    ...raw,
    questions: raw.questions.map((q) => ({
      ...q,
      ...questionMetadataSchema.parse(
        metadata[`${id}.v${version}`]?.[q.id] ?? {},
      ),
    })),
  };
}
export function getPracticeAssessment(
  id: string,
  version = 1,
): Assessment | null {
  if (!topicMap[id]) return null;
  const file = path.join(root, "practice", `${id}.v${version}.json`);
  return fs.existsSync(file)
    ? assessmentSchema.parse(JSON.parse(fs.readFileSync(file, "utf8")))
    : null;
}
export function getAssessmentCatalog(): ContractIndex {
  const catalog: ContractIndex = {};
  for (const purpose of ["diagnostic", "targeted"] as const) {
    const directory = path.join(
      root,
      purpose === "diagnostic" ? "assessments" : "practice",
    );
    for (const file of fs.readdirSync(directory)) {
      const match = file.match(/^([A-Z]+\d+)\.v(\d+)\.json$/);
      if (!match) continue;
      const contract =
        purpose === "diagnostic"
          ? getAssessment(match[1], Number(match[2]))
          : getPracticeAssessment(match[1], Number(match[2]));
      if (contract)
        catalog[contractKey(contract.topicId, contract.version, purpose)] =
          contract;
    }
  }
  return catalog;
}
export function practiceSkills(id: string): PracticeSkill[] {
  const map = new Map<string, PracticeSkill>();
  for (const q of getPracticeAssessment(id)?.questions ?? [])
    for (const tag of skillTagsFor(id, q)) {
      const entry = map.get(tag) ?? {
        tag,
        label: q.skillLabel ?? tag,
        knowledgeTypes: [],
        questionCount: 0,
      };
      const type = knowledgeTypeFor(q);
      if (!entry.knowledgeTypes.includes(type)) entry.knowledgeTypes.push(type);
      entry.questionCount++;
      map.set(tag, entry);
    }
  return [...map.values()];
}
export function publicAssessment(a: Assessment | null): Assessment | null {
  return a
    ? {
        ...a,
        questions: a.questions.map((q) => {
          const { answer: _, tolerance: __, explanation: ___, ...safe } = q;
          return { ...safe, explanation: "" };
        }),
      }
    : null;
}
export function getOverview(id: string): Overview {
  const entries = JSON.parse(
    fs.readFileSync(path.join(root, "overviews", "topics.json"), "utf8"),
  ) as Record<string, Overview>;
  return entries[id];
}
export { sources } from "./resources";

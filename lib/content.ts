import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import { topicMap } from "./curriculum";
import type { Assessment, Lesson, Overview } from "./types";
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
  return { meta: metaSchema.parse(parsed.data), body: parsed.content };
}
export function getAssessment(id: string, version = 1): Assessment | null {
  if (!topicMap[id]) return null;
  const file = path.join(root, "assessments", `${id}.v${version}.json`);
  return fs.existsSync(file)
    ? (JSON.parse(fs.readFileSync(file, "utf8")) as Assessment)
    : null;
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

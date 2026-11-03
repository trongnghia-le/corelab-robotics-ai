import { lessonMediaRegistry } from "./media";
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import { topicMap } from "./curriculum";
import type { Assessment, Lesson, Overview, PracticeSkill } from "./types";
import { splitSections, lessonSessions } from "./lesson-plan";
import type { Lang } from "./lang";
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
function headingsOf(body: string) {
  return splitSections(body).sections.map((s) => s.heading);
}

/** Lesson in the requested language, falling back to English per lesson. */
export function getLocalizedLesson(
  id: string,
  lang: Lang = "en",
): Lesson | null {
  const base = getLesson(id);
  if (!base) return null;
  const lesson: Lesson = {
    ...base,
    sessionMinutes: Object.fromEntries(
      lessonSessions(base.body).map((s) => [s.key, s.minutes]),
    ),
  };
  if (lang === "en") return lesson;
  const file = path.join(root, "lessons", "vi", `${id}.md`);
  if (!fs.existsSync(file)) return { ...lesson, missingTranslation: true };
  try {
    const parsed = matter(fs.readFileSync(file, "utf8"));
    const english = headingsOf(lesson.body);
    if (headingsOf(parsed.content).length !== english.length)
      return { ...lesson, missingTranslation: true };
    const data = z
      .object({
        title: z.string().min(1),
        summary: z.string().min(1),
        objectives: z.array(z.string()).min(1),
      })
      .parse(parsed.data);
    return {
      meta: { ...lesson.meta, ...data },
      body: parsed.content,
      lang: "vi",
      englishHeadings: english,
      sessionMinutes: lesson.sessionMinutes,
    };
  } catch {
    return { ...lesson, missingTranslation: true };
  }
}

/** Titles of translated lessons by topic id (Vietnamese). */
export function translatedTitles(): Record<string, string> {
  const dir = path.join(root, "lessons", "vi");
  if (!fs.existsSync(dir)) return {};
  const out: Record<string, string> = {};
  for (const file of fs.readdirSync(dir).filter((f) => f.endsWith(".md"))) {
    try {
      const title = matter(fs.readFileSync(path.join(dir, file), "utf8")).data
        .title;
      if (typeof title === "string" && title.trim())
        out[file.slice(0, -3)] = title;
    } catch {}
  }
  return out;
}

type Translation = {
  prompt?: string;
  options?: string[];
  explanation?: string;
  rubric?: string[];
};

function readTranslations(
  kind: "assessments" | "practice",
  id: string,
  version: number,
): Record<string, Translation> | null {
  const file = path.join(root, "i18n", "vi", kind, `${id}.v${version}.json`);
  if (!fs.existsSync(file)) return null;
  try {
    const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
    return parsed && typeof parsed.questions === "object"
      ? parsed.questions
      : null;
  } catch {
    return null;
  }
}

/** Overlay translated display text; answers, ids, kinds and tolerances are untouched. */
export function localizeAssessment(
  a: Assessment | null,
  kind: "assessments" | "practice",
  lang: Lang,
): Assessment | null {
  if (!a || lang === "en") return a;
  const tr = readTranslations(kind, a.topicId, a.version);
  if (!tr) return a;
  return {
    ...a,
    questions: a.questions.map((q) => {
      const t = tr[q.id];
      if (!t) return q;
      return {
        ...q,
        prompt: t.prompt ?? q.prompt,
        explanation: t.explanation ?? q.explanation,
        options:
          q.options && t.options?.length === q.options.length
            ? t.options
            : q.options,
        rubric:
          q.rubric && t.rubric?.length === q.rubric.length
            ? t.rubric
            : q.rubric,
      };
    }),
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

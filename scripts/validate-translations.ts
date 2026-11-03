// Validates optional Vietnamese translations against the English source.
// Passes (with a note) when no translations exist.
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { splitSections } from "../lib/lesson-plan";

const root = path.join(process.cwd(), "content");

export function fencedBlocks(body: string): string[] {
  const out: string[] = [];
  let current: string[] | null = null;
  for (const line of body.split("\n")) {
    if (/^\s*(```|~~~)/.test(line)) {
      if (current) {
        current.push(line);
        out.push(current.join("\n"));
        current = null;
      } else current = [line];
    } else if (current) current.push(line);
  }
  return out;
}

function outsideCode(body: string) {
  return body.replace(/^\s*(```|~~~)[\s\S]*?^\s*(```|~~~)\s*$/gm, "");
}

export function imageRefs(body: string): string[] {
  return [...outsideCode(body).matchAll(/!\[[^\]]*\]\(([^)\s]+)/g)].map(
    (m) => m[1],
  );
}

const same = (a: string[], b: string[]) =>
  a.length === b.length && a.every((x, i) => x === b[i]);

export function validateLesson(english: string, translated: string): string[] {
  const errors: string[] = [];
  const en = matter(english).content;
  const { data, content } = matter(translated);
  for (const key of ["title", "summary"])
    if (typeof data[key] !== "string" || !data[key].trim())
      errors.push(`frontmatter "${key}" is missing`);
  if (
    !Array.isArray(data.objectives) ||
    !data.objectives.length ||
    data.objectives.some((o: unknown) => typeof o !== "string")
  )
    errors.push('frontmatter "objectives" must be a non-empty string array');
  const enHeads = splitSections(en).sections.length;
  const viHeads = splitSections(content).sections.length;
  if (enHeads !== viHeads)
    errors.push(`expected ${enHeads} "## " headings, found ${viHeads}`);
  if (!same(fencedBlocks(en), fencedBlocks(content)))
    errors.push("fenced code blocks differ from the English lesson");
  if (!same(imageRefs(en), imageRefs(content)))
    errors.push("image references differ from the English lesson");
  return errors;
}

type Contract = {
  questions: { id: string; options?: string[]; rubric?: string[] }[];
};
const allowed = new Set(["prompt", "options", "explanation", "rubric"]);

export function validateQuestions(english: Contract, translation: unknown) {
  const errors: string[] = [];
  const questions = (translation as { questions?: Record<string, unknown> })
    ?.questions;
  if (!questions || typeof questions !== "object")
    return ['missing top-level "questions" object'];
  const byId = new Map(english.questions.map((q) => [q.id, q]));
  for (const [id, raw] of Object.entries(questions)) {
    const q = byId.get(id);
    if (!q) {
      errors.push(`question "${id}" does not exist in the English contract`);
      continue;
    }
    const t = raw as Record<string, unknown>;
    for (const key of Object.keys(t))
      if (!allowed.has(key))
        errors.push(`${id}: field "${key}" is not allowed`);
    if (t.options !== undefined) {
      const options = t.options as unknown[];
      if (
        !Array.isArray(options) ||
        options.some((o) => typeof o !== "string") ||
        options.length !== (q.options?.length ?? -1)
      )
        errors.push(
          `${id}: expected ${q.options?.length ?? 0} options, found ${Array.isArray(options) ? options.length : "invalid"}`,
        );
    }
    if (t.rubric !== undefined) {
      const rubric = t.rubric as unknown[];
      if (
        !Array.isArray(rubric) ||
        rubric.some((o) => typeof o !== "string") ||
        rubric.length !== (q.rubric?.length ?? -1)
      )
        errors.push(`${id}: rubric must be strings matching the English count`);
    }
    for (const key of ["prompt", "explanation"])
      if (t[key] !== undefined && typeof t[key] !== "string")
        errors.push(`${id}: "${key}" must be a string`);
  }
  return errors;
}

function list(dir: string, ext: string) {
  return fs.existsSync(dir)
    ? fs.readdirSync(dir).filter((f) => f.endsWith(ext))
    : [];
}

export function validateAll(contentRoot = root) {
  const errors: string[] = [];
  let count = 0;
  const lessons = path.join(contentRoot, "lessons");
  for (const file of list(path.join(lessons, "vi"), ".md")) {
    count++;
    const source = path.join(lessons, file);
    if (!fs.existsSync(source)) {
      errors.push(`lessons/vi/${file}: no English lesson ${file}`);
      continue;
    }
    for (const e of validateLesson(
      fs.readFileSync(source, "utf8"),
      fs.readFileSync(path.join(lessons, "vi", file), "utf8"),
    ))
      errors.push(`lessons/vi/${file}: ${e}`);
  }
  for (const [kind, folder] of [
    ["assessments", "assessments"],
    ["practice", "practice"],
  ] as const) {
    const dir = path.join(contentRoot, "i18n", "vi", kind);
    for (const file of list(dir, ".json")) {
      count++;
      const label = `i18n/vi/${kind}/${file}`;
      const source = path.join(contentRoot, folder, file);
      if (!fs.existsSync(source)) {
        errors.push(`${label}: no English contract ${folder}/${file}`);
        continue;
      }
      try {
        for (const e of validateQuestions(
          JSON.parse(fs.readFileSync(source, "utf8")),
          JSON.parse(fs.readFileSync(path.join(dir, file), "utf8")),
        ))
          errors.push(`${label}: ${e}`);
      } catch (e) {
        errors.push(`${label}: ${(e as Error).message}`);
      }
    }
  }
  return { errors, count };
}

if (process.argv[1]?.endsWith("validate-translations.ts")) {
  const { errors, count } = validateAll();
  if (errors.length) {
    console.error(errors.join("\n"));
    console.error(`\n${errors.length} translation problem(s).`);
    process.exit(1);
  }
  console.log(
    `Translations OK (${count} file${count === 1 ? "" : "s"} checked).`,
  );
}

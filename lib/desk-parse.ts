// Pulls the pieces the study desk needs out of a lesson body: numbered
// exercises with their answers, and the lab's starter and test code.
// Translated bodies keep the English heading order, so sections are matched
// by index through `englishHeadings` (see lib/lesson-plan.ts).
import { splitSections } from "./lesson-plan";

export type DeskExercise = { n: number; text: string; answer?: string };
export type DeskCode = { lang: string; code: string };

function slug(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function section(body: string, english: string, englishHeadings?: string[]) {
  const { sections } = splitSections(body);
  return sections.find(
    (s) => slug(englishHeadings?.[s.index] ?? s.heading) === english,
  )?.markdown;
}

/** Top-level numbered items (`1. ...`) with their continuation lines. */
export function numberedItems(markdown: string) {
  const items = new Map<number, string>();
  let current: number | null = null;
  let fence = false;
  for (const line of markdown.split("\n").slice(1)) {
    if (/^\s*(```|~~~)/.test(line)) fence = !fence;
    const m = !fence && line.match(/^(\d+)\.\s+(.*)$/);
    if (m) {
      current = Number(m[1]);
      items.set(current, m[2]);
    } else if (current !== null && !/^#{2,3} /.test(line))
      items.set(current, `${items.get(current)}\n${line}`);
  }
  for (const [n, text] of items) items.set(n, text.trim());
  return items;
}

export function deskExercises(
  body: string,
  englishHeadings?: string[],
): DeskExercise[] {
  const exercises = numberedItems(
    section(body, "exercises", englishHeadings) ?? "",
  );
  const answers = numberedItems(
    section(body, "exercise-answers", englishHeadings) ?? "",
  );
  return [...exercises].map(([n, text]) => ({
    n,
    text,
    answer: answers.get(n),
  }));
}

/** Code blocks under `### <title>` inside the Independent practice section. */
export function labCode(body: string, title: "Starter code" | "Tests") {
  const practice =
    section(body, "independent-practice") ??
    section(body, "independent-practice-and-transfer") ??
    "";
  const part = practice.split(/\n### /).find((p) => p.startsWith(title));
  if (!part) return [];
  return [...part.matchAll(/```([\w+-]*)\n([\s\S]*?)```/g)].map((m) => ({
    lang: m[1] || "text",
    code: m[2],
  }));
}

function extension(lang: string) {
  if (/^c$/i.test(lang)) return "c";
  if (/^(cpp|c\+\+|cc|cxx)$/i.test(lang)) return "cpp";
  if (/^(py|python|python3)$/i.test(lang)) return "py";
  return null;
}

/**
 * The lab as runnable files. Lessons say "paste the tests below the starter
 * code (same file)", so each language becomes one file: starter, then tests.
 */
export function labFiles(body: string) {
  const files = new Map<string, string[]>();
  const add = (blocks: DeskCode[], label: string) => {
    for (const b of blocks) {
      const ext = extension(b.lang);
      if (!ext) continue;
      const comment = ext === "py" ? "#" : "//";
      const parts = files.get(ext) ?? [];
      parts.push(`${comment} --- ${label} (from the lesson) ---\n${b.code}`);
      files.set(ext, parts);
    }
  };
  add(labCode(body, "Starter code"), "Starter code");
  add(labCode(body, "Tests"), "Tests");
  return [...files].map(([ext, parts]) => ({
    name: `lab.${ext}`,
    content: parts.join("\n\n"),
  }));
}

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  dictionaries,
  formatDuration,
  localizeRecommendation,
  translate,
} from "../lib/i18n";
import {
  fencedBlocks,
  imageRefs,
  validateAll,
  validateLesson,
  validateQuestions,
} from "../scripts/validate-translations";

const english = `---
id: X
---
## Intuition
Text ![fig](/lesson-figures/X.svg)
\`\`\`python
## not a heading
x = 1
\`\`\`
## Exercises
1. **(Easy)** a
`;
const front = '---\n{"title":"T","summary":"S","objectives":["a"]}\n---\n';

describe("Vietnamese UI dictionary", () => {
  it("defines every English key with the same placeholders", () => {
    const en = dictionaries.en,
      vi = dictionaries.vi;
    expect(Object.keys(vi).sort()).toEqual(Object.keys(en).sort());
    const holes = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort();
    for (const key of Object.keys(en) as (keyof typeof en)[]) {
      expect(vi[key].trim(), key).not.toBe("");
      expect(holes(vi[key]), key).toEqual(holes(en[key]));
    }
  });
  it("interpolates and formats durations", () => {
    expect(translate("vi", "lesson.sessionsDone", { n: 1, total: 4 })).toBe(
      "1/4 buổi",
    );
    expect(formatDuration(330, "en")).toBe("5 h 30 min");
    expect(formatDuration(45, "en")).toBe("45 min");
    expect(formatDuration(120, "en")).toBe("2 h");
    expect(formatDuration(65, "vi")).toBe("1 giờ 5 phút");
  });
});

describe("recommendation text", () => {
  it("translates the sentences the engine produces and leaves others alone", () => {
    const samples = [
      "Practice Dot product: 3 recorded mistakes. Focus on this skill rather than repeating the lesson.",
      "Review due: check retention without viewing the solution.",
      "The latest attempt revealed a gap; read the feedback and try again independently.",
      "You have shown you understand the concepts; next, implement independently and test your work.",
      "A foundation needed for your pinned goal R04; its prerequisites are now mastered.",
      "Its prerequisites are mastered. This is the next step in building your foundations.",
      "Not started yet. Begin with a foundation that has no prerequisites.",
      "Review the linked reasoning and solve a fresh focused set with no help (A0). Focused correction is separate from mastering the whole topic.",
      "Implement the assignment independently, run local tests, and import the report.",
      "Take the short check first with no help (A0); study and address gaps after your attempt.",
    ];
    for (const sample of samples) {
      const out = localizeRecommendation(sample, "vi");
      expect(out, sample).not.toBe(sample);
      expect(localizeRecommendation(sample, "en")).toBe(sample);
    }
    expect(localizeRecommendation("Something else", "vi")).toBe(
      "Something else",
    );
  });
  it("keeps the engine sentences in sync with the translator", async () => {
    const source = (await import("node:fs")).readFileSync(
      "lib/engine.ts",
      "utf8",
    );
    expect(source).toContain("Take the short check first with no help (A0)");
    expect(source).toContain("Not started yet. Begin with a foundation");
  });
});

describe("translation validator", () => {
  it("extracts fenced blocks and images", () => {
    expect(fencedBlocks(english)).toHaveLength(1);
    expect(imageRefs(english)).toEqual(["/lesson-figures/X.svg"]);
  });
  it("accepts a faithful translation", () => {
    const vi = `${front}## Trực giác\nVăn bản ![fig](/lesson-figures/X.svg)\n\`\`\`python\n## not a heading\nx = 1\n\`\`\`\n## Bài tập\n1. **(Easy)** b\n`;
    expect(validateLesson(english, vi)).toEqual([]);
  });
  it("rejects changed headings, code, images and frontmatter", () => {
    const bad = `---\n{"title":"T"}\n---\n## Một\n![x](/other.svg)\n\`\`\`python\nx = 2\n\`\`\`\n`;
    const errors = validateLesson(english, bad).join("\n");
    expect(errors).toMatch(/summary/);
    expect(errors).toMatch(/objectives/);
    expect(errors).toMatch(/expected 2/);
    expect(errors).toMatch(/code blocks/);
    expect(errors).toMatch(/image/);
  });
  it("checks question ids, option counts and forbidden fields", () => {
    const contract = {
      questions: [
        { id: "q1", options: ["a", "b", "c"] },
        { id: "q2", rubric: ["r1"] },
      ],
    };
    expect(
      validateQuestions(contract, {
        questions: { q1: { prompt: "p", options: ["x", "y", "z"] } },
      }),
    ).toEqual([]);
    const errors = validateQuestions(contract, {
      questions: {
        q1: { options: ["x"], answer: "1" },
        q9: { prompt: "p" },
        q2: { rubric: ["a", "b"] },
      },
    }).join("\n");
    expect(errors).toMatch(/expected 3 options/);
    expect(errors).toMatch(/"answer" is not allowed/);
    expect(errors).toMatch(/q9/);
    expect(errors).toMatch(/rubric/);
  });
  it("passes when no translations exist", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "corelab-i18n-"));
    fs.mkdirSync(path.join(dir, "lessons"), { recursive: true });
    expect(validateAll(dir)).toEqual({ errors: [], count: 0 });
  });
  it("passes for every translation currently in the repository", () => {
    expect(validateAll().errors).toEqual([]);
  });
});

describe("localized content", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });
  it("serves a valid translation, and falls back per lesson otherwise", async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "corelab-vi-"));
    const real = path.join(process.cwd(), "content");
    const lessons = path.join(dir, "content", "lessons");
    fs.mkdirSync(path.join(lessons, "vi"), { recursive: true });
    for (const id of ["M01", "M02"])
      fs.copyFileSync(
        path.join(real, "lessons", `${id}.md`),
        path.join(lessons, `${id}.md`),
      );
    const source = fs.readFileSync(path.join(lessons, "M01.md"), "utf8");
    const body = source
      .split(/^---\s*$/m)
      .slice(2)
      .join("---");
    const viBody = body.replace(/^## (.*)$/gm, "## $1 (vi)");
    fs.writeFileSync(path.join(lessons, "vi", "M01.md"), `${front}${viBody}`);
    // A broken translation (wrong heading count) must fall back to English.
    fs.writeFileSync(
      path.join(lessons, "vi", "M02.md"),
      `${front}## Only one\n`,
    );
    vi.spyOn(process, "cwd").mockReturnValue(dir);
    vi.resetModules();
    const content = await import("../lib/content");
    const en = content.getLocalizedLesson("M01", "en")!;
    expect(en.lang).toBeUndefined();
    const vn = content.getLocalizedLesson("M01", "vi")!;
    expect(vn.lang).toBe("vi");
    expect(vn.meta.title).toBe("T");
    expect(vn.meta.id).toBe(en.meta.id);
    expect(vn.englishHeadings).toHaveLength(
      (en.body.match(/^## /gm) ?? []).length,
    );
    const broken = content.getLocalizedLesson("M02", "vi")!;
    expect(broken.missingTranslation).toBe(true);
    expect(broken.body).toBe(content.getLesson("M02")!.body);
  });
  it("overlays question text without touching answers or ids", async () => {
    const content = await import("../lib/content");
    const base = {
      id: "A",
      topicId: "M01",
      version: 1,
      questions: [
        {
          id: "q1",
          prompt: "P",
          kind: "choice" as const,
          dimension: "C" as const,
          critical: true,
          options: ["a", "b"],
          answer: "1",
          explanation: "E",
        },
      ],
    };
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "corelab-q-"));
    fs.mkdirSync(path.join(dir, "content", "i18n", "vi", "assessments"), {
      recursive: true,
    });
    fs.writeFileSync(
      path.join(dir, "content", "i18n", "vi", "assessments", "M01.v1.json"),
      JSON.stringify({
        questions: {
          q1: { prompt: "Hỏi", options: ["x"], explanation: "Giải" },
        },
      }),
    );
    vi.spyOn(process, "cwd").mockReturnValue(dir);
    vi.resetModules();
    const fresh = await import("../lib/content");
    const out = fresh.localizeAssessment(base, "assessments", "vi")!;
    expect(out.questions[0]).toMatchObject({
      id: "q1",
      answer: "1",
      kind: "choice",
      prompt: "Hỏi",
      explanation: "Giải",
      options: ["a", "b"], // wrong length: English options are kept
    });
    expect(content.localizeAssessment(base, "assessments", "en")).toBe(base);
  });
});

describe("lesson time is language independent", () => {
  it("VI header minutes equal EN header minutes equal the sum of sessions", async () => {
    const { lessonIds, getLocalizedLesson } = await import("../lib/content");
    const { lessonPlan, lessonMinutes } = await import("../lib/lesson-plan");
    let checked = 0;
    for (const id of lessonIds()) {
      const en = getLocalizedLesson(id, "en")!;
      const vi = getLocalizedLesson(id, "vi")!;
      const enPlan = lessonPlan(en);
      // Project lessons (capstone) declare their total effort; others use the body.
      expect(enPlan.minutes, id).toBe(
        Math.max(lessonMinutes(en.body), en.meta.project_minutes ?? 0),
      );
      if (vi.lang !== "vi") continue;
      checked++;
      const viPlan = lessonPlan(vi);
      expect(viPlan.minutes, id).toBe(enPlan.minutes);
      expect(
        viPlan.sessions.map((s) => [s.key, s.minutes]),
        id,
      ).toEqual(enPlan.sessions.map((s) => [s.key, s.minutes]));
      expect(
        viPlan.sessions.reduce((n, s) => n + s.minutes, 0),
        id,
      ).toBe(enPlan.minutes);
    }
    expect(checked).toBeGreaterThan(0);
  });
});

describe("practice assignments", () => {
  it("have Vietnamese text for every assignment", async () => {
    const { practices } = await import("../lib/practice");
    const { practiceVi } = await import("../lib/practice-vi");
    for (const p of practices) {
      expect(practiceVi[p.id], p.id).toBeDefined();
      for (const key of ["title", "kind", "task"] as const)
        expect(practiceVi[p.id][key].trim(), `${p.id}.${key}`).not.toBe("");
    }
  });
});

import { describe, expect, it } from "vitest";
import katex from "katex";
import {
  insertSnippet,
  insideMath,
  lessonFormulas,
  mathGroups,
  noteTemplates,
} from "../lib/math-snippets";
import { getLesson } from "../lib/content";

describe("formula palette", () => {
  it("renders every snippet and its preview with KaTeX", () => {
    let count = 0;
    for (const group of mathGroups)
      for (const item of group.items)
        for (const tex of [item.tex, item.preview].filter(Boolean)) {
          count++;
          expect(
            () =>
              katex.renderToString(tex!.replace(/▮/g, "x"), {
                throwOnError: true,
                displayMode: !!item.block,
              }),
            `${group.id}: ${tex}`,
          ).not.toThrow();
        }
    expect(count).toBeGreaterThan(120);
  });

  it("covers the groups a robotics learner needs", () => {
    expect(mathGroups.map((g) => g.id)).toEqual([
      "basic",
      "greek",
      "calculus",
      "linear",
      "probability",
      "structure",
      "robotics",
    ]);
  });
});

describe("inserting formulas", () => {
  it("wraps inline snippets in $…$ and puts the selection in the slot", () => {
    const r = insertSnippet("speed v", 6, 7, { tex: "\\dot{▮}" });
    expect(r.text).toBe("speed $\\dot{v}$");
    expect(r.caret).toBe("speed $\\dot{v".length);
  });
  it("does not add dollars inside existing math", () => {
    const text = "$a + $";
    const r = insertSnippet(text, 5, 5, { tex: "\\frac{▮}{}" });
    expect(r.text).toBe("$a + \\frac{}{}$");
    expect(insideMath("$$x$$ y", 6)).toBe(false);
    expect(insideMath("$$\nx", 4)).toBe(true);
  });
  it("never glues two inline formulas into $$", () => {
    const r = insertSnippet("$a$", 3, 3, { tex: "b" });
    expect(r.text).toBe("$a$ $b$");
    expect(r.caret).toBe(6);
  });
  it("puts block snippets in their own $$ … $$ lines", () => {
    const r = insertSnippet("Bayes:", 6, 6, { tex: "P(A)", block: true });
    expect(r.text).toBe("Bayes:\n\n$$\nP(A)\n$$\n");
  });
  it("inserts note templates as-is, without wrapping them in math", () => {
    const r = insertSnippet("x", 1, 1, {
      tex: noteTemplates.formula.en,
      raw: true,
    });
    expect(r.text).toBe("x" + noteTemplates.formula.en);
  });
  it("offers formula and lesson templates in both languages", () => {
    for (const t of Object.values(noteTemplates)) {
      expect(t.en).toContain("$$");
      expect(t.vi).toContain("$$");
    }
  });
});

describe("lesson formulas", () => {
  it("collects display equations first, then inline equations", () => {
    const kalman = lessonFormulas(getLesson("C07")!.body);
    expect(kalman.length).toBeGreaterThan(3);
    expect(kalman[0].block).toBe(true);
    expect(new Set(kalman.map((f) => f.tex)).size).toBe(kalman.length);
    // Display equations come before inline ones; inline picks are equations.
    const vectors = lessonFormulas(getLesson("M02")!.body);
    expect(vectors.length).toBeGreaterThan(3);
    const firstInline = vectors.findIndex((f) => !f.block);
    expect(firstInline).toBeGreaterThanOrEqual(0);
    expect(vectors.slice(firstInline).every((f) => !f.block)).toBe(true);
    expect(
      vectors.filter((f) => !f.block).every((f) => /[=<>]|\\/.test(f.tex)),
    ).toBe(true);
    for (const f of [...kalman, ...vectors])
      expect(() =>
        katex.renderToString(f.tex, {
          throwOnError: true,
          displayMode: f.block,
        }),
      ).not.toThrow();
  });
});

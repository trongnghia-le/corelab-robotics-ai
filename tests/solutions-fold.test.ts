import { describe, expect, it } from "vitest";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkMath from "remark-math";
import remarkRehype from "remark-rehype";
import { toHtml } from "hast-util-to-html";
import type { Root } from "hast";
import {
  rehypeLessonSections,
  rehypeSolutions,
} from "../components/lesson-sections";

function render(md: string) {
  const processor = unified()
    .use(remarkParse)
    .use(remarkMath)
    .use(remarkRehype)
    .use(rehypeLessonSections)
    .use(rehypeSolutions, { summary: "Solution" });
  const tree = processor.runSync(processor.parse(md)) as Root;
  return toHtml(tree);
}

describe("folded solutions", () => {
  it("folds a worked case from Solution to the end of the case", () => {
    const html = render(
      [
        "## Worked example",
        "### Case 1",
        "**Problem.** Find x.",
        "**Solution.** Step one.",
        "1. Do this.",
        "**Check.** It fits.",
        "**Takeaway.** Remember it.",
        "### Case 2",
        "**Problem.** Find y.",
      ].join("\n\n"),
    );
    const fold = html.match(/<details[\s\S]*?<\/details>/)![0];
    expect(fold).toContain("<summary>Solution</summary>");
    expect(fold).toContain("Step one.");
    expect(fold).toContain("It fits.");
    expect(fold).toContain("Remember it.");
    expect(fold).not.toContain("Find y.");
    expect(fold).not.toContain("<strong>Solution.</strong>");
    expect(html).toContain("Find x.");
    expect(html.indexOf("<solutions-toggle>")).toBeLessThan(
      html.indexOf("<details"),
    );
  });
  it("in theory folds the solution and its equations, not the next paragraph", () => {
    const html = render(
      [
        "## Theory and derivation",
        "**Example.** A wheel turns.",
        "**Solution.** It turns at",
        "$$\n\\omega=2\n$$",
        "The theory goes on here.",
      ].join("\n\n"),
    );
    const fold = html.match(/<details[\s\S]*?<\/details>/)![0];
    expect(fold).toContain("It turns at");
    expect(fold).toContain("omega");
    expect(fold).not.toContain("The theory goes on here.");
    expect(html).toContain("A wheel turns.");
  });
  it("leaves sections without solutions untouched", () => {
    const html = render("## Intuition\n\nNo solution here.");
    expect(html).not.toContain("<details");
    expect(html).not.toContain("solutions-toggle");
  });
  it("folds Vietnamese labels too", () => {
    const html = render(
      "## Worked example\n\n### Ca 1\n\n**Đề bài.** Tìm x.\n\n**Lời giải.** Bước một.",
    );
    expect(html).toMatch(/<details[^>]*>[\s\S]*Bước một\./);
  });
});

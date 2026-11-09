import type { Element, Root, RootContent } from "hast";

export function headingId(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
const kinds = {
  "why-this-matters": "context",
  intuition: "concept",
  "intuition-and-definitions": "concept",
  "theory-and-derivation": "theory",
  "reasoning-and-assumptions": "theory",
  "worked-example": "example",
  "reference-implementation": "code",
  "implementation-and-verification": "code",
  "independent-practice": "practice",
  "independent-practice-and-transfer": "practice",
  verification: "verify",
  "failure-modes": "caution",
  "misconceptions-and-alternatives": "caution",
  "alternatives-and-trade-offs": "compare",
  "transfer-and-retention": "review",
  "further-reading": "reading",
} as const;
export function sectionKind(title: string) {
  const id = headingId(title);
  return Object.hasOwn(kinds, id) ? kinds[id as keyof typeof kinds] : "general";
}
function nodeText(node: RootContent): string {
  if (node.type === "text") return node.value;
  if (node.type === "element") return node.children.map(nodeText).join("");
  return "";
}
// Wrap authored h2 sections after Markdown parsing; never split source strings or fences.
// Heading IDs/text remain the same for the existing table of contents and illustrations.
export type SectionOptions = {
  /** Heading ids by section order; defaults to the id derived from the title. */
  ids?: string[];
  /** Displayed section numbers by section order; defaults to 1, 2, 3… */
  numbers?: number[];
};
export function rehypeLessonSections(options: SectionOptions = {}) {
  return (tree: Root) => {
    const children: RootContent[] = [];
    let section: Element | undefined;
    let index = 0;
    for (const node of tree.children) {
      if (node.type === "element" && node.tagName === "h2") {
        const title = nodeText(node);
        const id = options.ids?.[index] ?? headingId(title);
        node.properties["data-section-id"] = id;
        node.properties["data-section-number"] = String(
          options.numbers?.[index] ?? index + 1,
        ).padStart(2, "0");
        index++;
        section = {
          type: "element",
          tagName: "section",
          properties: {
            className: ["lesson-section", "lesson-section-" + sectionKind(id)],
            "aria-labelledby": id,
          },
          children: [],
        };
        children.push(section);
      }
      if (section) section.children.push(node as Element["children"][number]);
      else children.push(node);
    }
    tree.children = children;
  };
}

const SOLUTION_LABELS = new Set(["Solution.", "Lời giải."]);
const STOP_LABELS = new Set(["Example.", "Ví dụ.", "Problem.", "Đề bài."]);
/** The bold label a paragraph starts with ("Solution."), if any. */
function leadLabel(node: RootContent): string | undefined {
  if (node.type !== "element" || node.tagName !== "p") return undefined;
  const first = node.children.find(
    (c) => !(c.type === "text" && !c.value.trim()),
  );
  return first?.type === "element" && first.tagName === "strong"
    ? nodeText(first).trim()
    : undefined;
}
const isBlank = (n: RootContent) => n.type === "text" && !n.value.trim();
const isHeading = (n: RootContent) =>
  n.type === "element" && /^h[1-6]$/.test(n.tagName);

export type SolutionOptions = { summary: string };
/**
 * Fold every solution so the learner can try first. A paragraph that starts
 * with **Solution.** (VI **Lời giải.**) opens a fold. In the worked example
 * the fold runs to the end of the case (Check and Takeaway included); in the
 * other sections it takes the paragraph and the equations, lists or code that
 * follow it, and stops at the next ordinary paragraph. Each section with a
 * fold gets an "open / close all" control under its heading.
 * Runs after rehypeLessonSections.
 */
export function rehypeSolutions(options: SolutionOptions) {
  return (tree: Root) => {
    for (const section of tree.children) {
      if (
        section.type !== "element" ||
        section.tagName !== "section" ||
        !String(section.properties.className ?? "").includes("lesson-section")
      )
        continue;
      const wholeCase = String(section.properties.className).includes(
        "lesson-section-example",
      );
      const out: Element["children"] = [];
      const kids = section.children as RootContent[];
      let folds = 0;
      for (let i = 0; i < kids.length; i++) {
        const node = kids[i];
        if (!SOLUTION_LABELS.has(leadLabel(node) ?? "")) {
          out.push(node as Element["children"][number]);
          continue;
        }
        const body: RootContent[] = [node];
        let j = i + 1;
        for (; j < kids.length; j++) {
          const next = kids[j];
          if (isHeading(next)) break;
          const label = leadLabel(next);
          if (label && (STOP_LABELS.has(label) || SOLUTION_LABELS.has(label)))
            break;
          if (
            !wholeCase &&
            !isBlank(next) &&
            next.type === "element" &&
            next.tagName === "p"
          )
            break;
          body.push(next);
        }
        while (body.length > 1 && isBlank(body[body.length - 1])) body.pop();
        // The summary carries the label; drop it from the first paragraph.
        const p = node as Element;
        const lead = p.children.findIndex((c) => !isBlank(c as RootContent));
        p.children.splice(0, lead + 1);
        const rest = p.children[0];
        if (rest?.type === "text") rest.value = rest.value.replace(/^\s+/, "");
        // A label that stood alone leaves an empty paragraph behind.
        if (p.children.every((c) => isBlank(c as RootContent))) body.shift();
        out.push({
          type: "element",
          tagName: "details",
          properties: { className: ["lesson-solution"] },
          children: [
            {
              type: "element",
              tagName: "summary",
              properties: {},
              children: [{ type: "text", value: options.summary }],
            },
            ...(body as Element["children"]),
          ],
        });
        folds++;
        i = j - 1;
      }
      if (folds) {
        const h2 = out.findIndex(
          (n) => n.type === "element" && n.tagName === "h2",
        );
        out.splice(h2 + 1, 0, {
          type: "element",
          tagName: "solutions-toggle",
          properties: {},
          children: [],
        });
      }
      section.children = out;
    }
  };
}

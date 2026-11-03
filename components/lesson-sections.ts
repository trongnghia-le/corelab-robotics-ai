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

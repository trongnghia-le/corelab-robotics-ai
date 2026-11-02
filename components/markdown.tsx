"use client";
import { ConceptIllustration } from "./concept-illustration";
import type { LessonMedia } from "@/lib/media";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { isValidElement, type ReactNode } from "react";
import {
  BookOpen,
  Lightbulb,
  Sigma,
  PenLine,
  Braces,
  FlaskConical,
  ShieldCheck,
  TriangleAlert,
  GitCompare,
  RotateCcw,
  Library,
} from "lucide-react";
import { CodeBlock } from "./code-block";
import {
  headingId,
  sectionKind,
  rehypeLessonSections,
} from "./lesson-sections";
export { headingId } from "./lesson-sections";
const sectionIcons = {
  context: BookOpen,
  concept: Lightbulb,
  theory: Sigma,
  example: PenLine,
  code: Braces,
  practice: FlaskConical,
  verify: ShieldCheck,
  caution: TriangleAlert,
  compare: GitCompare,
  review: RotateCcw,
  reading: Library,
  general: BookOpen,
};
function textFromChildren(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number")
    return String(children);
  if (Array.isArray(children)) return children.map(textFromChildren).join("");
  if (children && typeof children === "object" && "props" in children)
    return textFromChildren(
      (children.props as { children?: ReactNode }).children,
    );
  return "";
}
export function LessonMarkdown({
  body,
  illustrations = [],
}: {
  body: string;
  illustrations?: LessonMedia["illustrations"];
}) {
  return (
    <div className="prose">
      <Markdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [rehypeKatex, { strict: "warn", trust: false }],
          rehypeLessonSections,
        ]}
        skipHtml
        components={{
          h2: ({ children, node }) => {
            const title = textFromChildren(children);
            const Icon = sectionIcons[sectionKind(title)];
            return (
              <>
                <h2 id={headingId(title)} className="lesson-section-heading">
                  <span className="lesson-section-icon" aria-hidden="true">
                    <Icon size={20} />
                  </span>
                  <span>{children}</span>
                  <span className="lesson-section-number" aria-hidden="true">
                    {String(node?.properties["data-section-number"] ?? "")}
                  </span>
                </h2>
                {illustrations
                  .filter((i) => i.heading === headingId(title))
                  .map((i) => (
                    <ConceptIllustration key={i.id} illustration={i} />
                  ))}
              </>
            );
          },
          pre: ({ children }) => {
            const element = isValidElement<{ className?: string }>(children)
              ? children
              : null;
            return (
              <CodeBlock
                code={textFromChildren(children)}
                language={
                  element?.props.className?.match(/language-([^\s]+)/)?.[1]
                }
              />
            );
          },
          table: ({ children }) => (
            <div
              className="lesson-table-scroll"
              role="region"
              aria-label="Lesson table"
              tabIndex={0}
            >
              <table>{children}</table>
            </div>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              rel={href?.startsWith("http") ? "noreferrer" : undefined}
            >
              {children}
            </a>
          ),
        }}
      >
        {body}
      </Markdown>
    </div>
  );
}

"use client";
import { LessonFigure } from "./lesson-figure";
import { Explore } from "./explore";
import { ConceptIllustration } from "./concept-illustration";
import type { LessonMedia } from "@/lib/media";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { isValidElement, useState, type ReactNode } from "react";
import {
  Eye,
  EyeOff,
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
import { useI18n } from "@/lib/i18n";
import {
  headingId,
  sectionKind,
  rehypeLessonSections,
  rehypeSolutions,
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
/** Opens every folded solution of the section, or closes them all. */
function SolutionsToggle() {
  const { tx } = useI18n();
  const [open, setOpen] = useState(false);
  return (
    <button
      type="button"
      className="button solutions-toggle"
      aria-pressed={open}
      onClick={(e) => {
        const section = e.currentTarget.closest("section");
        const next = !open;
        section
          ?.querySelectorAll<HTMLDetailsElement>("details.lesson-solution")
          .forEach((d) => (d.open = next));
        setOpen(next);
      }}
    >
      {open ? <EyeOff size={15} /> : <Eye size={15} />}
      {open
        ? tx("Hide all solutions", "Ẩn tất cả lời giải")
        : tx("Show all solutions", "Mở tất cả lời giải")}
    </button>
  );
}
export function LessonMarkdown({
  body,
  illustrations = [],
  headingIds,
  numbers,
}: {
  body: string;
  illustrations?: LessonMedia["illustrations"];
  /** Stable (English) heading ids by section order, for translated bodies. */
  headingIds?: string[];
  /** Section numbers by order when only part of a lesson is rendered. */
  numbers?: number[];
}) {
  const { tx, lang } = useI18n();
  return (
    <div className="prose">
      <Markdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [rehypeKatex, { strict: "warn", trust: false }],
          [rehypeLessonSections, { ids: headingIds, numbers }],
          [rehypeSolutions, { summary: tx("Solution", "Lời giải") }],
        ]}
        skipHtml
        components={{
          // Under each heading whose section has folded solutions.
          ...({
            "solutions-toggle": () => <SolutionsToggle />,
          } as object),
          h2: ({ children, node }) => {
            const title = textFromChildren(children);
            const id = String(
              node?.properties["data-section-id"] ?? headingId(title),
            );
            const Icon = sectionIcons[sectionKind(id)];
            return (
              <>
                <h2 id={id} className="lesson-section-heading">
                  <span className="lesson-section-icon" aria-hidden="true">
                    <Icon size={20} />
                  </span>
                  <span>{children}</span>
                  <span className="lesson-section-number" aria-hidden="true">
                    {String(node?.properties["data-section-number"] ?? "")}
                  </span>
                </h2>
                {illustrations
                  .filter((i) => i.heading === id)
                  .map((i) => (
                    <ConceptIllustration key={i.id} illustration={i} />
                  ))}
              </>
            );
          },
          // A paragraph made only of photos is a labelled gallery, so the
          // learner can compare components side by side.
          p: ({ children, node }) => {
            const items = (node?.children ?? []).filter(
              (c) => !(c.type === "text" && !c.value.trim()),
            );
            const photos = items.every(
              (c) =>
                c.type === "element" &&
                c.tagName === "img" &&
                String(c.properties.src ?? "").startsWith("/lesson-images/"),
            );
            if (!items.length || !photos) return <p>{children}</p>;
            return (
              <span
                className={
                  items.length > 1 ? "lesson-photos" : "lesson-photos is-single"
                }
              >
                {items.map((c, i) => {
                  if (c.type !== "element") return null;
                  const src = String(c.properties.src);
                  const alt = String(c.properties.alt ?? "");
                  const title = c.properties.title
                    ? String(c.properties.title)
                    : "";
                  return (
                    <span className="lesson-photo" key={src + i}>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={src} alt={alt} loading="lazy" />
                      {title && <span className="lesson-photo-label">{title}</span>}
                    </span>
                  );
                })}
              </span>
            );
          },
          img: ({ src, alt }) => {
            const original = typeof src === "string" ? src : "";
            if (/^\/lesson-figures\/[\w-]+\.svg$/.test(original))
              return (
                <LessonFigure
                  src={
                    lang === "vi"
                      ? original.replace(
                          "/lesson-figures/",
                          "/lesson-figures/vi/",
                        )
                      : original
                  }
                  fallback={original}
                  alt={alt ?? ""}
                />
              );
            // eslint-disable-next-line @next/next/no-img-element
            return <img src={original} alt={alt ?? ""} loading="lazy" />;
          },
          pre: ({ children }) => {
            const element = isValidElement<{ className?: string }>(children)
              ? children
              : null;
            const language =
              element?.props.className?.match(/language-([^\s]+)/)?.[1];
            if (language === "explore")
              return <Explore source={textFromChildren(children)} />;
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
              aria-label={tx("Lesson table", "Bảng trong bài học")}
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

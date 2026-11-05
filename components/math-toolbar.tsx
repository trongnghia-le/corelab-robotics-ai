"use client";
import { useMemo, useState } from "react";
import katex from "katex";
import { useI18n } from "@/lib/i18n";
import {
  lessonFormulas,
  mathGroups,
  type MathGroup,
  type MathSnippet,
} from "@/lib/math-snippets";

function render(tex: string) {
  return katex.renderToString(tex.replace(/▮/g, "x"), {
    throwOnError: false,
    displayMode: false,
    strict: "ignore",
  });
}

/** Formula palette: grouped LaTeX snippets plus the lesson's own equations. */
export function MathToolbar({
  lessonBody,
  onInsert,
}: {
  lessonBody?: string;
  onInsert: (snippet: Pick<MathSnippet, "tex" | "block">) => void;
}) {
  const { tx, lang } = useI18n();
  const formulas = useMemo(
    () => (lessonBody ? lessonFormulas(lessonBody) : []),
    [lessonBody],
  );
  const groups = useMemo<MathGroup[]>(
    () => [
      ...mathGroups,
      ...(formulas.length
        ? [
            {
              id: "lesson",
              en: "From this lesson",
              vi: "Trong bài này",
              items: formulas.map((f) => ({
                label: f.tex,
                tex: f.tex,
                block: f.block,
              })),
            },
          ]
        : []),
    ],
    [formulas],
  );
  const [group, setGroup] = useState("basic");
  const active = groups.find((g) => g.id === group) ?? groups[0];
  return (
    <div className="math-toolbar">
      <div
        className="math-groups"
        role="tablist"
        aria-label={tx("Formula groups", "Nhóm công thức")}
      >
        {groups.map((g) => (
          <button
            key={g.id}
            type="button"
            role="tab"
            aria-selected={g.id === active.id}
            className={g.id === active.id ? "selected" : ""}
            onClick={() => setGroup(g.id)}
          >
            {lang === "vi" ? g.vi : g.en}
          </button>
        ))}
      </div>
      <div
        className={`math-items ${active.id === "lesson" ? "is-lesson" : ""}`}
      >
        {active.items.map((item, i) => (
          <button
            key={`${active.id}-${i}`}
            type="button"
            className="math-item"
            title={item.label}
            aria-label={item.label}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => onInsert(item)}
            dangerouslySetInnerHTML={{
              __html: render(
                active.id === "lesson" ? item.tex : (item.preview ?? item.tex),
              ),
            }}
          />
        ))}
      </div>
    </div>
  );
}

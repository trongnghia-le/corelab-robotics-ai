"use client";
import { useEffect, useRef } from "react";
import { basicSetup } from "codemirror";
import { EditorView, keymap } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { indentWithTab } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import { cpp } from "@codemirror/lang-cpp";
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";

export type EditorLang = "python" | "cpp" | "markdown" | "text";

export function langFor(name: string): EditorLang {
  if (name.endsWith(".py")) return "python";
  if (/\.(c|cc|cpp|h|hpp)$/.test(name)) return "cpp";
  if (name.endsWith(".md")) return "markdown";
  return "text";
}

const languages = { python, cpp, markdown, text: () => [] };

/**
 * CodeMirror 6 editor. The document is owned by the editor; `onChange`
 * reports edits. Remount (change `key`) to load a different file.
 */
export function CodeEditor({
  value,
  lang,
  onChange,
  onRun,
  label,
}: {
  value: string;
  lang: EditorLang;
  onChange: (value: string) => void;
  onRun?: () => void;
  label: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const handlers = useRef({ onChange, onRun });
  useEffect(() => {
    handlers.current = { onChange, onRun };
  });
  useEffect(() => {
    const view = new EditorView({
      parent: host.current!,
      state: EditorState.create({
        doc: value,
        extensions: [
          basicSetup,
          keymap.of([
            indentWithTab,
            {
              key: "Mod-Enter",
              run: () => {
                handlers.current.onRun?.();
                return true;
              },
            },
          ]),
          languages[lang](),
          oneDark,
          EditorView.lineWrapping,
          EditorView.contentAttributes.of({ "aria-label": label }),
          EditorView.updateListener.of((u) => {
            if (u.docChanged) handlers.current.onChange(u.state.doc.toString());
          }),
        ],
      }),
    });
    return () => view.destroy();
    // The editor owns the document after mount; remount to load new content.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <div className="code-editor" ref={host} />;
}

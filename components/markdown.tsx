"use client";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { useState, type ReactNode } from "react";
import { Copy, Check } from "lucide-react";
import { copyText, useCore } from "./provider";
export function headingId(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
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
function CodeBlock({ children }: { children?: ReactNode }) {
  const [copied, setCopied] = useState(false);
  const { notify } = useCore();
  return (
    <div className="code-block">
      <button
        aria-label="Copy code"
        className="code-copy"
        onClick={async () => {
          try {
            await copyText(textFromChildren(children));
            setCopied(true);
          } catch (e) {
            notify(e instanceof Error ? e.message : "Unable to copy.");
          }
        }}
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}{" "}
        {copied ? "Copied" : "Copy"}
      </button>
      <pre>{children}</pre>
    </div>
  );
}
export function LessonMarkdown({ body }: { body: string }) {
  return (
    <div className="prose">
      <Markdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { strict: "warn", trust: false }]]}
        skipHtml
        components={{
          h2: ({ children }) => (
            <h2 id={headingId(textFromChildren(children))}>{children}</h2>
          ),
          pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
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

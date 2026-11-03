"use client";
import { useEffect, useState, type CSSProperties } from "react";
import { Braces, Check, Copy } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { copyText } from "./provider";
import type { highlightCode } from "./code-highlight";
const aliases = {
  python: "python",
  py: "python",
  cpp: "cpp",
  "c++": "cpp",
  cc: "cpp",
  cxx: "cpp",
  bash: "shellscript",
  sh: "shellscript",
  shell: "shellscript",
  shellscript: "shellscript",
  json: "json",
} as const;
const labels = {
  python: "Python",
  cpp: "C++",
  shellscript: "Shell",
  json: "JSON",
};
export function CodeBlock({
  code,
  language = "text",
}: {
  code: string;
  language?: string;
}) {
  const requested = language.toLowerCase();
  const lang = Object.hasOwn(aliases, requested)
    ? aliases[requested as keyof typeof aliases]
    : null;
  const label = lang ? labels[lang] : "Plain text";
  const [highlighted, setHighlighted] = useState<{
    code: string;
    lang: string;
    result: Awaited<ReturnType<typeof highlightCode>>;
  } | null>(null);
  const { tx } = useI18n();
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (lang && code.length <= 50000) {
      import("./code-highlight")
        .then(({ highlightCode }) => highlightCode(code, lang))
        .then((result) => {
          if (active) setHighlighted({ code, lang, result });
        })
        .catch(() => {
          /* Original, escaped source stays readable if highlighting fails. */
        });
    }
    return () => {
      active = false;
    };
  }, [code, lang]);
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(timer);
  }, [copied]);
  const result =
    highlighted?.code === code && highlighted.lang === lang
      ? highlighted.result
      : null;
  return (
    <div
      className="code-block"
      data-language={lang ?? "text"}
      data-highlighted={result ? "true" : "false"}
    >
      <div className="code-toolbar">
        <span className="code-language">
          <Braces size={16} aria-hidden="true" />
          {label}
        </span>
        <span className="code-theme">Dark+</span>
        <button
          aria-label={
            copied
              ? tx("Code copied", "Đã sao chép code")
              : tx("Copy code", "Sao chép code")
          }
          className="code-copy"
          type="button"
          onClick={async () => {
            try {
              await copyText(code);
              setCopied(true);
              setError("");
            } catch {
              setError("Could not copy. Select the code and copy it manually.");
            }
          }}
        >
          {copied ? (
            <Check size={15} aria-hidden="true" />
          ) : (
            <Copy size={15} aria-hidden="true" />
          )}
          {copied ? tx("Copied", "Đã chép") : tx("Copy", "Chép")}
        </button>
      </div>
      <pre
        tabIndex={0}
        role="region"
        aria-label={`${label} ${tx("code example", "ví dụ code")}`}
      >
        <code>
          {result
            ? result.tokens.map((line, i) => (
                <span className="code-line" key={i}>
                  {line.map((token, j) => {
                    const font = token.fontStyle ?? 0;
                    const style: CSSProperties = {
                      color: token.color,
                      ...(font & 1 ? { fontStyle: "italic" } : {}),
                      ...(font & 2 ? { fontWeight: 700 } : {}),
                      ...(font & 4 ? { textDecoration: "underline" } : {}),
                    };
                    return (
                      <span key={j} style={style}>
                        {token.content}
                      </span>
                    );
                  })}
                  {i < result.tokens.length - 1 ? "\n" : ""}
                </span>
              ))
            : code}
        </code>
      </pre>
      {error && (
        <p className="code-feedback" role="status">
          {error}
        </p>
      )}
    </div>
  );
}

import {
  createBundledHighlighter,
  createSingletonShorthands,
} from "@shikijs/core";
import { createJavaScriptRegexEngine } from "@shikijs/engine-javascript";

// Only the selected grammar/theme chunks are bundled; no CDN or code execution.
const createHighlighter = createBundledHighlighter({
  langs: {
    python: () => import("@shikijs/langs/python"),
    cpp: () => import("@shikijs/langs/cpp"),
    shellscript: () => import("@shikijs/langs/shellscript"),
    json: () => import("@shikijs/langs/json"),
  },
  themes: { "dark-plus": () => import("@shikijs/themes/dark-plus") },
  engine: () => createJavaScriptRegexEngine(),
});
const { codeToTokens } = createSingletonShorthands(createHighlighter);
export const highlightCode = (
  code: string,
  lang: "python" | "cpp" | "shellscript" | "json",
) => codeToTokens(code, { lang, theme: "dark-plus" });

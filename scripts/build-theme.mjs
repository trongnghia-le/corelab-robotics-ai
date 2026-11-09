// Generates app/theme.css (the stylesheet the app loads) from app/globals.css.
// globals.css is the dark-first source. For every rule that hard-codes a
// colour, a light copy (lightness mirrored, hue and saturation kept, scoped
// with :where(:root[data-theme="light"]) so it adds no specificity) is placed
// right after the original rule, keeping the cascade order. Code blocks and
// editors keep their dark theme. Edit globals.css, then run `npm run theme`.
//   node scripts/build-theme.mjs          write app/theme.css
//   node scripts/build-theme.mjs --check  fail if it is out of date
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import postcss from "postcss";
import * as prettier from "prettier";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.join(root, "app/globals.css");
const target = path.join(root, "app/theme.css");
const LIGHT = ':root[data-theme="light"]';
// Overrides add no specificity, so a light copy of a generic rule (e.g.
// "button") never beats a more specific dark rule that sets the property.
const SCOPE = `:where(${LIGHT})`;
const HEX = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/g;
// Syntax-highlighted code keeps its dark palette in both themes.
const KEEP_DARK = /\bpre\b|code-block|shiki|\.cm-|code-editor|desk-output/;
// SVG drawings with colours baked in are inverted as a whole in the light
// theme (see the filter below), so nothing inside them may be recoloured too:
// recolouring and then inverting turns dark text back into near-white text.
// The dashboard sketch (.robotics-concept) already uses theme variables and
// classes, so it is recoloured normally and never inverted.
const INVERTED =
  /\.(concept-illustration|concept-demo|lesson-svg)\s+svg\b|\.explore-(svg|tick|axis|label)\b/;

function hexToHsl(hex) {
  let raw = hex.slice(1);
  if (raw.length === 3) raw = [...raw].map((c) => c + c).join("");
  const [r, g, b] = [0, 2, 4].map(
    (i) => parseInt(raw.slice(i, i + 2), 16) / 255,
  );
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b),
    l = (max + min) / 2;
  let h = 0,
    s = 0;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    h =
      max === r
        ? (g - b) / d + (g < b ? 6 : 0)
        : max === g
          ? (b - r) / d + 2
          : (r - g) / d + 4;
    h /= 6;
  }
  return { h, s, l, alpha: raw.slice(6) };
}

function hslToHex({ h, s, l, alpha }) {
  const f = (n) => {
    const k = (n + h * 12) % 12;
    const a = s * Math.min(l, 1 - l);
    const c = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(c * 255)
      .toString(16)
      .padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}${alpha}`;
}

/** Mirror lightness; very light results are lifted towards white. */
export function lightColor(hex) {
  const c = hexToHsl(hex);
  let l = 1 - c.l;
  if (l > 0.8) l = 0.88 + (l - 0.8) * 0.6;
  return hslToHex({ ...c, l: Math.min(1, l) });
}

const THEME = `${LIGHT} {
  --bg: #f5f4f1;
  --surface-1: #ffffff;
  --surface-2: #f4f3f0;
  --surface-3: #e9e7e2;
  --border: #d9d6d0;
  --text: #1c1e22;
  --muted: #4c525c;
  --subtle: #676d77;
  --primary: #a95a24;
  --primary-hover: #8f4a1b;
  --success: #2c7a4d;
  --warning: #8a5f0e;
  --danger: #b03f3f;
  color-scheme: light;
}`;

function lightSelector(selectors) {
  return selectors
    .filter((s) => !INVERTED.test(s))
    .map((s) =>
      s === "html" || s === ":root"
        ? SCOPE
        : s.startsWith("html")
          ? SCOPE + s.slice(4)
          : `${SCOPE} ${s}`,
    )
    .join(",\n");
}

export function buildTheme(css) {
  const input = postcss.parse(css);
  const sources = [];
  input.walkRules((rule) => sources.push(rule));
  for (const rule of sources) {
    if (rule.parent?.type === "atrule" && rule.parent.name === "keyframes")
      continue;
    if (rule.selector === ":root") {
      rule.after(postcss.parse(THEME));
      continue;
    }
    if (KEEP_DARK.test(rule.selector)) continue;
    const tone = rule.selector.match(/^\[data-domain-tone(?:="(\w+)")?\]$/);
    const decls = [];
    rule.each((node) => {
      if (node.type !== "decl" || !HEX.test(node.value)) return;
      HEX.lastIndex = 0;
      decls.push(
        postcss.decl({
          prop: node.prop,
          value: node.value.replace(HEX, lightColor),
          important: node.important,
        }),
      );
    });
    if (!decls.length) continue;
    const selector = tone
      ? `${SCOPE} ${rule.selector}`
      : lightSelector(rule.selectors);
    if (!selector) continue;
    const light = postcss.rule({ selector });
    decls.forEach((d) => light.append(d));
    // Same parent (@media included), right after the original: same cascade.
    rule.after(light);
  }
  const extras = `
/* Lesson figures and concept drawings are drawn on dark backgrounds:
   invert lightness, keep hues. */
${LIGHT} img[src^="/lesson-figures/"],
${LIGHT} .lesson-svg svg,
${LIGHT} .concept-illustration svg,
${LIGHT} .concept-demo svg {
  filter: invert(1) hue-rotate(180deg) brightness(1.08);
}
${LIGHT} .react-flow__minimap {
  background: #ecebe7;
}
`;
  return prettier.format(
    `/* Generated by scripts/build-theme.mjs from app/globals.css. Do not edit:
   change globals.css and run \`npm run theme\`. */
${input.toString()}
${extras}`,
    { parser: "css" },
  );
}

const isMain = process.argv[1] === fileURLToPath(import.meta.url);
if (isMain) {
  const next = await buildTheme(readFileSync(source, "utf8"));
  if (process.argv.includes("--check")) {
    const current = readFileSync(target, "utf8");
    if (current !== next) {
      console.error("app/theme.css is out of date: run npm run theme");
      process.exit(1);
    }
    console.log("Theme stylesheet is up to date.");
  } else {
    writeFileSync(target, next);
    console.log("Wrote app/theme.css");
  }
}

// Vietnamese lesson figures. Lesson SVGs keep their text in <text>/<tspan>
// nodes; this tool moves that text in and out of JSON so it can be translated,
// and writes public/lesson-figures/vi/<ID>.svg with the same drawing.
//   node scripts/figure-text.mjs extract <outDir>   one <ID>.json per figure
//   node scripts/figure-text.mjs apply <inDir>      write vi/<ID>.svg from translations
// A translation file is {"texts": ["…", …], "title": "…", "desc": "…"} with the
// same number of texts, in the same order, as the extracted file.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const figures = path.join(root, "public", "lesson-figures");
const viDir = path.join(figures, "vi");

const TEXT = /<text\b[^>]*>[\s\S]*?<\/text>/g;
// Text runs between tags inside a <text> element (tspans included).
const RUN = />([^<]+)</g;

const decode = (s) =>
  s
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
const encode = (s) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** Translatable runs of an SVG, in document order. */
export function runs(svg) {
  const out = [];
  for (const el of svg.match(TEXT) ?? [])
    for (const m of el.matchAll(RUN)) if (m[1].trim()) out.push(decode(m[1]));
  const title = svg.match(/<title>([\s\S]*?)<\/title>/)?.[1];
  const desc = svg.match(/<desc>([\s\S]*?)<\/desc>/)?.[1];
  return {
    texts: out,
    title: title && decode(title),
    desc: desc && decode(desc),
  };
}

/** Replace the runs of `svg` with `t.texts`, keeping all markup. */
export function applyRuns(svg, t) {
  let i = 0;
  let out = svg.replace(TEXT, (el) =>
    el.replace(RUN, (whole, run) => {
      if (!run.trim()) return whole;
      const next = t.texts[i++];
      if (next === undefined) throw new Error("Too few translated texts");
      // Keep the original leading/trailing whitespace of the run.
      const lead = run.match(/^\s*/)[0],
        tail = run.match(/\s*$/)[0];
      return `>${lead}${encode(next.trim())}${tail}<`;
    }),
  );
  if (i !== t.texts.length) throw new Error("Too many translated texts");
  if (t.title)
    out = out.replace(
      /<title>[\s\S]*?<\/title>/,
      `<title>${encode(t.title)}</title>`,
    );
  if (t.desc)
    out = out.replace(
      /<desc>[\s\S]*?<\/desc>/,
      `<desc>${encode(t.desc)}</desc>`,
    );
  return out;
}

const isMain = process.argv[1] === fileURLToPath(import.meta.url);
if (isMain) {
  const [cmd, dir] = process.argv.slice(2);
  const ids = fs
    .readdirSync(figures)
    .filter((f) => f.endsWith(".svg"))
    .map((f) => f.slice(0, -4));
  if (cmd === "extract") {
    fs.mkdirSync(dir, { recursive: true });
    for (const id of ids) {
      const svg = fs.readFileSync(path.join(figures, `${id}.svg`), "utf8");
      fs.writeFileSync(
        path.join(dir, `${id}.json`),
        JSON.stringify(runs(svg), null, 1),
      );
    }
    console.log(`Extracted ${ids.length} figures to ${dir}`);
  } else if (cmd === "apply") {
    fs.mkdirSync(viDir, { recursive: true });
    let n = 0;
    for (const id of ids) {
      const file = path.join(dir, `${id}.json`);
      if (!fs.existsSync(file)) continue;
      const svg = fs.readFileSync(path.join(figures, `${id}.svg`), "utf8");
      const t = JSON.parse(fs.readFileSync(file, "utf8"));
      fs.writeFileSync(path.join(viDir, `${id}.svg`), applyRuns(svg, t));
      n++;
    }
    console.log(`Wrote ${n} Vietnamese figures to public/lesson-figures/vi/`);
  } else {
    console.error("Usage: node scripts/figure-text.mjs extract|apply <dir>");
    process.exit(1);
  }
}

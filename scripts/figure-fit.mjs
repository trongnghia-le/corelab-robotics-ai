// Keeps Vietnamese figure labels inside the space the English ones used.
// For every <text> in public/lesson-figures/vi/<ID>.svg, measures the rendered
// width of the English and Vietnamese label in Chromium (Playwright) and, when
// the Vietnamese one is more than 6% wider, shrinks that label's font size
// (never below 78% of the original).
//   node scripts/figure-fit.mjs [ID ...]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const figures = path.join(root, "public", "lesson-figures");
const viDir = path.join(figures, "vi");
const SLACK = 1.06;
const MIN_SCALE = 0.78;

async function widths(page, svg) {
  await page.setContent(`<!doctype html><body>${svg}</body>`);
  return page.$$eval("svg text", (els) =>
    els.map((el) => ({
      width: el.getComputedTextLength(),
      size: parseFloat(getComputedStyle(el).fontSize),
    })),
  );
}

const ids = process.argv.slice(2).length
  ? process.argv.slice(2)
  : fs
      .readdirSync(viDir)
      .filter((f) => f.endsWith(".svg"))
      .map((f) => f.slice(0, -4));
const browser = await chromium.launch();
const page = await browser.newPage();
let shrunk = 0;
for (const id of ids) {
  const en = fs.readFileSync(path.join(figures, `${id}.svg`), "utf8");
  const viFile = path.join(viDir, `${id}.svg`);
  let vi = fs.readFileSync(viFile, "utf8");
  const a = await widths(page, en);
  const b = await widths(page, vi);
  if (a.length !== b.length) {
    console.error(
      `${id}: text count differs (${a.length} vs ${b.length}), skipped`,
    );
    continue;
  }
  let i = -1;
  vi = vi.replace(/<text\b([^>]*)>/g, (tag, attrs) => {
    i++;
    const { width: we, size } = a[i];
    const wv = b[i].width;
    if (!we || wv <= we * SLACK || wv - we < 4) return tag;
    const scale = Math.max(MIN_SCALE, (we * SLACK) / wv);
    const px = +(size * scale).toFixed(2);
    shrunk++;
    // Override any font-size from attributes or classes for this label only.
    const style = attrs.match(/\sstyle="([^"]*)"/);
    if (style)
      return tag.replace(
        style[0],
        ` style="${style[1].replace(/;?\s*$/, "")};font-size:${px}px"`,
      );
    return `<text${attrs} style="font-size:${px}px">`;
  });
  fs.writeFileSync(viFile, vi);
}
await browser.close();
console.log(`Fitted ${ids.length} figures; shrank ${shrunk} labels.`);

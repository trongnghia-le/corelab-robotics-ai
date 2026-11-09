import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
// @ts-expect-error plain ESM script without type declarations
import { applyRuns, runs } from "../scripts/figure-text.mjs";

const dir = path.join(process.cwd(), "public", "lesson-figures");
const vi = path.join(dir, "vi");

describe("Vietnamese lesson figures", () => {
  const files = fs.existsSync(vi)
    ? fs.readdirSync(vi).filter((f) => f.endsWith(".svg"))
    : [];

  it("exist for every lesson figure", () => {
    const english = fs.readdirSync(dir).filter((f) => f.endsWith(".svg"));
    expect(files.sort()).toEqual(english.sort());
  });

  it("keep the frame and carry Vietnamese text", () => {
    // Vietnamese copies may be laid out differently so longer text fits, but
    // they keep the canvas and most of the original's labels.
    const box = (svg: string) => svg.match(/viewBox="([^"]+)"/)?.[1];
    for (const f of files) {
      const en = fs.readFileSync(path.join(dir, f), "utf8");
      const tr = fs.readFileSync(path.join(vi, f), "utf8");
      expect(box(tr), f).toBe(box(en));
      const a = runs(en).texts as string[];
      const b = runs(tr).texts as string[];
      expect(b.length, f).toBeGreaterThanOrEqual(Math.floor(a.length * 0.6));
    }
  });

  it("round-trips English text unchanged", () => {
    const svg =
      '<svg><text x="1">a &lt; b</text><text>c<tspan>d</tspan></text></svg>';
    expect(applyRuns(svg, runs(svg))).toBe(svg);
  });
});

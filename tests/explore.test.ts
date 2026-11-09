import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { compile, parse } from "../lib/expr";
import {
  compileSpec,
  exploreSpec,
  scene3dPrimitives,
  scopeFor,
} from "../lib/explore-spec";

describe("safe expressions", () => {
  it("follows precedence, unary minus and right-associative powers", () => {
    expect(compile("1 + 2 * 3")({})).toBe(7);
    expect(compile("-2^2")({})).toBe(-4);
    expect(compile("2^3^2")({})).toBe(512);
    expect(compile("(1+2)*3")({})).toBe(9);
    expect(compile("hypot(3, 4) + cos(0)")({})).toBe(6);
    expect(compile("q*deg")({ q: 180 })).toBeCloseTo(Math.PI);
    expect(compile("1.5e2 / 3")({})).toBe(50);
  });
  it("rejects anything outside the language", () => {
    for (const bad of [
      "alert(1)",
      "constructor",
      "x.y",
      "a[0]",
      "'s'",
      "1 +",
      "f()",
      "this",
    ])
      expect(() => compile(bad)({})).toThrow();
    expect(() => parse("process")).not.toThrow(); // a name, but unknown at run time
    expect(() => compile("process")({})).toThrow("Unknown name");
  });
});

// Every ```explore block in every lesson must parse and evaluate to finite
// numbers at its defaults and at each slider's ends.
const lessonsDir = path.join(process.cwd(), "content", "lessons");
const files = [
  ...fs.readdirSync(lessonsDir).filter((f) => f.endsWith(".md")),
  ...fs
    .readdirSync(path.join(lessonsDir, "vi"))
    .filter((f) => f.endsWith(".md"))
    .map((f) => `vi/${f}`),
];
const blocks = files.flatMap((f) =>
  [
    ...fs
      .readFileSync(path.join(lessonsDir, f), "utf8")
      .matchAll(/```explore\n([\s\S]*?)\n```/g),
  ].map((m) => ({ f, src: m[1] })),
);

describe("lesson explore blocks", () => {
  it.each(blocks.length ? blocks : [{ f: "(none)", src: "" }])(
    "$f evaluates",
    ({ f, src }) => {
      if (f === "(none)") return;
      const spec = exploreSpec.parse(JSON.parse(src));
      const compiled = compileSpec(spec);
      const base = Object.fromEntries(
        spec.params.map((p) => [p.name, p.value]),
      );
      const cases = [base];
      for (const p of spec.params)
        cases.push({ ...base, [p.name]: p.min }, { ...base, [p.name]: p.max });
      for (const values of cases) {
        const scope = scopeFor(spec, compiled, values);
        // Every 3D primitive must land on finite coordinates.
        for (const q of scene3dPrimitives(compiled, scope)) {
          const pts =
            q.kind === "poly" ? q.pts : q.kind === "line" ? [q.a, q.b] : [q.a];
          for (const v of pts)
            expect(
              v.every(Number.isFinite),
              `${f} 3D point at ${JSON.stringify(values)}`,
            ).toBe(true);
        }
        for (const r of compiled.readouts)
          expect(
            Number.isFinite(r(scope)),
            `${f} readout at ${JSON.stringify(values)}`,
          ).toBe(true);
      }
      const scope = scopeFor(spec, compiled, base);
      // At the defaults a 3D scene must fit its view box ("range" is the
      // half-size of the view), or the learner opens it already cut off.
      if (spec.scene3d) {
        const R = spec.scene3d.range * 1.25;
        for (const q of scene3dPrimitives(compiled, scope)) {
          const pts =
            q.kind === "poly" ? q.pts : q.kind === "line" ? [q.a, q.b] : [q.a];
          for (const v of pts)
            expect(
              Math.max(...v.map(Math.abs)),
              `${f}: a 3D point at the defaults lies outside range ${spec.scene3d.range}`,
            ).toBeLessThanOrEqual(R);
        }
      }
      for (const s of compiled.series)
        expect(
          Number.isFinite(
            s({ ...scope, [spec.plot!.x.name]: spec.plot!.x.min }),
          ),
        ).toBe(true);
    },
  );
});

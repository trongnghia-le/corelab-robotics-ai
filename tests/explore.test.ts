import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { compile, parse } from "../lib/expr";
import {
  compileSpec,
  exploreSpec,
  projector,
  scene3dPrimitives,
  scopeFor,
  VIEW3,
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
      // Slider ends combine: also try every corner of the parameter box
      // (at most 2^6 = 64 cases).
      for (let mask = 0; mask < 1 << spec.params.length; mask++)
        cases.push(
          Object.fromEntries(
            spec.params.map((p, i) => [p.name, mask & (1 << i) ? p.max : p.min]),
          ),
        );
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
      // A 3D scene must fit its view box as first shown, at the defaults
      // and at every slider end, or the learner sees it cut off.
      if (spec.scene3d) {
        const s3 = spec.scene3d;
        const project = projector(
          s3.range,
          s3.view?.azimuth ?? -50,
          s3.view?.elevation ?? 25,
        );
        for (const values of cases) {
          const at = scopeFor(spec, compiled, values);
          for (const q of scene3dPrimitives(compiled, at)) {
            const pts =
              q.kind === "poly"
                ? q.pts
                : q.kind === "line"
                  ? [q.a, q.b]
                  : [q.a];
            for (const v of pts) {
              const p = project(v);
              expect(
                p.x >= -2 && p.x <= VIEW3.W + 2 && p.y >= -2 && p.y <= VIEW3.H + 2,
                `${f}: a 3D point projects outside the view at ${JSON.stringify(values)} (${p.x.toFixed(0)}, ${p.y.toFixed(0)})`,
              ).toBe(true);
            }
          }
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

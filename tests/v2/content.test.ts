import { expect, it } from "vitest";
import {
  catalog,
  gradeItem,
  normalizedAnswers,
  publicItem,
  itemFingerprint,
  canonicalInputs,
} from "../../lib/v2/content";
it("loads original static contracts for twenty families and redacts answers/help", () => {
  const c = catalog();
  expect(c.families.filter((f) => /^X\d+$/.test(f.id))).toHaveLength(20);
  expect(c.families.find((f) => f.id === "XB1")?.items).toHaveLength(12);
  expect(c.families.reduce((n, f) => n + f.items.length, 0)).toBe(152);
  for (const f of c.families)
    for (const item of f.items) {
      expect(
        gradeItem(
          item,
          Object.fromEntries(
            item.fields.map((q, i) => [
              i,
              q.kind === "choice" ? q.answer : Number(q.answer).toFixed(9),
            ]),
          ),
        ).passed,
      ).toBe(true);
      const pub = publicItem(item);
      expect(JSON.stringify(pub)).not.toContain('"answer":');
      expect(JSON.stringify(pub)).not.toContain('"solution":');
      expect(() => normalizedAnswers(item, {})).toThrow();
    }
});
it("uses canonical decimal input bytes and treats equivalent numeric spellings identically", () => {
  const item = catalog().families[0].items[0];
  expect(itemFingerprint(item)).toBe(
    itemFingerprint({
      ...item,
      inputs: canonicalInputs(item.inputs) as Record<string, unknown>,
    }),
  );
  expect(canonicalInputs({ x: "+00.5000", zero: "-0.00", v: 2 })).toEqual({
    x: "0.5",
    zero: "0",
    v: "2",
  });
});
it("handles angle-equivalent answers and rejects wrong shape/unknown choices", () => {
  const fk = catalog().families.find((f) => f.id === "X11")!.items[0];
  const answers = Object.fromEntries(
    fk.fields.map((q, i) => [String(i), q.answer]),
  );
  answers["2"] = "6.28318530718";
  expect(gradeItem(fk, answers).passed).toBe(true);
  expect(() => gradeItem(fk, { ...answers, extra: "0" })).toThrow();
});
it("checks Bayes and projection anchors independently of serialized answer text", () => {
  const bayes = catalog().families.find((f) => f.id === "X04")!;
  for (const item of bayes.items) {
    const value = (v: unknown) => {
      const [n, d = "1"] = String(v).split("/");
      return Number(n) / Number(d);
    };
    const p = value(item.inputs.prior),
      sensitivity = value(item.inputs.sensitivity),
      fp = value(item.inputs.falsePositive);
    expect(Number(item.fields[0].answer)).toBeCloseTo(
      (p * sensitivity) / (p * sensitivity + (1 - p) * fp),
      12,
    );
  }
  for (const item of catalog().families[0].items) {
    const u = item.inputs.u as number[],
      v = item.inputs.v as number[];
    const projected = item.fields.map((f) => Number(f.answer));
    const residual = u.map((x, i) => x - projected[i]);
    expect(residual.reduce((n, x, i) => n + x * v[i], 0)).toBeCloseTo(0, 12);
  }
});

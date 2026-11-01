import { expect, it } from "vitest";
import {
  catalog,
  gradeItem,
  normalizedAnswers,
  publicItem,
} from "../../lib/v2/content";
it("loads original static contracts for twenty families and redacts answers/help", () => {
  const c = catalog();
  expect(c.families).toHaveLength(20);
  expect(c.families.reduce((n, f) => n + f.items.length, 0)).toBe(140);
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
    const p =
      Number(String(item.inputs.prior).split("/")[0]) /
      Number(String(item.inputs.prior).split("/")[1] ?? 1);
    expect(Number(item.fields[0].answer)).toBeCloseTo(
      (p * 0.9) / (p * 0.9 + (1 - p) * 0.05),
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

import { expect, it } from "vitest";
import { shuffled, samePresentation } from "../../lib/v2/presentation";
import { readableAnswer } from "../../components/v2/client";
import { catalog } from "../../lib/v2/content";
it("freezes a permutation of stable options while rejecting all other contract changes", () => {
  const item = catalog()
    .families.flatMap((f) => f.items)
    .find((i) => i.fields.some((f) => f.options))!;
  const copy = shuffled(item, () => 0);
  expect(samePresentation(item, copy)).toBe(true);
  const original = item.fields.find((f) => f.options)!.options!;
  expect(copy.fields.find((f) => f.options)!.options).not.toEqual(original);
  copy.prompt += " changed";
  expect(samePresentation(item, copy)).toBe(false);
  copy.prompt = item.prompt;
  copy.fields[0].options?.push("forged option");
  expect(samePresentation(item, copy)).toBe(false);
});
it("rounds displayed numeric oracles without touching choice answers", () => {
  expect(readableAnswer("1.2246467991473532e-16")).toBe("0");
  expect(readableAnswer("0.49999999999999994")).toBe("0.5");
  expect(readableAnswer("-0.0")).toBe("0");
  expect(readableAnswer("0.2222222222222222")).toBe("0.2222222222");
  expect(readableAnswer("1.8")).toBe("1.8");
  expect(readableAnswer("T_AC")).toBe("T_AC");
  expect(readableAnswer("B")).toBe("B");
});

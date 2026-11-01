import { expect, it } from "vitest";
import { shuffled, samePresentation } from "../../lib/v2/presentation";
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

import { randomInt } from "node:crypto";
import { canonical } from "./contracts";
// Stable option IDs are authored strings. Only their display order may change.
// The chosen order is frozen with the attempt and survives resume/restore.
export function shuffled<T extends { fields: { options?: string[] }[] }>(
  item: T,
  draw: (upper: number) => number = randomInt,
): T {
  const copy = structuredClone(item);
  for (const field of copy.fields)
    if (field.options) {
      for (let i = field.options.length - 1; i > 0; i--) {
        const j = draw(i + 1);
        [field.options[i], field.options[j]] = [
          field.options[j],
          field.options[i],
        ];
      }
    }
  return copy;
}
function normalized(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalized);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value).map(([k, v]) => [
        k,
        k === "options" && Array.isArray(v) ? [...v].sort() : normalized(v),
      ]),
    );
  return value;
}
export const samePresentation = (a: unknown, b: unknown) =>
  canonical(normalized(a)) === canonical(normalized(b));

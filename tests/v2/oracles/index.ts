import type { Item } from "../../../lib/v2/content";

// Independent per-family oracles for families added after X22. Each module is
// written by a reviewer who did not author the family and derives every answer
// from the item's inputs (never from its stored answers).
export type FamilyOracle = (item: Item) => (number | string)[];
export const familyOracles: Record<string, FamilyOracle> = {};

import type { Item } from "../../../lib/v2/content";

// Independent per-family oracles for families added after X22. Each module is
// written by a reviewer who did not author the family and derives every answer
// from the item's inputs (never from its stored answers).
export type FamilyOracle = (item: Item) => (number | string)[];
export const familyOracles: Record<string, FamilyOracle> = {};

// Independent numeric oracles for C/M "M" items added after Frames/FK, keyed
// by task structure; written by the source's reviewer, not its author.
export type TaskOracle = (inputs: Record<string, unknown>) => number[];
export const cmOracles: Record<string, TaskOracle> = {};

import { afterEach, expect, it, vi } from "vitest";
vi.mock("../../lib/v2/budget", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/v2/budget")>();
  return {
    ...actual,
    COLLECTION_LIMITS: { ...actual.COLLECTION_LIMITS, exposures: 2 },
  };
});
import { Store } from "../../lib/storage";
import { initialize, learningData, meta } from "../../lib/v2/db";
import { issue, assist } from "../../lib/v2/attempts";
import { exportBackup, validateFull } from "../../lib/v2/backup";
const stores: Store[] = [];
afterEach(() => stores.splice(0).forEach((s) => s.close()));

it("refuses a help exposure at the transport collection bound without changing help, history or counters", () => {
  const store = new Store(":memory:");
  stores.push(store);
  initialize(store.db);
  const attempt = issue(store, { purpose: "practice", source: "XB1" });
  assist(store, attempt.id, { level: 1 });
  const before = learningData(store.db),
    sequence = meta(store.db, "next_event_seq"),
    revision = meta(store.db, "data_revision");
  expect(() => assist(store, attempt.id, { level: 2 })).toThrow(
    "exposures count",
  );
  expect(learningData(store.db)).toEqual(before);
  expect(meta(store.db, "next_event_seq")).toBe(sequence);
  expect(meta(store.db, "data_revision")).toBe(revision);
  expect(validateFull(exportBackup(store)).backup.v2.exposures).toHaveLength(2);
});

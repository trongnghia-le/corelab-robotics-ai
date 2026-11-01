import { afterEach, expect, it } from "vitest";
import { Store } from "../../lib/storage";
import { initialize } from "../../lib/v2/db";
import { issue, submit, history } from "../../lib/v2/attempts";
import { select } from "../../lib/v2/read-model";
import { family } from "../../lib/v2/content";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => stores.splice(0).forEach((s) => s.close()));
it("is deterministic, follows optional readiness goals and prioritizes a credible independent gap", () => {
  const s = fresh(),
    params = new URLSearchParams({ goal: "manipulation" });
  const before = select(s, params);
  expect(before.items[0].id).toBe("XB1");
  expect(select(s, params)).toEqual(before);
  const a = issue(s, { purpose: "practice", source: "X01" });
  submit(s, a.id, {
    answers: { "0": "100", "1": "100", "2": "100" },
    declaredAssistance: 0,
  });
  expect(select(s, new URLSearchParams()).items[0]).toMatchObject({
    id: "X01",
    reason: expect.stringContaining("gap"),
  });
  expect(
    select(
      s,
      new URLSearchParams({ mode: "explore", domain: "Robotics" }),
    ).items.every((f) => f.domain === "Robotics"),
  ).toBe(true);
  expect(() => select(s, new URLSearchParams({ goal: "invented" }))).toThrow(
    "authored",
  );
});
it("filters and paginates bounded summaries without artifacts or oracle fields", () => {
  const s = fresh();
  for (let i = 0; i < 3; i++) issue(s, { purpose: "practice", source: "X01" });
  issue(s, { purpose: "practice", source: "X04" });
  const first = history(s, 2, undefined, family("X01")!.objectiveId);
  expect(first.items).toHaveLength(2);
  expect(first.items.every((a) => a.source === "X01")).toBe(true);
  const all = history(s, 2);
  expect(all.items).toHaveLength(2);
  expect(all.nextCursor).toBeTruthy();
  const next = history(s, 2, all.nextCursor!);
  expect(next.items).toHaveLength(2);
  expect(new Set([...all.items, ...next.items].map((a) => a.id)).size).toBe(4);
  expect(JSON.stringify(all)).not.toContain('"item"');
  expect(JSON.stringify(first).length).toBeLessThan(2000);
});

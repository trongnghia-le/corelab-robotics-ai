import { afterEach, expect, it, vi } from "vitest";
import { Store } from "../../lib/storage";
import { initialize, learningData, meta } from "../../lib/v2/db";
import { issue, assist, submit, attemptById } from "../../lib/v2/attempts";
import { family } from "../../lib/v2/content";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => {
  stores.splice(0).forEach((s) => s.close());
  vi.unstubAllEnvs();
});
function answers(id: string) {
  const item = family("X01")!.items.find((i) => i.id === id)!;
  return Object.fromEntries(
    item.fields.map((f, i) => [String(i), Number(f.answer).toFixed(9)]),
  );
}
it("issues/exposes durably, grades only practice, keeps assistance monotonic and closes once", () => {
  const s = fresh(),
    legacy = s.read(),
    a = issue(s, { purpose: "practice", source: "X01" });
  expect(learningData(s.db).v2_exposures).toHaveLength(1);
  expect(JSON.stringify(a.item)).not.toContain('"answer"');
  expect(assist(s, a.id, { level: 3 }).level).toBe(3);
  expect(assist(s, a.id, { level: 1 }).level).toBe(3);
  const request = { answers: answers(a.item.id), declaredAssistance: 0 };
  const r = submit(s, a.id, request);
  expect(r.result).toHaveProperty("passed", true);
  expect(r.result).toHaveProperty("effectiveAssistance", 3);
  const count = learningData(s.db).v2_exposures.length;
  expect(submit(s, a.id, request)).toEqual(r);
  expect(learningData(s.db).v2_exposures).toHaveLength(count);
  expect(() => submit(s, a.id, { ...request, declaredAssistance: 1 })).toThrow(
    "different submission",
  );
  expect(() => assist(s, a.id, { level: 1 })).toThrow("closed");
  expect(learningData(s.db).v2_evidence).toHaveLength(0);
  expect(s.read()).toEqual(legacy);
});
it("format errors leave the attempt open; fake grading and verification fields are rejected", () => {
  const s = fresh(),
    a = issue(s, { purpose: "placement", source: "X01" }),
    before = meta(s.db, "next_event_seq");
  expect(() =>
    submit(s, a.id, { answers: { "0": "NaN" }, declaredAssistance: 0 }),
  ).toThrow();
  expect(attemptById(s.db, a.id).status).toBe("issued");
  expect(meta(s.db, "next_event_seq")).toBe(before);
  expect(() =>
    submit(s, a.id, {
      answers: answers(a.item.id),
      declaredAssistance: 0,
      passed: true,
    }),
  ).toThrow();
  expect(() => issue(s, { purpose: "verify", source: "X01" })).toThrow(
    "independently reviewed",
  );
});

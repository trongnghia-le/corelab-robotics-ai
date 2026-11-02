import { afterEach, expect, it } from "vitest";
import { Store } from "../../lib/storage";
import { initialize } from "../../lib/v2/db";
import {
  objectiveDetail,
  reviewSourceFor,
  summaries,
} from "../../lib/v2/read-model";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
afterEach(() => stores.splice(0).forEach((s) => s.close()));
it("adds a readable title to every assessment form without changing its id", () => {
  const forms = summaries(fresh()).forms;
  expect(forms.length).toBeGreaterThan(0);
  for (const f of forms) {
    expect(typeof f.title).toBe("string");
    expect(f.title.length).toBeGreaterThan(0);
  }
  expect(forms.find((f) => f.id === "F-R04")?.title).toBe(
    "Planar arm pose check",
  );
});
it("names the approved review pool for an objective, or null", () => {
  expect(reviewSourceFor("R04.planar-fk")).toBe("RV-R04");
  expect(reviewSourceFor("M12.frame-labels")).toBe("RV-FRAMES");
  expect(reviewSourceFor("M07.euler-step")).toBe(null);
});
it("serves an objective's own bridge text and no bridge elsewhere", () => {
  const s = fresh();
  expect(objectiveDetail(s, "M01.radians-trig").bridge).toContain("radian");
  expect(objectiveDetail(s, "R04.planar-fk").bridge).toBe(null);
});

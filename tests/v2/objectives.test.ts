import { expect, it } from "vitest";
import {
  bridgeText,
  curriculumPreview,
  objectives,
  validateObjectives,
} from "../../lib/v2/objectives";
import { topics } from "../../lib/curriculum";
it("resolves typed authored objectives, readiness, media and advisory curriculum identities", () => {
  const r = objectives(),
    p = curriculumPreview();
  expect(r.objectives).toHaveLength(30);
  expect(topics).toHaveLength(169);
  expect(p.nodes).toHaveLength(176);
  expect(p.nodes.reduce((n, x) => n + x.prerequisites.length, 0)).toBe(319);
  expect(
    r.objectives.find((o) => o.id === "R04.planar-fk")?.learn,
  ).toContainEqual({
    type: "visualization",
    id: "forward-kinematics",
    topic: "R04",
  });
  expect(bridgeText()).toContain("optional");
});
it("rejects cycles, dangling references, duplicate readiness and incorrect media types", () => {
  const r = structuredClone(objectives());
  const fk = r.objectives.find((o) => o.id === "R04.planar-fk")!;
  fk.readiness.push({ objective: fk.id, version: 1, strength: "recommended" });
  expect(() => validateObjectives(r)).toThrow("cycle");
  fk.readiness.pop();
  fk.readiness.push({ ...fk.readiness[0] });
  expect(() => validateObjectives(r)).toThrow("Duplicate readiness");
  fk.readiness.pop();
  fk.practice.push("missing");
  expect(() => validateObjectives(r)).toThrow("practice reference");
  const invalid = JSON.parse(JSON.stringify(objectives()));
  invalid.objectives[0].learn.push({
    type: "visualization",
    id: "frames",
    topic: "R04",
  });
  expect(() => validateObjectives(invalid)).toThrow();
});

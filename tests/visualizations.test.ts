import { describe, it, expect } from "vitest";
import {
  add,
  dot,
  projection,
  transform,
  determinant,
  forward,
  jacobian,
  gradientStep,
  quadratic,
  pidResponse,
  convolve,
  gridTransition,
  qUpdate,
  initialGrid,
  trainGrid,
  GOAL,
  START,
} from "../lib/visualization-math";
describe("offline visual teaching models", () => {
  it("adds vectors and projects with an orthogonal residual, including zero direction", () => {
    expect(add([3, 2], [1, 1])).toEqual([4, 3]);
    expect(projection([3, 2], [1, 1])).toEqual([2.5, 2.5]);
    const u: [number, number] = [3, -2],
      v: [number, number] = [-2, 4],
      p = projection(u, v)!;
    expect(dot([u[0] - p[0], u[1] - p[1]], v)).toBeCloseTo(0);
    expect(projection(u, [0, 0])).toBeNull();
  });
  it("maps matrix columns, preserves rotation lengths and detects singularity", () => {
    expect(transform([1, 1, 0, 1], [1, 1])).toEqual([2, 1]);
    expect(transform([0, -1, 1, 0], [3, 4])).toEqual([-4, 3]);
    expect(determinant([1, 2, 2, 4])).toBe(0);
    expect(determinant([0, -1, 1, 0])).toBe(1);
  });
  it("distinguishes gradient convergence, oscillation and divergence", () => {
    expect(gradientStep(4, 0.4)).toBeCloseTo(2.4);
    let x = 4;
    for (let i = 0; i < 30; i++) x = gradientStep(x, 0.4);
    expect(quadratic(x)).toBeLessThan(1e-10);
    expect(gradientStep(4, 2)).toBe(-4);
    expect(Math.abs(gradientStep(4, 2.5))).toBeGreaterThan(4);
  });
  it("uses relative robot angles and correct planar FK", () => {
    const p = forward(Math.PI / 2, 0).tip;
    expect(p[0]).toBeCloseTo(0);
    expect(p[1]).toBeCloseTo(3.5);
    expect(forward(0, Math.PI).tip[0]).toBeCloseTo(0.5);
  });
  it("matches the analytic Jacobian to finite differences and singular configurations", () => {
    const a = 0.7,
      b = -0.5,
      h = 1e-6,
      j = jacobian(a, b),
      p = forward(a, b).tip,
      p1 = forward(a + h, b).tip,
      p2 = forward(a, b + h).tip;
    expect(j[0]).toBeCloseTo((p1[0] - p[0]) / h, 4);
    expect(j[2]).toBeCloseTo((p1[1] - p[1]) / h, 4);
    expect(j[1]).toBeCloseTo((p2[0] - p[0]) / h, 4);
    expect(j[3]).toBeCloseTo((p2[1] - p[1]) / h, 4);
    expect(determinant(jacobian(0, 0))).toBe(0);
  });
  it("models P offset, PI tracking and derivative damping without an algebraic error", () => {
    expect(pidResponse(0, 0, 0).every((p) => p.y === 0)).toBe(true);
    expect(pidResponse(2, 0, 0).at(-1)!.y).toBeCloseTo(2 / 3, 5);
    expect(pidResponse(2, 1, 0).at(-1)!.y).toBeCloseTo(1, 2);
    expect(pidResponse(2, 0, 3)[1].y).toBeLessThan(pidResponse(2, 0, 0)[1].y);
    for (const gains of [
      [0, 8, 0],
      [8, 8, 4],
      [8, 0, 0],
    ])
      expect(
        pidResponse(...(gains as [number, number, number])).every((p) =>
          Number.isFinite(p.y),
        ),
      ).toBe(true);
  });
  it("uses valid cross-correlation, without accidentally reversing the kernel", () => {
    const input = [
      [1, 2, 3],
      [4, 5, 6],
      [7, 8, 9],
    ];
    expect(
      convolve(input, [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
      ]),
    ).toEqual([[5]]);
    expect(
      convolve(input, [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
      ]),
    ).toEqual([[45]]);
    expect(
      convolve(input, [
        [-1, 0, 1],
        [-1, 0, 1],
        [-1, 0, 1],
      ]),
    ).toEqual([[6]]);
    expect(
      convolve(
        Array.from({ length: 5 }, () => [0, 0, 1, 1, 1]),
        [
          [-1, 0, 1],
          [-1, 0, 1],
          [-1, 0, 1],
        ],
      ),
    ).toEqual([
      [3, 3, 0],
      [3, 3, 0],
      [3, 3, 0],
    ]);
  });
  it("handles walls, boundaries and terminal Q targets", () => {
    expect(gridTransition(4, 1).next).toBe(4);
    expect(gridTransition(0, 0).next).toBe(0);
    expect(gridTransition(2, 1)).toEqual({
      next: 3,
      reward: 1,
      terminal: true,
    });
    expect(gridTransition(10, 1).terminal).toBe(true);
    expect(qUpdate(0, 1, 100, true, 0.3, 0.95)).toBeCloseTo(0.3);
    expect(qUpdate(0.2, -0.04, 0.8, false, 0.3, 0.95)).toBeCloseTo(0.356);
  });
  it("trains reproducibly without mutating prior state and learns a goal-reaching policy", () => {
    const empty = initialGrid(),
      trained = trainGrid(empty, 500, 0.3, 0.95, 0.2);
    expect(trained).toEqual(trainGrid(initialGrid(), 500, 0.3, 0.95, 0.2));
    expect(empty.episodes).toBe(0);
    expect(empty.q.flat().every((v) => v === 0)).toBe(true);
    expect(trained.successes).toBeGreaterThan(400);
    let state = START;
    for (let step = 0; step < 20 && state !== GOAL; step++) {
      const row = trained.q[state];
      state = gridTransition(state, row.indexOf(Math.max(...row))).next;
    }
    expect(state).toBe(GOAL);
  });
});

/** Small, deterministic teaching models. No hardware or mastery side effects. */
export type Vec2 = [number, number];
export type Mat2 = [number, number, number, number];
export const add = (u: Vec2, v: Vec2): Vec2 => [u[0] + v[0], u[1] + v[1]];
export const dot = (u: Vec2, v: Vec2) => u[0] * v[0] + u[1] * v[1];
export function projection(u: Vec2, v: Vec2): Vec2 | null {
  const d = dot(v, v);
  return d === 0 ? null : [(v[0] * dot(u, v)) / d, (v[1] * dot(u, v)) / d];
}
export const transform = (a: Mat2, v: Vec2): Vec2 => [
  a[0] * v[0] + a[1] * v[1],
  a[2] * v[0] + a[3] * v[1],
];
export const determinant = (a: Mat2) => a[0] * a[3] - a[1] * a[2];
export const quadratic = (x: number) => 0.5 * x * x;
export const gradientStep = (x: number, rate: number) => x - rate * x;
/** Angles in radians, lengths in metres. q2 is relative to link 1. */
export function forward(
  q1: number,
  q2: number,
  l1 = 2,
  l2 = 1.5,
): { elbow: Vec2; tip: Vec2 } {
  const elbow: Vec2 = [l1 * Math.cos(q1), l1 * Math.sin(q1)];
  return {
    elbow,
    tip: add(elbow, [l2 * Math.cos(q1 + q2), l2 * Math.sin(q1 + q2)]),
  };
}
export function jacobian(q1: number, q2: number, l1 = 2, l2 = 1.5): Mat2 {
  return [
    -l1 * Math.sin(q1) - l2 * Math.sin(q1 + q2),
    -l2 * Math.sin(q1 + q2),
    l1 * Math.cos(q1) + l2 * Math.cos(q1 + q2),
    l2 * Math.cos(q1 + q2),
  ];
}
/** Normalized plant y'=-y+u, unit step, derivative on measurement: u=Kp(1-y)+Ki*z-Kd*y'.
 * Solving that algebraic loop gives y'=[Kp(1-y)+Ki*z-y]/(1+Kd). Euler dt=.01. */
export function pidResponse(kp: number, ki: number, kd: number) {
  let y = 0,
    integral = 0;
  const samples = [{ t: 0, y: 0, u: kp / (1 + kd) }];
  for (let i = 1; i <= 1600; i++) {
    const error = 1 - y;
    const dy = (kp * error + ki * integral - y) / (1 + kd);
    const u = dy + y;
    y += 0.01 * dy;
    integral += 0.01 * error;
    if (i % 10 === 0) samples.push({ t: i * 0.01, y, u });
  }
  return samples;
}
/** CNN convention: valid cross-correlation (no kernel flip), stride=1, no padding. */
export function convolve(input: number[][], kernel: number[][]): number[][] {
  const size = input.length - kernel.length + 1;
  return Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) =>
      kernel.reduce(
        (sum, row, kr) =>
          sum +
          row.reduce((s, weight, kc) => s + input[r + kr][c + kc] * weight, 0),
        0,
      ),
    ),
  );
}
export const WALLS = [5, 9];
export const START = 12,
  GOAL = 3,
  HAZARD = 11;
export const ACTIONS = ["↑", "→", "↓", "←"];
export function gridTransition(state: number, action: number) {
  if (state === GOAL || state === HAZARD)
    return { next: state, reward: 0, terminal: true };
  const dr = [-1, 0, 1, 0][action],
    dc = [0, 1, 0, -1][action];
  const r = Math.floor(state / 4) + dr,
    c = (state % 4) + dc;
  const candidate = r * 4 + c;
  const next =
    r < 0 || r > 3 || c < 0 || c > 3 || WALLS.includes(candidate)
      ? state
      : candidate;
  return {
    next,
    reward: next === GOAL ? 1 : next === HAZARD ? -1 : -0.04,
    terminal: next === GOAL || next === HAZARD,
  };
}
export const qUpdate = (
  old: number,
  reward: number,
  nextMax: number,
  terminal: boolean,
  alpha: number,
  gamma: number,
) => old + alpha * (reward + (terminal ? 0 : gamma * nextMax) - old);
export type GridTraining = {
  q: number[][];
  seed: number;
  episodes: number;
  successes: number;
  last: {
    state: number;
    action: number;
    old: number;
    reward: number;
    nextMax: number;
    terminal: boolean;
    value: number;
  } | null;
};
export const initialGrid = (): GridTraining => ({
  q: Array.from({ length: 16 }, () => [0, 0, 0, 0]),
  seed: 42,
  episodes: 0,
  successes: 0,
  last: null,
});
export function trainGrid(
  previous: GridTraining,
  episodes: number,
  alpha: number,
  gamma: number,
  epsilon: number,
): GridTraining {
  const result: GridTraining = {
    ...previous,
    q: previous.q.map((row) => [...row]),
  };
  const random = () => {
    result.seed = (Math.imul(1664525, result.seed) + 1013904223) >>> 0;
    return result.seed / 4294967296;
  };
  for (let ep = 0; ep < episodes; ep++) {
    let state = START;
    for (let step = 0; step < 150; step++) {
      const row = result.q[state],
        best = Math.max(...row);
      const ties = row
        .map((v, i) => (v === best ? i : -1))
        .filter((i) => i >= 0);
      const action =
        random() < epsilon
          ? Math.floor(random() * 4)
          : ties[Math.floor(random() * ties.length)];
      const { next, reward, terminal } = gridTransition(state, action);
      const old = row[action],
        nextMax = Math.max(...result.q[next]);
      const value = qUpdate(old, reward, nextMax, terminal, alpha, gamma);
      row[action] = value;
      result.last = { state, action, old, reward, nextMax, terminal, value };
      state = next;
      if (terminal) {
        if (next === GOAL) result.successes++;
        break;
      }
    }
    result.episodes++;
  }
  return result;
}

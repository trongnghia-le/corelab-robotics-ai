import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X30 (pure-pursuit lookahead and trace evaluation).
// The lookahead uses the quadratic in the segment parameter (a t^2 + b t + c = 0)
// and keeps the larger root; the robot-frame lateral offset comes from the
// cross product of the heading unit vector with the target offset. Distances to
// segments (and to the sample polyline) are found by ternary search on the convex
// squared-distance function instead of a closed-form projection.
type P = [number, number];
const val = (v: unknown) => {
  const [n, d = "1"] = String(v).split("/");
  return Number(n) / Number(d);
};
const pt = (v: unknown): P => {
  const a = v as unknown[];
  return [val(a[0]), val(a[1])];
};
const pts = (v: unknown): P[] => (v as unknown[]).map(pt);

function segDist(a: P, b: P, p: P): number {
  let lo = 0,
    hi = 1;
  const f = (t: number) =>
    (a[0] + t * (b[0] - a[0]) - p[0]) ** 2 + (a[1] + t * (b[1] - a[1]) - p[1]) ** 2;
  for (let i = 0; i < 200; i++) {
    const m1 = lo + (hi - lo) / 3,
      m2 = hi - (hi - lo) / 3;
    if (f(m1) < f(m2)) hi = m2;
    else lo = m1;
  }
  return Math.sqrt(f((lo + hi) / 2));
}
const polyDist = (line: P[], p: P) =>
  Math.min(...line.slice(1).map((b, i) => segDist(line[i], b, p)));

function lookahead(path: P[], x: number, y: number, L: number) {
  for (let i = 0; i + 1 < path.length; i++) {
    const [ax, ay] = path[i],
      dx = path[i + 1][0] - ax,
      dy = path[i + 1][1] - ay;
    const fx = ax - x,
      fy = ay - y;
    const a = dx * dx + dy * dy,
      b = 2 * (fx * dx + fy * dy),
      c = fx * fx + fy * fy - L * L;
    const disc = b * b - 4 * a * c;
    if (disc < 0) continue;
    const t = (-b + Math.sqrt(disc)) / (2 * a);
    if (t >= -1e-12 && t <= 1 + 1e-12)
      return { kind: "circle", seg: i, tx: ax + t * dx, ty: ay + t * dy };
  }
  const g = path[path.length - 1];
  if (Math.hypot(g[0] - x, g[1] - y) < L)
    return { kind: "end", seg: path.length - 2, tx: g[0], ty: g[1] };
  throw new Error("lost");
}

function kappaOf(x: number, y: number, th: number, tx: number, ty: number) {
  const dx = tx - x,
    dy = ty - y;
  const yL = Math.cos(th) * dy - Math.sin(th) * dx; // cross(heading, offset)
  return (2 * yL) / (dx * dx + dy * dy);
}

function pick(item: Item, fieldIndex: number, conclusion: string) {
  const options = (item.fields[fieldIndex] as { options?: string[] }).options ?? [];
  const m = options.filter((o) => o === conclusion);
  expect(m).toHaveLength(1);
  return m[0];
}

function trace(p: Record<string, unknown>) {
  const path = pts(p.path),
    samples = pts(p.points);
  const err = samples.map((s) => polyDist(path, s));
  const goal = path[path.length - 1];
  const corridor = val(p.corridor),
    tol = val(p.goal_tol);
  const exit = err.findIndex((e) => e > corridor);
  const reach = samples.findIndex((s) => Math.hypot(s[0] - goal[0], s[1] - goal[1]) <= tol);
  const clear: number[] = [];
  for (let j = 1; j + 1 < path.length; j++)
    clear.push(samples.length === 1 ? Math.hypot(samples[0][0] - path[j][0], samples[0][1] - path[j][1]) : polyDist(samples, path[j]));
  const cut = clear.some((c) => c > corridor);
  const verdict = exit >= 0 ? "off-corridor" : reach < 0 ? "timeout" : cut ? "corner-cut" : "ok";
  const max = Math.max(...err);
  return { err, max, rms: Math.sqrt(err.reduce((s, e) => s + e * e, 0) / err.length), exit, reach, clear, verdict, argmax: err.indexOf(max) };
}

familyOracles["X30"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  switch (item.structure) {
    case "pure-pursuit.lookahead.circle-line@1": {
      const t = lookahead(pts(p.path), val(p.x), val(p.y), val(p.lookahead));
      return [t.tx, kappaOf(val(p.x), val(p.y), val(p.theta), t.tx, t.ty)];
    }
    case "pure-pursuit.lookahead.corner@1": {
      const t = lookahead(pts(p.path), val(p.x), val(p.y), val(p.lookahead));
      return [t.ty, t.seg, kappaOf(val(p.x), val(p.y), val(p.theta), t.tx, t.ty)];
    }
    case "pure-pursuit.lookahead.end-saturation@1": {
      const x = val(p.x),
        y = val(p.y),
        t = lookahead(pts(p.path), x, y, val(p.lookahead));
      const k = kappaOf(x, y, val(p.theta), t.tx, t.ty);
      let v = Math.min(val(p.v_cmd), val(p.v_max));
      if (Math.abs(v * k) > val(p.w_max)) v = val(p.w_max) / Math.abs(k);
      return [k, v, v * k];
    }
    case "pure-pursuit.trace.cross-track@1": {
      const r = trace({ ...p, corridor: "1", goal_tol: "1" });
      return [r.max, r.rms, r.argmax];
    }
    case "pure-pursuit.trace.vertex-clearance@1": {
      const r = trace(p);
      return [r.max, r.clear[0], pick(item, 2, r.verdict)];
    }
    case "pure-pursuit.trace.verdict@1": {
      const r = trace(p);
      return [r.exit, r.reach, r.max, pick(item, 3, r.verdict)];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

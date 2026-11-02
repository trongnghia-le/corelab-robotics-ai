import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X34 (target selection and a bounded pan/tilt visual
// servo step). The projection uses an explicit rotation matrix R = Ry(pan) Rx(tilt)
// whose columns are the camera axes in the base frame (x right, y down, z
// forward), and camera coordinates are R^T p. Target selection is a filter plus
// a sort (confidence descending, index ascending) instead of a running maximum.
// The suite is simulated by integrating the pan and tilt angles directly.
type V3 = [number, number, number];
type Row = { i: number; label: number; colour: number; u: number; v: number; depth: number; stamp: number; conf: number };

const num = (s: unknown) => Number(s as string);
const mul = (A: number[][], B: number[][]) => A.map((r) => B[0].map((_, j) => r.reduce((s, _v, k) => s + r[k] * B[k][j], 0)));

function rotation(pan: number, tilt: number): number[][] {
  const Ry = [
    [Math.cos(pan), 0, Math.sin(pan)],
    [0, 1, 0],
    [-Math.sin(pan), 0, Math.cos(pan)],
  ];
  // Rx maps +z toward +y (tilt positive = looking down), +y toward -z.
  const Rx = [
    [1, 0, 0],
    [0, Math.cos(tilt), Math.sin(tilt)],
    [0, -Math.sin(tilt), Math.cos(tilt)],
  ];
  return mul(Ry, Rx);
}

function project(pan: number, tilt: number, p: V3): { x: number; y: number; z: number } {
  const R = rotation(pan, tilt);
  const c = [0, 1, 2].map((j) => R[0][j] * p[0] + R[1][j] * p[1] + R[2][j] * p[2]); // R^T p
  return { x: c[0] / c[2], y: c[1] / c[2], z: c[2] };
}

const clip = (v: number, b: number) => Math.min(b, Math.max(-b, v));

function rows(d: unknown): Row[] {
  return (d as string[][]).map((r, i) => ({
    i, label: num(r[0]), colour: num(r[1]), u: num(r[2]), v: num(r[3]), depth: num(r[4]), stamp: num(r[5]), conf: num(r[6]),
  }));
}

function valid(rs: Row[], label: number, now: number, lim: number[]): Row[] {
  const eps = 1e-9; // decimal inputs: age 0.25 = 50 - 49.75 is exact in binary, others may not be
  return rs
    .filter((r) => {
      const age = now - r.stamp;
      return r.label === label && age >= -eps && age <= lim[0] + eps && r.depth >= lim[1] - eps && r.depth <= lim[2] + eps && r.conf >= lim[3] - eps;
    })
    .sort((a, b) => b.conf - a.conf || a.i - b.i);
}

function pick(options: string[], word: RegExp): string {
  const m = options.filter((o) => word.test(o));
  expect(m.length).toBe(1);
  return m[0];
}

familyOracles["X34"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  switch (item.structure) {
    case "alignment.select-target@1": {
      const rs = rows(p.detections);
      const label = num(p.label);
      const now = num(p.now);
      const lim = (p.limits as string[]).map(Number);
      const v = valid(rs, label, now, lim);
      const sel = v.length ? v[0].i : -1;
      const ageRule = rs.filter((r) => {
        if (r.label !== label) return false;
        const age = now - r.stamp;
        const ageBad = !(age >= -1e-9 && age <= lim[0] + 1e-9);
        const otherOk = r.depth >= lim[1] - 1e-9 && r.depth <= lim[2] + 1e-9 && r.conf >= lim[3] - 1e-9;
        return ageBad && otherOk;
      }).length;
      // field orders: item 1 = (age of row 1, #valid, selected); item 2 = (#valid, selected, age-only rejects)
      const labels = item.fields.map((f) => f.label);
      return labels.map((l) => {
        if (/^Age of row (\d+)/.test(l)) return Math.round((now - rs[Number(/(\d+)/.exec(l)![1])].stamp) * 1e6) / 1e6;
        if (/Number of valid/.test(l)) return v.length;
        if (/Selected row/.test(l)) return sel;
        if (/age rule/.test(l)) return ageRule;
        throw new Error("Unknown field " + l);
      });
    }
    case "alignment.servo-cycle-sequence@1": {
      const K = (p.K as string[]).map(Number);
      const lim = (p.limits as string[]).map(Number);
      const [gain, wmax, tol] = (p.loop as string[]).map(Number);
      const label = num(p.label);
      const cyc = (p.cycles as { now: string; detections: string[][] }[]).map((c) => {
        const rs = rows(c.detections);
        const now = num(c.now);
        const v = valid(rs, label, now, lim);
        if (!v.length) return { status: "stop", wpan: 0, wtilt: 0, age: NaN, rs, now };
        const s = v[0];
        const ex = (s.u - K[2]) / K[0];
        const ey = (s.v - K[3]) / K[1];
        const st = Math.abs(ex) <= tol + 1e-12 && Math.abs(ey) <= tol + 1e-12 ? "aligned" : "track";
        return { status: st, wpan: st === "track" ? clip(gain * ex, wmax) : 0, wtilt: st === "track" ? clip(gain * ey, wmax) : 0, age: now - s.stamp, rs, now };
      });
      const choiceField = (idx: number) => {
        const f = item.fields[idx];
        expect(f.kind).toBe("choice");
        return f.options as string[];
      };
      const c3 = cyc[2];
      const label5 = c3.rs.filter((r) => r.label === label)[0];
      return [
        Math.round(cyc[0].wpan * 1e9) / 1e9,
        pick(choiceField(1), new RegExp("^" + cyc[1].status + ":")),
        pick(choiceField(2), new RegExp("^" + cyc[2].status + ":")),
        Math.round((c3.now - label5.stamp) * 1e6) / 1e6,
      ];
    }
    case "alignment.servo-step@1": {
      const K = (p.K as string[]).map(Number);
      const ex = (num(p.u) - K[2]) / K[0];
      const ey = (num(p.v) - K[3]) / K[1];
      const g = num(p.gain);
      const w = num(p.wmax);
      return [ex, ey, clip(g * ex, w), clip(g * ey, w)];
    }
    case "alignment.project-target@1": {
      const pt = (p.point as string[]).map(Number) as V3;
      const r = project(num(p.pan), num(p.tilt), pt);
      expect(r.z).toBeGreaterThan(0);
      // the target is seen left of / above the centre when x / y is negative:
      // turn pan toward it (negative = left) and tilt toward it (negative = up).
      const wantPan = r.x < 0 ? /Pan negative/ : /Pan positive/;
      const wantTilt = r.y < 0 ? /tilt negative/ : /tilt positive/;
      const opts = item.fields[3].options as string[];
      const m = opts.filter((o) => wantPan.test(o) && wantTilt.test(o));
      expect(m.length).toBe(1);
      return [r.z, r.x, r.y, m[0]];
    }
    case "alignment.run-suite@1": {
      const t = (p.target as string[]).map(Number) as V3;
      const starts = (p.starts as string[][]).map((s) => s.map(Number));
      const g = num(p.gain);
      const w = num(p.wmax);
      const dt = num(p.dt);
      const tol = num(p.tol);
      const maxSteps = num(p.max_steps);
      const run = (s: number[]) => {
        let pan = s[0];
        let tilt = s[1];
        const trace: number[] = [pan];
        let result = -1;
        for (let k = 0; ; k++) {
          const e = project(pan, tilt, t);
          if (e.z <= 0) break;
          if (Math.abs(e.x) <= tol && Math.abs(e.y) <= tol) { result = k; break; }
          if (k >= maxSteps) break;
          pan += clip(g * e.x, w) * dt;
          tilt += clip(g * e.y, w) * dt;
          trace.push(pan);
        }
        return { result, trace };
      };
      const runs = starts.map(run);
      // Pan after 2 steps for the first start: record the trace without stopping early.
      let pan = starts[0][0];
      let tilt = starts[0][1];
      for (let k = 0; k < 2; k++) {
        const e = project(pan, tilt, t);
        pan += clip(g * e.x, w) * dt;
        tilt += clip(g * e.y, w) * dt;
      }
      const out: (number | string)[] = runs.map((r) => r.result);
      out.push(pan);
      expect(item.fields.length).toBe(out.length);
      return out;
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

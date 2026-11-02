import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle: numerically integrate the speed profile
// v(t) = clamp(A t, A (T - t), vpeak) and search (bisection) for the unknown
// duration or peak speed whose area equals the distance. No closed-form phase
// formulas and no quadratic are used.
const N = 20000;
const vel = (t: number, T: number, vp: number, A: number) =>
  Math.max(0, Math.min(A * t, vp, A * (T - t)));
function area(T: number, vp: number, A: number, upTo = T): number {
  const h = upTo / N;
  let s = 0.5 * (vel(0, T, vp, A) + vel(upTo, T, vp, A));
  for (let i = 1; i < N; i++) s += vel(i * h, T, vp, A);
  return s * h;
}
function bisect(f: (x: number) => boolean, lo: number, hi: number): number {
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (f(mid)) hi = mid;
    else lo = mid;
  }
  return (lo + hi) / 2;
}
// shortest time whose reachable distance (peak speed capped at vmax) is d
const minTime = (d: number, vmax: number, A: number) =>
  d === 0 ? 0 : bisect((T) => area(T, vmax, A) >= d, 0, 1000);
// peak speed for a fixed duration T with acceleration A kept
const peakFor = (d: number, T: number, A: number) =>
  bisect((v) => area(T, v, A) >= d, 0, (A * T) / 2);

familyOracles["X24"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const n = (k: string) => Number(p[k]);
  const pick = (idx: number, test: (o: string) => boolean) => {
    const f = item.fields[idx];
    const m = (f.options ?? []).filter(test);
    expect(m).toHaveLength(1);
    return m[0];
  };
  switch (item.structure) {
    case "trapezoid.profile.phases@1": {
      const d = Math.abs(n("distance")), vmax = n("vmax"), A = n("amax");
      const T = minTime(d, vmax, A);
      const cruises = A * T / 2 > vmax + 1e-6;
      const ta = cruises ? vmax / A : T / 2;
      const type = pick(0, (o) =>
        cruises
          ? /^Trapezoidal/.test(o) && /reaches vmax, cruises, then brakes/.test(o)
          : /^Triangular/.test(o) && /brakes before it ever reaches/.test(o),
      );
      return [type, ta, T - 2 * ta, T];
    }
    case "trapezoid.profile.sample-reversed@1": {
      const D = n("distance"), vmax = n("vmax"), A = n("amax"), t = n("t");
      const sg = Math.sign(D), d = Math.abs(D);
      const T = minTime(d, vmax, A);
      const vp = Math.min(vmax, (A * T) / 2);
      return [sg * vp, T, t >= T ? D : sg * area(T, vp, A, t)];
    }
    case "trapezoid.profile.scaled-sample@1": {
      const D = n("distance"), vmax = n("vmax"), A = n("amax");
      const T = n("duration"), t = n("t");
      const sg = Math.sign(D), d = Math.abs(D);
      const Tmin = minTime(d, vmax, A);
      expect(T).toBeGreaterThan(Tmin);
      const vp = peakFor(d, T, A);
      return [Tmin, vp, sg * area(T, vp, A, t), sg * vel(t, T, vp, A)];
    }
    case "trapezoid.sync.common-time@1": {
      const t1 = minTime(Math.abs(n("d1")), n("v1"), n("a1"));
      const t2 = minTime(Math.abs(n("d2")), n("v2"), n("a2"));
      return [t1, t2, Math.max(t1, t2)];
    }
    case "trapezoid.sync.scale-peak@1": {
      const t1 = minTime(Math.abs(n("d1")), n("v1"), n("a1"));
      const t2 = minTime(Math.abs(n("d2")), n("v2"), n("a2"));
      const T = Math.max(t1, t2);
      const d2 = Math.abs(n("d2")), A2 = n("a2");
      const vp = T - t2 < 1e-9 ? Math.min(n("v2"), (A2 * T) / 2) : peakFor(d2, T, A2);
      return [T, Math.sign(n("d2")) * vp, T - 2 * (vp / A2)];
    }
    case "trapezoid.sync.request-check@1": {
      const t1 = minTime(Math.abs(n("d1")), n("v1"), n("a1"));
      const t2 = minTime(Math.abs(n("d2")), n("v2"), n("a2"));
      const T = Math.max(t1, t2), req = n("request");
      const feasible = req >= T - 1e-9;
      expect(feasible).toBe(false);
      const choice = pick(
        1,
        (o) =>
          /^Impossible/.test(o) && o.includes(`joint ${t1 >= t2 ? 1 : 2} `),
      );
      // smallest vmax whose minimum time is <= request (min time falls as vmax rises)
      const need = bisect(
        (v) => minTime(Math.abs(n("d1")), v, n("a1")) <= req,
        0.01, 100,
      );
      return [T, choice, need];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

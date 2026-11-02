import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X25 (one-link pendulum model, integrators, computed torque).
// Energy uses the half-angle form 2 m g lc sin^2(q/2) instead of 1 - cos q; the
// holdable angle comes from atan2 rather than asin; the wrong-gravity rest angle is
// found by bisection on the (monotone) torque balance; every choice option is
// selected from the conclusion derived from the numbers, never from a stored answer.
const val = (v: unknown) => {
  const [n, d = "1"] = String(v).split("/");
  return Number(n) / Number(d);
};
const energy = (I: number, k: number, q: number, qd: number) =>
  0.5 * I * qd * qd + 2 * k * Math.sin(q / 2) ** 2;
function pick(options: string[], needle: RegExp): string {
  const hits = options.filter((o) => needle.test(o));
  expect(hits).toHaveLength(1);
  return hits[0];
}
familyOracles["X25"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const n = (key: string) => val(p[key]);
  const fieldOptions = (idx: number) => {
    const f = item.fields[idx];
    expect(f.kind).toBe("choice");
    const opts = (f as { options?: string[] }).options!;
    expect(opts.length).toBeGreaterThanOrEqual(4);
    return opts;
  };
  switch (item.structure) {
    case "pendulum.model.acceleration@1": {
      const I = n("ic") + n("m") * n("lc") ** 2;
      const k = n("m") * n("g") * n("lc");
      const grav = k * Math.sin(n("q"));
      const acc = (n("tau") - n("b") * n("qd") - grav) / I;
      return [I, grav, acc, energy(I, k, n("q"), n("qd"))];
    }
    case "pendulum.integrators.one-step@1": {
      const I = n("ic") + n("m") * n("lc") ** 2;
      const k = n("m") * n("g") * n("lc");
      const [q, v, h] = [n("q"), n("qd"), n("h")];
      const a = -(k * Math.sin(q)) / I;
      const vNext = v + h * a;
      // explicit: angle moves with the OLD rate; semi-implicit: with the NEW rate
      const qExplicit = q + h * v;
      const qSymplectic = q + h * vNext;
      return [
        energy(I, k, q, v),
        vNext,
        energy(I, k, qExplicit, vNext),
        qSymplectic,
        energy(I, k, qSymplectic, vNext),
      ];
    }
    case "pendulum.diagnose.energy-samples@1": {
      const qs = (p.qs as unknown[]).map(val);
      const qds = (p.qds as unknown[]).map(val);
      const k = n("m") * n("g") * n("lc");
      const spread = (I: number) => {
        const e = qs.map((q, i) => energy(I, k, q, qds[i]));
        return (Math.max(...e) - Math.min(...e)) / Math.max(...e);
      };
      const sA = spread(n("m") * n("lc") ** 2);
      const sB = spread(n("ic") + n("m") * n("lc") ** 2);
      const flat = (s: number) => s < 0.01;
      const opts = fieldOptions(2);
      let choice: string;
      if (flat(sA) && flat(sB)) choice = pick(opts, /^Both models/);
      else if (!flat(sA) && !flat(sB)) choice = pick(opts, /^Neither model/);
      else if (flat(sB)) choice = pick(opts, /^Model B/);
      else choice = pick(opts, /^Model A/);
      return [sA, sB, choice];
    }
    case "computed-torque.law@1": {
      const I = n("ic") + n("m") * n("lc") ** 2;
      const aCmd =
        n("qdd_d") + n("kd") * (n("qd_d") - n("qd")) + n("kp") * (n("q_d") - n("q"));
      const raw =
        I * aCmd + n("b") * n("qd") + n("m") * n("g") * n("lc") * Math.sin(n("q"));
      const lim = n("tau_max");
      return [aCmd, raw, Math.min(lim, Math.max(-lim, raw))];
    }
    case "computed-torque.hold-limit@1": {
      const k = n("m") * n("g") * n("lc");
      const hold = k * Math.sin(n("q_ref"));
      const s = n("tau_max") / k;
      expect(s).toBeLessThan(1);
      const qMax = Math.atan2(s, Math.sqrt(1 - s * s));
      expect(qMax).toBeLessThan(Math.PI / 2);
      const opts = fieldOptions(2);
      const choice =
        hold <= n("tau_max")
          ? pick(opts, /^It stops at q_ref/)
          : pick(opts, /^It stops short of q_ref/);
      return [hold, qMax, choice];
    }
    case "computed-torque.wrong-gravity-offset@1": {
      const I = n("ic") + n("m") * n("lc") ** 2;
      const dk = n("m") * n("lc") * (n("g") - n("g_model"));
      const kk = n("m") * n("g") * n("lc");
      // balance F(q) = I kp (q_ref - q) - dk sin q is strictly decreasing for dk >= 0
      expect(dk).toBeGreaterThanOrEqual(0);
      const F = (q: number) => I * n("kp") * (n("q_ref") - q) - dk * Math.sin(q);
      let lo = 0,
        hi = n("q_ref");
      expect(F(lo)).toBeGreaterThan(0);
      expect(F(hi)).toBeLessThan(0);
      for (let i = 0; i < 200; i++) {
        const mid = (lo + hi) / 2;
        if (F(mid) > 0) lo = mid;
        else hi = mid;
      }
      const qss = (lo + hi) / 2;
      // torque at rest from the controller side (P term + modelled gravity)
      const tau = I * n("kp") * (n("q_ref") - qss) + n("m") * n("g_model") * n("lc") * Math.sin(qss);
      expect(Math.abs(tau - kk * Math.sin(qss))).toBeLessThan(1e-9);
      return [qss, n("q_ref") - qss, tau];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

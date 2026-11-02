import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X36 (episode QA, alignment lag, train-only
// least-squares behaviour cloning). Exact rational arithmetic on bigint.
// Differences from the usual route: QA findings are built as a set of named
// kinds per episode and duplicates are found by exhaustive comparison of a
// canonical string with every earlier episode; the lag is found by testing
// every pair of points for collinearity with the first pair of distinct
// observations (cross products, no fitting); lines are solved from the 2x2
// normal equations by Cramer's rule, not from centred covariances.
type Q = [bigint, bigint];
const gcd = (a: bigint, b: bigint): bigint => (b === 0n ? (a < 0n ? -a : a) : gcd(b, a % b));
const mk = (n: bigint, d: bigint): Q => {
  if (d === 0n) throw new Error("division by zero");
  if (d < 0n) { n = -n; d = -d; }
  const g = gcd(n, d) || 1n;
  return [n / g, d / g];
};
const add = (a: Q, b: Q) => mk(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
const sub = (a: Q, b: Q) => mk(a[0] * b[1] - b[0] * a[1], a[1] * b[1]);
const mul = (a: Q, b: Q) => mk(a[0] * b[0], a[1] * b[1]);
const div = (a: Q, b: Q) => mk(a[0] * b[1], a[1] * b[0]);
const sgn = (a: Q) => (a[0] < 0n ? -1 : a[0] > 0n ? 1 : 0);
const cmp = (a: Q, b: Q) => sgn(sub(a, b));
const rat = (v: unknown): Q => {
  const s = String(v).trim();
  const m = /^(-?)(\d*)(?:\.(\d+))?$/.exec(s);
  if (!m) throw new Error("bad number " + s);
  const frac = m[3] ?? "";
  return mk(BigInt(m[1] + (m[2] || "0") + frac), 10n ** BigInt(frac.length));
};
const num = (a: Q) => Number((a[0] * 10n ** 18n) / a[1]) / 1e18;
const Z0 = mk(0n, 1n);
const N = (n: number) => mk(BigInt(n), 1n);
const sum = (xs: Q[]) => xs.reduce(add, Z0);
const vec = (v: unknown): Q[] => (v as unknown[]).map(rat);
const key = (q: Q) => q[0].toString() + "/" + q[1].toString();

// Normal equations: [n sx; sx sxx] [b w]^T = [sy sxy]^T, Cramer's rule.
const fit = (o: Q[], a: Q[]): { w: Q; b: Q } => {
  const n = N(o.length);
  const sx = sum(o), sy = sum(a);
  const sxx = sum(o.map((x) => mul(x, x)));
  const sxy = sum(o.map((x, i) => mul(x, a[i])));
  const det = sub(mul(n, sxx), mul(sx, sx));
  expect(sgn(det)).not.toBe(0);
  return {
    w: div(sub(mul(n, sxy), mul(sx, sy)), det),
    b: div(sub(mul(sy, sxx), mul(sx, sxy)), det),
  };
};
const mse = (o: Q[], a: Q[], pred: (x: Q) => Q): Q =>
  div(sum(o.map((x, i) => { const e = sub(a[i], pred(x)); return mul(e, e); })), N(o.length));
const outside = (x: Q, lo: Q, hi: Q) => cmp(x, lo) < 0 || cmp(x, hi) > 0;

familyOracles["X36"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  switch (item.structure) {
    case "imitation.qa-counts@1": {
      const t = vec(p.times), o = vec(p.obs), a = vec(p.acts);
      const g = rat(p.max_gap);
      const [olo, ohi] = vec(p.obs_range), [alo, ahi] = vec(p.act_range);
      let back = 0, gap = 0;
      for (let i = 1; i < t.length; i++) {
        const d = sub(t[i], t[i - 1]);
        if (sgn(d) <= 0) back++;
        if (cmp(d, g) > 0) gap++;
      }
      return [
        back,
        gap,
        o.filter((x) => outside(x, olo, ohi)).length,
        a.filter((x) => outside(x, alo, ahi)).length,
      ];
    }
    case "imitation.alignment-lag@1": {
      const o = vec(p.obs), a = vec(p.acts);
      const maxLag = Number(p.max_lag);
      const hits: { k: number; w: Q; b: Q }[] = [];
      for (let k = -maxLag; k <= maxLag; k++) {
        const pts: [Q, Q][] = [];
        for (let i = 0; i < o.length; i++) if (i + k >= 0 && i + k < a.length) pts.push([o[i], a[i + k]]);
        // anchor = first point; partner = first point with a different obs
        const [x0, y0] = pts[0];
        const partner = pts.find((q) => cmp(q[0], x0) !== 0);
        if (!partner) continue;
        const w = div(sub(partner[1], y0), sub(partner[0], x0));
        // collinear iff every point has zero cross product with the anchor-partner direction
        const ok = pts.every(([x, y]) =>
          sgn(sub(mul(sub(y, y0), sub(partner[0], x0)), mul(sub(x, x0), sub(partner[1], y0)))) === 0);
        if (ok) hits.push({ k, w, b: sub(y0, mul(w, x0)) });
      }
      expect(hits.length).toBe(1);
      return [hits[0].k, num(hits[0].w), num(hits[0].b)];
    }
    case "imitation.dataset-qa@1": {
      const T = p.times as unknown[][], O = p.obs as unknown[][], A = p.acts as unknown[][];
      const g = rat(p.max_gap);
      const [olo, ohi] = vec(p.obs_range), [alo, ahi] = vec(p.act_range);
      const canon = (e: number) => JSON.stringify([vec(T[e]).map(key), vec(O[e]).map(key), vec(A[e]).map(key)]);
      let defective = 0, copies = 0, findings = 0;
      for (let e = 0; e < T.length; e++) {
        const kinds = new Set<string>();
        const t = vec(T[e]), o = vec(O[e]), a = vec(A[e]);
        if (t.length !== o.length || o.length !== a.length) kinds.add("length");
        for (let i = 1; i < t.length; i++) {
          if (sgn(sub(t[i], t[i - 1])) <= 0) kinds.add("order");
          if (cmp(sub(t[i], t[i - 1]), g) > 0) kinds.add("gap");
        }
        if (o.some((x) => outside(x, olo, ohi))) kinds.add("obs-range");
        if (a.some((x) => outside(x, alo, ahi))) kinds.add("act-range");
        let dup = false;
        for (let j = 0; j < e; j++) if (canon(j) === canon(e)) dup = true;
        if (dup) { kinds.add("dup"); copies++; }
        if (kinds.size > 0) defective++;
        findings += kinds.size;
      }
      return [defective, copies, findings, T.length - defective];
    }
    case "imitation.fit-line@1": {
      const o = vec(p.obs), a = vec(p.acts), q = rat(p.query_obs);
      const { w, b } = fit(o, a);
      return [num(w), num(b), num(add(mul(w, q), b))];
    }
    case "imitation.heldout-mse@1": {
      const trO = (p.train_obs as unknown[][]).flat().map(rat);
      const trA = (p.train_acts as unknown[][]).flat().map(rat);
      const teO = vec(p.test_obs), teA = vec(p.test_acts);
      const { w, b } = fit(trO, trA);
      const mean = div(sum(trA), N(trA.length));
      return [
        num(w),
        num(b),
        num(mse(teO, teA, (x) => add(mul(w, x), b))),
        num(mse(teO, teA, () => mean)),
      ];
    }
    case "imitation.session-leak@1": {
      const S = p.sessions as string[];
      const test = new Set(p.test_sessions as string[]);
      const O = p.obs as unknown[][], A = p.acts as unknown[][];
      const pick = (inTest: boolean, src: unknown[][]) =>
        src.flatMap((row, e) => (test.has(S[e]) === inTest ? row.map(rat) : []));
      const trO = pick(false, O), trA = pick(false, A), teO = pick(true, O), teA = pick(true, A);
      const clean = fit(trO, trA);
      const mean = div(sum(trA), N(trA.length));
      const leaky = fit([...trO, ...teO], [...trA, ...teA]);
      return [
        num(mse(teO, teA, (x) => add(mul(clean.w, x), clean.b))),
        num(mse(teO, teA, () => mean)),
        num(mse(teO, teA, (x) => add(mul(leaky.w, x), leaky.b))),
        num(leaky.b),
      ];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

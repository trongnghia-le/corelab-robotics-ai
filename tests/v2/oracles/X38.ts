import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X38 (first-order least-squares identification).
// All linear algebra is exact rational arithmetic on bigint (no floats until
// the final square roots). Exact-fit items are solved by trying every pair of
// steps (2x2 Cramer on the step equations themselves, then all other steps
// must agree), not through normal equations. Noisy fits use the exact rational
// normal equations and are cross-checked by residual orthogonality. Condition
// numbers use cond = (t + s)^2 / (4 det) with s = sqrt(t^2 - 4 det) (a form
// that avoids subtracting nearly equal eigenvalues). Choice fields: the
// conclusion is derived first, then the one matching option is selected.
type R = [bigint, bigint];
const gcd = (a: bigint, b: bigint): bigint => (b === 0n ? (a < 0n ? -a : a) : gcd(b, a % b));
const mk = (n: bigint, d: bigint): R => {
  if (d < 0n) { n = -n; d = -d; }
  const g = gcd(n, d) || 1n;
  return [n / g, d / g];
};
const add = (a: R, b: R) => mk(a[0] * b[1] + b[0] * a[1], a[1] * b[1]);
const sub = (a: R, b: R) => mk(a[0] * b[1] - b[0] * a[1], a[1] * b[1]);
const mul = (a: R, b: R) => mk(a[0] * b[0], a[1] * b[1]);
const div = (a: R, b: R) => mk(a[0] * b[1], a[1] * b[0]);
const sign = (a: R) => (a[0] < 0n ? -1 : a[0] > 0n ? 1 : 0);
const rat = (v: unknown): R => {
  const s = String(v).trim();
  if (s.includes("/")) {
    const [a, b] = s.split("/");
    return div(rat(a), rat(b));
  }
  const m = /^(-?)(\d*)(?:\.(\d+))?$/.exec(s);
  if (!m) throw new Error("bad number " + s);
  const frac = m[3] ?? "";
  return mk(BigInt((m[1] ?? "") + (m[2] || "0") + frac), 10n ** BigInt(frac.length));
};
const num = (a: R) => Number(a[0]) / Number(a[1]);
const Z = mk(0n, 1n);
const rats = (v: unknown) => (v as unknown[]).map(rat);
const sum = (xs: R[]) => xs.reduce((s, x) => add(s, x), Z);

type Gram = { syy: R; syu: R; suu: R; g0: R; g1: R; det: R };
function gram(y: R[], u: R[]): Gram {
  const idx = u.map((_, k) => k);
  const syy = sum(idx.map((k) => mul(y[k], y[k])));
  const syu = sum(idx.map((k) => mul(y[k], u[k])));
  const suu = sum(idx.map((k) => mul(u[k], u[k])));
  const g0 = sum(idx.map((k) => mul(y[k + 1], y[k])));
  const g1 = sum(idx.map((k) => mul(y[k + 1], u[k])));
  return { syy, syu, suu, g0, g1, det: sub(mul(syy, suu), mul(syu, syu)) };
}
function solve(G: Gram): [R, R] {
  expect(sign(G.det)).not.toBe(0);
  return [
    div(sub(mul(G.g0, G.suu), mul(G.syu, G.g1)), G.det),
    div(sub(mul(G.syy, G.g1), mul(G.syu, G.g0)), G.det),
  ];
}
function rmsOf(a: R, b: R, y: R[], u: R[]): number {
  const sq = sum(u.map((_, k) => {
    const r = sub(y[k + 1], add(mul(a, y[k]), mul(b, u[k])));
    return mul(r, r);
  }));
  return Math.sqrt(num(div(sq, mk(BigInt(u.length), 1n))));
}
// cond from the exact trace/det of a symmetric PSD 2x2 matrix.
function cond(p: R, q: R, r: R): number {
  const t = num(add(p, r));
  const det = sub(mul(p, r), mul(q, q));
  if (sign(det) === 0) return Infinity;
  const d = num(det);
  const s = Math.sqrt(t * t - 4 * d);
  return ((t + s) * (t + s)) / (4 * d);
}
function pick(options: string[], test: (o: string) => boolean): string {
  const hit = options.filter(test);
  expect(hit.length, "options matching the derived conclusion").toBe(1);
  return hit[0];
}
function statusWord(c: number): "Identifiable" | "Weak" | "Unidentifiable" {
  return c === Infinity ? "Unidentifiable" : c > 1e4 ? "Weak" : "Identifiable";
}
const fieldOptions = (item: Item, i: number) =>
  (item.fields[i] as { options?: string[] }).options as string[];

familyOracles["X38"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  switch (item.structure) {
    case "identification.fit-exact@1": {
      const y = rats(p.y), u = rats(p.u), n = u.length;
      let found: [R, R] | null = null;
      for (let i = 0; i < n && !found; i++) {
        for (let j = i + 1; j < n && !found; j++) {
          const det = sub(mul(y[i], u[j]), mul(y[j], u[i]));
          if (sign(det) === 0) continue;
          const a = div(sub(mul(y[i + 1], u[j]), mul(y[j + 1], u[i])), det);
          const b = div(sub(mul(y[i], y[j + 1]), mul(y[j], y[i + 1])), det);
          found = [a, b];
        }
      }
      expect(found).not.toBeNull();
      const [a, b] = found as [R, R];
      for (let k = 0; k < n; k++) {
        expect(add(mul(a, y[k]), mul(b, u[k]))).toEqual(y[k + 1]);
      }
      const next = add(mul(a, y[n]), mul(b, rat(p.u_next)));
      return [num(a), num(b), num(next)];
    }
    case "identification.fit-noisy@1": {
      const y = rats(p.y), u = rats(p.u);
      const G = gram(y, u);
      const [a, b] = solve(G);
      const res = u.map((_, k) => sub(y[k + 1], add(mul(a, y[k]), mul(b, u[k]))));
      expect(sum(res.map((r, k) => mul(r, y[k])))).toEqual(Z);
      expect(sum(res.map((r, k) => mul(r, u[k])))).toEqual(Z);
      return [num(a), num(b), rmsOf(a, b, y, u)];
    }
    case "identification.heldout-gap@1": {
      const yt = rats(p.y_train), ut = rats(p.u_train);
      const det = gram(yt, ut).det;
      const rms = rmsOf(rat(p.a), rat(p.b), rats(p.y_test), rats(p.u_test));
      // conclusion: singular training log + held-out rejection => cannot pin down
      const singular = sign(det) === 0;
      const rejected = rms > Number(p.tol);
      expect(singular && rejected).toBe(true);
      const choice = pick(fieldOptions(item, 2), (o) => /cannot pin/i.test(o));
      return [num(det), rms, choice];
    }
    case "identification.gram-status@1": {
      const G = gram(rats(p.y), rats(p.u));
      const c = cond(G.syy, G.syu, G.suu);
      const word = statusWord(c);
      const choice = pick(fieldOptions(item, 2), (o) => o.startsWith(word));
      return [num(G.det), c, choice];
    }
    case "identification.domain-randomization@1": {
      const uni = (r: unknown, d: R) => {
        const [lo, hi] = rats(r);
        return add(lo, mul(d, sub(hi, lo)));
      };
      const [da, db, ds] = rats(p.draws);
      const a = uni(p.a_range, da), b = uni(p.b_range, db);
      const [slo, shi] = rats(p.s_range).map(num);
      // log-uniform by exponent form exp(ln lo + d (ln hi - ln lo))
      const s = Math.exp(Math.log(slo) + num(ds) * (Math.log(shi) - Math.log(slo)));
      const [alo, ahi] = rats(p.a_range).map(num);
      const real = num(rat(p.a_real));
      expect(real > ahi || real < alo).toBe(true);
      const choice = pick(fieldOptions(item, 3), (o) => /^Nothing was sampled/.test(o));
      return [num(a), num(b), s, choice];
    }
    case "identification.new-log-gram@1": {
      const G1 = p.G1 as unknown[][], G2 = p.G2 as unknown[][];
      const e = (M: unknown[][]) => [rat(M[0][0]), rat(M[0][1]), rat(M[1][1])] as R[];
      const [p1, q1, r1] = e(G1), [p2, q2, r2] = e(G2);
      const c1 = cond(p1, q1, r1);
      const P = add(p1, p2), Q = add(q1, q2), Rr = add(r1, r2);
      const c12 = cond(P, Q, Rr);
      const det = sub(mul(P, Rr), mul(Q, Q));
      const stdB = num(rat(p.sigma)) * Math.sqrt(num(div(P, det)));
      const word = statusWord(c1);
      const choice = pick(fieldOptions(item, 0), (o) => o.startsWith(word));
      return [choice, c1, c12, stdB];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

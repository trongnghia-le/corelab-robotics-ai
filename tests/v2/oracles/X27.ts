import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle in information (weighted-least-squares) form. Updates are
// computed as P+ = (P-^-1 + H' R^-1 H)^-1 and x+ = P+ (P-^-1 x- + H' R^-1 z),
// never with gain/innovation formulas; the gain and NIS are then recovered from
// the covariance identity K = P+ H' R^-1. Prediction is plain matrix algebra.
type M = number[][];
const mul = (A: M, B: M): M =>
  A.map((r) => B[0].map((_, j) => r.reduce((s, a, k) => s + a * B[k][j], 0)));
const T = (A: M): M => A[0].map((_, j) => A.map((r) => r[j]));
const add = (A: M, B: M): M => A.map((r, i) => r.map((v, j) => v + B[i][j]));
const inv2 = (A: M): M => {
  const d = A[0][0] * A[1][1] - A[0][1] * A[1][0];
  return [
    [A[1][1] / d, -A[0][1] / d],
    [-A[1][0] / d, A[0][0] / d],
  ];
};
const num = (v: unknown) => {
  const [a, b = "1"] = String(v).split("/");
  return Number(a) / Number(b);
};
// Abramowitz-Stegun 7.1.26-free: erfc via continued-fraction-free series
function erfc(x: number): number {
  // erf by Taylor series (x < ~3), accurate to 1e-12
  let term = x, sum = x;
  for (let n = 1; n < 80; n++) {
    term *= -x * x / n;
    sum += term / (2 * n + 1);
  }
  return 1 - (2 / Math.sqrt(Math.PI)) * sum;
}
const qMat = (q: number, dt: number): M => [
  [q * dt ** 3 / 3, q * dt ** 2 / 2],
  [q * dt ** 2 / 2, q * dt],
];
const cvPredict = (x: M, P: M, dt: number, q: number): [M, M] => {
  const F: M = [[1, dt], [0, 1]];
  return [mul(F, x), add(mul(mul(F, P), T(F)), qMat(q, dt))];
};
// position-only information update
function cvInfoUpdate(x: M, P: M, r: number, z: number): [M, M] {
  const Y = add(inv2(P), [[1 / r, 0], [0, 0]]);
  const Pp = inv2(Y);
  const b = add(mul(inv2(P), x), [[z / r], [0]]);
  return [mul(Pp, b), Pp];
}

familyOracles["X27"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const n = (k: string) => num(p[k]);
  const pick = (idx: number, test: (o: string) => boolean) => {
    const m = (item.fields[idx].options ?? []).filter(test);
    expect(m).toHaveLength(1);
    return m[0];
  };
  switch (item.structure) {
    case "kalman.scalar-update@1": {
      const h = n("h"), r = n("r"), P = n("P"), x = n("x"), z = n("z");
      const Pp = 1 / (1 / P + (h * h) / r);
      const xp = Pp * (x / P + (h * z) / r);
      const K = Pp * h / r; // information-form gain
      return [z - h * x, h * P * h + r, K, xp, Pp];
    }
    case "kalman.scalar-fusion-sequence@1": {
      const x0 = n("x0"), p0 = n("p0"), z1 = n("z1"), r1 = n("r1"), z2 = n("z2"), r2 = n("r2");
      const Y1 = 1 / p0 + 1 / r1;
      const m1 = (x0 / p0 + z1 / r1) / Y1;
      const Y = Y1 + 1 / r2;
      const m = (x0 / p0 + z1 / r1 + z2 / r2) / Y;
      return [m1, 1 / Y1, m, 1 / Y, Y];
    }
    case "kalman.correlated-noise@1": {
      const r1 = n("r1"), r2 = n("r2"), rho = n("rho");
      const claimed = 1 / (1 / r1 + 1 / r2);
      const w = [claimed / r1, claimed / r2];
      const c = rho * Math.sqrt(r1 * r2);
      const S: M = [[r1, c], [c, r2]];
      const truth = mul(mul([w], S), T([w]))[0][0];
      const opt = pick(2, (o) =>
        // declared variances are stated true, so the only cause is the ignored
        // correlation: pick the plain "Too small:/Too large:" statement
        truth > claimed + 1e-9 ? /^Too small: /.test(o)
        : truth < claimed - 1e-9 ? /^Too large: /.test(o)
        : /^Exactly right/.test(o));
      return [claimed, truth, opt];
    }
    case "kalman.cv-predict@1": {
      const x: M = [[n("pos")], [n("vel")]];
      const P: M = [[n("p00"), 0], [0, n("p11")]];
      const [xp, Pp] = cvPredict(x, P, n("dt"), n("q"));
      return [xp[0][0], xp[1][0], Pp[0][0], Pp[0][1], Pp[1][1]];
    }
    case "kalman.cv-update@1": {
      const x: M = [[n("pos")], [n("vel")]];
      const P: M = [[n("p00"), n("p01")], [n("p01"), n("p11")]];
      const r = n("r");
      const [xp, Pp] = cvInfoUpdate(x, P, r, n("z"));
      const S = P[0][0] + r;
      // information-form gain K = P+ H' / R
      return [S, Pp[0][0] / r, Pp[1][0] / r, xp[0][0], xp[1][0], Pp[1][1]];
    }
    case "kalman.cv-replay@1": {
      let x: M = [[n("pos")], [n("vel")]];
      let P: M = [[n("p00"), 0], [0, n("p11")]];
      const r = n("r");
      const zs = p.zs as (string | null)[];
      let nis = NaN;
      zs.forEach((zv, i) => {
        [x, P] = cvPredict(x, P, n("dt"), n("q"));
        if (zv !== null) {
          const z = num(zv);
          if (i === zs.length - 1) nis = (z - x[0][0]) ** 2 / (P[0][0] + r);
          [x, P] = cvInfoUpdate(x, P, r, z);
        }
      });
      // exceedance rate of a chi-square(1) gate g is P(|N|>sqrt g) = erfc(sqrt(g/2))
      const g = Number((item.prompt.match(/gate of ([0-9.]+)/) ?? [])[1]);
      expect(g).toBeGreaterThan(0);
      const rate = erfc(Math.sqrt(g / 2)) * 100;
      const opt = pick(4, (o) => Math.abs(Number(/(\d+)%/.exec(o)?.[1]) - rate) < 0.5);
      return [x[0][0], x[1][0], P[0][0], nis, opt];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

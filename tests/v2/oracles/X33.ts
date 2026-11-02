import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X33 (ideal pinhole, extrinsics, two-line intrinsic
// fit, held-out evaluation). Everything is exact rational arithmetic on bigint.
// Differences from the usual route: the world<-camera step uses the explicit
// adjugate/determinant inverse of R (not the transpose), and the least-squares
// lines are solved from the 2x2 normal equations by Cramer's rule (not
// centred covariance formulas). Only the final RMS square root is a float.
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
  if (s.includes("/")) {
    const [a, b] = s.split("/");
    return div(rat(a), rat(b));
  }
  const m = /^(-?)(\d*)(?:\.(\d+))?$/.exec(s);
  if (!m) throw new Error("bad number " + s);
  const frac = m[3] ?? "";
  return mk(BigInt(m[1] + (m[2] || "0") + frac), 10n ** BigInt(frac.length));
};
const num = (a: Q) => {
  // exact enough: scale to a fixed-point integer before converting
  const scaled = (a[0] * 10n ** 18n) / a[1];
  return Number(scaled) / 1e18;
};
const Z0 = mk(0n, 1n);
const sum = (xs: Q[]) => xs.reduce(add, Z0);
type Mat = Q[][];
const matOf = (v: unknown): Mat => (v as unknown[][]).map((r) => r.map(rat));
const vecOf = (v: unknown): Q[] => (v as unknown[]).map(rat);

const det3 = (m: Mat): Q =>
  add(
    sub(
      mul(m[0][0], sub(mul(m[1][1], m[2][2]), mul(m[1][2], m[2][1]))),
      mul(m[0][1], sub(mul(m[1][0], m[2][2]), mul(m[1][2], m[2][0]))),
    ),
    mul(m[0][2], sub(mul(m[1][0], m[2][1]), mul(m[1][1], m[2][0]))),
  );
// Inverse by cofactors: inv[i][j] = cofactor(j, i) / det.
const inv3 = (m: Mat): Mat => {
  const d = det3(m);
  expect(sgn(d)).not.toBe(0);
  const minor = (r: number, c: number): Q => {
    const rows = [0, 1, 2].filter((x) => x !== r), cols = [0, 1, 2].filter((x) => x !== c);
    return sub(mul(m[rows[0]][cols[0]], m[rows[1]][cols[1]]), mul(m[rows[0]][cols[1]], m[rows[1]][cols[0]]));
  };
  return [0, 1, 2].map((i) =>
    [0, 1, 2].map((j) => {
      const cof = (i + j) % 2 === 0 ? minor(j, i) : mul(mk(-1n, 1n), minor(j, i));
      return div(cof, d);
    }),
  );
};
const apply = (m: Mat, v: Q[]): Q[] => m.map((row) => sum(row.map((a, j) => mul(a, v[j]))));

// Least squares line y = a*x + b from the normal equations, Cramer's rule.
const line = (xs: Q[], ys: Q[]): [Q, Q] => {
  const n = mk(BigInt(xs.length), 1n);
  const sx = sum(xs), sy = sum(ys);
  const sxx = sum(xs.map((x) => mul(x, x))), sxy = sum(xs.map((x, i) => mul(x, ys[i])));
  const D = sub(mul(n, sxx), mul(sx, sx));
  expect(sgn(D)).not.toBe(0);
  return [div(sub(mul(n, sxy), mul(sx, sy)), D), div(sub(mul(sxx, sy), mul(sx, sxy)), D)];
};
type K4 = { fx: Q; fy: Q; cx: Q; cy: Q };
const fit = (pts: Q[][], pix: Q[][]): K4 => {
  const xs = pts.map((p) => div(p[0], p[2])), ys = pts.map((p) => div(p[1], p[2]));
  const [fx, cx] = line(xs, pix.map((m) => m[0]));
  const [fy, cy] = line(ys, pix.map((m) => m[1]));
  return { fx, fy, cx, cy };
};
const projectQ = (K: K4, p: Q[]): [Q, Q] => {
  expect(sgn(p[2])).toBeGreaterThan(0);
  return [add(mul(K.fx, div(p[0], p[2])), K.cx), add(mul(K.fy, div(p[1], p[2])), K.cy)];
};
const rms = (K: K4, pts: Q[][], pix: Q[][]): number => {
  expect(pts.length).toBeGreaterThan(0);
  const total = sum(
    pts.map((p, i) => {
      const [u, v] = projectQ(K, p);
      const du = sub(u, pix[i][0]), dv = sub(v, pix[i][1]);
      return add(mul(du, du), mul(dv, dv));
    }),
  );
  return Math.sqrt(num(div(total, mk(BigInt(pts.length), 1n))));
};

familyOracles["X33"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const pick = (idx: number, test: (o: string) => boolean) => {
    const m = (item.fields[idx].options ?? []).filter(test);
    expect(m).toHaveLength(1);
    return m[0];
  };
  switch (item.structure) {
    case "camera.project-world@1": {
      const R = matOf(p.R), t = vecOf(p.t), K = vecOf(p.K), w = vecOf(p.p);
      const rw = apply(R, w);
      const c = rw.map((v, i) => add(v, t[i]));
      const [u, v] = projectQ({ fx: K[0], fy: K[1], cx: K[2], cy: K[3] }, c);
      return [num(c[2]), num(u), num(v)];
    }
    case "camera.pixel-to-world@1": {
      const R = matOf(p.R), t = vecOf(p.t), K = vecOf(p.K);
      const u = rat(p.u), v = rat(p.v), d = rat(p.depth);
      expect(sgn(d)).toBeGreaterThan(0);
      const cam = [mul(div(sub(u, K[2]), K[0]), d), mul(div(sub(v, K[3]), K[1]), d), d];
      // R must be a proper rotation for the declared model; use the explicit
      // inverse so a typo in R would show as a failed identity.
      expect(cmp(det3(R), mk(1n, 1n))).toBe(0);
      const w = apply(inv3(R), cam.map((x, i) => sub(x, t[i])));
      // forward check: R w + t returns the camera point
      const back = apply(R, w).map((x, i) => add(x, t[i]));
      back.forEach((x, i) => expect(cmp(x, cam[i])).toBe(0));
      return w.map(num);
    }
    case "camera.depth-validity@1": {
      const R = matOf(p.R), t = vecOf(p.t), K = vecOf(p.K), minD = rat(p.minimum_depth);
      const pts = (p.points as unknown[]).map(vecOf);
      expect(pts).toHaveLength(4);
      const cams = pts.map((w) => apply(R, w).map((x, i) => add(x, t[i])));
      const depth = cams.map((c) => c[2]);
      const ok = depth.map((z) => cmp(z, minD) >= 0);
      const [u, v] = projectQ({ fx: K[0], fy: K[1], cx: K[2], cy: K[3] }, cams[3]);
      expect(ok[3]).toBe(true);
      // B has no image (depth below the minimum): a routine must raise an error.
      expect(ok[1]).toBe(false);
      return [
        num(depth[1]),
        num(depth[2]),
        ok.filter(Boolean).length,
        num(u),
        num(v),
        pick(5, (o) => /^Raise an error/.test(o) && /no image/.test(o)),
      ];
    }
    case "camera.fit-u-line@1": {
      const X = vecOf(p.X), Z = vecOf(p.Z), u = vecOf(p.u);
      const xs = X.map((a, i) => div(a, Z[i]));
      const [fx, cx] = line(xs, u);
      return [num(fx), num(cx)];
    }
    case "camera.fit-intrinsics-rms@1": {
      const pts = (p.points as unknown[]).map(vecOf), pix = (p.pixels as unknown[]).map(vecOf);
      const K = fit(pts, pix);
      return [num(K.fx), num(K.fy), num(K.cx), num(K.cy), rms(K, pts, pix)];
    }
    case "camera.heldout-eval@1": {
      const pts = (p.points as unknown[]).map(vecOf), pix = (p.pixels as unknown[]).map(vecOf);
      const n = Number(p.n_train);
      expect(n).toBeGreaterThanOrEqual(2);
      expect(n).toBeLessThan(pts.length);
      const K = fit(pts.slice(0, n), pix.slice(0, n));
      const words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
      const trainW = words[n], testW = words[pts.length - n];
      return [
        num(K.fx),
        num(K.fy),
        rms(K, pts.slice(0, n), pix.slice(0, n)),
        rms(K, pts.slice(n), pix.slice(n)),
        // valid procedure: fit on the training views only, evaluate on the unseen ones
        pick(4, (o) =>
          o.startsWith("Fit on the " + trainW + " training points only, then evaluate on the " + testW) &&
          /unseen/.test(o),
        ),
      ];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

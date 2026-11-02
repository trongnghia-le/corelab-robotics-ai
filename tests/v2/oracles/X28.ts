import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X28 (grid A* costs and exact segment/rectangle tests).
// Grid costs: Bellman-Ford style relaxation to a fixed point (no priority
// queue, no heuristic). Geometry: exact rational "event" test - the segment is
// cut at every parameter where it meets a rectangle side line, and membership
// is constant between consecutive cut points, so testing the cut points and
// the midpoints between them decides contact exactly (no slab clipping).
const SQ2 = Math.SQRT2;

// ---- tiny exact rational arithmetic on bigint ----
type R = [bigint, bigint]; // numerator, denominator > 0
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
const cmp = (a: R, b: R) => {
  const x = a[0] * b[1] - b[0] * a[1];
  return x < 0n ? -1 : x > 0n ? 1 : 0;
};
const rat = (v: unknown): R => {
  const s = String(v).trim();
  if (s.includes("/")) {
    const [a, b] = s.split("/");
    return div(rat(a), rat(b));
  }
  const m = /^(-?)(\d*)(?:\.(\d+))?$/.exec(s);
  if (!m) throw new Error("bad number " + s);
  const frac = m[3] ?? "";
  const n = BigInt((m[1] ?? "") + (m[2] || "0") + frac);
  return mk(n, 10n ** BigInt(frac.length));
};
const num = (a: R) => Number(a[0]) / Number(a[1]);
const ZERO = mk(0n, 1n), ONE = mk(1n, 1n), HALF = mk(1n, 2n);

type Pt = [R, R];
type Rect = [R, R, R, R];
const inside = (p: Pt, r: Rect, strict: boolean) =>
  strict
    ? cmp(p[0], r[0]) > 0 && cmp(p[0], r[2]) < 0 && cmp(p[1], r[1]) > 0 && cmp(p[1], r[3]) < 0
    : cmp(p[0], r[0]) >= 0 && cmp(p[0], r[2]) <= 0 && cmp(p[1], r[1]) >= 0 && cmp(p[1], r[3]) <= 0;
const at = (p: Pt, q: Pt, t: R): Pt => [
  add(p[0], mul(t, sub(q[0], p[0]))),
  add(p[1], mul(t, sub(q[1], p[1]))),
];
function cuts(p: Pt, q: Pt, r: Rect): R[] {
  const ts: R[] = [ZERO, ONE];
  for (const [axis, lines] of [[0, [r[0], r[2]]], [1, [r[1], r[3]]]] as [number, R[]][]) {
    const d = sub(q[axis], p[axis]);
    if (d[0] === 0n) continue;
    for (const L of lines) {
      const t = div(sub(L, p[axis]), d);
      if (cmp(t, ZERO) > 0 && cmp(t, ONE) < 0) ts.push(t);
    }
  }
  ts.sort(cmp);
  return ts;
}
// contact of the closed segment with the closed (strict=false) or open (strict=true) rect
function meets(p: Pt, q: Pt, r: Rect, strict = false): boolean {
  const ts = cuts(p, q, r);
  for (let i = 0; i < ts.length; i++) {
    if (inside(at(p, q, ts[i]), r, strict)) return true;
    if (i + 1 < ts.length && inside(at(p, q, mul(add(ts[i], ts[i + 1]), HALF)), r, strict)) return true;
  }
  return false;
}
const pt = (v: unknown): Pt => {
  const a = v as unknown[];
  return [rat(a[0]), rat(a[1])];
};
const rc = (v: unknown): Rect => {
  const a = v as unknown[];
  return [rat(a[0]), rat(a[1]), rat(a[2]), rat(a[3])];
};
const grow = (r: Rect, h: R): Rect => [sub(r[0], h), sub(r[1], h), add(r[2], h), add(r[3], h)];

// ---- grid ----
function costs(rows: string[], start: [number, number], conn: number, cut: boolean) {
  const H = rows.length, W = rows[0].length;
  const free = (r: number, c: number) => r >= 0 && c >= 0 && r < H && c < W && rows[r][c] === ".";
  const dist = rows.map((row) => Array.from(row, () => Infinity));
  dist[start[0]][start[1]] = 0;
  for (let changed = true; changed; ) {
    changed = false;
    for (let r = 0; r < H; r++)
      for (let c = 0; c < W; c++) {
        if (!free(r, c) || dist[r][c] === Infinity) continue;
        for (let dr = -1; dr <= 1; dr++)
          for (let dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            const diag = dr !== 0 && dc !== 0;
            if (diag && conn === 4) continue;
            if (!free(r + dr, c + dc)) continue;
            if (diag && !cut && !(free(r + dr, c) && free(r, c + dc))) continue;
            const nd = dist[r][c] + (diag ? SQ2 : 1);
            if (nd < dist[r + dr][c + dc] - 1e-12) {
              dist[r + dr][c + dc] = nd;
              changed = true;
            }
          }
      }
  }
  return dist;
}
const octile = (a: number[], b: number[]) => {
  const dr = Math.abs(a[0] - b[0]), dc = Math.abs(a[1] - b[1]);
  return Math.max(dr, dc) + (SQ2 - 1) * Math.min(dr, dc);
};
const manhattan = (a: number[], b: number[]) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);

familyOracles["X28"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const pick = (idx: number, test: (o: string) => boolean) => {
    const m = (item.fields[idx].options ?? []).filter(test);
    expect(m).toHaveLength(1);
    return m[0];
  };
  switch (item.structure) {
    case "grid-astar.cost-heuristic@1": {
      const rows = p.grid as string[], s = p.start as [number, number], g = p.goal as [number, number];
      const d = costs(rows, s, Number(p.connectivity), false);
      const cost = d[g[0]][g[1]];
      const reachable = d.flat().filter((x) => x < Infinity).length;
      // a search stopped early with unexpanded reachable cells proves nothing
      expect(reachable).toBeGreaterThan(1);
      return [cost, manhattan(s, g), pick(2, (o) => /^Budget exhausted/.test(o) && /not shown that no path exists/.test(o))];
    }
    case "grid-astar.corner-rule@1": {
      const rows = p.grid as string[], s = p.start as [number, number], g = p.goal as [number, number];
      const conn = Number(p.connectivity);
      return [
        costs(rows, s, conn, false)[g[0]][g[1]],
        costs(rows, s, conn, true)[g[0]][g[1]],
        octile(s, g),
      ];
    }
    case "grid-astar.heuristic-weight@1": {
      const rows = p.grid as string[], s = p.start as [number, number], g = p.goal as [number, number];
      const conn = Number(p.connectivity), w = Number(p.weight);
      const cost = costs(rows, s, conn, false)[g[0]][g[1]];
      const man = manhattan(s, g);
      const over = man > cost + 1e-9; // Manhattan overestimates -> inadmissible
      expect(over).toBe(true);
      return [
        octile(s, g), man, cost, w * cost,
        pick(4, (o) => /^Manhattan can exceed the true 8-connected cost/.test(o) && /not optimal/.test(o)),
      ];
    }
    case "segment-rect.classify@1": {
      const r = rc(p.rect);
      let hits = 0, touches = 0, missed = 0;
      for (const sg of p.segments as unknown[][]) {
        const a = pt(sg[0]), b = pt(sg[1]);
        if (!meets(a, b, r)) continue;
        hits++;
        if (!meets(a, b, r, true)) touches++;
        if (!inside(a, r, false) && !inside(b, r, false)) missed++;
      }
      return [hits, touches, missed];
    }
    case "segment-rect.thin-wall@1": {
      const a = pt(p.p), b = pt(p.q), r = rc(p.rect);
      const ts = cuts(a, b, r);
      const inn: R[] = [];
      for (let i = 0; i < ts.length; i++) {
        if (inside(at(a, b, ts[i]), r, false)) inn.push(ts[i]);
        if (i + 1 < ts.length) {
          const m = mul(add(ts[i], ts[i + 1]), HALF);
          if (inside(at(a, b, m), r, false)) inn.push(ts[i], ts[i + 1]);
        }
      }
      inn.sort(cmp);
      expect(inn.length).toBeGreaterThan(0);
      // the wall is vertical (spans the segment's y) and the segment horizontal
      const length = Math.hypot(num(sub(b[0], a[0])), num(sub(b[1], a[1])));
      const width = num(sub(r[2], r[0]));
      let n = 2;
      while (length / (n - 1) > width + 1e-12) n++;
      let found = false;
      for (let i = 0; i <= 10; i++) found ||= inside(at(a, b, mk(BigInt(i), 10n)), r, false);
      expect(found).toBe(false);
      return [
        num(inn[0]), num(inn[inn.length - 1]), n,
        pick(3, (o) => /^No sample lands inside the wall/.test(o) && /clear shortcut/.test(o)),
      ];
    }
    case "path-sweep.critical@1": {
      const pts = (p.points as unknown[]).map(pt);
      const rs = (p.rects as unknown[]).map(rc);
      const blocked = (i: number, h: R) => rs.some((r) => meets(pts[i], pts[i + 1], grow(r, h)));
      const first = (h: R) => {
        for (let i = 0; i < pts.length - 1; i++) if (blocked(i, h)) return i;
        return -1;
      };
      // smallest blocking half-width: bisection on the (monotone) contact test
      let lo = 0, hi = 1000;
      const anyBlocked = (h: number) => {
        const hq = mk(BigInt(Math.round(h * 2 ** 40)), 2n ** 40n);
        return pts.slice(0, -1).some((_, i) => blocked(i, hq));
      };
      for (let i = 0; i < 38; i++) {
        const mid = (lo + hi) / 2;
        if (anyBlocked(mid)) hi = mid; else lo = mid;
      }
      const hs = (p.half_widths as unknown[]).map(rat);
      return [hi, ...hs.map(first)];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

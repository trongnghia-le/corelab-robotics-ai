import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X35 (two-pad Coulomb grasp, retention observer).
// Exact rationals on bigint parsed from the decimal input strings. Hold
// quantities are found by the demand/capacity balance written as a ratio
// (capacity per unit squeeze = 2*mu), not by the printed formulas; trace
// events come from a table-driven scanner that classifies every sample into
// (phase, in-contact, outside-cone) and derives the events from transitions
// between consecutive classes.
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
const cmp = (a: Q, b: Q) => { const d = sub(a, b)[0]; return d < 0n ? -1 : d > 0n ? 1 : 0; };
const abs = (a: Q): Q => (a[0] < 0n ? mk(-a[0], a[1]) : a);
const rat = (v: unknown): Q => {
  const s = String(v).trim();
  const m = /^(-?)(\d*)(?:\.(\d+))?$/.exec(s);
  if (!m) throw new Error("bad number " + s);
  const frac = m[3] ?? "";
  return mk(BigInt(m[1] + (m[2] || "0") + frac), 10n ** BigInt(frac.length));
};
const num = (a: Q) => Number((a[0] * 10n ** 18n) / a[1]) / 1e18;
const I = (n: number) => mk(BigInt(n), 1n);
const G = rat("9.81");
const TWO = I(2);

type Ev = [number, string];
function scan(rows: Q[][], mu: Q, thr: Q, window: number): Ev[] {
  // Class of a sample: open / closed. State is carried as a small record.
  const out: Ev[] = [];
  let inContact = false, slipped = false, touched = false, run = 0, prevOpen = false;
  rows.forEach((r, k) => {
    const open = cmp(r[0], I(1)) === 0;
    if (open) {
      if (!prevOpen && inContact) out.push([k, "release"]);
      inContact = false; slipped = false; touched = false; run = 0; prevOpen = true;
      return;
    }
    prevOpen = false;
    run += 1;
    const strong = cmp(r[1], thr) >= 0;
    const outside = cmp(abs(r[2]), mul(mu, r[1])) > 0;
    if (!inContact && strong) { out.push([k, "contact"]); inContact = true; touched = true; }
    else if (inContact && !strong) { out.push([k, "lost"]); inContact = false; slipped = false; }
    else if (inContact) { /* held on: fall through to the slip rule below */ }
    if (inContact && !(out.length && out[out.length - 1][1] === "lost" && out[out.length - 1][0] === k)) {
      if (outside && !slipped) out.push([k, "slip"]);
      slipped = outside;
    }
    if (!inContact && !touched && run === window) out.push([k, "empty"]);
  });
  return out;
}

familyOracles["X35"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const q = (key: string) => rat(p[key]);
  // Smallest N per pad for mass m, lift a, friction mu: capacity 2*mu*N must
  // reach the weight demand m*(g+a); N = demand / (2 mu).
  const needN = (m: Q, a: Q, mu: Q) => div(mul(m, add(G, a)), mul(TWO, mu));
  switch (item.structure) {
    case "parallel-jaw.min-squeeze@1": {
      const demand = mul(q("m"), add(G, q("a")));
      const perPad = div(demand, TWO);
      const n = needN(q("m"), q("a"), q("mu"));
      expect(cmp(mul(mul(TWO, q("mu")), n), demand)).toBe(0);
      return [num(perPad), num(n)];
    }
    case "parallel-jaw.hold-limits@1": {
      const cap = mul(mul(TWO, q("mu")), q("n"));
      const demand = mul(q("m"), add(G, q("a")));
      const aMax = sub(div(cap, q("m")), G);
      expect(cmp(mul(q("m"), add(G, aMax)), cap)).toBe(0);
      return [num(div(cap, demand)), num(aMax)];
    }
    case "parallel-jaw.mass-squeeze@1": {
      const cap = mul(mul(TWO, q("mu")), q("n"));
      const mMax = div(cap, add(G, q("a")));
      const mNew = div(q("m_new_g"), I(1000));
      return [num(mMax), num(needN(mNew, q("a"), q("mu")))];
    }
    case "parallel-jaw.cone-check@1": {
      const capacity = mul(q("mu"), q("fn"));
      return [num(capacity), num(div(q("ft"), q("fn"))), num(sub(q("ft"), capacity))];
    }
    case "parallel-jaw.trace-events@1": {
      const rows = (p.samples as unknown[][]).map((r) => r.map(rat));
      const ev = scan(rows, q("mu"), q("contact"), Number(p.window));
      const first = (name: string) => {
        const hit = ev.filter((e) => e[1] === name);
        expect(hit.length).toBeGreaterThan(0);
        return hit[0][0];
      };
      return [first("contact"), first("slip"), first("release")];
    }
    case "parallel-jaw.trace-diagnosis@1": {
      const rows = (p.samples as unknown[][]).map((r) => r.map(rat));
      const ev = scan(rows, q("mu"), q("contact"), Number(p.window));
      const slip = ev.filter((e) => e[1] === "slip")[0][0];
      // hold phase = last closed in-cone loaded sample before the first slip
      const hold = rows[slip - 1][2];
      const mass = div(mul(TWO, hold), G);
      return [slip, num(mass), num(needN(mass, q("a_lift"), q("mu"))), num(needN(mass, q("a_lift"), q("mu_wet")))];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

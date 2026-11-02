import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X37 (tabular Q/SARSA updates, seed statistics,
// reward-loophole check). Different routes from the kit/solutions:
//  - TD target: sort next values descending and take the head; update written
//    as a convex blend (1 - alpha) * q + alpha * target.
//  - epsilon-greedy: two-stage mixture, P(a) = eps * P(uniform = a) +
//    (1 - eps) * P(uniform over the argmax set = a), built by enumeration.
//  - sample std from the pairwise form sum_{i<j}(x_i - x_j)^2 / (n (n - 1)),
//    not from deviations about the mean.
//  - loophole: explicit enumeration of every action sequence of the stated
//    length (goal vs never-terminal), with the time limit and the bonus swept
//    over a grid by rebuilding the tables, rather than closed forms.
const N = (v: unknown): number => {
  const x = Number(v);
  if (!Number.isFinite(x)) throw new Error("bad number " + String(v));
  return x;
};
const NS = (v: unknown): number[] => (v as unknown[]).map(N);
const pick = <T>(xs: T[]): T => {
  expect(xs.length).toBe(1);
  return xs[0];
};

function blend(q: number, target: number, alpha: number): number {
  return (1 - alpha) * q + alpha * target;
}
function descMax(xs: number[]): number {
  return [...xs].sort((a, b) => b - a)[0];
}
function mixtureProbs(q: number[], eps: number): number[] {
  const n = q.length;
  const top = descMax(q);
  const ties = q.map((v, i) => (v === top ? i : -1)).filter((i) => i >= 0);
  return q.map((_, a) => {
    let p = 0;
    // exploring branch: uniform over all n actions
    for (let b = 0; b < n; b++) if (b === a) p += eps / n;
    // greedy branch: uniform over the argmax set
    for (const b of ties) if (b === a) p += (1 - eps) / ties.length;
    return p;
  });
}

type Tables = { ns: number[][]; rw: number[][]; term: boolean[] };
function enumerate(t: Tables, start: number, steps: number) {
  let goal: number | null = null;
  let farm: number | null = null;
  const m = t.ns[0].length;
  const total = m ** steps;
  for (let code = 0; code < total; code++) {
    let c = code, s = start, sum = 0, ended = false;
    for (let k = 0; k < steps; k++) {
      const a = c % m;
      c = Math.floor(c / m);
      sum += t.rw[s][a];
      s = t.ns[s][a];
      if (t.term[s]) { ended = true; break; }
    }
    if (ended) goal = goal === null || sum > goal ? sum : goal;
    else farm = farm === null || sum > farm ? sum : farm;
  }
  return { goal, farm };
}
const loophole = (g: number | null, f: number | null): boolean =>
  f !== null && g !== null && f > g;

familyOracles["X37"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  switch (item.structure) {
    case "rl.tabular-q-step@1": {
      const q = N(p.q), r = N(p.reward), alpha = N(p.alpha), gamma = N(p.gamma);
      const nxt = NS(p.qNext);
      expect(p.terminated).toBe(false);
      const target = r + gamma * descMax(nxt);
      return [target, blend(q, target, alpha)];
    }
    case "rl.q-learning-vs-sarsa@1": {
      const q = N(p.q), r = N(p.reward), alpha = N(p.alpha), gamma = N(p.gamma);
      const eps = N(p.epsilon), nxt = NS(p.qNext), a = N(p.aNext);
      expect(p.terminated).toBe(false);
      const tq = r + gamma * descMax(nxt);
      const ts = r + gamma * nxt[a];
      // the prompt asks for the probability of action 1 (the first tied max)
      const probs = mixtureProbs(nxt, eps);
      expect(probs.reduce((x, y) => x + y, 0)).toBeCloseTo(1, 12);
      return [tq, ts, blend(q, ts, alpha), probs[1]];
    }
    case "rl.update-trace@1": {
      const table = (p.q as unknown[]).map(NS);
      const alpha = N(p.alpha), gamma = N(p.gamma);
      const tr = p.transitions as unknown[][];
      const step = (tab: number[][], t: unknown[], forceTerminal: boolean) => {
        const [s, a, r, s2] = [N(t[0]), N(t[1]), N(t[2]), N(t[3])];
        const terminated = (t[4] as boolean) || forceTerminal;
        const target = terminated ? r : r + gamma * descMax(tab[s2]);
        const out = tab.map((row) => [...row]);
        out[s][a] = blend(tab[s][a], target, alpha);
        return out;
      };
      let cur = table;
      const snaps: number[][][] = [];
      for (const t of tr) {
        cur = step(cur, t, false);
        snaps.push(cur);
      }
      // (d): replay T3 as a true terminal, from the table after T2
      const alt = step(snaps[1], tr[2], true);
      const [t1, t2, t3] = [tr[0], tr[1], tr[2]];
      return [
        snaps[0][N(t1[0])][N(t1[1])],
        snaps[1][N(t2[0])][N(t2[1])],
        snaps[2][N(t3[0])][N(t3[1])],
        alt[N(t3[0])][N(t3[1])],
      ];
    }
    case "rl.seed-statistics@1": {
      const x = NS(p.returns), n = x.length;
      expect(NS(p.seeds).length).toBe(n);
      expect(new Set(NS(p.seeds)).size).toBe(n);
      const mean = x.reduce((a, b) => a + b, 0) / n;
      let pair = 0;
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) pair += (x[i] - x[j]) ** 2;
      const sd = Math.sqrt(pair / (n * (n - 1)));
      return [mean, sd, sd / Math.sqrt(n), Math.max(...x) - mean];
    }
    case "rl.method-comparison@1": {
      const a = NS(p.returnsA), b = NS(p.returnsB), n = a.length;
      expect(b.length).toBe(n);
      const mean = (x: number[]) => x.reduce((s, v) => s + v, 0) / n;
      let pair = 0;
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) pair += (a[i] - a[j]) ** 2;
      const sdA = Math.sqrt(pair / (n * (n - 1)));
      const wins = a.filter((v, i) => v > b[i]).length;
      return [mean(a), mean(b), sdA, wins, Math.max(...a) - Math.max(...b)];
    }
    case "rl.reward-loophole-check@1": {
      const ns = (p.nextState as unknown[]).map(NS);
      const rw = (p.reward as unknown[]).map(NS);
      const term = p.terminal as boolean[];
      const start = N(p.start), H = N(p.horizon);
      const base: Tables = { ns, rw, term };
      const full = enumerate(base, start, H);
      // (a)/(b): best docking vs best never-docking return at the stated limit
      expect(full.goal).not.toBeNull();
      // (c): sweep the time limit upward until farming strictly wins
      let minH = -1;
      for (let h = 1; h <= 14; h++) {
        const e = enumerate(base, start, h);
        if (loophole(e.goal, e.farm)) { minH = h; break; }
      }
      expect(minH).toBeGreaterThan(0);
      // (d): the bonus is the positive self-loop reward on a non-terminal,
      // non-start state; sweep it on a 0.25 grid and keep the largest value
      // below which no loophole appears at the stated horizon.
      const bonuses: [number, number][] = [];
      ns.forEach((row, s) =>
        row.forEach((to, a) => {
          if (to === s && !term[s] && s !== start && rw[s][a] > 0) bonuses.push([s, a]);
        }),
      );
      const [bs, ba] = pick(bonuses);
      let bestB = 0;
      for (let k = 0; k <= 80; k++) {
        const b = k * 0.25;
        const rw2 = rw.map((row) => [...row]);
        rw2[bs][ba] = b;
        const e = enumerate({ ns, rw: rw2, term }, start, H);
        if (loophole(e.goal, e.farm)) break;
        bestB = b;
      }
      return [full.goal as number, full.farm as number, minH, bestB];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

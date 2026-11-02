import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle. Localization is done by brute force over complete
// trajectories (start cell, displacement at every step), weighting each path
// by prior x sensor likelihoods x motion probabilities and normalising only
// once at the end. Systematic resampling is done with exact BigInt arithmetic
// by counting, for each particle, the sample positions that fall in its
// half-open cumulative interval [prev, cum).
const num = (v: unknown) => {
  const [a, b = "1"] = String(v).split("/");
  return Number(a) / Number(b);
};
const nums = (v: unknown) => (v as unknown[]).map(num);

function pathPosterior(
  belief: number[], world: number[], pc: number, kernel: number[],
  off: number, cyclic: boolean, obs: number[], moveAfterLast: boolean,
): number[] {
  const n = belief.length;
  const out = new Array(n).fill(0);
  const land = (c: number) =>
    cyclic ? (((c % n) + n) % n) : Math.min(n - 1, Math.max(0, c));
  const walk = (t: number, cell: number, w: number) => {
    if (w === 0) return;
    if (t === obs.length) { out[cell] += w; return; }
    const like = world[cell] === obs[t] ? pc : 1 - pc;
    const last = t === obs.length - 1;
    if (last && !moveAfterLast) { walk(t + 1, cell, w * like); return; }
    kernel.forEach((pk, k) => walk(t + 1, land(cell + off + k), w * like * pk));
  };
  belief.forEach((b, c) => walk(0, c, b));
  const total = out.reduce((s, x) => s + x, 0);
  expect(total).toBeGreaterThan(0);
  return out.map((x) => x / total);
}

const decimals = (s: string) => (s.includes(".") ? s.split(".")[1].length : 0);

familyOracles["X26"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const idxOf = (label: string, word: string) => {
    const m = new RegExp(word + " (\\d+)").exec(label);
    expect(m).not.toBeNull();
    return Number(m![1]);
  };
  switch (item.structure) {
    case "grid-bayes.update@1": {
      const belief = nums(p.belief), world = nums(p.world);
      const z = num(p.z), pc = num(p.p_correct);
      // one observation, no move after it
      const post = pathPosterior(belief, world, pc, [1], 0, false, [z], false);
      return item.fields.map((f) =>
        /door cell/i.test(f.label)
          ? world.reduce((s, w, i) => s + (w === 1 ? post[i] : 0), 0)
          : post[idxOf(f.label, "cell")],
      );
    }
    case "grid-bayes.predict@1": {
      const belief = nums(p.belief), kernel = nums(p.kernel);
      const off = num(p.offset0), cyc = p.motion === "cyclic";
      expect(["cyclic", "walls"]).toContain(p.motion);
      const n = belief.length;
      const out = new Array(n).fill(0);
      for (let target = 0; target < n; target++) {
        // all (start, k) pairs whose landing cell is `target`
        for (let i = 0; i < n; i++)
          for (let k = 0; k < kernel.length; k++) {
            const raw = i + off + k;
            const hit = cyc
              ? (((raw % n) + n) % n) === target
              : (target === 0 ? raw <= 0 : target === n - 1 ? raw >= n - 1 : raw === target);
            if (hit) out[target] += belief[i] * kernel[k];
          }
      }
      return item.fields.map((f) => out[idxOf(f.label, "cell")]);
    }
    case "grid-bayes.cycle@1": {
      const belief = nums(p.belief), world = nums(p.world);
      const post = pathPosterior(
        belief, world, num(p.p_correct), nums(p.kernel), num(p.offset0),
        p.motion === "cyclic", nums(p.observations), true,
      );
      const top = Math.max(...post);
      return item.fields.map((f) =>
        /tied|number of cells/i.test(f.label)
          ? post.filter((x) => x >= top - 1e-9).length
          : post[idxOf(f.label, "cell")],
      );
    }
    case "particles.ess@1": {
      const w = nums(p.weights);
      const total = w.reduce((s, x) => s + x, 0);
      const ess = (total * total) / w.reduce((s, x) => s + x * x, 0);
      return item.fields.map((f) =>
        /heaviest/i.test(f.label) ? Math.max(...w) / total
          : /ESS \//.test(f.label) ? ess / w.length : ess,
      );
    }
    case "particles.reweight@1": {
      const cells = nums(p.cells), w = nums(p.weights), world = nums(p.world);
      const z = num(p.z), pc = num(p.p_correct);
      const raw = w.map((x, k) => x * (world[cells[k]] === z ? pc : 1 - pc));
      const total = raw.reduce((s, x) => s + x, 0);
      const nw = raw.map((x) => x / total);
      const ess = 1 / nw.reduce((s, x) => s + x * x, 0);
      return item.fields.map((f) =>
        /ESS/.test(f.label) ? ess : nw[idxOf(f.label, "particle")],
      );
    }
    case "particles.systematic-resample@1": {
      const ws = (p.weights as unknown[]).map(String), us = String(p.u0);
      const N = ws.length;
      const m = Math.max(decimals(us), ...ws.map(decimals));
      const scale = 10n ** BigInt(m);
      const toInt = (s: string) => {
        const [a, b = ""] = s.split(".");
        return BigInt(a + b.padEnd(m, "0"));
      };
      const W = ws.map(toInt), U = toInt(us);
      const T = W.reduce((s, x) => s + x, 0n);
      const copies = new Array(N).fill(0);
      let prev = 0n;
      W.forEach((w, i) => {
        const cum = prev + w;
        for (let k = 0; k < N; k++) {
          // prev/T <= (U + k*scale)/(scale*N) < cum/T
          const lhs = T * (U + BigInt(k) * scale);
          if (prev * scale * BigInt(N) <= lhs && lhs < cum * scale * BigInt(N))
            copies[i]++;
        }
        prev = cum;
      });
      expect(copies.reduce((s, x) => s + x, 0)).toBe(N);
      return item.fields.map((f) => copies[idxOf(f.label, "particle")]);
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

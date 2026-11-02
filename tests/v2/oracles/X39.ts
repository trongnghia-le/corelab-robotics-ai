import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X39 (belief update and conditional-plan counterexamples
// on the box-fetch toy). Worlds are enumerated from the stated rules (key in
// exactly one box, optional lock state); the action table is re-implemented
// from the prompt text; a plan tree is interpreted by a small recursive
// function that returns a trace (failure reason, failing action, looks
// executed). Probabilities are exact rationals reduced only at the end.
// Choice fields: the conclusion is derived first, then the one matching option
// is selected (exactly one must match).
type Spec = { pre: string[]; add: string[]; del: string[]; sense?: string };
type Plan = unknown[];
type World = { facts: Set<string>; key: string; unlocked: boolean | null };
type Trace = { ok: boolean; reason: "precondition" | "goal" | null; failing: string | null; looks: number };

function domain(boxes: string[], lockable: string | undefined): Record<string, Spec> {
  const t: Record<string, Spec> = {};
  t["goto_home"] = { pre: [], add: ["at(home)"], del: boxes.map((b) => `at(${b})`) };
  t["deliver"] = { pre: ["at(home)", "holding(key)"], add: ["delivered(key)"], del: ["holding(key)"] };
  for (const b of boxes) {
    t[`goto_${b}`] = { pre: [], add: [`at(${b})`], del: ["at(home)", ...boxes.filter((o) => o !== b).map((o) => `at(${o})`)] };
    t[`open_${b}`] = {
      pre: [`at(${b})`, `closed(${b})`, ...(b === lockable ? [`unlocked(${b})`] : [])],
      add: [`open(${b})`],
      del: [`closed(${b})`],
    };
    t[`look_${b}`] = { pre: [`at(${b})`, `open(${b})`], add: [], del: [], sense: `in(key,${b})` };
    t[`grab_${b}`] = { pre: [`at(${b})`, `open(${b})`, `in(key,${b})`], add: ["holding(key)"], del: [`in(key,${b})`] };
  }
  return t;
}

function worlds(boxes: string[], lockable: string | undefined): World[] {
  const out: World[] = [];
  for (const k of boxes) {
    const states: (boolean | null)[] = lockable ? [true, false] : [null];
    for (const u of states) {
      const facts = new Set<string>(["at(home)", `in(key,${k})`, ...boxes.map((b) => `closed(${b})`)]);
      if (u === true && lockable) facts.add(`unlocked(${lockable})`);
      out.push({ facts, key: k, unlocked: u });
    }
  }
  return out;
}

function run(w: World, plan: Plan, table: Record<string, Spec>, goal: string[]): Trace {
  const f = new Set(w.facts);
  let node = plan;
  let looks = 0;
  for (let guard = 0; guard < 200; guard++) {
    const kind = node[0] as string;
    if (kind === "stop") {
      const ok = goal.every((g) => f.has(g));
      return { ok, reason: ok ? null : "goal", failing: null, looks };
    }
    const name = node[1] as string;
    const s = table[name];
    expect(s, "unknown action " + name).toBeDefined();
    if (!s.pre.every((p) => f.has(p))) return { ok: false, reason: "precondition", failing: name, looks };
    if (kind === "do") {
      s.del.forEach((d) => f.delete(d));
      s.add.forEach((a) => f.add(a));
      node = node[2] as Plan;
    } else {
      looks++;
      node = (f.has(s.sense as string) ? node[2] : node[3]) as Plan;
    }
  }
  throw new Error("plan did not terminate");
}

function usedActions(plan: Plan, acc: string[] = []): string[] {
  if (plan[0] === "stop") return acc;
  acc.push(plan[1] as string);
  for (const child of plan.slice(2)) usedActions(child as Plan, acc);
  return acc;
}

function objectsOf(fact: string): string[] {
  const m = /^[a-z_0-9]+\((.*)\)$/.exec(fact);
  expect(m).not.toBeNull();
  return (m as RegExpExecArray)[1].split(",");
}

function removeAction(plan: Plan, name: string): Plan {
  if (plan[0] === "stop") return plan;
  if (plan[0] === "do" && plan[1] === name) return removeAction(plan[2] as Plan, name);
  return [plan[0], plan[1], ...plan.slice(2).map((c) => removeAction(c as Plan, name))];
}

const pick = (options: string[], conclusion: string): string => {
  const hits = options.filter((o) => o === conclusion);
  expect(hits.length, "options matching " + conclusion).toBe(1);
  return hits[0];
};
const nums = (xs: unknown): number[] => (xs as string[]).map((x) => Number(x));

familyOracles["X39"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const locs = p.locations as string[];
  switch (item.structure) {
    case "belief.observation-filter@1": {
      const obs = p.observations as string[][];
      let alive = [...locs];
      const counts = [alive.length];
      for (const [loc, what] of obs) {
        expect(what).toBe("empty");
        alive = alive.filter((l) => l !== loc);
        counts.push(alive.length);
      }
      const m = /probability that the key is in the (\w+) after both looks/.exec(item.prompt);
      expect(m).not.toBeNull();
      const target = (m as RegExpExecArray)[1];
      expect(alive).toContain(target);
      return [counts[0], counts[1], counts[2], 1 / alive.length];
    }
    case "belief.weighted-posterior@1": {
      const w = nums(p.weights);
      const obs = p.observations as string[][];
      const stage = (k: number): Map<string, number> => {
        const m = new Map<string, number>();
        locs.forEach((l, i) => m.set(l, w[i]));
        for (const [loc] of obs.slice(0, k)) m.delete(loc);
        return m;
      };
      const prob = (k: number, loc: string) => {
        const m = stage(k);
        let t = 0;
        m.forEach((v) => (t += v));
        return (m.get(loc) as number) / t;
      };
      return item.fields.map((fl) => {
        // The asked place is the first place named in the label.
        const lab = fl.label.toLowerCase();
        const loc = locs
          .filter((l) => lab.includes(l))
          .sort((a, b) => lab.indexOf(a) - lab.indexOf(b))[0];
        expect(loc, fl.label).toBeDefined();
        const k = /prior/i.test(fl.label) ? 0 : /both/i.test(fl.label) ? 2 : 1;
        return prob(k, loc as string);
      });
    }
    case "belief.two-factor-update@1": {
      const lockable = p.lockable as string;
      const obs = p.observations as string[][];
      // (key box, lid unlocked?) pairs minus the impossible (lockable box, locked).
      let ws = worlds(locs, lockable).filter((w) => !(w.key === lockable && w.unlocked === false));
      const sizes = [ws.length];
      let probBin = NaN;
      for (const o of obs) {
        if (o[0] === "look") {
          ws = ws.filter((w) => w.key !== o[1]);
          probBin = ws.filter((w) => w.key === lockable).length / ws.length;
        } else if (o[0] === "lid") {
          expect(o[2]).toBe("unlocked");
          ws = ws.filter((w) => w.unlocked === true);
        } else throw new Error("unknown observation");
        sizes.push(ws.length);
      }
      return [sizes[0], sizes[1], probBin, sizes[2]];
    }
    case "plan.blind-fetch@1": {
      const wt = nums(p.weights);
      const table = domain(locs, undefined);
      const ws = worlds(locs, undefined);
      const tr = ws.map((w) => run(w, p.plan as Plan, table, ["delivered(key)"]));
      const okW = tr.reduce((s, t, i) => s + (t.ok ? wt[i] : 0), 0);
      const total = wt.reduce((a, b) => a + b, 0);
      const bad = tr.filter((t) => !t.ok);
      expect(bad.length).toBeGreaterThan(0);
      // The first failing action must be the same in every counterexample world.
      const failing = new Set(bad.map((t) => t.failing));
      expect(failing.size).toBe(1);
      expect(bad.every((t) => t.reason === "precondition")).toBe(true);
      const f = item.fields[3];
      return [tr.filter((t) => t.ok).length, bad.length, okW / total, pick(f.options as string[], [...failing][0] as string)];
    }
    case "plan.sensing-search@1": {
      const wt = nums(p.weights);
      const table = domain(locs, undefined);
      const ws = worlds(locs, undefined);
      const tr = ws.map((w) => run(w, p.plan as Plan, table, ["delivered(key)"]));
      const okW = tr.reduce((s, t, i) => s + (t.ok ? wt[i] : 0), 0);
      const total = wt.reduce((a, b) => a + b, 0);
      const badIdx = tr.map((t, i) => (t.ok ? -1 : i)).filter((i) => i >= 0);
      expect(badIdx.length).toBe(1);
      const f = item.fields[2];
      return [badIdx.length, okW / total, pick(f.options as string[], ws[badIdx[0]].key), tr[badIdx[0]].looks];
    }
    case "plan.ungrounded-counterexample@1": {
      const lockable = p.lockable as string;
      const wt = nums(p.weights);
      const extra = p.extra_actions as Record<string, Spec>;
      const table: Record<string, Spec> = { ...domain(locs, lockable) };
      for (const [k, v] of Object.entries(extra)) table[k] = { pre: v.pre, add: v.add, del: v.del };
      const ws = worlds(locs, lockable);
      expect(ws.length).toBe(wt.length);
      wt.forEach((w) => expect(item.prompt).toContain(`(weight ${w})`));
      const plan = p.plan as Plan;
      const repaired = p.repaired_plan as Plan;
      expect(JSON.stringify(removeAction(plan, "wipe_with_cloth"))).toBe(JSON.stringify(repaired));
      const known = new Set<string>();
      ws.forEach((w) => w.facts.forEach((f) => objectsOf(f).forEach((o) => known.add(o))));
      const missing = new Set<string>();
      for (const name of new Set(usedActions(plan))) {
        const s = table[name];
        [...s.pre, ...s.add, ...s.del, ...(s.sense ? [s.sense] : [])].forEach((f) =>
          objectsOf(f).forEach((o) => {
            if (!known.has(o)) missing.add(o);
          }),
        );
      }
      const total = wt.reduce((a, b) => a + b, 0);
      const score = (pl: Plan) => {
        const tr = ws.map((w) => run(w, pl, table, ["delivered(key)"]));
        return [tr.filter((t) => !t.ok).length, tr.reduce((s, t, i) => s + (t.ok ? wt[i] : 0), 0) / total];
      };
      const [bw, pw] = score(plan);
      const [br, pr] = score(repaired);
      return [missing.size, bw, pw, br, pr];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

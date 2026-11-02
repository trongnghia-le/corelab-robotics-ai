import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X32 (mock executive with watchdog). Built from the
// prompt text as a data-driven rule list: each rule is (matcher, effect) and a
// step takes the FIRST matching rule, in the stated priority order. Traces are
// replayed by recomputing the observation age from the whole event prefix, and
// the trace monitor derives its latches by scanning index positions of the
// latest obs/fault/reset/cancel/start in the prefix (no running state).
const ACTIVE = ["APPROACH", "GRASP", "TRANSPORT", "RELEASE"];
const ENTRY: Record<string, string> = {
  APPROACH: "move_pick",
  GRASP: "close_gripper",
  TRANSPORT: "move_drop",
  RELEASE: "open_gripper",
};
const MOTION = Object.values(ENTRY);
type Ctx = { s: string; e: string; stale: boolean; r: number; mr: number };
type Out = { s: string; c: string[]; r: number };
type Rule = { when: (x: Ctx) => boolean; out: (x: Ctx) => Out };
const holdOf = (s: string) => (s.startsWith("HOLD_") ? s.slice(5) : null);
const keep = (x: Ctx): Out => ({ s: x.s, c: [], r: x.r });

const RULES: Rule[] = [
  // 1. fault
  {
    when: (x) => x.e === "fault" && x.s !== "FAULT",
    out: (x) => ({ s: "FAULT", c: ACTIVE.includes(x.s) ? ["stop"] : [], r: x.r }),
  },
  // 2. cancel
  {
    when: (x) => x.e === "cancel" && (ACTIVE.includes(x.s) || holdOf(x.s) !== null),
    out: (x) => ({ s: "IDLE", c: ACTIVE.includes(x.s) ? ["stop"] : [], r: 0 }),
  },
  // 3. watchdog (any event name, active phase only)
  {
    when: (x) => ACTIVE.includes(x.s) && x.stale,
    out: (x) => ({ s: "HOLD_" + x.s, c: ["stop"], r: x.r }),
  },
  // 4. table
  {
    when: (x) => x.s === "IDLE" && x.e === "start" && !x.stale,
    out: (x) => ({ s: "APPROACH", c: ["move_pick"], r: x.r }),
  },
  {
    when: (x) => x.s === "APPROACH" && x.e === "reached",
    out: (x) => ({ s: "GRASP", c: ["close_gripper"], r: x.r }),
  },
  {
    when: (x) => x.s === "GRASP" && x.e === "grasped",
    out: (x) => ({ s: "TRANSPORT", c: ["move_drop"], r: x.r }),
  },
  {
    when: (x) => x.s === "GRASP" && x.e === "grasp_failed" && x.r < x.mr,
    out: (x) => ({ s: "APPROACH", c: ["move_pick"], r: x.r + 1 }),
  },
  {
    when: (x) => x.s === "GRASP" && x.e === "grasp_failed",
    out: (x) => ({ s: "FAULT", c: ["stop"], r: x.r }),
  },
  {
    when: (x) => x.s === "TRANSPORT" && x.e === "reached",
    out: (x) => ({ s: "RELEASE", c: ["open_gripper"], r: x.r }),
  },
  {
    when: (x) => x.s === "RELEASE" && x.e === "released",
    out: (x) => ({ s: "DONE", c: [], r: x.r }),
  },
  {
    when: (x) => holdOf(x.s) !== null && x.e === "resume" && !x.stale && x.r < x.mr,
    out: (x) => {
      const ph = holdOf(x.s) as string;
      return { s: ph, c: [ENTRY[ph]], r: x.r + 1 };
    },
  },
  {
    when: (x) => (x.s === "FAULT" || x.s === "DONE") && x.e === "reset",
    out: (x) => ({ s: "IDLE", c: [], r: x.r }),
  },
];

function step(s: string, e: string, age: number | null, r: number, ma: number, mr: number): Out {
  const x: Ctx = { s, e, stale: age === null || age > ma, r, mr };
  const hit = RULES.find((rule) => rule.when(x));
  return hit ? hit.out(x) : keep(x);
}

type Ev = [number, string];
const parseEvents = (v: unknown): Ev[] =>
  (v as unknown[][]).map((p) => [Number(p[0]), String(p[1])] as Ev);

function replay(events: Ev[], ma: number, mr: number) {
  const states: string[] = [];
  const cmds: string[][] = [];
  let s = "IDLE";
  let r = 0;
  events.forEach(([t, e], i) => {
    let lastObs = -1;
    for (let j = 0; j <= i; j++) if (events[j][1] === "obs") lastObs = j;
    const age = lastObs < 0 ? null : t - events[lastObs][0];
    const o = step(s, e, age, r, ma, mr);
    s = o.s;
    r = o.r;
    states.push(s);
    cmds.push(o.c);
  });
  return { states, cmds };
}

// Why event i violates the invariant (null when it does not): the set of reasons.
function reasons(events: Ev[], cmds: string[][], ma: number, i: number): string[] {
  if (!cmds[i].some((c) => MOTION.includes(c))) return [];
  const upto = events.slice(0, i + 1);
  const last = (name: string) => upto.map((p) => p[1]).lastIndexOf(name);
  const lo = last("obs");
  const out: string[] = [];
  if (lo < 0 || events[i][0] - events[lo][0] > ma) out.push("Stale");
  if (events[i][1] === "cancel" || last("cancel") > last("start")) out.push("Cancelled");
  if (events[i][1] === "fault" || last("fault") > last("reset")) out.push("Faulted");
  return out;
}

function pick(options: string[], conclusion: string): string {
  const match = options.filter((o) => o === conclusion || o.startsWith(conclusion));
  expect(match).toHaveLength(1);
  return match[0];
}

familyOracles["X32"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const fields = item.fields as { label: string; kind: string; options?: string[] }[];
  const num = (k: string) => Number(p[k]);
  switch (item.structure) {
    case "executive.next-state@1": {
      const age = num("age");
      const run = (a: number) =>
        step(String(p.state), String(p.event), a, num("retries"), num("max_age"), num("max_retries"));
      return fields.map((f) => {
        const exact = /exactly/i.test(f.label);
        const o = run(exact ? num("max_age") : age);
        if (/retry/i.test(f.label)) return o.r;
        if (/command/i.test(f.label)) {
          expect(o.c).toHaveLength(1);
          return pick(f.options as string[], o.c[0]);
        }
        return pick(f.options as string[], o.s);
      });
    }
    case "executive.resume-guards@1": {
      const cases = (p.cases as unknown[][]).map((c) => [Number(c[0]), Number(c[1])]);
      const outs = cases.map(([a, r]) =>
        step(String(p.state), "resume", a, r, num("max_age"), num("max_retries")),
      );
      return fields.map((f) => {
        const k = /\(([a-z])\)/.exec(f.label);
        expect(k).not.toBeNull();
        const o = outs[(k as RegExpExecArray)[1].charCodeAt(0) - 97];
        return /retry/i.test(f.label) ? o.r : pick(f.options as string[], o.s);
      });
    }
    case "executive.trace-replay@1": {
      const { states, cmds } = replay(parseEvents(p.events), num("max_age"), num("max_retries"));
      const stops = cmds.map((c) => c.filter((x) => x === "stop").length);
      return fields.map((f) => {
        if (/^state/i.test(f.label)) return pick(f.options as string[], states[states.length - 1]);
        if (/index/i.test(f.label)) return stops.findIndex((n) => n > 0);
        if (/motion/i.test(f.label)) return cmds.flat().filter((c) => MOTION.includes(c)).length;
        if (/stop/i.test(f.label)) return stops.reduce((a, b) => a + b, 0);
        throw new Error("Unknown field " + f.label);
      });
    }
    case "executive.trace-invariant@1": {
      const events = parseEvents(p.events);
      const cmds = p.commands as string[][];
      const ma = num("max_age");
      expect(cmds).toHaveLength(events.length);
      const why = events.map((_, i) => reasons(events, cmds, ma, i));
      const bad = why.map((w, i) => (w.length ? i : -1)).filter((i) => i >= 0);
      return fields.map((f) => {
        if (/first/i.test(f.label)) return bad[0];
        if (/number/i.test(f.label)) return bad.length;
        const m = /event (\d+)/.exec(f.label);
        expect(m).not.toBeNull();
        const w = why[Number((m as RegExpExecArray)[1])];
        expect(w.length).toBeLessThanOrEqual(1);
        return pick(f.options as string[], w.length ? w[0] : "No violation");
      });
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

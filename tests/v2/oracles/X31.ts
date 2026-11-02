import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X31 (mock joint interface, trajectory validator,
// action client and joint-segment scene check). Every answer is derived from
// the item's inputs. The action client is a transition-table machine, the
// validator a list of named predicates, and the scene collision interval is
// found by scanning the arm angle and bisecting the exact boundary (a different
// method from the corner-direction argument in the solution).
const val = (v: unknown) => {
  const [n, d = "1"] = String(v).split("/");
  return Number(n) / Number(d);
};
const nums = (v: unknown) => (v as unknown[]).map(val);


function validate(p: Record<string, unknown>): string[] {
  const names = p.joint_names as string[],
    iface = p.interface_names as string[];
  const pts = (p.points as [unknown, unknown[]][]).map(
    ([t, q]) => [val(t), nums(q)] as [number, number[]],
  );
  const lo = nums(p.lower),
    hi = nums(p.upper),
    vm = nums(p.max_velocity),
    cur = nums(p.current),
    tol = val(p.start_tol);
  const checks: [string, () => boolean][] = [
    [
      "joint-order-mismatch",
      () =>
        names.length === iface.length &&
        [...names].sort().join("|") === [...iface].sort().join("|") &&
        names.join("|") !== iface.join("|"),
    ],
    [
      "time-not-increasing",
      () => pts.some((pt, i) => i > 0 && !(pt[0] > pts[i - 1][0])),
    ],
    [
      "position-limit",
      () =>
        pts.some(([, q]) => q.some((x, j) => x < lo[j] - 1e-12 || x > hi[j] + 1e-12)),
    ],
    [
      "velocity-limit",
      () =>
        pts.some(
          (pt, i) =>
            i > 0 &&
            pt[1].some(
              (x, j) =>
                Math.abs(x - pts[i - 1][1][j]) >
                vm[j] * (pt[0] - pts[i - 1][0]) + 1e-12,
            ),
        ),
    ],
    [
      "start-state-mismatch",
      () => pts[0][1].some((x, j) => Math.abs(x - cur[j]) > tol + 1e-12),
    ],
  ];
  return checks.filter(([, f]) => f()).map(([n]) => n);
}

// Exact-enough closed segment/rectangle test by clipping against four half-planes
// of the rectangle (parametric Cyrus-Beck), independent of the author's method.
function segHitsBox(
  a: [number, number],
  b: [number, number],
  box: number[],
): boolean {
  let t0 = 0,
    t1 = 1;
  const d = [b[0] - a[0], b[1] - a[1]];
  const planes: [number, number][] = [
    [-d[0], a[0] - box[0]],
    [d[0], box[2] - a[0]],
    [-d[1], a[1] - box[1]],
    [d[1], box[3] - a[1]],
  ];
  for (const [pp, qq] of planes) {
    if (pp === 0) {
      if (qq < -1e-12) return false;
    } else {
      const r = qq / pp;
      if (pp < 0) t0 = Math.max(t0, r);
      else t1 = Math.min(t1, r);
      if (t0 > t1 + 1e-12) return false;
    }
  }
  return true;
}

function armHits(q1: number, q2: number, l1: number, l2: number, box: number[]) {
  const e: [number, number] = [l1 * Math.cos(q1), l1 * Math.sin(q1)];
  const t: [number, number] = [
    e[0] + l2 * Math.cos(q1 + q2),
    e[1] + l2 * Math.sin(q1 + q2),
  ];
  return segHitsBox([0, 0], e, box) || segHitsBox(e, t, box);
}

function runClient(events: [unknown, string, unknown][], timeout: number) {
  const final = new Set(["succeeded", "aborted", "canceled", "rejected", "timed-out"]);
  const live = new Set(["pending", "executing", "canceling"]);
  const table: Record<string, Record<string, string>> = {
    idle: { send_goal: "pending" },
    pending: { accept: "executing", reject: "rejected", cancel_request: "canceling" },
    executing: {
      cancel_request: "canceling",
      result_ok: "succeeded",
      result_abort: "aborted",
    },
    canceling: {
      cancel_done: "canceled",
      result_ok: "succeeded",
      result_abort: "aborted",
    },
  };
  let state = "idle",
    progress = 0,
    sent = 0;
  const trace: { state: string; progress: number }[] = [];
  for (const [tt, name, v] of events) {
    const t = val(tt);
    if (final.has(state)) {
      // absorbed
    } else if (live.has(state) && t - sent > timeout) {
      state = "timed-out";
    } else if (name === "feedback" && (state === "executing" || state === "canceling")) {
      progress = Math.max(progress, val(v));
    } else {
      const next = table[state]?.[name];
      if (next) {
        if (state === "idle") sent = t;
        state = next;
        if (next === "succeeded") progress = 1;
      }
    }
    trace.push({ state, progress });
  }
  return trace;
}

function pick(options: string[], test: (o: string) => boolean): string {
  const hit = options.filter(test);
  expect(hit).toHaveLength(1);
  return hit[0];
}

familyOracles["X31"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const options = (i: number) => item.fields[i].options as string[];
  switch (item.structure) {
    case "mock-interface.trajectory-check@1": {
      const pts = (p.points as [unknown, unknown[]][]).map(
        ([t, q]) => [val(t), nums(q)] as [number, number[]],
      );
      const n = pts.length;
      const speed =
        Math.abs(pts[n - 1][1][0] - pts[n - 2][1][0]) / (pts[n - 1][0] - pts[n - 2][0]);
      const reasons = validate(p);
      expect(reasons.length).toBeLessThanOrEqual(1);
      const verdict = reasons.length ? reasons[0] : "Accepted";
      return [speed, pick(options(1), (o) => o === verdict)];
    }
    case "mock-interface.min-time@1": {
      const pts = (p.points as [unknown, unknown[]][]).map(
        ([t, q]) => [val(t), nums(q)] as [number, number[]],
      );
      const last = pts[pts.length - 1],
        next = nums(p.next_positions),
        lo = nums(p.lower),
        hi = nums(p.upper),
        vm = nums(p.max_velocity);
      const inside = next.every((x, j) => x >= lo[j] && x <= hi[j]);
      expect(inside).toBe(true);
      const need = next.map((x, j) => Math.abs(x - last[1][j]) / vm[j]);
      const dur = Math.max(...need);
      const setters = need.filter((x) => Math.abs(x - dur) < 1e-9).length;
      const who =
        setters > 1 ? "both" : need[0] > need[1] ? "shoulder" : "elbow";
      return [
        last[0] + dur,
        pick(options(1), (o) =>
          who === "both" ? o.startsWith("both") : o === who,
        ),
      ];
    }
    case "mock-interface.scene-sweep@1": {
      const qs = nums(p.q_start),
        qe = nums(p.q_end),
        l1 = val(p.l1),
        l2 = val(p.l2),
        box = nums(p.box);
      expect(qs[1]).toBe(qe[1]);
      const q2 = qs[1];
      const f = (s: number) => armHits(qs[0] + s * (qe[0] - qs[0]), q2, l1, l2, box);
      const N = 200000;
      let first = -1,
        lastHit = -1;
      for (let i = 0; i <= N; i++)
        if (f(i / N)) {
          if (first < 0) first = i;
          lastHit = i;
        }
      expect(first).toBeGreaterThanOrEqual(0);
      const bis = (inside: number, outside: number) => {
        for (let k = 0; k < 60; k++) {
          const m = (inside + outside) / 2;
          if (f(m)) inside = m;
          else outside = m;
        }
        return inside;
      };
      const sLo = first === 0 ? 0 : bis(first / N, (first - 1) / N);
      const sHi = lastHit === N ? 1 : bis(lastHit / N, (lastHit + 1) / N);
      const angle = (s: number) => qs[0] + s * (qe[0] - qs[0]);
      const startHit = f(0),
        endHit = f(1);
      const verdict = startHit
        ? /start pose is in collision/
        : endHit
          ? /end pose is in collision/
          : /only in the middle/;
      return [angle(sLo), angle(sHi), pick(options(2), (o) => verdict.test(o))];
    }
    case "mock-interface.action-trace@1": {
      const trace = runClient(p.events as [unknown, string, unknown][], val(p.timeout));
      const end = trace[trace.length - 1];
      return [pick(options(0), (o) => o === end.state), end.progress];
    }
    case "mock-interface.action-timeout@1": {
      const trace = runClient(p.events as [unknown, string, unknown][], val(p.timeout));
      const idx = trace.findIndex((s) => s.state === "timed-out");
      const end = trace[trace.length - 1];
      return [idx, pick(options(1), (o) => o === end.state), end.progress];
    }
    case "mock-interface.action-cancel-race@1": {
      const events = p.events as [unknown, string, unknown][];
      const trace = runClient(events, val(p.timeout));
      expect(events[5][1]).toBe("feedback");
      const end = trace[trace.length - 1];
      return [
        pick(options(0), (o) => o === end.state),
        trace[5].progress,
        trace.filter((s) => s.state === "canceling").length,
      ];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X23 (replay of a recorded odometry log through a
// ROS-free node core). The replay uses the instantaneous-centre-of-rotation
// form of the arc (R = d / phi, x += R (sin(th+phi) - sin th)), not the chord
// formula. The fault reproducer is an exhaustive search over all 2^n message
// subsets (no reasoning about which message matters): a subset exposes the
// fault when the correct and the faulty replays differ.
type Msg = { kind: string; stamp: number; frame: string; child: string; vl: number; vr: number; x: number; y: number; th: number };
type Cfg = { frame: string; child: string; track: number; gap: number; policy: string; init: [number, number, number] };
type Pose = { stamp: number; x: number; y: number; th: number; flag: string };
type Out = { poses: Pose[]; drops: [number, string][] };

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

function parseCfg(p: Record<string, unknown>): Cfg {
  const ip = (p.initial_pose as string[]).map(Number);
  return {
    frame: p.frame_id as string,
    child: p.child_frame_id as string,
    track: Number(p.track),
    gap: Number(p.max_gap_ms),
    policy: p.gap_policy as string,
    init: [ip[0], ip[1], wrap(ip[2])],
  };
}

function parseMsgs(p: Record<string, unknown>): Msg[] {
  return (p.messages as string[][]).map((r) => {
    if (r[0] === "reset") {
      return { kind: "reset", stamp: Number(r[1]), frame: "", child: "", vl: 0, vr: 0, x: Number(r[2]), y: Number(r[3]), th: Number(r[4]) };
    }
    expect(r[0]).toBe("odom");
    return { kind: "odom", stamp: Number(r[1]), frame: r[2], child: r[3], vl: Number(r[4]), vr: Number(r[5]), x: 0, y: 0, th: 0 };
  });
}

function arc(p: [number, number, number], dl: number, dr: number, track: number): [number, number, number] {
  const phi = (dr - dl) / track;
  const d = (dl + dr) / 2;
  if (Math.abs(phi) < 1e-9) return [p[0] + d * Math.cos(p[2]), p[1] + d * Math.sin(p[2]), wrap(p[2] + phi)];
  const R = d / phi;
  return [p[0] + R * (Math.sin(p[2] + phi) - Math.sin(p[2])), p[1] - R * (Math.cos(p[2] + phi) - Math.cos(p[2])), wrap(p[2] + phi)];
}

function replay(cfg: Cfg, msgs: Msg[], fault = ""): Out {
  const out: Out = { poses: [], drops: [] };
  let pose: [number, number, number] = [0, 0, 0];
  let clock: number | null = null;
  msgs.forEach((m, i) => {
    if (m.kind === "reset") {
      pose = [m.x, m.y, wrap(m.th)];
      clock = m.stamp;
      out.poses.push({ stamp: m.stamp, x: pose[0], y: pose[1], th: pose[2], flag: "reset" });
      return;
    }
    let reason = "";
    if (m.frame !== cfg.frame) reason = "frame";
    else if (m.child !== cfg.child && fault !== "child-ignored") reason = "child";
    else if (clock !== null && m.stamp === clock) reason = "duplicate";
    else if (clock !== null && m.stamp < clock) reason = "ooo";
    if (reason) {
      out.drops.push([i, reason]);
      if (reason === "ooo" && fault === "ooo-rewinds-clock") clock = m.stamp;
      return;
    }
    let flag = "ok";
    if (clock === null) {
      pose = [...cfg.init];
      flag = "init";
    } else {
      const dt = m.stamp - clock;
      const isGap = fault === "gap-inclusive" ? dt >= cfg.gap : dt > cfg.gap;
      if (isGap) flag = "gap";
      if (isGap && cfg.policy === "reset") pose = [...cfg.init];
      else pose = arc(pose, (m.vl * dt) / 1000, (m.vr * dt) / 1000, cfg.track);
    }
    clock = m.stamp;
    out.poses.push({ stamp: m.stamp, x: pose[0], y: pose[1], th: pose[2], flag });
  });
  return out;
}

function same(a: Out, b: Out): boolean {
  if (a.poses.length !== b.poses.length || a.drops.length !== b.drops.length) return false;
  for (let i = 0; i < a.poses.length; i++) {
    const p = a.poses[i], q = b.poses[i];
    if (p.stamp !== q.stamp || p.flag !== q.flag) return false;
    if (Math.abs(p.x - q.x) > 1e-9 || Math.abs(p.y - q.y) > 1e-9 || Math.abs(wrap(p.th - q.th)) > 1e-9) return false;
  }
  return a.drops.every((d, i) => d[0] === b.drops[i][0] && d[1] === b.drops[i][1]);
}

familyOracles["X23"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const cfg = parseCfg(p);
  const msgs = parseMsgs(p);
  switch (item.structure) {
    case "replay.stamp-policy@1": {
      const out = replay(cfg, msgs);
      const last = out.poses[out.poses.length - 1];
      return item.fields.map((f) => {
        const l = f.label.toLowerCase();
        if (l.startsWith("poses published")) return out.poses.length;
        if (l.startsWith("messages dropped")) return out.drops.length;
        if (l.startsWith("published poses flagged gap")) return out.poses.filter((q) => q.flag === "gap").length;
        if (l.startsWith("x of the last")) return last.x;
        if (l.startsWith("y of the last")) return last.y;
        if (l.startsWith("theta of the last")) return last.th;
        throw new Error("Unknown field " + f.label);
      });
    }
    case "replay.fault-reproducer@1": {
      const fault = p.fault as string;
      const n = msgs.length;
      expect(n).toBeLessThanOrEqual(12);
      let best = Infinity;
      let count = 0;
      for (let mask = 0; mask < 1 << n; mask++) {
        const sub: Msg[] = [];
        for (let i = 0; i < n; i++) if (mask >> i & 1) sub.push(msgs[i]);
        if (sub.length > best) continue;
        if (!same(replay(cfg, sub), replay(cfg, sub, fault))) {
          if (sub.length < best) { best = sub.length; count = 0; }
          count++;
        }
      }
      expect(best).toBeLessThan(Infinity);
      return item.fields.map((f) => {
        const l = f.label.toLowerCase();
        if (l.startsWith("smallest number")) return best;
        if (l.startsWith("number of different")) return count;
        throw new Error("Unknown field " + f.label);
      });
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

import { expect } from "vitest";
import type { Item } from "../../../lib/v2/content";
import { familyOracles } from "./registry";

// Independent oracle for X29 (URDF chain parsing and TF lookups). The URDF text
// is tokenised with a tag scanner (no XML library). Transforms are carried as
// (unit quaternion, translation) pairs: rpy -> q = qz*qy*qx by half-angle
// quaternions, revolute motion as an axis-angle quaternion, vectors rotated by
// v + 2w(u x v) + 2u x (u x v). Lookups walk BOTH frames to the root and compose
// relative poses with quaternion conjugates (no 4x4 matrices, no inverse).
type V = [number, number, number];
type Q = [number, number, number, number]; // w, x, y, z
type Pose = { q: Q; p: V };
type Joint = { name: string; type: string; parent: string; child: string; xyz: V; rpy: V; axis: V };

const qmul = (a: Q, b: Q): Q => [
  a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
  a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
  a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
  a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0],
];
const qconj = (a: Q): Q => [a[0], -a[1], -a[2], -a[3]];
const cross = (a: V, b: V): V => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const vadd = (a: V, b: V): V => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const vsub = (a: V, b: V): V => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const vscale = (a: V, s: number): V => [a[0] * s, a[1] * s, a[2] * s];
const rot = (q: Q, v: V): V => {
  const u: V = [q[1], q[2], q[3]];
  const t = vscale(cross(u, v), 2);
  return vadd(vadd(v, vscale(t, q[0])), cross(u, t));
};
const axisAngle = (axis: V, a: number): Q => {
  const n = Math.hypot(...axis);
  const s = Math.sin(a / 2) / n;
  return [Math.cos(a / 2), axis[0] * s, axis[1] * s, axis[2] * s];
};
const rpyQuat = (r: V): Q =>
  qmul(qmul(axisAngle([0, 0, 1], r[2]), axisAngle([0, 1, 0], r[1])), axisAngle([1, 0, 0], r[0]));
const compose = (a: Pose, b: Pose): Pose => ({ q: qmul(a.q, b.q), p: vadd(a.p, rot(a.q, b.p)) });
const ID: Pose = { q: [1, 0, 0, 0], p: [0, 0, 0] };

const triple = (s: string | undefined, dflt: V): V => {
  if (s === undefined) return dflt;
  const t = s.trim().split(/\s+/).map(Number);
  expect(t.length).toBe(3);
  return t as V;
};
const attr = (tag: string, name: string): string | undefined => {
  const m = new RegExp("\\b" + name + '\\s*=\\s*"([^"]*)"').exec(tag);
  return m ? m[1] : undefined;
};

function scan(urdf: string) {
  const links: string[] = [];
  const joints: Joint[] = [];
  let cur: Partial<Joint> & { hasAxis?: boolean } | null = null;
  const flush = () => {
    if (!cur) return;
    joints.push({
      name: cur.name!, type: cur.type!, parent: cur.parent!, child: cur.child!,
      xyz: cur.xyz ?? [0, 0, 0], rpy: cur.rpy ?? [0, 0, 0], axis: cur.axis ?? [1, 0, 0],
    });
    cur = null;
  };
  for (const m of urdf.matchAll(/<(\/?)([a-z]+)([^>]*)>/g)) {
    const [, close, tag, rest] = m;
    if (close) { if (tag === "joint") flush(); continue; }
    if (tag === "link") links.push(attr(rest, "name")!);
    else if (tag === "joint") cur = { name: attr(rest, "name"), type: attr(rest, "type") };
    else if (cur && tag === "parent") cur.parent = attr(rest, "link");
    else if (cur && tag === "child") cur.child = attr(rest, "link");
    else if (cur && tag === "origin") { cur.xyz = triple(attr(rest, "xyz"), [0, 0, 0]); cur.rpy = triple(attr(rest, "rpy"), [0, 0, 0]); }
    else if (cur && tag === "axis") cur.axis = triple(attr(rest, "xyz"), [1, 0, 0]);
  }
  flush();
  return { links, joints };
}

function order(links: string[], joints: Joint[]) {
  const childSet = new Set(joints.map((j) => j.child));
  const roots = links.filter((l) => !childSet.has(l));
  const chain: Joint[] = [];
  const seen = new Set<string>();
  if (roots.length === 1) {
    let at = roots[0];
    seen.add(at);
    for (;;) {
      const nxt = joints.find((j) => j.parent === at);
      if (!nxt || seen.has(nxt.child)) break;
      chain.push(nxt);
      seen.add(nxt.child);
      at = nxt.child;
    }
  }
  return { roots, chain, reachable: roots.length === 1 ? seen.size : 0 };
}

// pose of every link in the base frame, and the joint-frame pose at motion 0
function poses(urdf: string, q: Record<string, number>) {
  const { links, joints } = scan(urdf);
  const { roots, chain } = order(links, joints);
  const base: Record<string, Pose> = { [roots[0]]: ID };
  const jointFrame: Record<string, Pose> = {};
  const parentOf: Record<string, string> = {};
  let cur = ID;
  for (const j of chain) {
    const origin: Pose = { q: rpyQuat(j.rpy), p: j.xyz };
    jointFrame[j.name] = compose(cur, origin);
    const n = Math.hypot(...j.axis);
    const u = vscale(j.axis, 1 / n);
    const v = q[j.name] ?? 0;
    const motion: Pose = j.type === "revolute" ? { q: axisAngle(u, v), p: [0, 0, 0] }
      : j.type === "prismatic" ? { q: [1, 0, 0, 0], p: vscale(u, v) } : ID;
    cur = compose(jointFrame[j.name], motion);
    base[j.child] = cur;
    parentOf[j.child] = j.parent;
  }
  return { base, jointFrame, parentOf, chain, roots };
}

// pose of `source` in `target` by walking both to the root: p = conj(qt)(ps - pt)
function lookup(urdf: string, target: string, source: string, q: Record<string, number>): Pose {
  const { base } = poses(urdf, q);
  const t = base[target], s = base[source];
  const qi = qconj(t.q);
  return { q: qmul(qi, s.q), p: rot(qi, vsub(s.p, t.p)) };
}

const nums = (r: Record<string, unknown>): Record<string, number> =>
  Object.fromEntries(Object.entries(r).map(([k, v]) => [k, Number(v)]));
const only = (opts: string[], pred: (o: string) => boolean): string => {
  const hit = opts.filter(pred);
  expect(hit.length).toBe(1);
  return hit[0];
};

familyOracles["X29"] = (item: Item): (number | string)[] => {
  const p = item.inputs as Record<string, unknown>;
  const urdf = String(p.urdf);
  const optionsOf = (i: number): string[] => (item.fields[i] as { options?: string[] }).options!;
  switch (item.structure) {
    case "urdf-chain.parse.facts@1": {
      const { links, joints } = scan(urdf);
      const { roots, chain } = order(links, joints);
      expect(roots.length).toBe(1);
      const joinOrder = chain.map((j) => j.name).join(", ");
      const dof = joints.filter((j) => j.type === "revolute" || j.type === "prismatic").length;
      return [only(optionsOf(0), (o) => o === roots[0]), only(optionsOf(1), (o) => o === joinOrder), dof];
    }
    case "urdf-chain.parse.defaults@1": {
      const { chain } = poses(urdf, {});
      const unit = (name: string): V => {
        const j = chain.find((c) => c.name === name)!;
        return vscale(j.axis, 1 / Math.hypot(...j.axis));
      };
      const f = unit(String(p.axis_joint)), d = unit(String(p.default_joint));
      const tip = poses(urdf, {}).base[String(p.tip)].p;
      return [f[1], f[2], d[0], tip[0], tip[2]];
    }
    case "urdf-chain.parse.defect@1": {
      const { links, joints } = scan(urdf);
      const names = new Set(links);
      const { roots, reachable } = order(links, joints);
      const parentCount = new Map<string, number>();
      for (const j of joints) parentCount.set(j.child, (parentCount.get(j.child) ?? 0) + 1);
      let kind: string;
      if (joints.some((j) => !names.has(j.parent) || !names.has(j.child))) kind = "Undefined";
      else if ([...parentCount.values()].some((c) => c > 1)) kind = "Double parent";
      else if (roots.length > 1) kind = "Two roots";
      else kind = "Cycle";
      // a cycle: one root, but fewer links reachable than defined
      if (kind === "Cycle") expect(reachable).toBeLessThan(links.length);
      const choice = only(optionsOf(0), (o) => o.startsWith(kind + ":"));
      return [choice, roots.length, reachable];
    }
    case "urdf-chain.tf.planar-tip@1": {
      const pose = poses(urdf, nums(p.q as Record<string, unknown>)).base[String(p.link)];
      const c1 = rot(pose.q, [1, 0, 0]);
      return [pose.p[0], pose.p[1], pose.p[2], c1[0], c1[1]];
    }
    case "urdf-chain.tf.rpy-offset@1": {
      const q = nums(p.q as Record<string, unknown>);
      const all = poses(urdf, q);
      const pose = all.base[String(p.link)];
      const jf = all.jointFrame[String(p.axis_joint)];
      const j = all.chain.find((c) => c.name === p.axis_joint)!;
      const ax = rot(jf.q, vscale(j.axis, 1 / Math.hypot(...j.axis)));
      const r = ax.map((v) => Math.round(v));
      const vec = `(${r.join(", ")})`;
      return [pose.p[0], pose.p[1], pose.p[2], only(optionsOf(3), (o) => o.endsWith(vec))];
    }
    case "urdf-chain.tf.lookup-between@1": {
      const q = nums(p.q as Record<string, unknown>);
      const ls = p.lookups as { target: string; source: string }[];
      const a = lookup(urdf, ls[0].target, ls[0].source, q);
      const b = lookup(urdf, ls[1].target, ls[1].source, q);
      return [a.p[0], a.p[1], b.p[0], b.p[1], b.p[2]];
    }
  }
  throw new Error("Unknown structure " + item.structure);
};

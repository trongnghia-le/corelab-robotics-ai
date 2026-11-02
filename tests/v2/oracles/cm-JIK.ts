import { cmOracles } from "./registry";

// Independent numerical oracles for the R06.planar-jacobian / R05.planar-ik
// C/M sources (F-JIK and RV-JIK). Every answer is derived from the item inputs
// alone. The Jacobian comes from central finite differences of forward
// kinematics (no analytic derivative); IK uses circle-circle intersection of
// the elbow position (no law of cosines, no acos on the elbow angle).
type Vec = [number, number];

const num = (value: unknown): number => Number(String(value));
const TAU = 2 * Math.PI;
const wrap = (angle: number): number =>
  Math.atan2(Math.sin(angle), Math.cos(angle));

function fk(q1: number, q2: number, l1: number, l2: number): Vec {
  return [
    l1 * Math.cos(q1) + l2 * Math.cos(q1 + q2),
    l1 * Math.sin(q1) + l2 * Math.sin(q1 + q2),
  ];
}

// J = [[dx/dq1, dx/dq2], [dy/dq1, dy/dq2]] by central differences.
function jacobian(
  q1: number,
  q2: number,
  l1: number,
  l2: number,
): [[number, number], [number, number]] {
  const h = 1e-6;
  const a1 = fk(q1 + h, q2, l1, l2);
  const b1 = fk(q1 - h, q2, l1, l2);
  const a2 = fk(q1, q2 + h, l1, l2);
  const b2 = fk(q1, q2 - h, l1, l2);
  return [
    [(a1[0] - b1[0]) / (2 * h), (a2[0] - b2[0]) / (2 * h)],
    [(a1[1] - b1[1]) / (2 * h), (a2[1] - b2[1]) / (2 * h)],
  ];
}

interface Pose {
  q1: number;
  q2: number;
}

// All IK poses for a target: intersect the circle |e| = l1 (elbow) with the
// circle |t - e| = l2. A tangency (target on the ring edge) is one pose.
function solveIk(x: number, y: number, l1: number, l2: number): Pose[] {
  const d = Math.hypot(x, y);
  const edge = 1e-9;
  const outer = l1 + l2;
  const inner = Math.abs(l1 - l2);
  if (d > outer + edge || d < inner - edge || d < 1e-12) return [];
  // Distance from the base to the chord of the two circle intersections.
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
  const hh = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const ux = x / d;
  const uy = y / d;
  const mid: Vec = [a * ux, a * uy];
  const elbows: Vec[] =
    hh < 1e-7
      ? [mid]
      : [
          [mid[0] - hh * uy, mid[1] + hh * ux],
          [mid[0] + hh * uy, mid[1] - hh * ux],
        ];
  return elbows.map((e) => {
    const q1 = Math.atan2(e[1], e[0]);
    const q2 = wrap(Math.atan2(y - e[1], x - e[0]) - q1);
    return { q1, q2 };
  });
}

function inLimit(value: number, lo: number, hi: number): boolean {
  for (let k = -3; k <= 3; k++) {
    const v = value + k * TAU;
    if (v >= lo - 1e-9 && v <= hi + 1e-9) return true;
  }
  return false;
}

// The representative of an angle inside [lo, hi], if any.
function representative(value: number, lo: number, hi: number): number {
  for (let k = -3; k <= 3; k++) {
    const v = value + k * TAU;
    if (v >= lo - 1e-9 && v <= hi + 1e-9) return v;
  }
  return value;
}

cmOracles["jik.jacobian.entries@1"] = (p) => {
  const j = jacobian(num(p.q1), num(p.q2), num(p.l1), num(p.l2));
  return [j[0][0], j[0][1], j[1][0], j[1][1]];
};

cmOracles["jik.jacobian.tip-velocity@1"] = (p) => {
  // Tip velocity is the derivative of FK along the joint-rate direction.
  const q1 = num(p.q1);
  const q2 = num(p.q2);
  const r1 = num(p.dq1);
  const r2 = num(p.dq2);
  const l1 = num(p.l1);
  const l2 = num(p.l2);
  const h = 1e-6;
  const ahead = fk(q1 + h * r1, q2 + h * r2, l1, l2);
  const behind = fk(q1 - h * r1, q2 - h * r2, l1, l2);
  return [(ahead[0] - behind[0]) / (2 * h), (ahead[1] - behind[1]) / (2 * h)];
};

cmOracles["jik.jacobian.det-rate@1"] = (p) => {
  const j = jacobian(num(p.q1), num(p.q2), num(p.l1), num(p.l2));
  const det = j[0][0] * j[1][1] - j[0][1] * j[1][0];
  const vx = num(p.vx);
  const vy = num(p.vy);
  // Gauss elimination with partial pivoting instead of Cramer's rule.
  const m = [
    [j[0][0], j[0][1], vx],
    [j[1][0], j[1][1], vy],
  ];
  if (Math.abs(m[1][0]) > Math.abs(m[0][0])) m.reverse();
  const f = m[1][0] / m[0][0];
  const q2dot = (m[1][2] - f * m[0][2]) / (m[1][1] - f * m[0][1]);
  const q1dot = (m[0][2] - m[0][1] * q2dot) / m[0][0];
  return [det, q1dot, q2dot];
};

cmOracles["jik.ik.branch@1"] = (p) => {
  const want = String(p.branch);
  const sign = want === "q2<0" ? -1 : want === "q2>0" ? 1 : 0;
  if (sign === 0) throw new Error("Unknown branch " + want);
  const poses = solveIk(num(p.x), num(p.y), num(p.l1), num(p.l2));
  const pick = poses.find((s) => Math.sign(s.q2) === sign);
  if (!pick) throw new Error("No pose on branch " + want);
  return [pick.q1, pick.q2];
};

cmOracles["jik.ik.limited@1"] = (p) => {
  const poses = solveIk(num(p.x), num(p.y), num(p.l1), num(p.l2));
  const q1min = num(p.q1min);
  const q1max = num(p.q1max);
  const q2min = num(p.q2min);
  const q2max = num(p.q2max);
  const ok = poses.filter(
    (s) => inLimit(s.q1, q1min, q1max) && inLimit(s.q2, q2min, q2max),
  );
  if (ok.length !== 1) throw new Error("Expected exactly one admissible pose");
  return [
    poses.length,
    ok.length,
    representative(ok[0].q1, q1min, q1max),
    representative(ok[0].q2, q2min, q2max),
  ];
};

cmOracles["jik.ik.solution-count@1"] = (p) => {
  const l1 = num(p.l1);
  const l2 = num(p.l2);
  const q1min = num(p.q1min);
  const q1max = num(p.q1max);
  const q2min = num(p.q2min);
  const q2max = num(p.q2max);
  return (p.targets as unknown[][]).map(
    (t) =>
      solveIk(num(t[0]), num(t[1]), l1, l2).filter(
        (s) => inLimit(s.q1, q1min, q1max) && inLimit(s.q2, q2min, q2max),
      ).length,
  );
};

// Fields: cos q2 before clamping, residual distance, and the honest report as
// a status code (0 solution found, 1 unreachable target, 2 solver failed,
// 3 limits exclude every solution) because oracles return numbers only.
cmOracles["jik.ik.clamp-residual@1"] = (p) => {
  const x = num(p.x);
  const y = num(p.y);
  const l1 = num(p.l1);
  const l2 = num(p.l2);
  const raw = (x * x + y * y - l1 * l1 - l2 * l2) / (2 * l1 * l2);
  const clamped = Math.min(1, Math.max(-1, raw));
  const q2 = Math.acos(clamped);
  const q1 =
    Math.atan2(y, x) - Math.atan2(l2 * Math.sin(q2), l1 + l2 * Math.cos(q2));
  const tip = fk(q1, q2, l1, l2);
  const residual = Math.hypot(tip[0] - x, tip[1] - y);
  // The target is unreachable exactly when the residual cannot be removed.
  return [
    raw,
    residual,
    residual > 1e-6 ? "Unreachable target" : "Solution found",
  ];
};

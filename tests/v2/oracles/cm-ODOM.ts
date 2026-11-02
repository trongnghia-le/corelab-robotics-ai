import { cmOracles } from "./registry";

// Independent numerical oracles for the R02.exact-arc C/M sources (F-ODOM and
// RV-ODOM). Every answer is derived from the item inputs alone. The pose
// integrals use RK4 on the unicycle ODE instead of the closed-form arc, the
// wheel/body maps use the rigid-body velocity at the wheel contact points, and
// the turn centre is the circumcentre of three simulated poses.
type State = [number, number, number];

const num = (value: unknown): number => Number(String(value));
const wrap = (angle: number): number =>
  Math.atan2(Math.sin(angle), Math.cos(angle));

// Rim speeds of a rigid body: the left wheel sits at lateral offset +b/2 and
// the right at -b/2, so speed(s) = v - omega s. Two equations, two unknowns.
function bodyFromWheels(vl: number, vr: number, b: number): [number, number] {
  const omega = (vr - vl) / b;
  return [vl + (omega * b) / 2, omega];
}

function wheelsFromBody(v: number, omega: number, b: number): [number, number] {
  return [v - (omega * b) / 2, v + (omega * b) / 2];
}

function rk4(state: State, v: number, omega: number, duration: number): State {
  const steps = 4000;
  const h = duration / steps;
  const f = (s: State): State => [
    v * Math.cos(s[2]),
    v * Math.sin(s[2]),
    omega,
  ];
  const add = (s: State, k: State, scale: number): State => [
    s[0] + k[0] * scale,
    s[1] + k[1] * scale,
    s[2] + k[2] * scale,
  ];
  let s = state;
  for (let i = 0; i < steps; i++) {
    const k1 = f(s);
    const k2 = f(add(s, k1, h / 2));
    const k3 = f(add(s, k2, h / 2));
    const k4 = f(add(s, k3, h));
    s = [
      s[0] + (h / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]),
      s[1] + (h / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]),
      s[2] + (h / 6) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]),
    ];
  }
  return s;
}

function startPose(p: Record<string, unknown>): State {
  return [num(p.x0), num(p.y0), num(p.theta0)];
}

cmOracles["arc-odom.wheel-body@1"] = (p) =>
  bodyFromWheels(num(p.vl), num(p.vr), num(p.b));

cmOracles["arc-odom.body-wheels@1"] = (p) =>
  wheelsFromBody(num(p.v), num(p.omega), num(p.b));

cmOracles["arc-odom.world-pose@1"] = (p) => {
  const [v, omega] = bodyFromWheels(num(p.vl), num(p.vr), num(p.b));
  const end = rk4(startPose(p), v, omega, num(p.dt));
  return [end[0], end[1], end[2]];
};

cmOracles["arc-odom.heading-wrap@1"] = (p) => {
  const [, omega] = bodyFromWheels(num(p.vl), num(p.vr), num(p.b));
  const end = rk4([0, 0, num(p.theta0)], 0, omega, num(p.dt));
  return [end[2] - num(p.theta0), wrap(end[2])];
};

cmOracles["arc-odom.two-segment@1"] = (p) => {
  const b = num(p.b);
  let s = startPose(p);
  for (const raw of [p.seg1, p.seg2]) {
    const [vl, vr, dt] = (raw as unknown[]).map(num);
    const [v, omega] = bodyFromWheels(vl, vr, b);
    s = rk4(s, v, omega, dt);
  }
  return [s[0], s[1], s[2]];
};

// Encoder distances over an interval of unit length: the wheel travels equal
// the wheel speeds, so the same ODE applies with duration 1.
cmOracles["arc-odom.travel-step@1"] = (p) => {
  const [s, dTheta] = bodyFromWheels(num(p.dl), num(p.dr), num(p.b));
  const end = rk4(startPose(p), s, dTheta, 1);
  return [end[0], end[1], end[2]];
};

cmOracles["arc-odom.turn-centre@1"] = (p) => {
  const [v, omega] = bodyFromWheels(num(p.vl), num(p.vr), num(p.b));
  const step = 1 / Math.abs(omega);
  const a = startPose(p);
  const m = rk4(a, v, omega, step);
  const c = rk4(m, v, omega, step);
  // Circumcentre of the three simulated axle-midpoint positions.
  const d =
    2 * (a[0] * (m[1] - c[1]) + m[0] * (c[1] - a[1]) + c[0] * (a[1] - m[1]));
  const sa = a[0] ** 2 + a[1] ** 2;
  const sm = m[0] ** 2 + m[1] ** 2;
  const sc = c[0] ** 2 + c[1] ** 2;
  return [
    (sa * (m[1] - c[1]) + sm * (c[1] - a[1]) + sc * (a[1] - m[1])) / d,
    (sa * (c[0] - m[0]) + sm * (a[0] - c[0]) + sc * (m[0] - a[0])) / d,
  ];
};

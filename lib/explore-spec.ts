// Spec and compiler for interactive "explore" lesson blocks (no React here so
// tests can import it). See components/explore.tsx for the renderer.
import { z } from "zod";
import { compile } from "./expr";

const num = z.union([z.number(), z.string()]);
const pt = z.tuple([num, num]);
const label = { label: z.string(), label_vi: z.string().optional() };
const color = z.string().optional();
const item = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("segment"),
    from: pt,
    to: pt,
    color,
    width: z.number().optional(),
    dash: z.boolean().optional(),
  }),
  z.object({
    type: z.literal("arrow"),
    from: pt,
    to: pt,
    color,
    width: z.number().optional(),
  }),
  z.object({
    type: z.literal("point"),
    at: pt,
    color,
    label: z.string().optional(),
    label_vi: z.string().optional(),
  }),
  z.object({
    type: z.literal("circle"),
    center: pt,
    r: num,
    color,
    dash: z.boolean().optional(),
    fill: z.boolean().optional(),
  }),
  z.object({
    type: z.literal("polyline"),
    points: z.array(pt),
    color,
    dash: z.boolean().optional(),
  }),
  z.object({
    type: z.literal("label"),
    at: pt,
    text: z.string(),
    text_vi: z.string().optional(),
    color,
  }),
]);
const p3 = z.tuple([num, num, num]);
const range = z.tuple([z.number(), z.number()]);
const item3 = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("segment"),
    from: p3,
    to: p3,
    color,
    width: z.number().optional(),
    dash: z.boolean().optional(),
  }),
  z.object({
    type: z.literal("arrow"),
    from: p3,
    to: p3,
    color,
    width: z.number().optional(),
  }),
  z.object({
    type: z.literal("point"),
    at: p3,
    color,
    label: z.string().optional(),
    label_vi: z.string().optional(),
  }),
  z.object({
    type: z.literal("label"),
    at: p3,
    text: z.string(),
    text_vi: z.string().optional(),
    color,
  }),
  // A coordinate frame: origin plus a rotation given as 3 rows of R, or as
  // Z-Y-X Euler angles [yaw, pitch, roll] in radians (R = Rz·Ry·Rx).
  z.object({
    type: z.literal("frame"),
    origin: p3,
    R: z.tuple([p3, p3, p3]).optional(),
    euler: p3.optional(),
    length: num.optional(),
    label: z.string().optional(),
    label_vi: z.string().optional(),
  }),
  // Parametric curve x(t), y(t), z(t).
  z.object({
    type: z.literal("curve"),
    t: range,
    x: num,
    y: num,
    z: num,
    n: z.number().int().min(2).max(400).optional(),
    color,
    dash: z.boolean().optional(),
  }),
  // Parametric surface x(u,v), y(u,v), z(u,v); for z = f(x, y) use x: "u", y: "v".
  z.object({
    type: z.literal("surface"),
    u: range,
    v: range,
    x: num,
    y: num,
    z: num,
    n: z.number().int().min(2).max(40).optional(),
    color,
    fill: z.boolean().optional(),
  }),
]);
export const exploreSpec = z.object({
  title: z.string(),
  title_vi: z.string().optional(),
  prompt: z.string().optional(),
  prompt_vi: z.string().optional(),
  params: z
    .array(
      z.object({
        name: z.string().regex(/^[A-Za-z_]\w*$/),
        ...label,
        min: z.number(),
        max: z.number(),
        step: z.number().positive().optional(),
        value: z.number(),
        unit: z.string().optional(),
      }),
    )
    .min(1)
    .max(6),
  let: z
    .array(z.object({ name: z.string().regex(/^[A-Za-z_]\w*$/), expr: num }))
    .optional(),
  plot: z
    .object({
      x: z.object({
        name: z.string(),
        min: z.number(),
        max: z.number(),
        ...label,
      }),
      y: z.object({
        ...label,
        min: z.number().optional(),
        max: z.number().optional(),
      }),
      series: z
        .array(z.object({ expr: num, ...label, color }))
        .min(1)
        .max(5),
      points: z
        .array(
          z.object({
            x: num,
            y: num,
            color,
            label: z.string().optional(),
            label_vi: z.string().optional(),
          }),
        )
        .optional(),
    })
    .optional(),
  scene3d: z
    .object({
      range: z.number().positive(),
      floor: z.boolean().optional(),
      axes: z.boolean().optional(),
      view: z
        .object({
          azimuth: z.number().optional(),
          elevation: z.number().optional(),
        })
        .optional(),
      items: z.array(item3).min(1).max(40),
    })
    .optional(),
  scene: z
    .object({
      xmin: z.number(),
      xmax: z.number(),
      ymin: z.number(),
      ymax: z.number(),
      grid: z.boolean().optional(),
      items: z.array(item).min(1).max(40),
    })
    .optional(),
  readouts: z
    .array(
      z.object({
        ...label,
        expr: num,
        unit: z.string().optional(),
        digits: z.number().int().min(0).max(6).optional(),
      }),
    )
    .max(8)
    .optional(),
});
export type Spec = z.infer<typeof exploreSpec>;

export type Fn = (s: Record<string, number>) => number;
/** Compile every expression of a spec once; throws on any bad expression. */
export function compileSpec(spec: Spec) {
  const c = (v: string | number): Fn =>
    typeof v === "number" ? () => v : compile(v);
  return {
    lets: (spec.let ?? []).map((l) => ({ name: l.name, f: c(l.expr) })),
    series: spec.plot?.series.map((s) => c(s.expr)) ?? [],
    points: spec.plot?.points?.map((p) => [c(p.x), c(p.y)] as const) ?? [],
    items: (spec.scene?.items ?? []).map((it) => {
      const P = (p: [string | number, string | number]) =>
        [c(p[0]), c(p[1])] as const;
      switch (it.type) {
        case "segment":
        case "arrow":
          return { it, a: P(it.from), b: P(it.to) };
        case "point":
        case "label":
          return { it, a: P(it.at) };
        case "circle":
          return { it, a: P(it.center), r: c(it.r) };
        case "polyline":
          return { it, pts: it.points.map(P) };
      }
    }),
    readouts: (spec.readouts ?? []).map((r) => c(r.expr)),
    items3: (spec.scene3d?.items ?? []).map((it) => compileItem3(it, c)),
  };
}

export type V3 = [number, number, number];
export type Prim3 =
  | {
      kind: "line";
      a: V3;
      b: V3;
      color?: string;
      width: number;
      dash?: boolean;
      arrow?: boolean;
    }
  | { kind: "point"; a: V3; color?: string; label?: string; label_vi?: string }
  | { kind: "text"; a: V3; color?: string; label: string; label_vi?: string }
  | { kind: "poly"; pts: V3[]; color?: string; fill: boolean };
type Item3 = z.infer<typeof item3>;

function compileItem3(it: Item3, c: (v: string | number) => Fn) {
  const P = (p: readonly [string | number, string | number, string | number]) =>
    [c(p[0]), c(p[1]), c(p[2])] as const;
  const at = (f: readonly [Fn, Fn, Fn], s: Record<string, number>): V3 => [
    f[0](s),
    f[1](s),
    f[2](s),
  ];
  switch (it.type) {
    case "segment":
    case "arrow": {
      const a = P(it.from),
        b = P(it.to);
      return (s: Record<string, number>): Prim3[] => [
        {
          kind: "line",
          a: at(a, s),
          b: at(b, s),
          color: it.color,
          width: it.width ?? (it.type === "arrow" ? 2.5 : 4),
          dash: it.type === "segment" ? it.dash : false,
          arrow: it.type === "arrow",
        },
      ];
    }
    case "point": {
      const a = P(it.at);
      return (s: Record<string, number>): Prim3[] => [
        {
          kind: "point",
          a: at(a, s),
          color: it.color,
          label: it.label,
          label_vi: it.label_vi,
        },
      ];
    }
    case "label": {
      const a = P(it.at);
      return (s: Record<string, number>): Prim3[] => [
        {
          kind: "text",
          a: at(a, s),
          color: it.color,
          label: it.text,
          label_vi: it.text_vi,
        },
      ];
    }
    case "frame": {
      const o = P(it.origin);
      const R = it.R?.map(P);
      const E = it.euler ? P(it.euler) : null;
      const L = c(it.length ?? 1);
      return (s: Record<string, number>): Prim3[] => {
        const org = at(o, s),
          len = L(s);
        let M: number[][];
        if (R) M = R.map((row) => at(row, s));
        else if (E) {
          const [y, p, r] = at(E, s);
          const [cy, sy, cp, sp, cr, sr] = [
            Math.cos(y),
            Math.sin(y),
            Math.cos(p),
            Math.sin(p),
            Math.cos(r),
            Math.sin(r),
          ];
          // R = Rz(yaw) Ry(pitch) Rx(roll)
          M = [
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr],
          ];
        } else
          M = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
          ];
        const axis = (k: number): V3 => [
          org[0] + len * M[0][k],
          org[1] + len * M[1][k],
          org[2] + len * M[2][k],
        ];
        const out: Prim3[] = (["red", "green", "blue"] as const).map(
          (color, k) => ({
            kind: "line" as const,
            a: org,
            b: axis(k),
            color,
            width: 3,
            arrow: true,
          }),
        );
        if (it.label)
          out.push({
            kind: "text",
            a: org,
            label: it.label,
            label_vi: it.label_vi,
            color: "grey",
          });
        return out;
      };
    }
    case "curve": {
      const f = P([it.x, it.y, it.z]),
        n = it.n ?? 120;
      return (s: Record<string, number>): Prim3[] => {
        const out: Prim3[] = [];
        let prev: V3 | null = null;
        for (let i = 0; i <= n; i++) {
          const t = it.t[0] + ((it.t[1] - it.t[0]) * i) / n;
          const q = at(f, { ...s, t });
          if (prev && q.every(Number.isFinite))
            out.push({
              kind: "line",
              a: prev,
              b: q,
              color: it.color,
              width: 2.5,
              dash: it.dash,
            });
          prev = q.every(Number.isFinite) ? q : null;
        }
        return out;
      };
    }
    case "surface": {
      const f = P([it.x, it.y, it.z]),
        n = it.n ?? 18;
      return (s: Record<string, number>): Prim3[] => {
        const grid: V3[][] = [];
        for (let i = 0; i <= n; i++) {
          const row: V3[] = [];
          for (let j = 0; j <= n; j++) {
            const u = it.u[0] + ((it.u[1] - it.u[0]) * i) / n,
              v = it.v[0] + ((it.v[1] - it.v[0]) * j) / n;
            row.push(at(f, { ...s, u, v }));
          }
          grid.push(row);
        }
        const out: Prim3[] = [];
        for (let i = 0; i < n; i++)
          for (let j = 0; j < n; j++) {
            const pts = [
              grid[i][j],
              grid[i + 1][j],
              grid[i + 1][j + 1],
              grid[i][j + 1],
            ];
            if (pts.every((q) => q.every(Number.isFinite)))
              out.push({
                kind: "poly",
                pts,
                color: it.color,
                fill: it.fill !== false,
              });
          }
        return out;
      };
    }
  }
}

/** All 3D primitives of a scene for the given parameter values. */
export function scene3dPrimitives(
  compiled: ReturnType<typeof compileSpec>,
  scope: Record<string, number>,
) {
  return compiled.items3.flatMap((f) => f(scope));
}

/** Parameters plus the `let` values, evaluated in order. */
export function scopeFor(
  spec: Spec,
  compiled: ReturnType<typeof compileSpec>,
  values: Record<string, number>,
) {
  const scope: Record<string, number> = { ...values };
  for (const l of compiled.lets) scope[l.name] = l.f(scope);
  return scope;
}

/** Size of the 3D view box, in SVG units. */
export const VIEW3 = { W: 560, H: 400 } as const;
/**
 * The perspective projection of a scene3d view: world z is up; turn about z
 * by the azimuth, then tilt by the elevation (degrees). Shared by the
 * renderer and the tests that check a scene fits its box.
 */
export function projector(range: number, azimuth: number, elevation: number) {
  const { W, H } = VIEW3;
  const a = (azimuth * Math.PI) / 180,
    e = (elevation * Math.PI) / 180;
  const k = (Math.min(W, H) / 2 - 18) / (range * 1.12),
    dist = range * 6;
  return (p: V3) => {
    const x1 = p[0] * Math.cos(a) - p[1] * Math.sin(a);
    const y1 = p[0] * Math.sin(a) + p[1] * Math.cos(a);
    const up = p[2] * Math.cos(e) - y1 * Math.sin(e);
    const depth = y1 * Math.cos(e) + p[2] * Math.sin(e);
    const f = dist / (dist + depth);
    return { x: W / 2 + x1 * k * f, y: H / 2 - up * k * f, d: depth };
  };
}

import { expect, it } from "vitest";
import { catalog, family, gradeItem, type Item } from "../../lib/v2/content";
type Inputs = Record<string, unknown>;
const value = (v: unknown) => {
  const [n, d = "1"] = String(v).split("/");
  return Number(n) / Number(d);
};
const nums = (v: unknown) => (v as unknown[]).map(value);
function shortest(
  edges: [string, string, number][],
  from: string,
  to: string,
  seen = new Set<string>(),
): number {
  if (from === to) return 0;
  const next = new Set(seen).add(from);
  const costs = edges
    .filter((e) => e[0] === from && !next.has(e[1]))
    .map((e) => e[2] + shortest(edges, e[1], to, next));
  return Math.min(Infinity, ...costs);
}
function oracle(familyId: string, item: Item): (number | string)[] {
  const p: Inputs = item.inputs,
    n = (key: string) => value(p[key]);
  switch (familyId) {
    case "X01": {
      const u = nums(p.u),
        v = nums(p.v),
        scale =
          u.reduce((s, x, i) => s + x * v[i], 0) /
          v.reduce((s, x) => s + x * x, 0);
      return v.map((x) => x * scale);
    }
    case "X02": {
      const A = p.A as number[][],
        b = nums(p.b);
      const det = A[0][0] * A[1][1] - A[0][1] * A[1][0];
      expect(Math.abs(det)).toBeGreaterThan(0);
      return [
        (b[0] * A[1][1] - b[1] * A[0][1]) / det,
        (A[0][0] * b[1] - A[1][0] * b[0]) / det,
      ];
    }
    case "X03": {
      const f = (x: number) =>
        item.structure.includes("reciprocal")
          ? 1 / (n("a") * x + n("b"))
          : (n("a") * x + n("b")) ** 2;
      const h = 1e-5;
      return [(f(n("x") + h) - f(n("x") - h)) / (2 * h)];
    }
    case "X04": {
      const joint = n("prior") * n("sensitivity"),
        positive = joint + (1 - n("prior")) * n("falsePositive");
      return [joint / positive];
    }
    case "X05": {
      const x = nums(p.x),
        y = nums(p.y),
        N = x.length;
      const population =
        x.reduce((s, v, i) => s + v * y[i], 0) / N -
        (x.reduce((s, v) => s + v, 0) / N) * (y.reduce((s, v) => s + v, 0) / N);
      return [(population * N) / n("denominator")];
    }
    case "X06": {
      const factor = 1 - n("k") * n("h"),
        steady = n("u") / n("k");
      const at = (i: number) => steady + (n("y") - steady) * factor ** i;
      return p.steps === 2 ? [at(1), at(2)] : [at(1)];
    }
    case "X07": {
      const v = nums(p.values);
      const m = v.reduce((s, x) => s + x / v.length, 0);
      return [m];
    }
    case "X08": {
      if (p.mean !== undefined) {
        // Apply stored training-only statistics to the held-out sample.
        const x = nums(p.heldOut),
          m = nums(p.mean),
          sd = nums(p.std);
        return x.map((v, j) => (v - m[j]) / sd[j]);
      }
      if (p.layout === "feature-major")
        return (p.training as unknown[][]).map(
          (r) => nums(r).reduce((s, v) => s + v, 0) / r.length,
        );
      const rows = (p.rows ?? p.pixels) as number[][];
      return [0, 1, 2].map(
        (j) => rows.reduce((s, r) => s + r[j], 0) / rows.length,
      );
    }
    case "X09": {
      // A test kills the mutant when the correct and mutant outputs differ.
      const angle = (v: unknown) => {
        const m = /^(-?)(?:(\d+(?:\.\d+)?)\*?)?pi(?:\/(\d+))?$/.exec(String(v));
        if (!m) return value(v);
        const k = m[2] ? Number(m[2]) : 1;
        return ((m[1] ? -1 : 1) * k * Math.PI) / (m[3] ? Number(m[3]) : 1);
      };
      const project = (u: number[], v: number[]) => {
        const scale = (u[0] * v[0] + u[1] * v[1]) / (v[0] ** 2 + v[1] ** 2);
        return v.map((x) => x * scale);
      };
      const rotate = (t: number, d: number[]) => [
        Math.cos(t) * d[0] - Math.sin(t) * d[1],
        Math.sin(t) * d[0] + Math.cos(t) * d[1],
      ];
      const pair = (c: Inputs): [number[], number[]] => {
        switch (p.mutant) {
          case "zero-output":
            return [project(nums(c.u), nums(c.v)), [0, 0]];
          case "divide-by-norm": {
            const u = nums(c.u),
              v = nums(c.v),
              norm = Math.hypot(v[0], v[1]);
            return [
              project(u, v),
              v.map((x) => (x * (u[0] * v[0] + u[1] * v[1])) / norm),
            ];
          }
          case "swapped-arguments":
            return [
              project(nums(c.u), nums(c.v)),
              project(nums(c.v), nums(c.u)),
            ];
          case "orientation-zero":
            return [[angle(c.q1) + angle(c.q2)], [0]];
          case "direction-translated": {
            const r = rotate(angle(c.theta), nums(c.direction)),
              t = nums(c.translation);
            return [r, [r[0] + t[0], r[1] + t[1]]];
          }
          case "determinant-only": {
            const [[a, b], [cc, d]] = c.R as number[][];
            const det = a * d - b * cc,
              orthonormal =
                Math.abs(a * a + cc * cc - 1) < 1e-12 &&
                Math.abs(b * b + d * d - 1) < 1e-12 &&
                Math.abs(a * b + cc * d) < 1e-12;
            const unit = Math.abs(det - 1) < 1e-12;
            return [[orthonormal && unit ? 1 : 0], [unit ? 1 : 0]];
          }
        }
        throw new Error("Unknown X09 mutant " + String(p.mutant));
      };
      const kills = ["A", "B"].filter((k) => {
        const [good, bad] = pair(p[k] as Inputs);
        return good.some((g, i) => Math.abs(g - bad[i]) > 1e-9);
      });
      expect(kills, item.id).toHaveLength(1);
      return kills;
    }
    case "X10": {
      if (item.objectiveId.includes("frame-labels"))
        return [
          item.structure.includes("warehouse")
            ? "inverse(T_WS)"
            : p.query === "forward"
              ? "T_AB"
              : "T_BA",
        ];
      if (item.objectiveId.includes("point-vs-direction")) {
        const a = p.theta === "pi/2" ? Math.PI / 2 : n("theta"),
          v = nums(p.vector ?? p.point),
          t = nums(p.translation);
        const q = [
          Math.cos(a) * v[0] - Math.sin(a) * v[1],
          Math.sin(a) * v[0] + Math.cos(a) * v[1],
        ];
        return [q[0] + t[0], q[1] + t[1], ...q];
      }
      if (item.objectiveId.includes("rotation-validity")) {
        const R = p.R as number[][],
          a = R[0][0],
          b = R[0][1],
          c = R[1][0],
          d = R[1][1];
        const valid =
          Math.abs(a * a + c * c - 1) < 1e-9 &&
          Math.abs(b * b + d * d - 1) < 1e-9 &&
          Math.abs(a * b + c * d) < 1e-9 &&
          Math.abs(a * d - b * c - 1) < 1e-9;
        return [valid ? "yes" : "no"];
      }
      if (item.structure.includes("inverse.matrix")) {
        const a = n("theta"),
          c = Math.cos(a),
          s = Math.sin(a),
          [x, y] = nums(p.translation);
        return [c, s, -c * x - s * y, -s, c, s * x - c * y, 0, 0, 1];
      }
      const A = p.A as { translation: number[] },
        B = p.B as { translation: number[] };
      return [
        A.translation[0] - B.translation[1],
        A.translation[1] + B.translation[0],
      ];
    }
    case "X11": {
      // Rotate the local endpoint [l1+l2*cos(q2), l2*sin(q2)] by q1,
      // independently of the authoring script's summed absolute-angle formula.
      const a = n("q1"),
        b = n("q2"),
        t = a + b,
        local = [n("l1") + n("l2") * Math.cos(b), n("l2") * Math.sin(b)];
      const x = Math.cos(a) * local[0] - Math.sin(a) * local[1],
        y = Math.sin(a) * local[0] + Math.cos(a) * local[1];
      return item.fields.length === 9
        ? [Math.cos(t), -Math.sin(t), x, Math.sin(t), Math.cos(t), y, 0, 0, 1]
        : [x, y, t];
    }
    case "X12": {
      const theta0 = p.theta0 === undefined ? 0 : n("theta0"),
        x0 = p.x0 === undefined ? 0 : n("x0"),
        y0 = p.y0 === undefined ? 0 : n("y0");
      const angle = ((n("vr") - n("vl")) / n("b")) * n("dt"),
        distance = ((n("vl") + n("vr")) / 2) * n("dt");
      const sinc =
        Math.abs(angle) < 1e-8
          ? 1 - (angle * angle) / 6
          : Math.sin(angle) / angle;
      const cosc = angle === 0 ? 0 : (2 * Math.sin(angle / 2) ** 2) / angle;
      const dx = distance * sinc,
        dy = distance * cosc;
      return [
        x0 + Math.cos(theta0) * dx - Math.sin(theta0) * dy,
        y0 + Math.sin(theta0) * dx + Math.cos(theta0) * dy,
        theta0 + angle,
      ];
    }
    case "X13": {
      const raw = n("kp") * (n("r") - n("y")),
        u = Math.min(n("limit"), Math.max(-n("limit"), raw));
      return [u, n("y") + n("h") * u];
    }
    case "X14": {
      const result = shortest(
        p.edges as [string, string, number][],
        String(p.start),
        String(p.goal),
      );
      return [Number.isFinite(result) ? result : -1];
    }
    case "X15": {
      const a = nums(p.start),
        b = nums(p.end),
        c = nums(p.center),
        dx = b[0] - a[0],
        dy = b[1] - a[1],
        len = Math.hypot(dx, dy);
      if (!len) return [Math.hypot(c[0] - a[0], c[1] - a[1])];
      const dot = (c[0] - a[0]) * dx + (c[1] - a[1]) * dy;
      if (dot < 0) return [Math.hypot(c[0] - a[0], c[1] - a[1])];
      if (dot > len * len) return [Math.hypot(c[0] - b[0], c[1] - b[1])];
      return [Math.abs(dx * (c[1] - a[1]) - dy * (c[0] - a[0])) / len];
    }
    case "X16":
      return [
        n("fx") * (n("X") / n("Z")) + n("cx"),
        n("fy") * (n("Y") / n("Z")) + n("cy"),
      ];
    case "X17": {
      const f = (w: number) => {
        const a = w * n("x"),
          b = item.structure.includes("shared-product") ? w * a : w + a;
        return 0.5 * (b - (p.target === undefined ? 0 : n("target"))) ** 2;
      };
      const h = 1e-5;
      return [(f(n("w") + h) - f(n("w") - h)) / (2 * h)];
    }
    case "X18":
      return [
        p.nextValue === undefined
          ? n("reward") / (1 - n("gamma"))
          : n("reward") + (p.terminal ? 0 : n("gamma") * n("nextValue")),
      ];
    case "X19": {
      const group = (id: string) =>
        p.groupBy === "person" ? id.split("/")[0] : id;
      const train = new Set((p.train as string[]).map(group));
      return [
        (p.test as string[]).some((id) => train.has(group(id))) ? "yes" : "no",
      ];
    }
    case "X20": {
      let energy = n("energy"),
        holding = p.holding === undefined ? true : !!p.holding;
      const required =
        p.deliveryCost === undefined ? n("required") : n("deliveryCost");
      for (const action of p.plan as string[]) {
        if (action === "recharge") {
          if (p.atBase === false) return ["no"];
          energy = n("rechargeEnergy");
        } else if (action === "deliver") {
          if (!holding || energy < required) return ["no"];
          energy -= required;
          holding = false;
        } else return ["no"];
      }
      return ["yes"];
    }
    default:
      throw new Error("Missing oracle for " + familyId);
  }
}
for (const f of catalog().families.filter((f) => /^X\d+$/.test(f.id))) {
  it(
    f.id +
      " has checked numerical/reasoning outputs and rejects a wrong field on both routes",
    () => {
      expect(f.routes).toHaveLength(2);
      for (const item of f.items) {
        const expected = oracle(f.id, item);
        expect(expected, item.id).toHaveLength(item.fields.length);
        const answers = Object.fromEntries(
          expected.map((x, i) => [
            String(i),
            typeof x === "number" ? x.toFixed(9) : x,
          ]),
        );
        expect(gradeItem(item, answers).passed, item.id).toBe(true);
        for (const [i, field] of item.fields.entries()) {
          const bad = {
            ...answers,
            [String(i)]:
              field.kind === "choice"
                ? field.options!.find((o) => o !== expected[i])!
                : (Number(expected[i]) + 1).toFixed(9),
          };
          expect(gradeItem(item, bad).passed, item.id + " field " + i).toBe(
            false,
          );
        }
      }
    },
  );
}
it("retains immutable v1 contracts for resumed history", () => {
  for (let i = 1; i <= 20; i++) {
    const id = "X" + String(i).padStart(2, "0");
    const current = family(id)!.version;
    expect(current).toBeGreaterThanOrEqual(2);
    for (let v = 1; v < current; v++)
      expect(family(id, v)?.version, id + "@" + v).toBe(v);
  }
});

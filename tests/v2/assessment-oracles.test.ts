import { expect, it } from "vitest";
import { cmSources } from "../../lib/v2/assessments";
import { gradeItem } from "../../lib/v2/content";
// Parse the authored angle text independently, check the stored cos/sin
// against it, then derive everything from the angle.
function rotation(p: Record<string, unknown>): [number, number] {
  const text = String(p.theta);
  const atan = /^atan2\((-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)\)$/.exec(text);
  const pi = /^(-?)(\d+)?\*?pi(?:\/(\d+))?$/.exec(text);
  let theta: number;
  if (atan) theta = Math.atan2(Number(atan[1]), Number(atan[2]));
  else if (pi)
    theta =
      ((pi[1] ? -1 : 1) * Number(pi[2] ?? 1) * Math.PI) / Number(pi[3] ?? 1);
  else if (/^-?\d+(\.\d+)?$/.test(text)) theta = Number(text);
  else throw new Error("Unparsed angle " + text);
  expect(Math.abs(Math.cos(theta) - Number(p.cos)), text).toBeLessThan(1e-12);
  expect(Math.abs(Math.sin(theta) - Number(p.sin)), text).toBeLessThan(1e-12);
  return [Math.cos(theta), Math.sin(theta)];
}
for (const source of cmSources())
  it(
    source.id +
      " numerical form/retrieval items agree with independent scalar checks",
    () => {
      for (const variant of source.variants)
        for (const { task, dimension } of variant.items) {
          if (dimension !== "M") continue;
          const p = task.inputs;
          let expected: number[];
          switch (task.structure) {
            case "point-direction.apply@1": {
              const [c, sn] = rotation(p),
                [tx, ty] = p.translation as number[],
                point = p.point as number[],
                [x, y] = p.vector as number[];
              expected = [
                c * point[0] - sn * point[1] + tx,
                sn * point[0] + c * point[1] + ty,
                c * x - sn * y,
                sn * x + c * y,
              ];
              break;
            }
            case "se2.compose.translation@1": {
              const a = p.A as Record<string, unknown>,
                b = p.B as Record<string, unknown>;
              const [c, sn] = rotation(a),
                ta = a.translation as number[],
                tb = b.translation as number[];
              rotation(b);
              expected = [
                ta[0] + c * tb[0] - sn * tb[1],
                ta[1] + sn * tb[0] + c * tb[1],
              ];
              break;
            }
            case "se2.inverse.point@1": {
              const [c, sn] = rotation(p),
                t = p.translation as number[],
                point = p.point as number[];
              const d = [point[0] - t[0], point[1] - t[1]];
              expected = [c * d[0] + sn * d[1], -sn * d[0] + c * d[1]];
              break;
            }
            case "rotation.invariants@1": {
              const r = p.R as number[][];
              expected = [
                r[0][0] * r[1][1] - r[0][1] * r[1][0],
                r[0][1] ** 2 + r[1][1] ** 2,
              ];
              break;
            }
            case "planar-2r.pose@1": {
              const a = Number(p.q1),
                b = Number(p.q2),
                l1 = Number(p.l1),
                l2 = Number(p.l2);
              const local = [l1 + l2 * Math.cos(b), l2 * Math.sin(b)];
              expected = [
                Math.cos(a) * local[0] - Math.sin(a) * local[1],
                Math.sin(a) * local[0] + Math.cos(a) * local[1],
                a + b,
              ];
              break;
            }
            default:
              throw new Error(
                "No independent numerical check for " + task.structure,
              );
          }
          expect(expected).toHaveLength(task.fields.length);
          const answers = Object.fromEntries(
            expected.map((v, i) => [String(i), v.toFixed(9)]),
          );
          expect(gradeItem(task, answers).passed, task.id).toBe(true);
          for (let i = 0; i < expected.length; i++)
            expect(
              gradeItem(task, {
                ...answers,
                [String(i)]: (expected[i] + 0.1).toFixed(9),
              }).passed,
              task.id,
            ).toBe(false);
        }
    },
  );

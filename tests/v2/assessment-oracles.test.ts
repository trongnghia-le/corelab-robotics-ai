import { expect, it } from "vitest";
import { cmSources } from "../../lib/v2/assessments";
import { gradeItem } from "../../lib/v2/content";
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
              const [tx, ty] = p.translation as number[],
                [x, y] = p.vector as number[];
              expected = [tx - y, ty + x, -y, x];
              break;
            }
            case "se2.compose.translation@1": {
              const a = p.A as { translation: number[] },
                b = p.B as { translation: number[] };
              expected = [
                a.translation[0] - b.translation[1],
                a.translation[1] + b.translation[0],
              ];
              break;
            }
            case "se2.inverse.point@1": {
              const t = p.translation as number[],
                point = p.point as number[];
              expected = [point[1] - t[1], t[0] - point[0]];
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

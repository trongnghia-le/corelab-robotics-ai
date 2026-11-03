import { describe, expect, it } from "vitest";
import { layoutGraph } from "../lib/graph-layout";
import { topics, topicMap } from "../lib/curriculum";

// The graph view shows one domain plus the prerequisites it needs.
function domainView(domain: string) {
  const ids = new Set(
    topics
      .filter((t) => t.domain === domain)
      .flatMap((t) => [t.id, ...t.prerequisites]),
  );
  return [...ids].map((id) => ({
    id,
    prerequisites: topicMap[id].prerequisites,
  }));
}

function crossings(
  items: { id: string; prerequisites: string[] }[],
  pos: Map<string, { x: number; y: number }>,
) {
  const edges = items.flatMap((i) =>
    i.prerequisites.filter((p) => pos.has(p)).map((p) => [p, i.id]),
  );
  let n = 0;
  for (let a = 0; a < edges.length; a++)
    for (let b = a + 1; b < edges.length; b++) {
      const [s1, t1] = edges[a].map((id) => pos.get(id)!);
      const [s2, t2] = edges[b].map((id) => pos.get(id)!);
      if (s1.x !== s2.x || t1.x !== t2.x) continue;
      if ((s1.y - s2.y) * (t1.y - t2.y) < 0) n++;
    }
  return n;
}

describe("graph layout", () => {
  const domains = [...new Set(topics.map((t) => t.domain))];

  it("puts every prerequisite in an earlier column and never overlaps cards", () => {
    for (const domain of domains) {
      const items = domainView(domain);
      const placed = layoutGraph(items);
      const at = new Map(placed.map((p) => [p.id, p]));
      for (const { id, prerequisites } of items)
        for (const p of prerequisites.filter((p) => at.has(p)))
          expect(at.get(p)!.column).toBeLessThan(at.get(id)!.column);
      const height = (id: string) => 100 + (id.charCodeAt(1) % 3) * 30;
      const stacked = layoutGraph(items, { gap: 20, height });
      const columns = new Map<number, typeof stacked>();
      for (const p of stacked)
        columns.set(p.column, [...(columns.get(p.column) ?? []), p]);
      for (const col of columns.values()) {
        col.sort((a, b) => a.y - b.y);
        for (let i = 1; i < col.length; i++)
          expect(col[i].y).toBeGreaterThanOrEqual(
            col[i - 1].y + height(col[i - 1].id) + 20 - 1e-9,
          );
      }
    }
  });

  it("orders columns with fewer crossings than alphabetical order", () => {
    let ordered = 0;
    let naive = 0;
    for (const domain of domains) {
      const items = domainView(domain);
      const placed = layoutGraph(items);
      ordered += crossings(
        items,
        new Map(placed.map((p) => [p.id, { x: p.column, y: p.y }])),
      );
      const rows: Record<number, number> = {};
      naive += crossings(
        items,
        new Map(
          [...placed]
            .sort((a, b) => a.id.localeCompare(b.id))
            .map((p) => [
              p.id,
              { x: p.column, y: (rows[p.column] = (rows[p.column] ?? -1) + 1) },
            ]),
        ),
      );
    }
    expect(ordered).toBeLessThan(naive);
  });

  it("tolerates an empty view", () => {
    expect(layoutGraph([])).toEqual([]);
  });
});

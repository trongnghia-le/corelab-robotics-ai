// Layered left-to-right layout for the prerequisite graph: each topic sits one
// column right of its latest prerequisite, and columns are ordered by the
// barycenter heuristic so arrows cross as little as possible.

export type LayoutInput = { id: string; prerequisites: string[] }[];
/** `y` is the top edge; cards in a column are stacked by their heights. */
export type Placed = { id: string; column: number; y: number };

export function layoutGraph(
  items: LayoutInput,
  {
    gap = 24,
    height = () => 140,
  }: { gap?: number; height?: (id: string) => number } = {},
): Placed[] {
  const ids = new Set(items.map((i) => i.id));
  const preds = new Map<string, string[]>();
  const succs = new Map<string, string[]>();
  for (const { id } of items) {
    preds.set(id, []);
    succs.set(id, []);
  }
  for (const { id, prerequisites } of items)
    for (const p of prerequisites)
      if (ids.has(p) && p !== id) {
        preds.get(id)!.push(p);
        succs.get(p)!.push(id);
      }

  // Longest path from the sources, using only edges shown in this view.
  const column = new Map<string, number>();
  const visiting = new Set<string>();
  const col = (id: string): number => {
    if (column.has(id)) return column.get(id)!;
    if (visiting.has(id)) return 0; // cycles are rejected by validation; stay safe
    visiting.add(id);
    const c = Math.max(-1, ...preds.get(id)!.map(col)) + 1;
    visiting.delete(id);
    column.set(id, c);
    return c;
  };
  items.forEach((i) => col(i.id));
  // Pull sources right next to their first dependant so arrows stay short.
  for (const { id } of items)
    if (!preds.get(id)!.length && succs.get(id)!.length)
      column.set(
        id,
        Math.min(...succs.get(id)!.map((s) => column.get(s)!)) - 1,
      );

  const layers: string[][] = [];
  for (const { id } of [...items].sort((a, b) => a.id.localeCompare(b.id)))
    (layers[column.get(id)!] ??= []).push(id);
  for (let i = 0; i < layers.length; i++) layers[i] ??= [];

  // y holds each card's vertical centre while ordering.
  const y = new Map<string, number>();
  const h = new Map(items.map(({ id }) => [id, height(id)]));
  const place = (layer: string[]) => {
    const total =
      layer.reduce((n, id) => n + h.get(id)!, 0) +
      gap * Math.max(0, layer.length - 1);
    let top = -total / 2;
    for (const id of layer) {
      y.set(id, top + h.get(id)! / 2);
      top += h.get(id)! + gap;
    }
  };
  layers.forEach(place);
  const reorder = (layer: string[], neighbours: Map<string, string[]>) => {
    const key = (id: string) => {
      const n = neighbours.get(id)!;
      return n.length
        ? n.reduce((s, m) => s + y.get(m)!, 0) / n.length
        : y.get(id)!;
    };
    const keys = new Map(layer.map((id) => [id, key(id)]));
    layer.sort((a, b) => keys.get(a)! - keys.get(b)!);
    place(layer);
  };
  // Alternate forward and backward sweeps; a few passes settle the order.
  for (let pass = 0; pass < 6; pass++) {
    if (pass % 2 === 0)
      for (let i = 1; i < layers.length; i++) reorder(layers[i], preds);
    else for (let i = layers.length - 2; i >= 0; i--) reorder(layers[i], succs);
  }

  return items.map(({ id }) => ({
    id,
    column: column.get(id)!,
    y: y.get(id)! - h.get(id)! / 2,
  }));
}

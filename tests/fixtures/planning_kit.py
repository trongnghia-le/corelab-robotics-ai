"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (heap, list-scan and reopening A*, several
exact segment tests) that must pass, and named injected bugs that must be rejected.
Plain checks only, so it also works under python -O.
"""
import ast
import heapq
import importlib.util
import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('planning_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L11-planning.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math', 'fractions'}, 'kit imports beyond math/fractions: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
names = ('heuristic', 'astar_grid', 'plan_with_budget', 'segment_hits_rect', 'first_blocked_segment')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _dijkstra') > spoiler and text.index('def _hit_exact') > spoiler
        and text.index('_A_CASES =') > spoiler, 'oracle and tables must sit below the banner')
spec = importlib.util.spec_from_file_location('planning_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check([])
require(starter and len(starter) == 5 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))
require(all(f.isascii() for f in starter), 'starter messages must be ASCII')

# ---- samples manifest mirrors every hand-written positive case ----


def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def encode(value):
    return [encode(v) for v in value] if isinstance(value, (list, tuple)) else dec(value)


def entry(structure, keys, args):
    return {'structure': structure, 'inputs': {k: encode(v) for k, v in zip(keys, args)}}


expected = (
    [entry('planning.heuristic@1', ('cell', 'goal', 'connectivity'), a) for a, _ in kit._H_CASES]
    + [entry('planning.astar@1', ('grid', 'start', 'goal', 'connectivity', 'weight'),
             (kit._grid(c[0]),) + tuple(c[1:5])) for c in kit._A_CASES]
    + [entry('planning.budget@1', ('grid', 'start', 'goal', 'connectivity', 'max_expansions'),
             (kit._grid(c[0]),) + tuple(c[1:5])) for c in kit._B_CASES]
    + [entry('planning.segment-rect@1', ('p', 'q', 'rect'), a) for a, _ in kit._S_CASES]
    + [entry('planning.path-sweep@1', ('points', 'rects', 'half_width'), a) for a, _ in kit._P_CASES])
samples = json.loads((root / 'content/labs/L11-planning.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1', 'samples schema')
require(list(samples['kits']) == ['L11-planning'], 'samples must hold only L11-planning')
require(samples['kits']['L11-planning'] == expected, 'samples manifest does not mirror the self-check cases')
require(len(expected) <= 50, 'kit sample cap is 50')

# ---- independent cross-checks of the hand tables ----


def edges_hit(p, q, rect):
    """Independent segment-vs-rectangle test: endpoint inside or any edge crossed."""
    P, Q = [Fraction(v) for v in p], [Fraction(v) for v in q]
    x0, y0, x1, y1 = [Fraction(v) for v in rect]

    def inside(a):
        return x0 <= a[0] <= x1 and y0 <= a[1] <= y1

    def orient(a, b, c):
        v = (b[0] - a[0])*(c[1] - a[1]) - (b[1] - a[1])*(c[0] - a[0])
        return (v > 0) - (v < 0)

    def on(a, b, c):
        return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])

    def cross(a, b, c, d):
        o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
        if o1 != o2 and o3 != o4:
            return True
        return ((o1 == 0 and on(a, b, c)) or (o2 == 0 and on(a, b, d))
                or (o3 == 0 and on(c, d, a)) or (o4 == 0 and on(c, d, b)))

    if inside(P) or inside(Q):
        return True
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return any(cross(P, Q, corners[i], corners[(i + 1) % 4]) for i in range(4))


for args, want in kit._S_CASES:
    require(kit._hit_exact(*args) == want == edges_hit(*args), 'segment hand table: ' + repr(args))
for args, want in kit._random_segments(150, 4242):
    require(edges_hit(*args) == want, 'random segment oracle disagrees with the edge test')
for args, want in kit._P_CASES:
    require(kit._first_blocked_ref(*args) == want, 'sweep hand table: ' + repr(args))
for (rows, s, g, c, w, hand) in kit._A_CASES:
    d = kit._dijkstra(kit._grid(rows), s, c)
    if hand == 'none':
        require(g not in d, 'hand unreachable case is reachable')
    elif isinstance(hand, float):
        require(abs(d[g] - hand) <= 1e-9, 'hand cost table disagrees with Dijkstra: ' + repr(rows))
# BFS cross-check of the oracle for 4-connected unit costs
for grid, s, g in kit._random_grids(40, 5):
    seen = {s: 0}
    queue = [s]
    for cell in queue:
        for nb, _ in kit._steps(grid, cell, 4):
            if nb not in seen:
                seen[nb] = seen[cell] + 1
                queue.append(nb)
    d = kit._dijkstra(grid, s, 4)
    require(set(d) == set(seen) and all(abs(d[k] - seen[k]) < 1e-9 for k in d), 'BFS disagrees with Dijkstra')
# the coverage of the budget table
cats = set()
for rows, s, g, c, b in kit._B_CASES:
    cats.add(tuple(sorted(kit._allowed(kit._grid(rows), s, g, c, b))))
require(cats == {('found',), ('budget_exhausted',), ('unreachable',)}, 'budget table coverage: ' + str(cats))

# ---- author reference implementation ----
SQRT2 = math.sqrt(2.0)


def is_num(v, lo, hi):
    return type(v) in (int, float) and math.isfinite(v) and lo <= v <= hi


def v_cell(c, bound=1000):
    if not isinstance(c, (list, tuple)) or len(c) != 2 or any(type(v) is not int or abs(v) > bound for v in c):
        raise ValueError
    return (c[0], c[1])


def v_conn(c):
    if type(c) is not int or c not in (4, 8):
        raise ValueError
    return c


def v_grid(g):
    if not isinstance(g, (list, tuple)) or not 1 <= len(g) <= 12:
        raise ValueError
    cols = None
    for row in g:
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 12:
            raise ValueError
        if cols is None:
            cols = len(row)
        if len(row) != cols or any(type(v) is not int or v not in (0, 1) for v in row):
            raise ValueError
    return [list(r) for r in g]


def v_task(grid, start, goal, conn):
    g = v_grid(grid)
    s, e = v_cell(start), v_cell(goal)
    v_conn(conn)
    for r, c in (s, e):
        if not (0 <= r < len(g) and 0 <= c < len(g[0])) or g[r][c] != 0:
            raise ValueError
    return g, s, e


def v_weight(w):
    if not is_num(w, 1, 10):
        raise ValueError


def v_budget(b):
    if type(b) is not int or not 0 <= b <= 10000:
        raise ValueError


def octile(dr, dc, conn):
    dr, dc = abs(dr), abs(dc)
    return float(dr + dc) if conn == 4 else max(dr, dc) + (SQRT2 - 1.0)*min(dr, dc)


def heuristic(cell, goal, connectivity):
    a, b = v_cell(cell), v_cell(goal)
    v_conn(connectivity)
    return octile(a[0] - b[0], a[1] - b[1], connectivity)


class Opts:
    corner = 'both'
    diag = SQRT2
    hfun = staticmethod(octile)
    conn = None
    close_on_push = False
    stop_on_generate = False
    greedy = False
    wrap = False
    unreachable = None
    cost_mode = 'ok'
    path_mode = 'ok'
    same = 'ok'
    tie = 'fifo'
    reopen = False
    budget_mode = 'ok'


def make_opts(**kw):
    o = Opts()
    for k, v in kw.items():
        setattr(o, k, v)
    return o


DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))


def neighbours(g, cell, conn, o):
    rows, cols = len(g), len(g[0])
    r, c = cell
    use = o.conn or conn
    for dr, dc in DIRS:
        if use == 4 and dr and dc:
            continue
        nr, nc = r + dr, c + dc
        if o.wrap:
            if nr >= rows or nc >= cols:
                continue
        elif not (0 <= nr < rows and 0 <= nc < cols):
            continue
        if g[nr][nc]:
            continue
        if dr and dc:
            a, b = g[r + dr][c] if (o.wrap or 0 <= r + dr < rows) else 1, g[r][c + dc]
            if o.corner == 'both' and (a or b):
                continue
            if o.corner == 'one' and a and b:
                continue
            if o.corner == 'wrong' and g[nr][nc]:
                continue
        yield (nr, nc), (o.diag if dr and dc else 1.0)


def search(g, s, e, conn, weight, o, budget=None):
    """Returns ('found', cost, path) / ('unreachable',) / ('budget_exhausted',)."""
    if s == e:
        return ('found', 0.0, [s]) if o.same == 'ok' else ('unreachable',)
    gs, parent, closed, count = {s: 0.0}, {}, set(), 0
    h = o.hfun
    use = o.conn or conn

    def prio(cell, gv):
        hv = h(cell[0] - e[0], cell[1] - e[1], use)
        return hv if o.greedy else gv + weight*hv

    serial = 0
    heap = [(prio(s, 0.0), 0, s)]
    while True:
        while heap and heap[0][2] in closed:
            heapq.heappop(heap)
        if not heap:
            return ('unreachable',)
        _, _, cell = heapq.heappop(heap)
        if cell == e:
            break
        if budget is not None and count == budget:
            return ('budget_exhausted',)
        closed.add(cell)
        count += 1
        for nb, cost in neighbours(g, cell, conn, o):
            ng = gs[cell] + cost
            if nb in closed and not o.reopen:
                continue
            if nb in gs and (o.close_on_push or ng >= gs[nb] - 1e-12):
                continue
            gs[nb], parent[nb] = ng, cell
            closed.discard(nb)
            serial += 1
            tie = serial if o.tie == 'fifo' else -serial
            if o.tie == 'g':
                tie = -ng
            heapq.heappush(heap, (prio(nb, ng), tie, nb))
            if o.stop_on_generate and nb == e:
                cell = nb
                gs[e] = ng
                return finish(e, parent, gs, o)
    return finish(e, parent, gs, o)


def finish(e, parent, gs, o):
    path = [e]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    path.reverse()
    cost = gs[e]
    if o.cost_mode == 'dropfirst':
        cost = gs[parent[e]] if e in parent else 0.0
    if o.path_mode == 'nostart':
        path = path[1:]
    if o.path_mode == 'reversed':
        path.reverse()
    return ('found', float(cost), path)


def make_astar(o=None, ret=tuple):
    o = o or Opts()

    def astar_grid(grid, start, goal, connectivity, weight=1.0):
        g, s, e = v_task(grid, start, goal, connectivity)
        v_weight(weight)
        out = search(g, s, e, connectivity, weight, o)
        if out[0] != 'found':
            return o.unreachable
        return (out[1], ret(ret(c) for c in out[2]))
    return astar_grid


def make_budget(o=None, shift=0, ret=list):
    o = o or Opts()

    def plan_with_budget(grid, start, goal, connectivity, max_expansions):
        g, s, e = v_task(grid, start, goal, connectivity)
        v_budget(max_expansions)
        b = max_expansions + shift
        out = search(g, s, e, connectivity, 1.0, o, budget=max(b, 0))
        if out[0] == 'found':
            return ('found', out[1], ret(ret(c) for c in out[2]))
        if o.budget_mode == 'exhausted_as_unreachable' and out[0] == 'budget_exhausted':
            return ('unreachable', None, None)
        if o.budget_mode == 'never_unreachable' and out[0] == 'unreachable':
            return ('budget_exhausted', None, None)
        if o.budget_mode == 'partial' and out[0] == 'budget_exhausted':
            return ('budget_exhausted', 0.0, [s])
        return (out[0], None, None)
    return plan_with_budget


# ---- segment tests (all exact on dyadic data) ----
def v_pt(p):
    if not isinstance(p, (list, tuple)) or len(p) != 2 or any(not is_num(v, -1000, 1000) for v in p):
        raise ValueError
    return (p[0], p[1])


def v_rect(r):
    if not isinstance(r, (list, tuple)) or len(r) != 4 or any(not is_num(v, -1000, 1000) for v in r):
        raise ValueError
    if r[0] > r[2] or r[1] > r[3]:
        raise ValueError
    return tuple(r)


def seg_rule(rule):
    def segment_hits_rect(p, q, rect):
        return rule(v_pt(p), v_pt(q), v_rect(rect))
    return segment_hits_rect


def slab(p, q, r):
    lo, hi = 0.0, 1.0
    for a, d, l, h in ((p[0], q[0] - p[0], r[0], r[2]), (p[1], q[1] - p[1], r[1], r[3])):
        if d == 0:
            if a < l or a > h:
                return False
        else:
            t1, t2 = (l - a)/d, (h - a)/d
            lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
            if lo > hi:
                return False
    return True


def sat(p, q, r):
    if max(p[0], q[0]) < r[0] or min(p[0], q[0]) > r[2]:
        return False
    if max(p[1], q[1]) < r[1] or min(p[1], q[1]) > r[3]:
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    cx, cy = (r[0] + r[2])/2 - p[0], (r[1] + r[3])/2 - p[1]
    ex, ey = (r[2] - r[0])/2, (r[3] - r[1])/2
    return abs(dx*cy - dy*cx) <= abs(dx)*ey + abs(dy)*ex


def code(x, y, r):
    return (x < r[0]) | ((x > r[2]) << 1) | ((y < r[1]) << 2) | ((y > r[3]) << 3)


def cohen(p, q, r):
    x0, y0, x1, y1 = p[0], p[1], q[0], q[1]
    for _ in range(10):
        c0, c1 = code(x0, y0, r), code(x1, y1, r)
        if not (c0 | c1):
            return True
        if c0 & c1:
            return False
        c = c0 or c1
        if c & 8:
            x, y = x0 + (x1 - x0)*(r[3] - y0)/(y1 - y0), r[3]
        elif c & 4:
            x, y = x0 + (x1 - x0)*(r[1] - y0)/(y1 - y0), r[1]
        elif c & 2:
            x, y = r[2], y0 + (y1 - y0)*(r[2] - x0)/(x1 - x0)
        else:
            x, y = r[0], y0 + (y1 - y0)*(r[0] - x0)/(x1 - x0)
        if c == c0:
            x0, y0 = x, y
        else:
            x1, y1 = x, y
    return False


def frac(p, q, r):
    return edges_hit(p, q, r)


def make_sweep(seg):
    def first_blocked_segment(points, rects, half_width):
        if not isinstance(points, (list, tuple)) or not 2 <= len(points) <= 50:
            raise ValueError
        pts = [v_pt(p) for p in points]
        if not isinstance(rects, (list, tuple)) or len(rects) > 50:
            raise ValueError
        rs = [v_rect(r) for r in rects]
        if not is_num(half_width, 0, 100):
            raise ValueError
        h = half_width
        for i in range(len(pts) - 1):
            for r in rs:
                if seg(pts[i], pts[i + 1], (r[0] - h, r[1] - h, r[2] + h, r[3] + h)):
                    return i
        return None
    return first_blocked_segment


def scan_search(g, s, e, conn, budget=None, lifo=True):
    """List-scan A* (no heap): linear search of the open dict."""
    if s == e:
        return ('found', 0.0, [s])
    gs, parent, open_, closed, order = {s: 0.0}, {}, {s: 0}, set(), 0
    count = 0
    while open_:
        best = None
        for cell, o in open_.items():
            f = gs[cell] + octile(cell[0] - e[0], cell[1] - e[1], conn)
            key = (round(f, 9), -o if lifo else o)
            if best is None or key < best[0]:
                best = (key, cell)
        cell = best[1]
        del open_[cell]
        if cell == e:
            path = [e]
            while path[-1] in parent:
                path.append(parent[path[-1]])
            return ('found', gs[e], path[::-1])
        if budget is not None and count >= budget:
            return ('budget_exhausted',)
        closed.add(cell)
        count += 1
        for nb, cost in neighbours(g, cell, conn, Opts()):
            if nb not in closed and (nb not in gs or gs[cell] + cost < gs[nb] - 1e-12):
                gs[nb], parent[nb] = gs[cell] + cost, cell
                order += 1
                open_[nb] = order
    return ('unreachable',)


def scan_astar(grid, start, goal, connectivity, weight=1.0):
    g, s, e = v_task(grid, start, goal, connectivity)
    v_weight(weight)
    out = scan_search(g, s, e, connectivity)
    return None if out[0] != 'found' else (out[1], [tuple(c) for c in out[2]])


def scan_budget(grid, start, goal, connectivity, max_expansions):
    g, s, e = v_task(grid, start, goal, connectivity)
    v_budget(max_expansions)
    out = scan_search(g, s, e, connectivity, max_expansions, lifo=False)
    return (out[0], out[1], out[2]) if out[0] == 'found' else (out[0], None, None)


def h_alt(cell, goal, connectivity):
    a, b = v_cell(cell), v_cell(goal)
    v_conn(connectivity)
    dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    if connectivity == 4:
        return dr + dc
    return SQRT2*min(dr, dc) + (max(dr, dc) - min(dr, dc))


def h_dijk(cell, goal, connectivity):
    a, b = v_cell(cell), v_cell(goal)
    v_conn(connectivity)
    dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    total = 0.0
    if connectivity == 8:
        d = min(dr, dc)
        total, dr, dc = d*SQRT2, dr - d, dc - d
    return total + dr + dc


refs = {'heuristic': heuristic, 'astar_grid': make_astar(), 'plan_with_budget': make_budget(),
        'segment_hits_rect': seg_rule(slab), 'first_blocked_segment': make_sweep(slab)}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


alternatives = [
    ('author: heap A*, FIFO ties, float slab clipping', {}),
    ('list-scan A* (no heap), LIFO ties, Dijkstra-style heuristic, separating-axis segment test',
     {'astar_grid': scan_astar, 'plan_with_budget': scan_budget, 'heuristic': h_dijk,
      'segment_hits_rect': seg_rule(sat), 'first_blocked_segment': make_sweep(sat)}),
    ('reopening heap A* with larger-g ties, tuple paths, Cohen-Sutherland clipping',
     {'astar_grid': make_astar(make_opts(reopen=True, tie='g')),
      'plan_with_budget': make_budget(make_opts(tie='g'), ret=tuple),
      'heuristic': h_alt, 'segment_hits_rect': seg_rule(cohen), 'first_blocked_segment': make_sweep(cohen)}),
    ('LIFO-tie heap A*, exact rational edge-crossing test',
     {'astar_grid': make_astar(make_opts(tie='lifo'), ret=list),
      'plan_with_budget': make_budget(make_opts(tie='lifo')),
      'segment_hits_rect': seg_rule(frac), 'first_blocked_segment': make_sweep(frac)}),
    ('early goal test on generation (valid for a consistent heuristic), FIFO heap budget search',
     {'astar_grid': make_astar(make_opts(stop_on_generate=True))}),
    ('mixed: scan A* with heap budget search, slab test, alternative heuristic form',
     {'astar_grid': scan_astar, 'heuristic': h_alt, 'segment_hits_rect': seg_rule(sat),
      'first_blocked_segment': make_sweep(slab)}),
    ('heap budget search with reopening (never triggered), separating-axis sweep',
     {'plan_with_budget': make_budget(make_opts(reopen=True)), 'first_blocked_segment': make_sweep(sat),
      'segment_hits_rect': seg_rule(cohen)}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result[:5]))


# ---- injected bugs ----
def accepts_when(pred, fn, value):
    def run(*a):
        return value if pred(*a) else fn(*a)
    return run


def h_rule(rule):
    def run(cell, goal, connectivity):
        a, b = v_cell(cell), v_cell(goal)
        v_conn(connectivity)
        return rule(a[0] - b[0], a[1] - b[1], connectivity)
    return run


def ast_rule(rule):
    def run(grid, start, goal, connectivity, weight=1.0):
        g, s, e = v_task(grid, start, goal, connectivity)
        v_weight(weight)
        return rule(g, s, e, connectivity, weight, grid)
    return run


def bud_rule(rule):
    def run(grid, start, goal, connectivity, max_expansions):
        g, s, e = v_task(grid, start, goal, connectivity)
        v_budget(max_expansions)
        return rule(g, s, e, connectivity, max_expansions)
    return run


def strict_slab(p, q, r):
    lo, hi = 0.0, 1.0
    for a, d, l, h in ((p[0], q[0] - p[0], r[0], r[2]), (p[1], q[1] - p[1], r[1], r[3])):
        if d == 0:
            if a <= l or a >= h:
                return False
        else:
            t1, t2 = (l - a)/d, (h - a)/d
            lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
            if lo >= hi:
                return False
    return True


def slab_range(lo_start, hi_start, guard=True, order=False, eps=0.0):
    def rule(p, q, r):
        if order:
            r = (r[0], r[2], r[1], r[3])
        r = (r[0] - eps, r[1] - eps, r[2] + eps, r[3] + eps)
        lo, hi = lo_start, hi_start
        for a, d, l, h in ((p[0], q[0] - p[0], r[0], r[2]), (p[1], q[1] - p[1], r[1], r[3])):
            if d == 0 and guard:
                if a < l or a > h:
                    return False
            else:
                t1, t2 = (l - a)/d, (h - a)/d
                lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
                if lo > hi:
                    return False
        return True
    return rule


def sampled(n):
    def rule(p, q, r):
        for i in range(n + 1):
            t = i/n
            x, y = p[0] + t*(q[0] - p[0]), p[1] + t*(q[1] - p[1])
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                return True
        return False
    return rule


def step_sampled(step):
    def rule(p, q, r):
        length = math.hypot(q[0] - p[0], q[1] - p[1])
        n = max(1, int(length/step))
        return sampled(n)(p, q, r)
    return rule


def bbox(p, q, r):
    return not (max(p[0], q[0]) < r[0] or min(p[0], q[0]) > r[2]
                or max(p[1], q[1]) < r[1] or min(p[1], q[1]) > r[3])


def line_sides(p, q, r):
    signs = []
    for cx, cy in ((r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])):
        v = (q[0] - p[0])*(cy - p[1]) - (q[1] - p[1])*(cx - p[0])
        signs.append((v > 0) - (v < 0))
    return min(signs) <= 0 <= max(signs)


def vertical_skipped(p, q, r):
    return False if p[0] == q[0] else slab(p, q, r)


def zero_len_false(p, q, r):
    return False if p == q else slab(p, q, r)


def sweep_rule(rule):
    def run(points, rects, half_width):
        if not isinstance(points, (list, tuple)) or not 2 <= len(points) <= 50:
            raise ValueError
        pts = [v_pt(p) for p in points]
        rs = [v_rect(r) for r in rects]
        if not is_num(half_width, 0, 100):
            raise ValueError
        return rule(pts, rs, half_width)
    return run


def sweep_with(grow=lambda r, h: (r[0] - h, r[1] - h, r[2] + h, r[3] + h), order='first',
               segs=None, rect_limit=None, offset=0, clear=None, wrap=lambda i: i, seg=slab):
    def rule(pts, rs, h):
        hits = []
        use = rs if rect_limit is None else rs[:rect_limit]
        rng = range(len(pts) - 1) if segs is None else segs(len(pts))
        for i in rng:
            if any(seg(pts[i], pts[i + 1], grow(r, h)) for r in use):
                hits.append(i)
        if not hits:
            return clear
        return wrap(hits[0] if order == 'first' else hits[-1]) + offset
    return rule


def waypoints_only(pts, rs, h):
    for i, p in enumerate(pts[:-1]):
        if any(slab(p, p, (r[0] - h, r[1] - h, r[2] + h, r[3] + h)) for r in rs):
            return i
    return None


def ast_nonopt(rule_opts):
    return make_astar(make_opts(**rule_opts))


def budget_cost_limit(g, s, e, c, b):
    out = search(g, s, e, c, 1.0, Opts())
    if out[0] != 'found':
        return (out[0], None, None)
    return ('found', out[1], out[2]) if out[1] <= b else ('budget_exhausted', None, None)


def budget_ignored(g, s, e, c, b):
    out = search(g, s, e, c, 1.0, Opts())
    return ('found', out[1], out[2]) if out[0] == 'found' else (out[0], None, None)


def budget_same(g, s, e, c, b):
    if s == e and b == 0:
        return ('budget_exhausted', None, None)
    out = search(g, s, e, c, 1.0, Opts(), budget=b)
    return ('found', out[1], out[2]) if out[0] == 'found' else (out[0], None, None)


def mutates_grid(g, s, e, c, w, original):
    result = refs['astar_grid'](g, s, e, c, w)
    if isinstance(original, list) and original and isinstance(original[0], list):
        original[s[0]][s[1]] = 2 - 2
        original[0].reverse()
        original[0].reverse()
        original[e[0]][e[1]] = 0
        original.append(original[-1]) if False else None
        original[0][0:1] = original[0][0:1]
        original.sort()
    return result


def manhattan(dr, dc, conn):
    return abs(dr) + abs(dc)


def scaled(k):
    return lambda dr, dc, conn: k*octile(dr, dc, conn)


mutants = [
    ('heuristic: Manhattan distance with 8-connectivity (inadmissible)', {'heuristic': h_rule(
        lambda dr, dc, c: float(abs(dr) + abs(dc)))}, 'heuristic'),
    ('heuristic: Chebyshev distance (admissible but not tight)', {'heuristic': h_rule(
        lambda dr, dc, c: float(max(abs(dr), abs(dc))))}, 'heuristic'),
    ('heuristic: Euclidean distance', {'heuristic': h_rule(lambda dr, dc, c: math.hypot(dr, dc))}, 'heuristic'),
    ('heuristic: ignores connectivity (always octile)', {'heuristic': h_rule(
        lambda dr, dc, c: octile(dr, dc, 8))}, 'heuristic'),
    ('heuristic: diagonal steps charged sqrt(2) on top of the straight part', {'heuristic': h_rule(
        lambda dr, dc, c: float(abs(dr) + abs(dc)) if c == 4 else
        max(abs(dr), abs(dc)) + SQRT2*min(abs(dr), abs(dc)))}, 'heuristic'),
    ('heuristic: missing abs (negative offsets)', {'heuristic': h_rule(
        lambda dr, dc, c: float(dr + dc) if c == 4 else max(dr, dc) + (SQRT2 - 1)*min(dr, dc))}, 'heuristic'),
    ('heuristic: rounded to an int', {'heuristic': h_rule(lambda dr, dc, c: round(octile(dr, dc, c)))}, 'heuristic'),
    ('heuristic: zero heuristic', {'heuristic': h_rule(lambda dr, dc, c: 0.0)}, 'heuristic'),
    ('astar: corner cutting allowed', {'astar_grid': ast_nonopt({'corner': 'none'})}, 'astar_grid'),
    ('astar: corner rule needs only one free side', {'astar_grid': ast_nonopt({'corner': 'one'})}, 'astar_grid'),
    ('astar: diagonal costs 1', {'astar_grid': ast_nonopt({'diag': 1.0})}, 'astar_grid'),
    ('astar: diagonal costs 2', {'astar_grid': ast_nonopt({'diag': 2.0})}, 'astar_grid'),
    ('astar: Manhattan heuristic with 8-connectivity inside the search',
     {'astar_grid': ast_nonopt({'hfun': staticmethod(manhattan)})}, 'astar_grid'),
    ('astar: greedy best-first (g ignored)', {'astar_grid': ast_nonopt({'greedy': True})}, 'astar_grid'),
    ('astar: always 8-connected', {'astar_grid': ast_nonopt({'conn': 8})}, 'astar_grid'),
    ('astar: always 4-connected', {'astar_grid': ast_nonopt({'conn': 4})}, 'astar_grid'),
    ('astar: unreachable goal returns (inf, [])', {'astar_grid': ast_nonopt(
        {'unreachable': (float('inf'), [])})}, 'astar_grid'),
    ('astar: unreachable goal returns (0.0, [start]) style placeholder', {'astar_grid': ast_nonopt(
        {'unreachable': (0.0, [])})}, 'astar_grid'),
    ('astar: reported cost omits the last step', {'astar_grid': ast_nonopt({'cost_mode': 'dropfirst'})}, 'astar_grid'),
    ('astar: path omits the start cell', {'astar_grid': ast_nonopt({'path_mode': 'nostart'})}, 'astar_grid'),
    ('astar: path returned goal-to-start', {'astar_grid': ast_nonopt({'path_mode': 'reversed'})}, 'astar_grid'),
    ('astar: start == goal gives None', {'astar_grid': ast_nonopt({'same': 'bad'})}, 'astar_grid'),
    ('astar: marks a cell final when first generated (no improvement)',
     {'astar_grid': ast_nonopt({'close_on_push': True})}, 'astar_grid'),
    ('astar: negative index wraps around the grid', {'astar_grid': ast_nonopt({'wrap': True})}, 'astar_grid'),
    ('astar: heuristic scaled by 100 regardless of weight (greedy-like, unbounded)',
     {'astar_grid': ast_nonopt({'hfun': staticmethod(scaled(100.0))})}, 'astar_grid'),
    ('astar: path cells returned as floats', {'astar_grid': lambda *a: (lambda r: None if r is None else
                                                                      (r[0], [(float(x), float(y)) for x, y in r[1]]))(
        refs['astar_grid'](*a))}, 'astar_grid'),
    ('astar: modifies the input grid', {'astar_grid': ast_rule(mutates_grid)}, 'astar_grid'),
    ('plan: budget exhaustion reported as unreachable', {'plan_with_budget': make_budget(
        make_opts(budget_mode='exhausted_as_unreachable'))}, 'plan_with_budget'),
    ('plan: never reports unreachable', {'plan_with_budget': make_budget(
        make_opts(budget_mode='never_unreachable'))}, 'plan_with_budget'),
    ('plan: one expansion too many allowed', {'plan_with_budget': make_budget(shift=1)}, 'plan_with_budget'),
    ('plan: one expansion too few allowed', {'plan_with_budget': make_budget(shift=-1)}, 'plan_with_budget'),
    ('plan: partial path returned with budget_exhausted', {'plan_with_budget': make_budget(
        make_opts(budget_mode='partial'))}, 'plan_with_budget'),
    ('plan: zero heuristic (Dijkstra) uses more expansions than A*', {'plan_with_budget': make_budget(
        make_opts(hfun=staticmethod(lambda dr, dc, c: 0.0)))}, 'plan_with_budget'),
    ('plan: greedy search returns a non-optimal found path', {'plan_with_budget': make_budget(
        make_opts(greedy=True))}, 'plan_with_budget'),
    ('plan: budget used as a cost limit', {'plan_with_budget': bud_rule(budget_cost_limit)}, 'plan_with_budget'),
    ('plan: budget ignored', {'plan_with_budget': bud_rule(budget_ignored)}, 'plan_with_budget'),
    ('plan: start == goal with budget 0 reported exhausted', {'plan_with_budget': bud_rule(budget_same)},
     'plan_with_budget'),
    ('plan: corner cutting allowed', {'plan_with_budget': make_budget(make_opts(corner='none'))}, 'plan_with_budget'),
    ('segment: endpoints only (tunneling)', {'segment_hits_rect': seg_rule(
        lambda p, q, r: any(r[0] <= v[0] <= r[2] and r[1] <= v[1] <= r[3] for v in (p, q)))}, 'segment_hits_rect'),
    ('segment: 11 equally spaced samples', {'segment_hits_rect': seg_rule(sampled(10))}, 'segment_hits_rect'),
    ('segment: samples every 0.1 length', {'segment_hits_rect': seg_rule(step_sampled(0.1))}, 'segment_hits_rect'),
    ('segment: bounding box overlap only', {'segment_hits_rect': seg_rule(bbox)}, 'segment_hits_rect'),
    ('segment: touching does not count (open rectangle)', {'segment_hits_rect': seg_rule(strict_slab)},
     'segment_hits_rect'),
    ('segment: infinite line instead of segment', {'segment_hits_rect': seg_rule(
        slab_range(-1e18, 1e18))}, 'segment_hits_rect'),
    ('segment: ray from p (no upper limit on t)', {'segment_hits_rect': seg_rule(
        slab_range(0.0, 1e18))}, 'segment_hits_rect'),
    ('segment: rectangle read as (xmin, xmax, ymin, ymax)', {'segment_hits_rect': seg_rule(
        slab_range(0.0, 1.0, order=True))}, 'segment_hits_rect'),
    ('segment: vertical segments never hit', {'segment_hits_rect': seg_rule(vertical_skipped)}, 'segment_hits_rect'),
    ('segment: axis-parallel segment divides by zero', {'segment_hits_rect': seg_rule(
        slab_range(0.0, 1.0, guard=False))}, 'segment_hits_rect'),
    ('segment: rectangle grown by 1e-3', {'segment_hits_rect': seg_rule(slab_range(0.0, 1.0, eps=1e-3))},
     'segment_hits_rect'),
    ('segment: corners on both sides of the line (ignores segment extent)', {'segment_hits_rect': seg_rule(
        line_sides)}, 'segment_hits_rect'),
    ('segment: zero-length segment never hits', {'segment_hits_rect': seg_rule(zero_len_false)}, 'segment_hits_rect'),
    ('segment: returns 1/0 instead of bool', {'segment_hits_rect': seg_rule(lambda p, q, r: int(slab(p, q, r)))},
     'segment_hits_rect'),
    ('sweep: half_width ignored', {'first_blocked_segment': sweep_rule(sweep_with(grow=lambda r, h: r))},
     'first_blocked_segment'),
    ('sweep: inflation in x only', {'first_blocked_segment': sweep_rule(sweep_with(
        grow=lambda r, h: (r[0] - h, r[1], r[2] + h, r[3])))}, 'first_blocked_segment'),
    ('sweep: inflation in y only', {'first_blocked_segment': sweep_rule(sweep_with(
        grow=lambda r, h: (r[0], r[1] - h, r[2], r[3] + h)))}, 'first_blocked_segment'),
    ('sweep: only waypoints are checked', {'first_blocked_segment': sweep_rule(waypoints_only)},
     'first_blocked_segment'),
    ('sweep: returns the last blocked segment', {'first_blocked_segment': sweep_rule(sweep_with(order='last'))},
     'first_blocked_segment'),
    ('sweep: 1-based index', {'first_blocked_segment': sweep_rule(sweep_with(offset=1))}, 'first_blocked_segment'),
    ('sweep: -1 when clear', {'first_blocked_segment': sweep_rule(sweep_with(clear=-1))}, 'first_blocked_segment'),
    ('sweep: only the first rectangle', {'first_blocked_segment': sweep_rule(sweep_with(rect_limit=1))},
     'first_blocked_segment'),
    ('sweep: inflation 2*h', {'first_blocked_segment': sweep_rule(sweep_with(
        grow=lambda r, h: (r[0] - 2*h, r[1] - 2*h, r[2] + 2*h, r[3] + 2*h)))}, 'first_blocked_segment'),
    ('sweep: inflation h/2', {'first_blocked_segment': sweep_rule(sweep_with(
        grow=lambda r, h: (r[0] - h/2, r[1] - h/2, r[2] + h/2, r[3] + h/2)))}, 'first_blocked_segment'),
    ('sweep: last segment skipped', {'first_blocked_segment': sweep_rule(sweep_with(
        segs=lambda n: range(n - 2)))}, 'first_blocked_segment'),
    ('sweep: first segment skipped', {'first_blocked_segment': sweep_rule(sweep_with(
        segs=lambda n: range(1, n - 1)))}, 'first_blocked_segment'),
    ('sweep: sorts the caller rects in place', {'first_blocked_segment': lambda p, r, h: (
        refs['first_blocked_segment'](p, r, h), r.sort())[0]}, 'first_blocked_segment'),
    ('sweep: touching a grown rectangle does not count', {'first_blocked_segment': sweep_rule(sweep_with(
        grow=lambda r, h: (r[0] - h + 1e-3, r[1] - h + 1e-3, r[2] + h - 1e-3, r[3] + h - 1e-3)))},
     'first_blocked_segment'),
    ('sweep: a single-point touch of the grown rectangle counts as clear', {'first_blocked_segment': sweep_rule(
        sweep_with(seg=strict_slab))}, 'first_blocked_segment'),
    ('invalid: bool connectivity accepted by heuristic', {'heuristic': accepts_when(
        lambda c, g, k: k is True, heuristic, 0.0)}, 'heuristic'),
    ('invalid: connectivity 6 accepted by heuristic', {'heuristic': accepts_when(
        lambda c, g, k: k == 6, heuristic, 0.0)}, 'heuristic'),
    ('invalid: weight below 1 accepted', {'astar_grid': accepts_when(
        lambda *a: len(a) > 4 and type(a[4]) is float and a[4] < 1, refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: NaN weight accepted', {'astar_grid': accepts_when(
        lambda *a: len(a) > 4 and type(a[4]) is float and a[4] != a[4], refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: weight above 10 accepted', {'astar_grid': accepts_when(
        lambda *a: len(a) > 4 and type(a[4]) in (int, float) and a[4] > 10, refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: blocked start accepted', {'astar_grid': accepts_when(
        lambda g, s, e, c, w=1.0: isinstance(g, list) and 0 <= s[0] < len(g) and 0 <= s[1] < len(g[0])
        and g[s[0]][s[1]] == 1, refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: goal outside grid accepted', {'astar_grid': accepts_when(
        lambda g, s, e, c, w=1.0: isinstance(g, list) and e[0] >= len(g), refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: ragged grid accepted', {'astar_grid': accepts_when(
        lambda g, *a: isinstance(g, list) and len({len(r) for r in g if isinstance(r, list)}) > 1,
        refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: cell value 2 accepted', {'astar_grid': accepts_when(
        lambda g, *a: isinstance(g, list) and any(v == 2 for r in g for v in r), refs['astar_grid'], None)},
     'astar_grid'),
    ('invalid: connectivity 5 accepted', {'astar_grid': accepts_when(
        lambda g, s, e, c, w=1.0: c == 5, refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: empty grid accepted', {'astar_grid': accepts_when(
        lambda g, *a: isinstance(g, list) and len(g) == 0, refs['astar_grid'], None)}, 'astar_grid'),
    ('invalid: negative budget accepted', {'plan_with_budget': accepts_when(
        lambda g, s, e, c, b: type(b) is int and b < 0, refs['plan_with_budget'], ('budget_exhausted', None, None))},
     'plan_with_budget'),
    ('invalid: bool budget accepted', {'plan_with_budget': accepts_when(
        lambda g, s, e, c, b: b is True, refs['plan_with_budget'], ('budget_exhausted', None, None))},
     'plan_with_budget'),
    ('invalid: float budget accepted', {'plan_with_budget': accepts_when(
        lambda g, s, e, c, b: type(b) is float, refs['plan_with_budget'], ('budget_exhausted', None, None))},
     'plan_with_budget'),
    ('invalid: NaN coordinate accepted by segment test', {'segment_hits_rect': accepts_when(
        lambda p, q, r: any(isinstance(v, float) and v != v for v in list(p) + list(q)), slab, False)},
     'segment_hits_rect'),
    ('invalid: inverted rectangle accepted', {'segment_hits_rect': accepts_when(
        lambda p, q, r: r[0] > r[2] or r[1] > r[3], slab, False)}, 'segment_hits_rect'),
    ('invalid: out-of-range coordinate accepted', {'segment_hits_rect': accepts_when(
        lambda p, q, r: any(abs(v) > 1000 for v in list(p) + list(q)), slab, False)}, 'segment_hits_rect'),
    ('invalid: bool coordinate accepted', {'segment_hits_rect': accepts_when(
        lambda p, q, r: any(type(v) is bool for v in list(p) + list(q)), slab, False)}, 'segment_hits_rect'),
    ('invalid: single-point path accepted', {'first_blocked_segment': accepts_when(
        lambda p, r, h: len(p) < 2, refs['first_blocked_segment'], None)}, 'first_blocked_segment'),
    ('invalid: negative half_width accepted', {'first_blocked_segment': accepts_when(
        lambda p, r, h: type(h) in (int, float) and h < 0, refs['first_blocked_segment'], None)},
     'first_blocked_segment'),
    ('invalid: NaN half_width accepted', {'first_blocked_segment': accepts_when(
        lambda p, r, h: type(h) is float and h != h, refs['first_blocked_segment'], None)},
     'first_blocked_segment'),
    ('invalid: inverted obstacle in a path accepted', {'first_blocked_segment': accepts_when(
        lambda p, r, h: any(x[0] > x[2] for x in r), refs['first_blocked_segment'], None)}, 'first_blocked_segment'),
    ('starter-style: astar raises NotImplementedError on some inputs only', {'astar_grid': accepts_when(
        lambda *a: a[3] == 4 and a[0][0][0] == 0 and len(a[0]) == 3, refs['astar_grid'], None)
        if False else (lambda *a: (_ for _ in ()).throw(NotImplementedError()) if a[3] == 4 and len(a[0]) == 3
                       else refs['astar_grid'](*a))}, 'astar_grid'),
]
unique = {m[0] for m in mutants}
require(len(unique) == len(mutants), 'duplicate mutant labels')
accepted = [label for label, over, target in mutants if not run_with(over)]
require(not accepted, 'false accepts: ' + str(accepted))
for label, over, target in mutants:
    result = run_with(over)
    require(any(line.startswith(target) or (" " + target + "(") in line for line in result),
            'mutant rejected for the wrong function (' + label + '): ' + str(result[:3]))
require(len(mutants) >= 30, 'need at least 30 named mutants')
print('Planning kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

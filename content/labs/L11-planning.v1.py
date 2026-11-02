"""CoreLab Grid Search and Swept-Collision lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the five functions below, then run your edited file locally:
  Windows: py -3 L11-planning.v1.py
  macOS/Linux: python3 L11-planning.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared world. An occupancy grid is a list/tuple of rows; each row is a
list/tuple of ints, 0 = free cell and 1 = blocked cell (never bool). 1 to 12
rows, 1 to 12 columns, all rows the same length. A cell is (row, col) with
0-based ints; row 0 is the top row. Moves go to a neighbouring cell that is
inside the grid and free:
  connectivity 4: up, down, left, right, each of cost 1.
  connectivity 8: those four plus the four diagonals, each of cost sqrt(2).
  NO CORNER CUTTING: a diagonal step from (r, c) to (r+dr, c+dc) is legal only
  if BOTH (r+dr, c) and (r, c+dc) are free as well (the robot body would
  otherwise scrape a blocked corner). This rule is part of the contract.
A path is a list/tuple of cells from start to goal, one legal move between
consecutive cells; its cost is the sum of the step costs. start == goal is a
path of one cell and cost 0.

Contracts (numbers are finite int/float, never bool; bounds inclusive):
  heuristic(cell, goal, connectivity) -> float
      cell and goal are (row, col) ints with |value| <= 1000 (no grid is
      involved). Return the cost of the cheapest path between the two cells on
      an EMPTY, unbounded grid for this connectivity (4: Manhattan distance;
      8: max(|dr|, |dc|) + (sqrt(2) - 1)*min(|dr|, |dc|)), within 1e-9. This
      is the tightest heuristic that is still admissible (never above the true
      cost on any grid) and consistent. Weaker ones (zero, Chebyshev) are
      admissible but are NOT accepted here; Manhattan distance with
      connectivity 8 overestimates diagonal moves and is inadmissible.
  astar_grid(grid, start, goal, connectivity, weight=1.0) -> (cost, path) or None
      Search from start to goal; start and goal must be free cells inside the
      grid. weight is a finite number with 1 <= weight <= 10 that multiplies
      the heuristic in the priority f = g + weight*h.
      Unreachable goal -> return None (never an infinite cost, never an empty
      path, never "nearest cell"). Otherwise return (cost, path) with cost the
      float sum of the step costs of the returned path (within 1e-9).
      weight == 1: the cost must equal the optimal cost within 1e-9. Which of
      several equally cheap paths you return is up to you (tie-breaking is not
      graded); the path is graded for validity (starts at start, ends at goal,
      every step legal, summed cost equals the reported cost).
      weight > 1: the path must be valid and optimal <= cost <= weight*optimal
      (bounded suboptimal search); a larger weight may return a worse path.
      Accepted: path as list or tuple of lists or tuples; any search structure.
  plan_with_budget(grid, start, goal, connectivity, max_expansions)
          -> (status, cost, path)
      Weight-1 A* with exactly the heuristic above and a hard limit of
      max_expansions node expansions (an int, 0 <= max_expansions <= 10000).
      An expansion is the first time a cell is removed from the open set and
      its neighbours are generated; stale duplicate entries do not count.
      The loop is: (1) open set empty -> ("unreachable", None, None);
      (2) remove the best cell; (3) it is the goal -> ("found", cost, path)
      with the OPTIMAL cost and a valid path; (4) already max_expansions
      expansions done -> ("budget_exhausted", None, None); (5) expand it.
      So unreachable means the search ran out of cells to try, and
      budget_exhausted means only that the budget ran out: it proves nothing
      about reachability. A budget of 0 with start != goal is always
      budget_exhausted; start == goal is always found, cost 0.
      Graded against tie-breaking-independent bands: a budget below the number
      of cells with g*(n) + h(n) < optimal cost (at least 1 when start != goal)
      must be budget_exhausted; a budget of at least the number of cells other
      than the goal with g*(n) + h(n) <= optimal cost must be found; in
      between either is accepted. For an unreachable goal the search expands
      every reachable cell exactly once, so the status is exact.
  segment_hits_rect(p, q, rect) -> bool
      p = (x0, y0), q = (x1, y1): the closed straight segment from p to q.
      rect = (xmin, ymin, xmax, ymax) with xmin <= xmax and ymin <= ymax: the
      CLOSED axis-aligned rectangle, boundary included. True iff the two sets
      share at least one point, so touching an edge or a corner counts as a
      hit. p == q is a point test. A zero-width or zero-height rectangle is a
      wall segment and is allowed. All values finite with |value| <= 1000.
      The test is exact geometry: do not sample points along the segment (a
      thin wall between two samples is then missed, "tunneling"), and do not
      test only the endpoints or only the bounding box of the segment.
      Self-check cases are either exactly representable (halves, quarters,
      dyadic fractions) or clear of the boundary by at least 1e-6.
  first_blocked_segment(points, rects, half_width) -> int or None
      points: 2 to 50 waypoints (x, y) of a path of straight segments; rects:
      0 to 50 obstacle rectangles as above; half_width h: 0 <= h <= 100. The
      robot is an axis-aligned square of half-width h whose centre moves along
      the segments, so it sweeps exactly the segment inflated by h: segment i
      (points[i] to points[i+1]) is blocked iff the segment meets some
      rectangle grown by h on all four sides (closed, touching counts).
      Return the smallest blocked segment index i (0-based), or None when
      every segment is clear. Checking only the waypoints is not enough.
Invalid inputs (wrong type or shape, bool, NaN, infinity, ragged or oversized
grid, cell values other than 0 and 1, start or goal outside the grid or on a
blocked cell, connectivity other than the ints 4 and 8, weight outside [1, 10],
max_expansions not an int in range, xmin > xmax, ymin > ymax, a path with
fewer than 2 points, negative half_width) raise ValueError. Never mutate the
inputs. Cost, heuristic values and times are plain float (an int 0 is fine).

Pause before coding - write your predictions down first:
  1. 8-connected, diagonal cost sqrt(2): how many orthogonal steps does a
     diagonal replace? Why does the Manhattan distance overestimate there, and
     what can A* then return? What does weight = 3 trade away, and what bound
     does it keep?
  2. A free cell has a blocked cell directly above it and another directly to
     its right. Is the diagonal step up-right legal here? What if only one of
     them is blocked? Why does the rule matter for the cost?
  3. A wall is 0.02 wide and your segment is 10 long. How many equally spaced
     samples are enough to be sure of a hit? What does an exact test need
     instead?
  4. The search stopped after 50 expansions without reaching the goal. What can
     you conclude, and what can you NOT conclude? Which status is honest?
  5. The cheapest 8-connected grid path and a straight shortcut between two
     waypoints: which is shorter, and what must you check before using the
     shortcut?
Self-check tolerances are per-case and numerical, not physical. Failure
messages name the case and the kind of mismatch, never the expected values.
"your code raised X on a VALID input" means the case is inside the contract and
must return; "invalid f(name=...)" lines are the opposite: that input must
raise ValueError. A function still raising NotImplementedError is reported once.
This kit covers 2D occupancy-grid A* with a declared step cost and one exact
segment-vs-rectangle swept check only: no RRT or PRM (a single randomized run
proves no completeness), no arm or configuration-space planning, no robot
dynamics, no simulator, no sensing and no hardware interface.
Reflection: why does passing this toy NOT validate a real planner? (Think about
map resolution and inflation, robot footprint and heading, unknown or moving
obstacles, localisation error, costmap updates, kinematic and dynamic limits,
smoothing of grid paths, planning time limits, and failure handling.)
"""
import math


def heuristic(cell, goal, connectivity):
    """Return the empty-grid path cost from cell to goal (see the module docstring)."""
    raise NotImplementedError("write heuristic")


def astar_grid(grid, start, goal, connectivity, weight=1.0):
    """Return (cost, path) of an A* search, or None if the goal is unreachable."""
    raise NotImplementedError("write astar_grid")


def plan_with_budget(grid, start, goal, connectivity, max_expansions):
    """Return (status, cost, path) with status found, unreachable or budget_exhausted."""
    raise NotImplementedError("write plan_with_budget")


def segment_hits_rect(p, q, rect):
    """Return True iff the closed segment p-q meets the closed rectangle."""
    raise NotImplementedError("write segment_hits_rect")


def first_blocked_segment(points, rects, half_width):
    """Return the first blocked segment index of a swept square path, or None."""
    raise NotImplementedError("write first_blocked_segment")


# ---- SPOILER BELOW: the oracle (_dijkstra, _hit_exact, _allowed) and the case ----
# ---- tables hold expected answers. Attempt the functions first.              ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


_SQRT2 = math.sqrt(2.0)
_CONNECTIONS = (4, 8)


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _grid(rows):
    """Rows of '.' (free) and '#' (blocked) text to a nested list of 0/1 ints."""
    return [[1 if ch == "#" else 0 for ch in row] for row in rows]


def _steps(grid, cell, connectivity):
    """Oracle move generator: legal (cell, cost) neighbours, corner rule applied."""
    rows, cols = len(grid), len(grid[0])
    r, c = cell
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        if connectivity == 4 and dr != 0 and dc != 0:
            continue
        nr, nc = r + dr, c + dc
        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] != 0:
            continue
        if dr != 0 and dc != 0 and (grid[r + dr][c] != 0 or grid[r][c + dc] != 0):
            continue
        out.append(((nr, nc), 1.0 if dr == 0 or dc == 0 else _SQRT2))
    return out


_MEMO = {}


def _dijkstra(grid, start, connectivity):
    """Exact shortest costs from start to every reachable cell (cached, read-only use)."""
    key = ("dijkstra", tuple(tuple(row) for row in grid), start, connectivity)
    if key not in _MEMO:
        _MEMO[key] = _dijkstra_uncached(grid, start, connectivity)
    return _MEMO[key]


def _dijkstra_uncached(grid, start, connectivity):
    """No heap, no heuristic: repeatedly settle the cheapest unsettled cell."""
    dist = {start: 0.0}
    done = set()
    while True:
        frontier = [cell for cell in dist if cell not in done]
        if not frontier:
            return dist
        here = min(frontier, key=lambda cell: (dist[cell], cell))
        done.add(here)
        for there, cost in _steps(grid, here, connectivity):
            if there not in dist or dist[here] + cost < dist[there] - 1e-12:
                dist[there] = dist[here] + cost


def _octile(dr, dc, connectivity):
    dr, dc = abs(dr), abs(dc)
    if connectivity == 4:
        return float(dr + dc)
    return float(max(dr, dc)) + (_SQRT2 - 1.0)*min(dr, dc)


def _path_cost(grid, path, start, goal, connectivity):
    """Cost of a returned path, or _Mismatch naming the first problem."""
    if not isinstance(path, (list, tuple)) or len(path) < 1:
        raise _Mismatch("path must be a non-empty list/tuple of (row, col) pairs")
    for cell in path:
        if not (isinstance(cell, (list, tuple)) and len(cell) == 2
                and all(type(v) is int for v in cell)):
            raise _Mismatch("every path cell must be a (row, col) pair of ints")
    if tuple(path[0]) != start:
        raise _Mismatch("the path does not begin at start")
    if tuple(path[-1]) != goal:
        raise _Mismatch("the path does not end at goal")
    total = 0.0
    for i in range(1, len(path)):
        legal = dict(_steps(grid, tuple(path[i - 1]), connectivity))
        if tuple(path[i]) not in legal:
            raise _Mismatch("step " + str(i) + " of the path is not a legal move"
                            " (bounds, blocked cell, connectivity or corner rule)")
        total += legal[tuple(path[i])]
    return total


def _allowed(grid, start, goal, connectivity, budget):
    """Statuses plan_with_budget may return, from tie-breaking-independent bands."""
    if start == goal:
        return {"found"}
    dist = _dijkstra(grid, start, connectivity)
    if goal not in dist:
        return {"unreachable"} if budget >= len(dist) else {"budget_exhausted"}
    best = dist[goal]

    def f(cell):
        return dist[cell] + _octile(cell[0] - goal[0], cell[1] - goal[1], connectivity)

    below = sum(1 for cell in dist if f(cell) < best - 1e-9)
    up_to = sum(1 for cell in dist if cell != goal and f(cell) <= best + 1e-9)
    if budget < max(below, 1):
        return {"budget_exhausted"}
    if budget >= up_to:
        return {"found"}
    return {"found", "budget_exhausted"}


def _hit_exact(p, q, rect):
    """Exact slab clipping in rational arithmetic (inputs are binary floats)."""
    from fractions import Fraction
    px, py, qx, qy = (Fraction(v) for v in (p[0], p[1], q[0], q[1]))
    x0, y0, x1, y1 = (Fraction(v) for v in rect)
    lo, hi = Fraction(0), Fraction(1)
    for a, d, low, high in ((px, qx - px, x0, x1), (py, qy - py, y0, y1)):
        if d == 0:
            if a < low or a > high:
                return False
        else:
            ta, tb = (low - a)/d, (high - a)/d
            if ta > tb:
                ta, tb = tb, ta
            lo, hi = max(lo, ta), min(hi, tb)
            if lo > hi:
                return False
    return True


def _grown(rect, h):
    return (rect[0] - h, rect[1] - h, rect[2] + h, rect[3] + h)


def _first_blocked_ref(points, rects, h):
    from fractions import Fraction
    grow = Fraction(h)
    for i in range(len(points) - 1):
        for rect in rects:
            fr = [Fraction(v) for v in rect]
            if _hit_exact(points[i], points[i + 1], _grown(fr, grow)):
                return i
    return None


class _Lcg:
    """Tiny deterministic generator so the random sweeps are identical everywhere."""

    def __init__(self, seed):
        self.state = seed

    def below(self, n):
        self.state = (self.state*1103515245 + 12345) % 2147483648
        return (self.state >> 8) % n




def _bands(grid, start, goal, connectivity):
    """Budget thresholds. ('same',), ('unreachable', reach) or ('reachable', low, high):
    below low must be budget_exhausted, at least high must be found."""
    if start == goal:
        return ("same",)
    dist = _dijkstra(grid, start, connectivity)
    if goal not in dist:
        return ("unreachable", len(dist))
    best = dist[goal]

    def f(cell):
        return dist[cell] + _octile(cell[0] - goal[0], cell[1] - goal[1], connectivity)

    below = sum(1 for cell in dist if f(cell) < best - 1e-9)
    up_to = sum(1 for cell in dist if cell != goal and f(cell) <= best + 1e-9)
    return ("reachable", max(below, 1), up_to)


def _allowed(grid, start, goal, connectivity, budget):
    """Statuses plan_with_budget may return, from tie-breaking-independent bands."""
    key = ("bands", tuple(tuple(row) for row in grid), start, goal, connectivity)
    if key not in _MEMO:
        _MEMO[key] = _bands(grid, start, goal, connectivity)
    band = _MEMO[key]
    if band[0] == "same":
        return {"found"}
    if band[0] == "unreachable":
        return {"unreachable"} if budget >= band[1] else {"budget_exhausted"}
    if budget < band[1]:
        return {"budget_exhausted"}
    if budget >= band[2]:
        return {"found"}
    return {"found", "budget_exhausted"}


_W = ("....", ".##.", ".##.", "....")
_MAZE = ("...#.", ".#.#.", ".#...", ".####", ".....")
_GAP = (".....", ".###.", ".....")
# heuristic(cell, goal, connectivity) -> value; None = open-grid Dijkstra oracle.
_H_CASES = [
    (((0, 0), (2, 2), 8), 2.0*math.sqrt(2.0)),
    (((0, 0), (2, 2), 4), 4.0),
    (((3, 1), (0, 5), 8), 4.0 + 3.0*(math.sqrt(2.0) - 1.0)),
    (((4, 4), (4, 4), 8), 0.0),
]
# astar_grid(grid rows, start, goal, connectivity, weight) -> hand cost (float),
# "none" for an unreachable goal, or None = compare with the Dijkstra oracle.
_A_CASES = [
    (("...", "...", "..."), (0, 0), (2, 2), 8, 1.0, 2.0*math.sqrt(2.0)),
    (("...", "...", "..."), (0, 0), (2, 2), 4, 1.0, 4.0),
    (("..", "#."), (0, 0), (1, 1), 8, 1.0, 2.0),
    (_GAP, (1, 0), (1, 4), 8, 1.0, 6.0),
    (_GAP, (1, 0), (1, 4), 8, 3.0, None),
    (("#.", ".#"), (0, 1), (1, 0), 8, 1.0, "none"),
    (("..#.", "..#.", "..#."), (0, 0), (2, 3), 8, 1.0, "none"),
    (("....", "....", ".#..", "...."), (0, 0), (3, 3), 8, 1.0, 2.0 + 2.0*math.sqrt(2.0)),
    (_MAZE, (0, 0), (4, 4), 4, 1.0, 8.0),
    (("....", "..#.", ".#..", "....", "#..."), (0, 2), (4, 1), 8, 1.0, 3.0 + 2.0*math.sqrt(2.0)),
    ((".",), (0, 0), (0, 0), 8, 1.0, 0.0),
]
# plan_with_budget(grid rows, start, goal, connectivity, max_expansions); the
# allowed statuses come from the oracle bands.
_B_CASES = [
    (_W, (0, 0), (3, 3), 8, 4),
    (_W, (0, 0), (3, 3), 8, 11),
    (("..#.", "..#.", "..#."), (0, 0), (2, 3), 8, 5),
    (("..#.", "..#.", "..#."), (0, 0), (2, 3), 8, 6),
    (("#.", ".#"), (0, 1), (1, 0), 8, 0),
    (("#.", ".#"), (0, 1), (1, 0), 8, 1),
    (("...", "...", "..."), (0, 0), (2, 2), 8, 0),
    ((".",), (0, 0), (0, 0), 8, 0),
]
# segment_hits_rect(p, q, rect) -> bool, every answer derived by hand.
_S_CASES = [
    (((0, 0), (4, 0), (1, -1, 2, 1)), True),
    (((4, 0), (0, 0), (1, -1, 2, 1)), True),
    (((0, 0.5), (10, 0.5), (4.9375, 0, 4.96875, 1)), True),
    (((0, 0), (4, 4), (1, 2, 2, 3)), True),
    (((0, 0), (4, 4), (2.5, 0, 3.5, 2)), False),
    (((0, 1), (4, 1), (1, 0, 2, 1)), True),
    (((0, 0.5), (1, 0.5), (1, 0, 2, 1)), True),
    (((0, 0.5), (0.96875, 0.5), (1, 0, 2, 1)), False),
    (((1.25, 0.25), (1.75, 0.75), (1, 0, 2, 1)), True),
    (((1.5, -2), (1.5, 3), (1, 0, 2, 1)), True),
    (((2.5, -2), (2.5, 3), (1, 0, 2, 1)), False),
    (((1.5, 0.5), (1.5, 0.5), (1, 0, 2, 1)), True),
    (((0, 0), (4, 0), (2, -1, 2, 1)), True),
    (((0, 2), (4, 2), (2, -1, 2, 1)), False),
    (((0, 2), (2, 0), (1, 1, 3, 3)), True),
    (((0, 1.9375), (1.9375, 0), (1, 1, 3, 3)), False),
    (((0, 0), (4, 0), (1, 0.0009765625, 2, 1)), False),
    (((0, 0), (0.5, 0.5), (1, 1, 2, 2)), False),
    (((0, 0), (-1, -1), (1, 1, 2, 2)), False),
]
_PATH1 = ((0, 0), (2, 0), (2, 3), (5, 3))
_GATE = ((2, -5, 3, -0.5), (2, 0.5, 3, 5))
# first_blocked_segment(points, rects, half_width) -> index or None, by hand.
_P_CASES = [
    ((_PATH1, ((3.5, 1, 4.5, 2),), 0.75), None),
    ((_PATH1, ((3.5, 1, 4.5, 2),), 1.25), 2),
    ((((0, 0), (6, 0)), _GATE, 0.25), None),
    ((((0, 0), (6, 0)), _GATE, 0.5), 0),
    ((((0, 0), (2, 0), (2, 4), (6, 4), (6, 0)), ((1, 1, 3, 2), (5, 3.5, 7, 4.5)), 0), 1),
    ((((0, 0), (10, 0)), ((4.9375, -1, 4.96875, 1),), 0), 0),
    ((((0, 0), (4, 0)), ((1, 1.5, 2, 2),), 1.5), 0),
    ((((0, 0), (6, 6)), ((5, 2, 6, 3),), 1), 0),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _frozen(value):
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(v) for v in value)
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation?)"
    return text + ")"


def _random_grids(count, seed):
    key = ("_random_grids", count, seed)
    if key not in _MEMO:
        _MEMO[key] = _random_grids_make(count, seed)
    return _MEMO[key]


def _random_grids_make(count, seed):
    rng = _Lcg(seed)
    out = []
    while len(out) < count:
        rows, cols = 3 + rng.below(5), 3 + rng.below(5)
        grid = [[1 if rng.below(10) < 3 else 0 for _ in range(cols)] for _ in range(rows)]
        free = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 0]
        if len(free) >= 2:
            out.append((grid, free[rng.below(len(free))], free[rng.below(len(free))]))
    return out


def _random_segments(count, seed):
    key = ("_random_segments", count, seed)
    if key not in _MEMO:
        _MEMO[key] = _random_segments_make(count, seed)
    return _MEMO[key]


def _random_segments_make(count, seed):
    """Random segment/rectangle cases whose exact answer survives a 1e-6 shift."""
    rng = _Lcg(seed)
    tiny = 1e-6
    out = []
    while len(out) < count:
        def coord():
            return (rng.below(41) - 20)/4.0
        p, q = (coord(), coord()), (coord(), coord())
        x0, y0 = coord(), coord()
        rect = (x0, y0, x0 + (1 + rng.below(8))/4.0, y0 + (1 + rng.below(8))/4.0)
        want = _hit_exact(p, q, rect)
        if (_hit_exact(p, q, _grown(rect, tiny)) == want
                and _hit_exact(p, q, _grown(rect, -tiny)) == want):
            out.append(((p, q, rect), want))
    return out


def _random_sweeps(count, seed):
    key = ("_random_sweeps", count, seed)
    if key not in _MEMO:
        _MEMO[key] = _random_sweeps_make(count, seed)
    return _MEMO[key]


def _random_sweeps_make(count, seed):
    rng = _Lcg(seed)
    tiny = 1e-6
    out = []
    while len(out) < count:
        def coord():
            return (rng.below(33) - 16)/4.0
        points = [(coord(), coord()) for _ in range(2 + rng.below(4))]
        rects = []
        for _ in range(rng.below(4)):
            x0, y0 = coord(), coord()
            rects.append((x0, y0, x0 + (1 + rng.below(6))/4.0, y0 + (1 + rng.below(6))/4.0))
        h = rng.below(4)/4.0
        want = _first_blocked_ref(points, rects, h)
        if (_first_blocked_ref(points, rects, h + tiny) == want
                and _first_blocked_ref(points, rects, h - tiny) == want):
            out.append(((points, rects, h), want))
    return out


def _bad_cases():
    """(label, function name, args): inputs outside the contract that must raise ValueError."""
    g = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    box = (0, 0, 2, 2)
    pts = [(0, 0), (1, 1)]
    return [
        ("invalid heuristic(connectivity=6)", "heuristic", ((0, 0), (1, 1), 6)),
        ("invalid heuristic(connectivity=True)", "heuristic", ((0, 0), (1, 1), True)),
        ("invalid heuristic(cell=floats)", "heuristic", ((0.5, 0), (1, 1), 8)),
        ("invalid heuristic(goal has 3 entries)", "heuristic", ((0, 0), (1, 1, 1), 8)),
        ("invalid heuristic(cell=bool)", "heuristic", ((True, 0), (1, 1), 4)),
        ("invalid astar_grid(connectivity=5)", "astar_grid", (g, (0, 0), (2, 2), 5, 1.0)),
        ("invalid astar_grid(connectivity=True)", "astar_grid", (g, (0, 0), (2, 2), True, 1.0)),
        ("invalid astar_grid(start on a blocked cell)", "astar_grid", (g, (1, 1), (2, 2), 8, 1.0)),
        ("invalid astar_grid(goal on a blocked cell)", "astar_grid", (g, (0, 0), (1, 1), 4, 1.0)),
        ("invalid astar_grid(goal outside the grid)", "astar_grid", (g, (0, 0), (3, 0), 8, 1.0)),
        ("invalid astar_grid(start with a negative index)", "astar_grid", (g, (-1, 0), (2, 2), 8, 1.0)),
        ("invalid astar_grid(weight=0.5)", "astar_grid", (g, (0, 0), (2, 2), 8, 0.5)),
        ("invalid astar_grid(weight=nan)", "astar_grid", (g, (0, 0), (2, 2), 8, float("nan"))),
        ("invalid astar_grid(weight=inf)", "astar_grid", (g, (0, 0), (2, 2), 8, float("inf"))),
        ("invalid astar_grid(weight=11)", "astar_grid", (g, (0, 0), (2, 2), 8, 11)),
        ("invalid astar_grid(weight=True)", "astar_grid", (g, (0, 0), (2, 2), 8, True)),
        ("invalid astar_grid(ragged grid)", "astar_grid", ([[0, 0], [0]], (0, 0), (0, 1), 4, 1.0)),
        ("invalid astar_grid(empty grid)", "astar_grid", ([], (0, 0), (0, 0), 4, 1.0)),
        ("invalid astar_grid(cell value 2)", "astar_grid", ([[0, 2], [0, 0]], (0, 0), (1, 1), 4, 1.0)),
        ("invalid astar_grid(cell value True)", "astar_grid", ([[0, True], [0, 0]], (0, 0), (1, 1), 4, 1.0)),
        ("invalid astar_grid(13 rows)", "astar_grid", ([[0] for _ in range(13)], (0, 0), (12, 0), 4, 1.0)),
        ("invalid plan_with_budget(max_expansions=-1)", "plan_with_budget", (g, (0, 0), (2, 2), 8, -1)),
        ("invalid plan_with_budget(max_expansions=True)", "plan_with_budget", (g, (0, 0), (2, 2), 8, True)),
        ("invalid plan_with_budget(max_expansions=2.0)", "plan_with_budget", (g, (0, 0), (2, 2), 8, 2.0)),
        ("invalid plan_with_budget(max_expansions=10001)", "plan_with_budget", (g, (0, 0), (2, 2), 8, 10001)),
        ("invalid plan_with_budget(start blocked)", "plan_with_budget", (g, (1, 1), (2, 2), 8, 5)),
        ("invalid segment_hits_rect(nan coordinate)", "segment_hits_rect", ((float("nan"), 0), (1, 1), box)),
        ("invalid segment_hits_rect(inf coordinate)", "segment_hits_rect", ((0, 0), (float("inf"), 1), box)),
        ("invalid segment_hits_rect(xmin > xmax)", "segment_hits_rect", ((0, 0), (1, 1), (2, 0, 1, 2))),
        ("invalid segment_hits_rect(ymin > ymax)", "segment_hits_rect", ((0, 0), (1, 1), (0, 2, 2, 1))),
        ("invalid segment_hits_rect(p has 3 entries)", "segment_hits_rect", ((0, 0, 0), (1, 1), box)),
        ("invalid segment_hits_rect(bool coordinate)", "segment_hits_rect", ((True, 0), (1, 1), box)),
        ("invalid segment_hits_rect(|value| > 1000)", "segment_hits_rect", ((0, 0), (1001, 1), box)),
        ("invalid first_blocked_segment(one point)", "first_blocked_segment", ([(0, 0)], [], 0)),
        ("invalid first_blocked_segment(half_width=-0.1)", "first_blocked_segment", (pts, [], -0.1)),
        ("invalid first_blocked_segment(half_width=nan)", "first_blocked_segment", (pts, [], float("nan"))),
        ("invalid first_blocked_segment(rect with xmin > xmax)", "first_blocked_segment", (pts, [(2, 0, 1, 2)], 0)),
        ("invalid first_blocked_segment(point with bool)", "first_blocked_segment", ([(0, 0), (1, False)], [], 0)),
    ]


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, args, frozen=False):
        """Call once on a fresh copy; (True, result) or (False, None) after recording."""
        calls[name] = calls.get(name, 0) + 1
        live = _frozen(args) if frozen else _fresh(args)
        snapshot = repr(live)
        try:
            got = globals()[name](*live)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return False, None
        except Exception as error:
            failures.append(label + ": " + _raised(error))
            return False, None
        if repr(live) != snapshot:
            failures.append(label + ": modified its input (inputs must never be mutated)")
        return True, got

    def run(name, label, args, compare, frozen=False):
        ok, got = attempt(name, label, args, frozen)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def cmp_number(want, tolerance, what):
        def compare(got):
            if not _real(got):
                raise _Mismatch(what + " must be one finite int/float")
            if not abs(got - want) <= tolerance:
                raise _Mismatch(what + " is wrong (tolerance " + repr(tolerance) + ")")
        return compare

    def cmp_search(grid, start, goal, conn, weight, hand):
        def compare(got):
            dist = _dijkstra(grid, start, conn)
            if goal not in dist or hand == "none":
                if got is not None:
                    raise _Mismatch("reachability answer is wrong (None vs (cost, path))")
                return
            if got is None:
                raise _Mismatch("reachability answer is wrong (None vs (cost, path))")
            if not (isinstance(got, (list, tuple)) and len(got) == 2 and _real(got[0])):
                raise _Mismatch("result must be (cost, path) with a finite number as cost, or None")
            cost, path = got
            walked = _path_cost(grid, path, start, goal, conn)
            if not abs(cost - walked) <= 1e-9:
                raise _Mismatch("the reported cost is not the cost of the returned path")
            best = dist[goal]
            if weight == 1:
                if not abs(cost - best) <= 1e-9:
                    raise _Mismatch("the cost is not optimal (tolerance 1e-9)")
                if isinstance(hand, float) and not abs(cost - hand) <= 1e-9:
                    raise _Mismatch("the cost disagrees with the hand-derived anchor")
            elif not best - 1e-9 <= cost <= weight*best + 1e-9:
                raise _Mismatch("the cost is outside optimal..weight*optimal")
        return compare

    def cmp_budget(grid, start, goal, conn, budget):
        def compare(got):
            if not (isinstance(got, (list, tuple)) and len(got) == 3):
                raise _Mismatch("result must be a (status, cost, path) triple")
            status, cost, path = got
            if status not in ("found", "unreachable", "budget_exhausted"):
                raise _Mismatch("status must be found, unreachable or budget_exhausted")
            if status not in _allowed(grid, start, goal, conn, budget):
                raise _Mismatch("status is wrong for this budget (budget failure is not proof"
                                " of unreachability, and a found goal needs enough budget)")
            if status != "found":
                if cost is not None or path is not None:
                    raise _Mismatch("cost and path must both be None unless the goal was found")
                return
            if not _real(cost):
                raise _Mismatch("cost must be a finite number when found")
            walked = _path_cost(grid, path, start, goal, conn)
            if not abs(cost - walked) <= 1e-9:
                raise _Mismatch("the reported cost is not the cost of the returned path")
            if not abs(cost - _dijkstra(grid, start, conn)[goal]) <= 1e-9:
                raise _Mismatch("the found cost is not optimal (tolerance 1e-9)")
        return compare

    def cmp_bool(want):
        def compare(got):
            if type(got) is not bool:
                raise _Mismatch("output must be a bool")
            if got != want:
                raise _Mismatch("hit/miss answer is wrong")
        return compare

    def cmp_index(want):
        def compare(got):
            if got is not None and type(got) is not int:
                raise _Mismatch("output must be an int index or None")
            if got != want:
                raise _Mismatch("first blocked segment is wrong")
        return compare

    open_grid = [[0]*9 for _ in range(9)]
    for i, (args, want) in enumerate(_H_CASES):
        if want is None:
            want = _dijkstra(open_grid, (args[0][0], args[0][1]), args[2])[args[1]]
        run("heuristic", "heuristic case " + str(i), args, cmp_number(want, 1e-9, "heuristic value"))
    for conn in _CONNECTIONS:
        for k, (dr, dc) in enumerate(((0, 0), (1, 0), (0, 3), (2, 2), (3, 1), (4, 4), (-2, 4), (4, -3))):
            cell, goal = (4 + dr, 4 + dc), (4, 4)
            want = _dijkstra(open_grid, cell, conn)[goal]
            run("heuristic", "heuristic sweep " + str(conn) + "/" + str(k), (cell, goal, conn),
                cmp_number(want, 1e-9, "heuristic value"))
    for i, (rows, start, goal, conn, weight, hand) in enumerate(_A_CASES):
        grid = _grid(rows)
        args = (grid, start, goal, conn, weight)
        for frozen in (False, True):
            run("astar_grid", "astar_grid case " + str(i) + (" (tuples)" if frozen else ""),
                args, cmp_search(grid, start, goal, conn, weight, hand), frozen)
    for i, (grid, start, goal) in enumerate(_random_grids(28, 20260401)):
        for conn in _CONNECTIONS:
            run("astar_grid", "astar_grid sweep " + str(i) + "/" + str(conn),
                (grid, start, goal, conn, 1.0), cmp_search(grid, start, goal, conn, 1, None))
        if i % 2 == 0:
            run("astar_grid", "astar_grid weighted sweep " + str(i),
                (grid, start, goal, 8, 3.0), cmp_search(grid, start, goal, 8, 3.0, None))
    for i, (rows, start, goal, conn, budget) in enumerate(_B_CASES):
        grid = _grid(rows)
        run("plan_with_budget", "plan_with_budget case " + str(i),
            (grid, start, goal, conn, budget), cmp_budget(grid, start, goal, conn, budget))
    for i, (grid, start, goal) in enumerate(_random_grids(18, 77001)):
        for conn in _CONNECTIONS:
            band = _bands(grid, start, goal, conn)
            if band[0] == "same":
                budgets = [0]
            elif band[0] == "unreachable":
                budgets = [band[1] - 1, band[1], band[1] + 2]
            else:
                budgets = [band[1] - 1, band[1], band[2], band[2] + 2]
            for budget in budgets:
                run("plan_with_budget", "plan_with_budget sweep " + str(i) + "/" + str(conn)
                    + "/" + str(budget), (grid, start, goal, conn, budget),
                    cmp_budget(grid, start, goal, conn, budget))
    for i, (args, want) in enumerate(_S_CASES):
        for frozen in (False, True):
            run("segment_hits_rect", "segment_hits_rect case " + str(i)
                + (" (tuples)" if frozen else ""), args, cmp_bool(want), frozen)
    for i, (args, want) in enumerate(_random_segments(150, 4242)):
        run("segment_hits_rect", "segment_hits_rect sweep " + str(i), args, cmp_bool(want))
    for i, (args, want) in enumerate(_P_CASES):
        for frozen in (False, True):
            run("first_blocked_segment", "first_blocked_segment case " + str(i)
                + (" (tuples)" if frozen else ""), args, cmp_index(want), frozen)
    for i, (args, want) in enumerate(_random_sweeps(60, 9090)):
        run("first_blocked_segment", "first_blocked_segment sweep " + str(i), args, cmp_index(want))
    for label, name, args in _bad_cases():
        calls[name] = calls.get(name, 0) + 1
        live = _fresh(args)
        try:
            globals()[name](*live)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            continue
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__ + " instead of ValueError")
            continue
        failures.append(label + ": returned instead of raising ValueError")
    summary = []
    for name, labels in missing.items():
        if len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels)) + " of "
                           + str(calls[name]) + " checks (first: " + labels[0] + "); finish it")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError; "
                           + str(calls[name]) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    notes = []
    failures = self_check(notes)
    print("CoreLab manual grid-search / swept-collision self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

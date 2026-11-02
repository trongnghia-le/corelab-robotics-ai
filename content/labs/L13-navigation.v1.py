"""CoreLab Pure-pursuit path-follower lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the six functions below, then run your edited file locally:
  Windows: py -3 L13-navigation.v1.py
  macOS/Linux: python3 L13-navigation.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy world (numerical practice, not Nav2, ROS, a costmap or a real robot):
a point-like differential-drive robot (unicycle) in a flat plane, metres and
radians, x forward / y left, counter-clockwise positive, heading theta measured
from the world +x axis. A path is a polyline: a list/tuple of 2 to 50 points
[x, y]; consecutive points differ by at least 1e-6. Segment i joins path[i] to
path[i+1]; a path of n points has n-1 segments, indexed 0..n-2. The goal is the
last point. Arc length s is measured along the polyline from path[0].

Contracts (all numbers finite int/float, never bool; bounds inclusive):
  path_distance(path, x, y) -> (d, s)
      d = distance from (x, y) to the nearest point of the whole polyline
      (cross-track error, unsigned); s = arc length of that nearest point. If
      several nearest points tie, report the smallest s. Use all segments.
  lookahead_point(path, x, y, lookahead, start_index=0) -> (status, px, py, index)
      Scan segments start_index, start_index+1, ... in order. On a segment
      with end points A and B, the circle of radius `lookahead` around (x, y)
      meets the infinite line in up to two points; only the one further along
      A->B (the larger parameter t, P = A + t*(B-A)) is "ahead" of the robot.
      The segment qualifies when that point has 0 <= t <= 1 (a root within
      1e-9 of an end counts as at the end; a tangent contact, line distance
      exactly = lookahead, counts as one point). The FIRST qualifying
      segment wins, even if a later one has a point nearer the path end.
      Result ('circle', px, py, i) with i the winning segment. If the circle
      touches a vertex, the lower segment index is reported (the point is
      the same). If no segment qualifies and the goal is STRICTLY closer
      than `lookahead` to the robot, the result is ('end', gx, gy, n-2) with
      the goal as target. Otherwise ('none', None, None, start_index): the
      robot is lost; do not invent a target. start_index is an int
      with 0 <= start_index <= n-2. The self-check only uses tangent and
      vertex contacts whose arithmetic is exact.
  curvature(x, y, theta, tx, ty) -> kappa
      Pure pursuit: express the target in the robot frame, y_L = -sin(theta)*dx
      + cos(theta)*dy with dx = tx - x, dy = ty - y; kappa = 2*y_L/(dx*dx + dy*dy)
      in 1/m (positive = turn left). Use the ACTUAL squared distance to the
      target (it equals lookahead**2 for a 'circle' target, not for 'end').
      A target behind the robot on its heading line gives 0 (a known blind spot
      of the formula). Target distance below 1e-6 raises ValueError.
  limit_command(v_cmd, kappa, v_max, w_max) -> (v, omega)
      v = min(v_cmd, v_max); omega = v*kappa. If |omega| would exceed w_max,
      keep the curvature (the arc) and slow down: v = w_max/|kappa|, omega =
      v*kappa. Exactly at the limit nothing changes. Never clip omega alone
      (that changes the arc), never reverse (v >= 0).
  simulate(path, x0, y0, theta0, lookahead, v_cmd, v_max, w_max, h, goal_tol,
           max_steps) -> (status, rows)
      Closed loop from pose (x0, y0, theta0) with a scan index starting at 0.
      Each cycle, in this order:
        1. if distance to the goal <= goal_tol: status 'reached', stop.
        2. if the number of steps taken == max_steps: status 'timeout', stop.
        3. lookahead_point from the current scan index (feed the returned index
           back); 'none' -> status 'lost', stop.
        4. kappa = curvature to the target; (v, omega) = limit_command.
        5. record row (x, y, theta, v, omega) = current pose with the command
           applied during this step, then advance one step of h seconds by the
           exact circular arc: u = omega*h/2, chord = v*h*sin(u)/u (v*h*(1 -
           u*u/6) when |u| < 1e-6) along heading theta + u, then theta += 2*u.
      On stopping, append the final row (x, y, theta, 0, 0). So there are
      steps_taken + 1 rows. theta may be wrapped or unwrapped (compared modulo
      2*pi). Rows are compared to 1e-7. Constant commanded speed does not
      slow near the goal: a goal_tol smaller than roughly v*h may be circled
      forever and end 'timeout' - that is a report, not an error.
  evaluate_trace(path, points, corridor, goal_tol) -> (max_error, rms_error,
                 first_exit, goal_step, cut_corners, verdict)
      points = list/tuple of 1 to 2001 [x, y] samples (repeats allowed), sample
      k at time k*h. e_k = path_distance of sample k. max_error = max e_k;
      rms_error = sqrt(mean(e_k**2)). first_exit = smallest k with
      e_k > corridor (strict; exactly equal is inside) or None. goal_step =
      smallest k with distance to the goal <= goal_tol (inclusive) or None.
      cut_corners = ascending tuple/list of interior vertex indices j (1..n-2)
      whose clearance exceeds the corridor (strict); clearance = distance from
      path[j] to the POLYLINE through the samples (a single sample counts as
      a point), so a chord between two good samples can still cut a corner.
      It lists every such vertex, including ones the trace never reached.
      verdict (first rule that applies): 'off-corridor' if first_exit is not
      None; 'timeout' if goal_step is None; 'corner-cut' if cut_corners is
      not empty; else 'ok'.
Bounds: |x|, |y|, |tx|, |ty|, |coordinates| <= 1000; |theta|, |theta0| <= 100;
1e-3 <= lookahead <= 100; 0 <= v_cmd <= 100; |kappa| <= 1e6; 0 < v_max <= 100;
0 < w_max <= 100; 0 < h <= 1; 1e-3 <= goal_tol <= 100; 0 < corridor <= 100;
max_steps an int (not bool or float) with 1 <= max_steps <= 2000. Invalid
inputs (wrong type or shape, bool, NaN, infinity, out of bounds, a path with
fewer than 2 or more than 50 points or two equal consecutive points) raise
ValueError. Return exactly the shapes above (finite int/float, status and
verdict are str). Never mutate the inputs. Tolerances: 1e-9 for geometry,
1e-7 for simulate rows.

Pause before coding - write your predictions down first:
  1. Robot at (2, 3) heading 0, path along y = 0, lookahead 5: where is the
     lookahead point, and which sign does kappa have?
  2. Two circle points exist on a segment. Which one is "ahead", and why is the
     other one dangerous near a corner?
  3. The robot is 0.5 m before the last vertex and lookahead is 1 m. What is
     the target, and what is kappa's denominator?
  4. A sharp corner and a lookahead of 3 m: does the robot pass through the
     corner vertex? Which way does it miss, and how would you detect it with
     samples only?
  5. Why slow down, not just clip omega, when |v*kappa| exceeds w_max?
  6. A trace ends within goal_tol but left the corridor on the way: 'ok'?
Failure messages name the case and the kind of mismatch, never the expected
numbers. "your code raised X" means your function raised on a VALID input.
This does not implement Nav2, a controller plugin, costmaps, localization, TF,
time synchronisation, actuator limits beyond one speed and one turn-rate
bound, slip, latency, obstacles or any hardware interface.
Reflection: why does passing this kinematic toy NOT validate a real navigation
stack? (Think about pose estimates and TF timeouts, latency, wheel slip and
actuator dynamics, costmaps and obstacles, changed layouts, replanning, noisy
or lost localisation, and logs recorded by an independent observer.)
"""
import math


def path_distance(path, x, y):
    raise NotImplementedError("Nearest point over ALL segments; clamp the projection to each segment")


def lookahead_point(path, x, y, lookahead, start_index=0):
    raise NotImplementedError("First segment whose farther circle root lies on it; then the goal; else none")


def curvature(x, y, theta, tx, ty):
    raise NotImplementedError("Rotate the target into the robot frame; kappa = 2*y_L/(squared distance)")


def limit_command(v_cmd, kappa, v_max, w_max):
    raise NotImplementedError("Slow down along the same arc instead of clipping omega alone")


def simulate(path, x0, y0, theta0, lookahead, v_cmd, v_max, w_max, h, goal_tol, max_steps):
    raise NotImplementedError("Check goal, then step budget, then target; keep the scan index between steps")


def evaluate_trace(path, points, corridor, goal_tol):
    raise NotImplementedError("Sample errors, strict corridor test, polyline clearance at interior vertices")


# ---- SPOILER BELOW: the _oracle_* functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _seg_bisect(a, b, p):
    """Nearest point on segment a-b to p by bisection on the sign of the slope.

    Returns (distance, t). Independent of the closed-form projection.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 0 and dy == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1]), 0.0
    low, high = 0.0, 1.0
    for _ in range(80):
        mid = 0.5*(low + high)
        slope = (a[0] + mid*dx - p[0])*dx + (a[1] + mid*dy - p[1])*dy
        if slope > 0:
            high = mid
        else:
            low = mid
    t = 0.5*(low + high)
    return math.hypot(a[0] + t*dx - p[0], a[1] + t*dy - p[1]), t


def _oracle_distance(path, x, y):
    best, best_s, walked = None, 0.0, 0.0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        d, t = _seg_bisect(a, b, (x, y))
        if best is None or d < best - 1e-12:
            best, best_s = d, walked + t*length
        walked += length
    return best, best_s


def _oracle_hits(path, x, y, lookahead, start):
    """Per segment: (index, t2 or None, margin) using the foot-of-perpendicular form."""
    out = []
    for i in range(start, len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx*dx + dy*dy
        tf = ((x - a[0])*dx + (y - a[1])*dy)/length2
        fx, fy = a[0] + tf*dx - x, a[1] + tf*dy - y
        h2 = fx*fx + fy*fy
        if h2 > lookahead*lookahead*(1 + 1e-12):
            out.append((i, None, abs(h2 - lookahead*lookahead)))
            continue
        t2 = tf + math.sqrt(max(0.0, lookahead*lookahead - h2)/length2)
        out.append((i, t2, abs(h2 - lookahead*lookahead)))
    return out


def _oracle_lookahead(path, x, y, lookahead, start=0):
    for i, t2, _ in _oracle_hits(path, x, y, lookahead, start):
        if t2 is not None and -1e-9 <= t2 <= 1 + 1e-9:
            t = min(1.0, max(0.0, t2))
            a, b = path[i], path[i + 1]
            return ('circle', a[0] + t*(b[0] - a[0]), a[1] + t*(b[1] - a[1]), i)
    gx, gy = path[-1]
    if math.hypot(gx - x, gy - y) < lookahead:
        return ('end', gx, gy, len(path) - 2)
    return ('none', None, None, start)


def _oracle_well_conditioned(path, x, y, lookahead, start):
    """False when a decision sits within 1e-6 of a knife edge (random cases only)."""
    for i, t2, margin in _oracle_hits(path, x, y, lookahead, start):
        if margin < 1e-6:
            return False
        if t2 is not None and (abs(t2) < 1e-6 or abs(t2 - 1) < 1e-6):
            return False
    gx, gy = path[-1]
    return abs(math.hypot(gx - x, gy - y) - lookahead) > 1e-6


def _oracle_curvature(x, y, theta, tx, ty):
    c, s = math.cos(theta), math.sin(theta)
    dx, dy = tx - x, ty - y
    forward, left = c*dx + s*dy, -s*dx + c*dy
    return 2*left/(forward*forward + left*left)


def _oracle_limit(v_cmd, kappa, v_max, w_max):
    v = min(v_cmd, v_max)
    if abs(v*kappa) > w_max:
        v = w_max/abs(kappa)
    return v, v*kappa


def _oracle_advance(x, y, theta, v, omega, h):
    """Closed-form arc (differs from the chord-sinc form of the contract)."""
    if abs(omega) < 1e-6:
        mid = theta + 0.5*omega*h
        return x + v*h*math.cos(mid), y + v*h*math.sin(mid), theta + omega*h
    return (x + v/omega*(math.sin(theta + omega*h) - math.sin(theta)),
            y - v/omega*(math.cos(theta + omega*h) - math.cos(theta)),
            theta + omega*h)


def _oracle_sim(path, x, y, theta, lookahead, v_cmd, v_max, w_max, h, goal_tol, max_steps):
    index, rows, steps = 0, [], 0
    gx, gy = path[-1]
    while True:
        if math.hypot(gx - x, gy - y) <= goal_tol:
            status = 'reached'
            break
        if steps == max_steps:
            status = 'timeout'
            break
        kind, px, py, index = _oracle_lookahead(path, x, y, lookahead, index)
        if kind == 'none':
            status = 'lost'
            break
        v, omega = _oracle_limit(v_cmd, _oracle_curvature(x, y, theta, px, py), v_max, w_max)
        rows.append((x, y, theta, v, omega))
        x, y, theta = _oracle_advance(x, y, theta, v, omega, h)
        steps += 1
    rows.append((x, y, theta, 0.0, 0.0))
    return status, rows


def _oracle_polyline_distance(points, p):
    if len(points) == 1:
        return math.hypot(points[0][0] - p[0], points[0][1] - p[1])
    return min(_seg_bisect(points[k], points[k + 1], p)[0] for k in range(len(points) - 1))


def _oracle_evaluate(path, points, corridor, goal_tol):
    errors = [_oracle_distance(path, px, py)[0] for px, py in points]
    first_exit = next((k for k, e in enumerate(errors) if e > corridor), None)
    gx, gy = path[-1]
    goal_step = next((k for k, (px, py) in enumerate(points)
                      if math.hypot(px - gx, py - gy) <= goal_tol), None)
    cut = tuple(j for j in range(1, len(path) - 1)
                if _oracle_polyline_distance(points, path[j]) > corridor)
    verdict = ('off-corridor' if first_exit is not None else 'timeout' if goal_step is None
               else 'corner-cut' if cut else 'ok')
    return (max(errors), math.sqrt(sum(e*e for e in errors)/len(errors)),
            first_exit, goal_step, cut, verdict)


_P_L = [(0, 0), (4, 0), (4, 3)]
_P_U = [(0, 0), (4, 0), (4, 2), (0, 2)]
_P_CORNER = [(0, 0), (8, 0), (8, 8)]
_P_LINE = [(0, 0), (10, 0)]
_P_SQ = [(0, 0), (6, 0), (6, 6), (0, 6)]
_P_UTURN = [(0, 0), (10, 0), (10, 1), (0, 1)]

# path_distance(path, x, y) -> (d, s): hand-derived.
_DIST_CASES = [
    ((_P_L, 2, 1), (1.0, 2.0)),
    ((_P_L, 6, 0), (2.0, 4.0)),
    ((_P_L, -3, -4), (5.0, 0.0)),
    ((_P_L, 6, 6), (math.sqrt(13), 7.0)),
    ((_P_U, 2, 1), (1.0, 2.0)),
    ((_P_U, 3, 1.5), (0.5, 7.0)),
    (([(1.5, 2.5), (1.5, 8.5)], 4.5, 5.5), (3.0, 3.0)),
    (([(0, 0), (3, 4)], 4, 3), (1.4, 4.8)),
]

# lookahead_point(path, x, y, lookahead, start_index): hand-derived (circle meets line).
_LOOK_CASES = [
    (([(0, 0), (12, 0)], 2, 3, 5, 0), ('circle', 6.0, 0.0, 0)),
    ((_P_CORNER, 5, 0, 5, 0), ('circle', 8.0, 4.0, 1)),
    ((_P_CORNER, 5, 0, 3, 0), ('circle', 8.0, 0.0, 0)),
    ((_P_CORNER, 5, 0, 3, 1), ('circle', 8.0, 0.0, 1)),
    ((_P_LINE, 4, 3, 3, 0), ('circle', 4.0, 0.0, 0)),
    ((_P_LINE, 4, 3, 2.9, 0), ('none', None, None, 0)),
    (([(0, 0), (5, 0), (5, 5)], 5, 4, 3, 0), ('end', 5.0, 5.0, 1)),
    ((_P_LINE, 6, 0, 4, 0), ('circle', 10.0, 0.0, 0)),
    ((_P_LINE, 12, 0, 2, 0), ('none', None, None, 0)),
    ((_P_SQ, 3, 3, 3.5, 0), ('circle', 3 + math.sqrt(13)/2, 0.0, 0)),
    (([(0, 0), (1, 0), (1, 1), (1, 10)], 0, 0, 5, 0), ('circle', 1.0, math.sqrt(24), 2)),
    ((_P_UTURN, 8, 0.2, 3, 0), ('circle', 8 - math.sqrt(8.36), 1.0, 2)),
]
# curvature(x, y, theta, tx, ty) -> kappa: points on the circle of radius R tangent
# to the heading at the robot give kappa = 1/R exactly (x^2 + y^2 = 2*R*y_L).
_CURV_CASES = [
    ((0, 0, 0, 3, 1), 0.2),
    ((0, 0, 0, 6, 2), 0.1),
    ((0, 0, 0, 3, -1), -0.2),
    ((1, 1, math.pi/2, 0, 4), 0.2),
    ((1, 2, 0, 6, 2), 0.0),
    ((0, 0, 0, -4, 3), 0.24),
    ((0, 0, 0, -5, 0), 0.0),
]
# limit_command(v_cmd, kappa, v_max, w_max) -> (v, omega).
_LIMIT_CASES = [
    ((1, 0.5, 2, 1), (1.0, 0.5)),
    ((3, 0.5, 2, 1), (2.0, 1.0)),
    ((2, -2, 2, 1.5), (0.75, -1.5)),
    ((0, 1, 2, 1), (0.0, 0.0)),
    ((5, 0.1, 2, 0.1), (1.0, 0.1)),
]
# simulate(...) -> (status, rows): (args, status, number of rows, hand-derived rows).
_S_LINE = (_P_LINE, 0, 0, 0, 1, 1, 1, 1, 0.5, 0.1, 100)
_SIM_CASES = [
    (_S_LINE, 'reached', 21, {4: (2.0, 0.0, 0.0, 1.0, 0.0), 20: (10.0, 0.0, 0.0, 0.0, 0.0)}),
    (_S_LINE[:-1] + (20,), 'reached', 21, {20: (10.0, 0.0, 0.0, 0.0, 0.0)}),
    (_S_LINE[:-1] + (19,), 'timeout', 20, {19: (9.5, 0.0, 0.0, 0.0, 0.0)}),
    (([(0, 0), (40, 0)], 0, 3, 0, 5, 1, 1, 1, 0.5, 0.5, 200), 'reached', None,
     {0: (0.0, 3.0, 0.0, 1.0, -0.24)}),
    (([(0, 0), (10, 0), (10, 10)], 0, 0, 0, 2, 1, 1, 1, 0.1, 0.2, 400), 'reached', None, {}),
    ((_P_LINE, 0, 50, 0, 1, 1, 1, 1, 0.5, 0.1, 10), 'lost', 1, {0: (0.0, 50.0, 0.0, 0.0, 0.0)}),
    ((_P_LINE, 0, 0, 1.0, 3, 1, 1, 0.3, 0.1, 0.2, 600), 'reached', None,
     {0: (0.0, 0.0, 1.0, 0.3/(2/3*math.sin(1.0)), -0.3)}),
    ((_P_LINE, 13, 4, 1.0, 1, 1, 1, 1, 0.5, 5.0, 10), 'reached', 1, {0: (13.0, 4.0, 1.0, 0.0, 0.0)}),
    ((_P_LINE, 0, 0, 0, 1, 0, 1, 1, 0.5, 0.1, 4), 'timeout', 5, {2: (0.0, 0.0, 0.0, 0.0, 0.0)}),
]
# evaluate_trace(path, points, corridor, goal_tol) -> (max, rms, first_exit, goal_step,
# cut_corners, verdict): hand-derived.
_EVAL_CASES = [
    (([(0, 0), (10, 0), (10, 10)], [(2, 0.5), (5, -1), (9, 0.8), (10.6, 3), (10, 6)], 1.5, 0.5),
     (1.0, math.sqrt(2.25/5), None, None, (), 'timeout')),
    (([(0, 0), (6, 0), (6, 8)], [(0, 0), (4, 0), (6, 2), (6, 8)], 0.5, 0.5),
     (0.0, 0.0, None, 3, (1,), 'corner-cut')),
    ((_P_LINE, [(0, 0), (2, 0.3), (4, 1.0), (6, 1.6), (8, 0.7), (9.2, 0.2), (9.6, 0.1)], 1.0, 0.5),
     (1.6, math.sqrt(4.19/7), 3, 6, (), 'off-corridor')),
    (([(0, 0), (4, 0), (4, 4)], [(0, 0), (3, 0), (3, 3), (4, 4)], 1.0, 0.5),
     (1.0, 0.5, None, 3, (), 'ok')),
    (([(0, 0), (4, 0), (8, 0)], [(0, 0), (8, 0)], 0.5, 0.5), (0.0, 0.0, None, 1, (), 'ok')),
    (([(0, 0), (5, 0), (5, 5)], [(0, 0), (0, 0), (0, 0)], 1.0, 0.5),
     (0.0, 0.0, None, None, (1,), 'timeout')),
    ((_P_LINE, [(0, 0), (13, 4)], 6.0, 5.0), (5.0, math.sqrt(12.5), None, 1, (), 'ok')),
    ((_P_LINE, [(0, 3), (5, 0), (10, 0)], 2.0, 0.5), (3.0, math.sqrt(3), 0, 2, (), 'off-corridor')),
    ((_P_SQ, [(0, 0), (4, 0), (6, 2), (6, 4), (4, 6), (0, 6)], 0.5, 0.5),
     (0.0, 0.0, None, 5, (1, 2), 'corner-cut')),
]


def _clone(value, as_list):
    """Fresh nested copy as lists (as_list) or tuples."""
    if isinstance(value, (list, tuple)):
        items = [_clone(v, as_list) for v in value]
        return items if as_list else tuple(items)
    return value


def _lcg(seed):
    state = [seed]

    def draw():
        state[0] = (state[0]*1103515245 + 12345) % 2147483648
        return state[0]/2147483648
    return draw


def _random_path(draw, count, span):
    while True:
        path = [[round((draw()*2 - 1)*span, 6), round((draw()*2 - 1)*span, 6)] for _ in range(count)]
        if all(math.hypot(path[i+1][0] - path[i][0], path[i+1][1] - path[i][1]) > 0.5
               for i in range(count - 1)):
            return path


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures, missing, calls = [], {}, {}
    functions = {"path_distance": path_distance, "lookahead_point": lookahead_point,
                 "curvature": curvature, "limit_command": limit_command,
                 "simulate": simulate, "evaluate_trace": evaluate_trace}

    def run(label, name, args, compare, flip=0):
        calls[name] = calls.get(name, 0) + 1
        call_args = tuple(_clone(a, flip % 2 == 0) for a in args)
        before = tuple(_clone(a, True) for a in call_args)
        try:
            got = functions[name](*call_args)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return
        except Exception as error:
            failures.append(label + ": your code raised " + type(error).__name__
                            + " on a valid input")
            return
        try:
            if tuple(_clone(a, True) for a in call_args) != before:
                raise _Mismatch("an input argument was mutated")
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": result could not be checked (" + type(error).__name__ + ")")

    def close(got, want, name, tolerance=1e-9):
        if not _real(got) or abs(got - want) > tolerance:
            raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")

    def same_index(got, want, name):
        if type(got) is not int or got != want:
            raise _Mismatch(name + " is wrong (must be an int)")

    def maybe_index(got, want, name):
        if (got is None) != (want is None) or (got is not None and (type(got) is not int or got != want)):
            raise _Mismatch(name + " is wrong (int or None)")

    def check_distance(want):
        def compare(got):
            if not _vector(got, 2):
                raise _Mismatch("output must be a length-2 list/tuple (d, s) of finite int/float")
            close(got[0], want[0], "distance d")
            close(got[1], want[1], "arc length s")
        return compare

    def check_look(want):
        def compare(got):
            if not isinstance(got, (list, tuple)) or len(got) != 4 or type(got[0]) is not str:
                raise _Mismatch("output must be a length-4 list/tuple (status str, px, py, index)")
            if got[0] != want[0]:
                raise _Mismatch("status is wrong ('circle', 'end' or 'none')")
            if want[0] == 'none':
                if got[1] is not None or got[2] is not None:
                    raise _Mismatch("px and py must be None when the robot is lost")
            else:
                close(got[1], want[1], "px")
                close(got[2], want[2], "py")
            same_index(got[3], want[3], "segment index")
        return compare

    def check_pair(want):
        def compare(got):
            if not _vector(got, 2):
                raise _Mismatch("output must be a length-2 list/tuple (v, omega) of finite int/float")
            close(got[0], want[0], "speed v")
            close(got[1], want[1], "turn rate omega")
        return compare

    def check_scalar(want):
        def compare(got):
            if not _real(got):
                raise _Mismatch("output must be a finite int/float")
            close(got, want, "kappa")
        return compare

    for i, (args, want) in enumerate(_DIST_CASES):
        run("path_distance " + str(i), "path_distance", args, check_distance(want), i)

    for i, (args, want) in enumerate(_LOOK_CASES):
        run("lookahead_point " + str(i), "lookahead_point", args, check_look(want), i)

    draw = _lcg(20260713)
    for i in range(60):
        path = _random_path(draw, 3 + int(draw()*4), 10)
        x, y = round((draw()*2 - 1)*12, 6), round((draw()*2 - 1)*12, 6)
        run("path_distance random " + str(i), "path_distance", (path, x, y),
            check_distance(_oracle_distance(path, x, y)), i)
    done = 0
    while done < 80:
        path = _random_path(draw, 3 + int(draw()*4), 8)
        x, y = round((draw()*2 - 1)*10, 6), round((draw()*2 - 1)*10, 6)
        lookahead = round(0.5 + draw()*5.5, 6)
        start = int(draw()*(len(path) - 1))
        if not _oracle_well_conditioned(path, x, y, lookahead, start):
            continue
        run("lookahead_point random " + str(done), "lookahead_point",
            (path, x, y, lookahead, start),
            check_look(_oracle_lookahead(path, x, y, lookahead, start)), done)
        done += 1

    for i, (args, want) in enumerate(_CURV_CASES):
        run("curvature " + str(i), "curvature", args, check_scalar(want), i)
    for i in range(40):
        args = tuple(round((draw()*2 - 1)*scale, 6) for scale in (20, 20, 7, 20, 20))
        if math.hypot(args[3] - args[0], args[4] - args[1]) < 0.1:
            continue
        run("curvature random " + str(i), "curvature", args,
            check_scalar(_oracle_curvature(*args)), i)

    for i, (args, want) in enumerate(_LIMIT_CASES):
        run("limit_command " + str(i), "limit_command", args, check_pair(want), i)
    for i in range(40):
        args = (round(draw()*3, 6), round((draw()*2 - 1)*4, 6),
                round(0.2 + draw()*3, 6), round(0.2 + draw()*2, 6))
        run("limit_command random " + str(i), "limit_command", args,
            check_pair(_oracle_limit(*args)), i)

    def check_sim(args, status, count, hand):
        want_status, want_rows = _oracle_sim(*args)

        def compare(got):
            if not isinstance(got, (list, tuple)) or len(got) != 2 or type(got[0]) is not str \
                    or not isinstance(got[1], (list, tuple)):
                raise _Mismatch("output must be a length-2 list/tuple (status str, rows)")
            if got[0] != status or got[0] != want_status:
                raise _Mismatch("status is wrong ('reached', 'timeout' or 'lost')")
            rows = got[1]
            if len(rows) != len(want_rows) or (count is not None and len(rows) != count):
                raise _Mismatch("number of rows is wrong (steps taken + 1)")
            for k, row in enumerate(rows):
                if not _vector(row, 5):
                    raise _Mismatch("row " + str(k) + " must be a length-5 list/tuple"
                                    " (x, y, theta, v, omega) of finite int/float")
            for k, (row, ref) in enumerate(zip(rows, want_rows)):
                for index, name in ((0, "x"), (1, "y"), (3, "v"), (4, "omega")):
                    close(row[index], ref[index], name + " in row " + str(k), 1e-7)
                turn = (row[2] - ref[2] + math.pi) % (2*math.pi) - math.pi
                if abs(turn) > 1e-7:
                    raise _Mismatch("theta in row " + str(k) + " is wrong (modulo 2*pi, tolerance 1e-07)")
            for k, ref in hand.items():
                for slot in (0, 1, 3, 4):
                    close(rows[k][slot], ref[slot], "hand anchor row " + str(k) + " entry " + str(slot), 1e-7)
        return compare

    for i, (args, status, count, hand) in enumerate(_SIM_CASES):
        run("simulate " + str(i), "simulate", args, check_sim(args, status, count, hand), i)
    for i in range(6):
        path = _random_path(draw, 3 + int(draw()*3), 8)
        args = (path, round((draw()*2 - 1)*8, 4), round((draw()*2 - 1)*8, 4),
                round((draw()*2 - 1)*3, 4), round(0.8 + draw()*3, 4), round(0.5 + draw()*2, 4),
                round(0.8 + draw()*2, 4), round(0.4 + draw()*2, 4), 0.1, 0.3, 300)
        kind = _oracle_sim(*args)[0]
        run("simulate random " + str(i), "simulate", args, check_sim(args, kind, None, {}), i)

    def check_eval(want):
        def compare(got):
            if not isinstance(got, (list, tuple)) or len(got) != 6:
                raise _Mismatch("output must be a length-6 list/tuple (max_error, rms_error,"
                                " first_exit, goal_step, cut_corners, verdict)")
            close(got[0], want[0], "max_error")
            close(got[1], want[1], "rms_error")
            maybe_index(got[2], want[2], "first_exit")
            maybe_index(got[3], want[3], "goal_step")
            if (not isinstance(got[4], (list, tuple)) or any(type(v) is not int for v in got[4])
                    or tuple(got[4]) != tuple(want[4])):
                raise _Mismatch("cut_corners is wrong (ascending ints)")
            if type(got[5]) is not str or got[5] != want[5]:
                raise _Mismatch("verdict is wrong ('off-corridor', 'timeout', 'corner-cut' or 'ok')")
        return compare

    for i, (args, want) in enumerate(_EVAL_CASES):
        run("evaluate_trace " + str(i), "evaluate_trace", args, check_eval(want), i)
    for i in range(20):
        path = _random_path(draw, 3 + int(draw()*3), 8)
        points = [[round(path[0][0] + (draw()*2 - 1)*2, 4), round(path[0][1] + (draw()*2 - 1)*2, 4)]
                  for _ in range(1 + int(draw()*12))]
        if i % 2 == 0:
            points.append([round(path[-1][0] + (draw()*2 - 1)*0.2, 4),
                           round(path[-1][1] + (draw()*2 - 1)*0.2, 4)])
        args = (path, points, round(0.5 + draw()*2, 4), round(0.3 + draw(), 4))
        run("evaluate_trace random " + str(i), "evaluate_trace", args,
            check_eval(_oracle_evaluate(*args)), i)

    nan, inf = float('nan'), float('inf')
    good_path = [[0, 0], [4, 0], [4, 3]]
    bad_paths = [[], [[0, 0]], [[0, 0], [0, 0]], [[0, 0], [4, 0], [4, 0]], [[0, 0], [1e-7, 0]],
                 [[0, i] for i in range(51)], [[0, 0], [1]], [[0, 0], [1, 0, 0]],
                 [[0, 0], [1, True]], [[0, 0], [nan, 0]], [[0, 0], [inf, 0]],
                 [[0, 0], [1001, 0]], [[0, 0], [1, "2"]], [[0, 0], None], "ab", None, 5,
                 {0: [0, 0], 1: [1, 0]}]
    scalar = [nan, inf, -inf, True, 1001, -1001, "0", None]
    signatures = [
        ("path_distance", ("path", "x", "y"), (good_path, 1.0, 1.0)),
        ("lookahead_point", ("path", "x", "y", "lookahead", "start_index"),
         (good_path, 1.0, 1.0, 2.0, 0)),
        ("curvature", ("x", "y", "theta", "tx", "ty"), (0.0, 0.0, 0.5, 3.0, 1.0)),
        ("limit_command", ("v_cmd", "kappa", "v_max", "w_max"), (1.0, 0.5, 2.0, 1.0)),
        ("simulate", ("path", "x0", "y0", "theta0", "lookahead", "v_cmd", "v_max", "w_max",
                      "h", "goal_tol", "max_steps"),
         (good_path, 0.0, 0.5, 0.0, 2.0, 1.0, 1.0, 1.0, 0.1, 0.2, 10)),
        ("evaluate_trace", ("path", "points", "corridor", "goal_tol"),
         (good_path, [[0, 0], [2, 0.5]], 1.0, 0.5)),
    ]
    bad = {
        "path": bad_paths, "x": scalar, "y": scalar, "x0": scalar, "y0": scalar,
        "tx": scalar, "ty": scalar,
        "theta": [nan, inf, 100.01, -100.01, True, "0", None],
        "theta0": [nan, inf, 100.01, -100.01, True, "0", None],
        "lookahead": [0.0, 0.0009, -1.0, 100.01, nan, inf, True, "1", None],
        "start_index": [-1, 2, 3, 1.0, True, nan, "0", None],
        "v_cmd": [-0.01, 100.01, nan, inf, True, "1", None],
        "kappa": [nan, inf, 1e6 + 1, -1e6 - 1, True, "1", None],
        "v_max": [0.0, -1.0, 100.01, nan, inf, True, "1", None],
        "w_max": [0.0, -1.0, 100.01, nan, inf, True, "1", None],
        "h": [0.0, -0.1, 1.01, nan, inf, True, "0.1", None],
        "goal_tol": [0.0, 0.0009, -0.1, 100.01, nan, inf, True, "0.1", None],
        "corridor": [0.0, -0.1, 100.01, nan, inf, True, "1", None],
        "max_steps": [0, -1, 2001, 5.0, True, nan, "5", None],
        "points": [[], (), [[0]], [[0, 0, 0]], [[0, True]], [[0, nan]], [[0, inf]], [[1001, 0]],
                   [[0, "1"]], [[0, 0]] * 2002, "ab", None, [None], {0: [0, 0]}],
    }
    for title, names, base in signatures:
        for slot, name in enumerate(names):
            for value in bad[name]:
                trial = base[:slot] + (value,) + base[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                calls[title] = calls.get(title, 0) + 1
                try:
                    functions[title](*trial)
                except ValueError:
                    continue
                except NotImplementedError:
                    missing.setdefault(title, []).append(label)
                    continue
                except Exception as error:
                    failures.append(label + ": raised " + type(error).__name__
                                    + " instead of ValueError")
                    continue
                failures.append(label + ": returned instead of raising ValueError")
    for label, trial in (("curvature with the target on the robot", (1.0, 2.0, 0.3, 1.0, 2.0)),
                         ("curvature with the target 5e-7 away", (1.0, 2.0, 0.3, 1.0000005, 2.0))):
        calls["curvature"] = calls.get("curvature", 0) + 1
        try:
            curvature(*trial)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault("curvature", []).append(label)
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
    failures = self_check()
    print("CoreLab manual pure-pursuit self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

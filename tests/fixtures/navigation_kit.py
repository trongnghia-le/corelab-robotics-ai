"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected for their intended reason.
Plain checks only, so the fixture also works under python -O.
"""
import ast
import importlib.util
import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('navigation_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L13-navigation.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math'}, 'kit imports beyond math: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
NAMES = ('path_distance', 'lookahead_point', 'curvature', 'limit_command', 'simulate',
         'evaluate_trace')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name) < spoiler for name in NAMES),
        'starter functions must sit above the spoiler banner')
require(text.index('def _oracle_sim') > spoiler and text.index('_DIST_CASES = ') > spoiler,
        'oracles and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('navigation_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(len(starter) == 6 and all('not implemented yet' in line for line in starter),
        'unimplemented starter must report one collapsed line per function: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def deep(value):
    if isinstance(value, (list, tuple)):
        return [deep(v) for v in value]
    return dec(value)


def entry(structure, names, args):
    return {'structure': structure, 'inputs': {n: deep(v) for n, v in zip(names, args)}}


expected_samples = (
    [entry('nav.path-distance@1', ('path', 'x', 'y'), a) for a, _ in kit._DIST_CASES]
    + [entry('nav.lookahead@1', ('path', 'x', 'y', 'lookahead', 'start_index'), a)
       for a, _ in kit._LOOK_CASES]
    + [entry('nav.curvature@1', ('x', 'y', 'theta', 'tx', 'ty'), a) for a, _ in kit._CURV_CASES]
    + [entry('nav.limit-command@1', ('v_cmd', 'kappa', 'v_max', 'w_max'), a)
       for a, _ in kit._LIMIT_CASES]
    + [entry('nav.simulate@1', ('path', 'x0', 'y0', 'theta0', 'lookahead', 'v_cmd', 'v_max',
                                'w_max', 'h', 'goal_tol', 'max_steps'), c[0])
       for c in kit._SIM_CASES]
    + [entry('nav.evaluate-trace@1', ('path', 'points', 'corridor', 'goal_tol'), a)
       for a, _ in kit._EVAL_CASES])
samples = json.loads((root / 'content/labs/L13-navigation.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L13-navigation'], 'samples must hold only L13-navigation')
require(samples['kits']['L13-navigation'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- author reference implementation ----
def num(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def as_path(path):
    if not isinstance(path, (list, tuple)) or not 2 <= len(path) <= 50:
        raise ValueError
    out = []
    for p in path:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError
        num(p[0], -1000, 1000)
        num(p[1], -1000, 1000)
        out.append((p[0], p[1]))
    for a, b in zip(out, out[1:]):
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
            raise ValueError
    return out


def as_points(points):
    if not isinstance(points, (list, tuple)) or not 1 <= len(points) <= 2001:
        raise ValueError
    out = []
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError
        num(p[0], -1000, 1000)
        num(p[1], -1000, 1000)
        out.append((p[0], p[1]))
    return out


def seg_near(a, b, px, py):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx*dx + dy*dy
    t = 0.0 if n == 0 else min(1.0, max(0.0, ((px - a[0])*dx + (py - a[1])*dy)/n))
    return math.hypot(a[0] + t*dx - px, a[1] + t*dy - py), t


def core_distance(P, x, y, ties_last=False, local_t=False, squared=False, first_only=False,
                  vertices_only=False, infinite=False):
    best, best_s, walked = None, 0.0, 0.0
    for i in range(len(P) - 1 if not first_only else 1):
        a, b = P[i], P[i + 1]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if vertices_only:
            d, t = min((math.hypot(a[0] - x, a[1] - y), 0.0), (math.hypot(b[0] - x, b[1] - y), 1.0))
        elif infinite:
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = ((x - a[0])*dx + (y - a[1])*dy)/(dx*dx + dy*dy)
            d = math.hypot(a[0] + t*dx - x, a[1] + t*dy - y)
        else:
            d, t = seg_near(a, b, x, y)
        s = t*length if local_t else walked + t*length
        if best is None or d < best or (ties_last and d == best):
            best, best_s = d, s
        walked += length
    return (best*best if squared else best, best_s)


def core_lookahead(P, x, y, L, start, root='t2', tangent=True, clamp=False, end_le=False,
                   tie_high=False, reverse=False, always_end=False, end_index=None,
                   ignore_start=False):
    n = len(P)
    order = list(range(0 if ignore_start else start, n - 1))
    if reverse:
        order.reverse()
    for i in order:
        a, b = P[i], P[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        fx, fy = a[0] - x, a[1] - y
        qa, qb, qc = dx*dx + dy*dy, 2*(fx*dx + fy*dy), fx*fx + fy*fy - L*L
        disc = qb*qb - 4*qa*qc
        if disc < 0 or (disc == 0 and not tangent):
            continue
        r = math.sqrt(disc)
        t1, t2 = (-qb - r)/(2*qa), (-qb + r)/(2*qa)
        cands = [t2] if root == 't2' else [t1] if root == 't1' else [t1, t2]
        for t in cands:
            if clamp and t > 1:
                t = 1.0
            if -1e-9 <= t <= 1 + 1e-9:
                t = min(1.0, max(0.0, t))
                j = i + 1 if tie_high and t == 1.0 and i < n - 2 else i
                return ('circle', a[0] + t*dx, a[1] + t*dy, j)
    gx, gy = P[-1]
    d = math.hypot(gx - x, gy - y)
    if always_end or d < L or (end_le and d <= L):
        return ('end', gx, gy, (n - 2) if end_index is None else end_index)
    return ('none', None, None, start)


def core_curv(x, y, th, tx, ty, mode='ok'):
    dx, dy = tx - x, ty - y
    if mode == 'degrees':
        th = math.radians(th)
    left = -math.sin(th)*dx + math.cos(th)*dy
    if mode == 'rot-sign':
        left = math.sin(th)*dx + math.cos(th)*dy
    if mode == 'world':
        left = dy
    d2 = dx*dx + dy*dy
    if d2 < 1e-12:
        raise ValueError
    if mode == 'no-two':
        return left/d2
    if mode == 'sine':
        return 2*left/math.sqrt(d2)
    if mode == 'flip':
        return -2*left/d2
    return 2*left/d2


def core_limit(vc, k, vm, wm, mode='ok'):
    v = vc if mode == 'no-vmax' else min(vc, vm)
    if mode == 'clip-omega':
        return v, max(-wm, min(wm, v*k))
    if abs(v*k) > wm:
        if mode == 'spin':
            return 0.0, math.copysign(wm, k)
        v = wm/abs(k)
    if mode == 'stale-v':
        return v, vc*k if abs(vc*k) <= wm else v*k
    return v, v*k


def advance(x, y, th, v, om, h, euler=False, no_theta=False):
    if euler:
        return x + v*h*math.cos(th), y + v*h*math.sin(th), th + om*h
    u = om*h/2
    chord = v*h*(1 - u*u/6) if abs(u) < 1e-6 else v*h*math.sin(u)/u
    return (x + chord*math.cos(th + u), y + chord*math.sin(th + u),
            th if no_theta else th + 2*u)


def core_sim(P, x, y, th, L, vc, vm, wm, h, tol, nmax, timeout_first=False, strict=False,
             no_final=False, final_keeps=False, euler=False, no_theta=False, nominal=False,
             lost_to_goal=False, no_limit=False, post_row=False, ignore_goal=False):
    index, rows, steps = 0, [], 0
    gx, gy = P[-1]
    last = None
    while True:
        d = math.hypot(gx - x, gy - y)
        reached = d < tol if strict else d <= tol
        if timeout_first and steps == nmax:
            status = 'timeout'
            break
        if reached and not ignore_goal:
            status = 'reached'
            break
        if steps == nmax:
            status = 'timeout'
            break
        kind, px, py, index = core_lookahead(P, x, y, L, index)
        if kind == 'none':
            if lost_to_goal:
                px, py = gx, gy
            else:
                status = 'lost'
                break
        k = core_curv(x, y, th, px, py)
        if nominal:
            k = k*(px - x)**2 + k*(py - y)**2
            k = k/(L*L)
        v, om = (min(vc, vm), min(vc, vm)*k) if no_limit else core_limit(vc, k, vm, wm)
        last = (v, om)
        nx, ny, nth = advance(x, y, th, v, om, h, euler, no_theta)
        if post_row:
            rows.append((nx, ny, nth, v, om))
        else:
            rows.append((x, y, th, v, om))
        x, y, th = nx, ny, nth
        steps += 1
    if not no_final:
        rows.append((x, y, th, last[0], last[1]) if final_keeps and last else (x, y, th, 0.0, 0.0))
    return status, rows


def core_eval(P, pts, corr, tol, strict_goal=False, corr_ge=False, verdict_goal=False,
              samples_only=False, mean_not_rms=False, sample_var=False, signed=False,
              one_based=False, endpoints=False, cut_before_timeout=False, first_cut_only=False):
    errs = []
    for px, py in pts:
        d = core_distance(P, px, py)[0]
        errs.append(d)
    if signed:
        errs = [e if (px >= 0) else -e for e, (px, py) in zip(errs, pts)]
    exit_k = next((k for k, e in enumerate(errs) if (e >= corr if corr_ge else e > corr)), None)
    gx, gy = P[-1]
    goal_k = next((k for k, (px, py) in enumerate(pts)
                   if (math.hypot(px - gx, py - gy) < tol if strict_goal
                       else math.hypot(px - gx, py - gy) <= tol)), None)
    cut = []
    rng = range(0, len(P)) if endpoints else range(1, len(P) - 1)
    for j in rng:
        if samples_only or len(pts) == 1:
            c = min(math.hypot(px - P[j][0], py - P[j][1]) for px, py in pts)
        else:
            c = min(seg_near(pts[k], pts[k + 1], P[j][0], P[j][1])[0] for k in range(len(pts) - 1))
        if c > corr:
            cut.append(j)
    if first_cut_only:
        cut = cut[:1]
    n = len(errs)
    if mean_not_rms:
        rms = sum(abs(e) for e in errs)/n
    elif sample_var:
        rms = math.sqrt(sum(e*e for e in errs)/max(1, n - 1))
    else:
        rms = math.sqrt(sum(e*e for e in errs)/n)
    if exit_k is not None and not (verdict_goal and goal_k is not None):
        verdict = 'off-corridor'
    elif cut_before_timeout and cut and exit_k is None:
        verdict = 'corner-cut'
    elif goal_k is None:
        verdict = 'timeout'
    elif cut:
        verdict = 'corner-cut'
    else:
        verdict = 'ok'
    if one_based:
        exit_k = None if exit_k is None else exit_k + 1
    return (max(errs), rms, exit_k, goal_k, tuple(cut), verdict)


def v_distance(path, x, y, **kw):
    P = as_path(path)
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    return core_distance(P, x, y, **kw)


def v_lookahead(path, x, y, lookahead, start_index=0, **kw):
    P = as_path(path)
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    num(lookahead, 1e-3, 100)
    if type(start_index) is not int or not 0 <= start_index <= len(P) - 2:
        raise ValueError
    return core_lookahead(P, x, y, lookahead, start_index, **kw)


def v_curvature(x, y, theta, tx, ty, **kw):
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    num(theta, -100, 100)
    num(tx, -1000, 1000)
    num(ty, -1000, 1000)
    return core_curv(x, y, theta, tx, ty, **kw)


def v_limit(v_cmd, kappa, v_max, w_max, **kw):
    num(v_cmd, 0, 100)
    num(kappa, -1e6, 1e6)
    num(v_max, 0, 100)
    num(w_max, 0, 100)
    if v_max <= 0 or w_max <= 0:
        raise ValueError
    return core_limit(v_cmd, kappa, v_max, w_max, **kw)


def v_sim(path, x0, y0, theta0, lookahead, v_cmd, v_max, w_max, h, goal_tol, max_steps, **kw):
    P = as_path(path)
    num(x0, -1000, 1000)
    num(y0, -1000, 1000)
    num(theta0, -100, 100)
    num(lookahead, 1e-3, 100)
    num(v_cmd, 0, 100)
    num(v_max, 0, 100)
    num(w_max, 0, 100)
    num(h, 0, 1)
    num(goal_tol, 1e-3, 100)
    if v_max <= 0 or w_max <= 0 or h <= 0:
        raise ValueError
    if type(max_steps) is not int or not 1 <= max_steps <= 2000:
        raise ValueError
    return core_sim(P, x0, y0, theta0, lookahead, v_cmd, v_max, w_max, h, goal_tol, max_steps, **kw)


def v_eval(path, points, corridor, goal_tol, **kw):
    P = as_path(path)
    pts = as_points(points)
    num(corridor, 0, 100)
    num(goal_tol, 1e-3, 100)
    if corridor <= 0:
        raise ValueError
    return core_eval(P, pts, corridor, goal_tol, **kw)


refs = {'path_distance': v_distance, 'lookahead_point': v_lookahead, 'curvature': v_curvature,
        'limit_command': v_limit, 'simulate': v_sim, 'evaluate_trace': v_eval}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


def failing(lines):
    out = set()
    for line in lines:
        head = line.split(':')[0]
        if head.startswith('invalid '):
            head = head[8:].split('(')[0]
        out.add(head.split(' ')[0])
    return out


# ---- valid alternatives (different formulations) ----
def alt_distance_cross(path, x, y):
    """Dot/cross formulation on complex numbers; list result."""
    P = as_path(path)
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    z = complex(x, y)
    best, best_s, walked = None, 0.0, 0.0
    for i in range(len(P) - 1):
        a, b = complex(*P[i]), complex(*P[i + 1])
        seg = b - a
        t = ((z - a)*seg.conjugate()).real/abs(seg)**2
        if t <= 0:
            d, tt = abs(z - a), 0.0
        elif t >= 1:
            d, tt = abs(z - b), 1.0
        else:
            d, tt = abs(((z - a)*seg.conjugate()).imag)/abs(seg), t
        if best is None or d < best:
            best, best_s = d, walked + tt*abs(seg)
        walked += abs(seg)
    return [best, best_s]


def alt_lookahead_foot(path, x, y, lookahead, start_index=0):
    """Foot of the perpendicular plus half chord; tuple result."""
    P = as_path(path)
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    num(lookahead, 1e-3, 100)
    if type(start_index) is not int or not 0 <= start_index <= len(P) - 2:
        raise ValueError
    for i in range(start_index, len(P) - 1):
        (ax, ay), (bx, by) = P[i], P[i + 1]
        length = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax)/length, (by - ay)/length
        along = (x - ax)*ux + (y - ay)*uy
        h2 = (ax + along*ux - x)**2 + (ay + along*uy - y)**2
        if h2 <= lookahead*lookahead:
            s = along + math.sqrt(max(0.0, lookahead*lookahead - h2))
            if -1e-9 <= s <= length + 1e-9:
                s = min(length, max(0.0, s))
                return ('circle', ax + s*ux, ay + s*uy, i)
    gx, gy = P[-1]
    if (gx - x)**2 + (gy - y)**2 < lookahead*lookahead:
        return ('end', gx, gy, len(P) - 2)
    return ('none', None, None, start_index)


def alt_curvature_atan(x, y, theta, tx, ty):
    """Angle form: alpha = bearing - theta, kappa = 2 sin(alpha)/distance."""
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    num(theta, -100, 100)
    num(tx, -1000, 1000)
    num(ty, -1000, 1000)
    d = math.hypot(tx - x, ty - y)
    if d < 1e-6:
        raise ValueError
    alpha = math.atan2(ty - y, tx - x) - theta
    return 2*math.sin(alpha)/d


def alt_limit_fraction(v_cmd, kappa, v_max, w_max):
    """Exact rational arithmetic, converted back to float."""
    num(v_cmd, 0, 100)
    num(kappa, -1e6, 1e6)
    num(v_max, 0, 100)
    num(w_max, 0, 100)
    if v_max <= 0 or w_max <= 0:
        raise ValueError
    F = Fraction
    v = min(F(v_cmd), F(v_max))
    if kappa != 0:
        v = min(v, F(w_max)/abs(F(kappa)))
    return [float(v), float(v*F(kappa))]


def alt_sim_closed_arc(path, x0, y0, theta0, lookahead, v_cmd, v_max, w_max, h, goal_tol, max_steps):
    """Own loop, list rows, closed-form arc, never calling the other student functions."""
    P = as_path(path)
    num(x0, -1000, 1000)
    num(y0, -1000, 1000)
    num(theta0, -100, 100)
    num(lookahead, 1e-3, 100)
    num(v_cmd, 0, 100)
    num(v_max, 0, 100)
    num(w_max, 0, 100)
    num(h, 0, 1)
    num(goal_tol, 1e-3, 100)
    if v_max <= 0 or w_max <= 0 or h <= 0 or type(max_steps) is not int or not 1 <= max_steps <= 2000:
        raise ValueError
    x, y, th, index, rows = float(x0), float(y0), float(theta0), 0, []
    goal = P[-1]
    for step in range(max_steps + 1):
        if math.hypot(goal[0] - x, goal[1] - y) <= goal_tol:
            rows.append([x, y, th, 0.0, 0.0])
            return ['reached', rows]
        if step == max_steps:
            rows.append([x, y, th, 0.0, 0.0])
            return ['timeout', rows]
        kind, px, py, index = alt_lookahead_foot(P, x, y, lookahead, index)
        if kind == 'none':
            rows.append([x, y, th, 0.0, 0.0])
            return ['lost', rows]
        k = alt_curvature_atan(x, y, th, px, py)
        v = min(v_cmd, v_max)
        if k != 0:
            v = min(v, w_max/abs(k))
        om = v*k
        rows.append([x, y, th, v, om])
        if abs(om) < 1e-6:
            x, y = x + v*h*math.cos(th + om*h/2), y + v*h*math.sin(th + om*h/2)
        else:
            x, y = (x + v/om*(math.sin(th + om*h) - math.sin(th)),
                    y - v/om*(math.cos(th + om*h) - math.cos(th)))
        th += om*h
    return ['timeout', rows]


def alt_eval_squared(path, points, corridor, goal_tol):
    """Squared distances only (compares against squares), list outputs."""
    P = as_path(path)
    pts = as_points(points)
    num(corridor, 0, 100)
    num(goal_tol, 1e-3, 100)
    if corridor <= 0:
        raise ValueError

    def d2(a, b, p):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = dx*dx + dy*dy
        if n == 0:
            return (p[0] - a[0])**2 + (p[1] - a[1])**2
        t = max(0.0, min(1.0, ((p[0] - a[0])*dx + (p[1] - a[1])*dy)/n))
        return (a[0] + t*dx - p[0])**2 + (a[1] + t*dy - p[1])**2
    sq = [min(d2(P[i], P[i + 1], p) for i in range(len(P) - 1)) for p in pts]
    exit_k = next((k for k, e in enumerate(sq) if e > corridor*corridor), None)
    goal_k = next((k for k, p in enumerate(pts)
                   if (p[0] - P[-1][0])**2 + (p[1] - P[-1][1])**2 <= goal_tol*goal_tol), None)
    cut = []
    for j in range(1, len(P) - 1):
        c = (min(d2(pts[k], pts[k + 1], P[j]) for k in range(len(pts) - 1))
             if len(pts) > 1 else d2(pts[0], pts[0], P[j]))
        if c > corridor*corridor:
            cut.append(j)
    verdict = ('off-corridor' if exit_k is not None else 'timeout' if goal_k is None
               else 'corner-cut' if cut else 'ok')
    return [math.sqrt(max(sq)), math.sqrt(sum(sq)/len(sq)), exit_k, goal_k, cut, verdict]


def alt_distance_fraction(path, x, y):
    """Exact Fractions for the squared distance, float sqrt at the end."""
    P = as_path(path)
    num(x, -1000, 1000)
    num(y, -1000, 1000)
    F = Fraction
    best, best_s, walked = None, 0.0, 0.0
    for i in range(len(P) - 1):
        ax, ay, bx, by = F(P[i][0]), F(P[i][1]), F(P[i + 1][0]), F(P[i + 1][1])
        dx, dy = bx - ax, by - ay
        n = dx*dx + dy*dy
        t = max(F(0), min(F(1), ((F(x) - ax)*dx + (F(y) - ay)*dy)/n))
        d2 = (ax + t*dx - F(x))**2 + (ay + t*dy - F(y))**2
        length = math.hypot(float(dx), float(dy))
        if best is None or d2 < best:
            best, best_s = d2, walked + float(t)*length
        walked += length
    return (math.sqrt(float(best)), best_s)


alternatives = [
    ('author reference (quadratic lookahead, chord-sinc arc)', {}),
    ('complex-number distance, foot-of-perpendicular lookahead, angle-form curvature, '
     'own closed-form-arc simulate, squared-distance evaluation',
     {'path_distance': alt_distance_cross, 'lookahead_point': alt_lookahead_foot,
      'curvature': alt_curvature_atan, 'simulate': alt_sim_closed_arc,
      'evaluate_trace': alt_eval_squared}),
    ('exact Fraction limit_command and path_distance',
     {'limit_command': alt_limit_fraction, 'path_distance': alt_distance_fraction}),
    ('foot lookahead with list outputs from path_distance',
     {'lookahead_point': alt_lookahead_foot, 'path_distance': alt_distance_cross}),
    ('own simulate loop only, other functions reference',
     {'simulate': alt_sim_closed_arc}),
    ('squared-distance evaluation and angle-form curvature',
     {'evaluate_trace': alt_eval_squared, 'curvature': alt_curvature_atan}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result[:6]))


# ---- injected bugs: (label, replacement, functions that must fail) ----
def with_kw(function, **kw):
    return lambda *a: function(*a, **kw)


def accepts_when(check, function, dummy):
    def run(*args):
        if check(*args):
            return dummy
        return function(*args)
    return run


def is_real(v):
    return type(v) in (int, float) and math.isfinite(v)


def mutating_distance(path, x, y):
    result = v_distance(path, x, y)
    if isinstance(path, list):
        path.reverse()
    return result


def mutating_eval(path, points, corridor, goal_tol):
    result = v_eval(path, points, corridor, goal_tol)
    if isinstance(points, list):
        points.sort()
    return result


def eval_float_corner(path, points, corridor, goal_tol):
    out = v_eval(path, points, corridor, goal_tol)
    return (out[0], out[1], out[2], out[3], list(out[4]), out[5] + ' ')


def sim_rows_tuple_pairs(path, *a):
    status, rows = v_sim(path, *a)
    return (status, [(r[0], r[1]) for r in rows])


mutants = [
    ('distance to the first segment only', {'path_distance': with_kw(v_distance, first_only=True)},
     {'path_distance'}),
    ('distance to vertices only', {'path_distance': with_kw(v_distance, vertices_only=True)},
     {'path_distance'}),
    ('distance to infinite lines', {'path_distance': with_kw(v_distance, infinite=True)},
     {'path_distance'}),
    ('tie reports the largest s', {'path_distance': with_kw(v_distance, ties_last=True)},
     {'path_distance'}),
    ('s is the local segment length', {'path_distance': with_kw(v_distance, local_t=True)},
     {'path_distance'}),
    ('squared distance returned', {'path_distance': with_kw(v_distance, squared=True)},
     {'path_distance'}),
    ('lookahead takes the point behind (smaller root)',
     {'lookahead_point': with_kw(v_lookahead, root='t1')}, {'lookahead_point'}),
    ('lookahead prefers whichever root is on the segment',
     {'lookahead_point': with_kw(v_lookahead, root='both')}, {'lookahead_point'}),
    ('lookahead ignores start_index', {'lookahead_point': with_kw(v_lookahead, ignore_start=True)},
     {'lookahead_point'}),
    ('tangent contact rejected', {'lookahead_point': with_kw(v_lookahead, tangent=False)},
     {'lookahead_point'}),
    ('root beyond the segment clamped to its end',
     {'lookahead_point': with_kw(v_lookahead, clamp=True)}, {'lookahead_point'}),
    ('lost robot reported as end', {'lookahead_point': with_kw(v_lookahead, always_end=True)},
     {'lookahead_point'}),
    ('end reported at exactly the lookahead distance',
     {'lookahead_point': with_kw(v_lookahead, end_le=True)}, {'lookahead_point'}),
    ('vertex contact reports the higher segment',
     {'lookahead_point': with_kw(v_lookahead, tie_high=True)}, {'lookahead_point'}),
    ('segments scanned backwards', {'lookahead_point': with_kw(v_lookahead, reverse=True)},
     {'lookahead_point'}),
    ('end index 0', {'lookahead_point': with_kw(v_lookahead, end_index=0)}, {'lookahead_point'}),
    ('curvature sign flipped', {'curvature': with_kw(v_curvature, mode='flip')}, {'curvature'}),
    ('curvature ignores heading', {'curvature': with_kw(v_curvature, mode='world')}, {'curvature'}),
    ('curvature missing the factor 2', {'curvature': with_kw(v_curvature, mode='no-two')},
     {'curvature'}),
    ('curvature 2*y_L/distance', {'curvature': with_kw(v_curvature, mode='sine')}, {'curvature'}),
    ('rotation applied with the wrong sign', {'curvature': with_kw(v_curvature, mode='rot-sign')},
     {'curvature'}),
    ('heading treated as degrees', {'curvature': with_kw(v_curvature, mode='degrees')},
     {'curvature'}),
    ('omega clipped alone', {'limit_command': with_kw(v_limit, mode='clip-omega')},
     {'limit_command'}),
    ('speed limit ignored', {'limit_command': with_kw(v_limit, mode='no-vmax')}, {'limit_command'}),
    ('spin in place when over the turn-rate limit',
     {'limit_command': with_kw(v_limit, mode='spin')}, {'limit_command'}),
    ('omega from the unclipped speed', {'limit_command': with_kw(v_limit, mode='stale-v')},
     {'limit_command'}),
    ('timeout checked before the goal', {'simulate': with_kw(v_sim, timeout_first=True)},
     {'simulate'}),
    ('goal tolerance strict', {'simulate': with_kw(v_sim, strict=True)}, {'simulate'}),
    ('no final row', {'simulate': with_kw(v_sim, no_final=True)}, {'simulate'}),
    ('final row keeps the last command', {'simulate': with_kw(v_sim, final_keeps=True)},
     {'simulate'}),
    ('Euler update instead of the exact arc', {'simulate': with_kw(v_sim, euler=True)},
     {'simulate'}),
    ('heading never updated', {'simulate': with_kw(v_sim, no_theta=True)}, {'simulate'}),
    ('lost robot steered at the goal', {'simulate': with_kw(v_sim, lost_to_goal=True)},
     {'simulate'}),
    ('saturation skipped in the loop', {'simulate': with_kw(v_sim, no_limit=True)}, {'simulate'}),
    ('row records the next pose', {'simulate': with_kw(v_sim, post_row=True)}, {'simulate'}),
    ('goal never stops the run', {'simulate': with_kw(v_sim, ignore_goal=True)}, {'simulate'}),
    ('rows hold only x and y', {'simulate': sim_rows_tuple_pairs}, {'simulate'}),
    ('goal distance strict', {'evaluate_trace': with_kw(v_eval, strict_goal=True)},
     {'evaluate_trace'}),
    ('corridor edge counts as an exit', {'evaluate_trace': with_kw(v_eval, corr_ge=True)},
     {'evaluate_trace'}),
    ('goal reached hides an exit', {'evaluate_trace': with_kw(v_eval, verdict_goal=True)},
     {'evaluate_trace'}),
    ('clearance to samples only', {'evaluate_trace': with_kw(v_eval, samples_only=True)},
     {'evaluate_trace'}),
    ('mean error instead of RMS', {'evaluate_trace': with_kw(v_eval, mean_not_rms=True)},
     {'evaluate_trace'}),
    ('RMS with n-1', {'evaluate_trace': with_kw(v_eval, sample_var=True)}, {'evaluate_trace'}),
    ('signed errors', {'evaluate_trace': with_kw(v_eval, signed=True)}, {'evaluate_trace'}),
    ('first_exit one-based', {'evaluate_trace': with_kw(v_eval, one_based=True)},
     {'evaluate_trace'}),
    ('end points counted as corners', {'evaluate_trace': with_kw(v_eval, endpoints=True)},
     {'evaluate_trace'}),
    ('corner-cut outranks timeout', {'evaluate_trace': with_kw(v_eval, cut_before_timeout=True)},
     {'evaluate_trace'}),
    ('only the first cut corner listed', {'evaluate_trace': with_kw(v_eval, first_cut_only=True)},
     {'evaluate_trace'}),
    ('verdict string padded', {'evaluate_trace': eval_float_corner}, {'evaluate_trace'}),
    ('path_distance mutates the path', {'path_distance': mutating_distance}, {'path_distance'}),
    ('evaluate_trace sorts the points', {'evaluate_trace': mutating_eval}, {'evaluate_trace'}),
    ('bool x accepted', {'path_distance': accepts_when(
        lambda p, x, y: type(x) is bool, v_distance, (0.0, 0.0))}, {'path_distance'}),
    ('NaN lookahead accepted', {'lookahead_point': accepts_when(
        lambda *a: type(a[3]) is float and a[3] != a[3], v_lookahead, ('none', None, None, 0))},
     {'lookahead_point'}),
    ('bool start_index accepted', {'lookahead_point': accepts_when(
        lambda *a: len(a) > 4 and type(a[4]) is bool, v_lookahead, ('none', None, None, 0))},
     {'lookahead_point'}),
    ('path with equal consecutive points accepted', {'lookahead_point': accepts_when(
        lambda p, *a: isinstance(p, list) and len(p) > 2 and p[2] == p[1] and p[1] != p[0],
        v_lookahead, ('none', None, None, 0))}, {'lookahead_point'}),
    ('target on the robot accepted', {'curvature': accepts_when(
        lambda x, y, th, tx, ty: tx == x and ty == y, v_curvature, 0.0)}, {'curvature'}),
    ('negative speed accepted', {'limit_command': accepts_when(
        lambda v, *a: is_real(v) and v < 0, v_limit, (0.0, 0.0))}, {'limit_command'}),
    ('zero w_max accepted', {'limit_command': accepts_when(
        lambda v, k, vm, wm: is_real(wm) and wm == 0, v_limit, (0.0, 0.0))}, {'limit_command'}),
    ('float max_steps accepted', {'simulate': lambda *a: v_sim(*a[:10], int(a[10]))
                                  if type(a[10]) is float and math.isfinite(a[10]) and a[10] >= 1
                                  else v_sim(*a)}, {'simulate'}),
    ('51-point path accepted', {'path_distance': accepts_when(
        lambda p, *a: isinstance(p, list) and len(p) == 51, v_distance, (0.0, 0.0))},
     {'path_distance'}),
    ('empty points accepted', {'evaluate_trace': accepts_when(
        lambda p, pts, *a: isinstance(pts, (list, tuple)) and len(pts) == 0, v_eval,
        (0.0, 0.0, None, None, (), 'timeout'))}, {'evaluate_trace'}),
    ('NaN corridor accepted', {'evaluate_trace': accepts_when(
        lambda p, pts, c, g: type(c) is float and c != c, v_eval,
        (0.0, 0.0, None, None, (), 'timeout'))}, {'evaluate_trace'}),
]
for label, over, expected in mutants:
    result = run_with(over)
    require(result, 'false accept: ' + label)
    require(failing(result) == expected,
            'mutant ' + label + ' failed for the wrong reason: ' + str(failing(result))
            + ' ' + str(result[:3]))
require(len(mutants) >= 30, 'need at least 30 mutants')
print('Navigation kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different Jacobian formulations,
IK branch formulas and numerical solvers) that must pass, and named injected
bugs that must be rejected. Plain checks only, so it also works under python -O.
"""
import ast
import cmath
import importlib.util
import json
import math
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('jacobian_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L06-jacobian-ik.v1.py'
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
names = ('jacobian', 'jacobian_det', 'tip_velocity', 'ik_branches', 'solve_ik_numeric')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names + ('fk',)),
        'starter functions and the given fk must sit above the spoiler banner')
require(text.index('def _jacobian_ref') > spoiler and text.index('def _configurations') > spoiler,
        'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('jacobian_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter_notes = []
starter = kit.self_check(starter_notes)
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 4 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented core function into one line: ' + str(starter))
require(starter_notes == [n for n in starter_notes if n.startswith('optional: solve_ik_numeric')]
        and len(starter_notes) == 1, 'starter must note the optional solver once')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def encode(value):
    return [encode(v) for v in value] if isinstance(value, (list, tuple)) else dec(value)


def entry(structure, names_, args):
    return {'structure': structure,
            'inputs': {name: encode(value) for name, value in zip(names_, args)}}


expected_samples = (
    [entry('jacobian.matrix@1', ('q1', 'q2', 'l1', 'l2'), case[0]) for case in kit._J_CASES]
    + [entry('jacobian.det@1', ('q1', 'q2', 'l1', 'l2'), args) for args, _ in kit._DET_CASES]
    + [entry('jacobian.tip-velocity@1', ('q1', 'q2', 'l1', 'l2', 'dq1', 'dq2'), args)
       for args, _ in kit._TIP_CASES]
    + [entry('ik.branches@1', ('x', 'y', 'l1', 'l2', 'limits'), args)
       for args, _ in kit._IK_CASES]
    + [entry('ik.numeric@1', ('x', 'y', 'l1', 'l2', 'q_init', 'limits', 'tol', 'max_iter'), args)
       for _, args in kit._NUM_CASES])
samples = json.loads((root / 'content/labs/L06-jacobian-ik.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L06-jacobian-ik'], 'samples must hold only L06-jacobian-ik')
require(samples['kits']['L06-jacobian-ik'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50')


# ---- independent cross-check of the hand-derived tables ----
for args, mode, want in kit._J_CASES:
    if mode == 'hand':
        got = kit._jacobian_ref(*args)
        require(all(abs(got[r][c] - want[r][c]) <= 1e-12 for r in range(2) for c in range(2)),
                'hand Jacobian table disagrees with the expansion: ' + repr(args))
for args, want in kit._DET_CASES:
    if want is not None:
        require(abs(args[2]*args[3]*math.sin(args[1]) - want) <= 1e-12,
                'hand det table disagrees with l1*l2*sin(q2): ' + repr(args))


for args, count in kit._IK_CASES:
    x, y, l1, l2 = args[:4]
    lim = args[4] if len(args) > 4 else None
    configs = kit._configurations(x, y, l1, l2)
    if lim is not None:
        configs = [c for c in configs if kit._admissible(c[0], *lim[0], 1e-9)
                   and kit._admissible(c[1], *lim[1], 1e-9)]
    require(len(configs) == count, 'IK count table disagrees with the oracle: ' + repr(args))


# ---- author reference implementation ----
TWO_PI = 2*math.pi


def real(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def arm(q1, q2, l1, l2):
    real(q1, -TWO_PI, TWO_PI)
    real(q2, -TWO_PI, TWO_PI)
    real(l1, 0.01, 10)
    real(l2, 0.01, 10)


def check_limits(limits):
    if not isinstance(limits, (list, tuple)) or len(limits) != 2:
        raise ValueError
    for pair in limits:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError
        real(pair[0], -TWO_PI, TWO_PI)
        real(pair[1], -TWO_PI, TWO_PI)
        if pair[0] > pair[1]:
            raise ValueError
    return ((limits[0][0], limits[0][1]), (limits[1][0], limits[1][1]))


def target(x, y, l1, l2):
    real(x, -25, 25)
    real(y, -25, 25)
    real(l1, 0.01, 10)
    real(l2, 0.01, 10)


def raw_fk(q1, q2, l1, l2):
    return (l1*math.cos(q1) + l2*math.cos(q1 + q2), l1*math.sin(q1) + l2*math.sin(q1 + q2))


def raw_jacobian(q1, q2, l1, l2):
    s1, c1, s12, c12 = math.sin(q1), math.cos(q1), math.sin(q1 + q2), math.cos(q1 + q2)
    return [[-l1*s1 - l2*s12, -l2*s12], [l1*c1 + l2*c12, l2*c12]]


def jacobian(q1, q2, l1, l2):
    arm(q1, q2, l1, l2)
    return raw_jacobian(q1, q2, l1, l2)


def jacobian_det(q1, q2, l1, l2):
    arm(q1, q2, l1, l2)
    return l1*l2*math.sin(q2)


def tip_velocity(q1, q2, l1, l2, dq1, dq2):
    arm(q1, q2, l1, l2)
    real(dq1, -100, 100)
    real(dq2, -100, 100)
    J = raw_jacobian(q1, q2, l1, l2)
    return (J[0][0]*dq1 + J[0][1]*dq2, J[1][0]*dq1 + J[1][1]*dq2)


def reachable(x, y, l1, l2):
    r = math.hypot(x, y)
    return abs(l1 - l2) - 1e-9 <= r <= l1 + l2 + 1e-9


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def same(p, q):
    return abs(wrap(p[0] - q[0])) <= 1e-6 and abs(wrap(p[1] - q[1])) <= 1e-6


def representative(angle, low, high):
    for k in (0, -1, 1, -2, 2, -3, 3):
        value = angle + TWO_PI*k
        if low - 1e-9 <= value <= high + 1e-9:
            return min(max(value, low), high)
    return None


def admit(candidates, limits):
    found = []
    for q1, q2 in candidates:
        if limits is not None:
            q1 = representative(q1, *limits[0])
            q2 = representative(q2, *limits[1])
            if q1 is None or q2 is None:
                continue
        if not any(same((q1, q2), p) for p in found):
            found.append((q1, q2))
    return found


def ik_validate(x, y, l1, l2, limits):
    target(x, y, l1, l2)
    if limits is not None:
        limits = check_limits(limits)
    if x == 0 and y == 0 and abs(l1 - l2) <= 1e-9:
        raise ValueError('base-singular target: every q1 works')
    return limits


def ik_branches(x, y, l1, l2, limits=None):
    limits = ik_validate(x, y, l1, l2, limits)
    if not reachable(x, y, l1, l2):
        return []
    c2 = max(-1.0, min(1.0, (x*x + y*y - l1*l1 - l2*l2)/(2*l1*l2)))
    s2 = math.sqrt(1 - c2*c2)
    candidates = []
    for s in (s2, -s2):
        q2 = math.atan2(s, c2)
        q1 = math.atan2(y, x) - math.atan2(l2*s, l1 + l2*c2)
        candidates.append((q1, q2))
    return admit(candidates, limits)


def numeric_validate(x, y, l1, l2, q_init, limits, tol, max_iter):
    target(x, y, l1, l2)
    limits = check_limits(limits)
    if not isinstance(q_init, (list, tuple)) or len(q_init) != 2:
        raise ValueError
    for k in range(2):
        real(q_init[k], limits[k][0], limits[k][1])
    real(tol, 1e-12, 1)
    if type(max_iter) is not int or not 0 <= max_iter <= 1000:
        raise ValueError
    return limits


def clamp(q, limits):
    return [min(max(q[k], limits[k][0]), limits[k][1]) for k in range(2)]


def residual_of(q, x, y, l1, l2):
    fx, fy = raw_fk(q[0], q[1], l1, l2)
    return math.hypot(fx - x, fy - y)


def solve2(A, b):
    det = A[0][0]*A[1][1] - A[0][1]*A[1][0]
    return [(A[1][1]*b[0] - A[0][1]*b[1])/det, (A[0][0]*b[1] - A[1][0]*b[0])/det]


def dls_step(q, ex, ey, l1, l2, lam):
    J = raw_jacobian(q[0], q[1], l1, l2)
    A = [[J[0][0]**2 + J[0][1]**2 + lam*lam, J[0][0]*J[1][0] + J[0][1]*J[1][1]],
         [J[0][0]*J[1][0] + J[0][1]*J[1][1], J[1][0]**2 + J[1][1]**2 + lam*lam]]
    w = solve2(A, [ex, ey])
    return [J[0][0]*w[0] + J[1][0]*w[1], J[0][1]*w[0] + J[1][1]*w[1]]


def make_solver(step_rule, best=False):
    """Shared shell: validation, reach rule, check-before-step, clamped updates."""
    def solve(x, y, l1, l2, q_init, limits, tol, max_iter):
        limits = numeric_validate(x, y, l1, l2, q_init, limits, tol, max_iter)
        q = [q_init[0], q_init[1]]
        if not reachable(x, y, l1, l2):
            return ('unreachable', q, residual_of(q, x, y, l1, l2), 0)
        kept, kept_res = q, residual_of(q, x, y, l1, l2)
        steps = 0
        while True:
            res = residual_of(q, x, y, l1, l2)
            if best and res < kept_res:
                kept, kept_res = q, res
            if res <= tol:
                return ('converged', q, res, steps)
            if steps == max_iter:
                break
            fx, fy = raw_fk(q[0], q[1], l1, l2)
            q = clamp(step_rule(q, x - fx, y - fy, l1, l2, x, y), limits)
            steps += 1
        if best:
            return ('not_converged', kept, kept_res, steps)
        return ('not_converged', q, res, steps)
    return solve


def dls_rule(lam, cap=None):
    """Damped least squares; optional trust-region cap on the step length (rad)."""
    def rule(q, ex, ey, l1, l2, x, y):
        d = dls_step(q, ex, ey, l1, l2, lam)
        size = math.hypot(d[0], d[1])
        if cap is not None and size > cap:
            d = [d[0]*cap/size, d[1]*cap/size]
        return [q[0] + d[0], q[1] + d[1]]
    return rule


solve_ik_numeric = make_solver(dls_rule(0.01, 0.5))
refs = {'jacobian': jacobian, 'jacobian_det': jacobian_det, 'tip_velocity': tip_velocity,
        'ik_branches': ik_branches, 'solve_ik_numeric': solve_ik_numeric}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


# ---- valid alternatives ----
def jacobian_complex(q1, q2, l1, l2):
    """d(tip)/dq1 = i*tip and d(tip)/dq2 = i*l2*e^{i(q1+q2)}, as complex numbers."""
    arm(q1, q2, l1, l2)
    outer = l2*cmath.exp(1j*(q1 + q2))
    tip = l1*cmath.exp(1j*q1) + outer
    c1, c2 = 1j*tip, 1j*outer
    return ((c1.real, c2.real), (c1.imag, c2.imag))


def det_complex(q1, q2, l1, l2):
    (a, b), (c, d) = jacobian_complex(q1, q2, l1, l2)
    return a*d - b*c


def tip_complex(q1, q2, l1, l2, dq1, dq2):
    arm(q1, q2, l1, l2)
    real(dq1, -100, 100)
    real(dq2, -100, 100)
    outer = l2*cmath.exp(1j*(q1 + q2))
    v = 1j*(l1*cmath.exp(1j*q1)*dq1 + outer*(dq1 + dq2))
    return [v.real, v.imag]


def ik_acos_shoulder(x, y, l1, l2, limits=None):
    """Shoulder from the law of cosines in the base triangle; elbow-down first; tuples."""
    limits = ik_validate(x, y, l1, l2, limits)
    if not reachable(x, y, l1, l2):
        return ()
    r = math.hypot(x, y)
    c2 = max(-1.0, min(1.0, (r*r - l1*l1 - l2*l2)/(2*l1*l2)))
    beta = math.acos(max(-1.0, min(1.0, (r*r + l1*l1 - l2*l2)/(2*l1*r))))
    phi = math.atan2(y, x)
    candidates = [(phi + beta, -math.acos(c2)), (phi - beta, math.acos(c2))]
    return tuple(tuple(p) for p in admit(candidates, limits))


def ik_complex(x, y, l1, l2, limits=None):
    """Elbow position as a circle intersection in the complex plane; wraps by fmod."""
    limits = ik_validate(x, y, l1, l2, limits)
    if not reachable(x, y, l1, l2):
        return []
    t = complex(x, y)
    r = abs(t)
    along = max(-l1, min(l1, (r*r + l1*l1 - l2*l2)/(2*r)))
    across = math.sqrt(max(0.0, l1*l1 - along*along))
    unit = t/r
    found = []
    for side in (1, -1):
        elbow = unit*complex(along, side*across)
        q1 = cmath.phase(elbow)
        q2 = math.fmod(cmath.phase(t - elbow) - q1, TWO_PI)
        found.append([q1, q2])
    result = []
    for q1, q2 in found:
        if limits is not None:
            ok = []
            for angle, (low, high) in zip((q1, q2), limits):
                choice = None
                for k in range(-3, 4):
                    value = angle + TWO_PI*k
                    if low - 1e-9 <= value <= high + 1e-9:
                        choice = value
                        break
                ok.append(choice)
            if None in ok:
                continue
            q1, q2 = ok
        else:
            q1, q2 = wrap(q1), wrap(q2)
        if not any(same((q1, q2), p) for p in result):
            result.append([q1, q2])
    return result


def newton_limited_rule(q, ex, ey, l1, l2, x, y):
    """Newton step from the exact inverse, length limited to 0.5 rad; DLS if singular."""
    J = raw_jacobian(q[0], q[1], l1, l2)
    det = J[0][0]*J[1][1] - J[0][1]*J[1][0]
    if abs(det) < 1e-9:
        d = dls_step(q, ex, ey, l1, l2, 0.05)
    else:
        d = [(J[1][1]*ex - J[0][1]*ey)/det, (J[0][0]*ey - J[1][0]*ex)/det]
    size = math.hypot(d[0], d[1])
    if size > 0.5:
        d = [d[0]*0.5/size, d[1]*0.5/size]
    return [q[0] + d[0], q[1] + d[1]]


def line_search_solver(x, y, l1, l2, q_init, limits, tol, max_iter):
    """Gauss-Newton direction (lam = 1e-3) with backtracking on the clamped residual;
    stops early ('not_converged') when no clamped trial decreases the residual."""
    lim = numeric_validate(x, y, l1, l2, q_init, limits, tol, max_iter)
    q = (q_init[0], q_init[1])
    res = residual_of(q, x, y, l1, l2)
    if not reachable(x, y, l1, l2):
        return ('unreachable', q, res, 0)
    for steps in range(max_iter + 1):
        if res <= tol:
            return ('converged', q, res, steps)
        if steps == max_iter:
            break
        fx, fy = raw_fk(q[0], q[1], l1, l2)
        d = dls_step(q, x - fx, y - fy, l1, l2, 1e-3)
        alpha = min(1.0, 1.0/max(1e-300, math.hypot(d[0], d[1])))
        for _ in range(60):
            trial = tuple(clamp([q[0] + alpha*d[0], q[1] + alpha*d[1]], lim))
            trial_res = residual_of(trial, x, y, l1, l2)
            if trial_res < res:
                break
            alpha *= 0.5
        else:
            return ('not_converged', q, res, steps)
        q, res = trial, trial_res
    return ('not_converged', q, res, max_iter)


def solve_seeded(x, y, l1, l2, q_init, limits, tol, max_iter):
    """Analytic seeding: one step jumps to the admissible branch nearest q_init."""
    lim = numeric_validate(x, y, l1, l2, q_init, limits, tol, max_iter)
    q = (float(q_init[0]), float(q_init[1]))
    res = residual_of(q, x, y, l1, l2)
    if not reachable(x, y, l1, l2):
        return ['unreachable', q, res, 0]
    if res <= tol:
        return ['converged', q, res, 0]
    if max_iter == 0:
        return ['not_converged', q, res, 0]
    if x == 0 and y == 0:
        options = [(q[0], representative(math.pi, *lim[1]))]
        options = [p for p in options if p[1] is not None]
    else:
        options = ik_branches(x, y, l1, l2, lim)
    if not options:
        return ['not_converged', q, res, 0]
    best = min(options, key=lambda p: abs(p[0] - q[0]) + abs(p[1] - q[1]))
    best = tuple(clamp(best, lim))
    final = residual_of(best, x, y, l1, l2)
    return ['converged' if final <= tol else 'not_converged', best, final, 1]


def ik_tan_half(x, y, l1, l2, limits=None):
    """Tangent half-angle form for q2; branch order (+, -); lists."""
    limits = ik_validate(x, y, l1, l2, limits)
    if not reachable(x, y, l1, l2):
        return []
    r2 = x*x + y*y
    num = max(0.0, (l1 + l2)**2 - r2)
    den = max(0.0, r2 - (l1 - l2)**2)
    q2 = math.pi if den == 0 else 2*math.atan(math.sqrt(num/den))
    cands = []
    for t2 in (q2, -q2):
        cands.append((math.atan2(y, x) - math.atan2(l2*math.sin(t2), l1 + l2*math.cos(t2)), t2))
    return [list(p) for p in admit(cands, limits)]


def solver_not_attempted(*args):
    raise NotImplementedError("optional solver left as the starter")


alternatives = [
    ('author: sin/cos J, atan2 branches, DLS lam = 0.01', {}),
    ('complex-number J and tip velocity, circle-intersection IK, DLS lam = 0.1 (no cap)',
     {'jacobian': jacobian_complex, 'jacobian_det': det_complex, 'tip_velocity': tip_complex,
      'ik_branches': ik_complex, 'solve_ik_numeric': make_solver(dls_rule(0.1))}),
    ('law-of-cosines shoulder, elbow-down first, tuples; step-limited Newton',
     {'ik_branches': ik_acos_shoulder, 'solve_ik_numeric': make_solver(newton_limited_rule)}),
    ('Gauss-Newton with backtracking line search, early stop, tuples',
     {'solve_ik_numeric': line_search_solver}),
    ('analytic seeding from ik_branches; DLS lam = 1e-3',
     {'solve_ik_numeric': solve_seeded}),
    ('tangent half-angle IK, optional solver not attempted',
     {'ik_branches': ik_tan_half, 'solve_ik_numeric': solver_not_attempted}),
    ('DLS lam = 1e-3 capped at 0.3 rad, best-so-far result, complex J',
     {'jacobian': jacobian_complex,
      'solve_ik_numeric': make_solver(dls_rule(1e-3, 0.3), best=True)}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))
notes = []
setattr(kit, 'solve_ik_numeric', solver_not_attempted)
require(kit.self_check(notes) == [] and len(notes) == 1 and notes[0].startswith('optional:'),
        'an unattempted optional solver must give one note and no failure')
setattr(kit, 'solve_ik_numeric', solve_ik_numeric)


# ---- injected bugs ----
def j_rule(rule):
    def run(q1, q2, l1, l2):
        arm(q1, q2, l1, l2)
        return rule(q1, q2, l1, l2)
    return run


def det_rule(rule):
    def run(q1, q2, l1, l2):
        arm(q1, q2, l1, l2)
        return rule(q1, q2, l1, l2)
    return run


def tip_rule(rule):
    def run(q1, q2, l1, l2, dq1, dq2):
        arm(q1, q2, l1, l2)
        real(dq1, -100, 100)
        real(dq2, -100, 100)
        return rule(raw_jacobian(q1, q2, l1, l2), dq1, dq2)
    return run


def forward_difference(h):
    def rule(q1, q2, l1, l2):
        f = raw_fk(q1, q2, l1, l2)
        a = raw_fk(q1 + h, q2, l1, l2)
        b = raw_fk(q1, q2 + h, l1, l2)
        return [[(a[0] - f[0])/h, (b[0] - f[0])/h], [(a[1] - f[1])/h, (b[1] - f[1])/h]]
    return rule


def central_difference(h):
    def rule(q1, q2, l1, l2):
        a, b = raw_fk(q1 + h, q2, l1, l2), raw_fk(q1 - h, q2, l1, l2)
        c, d = raw_fk(q1, q2 + h, l1, l2), raw_fk(q1, q2 - h, l1, l2)
        return [[(a[0] - b[0])/(2*h), (c[0] - d[0])/(2*h)],
                [(a[1] - b[1])/(2*h), (c[1] - d[1])/(2*h)]]
    return rule


def ik_rule(rule):
    """ik_branches with full validation and a replaceable candidate generator."""
    def run(x, y, l1, l2, limits=None):
        lim = ik_validate(x, y, l1, l2, limits)
        return rule(x, y, l1, l2, lim)
    return run


def candidates(x, y, l1, l2, flip=1):
    c2 = max(-1.0, min(1.0, (x*x + y*y - l1*l1 - l2*l2)/(2*l1*l2)))
    s2 = math.sqrt(1 - c2*c2)
    out = []
    for s in (s2, -s2):
        q2 = math.atan2(s, c2)
        out.append((math.atan2(y, x) - flip*math.atan2(l2*s, l1 + l2*c2), q2))
    return out


def ik_one_branch(x, y, l1, l2, lim):
    return admit(candidates(x, y, l1, l2)[:1], lim) if reachable(x, y, l1, l2) else []


def ik_wrong_sign(x, y, l1, l2, lim):
    return admit(candidates(x, y, l1, l2, flip=-1), lim) if reachable(x, y, l1, l2) else []


def ik_no_limits(x, y, l1, l2, lim):
    return ik_branches(x, y, l1, l2)


def ik_nearest(x, y, l1, l2, lim):
    if reachable(x, y, l1, l2):
        return ik_branches(x, y, l1, l2, lim)
    r = math.hypot(x, y)
    scale = (l1 + l2)/r if r > l1 + l2 else max(abs(l1 - l2), 1e-9)/max(r, 1e-12)
    return ik_branches(x*scale if r else abs(l1 - l2), y*scale, l1, l2, lim)


def ik_duplicates(x, y, l1, l2, lim):
    if not reachable(x, y, l1, l2):
        return []
    out = []
    for q1, q2 in candidates(x, y, l1, l2):
        if lim is not None:
            q1, q2 = representative(q1, *lim[0]), representative(q2, *lim[1])
            if q1 is None or q2 is None:
                continue
        out.append((q1, q2))
    return out


def ik_exact_dedupe(x, y, l1, l2, lim):
    out = ik_duplicates(x, y, l1, l2, lim)
    return out[:1] if len(out) == 2 and tuple(out[0]) == tuple(out[1]) else out


def ik_strict_reach(x, y, l1, l2, lim):
    r = math.hypot(x, y)
    if not abs(l1 - l2) <= r <= l1 + l2:
        return []
    c2 = (x*x + y*y - l1*l1 - l2*l2)/(2*l1*l2)
    q2 = math.acos(c2)
    cands = [(math.atan2(y, x) - math.atan2(l2*math.sin(s), l1 + l2*math.cos(s)), s)
             for s in (q2, -q2)]
    return admit(cands, lim)


def ik_raw_limits(x, y, l1, l2, lim):
    """Checks the limits against the atan2 values only (no 2*pi representative)."""
    out = ik_branches(x, y, l1, l2)
    if lim is None:
        return out
    return [p for p in out if all(lim[k][0] - 1e-9 <= p[k] <= lim[k][1] + 1e-9 for k in range(2))]


def ik_strict_limits(x, y, l1, l2, lim):
    """No slack at a limit: a solution that rounds a hair outside is dropped."""
    out = ik_branches(x, y, l1, l2, lim)
    if lim is None or not reachable(x, y, l1, l2):
        return out
    kept = []
    for p in candidates(x, y, l1, l2):
        q = [next((p[k] + TWO_PI*j for j in range(-3, 4)
                   if lim[k][0] <= p[k] + TWO_PI*j <= lim[k][1]), None) for k in range(2)]
        if None not in q and not any(same(q, e) for e in kept):
            kept.append(q)
    return kept


def ik_all_representatives(x, y, l1, l2, lim):
    out = ik_branches(x, y, l1, l2, lim)
    if lim is None:
        return out
    extra = []
    for q1, q2 in out:
        for k in (-1, 1):
            if lim[0][0] <= q1 + TWO_PI*k <= lim[0][1]:
                extra.append((q1 + TWO_PI*k, q2))
    return [out[0], extra[0]] if extra else out


def ik_degrees(x, y, l1, l2, lim):
    return [(math.degrees(a), math.degrees(b)) for a, b in ik_branches(x, y, l1, l2, lim)]


def ik_swapped_links(x, y, l1, l2, lim):
    return admit(candidates(x, y, l2, l1), lim) if reachable(x, y, l1, l2) else []


def ik_atan_quadrant(x, y, l1, l2, lim):
    if not reachable(x, y, l1, l2):
        return []
    out = []
    for q1, q2 in candidates(x, y, l1, l2):
        phi = math.atan(y/x) if x != 0 else math.copysign(math.pi/2, y)
        out.append((q1 - math.atan2(y, x) + phi, q2))
    return admit(out, lim)


def ik_base_empty(x, y, l1, l2, limits=None):
    if x == 0 and y == 0:
        target(x, y, l1, l2)
        return []
    return ik_branches(x, y, l1, l2, limits)


def ik_base_point(x, y, l1, l2, limits=None):
    if x == 0 and y == 0 and l1 == l2:
        target(x, y, l1, l2)
        return [(0.0, math.pi)]
    return ik_branches(x, y, l1, l2, limits)


def ik_mutating(x, y, l1, l2, limits=None):
    out = ik_branches(x, y, l1, l2, limits)
    if isinstance(limits, list) and isinstance(limits[0], list):
        limits[0][0] = max(limits[0][0], -math.pi/2)
    return out


def solver_shell(body):
    def solve(x, y, l1, l2, q_init, limits, tol, max_iter):
        lim = numeric_validate(x, y, l1, l2, q_init, limits, tol, max_iter)
        return body(x, y, l1, l2, q_init, lim, tol, max_iter)
    return solve


def converged_blindly(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return ('converged' if status == 'not_converged' else status, q, res, steps)


def cap_is_unreachable(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return ('unreachable' if status == 'not_converged' else status, q, res, steps)


def no_reach_test(x, y, l1, l2, q_init, lim, tol, max_iter):
    rule = dls_rule(0.01, 0.5)
    q, steps = [q_init[0], q_init[1]], 0
    while True:
        res = residual_of(q, x, y, l1, l2)
        if res <= tol:
            return ('converged', q, res, steps)
        if steps == max_iter:
            return ('not_converged', q, res, steps)
        fx, fy = raw_fk(q[0], q[1], l1, l2)
        q = clamp(rule(q, x - fx, y - fy, l1, l2, x, y), lim)
        steps += 1


def ignores_q_init(x, y, l1, l2, q_init, lim, tol, max_iter):
    start = [(lim[0][0] + lim[0][1])/2, (lim[1][0] + lim[1][1])/2]
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, start, lim, tol, max_iter)
    if status == 'unreachable':
        q = [q_init[0], q_init[1]]
        res = residual_of(q, x, y, l1, l2)
    return (status, q, res, steps)


def step_before_check(x, y, l1, l2, q_init, lim, tol, max_iter):
    if not reachable(x, y, l1, l2) or max_iter == 0:
        return solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    fx, fy = raw_fk(q_init[0], q_init[1], l1, l2)
    q = clamp(dls_rule(0.01, 0.5)(list(q_init), x - fx, y - fy, l1, l2, x, y), lim)
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q, lim, tol, max_iter - 1)
    return (status, q, res, steps + 1)


def no_projection(x, y, l1, l2, q_init, lim, tol, max_iter):
    wide = ((-TWO_PI, TWO_PI), (-TWO_PI, TWO_PI))
    return solve_ik_numeric(x, y, l1, l2, q_init, wide, tol, max_iter)


def stale_residual(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    if steps:
        res = residual_of(q_init, x, y, l1, l2)
    return (status, q, res, steps)


def squared_residual(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return (status, q, res*res, steps)


def extra_step_count(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return (status, q, res, steps + 1 if status == 'not_converged' else steps)


def transpose_rule(q, ex, ey, l1, l2, x, y):
    J = raw_jacobian(q[0], q[1], l1, l2)
    return [q[0] + 0.01*(J[0][0]*ex + J[1][0]*ey), q[1] + 0.01*(J[0][1]*ex + J[1][1]*ey)]


def undamped_newton_rule(q, ex, ey, l1, l2, x, y):
    J = raw_jacobian(q[0], q[1], l1, l2)
    det = J[0][0]*J[1][1] - J[0][1]*J[1][0]
    if det == 0:
        det = 1e-300
    return [q[0] + (J[1][1]*ex - J[0][1]*ey)/det, q[1] + (J[0][0]*ey - J[1][0]*ex)/det]


def unreachable_moves(x, y, l1, l2, q_init, lim, tol, max_iter):
    if reachable(x, y, l1, l2):
        return solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    status, q, res, steps = no_reach_test(x, y, l1, l2, q_init, lim, 1e-12, max_iter)
    return ('unreachable', q, res, steps)


def mutating_solver(x, y, l1, l2, q_init, limits, tol, max_iter):
    result = solve_ik_numeric(x, y, l1, l2, q_init, limits, tol, max_iter)
    if isinstance(q_init, list):
        q_init[0], q_init[1] = result[1][0], result[1][1]
    return result


def wrong_case_status(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return (status.capitalize(), q, res, steps)


def float_steps(x, y, l1, l2, q_init, lim, tol, max_iter):
    status, q, res, steps = solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)
    return (status, q, res, float(steps))


def accepts_when(check, function, value):
    """Full validation except one named gap: returns a plausible value instead."""
    def run(*args):
        if check(*args):
            return value
        return function(*args)
    return run


def is_nan(v):
    return type(v) is float and v != v


def floats_only(function):
    def run(*args):
        if not all(type(v) is float for v in args if not isinstance(v, (list, tuple))):
            raise ValueError
        return function(*args)
    return run


def ik_merge_c2(x, y, l1, l2, lim):
    """One solution whenever |c2| is within 1e-9 of 1 (over-merging)."""
    out = ik_branches(x, y, l1, l2, lim)
    c2 = (x*x + y*y - l1*l1 - l2*l2)/(2*l1*l2)
    return out[:1] if abs(abs(c2) - 1) <= 1e-9 else out


def ik_merge_close(tolerance):
    def rule(x, y, l1, l2, lim):
        out = ik_branches(x, y, l1, l2, lim)
        if (len(out) == 2 and abs(wrap(out[0][0] - out[1][0])) <= tolerance
                and abs(wrap(out[0][1] - out[1][1])) <= tolerance):
            return out[:1]
        return out
    return rule


def ik_with_representative(pick):
    def rule(x, y, l1, l2, lim):
        if not reachable(x, y, l1, l2):
            return []
        found = []
        for p in candidates(x, y, l1, l2):
            q = list(p)
            if lim is not None:
                q = [pick(q[k], lim[k][0], lim[k][1]) for k in range(2)]
                if None in q:
                    continue
            if not any(same(q, f) for f in found):
                found.append(q)
        return found
    return rule


def plus_only(angle, low, high):
    if angle < low - 1e-9:
        angle += TWO_PI
    return angle if low - 1e-9 <= angle <= high + 1e-9 else None


def wrap_then_up(angle, low, high):
    angle = wrap(angle)
    for k in (0, 1):
        if low - 1e-9 <= angle + TWO_PI*k <= high + 1e-9:
            return angle + TWO_PI*k
    return None


def wide_slack(angle, low, high):
    for k in range(-3, 4):
        if low - 1e-4 <= angle + TWO_PI*k <= high + 1e-4:
            return min(max(angle + TWO_PI*k, low), high)
    return None


def ik_unclamped_shoulder(x, y, l1, l2, limits=None):
    limits = ik_validate(x, y, l1, l2, limits)
    if not reachable(x, y, l1, l2):
        return []
    r = math.hypot(x, y)
    c2 = max(-1.0, min(1.0, (r*r - l1*l1 - l2*l2)/(2*l1*l2)))
    beta = math.acos((r*r + l1*l1 - l2*l2)/(2*l1*r))
    phi = math.atan2(y, x)
    return admit([(phi - beta, math.acos(c2)), (phi + beta, -math.acos(c2))], limits)


def ik_wide_band(x, y, l1, l2, lim):
    r = math.hypot(x, y)
    if not abs(l1 - l2) - 1e-7 <= r <= l1 + l2 + 1e-7:
        return []
    return admit(candidates(x, y, l1, l2), lim)


def base_rule(tolerance):
    def run(x, y, l1, l2, limits=None):
        target(x, y, l1, l2)
        if x == 0 and y == 0 and abs(l1 - l2) <= tolerance:
            raise ValueError
        if x == 0 and y == 0:
            if limits is not None:
                check_limits(limits)
            return []
        return ik_branches(x, y, l1, l2, limits)
    return run


def partial_solver(x, y, l1, l2, q_init, lim, tol, max_iter):
    if not reachable(x, y, l1, l2):
        raise NotImplementedError("unreachable branch left for later")
    return solve_ik_numeric(x, y, l1, l2, q_init, lim, tol, max_iter)


def partial_ik(x, y, l1, l2, limits=None):
    if limits is not None:
        raise NotImplementedError("limits left for later")
    return ik_branches(x, y, l1, l2)


ZERO_J = [[0.0, 0.0], [0.0, 0.0]]
mutants = [
    ('J columns swapped', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [r[::-1] for r in raw_jacobian(q1, q2, l1, l2)])}),
    ('J transposed', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [list(c) for c in zip(*raw_jacobian(q1, q2, l1, l2))])}),
    ('J rows swapped (y, x)', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: raw_jacobian(q1, q2, l1, l2)[::-1])}),
    ('J x row sign error', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[-v for v in raw_jacobian(q1, q2, l1, l2)[0]],
                                raw_jacobian(q1, q2, l1, l2)[1]])}),
    ('J with absolute angles (q2 not added to q1)', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[-l1*math.sin(q1) - l2*math.sin(q2), -l2*math.sin(q2)],
                                [l1*math.cos(q1) + l2*math.cos(q2), l2*math.cos(q2)]])}),
    ('J in degrees', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: raw_jacobian(math.radians(q1), math.radians(q2), l1, l2))}),
    ('J per degree (scaled by pi/180)', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[v*math.pi/180 for v in r] for r in raw_jacobian(q1, q2, l1, l2)])}),
    ('J column 1 misses the link-2 term', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[-l1*math.sin(q1), -l2*math.sin(q1 + q2)],
                                [l1*math.cos(q1), l2*math.cos(q1 + q2)]])}),
    ('J column 2 uses l1', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[r[0], r[1]*l1/l2] for r in raw_jacobian(q1, q2, l1, l2)])}),
    ('J forward difference h = 1e-2', {'jacobian': j_rule(forward_difference(1e-2))}),
    ('J forward difference h = 1e-6', {'jacobian': j_rule(forward_difference(1e-6))}),
    ('J central difference h = 0.1 (huge step)', {'jacobian': j_rule(central_difference(0.1))}),
    ('J zero at singular poses', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: ZERO_J if abs(math.sin(q2)) < 1e-3 else raw_jacobian(q1, q2, l1, l2))}),
    ('det = l1*l2*cos(q2)', {'jacobian_det': det_rule(lambda q1, q2, l1, l2: l1*l2*math.cos(q2))}),
    ('det absolute value', {'jacobian_det': det_rule(lambda q1, q2, l1, l2: abs(l1*l2*math.sin(q2)))}),
    ('det sign flipped (bc - ad)', {'jacobian_det': det_rule(lambda q1, q2, l1, l2: -l1*l2*math.sin(q2))}),
    ('det uses q1 + q2', {'jacobian_det': det_rule(lambda q1, q2, l1, l2: l1*l2*math.sin(q1 + q2))}),
    ('det rounds near-singular poses to zero', {'jacobian_det': det_rule(
        lambda q1, q2, l1, l2: 0.0 if abs(math.sin(q2)) < 1e-4 else l1*l2*math.sin(q2))}),
    ('tip velocity uses J transpose', {'tip_velocity': tip_rule(
        lambda J, a, b: (J[0][0]*a + J[1][0]*b, J[0][1]*a + J[1][1]*b))}),
    ('tip velocity with joint rates swapped', {'tip_velocity': tip_rule(
        lambda J, a, b: (J[0][0]*b + J[0][1]*a, J[1][0]*b + J[1][1]*a))}),
    ('tip velocity ignores dq2', {'tip_velocity': tip_rule(
        lambda J, a, b: (J[0][0]*a, J[1][0]*a))}),
    ('tip velocity returns (vy, vx)', {'tip_velocity': tip_rule(
        lambda J, a, b: (J[1][0]*a + J[1][1]*b, J[0][0]*a + J[0][1]*b))}),
    ('tip velocity with absolute joint-2 rate (dq1 + dq2 used twice)', {'tip_velocity': tip_rule(
        lambda J, a, b: (J[0][0]*a + J[0][1]*(a + b), J[1][0]*a + J[1][1]*(a + b)))}),
    ('IK one branch only', {'ik_branches': ik_rule(ik_one_branch)}),
    ('IK wrong branch sign in the shoulder offset', {'ik_branches': ik_rule(ik_wrong_sign)}),
    ('IK ignores joint limits', {'ik_branches': ik_rule(ik_no_limits)}),
    ('IK fake nearest solution for unreachable targets', {'ik_branches': ik_rule(ik_nearest)}),
    ('IK boundary duplicates not collapsed', {'ik_branches': ik_rule(ik_duplicates)}),
    ('IK collapses only bit-identical duplicates', {'ik_branches': ik_rule(ik_exact_dedupe)}),
    ('IK strict reach test without the 1e-9 band or clamp', {'ik_branches': ik_rule(ik_strict_reach)}),
    ('IK limits checked on raw atan2 values (no 2*pi representative)',
     {'ik_branches': ik_rule(ik_raw_limits)}),
    ('IK limits without slack', {'ik_branches': ik_rule(ik_strict_limits)}),
    ('IK lists several representatives of one configuration',
     {'ik_branches': ik_rule(ik_all_representatives)}),
    ('IK answers in degrees', {'ik_branches': ik_rule(ik_degrees)}),
    ('IK link lengths swapped', {'ik_branches': ik_rule(ik_swapped_links)}),
    ('IK atan(y/x) quadrant error', {'ik_branches': ik_rule(ik_atan_quadrant)}),
    ('IK base-singular target returns []', {'ik_branches': ik_base_empty}),
    ('IK base-singular target returns one arbitrary pair', {'ik_branches': ik_base_point}),
    ('IK mutates limits', {'ik_branches': ik_mutating}),
    ('solver reports converged without checking the residual',
     {'solve_ik_numeric': solver_shell(converged_blindly)}),
    ('solver labels an exhausted budget unreachable',
     {'solve_ik_numeric': solver_shell(cap_is_unreachable)}),
    ('solver has no reach test', {'solve_ik_numeric': solver_shell(no_reach_test)}),
    ('solver ignores q_init (starts mid-limits)', {'solve_ik_numeric': solver_shell(ignores_q_init)}),
    ('solver steps before checking q_init', {'solve_ik_numeric': solver_shell(step_before_check)}),
    ('solver ignores joint limits', {'solve_ik_numeric': solver_shell(no_projection)}),
    ('solver reports a stale residual', {'solve_ik_numeric': solver_shell(stale_residual)}),
    ('solver reports the squared residual', {'solve_ik_numeric': solver_shell(squared_residual)}),
    ('solver step count off by one', {'solve_ik_numeric': solver_shell(extra_step_count)}),
    ('solver uses a slow Jacobian-transpose step', {'solve_ik_numeric': make_solver(transpose_rule)}),
    ('solver uses an undamped, unlimited Newton step',
     {'solve_ik_numeric': make_solver(undamped_newton_rule)}),
    ('solver uses lightly damped DLS (lam = 0.01) with no step cap',
     {'solve_ik_numeric': make_solver(dls_rule(0.01))}),
    ('solver iterates on unreachable targets and moves q',
     {'solve_ik_numeric': solver_shell(unreachable_moves)}),
    ('solver mutates q_init', {'solve_ik_numeric': mutating_solver}),
    ('solver status capitalised', {'solve_ik_numeric': solver_shell(wrong_case_status)}),
    ('solver float step count', {'solve_ik_numeric': solver_shell(float_steps)}),
    ('bool q1 accepted by jacobian', {'jacobian': accepts_when(
        lambda *a: type(a[0]) is bool, jacobian, ZERO_J)}),
    ('NaN l2 accepted by jacobian_det', {'jacobian_det': accepts_when(
        lambda *a: is_nan(a[3]), jacobian_det, 0.0)}),
    ('dq bound unchecked', {'tip_velocity': accepts_when(
        lambda *a: type(a[4]) in (int, float) and abs(a[4]) > 100, tip_velocity, (0.0, 0.0))}),
    ('infinite x accepted by ik_branches', {'ik_branches': accepts_when(
        lambda *a: type(a[0]) is float and math.isinf(a[0]), ik_branches, [])}),
    ('limits with lo > hi accepted', {'ik_branches': accepts_when(
        lambda *a: len(a) > 4 and isinstance(a[4], list) and len(a[4]) == 2
        and all(isinstance(p, list) and len(p) == 2 for p in a[4])
        and any(type(p[0]) is float and type(p[1]) is float and p[0] > p[1] for p in a[4]),
        ik_branches, [])}),
    ('NaN limit accepted by the solver', {'solve_ik_numeric': accepts_when(
        lambda *a: isinstance(a[5], list) and is_nan(a[5][0][0]), solve_ik_numeric,
        ('not_converged', [0.5, 1.0], 1.0, 0))}),
    ('q_init outside limits accepted', {'solve_ik_numeric': accepts_when(
        lambda *a: isinstance(a[4], list) and len(a[4]) == 2
        and all(type(v) is float for v in a[4]) and abs(a[4][0]) > 3,
        solve_ik_numeric, ('not_converged', [0.5, 1.0], 1.0, 0))}),
    ('float max_iter accepted', {'solve_ik_numeric': lambda *a: solve_ik_numeric(*a[:7], int(a[7]))
                                 if type(a[7]) is float and math.isfinite(a[7])
                                 else solve_ik_numeric(*a)}),
    ('tol = 0 accepted', {'solve_ik_numeric': accepts_when(
        lambda *a: a[6] == 0 and type(a[6]) is float, solve_ik_numeric,
        ('not_converged', [0.5, 1.0], 1.0, 0))}),
    ('rejects int inputs', {'jacobian': floats_only(jacobian)}),
    ('rejects limits=None in ik_branches', {'ik_branches': lambda x, y, l1, l2, limits=None:
                                            ik_branches(x, y, l1, l2, limits)
                                            if limits is not None else
                                            (_ for _ in ()).throw(ValueError())}),
    ('rejects tuple q_init', {'solve_ik_numeric': lambda *a: solve_ik_numeric(*a)
                              if isinstance(a[4], list) else (_ for _ in ()).throw(ValueError())}),
    ('review M1: one solution whenever |c2| is within 1e-9 of 1',
     {'ik_branches': ik_rule(ik_merge_c2)}),
    ('review M1: branches within 1e-3 rad merged', {'ik_branches': ik_rule(ik_merge_close(1e-3))}),
    ('review M1: dedupe tolerance 1e-2 rad on both angles',
     {'ik_branches': ik_rule(ik_merge_close(1e-2))}),
    ('review M2: representative only adds +2*pi', {'ik_branches': ik_rule(
        ik_with_representative(plus_only))}),
    ('review M2: wrap to (-pi, pi] then try only k in {0, 1}', {'ik_branches': ik_rule(
        ik_with_representative(wrap_then_up))}),
    ('review m3: unclamped shoulder cosine in acos', {'ik_branches': ik_unclamped_shoulder}),
    ('review m4: limit slack 1e-4 rad', {'ik_branches': ik_rule(
        ik_with_representative(wide_slack))}),
    ('review m4: reach band 1e-7 m', {'ik_branches': ik_rule(ik_wide_band)}),
    ('review m4: base rule needs exactly l1 == l2', {'ik_branches': base_rule(0)}),
    ('review m4: base rule tolerance 1e-8', {'ik_branches': base_rule(1e-8)}),
    ('review m2: constant heavy damping lam = 0.3 m', {'solve_ik_numeric': make_solver(
        dls_rule(0.3, 0.5))}),
    ('review m1: solver raises NotImplementedError on some inputs only',
     {'solve_ik_numeric': solver_shell(partial_solver)}),
    ('review m6: ik_branches raises NotImplementedError when limits are given',
     {'ik_branches': partial_ik}),
    ('NaN in J returned at a singular pose', {'jacobian': j_rule(
        lambda q1, q2, l1, l2: [[float('nan'), 0.0], [0.0, 0.0]] if q2 == 0
        else raw_jacobian(q1, q2, l1, l2))}),
]
for label, over in mutants:
    require(run_with(over), 'false accept: ' + label)
print('Jacobian kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

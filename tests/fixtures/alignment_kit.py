"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different formulations) that must
pass, and named injected bugs that must be rejected for the intended reason.
Plain checks only, so the fixture also works under python -O.
"""
import ast
import importlib.util
import json
import math
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('alignment_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L17-alignment.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names}
require(imported <= {'math'}, 'kit imports beyond math: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
require('_Mismatch' in text and 'SPOILER BELOW' in text, 'kit needs _Mismatch and a spoiler banner')
spoiler = text.index('SPOILER BELOW')
NAMES = ('project_target', 'pixel_error', 'select_target', 'servo_step', 'servo_cycle', 'run_suite')
require(all(text.index('def ' + name) < spoiler for name in NAMES),
        'starter functions must sit above the spoiler banner')
require(text.index('def _ref_suite') > spoiler and text.index('_SUITE_CASES = ') > spoiler,
        'references and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('alignment_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(sum('not implemented yet' in line for line in starter) == 6 and len(starter) == 6,
        'starter NotImplementedError must collapse to one line per function')


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def enc(value):
    return [enc(x) for x in value] if isinstance(value, (list, tuple)) else dec(value)


def entry(structure, names, args):
    return {'structure': structure, 'inputs': {n: enc(v) for n, v in zip(names, args)}}


def pick(items, indexes):
    return [items[i] for i in indexes]


positive_project = [a for a, w in kit._PROJECT_CASES if w != 'invalid']
expected_samples = (
    [entry('alignment.project-target@1', ('pan', 'tilt', 'point'), a)
     for a in pick(positive_project, (0, 1, 3, 4, 7, 10, 12, 14))]
    + [entry('alignment.pixel-error@1', ('K', 'u', 'v'), a)
       for a, _ in pick(kit._PIXEL_CASES, (0, 1, 2, 4))]
    + [entry('alignment.select-target@1', ('detections', 'label', 'now', 'limits'), a)
       for a, _ in pick(kit._SELECT_CASES, (0, 2, 3, 4, 7, 10, 11, 13, 15, 16))]
    + [entry('alignment.servo-step@1', ('ex', 'ey', 'gain', 'wmax'), a)
       for a, _ in pick(kit._STEP_CASES, (0, 2, 3, 4, 6))]
    + [entry('alignment.servo-cycle@1', ('K', 'detections', 'label', 'now', 'limits', 'loop'), a)
       for a, _ in pick(kit._CYCLE_CASES, (0, 1, 2, 4, 6, 7, 9, 11, 12, 13))]
    + [entry('alignment.run-suite@1', ('target', 'starts', 'gain', 'wmax', 'dt', 'tol', 'max_steps'), a)
       for a, _ in pick(kit._SUITE_CASES, (0, 2, 4, 5, 6, 8))])
SAMPLE_PATH = root / 'content/labs/L17-alignment.samples.v1.json'
samples = json.loads(SAMPLE_PATH.read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L17-alignment'], 'samples must hold only L17-alignment')
require(samples['kits']['L17-alignment'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50: ' + str(len(expected_samples)))


# ---- independent oracles (different formulations) agree with the kit tables ----
def matmul_project(pan, tilt, p):
    """Camera coordinates as Rx(tilt) Ry(-pan) p (two sequential inverse rotations)."""
    c, s = math.cos(pan), math.sin(pan)
    x1, y1, z1 = c*p[0] - s*p[2], p[1], s*p[0] + c*p[2]
    c, s = math.cos(tilt), math.sin(tilt)
    x2, y2, z2 = x1, c*y1 - s*z1, s*y1 + c*z1
    return (x2/z2, y2/z2) if z2 >= 1e-3 else None


def bearing_project(pan, tilt, p):
    """Spherical bearing form: angles of the camera frame at the target direction."""
    r = math.sqrt(sum(c*c for c in p))
    if r == 0:
        return None
    tp = math.asin(max(-1, min(1, p[1]/r)))        # target tilt (down positive)
    pp = math.atan2(p[0], p[2])                       # target pan
    d = (math.sin(pp)*math.cos(tp), math.sin(tp), math.cos(pp)*math.cos(tp))
    f = (math.sin(pan)*math.cos(tilt), math.sin(tilt), math.cos(pan)*math.cos(tilt))
    depth = r*sum(a*b for a, b in zip(d, f))
    if depth < 1e-3:
        return None
    ex = (math.cos(pan), 0.0, -math.sin(pan))
    ey = (-math.sin(pan)*math.sin(tilt), math.cos(tilt), -math.cos(pan)*math.sin(tilt))
    return (r*sum(a*b for a, b in zip(d, ex))/depth, r*sum(a*b for a, b in zip(d, ey))/depth)


for args, want in kit._PROJECT_CASES:
    ref = kit._ref_project(*args)
    if want == 'invalid':
        require(ref is None and matmul_project(*args) is None, 'invalid project case must be invalid')
        continue
    a, b = matmul_project(*args), bearing_project(*args)
    require(ref is not None and a is not None and b is not None, 'project oracle availability')
    if want is not None:
        require(all(abs(x - y) < 1e-12 for x, y in zip(ref, want)), 'project hand anchor')
    require(all(abs(x - y) < 1e-9*max(1, abs(x)) for x, y in zip(ref, a)), 'project matrix oracle')
    require(all(abs(x - y) < 1e-8*max(1, abs(x)) for x, y in zip(ref, b)), 'project bearing oracle')
# closed-form tan geometry for pan-only and tilt-only aligned axes
for ang in (-0.9, -0.3, 0.1, 0.6, 1.1):
    for z in (0.5, 2.0, 7.0):
        got = kit._ref_project(ang, 0.0, (0.0, 0.0, z))
        require(abs(got[0] + math.tan(ang)) < 1e-12 and abs(got[1]) < 1e-12, 'pan-only tan law')
        got = kit._ref_project(0.0, ang, (0.0, 0.0, z))
        require(abs(got[1] + math.tan(ang)) < 1e-12 and abs(got[0]) < 1e-12, 'tilt-only tan law')
for (K, u, v), want in kit._PIXEL_CASES:
    require(all(abs(a - b) <= 1e-12*max(1, abs(b)) for a, b in zip(kit._ref_pixel(K, u, v), want)),
            'pixel anchor')
for (dets, label, now, limits), want in kit._SELECT_CASES:
    require(kit._ref_select(dets, label, now, limits) == want, 'select table disagrees with reference')
for (ex, ey, gain, wmax), want in kit._STEP_CASES:
    got = kit._ref_step(ex, ey, gain, wmax)
    require(all(abs(a - b) <= 1e-12 for a, b in zip(got, want)), 'step anchor')
for args, want in kit._CYCLE_CASES:
    got = kit._ref_cycle(*args)
    require(got[0] == want[0] and all(abs(a - b) <= 1e-12 for a, b in zip(got[1:], want[1:])),
            'cycle table disagrees with reference')


def scalar_suite(pan0, tilt0, gain, wmax, dt, tol, max_steps):
    """Independent on-axis oracle: the two axes decouple when the target is straight ahead
    and one axis starts at 0 (x = -tan(pan), y = -tan(tilt))."""
    res = []
    for ang in (pan0, tilt0):
        k, a = 0, ang
        while True:
            e = math.tan(a)
            if e <= tol and -e <= tol:
                res.append(k)
                break
            if k == max_steps:
                res.append(-1)
                break
            w = max(-wmax, min(wmax, gain*e))
            a -= w*dt
            k += 1
    return res


def margins(target, starts, gain, wmax, dt, tol, max_steps):
    """Smallest distance to a tolerance or saturation decision along every trajectory."""
    smallest = 1.0
    for pan, tilt in starts:
        for k in range(max_steps + 1):
            e = kit._ref_project(pan, tilt, target)
            if e is None:
                break
            for value in e:
                for gap in (abs(abs(value) - tol), abs(abs(gain*value) - wmax)):
                    if gap != 0.0:  # exact binary boundaries are deliberate
                        smallest = min(smallest, gap)
            if abs(e[0]) <= tol and abs(e[1]) <= tol or k == max_steps:
                break
            w = kit._ref_step(e[0], e[1], gain, wmax)
            pan += w[0]*dt
            tilt += w[1]*dt
    return smallest


for args, _ in kit._SUITE_CASES:
    require(margins(*args) > 1e-7, 'suite case too close to a decision boundary: ' + str(args[:1]))
single = kit._SUITE_CASES[0][0]
got = kit._ref_suite(*single)
require(got[0] == scalar_suite(0.5, 0.0, *single[2:])[0] and got[1] == scalar_suite(0.0, 0.3, *single[2:])[1]
        and got[4] == 0, 'pan-only/tilt-only closed-form recursion')
require(max(kit._ref_suite(*kit._SUITE_CASES[0][0])) > 0 and -1 in kit._ref_suite(*kit._SUITE_CASES[4][0])
        and -1 in kit._ref_suite(*kit._SUITE_CASES[5][0]), 'suite tables should include failures')
# linear regime closed form: with gain*dt = c and no saturation, tan(a_k) shrinks by (1 - c) per
# step only to first order; for c = 1 the next error is a - tan(a) ~ -a^3/3 = -4.2e-5, so 1 step suffices
r = kit._ref_suite((0.0, 0.0, 2.0), [(0.05, 0.0)], 4.0, 10.0, 0.25, 1e-3, 10)
require(r == [1], 'deadbeat closed form')


# ---- author reference implementation ----
def finite(value, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError


def whole(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError


def seq(value, n):
    if not isinstance(value, (list, tuple)) or len(value) != n:
        raise ValueError


def v_project(pan, tilt, point):
    finite(pan, -10, 10); finite(tilt, -10, 10)
    seq(point, 3)
    for c in point:
        finite(c, -1000, 1000)


def v_K(K):
    seq(K, 4)
    finite(K[0], 1, 1e4); finite(K[1], 1, 1e4); finite(K[2], -1e4, 1e4); finite(K[3], -1e4, 1e4)


def v_dets(dets):
    if not isinstance(dets, (list, tuple)) or len(dets) > 50:
        raise ValueError
    for r in dets:
        seq(r, 7)
        whole(r[0], 0, 1000); whole(r[1], 0, 1000)
        for c in r[2:6]:
            finite(c, -1e6, 1e6)
        finite(r[6], 0, 1)


def v_limits(lim):
    seq(lim, 4)
    finite(lim[0], 0, 1000); finite(lim[1], 1e-3, 1e4); finite(lim[2], 1e-3, 1e4); finite(lim[3], 0, 1)
    if lim[1] > lim[2]:
        raise ValueError


def v_select(dets, label, now, limits):
    v_dets(dets); whole(label, 0, 1000); finite(now, -1e6, 1e6); v_limits(limits)


def v_step(ex, ey, gain, wmax):
    finite(ex, -1000, 1000); finite(ey, -1000, 1000); finite(gain, 1e-300, 1000); finite(wmax, 1e-300, 10)


def v_loop(loop):
    seq(loop, 3)
    finite(loop[0], 1e-300, 1000); finite(loop[1], 1e-300, 10); finite(loop[2], 1e-300, 1)


def v_suite(target, starts, gain, wmax, dt, tol, max_steps):
    seq(target, 3)
    finite(target[0], -1000, 1000); finite(target[1], -1000, 1000); finite(target[2], 0.1, 1000)
    if not isinstance(starts, (list, tuple)) or not 1 <= len(starts) <= 30:
        raise ValueError
    for s in starts:
        seq(s, 2)
        finite(s[0], -1, 1); finite(s[1], -1, 1)
    finite(gain, 1e-300, 1000); finite(wmax, 1e-300, 10); finite(dt, 1e-300, 1); finite(tol, 1e-300, 1)
    whole(max_steps, 1, 1000)
    if gain*dt > 1 + 1e-12 or wmax*dt > 0.5 + 1e-12:
        raise ValueError


def project(pan, tilt, point):
    v_project(pan, tilt, point)
    out = kit._ref_project(pan, tilt, point)
    if out is None:
        raise ValueError
    return out


def pixel_error(K, u, v):
    v_K(K); finite(u, -1e6, 1e6); finite(v, -1e6, 1e6)
    return kit._ref_pixel(K, u, v)


def select_target(dets, label, now, limits):
    v_select(dets, label, now, limits)
    return kit._ref_select(dets, label, now, limits)


def servo_step(ex, ey, gain, wmax):
    v_step(ex, ey, gain, wmax)
    return kit._ref_step(ex, ey, gain, wmax)


def servo_cycle(K, dets, label, now, limits, loop):
    v_K(K); v_select(dets, label, now, limits); v_loop(loop)
    return kit._ref_cycle(K, dets, label, now, limits, loop)


def run_suite(target, starts, gain, wmax, dt, tol, max_steps):
    v_suite(target, starts, gain, wmax, dt, tol, max_steps)
    return kit._ref_suite(target, starts, gain, wmax, dt, tol, max_steps)


refs = {'project_target': project, 'pixel_error': pixel_error, 'select_target': select_target,
        'servo_step': servo_step, 'servo_cycle': servo_cycle, 'run_suite': run_suite}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


require(run_with({}) == [], 'author reference must pass: ' + str(run_with({})[:3]))


# ---- valid alternatives (different formulations) ----
def project_matrix(pan, tilt, point):
    v_project(pan, tilt, point)
    out = matmul_project(pan, tilt, point)
    if out is None:
        raise ValueError
    return out


def project_bearing(pan, tilt, point):
    v_project(pan, tilt, point)
    out = bearing_project(pan, tilt, point)
    if out is None:
        raise ValueError
    return list(out)


def project_rows(pan, tilt, point):
    """R = Ry(pan) Rx(-tilt) built as a matrix, camera coordinates R^T p."""
    v_project(pan, tilt, point)
    cp, sp, ct, st = math.cos(pan), math.sin(pan), math.cos(tilt), math.sin(tilt)
    R = [[cp, -sp*st, sp*ct], [0.0, ct, st], [-sp, -cp*st, cp*ct]]
    xc, yc, zc = (sum(R[r][c]*point[r] for r in range(3)) for c in range(3))
    if zc < 1e-3:
        raise ValueError
    return (xc/zc, yc/zc)


def pixel_reciprocal(K, u, v):
    v_K(K); finite(u, -1e6, 1e6); finite(v, -1e6, 1e6)
    return [(u - K[2])*(1.0/K[0]), (v - K[3])*(1.0/K[1])]


def select_sorted(dets, label, now, limits):
    v_select(dets, label, now, limits)
    max_age, dmin, dmax, min_conf = limits
    valid = [(-r[6], i) for i, r in enumerate(dets)
             if r[0] == label and r[5] <= now <= r[5] + max_age and dmin <= r[4] <= dmax
             and r[6] >= min_conf]
    return min(valid)[1] if valid else None


def select_filtered(dets, label, now, limits):
    v_select(dets, label, now, limits)
    rows = list(enumerate(dets))
    rows = [(i, r) for i, r in rows if r[0] == label]
    rows = [(i, r) for i, r in rows if 0 <= now - r[5] <= limits[0]]
    rows = [(i, r) for i, r in rows if limits[1] <= r[4] <= limits[2]]
    rows = [(i, r) for i, r in rows if r[6] >= limits[3]]
    if not rows:
        return None
    top = max(r[6] for _, r in rows)
    return [i for i, r in rows if r[6] == top][0]


def step_abs(ex, ey, gain, wmax):
    v_step(ex, ey, gain, wmax)
    out = []
    for e in (ex, ey):
        w = gain*e
        out.append(math.copysign(min(abs(w), wmax), w) if w else 0.0)
    return tuple(out)


def cycle_composed(K, dets, label, now, limits, loop):
    v_K(K); v_select(dets, label, now, limits); v_loop(loop)
    i = select_target(dets, label, now, limits)
    if i is None:
        return ["stop", 0.0, 0.0]
    ex, ey = pixel_error(K, dets[i][2], dets[i][3])
    if max(abs(ex), abs(ey)) <= loop[2]:
        return ["aligned", 0.0, 0.0]
    return ["track", *servo_step(ex, ey, loop[0], loop[1])]


def suite_matrix(target, starts, gain, wmax, dt, tol, max_steps):
    v_suite(target, starts, gain, wmax, dt, tol, max_steps)
    out = []
    for pan, tilt in starts:
        k, res = 0, -1
        while True:
            e = matmul_project(pan, tilt, target)
            if e is None:
                break
            if max(abs(e[0]), abs(e[1])) <= tol:
                res = k
                break
            if k >= max_steps:
                break
            pan += max(-wmax, min(wmax, gain*e[0]))*dt
            tilt += max(-wmax, min(wmax, gain*e[1]))*dt
            k += 1
        out.append(res)
    return tuple(out)


def suite_bearing(target, starts, gain, wmax, dt, tol, max_steps):
    v_suite(target, starts, gain, wmax, dt, tol, max_steps)
    out = []
    for pan, tilt in starts:
        res = -1
        for k in range(max_steps + 1):
            e = bearing_project(pan, tilt, target)
            if e is None:
                break
            if abs(e[0]) <= tol and abs(e[1]) <= tol:
                res = k
                break
            dp, dtl = (min(wmax, max(-wmax, gain*c))*dt for c in e)
            pan, tilt = pan + dp, tilt + dtl
        out.append(res)
    return out


alternatives = [
    ('projection as Rx(tilt) Ry(-pan) p, two sequential rotations', {'project_target': project_matrix}),
    ('projection via the spherical bearing form', {'project_target': project_bearing}),
    ('projection with an explicit R matrix and its transpose', {'project_target': project_rows}),
    ('pixel error with a reciprocal focal length, list output', {'pixel_error': pixel_reciprocal}),
    ('selection as a tuple-key minimum over fresh candidates', {'select_target': select_sorted}),
    ('selection as chained filters then the first top confidence', {'select_target': select_filtered}),
    ('step with copysign and abs saturation, tuple output', {'servo_step': step_abs}),
    ('cycle composed from own helpers returning lists', {'servo_cycle': cycle_composed}),
    ('suite with a matrix projection and a while loop', {'run_suite': suite_matrix}),
    ('suite with the bearing projection, tuple output', {'run_suite': suite_bearing}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject of valid alternative: ' + label + ': ' + str(result[:2]))


# ---- injected bugs, each rejected by a failure line for the intended function ----
def is_real(x):
    return type(x) in (int, float) and math.isfinite(x)


def lenient(good, test, fallback):
    """Return `fallback` instead of ValueError when `test(args)` marks an invalid-input probe."""
    def wrapped(*args):
        if test(*args):
            return fallback
        return good(*args)
    return wrapped


def raw_project(pan, tilt, p, ysign=1, xsign=1, tsign=1, div='depth', coupling=True, pan_on=True,
                tilt_on=True, minz=1e-3, absz=False):
    v_project(pan, tilt, p)
    pan = pan if pan_on else 0.0
    tilt = tsign*(tilt if tilt_on else 0.0)
    sp, cp, st, ct = math.sin(pan), math.cos(pan), math.sin(tilt), math.cos(tilt)
    x, y, z = p
    xc = x*cp - z*sp
    yc = -x*sp*st + y*ct - z*cp*st if coupling else y
    zc = x*sp*ct + y*st + z*cp*ct if coupling else x*sp + z*cp
    if (abs(zc) if absz else zc) < minz:
        raise ValueError
    d = abs(zc) if absz else zc
    if div == 'range':
        d = math.sqrt(x*x + y*y + z*z)
    if div == 'none':
        d = 1.0
    return (xsign*xc/d, ysign*yc/d)


def gen_select(valid, pick='max'):
    def f(dets, label, now, limits):
        v_select(dets, label, now, limits)
        best = None
        for i, r in enumerate(dets):
            if not valid(r, label, now, limits):
                continue
            if best is None:
                best = i
            elif pick == 'max' and r[6] > dets[best][6]:
                best = i
            elif pick == 'last' and r[6] >= dets[best][6]:
                best = i
            elif pick == 'min' and r[6] < dets[best][6]:
                best = i
        return best
    return f


def standard(r, label, now, limits):
    return kit._ref_valid(r, label, now, limits)


def v(label_ok=True, age=True, depth=True, conf=True, colour_alt=False, strict_age=False,
      future=False, hi=True, lo=True, strict_depth=False, strict_conf=False):
    def test(r, label, now, limits):
        max_age, dmin, dmax, min_conf = limits
        a = now - r[5]
        if label_ok and not (r[0] == label or (colour_alt and r[1] == 1)):
            return False
        if age:
            if strict_age and not 0 <= a < max_age:
                return False
            if not strict_age and not (a <= max_age and (future or a >= 0)):
                return False
        if depth:
            if lo and (r[4] <= dmin if strict_depth else r[4] < dmin):
                return False
            if hi and (r[4] >= dmax if strict_depth else r[4] > dmax):
                return False
        if conf and (r[6] <= min_conf if strict_conf else r[6] < min_conf):
            return False
        return True
    return test


def step_variant(kind):
    def f(ex, ey, gain, wmax):
        v_step(ex, ey, gain, wmax)
        a, b = gain*ex, gain*ey
        if kind == 'noclip':
            return (a, b)
        if kind == 'upper':
            return (min(a, wmax), min(b, wmax))
        if kind == 'norm':
            n = math.hypot(a, b)
            s = wmax/n if n > wmax else 1.0
            return (a*s, b*s)
        if kind == 'sign':
            return (-a if abs(a) <= wmax else _c(a, wmax), -b if abs(b) <= wmax else _c(b, wmax))
        if kind == 'clip_error':
            return (_c(ex, wmax)*gain, _c(ey, wmax)*gain)
        if kind == 'swap':
            return (_c(b, wmax), _c(a, wmax))
        if kind == 'gain_in_clip':
            return (_c(a, wmax*gain), _c(b, wmax*gain))
        if kind == 'one_axis':
            return (_c(a, wmax), _c(b, wmax) if abs(a) <= wmax else _c(a, wmax))
        if kind == 'sat_mid':
            return (_c(a, wmax) * (0.5 if abs(a) > wmax else 1), _c(b, wmax))
        raise ValueError
    return f


def _c(value, bound):
    return max(-bound, min(bound, value))


def cycle_variant(kind):
    def f(K, dets, label, now, limits, loop):
        v_K(K); v_select(dets, label, now, limits); v_loop(loop)
        gain, wmax, tol = loop
        idx = kit._ref_select(dets, label, now, limits)
        if kind == 'first_row':
            idx = 0 if dets else None
        elif kind == 'best_any_label':
            idx = max(range(len(dets)), key=lambda i: dets[i][6]) if dets else None
        elif kind == 'no_fresh' and dets:
            ok = [i for i, r in enumerate(dets) if r[0] == label and r[4] >= limits[1]
                  and r[4] <= limits[2] and r[6] >= limits[3]]
            idx = max(ok, key=lambda i: dets[i][6]) if ok else None
        if idx is None:
            if kind == 'stop_status':
                return ('idle', 0.0, 0.0)
            if kind == 'hold':
                return ('track', 0.1, 0.1)
            return ('stop', 0.0, 0.0)
        ex, ey = kit._ref_pixel(K, dets[idx][2], dets[idx][3])
        if kind == 'or_aligned':
            done = abs(ex) <= tol or abs(ey) <= tol
        elif kind == 'strict_aligned':
            done = abs(ex) < tol and abs(ey) < tol
        elif kind == 'x_only':
            done = abs(ex) <= tol
        elif kind == 'double_tol':
            done = abs(ex) <= 2*tol and abs(ey) <= 2*tol
        else:
            done = abs(ex) <= tol and abs(ey) <= tol
        if done:
            if kind == 'aligned_moves':
                return ('aligned',) + kit._ref_step(ex, ey, gain, wmax)
            return ('aligned', 0.0, 0.0)
        if kind == 'centroid_of_first':
            ex, ey = kit._ref_pixel(K, dets[0][2], dets[0][3])
        if kind == 'no_clip':
            return ('track', gain*ex, gain*ey)
        if kind == 'pixel_cmd':
            return ('track',) + kit._ref_step(dets[idx][2], dets[idx][3], gain, wmax)
        return ('track',) + kit._ref_step(ex, ey, gain, wmax)
    return f


def suite_variant(kind):
    def f(target, starts, gain, wmax, dt, tol, max_steps):
        v_suite(target, starts, gain, wmax, dt, tol, max_steps)
        out = []
        for pan0, tilt0 in starts:
            pan, tilt, res = pan0, tilt0, -1
            limit = max_steps + (1 if kind == 'budget_plus' else -1 if kind == 'budget_minus' else 0)
            for k in range(limit + 1):
                e = kit._ref_project(pan, tilt, target)
                if e is None:
                    if kind == 'lost_continue':
                        e = (0.0, 0.0) if False else None
                    break
                ex, ey = e
                if kind == 'pan_only':
                    ey = 0.0
                if kind == 'strict_tol':
                    done = abs(ex) < tol and abs(ey) < tol
                elif kind == 'or_tol':
                    done = abs(ex) <= tol or abs(ey) <= tol
                else:
                    done = abs(ex) <= tol and abs(ey) <= tol
                if done:
                    res = k + 1 if kind == 'one_based' else k
                    break
                if k == limit:
                    break
                wp, wt = kit._ref_step(ex, ey, gain, wmax) if kind != 'no_sat' else (gain*ex, gain*ey)
                if kind == 'wrong_sign':
                    wp, wt = -wp, -wt
                if kind == 'no_dt':
                    pan, tilt = pan + wp, tilt + wt
                elif kind == 'sequential':
                    pan += wp*dt
                    e2 = kit._ref_project(pan, tilt, target)
                    wt = kit._ref_step(e2[0], e2[1], gain, wmax)[1] if e2 else wt
                    tilt += wt*dt
                elif kind == 'tilt_up':
                    pan, tilt = pan + wp*dt, tilt - wt*dt
                else:
                    pan, tilt = pan + wp*dt, tilt + wt*dt
            out.append(res)
        if kind == 'mutate':
            starts.reverse() if isinstance(starts, list) else None
        return out
    return f


mutants = [
    ('x sign flipped (target left of centre reads positive)', 'project_target',
     {'project_target': lambda p, t, q: raw_project(p, t, q, xsign=-1)}),
    ('y flipped (up positive)', 'project_target',
     {'project_target': lambda p, t, q: raw_project(p, t, q, ysign=-1)}),
    ('tilt positive up', 'project_target', {'project_target': lambda p, t, q: raw_project(p, t, q, tsign=-1)}),
    ('no division by depth', 'project_target', {'project_target': lambda p, t, q: raw_project(p, t, q, div='none')}),
    ('division by range instead of depth', 'project_target',
     {'project_target': lambda p, t, q: raw_project(p, t, q, div='range')}),
    ('pan ignored', 'project_target', {'project_target': lambda p, t, q: raw_project(p, t, q, pan_on=False)}),
    ('tilt ignored', 'project_target', {'project_target': lambda p, t, q: raw_project(p, t, q, tilt_on=False)}),
    ('pan and tilt treated as independent (no coupling)', 'project_target',
     {'project_target': lambda p, t, q: raw_project(p, t, q, coupling=False)}),
    ('negative depth accepted (mirrored projection)', 'invalid project_target(point=(0, 0, 0.0)',
     {'project_target': lambda p, t, q: raw_project(p, t, q, minz=-1e9, absz=True) if True else None}),
    ('depth floor 1e-6 instead of 1e-3', 'invalid project_target(point=(0, 0, 0.0009)',
     {'project_target': lambda p, t, q: raw_project(p, t, q, minz=1e-6)}),
    ('pan range unchecked', 'invalid project_target(pan=10.01',
     {'project_target': lenient(project, lambda p, t, q: is_real(p) and abs(p) > 10, (0.0, 0.0))}),
    ('pixel error swaps fx and fy', 'pixel_error',
     {'pixel_error': lambda K, u, v: (v_K(K), finite(u, -1e6, 1e6), finite(v, -1e6, 1e6),
                                      ((u - K[2])/K[1], (v - K[3])/K[0]))[-1]}),
    ('pixel error sign flipped (cx - u)', 'pixel_error',
     {'pixel_error': lambda K, u, v: (v_K(K), finite(u, -1e6, 1e6), finite(v, -1e6, 1e6),
                                      ((K[2] - u)/K[0], (K[3] - v)/K[1]))[-1]}),
    ('pixel error forgets the principal point', 'pixel_error',
     {'pixel_error': lambda K, u, v: (v_K(K), finite(u, -1e6, 1e6), finite(v, -1e6, 1e6),
                                      (u/K[0], v/K[1]))[-1]}),
    ('pixel error uses fx for both axes', 'pixel_error',
     {'pixel_error': lambda K, u, v: (v_K(K), finite(u, -1e6, 1e6), finite(v, -1e6, 1e6),
                                      ((u - K[2])/K[0], (v - K[3])/K[0]))[-1]}),
    ('identity by colour (label ignored, colour 1 matches)', 'select_target',
     {'select_target': gen_select(v(colour_alt=True, label_ok=False) if False else (
         lambda r, label, now, limits: r[1] == 1 and v()(r, r[0], now, limits)))}),
    ('label ignored (best confidence wins)', 'select_target', {'select_target': gen_select(v(label_ok=False))}),
    ('label or colour accepted', 'select_target', {'select_target': gen_select(v(colour_alt=True))}),
    ('label or colour-equals-label accepted', 'select_target', {'select_target': gen_select(
        lambda r, l, n, li: kit._ref_valid((l,) + tuple(r[1:]), l, n, li) and (r[0] == l or r[1] == l))}),
    ('tolerance above 0.5 rejected in the cycle', 'servo_cycle',
     {'servo_cycle': lambda K, d, l, n, li, lo: (_ for _ in ()).throw(ValueError()) if isinstance(lo, (list, tuple)) and len(lo) == 3 and is_real(lo[2]) and lo[2] > 0.5
      else servo_cycle(K, d, l, n, li, lo)}),
    ('tolerance 1 rejected in the suite', 'run_suite',
     {'run_suite': lambda t, s_, g, w, dt, tl, m: (_ for _ in ()).throw(ValueError()) if is_real(tl) and tl >= 1
      else run_suite(t, s_, g, w, dt, tl, m)}),
    ('freshness ignored', 'select_target', {'select_target': gen_select(v(age=False))}),
    ('age exactly max_age rejected', 'select_target', {'select_target': gen_select(v(strict_age=True))}),
    ('future stamp accepted', 'select_target', {'select_target': gen_select(v(future=True))}),
    ('no depth upper bound', 'select_target', {'select_target': gen_select(v(hi=False))}),
    ('no depth lower bound (zero and negative accepted)', 'select_target',
     {'select_target': gen_select(v(lo=False))}),
    ('depth window strict', 'select_target', {'select_target': gen_select(v(strict_depth=True))}),
    ('confidence threshold strict', 'select_target', {'select_target': gen_select(v(strict_conf=True))}),
    ('confidence threshold ignored', 'select_target', {'select_target': gen_select(v(conf=False))}),
    ('first valid detection instead of the best', 'select_target',
     {'select_target': lambda d, l, n, li: (v_select(d, l, n, li), next(
         (i for i, r in enumerate(d) if kit._ref_valid(r, l, n, li)), None))[-1]}),
    ('ties go to the last index', 'select_target', {'select_target': gen_select(standard, pick='last')}),
    ('lowest confidence picked', 'select_target', {'select_target': gen_select(standard, pick='min')}),
    ('1-based index', 'select_target', {'select_target': lambda d, l, n, li: (
        lambda r: None if r is None else r + 1)(select_target(d, l, n, li))}),
    ('-1 instead of None', 'select_target', {'select_target': lambda d, l, n, li: (
        lambda r: -1 if r is None else r)(select_target(d, l, n, li))}),
    ('detection row returned instead of the index', 'select_target', {'select_target': lambda d, l, n, li: (
        lambda r: None if r is None else list(d[r]))(select_target(d, l, n, li))}),
    ('selection sorts the caller list', 'select_target', {'select_target': lambda d, l, n, li: (
        v_select(d, l, n, li), d.sort(key=lambda r: -r[6]) if isinstance(d, list) else None,
        kit._ref_select(d, l, n, li))[-1]}),
    ('no saturation', 'servo_step', {'servo_step': step_variant('noclip')}),
    ('only the positive side saturates', 'servo_step', {'servo_step': step_variant('upper')}),
    ('saturation scales the vector (direction preserved)', 'servo_step', {'servo_step': step_variant('norm')}),
    ('command sign flipped', 'servo_step', {'servo_step': step_variant('sign')}),
    ('error clipped before the gain', 'servo_step', {'servo_step': step_variant('clip_error')}),
    ('axes swapped', 'servo_step', {'servo_step': step_variant('swap')}),
    ('limit scaled by the gain', 'servo_step', {'servo_step': step_variant('gain_in_clip')}),
    ('saturated pan halved', 'servo_step', {'servo_step': step_variant('sat_mid')}),
    ('cancel missing: holds the last motion', 'servo_cycle', {'servo_cycle': cycle_variant('hold')}),
    ('stop status misnamed', 'servo_cycle', {'servo_cycle': cycle_variant('stop_status')}),
    ('steers to the first row regardless of validity', 'servo_cycle', {'servo_cycle': cycle_variant('first_row')}),
    ('steers to the best detection of any label', 'servo_cycle', {'servo_cycle': cycle_variant('best_any_label')}),
    ('freshness skipped inside the cycle', 'servo_cycle', {'servo_cycle': cycle_variant('no_fresh')}),
    ('aligned when either axis is small', 'servo_cycle', {'servo_cycle': cycle_variant('or_aligned')}),
    ('aligned strict at the tolerance', 'servo_cycle', {'servo_cycle': cycle_variant('strict_aligned')}),
    ('aligned looks at x only', 'servo_cycle', {'servo_cycle': cycle_variant('x_only')}),
    ('aligned with a doubled tolerance', 'servo_cycle', {'servo_cycle': cycle_variant('double_tol')}),
    ('aligned still commands motion', 'servo_cycle', {'servo_cycle': cycle_variant('aligned_moves')}),
    ('error taken from the first row instead of the selected', 'servo_cycle',
     {'servo_cycle': cycle_variant('centroid_of_first')}),
    ('cycle without saturation', 'servo_cycle', {'servo_cycle': cycle_variant('no_clip')}),
    ('command from raw pixels instead of normalized error', 'servo_cycle', {'servo_cycle': cycle_variant('pixel_cmd')}),
    ('suite counts from 1', 'run_suite', {'run_suite': suite_variant('one_based')}),
    ('suite budget one step short', 'run_suite', {'run_suite': suite_variant('budget_minus')}),
    ('suite budget one step long', 'run_suite', {'run_suite': suite_variant('budget_plus')}),
    ('suite tolerance strict', 'run_suite', {'run_suite': suite_variant('strict_tol')}),
    ('suite aligned when either axis is inside', 'run_suite', {'run_suite': suite_variant('or_tol')}),
    ('suite looks at pan only', 'run_suite', {'run_suite': suite_variant('pan_only')}),
    ('suite without saturation', 'run_suite', {'run_suite': suite_variant('no_sat')}),
    ('suite with the wrong sign (diverges)', 'run_suite', {'run_suite': suite_variant('wrong_sign')}),
    ('suite ignores dt', 'run_suite', {'run_suite': suite_variant('no_dt')}),
    ('suite updates tilt with the already moved pan', 'run_suite', {'run_suite': suite_variant('sequential')}),
    ('suite with tilt moving the wrong way', 'run_suite', {'run_suite': suite_variant('tilt_up')}),
    ('suite reverses the caller starts', 'run_suite', {'run_suite': suite_variant('mutate')}),
    ('bool pan accepted', 'invalid project_target(pan=True',
     {'project_target': lenient(project, lambda p, t, q: type(p) is bool, (0.0, 0.0))}),
    ('NaN point accepted', 'invalid project_target(point=(0, 0, nan)',
     {'project_target': lenient(project, lambda p, t, q: isinstance(q, tuple) and any(
         type(c) is float and c != c for c in q), (0.0, 0.0))}),
    ('fx below 1 accepted', 'invalid pixel_error(K=(0.99',
     {'pixel_error': lenient(pixel_error, lambda K, u, v: isinstance(K, tuple) and len(K) == 4
                             and is_real(K[0]) and K[0] < 1, (0.0, 0.0))}),
    ('float label accepted', 'invalid select_target(label=7.0',
     {'select_target': lenient(select_target, lambda d, l, n, li: type(l) is float, None)}),
    ('conf above 1 accepted', 'invalid select_target(detections=',
     {'select_target': lenient(select_target, lambda d, l, n, li: isinstance(d, list) and any(
         isinstance(r, tuple) and len(r) == 7 and is_real(r[6]) and r[6] > 1 for r in d), None)}),
    ('depth_min above depth_max accepted', 'invalid select_target(limits=(0.5, 0.25, 0.2',
     {'select_target': lenient(select_target, lambda d, l, n, li: isinstance(li, tuple) and len(li) == 4
                               and is_real(li[1]) and is_real(li[2]) and li[1] > li[2], None)}),
    ('gain 0 accepted', 'invalid servo_step(gain=0.0',
     {'servo_step': lenient(servo_step, lambda a, b, g, w: g == 0, (0.0, 0.0))}),
    ('wmax above 10 accepted', 'invalid servo_cycle(loop=(1.5, 10.01',
     {'servo_cycle': lenient(servo_cycle, lambda K, d, l, n, li, lo: isinstance(lo, tuple) and len(lo) == 3
                             and is_real(lo[1]) and lo[1] > 10, ('stop', 0.0, 0.0))}),
    ('gain*dt above 1 accepted', 'invalid run_suite(gain=4.01',
     {'run_suite': lenient(run_suite, lambda t, s, g, w, dt, tl, m: is_real(g) and g > 4, [0])}),
    ('wmax*dt above 0.5 accepted', 'invalid run_suite(wmax=2.1',
     {'run_suite': lenient(run_suite, lambda t, s, g, w, dt, tl, m: is_real(w) and w > 2, [0])}),
    ('float max_steps accepted', 'invalid run_suite(max_steps=5.0',
     {'run_suite': lenient(run_suite, lambda t, s, g, w, dt, tl, m: type(m) is float, [0])}),
    ('empty starts accepted', 'invalid run_suite(starts=[]',
     {'run_suite': lenient(run_suite, lambda t, s, g, w, dt, tl, m: isinstance(s, list) and not s, [])}),
    ('target depth below 0.1 accepted', 'invalid run_suite(target=(0, 0, 0.09)',
     {'run_suite': lenient(run_suite, lambda t, s, g, w, dt, tl, m: isinstance(t, tuple) and len(t) == 3
                           and is_real(t[2]) and t[2] < 0.1, [0])}),
    ('depth 0.001 rejected as over-strict', 'project_target 9',
     {'project_target': lambda p, t, q: (_ for _ in ()).throw(ValueError()) if q[2] == 0.001
      else project(p, t, q)}),
    ('integer inputs rejected', 'servo_step',
     {'servo_step': lambda a, b, g, w: (_ for _ in ()).throw(ValueError()) if type(g) is int
      else servo_step(a, b, g, w)}),
    ('empty detections rejected', 'select_target 1',
     {'select_target': lambda d, l, n, li: (_ for _ in ()).throw(ValueError()) if not d
      else select_target(d, l, n, li)}),
]
require(len(mutants) >= 30, 'need at least 30 mutants')
for label, prefix, over in mutants:
    result = run_with(over)
    require(result, 'false accept: ' + label)
    require(any(line.startswith(prefix) for line in result),
            'mutant rejected for the wrong reason: ' + label + ' -> ' + result[0])
print('Alignment kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

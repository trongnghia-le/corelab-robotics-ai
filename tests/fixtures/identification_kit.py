"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (Cramer, QR, pivoted elimination,
exact rational, conjugate-gradient solves; different condition-number and
clamping formulations) that must pass, and named injected bugs that must be
rejected for the function they target. Plain checks only, so it also works
under python -O.
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
        raise SystemExit('identification_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L21-identification.v1.py'
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
names = ('simulate', 'normal_equations', 'condition_number', 'identifiability',
         'fit_first_order', 'residual_rms', 'heldout_check', 'parameter_std', 'randomize')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _cramer_ref') > spoiler and text.index('_FIT_CASES = ') > spoiler,
        'oracle and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('identification_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 9 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if value is None or isinstance(value, str):
        return value
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
    [entry('identification.simulate@1', ('a', 'b', 'y0', 'u'), c[0]) for c in kit._SIM_CASES]
    + [entry('identification.normal-equations@1', ('y', 'u'), c[0]) for c in kit._NE_CASES]
    + [entry('identification.condition-number@1', ('G',), c[0]) for c in kit._COND_CASES]
    + [entry('identification.status@1', ('y', 'u'), c[0]) for c in kit._ID_CASES]
    + [entry('identification.fit@1', ('y', 'u'), c[0]) for c in kit._FIT_CASES]
    + [entry('identification.fit-unidentifiable@1', ('y', 'u'), c) for c in kit._UNID_LOGS]
    + [entry('identification.residual@1', ('a', 'b', 'y', 'u'), c[0]) for c in kit._RES_CASES]
    + [entry('identification.heldout@1', ('a', 'b', 'y_test', 'u_test', 'tol'), c[0])
       for c in kit._HELD_CASES]
    + [entry('identification.parameter-std@1', ('y', 'u', 'sigma'), c[0]) for c in kit._STD_CASES]
    + [entry('identification.randomize@1', ('ranges', 'draws', 'mode'), c[0])
       for c in kit._RAND_CASES])
samples = json.loads((root / 'content/labs/L21-identification.samples.v1.json')
                     .read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L21-identification'], 'samples must hold only L21-identification')
require(samples['kits']['L21-identification'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50: ' + str(len(expected_samples)))


# ---- exact rational cross-check of the tables (independent of the kit's float oracle) ----
def exact_fit(y, u):
    n = len(u)
    fy, fu, fz = [Fraction(v) for v in y], [Fraction(v) for v in u], None
    syy = sum(fy[k]*fy[k] for k in range(n))
    syu = sum(fy[k]*fu[k] for k in range(n))
    suu = sum(fu[k]*fu[k] for k in range(n))
    g0 = sum(fy[k+1]*fy[k] for k in range(n))
    g1 = sum(fy[k+1]*fu[k] for k in range(n))
    det = syy*suu - syu*syu
    if det == 0:
        return None
    return (g0*suu - syu*g1)/det, (syy*g1 - syu*g0)/det


for args, mode, want in kit._FIT_CASES:
    got = exact_fit(*args)
    require(got is not None, 'fit case must be identifiable')
    ref = want if mode == 'hand' else kit._cramer_ref(*args)
    require(all(abs(float(g) - w) <= 1e-9*max(1.0, abs(w)) * max(1.0, kit._cond_ref(kit._ne_ref(*args)[0])/1000.0)
                for g, w in zip(got, ref)), 'exact rational disagrees with fit table')
for y, u in kit._UNID_LOGS:
    require(exact_fit(y, u) is None, 'unidentifiable table log must have a singular exact Gram')
for args, status in kit._ID_CASES:
    singular = exact_fit(*args) is None
    require(singular == (status == 'unidentifiable'), 'identifiability table vs exact singularity')


# ---- author reference implementation (validation + replaceable cores) ----
def isreal(v):
    return type(v) in (int, float) and math.isfinite(v)


def rv(v, low, high):
    if not isreal(v) or not low <= v <= high:
        raise ValueError


def cseq(y, u):
    if not isinstance(y, (list, tuple)) or not isinstance(u, (list, tuple)):
        raise ValueError
    if not 2 <= len(u) <= 50 or len(y) != len(u) + 1:
        raise ValueError
    for v in list(y) + list(u):
        rv(v, -1e4, 1e4)
    return [float(v) for v in y], [float(v) for v in u]


def cG(G):
    if not isinstance(G, (list, tuple)) or len(G) != 2:
        raise ValueError
    out = []
    for row in G:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise ValueError
        for v in row:
            rv(v, -1e10, 1e10)
        out.append([float(v) for v in row])
    scale = max(1.0, max(abs(v) for row in out for v in row))
    if abs(out[0][1] - out[1][0]) > 1e-9*scale:
        raise ValueError
    b = (out[0][1] + out[1][0])/2
    low = (out[0][0] + out[1][1])/2 - math.hypot((out[0][0] - out[1][1])/2, b)
    if low < -1e-9*scale:
        raise ValueError
    return out


# cores take validated float lists
def sim_core(a, b, y0, u):
    out = [y0]
    for x in u:
        out.append(a*out[-1] + b*x)
    return out


def ne_core(y, u):
    return kit._ne_ref(y, u)


def cond_core(G):
    return kit._cond_ref(G)


def ident_core(y, u):
    return kit._status_ref(y, u)


def check_identifiable(y, u):
    if kit._status_ref(y, u) == 'unidentifiable':
        raise ValueError


def fit_core(y, u):
    check_identifiable(y, u)
    return kit._cramer_ref(y, u)


def rms_core(a, b, y, u):
    return kit._rms_ref(a, b, y, u)


def held_core(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return r, r <= tol


def std_core(y, u, sigma):
    check_identifiable(y, u)
    return kit._std_ref(y, u, sigma)


def rand_core(ranges, draws, mode):
    return kit._rand_ref(ranges, draws, mode)


def validated(cores):
    def simulate(a, b, y0, u):
        rv(a, -100, 100)
        rv(b, -100, 100)
        rv(y0, -1e4, 1e4)
        if not isinstance(u, (list, tuple)) or not 1 <= len(u) <= 50:
            raise ValueError
        for v in u:
            rv(v, -1e4, 1e4)
        return cores['sim'](float(a), float(b), float(y0), [float(v) for v in u])

    def normal_equations(y, u):
        return cores['ne'](*cseq(y, u))

    def condition_number(G):
        return cores['cond'](cG(G))

    def identifiability(y, u):
        return cores['ident'](*cseq(y, u))

    def fit_first_order(y, u):
        return cores['fit'](*cseq(y, u))

    def residual_rms(a, b, y, u):
        rv(a, -100, 100)
        rv(b, -100, 100)
        y, u = cseq(y, u)
        return cores['rms'](float(a), float(b), y, u)

    def heldout_check(a, b, y, u, tol):
        rv(a, -100, 100)
        rv(b, -100, 100)
        rv(tol, 0, 1e4)
        if tol <= 0:
            raise ValueError
        y, u = cseq(y, u)
        return cores['held'](float(a), float(b), y, u, float(tol))

    def parameter_std(y, u, sigma):
        rv(sigma, 0, 1e3)
        if sigma <= 0:
            raise ValueError
        y, u = cseq(y, u)
        return cores['std'](y, u, float(sigma))

    def randomize(ranges, draws, mode='uniform'):
        if mode not in ('uniform', 'log') or type(mode) is not str:
            raise ValueError
        if not isinstance(ranges, (list, tuple)) or not 1 <= len(ranges) <= 6:
            raise ValueError
        if not isinstance(draws, (list, tuple)) or len(draws) != len(ranges):
            raise ValueError
        rr = []
        for pair in ranges:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError
            lo, hi = pair
            rv(lo, -1e6, 1e6)
            rv(hi, -1e6, 1e6)
            if lo > hi or (mode == 'log' and lo <= 0):
                raise ValueError
            rr.append((lo, hi))
        for d in draws:
            rv(d, 0, 1)
        return cores['rand'](rr, [float(d) for d in draws], mode)

    return {'simulate': simulate, 'normal_equations': normal_equations,
            'condition_number': condition_number, 'identifiability': identifiability,
            'fit_first_order': fit_first_order, 'residual_rms': residual_rms,
            'heldout_check': heldout_check, 'parameter_std': parameter_std,
            'randomize': randomize}


BASE = {'sim': sim_core, 'ne': ne_core, 'cond': cond_core, 'ident': ident_core,
        'fit': fit_core, 'rms': rms_core, 'held': held_core, 'std': std_core,
        'rand': rand_core}


def run_with(cores=None, raw=None):
    """Install cores (and/or raw public functions) and run the kit self-check."""
    merged = dict(BASE)
    merged.update(cores or {})
    functions = validated(merged)
    functions.update(raw or {})
    for name, fn in functions.items():
        setattr(kit, name, fn)
    return kit.self_check()


require(run_with() == [], 'author reference must pass: ' + str(run_with()))


# ---- valid alternatives ----
def fit_qr(y, u):
    """Gram-Schmidt on the regressor columns, then back substitution."""
    check_identifiable(y, u)
    n = len(u)
    c1 = [y[k] for k in range(n)]
    c2 = [u[k] for k in range(n)]
    t = [y[k+1] for k in range(n)]
    r11 = math.sqrt(math.fsum(v*v for v in c1))
    if r11 == 0.0:
        raise ValueError
    q1 = [v/r11 for v in c1]
    r12 = math.fsum(q1[k]*c2[k] for k in range(n))
    w = [c2[k] - r12*q1[k] for k in range(n)]
    r22 = math.sqrt(math.fsum(v*v for v in w))
    q2 = [v/r22 for v in w]
    z1 = math.fsum(q1[k]*t[k] for k in range(n))
    z2 = math.fsum(q2[k]*t[k] for k in range(n))
    b = z2/r22
    a = (z1 - r12*b)/r11
    return (a, b)


def fit_pivot(y, u):
    """Gaussian elimination with partial pivoting on the augmented normal equations."""
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    M = [[G[0][0], G[0][1], g[0]], [G[1][0], G[1][1], g[1]]]
    if abs(M[1][0]) > abs(M[0][0]):
        M[0], M[1] = M[1], M[0]
    f = M[1][0]/M[0][0]
    M[1] = [M[1][j] - f*M[0][j] for j in range(3)]
    b = M[1][2]/M[1][1]
    return [(M[0][2] - M[0][1]*b)/M[0][0], b]


def fit_exact(y, u):
    """Exact rational solution (Fraction of the stored floats), rounded to float."""
    check_identifiable(y, u)
    a, b = exact_fit(y, u)
    return (float(a), float(b))


def fit_cg(y, u):
    """Conjugate gradient on the 2x2 normal equations: two exact-in-theory steps."""
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    x = [0.0, 0.0]
    r = list(g)
    p = list(r)
    for _ in range(2):
        Gp = [G[0][0]*p[0] + G[0][1]*p[1], G[1][0]*p[0] + G[1][1]*p[1]]
        rr = r[0]*r[0] + r[1]*r[1]
        if rr == 0.0:
            break
        alpha = rr/(p[0]*Gp[0] + p[1]*Gp[1])
        x = [x[0] + alpha*p[0], x[1] + alpha*p[1]]
        r2 = [r[0] - alpha*Gp[0], r[1] - alpha*Gp[1]]
        beta = (r2[0]*r2[0] + r2[1]*r2[1])/rr
        p = [r2[0] + beta*p[0], r2[1] + beta*p[1]]
        r = r2
    return tuple(x)


def fit_inverse(y, u):
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    inv = [[G[1][1]/det, -G[0][1]/det], [-G[1][0]/det, G[0][0]/det]]
    return [inv[0][0]*g[0] + inv[0][1]*g[1], inv[1][0]*g[0] + inv[1][1]*g[1]]


def cond_squared(G):
    """lambda_max^2 / det with a tuple-free closed form."""
    t = G[0][0] + G[1][1]
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    if t <= 0 or det <= 1e-12*t*t:
        return math.inf
    big = (t + math.sqrt(max(0.0, t*t - 4*det)))/2
    return big*big/det


def cond_hypot(G):
    t = G[0][0] + G[1][1]
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    if t <= 0 or det <= 1e-12*t*t:
        return math.inf
    big = t/2 + math.hypot((G[0][0] - G[1][1])/2, (G[0][1] + G[1][0])/2)
    small = det/big
    return float(big/small)


def ident_via_rank(y, u):
    """Singular exactly via a relative determinant test, bands from the hypot condition number."""
    c = cond_hypot(kit._ne_ref(y, u)[0])
    return 'unidentifiable' if math.isinf(c) else ('weak' if c > 1e4 else 'identifiable')


def sim_recursive(a, b, y0, u):
    def go(k, y):
        return (y,) if k == len(u) else (y,) + go(k + 1, a*y + b*u[k])
    return go(0, y0)


def ne_loops(y, u):
    n = len(u)
    G = [[0.0, 0.0], [0.0, 0.0]]
    g = [0.0, 0.0]
    for k in range(n):
        row = (y[k], u[k])
        for i in range(2):
            for j in range(2):
                G[i][j] += row[i]*row[j]
            g[i] += row[i]*y[k+1]
    return (tuple(map(tuple, G)), tuple(g))


def rms_gen(a, b, y, u):
    total = 0.0
    for k in range(len(u)):
        e = y[k+1] - a*y[k] - b*u[k]
        total += e*e
    return math.sqrt(total/len(u))


def held_tuple(a, b, y, u, tol):
    r = rms_gen(a, b, y, u)
    return (r, bool(r <= tol))


def std_inverse(y, u, sigma):
    check_identifiable(y, u)
    G = kit._ne_ref(y, u)[0]
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    inv00, inv11 = G[1][1]/det, G[0][0]/det
    return (math.sqrt(sigma*sigma*inv00), math.sqrt(sigma*sigma*inv11))


def rand_lerp(ranges, draws, mode):
    out = []
    for (lo, hi), d in zip(ranges, draws):
        if mode == 'uniform':
            v = lo*(1 - d) + hi*d
        else:
            v = math.exp(math.log(lo)*(1 - d) + math.log(hi)*d)
        out.append(max(lo, min(hi, v)))
    return tuple(out)


alternatives = [
    ('author: Cramer fit, hypot-free condition number, clamped lerp', {}),
    ('Gram-Schmidt QR fit, lambda_max^2/det condition number, recursive tuple simulation',
     {'fit': fit_qr, 'cond': cond_squared, 'sim': sim_recursive}),
    ('pivoted elimination fit, loop-accumulated normal equations returning tuples, '
     'hypot condition number', {'fit': fit_pivot, 'ne': ne_loops, 'cond': cond_hypot}),
    ('exact rational fit, band classification from the hypot condition number, tuple held-out',
     {'fit': fit_exact, 'ident': ident_via_rank, 'held': held_tuple}),
    ('conjugate-gradient fit, plain-loop residual, std via variance then sqrt, lerp randomiser',
     {'fit': fit_cg, 'rms': rms_gen, 'std': std_inverse, 'rand': rand_lerp}),
    ('explicit inverse-matrix fit, log-lerp randomiser',
     {'fit': fit_inverse, 'rand': rand_lerp}),
]
for label, cores in alternatives:
    result = run_with(cores)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs ----
def swap(pair):
    return (pair[1], pair[0])


def sim_shift(a, b, y0, u):
    out = [y0]
    for k in range(len(u)):
        out.append(a*out[-1] + b*u[min(k + 1, len(u) - 1)])
    return out


def sim_swapped(a, b, y0, u):
    out = [y0]
    for x in u:
        out.append(b*out[-1] + a*x)
    return out


def sim_no_y0(a, b, y0, u):
    return sim_core(a, b, y0, u)[1:]


def sim_no_b(a, b, y0, u):
    return sim_core(a, 1.0, y0, u)


def sim_input_uses_state(a, b, y0, u):
    out = [y0]
    for x in u:
        out.append(a*out[-1] + b*out[-1])
    return out


def ne_suu_linear(y, u):
    G, g = kit._ne_ref(y, u)
    return [[G[0][0], G[0][1]], [G[1][0], math.fsum(u)]], g


def ne_target_current(y, u):
    G, g = kit._ne_ref(y, u)
    n = len(u)
    return G, [math.fsum(y[k]*y[k] for k in range(n)), math.fsum(u[k]*y[k] for k in range(n))]


def ne_diag_only(y, u):
    G, g = kit._ne_ref(y, u)
    return [[G[0][0], 0.0], [0.0, G[1][1]]], g


def ne_misaligned(y, u):
    n = len(u)
    G = [[math.fsum(y[k+1]*y[k+1] for k in range(n)), math.fsum(y[k+1]*u[k] for k in range(n))],
         [math.fsum(y[k+1]*u[k] for k in range(n)), math.fsum(u[k]*u[k] for k in range(n))]]
    return G, kit._ne_ref(y, u)[1]


def ne_swapped_order(y, u):
    G, g = kit._ne_ref(y, u)
    return [[G[1][1], G[1][0]], [G[0][1], G[0][0]]], [g[1], g[0]]


def ne_mean(y, u):
    G, g = kit._ne_ref(y, u)
    n = len(u)
    return [[v/n for v in row] for row in G], [v/n for v in g]


def ne_drop_last(y, u):
    return kit._ne_ref(y[:-1], u[:-1])


def cond_flipped(G):
    c = kit._cond_ref(G)
    return 0.0 if math.isinf(c) else 1.0/c


def cond_diag_ratio(G):
    if kit._cond_ref(G) == math.inf:
        return math.inf
    lo, hi = sorted((G[0][0], G[1][1]))
    return hi/lo


def cond_sqrt(G):
    c = kit._cond_ref(G)
    return c if math.isinf(c) else math.sqrt(c)


def cond_big_finite(G):
    c = kit._cond_ref(G)
    return 1e16 if math.isinf(c) else c


def cond_none(G):
    c = kit._cond_ref(G)
    return None if math.isinf(c) else c


def cond_loose_singular(G):
    c = kit._cond_ref(G)
    return math.inf if c > 1e6 else c


def cond_trace_det(G):
    c = kit._cond_ref(G)
    if math.isinf(c):
        return c
    return (G[0][0] + G[1][1])**2/(G[0][0]*G[1][1] - G[0][1]*G[1][0])


def cond_zero_ok(G):
    c = kit._cond_ref(G)
    if math.isinf(c) and G[0][0] + G[1][1] == 0:
        return 1.0
    return c


def ident_u_only(y, u):
    return 'unidentifiable' if max(u) == min(u) else 'identifiable'


def ident_needs_y_vary(y, u):
    st = kit._status_ref(y, u)
    return 'unidentifiable' if max(y) == min(y) else st


def ident_low_weak(y, u):
    c = kit._cond_ref(kit._ne_ref(y, u)[0])
    if math.isinf(c):
        return 'unidentifiable'
    return 'weak' if c > 2.0 else 'identifiable'


def ident_const_u_unid(y, u):
    st = kit._status_ref(y, u)
    return 'unidentifiable' if max(u) == min(u) else st


def ident_weak_from_1e2(y, u):
    c = kit._cond_ref(kit._ne_ref(y, u)[0])
    return 'unidentifiable' if math.isinf(c) else ('weak' if c > 1e2 else 'identifiable')


def ident_weak_from_1e3(y, u):
    c = kit._cond_ref(kit._ne_ref(y, u)[0])
    return 'unidentifiable' if math.isinf(c) else ('weak' if c > 1e3 else 'identifiable')


def ident_weak_from_1e5(y, u):
    c = kit._cond_ref(kit._ne_ref(y, u)[0])
    return 'unidentifiable' if math.isinf(c) else ('weak' if c > 1e5 else 'identifiable')


def ident_weak_from_1e6(y, u):
    c = kit._cond_ref(kit._ne_ref(y, u)[0])
    return 'unidentifiable' if math.isinf(c) else ('weak' if c > 1e6 else 'identifiable')


def fit_const_u_raises(y, u):
    if max(u) == min(u):
        raise ValueError
    return fit_core(y, u)


def held_strict(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return r, r < tol


def ident_weak_as_unid(y, u):
    st = kit._status_ref(y, u)
    return 'unidentifiable' if st == 'weak' else st


def ident_never_weak(y, u):
    st = kit._status_ref(y, u)
    return 'identifiable' if st == 'weak' else st


def ident_only_zero_u(y, u):
    return 'unidentifiable' if all(v == 0 for v in u) else 'identifiable'


def fit_swapped(y, u):
    check_identifiable(y, u)
    return swap(kit._cramer_ref(y, u))


def fit_separate(y, u):
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    return (g[0]/G[0][0], g[1]/G[1][1])


def fit_ridge(y, u):
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    G = [[G[0][0] + 0.05, G[0][1]], [G[1][0], G[1][1] + 0.05]]
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    return ((g[0]*G[1][1] - G[0][1]*g[1])/det, (G[0][0]*g[1] - G[1][0]*g[0])/det)


def fit_drop_last(y, u):
    return kit._cramer_ref(y[:-1], u[:-1])


def fit_no_raise(y, u):
    if kit._status_ref(y, u) == 'unidentifiable':
        return (0.0, 0.0)
    return kit._cramer_ref(y, u)


def fit_nan_on_singular(y, u):
    if kit._status_ref(y, u) == 'unidentifiable':
        return (float('nan'), float('nan'))
    return kit._cramer_ref(y, u)


def fit_raises_weak(y, u):
    if kit._status_ref(y, u) != 'identifiable':
        raise ValueError
    return kit._cramer_ref(y, u)


def fit_ignore_u(y, u):
    check_identifiable(y, u)
    G, g = kit._ne_ref(y, u)
    return (g[0]/G[0][0], 0.0)


def fit_target_previous(y, u):
    check_identifiable(y, u)
    return kit._cramer_ref(y[1:] + [y[-1]], u)


def fit_mean_removed(y, u):
    check_identifiable(y, u)
    n = len(u)
    my = math.fsum(y[:-1])/n
    mt = math.fsum(y[1:])/n
    mu = math.fsum(u)/n
    yy = [v - my for v in y[:-1]]
    uu = [v - mu for v in u]
    tt = [v - mt for v in y[1:]]
    syy = math.fsum(v*v for v in yy)
    suu = math.fsum(v*v for v in uu)
    syu = math.fsum(p*q for p, q in zip(yy, uu))
    g0 = math.fsum(p*q for p, q in zip(yy, tt))
    g1 = math.fsum(p*q for p, q in zip(uu, tt))
    det = syy*suu - syu*syu
    if abs(det) < 1e-12:
        raise ValueError
    return ((g0*suu - syu*g1)/det, (syy*g1 - syu*g0)/det)


def rms_sum(a, b, y, u):
    return math.sqrt(math.fsum((y[k+1] - a*y[k] - b*u[k])**2 for k in range(len(u))))


def rms_mse(a, b, y, u):
    return kit._rms_ref(a, b, y, u)**2


def rms_maxabs(a, b, y, u):
    return max(abs(y[k+1] - a*y[k] - b*u[k]) for k in range(len(u)))


def rms_mean_signed(a, b, y, u):
    return abs(math.fsum(y[k+1] - a*y[k] - b*u[k] for k in range(len(u)))/len(u))


def rms_n_plus_one(a, b, y, u):
    n = len(u)
    return math.sqrt(math.fsum((y[k+1] - a*y[k] - b*u[k])**2 for k in range(n))/(n + 1))


def rms_rollout(a, b, y, u):
    sim = sim_core(a, b, y[0], u)
    n = len(u)
    return math.sqrt(math.fsum((y[k+1] - sim[k+1])**2 for k in range(n))/n)


def rms_no_b(a, b, y, u):
    return kit._rms_ref(a, 0.0, y, u)


def rms_wrong_pred(a, b, y, u):
    n = len(u)
    return math.sqrt(math.fsum((y[k+1] - (b*y[k] + a*u[k]))**2 for k in range(n))/n)


def held_train_scale(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return r, r <= tol*0.5


def held_inverted(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return r, r > tol


def held_mse_vs_tol(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return r, r*r <= tol


def held_always(a, b, y, u, tol):
    return rms_core(a, b, y, u), True


def held_returns_flag_only(a, b, y, u, tol):
    r = rms_core(a, b, y, u)
    return int(r <= tol), r <= tol


def held_sum(a, b, y, u, tol):
    r = rms_sum(a, b, y, u)
    return r, r <= tol


def std_no_sigma(y, u, sigma):
    return std_core(y, u, 1.0)


def std_variance(y, u, sigma):
    sa, sb = std_core(y, u, sigma)
    return sa*sa, sb*sb


def std_diag_only(y, u, sigma):
    G = kit._ne_ref(y, u)[0]
    check_identifiable(y, u)
    return (sigma/math.sqrt(G[0][0]), sigma/math.sqrt(G[1][1]))


def std_swapped(y, u, sigma):
    return swap(std_core(y, u, sigma))


def std_not_inverse(y, u, sigma):
    check_identifiable(y, u)
    G = kit._ne_ref(y, u)[0]
    return (sigma*math.sqrt(G[0][0]), sigma*math.sqrt(G[1][1]))


def std_sigma_squared(y, u, sigma):
    return std_core(y, u, sigma*sigma)


def std_no_raise(y, u, sigma):
    if kit._status_ref(y, u) == 'unidentifiable':
        return (float('inf'), float('inf'))
    return kit._std_ref(y, u, sigma)


def rand_midpoint(ranges, draws, mode):
    return [(lo + hi)/2.0 for lo, hi in ranges]


def rand_lo_plus_d_hi(ranges, draws, mode):
    return [min(max(lo + d*hi, lo), hi) for (lo, hi), d in zip(ranges, draws)]


def rand_d_only(ranges, draws, mode):
    return [min(max(d*(hi - lo), lo), hi) for (lo, hi), d in zip(ranges, draws)]


def rand_unclamped(ranges, draws, mode):
    return [lo + d*(hi - lo) if mode == 'uniform' else lo*(hi/lo)**d
            for (lo, hi), d in zip(ranges, draws)]


def rand_log_as_uniform(ranges, draws, mode):
    return [min(max(lo + d*(hi - lo), lo), hi) for (lo, hi), d in zip(ranges, draws)]


def rand_uniform_as_log(ranges, draws, mode):
    return [min(max(lo*(hi/lo)**d if lo > 0 else lo + d*(hi - lo), lo), hi)
            for (lo, hi), d in zip(ranges, draws)]


def rand_reversed(ranges, draws, mode):
    return rand_core(ranges, list(reversed(draws)), mode)


def rand_first_draw(ranges, draws, mode):
    return rand_core(ranges, [draws[0]]*len(draws), mode)


def rand_one_minus(ranges, draws, mode):
    return rand_core(ranges, [1.0 - d for d in draws], mode)


def rand_reversed_ranges(ranges, draws, mode):
    return [min(max(hi + d*(lo - hi), lo), hi) for (lo, hi), d in zip(ranges, draws)]


def rand_rounded(ranges, draws, mode):
    return [round(v, 1) if lo != hi else v for v, (lo, hi) in zip(rand_core(ranges, draws, mode),
                                                                  ranges)]


def accepts_when(check, function, value):
    def run(*args):
        if check(*args):
            return value
        return function(*args)
    return run


nonfinite = lambda v: type(v) is float and not math.isfinite(v)  # noqa: E731
F_ = validated(BASE)


def raw_fit_mutating(y, u):
    out = F_['fit_first_order'](y, u)
    if isinstance(y, list):
        y[0] = y[0] + 0.0
        y.sort()
    return out


def raw_ne_mutating(y, u):
    out = F_['normal_equations'](y, u)
    if isinstance(u, list):
        u.reverse()
    return out


def raw_sim_mutating(a, b, y0, u):
    out = F_['simulate'](a, b, y0, u)
    if isinstance(u, list):
        u.append(0.0)
    return out


def raw_rand_mutating(ranges, draws, mode='uniform'):
    out = F_['randomize'](ranges, draws, mode)
    if isinstance(draws, list):
        draws[0] = out[0]
    return out


mutants = [
    ('simulate: input index shifted, b*u[k+1]', 'simulate', {'cores': {'sim': sim_shift}}),
    ('simulate: a and b swapped', 'simulate', {'cores': {'sim': sim_swapped}}),
    ('simulate: initial sample dropped from the result', 'simulate', {'cores': {'sim': sim_no_y0}}),
    ('simulate: input gain b ignored (b = 1)', 'simulate', {'cores': {'sim': sim_no_b}}),
    ('simulate: input replaced by the state, (a + b)*y', 'simulate',
     {'cores': {'sim': sim_input_uses_state}}),
    ('normal_equations: Suu replaced by sum u (not squared)', 'normal_equations',
     {'cores': {'ne': ne_suu_linear}}),
    ('normal_equations: target is y[k] instead of y[k+1]', 'normal_equations',
     {'cores': {'ne': ne_target_current}}),
    ('normal_equations: cross term Syu dropped', 'normal_equations', {'cores': {'ne': ne_diag_only}}),
    ('normal_equations: Syy summed over y[k+1] (misaligned)', 'normal_equations',
     {'cores': {'ne': ne_misaligned}}),
    ('normal_equations: regressor order swapped', 'normal_equations',
     {'cores': {'ne': ne_swapped_order}}),
    ('normal_equations: sums divided by n', 'normal_equations', {'cores': {'ne': ne_mean}}),
    ('normal_equations: last sample pair dropped', 'normal_equations',
     {'cores': {'ne': ne_drop_last}}),
    ('condition_number: ratio inverted (lambda_min/lambda_max)', 'condition_number',
     {'cores': {'cond': cond_flipped}}),
    ('condition_number: max diagonal / min diagonal', 'condition_number',
     {'cores': {'cond': cond_diag_ratio}}),
    ('condition_number: square root (condition number of the regressor, not of G)',
     'condition_number', {'cores': {'cond': cond_sqrt}}),
    ('condition_number: singular matrix gets a huge finite number', 'condition_number',
     {'cores': {'cond': cond_big_finite}}),
    ('condition_number: singular matrix returns None', 'condition_number',
     {'cores': {'cond': cond_none}}),
    ('condition_number: anything above 1e6 reported as inf', 'condition_number',
     {'cores': {'cond': cond_loose_singular}}),
    ('condition_number: trace^2/det instead of lambda ratio', 'condition_number',
     {'cores': {'cond': cond_trace_det}}),
    ('condition_number: zero matrix reported as perfectly conditioned', 'condition_number',
     {'cores': {'cond': cond_zero_ok}}),
    ('identifiability: only a constant input counts as unidentifiable', 'identifiability',
     {'cores': {'ident': ident_u_only}}),
    ('identifiability: a constant y is declared unidentifiable even with a moving u',
     'identifiability', {'cores': {'ident': ident_needs_y_vary}}),
    ('identifiability: weak band starts at condition number 2', 'identifiability',
     {'cores': {'ident': ident_low_weak}}),
    ('identifiability: a constant input with a still-moving y called unidentifiable',
     'identifiability', {'cores': {'ident': ident_const_u_unid}}),
    ('identifiability: weak band starts at condition number 1e2', 'identifiability',
     {'cores': {'ident': ident_weak_from_1e2}}),
    ('identifiability: weak band starts at condition number 1e3', 'identifiability',
     {'cores': {'ident': ident_weak_from_1e3}}),
    ('identifiability: weak band starts at condition number 1e5', 'identifiability',
     {'cores': {'ident': ident_weak_from_1e5}}),
    ('identifiability: weak band starts at condition number 1e6', 'identifiability',
     {'cores': {'ident': ident_weak_from_1e6}}),
    ('fit_first_order: constant input refused as unidentifiable', 'fit_first_order',
     {'cores': {'fit': fit_const_u_raises}}),
    ('heldout_check: strict < instead of <= at rms == tol', 'heldout_check',
     {'cores': {'held': held_strict}}),
    ('identifiability: weak logs called unidentifiable', 'identifiability',
     {'cores': {'ident': ident_weak_as_unid}}),
    ('identifiability: weak logs called identifiable', 'identifiability',
     {'cores': {'ident': ident_never_weak}}),
    ('identifiability: only u == 0 recognised as unidentifiable', 'identifiability',
     {'cores': {'ident': ident_only_zero_u}}),
    ('fit_first_order: a and b returned swapped', 'fit_first_order', {'cores': {'fit': fit_swapped}}),
    ('fit_first_order: two separate 1-D regressions (coupling ignored)', 'fit_first_order',
     {'cores': {'fit': fit_separate}}),
    ('fit_first_order: ridge term added (biased)', 'fit_first_order', {'cores': {'fit': fit_ridge}}),
    ('fit_first_order: last sample pair dropped', 'fit_first_order',
     {'cores': {'fit': fit_drop_last}}),
    ('fit_first_order: unidentifiable log returns (0, 0) instead of raising', 'fit_first_order',
     {'cores': {'fit': fit_no_raise}}),
    ('fit_first_order: unidentifiable log returns NaN instead of raising', 'fit_first_order',
     {'cores': {'fit': fit_nan_on_singular}}),
    ('fit_first_order: weak logs refused too', 'fit_first_order',
     {'cores': {'fit': fit_raises_weak}}),
    ('fit_first_order: input ignored (b = 0)', 'fit_first_order', {'cores': {'fit': fit_ignore_u}}),
    ('fit_first_order: targets taken one step late', 'fit_first_order',
     {'cores': {'fit': fit_target_previous}}),
    ('fit_first_order: means removed (intercept model)', 'fit_first_order',
     {'cores': {'fit': fit_mean_removed}}),
    ('residual_rms: sum of squares without the mean', 'residual_rms', {'cores': {'rms': rms_sum}}),
    ('residual_rms: mean square without sqrt', 'residual_rms', {'cores': {'rms': rms_mse}}),
    ('residual_rms: largest absolute residual', 'residual_rms', {'cores': {'rms': rms_maxabs}}),
    ('residual_rms: mean signed residual (errors cancel)', 'residual_rms',
     {'cores': {'rms': rms_mean_signed}}),
    ('residual_rms: divided by n + 1', 'residual_rms', {'cores': {'rms': rms_n_plus_one}}),
    ('residual_rms: multi-step rollout error instead of one-step', 'residual_rms',
     {'cores': {'rms': rms_rollout}}),
    ('residual_rms: input term b*u omitted', 'residual_rms', {'cores': {'rms': rms_no_b}}),
    ('residual_rms: a and b swapped in the prediction', 'residual_rms',
     {'cores': {'rms': rms_wrong_pred}}),
    ('heldout_check: tolerance halved', 'heldout_check', {'cores': {'held': held_train_scale}}),
    ('heldout_check: verdict inverted', 'heldout_check', {'cores': {'held': held_inverted}}),
    ('heldout_check: mean square compared with tol', 'heldout_check',
     {'cores': {'held': held_mse_vs_tol}}),
    ('heldout_check: always passes', 'heldout_check', {'cores': {'held': held_always}}),
    ('heldout_check: returns int flag instead of rms first', 'heldout_check',
     {'cores': {'held': held_returns_flag_only}}),
    ('heldout_check: rms replaced by sum of squares root', 'heldout_check',
     {'cores': {'held': held_sum}}),
    ('parameter_std: sigma forgotten', 'parameter_std', {'cores': {'std': std_no_sigma}}),
    ('parameter_std: variance returned instead of std', 'parameter_std',
     {'cores': {'std': std_variance}}),
    ('parameter_std: sigma/sqrt(G_ii), correlation ignored', 'parameter_std',
     {'cores': {'std': std_diag_only}}),
    ('parameter_std: std_a and std_b swapped', 'parameter_std', {'cores': {'std': std_swapped}}),
    ('parameter_std: sigma*sqrt(G_ii), G used instead of its inverse', 'parameter_std',
     {'cores': {'std': std_not_inverse}}),
    ('parameter_std: sigma squared inside the root', 'parameter_std',
     {'cores': {'std': std_sigma_squared}}),
    ('parameter_std: unidentifiable log returns inf instead of raising', 'parameter_std',
     {'cores': {'std': std_no_raise}}),
    ('randomize: draws ignored, midpoint returned', 'randomize', {'cores': {'rand': rand_midpoint}}),
    ('randomize: lo + d*hi', 'randomize', {'cores': {'rand': rand_lo_plus_d_hi}}),
    ('randomize: d*(hi - lo) without lo', 'randomize', {'cores': {'rand': rand_d_only}}),
    ('randomize: no clamp, floating point leaves the range', 'randomize',
     {'cores': {'rand': rand_unclamped}}),
    ('randomize: log mode treated as uniform', 'randomize', {'cores': {'rand': rand_log_as_uniform}}),
    ('randomize: uniform mode treated as log', 'randomize', {'cores': {'rand': rand_uniform_as_log}}),
    ('randomize: draws applied in reverse order', 'randomize', {'cores': {'rand': rand_reversed}}),
    ('randomize: first draw reused for every parameter', 'randomize',
     {'cores': {'rand': rand_first_draw}}),
    ('randomize: 1 - d instead of d', 'randomize', {'cores': {'rand': rand_one_minus}}),
    ('randomize: range walked from hi down to lo', 'randomize',
     {'cores': {'rand': rand_reversed_ranges}}),
    ('randomize: result rounded to one decimal', 'randomize', {'cores': {'rand': rand_rounded}}),
    # validation and contract bugs
    ('NaN in y accepted by fit_first_order', 'fit_first_order', {'raw': {
        'fit_first_order': accepts_when(
            lambda y, u: isinstance(y, list) and any(nonfinite(v) for v in y),
            F_['fit_first_order'], (0.0, 0.0))}}),
    ('bool in u accepted by normal_equations', 'normal_equations', {'raw': {
        'normal_equations': accepts_when(
            lambda y, u: isinstance(u, list) and any(v is True for v in u),
            F_['normal_equations'], ([[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0]))}}),
    ('length mismatch accepted by fit_first_order', 'fit_first_order', {'raw': {
        'fit_first_order': accepts_when(
            lambda y, u: isinstance(y, list) and isinstance(u, list) and len(y) == len(u),
            F_['fit_first_order'], (0.0, 0.0))}}),
    ('single sample pair accepted by identifiability', 'identifiability', {'raw': {
        'identifiability': accepts_when(
            lambda y, u: isinstance(u, list) and len(u) == 1,
            F_['identifiability'], 'identifiable')}}),
    ('51 sample pairs accepted by normal_equations', 'normal_equations', {'raw': {
        'normal_equations': accepts_when(
            lambda y, u: isinstance(u, list) and len(u) > 50,
            F_['normal_equations'], ([[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0]))}}),
    ('sigma = 0 accepted by parameter_std', 'parameter_std', {'raw': {
        'parameter_std': accepts_when(
            lambda y, u, s: s == 0 and type(s) is float, F_['parameter_std'], (0.0, 0.0))}}),
    ('negative tol accepted by heldout_check', 'heldout_check', {'raw': {
        'heldout_check': accepts_when(
            lambda a, b, y, u, t: isinstance(t, float) and t < 0, F_['heldout_check'],
            (0.0, False))}}),
    ('asymmetric G accepted by condition_number', 'condition_number', {'raw': {
        'condition_number': accepts_when(
            lambda G: isinstance(G, list) and len(G) == 2 and isinstance(G[0], list)
            and G[0][1] != G[1][0] and abs(G[0][1] - G[1][0]) > 0.5,
            F_['condition_number'], 1.0)}}),
    ('indefinite G accepted by condition_number', 'condition_number', {'raw': {
        'condition_number': accepts_when(
            lambda G: isinstance(G, list) and len(G) == 2 and isinstance(G[0], list)
            and G[0][0] == 1.0 and G[0][1] == 2.0 and G[1][1] == 1.0,
            F_['condition_number'], 3.0)}}),
    ('lo > hi accepted by randomize', 'randomize', {'raw': {
        'randomize': accepts_when(
            lambda r, d, m='uniform': isinstance(r, list) and any(
                isinstance(p, (list, tuple)) and len(p) == 2 and p[0] > p[1] for p in r),
            F_['randomize'], [0.0])}}),
    ('draw above 1 accepted by randomize', 'randomize', {'raw': {
        'randomize': accepts_when(
            lambda r, d, m='uniform': isinstance(d, list) and any(
                type(v) is float and v > 1 for v in d), F_['randomize'], [0.0])}}),
    ('log with lo = 0 raises ZeroDivisionError, not ValueError', 'randomize', {'raw': {
        'randomize': lambda r, d, m='uniform': (
            (_ for _ in ()).throw(ZeroDivisionError()) if m == 'log' and isinstance(r, tuple)
            and r[0][0] == 0.0 else F_['randomize'](r, d, m))}}),
    ('unknown mode accepted by randomize', 'randomize', {'raw': {
        'randomize': accepts_when(
            lambda r, d, m='uniform': m == 'gauss', F_['randomize'], [0.0])}}),
    ('empty u accepted by simulate', 'simulate', {'raw': {
        'simulate': accepts_when(
            lambda a, b, y0, u: isinstance(u, list) and len(u) == 0, F_['simulate'], [0.0])}}),
    ('fit mutates y', 'fit_first_order', {'raw': {'fit_first_order': raw_fit_mutating}}),
    ('normal_equations mutates u', 'normal_equations', {'raw': {
        'normal_equations': raw_ne_mutating}}),
    ('simulate mutates u', 'simulate', {'raw': {'simulate': raw_sim_mutating}}),
    ('randomize mutates draws', 'randomize', {'raw': {'randomize': raw_rand_mutating}}),
]
require(len(mutants) >= 30, 'need at least 30 injected bugs: ' + str(len(mutants)))
for label, function, spec_ in mutants:
    result = run_with(spec_.get('cores'), spec_.get('raw'))
    require(result, 'injected bug survived: ' + label)
    require(any(function in line for line in result),
            'bug rejected for the wrong reason (' + label + '): ' + str(result[:3]))

# restore the author reference and run the starter once more
run_with()
print('Identification kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (standard, Joseph, P - K S K^T and
information-form updates; sequential and batch fusion; different covariance
tests) that must pass, and named injected bugs that must be rejected for the
function they target. Plain checks only, so it also works under python -O.
"""
import ast
import importlib.util
import json
import math
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('kalman_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L10-kalman.v1.py'
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
names = ('predict', 'innovation', 'kalman_gain', 'update', 'fuse_sequential',
         'fuse_information', 'nis', 'cv_model', 'run_filter', 'is_valid_covariance')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _update_ref') > spoiler and text.index('_UPD_CASES = ') > spoiler,
        'oracle and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('kalman_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 10 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if value is None:
        return None
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def encode(value):
    return [encode(v) for v in value] if isinstance(value, (list, tuple)) else dec(value)


def entry(structure, names_, args):
    return {'structure': structure,
            'inputs': {name: encode(value) for name, value in zip(names_, args)}}


def sensor_entry(args):
    return [list(map(encode, s)) for s in args]


expected_samples = (
    [entry('kalman.predict@1', ('x', 'P', 'F', 'Q'), c[0]) for c in kit._PRED_CASES]
    + [entry('kalman.innovation@1', ('x_pred', 'P_pred', 'H', 'R', 'z'), c[0])
       for c in kit._INNOV_CASES]
    + [entry('kalman.gain@1', ('P_pred', 'H', 'R'), c[0]) for c in kit._GAIN_CASES]
    + [entry('kalman.update@1', ('x_pred', 'P_pred', 'H', 'R', 'z'), c[0]) for c in kit._UPD_CASES]
    + [entry('kalman.fuse@1', ('x0', 'P0', 'sensors'), c[0]) for c in kit._FUSE_CASES]
    + [entry('kalman.nis@1', ('y', 'S'), c[0]) for c in kit._NIS_CASES]
    + [entry('kalman.cv-model@1', ('dt', 'q'), c[0]) for c in kit._CV_CASES]
    + [entry('kalman.run@1', ('x0', 'P0', 'F', 'Q', 'H', 'R', 'zs'), c[0]) for c in kit._RUN_CASES]
    + [entry('kalman.covariance-check@1', ('P',), (c[0],)) for c in kit._COV_CASES])
samples = json.loads((root / 'content/labs/L10-kalman.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L10-kalman'], 'samples must hold only L10-kalman')
require(samples['kits']['L10-kalman'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50: ' + str(len(expected_samples)))


# ---- author reference implementation (validation + replaceable cores) ----
def isreal(v):
    return type(v) in (int, float) and math.isfinite(v)


def rv(v, low, high):
    if not isreal(v) or not low <= v <= high:
        raise ValueError


def cvec(x):
    if not isinstance(x, (list, tuple)) or len(x) not in (1, 2):
        raise ValueError
    for v in x:
        rv(v, -1e4, 1e4)
    return [float(v) for v in x]


def cmat(M, n, bound):
    if not isinstance(M, (list, tuple)) or len(M) != n:
        raise ValueError
    out = []
    for row in M:
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise ValueError
        for v in row:
            rv(v, -bound, bound)
        out.append([float(v) for v in row])
    return out


def min_eig(P):
    if len(P) == 1:
        return P[0][0]
    return (P[0][0] + P[1][1])/2 - math.hypot((P[0][0] - P[1][1])/2, (P[0][1] + P[1][0])/2)


def scale(P):
    return max(1.0, max(abs(v) for row in P for v in row))


def cov_ok(P, floor=0.0, sym_tol=1e-9):
    t = sym_tol*scale(P)
    asym = abs(P[0][1] - P[1][0]) if len(P) == 2 else 0.0
    return asym <= t and min_eig(P) >= -1e-9*scale(P) + floor


def ccov(P, n, pd=False):
    P = cmat(P, n, 1e4)
    if not cov_ok(P):
        raise ValueError
    if pd and min_eig(P) < 1e-6:
        raise ValueError
    return P


def cH(H, n):
    if not isinstance(H, (list, tuple)) or len(H) != 1:
        raise ValueError
    row = H[0]
    if not isinstance(row, (list, tuple)) or len(row) != n:
        raise ValueError
    for v in row:
        rv(v, -100, 100)
    return [[float(v) for v in row]]


def cR(R):
    rv(R, 1e-6, 1e4)
    return float(R)


def csens(sensors, n):
    if not isinstance(sensors, (list, tuple)) or not 1 <= len(sensors) <= 4:
        raise ValueError
    out = []
    for s in sensors:
        if not isinstance(s, (list, tuple)) or len(s) != 3:
            raise ValueError
        rv(s[2], -1e4, 1e4)
        out.append((cH(s[0], n), cR(s[1]), float(s[2])))
    return out


def mm(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def tr(A):
    return [list(c) for c in zip(*A)]


def eye(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def sym(A):
    n = len(A)
    return [[(A[i][j] + A[j][i])/2 for j in range(n)] for i in range(n)]


def madd(A, B):
    return [[a + b for a, b in zip(r, s)] for r, s in zip(A, B)]


def msub(A, B):
    return [[a - b for a, b in zip(r, s)] for r, s in zip(A, B)]


def inv(A):
    n = len(A)
    M = [list(A[i]) + eye(n)[i] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        d = M[c][c]
        M[c] = [v/d for v in M[c]]
        for r in range(n):
            if r != c:
                f = M[r][c]
                M[r] = [a - f*b for a, b in zip(M[r], M[c])]
    return [row[n:] for row in M]


def matvec(A, v):
    return [sum(a*b for a, b in zip(row, v)) for row in A]


# cores take validated float lists
def predict_core(x, P, F, Q):
    return matvec(F, x), madd(mm(mm(F, P), tr(F)), Q)


def innov_core(x, P, H, R, z):
    h = H[0]
    y = z - sum(a*b for a, b in zip(h, x))
    return y, sum(h[i]*sum(P[i][j]*h[j] for j in range(len(x))) for i in range(len(x))) + R


def gain_core(P, H, R):
    h = H[0]
    n = len(h)
    PHt = [sum(P[i][j]*h[j] for j in range(n)) for i in range(n)]
    S = sum(h[i]*PHt[i] for i in range(n)) + R
    return [v/S for v in PHt]


def update_core(x, P, H, R, z):
    n = len(x)
    y, S = innov_core(x, P, H, R, z)
    K = gain_core(P, H, R)
    A = msub(eye(n), [[K[i]*H[0][j] for j in range(n)] for i in range(n)])
    J = madd(mm(mm(A, P), tr(A)), [[R*K[i]*K[j] for j in range(n)] for i in range(n)])
    return [x[i] + K[i]*y for i in range(n)], sym(J)


def fuse_seq_core(x, P, sensors):
    for H, R, z in sensors:
        x, P = kit_update(x, P, H, R, z)
    return x, P


def fuse_info_core(x, P, sensors):
    n = len(x)
    Pi = inv(P)
    Y = [r[:] for r in Pi]
    v = matvec(Pi, x)
    for H, R, z in sensors:
        h = H[0]
        for i in range(n):
            v[i] += h[i]*z/R
            for j in range(n):
                Y[i][j] += h[i]*h[j]/R
    Pn = inv(Y)
    return matvec(Pn, v), sym(Pn)


def nis_core(y, S):
    return y*y/S


def cv_core(dt, q):
    return ([[1.0, dt], [0.0, 1.0]],
            [[q*dt**3/3, q*dt**2/2], [q*dt**2/2, q*dt]])


def run_core(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        x, P = predict_core(x, P, F, Q)
        if z is None:
            out.append((x, P, None))
            continue
        y, S = innov_core(x, P, H, R, z)
        x, P = kit_update(x, P, H, R, z)
        out.append((x, P, nis_core(y, S)))
    return out


def cov_core(P):
    return cov_ok(P)


# `kit_update` resolves to whichever core update the current scenario installs.
current = {}


def kit_update(x, P, H, R, z):
    return current['update_core'](x, P, H, R, z)


def validated(cores):
    """Build the ten public functions from replaceable cores."""
    def predict(x, P, F, Q):
        x = cvec(x)
        n = len(x)
        return cores['predict'](x, ccov(P, n), cmat(F, n, 100), ccov(Q, n))

    def innovation(x, P, H, R, z):
        x = cvec(x)
        n = len(x)
        P, H, R = ccov(P, n), cH(H, n), cR(R)
        rv(z, -1e4, 1e4)
        return cores['innov'](x, P, H, R, float(z))

    def kalman_gain(P, H, R):
        n = len(P) if isinstance(P, (list, tuple)) else 0
        if n not in (1, 2):
            raise ValueError
        P = ccov(P, n)
        return cores['gain'](P, cH(H, n), cR(R))

    def update(x, P, H, R, z):
        x = cvec(x)
        n = len(x)
        P, H, R = ccov(P, n), cH(H, n), cR(R)
        rv(z, -1e4, 1e4)
        return cores['update'](x, P, H, R, float(z))

    def fuse_sequential(x, P, sensors):
        x = cvec(x)
        n = len(x)
        return cores['fuse_seq'](x, ccov(P, n, pd=True), csens(sensors, n))

    def fuse_information(x, P, sensors):
        x = cvec(x)
        n = len(x)
        return cores['fuse_info'](x, ccov(P, n, pd=True), csens(sensors, n))

    def nis(y, S):
        rv(y, -1e4, 1e4)
        if not isreal(S) or not 0 < S <= 1e8:
            raise ValueError
        return cores['nis'](y, S)

    def cv_model(dt, q):
        rv(dt, 1e-3, 10)
        rv(q, 0, 100)
        return cores['cv'](float(dt), float(q))

    def run_filter(x, P, F, Q, H, R, zs):
        x = cvec(x)
        n = len(x)
        P, F, Q, H, R = ccov(P, n), cmat(F, n, 100), ccov(Q, n), cH(H, n), cR(R)
        if not isinstance(zs, (list, tuple)) or len(zs) > 20:
            raise ValueError
        for z in zs:
            if z is not None:
                rv(z, -1e4, 1e4)
        return cores['run'](x, P, F, Q, H, R, [None if z is None else float(z) for z in zs])

    def is_valid_covariance(P):
        n = len(P) if isinstance(P, (list, tuple)) else 0
        if n not in (1, 2):
            raise ValueError
        return cores['cov'](cmat(P, n, 1e4))

    return {'predict': predict, 'innovation': innovation, 'kalman_gain': kalman_gain,
            'update': update, 'fuse_sequential': fuse_sequential,
            'fuse_information': fuse_information, 'nis': nis, 'cv_model': cv_model,
            'run_filter': run_filter, 'is_valid_covariance': is_valid_covariance}


BASE = {'predict': predict_core, 'innov': innov_core, 'gain': gain_core,
        'update': update_core, 'fuse_seq': fuse_seq_core, 'fuse_info': fuse_info_core,
        'nis': nis_core, 'cv': cv_core, 'run': run_core, 'cov': cov_core}


def run_with(cores=None, raw=None):
    """Install cores (and/or raw public functions) and run the kit self-check."""
    merged = dict(BASE)
    merged.update(cores or {})
    current['update_core'] = merged['update']
    functions = validated(merged)
    functions.update(raw or {})
    for name, fn in functions.items():
        setattr(kit, name, fn)
    return kit.self_check()


require(run_with() == [], 'author reference must pass: ' + str(run_with()))


# ---- independent cross-check of the hand tables against the information form ----
for args, mode, want in kit._UPD_CASES:
    if mode == 'hand':
        got = update_core(*[kit._fresh(a) if isinstance(a, list) else a for a in args])
        require(all(abs(a - b) <= 1e-12 for a, b in zip(got[0], want[0])), 'hand update x table')
        alt = kit._info_update_ref(*args)
        require(all(abs(a - b) <= 1e-12 for a, b in zip(alt[0], want[0])), 'hand update x info')
        require(all(abs(alt[1][i][j] - want[1][i][j]) <= 1e-12
                    for i in range(len(want[1])) for j in range(len(want[1]))),
                'hand update P info')
for args, _mode, _want in kit._FUSE_CASES:
    a = kit._fuse_ref(*args)
    b = kit._info_update_ref(args[0], args[1], None, None, None, args[2])
    require(all(abs(u - v) <= 1e-9 for u, v in zip(a[0], b[0])), 'sequential ref vs information ref')
    require(all(abs(a[1][i][j] - b[1][i][j]) <= 1e-9
                for i in range(len(a[1])) for j in range(len(a[1]))), 'fuse P agrees')


# ---- valid alternatives ----
def update_standard(x, P, H, R, z):
    """(I - KH) P, not symmetrised (rounding asymmetry stays within the band)."""
    n = len(x)
    y, S = innov_core(x, P, H, R, z)
    K = gain_core(P, H, R)
    A = msub(eye(n), [[K[i]*H[0][j] for j in range(n)] for i in range(n)])
    return [x[i] + K[i]*y for i in range(n)], mm(A, P)


def update_pks(x, P, H, R, z):
    """P - K S K^T, symmetrised."""
    n = len(x)
    y, S = innov_core(x, P, H, R, z)
    K = gain_core(P, H, R)
    return ([x[i] + K[i]*y for i in range(n)],
            sym([[P[i][j] - K[i]*S*K[j] for j in range(n)] for i in range(n)]))


def update_information(x, P, H, R, z):
    """Information form when P is invertible, else Joseph."""
    det = P[0][0] if len(P) == 1 else P[0][0]*P[1][1] - P[0][1]*P[1][0]
    if det <= 1e-8:
        return update_core(x, P, H, R, z)
    return fuse_info_core(x, P, [(H, R, z)])


def update_outer(x, P, H, R, z):
    """P - (P H^T)(P H^T)^T / S with explicit loops; tuple output."""
    n = len(x)
    h = H[0]
    PHt = [sum(P[i][j]*h[j] for j in range(n)) for i in range(n)]
    S = sum(h[i]*PHt[i] for i in range(n)) + R
    y = z - sum(h[i]*x[i] for i in range(n))
    return (tuple(x[i] + PHt[i]*y/S for i in range(n)),
            tuple(tuple((P[i][j] + P[j][i])/2 - PHt[i]*PHt[j]/S for j in range(n))
                  for i in range(n)))


def fuse_seq_stepwise(x, P, sensors):
    """Sequential through the information increment of each sensor."""
    for H, R, z in sensors:
        x, P = fuse_info_core(x, P, [(H, R, z)])
    return x, P


def fuse_info_gauss(x, P, sensors):
    """Batch weighted least squares: normal equations with the prior as a pseudo-measurement."""
    n = len(x)
    rows = [(row, 1.0) for row in eye(n)]
    Pi = inv(P)
    A = [r[:] for r in Pi]
    b = matvec(Pi, x)
    for H, R, z in sensors:
        h = H[0]
        for i in range(n):
            b[i] += h[i]*z/R
            for j in range(n):
                A[i][j] += h[i]*h[j]/R
    Pn = inv(A)
    return tuple(matvec(Pn, b)), tuple(tuple(r) for r in sym(Pn))


def cov_trace_det(P):
    """Eigenvalues from trace and determinant."""
    if len(P) == 1:
        return P[0][0] >= -1e-9*scale(P)
    t = 1e-9*scale(P)
    if abs(P[0][1] - P[1][0]) > t:
        return False
    tr_, det = P[0][0] + P[1][1], P[0][0]*P[1][1] - P[0][1]*P[1][0]
    lo = (tr_ - math.sqrt(max(0.0, tr_*tr_ - 4*det)))/2
    return lo >= -t


def cov_leading(P):
    """Diagonal and determinant (principal minors) with the same tolerance."""
    t = 1e-9*scale(P)
    if len(P) == 1:
        return P[0][0] >= -t
    if abs(P[0][1] - P[1][0]) > t:
        return False
    det = P[0][0]*P[1][1] - P[0][1]*P[1][0]
    return P[0][0] >= -t and P[1][1] >= -t and det >= -t*max(1.0, P[0][0] + P[1][1])


def run_stepwise(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        xp, Pp = current_pred(x, P, F, Q)
        if z is None:
            x, P = xp, Pp
            out.append((tuple(x), tuple(map(tuple, P)), None))
            continue
        y, S = innov_core(xp, Pp, H, R, z)
        x, P = current['update_core'](xp, Pp, H, R, z)
        out.append((tuple(x), tuple(map(tuple, P)), float(y*y/S)))
    return out


def current_pred(x, P, F, Q):
    n = len(x)
    xn = [sum(F[i][j]*x[j] for j in range(n)) for i in range(n)]
    Pn = [[sum(F[i][a]*P[a][b]*F[j][b] for a in range(n) for b in range(n)) + Q[i][j]
           for j in range(n)] for i in range(n)]
    return xn, Pn


def predict_loops(x, P, F, Q):
    return current_pred(x, P, F, Q)


def cv_int(dt, q):
    return ([[1, dt], [0, 1]], [[q*dt*dt*dt/3, q*dt*dt/2], [q*dt*dt/2, q*dt]])


alternatives = [
    ('author: Joseph form, sequential fusion, eigenvalue test', {}),
    ('standard (I-KH)P update unsymmetrised, trace/determinant covariance test',
     {'update': update_standard, 'cov': cov_trace_det}),
    ('P - K S K^T update, explicit-loop prediction, principal-minor test',
     {'update': update_pks, 'predict': predict_loops, 'cov': cov_leading}),
    ('information-form update with Joseph fallback, step-wise information-increment fusion',
     {'update': update_information, 'fuse_seq': fuse_seq_stepwise}),
    ('outer-product update with tuples, normal-equation batch fusion returning tuples',
     {'update': update_outer, 'fuse_info': fuse_info_gauss}),
    ('step-wise tuple run_filter on the standard update, integer-safe CV model',
     {'update': update_standard, 'run': run_stepwise, 'cv': cv_int}),
]
for label, cores in alternatives:
    result = run_with(cores)
    require(result == [], 'false reject (' + label + '): ' + str(result))


# ---- injected bugs ----
def pc(f):
    return {'predict': f}


def mut_update(f):
    return {'update': f}


def eyeminus(K, H):
    n = len(K)
    return msub(eye(n), [[K[i]*H[0][j] for j in range(n)] for i in range(n)])


def predict_transposed(x, P, F, Q):
    return matvec(F, x), madd(mm(mm(tr(F), P), F), Q)


def predict_no_q(x, P, F, Q):
    return matvec(F, x), mm(mm(F, P), tr(F))


def predict_q_inside(x, P, F, Q):
    return matvec(F, x), mm(mm(F, madd(P, Q)), tr(F))


def predict_no_transpose(x, P, F, Q):
    return matvec(F, x), madd(mm(mm(F, P), F), Q)


def predict_ft_x(x, P, F, Q):
    return matvec(tr(F), x), madd(mm(mm(F, P), tr(F)), Q)


def predict_ignore_f(x, P, F, Q):
    return matvec(F, x), madd(P, Q)


def predict_diag(x, P, F, Q):
    px, pp = predict_core(x, P, F, Q)
    return px, [[pp[i][j] if i == j else 0.0 for j in range(len(x))] for i in range(len(x))]


def innov_sign(x, P, H, R, z):
    y, S = innov_core(x, P, H, R, z)
    return -y, S


def innov_no_r(x, P, H, R, z):
    y, S = innov_core(x, P, H, R, z)
    return y, S - R


def innov_p00(x, P, H, R, z):
    y, S = innov_core(x, P, H, R, z)
    return y, P[0][0] + R


def innov_std(x, P, H, R, z):
    y, S = innov_core(x, P, H, R, z)
    return y, S - R + R*R


def innov_raw_z(x, P, H, R, z):
    y, S = innov_core(x, P, H, R, z)
    return z - x[0], S


def gain_no_p_in_s(P, H, R):
    h = H[0]
    n = len(h)
    return [sum(P[i][j]*h[j] for j in range(n))/R for i in range(n)]


def gain_no_r(P, H, R):
    h = H[0]
    n = len(h)
    PHt = [sum(P[i][j]*h[j] for j in range(n)) for i in range(n)]
    S = sum(h[i]*PHt[i] for i in range(n))
    return [v/S for v in PHt]


def gain_normalised(P, H, R):
    K = gain_core(P, H, R)
    total = sum(abs(v) for v in K)
    return [v/total for v in K]


def gain_first_only(P, H, R):
    K = gain_core(P, H, R)
    return [K[0]]*len(K)


def upd_no_cov(x, P, H, R, z):
    return update_core(x, P, H, R, z)[0], P


def upd_p_minus_kh(x, P, H, R, z):
    K = gain_core(P, H, R)
    n = len(x)
    return update_core(x, P, H, R, z)[0], [[P[i][j] - K[i]*H[0][j] for j in range(n)]
                                          for i in range(n)]


def upd_joseph_no_r(x, P, H, R, z):
    K = gain_core(P, H, R)
    A = eyeminus(K, H)
    return update_core(x, P, H, R, z)[0], mm(mm(A, P), tr(A))


def upd_no_hx(x, P, H, R, z):
    K = gain_core(P, H, R)
    xn, Pn = update_core(x, P, H, R, z)
    return [x[i] + K[i]*z for i in range(len(x))], Pn


def upd_minus(x, P, H, R, z):
    K = gain_core(P, H, R)
    y, _ = innov_core(x, P, H, R, z)
    return [x[i] - K[i]*y for i in range(len(x))], update_core(x, P, H, R, z)[1]


def upd_joseph_k_unscaled(x, P, H, R, z):
    K = gain_core(P, H, R)
    n = len(x)
    A = eyeminus(K, H)
    return (update_core(x, P, H, R, z)[0],
            sym(madd(mm(mm(A, P), tr(A)), [[K[i]*K[j] for j in range(n)] for i in range(n)])))


def upd_right_multiply(x, P, H, R, z):
    K = gain_core(P, H, R)
    return update_core(x, P, H, R, z)[0], mm(P, eyeminus(K, H))


def upd_first_component(x, P, H, R, z):
    xn, Pn = update_core(x, P, H, R, z)
    return [xn[0]] + list(x[1:]), Pn


def upd_prior_gain(x, P, H, R, z):
    xn, Pn = update_core(x, P, H, R, z)
    K = [v for v in gain_core(P, H, R)]
    y, _ = innov_core(x, P, H, R, z)
    return [x[i] + 0.5*K[i]*y for i in range(len(x))], Pn


def fuse_seq_stale_p(x, P, sensors):
    x0 = list(x)
    P0 = P
    for H, R, z in sensors:
        x, _ = update_core(x, P0, H, R, z)
    return x, update_core(x0, P0, sensors[-1][0], sensors[-1][1], sensors[-1][2])[1]


def fuse_seq_stale_x(x, P, sensors):
    x0 = list(x)
    for H, R, z in sensors:
        _, P = update_core(x0, P, H, R, z)
        x, _ = update_core(x0, P, H, R, z)
    return x, P


def fuse_seq_first_only(x, P, sensors):
    return update_core(x, P, *sensors[0])


def fuse_seq_last_only(x, P, sensors):
    return update_core(x, P, *sensors[-1])


def fuse_info_no_prior_mean(x, P, sensors):
    return fuse_info_core([0.0]*len(x), P, sensors)[0], fuse_info_core(x, P, sensors)[1]


def fuse_info_adds_r(x, P, sensors):
    n = len(x)
    Pi = inv(P)
    Y = [r[:] for r in Pi]
    v = matvec(Pi, x)
    for H, R, z in sensors:
        h = H[0]
        for i in range(n):
            v[i] += h[i]*z*R
            for j in range(n):
                Y[i][j] += h[i]*h[j]*R
    Pn = inv(Y)
    return matvec(Pn, v), Pn


def fuse_info_returns_y(x, P, sensors):
    xn, Pn = fuse_info_core(x, P, sensors)
    return xn, inv(Pn)


def fuse_info_y_times(x, P, sensors):
    n = len(x)
    Pi = inv(P)
    Y = [r[:] for r in Pi]
    v = matvec(Pi, x)
    for H, R, z in sensors:
        h = H[0]
        for i in range(n):
            v[i] += h[i]*z/R
            for j in range(n):
                Y[i][j] += h[i]*h[j]/R
    return matvec(Y, v), inv(Y)


def fuse_seq_equal_weights(x, P, sensors):
    n = len(x)
    xn, Pn = fuse_info_core(x, P, sensors)
    avg = sum(s[2] for s in sensors)/len(sensors)
    return [xn[i] if n == 2 and i == 1 else (x[i] + avg)/2 for i in range(n)], Pn


def nis_linear(y, S):
    return y/S


def nis_times(y, S):
    return y*y*S


def nis_not_squared(y, S):
    return abs(y)/math.sqrt(S)


def nis_sqrt_s(y, S):
    return y*y/math.sqrt(S)


def cv_swapped(dt, q):
    F, Q = cv_core(dt, q)
    return F, [[Q[1][1], Q[0][1]], [Q[1][0], Q[0][0]]]


def cv_const_half(dt, q):
    F, Q = cv_core(dt, q)
    return F, [[q*dt**3/2, Q[0][1]], [Q[1][0], Q[1][1]]]


def cv_f_transposed(dt, q):
    F, Q = cv_core(dt, q)
    return tr(F), Q


def cv_diag_q(dt, q):
    F, _ = cv_core(dt, q)
    return F, [[q*dt, 0.0], [0.0, q*dt]]


def cv_no_q_scale(dt, q):
    F, Q = cv_core(dt, q)
    return F, [[v/q if q else v for v in row] for row in Q]


def run_dropout_updates(x, P, F, Q, H, R, zs):
    return run_core(x, P, F, Q, H, R, [0.0 if z is None else z for z in zs])


def run_dropout_no_predict(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        if z is None:
            out.append((x, P, None))
            continue
        out.extend(run_core(x, P, F, Q, H, R, [z]))
        x, P = out[-1][0], out[-1][1]
    return out


def run_nis_after(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        x, P = predict_core(x, P, F, Q)
        if z is None:
            out.append((x, P, None))
            continue
        x, P = update_core(x, P, H, R, z)
        y, S = innov_core(x, P, H, R, z)
        out.append((x, P, y*y/S))
    return out


def run_nis_no_r(x, P, F, Q, H, R, zs):
    rows = run_core(x, P, F, Q, H, R, zs)
    out = []
    for z, row in zip(zs, rows):
        out.append(row)
    res = []
    xs, Ps = x, P
    for z, row in zip(zs, rows):
        xs, Ps = predict_core(xs, Ps, F, Q)
        if z is None:
            res.append(row)
        else:
            y, S = innov_core(xs, Ps, H, R, z)
            res.append((row[0], row[1], y*y/(S - R)))
            xs, Ps = update_core(xs, Ps, H, R, z)
    return res


def run_skip_first_predict(x, P, F, Q, H, R, zs):
    out = []
    for k, z in enumerate(zs):
        if k > 0:
            x, P = predict_core(x, P, F, Q)
        if z is None:
            out.append((x, P, None))
            continue
        y, S = innov_core(x, P, H, R, z)
        x, P = update_core(x, P, H, R, z)
        out.append((x, P, y*y/S))
    return out


def run_zero_nis(x, P, F, Q, H, R, zs):
    return [(a, b, 0.0 if c is None else c) for a, b, c in run_core(x, P, F, Q, H, R, zs)]


def run_prior_state(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        x, P = predict_core(x, P, F, Q)
        if z is None:
            out.append((x, P, None))
            continue
        y, S = innov_core(x, P, H, R, z)
        out.append((x, P, y*y/S))
        x, P = update_core(x, P, H, R, z)
    return out


def cov_diag_only(P):
    return all(P[i][i] >= 0 for i in range(len(P)))


def cov_sym_only(P):
    return len(P) == 1 or abs(P[0][1] - P[1][0]) <= 1e-9*scale(P)


def cov_strict(P):
    return cov_ok(P) and min_eig(P) > 1e-12


def cov_det_only(P):
    det = P[0][0] if len(P) == 1 else P[0][0]*P[1][1] - P[0][1]*P[1][0]
    return det >= 0 and cov_sym_only(P)


def cov_loose_sym(P):
    return len(P) == 1 or (abs(P[0][1] - P[1][0]) <= 1e-3 and min_eig(P) >= -1e-9*scale(P))


def cov_loose_eig(P):
    return cov_ok(P, floor=0.0) or (cov_sym_only(P) and min_eig(P) >= -1e-4)


def cov_int(P):
    return 1 if cov_ok(P) else 0


def accepts_when(check, function, value):
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


def mutating_predict(x, P, F, Q):
    x = cvec(x)
    return None


def raw_predict_mutating(x, P, F, Q):
    px, pP = validated(BASE)['predict'](x, P, F, Q)
    if isinstance(P, list):
        P[0][0] = P[0][0]*1.0 + 0.0
        x[0] = x[0] + 0.0
        P[0][0] += 1e-3
    return px, pP


def raw_update_mutating(x, P, H, R, z):
    out = validated(BASE)['update'](x, P, H, R, z)
    if isinstance(x, list):
        x[0] = out[0][0]
    return out


def zdiv_nis(y, S):
    return y*y/S


def partial_update(x, P, H, R, z):
    if len(x) == 2 and H[0][1] != 0:
        raise NotImplementedError('velocity measurement left as the starter')
    return update_core(x, P, H, R, z)


def vdt(cores_key, name):
    pass


F_ = validated(BASE)
nonfinite = lambda v: type(v) is float and not math.isfinite(v)  # noqa: E731

mutants = [
    ('predict: P_pred = F^T P F (wrong side)', 'predict', {'cores': {'predict': predict_transposed}}),
    ('predict: process noise Q left out', 'predict', {'cores': {'predict': predict_no_q}}),
    ('predict: Q added before propagating, F (P + Q) F^T', 'predict',
     {'cores': {'predict': predict_q_inside}}),
    ('predict: F P F without the transpose', 'predict', {'cores': {'predict': predict_no_transpose}}),
    ('predict: mean propagated with F^T', 'predict', {'cores': {'predict': predict_ft_x}}),
    ('predict: F ignored in the covariance, P + Q', 'predict', {'cores': {'predict': predict_ignore_f}}),
    ('predict: cross-covariance dropped (diagonal P only)', 'predict',
     {'cores': {'predict': predict_diag}}),
    ('innovation: sign flipped, H x - z', 'innovation', {'cores': {'innov': innov_sign}}),
    ('innovation: S without the measurement noise R', 'innovation', {'cores': {'innov': innov_no_r}}),
    ('innovation: S = P00 + R regardless of H', 'innovation', {'cores': {'innov': innov_p00}}),
    ('innovation: R treated as a standard deviation (R^2 in S)', 'innovation',
     {'cores': {'innov': innov_std}}),
    ('innovation: z minus the first state ignoring H', 'innovation', {'cores': {'innov': innov_raw_z}}),
    ('gain: K = P H^T / R (prior variance missing from S)', 'kalman_gain',
     {'cores': {'gain': gain_no_p_in_s}}),
    ('gain: K = P H^T / (H P H^T) (R missing from S)', 'kalman_gain', {'cores': {'gain': gain_no_r}}),
    ('gain: entries normalised to sum 1', 'kalman_gain', {'cores': {'gain': gain_normalised}}),
    ('gain: first entry repeated for every state', 'kalman_gain', {'cores': {'gain': gain_first_only}}),
    ('update: covariance never reduced', 'update', {'cores': {'update': upd_no_cov}}),
    ('update: P - K H instead of (I - KH) P', 'update', {'cores': {'update': upd_p_minus_kh}}),
    ('update: Joseph form without the K R K^T term', 'update', {'cores': {'update': upd_joseph_no_r}}),
    ('update: x + K z (predicted measurement not subtracted)', 'update',
     {'cores': {'update': upd_no_hx}}),
    ('update: x - K y', 'update', {'cores': {'update': upd_minus}}),
    ('update: Joseph K R K^T term without R', 'update',
     {'cores': {'update': upd_joseph_k_unscaled}}),
    ('update: P (I - KH), multiplied on the wrong side', 'update',
     {'cores': {'update': upd_right_multiply}}),
    ('update: only the first state component corrected', 'update',
     {'cores': {'update': upd_first_component}}),
    ('update: half-size gain applied to the mean', 'update', {'cores': {'update': upd_prior_gain}}),
    ('fuse_sequential: P not carried between sensors (stale prior)', 'fuse_sequential',
     {'cores': {'fuse_seq': fuse_seq_stale_p}}),
    ('fuse_sequential: mean not carried between sensors', 'fuse_sequential',
     {'cores': {'fuse_seq': fuse_seq_stale_x}}),
    ('fuse_sequential: only the first sensor used', 'fuse_sequential',
     {'cores': {'fuse_seq': fuse_seq_first_only}}),
    ('fuse_sequential: only the last sensor used', 'fuse_sequential',
     {'cores': {'fuse_seq': fuse_seq_last_only}}),
    ('fuse_information: prior mean term forgotten', 'fuse_information',
     {'cores': {'fuse_info': fuse_info_no_prior_mean}}),
    ('fuse_information: R added where 1/R belongs', 'fuse_information',
     {'cores': {'fuse_info': fuse_info_adds_r}}),
    ('fuse_information: information matrix returned as covariance', 'fuse_information',
     {'cores': {'fuse_info': fuse_info_returns_y}}),
    ('fuse_information: mean = Y y instead of Y^-1 y', 'fuse_information',
     {'cores': {'fuse_info': fuse_info_y_times}}),
    ('fuse_sequential: sensors averaged with equal weights', 'fuse_sequential',
     {'cores': {'fuse_seq': fuse_seq_equal_weights}}),
    ('nis: y/S (not squared)', 'nis', {'cores': {'nis': nis_linear}}),
    ('nis: y^2 S (multiplied)', 'nis', {'cores': {'nis': nis_times}}),
    ('nis: |y|/sqrt(S), not squared', 'nis', {'cores': {'nis': nis_not_squared}}),
    ('nis: y^2/sqrt(S)', 'nis', {'cores': {'nis': nis_sqrt_s}}),
    ('cv_model: Q entries mirrored', 'cv_model', {'cores': {'cv': cv_swapped}}),
    ('cv_model: dt^3/2 instead of dt^3/3', 'cv_model', {'cores': {'cv': cv_const_half}}),
    ('cv_model: F transposed', 'cv_model', {'cores': {'cv': cv_f_transposed}}),
    ('cv_model: diagonal Q = q dt', 'cv_model', {'cores': {'cv': cv_diag_q}}),
    ('cv_model: Q not scaled by q', 'cv_model', {'cores': {'cv': cv_no_q_scale}}),
    ('run_filter: dropout treated as a zero measurement', 'run_filter',
     {'cores': {'run': run_dropout_updates}}),
    ('run_filter: dropout skips the prediction', 'run_filter',
     {'cores': {'run': run_dropout_no_predict}}),
    ('run_filter: NIS taken from the posterior', 'run_filter', {'cores': {'run': run_nis_after}}),
    ('run_filter: NIS with S missing R', 'run_filter', {'cores': {'run': run_nis_no_r}}),
    ('run_filter: first step not predicted', 'run_filter',
     {'cores': {'run': run_skip_first_predict}}),
    ('run_filter: dropout reports nis 0.0', 'run_filter', {'cores': {'run': run_zero_nis}}),
    ('run_filter: reports the state before the update', 'run_filter',
     {'cores': {'run': run_prior_state}}),
    ('is_valid_covariance: diagonal non-negative only', 'is_valid_covariance',
     {'cores': {'cov': cov_diag_only}}),
    ('is_valid_covariance: symmetry only', 'is_valid_covariance', {'cores': {'cov': cov_sym_only}}),
    ('is_valid_covariance: strictly positive definite required', 'is_valid_covariance',
     {'cores': {'cov': cov_strict}}),
    ('is_valid_covariance: determinant sign only', 'is_valid_covariance',
     {'cores': {'cov': cov_det_only}}),
    ('is_valid_covariance: symmetry tolerance 1e-3', 'is_valid_covariance',
     {'cores': {'cov': cov_loose_sym}}),
    ('is_valid_covariance: eigenvalue tolerance 1e-4', 'is_valid_covariance',
     {'cores': {'cov': cov_loose_eig}}),
    ('is_valid_covariance: returns int instead of bool', 'is_valid_covariance',
     {'cores': {'cov': cov_int}}),
    # validation and contract bugs
    ('NaN in x accepted by predict', 'predict', {'raw': {'predict': accepts_when(
        lambda x, P, F, Q: isinstance(x, list) and any(nonfinite(v) for v in x),
        F_['predict'], ([0.0], [[0.0]]))}}),
    ('asymmetric P accepted by update', 'update', {'raw': {'update': accepts_when(
        lambda x, P, H, R, z: isinstance(P, list) and len(P) == 2 and P[0][1] != P[1][0]
        and abs(P[0][1] - P[1][0]) > 0.05, F_['update'], ([0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]]))}}),
    ('R = 0 accepted by update', 'update', {'raw': {'update': accepts_when(
        lambda x, P, H, R, z: R == 0 and type(R) is float, F_['update'],
        ([0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]]))}}),
    ('bool R accepted by kalman_gain', 'kalman_gain', {'raw': {'kalman_gain': accepts_when(
        lambda P, H, R: R is True, F_['kalman_gain'], [0.5, 0.5])}}),
    ('empty sensors accepted by fuse_sequential', 'fuse_sequential',
     {'raw': {'fuse_sequential': accepts_when(
         lambda x, P, s: isinstance(s, list) and len(s) == 0, F_['fuse_sequential'],
         ([0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]]))}}),
    ('singular P0 accepted by fuse_information', 'fuse_information',
     {'raw': {'fuse_information': accepts_when(
         lambda x, P, s: isinstance(P, list) and len(P) == 2 and P[1][1] == 0.0,
         F_['fuse_information'], ([0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]]))}}),
    ('21 measurement slots accepted by run_filter', 'run_filter',
     {'raw': {'run_filter': accepts_when(
         lambda x, P, F, Q, H, R, zs: isinstance(zs, list) and len(zs) > 20,
         F_['run_filter'], [])}}),
    ('NaN measurement accepted by run_filter', 'run_filter',
     {'raw': {'run_filter': accepts_when(
         lambda x, P, F, Q, H, R, zs: isinstance(zs, list) and any(nonfinite(v) for v in zs),
         F_['run_filter'], [])}}),
    ('S = 0 raises ZeroDivisionError in nis, not ValueError', 'nis',
     {'raw': {'nis': lambda y, S: zdiv_nis(y, S) if (type(S) is float and S == 0)
              else F_['nis'](y, S)}}),
    ('dt = 0 accepted by cv_model', 'cv_model', {'raw': {'cv_model': accepts_when(
        lambda dt, q: dt == 0 and type(dt) is float, F_['cv_model'],
        ([[1.0, 0.0], [0.0, 1.0]], [[0.0, 0.0], [0.0, 0.0]]))}}),
    ('mixed state sizes accepted by predict', 'predict', {'raw': {'predict': accepts_when(
        lambda x, P, F, Q: isinstance(x, list) and isinstance(P, list) and len(x) != len(P)
        and len(x) == 1, F_['predict'], ([0.0], [[0.0]]))}}),
    ('H given as a column accepted by innovation', 'innovation',
     {'raw': {'innovation': accepts_when(
         lambda x, P, H, R, z: isinstance(H, list) and len(H) == 2, F_['innovation'], (0.0, 1.0))}}),
    ('predict mutates the input covariance and state', 'predict', {'raw': {
        'predict': raw_predict_mutating}}),
    ('update mutates the input state', 'update', {'raw': {'update': raw_update_mutating}}),
    ('rejects int inputs in kalman_gain', 'kalman_gain', {'raw': {
        'kalman_gain': floats_only(F_['kalman_gain'])}}),
    ('rejects tuple inputs in update', 'update', {'raw': {'update': lambda *a: F_['update'](*a)
                                                          if isinstance(a[0], list)
                                                          else (_ for _ in ()).throw(ValueError())}}),
    ('rejects an int measurement in run_filter', 'run_filter', {'raw': {
        'run_filter': lambda x, P, F, Q, H, R, zs: F_['run_filter'](x, P, F, Q, H, R, zs)
        if not any(type(z) is int for z in zs) else (_ for _ in ()).throw(ValueError())}}),
    ('update raises NotImplementedError only for velocity measurements', 'update',
     {'cores': {'update': partial_update}}),
]
for label, target, spec_ in mutants:
    result = run_with(spec_.get('cores'), spec_.get('raw'))
    require(result, 'false accept: ' + label)
    require(any(target in line for line in result),
            'rejected for the wrong function (' + label + '): ' + str(result[:3]))
run_with()
print('Kalman kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

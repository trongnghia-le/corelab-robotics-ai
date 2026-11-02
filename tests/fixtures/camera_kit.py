"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (homogeneous matrices, inverse K,
column form, hypot/fsum, raw-sum Cramer, Gaussian elimination, Gram-Schmidt QR,
exact rational arithmetic) that must pass, and named injected bugs that must be
rejected for the function they target. Plain checks only (python -O safe).
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
        raise SystemExit('camera_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L16-camera.v1.py'
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
names = ('world_to_camera', 'project', 'deproject', 'pixel_to_world', 'reprojection_rms',
         'fit_intrinsics', 'split_eval')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _fit_ref') > spoiler and text.index('_FIT_CASES = ') > spoiler,
        'oracle and case tables must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('camera_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter = kit.self_check()
require(starter, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 7 and all('not implemented yet' in f for f in starter),
        'starter must collapse each unimplemented function into one line: ' + str(starter))


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
    [entry('camera.world-to-camera@1', ('R', 't', 'p'), c[0]) for c in kit._WTC_CASES]
    + [entry('camera.project@1', ('K', 'p'), c[0]) for c in kit._PROJ_CASES]
    + [entry('camera.deproject@1', ('K', 'u', 'v', 'depth'), c[0]) for c in kit._DEPROJ_CASES]
    + [entry('camera.pixel-to-world@1', ('K', 'R', 't', 'u', 'v', 'depth'), c[0])
       for c in kit._P2W_CASES]
    + [entry('camera.reprojection-rms@1', ('K', 'points', 'pixels'), c[0]) for c in kit._RMS_CASES]
    + [entry('camera.fit-intrinsics@1', ('points', 'pixels'), c[:2]) for c in kit._FIT_CASES]
    + [entry('camera.split-eval@1', ('points', 'pixels', 'n_train'), c[:3])
       for c in kit._SPLIT_CASES])
samples = json.loads((root / 'content/labs/L16-camera.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L16-camera'], 'samples must hold only L16-camera')
require(samples['kits']['L16-camera'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50: ' + str(len(expected_samples)))


# ---- independent exact-rational oracle for the hand tables and fits ----
def frac_line(xs, ys):
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x*x for x in xs)
    sxy = sum(x*y for x, y in zip(xs, ys))
    den = n*sxx - sx*sx
    return (n*sxy - sx*sy)/den, (sxx*sy - sx*sxy)/den


def frac_fit(pts, pix):
    F_ = Fraction
    xs = [F_(p[0])/F_(p[2]) for p in pts]
    ys = [F_(p[1])/F_(p[2]) for p in pts]
    fx, cx = frac_line(xs, [F_(m[0]) for m in pix])
    fy, cy = frac_line(ys, [F_(m[1]) for m in pix])
    return (fx, fy, cx, cy)


for pts, pix, want in kit._FIT_CASES:
    exact = frac_fit(pts, pix)
    got = kit._fit_ref(pts, pix)
    require(all(abs(float(e) - g) <= 1e-9*max(1.0, abs(g)) for e, g in zip(exact, got)),
            'float fit reference disagrees with exact rational normal equations')
    if want is not None:
        require(all(abs(float(e) - w) <= 1e-12 for e, w in zip(exact, want)), 'hand fit table')
for pts, pix, n, want in kit._SPLIT_CASES:
    if want is not None:
        exact = frac_fit(pts[:n], pix[:n])
        require(all(abs(float(e) - w) <= 1e-12 for e, w in zip(exact, want[0])), 'hand split K')
        for (a, b, rms) in ((0, n, want[1]), (n, len(pts), want[2])):
            total = Fraction(0)
            for p, m in zip(pts[a:b], pix[a:b]):
                u = exact[2] + exact[0]*Fraction(p[0])/Fraction(p[2])
                v = exact[3] + exact[1]*Fraction(p[1])/Fraction(p[2])
                total += (u - Fraction(m[0]))**2 + (v - Fraction(m[1]))**2
            require(abs(math.sqrt(float(total/(b - a))) - rms) <= 1e-9, 'hand split rms')
# rotation tables are proper rotations
for R in (kit._I3, kit._RZ90, kit._DOWN, kit._RGEN):
    for i in range(3):
        for j in range(3):
            dot = sum(R[i][k]*R[j][k] for k in range(3))
            require(abs(dot - (1 if i == j else 0)) <= 1e-12, 'table rotation orthonormal')
    det = (R[0][0]*(R[1][1]*R[2][2] - R[1][2]*R[2][1]) - R[0][1]*(R[1][0]*R[2][2] - R[1][2]*R[2][0])
           + R[0][2]*(R[1][0]*R[2][1] - R[1][1]*R[2][0]))
    require(abs(det - 1) <= 1e-12, 'table rotation det +1')
# deproject/pixel_to_world hand tables round-trip through project/extrinsics
for args, want in kit._DEPROJ_CASES:
    if want is not None:
        back = kit._project_ref(args[0], want)
        require(abs(back[0] - args[1]) <= 1e-9 and abs(back[1] - args[2]) <= 1e-9, 'hand deproject')
for args, want in kit._P2W_CASES:
    if want is not None:
        cam = kit._wtc_ref(args[1], args[2], want)
        back = kit._project_ref(args[0], cam)
        require(abs(back[0] - args[3]) <= 1e-9 and abs(back[1] - args[4]) <= 1e-9
                and abs(cam[2] - args[5]) <= 1e-9, 'hand pixel_to_world')


# ---- author reference implementation (validation + replaceable cores) ----
def isreal(v):
    return type(v) in (int, float) and math.isfinite(v)


def seq(v, n):
    if not isinstance(v, (list, tuple)) or len(v) != n:
        raise ValueError


def bounded(v, low, high):
    if not isreal(v) or not low <= v <= high:
        raise ValueError
    return float(v)


def vK(K):
    seq(K, 4)
    return [bounded(K[0], 1, 1e4), bounded(K[1], 1, 1e4), bounded(K[2], -1e4, 1e4),
            bounded(K[3], -1e4, 1e4)]


def vvec(v, limit=1e4):
    seq(v, 3)
    return [bounded(x, -limit, limit) for x in v]


def vcam(p):
    seq(p, 3)
    return [bounded(p[0], -1e4, 1e4), bounded(p[1], -1e4, 1e4), bounded(p[2], 1e-3, 1e4)]


def vR(R, tol=1e-9):
    seq(R, 3)
    M = []
    for row in R:
        seq(row, 3)
        M.append([bounded(x, -2, 2) for x in row])
    for i in range(3):
        for j in range(3):
            if abs(sum(M[i][k]*M[j][k] for k in range(3)) - (1.0 if i == j else 0.0)) > tol:
                raise ValueError
    det = (M[0][0]*(M[1][1]*M[2][2] - M[1][2]*M[2][1]) - M[0][1]*(M[1][0]*M[2][2] - M[1][2]*M[2][0])
           + M[0][2]*(M[1][0]*M[2][1] - M[1][1]*M[2][0]))
    if abs(det - 1.0) > tol:
        raise ValueError
    return M


def vpix(v):
    return bounded(v, -1e6, 1e6)


def vdepth(d):
    return bounded(d, 1e-3, 1e4)


def vpairs(points, pixels, minimum):
    if not isinstance(points, (list, tuple)) or not isinstance(pixels, (list, tuple)):
        raise ValueError
    if len(points) != len(pixels) or not minimum <= len(points) <= 200:
        raise ValueError
    pts = [vcam(p) for p in points]
    pix = []
    for m in pixels:
        seq(m, 2)
        pix.append([vpix(m[0]), vpix(m[1])])
    return pts, pix


def vspread(pts):
    for axis in (0, 1):
        xs = [p[axis]/p[2] for p in pts]
        if max(xs) - min(xs) < 1e-6:
            raise ValueError


def wtc_core(R, t, p):
    return tuple(sum(R[i][j]*p[j] for j in range(3)) + t[i] for i in range(3))


def proj_core(K, p):
    return (K[0]*p[0]/p[2] + K[2], K[1]*p[1]/p[2] + K[3])


def depr_core(K, u, v, d):
    return ((u - K[2])/K[0]*d, (v - K[3])/K[1]*d, d)


def p2w_core(K, R, t, u, v, d):
    c = depr_core(K, u, v, d)
    q = [c[i] - t[i] for i in range(3)]
    return tuple(R[0][i]*q[0] + R[1][i]*q[1] + R[2][i]*q[2] for i in range(3))


def rms_core(K, pts, pix):
    total = 0.0
    for p, m in zip(pts, pix):
        u, v = proj_core(K, p)
        total += (u - m[0])**2 + (v - m[1])**2
    return math.sqrt(total/len(pts))


def line_core(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    slope = sum((x - mx)*(y - my) for x, y in zip(xs, ys))/sum((x - mx)**2 for x in xs)
    return slope, my - slope*mx


def fit_core(pts, pix):
    fx, cx = line_core([p[0]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = line_core([p[1]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


current = {}


def split_core(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    return (tuple(K), current['rms'](K, pts[:n], pix[:n]), current['rms'](K, pts[n:], pix[n:]))


BASE = {'wtc': wtc_core, 'proj': proj_core, 'depr': depr_core, 'p2w': p2w_core,
        'rms': rms_core, 'fit': fit_core, 'split': split_core}


def validated(cores):
    def world_to_camera(R, t, p):
        R, t, p = vR(R), vvec(t), vvec(p)
        return tuple(cores['wtc'](R, t, p))

    def project(K, p_cam):
        K, p = vK(K), vcam(p_cam)
        return tuple(cores['proj'](K, p))

    def deproject(K, u, v, depth):
        K = vK(K)
        return tuple(cores['depr'](K, vpix(u), vpix(v), vdepth(depth)))

    def pixel_to_world(K, R, t, u, v, depth):
        K, R, t = vK(K), vR(R), vvec(t)
        return tuple(cores['p2w'](K, R, t, vpix(u), vpix(v), vdepth(depth)))

    def reprojection_rms(K, points, pixels):
        K = vK(K)
        pts, pix = vpairs(points, pixels, 1)
        return cores['rms'](K, pts, pix)

    def fit_intrinsics(points, pixels):
        pts, pix = vpairs(points, pixels, 2)
        vspread(pts)
        return tuple(cores['fit'](pts, pix))

    def split_eval(points, pixels, n_train):
        pts, pix = vpairs(points, pixels, 3)
        if type(n_train) is not int or not 2 <= n_train <= len(pts) - 1:
            raise ValueError
        vspread(pts[:n_train])
        return cores['split'](pts, pix, n_train)
    return {'world_to_camera': world_to_camera, 'project': project, 'deproject': deproject,
            'pixel_to_world': pixel_to_world, 'reprojection_rms': reprojection_rms,
            'fit_intrinsics': fit_intrinsics, 'split_eval': split_eval}


def run_with(cores=None, raw=None):
    merged = dict(BASE)
    merged.update(cores or {})
    current['fit'] = merged['fit']
    current['rms'] = merged['rms']
    functions = validated(merged)
    functions.update(raw or {})
    for name, fn in functions.items():
        setattr(kit, name, fn)
    return kit.self_check()


require(run_with() == [], 'author reference must pass: ' + str(run_with()))
REF = validated(BASE)


# ---- valid alternatives ----
def hom(R, t):
    return [list(R[0]) + [t[0]], list(R[1]) + [t[1]], list(R[2]) + [t[2]], [0.0, 0.0, 0.0, 1.0]]


def wtc_homogeneous(R, t, p):
    T, v = hom(R, t), list(p) + [1.0]
    return tuple(sum(T[i][j]*v[j] for j in range(4)) for i in range(3))


def wtc_columns(R, t, p):
    return tuple(p[0]*R[i][0] + p[1]*R[i][1] + p[2]*R[i][2] + t[i] for i in range(3))


def proj_matrix(K, p):
    row = [[K[0], 0.0, K[2]], [0.0, K[1], K[3]], [0.0, 0.0, 1.0]]
    h = [sum(row[i][j]*p[j] for j in range(3)) for i in range(3)]
    return (h[0]/h[2], h[1]/h[2])


def depr_inverse_k(K, u, v, d):
    inv = [[1/K[0], 0.0, -K[2]/K[0]], [0.0, 1/K[1], -K[3]/K[1]], [0.0, 0.0, 1.0]]
    r = [sum(inv[i][j]*(u, v, 1.0)[j] for j in range(3)) for i in range(3)]
    return (r[0]*d, r[1]*d, r[2]*d)


def p2w_homogeneous(K, R, t, u, v, d):
    c = list(depr_inverse_k(K, u, v, d)) + [1.0]
    Rt = [[R[j][i] for j in range(3)] for i in range(3)]
    shift = [-sum(Rt[i][j]*t[j] for j in range(3)) for i in range(3)]
    inv = [Rt[i] + [shift[i]] for i in range(3)]
    return tuple(sum(inv[i][j]*c[j] for j in range(4)) for i in range(3))


def rms_hypot(K, pts, pix):
    errors = [math.hypot(proj_core(K, p)[0] - m[0], proj_core(K, p)[1] - m[1])
              for p, m in zip(pts, pix)]
    return math.sqrt(math.fsum(e*e for e in errors)/len(errors))


def rms_axes(K, pts, pix):
    du = [proj_core(K, p)[0] - m[0] for p, m in zip(pts, pix)]
    dv = [proj_core(K, p)[1] - m[1] for p, m in zip(pts, pix)]
    return math.sqrt((sum(a*a for a in du) + sum(b*b for b in dv))/len(du))


def line_cramer(xs, ys):
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x*x for x in xs)
    sxy = sum(x*y for x, y in zip(xs, ys))
    den = n*sxx - sx*sx
    return (n*sxy - sx*sy)/den, (sxx*sy - sx*sxy)/den


def fit_cramer(pts, pix):
    fx, cx = line_cramer([p[0]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = line_cramer([p[1]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def line_gauss(xs, ys):
    n = len(xs)
    a, b, c = sum(x*x for x in xs), sum(xs), float(n)
    r1, r2 = sum(x*y for x, y in zip(xs, ys)), sum(ys)
    factor = b/a
    c2, r2b = c - factor*b, r2 - factor*r1
    intercept = r2b/c2
    return (r1 - b*intercept)/a, intercept


def fit_gauss(pts, pix):
    fx, cx = line_gauss([p[0]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = line_gauss([p[1]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def line_qr(xs, ys):
    ones = [1.0]*len(xs)
    q1 = math.sqrt(sum(x*x for x in xs))
    e1 = [x/q1 for x in xs]
    proj = sum(a*b for a, b in zip(ones, e1))
    w = [o - proj*e for o, e in zip(ones, e1)]
    q2 = math.sqrt(sum(x*x for x in w))
    e2 = [x/q2 for x in w]
    y1 = sum(a*b for a, b in zip(e1, ys))
    y2 = sum(a*b for a, b in zip(e2, ys))
    # R = [[q1, proj], [0, q2]] solves R [f, c]^T = Q^T y
    c = y2/q2
    f = (y1 - proj*c)/q1
    return f, c


def fit_qr(pts, pix):
    fx, cx = line_qr([p[0]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = line_qr([p[1]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def fit_exact(pts, pix):
    return tuple(float(v) for v in frac_fit(pts, pix))


def split_halves(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    train = current['rms'](K, pts[:n], pix[:n])
    test = current['rms'](K, pts[n:], pix[n:])
    return (tuple(K), train, test)


alternatives = [
    ('homogeneous 4x4 extrinsics and inverse', {'wtc': wtc_homogeneous, 'p2w': p2w_homogeneous}),
    ('column form of R*p', {'wtc': wtc_columns}),
    ('projection through the 3x3 K matrix', {'proj': proj_matrix}),
    ('deprojection through the inverse K matrix', {'depr': depr_inverse_k}),
    ('hypot and fsum RMS', {'rms': rms_hypot}),
    ('RMS as separate u and v sums', {'rms': rms_axes}),
    ('raw-sum Cramer rule fit', {'fit': fit_cramer}),
    ('Gaussian elimination on the normal equations', {'fit': fit_gauss}),
    ('Gram-Schmidt QR fit', {'fit': fit_qr}),
    ('exact rational arithmetic fit', {'fit': fit_exact}),
    ('split with explicit train and test slices', {'split': split_halves}),
]
for label, cores in alternatives:
    result = run_with(cores)
    require(result == [], 'valid alternative rejected (' + label + '): ' + str(result[:3]))
run_with()


# ---- injected bugs ----
def tr(R):
    return [[R[j][i] for j in range(3)] for i in range(3)]


def mv(M, v):
    return [sum(M[i][j]*v[j] for j in range(3)) for i in range(3)]


def wtc_transposed(R, t, p):
    return tuple(a + b for a, b in zip(mv(tr(R), p), t))


def wtc_camera_position(R, t, p):
    return tuple(mv(R, [p[i] - t[i] for i in range(3)]))


def wtc_translate_first(R, t, p):
    return tuple(mv(R, [p[i] + t[i] for i in range(3)]))


def wtc_minus_t(R, t, p):
    return tuple(a - b for a, b in zip(mv(R, p), t))


def wtc_no_t(R, t, p):
    return tuple(mv(R, p))


def proj_no_center(K, p):
    return (K[0]*p[0]/p[2], K[1]*p[1]/p[2])


def proj_swapped_f(K, p):
    return (K[1]*p[0]/p[2] + K[2], K[0]*p[1]/p[2] + K[3])


def proj_v_up(K, p):
    return (K[0]*p[0]/p[2] + K[2], K[3] - K[1]*p[1]/p[2])


def proj_single_f(K, p):
    return (K[0]*p[0]/p[2] + K[2], K[0]*p[1]/p[2] + K[3])


def proj_times_z(K, p):
    return (K[0]*p[0]*p[2] + K[2], K[1]*p[1]*p[2] + K[3])


def proj_swapped_c(K, p):
    return (K[0]*p[0]/p[2] + K[3], K[1]*p[1]/p[2] + K[2])


def depr_no_depth(K, u, v, d):
    return ((u - K[2])/K[0], (v - K[3])/K[1], d)


def depr_no_center(K, u, v, d):
    return (u/K[0]*d, v/K[1]*d, d)


def depr_swapped_f(K, u, v, d):
    return ((u - K[2])/K[1]*d, (v - K[3])/K[0]*d, d)


def depr_single_f(K, u, v, d):
    return ((u - K[2])/K[0]*d, (v - K[3])/K[0]*d, d)


def depr_range(K, u, v, d):
    x, y = (u - K[2])/K[0], (v - K[3])/K[1]
    n = math.sqrt(x*x + y*y + 1)
    return (x*d/n, y*d/n, d/n)


def depr_divide_depth(K, u, v, d):
    return ((u - K[2])/K[0]/d, (v - K[3])/K[1]/d, d)


def p2w_forward(K, R, t, u, v, d):
    c = depr_core(K, u, v, d)
    return tuple(a + b for a, b in zip(mv(R, [c[i] - t[i] for i in range(3)]), [0, 0, 0]))


def p2w_no_t(K, R, t, u, v, d):
    return tuple(mv(tr(R), list(depr_core(K, u, v, d))))


def p2w_subtract_after(K, R, t, u, v, d):
    r = mv(tr(R), list(depr_core(K, u, v, d)))
    return tuple(r[i] - t[i] for i in range(3))


def p2w_add_t(K, R, t, u, v, d):
    c = depr_core(K, u, v, d)
    return tuple(mv(tr(R), [c[i] + t[i] for i in range(3)]))


def errors(K, pts, pix):
    return [(proj_core(K, p)[0] - m[0], proj_core(K, p)[1] - m[1]) for p, m in zip(pts, pix)]


def rms_sum(K, pts, pix):
    return math.sqrt(sum(a*a + b*b for a, b in errors(K, pts, pix)))


def rms_mean_dist(K, pts, pix):
    e = errors(K, pts, pix)
    return sum(math.hypot(a, b) for a, b in e)/len(e)


def rms_mse(K, pts, pix):
    e = errors(K, pts, pix)
    return sum(a*a + b*b for a, b in e)/len(e)


def rms_n_minus_1(K, pts, pix):
    e = errors(K, pts, pix)
    return math.sqrt(sum(a*a + b*b for a, b in e)/max(1, len(e) - 1))


def rms_u_only(K, pts, pix):
    e = errors(K, pts, pix)
    return math.sqrt(sum(a*a for a, b in e)/len(e))


def rms_max(K, pts, pix):
    return max(math.hypot(a, b) for a, b in errors(K, pts, pix))


def rms_l1(K, pts, pix):
    e = errors(K, pts, pix)
    return sum(abs(a) + abs(b) for a, b in e)/len(e)


def rms_per_axis(K, pts, pix):
    e = errors(K, pts, pix)
    return math.sqrt(sum(a*a + b*b for a, b in e)/(2*len(e)))


def fit_no_intercept(pts, pix):
    xs = [p[0]/p[2] for p in pts]
    ys = [p[1]/p[2] for p in pts]
    return (sum(x*m[0] for x, m in zip(xs, pix))/sum(x*x for x in xs),
            sum(y*m[1] for y, m in zip(ys, pix))/sum(y*y for y in ys), 0.0, 0.0)


def fit_order(pts, pix):
    fx, fy, cx, cy = fit_core(pts, pix)
    return (fx, fy, cy, cx)


def fit_axes_swapped(pts, pix):
    fx, cx = line_core([p[1]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = line_core([p[0]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def fit_no_depth(pts, pix):
    fx, cx = line_core([p[0] for p in pts], [m[0] for m in pix])
    fy, cy = line_core([p[1] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def fit_endpoints(pts, pix):
    a, b = pts[0], pts[-1]
    fx = (pix[-1][0] - pix[0][0])/(b[0]/b[2] - a[0]/a[2])
    fy = (pix[-1][1] - pix[0][1])/(b[1]/b[2] - a[1]/a[2])
    return (fx, fy, pix[0][0] - fx*a[0]/a[2], pix[0][1] - fy*a[1]/a[2])


def fit_inverse_regression(pts, pix):
    xs = [p[0]/p[2] for p in pts]
    ys = [p[1]/p[2] for p in pts]
    sx, cx0 = line_core([m[0] for m in pix], xs)
    sy, cy0 = line_core([m[1] for m in pix], ys)
    fx, fy = 1/sx, 1/sy
    return (fx, fy, -cx0*fx, -cy0*fy)


def fit_single_f(pts, pix):
    fx, fy, cx, cy = fit_core(pts, pix)
    f = (fx + fy)/2
    mx = sum(p[0]/p[2] for p in pts)/len(pts)
    my = sum(p[1]/p[2] for p in pts)/len(pts)
    return (f, f, sum(m[0] for m in pix)/len(pix) - f*mx, sum(m[1] for m in pix)/len(pix) - f*my)


def fit_fixed_center(pts, pix):
    xs = [p[0]/p[2] for p in pts]
    ys = [p[1]/p[2] for p in pts]
    return (sum(x*(m[0] - 320) for x, m in zip(xs, pix))/sum(x*x for x in xs),
            sum(y*(m[1] - 240) for y, m in zip(ys, pix))/sum(y*y for y in ys), 320.0, 240.0)


def fit_mean_ratio(pts, pix):
    xs = [p[0]/p[2] for p in pts]
    ys = [p[1]/p[2] for p in pts]
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    mu, mv_ = sum(m[0] for m in pix)/len(pix), sum(m[1] for m in pix)/len(pix)
    fx, fy = mu/mx if mx else 1.0, mv_/my if my else 1.0
    return (fx, fy, 0.0, 0.0)


def fit_midpoint(pts, pix):
    """Slope by the fitted line but intercept from the first point only."""
    fx, fy, cx, cy = fit_core(pts, pix)
    return (fx, fy, pix[0][0] - fx*pts[0][0]/pts[0][2], pix[0][1] - fy*pts[0][1]/pts[0][2])


def split_leak(pts, pix, n):
    K = current['fit'](pts, pix)
    return (tuple(K), current['rms'](K, pts[:n], pix[:n]), current['rms'](K, pts[n:], pix[n:]))


def split_test_on_train(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    r = current['rms'](K, pts[:n], pix[:n])
    return (tuple(K), r, r)


def split_swapped(pts, pix, n):
    K, a, b = split_core(pts, pix, n)
    return (K, b, a)


def split_test_all(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    return (tuple(K), current['rms'](K, pts[:n], pix[:n]), current['rms'](K, pts, pix))


def split_off_by_one(pts, pix, n):
    K = current['fit'](pts[:n - 1], pix[:n - 1]) if n > 2 else current['fit'](pts[:n], pix[:n])
    return (tuple(K), current['rms'](K, pts[:n], pix[:n]), current['rms'](K, pts[n:], pix[n:]))


def split_from_end(pts, pix, n):
    K = current['fit'](pts[-n:], pix[-n:])
    return (tuple(K), current['rms'](K, pts[-n:], pix[-n:]), current['rms'](K, pts[:-n], pix[:-n]))


def split_train_all(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    return (tuple(K), current['rms'](K, pts, pix), current['rms'](K, pts[n:], pix[n:]))


def split_test_first_only(pts, pix, n):
    K = current['fit'](pts[:n], pix[:n])
    return (tuple(K), current['rms'](K, pts[:n], pix[:n]), current['rms'](K, pts[n:n + 1], pix[n:n + 1]))


# raw (validation / contract) bugs: replace the public function wholesale
def lenient_project(K, p):
    """No depth check beyond division by zero (negative depth gives a mirrored pixel)."""
    K = vK(K)
    seq(p, 3)
    return tuple(proj_core(K, [bounded(p[0], -1e4, 1e4), bounded(p[1], -1e4, 1e4), bounded(p[2], -1e4, 1e4)]))


def project_abs_depth(K, p):
    K = vK(K)
    seq(p, 3)
    z = bounded(p[2], -1e4, 1e4)
    if abs(z) < 1e-3:
        raise ValueError
    return tuple(proj_core(K, [bounded(p[0], -1e4, 1e4), bounded(p[1], -1e4, 1e4), abs(z)]))


def project_zero_only(K, p):
    K = vK(K)
    seq(p, 3)
    z = bounded(p[2], -1e4, 1e4)
    if z < 0:
        raise ValueError
    return tuple(proj_core(K, [bounded(p[0], -1e4, 1e4), bounded(p[1], -1e4, 1e4), z]))


def project_positive_only(K, p):
    K = vK(K)
    seq(p, 3)
    z = bounded(p[2], -1e4, 1e4)
    if z <= 0:
        raise ValueError
    return tuple(proj_core(K, [bounded(p[0], -1e4, 1e4), bounded(p[1], -1e4, 1e4), z]))


def deproject_negative_depth(K, u, v, depth):
    K = vK(K)
    return tuple(depr_core(K, vpix(u), vpix(v), bounded(depth, -1e4, 1e4)))


def deproject_zero_depth_ok(K, u, v, depth):
    K = vK(K)
    return tuple(depr_core(K, vpix(u), vpix(v), bounded(depth, 0, 1e4)))


def wtc_reflection_ok(R, t, p):
    seq(R, 3)
    for row in R:
        seq(row, 3)
    return tuple(wtc_core([[bounded(x, -2, 2) for x in row] for row in R], vvec(t), vvec(p)))


def wtc_rejects_behind(R, t, p):
    out = REF['world_to_camera'](R, t, p)
    if out[2] <= 0:
        raise ValueError
    return out


def wtc_bool_ok(R, t, p):
    if isinstance(t, (list, tuple)) and any(type(x) is bool for x in t):
        t = [float(x) for x in t]
    return REF['world_to_camera'](R, t, p)


def wtc_nan_ok(R, t, p):
    if isinstance(p, (list, tuple)) and len(p) == 3 and any(type(x) is float and x != x for x in p):
        return (0.0, 0.0, 0.0)
    return REF['world_to_camera'](R, t, p)


def wtc_mutates_t(R, t, p):
    out = REF['world_to_camera'](R, t, p)
    if isinstance(t, list):
        t[0] = t[0] + 0.0
        t.reverse()
        t.reverse()
        t[2] = t[2] + 1e-3
    return out


def wtc_ints_only_fails(R, t, p):
    if any(type(x) is int for x in p):
        raise ValueError
    return REF['world_to_camera'](R, t, p)


def wtc_tuples_rejected(R, t, p):
    if isinstance(t, tuple):
        raise ValueError
    return REF['world_to_camera'](R, t, p)


def rms_truncating_zip(K, points, pixels):
    K = vK(K)
    n = min(len(points), len(pixels))
    pts, pix = vpairs(points[:n], pixels[:n], 1)
    return rms_core(K, pts, pix)


def rms_empty_zero_division(K, points, pixels):
    if isinstance(points, (list, tuple)) and len(points) == 0 and len(pixels) == 0:
        return 1 / len(points)
    return REF['reprojection_rms'](K, points, pixels)


def rms_unvalidated_depth(K, points, pixels):
    K = vK(K)
    return rms_core(K, [[p[0], p[1], p[2]] for p in points], [list(m) for m in pixels])


def rms_mutates_pixels(K, points, pixels):
    out = REF['reprojection_rms'](K, points, pixels)
    if isinstance(pixels, list) and pixels and isinstance(pixels[0], list):
        pixels[0][0] = float(pixels[0][0])
        pixels.sort()
    return out


def fit_degenerate_zero_division(pts_, pix_):
    pts, pix = vpairs(pts_, pix_, 2)
    xs = [p[0]/p[2] for p in pts]
    if max(xs) - min(xs) < 1e-6:
        return 1 / (max(xs) - min(xs))
    return REF['fit_intrinsics'](pts_, pix_)


def fit_single_point_ok(pts_, pix_):
    if isinstance(pts_, (list, tuple)) and len(pts_) == 1:
        return (500.0, 500.0, 320.0, 240.0)
    return REF['fit_intrinsics'](pts_, pix_)


def fit_loose_spread(pts_, pix_):
    pts, pix = vpairs(pts_, pix_, 2)
    for axis in (0, 1):
        xs = [p[axis]/p[2] for p in pts]
        if max(xs) - min(xs) < 1e-12:
            raise ValueError
    return tuple(fit_core(pts, pix))


def fit_x_only_spread(pts_, pix_):
    pts, pix = vpairs(pts_, pix_, 2)
    xs = [p[0]/p[2] for p in pts]
    if max(xs) - min(xs) < 1e-6:
        raise ValueError
    ys = [p[1]/p[2] for p in pts]
    if max(ys) == min(ys):
        return (line_core(xs, [m[0] for m in pix])[0], 500.0, line_core(xs, [m[0] for m in pix])[1], 240.0)
    return tuple(fit_core(pts, pix))


def fit_sorts_input(pts_, pix_):
    out = REF['fit_intrinsics'](pts_, pix_)
    if isinstance(pts_, list):
        pts_.sort()
    return out


def fit_positive_f_clamp(pts_, pix_):
    fx, fy, cx, cy = REF['fit_intrinsics'](pts_, pix_)
    return (max(fx, 1.0), max(fy, 1.0), cx, cy)


def split_all_train_ok(pts_, pix_, n):
    if type(n) is int and isinstance(pts_, (list, tuple)) and n == len(pts_):
        pts, pix = vpairs(pts_, pix_, 2)
        K = fit_core(pts, pix)
        return (tuple(K), rms_core(K, pts, pix), 0.0)
    return REF['split_eval'](pts_, pix_, n)


def split_float_n_ok(pts_, pix_, n):
    if type(n) is float and n == int(n):
        n = int(n)
    return REF['split_eval'](pts_, pix_, n)


def split_one_train_ok(pts_, pix_, n):
    if n == 1 and type(n) is int:
        return ((500.0, 500.0, 320.0, 240.0), 0.0, 0.0)
    return REF['split_eval'](pts_, pix_, n)


def split_rounds_to_int(pts_, pix_, n):
    K, a, b = REF['split_eval'](pts_, pix_, n)
    return (K, round(a), round(b))


def project_returns_list_of_ints(K, p):
    u, v = REF['project'](K, p)
    return [int(round(u)), int(round(v))]


def deproject_returns_xy_only(K, u, v, d):
    return REF['deproject'](K, u, v, d)[:2]


def wtc_with_tol(tol):
    def f(R, t, p):
        return tuple(wtc_core(vR(R, tol), vvec(t), vvec(p)))
    return f


def p2w_with_tol(tol):
    def f(K, R, t, u, v, d):
        return tuple(p2w_core(vK(K), vR(R, tol), vvec(t), vpix(u), vpix(v), vdepth(d)))
    return f


mutants = [
    ('world_to_camera: orthogonality tolerance 1e-3', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_with_tol(1e-3)}}),
    ('world_to_camera: orthogonality tolerance 1e-6', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_with_tol(1e-6)}}),
    ('world_to_camera: orthogonality tolerance 1e-12 rejects a float-rounded rotation', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_with_tol(1e-12)}}),
    ('pixel_to_world: orthogonality tolerance 1e-6', 'pixel_to_world',
     {'raw': {'pixel_to_world': p2w_with_tol(1e-6)}}),
    ('world_to_camera: R^T used where R belongs', 'world_to_camera', {'wtc': wtc_transposed}),
    ('world_to_camera: t treated as the camera position, R(p - t)', 'world_to_camera',
     {'wtc': wtc_camera_position}),
    ('world_to_camera: translation before rotation, R(p + t)', 'world_to_camera',
     {'wtc': wtc_translate_first}),
    ('world_to_camera: t subtracted instead of added', 'world_to_camera', {'wtc': wtc_minus_t}),
    ('world_to_camera: translation forgotten', 'world_to_camera', {'wtc': wtc_no_t}),
    ('project: principal point forgotten', 'project', {'proj': proj_no_center}),
    ('project: fx and fy swapped', 'project', {'proj': proj_swapped_f}),
    ('project: image v measured upward, cy - fy Y/Z', 'project', {'proj': proj_v_up}),
    ('project: fx used for both axes', 'project', {'proj': proj_single_f}),
    ('project: multiplies by depth instead of dividing', 'project', {'proj': proj_times_z}),
    ('project: cx and cy swapped', 'project', {'proj': proj_swapped_c}),
    ('project: negative depth accepted (mirrored pixel / division by zero)', 'project',
     {'raw': {'project': lenient_project}}),
    ('project: abs(Z) makes a point behind the camera look in front', 'project',
     {'raw': {'project': project_abs_depth}}),
    ('project: only Z < 0 rejected, Z = 0 divides by zero', 'project',
     {'raw': {'project': project_zero_only}}),
    ('project: only Z <= 0 rejected, Z = 0.0009 accepted', 'project',
     {'raw': {'project': project_positive_only}}),
    ('project: returns rounded integer pixels', 'project',
     {'raw': {'project': project_returns_list_of_ints}}),
    ('deproject: depth not applied', 'deproject', {'depr': depr_no_depth}),
    ('deproject: principal point not subtracted', 'deproject', {'depr': depr_no_center}),
    ('deproject: fx and fy swapped', 'deproject', {'depr': depr_swapped_f}),
    ('deproject: fx used for both axes', 'deproject', {'depr': depr_single_f}),
    ('deproject: depth treated as range along the ray', 'deproject', {'depr': depr_range}),
    ('deproject: divides by depth instead of multiplying', 'deproject', {'depr': depr_divide_depth}),
    ('deproject: negative depth accepted', 'deproject', {'raw': {'deproject': deproject_negative_depth}}),
    ('deproject: depth 0 accepted', 'deproject', {'raw': {'deproject': deproject_zero_depth_ok}}),
    ('deproject: returns only (X, Y)', 'deproject', {'raw': {'deproject': deproject_returns_xy_only}}),
    ('pixel_to_world: stops in the camera frame (R applied forward, not R^T)', 'pixel_to_world',
     {'p2w': p2w_forward}),
    ('pixel_to_world: translation not removed', 'pixel_to_world', {'p2w': p2w_no_t}),
    ('pixel_to_world: R^T p - t, subtracted after rotating', 'pixel_to_world',
     {'p2w': p2w_subtract_after}),
    ('pixel_to_world: t added instead of subtracted', 'pixel_to_world', {'p2w': p2w_add_t}),
    ('reprojection_rms: sum of squares, not the mean', 'reprojection_rms', {'rms': rms_sum}),
    ('reprojection_rms: mean distance instead of RMS', 'reprojection_rms', {'rms': rms_mean_dist}),
    ('reprojection_rms: mean squared error without the root', 'reprojection_rms', {'rms': rms_mse}),
    ('reprojection_rms: divides by n - 1', 'reprojection_rms', {'rms': rms_n_minus_1}),
    ('reprojection_rms: only the u residual', 'reprojection_rms', {'rms': rms_u_only}),
    ('reprojection_rms: maximum error', 'reprojection_rms', {'rms': rms_max}),
    ('reprojection_rms: L1 pixel error', 'reprojection_rms', {'rms': rms_l1}),
    ('reprojection_rms: divides by 2n (per-axis RMS)', 'reprojection_rms', {'rms': rms_per_axis}),
    ('fit_intrinsics: line forced through the origin, no principal point', 'fit_intrinsics',
     {'fit': fit_no_intercept}),
    ('fit_intrinsics: cx and cy returned in the wrong order', 'fit_intrinsics', {'fit': fit_order}),
    ('fit_intrinsics: u fitted on Y/Z and v on X/Z', 'fit_intrinsics', {'fit': fit_axes_swapped}),
    ('fit_intrinsics: X and Y used without dividing by depth', 'fit_intrinsics', {'fit': fit_no_depth}),
    ('fit_intrinsics: slope from the first and last point only', 'fit_intrinsics', {'fit': fit_endpoints}),
    ('fit_intrinsics: regresses x on u and inverts the slope', 'fit_intrinsics',
     {'fit': fit_inverse_regression}),
    ('fit_intrinsics: one shared focal length', 'fit_intrinsics', {'fit': fit_single_f}),
    ('fit_intrinsics: principal point fixed at (320, 240)', 'fit_intrinsics',
     {'fit': fit_fixed_center}),
    ('fit_intrinsics: mean ratio u/x with no intercept', 'fit_intrinsics', {'fit': fit_mean_ratio}),
    ('fit_intrinsics: intercept taken from the first point only', 'fit_intrinsics',
     {'fit': fit_midpoint}),
    ('fit_intrinsics: degenerate X/Z raises ZeroDivisionError', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_degenerate_zero_division}}),
    ('fit_intrinsics: a single point accepted', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_single_point_ok}}),
    ('fit_intrinsics: spread threshold 1e-12 accepts a near-degenerate fit', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_loose_spread}}),
    ('fit_intrinsics: only the X/Z spread checked, flat Y/Z accepted', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_x_only_spread}}),
    ('fit_intrinsics: sorts the caller point list in place', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_sorts_input}}),
    ('fit_intrinsics: focal lengths clamped to >= 1', 'fit_intrinsics',
     {'raw': {'fit_intrinsics': fit_positive_f_clamp}}),
    ('split_eval: fitted on ALL points (held-out leakage)', 'split_eval', {'split': split_leak}),
    ('split_eval: held-out RMS evaluated on the training points', 'split_eval',
     {'split': split_test_on_train}),
    ('split_eval: train and held-out RMS swapped', 'split_eval', {'split': split_swapped}),
    ('split_eval: held-out RMS over all points', 'split_eval', {'split': split_test_all}),
    ('split_eval: fit uses n_train - 1 points', 'split_eval', {'split': split_off_by_one}),
    ('split_eval: split taken from the end of the list', 'split_eval', {'split': split_from_end}),
    ('split_eval: training RMS over all points', 'split_eval', {'split': split_train_all}),
    ('split_eval: held-out RMS from the first test point only', 'split_eval',
     {'split': split_test_first_only}),
    ('split_eval: n_train equal to n (no held-out view) accepted', 'split_eval',
     {'raw': {'split_eval': split_all_train_ok}}),
    ('split_eval: float n_train accepted', 'split_eval', {'raw': {'split_eval': split_float_n_ok}}),
    ('split_eval: n_train = 1 accepted', 'split_eval', {'raw': {'split_eval': split_one_train_ok}}),
    ('split_eval: RMS values rounded to integers', 'split_eval',
     {'raw': {'split_eval': split_rounds_to_int}}),
    ('world_to_camera: reflection matrix accepted', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_reflection_ok}}),
    ('world_to_camera: raises for a point behind the camera', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_rejects_behind}}),
    ('world_to_camera: bool in t accepted', 'world_to_camera', {'raw': {'world_to_camera': wtc_bool_ok}}),
    ('world_to_camera: NaN point accepted', 'world_to_camera', {'raw': {'world_to_camera': wtc_nan_ok}}),
    ('world_to_camera: mutates the translation list', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_mutates_t}}),
    ('world_to_camera: rejects int coordinates', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_ints_only_fails}}),
    ('world_to_camera: rejects tuple translation', 'world_to_camera',
     {'raw': {'world_to_camera': wtc_tuples_rejected}}),
    ('reprojection_rms: zip truncates mismatched lengths', 'reprojection_rms',
     {'raw': {'reprojection_rms': rms_truncating_zip}}),
    ('reprojection_rms: empty input raises ZeroDivisionError', 'reprojection_rms',
     {'raw': {'reprojection_rms': rms_empty_zero_division}}),
    ('reprojection_rms: depth not validated', 'reprojection_rms',
     {'raw': {'reprojection_rms': rms_unvalidated_depth}}),
    ('reprojection_rms: mutates the pixel list', 'reprojection_rms',
     {'raw': {'reprojection_rms': rms_mutates_pixels}}),
]
for label, target, spec_ in mutants:
    result = run_with({k: v for k, v in spec_.items() if k != 'raw'}, spec_.get('raw'))
    require(result, 'false accept: ' + label)
    require(any(target in line for line in result),
            'rejected for the wrong function (' + label + '): ' + str(result[:3]))
run_with()
require(len(mutants) >= 30, 'at least 30 named mutants')
print('Camera kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')

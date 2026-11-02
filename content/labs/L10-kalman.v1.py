"""CoreLab Linear Kalman and fusion lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the ten core functions below, then run your edited file locally:
  Windows: py -3 L10-kalman.v1.py
  macOS/Linux: python3 L10-kalman.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared model (you choose nothing: every matrix is an argument). State x has
n = 1 or 2 components (scalar, or position + velocity). One scalar measurement:
    x_k = F x_(k-1) + w,   w ~ N(0, Q)          (prediction)
    z_k = H x_k + v,       v ~ N(0, R)          (measurement, R a variance)
with w and v independent of each other and over time. Nothing here estimates
F, Q, H or R: they are DECLARED, and every guarantee below is conditional on
them being the truth.

Representation (finite int/float, never bool; lists or tuples both accepted):
  x: length-n vector.   P, Q, F: n x n nested lists.   H: [[h1, ..., hn]], 1 x n.
  R: scalar variance, 1e-6 <= R <= 1e4.   z: scalar measurement.
  Bounds: |x_i|, |z| <= 1e4; |P_ij|, |Q_ij| <= 1e4; |F_ij|, |H_j| <= 100.
  P and Q must be covariances: symmetric and positive semi-definite, each
  within a tolerance of 1e-9*max(1, largest |entry|) (asymmetry |P01 - P10|
  and the lowest eigenvalue >= -tolerance). Everything must have the same n.
  Wrong type or shape, bool, NaN, infinity, out of bounds, mixed n, or a
  matrix that is not a covariance -> raise ValueError. Never mutate inputs.
  Returned vectors/matrices are lists/tuples of finite int/float.
  Output tolerance: 1e-9*max(1, largest magnitude in the case), absolute.

Contracts:
  predict(x, P, F, Q) -> (x_pred, P_pred)
      x_pred = F x,   P_pred = F P F^T + Q.
  innovation(x_pred, P_pred, H, R, z) -> (y, S)
      y = z - H x_pred (innovation, measurement units),
      S = H P_pred H^T + R (innovation variance, measurement units squared).
  kalman_gain(P_pred, H, R) -> K, a length-n list: K = P_pred H^T / S.
  update(x_pred, P_pred, H, R, z) -> (x_post, P_post)
      x_post = x_pred + K y. Use the standard form (I - KH)P or the Joseph form
      (I - KH) P (I - KH)^T + K R K^T, or P - K S K^T; all are accepted. Judged
      by a behaviour band: P_post must equal the reference within the output
      tolerance, be symmetric within 1e-9*max(1, largest |entry|) (symmetrise a
      standard-form result if you need to) and have lowest eigenvalue
      >= -1e-9*max(1, largest |entry|).
  fuse_sequential(x0, P0, sensors) -> (x, P)
      sensors is a list/tuple of 1 to 4 triples (H, R, z). Apply update with
      each triple in the order given, with NO prediction between them: several
      independent sensors observing the same instant. P0 must additionally be
      positive definite (lowest eigenvalue >= 1e-6) for both fuse functions.
  fuse_information(x0, P0, sensors) -> (x, P)
      The batch / information-form route to the same posterior:
      Y = P0^-1 + sum H^T H / R,  y = P0^-1 x0 + sum H^T z / R,  P = Y^-1,
      x = P y. It is the independent oracle for fuse_sequential: independent
      sensors give the same posterior in any order, and the two functions
      must agree (this self-check also tries every call in reverse order).
  nis(y, S) -> y*y/S. NIS = normalised innovation squared. |y| <= 1e4,
      0 < S <= 1e8.
  cv_model(dt, q) -> (F, Q) for the constant-velocity model, x = (position,
      velocity), dt seconds (1e-3 <= dt <= 10), continuous white-noise
      acceleration with intensity q (0 <= q <= 100, m^2/s^3):
      F = [[1, dt], [0, 1]],   Q = q*[[dt^3/3, dt^2/2], [dt^2/2, dt]].
  run_filter(x0, P0, F, Q, H, R, zs) -> list with one (x, P, nis) per entry of
      zs (0 to 20 entries; each entry a measurement or None). For every step:
      predict; if the entry is None (dropout) stop there and report nis = None;
      otherwise compute y and S, nis = y*y/S, update, report that nis.
      The reported x, P are the values AFTER the step. x0, P0 are the state
      before the first prediction (P0 only needs to be a covariance here).
  is_valid_covariance(P) -> bool, True iff P (1x1 or 2x2 nested list of finite
      numbers, |entries| <= 1e4) is symmetric and positive semi-definite within
      the tolerance above. Wrong shape or non-finite entries raise ValueError;
      an asymmetric or indefinite matrix returns False, it does not raise. The
      self-check keeps its cases away from the tolerance edge.

Pause before coding - write your predictions down first:
  1. Prior variance 1.5, R = 0.5, H = 1: is the gain nearer 0 or 1? What is
     P_post relative to P_pred and to R? What if R grows without bound?
  2. Fusing two independent thermometers in either order: why must the answer
     match the information form? Which quantity ADDS in that form?
  3. Why can the standard-form (I-KH)P lose symmetry or positivity in floating
     point, and what does the Joseph form add? Does it fix a wrong Q or R?
  4. A dropout step: what happens to P and to the next innovation variance?
  5. NIS has one degree of freedom here. If the declared model were exactly
     true, how often would a single step exceed the 95 percent gate (3.841)?
     What may you conclude from ONE exceedance, and what may you not?
  6. Two sensors share a noise source (correlated errors) but you fuse them as
     independent: is the reported P too small or too large? By how much?
  7. The filter is fed measurements timestamped late, or the true motion
     accelerates though F says constant velocity: what do NIS and P report?
Failure messages name the case and the kind of mismatch, never the expected
numbers. "your code raised X on a VALID input" means the case is inside the
contract and must return; "invalid f(name=...)" lines are the opposite: that
input must raise ValueError. A function still raising NotImplementedError is
reported once, not once per case.
This kit covers declared scalar and 2-state LINEAR Kalman steps with one scalar
measurement: no EKF/UKF, no multi-measurement vectors, no ensemble consistency
statistics over random draws (a Monte-Carlo NIS/NEES test needs an explicit
false-failure policy), no correlated-noise handling, no tuning or estimation of
Q and R, no sensor drivers or timestamps.
Reflection: why does passing this toy NOT validate a real fusion stack?
(Think about wrong or drifting noise levels, biases, correlated and non-Gaussian
errors, outliers, nonlinear models, delayed or out-of-order data, clock sync,
calibration and frames, observability, covariance that looks right but is
optimistic, and finite precision.)
"""
import math


def predict(x, P, F, Q):
    raise NotImplementedError("x_pred = F x and P_pred = F P F^T + Q; note the transpose side")


def innovation(x_pred, P_pred, H, R, z):
    raise NotImplementedError("y = z - H x_pred and S = H P_pred H^T + R")


def kalman_gain(P_pred, H, R):
    raise NotImplementedError("K = P_pred H^T / S; S includes R")


def update(x_pred, P_pred, H, R, z):
    raise NotImplementedError("x + K y, then a covariance update that stays symmetric")


def fuse_sequential(x0, P0, sensors):
    raise NotImplementedError("Chain update over the sensors; carry both x AND P forward")


def fuse_information(x0, P0, sensors):
    raise NotImplementedError("Add information matrices and vectors, then invert once")


def nis(y, S):
    raise NotImplementedError("Normalised innovation squared: y*y/S")


def cv_model(dt, q):
    raise NotImplementedError("F = [[1, dt], [0, 1]] and Q = q*[[dt^3/3, dt^2/2], [dt^2/2, dt]]")


def run_filter(x0, P0, F, Q, H, R, zs):
    raise NotImplementedError("Per step: predict; skip the update on None; else NIS then update")


def is_valid_covariance(P):
    raise NotImplementedError("Symmetric and positive semi-definite, within the stated tolerance")


# ---- SPOILER BELOW: the reference implementations and the case tables hold ----
# ---- the expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _matrix(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_vector(row, length) for row in value))


def _flat(value):
    if isinstance(value, (list, tuple)):
        return [leaf for item in value for leaf in _flat(item)]
    return [value] if _real(value) else []


def _mag(*values):
    return max([1.0] + [abs(v) for value in values for v in _flat(value)])


def _mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def _tr(A):
    return [list(col) for col in zip(*A)]


def _inv(A):
    if len(A) == 1:
        return [[1.0/A[0][0]]]
    det = A[0][0]*A[1][1] - A[0][1]*A[1][0]
    return [[A[1][1]/det, -A[0][1]/det], [-A[1][0]/det, A[0][0]/det]]


def _min_eig(P):
    """Lowest eigenvalue of the symmetric part of a 1x1 or 2x2 matrix."""
    if len(P) == 1:
        return P[0][0]
    b = (P[0][1] + P[1][0])/2.0
    return (P[0][0] + P[1][1])/2.0 - math.hypot((P[0][0] - P[1][1])/2.0, b)


def _is_cov(P):
    tolerance = 1e-9*_mag(P)
    asym = abs(P[0][1] - P[1][0]) if len(P) == 2 else 0.0
    return asym <= tolerance and _min_eig(P) >= -tolerance


def _predict_ref(x, P, F, Q):
    n = len(x)
    xn = [sum(F[i][j]*x[j] for j in range(n)) for i in range(n)]
    FPFt = _mul(_mul(F, P), _tr(F))
    return xn, [[FPFt[i][j] + Q[i][j] for j in range(n)] for i in range(n)]


def _innovation_ref(x, P, H, R, z):
    n = len(x)
    h = H[0]
    y = z - sum(h[j]*x[j] for j in range(n))
    PHt = [sum(P[i][j]*h[j] for j in range(n)) for i in range(n)]
    return y, sum(h[i]*PHt[i] for i in range(n)) + R, PHt


def _update_ref(x, P, H, R, z):
    """Joseph form with explicit symmetrisation (author reference)."""
    n = len(x)
    y, S, PHt = _innovation_ref(x, P, H, R, z)
    K = [PHt[i]/S for i in range(n)]
    A = [[(1.0 if i == j else 0.0) - K[i]*H[0][j] for j in range(n)] for i in range(n)]
    J = _mul(_mul(A, P), _tr(A))
    Pn = [[J[i][j] + R*K[i]*K[j] for j in range(n)] for i in range(n)]
    Pn = [[(Pn[i][j] + Pn[j][i])/2.0 for j in range(n)] for i in range(n)]
    return [x[i] + K[i]*y for i in range(n)], Pn


def _info_update_ref(x, P, H, R, z, sensors=None):
    """Independent route: information form / batch weighted least squares."""
    n = len(x)
    group = sensors if sensors is not None else [(H, R, z)]
    Pinv = _inv(P)
    Y = [row[:] for row in Pinv]
    vec = [sum(Pinv[i][j]*x[j] for j in range(n)) for i in range(n)]
    for (h_, r_, z_) in group:
        h = h_[0]
        for i in range(n):
            vec[i] += h[i]*z_/r_
            for j in range(n):
                Y[i][j] += h[i]*h[j]/r_
    Pn = _inv(Y)
    return [sum(Pn[i][j]*vec[j] for j in range(n)) for i in range(n)], Pn


def _fuse_ref(x, P, sensors):
    for (H, R, z) in sensors:
        x, P = _update_ref(x, P, H, R, z)
    return x, P


def _cv_ref(dt, q):
    return ([[1.0, dt], [0.0, 1.0]],
            [[q*dt**3/3.0, q*dt**2/2.0], [q*dt**2/2.0, q*dt]])


def _run_ref(x, P, F, Q, H, R, zs):
    out = []
    for z in zs:
        x, P = _predict_ref(x, P, F, Q)
        if z is None:
            out.append((x, P, None))
            continue
        y, S, _ = _innovation_ref(x, P, H, R, z)
        value = y*y/S
        x, P = _update_ref(x, P, H, R, z)
        out.append((x, P, value))
    return out


_I2 = [[1, 0], [0, 1]]
_CV = [[1, 1], [0, 1]]
_Z2 = [[0, 0], [0, 0]]
_P2 = [[2.0, 0.5], [0.5, 1.0]]
_SP = [[2, 1], [1, 1]]  # predicted covariance of the constant-velocity hand case
# predict(x, P, F, Q): "hand" answers derived on paper; "formula" cases are
# compared with the reference F P F^T + Q.
_PRED_CASES = [
    (([2], [[1]], [[1]], [[0.5]]), "hand", ([2], [[1.5]])),
    (([1.5], [[0.25]], [[2]], [[0.1]]), "hand", ([3.0], [[1.1]])),
    (([0, 1], _I2, _CV, _Z2), "hand", ([1, 1], _SP)),
    (([3.0, -0.5], [[0.4, 0.0], [0.0, 0.09]], [[1.0, 0.5], [0.0, 1.0]],
      [[0.01, 0.02], [0.02, 0.1]]), "formula", None),
    (([1.0, 2.0], [[1.0, 0.3], [0.3, 2.0]], [[0.9, 0.2], [-0.1, 0.8]],
      [[0.05, 0.01], [0.01, 0.02]]), "formula", None),
]
# innovation(x_pred, P_pred, H, R, z) -> (y, S)
_INNOV_CASES = [
    (([2], [[1.5]], [[1]], 0.5, 3), "hand", (1, 2)),
    (([1.0], [[0.5]], [[2.0]], 0.25, 3.0), "hand", (1.0, 2.25)),
    (([1, 1], _SP, [[1, 0]], 1, 1.5), "hand", (0.5, 3)),
    (([1, 1], _SP, [[0, 1]], 0.5, 0.2), "hand", (-0.8, 1.5)),
    (([1.0, 0.5], _P2, [[1.0, 0.5]], 0.5, 1.2), "formula", None),
]
# kalman_gain(P_pred, H, R) -> K
_GAIN_CASES = [
    (([[1.5]], [[1]], 0.5), "hand", [0.75]),
    ((_SP, [[1, 0]], 1), "hand", [2.0/3.0, 1.0/3.0]),
    ((_SP, [[0, 1]], 0.5), "hand", [2.0/3.0, 2.0/3.0]),
    ((_P2, [[1.0, 0.5]], 0.5), "formula", None),
]
# update(x_pred, P_pred, H, R, z) -> (x_post, P_post). "info" = P_pred is
# positive definite, so the information form is an independent check too.
_UPD_CASES = [
    (([2], [[1.5]], [[1]], 0.5, 3), "hand", ([2.75], [[0.375]])),
    (([10.0], [[1.0]], [[1.0]], 10000.0, 12.0), "info", None),
    (([1, 1], _SP, [[1, 0]], 1, 1.5), "hand",
     ([4.0/3.0, 7.0/6.0], [[2.0/3.0, 1.0/3.0], [1.0/3.0, 2.0/3.0]])),
    (([1, 1], _SP, [[0, 1]], 0.5, 0.2), "info", None),
    (([1.0, 0.5], _P2, [[1.0, 0.5]], 0.5, 1.2), "info", None),
    (([3.0, 1.0], [[1.0, 1.0], [1.0, 1.0]], [[1.0, 0.0]], 1.0, 4.0), "formula", None),
    (([0.0, 0.0], [[100.0, 0.0], [0.0, 100.0]], [[1.0, 0.0]], 1e-06, 7.0), "info", None),
]
_S2 = [([[1.0, 0.0]], 0.5, 1.2), ([[0.0, 1.0]], 0.25, 0.4)]
# fuse_sequential / fuse_information (x0, P0, sensors) -> (x, P); both are
# compared with the information-form reference and tried in reverse order.
_FUSE_CASES = [
    (([0], [[4]], [([[1]], 1, 3), ([[1]], 4, 1)]), "hand", ([13.0/6.0], [[2.0/3.0]])),
    (([1.0], [[2.0]], [([[2.0]], 0.5, 2.5), ([[1.0]], 1.0, 0.8), ([[0.5]], 2.0, 2.0)]),
     "formula", None),
    (([0, 1], [[4, 0], [0, 1]], [([[1, 0]], 1, 2), ([[0, 1]], 0.5, 1.5)]), "hand",
     ([1.6, 4.0/3.0], [[0.8, 0.0], [0.0, 1.0/3.0]])),
    (([0.0, 1.0], [[2.0, 0.5], [0.5, 1.0]], [([[1.0, 1.0]], 0.5, 2.5), ([[1.0, -1.0]], 0.3, -0.7)]),
     "formula", None),
    (([0.5, -0.5], [[1.0, 0.2], [0.2, 3.0]], [([[1.0, 0.0]], 0.4, 1.0)]), "formula", None),
]
# nis(y, S)
_NIS_CASES = [((1, 2), 0.5), ((-3, 9), 1.0), ((0, 5), 0.0), ((2.5, 0.25), 25.0)]
# cv_model(dt, q) -> (F, Q): hand answers
_CV_CASES = [
    ((1, 0), ([[1, 1], [0, 1]], [[0, 0], [0, 0]])),
    ((0.5, 0.6), ([[1.0, 0.5], [0.0, 1.0]], [[0.025, 0.075], [0.075, 0.3]])),
    ((2.0, 0.3), ([[1.0, 2.0], [0.0, 1.0]], [[0.8, 0.6], [0.6, 0.6]])),
    ((0.001, 100.0), None),
]
# run_filter(x0, P0, F, Q, H, R, zs) -> [(x, P, nis)]. The scalar hand case is
# a random walk: P 1 -> 2 -> 2/3, dropout 5/3, then 8/3 -> 8/11.
_RUN_CASES = [
    (([0], [[1]], [[1]], [[1]], [[1]], 1, [1.0, None, 2.0]), "hand",
     [([2.0/3.0], [[2.0/3.0]], 1.0/3.0), ([2.0/3.0], [[5.0/3.0]], None),
      ([18.0/11.0], [[8.0/11.0]], 16.0/33.0)]),
    (([0.0, 1.0], _I2, _CV, [[0.5, 0.75], [0.75, 1.5]], [[1.0, 0.0]], 1.0,
      [1.2, 1.9, None, 4.1]), "formula", None),
    (([0.0, 0.0], _I2, _CV, _Z2, [[1.0, 0.0]], 1.0, []), "hand", []),
    (([1.0, 2.0], _P2, _CV, [[0.1, 0.0], [0.0, 0.1]], [[1.0, 0.0]], 0.5, [None, None]),
     "formula", None),
]
# is_valid_covariance(P) -> bool
_COV_CASES = [
    ([[1.0, 0.0], [0.0, 1.0]], True), ([[1.0, 2.0], [2.0, 1.0]], False),
    ([[1.0, 0.5], [0.4, 1.0]], False), ([[0.0, 0.0], [0.0, 0.0]], True),
    ([[4.0, 2.0], [2.0, 1.0]], True), ([[1.0, 0.0], [0.0, -1e-12]], True),
    ([[1.0, 0.0], [0.0, -1e-06]], False), ([[1.0, 1e-12], [0.0, 1.0]], True),
    ([[2.0]], True), ([[-2.0]], False), ([[-1.0, 0.0], [0.0, -1.0]], False),
    ([[1.0, 1e-06], [0.0, 1.0]], False),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _tupled(value):
    if isinstance(value, (list, tuple)):
        return tuple(_tupled(v) for v in value)
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation?)"
    return text + ")"


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.
    Explicit checks only (no assert), so python -O cannot disable them.
    `notes` is accepted for symmetry with the other kits; this kit has no optional part.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, function, args):
        calls[name] = calls.get(name, 0) + 1
        try:
            return True, function(*args)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
        except Exception as error:
            failures.append(label + ": " + _raised(error))
        return False, None

    def run(label, function, args, compare, index):
        shown = _fresh(args) if index % 2 == 0 else _tupled(args)
        snapshot = _fresh(shown)
        ok, got = attempt(label.split(" ")[0], label, function, shown)
        if not ok:
            return
        try:
            if _fresh(shown) != snapshot:
                raise _Mismatch("an input argument was mutated")
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def close(got, want, name, tolerance):
        if not abs(got - want) <= tolerance:
            raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")

    def vec(got, want, name, tolerance):
        if not _vector(got, len(want)):
            raise _Mismatch(name + " must be a length-" + str(len(want))
                            + " list/tuple of finite int/float")
        for i in range(len(want)):
            close(got[i], want[i], name + "[" + str(i) + "]", tolerance)

    def cov(got, want, name, tolerance, psd=True):
        n = len(want)
        if not _matrix(got, n):
            raise _Mismatch(name + " must be an " + str(n) + "x" + str(n)
                            + " nested list/tuple of finite int/float")
        for i in range(n):
            for j in range(n):
                close(got[i][j], want[i][j], name + "[" + str(i) + "][" + str(j) + "]", tolerance)
        if not psd:
            return
        edge = 1e-9*_mag(got)
        if n == 2 and abs(got[0][1] - got[1][0]) > edge:
            raise _Mismatch(name + " is not symmetric (symmetrise: P = (P + P^T)/2)")
        if _min_eig(got) < -edge:
            raise _Mismatch(name + " has a negative eigenvalue: not positive semi-definite")

    def hand_or_ref(mode, want, ref):
        return want if mode == "hand" else ref

    for i, (args, mode, want) in enumerate(_PRED_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = hand_or_ref(mode, want, _predict_ref(*args))
            if not (isinstance(got, (list, tuple)) and len(got) == 2):
                raise _Mismatch("output must be (x_pred, P_pred)")
            tolerance = 1e-9*_mag(args, ref)
            vec(got[0], ref[0], "x_pred", tolerance)
            cov(got[1], ref[1], "P_pred", tolerance)
        run("predict " + str(i) + " (" + mode + ")", predict, args, compare, i)

    for i, (args, mode, want) in enumerate(_INNOV_CASES):
        def compare(got, args=args, mode=mode, want=want):
            r = _innovation_ref(*args)
            ref = hand_or_ref(mode, want, (r[0], r[1]))
            if not _vector(got, 2):
                raise _Mismatch("output must be (y, S), two finite int/float")
            tolerance = 1e-9*_mag(args, ref)
            close(got[0], ref[0], "innovation y", tolerance)
            close(got[1], ref[1], "innovation variance S", tolerance)
        run("innovation " + str(i) + " (" + mode + ")", innovation, args, compare, i)

    for i, (args, mode, want) in enumerate(_GAIN_CASES):
        def compare(got, args=args, mode=mode, want=want):
            P, H, R = args
            if mode != "hand":
                _, S, PHt = _innovation_ref([0.0]*len(P), P, H, R, 0.0)
                want = [v/S for v in PHt]
            vec(got, want, "gain K", 1e-9*_mag(args, want))
        run("kalman_gain " + str(i) + " (" + mode + ")", kalman_gain, args, compare, i)

    for i, (args, mode, want) in enumerate(_UPD_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = hand_or_ref(mode, want, _update_ref(*args))
            if not (isinstance(got, (list, tuple)) and len(got) == 2):
                raise _Mismatch("output must be (x_post, P_post)")
            tolerance = 1e-9*_mag(args, ref)
            vec(got[0], ref[0], "x_post", tolerance)
            cov(got[1], ref[1], "P_post", tolerance)
            if mode == "info":  # independent information-form cross-check
                alt = _info_update_ref(*args)
                vec(got[0], alt[0], "x_post (information form)", 1e-8*_mag(args, alt))
                cov(got[1], alt[1], "P_post (information form)", 1e-8*_mag(args, alt))
        run("update " + str(i) + " (" + mode + ")", update, args, compare, i)

    for name, function in (("fuse_sequential", fuse_sequential),
                           ("fuse_information", fuse_information)):
        for i, (args, mode, want) in enumerate(_FUSE_CASES):
            def compare(got, args=args, mode=mode, want=want, function=function):
                x0, P0, sensors = args
                ref = _info_update_ref(x0, P0, None, None, None, sensors)
                if mode == "hand":
                    vec(want[0], ref[0], "kit table", 1e-9)
                    ref = want
                if not (isinstance(got, (list, tuple)) and len(got) == 2):
                    raise _Mismatch("output must be (x, P)")
                tolerance = 1e-9*_mag(args, ref)
                vec(got[0], ref[0], "fused x", tolerance)
                cov(got[1], ref[1], "fused P", tolerance)
                if len(sensors) > 1:
                    back = function(_fresh(x0), _fresh(P0), list(reversed(_fresh(sensors))))
                    vec(back[0], ref[0], "fused x (sensors in reverse order)", tolerance)
                    cov(back[1], ref[1], "fused P (sensors in reverse order)", tolerance)
            run(name + " " + str(i) + " (" + mode + ")", function, args, compare, i)

    for i, (args, want) in enumerate(_NIS_CASES):
        def compare(got, args=args, want=want):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            close(got, want, "NIS", 1e-9*max(1.0, want))
        run("nis " + str(i), nis, args, compare, i)

    for i, (args, want) in enumerate(_CV_CASES):
        def compare(got, args=args, want=want):
            ref = want if want is not None else _cv_ref(*args)
            if not (isinstance(got, (list, tuple)) and len(got) == 2):
                raise _Mismatch("output must be (F, Q)")
            tolerance = 1e-9*_mag(args, ref)
            cov(got[0], ref[0], "F", tolerance, False)
            cov(got[1], ref[1], "Q", tolerance)
        run("cv_model " + str(i), cv_model, args, compare, i)

    for i, (args, mode, want) in enumerate(_RUN_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = hand_or_ref(mode, want, _run_ref(*args))
            if not (isinstance(got, (list, tuple)) and len(got) == len(ref)):
                raise _Mismatch("output must have one (x, P, nis) entry per measurement slot")
            tolerance = 1e-9*_mag(args, [(r[0], r[1]) for r in ref],
                                  [r[2] for r in ref if r[2] is not None])
            for k, (step, row) in enumerate(zip(got, ref)):
                tag = "step " + str(k) + " "
                if not (isinstance(step, (list, tuple)) and len(step) == 3):
                    raise _Mismatch(tag + "must be (x, P, nis)")
                vec(step[0], row[0], tag + "x", tolerance)
                cov(step[1], row[1], tag + "P", tolerance)
                if row[2] is None:
                    if step[2] is not None:
                        raise _Mismatch(tag + "is a dropout: nis must be None")
                elif not _real(step[2]):
                    raise _Mismatch(tag + "nis must be a finite number")
                else:
                    close(step[2], row[2], tag + "nis", tolerance)
        run("run_filter " + str(i) + " (" + mode + ")", run_filter, args, compare, i)

    for i, (matrix, want) in enumerate(_COV_CASES):
        def compare(got, want=want):
            if type(got) is not bool:
                raise _Mismatch("output must be True or False")
            if got != want:
                raise _Mismatch("verdict is wrong for this matrix")
        run("is_valid_covariance " + str(i), is_valid_covariance, (matrix,), compare, i)

    nan, inf = float('nan'), float('inf')
    x2, P2, F2, Q2 = [1.0, 0.5], [[2.0, 0.5], [0.5, 1.0]], [[1.0, 0.1], [0.0, 1.0]], \
        [[0.1, 0.0], [0.0, 0.1]]
    H2 = [[1.0, 0.0]]
    bad_vec = [[1.0], [1.0, 2.0, 3.0], [nan, 1.0], [inf, 1.0], [True, 1.0], [10001.0, 0.0],
               [-10001.0, 0.0], ["1", 1.0], [[1.0, 0.5]], [], "ab", None, {0: 1.0}, 3.0]
    bad_cov = [[[1.0, 0.0]], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]], [[1.0, 0.5], [0.4, 1.0]],
               [[1.0, 2.0], [2.0, 1.0]], [[-1.0, 0.0], [0.0, 1.0]], [[nan, 0.0], [0.0, 1.0]],
               [[inf, 0.0], [0.0, 1.0]], [[True, 0.0], [0.0, 1.0]], [[10001.0, 0.0], [0.0, 1.0]],
               [[1.0]], [1.0, 0.0], "ab", None, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]
    bad_pd = bad_cov + [[[1.0, 0.0], [0.0, 0.0]], [[0.0, 0.0], [0.0, 0.0]],
                        [[1.0, 1.0], [1.0, 1.0]]]
    bad_f = [[[1.0, 0.0]], [[101.0, 0.0], [0.0, 1.0]], [[nan, 0.0], [0.0, 1.0]],
             [[inf, 0.0], [0.0, 1.0]], [[True, 0.0], [0.0, 1.0]], [[1.0]], [1.0, 0.0], None, "ab",
             [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]
    bad_h = [[1.0, 0.0], [[1.0], [0.0]], [[1.0, 0.0], [0.0, 1.0]], [[nan, 0.0]], [[inf, 0.0]],
             [[101.0, 0.0]], [[True, 0.0]], [[1.0]], [[1.0, 0.0, 0.0]], [[]], None, "ab"]
    bad_r = [0.0, -1.0, 1e-07, 10001.0, nan, inf, True, "1", None, [1.0]]
    bad_z = [nan, inf, -inf, True, 10001.0, -10001.0, "1", None, [1.0]]
    bad_scalar_y = [nan, inf, True, 10001.0, -10001.0, "1", None]
    bad_s = [0.0, -1.0, nan, inf, True, 1e8 + 1.0, "1", None]
    bad_dt = [0.0, 0.0009, 10.01, -1.0, nan, inf, True, "1", None]
    bad_q = [-0.1, 100.01, nan, inf, True, "1", None]
    bad_sensors = [[], [(H2, 0.5, 1.2)]*5, [(H2, 0.5)], [(H2, 0.5, 1.2, 0.0)], "ab", None,
                   [(H2, -1.0, 1.2)], [(H2, 0.5, nan)], [([1.0, 0.0], 0.5, 1.2)],
                   [([[1.0]], 0.5, 1.2)], [(H2, True, 1.2)], [H2], 3.0]
    bad_zs = [1.0, None, [nan], [True], ["1"], [10001.0], [1.0]*21, "ab", [[1.0]]]
    bad_matrix_any = [[[1.0, 0.0]], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]], [[nan, 0.0], [0.0, 1.0]],
                      [[inf, 0.0], [0.0, 1.0]], [[True, 0.0], [0.0, 1.0]],
                      [[10001.0, 0.0], [0.0, 1.0]], [1.0, 0.0], "ab", None, [], [[]], 2.0,
                      [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]
    signatures = [
        ("predict", predict, ("x", "P", "F", "Q"), (x2, P2, F2, Q2),
         {"x": bad_vec, "P": bad_cov, "F": bad_f, "Q": bad_cov}),
        ("innovation", innovation, ("x_pred", "P_pred", "H", "R", "z"), (x2, P2, H2, 0.5, 1.2),
         {"x_pred": bad_vec, "P_pred": bad_cov, "H": bad_h, "R": bad_r, "z": bad_z}),
        ("kalman_gain", kalman_gain, ("P_pred", "H", "R"), (P2, H2, 0.5),
         {"P_pred": bad_cov, "H": bad_h, "R": bad_r}),
        ("update", update, ("x_pred", "P_pred", "H", "R", "z"), (x2, P2, H2, 0.5, 1.2),
         {"x_pred": bad_vec, "P_pred": bad_cov, "H": bad_h, "R": bad_r, "z": bad_z}),
        ("fuse_sequential", fuse_sequential, ("x0", "P0", "sensors"), (x2, P2, _S2),
         {"x0": bad_vec, "P0": bad_pd, "sensors": bad_sensors}),
        ("fuse_information", fuse_information, ("x0", "P0", "sensors"), (x2, P2, _S2),
         {"x0": bad_vec, "P0": bad_pd, "sensors": bad_sensors}),
        ("nis", nis, ("y", "S"), (0.5, 2.0), {"y": bad_scalar_y, "S": bad_s}),
        ("cv_model", cv_model, ("dt", "q"), (0.5, 0.2), {"dt": bad_dt, "q": bad_q}),
        ("run_filter", run_filter, ("x0", "P0", "F", "Q", "H", "R", "zs"),
         (x2, P2, F2, Q2, H2, 0.5, [1.2, None, 0.8]),
         {"x0": bad_vec, "P0": bad_cov, "F": bad_f, "Q": bad_cov, "H": bad_h, "R": bad_r,
          "zs": bad_zs}),
        ("is_valid_covariance", is_valid_covariance, ("P",), (P2,), {"P": bad_matrix_any}),
    ]
    for title, function, names, args, bad in signatures:
        for slot, name in enumerate(names):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                calls[title] = calls.get(title, 0) + 1
                try:
                    function(*trial)
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
    print("CoreLab manual linear Kalman self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

"""CoreLab Parameter identification lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the nine core functions below, then run your edited file locally:
  Windows: py -3 L21-identification.v1.py
  macOS/Linux: python3 L21-identification.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared model (SYNTHETIC logs only): one scalar output y and one scalar input u,
sampled at a fixed step, obey the discrete first-order law
    y[k+1] = a*y[k] + b*u[k]        (k = 0 .. n-1)
with unknown parameters a (decay, dimensionless) and b (input gain, y-units per
u-unit). A log is two sequences: y with n+1 samples and u with n samples, so
2 <= n <= 50 (len(u) = n, len(y) = n + 1). Nothing here measures a robot: every
number is made up, and every guarantee is conditional on the declared law.

Representation (finite int/float, never bool; lists or tuples both accepted):
  y, u: sequences as above, |value| <= 1e4.   a, b: |value| <= 100.
  y0: |y0| <= 1e4 (simulate only; there u has 1 to 50 entries).
  G: 2x2 nested list, finite, |entry| <= 1e10, symmetric within
     1e-9*max(1, largest |entry|) and positive semi-definite within the same
     tolerance (lowest eigenvalue >= -tolerance).
  sigma: 0 < sigma <= 1e3.   tol: 0 < tol <= 1e4.
  ranges: 1 to 6 pairs (lo, hi), |value| <= 1e6, lo <= hi (lo == hi allowed).
  draws: same length as ranges, each a number in [0, 1] (both ends allowed).
  mode: the string "uniform" (default) or "log".
  Wrong type or shape, bool, NaN, infinity, out of bounds -> raise ValueError.
  Never mutate the inputs. Returned numbers are finite int/float except where
  condition_number is allowed to return math.inf (below).
  Output tolerance (unless stated): 1e-9*max(1, largest magnitude in the case),
  absolute.

The linear least-squares view. Stack the rows (y[k], u[k]) as the regressors and
y[k+1] as the target. The 2x2 normal equations are G p = g with p = (a, b):
  G = [[Syy, Syu], [Syu, Suu]],  g = [Sy1y, Sy1u]
  Syy = sum y[k]^2, Syu = sum y[k]*u[k], Suu = sum u[k]^2,
  Sy1y = sum y[k+1]*y[k], Sy1u = sum y[k+1]*u[k]        (k = 0 .. n-1).
G is the Gram matrix of the regressors. If its columns are parallel (u all zero,
y and u both constant, u proportional to y ...) it is singular and no unique
(a, b) exists: the parameters are NOT IDENTIFIABLE from that log.

Contracts:
  simulate(a, b, y0, u) -> list [y0, y1, ..., yn], y[k+1] = a*y[k] + b*u[k],
      u has 1 to 50 entries; the result has len(u) + 1 entries.
  normal_equations(y, u) -> (G, g): G a 2x2 nested list, g a length-2 list, as
      defined above.
  condition_number(G) -> the 2-norm condition number lambda_max/lambda_min of
      the symmetric PSD 2x2 Gram matrix G (float >= 1). With t = trace and
      det = G00*G11 - G01*G10: if det <= 1e-12*t*t (this includes G = 0) the
      matrix is treated as singular and the function returns math.inf (it does
      not raise). The self-check keeps its cases away from this edge.
      Relative tolerance 1e-6 for finite results.
  identifiability(y, u) -> one of the strings
      "identifiable"    (condition number of G <= 1e4),
      "weak"            (1e4 < condition number < inf: a fit exists but its
                         parameters are very sensitive to small noise),
      "unidentifiable"  (condition number is inf: singular).
      The self-check keeps its cases away from the 1e4 edge. Honest limits:
      "unidentifiable" here means NUMERICALLY singular (det <= 1e-12*trace^2),
      which also covers badly scaled or tiny-signal logs that are not exactly
      parallel, and the condition number depends on the units of y and u
      (rescaling a column changes it). The bands are a convention, not a theorem.
  fit_first_order(y, u) -> (a, b), the least-squares parameters: solve G p = g
      (Cramer's rule, elimination, QR or any exact-in-theory method are all
      accepted). Judged by behaviour: within the output tolerance scaled by
      max(1, condition_number/1000), and the residual must be orthogonal to both
      regressor columns. If identifiability(y, u) is "unidentifiable" raise
      ValueError (YES: for an unidentifiable log the function raises, it does not
      return a guess). "weak" logs still return a fit. Note ValueError is also
      the answer for invalid input; the self-check distinguishes the two cases.
  residual_rms(a, b, y, u) -> sqrt(mean over k of (y[k+1] - (a*y[k] + b*u[k]))^2),
      the ONE-STEP prediction error of the given parameters on the given log.
  heldout_check(a, b, y_test, u_test, tol) -> (rms, ok): rms as in residual_rms
      on the held-out log, ok is the bool rms <= tol. Use a log that was NOT
      used for the fit.
  parameter_std(y, u, sigma) -> (std_a, std_b): the standard deviations of the
      least-squares estimates if the targets carry independent noise of
      standard deviation sigma: std_a = sigma*sqrt((G^-1)00),
      std_b = sigma*sqrt((G^-1)11). Raises ValueError when unidentifiable.
  randomize(ranges, draws, mode="uniform") -> list of floats, one per pair, from
      explicit deterministic draws d in [0, 1]. "uniform": lo + d*(hi - lo).
      "log" (needs lo > 0): lo*(hi/lo)**d, i.e. uniform in log scale. Equivalent
      forms such as lo*(1-d) + hi*d are accepted. Every result must lie inside
      [lo, hi] EXACTLY (no tolerance): clamp, because floating point can step
      an ulp outside. Domain randomisation widens training data over declared
      ranges; it does not make a model true.

Pause before coding - write your predictions down first:
  1. With y[k+1] = y[k] + u[k], which log can you recover (a, b) = (1, 1) from
     exactly: u all zero, or u alternating? Why does the Gram matrix tell you?
  2. A step input held at 1 while y has already settled at 1: is (a, b) unique?
     Which direction in (a, b) space can the data not see?
  3. A near-constant input gives condition number around 1e6: how much does a
     0.001 error in a target move the fitted parameters, roughly?
  4. Noise-free data are fitted exactly on the training log. Why can the
     held-out residual still be large, and what does that say about the fit?
  5. Draws 0, 0.5 and 1 on the range (2, 8): what do you expect, and does a
     log-uniform draw 0.5 land at the same value?
Failure messages name the case and the kind of mismatch, never the expected
numbers. "your code raised X on a VALID input" means the case is inside the
contract and must return; "invalid f(name=...)" lines are the opposite: that
input must raise ValueError. A function still raising NotImplementedError is
reported once, not once per case.
This kit covers a declared first-order linear model on SYNTHETIC logs, with
noise supplied as explicit numbers: no random sampling, no nonlinear or
multi-input models, no physics-simulator identification, no real robot data and
no sim-to-real claim.
Reflection: why does passing this toy NOT validate a real system? (Think about
unmodelled dynamics and delay, friction and saturation, noise that is coloured
or correlated with the input, closed-loop data, sample-time jitter, sensor
calibration, a model class that is wrong, ranges that exclude the truth, and
whether randomised simulations cover reality at all.)
"""
import math


def simulate(a, b, y0, u):
    raise NotImplementedError("y[k+1] = a*y[k] + b*u[k]; return y0 first, then n more samples")


def normal_equations(y, u):
    raise NotImplementedError("Sums over k = 0..n-1 of the regressors (y[k], u[k]) and target y[k+1]")


def condition_number(G):
    raise NotImplementedError("lambda_max / lambda_min of the Gram matrix; math.inf when singular")


def identifiability(y, u):
    raise NotImplementedError("Classify from the condition number of the Gram matrix of this log")


def fit_first_order(y, u):
    raise NotImplementedError("Solve the 2x2 normal equations; raise ValueError if unidentifiable")


def residual_rms(a, b, y, u):
    raise NotImplementedError("Root-mean-square of the one-step prediction errors")


def heldout_check(a, b, y_test, u_test, tol):
    raise NotImplementedError("Score parameters on a log that was not used for the fit")


def parameter_std(y, u, sigma):
    raise NotImplementedError("sigma times the square root of the diagonal of the inverse Gram matrix")


def randomize(ranges, draws, mode="uniform"):
    raise NotImplementedError("Map each draw in [0, 1] into its (lo, hi) range and stay inside it")


# ---- SPOILER BELOW: the reference implementations and the case tables hold ----
# ---- the expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _flat(value):
    if isinstance(value, (list, tuple)):
        return [leaf for item in value for leaf in _flat(item)]
    return [value] if _real(value) else []


def _mag(*values):
    return max([1.0] + [abs(v) for value in values for v in _flat(value)])


def _sim_ref(a, b, y0, u):
    out = [float(y0)]
    for x in u:
        out.append(a*out[-1] + b*x)
    return out


def _ne_ref(y, u):
    n = len(u)
    G = [[math.fsum(y[k]*y[k] for k in range(n)), math.fsum(y[k]*u[k] for k in range(n))],
         [0.0, math.fsum(u[k]*u[k] for k in range(n))]]
    G[1][0] = G[0][1]
    return G, [math.fsum(y[k+1]*y[k] for k in range(n)), math.fsum(y[k+1]*u[k] for k in range(n))]


def _cond_ref(G):
    t = G[0][0] + G[1][1]
    off = (G[0][1] + G[1][0])/2.0
    det = G[0][0]*G[1][1] - off*off
    if t <= 0 or det <= 1e-12*t*t:
        return math.inf
    root = math.sqrt(max(0.0, t*t/4.0 - det))
    big = t/2.0 + root
    return big/(det/big)


def _status_ref(y, u):
    c = _cond_ref(_ne_ref(y, u)[0])
    if c == math.inf:
        return "unidentifiable"
    return "weak" if c > 1e4 else "identifiable"


def _cramer_ref(y, u):
    G, g = _ne_ref(y, u)
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    return ((g[0]*G[1][1] - G[0][1]*g[1])/det, (G[0][0]*g[1] - G[1][0]*g[0])/det)


def _rms_ref(a, b, y, u):
    n = len(u)
    return math.sqrt(math.fsum((y[k+1] - (a*y[k] + b*u[k]))**2 for k in range(n))/n)


def _std_ref(y, u, sigma):
    G = _ne_ref(y, u)[0]
    det = G[0][0]*G[1][1] - G[0][1]*G[1][0]
    return (sigma*math.sqrt(G[1][1]/det), sigma*math.sqrt(G[0][0]/det))


def _rand_ref(ranges, draws, mode):
    out = []
    for (lo, hi), d in zip(ranges, draws):
        v = lo + d*(hi - lo) if mode == "uniform" else lo*(hi/lo)**d
        out.append(min(max(v, lo), hi))
    return out


_U1 = [1.0, 0.0, -1.0]
_Y1 = [1.0, 2.5, 1.25, -1.375]            # simulate(0.5, 2.0, 1.0, _U1)
_U2 = [1.0, 0.0, 1.0]
_Y2 = [0.0, 1.0, 1.0, 2.0]                # y[k+1] = y[k] + u[k]
_U3 = [1.0, -1.0]
_Y3 = [1.0, 2.0, 3.0]
_U4 = [1.0, 0.5, -1.0, 0.8, -0.6]
_Y4 = [1.0, 1.4, 1.1, 0.9, 1.3, 0.7]      # noisy log, no exact (a, b)
_U5 = [1, -1, 0.5, -0.5, 1, 1, -1, 0.25]
_Y5 = _sim_ref(0.8, 0.5, 0.5, _U5)
_U6 = [1.0, 1.002, 1.0, 0.998, 1.0, 1.002, 1.0, 0.998]
_Y6 = _sim_ref(0.7, 0.3, 1.0, _U6)        # near-constant input: weak
_U13 = [1.0, 1.05, 1.0, 0.95, 1.0, 1.05, 1.0, 0.95]
_Y13 = _sim_ref(0.7, 0.3, 1.0, _U13)      # near-constant input, condition number about 2.5e3
_U14 = [1.0, 1.015, 1.0, 0.985, 1.0, 1.015, 1.0, 0.985]
_Y14 = _sim_ref(0.7, 0.3, 1.0, _U14)      # weaker excitation, condition number about 2.8e4
_Y15 = [0.0, 4.0, 6.0, 7.0]
_U15 = [4.0, 4.0, 4.0]                    # constant u but y still moving: identifiable
_U7 = [0.0, 0.0, 0.0, 0.0]
_Y7 = _sim_ref(0.5, 1.0, 1.0, _U7)        # u == 0: b invisible
_U8 = [1.0, 1.0, 1.0]
_Y8 = [2.0, 2.0, 2.0, 2.0]                # settled step: a*2 + b = 2 has many solutions
_Y9 = [1.0, 2.0, 4.0, 8.0]
_U9 = [2.0, 4.0, 8.0]                     # u = 2*y: parallel columns
_Y10 = [0.0, 0.0, 0.0]
_U10 = [1.0, 1.0]                         # y == 0: a invisible
_Y11 = [1.0, 1.0, 1.0, 1.0]
_U11 = [0.0, 1.0, -1.0]                   # y constant but u moves: identifiable (a=1, b=0)
_Y12 = [1.0, 2.0, 1.0, 2.0]
_U12 = [0.0, 0.0, 0.0]

# simulate(a, b, y0, u)
_SIM_CASES = [
    ((0.5, 2.0, 1.0, _U1), "hand", [1.0, 2.5, 1.25, -1.375]),
    ((1.0, 0.0, 3.0, [5.0, 5.0]), "hand", [3.0, 3.0, 3.0]),
    ((0.9, 0.1, 0.0, [1.0]*4), "hand", [0.0, 0.1, 0.19, 0.271, 0.3439]),
]
# normal_equations(y, u) -> (G, g)
_NE_CASES = [
    ((_Y3, _U3), "hand", ([[5.0, -1.0], [-1.0, 2.0]], [8.0, -1.0])),
    ((_Y2, _U2), "hand", ([[2.0, 1.0], [1.0, 2.0]], [3.0, 3.0])),
    ((_Y4, _U4), "formula", None),
]
# condition_number(G): lambda_max/lambda_min, math.inf if singular
_COND_CASES = [
    (([[4.0, 0.0], [0.0, 1.0]],), "hand", 4.0),
    (([[2.0, 1.0], [1.0, 2.0]],), "hand", 3.0),
    (([[1.0, 1.0], [1.0, 1.0]],), "hand", math.inf),
    (([[0.0, 0.0], [0.0, 0.0]],), "hand", math.inf),
    (([[5.0, -1.0], [-1.0, 2.0]],), "formula", None),
    (([[1000000.0, 0.0], [0.0, 0.001]],), "hand", 1e9),
]
# identifiability(y, u)
_ID_CASES = [
    ((_Y5, _U5), "identifiable"), ((_Y6, _U6), "weak"), ((_Y7, _U7), "unidentifiable"),
    ((_Y8, _U8), "unidentifiable"), ((_Y9, _U9), "unidentifiable"),
    ((_Y11, _U11), "identifiable"), ((_Y15, _U15), "identifiable"),
    ((_Y13, _U13), "identifiable"), ((_Y14, _U14), "weak"),
]
# fit_first_order(y, u) -> (a, b); "hand" = known generating parameters
_FIT_CASES = [
    ((_Y1, _U1), "hand", (0.5, 2.0)),
    ((_Y2, _U2), "hand", (1.0, 1.0)),
    ((_Y11, _U11), "hand", (1.0, 0.0)),
    ((_Y5, _U5), "hand", (0.8, 0.5)),
    ((_Y4, _U4), "formula", None),
    ((_Y6, _U6), "hand", (0.7, 0.3)),
    ((_Y15, _U15), "hand", (0.5, 1.0)),
]
# unidentifiable logs: fit_first_order and parameter_std must raise ValueError
_UNID_LOGS = [(_Y7, _U7), (_Y8, _U8), (_Y9, _U9), (_Y10, _U10)]
# residual_rms(a, b, y, u)
_RES_CASES = [
    ((0.5, 2.0, _Y1, _U1), "hand", 0.0),
    ((1.0, 0.0, _Y12, _U12), "hand", 1.0),
    ((0.5, 1.0, [2.0, 3.0, 2.0, 4.0], [2.0, 1.0, 2.0]), "formula", None),
]
# heldout_check(a, b, y_test, u_test, tol) -> (rms, ok)
_HELD_CASES = [
    ((0.5, 2.0, _Y1, _U1, 0.01), "hand", (0.0, True)),
    ((1.0, 0.0, _Y12, _U12, 0.5), "hand", (1.0, False)),
    ((1.0, 0.0, _Y12, _U12, 1.5), "hand", (1.0, True)),
    ((1.0, 0.0, _Y12, _U12, 1.0), "hand", (1.0, True)),
    ((0.9, 0.2, _Y4, _U4, 0.2), "formula", None),
]
# parameter_std(y, u, sigma) -> (std_a, std_b)
_STD_CASES = [
    ((_Y2, _U2, 0.3), "formula", None),
    ((_Y3, _U3, 0.1), "formula", None),
    ((_Y11, _U11, 2.0), "hand", (2.0*math.sqrt(1.0/3.0), 2.0*math.sqrt(1.0/2.0))),
]
# randomize(ranges, draws, mode) -> parameters inside [lo, hi]
_RAND_CASES = [
    ((((0, 2), (10, 20)), (0.25, 0.5), "uniform"), "hand", [0.5, 15.0]),
    ((((0, 2), (10, 20)), (0.0, 1.0), "uniform"), "hand", [0.0, 20.0]),
    ((((1, 100),), (0.5,), "log"), "hand", [10.0]),
    ((((0.01, 1.0),), (0.5,), "log"), "hand", [0.1]),
    ((((3, 3), (-2, -1)), (0.7, 0.5), "uniform"), "hand", [3.0, -1.5]),
    ((((0.3, 0.9),), (1.0,), "uniform"), "bounds", None),
    ((((0.1, 0.7), (0.3, 0.9), (2.0, 8.0)), (0.123, 0.987, 0.5), "uniform"), "formula", None),
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

    def mat(got, want, name, tolerance):
        if not (isinstance(got, (list, tuple)) and len(got) == 2
                and all(_vector(row, 2) for row in got)):
            raise _Mismatch(name + " must be a 2x2 nested list/tuple of finite int/float")
        for i in range(2):
            for j in range(2):
                close(got[i][j], want[i][j], name + "[" + str(i) + "][" + str(j) + "]", tolerance)

    for i, (args, mode, want) in enumerate(_SIM_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _sim_ref(*args)
            if not (isinstance(got, (list, tuple)) and len(got) == len(args[3]) + 1):
                raise _Mismatch("output must be a list with len(u) + 1 samples (y0 first)")
            vec(got, ref, "y", 1e-9*_mag(args, ref))
        run("simulate " + str(i) + " (" + mode + ")", simulate, args, compare, i)

    for i, (args, mode, want) in enumerate(_NE_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _ne_ref(*args)
            if not (isinstance(got, (list, tuple)) and len(got) == 2):
                raise _Mismatch("output must be (G, g)")
            tolerance = 1e-9*_mag(args, ref)
            mat(got[0], ref[0], "G", tolerance)
            vec(got[1], ref[1], "g", tolerance)
        run("normal_equations " + str(i) + " (" + mode + ")", normal_equations, args, compare, i)

    for i, (args, mode, want) in enumerate(_COND_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _cond_ref(*args)
            if ref == math.inf:
                if got != math.inf:
                    raise _Mismatch("a singular Gram matrix must give math.inf")
                return
            if not _real(got):
                raise _Mismatch("output must be one finite number for this matrix")
            close(got, ref, "condition number", 1e-6*ref)
        run("condition_number " + str(i) + " (" + mode + ")", condition_number, args, compare, i)

    for i, (args, want) in enumerate(_ID_CASES):
        def compare(got, args=args, want=want):
            if got != want:
                raise _Mismatch("verdict for this log is wrong (one of identifiable / weak / "
                                "unidentifiable)")
            if _status_ref(*args) != want:
                raise _Mismatch("kit table disagrees with its reference")
        run("identifiability " + str(i), identifiability, args, compare, i)

    for i, (args, mode, want) in enumerate(_FIT_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _cramer_ref(*args)
            cn = _cond_ref(_ne_ref(*args)[0])
            tolerance = 1e-9*_mag(args, ref)*max(1.0, cn/1000.0)
            vec(got, ref, "fitted (a, b)", tolerance)
            y, u = args
            res = [y[k+1] - (got[0]*y[k] + got[1]*u[k]) for k in range(len(u))]
            scale = _mag(args)*max(1.0, cn/1000.0)
            for name, column in (("y", y), ("u", u)):
                dot = math.fsum(res[k]*column[k] for k in range(len(u)))
                if abs(dot) > 1e-6*scale*scale:
                    raise _Mismatch("the residual is not orthogonal to the " + name
                                    + " regressor column: not a least-squares solution")
        run("fit_first_order " + str(i) + " (" + mode + ")", fit_first_order, args, compare, i)

    for i, (y, u) in enumerate(_UNID_LOGS):
        label = "fit_first_order unidentifiable " + str(i)
        calls["fit_first_order"] = calls.get("fit_first_order", 0) + 1
        try:
            fit_first_order(_fresh(y), _fresh(u))
        except ValueError:
            pass
        except NotImplementedError:
            missing.setdefault("fit_first_order", []).append(label)
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__ + " instead of ValueError")
        else:
            failures.append(label + ": returned a fit for a log that cannot identify (a, b); "
                            "raise ValueError")

    for i, (args, mode, want) in enumerate(_RES_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _rms_ref(*args)
            if not _real(got):
                raise _Mismatch("output must be one finite number")
            close(got, ref, "residual rms", 1e-9*_mag(args, ref))
        run("residual_rms " + str(i) + " (" + mode + ")", residual_rms, args, compare, i)

    for i, (args, mode, want) in enumerate(_HELD_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else (_rms_ref(*args[:4]), _rms_ref(*args[:4]) <= args[4])
            if not (isinstance(got, (list, tuple)) and len(got) == 2 and _real(got[0])
                    and type(got[1]) is bool):
                raise _Mismatch("output must be (rms, ok) with ok a bool")
            close(got[0], ref[0], "held-out rms", 1e-9*_mag(args, ref[0]))
            if got[1] != ref[1]:
                raise _Mismatch("the pass/fail verdict against tol is wrong")
        run("heldout_check " + str(i) + " (" + mode + ")", heldout_check, args, compare, i)

    for i, (args, mode, want) in enumerate(_STD_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ref = want if mode == "hand" else _std_ref(*args)
            vec(got, ref, "std (a, b)", 1e-9*_mag(args, ref))
        run("parameter_std " + str(i) + " (" + mode + ")", parameter_std, args, compare, i)

    for i, (y, u) in enumerate(_UNID_LOGS):
        label = "parameter_std unidentifiable " + str(i)
        calls["parameter_std"] = calls.get("parameter_std", 0) + 1
        try:
            parameter_std(_fresh(y), _fresh(u), 0.5)
        except ValueError:
            pass
        except NotImplementedError:
            missing.setdefault("parameter_std", []).append(label)
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__ + " instead of ValueError")
        else:
            failures.append(label + ": returned for an unidentifiable log; raise ValueError")

    for i, (args, mode, want) in enumerate(_RAND_CASES):
        def compare(got, args=args, mode=mode, want=want):
            ranges, draws, kind = args
            ref = want if mode == "hand" else _rand_ref(*args)
            if not (isinstance(got, (list, tuple)) and len(got) == len(ranges)
                    and all(_real(v) for v in got)):
                raise _Mismatch("output must have one finite number per range")
            for k, (lo, hi) in enumerate(ranges):
                if not lo <= got[k] <= hi:
                    raise _Mismatch("parameter " + str(k) + " lies outside its declared range "
                                    "(clamp into [lo, hi])")
            if mode != "bounds":
                vec(got, ref, "randomised parameters", 1e-9*_mag(args, ref))
        run("randomize " + str(i) + " (" + mode + ")", randomize, args, compare, i)

    nan, inf = float('nan'), float('inf')
    bad_seq = [[1.0], [], "abc", None, 3.0, [nan, 1.0, 2.0], [inf, 1.0, 2.0], [True, 1.0, 2.0],
               ["1", 1.0, 2.0], [10001.0, 1.0, 2.0], [[1.0], [2.0], [3.0]], {0: 1.0},
               [1.0]*52]
    good_y, good_u = [1.0, 2.0, 1.5, 0.5], [1.0, -1.0, 0.5]
    bad_y = bad_seq + [good_y[:3], good_y + [0.0]]
    bad_u = bad_seq + [good_u[:2], good_u + [0.0], [1.0]]
    bad_par = [nan, inf, True, 101.0, -101.0, "1", None, [1.0]]
    bad_y0 = [nan, inf, True, 10001.0, "1", None, [1.0]]
    bad_sim_u = [[], "abc", None, [nan], [True], [10001.0], [1.0]*51, 3.0, [[1.0]]]
    bad_G = [[[1.0, 0.0]], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]], [[1.0, 2.0], [3.0, 1.0]],
             [[1.0, 2.0], [2.0, 1.0]], [[-1.0, 0.0], [0.0, 1.0]], [[nan, 0.0], [0.0, 1.0]],
             [[inf, 0.0], [0.0, 1.0]], [[True, 0.0], [0.0, 1.0]], [[1e11, 0.0], [0.0, 1.0]],
             [1.0, 0.0], "ab", None, [[1.0]], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]
    bad_sigma = [0.0, -1.0, nan, inf, True, 1001.0, "1", None]
    bad_tol = [0.0, -0.1, nan, inf, True, 10001.0, "1", None]
    ok_ranges = ((0.5, 1.5), (2.0, 4.0))
    ok_draws = (0.25, 0.75)
    bad_ranges = [[], [(1.0, 2.0)]*7, [(2.0, 1.0), (2.0, 4.0)], [(nan, 1.0), (2.0, 4.0)],
                  [(True, 1.0), (2.0, 4.0)], [(1.0, 2.0, 3.0), (2.0, 4.0)], [(1.0,), (2.0, 4.0)],
                  [(1e7, 1e7), (2.0, 4.0)], "ab", None, 3.0, [1.0, 2.0], [("1", 2.0), (2.0, 4.0)]]
    bad_draws = [[], [0.25], [0.25, 0.5, 0.75], [1.01, 0.5], [-0.01, 0.5], [nan, 0.5],
                 [inf, 0.5], [True, 0.5], ["0.5", 0.5], None, 0.5, "ab"]
    bad_mode = ["Uniform", "gauss", "", None, 1, True, ["uniform"]]
    signatures = [
        ("simulate", simulate, ("a", "b", "y0", "u"), (0.5, 2.0, 1.0, good_u),
         {"a": bad_par, "b": bad_par, "y0": bad_y0, "u": bad_sim_u}),
        ("normal_equations", normal_equations, ("y", "u"), (good_y, good_u),
         {"y": bad_y, "u": bad_u}),
        ("condition_number", condition_number, ("G",), ([[2.0, 1.0], [1.0, 2.0]],),
         {"G": bad_G}),
        ("identifiability", identifiability, ("y", "u"), (good_y, good_u),
         {"y": bad_y, "u": bad_u}),
        ("fit_first_order", fit_first_order, ("y", "u"), (good_y, good_u),
         {"y": bad_y, "u": bad_u}),
        ("residual_rms", residual_rms, ("a", "b", "y", "u"), (0.5, 1.0, good_y, good_u),
         {"a": bad_par, "b": bad_par, "y": bad_y, "u": bad_u}),
        ("heldout_check", heldout_check, ("a", "b", "y_test", "u_test", "tol"),
         (0.5, 1.0, good_y, good_u, 0.5),
         {"a": bad_par, "b": bad_par, "y_test": bad_y, "u_test": bad_u, "tol": bad_tol}),
        ("parameter_std", parameter_std, ("y", "u", "sigma"), (good_y, good_u, 0.5),
         {"y": bad_y, "u": bad_u, "sigma": bad_sigma}),
        ("randomize", randomize, ("ranges", "draws", "mode"), (ok_ranges, ok_draws, "uniform"),
         {"ranges": bad_ranges, "draws": bad_draws, "mode": bad_mode}),
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
    for title, function in (("normal_equations", normal_equations),
                            ("identifiability", identifiability),
                            ("fit_first_order", fit_first_order)):
        for label, y, u in (("n = 1 sample pair", [1.0, 2.0], [1.0]),
                            ("n = 51 sample pairs", [0.5]*52, [1.0]*51)):
            full = "invalid " + title + "(" + label + ")"
            calls[title] = calls.get(title, 0) + 1
            try:
                function(y, u)
            except ValueError:
                continue
            except NotImplementedError:
                missing.setdefault(title, []).append(full)
                continue
            except Exception as error:
                failures.append(full + ": raised " + type(error).__name__
                                + " instead of ValueError")
                continue
            failures.append(full + ": returned instead of raising ValueError")
    for label, ranges, draws in (("log with lo = 0", ((0.0, 1.0),), (0.5,)),
                                 ("log with lo < 0", ((-1.0, 1.0),), (0.5,))):
        full = "invalid randomize(" + label + ")"
        calls["randomize"] = calls.get("randomize", 0) + 1
        try:
            randomize(ranges, draws, "log")
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault("randomize", []).append(full)
            continue
        except Exception as error:
            failures.append(full + ": raised " + type(error).__name__ + " instead of ValueError")
            continue
        failures.append(full + ": returned instead of raising ValueError")
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
    print("CoreLab manual parameter-identification self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

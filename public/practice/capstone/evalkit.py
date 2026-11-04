"""corebot.evalkit: small standard-library helpers shared by the CoreBot Tidy acceptance tests.

Copy this file to ``src/corebot/evalkit.py`` in your capstone repository (``make_skeleton.sh``
creates the folder). Only the Python standard library is used; ``trace_hash`` accepts either
a ``.npz`` file (needs numpy, imported lazily) or any bytes-like/JSON-able object.

Functions
---------
wilson_interval, step_metrics, crc8, all_single_bit_flips_detected, nees_consistency,
chi2_ppf, paired_mcnemar, bootstrap_ci, trace_hash, load_episodes
"""
import hashlib
import json
import math
import random

__all__ = ["wilson_interval", "step_metrics", "crc8", "all_single_bit_flips_detected",
           "chi2_ppf", "nees_consistency", "paired_mcnemar", "bootstrap_ci",
           "trace_hash", "load_episodes"]


def wilson_interval(successes, n, z=1.96):
    """Wilson score interval (lo, hi) for a binomial proportion; z=1.96 is 95 %."""
    if n <= 0 or not 0 <= successes <= n:
        raise ValueError("need 0 <= successes <= n and n > 0")
    p = successes / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def step_metrics(t, y, target, band=0.02):
    """Return (settling_time, overshoot_fraction, steady_state_error_fraction).

    The step is applied at t[0]. Settling time is the time after which y stays inside
    +-band*|target|; overshoot is max(0, (max(y)-target)/|target|); the steady-state error
    uses the mean of the last 10 % of samples.
    """
    if len(t) != len(y) or len(t) < 10 or target == 0:
        raise ValueError("bad step data: need equal lengths, >= 10 samples, target != 0")
    overshoot = max(0.0, (max(y) - target) / abs(target))
    tail = y[int(0.9 * len(y)):]
    sse = abs(sum(tail) / len(tail) - target) / abs(target)
    settle = 0.0
    for i in range(len(y) - 1, -1, -1):
        if abs(y[i] - target) > band * abs(target):
            settle = t[min(i + 1, len(t) - 1)] - t[0]
            break
    return settle, overshoot, sse


def crc8(data, poly=0x07, init=0x00):
    """CRC-8 (polynomial 0x07, no reflection, no xorout); crc8(b"123456789") == 0xF4."""
    c = init
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c


def all_single_bit_flips_detected(frame_payload):
    """True if flipping any single bit of the payload changes its CRC-8."""
    good = crc8(frame_payload)
    for i in range(len(frame_payload)):
        for bit in range(8):
            bad = bytearray(frame_payload)
            bad[i] ^= 1 << bit
            if crc8(bytes(bad)) == good:
                return False
    return True


def _norm_ppf(p):
    """Inverse standard normal CDF (Acklam's rational approximation, rel. error ~1e-9)."""
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - lo:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def chi2_ppf(p, dof):
    """Chi-square quantile by the Wilson-Hilferty approximation (good to ~1 % for dof >= 2)."""
    if dof <= 0:
        raise ValueError("dof must be positive")
    k = 2.0 / (9.0 * dof)
    return dof * (1 - k + _norm_ppf(p) * math.sqrt(k)) ** 3


def nees_consistency(errors, covs, dof, alpha=0.05):
    """Fraction of NEES samples inside the two-sided (1-alpha) chi-square interval, and the mean NEES.

    errors: list of error vectors (length dof); covs: list of dof x dof covariance matrices
    (lists of lists). Returns (fraction_inside, mean_nees). A consistent filter has a mean
    near ``dof`` and a fraction near 1-alpha. Uses a small Gaussian-elimination solver.
    """
    if len(errors) != len(covs) or not errors:
        raise ValueError("errors and covs must be non-empty and equal in length")
    lo, hi = chi2_ppf(alpha / 2, dof), chi2_ppf(1 - alpha / 2, dof)
    vals = []
    for e, P in zip(errors, covs):
        x = _solve(P, e)
        vals.append(sum(a * b for a, b in zip(e, x)))
    inside = sum(1 for v in vals if lo <= v <= hi) / len(vals)
    return inside, sum(vals) / len(vals)


def _solve(A, b):
    n = len(b)
    M = [list(map(float, A[i])) + [float(b[i])] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-15:
            raise ValueError("covariance is singular")
        M[c], M[piv] = M[piv], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / M[r][r]
    return x


def paired_mcnemar(b, c):
    """Exact two-sided McNemar p-value for discordant pair counts b (A ok, B fail) and c (A fail, B ok)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_ci(values, n=2000, seed=0, alpha=0.05):
    """Percentile bootstrap CI of the mean: (lo, hi). Deterministic for a given seed."""
    if not values:
        raise ValueError("values must be non-empty")
    rng = random.Random(seed)
    m = len(values)
    means = sorted(sum(values[rng.randrange(m)] for _ in range(m)) / m for _ in range(n))
    return means[int(n * alpha / 2)], means[min(n - 1, int(n * (1 - alpha / 2)))]


def trace_hash(obj, decimals=9):
    """SHA-256 hex digest of a trace. obj: path to .npz (numpy needed), bytes, or JSON-able data.

    Floats are rounded to ``decimals`` so that the hash survives harmless last-bit noise.
    """
    h = hashlib.sha256()
    if isinstance(obj, (bytes, bytearray)):
        h.update(obj)
    elif isinstance(obj, str) and obj.endswith(".npz"):
        import numpy as np  # lazy: only needed for npz traces
        with np.load(obj) as z:
            for k in sorted(z.files):
                h.update(k.encode())
                h.update(np.round(z[k].astype(float), decimals).tobytes() if z[k].dtype.kind == "f" else z[k].tobytes())
    else:
        def r(x):
            if isinstance(x, float):
                return round(x, decimals)
            if isinstance(x, (list, tuple)):
                return [r(i) for i in x]
            if isinstance(x, dict):
                return {k: r(v) for k, v in x.items()}
            return x
        h.update(json.dumps(r(obj), sort_keys=True).encode())
    return h.hexdigest()


def load_episodes(path):
    """Read a JSON-lines file into a list of dicts (blank lines skipped)."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


if __name__ == "__main__":
    import os
    import tempfile
    assert crc8(b"123456789") == 0xF4
    lo, hi = wilson_interval(78, 100)
    assert abs(lo - 0.689) < 0.001 and abs(hi - 0.850) < 0.001, (lo, hi)
    assert wilson_interval(0, 10)[0] == 0.0 and wilson_interval(10, 10)[1] == 1.0
    t = [i * 0.01 for i in range(300)]
    y = [6 * (1 - math.exp(-x / 0.08)) for x in t]
    s, o, e = step_metrics(t, y, 6.0)
    assert 0.28 < s < 0.34 and o == 0.0 and e < 1e-6, (s, o, e)
    assert all_single_bit_flips_detected(bytes(range(12)))
    assert abs(chi2_ppf(0.95, 3) - 7.815) < 0.05 and abs(chi2_ppf(0.975, 3) - 9.348) < 0.1
    assert abs(chi2_ppf(0.025, 3) - 0.216) < 0.05
    rng = random.Random(1)
    errs = [[rng.gauss(0, 1), rng.gauss(0, 2), rng.gauss(0, 0.5)] for _ in range(2000)]
    P = [[1, 0, 0], [0, 4, 0], [0, 0, 0.25]]
    inside, mean = nees_consistency(errs, [P] * 2000, 3)
    assert 0.93 < inside < 0.97 and 2.8 < mean < 3.2, (inside, mean)
    over, mean2 = nees_consistency(errs, [[[x * 0.1 for x in row] for row in P]] * 2000, 3)
    assert mean2 > 20 and over < 0.2
    assert paired_mcnemar(0, 0) == 1.0 and abs(paired_mcnemar(1, 9) - 0.021484375) < 1e-9
    ci = bootstrap_ci([1, 0, 1, 1, 0, 1, 1, 1], seed=3)
    assert ci == bootstrap_ci([1, 0, 1, 1, 0, 1, 1, 1], seed=3) and 0 <= ci[0] <= ci[1] <= 1
    assert trace_hash({"a": [1.0000000001, 2]}) == trace_hash({"a": [1.0, 2]})
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "e.jsonl")
        with open(p, "w") as f:
            f.write('{"seed": 1, "success": true}\n\n{"seed": 2, "success": false}\n')
        assert [e["seed"] for e in load_episodes(p)] == [1, 2]
    print("evalkit self-test OK")

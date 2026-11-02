"""CoreLab Planar Jacobian and IK lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the four core functions below (solve_ik_numeric is OPTIONAL), then
run your edited file locally:
  Windows: py -3 L06-jacobian-ik.v1.py
  macOS/Linux: python3 L06-jacobian-ik.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared arm (the L02 convention): a planar 2R arm in the x-y plane, base at the
origin. q1 is the angle of link 1 from +x and q2 is the RELATIVE angle of link 2
from link 1, both in radians, counter-clockwise positive. Link lengths l1, l2
are in metres. fk below is GIVEN (do not edit): it returns the endpoint
    x = l1*cos(q1) + l2*cos(q1 + q2),   y = l1*sin(q1) + l2*sin(q1 + q2).
Only the endpoint POSITION is used here; tool orientation is not part of L06.

Contracts (all numbers finite int/float, never bool; bounds inclusive):
  jacobian(q1, q2, l1, l2) -> J, a 2x2 nested list/tuple
      J[i][j] = d(endpoint coordinate i)/d(q_j): rows are (x, y), columns are
      (q1, q2), so J[0][1] = dx/dq2. Units: metres per radian.
  jacobian_det(q1, q2, l1, l2) -> det(J), in m^2 per rad^2.
      det = 0 means the arm is singular: the two columns of J are parallel and
      some tip direction cannot be produced by any joint rates.
  tip_velocity(q1, q2, l1, l2, dq1, dq2) -> (vx, vy) = J*(dq1, dq2)
      Joint rates in rad/s, tip velocity in m/s.
  ik_branches(x, y, l1, l2, limits=None) -> list/tuple of (q1, q2) pairs
      Every configuration whose endpoint is (x, y) and that fits the limits:
      0, 1 or 2 pairs, in any order. Never a "nearest" pose.
      Reach rule (the same in both IK functions): with r = math.hypot(x, y),
      the target is reachable iff |l1 - l2| - 1e-9 <= r <= l1 + l2 + 1e-9.
      Unreachable -> return an empty list/tuple. Rounding can push a cosine a
      hair past +-1 (1.0000000000000002) on or near a boundary, so clamp EVERY
      cosine you pass to acos into [-1, 1] - cos(q2) and, if you use one, the
      shoulder-angle cosine of the base triangle; do not crash. Inside the
      1e-9 reach band cos(q2) can exceed 1 by more than rounding, so clamp it
      there too.
      Same configuration: two pairs whose angles BOTH agree within 1e-6 rad
      modulo 2*pi are one configuration (q2 = pi and q2 = -pi on the folded
      boundary; the two branches for a target on a reach boundary, or so near
      it that they agree within 1e-6 rad). List each configuration once.
      Joint limits: limits = ((lo1, hi1), (lo2, hi2)) restrict the ACTUAL joint
      values, with -2*pi <= lo <= hi <= 2*pi. An angle plus a whole number of
      turns (q + 2*pi*k) is the same configuration: report a configuration if
      some such representative lies inside the limits (1e-9 rad slack allowed
      at each end) and return that representative. With limits=None any
      representative with |q1|, |q2| <= 2*pi is fine.
      Base-singular target: x == 0 and y == 0 with |l1 - l2| <= 1e-9 is reached
      by q2 = pi with EVERY q1, so no finite list exists: raise ValueError
      (with or without limits). With |l1 - l2| > 1e-9 the base is unreachable.
      The self-check accepts a pair when its FK residual (distance from fk of
      the pair to the target) is at most 1e-8*max(1, l1 + l2) metres.
  solve_ik_numeric(x, y, l1, l2, q_init, limits, tol, max_iter)
          -> (status, q, residual, steps)                          OPTIONAL
      An iterative solver. Leave the starter (raising NotImplementedError) to
      skip it: the self-check then prints one note and does not count it as a
      failure only if it raises NotImplementedError on EVERY call; raising it
      on some calls is reported as a failure, and every check below applies.
      residual(q) = math.hypot(fx - x, fy - y) with
      (fx, fy) = fk(q1, q2, l1, l2); steps = update steps actually taken.
      limits is required here; q_init must lie inside it (inclusive).
      1. Reach rule fails -> ("unreachable", q_init, residual(q_init), 0)
         without iterating. Report "unreachable" ONLY in this case. The
         base-singular target passes the reach rule: do not raise, iterate.
      2. Otherwise start at q = q_init. Before every step, if residual(q) <= tol
         return ("converged", q, residual(q), steps). So a q_init that already
         meets tol comes back unchanged with steps = 0.
      3. Take at most max_iter steps. Keep every iterate inside the limits
         (clamp or project each update onto the box). If tol is still not met
         when the budget is used up (or your solver stops early because it
         cannot make progress) return ("not_converged", q, residual(q), steps)
         for the q you return.
      So for a reachable target the status is "converged" exactly when the
      returned residual is <= tol, the reported residual is the true FK
      residual of the returned q, and q is always inside the limits.
      "not_converged" is NOT a proof that the target is impossible: the
      limits may exclude every solution, the budget may be too small or the
      start may sit near a singular pose. A fixed iteration cap never
      certifies a reachable problem as impossible.
      Required: report "converged" on the self-check's declared solvable
      cases (reachable, an admissible solution within about 1.6 rad of q_init,
      max_iter >= 200), one of which starts close to the straight-arm singular
      pose. There a lightly damped or undamped step is huge and can throw q
      onto the limits, so bound each step: a damped least-squares step
          dq = J^T (J J^T + lam^2 I)^-1 (target - fk(q)),  lam about 1e-3..0.1 m,
      scaled down so that |dq| <= 0.5 rad (a trust region), then clamped to
      the limits, converges on these cases; so does a Newton step limited the
      same way, or a backtracking line search. Any method that meets the
      contract is accepted, including seeding from your own ik_branches.
      A 2x2 inverse is enough; no SVD is needed. The other extreme also fails:
      a large constant damping (lam of about 0.2 m or more here) or a
      first-order J^T gradient step converges far too slowly near a singular
      pose to reach tol = 1e-9 within the budget.
      steps and the path your iterates took are self-reported: the self-check
      verifies the returned q, residual, status and 0 <= steps <= max_iter,
      not how many steps you really took.
Bounds: |q1|, |q2| <= 2*pi; 0.01 <= l1, l2 <= 10; |dq1|, |dq2| <= 100;
|x|, |y| <= 25; limits as above (exactly two pairs, lo <= hi); q_init is a
length-2 list/tuple; 1e-12 <= tol <= 1; max_iter is an int (not bool or
float) with 0 <= max_iter <= 1000. Invalid inputs (wrong type or shape, bool,
NaN, infinity, out of bounds, q_init outside limits) raise ValueError.
status is one of the strings "converged", "not_converged", "unreachable";
steps is an int. Every other returned number is a finite int/float
(non-bool) in a list/tuple. Never mutate inputs (q_init, limits).
Tolerances (absolute): J entries 1e-9*max(1, l1 + l2); det
1e-8*max(1, (l1 + l2)**2); tip velocity 1e-9*max(1, (l1 + l2)*(|dq1| + |dq2|)).
An accurate numerical derivative can meet these, but derive J analytically:
the self-check compares your J with central differences of fk at
h = 1e-2, 1e-3 and 1e-4 rad, using the error bound (l1 + l2)*h*h/6 plus
rounding, so a careless finite difference is caught.

Pause before coding - write your predictions down first:
  1. Straight arm (q2 = 0): which tip direction is lost? Sketch both columns
     of J. What is det J? And for the folded arm (q2 = pi)?
  2. Why does det J not depend on q1? What does its sign tell you?
  3. At a straight arm, can joint rates move the tip along the arm? What do
     they do to the tip velocity instead?
  4. How many IK solutions for a target inside the annulus, on its outer
     circle, on its inner circle, in the hole, and at the base when l1 == l2?
  5. q1 limits [4.5, 6.2] rad and an atan2 answer of -1.0 rad: admissible?
  6. A numeric solver stops after max_iter with a large residual. What can
     you conclude, and what can you NOT conclude?
  7. Near a singular pose, what does an undamped Newton step do to |dq|?
     Why damp it or limit its length?
Self-check tolerances are per-case metres and radians, not physical accuracy.
Failure messages name the case and the kind of mismatch, never the expected
numbers. "your code raised X on a VALID input" means the case is inside the
contract and must return; "invalid f(name=...)" lines are the opposite: that
input must raise ValueError. A function still raising NotImplementedError is
reported once, not once per case.
This kit covers the 2x2 endpoint-position Jacobian of one declared planar arm
only: no 6D/spatial Jacobian, twist, product of exponentials, orientation IK,
redundancy, dynamics, trajectory or hardware interface.
Reflection: why does passing this 2R toy NOT validate IK or velocity control
on a real manipulator? (Think about calibration and joint offsets, link and
gear flex, backlash, encoder resolution, joint velocity and torque limits,
tool orientation, more joints and redundancy, self-collision and obstacles,
timing and delay, singularities met during motion, and safety stops.)
"""
import math


def fk(q1, q2, l1, l2):
    """GIVEN - do not edit. Endpoint (x, y) of the declared arm (L02 practises this)."""
    for value in (q1, q2, l1, l2):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("fk needs finite int/float values")
    if not (abs(q1) <= 2*math.pi and abs(q2) <= 2*math.pi
            and 0.01 <= l1 <= 10 and 0.01 <= l2 <= 10):
        raise ValueError("fk input out of bounds")
    return (l1*math.cos(q1) + l2*math.cos(q1 + q2),
            l1*math.sin(q1) + l2*math.sin(q1 + q2))


def jacobian(q1, q2, l1, l2):
    raise NotImplementedError("Differentiate each fk coordinate by q1 and by q2; rows x, y")


def jacobian_det(q1, q2, l1, l2):
    raise NotImplementedError("Simplify det J by hand first; where is it zero?")


def tip_velocity(q1, q2, l1, l2, dq1, dq2):
    raise NotImplementedError("Multiply J by the joint-rate column")


def ik_branches(x, y, l1, l2, limits=None):
    raise NotImplementedError("Reach rule first, then both elbow branches, then limits modulo 2*pi")


def solve_ik_numeric(x, y, l1, l2, q_init, limits, tol, max_iter):
    raise NotImplementedError("Reach rule, residual check before every step, bounded damped steps")


# ---- SPOILER BELOW: _jacobian_ref and _configurations are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _fk_ref(a, b, c, d):
    """Independent scalar expansion (angle-sum identities), not a call to fk."""
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    return (c*ca + d*(ca*cb - sa*sb), c*sa + d*(sa*cb + ca*sb))


def _jacobian_ref(a, b, c, d):
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    cab, sab = ca*cb - sa*sb, sa*cb + ca*sb
    return ((-c*sa - d*sab, -d*sab), (c*ca + d*cab, d*cab))


def _wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def _same(p, q):
    return abs(_wrap(p[0] - q[0])) <= 1e-6 and abs(_wrap(p[1] - q[1])) <= 1e-6


def _reachable(x, y, l1, l2):
    r = math.hypot(x, y)
    return abs(l1 - l2) - 1e-9 <= r <= l1 + l2 + 1e-9


def _configurations(x, y, l1, l2):
    """Author reference: law of cosines plus atan2, duplicates collapsed."""
    if not _reachable(x, y, l1, l2):
        return []
    c2 = max(-1.0, min(1.0, (x*x + y*y - l1*l1 - l2*l2)/(2*l1*l2)))
    found = []
    for q2 in (math.acos(c2), -math.acos(c2)):
        q1 = math.atan2(y, x) - math.atan2(l2*math.sin(q2), l1 + l2*math.cos(q2))
        if not any(_same((q1, q2), p) for p in found):
            found.append((q1, q2))
    return found


def _admissible(angle, low, high, slack):
    return any(low - slack <= angle + 2*math.pi*k <= high + slack for k in range(-3, 4))


def _residual(q, x, y, l1, l2):
    fx, fy = _fk_ref(q[0], q[1], l1, l2)
    return math.hypot(fx - x, fy - y)


_P = math.pi
_FULL = ((-_P, _P), (-_P, _P))
# jacobian(q1, q2, l1, l2): "hand" answers derived on paper; "formula" cases
# are compared with _jacobian_ref AND central differences; "difference" cases
# only with central differences of an independent fk expansion.
_J_CASES = [
    ((0, 0, 2, 1), "hand", ((0, 0), (3, 1))),
    ((_P/2, 0.0, 2.0, 1.0), "hand", ((-3.0, -1.0), (0.0, 0.0))),
    ((_P/2, -_P/2, 2.0, 1.0), "hand", ((-2.0, 0.0), (1.0, 1.0))),
    ((_P, _P, 2.0, 1.0), "hand", ((0.0, 0.0), (-1.0, 1.0))),
    ((-1.2, 2.2, 0.7, 1.3), "formula", None),
    ((5.9, -6.1, 10.0, 10.0), "formula", None),
    ((0.7, 1e-06, 2.0, 1.0), "difference", None),
    ((-2.3, 3.0, 0.5, 1.5), "difference", None),
]
# jacobian_det(q1, q2, l1, l2): hand answers, None = l1*l2*sin(q2) from the
# reference expansion.
_DET_CASES = [
    ((0.3, 0.0, 2.0, 1.0), 0.0),
    ((1.0, _P, 2.0, 1.0), 0.0),
    ((1.0, _P/2, 2.0, 1.0), 2.0),
    ((-0.4, -_P/2, 0.7, 1.3), -0.91),
    ((0.2, 1e-06, 2.0, 1.0), None),
]
# tip_velocity(q1, q2, l1, l2, dq1, dq2): hand answers, None = reference J*dq
# plus a directional central difference of fk.
_TIP_CASES = [
    ((0, 0, 2, 1, 1, 0), (0, 3)),
    ((_P/2, 0.0, 2.0, 1.0, 0.5, -1.0), (-0.5, 0.0)),
    ((0.0, _P/2, 2.0, 1.0, 1.0, 1.0), (-2.0, 2.0)),
    ((0.4, 1.1, 0.7, 1.3, -2.0, 3.5), None),
    ((-3.0, -2.0, 4.0, 2.5, 50.0, -100.0), None),
]
# ik_branches(x, y, l1, l2[, limits]) -> number of distinct admissible
# configurations. Pairs are judged by FK residual, limits and distinctness.
_IK_CASES = [
    ((0.4, -0.9, 0.7, 1.3), 2),
    ((2.9999999999, 0.0, 2.0, 1.0), 2),
    ((3.0, 0.0, 2.0, 1.0), 1),
    ((1.1, 2.791057147390573, 2.0, 1.0), 1),
    ((0.7, 2.917190429162964, 2.0, 1.0), 1),
    ((-1.0, 0.0, 2.0, 1.0), 1),
    ((1.0, 0.0, 2.0, 1.0, ((-_P, _P), (-_P, 0.0))), 1),
    ((3.5, 0.0, 2.0, 1.0), 0),
    ((0.5, 0.0, 2.0, 1.0), 0),
    ((0.0, 0.0, 1.0, 1.000000002), 0),
    ((3.00000005, 0.0, 2.0, 1.0), 0),
    ((1.2, 1.9, 1.5, 1.0, ((-_P, _P), (0.0, _P))), 1),
    ((1.0, 2.0, 2.0, 1.0, ((-_P, _P), (0.2, _P/2 - 1e-05))), 0),
    ((0.1, -1.75, 1.0, 1.0, ((4.5, 6.2), (-_P, _P))), 1),
    ((0.1, 1.75, 1.0, 1.0, ((-6.2, -4.5), (-_P, _P))), 1),
    ((1.0, 2.0, 2.0, 1.0, ((-2*_P, 2*_P), (-2*_P, 2*_P))), 2),
    ((1.88660085511399, 1.33448767005344, 1.5, 1.0, ((0.3, 1.0), (0.8, 2.0))), 1),
    ((0.001, 0.0, 1.0, 1.0), 2),
]
# solve_ik_numeric(x, y, l1, l2, q_init, limits, tol, max_iter):
# "solve" must converge; "stay" starts on a solution (unchanged, 0 steps);
# "blocked" is reachable but every solution violates the limits; "honest"
# accepts either reachable status if it is consistent; "zero" has no step
# budget; "unreachable" fails the reach rule.
_NUM_CASES = [
    ("solve", (1.2, 1.9, 1.5, 1.0, (0.3, 1.0), _FULL, 1e-09, 200)),
    ("solve", (0.4, -0.9, 0.7, 1.3, (0.3, -2.0), ((-_P, _P), (-_P, -0.05)), 1e-09, 200)),
    ("solve", (1.0, 1.0, 1.0, 1.0, (0.2, 0.01), ((-_P, _P), (0.0, _P)), 1e-09, 200)),
    ("solve", (0.1, -1.75, 1.0, 1.0, (5.0, -0.8), ((4.5, 6.2), (-_P, _P)), 1e-10, 200)),
    ("solve", (-6.0, 8.0, 10.0, 5.0, (1.5, 0.8), _FULL, 1e-09, 200)),
    ("solve", (2.999, 0.0, 2.0, 1.0, (0.1, 0.3), _FULL, 1e-09, 500)),
    ("stay", (1.0, 1.0, 1.0, 1.0, (0.0, _P/2), _FULL, 1e-09, 200)),
    ("stay", (3, 0, 2, 1, (0, 0), _FULL, 1e-12, 50)),
    ("blocked", (1.0, 2.0, 2.0, 1.0, (0.5, 0.3), ((-_P, _P), (0.0, 0.3)), 1e-09, 200)),
    ("honest", (-1.5, 1.0, 2.0, 1.0, (0.3, 0.3), _FULL, 1e-12, 1)),
    ("honest", (0.0, 0.0, 1.0, 1.0, (0.3, 2.5), _FULL, 1e-09, 200)),
    ("zero", (1.2, 1.9, 1.5, 1.0, (0.3, 1.0), _FULL, 1e-09, 0)),
    ("unreachable", (3.0001, 0.0, 2.0, 1.0, (0.1, 0.1), _FULL, 0.001, 200)),
    ("unreachable", (0.2, 0.1, 2.0, 1.0, (0.5, 2.5), _FULL, 1e-09, 200)),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return (text + ": over-strict validation, or a math domain error such as"
                " acos(1.0000000000000002) from an unclamped cosine?)")
    return text + ")"


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    Optional parts that were not attempted are reported in `notes`, not as failures.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, function, args):
        """Call once; (True, result) or (False, None) after recording the problem."""
        calls[name] = calls.get(name, 0) + 1
        try:
            return True, function(*args)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
        except Exception as error:
            failures.append(label + ": " + _raised(error))
        return False, None

    def run(label, function, args, compare):
        ok, got = attempt(label.split(" ")[0], label, function, args)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def close(got, want, name, tolerance):
        if not abs(got - want) <= tolerance:
            raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")

    def matrix(got):
        if not (isinstance(got, (list, tuple)) and len(got) == 2
                and all(_vector(row, 2) for row in got)):
            raise _Mismatch("output must be a 2x2 nested list/tuple of finite int/float")

    names = (("dx/dq1", "dx/dq2"), ("dy/dq1", "dy/dq2"))

    def differences(got, q1, q2, l1, l2):
        """Central differences of the independent fk expansion, columns q1 and q2."""
        for h in (1e-2, 1e-3, 1e-4):
            bound = (l1 + l2)*(h*h/6 + 1e-15/h) + 1e-15
            for j in range(2):
                dq = (h, 0) if j == 0 else (0, h)
                plus = _fk_ref(q1 + dq[0], q2 + dq[1], l1, l2)
                minus = _fk_ref(q1 - dq[0], q2 - dq[1], l1, l2)
                for i in range(2):
                    slope = (plus[i] - minus[i])/(2*h)
                    if not abs(got[i][j] - slope) <= bound:
                        raise _Mismatch(names[i][j] + " disagrees with a central difference"
                                        " of fk at h = " + repr(h))

    for i, (args, mode, want) in enumerate(_J_CASES):
        def compare(got, args=args, mode=mode, want=want):
            matrix(got)
            tolerance = 1e-9*max(1, args[2] + args[3])
            if mode != "difference":
                want = want if mode == "hand" else _jacobian_ref(*args)
                for r in range(2):
                    for c in range(2):
                        close(got[r][c], want[r][c], "J entry " + names[r][c], tolerance)
            if mode != "hand":
                differences(got, *args)
        run("jacobian " + str(i) + " (" + mode + ")", jacobian, args, compare)

    for i, (args, want) in enumerate(_DET_CASES):
        def compare(got, args=args, want=want):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            if want is None:
                (a, b), (c, d) = _jacobian_ref(*args)
                want = a*d - b*c
            close(got, want, "det J", 1e-8*max(1, (args[2] + args[3])**2))
        run("jacobian_det " + str(i), jacobian_det, args, compare)

    for i, (args, want) in enumerate(_TIP_CASES):
        def compare(got, args=args, want=want):
            if not _vector(got, 2):
                raise _Mismatch("output must be a length-2 list/tuple (vx, vy) of finite int/float")
            q1, q2, l1, l2, dq1, dq2 = args
            tolerance = 1e-9*max(1, (l1 + l2)*(abs(dq1) + abs(dq2)))
            if want is None:
                J = _jacobian_ref(q1, q2, l1, l2)
                want = (J[0][0]*dq1 + J[0][1]*dq2, J[1][0]*dq1 + J[1][1]*dq2)
                speed = abs(dq1) + abs(dq2)
                h = 1e-4/speed
                plus = _fk_ref(q1 + h*dq1, q2 + h*dq2, l1, l2)
                minus = _fk_ref(q1 - h*dq1, q2 - h*dq2, l1, l2)
                bound = (l1 + l2)*speed*(1e-8/6 + 1e-11) + 1e-15
                for k, name in enumerate(("vx", "vy")):
                    if not abs(got[k] - (plus[k] - minus[k])/(2*h)) <= bound:
                        raise _Mismatch(name + " disagrees with a directional central"
                                        " difference of fk")
            close(got[0], want[0], "vx", tolerance)
            close(got[1], want[1], "vy", tolerance)
        run("tip_velocity " + str(i), tip_velocity, args, compare)

    def inside(q, limits, slack):
        if limits is None:
            return abs(q[0]) <= 2*math.pi + slack and abs(q[1]) <= 2*math.pi + slack
        return all(limits[k][0] - slack <= q[k] <= limits[k][1] + slack for k in range(2))

    for i, (args, count) in enumerate(_IK_CASES):
        x, y, l1, l2 = args[:4]
        limits = args[4] if len(args) > 4 else None
        if limits is not None:  # lists (mutation is detectable) or the tuples as given
            call = args[:4] + ((_fresh(limits) if i % 2 else limits),)
        else:
            call = args[:4]

        def compare(got, x=x, y=y, l1=l1, l2=l2, limits=limits, call=call, count=count):
            if len(call) > 4 and _fresh(call[4]) != _fresh(limits):
                raise _Mismatch("input limits were mutated")
            if not (isinstance(got, (list, tuple)) and len(got) <= 2
                    and all(_vector(pair, 2) for pair in got)):
                raise _Mismatch("output must be a list/tuple of at most two length-2"
                                " (q1, q2) pairs of finite int/float")
            for k, pair in enumerate(got):
                if not inside(pair, limits, 1e-9):
                    raise _Mismatch("pair " + str(k) + " is outside the joint limits"
                                    + (" (|q| <= 2*pi)" if limits is None else
                                       " (return the representative inside them)"))
                if _residual(pair, x, y, l1, l2) > 1e-8*max(1, l1 + l2):
                    raise _Mismatch("pair " + str(k) + " misses the target (FK residual"
                                    " too large; never return a nearest pose)")
            if len(got) == 2 and _same(got[0], got[1]):
                raise _Mismatch("the same configuration is listed twice (angles agree"
                                " within 1e-6 rad modulo 2*pi)")
            if len(got) != count:
                raise _Mismatch("number of distinct admissible configurations is wrong")
        run("ik_branches " + str(i), ik_branches, call, compare)

    statuses = ("converged", "not_converged", "unreachable")
    for i, (kind, args) in enumerate(_NUM_CASES):
        x, y, l1, l2, q_init, limits, tol, max_iter = args
        call = args[:4] + ((_fresh(q_init), _fresh(limits)) if i % 2 == 0
                           else (q_init, limits)) + args[6:]

        def compare(got, kind=kind, x=x, y=y, l1=l1, l2=l2, q_init=q_init,
                    limits=limits, tol=tol, max_iter=max_iter, call=call):
            if _fresh(call[4]) != _fresh(q_init) or _fresh(call[5]) != _fresh(limits):
                raise _Mismatch("input q_init or limits was mutated")
            if not (isinstance(got, (list, tuple)) and len(got) == 4
                    and got[0] in statuses and type(got[0]) is str
                    and _vector(got[1], 2) and _real(got[2]) and got[2] >= 0
                    and type(got[3]) is int):
                raise _Mismatch("output must be (status string, length-2 q, finite"
                                " residual >= 0, int steps)")
            status, q, residual, steps = got
            if not 0 <= steps <= max_iter:
                raise _Mismatch("steps outside 0..max_iter")
            if not inside(q, limits, 1e-12):
                raise _Mismatch("returned q is outside the joint limits")
            true = _residual(q, x, y, l1, l2)
            if not abs(residual - true) <= 1e-12 + 1e-9*true:
                raise _Mismatch("reported residual is not the FK residual of the returned q")
            if kind == "unreachable":
                if status != "unreachable":
                    raise _Mismatch("target fails the reach rule but status is not"
                                    " 'unreachable'")
                if list(q) != list(q_init) or steps != 0:
                    raise _Mismatch("unreachable must return q_init unchanged with 0 steps")
                return
            if status == "unreachable":
                raise _Mismatch("'unreachable' reported for a target that passes the"
                                " reach rule (an iteration cap proves nothing)")
            if (status == "converged") != (true <= tol):
                raise _Mismatch("status does not match the residual: 'converged' exactly"
                                " when the returned residual is <= tol")
            if kind == "solve" and status != "converged":
                raise _Mismatch("did not converge on a declared solvable case (steps too"
                                " wild near a singular pose, or too timid: large constant"
                                " damping or J^T descent?)")
            if kind == "blocked" and status != "not_converged":
                raise _Mismatch("no admissible solution exists, so it cannot converge")
            if kind in ("stay", "zero") and (list(q) != list(q_init) or steps != 0):
                raise _Mismatch("q_init must come back unchanged with 0 steps"
                                + (" (it already meets tol: check before stepping)"
                                   if kind == "stay" else " (max_iter = 0)"))
            if kind == "stay" and status != "converged":
                raise _Mismatch("q_init already meets tol but status is not 'converged'")
        run("solve_ik_numeric " + str(i) + " (" + kind + ")", solve_ik_numeric, call, compare)

    nan, inf = float('nan'), float('inf')
    good_limits = [[-3.0, 3.0], [-3.0, 3.0]]
    signatures = [
        ("jacobian", jacobian, ("q1", "q2", "l1", "l2"), (0.3, 0.4, 2.0, 1.0)),
        ("jacobian_det", jacobian_det, ("q1", "q2", "l1", "l2"), (0.3, 0.4, 2.0, 1.0)),
        ("tip_velocity", tip_velocity, ("q1", "q2", "l1", "l2", "dq1", "dq2"),
         (0.3, 0.4, 2.0, 1.0, 1.0, -1.0)),
        ("ik_branches", ik_branches, ("x", "y", "l1", "l2", "limits"),
         (1.0, 2.0, 2.0, 1.0, good_limits)),
        ("solve_ik_numeric", solve_ik_numeric,
         ("x", "y", "l1", "l2", "q_init", "limits", "tol", "max_iter"),
         (1.0, 2.0, 2.0, 1.0, [0.5, 1.0], good_limits, 1e-9, 50)),
    ]
    angle = [nan, inf, -inf, True, 6.3, -6.3, "0", None]
    length = [0.0, -1.0, 0.009, 10.01, nan, inf, True, "1", None]
    target = [nan, inf, -inf, True, 25.01, -25.01, "1", None]
    bad = {
        "q1": angle, "q2": angle, "l1": length, "l2": length,
        "dq1": [nan, inf, True, 100.01, -100.01, "1", None],
        "dq2": [nan, inf, False, 100.01, -100.01, "1", None],
        "x": target, "y": target,
        "limits": ["abc", [[0.0, 1.0]], [[-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0]],
                   [[1.0, 0.0], [-1.0, 1.0]], [[-1.0, 1.0], [0.5, -0.5]],
                   [[-7.0, 1.0], [-1.0, 1.0]], [[-1.0, 1.0], [-1.0, 7.0]],
                   [[nan, 1.0], [-1.0, 1.0]], [[-1.0, inf], [-1.0, 1.0]],
                   [[True, 1.0], [-1.0, 1.0]], [[-1.0, 1.0, 2.0], [-1.0, 1.0]],
                   [[-1.0, "1"], [-1.0, 1.0]], [-1.0, 1.0], {0: 1.0}],
        "q_init": [[0.5], [0.5, 1.0, 0.0], [nan, 1.0], [0.5, inf], [True, 1.0],
                   [3.5, 1.0], [0.5, -3.5], "ab", None, {0: 0.5}],
        "tol": [0.0, -1e-9, 1e-13, 1.01, nan, inf, True, "1e-9", None],
        "max_iter": [-1, 1001, 50.0, True, nan, "50", None],
    }
    for title, function, names_, args in signatures:
        for slot, name in enumerate(names_):
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
    for label, args in (("base target with l1 == l2", (0.0, 0.0, 1.5, 1.5)),
                        ("base target with l1 == l2 and limits", (0, 0, 1, 1, good_limits)),
                        ("base target with |l1 - l2| = 5e-10", (0.0, 0.0, 1.0, 1.0000000005))):
        calls["ik_branches"] = calls.get("ik_branches", 0) + 1
        try:
            ik_branches(*args)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault("ik_branches", []).append("ik_branches " + label)
            continue
        except Exception as error:
            failures.append("ik_branches " + label + ": raised " + type(error).__name__
                            + " instead of ValueError (no finite answer list)")
            continue
        failures.append("ik_branches " + label + ": returned instead of raising ValueError"
                        " (every q1 works, so no finite answer list exists)")
    summary = []
    for name, labels in missing.items():
        if len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels)) + " of "
                           + str(calls[name]) + " checks (first: " + labels[0] + "); finish it")
        elif name == "solve_ik_numeric":
            if notes is not None:
                notes.append("optional: solve_ik_numeric not attempted (its "
                             + str(calls[name]) + " checks were skipped)")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError; "
                           + str(calls[name]) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    notes = []
    failures = self_check(notes)
    print("CoreLab manual planar Jacobian/IK self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

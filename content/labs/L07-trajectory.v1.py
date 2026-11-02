"""CoreLab Trajectory time-law lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the five functions below, then run your edited file locally:
  Windows: py -3 L07-trajectory.v1.py
  macOS/Linux: python3 L07-trajectory.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

One axis (a joint in rad, or a slide in m) must move a signed distance D from
rest to rest in ONE straight move. Time law: constant acceleration +A, then
(maybe) cruising at constant speed, then constant deceleration -A. Limits:
|v| <= vmax and |a| <= amax at every instant. Write d = |D|, A = amax.
  Triangular: d*A < vmax^2. The axis never reaches vmax. ta = sqrt(d/A),
              no cruise, peak speed A*ta, duration 2*ta.
  Trapezoidal: d*A >= vmax^2. ta = vmax/A, tc = d/vmax - vmax/A,
              duration 2*ta + tc. (At d*A == vmax^2, tc = 0: both formulas agree.)
Both ramps last the same time ta and cover the same distance. The sign of D
only flips the sign of v and a; the shape is identical. D == 0 means no motion.
The area under |v(t)| must equal d: that is the analytic segment check.

Contracts (all numbers finite int/float, never bool; bounds inclusive):
  Bounds: |distance| <= 1000 (0 allowed), 0.01 <= vmax <= 100,
  0.01 <= amax <= 1000, 0 <= t <= 1e6, 0 <= duration <= 1e6.
  Units: distance in m (or rad), vmax in m/s (rad/s), amax in m/s^2
  (rad/s^2), times in s. Every bound violation, bool, NaN, infinity or non-number
  raises ValueError. All arguments are numbers, so nothing is mutated.
  profile(distance, vmax, amax) -> (kind, t_acc, t_cruise, v_peak, duration)
      The minimum-time profile. kind is the string "none" (distance == 0),
      "triangular" or "trapezoidal". t_acc is the duration of EACH ramp,
      t_cruise the cruise time (0.0 when triangular), v_peak the SIGNED peak
      velocity (same sign as distance; 0.0 for "none"), duration the total
      time. Times are 0.0 for "none". Exactly on the boundary
      (|distance*amax - vmax^2| <= 1e-9*max(1, vmax^2)) either kind label is
      accepted because the numbers agree; elsewhere the label must be right.
  min_duration(distance, vmax, amax) -> float
      The shortest possible time (the profile's duration); 0.0 for distance 0.
  scaled_profile(distance, vmax, amax, duration) -> (kind, t_acc, t_cruise,
          v_peak, duration)
      A slower profile that takes exactly `duration`. The acceleration phases
      KEEP |a| = amax; the peak speed is lowered until the area under the
      speed curve equals |distance|: v*(duration - v/amax) = |distance|, the
      smaller root. kind is "trapezoidal" when t_cruise > 0 (at the exact
      boundary where t_cruise is about 0 either label is accepted),
      "none" for distance 0 (any duration, all phases 0.0, v_peak 0.0, the
      reported duration is the requested one).
      IMPOSSIBLE request: if duration < min_duration(...) - 1e-9*max(1, that
      minimum), return ("infeasible", 0.0, 0.0, 0.0, min_duration) - the last
      slot then reports the shortest possible time. Never silently exceed
      vmax or amax and never return a profile for an impossible request.
      A request inside that 1e-9 band is feasible and equals profile().
  sample(distance, vmax, amax, t, duration=None) -> (q, v, a)
      Position, velocity and acceleration at time t (from the start, at rest at
      q = 0, ending at q = distance). duration=None: the minimum-time profile;
      otherwise the scaled profile above. For t >= the total duration the axis
      holds: (distance, 0.0, 0.0). An infeasible duration raises ValueError
      (there is no profile to sample). a is +A*sign during the first ramp, 0 in
      the cruise and -A*sign in the last ramp; exactly AT a phase boundary a is
      ambiguous and is not checked (within 1e-6*max(1, duration)), but q and v
      are continuous everywhere and are always checked.
  sync_duration(d1, v1, a1, d2, v2, a2) -> float
      Shortest COMMON duration for two independent axes that must start and
      stop together (each axis has its own distance and limits): the larger of
      the two minimum durations. The faster axis is then slowed with
      scaled_profile; it never needs to wait.
Tolerances (absolute): times 1e-8*max(1, duration), position
1e-8*max(1, |distance|), velocity 1e-8*max(1, vmax), acceleration
1e-8*max(1, amax). The self-check also samples your sample() at the start, the
end and after the end (rest), across every phase boundary (continuity), and on a
grid (|v| <= vmax, |a| <= amax, no overshoot of the target, monotone motion).

Pause before coding - write your predictions down first:
  1. d = 8 m, vmax = 2 m/s, amax = 1 m/s^2. Triangular or trapezoidal? Phase
     times and total time? Now d = 2 m with vmax = 5 m/s.
  2. What happens to the velocity peak and the time if the SAME move is reversed
     (D negative)? If D = 0?
  3. Why does the triangular peak never reach vmax? What is the one number you
     compare to choose the type?
  4. A planner asks for 5 s but the minimum is 6 s. What do you return? Why is it
     wrong to "just run slower" or to exceed amax? If asked for 9 s, which of
     the two limits stays active?
  5. Two joints must finish together. Which joint sets the common time, and what
     must the other do? Can the common time ever be below either minimum?
  6. At the instant the cruise ends, is a continuous? Is v? Is q? Which of the
     three could a bug make jump?
Self-check tolerances are per-case numbers, not physical accuracy. Failure
messages name the case and the kind of mismatch, never the expected numbers.
"your code raised X on a VALID input" means the case is inside the contract and
must return; "invalid f(name=...)" lines are the opposite: that input must raise
ValueError. A function still raising NotImplementedError is reported once.
This kit covers one-axis rest-to-rest triangular/trapezoidal time laws and the
common-duration rule for independent axes: numerical only. No jerk limit
(S-curve), torque, dynamics, path geometry, Cartesian or multi-point
trajectory, collision check, controller tracking or robot execution.
Reflection: why does passing this toy NOT validate motion on a real robot? (Think
about jerk, which this profile makes infinite at every phase boundary, and the
mechanical excitation it causes; motor torque and current limits, gear and link
flex, payload and friction, speed limits that depend on configuration, controller
tracking error and sample time, coupling between joints, path geometry between
via points, and safety stops. Accelerating at amax is not the same as the motor
being able to do so.)
"""
import math


def profile(distance, vmax, amax):
    raise NotImplementedError("Compare distance*amax with vmax**2, then derive ta, tc, v_peak, duration")


def min_duration(distance, vmax, amax):
    raise NotImplementedError("Total time of the minimum-time profile; 0 for no motion")


def scaled_profile(distance, vmax, amax, duration):
    raise NotImplementedError("Keep amax, lower the peak speed: solve v*(T - v/amax) = |distance|; reject T below the minimum")


def sample(distance, vmax, amax, t, duration=None):
    raise NotImplementedError("Pick the phase containing t; integrate constant acceleration; hold after the end")


def sync_duration(d1, v1, a1, d2, v2, a2):
    raise NotImplementedError("The common time is the larger of the two minimum durations")


# ---- SPOILER BELOW: _ref_* functions are complete references, and the case ----
# ---- tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _ref_profile(distance, vmax, amax):
    d = abs(distance)
    if d == 0:
        return ("none", 0.0, 0.0, 0.0, 0.0)
    sign = 1.0 if distance > 0 else -1.0
    if d*amax < vmax*vmax:
        ta = math.sqrt(d/amax)
        return ("triangular", ta, 0.0, sign*amax*ta, 2*ta)
    ta = vmax/amax
    tc = d/vmax - ta
    return ("trapezoidal", ta, tc, sign*vmax, 2*ta + tc)


def _ref_scaled(distance, vmax, amax, duration):
    tmin = _ref_profile(distance, vmax, amax)[4]
    d = abs(distance)
    if d == 0:
        return ("none", 0.0, 0.0, 0.0, float(duration))
    if duration < tmin - 1e-9*max(1.0, tmin):
        return ("infeasible", 0.0, 0.0, 0.0, tmin)
    if duration <= tmin:
        return _ref_profile(distance, vmax, amax)
    sign = 1.0 if distance > 0 else -1.0
    root = math.sqrt(max(0.0, (amax*duration)**2 - 4*amax*d))
    v = 2*amax*d/(amax*duration + root)
    ta = v/amax
    return ("trapezoidal", ta, duration - 2*ta, sign*v, float(duration))


def _ref_sample(distance, vmax, amax, t, duration=None):
    kind, ta, tc, vp, total = (_ref_profile(distance, vmax, amax) if duration is None
                               else _ref_scaled(distance, vmax, amax, duration))
    if kind == "none" or t >= total:
        return (float(distance), 0.0, 0.0)
    a = vp/ta
    if t < ta:
        return (0.5*a*t*t, a*t, a)
    if t < ta + tc:
        return (0.5*vp*ta + vp*(t - ta), vp, 0.0)
    s = total - t
    return (distance - 0.5*a*s*s, a*s, -a)


def _kind_allowed(distance, vmax, amax):
    if distance == 0:
        return ("none",)
    gap = abs(distance)*amax - vmax*vmax
    band = 1e-9*max(1.0, vmax*vmax)
    if gap < -band:
        return ("triangular",)
    if gap > band:
        return ("trapezoidal",)
    return ("triangular", "trapezoidal")


# profile(distance, vmax, amax): hand = (t_acc, t_cruise, v_peak, duration) on
# paper, None = _ref_profile (kind label judged from distance*amax vs vmax^2).
_PROFILE_CASES = [
    ((8, 2, 1), (2, 2, 2, 6)),
    ((2, 5, 2), (1, 0, 2, 2)),
    ((-2, 5, 2), (1, 0, -2, 2)),
    ((0, 3, 1), (0, 0, 0, 0)),
    ((4, 2, 1), (2, 0, 2, 4)),
    ((-8.0, 2.0, 1.0), (2, 2, -2, 6)),
    ((3.9, 2.0, 1.0), None),
    ((4.1, 2.0, 1.0), None),
    ((4.0000000001, 2.0, 1.0), None),
    ((4.001, 2.0, 1.0), None),
    ((1e-06, 0.5, 0.1), None),
    ((123.456, 0.01, 0.01), None),
]
# min_duration(distance, vmax, amax): hand answers; None = reference.
_DUR_CASES = [
    ((8, 2, 1), 6),
    ((-8, 2, 1), 6),
    ((0, 1, 1), 0),
    ((1, 2, 1000), None),
    ((0.7, 1.3, 0.9), None),
]
# scaled_profile(distance, vmax, amax, duration): hand = (kind, t_acc,
# t_cruise, v_peak, duration) written on paper; None = reference.
_SCALED_CASES = [
    ((8, 2, 1, 9), ("trapezoidal", 1, 7, 1, 9)),
    ((-8, 2, 1, 9), ("trapezoidal", 1, 7, -1, 9)),
    ((4, 2, 1, 5), ("trapezoidal", 1, 3, 1, 5)),
    ((8, 2, 1, 5.5), ("infeasible", 0, 0, 0, 6)),
    ((2, 5, 2, 1.5), ("infeasible", 0, 0, 0, 2)),
    ((0, 2, 1, 3.5), ("none", 0, 0, 0, 3.5)),
    ((8, 2, 1, 5.9999999999), None),
    ((1.0, 1.0, 1.0, 1000.0), None),
    ((1, 2, 1, 1000000.0), None),
    ((1, 2, 1, 0), ("infeasible", 0, 0, 0, 2)),
    ((8, 2, 1, 5.999999), ("infeasible", 0, 0, 0, 6)),
    ((8, 2, 1, 6.000001), None),
]
# sample(distance, vmax, amax, t[, duration]): hand = (q, v, a) with a = None
# when t is a phase boundary; None = reference.
_SAMPLE_CASES = [
    ((8, 2, 1, 1), (0.5, 1, 1)),
    ((8, 2, 1, 5), (7.5, 1, -1)),
    ((8, 2, 1, 6), (8, 0, None)),
    ((8, 2, 1, 10), (8, 0, 0)),
    ((-2, 5, 2, 0.5), (-0.25, -1, -2)),
    ((8, 2, 1, 1000000.0), (8, 0, 0)),
    ((8, 2, 1, 0.5, 9), (0.125, 0.5, 1)),
    ((8, 2, 1, 4, 9), (3.5, 1, 0)),
    ((8, 2, 1, 8.5, 9), (7.875, 0.5, -1)),
    ((0, 1, 1, 0.3), (0, 0, 0)),
    ((0, 1, 1, 2.0, 4.0), (0, 0, 0)),
    ((0.7, 1.3, 0.9, 0.9, 1.9), None),
    ((-5.5, 3.0, 4.0, 1.3), None),
]
# Endpoint / continuity / bound checks: (distance, vmax, amax[, duration]).
_SHAPE_CASES = [
    (8, 2, 1),
    (-2, 5, 2),
    (-8, 2, 1, 9),
]
# sync_duration(d1, v1, a1, d2, v2, a2): hand answers; None = reference.
_SYNC_CASES = [
    ((8, 2, 1, 2, 5, 2), 6),
    ((-8, 2, 1, -2, 5, 2), 6),
    ((0, 1, 1, 4, 2, 1), 4),
    ((0, 1, 1, 0, 1, 1), 0),
    ((1000.0, 100.0, 1000.0, 0.5, 0.01, 0.01), None),
]
# (function name, args): every one must raise ValueError.
_INVALID = [
    ("profile", (True, 2, 1)), ("profile", (1, True, 1)), ("profile", (1, 2, True)),
    ("profile", (float("nan"), 2, 1)), ("profile", (float("inf"), 2, 1)),
    ("profile", (1001, 2, 1)), ("profile", (-1001, 2, 1)),
    ("profile", (1, 0, 1)), ("profile", (1, -2, 1)), ("profile", (1, 0.005, 1)),
    ("profile", (1, 101, 1)), ("profile", (1, 2, 0)), ("profile", (1, 2, -1)),
    ("profile", (1, 2, 0.005)), ("profile", (1, 2, 1001)), ("profile", ("1", 2, 1)),
    ("profile", (None, 2, 1)), ("profile", (1, float("nan"), 1)),
    ("profile", (1, 2, float("-inf"))),
    ("min_duration", (1001, 2, 1)), ("min_duration", (1, 0, 1)),
    ("min_duration", (1, 2, 0)), ("min_duration", (True, 2, 1)),
    ("min_duration", (1, float("nan"), 1)),
    ("scaled_profile", (1, 2, 1, -1)), ("scaled_profile", (1, 2, 1, 1000001)),
    ("scaled_profile", (1, 2, 1, float("nan"))), ("scaled_profile", (1, 2, 1, True)),
    ("scaled_profile", (1, 2, 1, "5")), ("scaled_profile", (1, 0, 1, 5)),
    ("scaled_profile", (1001, 2, 1, 5)), ("scaled_profile", (1, 2, 0, 5)),
    ("sample", (8, 2, 1, -0.1)), ("sample", (8, 2, 1, float("nan"))),
    ("sample", (8, 2, 1, True)), ("sample", (8, 2, 1, 1000001)),
    ("sample", (8, 2, 1, "1")), ("sample", (8, 2, 1, 1, -1)),
    ("sample", (8, 2, 1, 1, True)), ("sample", (8, 2, 1, 1, 5.0)),
    ("sample", (8, 2, 1, 1, float("inf"))), ("sample", (1001, 2, 1, 1)),
    ("sample", (8, 0, 1, 1)), ("sample", (8, 2, 0, 1)),
    ("sync_duration", (1, 2, 1, 1001, 2, 1)), ("sync_duration", (1, 2, 1, 1, 0, 1)),
    ("sync_duration", (1, 2, 1, 1, 2, 0)), ("sync_duration", (1, 0, 1, 1, 2, 1)),
    ("sync_duration", (True, 2, 1, 1, 2, 1)), ("sync_duration", (1, 2, 1, 1, 2, float("nan"))),
]


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation, or a bound that is too tight?)"
    return text + ")"


def _show(args):
    return "(" + ", ".join(repr(a) for a in args) + ")"


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    `notes` is accepted for symmetry with the other kits and is not used.
    """
    failures = []
    calls, missing = {}, {}
    functions = {"profile": profile, "min_duration": min_duration,
                 "scaled_profile": scaled_profile, "sample": sample,
                 "sync_duration": sync_duration}

    def attempt(name, label, function, args):
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
        except NotImplementedError:
            missing.setdefault(label.split(" ")[0], []).append(label)
        except ValueError as error:
            failures.append(label + ": " + _raised(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def close(got, want, name, tolerance):
        if not abs(got - want) <= tolerance:
            raise _Mismatch(name + " is wrong (tolerance " + repr(tolerance) + ")")

    def tuple_of(got, count, text):
        if not (isinstance(got, (list, tuple)) and len(got) == count):
            raise _Mismatch("output must be " + text)

    def tolerances(distance, vmax, amax, total):
        return (1e-8*max(1.0, total), 1e-8*max(1.0, abs(distance)),
                1e-8*max(1.0, vmax), 1e-8*max(1.0, amax))

    def phases(got, want, distance, vmax, amax, allowed):
        shape = "(kind string, t_acc, t_cruise, v_peak, duration) with finite int/float numbers"
        tuple_of(got, 5, shape)
        if not (type(got[0]) is str and all(_real(v) for v in got[1:])):
            raise _Mismatch("output must be " + shape)
        if got[0] not in allowed:
            raise _Mismatch("kind label is wrong")
        ttol = 1e-8*max(1.0, want[4])
        close(got[1], want[1], "t_acc", ttol)
        close(got[2], want[2], "t_cruise", ttol)
        close(got[3], want[3], "v_peak", 1e-8*max(1.0, vmax))
        close(got[4], want[4], "duration", ttol)

    for i, (args, hand) in enumerate(_PROFILE_CASES):
        def compare(got, args=args, hand=hand):
            want = ("", *hand) if hand is not None else _ref_profile(*args)
            phases(got, want, *args, _kind_allowed(*args))
        run("profile " + str(i) + " " + _show(args), profile, args, compare)

    for i, (args, hand) in enumerate(_DUR_CASES):
        def compare(got, args=args, hand=hand):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            want = hand if hand is not None else _ref_profile(*args)[4]
            close(got, want, "min_duration", 1e-8*max(1.0, want))
        run("min_duration " + str(i) + " " + _show(args), min_duration, args, compare)

    for i, (args, hand) in enumerate(_SCALED_CASES):
        def compare(got, args=args, hand=hand):
            want = hand if hand is not None else _ref_scaled(*args)
            if want[0] == "infeasible":
                tuple_of(got, 5, "(kind string, t_acc, t_cruise, v_peak, duration)")
                if got[0] != "infeasible":
                    raise _Mismatch("a request shorter than the minimum duration must be"
                                    " reported as impossible")
                if not (all(_real(v) for v in got[1:]) and got[1] == 0 and got[2] == 0
                        and got[3] == 0):
                    raise _Mismatch("an infeasible result must have zero phases and v_peak")
                close(got[4], want[4], "reported minimum duration", 1e-8*max(1.0, want[4]))
                return
            if want[0] == "none":
                allowed = ("none",)
            elif want[2] > 1e-6*max(1.0, want[4]):
                allowed = ("trapezoidal",)
            else:
                allowed = ("triangular", "trapezoidal")
            phases(got, want, args[0], args[1], args[2], allowed)
        run("scaled_profile " + str(i) + " " + _show(args), scaled_profile, args, compare)

    for i, (args, hand) in enumerate(_SAMPLE_CASES):
        def compare(got, args=args, hand=hand):
            tuple_of(got, 3, "(q, v, a), three finite int/float")
            if not all(_real(v) for v in got):
                raise _Mismatch("output must be (q, v, a), three finite int/float")
            distance, vmax, amax, t = args[:4]
            duration = args[4] if len(args) > 4 else None
            want = hand if hand is not None else _ref_sample(distance, vmax, amax, t, duration)
            total = _ref_profile(distance, vmax, amax)[4] if duration is None else duration
            ttol, qtol, vtol, atol = tolerances(distance, vmax, amax, total)
            close(got[0], want[0], "q", qtol)
            close(got[1], want[1], "v", vtol)
            _, ta, tc, _, end = (_ref_profile(distance, vmax, amax) if duration is None
                                 else _ref_scaled(distance, vmax, amax, duration))
            near = any(abs(t - b) <= 1e-6*max(1.0, end) for b in (0.0, ta, ta + tc, end))
            if want[2] is not None and not near:
                close(got[2], want[2], "a", atol)
        run("sample " + str(i) + " " + _show(args), sample, args, compare)

    for i, args in enumerate(_SHAPE_CASES):
        distance, vmax, amax = args[:3]
        duration = args[3] if len(args) > 3 else None
        _, ta, tc, _, end = (_ref_profile(distance, vmax, amax) if duration is None
                             else _ref_scaled(distance, vmax, amax, duration))
        ttol, qtol, vtol, atol = tolerances(distance, vmax, amax, end)
        sign = 1.0 if distance > 0 else -1.0

        def at(t, distance=distance, vmax=vmax, amax=amax, duration=duration):
            got = sample(distance, vmax, amax, t, duration)
            if not (isinstance(got, (list, tuple)) and len(got) == 3
                    and all(_real(v) for v in got)):
                raise _Mismatch("sample must return (q, v, a), three finite int/float")
            return got

        def compare(_, distance=distance, vmax=vmax, amax=amax, ta=ta, tc=tc, end=end,
                    qtol=qtol, vtol=vtol, atol=atol, sign=sign, at=at):
            start, finish = at(0.0), at(end)
            if abs(start[0]) > qtol or abs(start[1]) > vtol:
                raise _Mismatch("endpoint check: the move must start at q = 0 with v = 0")
            if abs(finish[0] - distance) > qtol or abs(finish[1]) > vtol:
                raise _Mismatch("endpoint check: the move must end at q = distance with v = 0")
            for late in (end + 1.0, end + 100.0):
                after = at(late)
                if abs(after[0] - distance) > qtol or abs(after[1]) > vtol or abs(after[2]) > atol:
                    raise _Mismatch("after the end the axis must hold (distance, 0, 0)")
            e = 1e-6*max(1.0, end)
            for b in {ta, ta + tc}:
                before, after = at(b - e), at(b + e)
                if (abs(after[0] - before[0]) > 3*vmax*e + qtol
                        or abs(after[1] - before[1]) > 3*amax*e + vtol):
                    raise _Mismatch("continuity check: q or v jumps across a phase boundary")
            previous = 0.0
            for k in range(1, 61):
                q, v, a = at(end*k/60)
                if abs(v) > vmax + vtol:
                    raise _Mismatch("bound check: |v| exceeds vmax")
                if abs(a) > amax + atol:
                    raise _Mismatch("bound check: |a| exceeds amax")
                if sign*q > abs(distance) + qtol or sign*q < -qtol:
                    raise _Mismatch("bound check: q leaves the interval between start and target")
                if sign*(q - previous) < -qtol:
                    raise _Mismatch("monotone check: the axis moves backwards")
                previous = q
        run("sample shape " + str(i) + " " + _show(args), lambda *a: None, (), compare)

    for i, (args, hand) in enumerate(_SYNC_CASES):
        def compare(got, args=args, hand=hand):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            want = hand if hand is not None else max(_ref_profile(*args[:3])[4],
                                                      _ref_profile(*args[3:])[4])
            close(got, want, "common duration", 1e-8*max(1.0, want))
        run("sync_duration " + str(i) + " " + _show(args), sync_duration, args, compare)

    for i, (name, args) in enumerate(_INVALID):
        label = "invalid " + name + "(" + _show(args)[1:-1] + ")"
        calls[name] = calls.get(name, 0) + 1
        try:
            functions[name](*args)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            continue
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__ + " instead of ValueError")
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
    notes = []
    failures = self_check(notes)
    print("CoreLab manual trajectory time-law self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

"""CoreLab Parallel-jaw friction grasp lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the five functions below, then run your edited file locally:
  Windows: py -3 L18-grasp.v1.py
  macOS/Linux: python3 L18-grasp.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared toy model (analytic, quasi-static; not a physics engine or a gripper):
two flat parallel pads squeeze a rigid box of mass m (kg) from opposite sides.
Each pad presses with normal force n (N); both pads have the same Coulomb
friction coefficient mu (dimensionless). A pad can carry a tangential force of
at most mu*n (the friction cone |ft| <= mu*fn). The box is lifted straight up
with acceleration a (m/s^2, positive up). Gravity g = 9.81 m/s^2 exactly.
Newton for the box: total friction upward F must satisfy F = m*(g + a), and the
two pads together can give at most 2*mu*n. So the grasp HOLDS iff
    2*mu*n >= m*(g + a)          (equality holds: the cone is closed).
Contracts (all numbers finite int/float, never bool; bounds inclusive):
  safety_factor(m, mu, n, a) -> float
      S = 2*mu*n / (m*(g + a)); S >= 1 means the grasp holds. S = 0 when n = 0.
  min_squeeze(m, mu, a) -> float
      the smallest per-pad normal force n (N) that just holds: m*(g + a)/(2*mu).
  max_lift_accel(m, mu, n) -> float
      the largest upward acceleration that still holds: 2*mu*n/m - g (m/s^2).
      It may be negative: the pads cannot even hold the box still.
  in_friction_cone(fn, ft, mu) -> bool
      True iff the pad force (normal fn, tangential ft, both in N, ft of either
      sign) lies inside the closed cone: fn >= 0 and |ft| <= mu*fn. A pad can
      only push (fn < 0 is outside the cone); fn = 0 with ft = 0 is inside.
      Compare exactly or with a relative tolerance of at most 1e-9.
  retention_events(samples, mu, contact, window) -> list of (index, name)
      samples is a list/tuple of 1 to 1000 samples (cmd, fn, ft): cmd is the int
      0 (gripper commanded closed) or 1 (commanded open); fn >= 0 is the
      measured normal force per pad and ft the measured tangential force per
      pad, both in N. contact is the force threshold in N, window the number
      of consecutive closed samples to wait before calling the grasp empty (an
      int). A synthetic trace, one reading per sample, not a recording.
      Four monitors run independently over the samples, in order; a "closed
      run" is a maximal block of consecutive cmd == 0 samples and c is the
      1-based position of a sample inside its run (c resets at every open).
      * contact monitor (cmd == 0 only): while not in contact, fn >= contact
        emits "contact" and starts the contact state; while in contact,
        fn < contact emits "lost" (the grasp was lost with no open command)
        and ends the contact state. After "lost" a later contact is new.
      * object monitor (cmd == 0, in contact after the contact monitor, and
        not on the "lost" sample): when |ft| > mu*fn (strictly, the closed cone
        is not a slip) it emits "slip" once, then stays silent until a sample
        back inside the cone (|ft| <= mu*fn) re-arms it. A contact sample that
        starts outside the cone emits "contact" and then "slip" at the same
        index.
      * empty monitor (cmd == 0): if no contact happened since the closed run
        began, the sample is not in contact and c == window, emit "empty" (once
        per run). A contact at that same sample wins and no "empty" is emitted.
      * release monitor: the first sample of an open run (cmd == 1) emits
        "release" if the contact state was on, and then clears the contact and
        slip states. While cmd == 1 the monitors emit nothing and readings are
        ignored.
      The cone comparison |ft| > mu*fn is strict and exact: the kit's boundary cases
      use exactly representable values; an implementation may allow a relative
      tolerance of at most 1e-9 (as in_friction_cone), so ft = 3.6 with mu = 0.6
      and fn = 6 is on the edge, not a slip. Events are returned in sample order; events at one index appear in the
      order contact/lost, slip, empty, release. Return a list or tuple of
      2-element list/tuples (int index, str name); an empty trace of events is
      an empty list.
Bounds: 0 < m <= 100 (kg); 0.01 <= mu <= 5; 0 <= n <= 10000 (N); -5 <= a <= 50
(so g + a > 0); fn, ft in cone checks: |value| <= 1000 (fn in the trace: 0 to
1000); 0 < contact <= 1000; window an int (not bool or float) 1..1000; samples
as above, cmd exactly the int 0 or 1. Invalid inputs (wrong type or shape,
bool, NaN, infinity, out of bounds) raise ValueError. Never mutate inputs.
Tolerance for floats: relative 1e-9 (absolute 1e-9 near zero).

Pause before coding - write your predictions down first:
  1. A 0.5 kg box, mu = 0.5, held still (a = 0): what per-pad force is needed?
     What if the pads are wet and mu halves?
  2. You lift at a = 5 m/s^2 instead: does the needed squeeze rise by exactly
     the factor (g + a)/g? And what safety factor do you get if you keep the
     old squeeze?
  3. A tangential force of exactly mu*fn: slip or not? What would a rounded
     sensor reading do to your answer?
  4. A trace where fn never reaches the contact threshold while closing:
     which event, and why is it not the same as "lost"?
  5. A slip that starts, then fn rises so the force is back inside the cone:
     what should a second excursion do?
  6. Which event do you expect if the box mass doubles mid-lift with the same
     squeeze: contact, slip or lost?
Self-check tolerances are per-case, not physical accuracy. Failure messages name
the case and the kind of mismatch, never the expected numbers. "your code
raised X" means your function raised on a VALID input. A function that still
raises NotImplementedError is reported once, not once per case.
This does not implement a physics-engine contact simulation, soft or deformable
contacts, torsional or rolling friction, multi-finger grasps, grasp planning, a
force/torque sensor model, a gripper controller, or any hardware interface; the
transport and object-pose monitors of a real pick-and-place are not here.
Reflection: why does passing this analytic toy NOT validate a real grasp? Think
about pad compliance and contact patches, friction that is not Coulomb (speed
and pressure dependence, wet or dusty surfaces), a mass and centre of mass that
are not known, off-centre loads that twist the box, force-sensor noise, offset
and delay, a gripper that needs time to build force, and what a threshold
observer cannot see.
"""
import math


def safety_factor(m, mu, n, a):
    raise NotImplementedError("S = 2*mu*n / (m*(g + a)) with g = 9.81")


def min_squeeze(m, mu, a):
    raise NotImplementedError("Solve 2*mu*n = m*(g + a) for n")


def max_lift_accel(m, mu, n):
    raise NotImplementedError("Solve 2*mu*n = m*(g + a) for a")


def in_friction_cone(fn, ft, mu):
    raise NotImplementedError("Closed cone: fn >= 0 and |ft| <= mu*fn")


def retention_events(samples, mu, contact, window):
    raise NotImplementedError("Run the contact, object, empty and release monitors over the samples")


# ---- SPOILER BELOW: the _ref_* functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----

_G = 9.81


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _tol(want, base=1e-9):
    return base*max(1.0, abs(want))


def _ref_factor(m, mu, n, a):
    return 2*mu*n/(m*(_G + a))


def _ref_squeeze(m, mu, a):
    return m*(_G + a)/(2*mu)


def _ref_accel(m, mu, n):
    return 2*mu*n/m - _G


def _ref_cone(fn, ft, mu):
    return fn >= 0 and abs(ft) <= mu*fn


def _ref_events(samples, mu, contact, window):
    events, on, slipping, c, had, was_open = [], False, False, 0, False, False
    for k, (cmd, fn, ft) in enumerate(samples):
        if cmd == 1:
            if not was_open and on:
                events.append((k, "release"))
            on = slipping = had = False
            c, was_open = 0, True
            continue
        was_open = False
        c += 1
        lost = False
        if not on and fn >= contact:
            events.append((k, "contact"))
            on, had = True, True
        elif on and fn < contact:
            events.append((k, "lost"))
            on = slipping = False
            lost = True
        if on and not lost:
            if abs(ft) > mu*fn:
                if not slipping:
                    events.append((k, "slip"))
                slipping = True
            else:
                slipping = False
        if not on and not had and c == window:
            events.append((k, "empty"))
    return events


# (m, mu, n, a) -> S: hand-derived where the numbers are clean.
_FACTOR_CASES = [
    ((2.0, 0.4, 25.0, 0.19), 1.0),
    ((1.0, 0.5, 4.905, 0.0), 0.5),
    ((0.5, 0.8, 10.0, 5.19), 2.1333333333333333),
    ((3.0, 0.25, 0.0, 0.0), 0.0),
    ((10.0, 0.3, 100.0, -4.81), 1.2),
    ((1, 1, 10, 0.19), 2.0),
    ((0.2, 0.6, 2.0, 2.0), None),
    ((100.0, 5.0, 10000.0, 50.0), None),
    ((0.5, 0.01, 1.0, -5.0), None),
]
# (m, mu, a) -> n per pad
_SQUEEZE_CASES = [
    ((0.5, 0.5, 0.0), 4.905),
    ((0.5, 0.25, 0.0), 9.81),
    ((2.0, 0.4, 0.19), 25.0),
    ((1.0, 0.5, 5.19), 15.0),
    ((4, 1, -4.81), 10.0),
    ((0.3, 0.7, 12.0), None),
    ((100.0, 0.01, 50.0), None),
    ((0.05, 5.0, -5.0), None),
]
# (m, mu, n) -> a_max
_ACCEL_CASES = [
    ((2.0, 0.4, 25.0), 0.19),
    ((1.0, 0.5, 4.905), -4.905),
    ((0.5, 0.8, 10.0), 22.19),
    ((1, 1, 0), -9.81),
    ((10.0, 0.3, 100.0), None),
    ((0.2, 0.6, 3.0), None),
    ((100.0, 5.0, 10000.0), None),
]
# (fn, ft, mu) -> bool
_CONE_CASES = [
    ((4.0, 1.0, 0.5), True),
    ((4.0, 2.0, 0.5), True),
    ((4.0, 2.5, 0.5), False),
    ((4.0, -2.0, 0.5), True),
    ((4.0, -2.5, 0.5), False),
    ((0.0, 0.0, 0.5), True),
    ((0.0, 0.1, 0.5), False),
    ((-2.0, 0.0, 0.5), False),
    ((-2.0, 1.0, 0.5), False),
    ((8, 2, 0.25), True),
    ((8, 3, 0.25), False),
    ((1000.0, 1000.0, 1.0), True),
]
# (samples, mu, contact, window) -> [(index, name), ...]
_EVENT_CASES = [
    # normal pick with a boundary sample, two slips and a release
    (([(0, 0.0, 0.0), (0, 0.0, 0.0), (0, 3.0, 0.5), (0, 4.0, 1.0), (0, 4.0, 1.5),
       (0, 4.0, 2.0), (0, 4.0, 2.5), (0, 4.0, 1.5), (0, 4.0, 2.2), (1, 3.0, 0.5),
       (1, 0.0, 0.0)], 0.5, 1.0, 3),
     [(2, "contact"), (6, "slip"), (8, "slip"), (9, "release")]),
    # empty grasp, then an open with nothing held
    (([(0, 0.0, 0.0), (0, 0.2, 0.0), (0, 0.5, 0.0), (0, 0.3, 0.0), (1, 0.0, 0.0)],
      0.5, 1.0, 3), [(2, "empty")]),
    # lost without an open command, then a fresh contact and release
    (([(0, 0.0, 0.0), (0, 2.0, 0.5), (0, 2.0, 0.5), (0, 0.5, 0.1), (0, 0.5, 0.0),
       (0, 2.0, 0.5), (1, 2.0, 0.5)], 0.5, 1.0, 3),
     [(1, "contact"), (3, "lost"), (5, "contact"), (6, "release")]),
    # contact and slip on the same sample, release while slipping
    (([(0, 2.0, 2.0), (1, 2.0, 2.0)], 0.5, 1.0, 2),
     [(0, "contact"), (0, "slip"), (1, "release")]),
    (([(1, 0.0, 0.0), (1, 5.0, 0.0)], 0.5, 1.0, 2), []),
    # the closed-run counter resets at every open
    (([(0, 0.0, 0.0), (0, 0.0, 0.0), (1, 0.0, 0.0), (0, 0.0, 0.0), (0, 0.0, 0.0)],
      0.5, 1.0, 2), [(1, "empty"), (4, "empty")]),
    # window 1: threshold sample counts as contact; just below is empty, only once
    (([(0, 1.0, 0.0)], 0.5, 1.0, 1), [(0, "contact")]),
    (([(0, 0.99, 0.0), (0, 0.99, 0.0)], 0.5, 1.0, 1), [(0, "empty")]),
    # negative tangential reading, magnitude counts
    (([(0, 2.0, -1.5)], 0.5, 1.0, 5), [(0, "contact"), (0, "slip")]),
    # long open run reports one release; the next closed run is a new grasp
    (([(0, 3.0, 1.0), (1, 3.0, 1.0), (1, 3.0, 1.0), (0, 3.0, 1.0)], 0.5, 1.0, 5),
     [(0, "contact"), (1, "release"), (3, "contact")]),
    # slip recovers and a lost on a slipping sample ends both states
    (([(0, 4.0, 3.0), (0, 4.0, 3.0), (0, 4.0, 1.0), (0, 4.0, 3.0), (0, 0.5, 3.0),
       (0, 4.0, 1.0)], 0.5, 1.0, 3),
     [(0, "contact"), (0, "slip"), (3, "slip"), (4, "lost"), (5, "contact")]),
    # slip state is cleared by a release: a new closed run starting outside the cone
    (([(0, 4.0, 3.0), (1, 0.0, 0.0), (0, 2.0, 2.0)], 0.5, 1.0, 3),
     [(0, "contact"), (0, "slip"), (1, "release"), (2, "contact"), (2, "slip")]),
    # lost exactly at c == window after a contact in this run: lost, not empty
    (([(0, 0.0, 0.0), (0, 2.0, 0.5), (0, 0.5, 0.0)], 0.5, 1.0, 3),
     [(1, "contact"), (2, "lost")]),
    # contact arrives exactly at c == window: contact wins, no empty
    (([(0, 0.0, 0.0), (0, 1.0, 0.0)], 0.5, 1.0, 2), [(1, "contact")]),
]


def _fresh(value):
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _raised(error):
    return "your code raised " + type(error).__name__ + " on a VALID input (inside the contract)"


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
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

    def run(name, label, function, args, compare, index):
        ok, got = attempt(name, label, function, _fresh(args) if index % 2 else args)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def number(got, want, name):
        if not _real(got):
            raise _Mismatch("output must be one finite int/float")
        if not abs(got - want) <= _tol(want):
            raise _Mismatch(name + " is wrong (relative tolerance 1e-9)")

    tables = [
        ("safety_factor", safety_factor, _FACTOR_CASES, _ref_factor, "safety factor"),
        ("min_squeeze", min_squeeze, _SQUEEZE_CASES, _ref_squeeze, "squeeze force"),
        ("max_lift_accel", max_lift_accel, _ACCEL_CASES, _ref_accel, "acceleration"),
    ]
    for name, function, table, ref, what in tables:
        for i, (args, want) in enumerate(table):
            want = ref(*args) if want is None else want
            run(name, name + " " + str(i), function, args,
                lambda got, want=want, what=what: number(got, want, what), i)

    for i, (args, want) in enumerate(_CONE_CASES):
        def compare(got, want=want):
            if type(got) is not bool:
                raise _Mismatch("output must be a bool")
            if got != want:
                raise _Mismatch("cone membership is wrong")
        run("in_friction_cone", "in_friction_cone " + str(i), in_friction_cone, args, compare, i)

    for i, (args, want) in enumerate(_EVENT_CASES):
        def compare(got, want=want):
            if not isinstance(got, (list, tuple)) or not all(
                    isinstance(e, (list, tuple)) and len(e) == 2 and type(e[0]) is int
                    and type(e[1]) is str for e in got):
                raise _Mismatch("output must be a list/tuple of (int index, str name) pairs")
            got = [(e[0], e[1]) for e in got]
            if got == want:
                return
            if len(got) != len(want):
                raise _Mismatch("the number of events is wrong (" + str(len(got)) + " returned)")
            if [e[1] for e in got] != [e[1] for e in want]:
                raise _Mismatch("the sequence of event names is wrong")
            raise _Mismatch("an event is reported at the wrong sample index")
        run("retention_events", "retention_events " + str(i), retention_events, args, compare, i)

    if "retention_events" not in missing:
        trace = [[0, 0.0, 0.0], [0, 3.0, 0.5], [0, 4.0, 2.5], [1, 3.0, 0.5]]
        before = [list(row) for row in trace]
        try:
            retention_events(trace, 0.5, 1.0, 3)
            if trace != before:
                failures.append("retention_events input-mutation check: your function changed the samples")
        except Exception:
            pass

    nan, inf = float('nan'), float('inf')
    scalar = [nan, inf, -inf, True, "1", None]
    bad = {
        "m": [0.0, -1.0, 100.01, nan, inf, True, "1", None],
        "mu": [0.0, 0.0099, 5.01, -0.5, nan, inf, True, "1", None],
        "n": [-0.01, 10000.01, nan, inf, True, "1", None],
        "a": [-5.01, 50.01, nan, inf, True, "1", None],
        "fn": scalar + [1000.01, -1000.01],
        "ft": scalar + [1000.01, -1000.01],
        "contact": [0.0, -1.0, 1000.01, nan, inf, True, "1", None],
        "window": [0, -1, 1001, 2.0, True, nan, "2", None],
        "samples": [[], (), None, "abc", [(0, 1.0)], [(0, 1.0, 0.0, 0.0)], [(2, 1.0, 0.0)],
                    [(-1, 1.0, 0.0)], [(True, 1.0, 0.0)], [(0.0, 1.0, 0.0)], [("0", 1.0, 0.0)],
                    [(0, -0.1, 0.0)], [(0, 1000.01, 0.0)], [(0, nan, 0.0)], [(0, 1.0, inf)],
                    [(0, True, 0.0)], [(0, 1.0, 1000.01)], [(0, 1.0, "0")], [[0, 1.0, 0.0], None],
                    [(0, 1.0, 0.0)]*1001, {0: (0, 1.0, 0.0)}],
    }
    signatures = [
        ("safety_factor", safety_factor, ("m", "mu", "n", "a"), (1.0, 0.5, 5.0, 0.0)),
        ("min_squeeze", min_squeeze, ("m", "mu", "a"), (1.0, 0.5, 0.0)),
        ("max_lift_accel", max_lift_accel, ("m", "mu", "n"), (1.0, 0.5, 5.0)),
        ("in_friction_cone", in_friction_cone, ("fn", "ft", "mu"), (4.0, 1.0, 0.5)),
        ("retention_events", retention_events, ("samples", "mu", "contact", "window"),
         ([(0, 1.0, 0.0)], 0.5, 1.0, 2)),
    ]
    for title, function, names, args in signatures:
        for slot, name in enumerate(names):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                try:
                    function(*trial)
                except NotImplementedError:
                    missing.setdefault(title, []).append(label)
                    continue
                except ValueError:
                    continue
                except Exception as error:
                    failures.append(label + ": raised " + type(error).__name__
                                    + " instead of ValueError")
                    continue
                failures.append(label + ": returned instead of raising ValueError")

    summary = []
    for name, labels in missing.items():
        summary.append(name + ": not implemented yet (raises NotImplementedError; "
                       + str(len(labels)) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual parallel-jaw grasp self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

"""CoreLab Mock Interfaces lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
MOCK / SIMULATION MODE ONLY. Everything here is a plain numerical model of a
made-up 2-joint arm. It is NOT ros2_control, NOT a controller manager, NOT
MoveIt, NOT a real-time loop and NOT a safety function. Passing it says nothing
about any real controller, planner, driver or hardware, which need their own
separate review. Never connect code written here to a real robot on the
strength of this kit.
Implement the five functions below, then run your edited file locally:
  Windows: py -3 L14-interfaces.v1.py
  macOS/Linux: python3 L14-interfaces.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Conventions. Joint positions in radians, times in seconds (the action client
uses integer milliseconds), joint 0 first. "Number" means a finite int or
float, never bool. Anything outside the stated bounds raises ValueError. No
function may modify its inputs.

lifecycle_next(state, request) -> (next_state, accepted)
  A mock hardware interface has a lifecycle state (str): unconfigured,
  inactive, active, finalized. Requests (str): configure, activate, deactivate,
  cleanup, shutdown. Allowed transitions:
    unconfigured + configure  -> inactive      inactive + activate   -> active
    active + deactivate       -> inactive      inactive + cleanup    -> unconfigured
    shutdown from unconfigured, inactive or active -> finalized
  Any other pair is refused: the state is returned unchanged with accepted
  False (finalized refuses everything). accepted is a real bool. Unknown
  names raise ValueError.

write_cycle(lifecycle, position, command, dt, lower, upper, max_velocity)
    -> (new_position, velocity, status)
  One control cycle of the mock interface for 2 joints. position is the current
  state interface, command the position command interface just written.
  position, command, lower, upper and max_velocity are lists or tuples of
  exactly 2 numbers with absolute value <= 100; lower[j] < upper[j];
  max_velocity[j] > 0 (rad/s); position[j] lies inside [lower[j], upper[j]]
  (limits inclusive); dt is a number with 0 < dt <= 1 (seconds); lifecycle is
  one of the 4 lifecycle names. The command may lie anywhere in the allowed
  magnitude range, including outside the limits. Rules in priority order:
    1. lifecycle is not "active": the command is refused, status
       "rejected-not-active".
    2. any command[j] outside [lower[j], upper[j]] (exactly on a limit is
       inside): the WHOLE command is refused, status "rejected-position-limit".
    3. otherwise each joint moves toward its command by at most
       max_velocity[j] * dt; a joint whose distance is within that step
       (ties within 1e-9 count as reachable) lands exactly on its command. If
       any joint was cut short the status is "rate-limited", else "ok".
  A refused command leaves position unchanged and velocity [0.0, 0.0].
  Otherwise velocity[j] = (new_position[j] - position[j]) / dt, the state
  interface read back after the cycle. Return (list of 2 floats, list of 2
  floats, str). Comparison tolerance 1e-9.

validate_trajectory(joint_names, points, interface_names, current, lower,
                    upper, max_velocity, start_tol) -> list of str
  A joint trajectory is a list of waypoints (time_s, positions), plus the
  joint names it was written for. interface_names are the 2 distinct names (non
  empty ASCII strings) of the interface, in interface order. joint_names is a
  list or tuple of 0 to 6 non-empty strings (may repeat). points is a list or
  tuple of 0 to 50 pairs (t, q): t a number with 0 <= t <= 1000, q a list or
  tuple of 0 to 6 numbers (|value| <= 100). current, lower, upper and
  max_velocity are 2-number lists/tuples as for write_cycle (lower < upper,
  max_velocity > 0, |value| <= 100, current need not be inside the limits);
  start_tol is a number with 0 <= start_tol <= 1. Return the NAMES of every
  reason the trajectory is rejected, in this fixed order, each at most once;
  an empty list means accepted:
    "empty-trajectory"        points is empty (then no other point check runs)
    "joint-names-mismatch"    joint_names is not a reordering of interface_names
                              (different names, missing, extra or repeated)
    "joint-order-mismatch"    same names as interface_names but in another order
    "positions-length-mismatch"  some waypoint does not have exactly 2 positions
                              (then the three checks marked * do not run)
    "time-not-increasing"     some waypoint time is not strictly greater than
                              the previous one (equal times fail)
    "position-limit" *        some waypoint position is outside [lower, upper]
                              (limits inclusive, slack 1e-9)
    "velocity-limit" *        between two consecutive waypoints with a strictly
                              larger time, some joint moves more than
                              max_velocity[j] * (t_next - t_prev) (slack 1e-9)
    "start-state-mismatch" *  the first waypoint differs from current by more
                              than start_tol (+1e-9) in some joint
  Positions are read by index; the names are only judged by the two name rules.

action_run(events, timeout) -> (states, progress)
  A mock action client for a follow-trajectory goal, driven by a declared
  event list. events is a list or tuple of 0 to 200 triples (t, name, value):
  t an int time in milliseconds, 0 <= t <= 1000000, non-decreasing; name one of
  send_goal, accept, reject, feedback, cancel_request, cancel_done, result_ok,
  result_abort, tick; value None for every name except feedback, where it is a
  number in [0, 1] (the fraction done). timeout is an int, 1 <= timeout <=
  100000 ms. Client states (str): idle (start), pending, executing, canceling,
  succeeded, aborted, canceled, rejected, timed-out. Terminal states: succeeded,
  aborted, canceled, rejected, timed-out. progress starts at 0.0.
  Per event, in this order (first rule that applies wins):
    1. In a terminal state every event is ignored.
    2. If the state is pending, executing or canceling and t - t_goal > timeout
       (t_goal = time of the accepted send_goal; exactly timeout is still in
       time), the state becomes timed-out and the event itself is discarded.
    3. idle + send_goal -> pending (t_goal = t).  pending + accept -> executing.
       pending + reject -> rejected.
       pending or executing + cancel_request -> canceling.
       canceling + cancel_done -> canceled.
       executing or canceling + result_ok -> succeeded, progress 1.0.
       executing or canceling + result_abort -> aborted (progress kept).
       executing or canceling + feedback v -> progress = v only if v >= the
       current progress (a smaller value is dropped); feedback 1.0 alone does
       not finish the goal.
    4. Every other (state, event) pair is ignored: nothing changes.
  states[i] and progress[i] (float) are the values AFTER event i; both have
  len(events) entries (empty trace gives ([], [])). Comparison tolerance 1e-9
  on progress. Nothing is checked between events: a real client needs its own
  timer; here time only passes when an event arrives.

segment_free(q_start, q_end, l1, l2, box) -> bool
  Is the straight JOINT-SPACE segment from q_start to q_end collision free in
  the planar workspace? q_start, q_end are pairs (q1, q2) of absolute-value
  <= 10 rad (relative joint angles, q1 from the +x axis, q2 from link 1,
  counter-clockwise positive); l1, l2 link lengths with 0 < l <= 10 (metres);
  box = (xmin, ymin, xmax, ymax), xmin <= xmax, ymin <= ymax, |value| <= 100,
  the CLOSED axis-aligned obstacle (touching counts as collision). The base is
  at the origin; the elbow is l1 (cos q1, sin q1); the tip is the elbow plus
  l2 (cos(q1+q2), sin(q1+q2)). The arm is the two line segments base-elbow and
  elbow-tip. Method (stated so alternatives are legitimate): sample the joint
  segment at s = k/200, k = 0..200 (both ends included), q(s) = q_start +
  s (q_end - q_start), and report False as soon as either link segment meets
  the box, judged by exact segment/rectangle geometry (no tolerance, no
  inflation). Any uniform subdivision with 100 or more steps (101 or more samples)
  gives the same answer on every case in this kit; a coarser one (for example
  50 steps), skipping the first or last sample, inflating the box by even 0.001 m, only the end poses, only the tip, or only the elbow do not. This
  is a sampling check, not a proof: a thin obstacle can slip between samples
  and swept-volume, link thickness and self-collision are out of scope.
  Return a real bool (True = free).

Pause before coding - write your predictions down first:
  1. The interface is inactive and a position command arrives. Is it queued for
     later, executed partly or refused? What do the state interfaces read?
  2. One joint is asked 0.5 rad away with max_velocity 0.5 rad/s and dt 0.25 s;
     the other joint is already at its target. Which status? Which velocities?
  3. A command is 0.01 rad outside one joint's limit and only that joint is
     moving. Does the other joint still move? Is clamping an alternative design,
     and what would it hide from the caller?
  4. A trajectory has the right joint names in the wrong order and otherwise
     perfect positions. Which reasons are reported, and what would a controller
     do if you ignored the order?
  5. Two waypoints have equal times. Is it a time reason, a velocity reason
     (division by zero) or both?
  6. send_goal at 1000 ms, timeout 2000, an event at 3000 ms and another at
     3001 ms. In which state is the client after each?
  7. cancel_request has been sent, then result_ok arrives before cancel_done.
     Is the goal canceled or succeeded? Why can a real client not prevent this?
  8. A straight line between two collision free joint configurations: must the
     arm be free all along it? Draw a configuration pair where it is not.
Self-check tolerances: exact equality for names, states and booleans, 1e-9 for
positions, velocities and progress. Failure messages name the case and the kind
of mismatch, never the expected values. "your code raised X" means your
function raised on a VALID input; "invalid f(name=...)" lines are the opposite:
that input must raise ValueError. A function still raising NotImplementedError
is reported once. Sweeps report one line with a count and the first failing
input.
This kit covers deterministic, stateless mock models only: no ros2_control,
lifecycle nodes, controller manager, MoveIt or planner, no real-time timing, no
real controller, driver or hardware, no certification.
Reflection: why does passing this toy NOT make a real controller or planner
trustworthy? (Think about hardware that lies or lags, real-time jitter and
missed deadlines, the controller manager and real lifecycle callbacks,
interpolation between waypoints that this validator never samples, tracking
error, collision geometry of real links and meshes, planners that fail or find
a different path, and the fact that mock evidence stays mock: a real device
needs its own separate review.)
"""

LIFECYCLES = ("unconfigured", "inactive", "active", "finalized")
REQUESTS = ("configure", "activate", "deactivate", "cleanup", "shutdown")
REASONS = ("empty-trajectory", "joint-names-mismatch", "joint-order-mismatch",
           "positions-length-mismatch", "time-not-increasing", "position-limit",
           "velocity-limit", "start-state-mismatch")
ACTION_EVENTS = ("send_goal", "accept", "reject", "feedback", "cancel_request",
                 "cancel_done", "result_ok", "result_abort", "tick")
ACTION_STATES = ("idle", "pending", "executing", "canceling", "succeeded", "aborted",
                 "canceled", "rejected", "timed-out")


def lifecycle_next(state, request):
    raise NotImplementedError("Look up the (state, request) pair; refuse anything not in the table")


def write_cycle(lifecycle, position, command, dt, lower, upper, max_velocity):
    raise NotImplementedError("Refuse when not active, refuse out-of-limit commands, then rate-limit each joint")


def validate_trajectory(joint_names, points, interface_names, current, lower, upper, max_velocity, start_tol):
    raise NotImplementedError("Collect every named rejection reason, in the documented order")


def action_run(events, timeout):
    raise NotImplementedError("Track the state, the goal time and the progress; apply the timeout before the table")


def segment_free(q_start, q_end, l1, l2, box):
    raise NotImplementedError("Sample the joint segment, forward kinematics for both links, exact segment/box test")


# ---- SPOILER BELOW: the _..._ref functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----

import math
from fractions import Fraction


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


_NEXT = {("unconfigured", "configure"): "inactive", ("inactive", "activate"): "active",
         ("active", "deactivate"): "inactive", ("inactive", "cleanup"): "unconfigured",
         ("unconfigured", "shutdown"): "finalized", ("inactive", "shutdown"): "finalized",
         ("active", "shutdown"): "finalized"}
_SLACK = 1e-9
_TERMINAL = ("succeeded", "aborted", "canceled", "rejected", "timed-out")
_STEPS = 200


def _num(value, bound):
    return (type(value) in (int, float) and math.isfinite(value) and abs(value) <= bound)


def _int(value, low, high):
    return type(value) is int and low <= value <= high


def _name(value, names):
    return type(value) is str and value in names


def _pair(value, bound=100):
    return (isinstance(value, (list, tuple)) and len(value) == 2
            and all(_num(v, bound) for v in value))


def _lifecycle_ref(state, request):
    if not _name(state, LIFECYCLES) or not _name(request, REQUESTS):
        raise ValueError("lifecycle")
    nxt = _NEXT.get((state, request))
    return (state, False) if nxt is None else (nxt, True)


def _check_limits(lower, upper, max_velocity):
    if not (_pair(lower) and _pair(upper) and _pair(max_velocity)):
        raise ValueError("limits")
    if not all(lower[j] < upper[j] and max_velocity[j] > 0 for j in range(2)):
        raise ValueError("limits")


def _write_ref(lifecycle, position, command, dt, lower, upper, max_velocity):
    if not _name(lifecycle, LIFECYCLES) or not _pair(position) or not _pair(command):
        raise ValueError("arguments")
    if not (_num(dt, 1) and dt > 0):
        raise ValueError("dt")
    _check_limits(lower, upper, max_velocity)
    if not all(lower[j] <= position[j] <= upper[j] for j in range(2)):
        raise ValueError("position outside limits")
    if lifecycle != "active":
        return [float(position[0]), float(position[1])], [0.0, 0.0], "rejected-not-active"
    if any(not lower[j] <= command[j] <= upper[j] for j in range(2)):
        return [float(position[0]), float(position[1])], [0.0, 0.0], "rejected-position-limit"
    new, status = [], "ok"
    for j in range(2):
        step = max_velocity[j] * dt
        gap = command[j] - position[j]
        if abs(gap) <= step + _SLACK:
            new.append(float(command[j]))
        else:
            new.append(float(position[j] + math.copysign(step, gap)))
            status = "rate-limited"
    return new, [(new[j] - position[j]) / dt for j in range(2)], status


def _trajectory_ref(joint_names, points, interface_names, current, lower, upper, max_velocity, start_tol):
    if not (isinstance(interface_names, (list, tuple)) and len(interface_names) == 2
            and all(type(n) is str and n and n.isascii() for n in interface_names)
            and interface_names[0] != interface_names[1]):
        raise ValueError("interface_names")
    if not (isinstance(joint_names, (list, tuple)) and len(joint_names) <= 6
            and all(type(n) is str and n for n in joint_names)):
        raise ValueError("joint_names")
    if not (isinstance(points, (list, tuple)) and len(points) <= 50):
        raise ValueError("points")
    for p in points:
        if not (isinstance(p, (list, tuple)) and len(p) == 2 and _num(p[0], 1000) and 0 <= p[0]
                and isinstance(p[1], (list, tuple)) and len(p[1]) <= 6
                and all(_num(v, 100) for v in p[1])):
            raise ValueError("point")
    if not _pair(current):
        raise ValueError("current")
    _check_limits(lower, upper, max_velocity)
    if not (_num(start_tol, 1) and start_tol >= 0):
        raise ValueError("start_tol")
    out = []
    if not points:
        out.append("empty-trajectory")
    if list(joint_names) != list(interface_names):
        if len(joint_names) == 2 and sorted(joint_names) == sorted(interface_names):
            out.append("joint-order-mismatch")
        else:
            out.append("joint-names-mismatch")
    if not points:
        return sorted(out, key=REASONS.index)
    if any(len(p[1]) != 2 for p in points):
        out.append("positions-length-mismatch")
    times = [p[0] for p in points]
    if any(times[i + 1] <= times[i] for i in range(len(times) - 1)):
        out.append("time-not-increasing")
    if all(len(p[1]) == 2 for p in points):
        if any(not lower[j] - _SLACK <= p[1][j] <= upper[j] + _SLACK for p in points for j in range(2)):
            out.append("position-limit")
        for i in range(len(points) - 1):
            dtt = times[i + 1] - times[i]
            if dtt > 0 and any(abs(points[i + 1][1][j] - points[i][1][j]) > max_velocity[j] * dtt + _SLACK
                               for j in range(2)):
                out.append("velocity-limit")
                break
        if any(abs(points[0][1][j] - current[j]) > start_tol + _SLACK for j in range(2)):
            out.append("start-state-mismatch")
    return out


def _events_ref(events):
    if not isinstance(events, (list, tuple)) or len(events) > 200:
        raise ValueError("events")
    out, last = [], 0
    for e in events:
        if not (isinstance(e, (list, tuple)) and len(e) == 3):
            raise ValueError("event")
        t, name, value = e
        if not _int(t, 0, 1000000) or t < last or not _name(name, ACTION_EVENTS):
            raise ValueError("event")
        if name == "feedback":
            if not (_num(value, 1) and 0 <= value <= 1):
                raise ValueError("feedback value")
        elif value is not None:
            raise ValueError("value")
        last = t
        out.append((t, name, value))
    return out


def _action_ref(events, timeout):
    evs = _events_ref(events)
    if not _int(timeout, 1, 100000):
        raise ValueError("timeout")
    state, progress, t_goal = "idle", 0.0, None
    states, progs = [], []
    for t, name, value in evs:
        if state in _TERMINAL:
            pass
        elif state in ("pending", "executing", "canceling") and t - t_goal > timeout:
            state = "timed-out"
        elif state == "idle" and name == "send_goal":
            state, t_goal = "pending", t
        elif state == "pending" and name == "accept":
            state = "executing"
        elif state == "pending" and name == "reject":
            state = "rejected"
        elif state in ("pending", "executing") and name == "cancel_request":
            state = "canceling"
        elif state == "canceling" and name == "cancel_done":
            state = "canceled"
        elif state in ("executing", "canceling") and name == "result_ok":
            state, progress = "succeeded", 1.0
        elif state in ("executing", "canceling") and name == "result_abort":
            state = "aborted"
        elif state in ("executing", "canceling") and name == "feedback" and value >= progress:
            progress = float(value)
        states.append(state)
        progs.append(progress)
    return states, progs


def _seg_hits_exact(p, q, rect):
    """Closed segment p-q meets the closed rectangle, exact on the given float values."""
    lo_x, lo_y, hi_x, hi_y = rect
    if (max(p[0], q[0]) < lo_x - 1e-6 or min(p[0], q[0]) > hi_x + 1e-6
            or max(p[1], q[1]) < lo_y - 1e-6 or min(p[1], q[1]) > hi_y + 1e-6):
        return False
    t0, t1 = Fraction(0), Fraction(1)
    for a, b, lo, hi in ((p[0], q[0], lo_x, hi_x), (p[1], q[1], lo_y, hi_y)):
        a, b, lo, hi = Fraction(a), Fraction(b), Fraction(lo), Fraction(hi)
        d = b - a
        if d == 0:
            if a < lo or a > hi:
                return False
        else:
            ta, tb = (lo - a) / d, (hi - a) / d
            if ta > tb:
                ta, tb = tb, ta
            t0, t1 = max(t0, ta), min(t1, tb)
            if t0 > t1:
                return False
    return True


def _pose(q, l1, l2):
    ex, ey = l1 * math.cos(q[0]), l1 * math.sin(q[0])
    return (ex, ey), (ex + l2 * math.cos(q[0] + q[1]), ey + l2 * math.sin(q[0] + q[1]))


def _free_ref(q_start, q_end, l1, l2, box, steps=_STEPS):
    if not (_pair(q_start, 10) and _pair(q_end, 10)):
        raise ValueError("configuration")
    if not (_num(l1, 10) and l1 > 0 and _num(l2, 10) and l2 > 0):
        raise ValueError("link length")
    if not (isinstance(box, (list, tuple)) and len(box) == 4 and all(_num(v, 100) for v in box)
            and box[0] <= box[2] and box[1] <= box[3]):
        raise ValueError("box")
    for k in range(steps + 1):
        s = k / steps
        q = (q_start[0] + s * (q_end[0] - q_start[0]), q_start[1] + s * (q_end[1] - q_start[1]))
        elbow, tip = _pose(q, l1, l2)
        if _seg_hits_exact((0.0, 0.0), elbow, box) or _seg_hits_exact(elbow, tip, box):
            return False
    return True


def _hit_float(p, q, rect):
    """Independent float slab test (used only for case filtering)."""
    t0, t1 = 0.0, 1.0
    for a, b, lo, hi in ((p[0], q[0], rect[0], rect[2]), (p[1], q[1], rect[1], rect[3])):
        d = b - a
        if d == 0.0:
            if a < lo or a > hi:
                return False
        else:
            ta, tb = (lo - a) / d, (hi - a) / d
            if ta > tb:
                ta, tb = tb, ta
            t0, t1 = max(t0, ta), min(t1, tb)
            if t0 > t1:
                return False
    return True


def _free_float(q_start, q_end, l1, l2, box, steps):
    for k in range(steps + 1):
        s = k / steps
        q = (q_start[0] + s * (q_end[0] - q_start[0]), q_start[1] + s * (q_end[1] - q_start[1]))
        elbow, tip = _pose(q, l1, l2)
        if _hit_float((0.0, 0.0), elbow, box) or _hit_float(elbow, tip, box):
            return False
    return True


# lifecycle_next(state, request) -> (next_state, accepted)
_L_CASES = [
    (("unconfigured", "configure"), ("inactive", True)),
    (("inactive", "activate"), ("active", True)),
    (("active", "deactivate"), ("inactive", True)),
    (("inactive", "cleanup"), ("unconfigured", True)),
    (("unconfigured", "shutdown"), ("finalized", True)),
    (("inactive", "shutdown"), ("finalized", True)),
    (("active", "shutdown"), ("finalized", True)),
    (("unconfigured", "activate"), ("unconfigured", False)),
    (("active", "configure"), ("active", False)),
    (("active", "cleanup"), ("active", False)),
    (("inactive", "deactivate"), ("inactive", False)),
    (("finalized", "configure"), ("finalized", False)),
    (("finalized", "shutdown"), ("finalized", False)),
]

_LO, _HI, _VM = (-1.0, -2.0), (1.0, 2.0), (0.5, 1.0)
# write_cycle(lifecycle, position, command, dt, lower, upper, max_velocity) -> (position, velocity, status)
_W_CASES = [
    (("active", (0.0, 0.0), (0.0625, 0.125), 0.25, _LO, _HI, _VM), ([0.0625, 0.125], [0.25, 0.5], "ok")),
    (("active", (0.0, 0.0), (0.5, 0.125), 0.25, _LO, _HI, _VM), ([0.125, 0.125], [0.5, 0.5], "rate-limited")),
    (("active", (0.0, 0.0), (-0.5, -1.0), 0.25, _LO, _HI, _VM), ([-0.125, -0.25], [-0.5, -1.0], "rate-limited")),
    (("active", (0.0, 0.0), (0.125, 0.25), 0.25, _LO, _HI, _VM), ([0.125, 0.25], [0.5, 1.0], "ok")),
    (("active", (0.0, -1.75), (0.0, -2.0), 0.25, _LO, _HI, _VM), ([0.0, -2.0], [0.0, -1.0], "ok")),
    (("active", (1.0, 0.0), (1.0, 0.5), 0.25, _LO, _HI, _VM), ([1.0, 0.25], [0.0, 1.0], "rate-limited")),
    (("active", (0.5, 0.5), (0.5, 0.5), 0.5, _LO, _HI, _VM), ([0.5, 0.5], [0.0, 0.0], "ok")),
    (("active", (0.0, 0.0), (1.5, 0.0), 0.25, _LO, _HI, _VM), ([0.0, 0.0], [0.0, 0.0], "rejected-position-limit")),
    (("active", (0.0, 0.0), (0.0625, -2.25), 0.25, _LO, _HI, _VM), ([0.0, 0.0], [0.0, 0.0], "rejected-position-limit")),
    (("active", (0.75, 0.0), (1.0625, 0.0), 0.25, _LO, _HI, _VM), ([0.75, 0.0], [0.0, 0.0], "rejected-position-limit")),
    (("inactive", (0.0, 0.0), (0.0625, 0.125), 0.25, _LO, _HI, _VM), ([0.0, 0.0], [0.0, 0.0], "rejected-not-active")),
    (("unconfigured", (0.25, -0.5), (0.0, 0.0), 0.25, _LO, _HI, _VM), ([0.25, -0.5], [0.0, 0.0], "rejected-not-active")),
    (("finalized", (0.25, -0.5), (5.0, 0.0), 0.25, _LO, _HI, _VM), ([0.25, -0.5], [0.0, 0.0], "rejected-not-active")),
    (("active", (0.0, 0.0), (0.5, -1.0), 1.0, _LO, _HI, _VM), ([0.5, -1.0], [0.5, -1.0], "ok")),
    (("active", (0.25, 0.0), (-0.75, 1.5), 0.5, _LO, _HI, _VM), ([0.0, 0.5], [-0.5, 1.0], "rate-limited")),
    (("active", (0.0, 0.0), (0.1255, 0.0), 0.25, _LO, _HI, _VM), ([0.125, 0.0], [0.5, 0.0], "rate-limited")),
    (("active", (0.0, 0.0), (0.07, 0.0), 0.3, _LO, _HI, _VM), ([0.07, 0.0], [0.07 / 0.3, 0.0], "ok")),
]

_NAMES = ("shoulder", "elbow")
_TLO, _THI, _TVM = (-1.5, -1.5), (1.5, 1.5), (1.0, 2.0)
_CUR = (0.0, 0.5)


def _tc(names=_NAMES, points=None, tol=0.125, cur=_CUR):
    base = [(0.0, (0.0, 0.5)), (1.0, (0.5, 1.0)), (2.0, (1.0, 1.5))]
    return (tuple(names), tuple(base if points is None else points), _NAMES, cur, _TLO, _THI, _TVM, tol)


# validate_trajectory(...) -> list of reason names
_V_CASES = [
    (_tc(), []),
    (_tc(names=("elbow", "shoulder")), ["joint-order-mismatch"]),
    (_tc(names=("shoulder", "wrist")), ["joint-names-mismatch"]),
    (_tc(names=("shoulder",)), ["joint-names-mismatch"]),
    (_tc(names=("shoulder", "elbow", "wrist")), ["joint-names-mismatch"]),
    (_tc(names=("shoulder", "shoulder")), ["joint-names-mismatch"]),
    (_tc(names=()), ["joint-names-mismatch"]),
    (_tc(points=()), ["empty-trajectory"]),
    (_tc(names=("elbow", "shoulder"), points=()), ["empty-trajectory", "joint-order-mismatch"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (1.0, (0.5, 1.0)), (1.0, (0.75, 1.0))]), ["time-not-increasing"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (2.0, (0.5, 1.0)), (1.0, (0.75, 1.0))]), ["time-not-increasing"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (4.0, (1.5, 1.0)), (8.0, (1.625, 1.0))]), ["position-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (4.0, (1.5, 1.0)), (8.0, (1.5, -1.5))]), []),
    (_tc(points=[(0.0, (0.0, 0.5)), (4.0, (0.0, -1.625))]), ["position-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.75, 0.5))]), ["velocity-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.5, 0.5))]), []),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.0, -1.0))]), ["velocity-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.0, 1.5))]), []),
    (_tc(points=[(0.0, (0.25, 0.5)), (1.0, (0.5, 1.0))]), ["start-state-mismatch"]),
    (_tc(points=[(0.0, (0.0, 0.75)), (1.0, (0.5, 1.0))]), ["start-state-mismatch"]),
    (_tc(points=[(0.0, (0.125, 0.5)), (1.0, (0.5, 1.0))]), []),
    (_tc(points=[(0.0, (0.0, 0.5)), (1.0, (0.5, 1.0))], tol=0.0, cur=(0.0, 0.5)), []),
    (_tc(points=[(0.0, (0.0625, 0.5)), (1.0, (0.5, 1.0))], tol=0.0), ["start-state-mismatch"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (1.0, (0.5, 1.0, 0.0))]), ["positions-length-mismatch"]),
    (_tc(points=[(0.0, (0.0,)), (1.0, (0.5, 1.0))]), ["positions-length-mismatch"]),
    (_tc(points=[(0.0, ()), (0.0, (9.0, 9.0, 9.0))]), ["positions-length-mismatch", "time-not-increasing"]),
    (_tc(points=[(0.0, (0.5, 0.5)), (0.5, (2.0, 0.5))]), ["position-limit", "velocity-limit", "start-state-mismatch"]),
    (_tc(names=("elbow", "shoulder"), points=[(0.0, (0.5, 0.5)), (0.0, (2.0, 0.5))]),
     ["joint-order-mismatch", "time-not-increasing", "position-limit", "start-state-mismatch"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.75, 0.5)), (1.0, (0.75, 0.5))]), ["velocity-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (1.0, (1.0, 0.5)), (1.5, (0.0, 0.5))]), ["velocity-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (1.0, (0.5, 2.5)), (1.0, (0.5, 2.5))]), ["time-not-increasing", "position-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5)), (0.5, (0.0, 1.5)), (1.0, (0.0, -0.5))]), ["velocity-limit"]),
    (_tc(points=[(0.0, (0.0, 0.5))]), []),
    (_tc(points=[(0.25, (0.0, 0.5))]), []),
]

_E = lambda *x: tuple(x)  # noqa: E731
# action_run(events, timeout) -> (states, progress)
_A_CASES = [
    (((), 1000), ([], [])),
    (((_E(0, "send_goal", None), _E(100, "accept", None), _E(200, "feedback", 0.25),
       _E(300, "feedback", 0.5), _E(400, "result_ok", None)), 1000),
     (["pending", "executing", "executing", "executing", "succeeded"], [0.0, 0.0, 0.25, 0.5, 1.0])),
    (((_E(0, "send_goal", None), _E(100, "reject", None), _E(200, "accept", None)), 1000),
     (["pending", "rejected", "rejected"], [0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(50, "accept", None), _E(60, "feedback", 0.5), _E(70, "feedback", 0.25),
       _E(80, "feedback", 0.5), _E(90, "result_abort", None), _E(95, "result_ok", None)), 1000),
     (["pending", "executing", "executing", "executing", "executing", "aborted", "aborted"],
      [0.0, 0.0, 0.5, 0.5, 0.5, 0.5, 0.5])),
    (((_E(1000, "send_goal", None), _E(1500, "accept", None), _E(3000, "feedback", 0.5),
       _E(3001, "result_ok", None), _E(3500, "tick", None)), 2000),
     (["pending", "executing", "executing", "timed-out", "timed-out"], [0.0, 0.0, 0.5, 0.5, 0.5])),
    (((_E(0, "send_goal", None), _E(5000, "accept", None)), 4999), (["pending", "timed-out"], [0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(5000, "accept", None)), 5000), (["pending", "executing"], [0.0, 0.0])),
    (((_E(0, "tick", None), _E(10, "accept", None), _E(20, "result_ok", None), _E(30, "send_goal", None),
       _E(40, "accept", None)), 1000),
     (["idle", "idle", "idle", "pending", "executing"], [0.0, 0.0, 0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(10, "send_goal", None), _E(20, "accept", None), _E(30, "accept", None)), 1000),
     (["pending", "pending", "executing", "executing"], [0.0, 0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(10, "feedback", 0.75), _E(20, "result_ok", None), _E(30, "cancel_request", None)), 1000),
     (["pending", "pending", "pending", "canceling"], [0.0, 0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(10, "accept", None), _E(20, "feedback", 0.25), _E(30, "cancel_request", None),
       _E(40, "feedback", 0.5), _E(50, "feedback", 0.25), _E(60, "cancel_done", None), _E(70, "result_ok", None)), 1000),
     (["pending", "executing", "executing", "canceling", "canceling", "canceling", "canceled", "canceled"],
      [0.0, 0.0, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5])),
    (((_E(0, "send_goal", None), _E(10, "accept", None), _E(20, "cancel_request", None), _E(30, "result_ok", None)), 1000),
     (["pending", "executing", "canceling", "succeeded"], [0.0, 0.0, 0.0, 1.0])),
    (((_E(0, "send_goal", None), _E(10, "accept", None), _E(20, "cancel_request", None), _E(30, "result_abort", None)), 1000),
     (["pending", "executing", "canceling", "aborted"], [0.0, 0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(10, "cancel_request", None), _E(20, "accept", None), _E(30, "cancel_done", None)), 1000),
     (["pending", "canceling", "canceling", "canceled"], [0.0, 0.0, 0.0, 0.0])),
    (((_E(0, "send_goal", None), _E(10, "accept", None), _E(20, "cancel_done", None), _E(30, "feedback", 1.0),
       _E(40, "tick", None), _E(50, "cancel_request", None), _E(2000, "cancel_done", None)), 1500),
     (["pending", "executing", "executing", "executing", "executing", "canceling", "timed-out"],
      [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0])),
    (((_E(100, "send_goal", None), _E(100, "accept", None), _E(100, "feedback", 0.0), _E(100, "result_ok", None)), 1),
     (["pending", "executing", "executing", "succeeded"], [0.0, 0.0, 0.0, 1.0])),
    (((_E(0, "send_goal", None), _E(1, "accept", None), _E(2, "feedback", 0.5), _E(3, "tick", None)), 2),
     (["pending", "executing", "executing", "timed-out"], [0.0, 0.0, 0.5, 0.5])),
]

_BOX = (0.5, 0.5, 1.0, 1.0)
_PI = math.pi
# segment_free(q_start, q_end, l1, l2, box) -> bool
_S_CASES = [
    (((0.0, 0.0), (1.5, 0.0), 1.0, 1.0, _BOX), False),
    (((0.0, 0.0), (0.25, 0.0), 1.0, 1.0, _BOX), True),
    (((1.5, 0.0), (1.5, 0.0), 1.0, 1.0, _BOX), True),
    (((0.0, 0.0), (0.0, 0.0), 1.0, 1.0, (0.5, -0.25, 3.0, 0.25)), False),
    (((0.0, 0.0), (0.0, 0.0), 1.0, 1.0, (2.0, -1.0, 3.0, 1.0)), False),
    (((0.0, 0.0), (0.0, 0.0), 1.0, 1.0, (2.25, -1.0, 3.0, 1.0)), True),
    (((0.0, 0.0), (0.0, 0.0), 1.0, 1.0, (0.5, 0.0, 1.5, 1.0)), False),
    (((_PI / 2, 0.0), (_PI / 2, 0.0), 1.0, 1.0, (-1.0, 0.5, 1.0, 1.5)), False),
    (((0.0, 0.0), (_PI / 2, 0.0), 1.0, 1.0, (-0.5, 1.5, 0.5, 2.5)), False),
    (((0.0, 0.0), (_PI / 2, 0.0), 1.0, 1.0, (-0.5, 2.25, 0.5, 2.5)), True),
    (((0.0, 0.0), (-1.5, 0.0), 1.0, 1.0, _BOX), True),
    (((-0.5, 0.0), (0.0, 0.0), 1.0, 1.0, (0.25, 0.25, 1.25, 1.25)), True),
    (((0.0, 2.5), (0.0, 2.5), 1.0, 1.0, (0.5, 0.5, 0.75, 0.75)), True),
    (((0.0, 3.0), (_PI / 2, 3.0), 1.0, 1.0, (-0.25, -1.5, 0.25, -0.5)), True),
    (((0.0, 1.5), (1.5, -1.5), 1.0, 1.0, (0.5, 0.25, 0.75, 0.5)), False),
    (((1.0, 0.0), (2.0, 0.0), 0.75, 0.5, (-0.25, 0.75, 0.25, 1.25)), False),
    (((0.0, -0.25), (0.0, 0.25), 1.0, 0.5, (1.25, 0.05, 1.5, 0.6)), False),
    (((0.0, -0.25), (0.0, 0.25), 1.0, 0.5, (1.25, 0.2, 1.5, 0.6)), True),
    (((0.0, 2.6), (0.0, 2.6), 1.0, 0.25, (0.4, -0.1, 0.6, 0.1)), False),
    (((2.0, 0.0), (3.0, 0.0), 0.75, 0.5, (-0.25, 0.75, 0.25, 1.25)), True),
    (((0.0, 0.0), (3.0, 0.0), 1.0, 1.0, (-0.0625, 1.5, 0.0625, 2.5)), False),
    (((0.0, 0.0), (_PI / 2, 0.0), 1.0, 1.0, (-0.3, 1.5, 0.005, 2.5)), False),
    (((_PI / 2, 0.0), (0.0, 0.0), 1.0, 1.0, (-0.3, 1.5, 0.005, 2.5)), False),
    (((0.0, 0.0), (2.75, 0.0), 1.0, 1.0, (-0.03125, 1.5, 0.03125, 2.5)), False),
    (((0.0, 0.0), (0.0, 0.0), 1.0, 1.0, (2.0005, -1.0, 3.0, 1.0)), True),
]


_MEMO = {}
_FAST = [1, 300, 400, 150]  # sweep sizes, shrunk by the author fixture only


def _fresh(value):
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _frozen(value):
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(v) for v in value)
    return value


def _raised(error):
    return "your code raised " + type(error).__name__


class _Lcg:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF

    def below(self, n):
        self.state = (self.state * 1664525 + 1013904223) & 0xFFFFFFFF
        return (self.state >> 8) % n


def _real(v):
    return type(v) in (int, float) and math.isfinite(v)


def _norm_write(got):
    if not isinstance(got, (list, tuple)) or len(got) != 3:
        raise _Mismatch("must return (new_position, velocity, status)")
    pos, vel, status = got
    for part in (pos, vel):
        if not isinstance(part, (list, tuple)) or len(part) != 2 or not all(_real(v) for v in part):
            raise _Mismatch("positions and velocities must be lists of 2 finite numbers")
    if type(status) is not str:
        raise _Mismatch("status must be a str")
    return [float(v) for v in pos], [float(v) for v in vel], status


def _norm_reasons(got):
    if not isinstance(got, (list, tuple)) or any(type(r) is not str for r in got):
        raise _Mismatch("must return a list of reason names (str)")
    return list(got)


def _norm_action(got):
    if not isinstance(got, (list, tuple)) or len(got) != 2:
        raise _Mismatch("must return (states, progress)")
    states, prog = got
    if (not isinstance(states, (list, tuple)) or not isinstance(prog, (list, tuple))
            or any(type(s) is not str for s in states) or not all(_real(v) for v in prog)):
        raise _Mismatch("states must be str and progress finite numbers")
    return list(states), [float(v) for v in prog]


def _write_cases(count, seed):
    rng = _Lcg(seed)
    limits = (((-1.0, -2.0), (1.0, 2.0)), ((-0.5, -0.5), (0.5, 0.5)), ((0.0, -1.0), (2.0, 1.0)))
    speeds = ((0.5, 1.0), (0.25, 0.75), (2.0, 2.0))
    out = []
    for _ in range(count):
        lo, hi = limits[rng.below(3)]
        pos = tuple(lo[j] + 0.125 * rng.below(int((hi[j] - lo[j]) / 0.125) + 1) for j in range(2))
        cmd = tuple(-2.5 + 0.0625 * rng.below(81) for _ in range(2))
        if rng.below(2):
            cmd = tuple(min(max(cmd[j], lo[j]), hi[j]) for j in range(2))
        out.append((LIFECYCLES[(0, 1, 2, 2, 2, 3)[rng.below(6)]], pos, cmd, (0.25, 0.5, 1.0)[rng.below(3)],
                    lo, hi, speeds[rng.below(3)]))
    return out


def _trajectory_cases(count, seed):
    rng = _Lcg(seed)
    name_sets = (_NAMES, _NAMES, ("elbow", "shoulder"), ("shoulder", "wrist"), ("shoulder",),
                 ("shoulder", "elbow", "wrist"), (), ("elbow", "elbow"))
    out = []
    for _ in range(count):
        n = (0, 1, 2, 2, 3, 3, 4)[rng.below(7)]
        t = 0.25 * rng.below(3)
        pts = []
        for _ in range(n):
            width = 2 if rng.below(12) else (1, 3, 0)[rng.below(3)]
            pts.append((t, tuple(0.125 * rng.below(25) - 1.5 + (0.25 if rng.below(9) == 0 else 0.0)
                                 for _ in range(width))))
            t += (0.0, 0.25, 0.5, 0.5, 1.0, 1.0)[rng.below(6)]
        if rng.below(10) == 0 and len(pts) > 1:
            pts[1] = (pts[0][0] - 0.25 if pts[0][0] >= 0.25 else pts[0][0], pts[1][1])
        cur = (0.125 * rng.below(5) - 0.25, 0.5)
        out.append((name_sets[rng.below(8)], tuple(pts), _NAMES, cur, _TLO, _THI, _TVM,
                    (0.0, 0.125, 0.25)[rng.below(3)]))
    return out


def _action_sequences():
    base = [(None, n) for n in ACTION_EVENTS if n != "feedback"] + [(0.25, "feedback"), (0.75, "feedback")]
    out = []
    for a in base:
        for b in base:
            for c in base:
                out.append((a, b, c))
    return out


def _action_cases(count, seed):
    rng = _Lcg(seed)
    out = []
    for seq in _action_sequences()[::3]:
        evs, t = [], 0
        for i, (v, name) in enumerate(seq):
            evs.append((t, name, v))
            t += (400, 400, 400)[i] if i else 400
        out.append((tuple(evs), 1000))
    for _ in range(count):
        evs, t = [], 0
        for _ in range(8):
            name = ACTION_EVENTS[rng.below(9)]
            value = (0.0, 0.25, 0.5, 1.0)[rng.below(4)] if name == "feedback" else None
            t += (0, 100, 300, 700, 1200)[rng.below(5)]
            evs.append((t, name, value))
        evs[0] = (evs[0][0], "send_goal", None) if rng.below(3) else evs[0]
        out.append((tuple(evs), (500, 1000, 2000)[rng.below(3)]))
    return out


def _scene_cases(count, seed):
    """Random box/arm cases whose answer is robust against the subdivision (clearance > ~0.01 m)."""
    key = ("scene", count, seed)
    if key in _MEMO:
        return _MEMO[key]
    rng = _Lcg(seed)
    out = []
    tries = 0
    while len(out) < count and tries < count * 40:
        tries += 1
        q0 = (0.25 * rng.below(25) - 3.0, 0.25 * rng.below(21) - 2.5)
        q1 = (0.25 * rng.below(25) - 3.0, 0.25 * rng.below(21) - 2.5)
        l1, l2 = (0.5, 0.75, 1.0)[rng.below(3)], (0.25, 0.5, 1.0)[rng.below(3)]
        x0, y0 = 0.25 * rng.below(17) - 2.0, 0.25 * rng.below(17) - 2.0
        box = (x0, y0, x0 + 0.125 * (1 + rng.below(10)), y0 + 0.125 * (1 + rng.below(10)))
        answers = {_free_float(q0, q1, l1, l2, box, n) for n in (100, 137, 200, 400, 1000)}
        if len(answers) != 1:
            continue
        grown = (box[0] - 0.02, box[1] - 0.02, box[2] + 0.02, box[3] + 0.02)
        shrunk = (box[0] + 0.02, box[1] + 0.02, box[2] - 0.02, box[3] - 0.02)
        base = answers.pop()
        if _free_float(q0, q1, l1, l2, grown, 200) != base:
            continue
        if shrunk[0] <= shrunk[2] and shrunk[1] <= shrunk[3] and _free_float(q0, q1, l1, l2, shrunk, 200) != base:
            continue
        out.append(((q0, q1), l1, l2, box))
    out = [(a[0][0], a[0][1], a[1], a[2], a[3]) for a in out]
    _MEMO[key] = out
    return out


def _bad_cases():
    cases = []
    for bad in ("Active", "ready", 3, None, ["active"]):
        cases.append(("lifecycle_next(state=" + repr(bad) + ")", "lifecycle_next", (bad, "configure")))
    for bad in ("start", "", 1, None, ("configure",)):
        cases.append(("lifecycle_next(request=" + repr(bad) + ")", "lifecycle_next", ("inactive", bad)))
    base = ["active", (0.0, 0.0), (0.0625, 0.125), 0.25, _LO, _HI, _VM]

    def with_(index, value):
        args = list(base)
        args[index] = value
        return tuple(args)
    for bad in ("Active", "run", 2, None):
        cases.append(("write_cycle(lifecycle=" + repr(bad) + ")", "write_cycle", with_(0, bad)))
    for index, label in ((1, "position"), (2, "command")):
        for bad in ((0.0,), (0.0, 0.0, 0.0), (True, 0.0), (float("nan"), 0.0), (float("inf"), 0.0),
                    ("0", 0.0), (0.0, 101.0), None, 0.5):
            cases.append(("write_cycle(" + label + "=" + repr(bad) + ")", "write_cycle", with_(index, bad)))
    for bad in (0, -0.25, 1.5, True, float("nan"), float("inf"), None, "0.25"):
        cases.append(("write_cycle(dt=" + repr(bad) + ")", "write_cycle", with_(3, bad)))
    for bad in ((1.0, -2.0), (-1.0, 2.0), (-1.0,), (-1.0, 0.0, 1.0), (True, -2.0), (-1.0, 3.0)):
        cases.append(("write_cycle(lower=" + repr(bad) + ")", "write_cycle", with_(4, bad)))
    for bad in ((-1.0, 2.0), (1.0, -2.0), (1.0,), (1.0, float("nan")), (-2.0, 2.0)):
        cases.append(("write_cycle(upper=" + repr(bad) + ")", "write_cycle", with_(5, bad)))
    for bad in ((0.0, 1.0), (0.5, -1.0), (0.5,), (True, 1.0), (0.5, float("inf")), (0.5, 101.0)):
        cases.append(("write_cycle(max_velocity=" + repr(bad) + ")", "write_cycle", with_(6, bad)))
    for bad in ((1.5, 0.0), (0.0, -2.5)):
        cases.append(("write_cycle(position outside limits=" + repr(bad) + ")", "write_cycle", with_(1, bad)))
    tbase = list(_tc(points=[(0.0, (0.0, 0.5)), (1.0, (0.5, 1.0))]))

    def tw(index, value):
        args = list(tbase)
        args[index] = value
        return tuple(args)
    for bad in (None, "shoulder", (1, "elbow"), ("", "elbow"), ("a",) * 7, (None,)):
        cases.append(("validate_trajectory(joint_names=" + repr(bad) + ")", "validate_trajectory", tw(0, bad)))
    for bad in (None, 5, [(0.0,)], [(0.0, (0.0, 0.5), 1)], [(-1.0, (0.0, 0.5))], [(1001.0, (0.0, 0.5))],
                [(True, (0.0, 0.5))], [(float("nan"), (0.0, 0.5))], [(0.0, (0.0, float("nan")))],
                [(0.0, (101.0, 0.5))], [(0.0, "ab")], [(0.0, (True, 0.5))], [(0.0, (0.0,) * 7)],
                [(0.0, (0.0, 0.5))] * 51):
        cases.append(("validate_trajectory(points=" + repr(bad)[:40] + ")", "validate_trajectory", tw(1, bad)))
    for bad in (("shoulder", "shoulder"), ("shoulder",), ("shoulder", ""), ("shoulder", "elb" + chr(246) + "w"),
                ("shoulder", 3), None):
        cases.append(("validate_trajectory(interface_names=" + repr(bad) + ")", "validate_trajectory", tw(2, bad)))
    for bad in ((0.0,), (0.0, True), (0.0, float("nan")), (0.0, 101.0), None):
        cases.append(("validate_trajectory(current=" + repr(bad) + ")", "validate_trajectory", tw(3, bad)))
    for index, label, bads in ((4, "lower", ((1.5, -1.5), (-1.5,))), (5, "upper", ((-2.0, 1.5), (True, 1.5))),
                               (6, "max_velocity", ((0.0, 2.0), (1.0, -2.0), (1.0,)))):
        for bad in bads:
            cases.append(("validate_trajectory(" + label + "=" + repr(bad) + ")", "validate_trajectory",
                          tw(index, bad)))
    for bad in (-0.125, 1.5, True, float("nan"), None, "0.1"):
        cases.append(("validate_trajectory(start_tol=" + repr(bad) + ")", "validate_trajectory", tw(7, bad)))
    ok_events = ((0, "send_goal", None), (100, "accept", None))
    for bad in (None, 5, ((0, "send_goal"),), ((0, "send_goal", None, 1),), ((-1, "send_goal", None),),
                ((0.5, "send_goal", None),), ((True, "send_goal", None),), ((0, "launch", None),),
                ((0, 3, None),), ((100, "send_goal", None), (50, "accept", None)),
                ((0, "send_goal", 0.5),), ((0, "feedback", None),), ((0, "feedback", 1.5),),
                ((0, "feedback", -0.25),), ((0, "feedback", float("nan")),), ((0, "feedback", True),),
                ((1000001, "send_goal", None),), ((0, "tick", None),) * 201):
        cases.append(("action_run(events=" + repr(bad)[:40] + ")", "action_run", (bad, 1000)))
    for bad in (0, -1, 100001, 1.5, True, None, "1000"):
        cases.append(("action_run(timeout=" + repr(bad) + ")", "action_run", (ok_events, bad)))
    sbase = [(0.0, 0.0), (1.0, 0.0), 1.0, 1.0, _BOX]

    def sw(index, value):
        args = list(sbase)
        args[index] = value
        return tuple(args)
    for index, label in ((0, "q_start"), (1, "q_end")):
        for bad in ((0.0,), (0.0, True), (10.5, 0.0), (0.0, float("nan")), None, 1.0):
            cases.append(("segment_free(" + label + "=" + repr(bad) + ")", "segment_free", sw(index, bad)))
    for index, label in ((2, "l1"), (3, "l2")):
        for bad in (0, -1.0, 10.5, True, float("inf"), None, "1"):
            cases.append(("segment_free(" + label + "=" + repr(bad) + ")", "segment_free", sw(index, bad)))
    for bad in ((0.5, 0.5, 1.0), (1.0, 0.5, 0.5, 1.0), (0.5, 1.0, 1.0, 0.5), (0.5, 0.5, 1.0, float("nan")),
                (0.5, 0.5, True, 1.0), (0.5, 0.5, 1.0, 101.0), None, "box"):
        cases.append(("segment_free(box=" + repr(bad) + ")", "segment_free", sw(4, bad)))
    return cases


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, args, frozen=False):
        calls[name] = calls.get(name, 0) + 1
        live = _frozen(args) if frozen else _fresh(args)
        snapshot = repr(live)
        try:
            got = globals()[name](*live)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return False, None
        except Exception as error:
            failures.append(label + ": " + _raised(error))
            return False, None
        if repr(live) != snapshot:
            failures.append(label + ": modified its input (inputs must never be mutated)")
        return True, got

    def run(name, label, args, compare, frozen=False):
        ok, got = attempt(name, label, args, frozen)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def cmp_lifecycle(want):
        def compare(got):
            if not isinstance(got, (list, tuple)) or len(got) != 2:
                raise _Mismatch("must return (next_state, accepted)")
            if type(got[0]) is not str or got[0] != want[0]:
                raise _Mismatch("next state is wrong")
            if type(got[1]) is not bool:
                raise _Mismatch("accepted must be a real bool")
            if got[1] != want[1]:
                raise _Mismatch("accepted flag is wrong")
        return compare

    def cmp_write(want):
        def compare(got):
            pos, vel, status = _norm_write(got)
            if status != want[2]:
                raise _Mismatch("status is wrong")
            if any(abs(a - b) > 1e-9 for a, b in zip(pos, want[0])):
                raise _Mismatch("new position is wrong")
            if any(abs(a - b) > 1e-9 for a, b in zip(vel, want[1])):
                raise _Mismatch("velocity read back is wrong")
        return compare

    def cmp_reasons(want):
        def compare(got):
            reasons = _norm_reasons(got)
            if reasons != list(want):
                if sorted(reasons) == sorted(want):
                    raise _Mismatch("right reasons in the wrong order (use the documented fixed order)")
                if set(reasons) - set(want) and not set(want) - set(reasons):
                    raise _Mismatch("reports a reason that does not apply")
                if set(want) - set(reasons) and not set(reasons) - set(want):
                    raise _Mismatch("misses a reason that applies")
                raise _Mismatch("wrong set of rejection reasons")
        return compare

    def cmp_action(want):
        def compare(got):
            states, prog = _norm_action(got)
            if len(states) != len(want[0]) or len(prog) != len(want[1]):
                raise _Mismatch("states and progress need one entry per event")
            for i, (a, b) in enumerate(zip(states, want[0])):
                if a != b:
                    raise _Mismatch("state after event " + str(i) + " is wrong")
            for i, (a, b) in enumerate(zip(prog, want[1])):
                if abs(a - b) > 1e-9:
                    raise _Mismatch("progress after event " + str(i) + " is wrong")
        return compare

    def cmp_bool(want):
        def compare(got):
            if type(got) is not bool:
                raise _Mismatch("must return a real bool")
            if got != want:
                raise _Mismatch("wrong answer")
        return compare

    for i, (args, want) in enumerate(_L_CASES):
        run("lifecycle_next", "lifecycle_next case " + str(i) + " (" + args[0] + " + " + args[1] + ")", args,
            cmp_lifecycle(want))
    for i, (args, want) in enumerate(_W_CASES):
        for frozen in (False, True):
            run("write_cycle", "write_cycle case " + str(i) + " (" + args[0] + ")" + (" (tuples)" if frozen else ""),
                args, cmp_write(want), frozen)
    for i, (args, want) in enumerate(_V_CASES):
        for frozen in (False, True):
            run("validate_trajectory", "validate_trajectory case " + str(i) + (" (tuples)" if frozen else ""),
                args, cmp_reasons(want), frozen)
    for i, (args, want) in enumerate(_A_CASES):
        for frozen in (False, True):
            run("action_run", "action_run case " + str(i) + (" (tuples)" if frozen else ""), args,
                cmp_action(want), frozen)
    for i, (args, want) in enumerate(_S_CASES):
        for frozen in (False, True):
            run("segment_free", "segment_free case " + str(i) + (" (tuples)" if frozen else ""), args,
                cmp_bool(want), frozen)

    def sweep(name, label, cases, call, compare):
        """One line with a count and the first failing input, never the expected value."""
        if name in missing:
            return
        total = bad = 0
        first = None
        for args in cases:
            total += 1
            calls[name] = calls.get(name, 0) + 1
            try:
                got = call(*_fresh(args))
                compare(args, got)
            except NotImplementedError:
                missing.setdefault(name, []).append(label)
                return
            except _Mismatch as error:
                bad += 1
                if first is None:
                    first = (args, str(error))
            except Exception as error:
                bad += 1
                if first is None:
                    first = (args, _raised(error))
        if bad:
            failures.append(label + ": " + str(bad) + " of " + str(total) + " valid cases wrong; first: "
                            + first[1] + " for input " + repr(first[0]))

    size = _FAST
    sweep("lifecycle_next", "lifecycle_next sweep over every (state, request)",
          [(s, r) for s in LIFECYCLES for r in REQUESTS], lifecycle_next,
          lambda args, got: cmp_lifecycle(_lifecycle_ref(*args))(got))
    sweep("write_cycle", "write_cycle random sweep", _write_cases(size[1], 4141), write_cycle,
          lambda args, got: cmp_write(_write_ref(*args))(got))
    sweep("validate_trajectory", "validate_trajectory random sweep", _trajectory_cases(size[2], 5252),
          validate_trajectory, lambda args, got: cmp_reasons(_trajectory_ref(*args))(got))
    if ("act", size[2]) not in _MEMO:
        _MEMO[("act", size[2])] = _action_cases(size[2] // 2, 6363)
    sweep("action_run", "action_run sweep (every 3-event order and random 8-event traces)",
          _MEMO[("act", size[2])], action_run, lambda args, got: cmp_action(_action_ref(*args))(got))
    scenes = _scene_cases(size[3], 7474)
    sweep("segment_free", "segment_free random sweep (clearances above 0.01 m)", scenes, segment_free,
          lambda args, got: cmp_bool(_cached_free(args))(got))

    for label, name, args in _bad_cases():
        calls[name] = calls.get(name, 0) + 1
        live = _fresh(args)
        try:
            globals()[name](*live)
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            continue
        except Exception as error:
            failures.append("invalid " + label + ": raised " + type(error).__name__ + " instead of ValueError")
            continue
        failures.append("invalid " + label + ": returned instead of raising ValueError")
    summary = []
    for name, labels in missing.items():
        if len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels)) + " of "
                           + str(calls[name]) + " checks (first: " + labels[0] + "); finish it")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError; "
                           + str(calls[name]) + " checks skipped)")
    return summary + failures


def _cached_free(args):
    key = ("free", repr(args))
    if key not in _MEMO:
        _MEMO[key] = _free_ref(*args)
    return _MEMO[key]


if __name__ == "__main__":
    notes = []
    failures = self_check(notes)
    print("CoreLab manual mock interfaces self-check - mock simulation practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

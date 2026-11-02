"""CoreLab Visual Alignment lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the six functions below, then run your edited file locally:
  Windows: py -3 L17-alignment.v1.py
  macOS/Linux: python3 L17-alignment.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared model (synthetic geometry only, no image is ever read): a camera sits at
the origin of a BASE frame on a two-axis pan/tilt head. Base and camera axes use
the L16 pinhole conventions: x to the right, y DOWN, z forward (metres).
  pan  (rad): rotation about the vertical axis; positive pan turns the optical
              axis toward +x (to the right).
  tilt (rad): positive tilt turns the optical axis DOWN (toward +y).
  forward axis f  = ( sin(pan)*cos(tilt),  sin(tilt),  cos(pan)*cos(tilt) )
  camera x axis ex = ( cos(pan), 0, -sin(pan) )
  camera y axis ey = ( -sin(pan)*sin(tilt), cos(tilt), -cos(pan)*sin(tilt) )
  A base point p has camera coordinates (Xc, Yc, Zc) = (p.ex, p.ey, p.f); Zc is
  the depth. Normalized image coordinates are x = Xc/Zc and y = Yc/Zc: the
  tangents of the bearing angles, 0 at the image centre, x > 0 to the right of
  the centre and y > 0 below it. Intrinsics K = (fx, fy, cx, cy) in pixels give
  pixel (u, v) = (fx*x + cx, fy*y + cy). No lens distortion, no skew.
A detection is a row (label, colour, u, v, depth, stamp, conf):
  label  integer class id; colour integer colour id; (u, v) centroid in pixels;
  depth in metres as reported by a depth sensor (may be zero, negative or too
  large when the sensor failed); stamp in seconds; conf in [0, 1].
Colour is NOT evidence of identity: a distractor can share the target's colour
and the real target can appear in another colour. Never select by colour.

Contracts (all numbers finite int/float, never bool; label, colour and
max_steps are int; bounds inclusive; every sequence is a list or tuple; inputs
are never mutated; invalid input -> ValueError):
  project_target(pan, tilt, point) -> (x, y)
      Exact projection of the base-frame point (X, Y, Z) with the formulas above.
      Requires |pan|, |tilt| <= 10, |X|, |Y|, |Z| <= 1000, and depth Zc >= 1e-3;
      a point at or behind the camera plane (Zc < 1e-3) raises ValueError.
  pixel_error(K, u, v) -> (ex, ey) = ((u - cx)/fx, (v - cy)/fy)
      The OBSERVED normalized error of a measured centroid. 1 <= fx, fy <= 1e4,
      |cx|, |cy| <= 1e4, |u|, |v| <= 1e6.
  select_target(detections, label, now, limits) -> int index or None
      limits = (max_age, depth_min, depth_max, min_conf). A detection is VALID
      when ALL hold: its label equals label; age = now - stamp satisfies
      0 <= age <= max_age (an older detection is stale; a stamp in the future
      is invalid); depth_min <= depth <= depth_max; conf >= min_conf. Among the
      valid detections return the index (0-based) of the highest conf; a tie
      goes to the lowest index. Return None when no detection is valid or the
      list is empty. 0 to 50 rows; |u|, |v|, |depth|, |stamp|, |now| <= 1e6;
      0 <= label, colour <= 1000; 0 <= conf, min_conf <= 1; 0 <= max_age <= 1e3;
      1e-3 <= depth_min <= depth_max <= 1e4.
  servo_step(ex, ey, gain, wmax) -> (wpan, wtilt), rad/s
      Proportional command with PER-AXIS saturation:
      wpan = clip(gain*ex, -wmax, wmax), wtilt = clip(gain*ey, -wmax, wmax)
      (no minus sign: the pan/tilt signs above make a positive error mean turn
      positive). |ex|, |ey| <= 1000, 0 < gain <= 1000, 0 < wmax <= 10.
  servo_cycle(K, detections, label, now, limits, loop) -> (status, wpan, wtilt)
      loop = (gain, wmax, tol). Select the target as above; if none is valid,
      CANCEL: return ("stop", 0.0, 0.0). Otherwise take the observed error from
      the SELECTED detection's centroid with pixel_error; if |ex| <= tol and
      |ey| <= tol return ("aligned", 0.0, 0.0), else ("track", wpan, wtilt)
      from servo_step. 0 < gain <= 1000, 0 < wmax <= 10, 0 < tol <= 1.
      Never steer toward a rejected detection.
  run_suite(target, starts, gain, wmax, dt, tol, max_steps) -> list of int
      Closed-loop simulation of a fixed target (X, Y, Z) with 0.1 <= Z <= 1000,
      |X|, |Y| <= 1000. For each start (pan0, tilt0) (|.| <= 1 rad) run:
      for k = 0, 1, 2, ...: e = project_target(pan, tilt, target) (the
      geometry, not a pixel); if the target is not in front (project_target
      would raise) the result is -1; if |ex| <= tol and |ey| <= tol the result
      is k; if k == max_steps the result is -1; otherwise
      (wpan, wtilt) = servo_step(ex, ey, gain, wmax), pan += wpan*dt,
      tilt += wtilt*dt. Return one int per start, in order: the number of
      commands applied, or -1 (not converged within max_steps, or target lost).
      0 < dt <= 1, gain*dt <= 1 (1e-12 slack), wmax*dt <= 0.5 (one step turns at
      most 0.5 rad), 0 < tol <= 1, 1 <= max_steps <= 1000, 1 to 30 starts.
      All starts share one declared finite suite; passing it says nothing about
      other targets, gains or start offsets.
All returned numbers are finite; sequences are lists or tuples. Tolerances
(absolute, the larger of): geometry and commands 1e-9*max(1, |value|); indices
and step counts exact.

Pause before coding - write your predictions down first:
  1. Camera at pan = tilt = 0, a target at (0.4, 0.2, 2.0) m. Which normalized
     (x, y)? Is the target right or left of centre? Above or below it? Which way
     must each axis turn?
  2. The target sits straight ahead at (0, 0, 2) and the camera is panned
     0.3 rad to the right. Is x positive or negative? Why does the camera need
     a NEGATIVE pan command?
  3. A same-colour distractor has conf 0.95 and the true target 0.60. Which one
     does a colour-and-confidence rule pick? Which does the label rule pick?
  4. A detection is 0.6 s old and max_age is 0.5 s. What does a proportional
     controller do if it keeps using its pixels? What should the cycle do?
  5. Gain 2 and error 0.8 with wmax 1.0: what is the command? What does a
     saturated step do to the convergence time compared with a small error?
  6. With gain*dt = 1, how many steps would a linear plant need to reach zero
     error? Why does tan(angle) instead of the angle change that answer a little?
  7. The suite converged from every start offset you listed. What do you still
     not know about starts, targets or lighting outside the list?
Self-check tolerances are per-case numbers, not physical accuracy. Failure
messages name the case and the kind of mismatch, never the expected numbers.
"your code raised X on a VALID input" means the case is inside the contract and
must return; "invalid f(name=...)" lines are the opposite: that input must
raise ValueError. A function still raising NotImplementedError is reported
once, not once per case.
This kit covers a synthetic pan/tilt pinhole, labelled synthetic detections and a
bounded proportional step only: no image I/O, no feature detector, no 6-DOF
image Jacobian, no latency or motor dynamics, no physics simulator and no robot.
Reflection: why does converging on this finite suite NOT validate a real visual
servo? (Think about detector dropouts and false positives of another look, depth
sensor noise and holes, camera-to-motor latency, backlash and motor saturation,
lens distortion, rolling shutter and blur, lighting that shifts the colour, a
target that moves, and start offsets or gains you never tried.)
"""
import math


def project_target(pan, tilt, point):
    raise NotImplementedError("Build f, ex, ey from pan and tilt, dot with the point, divide by the depth")


def pixel_error(K, u, v):
    raise NotImplementedError("Normalized error ((u - cx)/fx, (v - cy)/fy)")


def select_target(detections, label, now, limits):
    raise NotImplementedError("Keep label, fresh, in-depth, confident detections; best conf wins")


def servo_step(ex, ey, gain, wmax):
    raise NotImplementedError("Per-axis clip(gain * error, -wmax, wmax)")


def servo_cycle(K, detections, label, now, limits, loop):
    raise NotImplementedError("Select, stop if none, else aligned inside tol, else a saturated step")


def run_suite(target, starts, gain, wmax, dt, tol, max_steps):
    raise NotImplementedError("Simulate pan/tilt from each start with the exact projection as the error")


# ---- SPOILER BELOW: the _ref_* functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _tol(want, base=1e-9):
    return base*max(1.0, abs(want))


def _ref_project(pan, tilt, point):
    sp, cp, st, ct = math.sin(pan), math.cos(pan), math.sin(tilt), math.cos(tilt)
    x, y, z = point
    depth = x*sp*ct + y*st + z*cp*ct
    if depth < 1e-3:
        return None
    return ((x*cp - z*sp)/depth, (-x*sp*st + y*ct - z*cp*st)/depth)


def _ref_pixel(K, u, v):
    return ((u - K[2])/K[0], (v - K[3])/K[1])


def _ref_valid(row, label, now, limits):
    max_age, dmin, dmax, min_conf = limits
    age = now - row[5]
    return (row[0] == label and 0 <= age <= max_age and dmin <= row[4] <= dmax
            and row[6] >= min_conf)


def _ref_select(detections, label, now, limits):
    best = None
    for i, row in enumerate(detections):
        if _ref_valid(row, label, now, limits) and (best is None or row[6] > detections[best][6]):
            best = i
    return best


def _clip(value, bound):
    return max(-bound, min(bound, value))


def _ref_step(ex, ey, gain, wmax):
    return (_clip(gain*ex, wmax), _clip(gain*ey, wmax))


def _ref_cycle(K, detections, label, now, limits, loop):
    gain, wmax, tol = loop
    index = _ref_select(detections, label, now, limits)
    if index is None:
        return ("stop", 0.0, 0.0)
    ex, ey = _ref_pixel(K, detections[index][2], detections[index][3])
    if abs(ex) <= tol and abs(ey) <= tol:
        return ("aligned", 0.0, 0.0)
    wpan, wtilt = _ref_step(ex, ey, gain, wmax)
    return ("track", wpan, wtilt)


def _ref_suite(target, starts, gain, wmax, dt, tol, max_steps):
    out = []
    for pan, tilt in starts:
        result = -1
        for k in range(max_steps + 1):
            err = _ref_project(pan, tilt, target)
            if err is None:
                break
            if abs(err[0]) <= tol and abs(err[1]) <= tol:
                result = k
                break
            if k == max_steps:
                break
            wpan, wtilt = _ref_step(err[0], err[1], gain, wmax)
            pan += wpan*dt
            tilt += wtilt*dt
        out.append(result)
    return out


_S2 = 2 ** 0.5
# (pan, tilt, point) -> (x, y) or None when the point is not in front. Hand anchors
# first (exact tangents), then generic poses checked against the reference.
_PROJECT_CASES = [
    ((0.0, 0.0, (0.0, 0.0, 2.0)), (0.0, 0.0)),
    ((0.0, 0.0, (1.0, 0.5, 2.0)), (0.5, 0.25)),
    ((0.0, 0.0, (-0.4, 0.2, 2.0)), (-0.2, 0.1)),
    ((math.pi/4, 0.0, (2.0, 0.0, 2.0)), (0.0, 0.0)),
    ((math.pi/4, 0.0, (0.0, 0.0, 2.0)), (-1.0, 0.0)),
    ((0.0, math.pi/4, (0.0, 2.0, 2.0)), (0.0, 0.0)),
    ((0.0, math.pi/4, (0.0, 0.0, 2.0)), (0.0, -1.0)),
    ((math.pi/4, 0.0, (0.0, 1.0, 1.0)), (-1.0, _S2)),
    ((-math.pi/4, 0.0, (0.0, 0.0, 1.0)), (1.0, 0.0)),
    ((0.0, 0.0, (0.0, 0.0, 0.001)), (0.0, 0.0)),
    ((0.3, -0.2, (1.0, -0.5, 3.0)), None),
    ((-0.7, 0.4, (0.25, 0.75, 1.5)), None),
    ((1.2, 0.9, (3.0, 2.0, 1.0)), None),
    ((-2.0, 0.5, (-5.0, 1.0, -1.0)), None),
    ((10.0, -10.0, (100.0, -200.0, 300.0)), None),
    ((0.0, 0.0, (1000.0, 1000.0, 1000.0)), None),
    ((0.5, 0.5, (0.0, 0.0, 0.0009)), "invalid"),
]
_K = (500.0, 400.0, 320.0, 240.0)
# (K, u, v) -> (ex, ey)
_PIXEL_CASES = [
    ((_K, 320.0, 240.0), (0.0, 0.0)),
    ((_K, 570.0, 240.0), (0.5, 0.0)),
    ((_K, 320.0, 80.0), (0.0, -0.4)),
    ((_K, 120.0, 400.0), (-0.4, 0.4)),
    (((512, 384, 320, 240), 352, 264), (0.0625, 0.0625)),
    (((800.0, 800.0, 0.0, 0.0), -400.0, 200.0), (-0.5, 0.25)),
    (((1, 1, 0, 0), 1000000, -1000000), (1000000.0, -1000000.0)),
]
_LIM = (0.5, 0.25, 4.0, 0.5)
_NOW = 10.0


def _d(label=7, colour=1, u=320.0, v=240.0, depth=1.0, stamp=10.0, conf=0.75):
    return (label, colour, u, v, depth, stamp, conf)


# (detections, label, now, limits) -> index or None
_SELECT_CASES = [
    (([_d()], 7, _NOW, _LIM), 0),
    (([], 7, _NOW, _LIM), None),
    # same-colour distractor with the higher confidence must lose
    (([_d(label=3, conf=0.95), _d(conf=0.625)], 7, _NOW, _LIM), 1),
    # the true target in a shifted colour is still the target
    (([_d(colour=9, conf=0.625), _d(label=3, colour=1, conf=0.875)], 7, _NOW, _LIM), 0),
    # stale best detection loses to a fresh weaker one; age 0.5 is allowed, 0.75 is not
    (([_d(stamp=9.25, conf=0.875), _d(stamp=9.5, conf=0.625)], 7, _NOW, _LIM), 1),
    (([_d(stamp=9.5)], 7, _NOW, _LIM), 0),
    (([_d(stamp=9.25)], 7, _NOW, _LIM), None),
    # a stamp in the future is invalid; age exactly 0 is valid
    (([_d(stamp=10.25, conf=0.875), _d(stamp=10.0, conf=0.625)], 7, _NOW, _LIM), 1),
    # depth window: both ends valid, outside invalid (zero, negative, too small, too large)
    (([_d(depth=0.25)], 7, _NOW, _LIM), 0),
    (([_d(depth=4.0)], 7, _NOW, _LIM), 0),
    (([_d(depth=0.125, conf=0.875), _d(depth=4.125, conf=0.875), _d(depth=0.0, conf=0.875),
       _d(depth=-1.0, conf=0.875), _d(depth=2.0, conf=0.625)], 7, _NOW, _LIM), 4),
    # confidence threshold is inclusive
    (([_d(conf=0.5)], 7, _NOW, _LIM), 0),
    (([_d(conf=0.4375)], 7, _NOW, _LIM), None),
    # tie on confidence goes to the lowest index; a later better one wins
    (([_d(conf=0.75), _d(conf=0.75)], 7, _NOW, _LIM), 0),
    (([_d(conf=0.625), _d(conf=0.75), _d(conf=0.6875)], 7, _NOW, _LIM), 1),
    # nothing valid: only wrong labels
    (([_d(label=2), _d(label=5)], 7, _NOW, _LIM), None),
    # label 0 and a different max_age/limits set
    (([_d(label=0, stamp=7.5, conf=0.25), _d(label=0, stamp=9.0, conf=0.125)], 0, _NOW,
      (3.0, 0.25, 4.0, 0.125)), 0),
    (([_d(label=0, stamp=6.5, conf=0.25), _d(label=0, stamp=9.0, conf=0.125)], 0, _NOW,
      (3.0, 0.25, 4.0, 0.125)), 1),
    # a distractor whose colour id equals the wanted label must not match
    (([_d(label=3, colour=7, conf=0.95), _d(label=7, colour=2, conf=0.625)], 7, _NOW, _LIM), 1),
    (([_d(label=3, colour=7, conf=0.95)], 7, _NOW, _LIM), None),
    # max_age 0 keeps only a detection stamped exactly now
    (([_d(stamp=9.75), _d(stamp=10.0, conf=0.5)], 7, _NOW, (0.0, 0.25, 4.0, 0.5)), 1),
]
# (ex, ey, gain, wmax) -> (wpan, wtilt)
_STEP_CASES = [
    ((0.2, -0.1, 1.5, 2.0), (0.3, -0.15)),
    ((0.0, 0.0, 1.5, 2.0), (0.0, 0.0)),
    ((2.0, -3.0, 1.5, 2.0), (2.0, -2.0)),
    ((2.0, 0.2, 1.5, 2.0), (2.0, 0.3)),
    ((-0.2, 4.0, 2.0, 0.5), (-0.4, 0.5)),
    ((1.0, -1.0, 2.0, 2.0), (2.0, -2.0)),
    ((0.8, 0.8, 2.0, 1.0), (1.0, 1.0)),
    ((1000.0, -1000.0, 1000.0, 10.0), (10.0, -10.0)),
    ((0.001, -0.002, 0.5, 10.0), (0.0005, -0.001)),
    ((3, -1, 1, 4), (3.0, -1.0)),
]
_KS = (512.0, 384.0, 320.0, 240.0)
_LOOP = (1.5, 0.5, 0.0625)
# (K, detections, label, now, limits, loop) -> (status, wpan, wtilt)
_CYCLE_CASES = [
    # far right of centre: saturated pan, no tilt
    ((_KS, [_d(u=576.0, v=240.0)], 7, _NOW, _LIM, _LOOP), ("track", 0.5, 0.0)),
    # small error on both axes, not saturated
    ((_KS, [_d(u=336.0, v=288.0)], 7, _NOW, _LIM, _LOOP), ("track", 0.046875, 0.1875)),
    # exactly on the tolerance boundary on both axes: aligned
    ((_KS, [_d(u=352.0, v=264.0)], 7, _NOW, _LIM, _LOOP), ("aligned", 0.0, 0.0)),
    ((_KS, [_d(u=288.0, v=216.0)], 7, _NOW, _LIM, _LOOP), ("aligned", 0.0, 0.0)),
    # one pixel outside on one axis: track
    ((_KS, [_d(u=353.0, v=264.0)], 7, _NOW, _LIM, _LOOP), ("track", 0.0966796875, 0.09375)),
    ((_KS, [_d(u=-192.0, v=240.0)], 7, _NOW, _LIM, _LOOP), ("track", -0.5, 0.0)),
    # a wrong-label distractor at the centre and more confident: follow the target
    ((_KS, [_d(label=3, u=320.0, v=240.0, conf=0.95), _d(u=448.0, v=240.0, conf=0.625)],
      7, _NOW, _LIM, _LOOP), ("track", 0.375, 0.0)),
    # only a stale target (a fresh distractor is present): cancel
    ((_KS, [_d(stamp=9.0, u=448.0), _d(label=3, u=448.0)], 7, _NOW, _LIM, _LOOP), ("stop", 0.0, 0.0)),
    # no detections: cancel
    ((_KS, [], 7, _NOW, _LIM, _LOOP), ("stop", 0.0, 0.0)),
    # invalid depth only: cancel
    ((_KS, [_d(depth=0.0, u=448.0), _d(depth=-2.0, u=448.0)], 7, _NOW, _LIM, _LOOP),
     ("stop", 0.0, 0.0)),
    # low confidence only: cancel
    ((_KS, [_d(conf=0.25, u=448.0)], 7, _NOW, _LIM, _LOOP), ("stop", 0.0, 0.0)),
    # the aligned decision uses the selected detection, not another valid one
    ((_KS, [_d(u=320.0, v=240.0, conf=0.875), _d(u=576.0, v=240.0, conf=0.625)],
      7, _NOW, _LIM, _LOOP), ("aligned", 0.0, 0.0)),
    # a shifted colour does not matter
    ((_KS, [_d(colour=200, u=384.0, v=240.0)], 7, _NOW, _LIM, _LOOP), ("track", 0.1875, 0.0)),
    # selected detection decides even when a lower-confidence one sits closer
    ((_KS, [_d(u=576.0, v=432.0, conf=0.875), _d(u=330.0, v=250.0, conf=0.625)],
      7, _NOW, _LIM, _LOOP), ("track", 0.5, 0.5)),
    # upper tolerance bound: tol = 1 accepts normalized errors up to 1 on both axes
    ((_KS, [_d(u=832.0, v=624.0)], 7, _NOW, _LIM, (1.5, 0.5, 1.0)), ("aligned", 0.0, 0.0)),
    ((_KS, [_d(u=833.0, v=240.0)], 7, _NOW, _LIM, (1.5, 0.5, 1.0)), ("track", 0.5, 0.0)),
    ((_KS, [_d(u=576.0, v=240.0)], 7, _NOW, _LIM, (1.5, 0.5, 0.75)), ("aligned", 0.0, 0.0)),
]
_T0 = (0.0, 0.0, 2.0)
_T1 = (1.0, -0.5, 2.0)
_STARTS0 = [(0.5, 0.0), (0.0, 0.3), (0.2, -0.2), (-0.4, 0.4), (0.0, 0.0)]
_STARTS1 = [(0.0, 0.0), (-0.3, 0.2), (0.6, -0.4), (0.9, 0.9), (-0.9, -0.9)]
# (target, starts, gain, wmax, dt, tol, max_steps) -> step counts
_SUITE_CASES = [
    ((_T0, _STARTS0, 2.0, 0.4, 0.25, 0.03, 40), None),
    ((_T0, _STARTS0, 4.0, 0.4, 0.25, 0.03, 40), None),
    ((_T1, _STARTS1, 2.0, 0.4, 0.25, 0.03, 40), None),
    ((_T1, _STARTS1, 3.0, 2.0, 0.25, 0.03, 40), None),
    # a small step budget fails the far starts
    ((_T0, _STARTS0, 2.0, 0.4, 0.25, 0.03, 4), None),
    # target lost: the start camera looks away from a far-right target
    (((3.0, 0.0, 0.5), [(-1.0, 0.0), (0.5, 0.0), (1.0, 1.0)], 2.0, 0.4, 0.25, 0.03, 60), None),
    # an already aligned start needs 0 steps; a loose tolerance finishes early
    ((_T0, [(0.0, 0.0), (0.02, -0.02)], 2.0, 0.4, 0.25, 0.03, 10), None),
    ((_T0, [(0.5, 0.0), (0.0, -0.9)], 1.0, 0.5, 0.5, 0.5, 10), None),
    # slow gain: saturation never reached
    ((_T0, [(0.05, 0.0), (0.0, -0.05)], 0.5, 0.4, 0.25, 0.01, 100), None),
    # steps limited by saturation (wmax*dt = 0.05)
    ((_T0, [(1.0, 1.0), (-1.0, 0.0)], 4.0, 0.2, 0.25, 0.02, 100), None),
    # single-step budget: only a start already inside the tolerance succeeds
    ((_T0, [(0.0, 0.0), (0.03, 0.0), (0.2, 0.0)], 4.0, 0.4, 0.25, 0.05, 1), None),
    # the start error sits exactly on the tolerance (x = 0.5, y = 0.25): 0 steps, inclusive
    ((_T1, [(0.0, 0.0), (0.3, 0.0), (0.0, 0.3)], 1.0, 0.5, 0.5, 0.5, 10), None),
    # a target off the axis couples pan and tilt: both axes use the same error each step
    (((1.0, 1.0, 1.0), [(0.2, -0.2)], 1.0, 0.5, 0.25, 0.03, 40), None),
    # tolerance 1 (upper bound): aligned at once from a modest start
    ((_T0, [(0.5, 0.0), (0.7, 0.7)], 1.0, 0.5, 0.25, 1.0, 10), None),
    # only one axis is inside the tolerance at the start (x = 0.5, y = 0.25 > 0.2)
    ((_T1, [(0.0, 0.0)], 1.0, 0.5, 0.5, 0.2, 10), None),
]


def _fresh(value):
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _copy(value):
    if isinstance(value, tuple):
        return tuple(_copy(v) for v in value)
    if isinstance(value, list):
        return [_copy(v) for v in value]
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
        ok, got = attempt(name, label, function, _fresh(args) if index % 2 else _copy(args))
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def pair(got, want, what):
        if (not isinstance(got, (list, tuple)) or len(got) != 2
                or not all(_real(g) for g in got)):
            raise _Mismatch("output must be two finite numbers")
        for g, w, axis in zip(got, want, ("first", "second")):
            if not abs(g - w) <= _tol(w):
                raise _Mismatch(what + " " + axis + " value is wrong (relative tolerance 1e-9)")

    for i, (args, want) in enumerate(_PROJECT_CASES):
        if want == "invalid":
            continue
        if want is None:
            want = _ref_project(*args)
        run("project_target", "project_target " + str(i), project_target, args,
            lambda got, want=want: pair(got, want, "normalized coordinate"), i)

    for i, (args, want) in enumerate(_PIXEL_CASES):
        run("pixel_error", "pixel_error " + str(i), pixel_error, args,
            lambda got, want=want: pair(got, want, "pixel error"), i)

    for i, (args, want) in enumerate(_SELECT_CASES):
        def compare(got, want=want):
            if got is not None and (type(got) is not int):
                raise _Mismatch("output must be an int index or None")
            if got is None and want is not None:
                raise _Mismatch("no detection returned although one is valid")
            if got is not None and want is None:
                raise _Mismatch("a detection was returned although none is valid")
            if got != want:
                raise _Mismatch("the selected detection is wrong")
        run("select_target", "select_target " + str(i), select_target, args, compare, i)

    for i, (args, want) in enumerate(_STEP_CASES):
        run("servo_step", "servo_step " + str(i), servo_step, args,
            lambda got, want=want: pair(got, want, "command"), i)

    for i, (args, want) in enumerate(_CYCLE_CASES):
        def compare(got, want=want):
            if not isinstance(got, (list, tuple)) or len(got) != 3 or type(got[0]) is not str:
                raise _Mismatch("output must be (status string, wpan, wtilt)")
            if got[0] != want[0]:
                raise _Mismatch("the status is wrong")
            pair(got[1:], want[1:], "command")
        run("servo_cycle", "servo_cycle " + str(i), servo_cycle, args, compare, i)

    for i, (args, want) in enumerate(_SUITE_CASES):
        want = _ref_suite(*args)

        def compare(got, want=want):
            if (not isinstance(got, (list, tuple)) or len(got) != len(want)
                    or not all(type(g) is int for g in got)):
                raise _Mismatch("output must be one int per start")
            if list(got) != want:
                bad = [str(k) for k in range(len(want)) if got[k] != want[k]]
                raise _Mismatch("the result is wrong for start(s) " + ", ".join(bad))
        run("run_suite", "run_suite " + str(i), run_suite, args, compare, i)

    # non-mutation of nested inputs
    if "select_target" not in missing:
        dets = [_d(label=3, conf=0.95), _d(conf=0.625), _d(stamp=9.0, conf=0.875)]
        before = [list(r) for r in dets]
        try:
            select_target(dets, 7, _NOW, _LIM)
            if [list(r) for r in dets] != before:
                failures.append("select_target input-mutation check: your function changed the detections")
        except Exception:
            pass
    if "servo_cycle" not in missing:
        dets = [_d(label=3, conf=0.95), _d(u=448.0, conf=0.625)]
        before = [list(r) for r in dets]
        try:
            servo_cycle(_KS, dets, 7, _NOW, _LIM, _LOOP)
            if [list(r) for r in dets] != before:
                failures.append("servo_cycle input-mutation check: your function changed the detections")
        except Exception:
            pass
    if "run_suite" not in missing:
        starts = [[0.5, 0.0], [0.0, 0.3]]
        before = [list(s) for s in starts]
        try:
            run_suite(_T0, starts, 2.0, 0.4, 0.25, 0.03, 20)
            if starts != before:
                failures.append("run_suite input-mutation check: your function changed the starts")
        except Exception:
            pass

    nan, inf = float('nan'), float('inf')
    scalar = [nan, inf, -inf, True, "1", None]
    row = (7, 1, 320.0, 240.0, 1.0, 10.0, 0.75)

    def bad_rows(ok_row):
        out = [None, "abc", (1,), ok_row[:6], ok_row + (0,), 5]
        for slot, values in {
                0: [-1, 1001, 7.0, True, "7", None], 1: [-1, 1001, 1.0, True, "1", None],
                2: scalar + [1000001.0, -1000001.0], 3: scalar + [1000001.0, -1000001.0],
                4: scalar + [1000001.0, -1000001.0], 5: scalar + [1000001.0, -1000001.0],
                6: scalar + [-0.01, 1.01]}.items():
            for value in values:
                out.append(ok_row[:slot] + (value,) + ok_row[slot+1:])
        return out

    dets_bad = [None, "abc", 5, {0: row}, [row]*51] + [[r] for r in bad_rows(row)]
    kbad = [None, "abcd", 5, (500, 500, 320), (500, 500, 320, 240, 1), (0.99, 500, 320, 240),
            (500, 0.99, 320, 240), (10000.01, 500, 320, 240), (500, 10000.01, 320, 240),
            (500, 500, 10000.01, 240), (500, 500, 320, -10000.01), (nan, 500, 320, 240),
            (500, inf, 320, 240), (True, 500, 320, 240), ("500", 500, 320, 240),
            (500, 500, None, 240)]
    limits_bad = [None, "abcd", 5, (0.5, 0.25, 4.0), (0.5, 0.25, 4.0, 0.5, 1), (-0.01, 0.25, 4.0, 0.5),
                  (1000.01, 0.25, 4.0, 0.5), (0.5, 0.0009, 4.0, 0.5), (0.5, 0.25, 0.2, 0.5),
                  (0.5, 0.25, 10000.01, 0.5), (0.5, 0.25, 4.0, -0.01), (0.5, 0.25, 4.0, 1.01),
                  (nan, 0.25, 4.0, 0.5), (0.5, inf, 4.0, 0.5), (True, 0.25, 4.0, 0.5),
                  ("0.5", 0.25, 4.0, 0.5), (0.5, 0.25, 4.0, None)]
    loop_bad = [None, "abc", 5, (1.5, 0.5), (1.5, 0.5, 0.1, 1), (0.0, 0.5, 0.1), (-1.0, 0.5, 0.1),
                (1000.01, 0.5, 0.1), (1.5, 0.0, 0.1), (1.5, 10.01, 0.1), (1.5, 0.5, 0.0),
                (1.5, 0.5, 1.01), (nan, 0.5, 0.1), (1.5, inf, 0.1), (True, 0.5, 0.1),
                ("1.5", 0.5, 0.1), (1.5, 0.5, None)]
    bad = {
        "pan": [10.01, -10.01, 1.5707963267948966, nan, inf, True, "1", None],
        "tilt": [10.01, -10.01, 1.5707963267948966, nan, inf, True, "1", None],
        "point": [None, "abc", (0, 0), (0, 0, 1, 1), (0, 0, "1"), (0, 0, nan), (0, nan, 1),
                  (0, 0, True), (0, 0, 1000.01), (1000.01, 0, 1), (0, -1000.01, 1), (0, 0, 0.0),
                  (0, 0, 0.0009), (0, 0, -1.0), [], {0: 1}],
        "K": kbad,
        "u": scalar + [1000001.0, -1000001.0],
        "v": scalar + [1000001.0, -1000001.0],
        "detections": dets_bad,
        "label": [-1, 1001, 7.0, True, "7", None, nan],
        "now": scalar + [1000001.0, -1000001.0],
        "limits": limits_bad,
        "loop": loop_bad,
        "ex": scalar + [1000.01, -1000.01],
        "ey": scalar + [1000.01, -1000.01],
        "gain": [0.0, -1.0, 1000.01, nan, inf, True, "1", None],
        "wmax": [0.0, -1.0, 10.01, nan, inf, True, "1", None],
        "target": [None, "abc", (0, 0), (0, 0, 2, 1), (0, 0, 0.09), (1000.01, 0, 2), (0, -1000.01, 2),
                   (0, 0, 1000.01), (nan, 0, 2), (0, 0, True), (0, 0, "2"), [], {0: 1}],
        "starts": [[], (), None, "abc", [(0,)], [(0, 0, 0)], [(1.01, 0)], [(0, -1.01)], [(nan, 0)],
                   [(True, 0)], [(0, "0")], [None], [(0.0, 0.0)]*31, {0: (0, 0)}],
        "dt": [0.0, -0.1, 1.01, 0.51, nan, inf, True, "0.25", None],
        "tol": [0.0, -0.1, 1.01, nan, inf, True, "0.1", None],
        "max_steps": [0, -1, 1001, 5.0, True, "5", None, nan],
    }
    run_bad_gain = [0.0, -1.0, 1000.01, 4.01, nan, inf, True, "1", None]
    run_bad_wmax = [0.0, -1.0, 10.01, 2.1, nan, inf, True, "1", None]
    signatures = [
        ("project_target", project_target, ("pan", "tilt", "point"), (0.0, 0.0, (0.0, 0.0, 2.0))),
        ("pixel_error", pixel_error, ("K", "u", "v"), (_KS, 400.0, 300.0)),
        ("select_target", select_target, ("detections", "label", "now", "limits"),
         ([row], 7, _NOW, _LIM)),
        ("servo_step", servo_step, ("ex", "ey", "gain", "wmax"), (0.2, 0.1, 1.5, 2.0)),
        ("servo_cycle", servo_cycle, ("K", "detections", "label", "now", "limits", "loop"),
         (_KS, [row], 7, _NOW, _LIM, _LOOP)),
        ("run_suite", run_suite, ("target", "starts", "gain", "wmax", "dt", "tol", "max_steps"),
         (_T0, [(0.3, 0.1)], 2.0, 0.4, 0.25, 0.03, 20)),
    ]
    for title, function, names, args in signatures:
        for slot, name in enumerate(names):
            values = bad[name]
            if title == "run_suite" and name == "gain":
                values = run_bad_gain
            if title == "run_suite" and name == "wmax":
                values = run_bad_wmax
            if title in ("select_target", "servo_cycle") and name == "now":
                values = scalar + [1000001.0, -1000001.0]
            for value in values:
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

    # a point behind the camera through the pose (not the point): invalid
    try:
        project_target(1.5707963267948966, 0.0, (0.0, 0.0, 1.0))
        failures.append("invalid project_target(pose puts the point beside the camera plane): "
                        "returned instead of raising ValueError")
    except (NotImplementedError, ValueError):
        pass
    except Exception as error:
        failures.append("invalid project_target(pose puts the point beside the camera plane): raised "
                        + type(error).__name__ + " instead of ValueError")

    summary = []
    for name, labels in missing.items():
        summary.append(name + ": not implemented yet (raises NotImplementedError; "
                       + str(len(labels)) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual visual alignment self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

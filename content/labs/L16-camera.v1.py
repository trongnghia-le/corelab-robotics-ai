"""CoreLab Pinhole Camera and Calibration lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the seven functions below, then run your edited file locally:
  Windows: py -3 L16-camera.v1.py
  macOS/Linux: python3 L16-camera.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Declared model (synthetic geometry only, no image is ever read):
  Camera frame: +X to the right of the image, +Y DOWN the image, +Z forward
  along the optical axis. A point is IN FRONT of the camera when its camera Z
  is positive; Z is the depth in metres. Pixel (u, v): u to the right, v down.
  Intrinsics K = (fx, fy, cx, cy): focal lengths in PIXELS and the principal
  point in pixels. Ideal pinhole, NO lens distortion, no skew:
      u = fx*X/Z + cx,      v = fy*Y/Z + cy.
  Extrinsics (R, t) map a WORLD point to the camera frame:
      p_cam = R*p_world + t.
  R is a 3x3 rotation (columns = the world axes written in camera axes) and t
  is the camera-frame position of the world origin, in metres. R is given as
  three rows. The inverse is p_world = R^T*(p_cam - t).

Contracts (all numbers finite int/float, never bool; bounds inclusive; every
sequence is a list or tuple; inputs are never mutated):
  world_to_camera(R, t, p) -> (X, Y, Z) = R*p + t
      Pure rigid transform. It does NOT check depth: the returned Z may be zero
      or negative (the point is then behind the camera).
  project(K, p_cam) -> (u, v), pixels
      Requires 1e-3 <= Z <= 1e4 (metres). Z below 1e-3 - zero, or negative,
      which means behind the camera - raises ValueError; never divide by zero,
      never return a "mirrored" pixel for a point behind the camera.
  deproject(K, u, v, depth) -> (X, Y, Z) in the camera frame, Z = depth
      The pixel (u, v) and the DEPTH Z (not the range along the ray) give one
      3-D point. Requires 1e-3 <= depth <= 1e4; otherwise ValueError.
  pixel_to_world(K, R, t, u, v, depth) -> (x, y, z) in the world frame
      deproject, then invert the extrinsics: R^T*(p_cam - t).
  reprojection_rms(K, points, pixels) -> RMS reprojection error, in pixels
      points: n camera-frame points (valid depth as in project), pixels: n
      measured (u, v). error_i = distance in pixels between project(K, point_i)
      and pixel_i. Return sqrt(sum(error_i^2)/n), the root mean square of the
      Euclidean pixel distances (NOT the mean of the distances, NOT n-1).
  fit_intrinsics(points, pixels) -> (fx, fy, cx, cy)
      A LINEAR calibrator with KNOWN camera-frame points (so no extrinsics and
      no pose are estimated). With x = X/Z and y = Y/Z it fits the two
      independent 2-parameter least-squares lines
          u ~ fx*x + cx      and      v ~ fy*y + cy,
      minimising the sum of squared residuals of each line (ordinary least
      squares on the pixel side). The answer is returned as fitted: fx, fy are
      not forced to be positive. Needs n >= 2; if max(x) - min(x) < 1e-6 or
      max(y) - min(y) < 1e-6 the fit cannot separate focal length from the
      principal point: raise ValueError.
  split_eval(points, pixels, n_train) -> (K, train_rms, test_rms)
      The train/test split is by ORDER: the first n_train correspondences
      are the TRAINING views, the rest (at least one) are the HELD-OUT test
      views. Fit with fit_intrinsics on the training views ONLY, return the
      fitted K as a 4-tuple, the reprojection RMS of that K on the training
      views and its RMS on the held-out views. Using any held-out point in the
      fit is leakage and makes test_rms meaningless. Requires 2 <= n_train <=
      n - 1 and the fit conditions above on the training points.
Bounds: R a 3x3 rotation with R*R^T = I and det R = +1 (each entry within 1e-9)
- a reflection or a scaled matrix is ValueError; |t_i| <= 1e4; world |p_i| <=
1e4; camera X, Y within +-1e4; 1 <= fx, fy <= 1e4 and |cx|, |cy| <= 1e4 for K
passed IN; |u|, |v| <= 1e6; depth as above; 1 <= n <= 200 (fit/split: n >= 2
and n >= 3 respectively), points and pixels the same length; n_train an int
(not bool or float). Invalid inputs (wrong type or shape, bool, NaN,
infinity, out of bounds) raise ValueError. All returned numbers are finite
float/int; returned sequences are lists or tuples. Outputs of deproject and
pixel_to_world are NOT range-checked: they may exceed +-1e4 for extreme pixels and depths.
Tolerances (absolute, the larger of): coordinates and pixels 1e-9*max(1,|value|);
RMS values and fitted parameters 1e-6*max(1,|value|). The self-check compares
fits with the normal-equation conditions as well as with a reference.

Pause before coding - write your predictions down first:
  1. A point 2 m in front, 0.4 m to the right, 0.2 m above the axis; fx = fy =
     500, (cx, cy) = (320, 240). Which pixel? Is v above or below cy, and why?
  2. The same point at 4 m: which pixel moves toward the principal point, and
     by how much? Can a pixel tell you the depth?
  3. R maps world to camera. If you use R where R^T belongs, which points
     still come out right (name two special rotations) and which do not?
  4. What should project do for Z = 0? For Z = -1 (behind the camera)? What
     would a "mirrored" pixel look like to a downstream planner?
  5. A fit on two points gives a perfect train RMS. What does a held-out RMS
     of several pixels tell you that the train RMS cannot?
  6. Why does a fit with all points at the same x/Z have no unique (fx, cx)?
  7. If you calibrate on points near the image centre and test far from it, what
     could a larger held-out error mean, in this ideal-pinhole model?
Self-check tolerances are per-case numbers, not physical accuracy. Failure
messages name the case and the kind of mismatch, never the expected numbers.
"your code raised X on a VALID input" means the case is inside the contract and
must return; "invalid f(name=...)" lines are the opposite: that input must
raise ValueError. A function still raising NotImplementedError is reported
once, not once per case.
This kit covers a synthetic ideal pinhole, a declared rigid transform and a
two-line linear intrinsic fit only: no image I/O, no corner detection, no
Zhang-style calibration with unknown poses, no lens distortion, no PnP, no
stereo, no rolling shutter and no device calibration.
Reflection: why does a small reprojection error here NOT validate a real camera
calibration? (Think about lens distortion, a printed target that is not flat,
corner detection error, too few poses or poses that do not excite the model,
focus and zoom changes, temperature, rolling shutter and motion blur, a
hand-eye transform that was never measured, and error that is small on the
training views but large away from them.)
"""
import math


def world_to_camera(R, t, p):
    raise NotImplementedError("p_cam = R*p + t: rows of R times p, then add t")


def project(K, p_cam):
    raise NotImplementedError("Reject depth below 1e-3 first, then u = fx*X/Z + cx, v = fy*Y/Z + cy")


def deproject(K, u, v, depth):
    raise NotImplementedError("Invert the projection for a known depth")


def pixel_to_world(K, R, t, u, v, depth):
    raise NotImplementedError("Deproject, then R^T*(p_cam - t)")


def reprojection_rms(K, points, pixels):
    raise NotImplementedError("Project each point, take Euclidean pixel distances, root mean square")


def fit_intrinsics(points, pixels):
    raise NotImplementedError("Two independent least-squares lines: u on X/Z and v on Y/Z")


def split_eval(points, pixels, n_train):
    raise NotImplementedError("Fit on the first n_train points only; report train and held-out RMS")


# ---- SPOILER BELOW: the _..._ref functions are complete references, ----
# ---- and the case tables hold expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _rot(axis, angle):
    """Rodrigues rotation matrix (rows) about a non-zero axis."""
    n = math.sqrt(sum(a*a for a in axis))
    x, y, z = (a/n for a in axis)
    c, s = math.cos(angle), math.sin(angle)
    w = 1 - c
    return ((c + x*x*w, x*y*w - z*s, x*z*w + y*s),
            (y*x*w + z*s, c + y*y*w, y*z*w - x*s),
            (z*x*w - y*s, z*y*w + x*s, c + z*z*w))


def _wtc_ref(R, t, p):
    return tuple(sum(R[i][j]*p[j] for j in range(3)) + t[i] for i in range(3))


def _project_ref(K, p):
    return (K[2] + K[0]*(p[0]/p[2]), K[3] + K[1]*(p[1]/p[2]))


def _deproject_ref(K, u, v, d):
    return ((u - K[2])*d/K[0], (v - K[3])*d/K[1], d)


def _p2w_ref(K, R, t, u, v, d):
    c = _deproject_ref(K, u, v, d)
    q = [c[i] - t[i] for i in range(3)]
    return tuple(sum(R[j][i]*q[j] for j in range(3)) for i in range(3))


def _rms_ref(K, pts, pix):
    total = 0.0
    for p, m in zip(pts, pix):
        u, v = _project_ref(K, p)
        total += (u - m[0])**2 + (v - m[1])**2
    return math.sqrt(total/len(pts))


def _line_ref(xs, ys):
    """Slope and intercept of the least-squares line, centred formulas."""
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x - mx)**2 for x in xs)
    sxy = sum((x - mx)*(y - my) for x, y in zip(xs, ys))
    slope = sxy/sxx
    return slope, my - slope*mx


def _fit_ref(pts, pix):
    fx, cx = _line_ref([p[0]/p[2] for p in pts], [m[0] for m in pix])
    fy, cy = _line_ref([p[1]/p[2] for p in pts], [m[1] for m in pix])
    return (fx, fy, cx, cy)


def _split_ref(pts, pix, n):
    K = _fit_ref(pts[:n], pix[:n])
    return (K, _rms_ref(K, pts[:n], pix[:n]), _rms_ref(K, pts[n:], pix[n:]))


def _normal_equations_hold(K, pts, pix, tol):
    """Least-squares optimality: u/v residuals sum to zero and are orthogonal to x/y."""
    n = len(pts)
    scale = max(1.0, max(abs(m[0]) for m in pix), max(abs(m[1]) for m in pix))
    for axis, f, c in ((0, K[0], K[2]), (1, K[1], K[3])):
        res = [pix[i][axis] - (f*(pts[i][axis]/pts[i][2]) + c) for i in range(n)]
        if abs(sum(res)) > tol*scale*n:
            return False
        if abs(sum(r*(pts[i][axis]/pts[i][2]) for i, r in enumerate(res))) > tol*scale*n:
            return False
    return True


_I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
_RZ90 = ((0, -1, 0), (1, 0, 0), (0, 0, 1))
_DOWN = ((1, 0, 0), (0, -1, 0), (0, 0, -1))
_RGEN = _rot((1.0, 2.0, 2.0), 0.7)
# a rotation rounded to 10 decimals: orthonormal only to about 1e-10, still valid (< 1e-9)
_RGEN10 = tuple(tuple(round(v, 10) for v in row) for row in _RGEN)
_KA = (500, 500, 320, 240)
_KB = (600, 450, 310, 235)
# world_to_camera(R, t, p): hand answers; None = reference.
_WTC_CASES = [
    ((_I3, (0, 0, 0), (1, 2, 3)), (1, 2, 3)),
    ((_RZ90, (1, 2, 3), (1, 0, 0)), (1, 3, 3)),
    ((_RZ90, (1, 2, 3), (0, 1, 0)), (0, 2, 3)),
    ((_DOWN, (0, 0, 2), (0.5, 0.25, 0.5)), (0.5, -0.25, 1.5)),
    ((_DOWN, (0, 0, 2), (0, 0, 3)), (0, 0, -1)),
    ((_RGEN, (0.3, -1.2, 4.0), (1.5, -0.7, 2.2)), None),
    ((_RGEN10, (0.3, -1.2, 4.0), (1.5, -0.7, 2.2)), None),
]
# project(K, p_cam): hand answers; None = reference.
_PROJ_CASES = [
    ((_KA, (0.4, -0.2, 2)), (420, 190)),
    ((_KA, (0, 0, 5)), (320, 240)),
    ((_KB, (-0.3, 0.2, 1.5)), (190, 295)),
    ((_KB, (0.8, 0.6, 0.001)), None),
    ((_KB, (-0.001, 0.0005, 0.001)), None),
    ((_KB, (-3.1, 7.7, 10000)), None),
]
# deproject(K, u, v, depth): hand answers; None = reference + round trip.
_DEPROJ_CASES = [
    ((_KA, 420, 190, 2), (0.4, -0.2, 2)),
    ((_KB, 190, 295, 1.5), (-0.3, 0.2, 1.5)),
    ((_KA, 320, 240, 3.5), (0, 0, 3.5)),
    ((_KB, 711.25, -80.5, 0.001), None),
    ((_KB, -250.0, 600.0, 10000), None),
]
# pixel_to_world(K, R, t, u, v, depth): hand answers; None = reference.
_P2W_CASES = [
    ((_KA, _RZ90, (1, 2, 3), 420, 290, 3), (-1.7, 0.4, 0)),
    ((_KA, _I3, (0, 0, 0), 420, 190, 2), (0.4, -0.2, 2)),
    ((_KB, _RGEN, (0.3, -1.2, 4.0), 500.5, 120.25, 3.3), None),
]
# reprojection_rms(K, points, pixels): hand answers; None = reference.
_RMS_CASES = [
    ((_KA, ((0.4, -0.2, 2), (0, 0, 5)), ((423, 186), (320, 245))), 5.0),
    ((_KA, ((0.4, -0.2, 2),), ((420, 190),)), 0.0),
    ((_KA, ((0.4, -0.2, 2), (0, 0, 5)), ((423, 186), (320, 240))), math.sqrt(12.5)),
    ((_KB, ((0.1, 0.2, 1.1), (-0.5, 0.3, 2.5), (1.0, -0.8, 4.0)),
      ((371.2, 331.5), (110.0, 270.7), (460.1, 144.9))), None),
    ((_KB, ((0.0005, 0.0004, 0.001), (-0.0003, 0.0002, 0.001), (900.0, -700.0, 10000)),
      ((905.0, 460.0), (130.0, 335.0), (359.0, 203.0))), None),
]
# fit_intrinsics(points, pixels): hand answers; None = reference + normal equations.
_FIT_CASES = [
    (((0, 0, 1), (0.5, 0.25, 1), (-0.25, -0.5, 1)), ((320, 240), (570, 340), (195, 40)),
     (500, 400, 320, 240)),
    (((-1, 0.5, 2), (0, -0.25, 1), (2, 0, 4)), ((70, 342), (322, 139), (568, 239)),
     (498, 406, 320, 240)),
    (((0.2, 0.3, 1.6), (-0.7, 0.1, 2.1), (1.1, -0.4, 3.0), (0.3, 0.9, 2.2), (-0.2, -0.6, 1.7)),
     ((445.3, 427.1), (180.2, 269.8), (556.9, 164.4), (357.8, 525.3), (278.0, 8.1)), None),
    (((0.0005, 0.0002, 0.001), (-0.0003, 0.0004, 0.001), (0.0001, -0.0001, 0.001), (3000.0, 500.0, 10000)),
     ((570, 330), (170, 430), (320, 160), (480, 245)), None),
    (((0.5, 0.5, 1), (0.6, 0.55, 1)), ((570, 440), (620, 462.5)), (500, 450, 320, 215)),
    (((0, 0, 1), (0.5, 0.25, 1), (-0.25, -0.5, 1)), ((320, 240), (70, 340), (445, 40)),
     (-500, 400, 320, 240)),
]
# split_eval(points, pixels, n_train): hand answers (K, train, test); None = reference.
_SPLIT_CASES = [
    (((0, 0, 1), (0.5, 0.25, 1), (-0.5, -0.5, 1), (1, 0, 2)),
     ((320, 240), (570, 340), (73, 36), (570, 245)), 2, ((500, 400, 320, 240), 0.0, 5.0)),
    (((-1, 0.5, 2), (0, -0.25, 1), (2, 0, 4), (0.3, 0.2, 1)),
     ((70, 342), (322, 139), (568, 239), (471, 321)), 3, None),
    (((0.1, 0.1, 1), (-0.1, 0.05, 1), (0.05, -0.1, 1), (0.9, 0.7, 1), (-0.8, 0.8, 1), (0.7, -0.9, 1)),
     ((371, 283), (270, 262), (345, 198), (770, 521), (-60, 543), (655, -57)), 3, None),
]


def _fresh(value):
    """Nested list copy of a tuple table entry, so mutation can be detected."""
    if isinstance(value, (list, tuple)):
        return [_fresh(v) for v in value]
    return value


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation, for example rejecting a point behind the camera in world_to_camera?)"
    return text + ")"


def _tol(want, base):
    return base*max(1.0, abs(want))


def self_check(notes=None):
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

    def run(name, label, function, args, compare):
        # odd-numbered cases arrive as nested lists, even-numbered as tuples
        ok, got = attempt(name, label, function,
                          _fresh(args) if int(label.split(" ")[-1]) % 2 else args)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def close(got, want, name, base):
        if not abs(got - want) <= _tol(want, base):
            raise _Mismatch(name + " is wrong (tolerance " + repr(_tol(want, base)) + ")")

    def triple(got, want, names, base):
        if not _vector(got, len(want)):
            raise _Mismatch("output must be a list/tuple of " + str(len(want)) + " finite int/float")
        for g, w, n in zip(got, want, names):
            close(g, w, n, base)

    for i, (args, want) in enumerate(_WTC_CASES):
        want = _wtc_ref(*args) if want is None else want
        run("world_to_camera", "world_to_camera " + str(i), world_to_camera, args,
            lambda got, want=want: triple(got, want, ("X", "Y", "Z"), 1e-9))
    for i, (args, want) in enumerate(_PROJ_CASES):
        want = _project_ref(*args) if want is None else want
        run("project", "project " + str(i), project, args,
            lambda got, want=want: triple(got, want, ("u", "v"), 1e-9))
    for i, (args, want) in enumerate(_DEPROJ_CASES):
        K = args[0]
        want = _deproject_ref(*args) if want is None else want
        def compare(got, want=want, args=args):
            triple(got, want, ("X", "Y", "Z"), 1e-9)
            back = _project_ref(args[0], got)
            if not (abs(back[0] - args[1]) <= _tol(args[1], 1e-8)
                    and abs(back[1] - args[2]) <= _tol(args[2], 1e-8)):
                raise _Mismatch("projecting your point does not give the pixel back")
        run("deproject", "deproject " + str(i), deproject, args, compare)
    for i, (args, want) in enumerate(_P2W_CASES):
        want = _p2w_ref(*args) if want is None else want
        def compare(got, want=want, args=args):
            triple(got, want, ("x", "y", "z"), 1e-9)
            cam = _wtc_ref(args[1], args[2], got)
            back = _project_ref(args[0], cam)
            if not (abs(back[0] - args[3]) <= _tol(args[3], 1e-8)
                    and abs(back[1] - args[4]) <= _tol(args[4], 1e-8)
                    and abs(cam[2] - args[5]) <= _tol(args[5], 1e-8)):
                raise _Mismatch("sending your world point forward does not reproduce pixel and depth")
        run("pixel_to_world", "pixel_to_world " + str(i), pixel_to_world, args, compare)
    for i, (args, want) in enumerate(_RMS_CASES):
        want = _rms_ref(*args) if want is None else want
        def compare(got, want=want):
            if not _real(got):
                raise _Mismatch("output must be one finite int/float")
            close(got, want, "RMS error", 1e-6)
        run("reprojection_rms", "reprojection_rms " + str(i), reprojection_rms, args, compare)
    for i, (pts, pix, want) in enumerate(_FIT_CASES):
        want = _fit_ref(pts, pix) if want is None else want
        def compare(got, want=want, pts=pts, pix=pix):
            triple(got, want, ("fx", "fy", "cx", "cy"), 1e-6)
            if not _normal_equations_hold(got, pts, pix, 1e-8):
                raise _Mismatch("the fitted line is not the least-squares minimiser")
        run("fit_intrinsics", "fit_intrinsics " + str(i), fit_intrinsics, (pts, pix), compare)
    for i, (pts, pix, n_train, want) in enumerate(_SPLIT_CASES):
        want = _split_ref(pts, pix, n_train) if want is None else want
        def compare(got, want=want):
            if not (isinstance(got, (list, tuple)) and len(got) == 3):
                raise _Mismatch("output must be (K, train_rms, test_rms)")
            triple(got[0], want[0], ("fx", "fy", "cx", "cy"), 1e-6)
            if not (_real(got[1]) and _real(got[2])):
                raise _Mismatch("train_rms and test_rms must be finite int/float")
            close(got[1], want[1], "train RMS", 1e-6)
            close(got[2], want[2], "held-out RMS", 1e-6)
        run("split_eval", "split_eval " + str(i), split_eval, (pts, pix, n_train), compare)

    # Non-mutation: hand every function fresh nested lists and compare afterwards.
    pts = [[-1.0, 0.5, 2.0], [0.0, -0.25, 1.0], [2.0, 0.0, 4.0], [0.3, 0.2, 1.0]]
    pix = [[70.0, 342.0], [322.0, 139.0], [568.0, 239.0], [471.0, 321.0]]
    Kl, Rl, tl = [600.0, 450.0, 310.0, 235.0], [list(r) for r in _RGEN], [0.3, -1.2, 4.0]
    snapshot = _fresh((Kl, Rl, tl, pts, pix))
    pl = [1.5, -0.7, 2.2]
    for name, function, args in (
            ("world_to_camera", world_to_camera, (Rl, tl, pl)),
            ("project", project, (Kl, pts[0])),
            ("deproject", deproject, (Kl, 500.5, 120.25, 3.3)),
            ("pixel_to_world", pixel_to_world, (Kl, Rl, tl, 500.5, 120.25, 3.3)),
            ("reprojection_rms", reprojection_rms, (Kl, pts, pix)),
            ("fit_intrinsics", fit_intrinsics, (pts, pix)),
            ("split_eval", split_eval, (pts, pix, 3))):
        ok, _ = attempt(name, name + " input-mutation check", function, args)
        changed = _fresh((Kl, Rl, tl, pts, pix)) != snapshot or pl != [1.5, -0.7, 2.2]
        if ok and changed:
            failures.append(name + " input-mutation check: your function changed an input list")
            Kl, Rl, tl, pts, pix = _fresh(snapshot)
            pl[:] = [1.5, -0.7, 2.2]

    # Invalid inputs.
    nan, inf = float("nan"), float("inf")
    goodK = [500.0, 500.0, 320.0, 240.0]
    goodR = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    goodP = [[0.1, 0.2, 2.0], [0.3, -0.1, 3.0], [-0.2, 0.4, 2.5]]
    goodM = [[340.0, 280.0], [380.0, 220.0], [280.0, 300.0]]
    def with_slot(base, index, value):
        copy = [list(row) if isinstance(row, list) else row for row in base]
        copy[index] = value
        return copy
    badK = [[500.0, 500.0, 320.0], [500.0, 500.0, 320.0, 240.0, 1.0], [0.0, 500.0, 320.0, 240.0],
            [500.0, -1.0, 320.0, 240.0], [0.5, 500.0, 320.0, 240.0], [10001.0, 500.0, 320.0, 240.0],
            [500.0, 500.0, 10001.0, 240.0], [500.0, 500.0, 320.0, -10001.0],
            [nan, 500.0, 320.0, 240.0], [500.0, inf, 320.0, 240.0], [True, 500.0, 320.0, 240.0],
            [500.0, 500.0, "320", 240.0], "abcd", None, 500.0]
    badR = [[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]],
            [[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]],
            [[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[nan, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[1.0000001, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[1.000001, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[1.0, 0.000001, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0000001]],
            [[True, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, "1"]], "abc", None]
    def vec3(limit):
        return [[0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [nan, 0.0, 0.0], [0.0, inf, 0.0],
                [True, 0.0, 0.0], [limit + 1.0, 0.0, 0.0], [0.0, 0.0, -limit - 1.0],
                [0.0, "0", 0.0], "abc", None, 1.0]
    badT = vec3(1e4)
    badWorld = vec3(1e4)
    badCam = [[0.0, 0.0], [0.0, 0.0, 1.0, 1.0], [nan, 0.0, 1.0], [0.0, inf, 1.0],
              [True, 0.0, 1.0], [10001.0, 0.0, 1.0], [0.0, -10001.0, 1.0],
              [0.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 0.0, -1e-9], [0.0, 0.0, 0.0009],
              [0.0, 0.0, 10001.0], [0.0, 0.0, nan], [0.0, 0.0, True],
              [0.0, "0", 1.0], "abc", None]
    badPix = [nan, inf, -inf, True, 1000001.0, -1000001.0, "1", None]
    badDepth = [0.0, -1.0, -1e-9, 0.0009, 10001.0, nan, inf, True, "1", None]
    badPoints = [[], [[0.0, 0.0, 1.0]] * 201, goodP[:2], [[0.1, 0.2], [0.3, -0.1], [-0.2, 0.4]],
                 with_slot(goodP, 0, [0.1, 0.2, 0.0]), with_slot(goodP, 1, [0.3, -0.1, -2.0]),
                 with_slot(goodP, 2, [-0.2, 0.4, 0.0009]), with_slot(goodP, 0, [nan, 0.2, 2.0]),
                 with_slot(goodP, 1, [0.3, True, 3.0]), with_slot(goodP, 2, [0.1, 0.2, 10001.0]),
                 with_slot(goodP, 0, [10001.0, 0.2, 2.0]), with_slot(goodP, 1, "abc"),
                 "abc", None, 5.0]
    badPixels = [[], goodM[:2], goodM + [[1.0, 1.0]], [[340.0], [380.0], [280.0]],
                 with_slot(goodM, 0, [340.0, 280.0, 1.0]), with_slot(goodM, 1, [nan, 220.0]),
                 with_slot(goodM, 2, [280.0, inf]), with_slot(goodM, 0, [True, 280.0]),
                 with_slot(goodM, 1, [1000001.0, 220.0]), with_slot(goodM, 2, "ab"),
                 "abc", None, 5.0]
    badN = [0, 1, 3, 4, -1, 2.0, True, nan, "2", None]
    signatures = [
        ("world_to_camera", world_to_camera, ("R", "t", "p"), (goodR, [1.0, 2.0, 3.0], [0.5, 0.5, 0.5]),
         {"R": badR, "t": badT, "p": badWorld}),
        ("project", project, ("K", "p_cam"), (goodK, [0.1, 0.2, 2.0]), {"K": badK, "p_cam": badCam}),
        ("deproject", deproject, ("K", "u", "v", "depth"), (goodK, 340.0, 280.0, 2.0),
         {"K": badK, "u": badPix, "v": badPix, "depth": badDepth}),
        ("pixel_to_world", pixel_to_world, ("K", "R", "t", "u", "v", "depth"),
         (goodK, goodR, [1.0, 2.0, 3.0], 340.0, 280.0, 2.0),
         {"K": badK, "R": badR, "t": badT, "u": badPix, "v": badPix, "depth": badDepth}),
        ("reprojection_rms", reprojection_rms, ("K", "points", "pixels"), (goodK, goodP, goodM),
         {"K": badK, "points": badPoints, "pixels": badPixels}),
        ("fit_intrinsics", fit_intrinsics, ("points", "pixels"), (goodP, goodM),
         {"points": badPoints, "pixels": badPixels}),
        ("split_eval", split_eval, ("points", "pixels", "n_train"), (goodP, goodM, 2),
         {"points": badPoints, "pixels": badPixels, "n_train": badN}),
    ]
    for title, function, names_, args, bad in signatures:
        for slot, name in enumerate(names_):
            for value in bad[name]:
                trial = args[:slot] + (value,) + args[slot+1:]
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                calls[title] = calls.get(title, 0) + 1
                try:
                    function(*_fresh(trial))
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
    # Degenerate fits: the focal length cannot be separated from the principal point.
    flatX = [[0.2, 0.1, 2.0], [0.4, 0.4, 4.0], [0.1, -0.3, 1.0]]
    flatY = [[0.1, 0.2, 2.0], [-0.3, 0.4, 4.0], [0.4, 0.1, 1.0]]
    spread = [[0.2, 0.1, 2.0], [0.20000001, 0.4, 2.0]]
    sameY = ([[0.1, 0.2, 2.0], [0.3, 0.4, 4.0], [0.0, 0.0, 1.0]], goodM, 2)
    for title, function, args, why in (
            ("fit_intrinsics", fit_intrinsics, (flatX, goodM), "every X/Z equal"),
            ("fit_intrinsics", fit_intrinsics, (flatY, goodM), "every Y/Z equal"),
            ("fit_intrinsics", fit_intrinsics, (goodP[:1], goodM[:1]), "one point"),
            ("fit_intrinsics", fit_intrinsics, ([], []), "no points"),
            ("reprojection_rms", reprojection_rms, (goodK, [], []), "no points"),
            ("split_eval", split_eval, ([], [], 2), "no points"),
            ("fit_intrinsics", fit_intrinsics, (spread, goodM[:2]), "X/Z spread below 1e-6"),
            ("split_eval", split_eval, (flatX + [goodP[0]], goodM + [goodM[0]], 3), "training X/Z all equal"),
            ("split_eval", split_eval, sameY, "training Y/Z all equal")):
        calls[title] = calls.get(title, 0) + 1
        try:
            function(*_fresh(args))
        except ValueError:
            continue
        except NotImplementedError:
            missing.setdefault(title, []).append(title + " degenerate (" + why + ")")
            continue
        except Exception as error:
            failures.append(title + " degenerate (" + why + "): raised " + type(error).__name__
                            + " instead of ValueError")
            continue
        failures.append(title + " degenerate (" + why + "): returned instead of raising ValueError")
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
    print("CoreLab manual pinhole camera self-check - practice only, no signed evidence")
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

"""CoreLab Odometry lab — original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the four functions below, then run your edited file locally:
  Windows: py -3 L03-odometry.v1.py
  macOS/Linux: python3 L03-odometry.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.

Model: ideal differential drive, no slip, constant wheel-speed ratio per step.
Pose (x,y,theta) is the axle midpoint in the world frame; +x forward at theta=0,
+theta counter-clockwise. Left/right wheel order is fixed. Wheel speeds are
LINEAR rim speeds in m/s, distances dl/dr in metres, full track width in metres,
angles in radians, dt in seconds. Encoder ticks/radii are outside this kit.

Contracts (finite int/float, never bool):
  wheel_to_body(vl,vr,track) -> (v,omega); |vl|,|vr| <= 2.
  body_to_wheels(v,omega,track) -> (vl,vr); |v| <= 2, |omega| <= 40.
  odom_step(pose,dl,dr,track) -> (x,y,theta); |dl|,|dr| <= 10.
  velocity_step(pose,vl,vr,track,dt) -> pose; speed bounds above, 0 < dt <= 5.
For every function 0.1 <= track <= 2. Pose is exactly a length-3 list/tuple,
|x|,|y| <= 1000 and |theta| <= 2*pi. Invalid inputs raise ValueError.
Return exactly a list/tuple of finite non-bool values; never mutate inputs.
Pose heading must be in [-pi,pi], allowing either endpoint. Output positions or
inverse wheel speeds may exceed the input bounds; do not silently clip them.

Predict straight, reverse, pure-spin and arc cases before coding. Derive the
wheel/body map. Integrate each constant-curvature segment exactly, including
its initial heading; a stable small-angle expression avoids 1-cos cancellation.
For changing curvature, apply segments in order, not just cumulative wheel totals.
Self-check tolerances are per-case metres and radians, not physical accuracy.
This does not implement calibration, localization, SLAM, ROS or a simulator.
Explain why passing an ideal integrator cannot establish accurate robot position.

Background link only: Dellaert & Hutchinson, Introduction to Robotics and
Perception, section 5.2, https://www.roboticsbook.org/S52_diffdrive_actions.html
No source code, text, diagrams or dataset from that work is redistributed here.
"""
import math
from decimal import Decimal, localcontext


def wheel_to_body(vl, vr, track):
    raise NotImplementedError("Derive body speed and counter-clockwise yaw rate")


def body_to_wheels(v, omega, track):
    raise NotImplementedError("Derive the inverse map using full track width")


def odom_step(pose, dl, dr, track):
    raise NotImplementedError("Integrate an exact arc in the world frame")


def velocity_step(pose, vl, vr, track, dt):
    raise NotImplementedError("Convert metres/second to wheel travel before integrating")


def _finite_vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(type(v) in (int, float) and math.isfinite(v) for v in value))


def _decimal_arc(pose, dl, dr, track):
    """Author oracle: high-precision integrated sine/cosine power series.

    Independent arithmetic from the common half-angle/sinc implementation.
    Only these bounded fixtures are claimed; this is an inspectable practice
    oracle, never a protected grader or mathematical proof for arbitrary inputs.
    """
    with localcontext() as ctx:
        ctx.prec = 140
        left, right, width = map(Decimal.from_float, map(float, (dl, dr, track)))
        distance, angle = (left+right)/2, (right-left)/width
        even, odd = Decimal(1), angle/2
        sx, sy = even, odd
        for k in range(1, 400):
            even *= -angle*angle / Decimal((2*k)*(2*k+1))
            odd *= -angle*angle / Decimal((2*k+1)*(2*k+2))
            sx += even
            sy += odd
        bx, by = float(distance*sx), float(distance*sy)
    x, y, theta = pose
    return (x + math.cos(theta)*bx - math.sin(theta)*by,
            y + math.sin(theta)*bx + math.cos(theta)*by,
            math.atan2(math.sin(theta+float(angle)), math.cos(theta+float(angle))))


def self_check():
    """Return failure descriptions. These fixed author fixtures are practice only."""
    failures = []

    def vector_case(label, function, args, expected, tolerance=1e-10):
        try:
            got = function(*args)
            if not _finite_vector(got, len(expected)):
                raise ValueError("wrong output shape/type/finiteness")
            if any(abs(a-b) > tolerance for a, b in zip(got, expected)):
                raise ValueError("wrong numeric result")
        except Exception as error:
            failures.append(label + ": " + type(error).__name__)

    for vl, vr, width, expected in [
        (.2, .2, .5, (.2, 0.)), (-.2, .2, .5, (0., .8)),
        (-.3, -.1, .4, (-.2, .5)), (2., -2., .1, (0., -40.)),
        (0., 0., 2., (0., 0.)), (.12, .44, .8, (.28, .4)),
    ]:
        vector_case("wheel/body", wheel_to_body, (vl, vr, width), expected)
    for v, w, width, expected in [
        (.2, 0., .5, (.2, .2)), (0., .8, .5, (-.2, .2)),
        (-.2, .5, .4, (-.3, -.1)), (2., 40., 2., (-38., 42.)),
        (0., 0., .1, (0., 0.)),
    ]:
        vector_case("body/wheel", body_to_wheels, (v, w, width), expected)

    def pose_case(label, function, args, expected, position_tolerance=1e-9):
        original = list(args[0])
        try:
            got = function(*args)
            if not _finite_vector(got, 3):
                raise ValueError("wrong pose shape/type/finiteness")
            if list(args[0]) != original:
                raise ValueError("input pose mutated")
            if abs(got[0]-expected[0]) > position_tolerance or abs(got[1]-expected[1]) > position_tolerance:
                raise ValueError("position error in metres")
            if not -math.pi <= got[2] <= math.pi:
                raise ValueError("heading not wrapped")
            error = math.atan2(math.sin(got[2]-expected[2]), math.cos(got[2]-expected[2]))
            if abs(error) > 1e-10:
                raise ValueError("heading error in radians")
        except Exception as error:
            failures.append(label + ": " + type(error).__name__)

    anchors = [
        ([1., 2., math.pi/2], 1., 1., .5, (1., 3., math.pi/2)),
        ([0., 0., 0.], 0., math.pi/2, 1., (.5, .5, math.pi/2)),
        ([2., -1., 0.], -.5, .5, 1., (2., -1., 1.)),
        ([1., 2., math.pi/2], -.5, -.5, .5, (1., 1.5, math.pi/2)),
        ([0., 0., math.pi], 0., 0., .5, (0., 0., math.pi)),
    ]
    for i, (pose, dl, dr, track, expected) in enumerate(anchors):
        pose_case("hand anchor " + str(i), odom_step, (pose, dl, dr, track), expected)
    for i, (pose, dl, dr, track, tol) in enumerate([
        ([.3, -.2, 1.1], .1, .3, .4, 1e-9),
        ([-2., 3., -2.2], -.7, -.2, .6, 1e-9),
        ([0., 0., 0.], .5, .500000000001, .5, 1e-15),
        ([0., 0., 0.], 1e-12, 2e-12, .4, 1e-24),
        ([999., -999., 2*math.pi], -10., 10., .1, 1e-9),
        ([0., 0., -math.pi], -9., 10., .1, 1e-9),
        ([0., 0., 3.1], -.4, .4, 2., 1e-9),
    ]):
        expected = _decimal_arc(pose, dl, dr, track)
        pose_case("decimal arc " + str(i), odom_step, (pose, dl, dr, track), expected, tol)
    for i, (pose, vl, vr, track, dt) in enumerate([
        ([0., 0., 0.], .1, .3, .5, .25),
        ([1., -1., .7], -.2, .4, .6, 2.),
        ([0., 0., 0.], 2., -2., .1, 5.),
        ([0., 0., 0.], .2, .2, .5, 1e-6),
    ]):
        expected = _decimal_arc(pose, vl*dt, vr*dt, track)
        pose_case("velocity/dt " + str(i), velocity_step, (pose, vl, vr, track, dt), expected)

    invalid = [
        (wheel_to_body, (True, 0., .5)), (wheel_to_body, (float('nan'), 0., .5)),
        (wheel_to_body, (0., float('inf'), .5)), (wheel_to_body, (2.01, 0., .5)),
        (wheel_to_body, (0., 0., .099)), (wheel_to_body, (0., 0., 2.01)),
        (body_to_wheels, (False, 0., .5)), (body_to_wheels, (0., float('nan'), .5)),
        (body_to_wheels, (2.01, 0., .5)), (body_to_wheels, (0., 40.01, .5)),
        (body_to_wheels, (0., 0., 0.)),
    ]
    for bad_pose in ([0., 0.], [0., 0., 0., 0.], [True, 0., 0.],
                     [0., float('nan'), 0.], [1001., 0., 0.], [0., 0., 7.], 'bad'):
        invalid.append((odom_step, (bad_pose, 0., 0., .5)))
        invalid.append((velocity_step, (bad_pose, 0., 0., .5, 1.)))
    invalid += [
        (odom_step, ([0., 0., 0.], True, 0., .5)),
        (odom_step, ([0., 0., 0.], 10.01, 0., .5)),
        (odom_step, ([0., 0., 0.], 0., float('inf'), .5)),
        (odom_step, ([0., 0., 0.], 0., 0., -.5)),
        (velocity_step, ([0., 0., 0.], 0., 0., .5, 0.)),
        (velocity_step, ([0., 0., 0.], 0., 0., .5, -1.)),
        (velocity_step, ([0., 0., 0.], 0., 0., .5, 5.01)),
        (velocity_step, ([0., 0., 0.], 0., 0., .5, True)),
        (velocity_step, ([0., 0., 0.], 0., 0., .5, float('inf'))),
        (velocity_step, ([0., 0., 0.], 2.01, 0., .5, 1.)),
        (velocity_step, ([0., 0., 0.], 0., 0., 2.01, 1.)),
    ]
    for function, args in invalid:
        try:
            function(*args)
        except ValueError:
            continue
        except Exception:
            pass
        failures.append(function.__name__ + ": invalid input must raise ValueError")
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual odometry self-check — practice only, no signed evidence")
    print("Failures:", failures if failures else "none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)

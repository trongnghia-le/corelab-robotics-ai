# Image-based servo step: pick the target, then take a bounded step

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence.

A pan/tilt camera that follows a target needs two answers every cycle: which detection is the target, and how fast should each axis turn. Everything below is a synthetic, numerical model with no image and no motor, so a clean result says nothing about a real robot.

## Frames and the normalized error

Use the pinhole conventions of the camera bridge: x to the right, y DOWN, z forward along the optical axis, depth = z. For a point in camera coordinates (X, Y, Z) the normalized image coordinates are x = X/Z and y = Y/Z. They are the tangents of the bearing angles to the point, so they are 0 at the image centre, positive to the right and positive below it.

From a measured pixel (u, v) with intrinsics (fx, fy, cx, cy) the observed normalized error is

ex = (u − cx)/fx, ey = (v − cy)/fy.

This number comes from the image, not from what you commanded, so it is the honest "how far am I from aligned" signal.

## Pan and tilt geometry

Put the camera at the origin of a base frame with the same axes. Positive pan turns the optical axis to the right, positive tilt turns it down. The camera axes are

forward f = (sin p cos t, sin t, cos p cos t), right ex = (cos p, 0, −sin p), down ey = (−sin p sin t, cos t, −cos p sin t).

A base point P has camera coordinates (P·ex, P·ey, P·f); the last one is the depth. Check with a target straight ahead at P = (0, 0, 2) and tilt 0: the depth is 2 cos p and x = −tan p. A camera panned right sees the target on its left, so x is negative and the correct pan command is negative. Pan and tilt are not independent in general; with both non-zero the formulas above are exact, not a sum of two tangents. A point with depth below a stated floor is beside or behind the camera and has no valid image coordinates.

## Choosing the target: label, not colour

A detection is a row (label, colour, u, v, depth, stamp, conf). A selector that follows "the red thing" fails the day a red distractor appears, or the day lighting makes the true target look orange. Identity is the label. Then reject what you must not steer by:

- stale: age = now − stamp must satisfy 0 ≤ age ≤ max_age (a stamp in the future is also invalid);
- invalid depth: keep depth_min ≤ depth ≤ depth_max, so zero, negative and absurdly large readings are dropped;
- low confidence: keep conf ≥ min_conf.

Among what remains pick the highest confidence and break ties by the lowest index. If nothing remains, the cycle must cancel: command zero and report "stop". Holding the last command or steering toward a rejected detection is how a camera swings off after a target that is no longer there.

## The bounded proportional step

With gain g (1/s) and a velocity limit wmax (rad/s), each axis gets

wpan = clip(g·ex, −wmax, wmax), wtilt = clip(g·ey, −wmax, wmax).

A positive error means turn positive, because the target is on the positive side. Clipping each axis separately keeps one large error from slowing the other axis. Inside a tolerance (|ex| ≤ tol and |ey| ≤ tol) the cycle reports "aligned" with zero command.

## A convergence suite

Simulate pan += wpan·dt, tilt += wtilt·dt with the exact geometry as the error. Worked example (different numbers from the practice items): target at (0, 0, 2), start pan 0.4 rad, tilt 0, gain 2.5, wmax 0.3, dt = 0.25 s, tol 0.05. Here x = −tan(pan), and a saturated step moves 0.3 · 0.25 = 0.075 rad.

- Pan 0.4: g|x| = 2.5 · 0.423 = 1.06 exceeds 0.3, so the pan drops by 0.075 to 0.325.
- Pan 0.325 (g|x| = 0.84) drops to 0.25, then 0.25 (g|x| = 0.64) drops to 0.175, then 0.175 (g|x| = 0.44) drops to 0.100.
- Pan 0.100: g|x| = 0.251 < 0.3, so the step is 0.251 · 0.25 = 0.063 and pan becomes 0.037.
- Pan 0.037: |x| = 0.037 ≤ 0.05, converged after 5 commands.

While saturated the loop moves at a constant angular speed, so the time is linear in the start offset; near the target it behaves like the linear law e ← (1 − g·dt)·e, which shrinks the error by a factor 1 − g·dt per step. With g·dt = 1 the linear part would reach zero in one step; the tangent makes it only nearly so. Requiring g·dt ≤ 1 stops the linear part from overshooting.

A convergence suite is a declared finite list of targets and start offsets with a step budget. A run that is lost (the target leaves the front half-space) or exceeds the budget counts as not converged. Passing the list says the controller works from those starts for that model; it does not say it works from others, with lag, noise or a moving target.

## Where this model stops

There are no images, no feature detector, no 6-DOF image Jacobian, no latency, backlash or motor limits, and no physics. A same-colour distractor, a stale frame and a bad depth are cheap to model and worth rejecting; the many other ways a real camera misleads a controller are not covered.

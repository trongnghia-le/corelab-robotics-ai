# Differential-drive odometry: wheel speeds to an exact arc

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers one ideal planar differential-drive model with constant wheel speeds over a step; it is not a localisation or calibration course.

## The model and conventions

The robot has a left and a right wheel, a full track width b (distance between the two contact points, in metres), and a pose (x, y, theta): the midpoint of the axle in the world frame and its heading. Heading is measured counter-clockwise from the world +x axis, in radians. The wheel speeds vl and vr are LINEAR rim speeds in m/s. Assume no slip, ideal encoders and speeds that are constant during one step of length dt seconds.

## From wheel speeds to body motion

The axle midpoint moves at the average of the two wheels; the body turns at the speed difference spread over the full width:

v = (vl + vr) / 2        omega = (vr - vl) / b

If the right wheel is faster, omega is positive (a counter-clockwise turn). Dividing by b/2 instead of b doubles omega: a common slip. The inverse map is vl = v - omega b / 2 and vr = v + omega b / 2, since each wheel sits b/2 from the midpoint. Adding the same amount to both wheels changes v but not omega; swapping the wheels flips the sign of omega.

## The exact arc

With v and omega constant the midpoint follows a circle of signed radius R = v / omega. Over the step the heading changes by phi = omega dt, and the exact update in the world frame is

theta1 = theta0 + phi
x1 = x0 + R (sin(theta1) - sin(theta0))
y1 = y0 - R (cos(theta1) - cos(theta0))

The initial heading theta0 matters: the sine and cosine differences already rotate the arc into the world frame. If you compute the arc for theta0 = 0 first, rotate that displacement by theta0 and add it to the start position.

If you only have wheel travels dl and dr over a step, use s = (dl + dr)/2 in place of v dt and dtheta = (dr - dl)/b in place of phi, with R = s / dtheta.

## The straight-line limit

When vr is nearly vl, omega is almost zero, R is huge and both sine differences nearly cancel, so the formula suffers 0/0 style round-off. As omega tends to 0 the result tends to straight motion: x1 = x0 + v dt cos(theta0), y1 = y0 + v dt sin(theta0). A guard that simply drives straight along the start heading drops the first-order sideways offset (about v dt phi / 2); keep that term or use a series (sinc) form for tiny omega.

## Why Euler and midpoint steps differ

An Euler step moves v dt along the START heading. That is a straight tangent segment, so its end lies outside the circle. A midpoint step uses the heading halfway through but still the arc length v dt, which is longer than the chord 2R sin(phi / 2), so it overshoots along the chord direction. Both update the heading exactly (theta + omega dt); only the position is approximate, and the per-step position error shrinks roughly with dt squared. The exact arc has no such error for constant speeds.

## Heading wrap

Headings are often stored in (-pi, pi]. Sine and cosine are 2 pi periodic, so wrapping does not change a position update. A safe wrap is atan2(sin(theta), cos(theta)). To compare two headings, wrap their DIFFERENCE, not the headings: 3.1 and -3.1 are only 0.083 rad apart although the raw difference is 6.2.

## Chaining segments

When the wheel speeds change, apply the exact update to each constant segment IN ORDER, starting each one from the pose (position AND heading) where the previous ended. Averaging the speeds into one arc, or starting segment 2 from the original heading, gives a different answer.

## Worked examples

The numbers here are specific to this bridge.

1. b = 0.36 m, vl = 0.27, vr = 0.45 m/s, dt = 1.5 s, start (0.5, 0.2, 0.3 rad). v = 0.36 m/s, omega = 0.5 rad/s, phi = 0.75 rad, R = 0.72 m. theta1 = 1.05. x1 = 0.5 + 0.72 (sin 1.05 - sin 0.3) = 0.9118; y1 = 0.2 - 0.72 (cos 1.05 - cos 0.3) = 0.5296. Euler would give (1.0159, 0.3596); the midpoint rule gives (0.9216, 0.5374). Both are wrong in position.
2. Straight limit: b = 0.36, vl = 0.3, vr = 0.3001, dt = 1.5, same start. omega = 0.000278 rad/s, so the result is almost x = 0.5 + 0.45 cos 0.3 = 0.9299, y = 0.2 + 0.45 sin 0.3 = 0.3330, with a tiny sideways offset kept by the series form.
3. Wrap: heading 3.0 rad plus a turn of 0.5 rad is 3.5 rad, wrapped to 3.5 - 2 pi = -2.7832 rad. The position is unaffected.
4. Two segments from (0, 0, 0 rad), b = 0.36: segment 1 vl = 0.18, vr = 0.30, 2 s gives (0.4452, 0.1542, 0.6667 rad). Segment 2 vl = 0.30, vr = 0.12, 2 s starts there: v = 0.21, omega = -0.5, R = -0.42, ending at (0.8424, 0.2210) with heading -0.3333 rad.

## Check yourself

1. vl = 0.1, vr = 0.4, b = 0.5: what are v and omega?
2. Two wrapped headings are 3.0 rad and -3.0 rad. What is the shortest signed value of (first - second) in (-pi, pi]?
3. Over one step the left wheel travelled dl = 0.5 m and the right wheel dr = 0.3 m, with b = 0.4 m. What are the midpoint travel s and the turn angle?

Answers: (1) v = 0.25 m/s, omega = 0.6 rad/s. (2) The raw difference is 6.0; wrapping gives 6.0 - 2 pi = -0.2832 rad. (3) s = (0.5 + 0.3)/2 = 0.4 m and dtheta = (0.3 - 0.5)/0.4 = -0.5 rad, a clockwise turn.

## Honest scope

This is the ideal constant-speed arc on a planar model. It does not cover wheel slip, noisy or quantised encoders, wheel radius or track-width calibration, varying speed within a step, localisation or sensor fusion, or any real robot. A passing integrator self-check shows agreement with the ideal model on the cases it ran; it does not show the real robot's position accuracy. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

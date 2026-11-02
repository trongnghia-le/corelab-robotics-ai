# Pure pursuit: steer toward a lookahead point and judge the trace

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers one simple path-following rule for a differential-drive robot, written as plain geometry and a short loop. Nonlinear control (C10) has no full lesson here, so this is a bridge, not a course. It does not teach Nav2, localization, costmaps or controller tuning, and nothing here runs a robot.

## The problem

You have a route, a polyline of straight segments, and a robot at a pose (x, y, theta): position in metres, heading in radians from the world +x axis, counter-clockwise positive. You want a speed v and a turn rate omega (rad/s) that bring the robot along the route. A unicycle model says the robot moves on a circular arc when v and omega are constant, with curvature kappa = omega / v (1/m), positive to the left.

## The rule in three steps

**1. Pick a lookahead point.** Draw a circle of radius L (the lookahead distance) around the robot. The target is where that circle meets the route ahead of the robot. On one segment the circle meets the segment's line in up to two points. They sit symmetrically on either side of the foot of the perpendicular from the robot, so exactly one is further along the segment direction: that is the "ahead" one, and the other lies behind the robot and must never be used. Write the root along the segment as P = A + t (B - A). The segment qualifies if the ahead root has 0 <= t <= 1. Scan the segments in order and take the first one that qualifies. A root past the end (t > 1) does not qualify; the circle then meets a later segment, which is what happens at a corner. If no segment qualifies and the goal (last vertex) is closer than L, steer at the goal itself. If nothing qualifies and the goal is still far, the robot is lost and you should say so instead of inventing a target. Remember the segment index you used and start the next scan there, so a route that doubles back cannot pull the target backwards.

**2. Express the target in the robot frame.** With dx = tx - x and dy = ty - y, the target is y_L = -sin(theta) dx + cos(theta) dy to the left of the robot's heading line (the forward part is cos(theta) dx + sin(theta) dy).

**3. Steer on the arc through the target.** The circle that is tangent to the heading at the robot and passes through the target has curvature

kappa = 2 y_L / d^2, where d^2 = dx^2 + dy^2.

For a target on the lookahead circle d = L, which is why textbooks write 2 y_L / L^2; near the goal d is smaller, and you must use the actual distance. A target straight behind gives y_L = 0 and kappa = 0, a known blind spot: the rule does not turn the robot around.

## Limits: slow down, do not clip omega

Real robots have a speed limit v_max and a turn-rate limit w_max. Cap the speed first. If |v kappa| then exceeds w_max, reduce the speed to w_max / |kappa|. That keeps kappa and so the arc; clipping omega alone with the speed unchanged would make the robot drive a wider arc than the rule intended and run wide of the corner. A speed of exactly the limit is not reduced.

## A worked example

Route (0, 0), (6, 0), (6, 6); robot at (4, 1), heading 0, L = 3, v_cmd = 1 m/s, v_max = 1 m/s, w_max = 0.4 rad/s.

- Segment 0 lies on y = 0. The robot is 1 m above it, so the circle meets the line where (x - 4)^2 + 1 = 9, x = 4 ± 2.828. The ahead root is x = 6.828, past the end x = 6. Segment 0 does not qualify.
- Segment 1 lies on x = 6. (6 - 4)^2 + (y - 1)^2 = 9 gives y = 1 ± 2.236; the ahead root is y = 3.236, between 0 and 6. Target (6, 3.236) on segment 1.
- dx = 2, dy = 2.236, y_L = 2.236 (heading 0), d^2 = 9. kappa = 2 · 2.236 / 9 = 0.497 1/m, a left turn with radius about 2 m.
- Speed 1 m/s gives omega = 0.497 > 0.4, so v = 0.4 / 0.497 = 0.805 m/s and omega = 0.4 rad/s.

If you had taken the root behind the robot on segment 0, the target would be (1.172, 0) and the robot would turn right, away from the corner. If you had clipped omega to 0.4 and kept v = 1, the arc would be wider (radius 2.5 m, not 2.01 m) and the robot would run wide.

## Why pure pursuit cuts corners

The target is a point on the route, but the arc through it is not the route: while the lookahead point is already on the second segment, the robot is still on the first, and it turns early. The larger L is, the earlier it turns and the more it cuts. A smaller L tracks better but turns more sharply, which is where the turn-rate limit bites.

## Judging a recorded trace

A trace is a list of positions sampled at a fixed rate. Four plain checks, in a stated order, make the judgement reproducible:

- Cross-track error of a sample: its distance to the nearest point of the whole polyline (clamp the projection to each segment, then take the smallest). Report the maximum and the root-mean-square value.
- Corridor: a half-width w. A sample is outside when its error is strictly greater than w; an error exactly equal to w is inside. Say which edge rule you use.
- Goal: the first sample within a goal tolerance of the last vertex. If none, the run timed out. Number samples from 0 and say so.
- Corner clearance: the distance from each interior vertex to the polyline drawn through the samples (chords between consecutive samples). Measuring only to the sample points misses a chord that skips the corner.

Then fix an order for the verdict, for example off-corridor first, then timeout, then corner-cut, then ok.

## Scope

You can write and test the geometry, the steering rule, the limits and the trace checks as pure functions on numbers. This does not show that a real robot would follow the route. Pose estimation error, TF and clock delays, controller update jitter, wheel slip, actuator dynamics, obstacles, costmaps, changed floor layouts and replanning are outside the toy. Evidence about a real navigation stack would come from an independent log of a real run, not from your simulation. Practice and AI solutions never automatically establish verified mastery.

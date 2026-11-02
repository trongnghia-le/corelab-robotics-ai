# A mock joint interface, trajectory validator and action client

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. Everything here is a MOCK: plain numbers and small state machines for a made-up 2-joint arm. It is not ros2_control, not MoveIt, not a controller manager and not a real-time loop, and nothing here may be connected to a real robot.

## What a hardware interface promises

A ros2_control style hardware interface exposes command interfaces (what a controller writes, such as a joint position) and state interfaces (what it reads back, such as position and velocity). In a mock, you replace the device by arithmetic, so you can test the contract without a robot. Mock evidence stays mock: it shows your logic follows the written contract, not that a real device obeys it.

The contract in this lab has three parts.

**Lifecycle.** The interface is unconfigured, inactive, active or finalized. configure takes unconfigured to inactive, activate takes inactive to active, deactivate returns to inactive, cleanup returns to unconfigured, and shutdown reaches finalized from unconfigured, inactive or active. Any other request is refused and the state does not change. Commands are accepted only when the state is active.

**Limits.** Each joint has a position range [lower, upper] (inclusive) and a maximum speed. In this lab a command outside the range is refused as a whole, rather than silently clamped (a design choice of this lab; real limit enforcers often saturate instead), so the caller learns that it asked for something impossible. A command inside the range is followed at most max_velocity x dt per cycle; a joint that is too far away moves a limited step and the cycle reports rate-limited. The velocity read back is the actual motion divided by dt, not the requested motion.

**Order of checks.** Not active comes first, then the position limit, then the rate limit. Writing the order down matters: with a different order the same input reports a different reason.

## Validating a trajectory

A joint trajectory is a list of waypoints (time, positions) plus the joint names it was written for. A validator should return every named reason it rejects, so a test can say which fault it injected. Typical reasons: names that are wrong or in another order, times that do not strictly increase, positions outside the limits, a speed between two waypoints above max_velocity x time difference, and a first waypoint that is not the current state within a tolerance. Positions are matched to joints by index, so a trajectory in the wrong joint order is dangerous even if each number is fine.

Worked example (pan and tilt, positions in rad, limits +/-1 rad, max_velocity 0.3 rad/s for both, current state pan 0.1 and tilt 0.2, start_tol 0.02). Waypoints: (0 s; 0.1, 0.2), (2 s; 0.5, 0.6), (3 s; 0.9, 0.6). Segment 1: each joint moves 0.4 rad in 2 s = 0.2 rad/s, allowed. Segment 2: pan moves 0.4 rad in 1 s = 0.4 rad/s, above 0.3, so velocity-limit. Positions are inside the range, the times increase and the first waypoint equals the current state. Result: velocity-limit only. To fix the fault, stretch segment 2 to at least 0.4/0.3 = 1.33 s.

## A follow-trajectory action client

An action goal has a longer life than a function call. The client sends a goal (pending), the server accepts or rejects it, feedback reports progress while executing, and the end is succeeded, aborted or canceled. A client also needs its own timeout, because a silent server never sends an end. The mock keeps a declared event list and applies rules in a fixed order: final states ignore everything; then the timeout (strictly greater than the limit, measured from send_goal) turns a live goal into timed-out and discards the event; then the table.

Two traps. First, a cancel is a request: if the server finishes first, the result arrives while the client is canceling and the goal succeeds, so canceled is not guaranteed. Second, progress should never go backwards, so lower feedback is dropped.

Worked example, timeout 500 ms: send_goal at 50, accept at 100, feedback 0.4 at 200, cancel_request at 300, result_abort at 400, cancel_done at 450. States: pending, executing, executing (progress 0.4), canceling, aborted, aborted (final, cancel_done changes nothing).

## A planning-scene check by dense subdivision

Planners check that a motion is free of obstacles. For a straight line in joint space, the tip does not move on a straight line, so a pose check needs forward kinematics: elbow = l1 (cos q1, sin q1), tip = elbow + l2 (cos(q1+q2), sin(q1+q2)). The arm is the segments base-elbow and elbow-tip, and the obstacle is a closed box. The method here: sample the joint segment at s = k/200 for k = 0..200, compute both link segments, and test each exactly against the box. It is a sampling check, not a proof: a very thin obstacle can fall between samples, and link thickness, joint limits and self-collision are ignored. Both end poses being free does not make the motion free.

Worked example: l1 = l2 = 0.5 m, q2 = 0 (a straight arm of reach 1 m), box x from 0.5 to 0.9 and y from 0.2 to 0.4 m. A ray from the origin meets the box between the lowest corner direction (0.9, 0.2), atan2(0.2, 0.9) = 0.2187 rad, and the highest (0.5, 0.4), atan2(0.4, 0.5) = 0.6747 rad; both corners are within reach (0.92 m and 0.64 m). A sweep of q1 from 0 to 1 rad starts and ends clear but is blocked in between.

## Honest scope

Real ros2_control, a controller manager, MoveIt planning, real controllers and timing guarantees are not covered, and a real device needs its own separate review. Passing the kit says your toy logic matches the written contract. It says nothing about jitter, latency, tracking error, real collision geometry or a planner that finds a different path.

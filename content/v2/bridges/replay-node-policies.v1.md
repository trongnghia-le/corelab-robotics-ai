# Replaying a message log through a node: frame, stamp, gap and reset policies

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers the plain logic that a ROS 2 odometry node needs, written as ordinary functions over a recorded list of messages. It does not teach ROS 2 itself: nodes, topics, QoS, DDS, TF2, ROS time and launch files are all outside it, and nothing here runs a robot.

## Why separate the logic from the middleware

A node that subscribes to wheel odometry and publishes a pose does three jobs: it receives messages, it decides which ones to use, and it integrates them. Only the middle and last jobs are logic you can test without a robot. If you write them as a pure function of a message list, you can replay a recorded log through it, compare the output with hand-computed numbers, and run the same log again tomorrow with the same result. It does not tell you whether real messages arrive, in what order, or how late.

## A message and its policy

Take a message to be a small record: a stamp (an integer in nanoseconds, never a float, because a float seconds value loses precision for large times), a frame_id and a child_frame_id (text), and the left and right wheel speeds in m/s. A pose output carries the same stamp, the frame ids and x, y, theta. Four decisions must be written down before any code, because each unwritten decision becomes a hidden default.

**Frames.** The node expects one frame_id and one child_frame_id. A message with different ones is not wrong data to repair; it is data that does not belong to this node, so drop it. If a message is both a duplicate and in the wrong frame, decide which reason is reported.

**Stamps.** Keep a clock: the stamp of the last accepted message. A message with the same stamp is a duplicate; one with an earlier stamp is out of order. Both are dropped. The key rule: a dropped message changes no state, not even the clock. A node that moves the clock back on a stale message makes the next good message cover a longer interval than it really did, and the pose is wrong even though every dropped message was handled "correctly".

**Gaps.** The interval between two accepted stamps is the time the wheel speeds are assumed constant. If a sensor was silent for a long time that assumption is not believable. Declare a maximum gap, and decide the boundary: an interval equal to the maximum is usually still normal, and one nanosecond more is a gap. Then choose a policy: reset the pose to the initial pose and integrate nothing, or integrate anyway and mark the output with a flag so a consumer can see it.

**Reset.** An explicit reset message sets the pose and also the clock. It is never dropped, even when its stamp is earlier than the clock, because moving the clock is its job. The message after it is then measured from the reset stamp.

## Intermediate poses

Publish one pose for every accepted message, not only the final one. The first accepted message has nothing to integrate over, so it publishes the initial pose and only starts the clock. Each later message publishes the pose after its interval, using the speeds it carries.

## The integration step

Within one interval the wheel speeds are constant, so the robot moves along a circular arc (or a straight line when both wheels have the same speed). With wheel travel dl = vl * dt and dr = vr * dt, track width b, turn = (dr - dl) / b and mean distance d = (dl + dr) / 2, the pose moves by chord d * sin(turn/2) / (turn/2) along the heading theta + turn/2, then theta becomes theta + turn, wrapped to [-pi, pi]. Use the series 1 - u^2/6 for sin(u)/u when u is tiny (the exact-arc step of the odometry lab).

## A worked example

Frame "odom", child "base_link", track 0.4 m, maximum gap 600 ms, policy reset, initial pose (0, 0, 0). Messages as (stamp in ms, frame, child, vl, vr): (200, odom, base_link, 0, 0); (400, odom, base_link, 0.5, 0.5); (300, odom, base_link, 0.7, 0.7); (700, odom, tool0, 0.3, 0.3); (900, odom, base_link, -0.2, 0.2).

- Message 1: no clock yet. It publishes (0, 0, 0) with flag init. Clock 200.
- Message 2: interval 200 ms, not a gap. Straight at 0.5 m/s for 0.2 s: x = 0.1. Clock 400.
- Message 3: stamp 300 is earlier than the clock 400, so it is out of order. Dropped, clock stays 400.
- Message 4: child frame "tool0" is not "base_link". Dropped, clock stays 400.
- Message 5: interval 500 ms, within the maximum. vl = -0.2 and vr = 0.2 spin in place: turn = (0.2 - (-0.2)) * 0.5 / 0.4 = 0.5 rad, no translation.

Three poses are published, two messages are dropped, and the last pose is (0.1, 0, 0.5). If a dropped stale message had moved the clock to 300, message 5 would cover 600 ms and end at theta 0.6. If the child-frame check were missing, message 4 would add a fourth pose. If the stale message were accepted, x would fall to 0.03.

## Testing the tests

Once the node core works, write checks for it: a test suite is a function that accepts a correct node and rejects a broken one. To see whether your suite is any good, you need broken nodes to throw it at: one that ignores the child frame, one that lets a duplicate through, one that moves the clock on a dropped message, one whose gap test is off by one, one that mutates its input list, one that keeps state between calls. A suite that passes every one of them is not testing that rule. Two correct nodes may differ in the last digits of a float, so compare with a tolerance.

When a node misbehaves on a long log, shrink the log: find the smallest set of messages, kept in order with their original stamps, on which it still differs from the correct node. A short reproducer names the rule that fails and can be replayed forever. Note that the smallest set is often not contiguous and often needs a "setup" message, such as the earlier message that makes a later one stale.

## Scope

You can write and test the decision logic of a node on a recorded list. This does not show that a real node subscribes, publishes or runs. DDS delivery, QoS history and reliability, transport latency, ROS and simulated clocks, time jumps, TF2 buffering and lookups, executors, launch files and wheel slip are outside this toy, and a perfect replay of one log says nothing about the next. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

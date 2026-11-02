# Planar 2R inverse kinematics: reach, branches and honest failure

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence. It covers position-only inverse kinematics (IK) for one declared planar arm; it is not a general IK course.

## The model and conventions

The arm lies in the x-y plane with its base at the origin. Link lengths l1 and l2 are in metres. Angles are in radians, counter-clockwise positive, and RELATIVE: q1 is link 1 measured from the base +x axis, and q2 is link 2 measured from link 1. The tip is at

x = l1 cos q1 + l2 cos(q1 + q2)
y = l1 sin q1 + l2 sin(q1 + q2)

Forward kinematics (FK) maps (q1, q2) to (x, y) with one answer. IK goes the other way: given a target (x, y), find every (q1, q2) that reaches it. There can be zero, one or two.

## Is the target reachable?

Let r = sqrt(x^2 + y^2). The tip distance depends only on the elbow: r^2 = l1^2 + l2^2 + 2 l1 l2 cos q2. As q2 runs from 0 (straight) to pi (folded), r runs from l1 + l2 down to |l1 - l2|. The reachable set is a ring:

|l1 - l2| <= r <= l1 + l2

- Strictly inside: two solutions, one per elbow branch.
- On either edge (straight or folded): one solution, because the branches coincide.
- Outside: none.

Floating-point rounding can push a target that is on an edge on paper a hair outside. If you accept a small band such as 1e-9 m, state it.

## Step 1: the elbow

Solve the distance formula for the cosine:

c = cos q2 = (x^2 + y^2 - l1^2 - l2^2) / (2 l1 l2)

In floating point c can come out as 1.0000000000000002 near an edge, and acos then fails. Clamp c into [-1, 1] before acos, but only AFTER the ring test said the target is reachable. Clamping repairs rounding; it must never make an unreachable target look reachable.

Then q2 = +acos(c) or q2 = -acos(c): the two elbow branches. For q2 > 0 the elbow bends counter-clockwise relative to link 1.

## Step 2: the shoulder, with atan2

q1 = atan2(y, x) - atan2(l2 sin q2, l1 + l2 cos q2)

The first term points at the target; the second is the angle by which link 2 pulls the tip away from link 1. Use two-argument atan2, not atan(y / x): the ratio loses both signs, so (-0.9, 0.6) would get the angle of (0.9, -0.6), a half-turn wrong, and x = 0 divides by zero. Also l1 + l2 cos q2 can be zero or negative when strongly folded. The two branches give different q1, so compute q1 separately for each q2.

## Joint limits and equivalent angles

q and q + 2 pi k are the same pose. With limits [lo, hi], a branch is allowed if SOME representative lies inside, and you report that representative. Example: q1 = -1.0 fits limits [5.0, 6.0] as -1.0 + 2 pi = 5.283. Test each branch separately. If limits remove both, say "no admissible solution" and whether the target was reachable without limits.

## The base-singular case

If l1 = l2 the ring includes the origin: fold the arm with q2 = pi. But then EVERY q1 works, since rotating the folded arm about the base does not move the tip. No finite list exists; report that, or raise a clear error. If l1 and l2 differ, the origin is outside the ring.

## Check every answer with forward kinematics

Compute FK on your (q1, q2) and take the residual, the distance from the FK tip to the target. Accept a pose when the residual is tiny for the arm size, for example below 1e-8 m for an arm about a metre long. Judge by residual and limits, not by matching one reference pair: a correct pose may be the other branch or another representative of an angle. The residual also exposes degrees-for-radians, world-frame q2 and atan slips.

## Worked example

Arm: l1 = 0.8 m, l2 = 0.5 m. Target: (0.9, -0.6) m.

1. r^2 = 0.81 + 0.36 = 1.17, so r = 1.0817. The ring is 0.3 <= r <= 1.3: reachable, strictly inside, so two solutions.
2. c = (1.17 - 0.64 - 0.25) / 0.8 = 0.35, and acos(0.35) = 1.213225 rad.
3. Branch A, q2 = +1.213225: sin q2 = 0.936750, so l2 sin q2 = 0.468375 and l1 + l2 cos q2 = 0.975. atan2(0.468375, 0.975) = 0.447832, and atan2(-0.6, 0.9) = -0.588003. So q1 = -1.035835 rad.
4. Branch B, q2 = -1.213225: the second term changes sign, so q1 = -0.588003 + 0.447832 = -0.140171 rad.
5. FK of branch A: x = 0.8 cos(-1.035835) + 0.5 cos(0.177390) = 0.407846 + 0.492154 = 0.9, and y = 0.8 sin(-1.035835) + 0.5 sin(0.177390) = -0.688231 + 0.088231 = -0.6. Residual about 1e-6 m or less from the rounded angles.
6. With q2 limited to [0, 2], only branch A survives. With q1 limited to [5.0, 6.0] too, A is allowed through the representative -1.035835 + 2 pi = 5.247350.

## Honest failure

Outside the ring, return "unreachable" with no angles. A clamped pose or the nearest ring point may be logged only as a "closest approach" with its non-zero residual; never present it as a solution to the original target.

An iterative solver that stops at its iteration cap has shown only that it did not converge. That is not proof of unreachability: a poor start, small steps or a singular pose can stall it. Decide reachability with the exact ring test, and use the residual to say whether the iteration succeeded.

## Check yourself

1. With l1 = 1.0 m and l2 = 0.6 m, how many solutions for (1.6, 0) and for (0.3, 0.1)?
2. With l1 = l2 = 0.7 m and target (0, 0), what should a solver report?
3. A solver returns a pose whose FK residual is 0.05 m. Is it a solution?

Answers: (1) The first is on the outer edge: exactly one (q2 = 0). The second has r = 0.316, below 0.4: none. (2) An infinite set (q2 = pi, any q1), so no finite list. (3) No; the residual is far above tolerance. Re-check units and branch, or report failure.

## Scope

You can solve a declared planar 2R arm for position with a chosen branch and limits, and verify any answer by FK residual. This is not orientation IK, redundant or spatial arms, singularity-robust numerical methods, or hardware: a real arm also needs calibration, collision checking, speed limits and safety review. Practice and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

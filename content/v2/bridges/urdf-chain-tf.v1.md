# Robot description: read a URDF chain and look up transforms

This optional bridge takes about 30 minutes. You can skip it and open any activity. Reading it creates no evidence.

A robot description says where each link sits relative to the one before it. Everything below is a small numerical subset of URDF: a serial chain read from a text string. No mesh is loaded and nothing runs on a robot.

## Links, joints and the root

A description lists links (named frames) and joints. Each joint has a parent link, a child link, a type and an origin. The types here are revolute (turns about an axis), prismatic (slides along an axis) and fixed (no motion). A joint's frame is its child link's frame.

Do not trust the order of the lines. The root is the one link that is no joint's child; the chain order is found by following parent to child from the root. A text is a valid serial chain only if: every name is defined once, every joint names defined links, each link has at most one parent joint and one child joint, there is exactly one root, and every link is reachable from the root. Counting "joints = links - 1" is not enough: a cycle detached from the root can pass that count and a single-root test, and only a reachability walk exposes it.

## Origin, axis and joint motion

The origin gives xyz (metres) and rpy (radians) of the child frame at joint value 0, expressed in the parent frame. Roll-pitch-yaw here is fixed-axis: R = Rz(yaw) Ry(pitch) Rx(roll), so roll is applied first about the parent x axis. Other libraries state other orders, so always write yours down.

The axis is a direction in the joint frame. Normalise it to length 1 (an axis "0 3 4" becomes (0, 0.6, 0.8)). A missing axis defaults to (1, 0, 0), a missing origin is all zeros.

The motion comes after the origin:

T_parent_child = T_origin * T_motion(q)

where T_motion is a rotation by q about the unit axis (revolute) or a translation by q along it (prismatic). Because the motion is in the joint frame, an origin rotated by a roll of 90 degrees carries the axis with it: a declared axis (0, 0, 1) points along base -y when the origin rpy is (pi/2, 0, 0), since Rx(pi/2) maps (a, b, c) to (a, -c, b).

## Transforms along the chain

T_base_link is the product of the T_parent_child factors from the root to that link. Write T as a 4x4 matrix [R | p; 0 0 0 1]. A point in the link frame goes to the base frame by p_base = R p_link + p. The inverse is [R^T | -R^T p]: transpose R, then rotate and negate p. Negating p alone is a common slip.

## Lookup between two links

A TF-style lookup(target, source) returns T_target_source, which converts coordinates in the source frame into the target frame:

T_target_source = inverse(T_base_target) * T_base_source.

Two checks: a lookup of a frame with itself is the identity, and lookup(a, b) times lookup(b, a) is the identity. Joints above the shallower of the two frames cancel out of the product.

## Worked example

Chain: base to arm by a revolute joint "swing" with origin xyz = (0.1, 0, 0.2), rpy = (0, 0, 0), axis (0, 0, 1); arm to tip by a fixed joint with origin xyz = (0.5, 0, 0). Take swing = 0.5 rad.

T_base_arm = Trans(0.1, 0, 0.2) Rz(0.5). The tip offset (0.5, 0, 0) rotates to 0.5 (cos 0.5, sin 0.5, 0) = (0.438791, 0.239713, 0). So the tip is at (0.1 + 0.438791, 0.239713, 0.2) = (0.538791, 0.239713, 0.2) m, with the frame turned 0.5 rad about z.

Now lookup(target = tip, source = base). R = Rz(0.5), p = (0.538791, 0.239713, 0.2). R^T p = (cos 0.5 * 0.538791 + sin 0.5 * 0.239713, -sin 0.5 * 0.538791 + cos 0.5 * 0.239713, 0.2) = (0.587758, -0.047943, 0.2) approximately, so the base origin lies at about (-0.587758, 0.047943, -0.2) in the tip frame. Check: rotating that by R and adding p must return the origin (0, 0, 0).

## Test it independently

Your own forward kinematics agreeing with itself proves little. Compare a planar chain with your L02 planar_2r, then compare a spatial chain with a hand-written product of elementary matrices at joint values you did not use while developing. If a transform comes out as the inverse of what you expected, check the direction of the lookup before changing the rotations.

## Honest scope

This bridge covers a serial chain read from a string: revolute, prismatic and fixed joints, origin and axis, base-to-link transforms and lookups. It does not cover meshes, inertia, collision, xacro, branching trees, mimic or continuous joints, joint limits, TF2 timing and interpolation, robot_state_publisher or visualisation. A correct transform in a toy does not validate a real robot model, whose offsets must be measured and whose zero positions must be calibrated.

Try the practice with a pencil, then run the robot-description self-check kit. Ask a Socratic tutor for a conceptual question or one next step; declare any external help. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

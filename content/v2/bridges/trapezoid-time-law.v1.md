# Time laws: speed, acceleration and distance

This optional bridge takes about 20 minutes. You can skip it and open any activity. Reading it creates no evidence.

The derivative lesson (M05) goes from position to velocity to acceleration. A time law runs the other way: you choose how the acceleration behaves, and integrate. If acceleration a is constant for a time t starting at speed v0, then v = v0 + a t, and the distance covered is v0 t + a t²/2. The distance is also the area under the speed-time graph.

A rest-to-rest move of one axis (a joint in radians or a slide in metres) uses three phases: speed up at +amax, optionally cruise at the speed limit vmax, slow down at −amax. The limits are |v| ≤ vmax and |a| ≤ amax at every instant. The two ramps are mirror images, so they last the same time ta and cover the same distance.

## Choosing the shape

Let d = |D| be the distance to travel. Two ramps up to vmax last 2 vmax/amax and cover vmax²/amax in total.

- If d·amax < vmax², the axis cannot reach vmax. The profile is a triangle: ta = √(d/amax), peak speed amax·ta, total time T = 2 ta.
- Otherwise the profile is a trapezoid: ta = vmax/amax, cruise time tc = d/vmax − vmax/amax, T = 2 ta + tc.

Worked example. D = 8 m, vmax = 2 m/s, amax = 1 m/s². Here d·amax = 8 > vmax² = 4, so it is a trapezoid: ta = 2 s, tc = 8/2 − 2 = 2 s, T = 6 s. Check by area: the ramps cover 2 m each and the cruise covers 2 m/s × 2 s = 4 m, a total of 8 m. For D = 2 m with the same limits, d·amax = 2 < 4 gives a triangle: ta = √2 s, T ≈ 2.83 s, peak speed ≈ 1.41 m/s, below vmax.

A negative D only flips the signs of velocity and acceleration; the times are the same. D = 0 means no motion and T = 0.

## Position at a time

Find the phase containing t, then integrate. In the braking phase it is easiest to measure the time left, s = T − t: the speed is amax·s and the axis is still amax·s²/2 short of the target. At the boundaries position and speed are continuous, but acceleration jumps. That jump is a real limitation: a jerk (change of acceleration) is infinite here, and this profile says nothing about it.

## A slower, longer move

Asked for a duration T longer than the minimum, keep the acceleration at amax and lower the cruise speed v. The ramps then last v/amax each, so the area condition is v (T − v/amax) = d, a quadratic in v whose smaller root is the answer: the larger root would make the ramps last more than T/2 each, leaving a negative cruise time. A request shorter than the minimum duration is impossible with these limits: report that honestly instead of exceeding vmax or amax.

## Two joints together

Two independent joints that must start and stop together can finish no sooner than the larger of their two minimum durations. The faster joint is then slowed with the rule above.

## Scope

This is a numerical one-axis toy. It has no jerk limit, no torque or motor model, no path geometry between several points, and no controller or robot execution. Passing exercises here does not show that a real robot can follow the motion.

Try the bridge practice, say the phase formulas aloud, then open the Trajectories exercises. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

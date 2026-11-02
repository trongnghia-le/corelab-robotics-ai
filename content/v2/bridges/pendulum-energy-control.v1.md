# One-link dynamics: energy, integrators and computed torque

This optional bridge takes about 30 minutes. You can skip it and open any activity. Reading it creates no evidence. It builds on the R07 lesson (the point-mass pendulum) and adds three things the lab needs: a link whose mass is not a point, a comparison of three ways to step the equation forward, and a computed-torque law with a torque limit. Everything here is a one-link toy in a vertical plane.

## The model

Measure the angle q from the downward vertical, counter-clockwise positive, so q = 0 hangs straight down. A link of mass m has its centre of mass at distance lc from the pivot and an inertia Ic about that centre. The parallel-axis rule gives the pivot inertia I = Ic + m·lc². The equation of motion is

I·q'' + b·q' + m·g·lc·sin q = τ,

with viscous damping b and motor torque τ. The gravity torque m·g·lc·sin q pulls q back toward 0. The energy E = ½·I·q'² + m·g·lc·(1 − cos q) is zero when the link hangs at rest, and dE/dt = (τ − b·q')·q'. With τ = 0 and b = 0, E is constant in the true motion.

For small angles sin q ≈ q, so q'' = −ω²·q with ω² = m·g·lc/I and period T = 2π/ω. Notice that adding Ic makes I larger and the swing slower; doubling m alone with Ic = 0 changes nothing.

## Three ways to take one step

Let a be the acceleration at the start of the step.

- Explicit Euler: q_next = q + h·q', q'_next = q' + h·a. The angle uses the old rate.
- Semi-implicit (symplectic) Euler: q'_next = q' + h·a first, then q_next = q + h·q'_next. The angle uses the new rate.
- RK4: four evaluations of the acceleration inside the step, combined with weights 1, 2, 2, 1 over 6.

Worked example. Take m = 1 kg, lc = 1 m, Ic = 0, g = 10 m/s², no damping or torque, start at q = π/2, q' = 0, with h = 0.05 s. Then a = −10 rad/s², E = 10 J, and both Euler variants give q'_next = −0.5 rad/s. Explicit Euler keeps q = π/2, so E = 0.125 + 10 = 10.125 J (up by 0.125 J). The semi-implicit step moves the angle to π/2 − 0.025 ≈ 1.5458, so E = 0.125 + 10·(1 − cos 1.5458) ≈ 9.875 J (down by 0.125 J). Over many steps the explicit method keeps adding energy, while the semi-implicit one stays close to the true value and only wobbles around it.

## Energy as a test

In the small-angle region explicit Euler multiplies E by exactly 1 + (h·ω)² each step. With ω² = 10 s⁻² and h = 0.05 s that is 1.025 per step, about 140 after 200 steps (10 s); with h = 0.025 s it is about 12 after 400 steps. Halving h roughly halves the logarithm of the gain, so the drift is a numerical artefact that shrinks with h. RK4 keeps E nearly flat for the same h. A trace that gains energy with b = 0 and τ = 0 therefore has three suspects: the integrator, the step size, or the model (wrong sign or size of gravity or inertia). Rerun with a smaller step and with RK4: if the drift disappears it was the solver; if it stays, the model is wrong.

A wrong model also shows up in measured data. For a real free swing the energy computed from (q, q') samples must stay flat. Evaluate E with each candidate model on the same samples and compare the spread (Emax − Emin)/Emax; the model with a spread near 0 matches. Be honest about the limit: scaling I and m·g·lc by the same factor leaves the spread unchanged, so energy flatness only identifies the ratio ω² = m·g·lc/I, not the mass itself. Damped data lose energy by design, so use only undamped data or include the damping model.

## Computed torque and its limit

Inverse dynamics asks which torque produces a wanted acceleration. Computed torque turns that into a feedback law. With errors e = q_d − q and ė = q_d' − q', choose the commanded acceleration a_cmd = q_d'' + kd·ė + kp·e and apply

τ_raw = I·a_cmd + b·q' + m·g·lc·sin q,  τ = clip(τ_raw, −τ_max, τ_max).

With an exact model and no clipping, the model terms cancel the plant and the error obeys ë + kd·ė + kp·e = 0; kd = 2·√kp is critically damped. Worked example: m = 1, lc = 1, Ic = 0, g = 10, b = 0, at q = 0.5 rad at rest, target q_d = 0.8 rad at rest with kp = 25, kd = 10. Then a_cmd = 25·0.3 = 7.5 rad/s² and τ_raw = 7.5 + 10·sin 0.5 ≈ 7.5 + 4.794 = 12.294 N·m. With τ_max = 10 N·m the applied torque is 10: the clip acts on the whole sum, and the linear error equation no longer holds.

Two consequences. First, holding a pose needs τ = m·g·lc·sin q; if τ_max is smaller than that at the target, the link rests where m·g·lc·sin q = τ_max, short of the target. Second, a wrong parameter in the controller model is not cancelled. With a wrong g_model the link rests where I·kp·(q_ref − q) = m·lc·(g − g_model)·sin q, a steady offset that shrinks only as kp grows (or with an integral term, which this bridge does not cover).

## Scope

This is a numerical toy of a single rigid link with viscous damping. It has no multi-link coupling, contact, backlash or other friction, motor or gearbox model, sensor noise, delay, physics engine or hardware torque control. Passing exercises here does not show that a real arm will behave the same way.

Try the bridge practice, then open the dynamics exercises. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

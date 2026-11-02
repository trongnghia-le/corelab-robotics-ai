# Holding a box with two friction pads: the hold condition and a retention observer

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence.

A parallel-jaw gripper squeezes a box between two flat pads. Nothing pushes the box up except friction, so whether it stays in the gripper is a statement about forces. Everything below is a made-up, quasi-static toy: rigid box, rigid pads, the same Coulomb friction coefficient on both pads, no physics engine.

## Coulomb friction and the cone

Each pad presses with a normal force fn (N), which can only push, so fn ≥ 0. Along the pad it can carry a tangential force ft, but only up to a limit proportional to the push:

|ft| ≤ μ · fn

μ is dimensionless. Drawn in the (fn, ft) plane, the allowed forces form a wedge, the friction cone, with half-angle atan μ. The edge |ft| = μ·fn still belongs to the cone (the pad is on the verge of slipping, not slipping), and a "pulling" pad (fn < 0) is never inside it. A pad whose reading has |ft| > μ·fn is outside the cone: in this model that pad is slipping and the number is no longer a static force balance.

## The hold condition for a lift

Take upward as positive and let the box have mass m (kg) and upward acceleration a (m/s²). Gravity g = 9.81 m/s². Newton's second law on the box in the vertical direction says the total friction F from both pads must be

F = m · (g + a)

Each pad can supply at most μN where N is its normal force, so the pair supplies at most 2μN. The grasp holds when

2 μ N ≥ m (g + a)

and equality is the boundary. The safety factor S = 2μN / (m (g + a)) says how many times over the capacity covers the demand; S ≥ 1 holds. Solving the same equation for another unknown gives the smallest squeeze N = m (g + a) / (2μ), the largest holding acceleration a_max = 2μN/m − g (which is negative when the squeeze cannot even hold the box still), or the largest mass m_max = 2μN / (g + a).

Three things to watch. The factor 2 is there because there are two pads. The acceleration enters as g + a, not g: accelerating up raises the demand, and accelerating down lowers it. Mass is in kilograms: a part labelled 900 g is 0.9 kg.

## Worked example

A 0.5 kg box, μ = 0.5, lifted with a = 3 m/s². Demand: m(g + a) = 0.5 · 12.81 = 6.405 N, so each pad carries 3.2025 N of friction. The smallest squeeze is N = 6.405 / (2 · 0.5) = 6.405 N per pad. With N = 8 N the capacity is 2 · 0.5 · 8 = 8 N, so S = 8 / 6.405 = 1.249 and the grasp holds. If the pads become oily and μ drops to 0.35, the capacity is 5.6 N and S = 0.874: the box slips. To recover, N must be at least 6.405 / 0.7 = 9.15 N. Check by rearranging: a_max at N = 8 and μ = 0.5 is 2 · 0.5 · 8 / 0.5 − 9.81 = 6.19 m/s², so a = 3 is inside it.

## A retention observer on a force trace

A real pick produces readings from force sensors on the pads. Here a trace is a list of samples (cmd, fn, ft): cmd is 0 while the gripper is commanded closed and 1 while commanded open; fn and ft are the measured normal and tangential force on one pad. The observer is four small monitors that do not depend on each other:

- Contact. While closed and not in contact, the first sample with fn ≥ the threshold is "contact". While in contact, a sample with fn below the threshold is "lost": the box left without any open command.
- Object. While in contact, |ft| > μ·fn is "slip", reported once and re-armed only after a sample back inside the cone (so the boundary |ft| = μ·fn is not a slip).
- Empty. If a closed run of a stated number of samples (the window) ends with no contact at all, the grasp is "empty". It is not the same as "lost": nothing was ever held.
- Release. The first open sample while in contact is "release". An open command with nothing held produces no event.

Worked trace: μ = 0.5, threshold 1.0 N, window 3, samples (0, 0, 0), (0, 3.0, 0.5), (0, 3.0, 1.5), (0, 3.0, 1.8), (1, 2.0, 0.5). Sample 1 has fn ≥ 1.0: "contact". Sample 2 sits on the edge, 1.5 = 0.5 · 3.0: no event. Sample 3 has 1.8 > 1.5: "slip". Sample 4 is the first open sample in contact: "release". Events: (1 contact), (3 slip), (4 release), with indices counted from 0. If a contact sample already starts outside the cone, both "contact" and "slip" are reported at that same index; and after "lost", a later sample with enough force is a new "contact".

## From a trace to a changed mass or friction

A trace is evidence for what changed, but only inside the model. During a steady hold (a = 0) each pad reads ft ≈ m·g/2, so the mass is m ≈ 2·ft/g. If a slip appears when the lift starts, either the mass is larger than planned or μ is smaller than planned; the observer alone cannot tell which. A mass check from the hold samples and the hold condition can: if the mass matches the plan, suspect friction and size the new squeeze with the smaller μ; if the mass is larger, size it with that mass. An "empty" event points elsewhere, to a missed grasp or a sensor that never reads contact.

## Scope

This bridge covers an analytic two-pad Coulomb model and a threshold observer over a synthetic trace. It does not cover physics-engine contact simulation, soft or deformable contacts, torsional or rolling friction, multi-finger or form-closure grasps, grasp planning, a force-sensor noise or delay model, or any real gripper. A synthetic trace that the observer labels correctly says nothing about whether it works on hardware. Real friction depends on speed, pressure, surface and contamination, and the mass and centre of mass are usually not known as exactly as here.

Try the practice with a pencil, then run the self-check kit. Ask a Socratic tutor for a conceptual question or one next step; declare any external help. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

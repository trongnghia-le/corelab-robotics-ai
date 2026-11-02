# Linear Kalman filter: predict, update, fuse

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence.

A Kalman filter keeps a belief about a state x as a mean and a covariance P (a variance when x is a single number). It alternates two steps under a model that you declare: x_k = F x_(k-1) + w and z_k = H x_k + v, with w ~ N(0, Q), v ~ N(0, R), and w, v independent of each other and over time. Everything below is true only if F, Q, H and R are the truth. The filter never checks that.

## Predict

x⁻ = F x and P⁻ = F P Fᵀ + Q. The transpose goes on the right factor. Uncertainty grows: Q adds, and F can leak uncertainty from one component into another. For a position-velocity state with step dt, F = [[1, dt], [0, 1]]: velocity uncertainty becomes position uncertainty, so a cross-covariance appears even if P started diagonal.

## Update

Given one scalar measurement z:

- innovation y = z − H x⁻ (what the sensor says minus what the model expected),
- innovation variance S = H P⁻ Hᵀ + R,
- gain K = P⁻ Hᵀ / S,
- x = x⁻ + K y and P = (I − K H) P⁻.

The Joseph form (I − KH) P⁻ (I − KH)ᵀ + K R Kᵀ gives the same P in exact arithmetic and stays symmetric and positive semi-definite in floating point; either is fine for small examples, but check symmetry. K lies between 0 and 1 for a direct scalar measurement: near 1 when R is small, near 0 when R is large.

Worked example (scalar, H = 1). Prior x⁻ = 10, P⁻ = 4, sensor R = 2, reading z = 13. Then y = 3, S = 4 + 2 = 6, K = 4/6 = 0.6667, x = 10 + 0.6667·3 = 12, P = (1 − 0.6667)·4 = 1.3333. The posterior is closer to the reading because the prior is less certain than the sensor, and its variance, 1.3333, is smaller than both 4 and 2. Check with precisions: 1/4 + 1/2 = 0.75 and 1/0.75 = 1.3333.

## Fuse two sensors

Independent sensors measuring the same instant can be applied one after another, each update using the previous posterior (mean and covariance) as its prior. The result equals the batch information form: add information, Y = P0⁻¹ + Σ Hᵀ R⁻¹ H, and y = P0⁻¹ x0 + Σ Hᵀ R⁻¹ z; then P = Y⁻¹ and x = P y. The order does not matter. If your sequential result depends on the order, a covariance was not carried forward.

## Is the filter consistent?

NIS = y² / S (normalised innovation squared) should behave like a chi-square variable with one degree of freedom when the model is right. A correct model exceeds a gate set at the 95th percentile (3.841) on about 5% of steps by chance, and a gate at the 99th percentile (6.635) on about 1%. One exceedance proves nothing; a long run far above 5% suggests that some assumption, such as the noise level, the motion model or the timing, is wrong, but not which one. A dropout (no measurement) is a prediction with no update: P keeps growing.

## Where the assumptions break

- Positively correlated noise treated as independent gives a claimed variance that is too small: the filter is overconfident. The fused value may look fine while its stated uncertainty is wrong. Negative correlation does the opposite (claimed variance too large), which is safe but wasteful.
- A motion model that says constant velocity while the target accelerates, or measurements stamped with the wrong time, produce innovations that are consistently too large.
- Nonlinear models need an extended or unscented filter, which are outside this bridge and its lab.

To test a mismatch, build a counterexample, state which assumption it breaks, then draw fresh noise and see whether the symptom repeats. The numerical lab uses small fixed examples only; passing it says nothing about a real sensor stack.

Try the Kalman practice with a pencil, then run the Kalman self-check kit. Ask a Socratic tutor for a conceptual question or one next step; declare any external help. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.

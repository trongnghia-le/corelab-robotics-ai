# Episode QA, session splits and a behaviour-cloning baseline

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence. It uses tiny lists of numbers, not a real robot dataset, and it makes no claim that any learned policy generalises.

## Demonstrations as episodes

Behaviour cloning (BC) learns a policy from demonstrations: pairs of an observation o (what the robot sensed) and an action a (what the demonstrator did). Demonstrations arrive as episodes, each a short run with a timestamp, an observation and an action at every step. Steps within an episode are strongly related, and episodes recorded in one session (one day, one operator, one set-up) share conditions. That makes the unit of data the episode or the session, not the single step.

## Check the data before fitting anything

A QA (quality assurance) pass looks for named defects, each with a rule you can state:

- Time not strictly increasing: some stamp is not later than the one before it (a repeat or a step back).
- Time gap: two consecutive stamps more than a declared maximum apart, for example 0.15 s. Dropped samples look like this. Allow a tiny tolerance such as 1e-9, because 1.1 - 1.0 in floating point is 0.10000000000000009.
- Length mismatch: a different number of timestamps, observations and actions.
- Non-finite value: NaN or infinity. A NaN is not "out of range"; report it once, as its own defect.
- Out of range: a finite value outside the declared closed interval. A value exactly on a bound is inside.
- Empty: no timestamps, observations or actions at all; report only this.
- Duplicate: an exact copy of an earlier episode. Keep the first copy and flag the later ones.

Count each defect type at most once per episode, however many samples show it (three out-of-range values are one finding), but an episode with two different defect types has two findings.

Misalignment is subtler: the action log may be shifted by k steps against the observations. Try each small lag k, pair o[i] with a[i+k], fit the least-squares line through those pairs and prefer the lag with the smallest mean squared residual. Pairs never wrap around the ends. The score is a mean over fewer pairs at large lags, so on noisy data a large lag with only three or four pairs can win by chance; keep the lag range small. A lag of 0 on shifted data gives a wrong, flatter slope that still looks like a fit.

## Split by session, before fitting

If two steps of one episode land on different sides of a train/test split, the test step is not new: its neighbours were in training. The same holds for two episodes from one session. So split whole episodes, and where sessions differ in conditions, whole sessions. The audit is a set intersection: the ids that appear on both sides must be empty. Any statistic you compute from the data, such as a mean, must come from the training side only.

## The baseline: a line and a constant

With a scalar observation, the simplest BC policy is a line a = w o + b. Least squares chooses w and b to minimise the sum of squared errors on the training steps. Using the means mo and ma:

Sxx = sum (o - mo)^2, Sxy = sum (o - mo)(a - ma), w = Sxy / Sxx, b = ma - w mo.

If all training observations are equal, Sxx = 0 and no slope exists.

A line is only worth reporting next to a baseline that uses no observation: predict the mean training action for every held-out step. Both are judged by the mean squared error (MSE) on the held-out steps, the average of (a - prediction)^2, with every step weighing the same. If the line does not clearly beat the constant on episodes it never saw, it has learned little.

## Worked example

Training episode A: o = [0, 1], a = [1, 3]. Training episode B: o = [2, 3], a = [5, 7]. Held-out episode C: o = [4], a = [10].

Pool the four training steps: mo = 1.5, ma = 4, Sxx = 2.25 + 0.25 + 0.25 + 2.25 = 5, Sxy = (-1.5)(-3) + (-0.5)(-1) + (0.5)(1) + (1.5)(3) = 10. So w = 2 and b = 4 - 2(1.5) = 1. On C the prediction is 2(4) + 1 = 9, the error is 1 and the held-out MSE is 1. The mean baseline predicts 4, error 6, MSE 36. The line wins by a wide margin on this single step, which is exactly why a one-step test set proves nothing.

Now let C leak: fit on A, B and C together (five steps). The line moves toward C and the MSE on C falls (to 0.16 for this example: w = 2.2, b = 0.8), although nothing about the policy improved. A leaky number looks better and tells you less.

## When the result looks wrong

1. Shrink to the smallest dataset that still shows the problem, such as two episodes with two steps each, and compute it by hand.
2. Fix one defect or one rule at a time and rerun the QA.
3. Collect or hold back fresh episodes for the check. Numbers tuned on the test episodes are no longer a test.

## What this does not show

A closed-form line on a handful of toy steps says nothing about a neural policy, a real demonstrator, multi-dimensional observations, multimodal actions that an average destroys, compounding errors when the policy acts in a closed loop, or a new session with different conditions. A held-out comparison on a few episodes cannot support a generalisation claim. Open-source libraries such as LeRobot provide real datasets and training code, but nothing here depends on them.

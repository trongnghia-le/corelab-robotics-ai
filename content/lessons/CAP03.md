---
{
  "id": "cap03-capstone",
  "module_id": "CAP03",
  "title": "Capstone state estimation and localisation: calibration, EKF and consistency",
  "summary": "Localise CoreBot Tidy: calibrate the simulated camera, detect wall markers with PnP, fuse wheel odometry, gyro and landmark detections in an EKF with Joseph-form updates and gating, and audit the filter with NEES and NIS on five seeded trajectories.",
  "estimated_minutes": 1560,
  "project_minutes": 1560,
  "prerequisites": [
    "CAP02",
    "C08",
    "C12",
    "V04",
    "V11"
  ],
  "source_refs": [
    {
      "title": "Camera calibration using OpenCV (LearnOpenCV)",
      "url": "https://learnopencv.com/camera-calibration-using-opencv/"
    },
    {
      "title": "robot_localization (ROS 2 Jazzy)",
      "url": "https://docs.ros.org/en/jazzy/p/robot_localization/"
    },
    {
      "title": "AprilTag library (AprilRobotics)",
      "url": "https://github.com/AprilRobotics/apriltag"
    },
    {
      "title": "Probabilistic Robotics (MIT Press)",
      "url": "https://mitpress.mit.edu/9780262201629/probabilistic-robotics/"
    },
    {
      "title": "Thrun author page",
      "url": "https://sites.google.com/site/thrunstuff"
    }
  ],
  "objectives": [
    "Calibrate a simulated camera from checkerboard renders and judge the result by reprojection RMS and focal-length error.",
    "Turn marker detections into range-bearing measurements with known extrinsics and wrapped angles.",
    "Implement an EKF over odometry, gyro and landmarks with a Joseph-form update and a Mahalanobis gate.",
    "Audit a filter with NEES and NIS, and diagnose overconfidence and underconfidence from the numbers.",
    "Explain observability with no landmarks in view and keep tuning seeds separate from test seeds."
  ],
  "core_theory": [
    "Sensor fusion (C08)",
    "Nonlinear state estimation (C12)",
    "Camera calibration (V04)",
    "Multi-view geometry (V11)",
    "Kalman filtering (C07)"
  ],
  "labs": [
    "Build the localiser in ~/corebot-capstone and pass tests/acceptance/test_cap03.py, including the gate checks for camera calibration, EKF accuracy and filter consistency."
  ],
  "assessment_refs": [
    "CAP03-diagnostic-v1"
  ],
  "review_prompts": [
    "State what a mean NEES of 9 with 3 degrees of freedom tells you about your filter and what you would change first.",
    "Describe what your covariance does while no landmark is visible and show the plot that proves it."
  ],
  "extension_refs": [
    "https://docs.ros.org/en/jazzy/p/robot_localization/",
    "https://learnopencv.com/camera-calibration-using-opencv/"
  ]
}
---

## Why this matters

After CAP02 the base reports wheel counts and your odometry drifts: a 1.5 % scale error is 15 cm over 10 m, a 2 % heading error bends every long path. Navigation (CAP04) needs to know where the robot is to a few centimetres, and manipulation (CAP05) needs to know where the camera is. This milestone makes the robot **localise itself**: you calibrate the simulated camera, detect the wall markers, fuse wheel odometry, the gyro and the marker detections in an Extended Kalman Filter, and, most importantly, you **test whether the filter is honest**. A filter that reports a 2 cm uncertainty while being 15 cm wrong is worse than no filter, because every later module trusts its covariance.

The deliverable is not "an EKF"; it is an EKF plus evidence: calibration residuals, error plots with 2-sigma bands, NEES/NIS consistency statistics, an outlier test and a discussion of what happens when no landmark is in view. The approach and numbers follow the usual practice in *Probabilistic Robotics* and in the `robot_localization` package; you implement the filter yourself first and may compare with the library later.

## Intuition

![The CoreBot Tidy architecture: sensors and simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation, task layer and a safety supervisor that can stop every actuator path](/lesson-figures/CAP-architecture.svg)

*The whole system. This milestone is the blue estimation band: odometry from CAP02 plus gyro plus landmark detections go in, a pose with covariance (`Pose2DCov`) comes out.*

An EKF is a **bookkeeper with two sources of income**. Between landmark sightings it adds up small, noisy movements (wheels and gyro) and writes down, honestly, how much its uncertainty grew. When a marker is seen, it compares what it saw with what it expected to see, and corrects the pose by a fraction proportional to how much it trusts the measurement relative to its own uncertainty (the Kalman gain). If the bookkeeper is overconfident (writes uncertainty too small) it will ignore good measurements; if underconfident it will jitter. The NEES and NIS tests are the audit.

![The CAP03 pipeline: wheel odometry and gyro feed the EKF prediction, marker corners go through camera calibration and PnP to a range-bearing measurement, the EKF update with a Mahalanobis gate corrects the pose, and NEES and NIS audit the covariance](/lesson-figures/CAP03.svg)

This milestone reuses: [CAP02](/lessons/CAP02) (the calibrated odometry and the `WheelState`/`OdomSample` data), [C08](/lessons/C08) (sensor fusion, the complementary and Kalman view), [C12](/lessons/C12) (nonlinear state estimation: EKF, Jacobians, consistency), [V04](/lessons/V04) (camera model and calibration) and [V11](/lessons/V11) (multi-view geometry, PnP, essential matrix). Kalman basics are in [C07](/lessons/C07).

## Theory and derivation

These are the **integration notes**: the formulas and interfaces that matter, each with the topic that derived them.

### 1. State, prediction and the frames ([C12](/lessons/C12), [C08](/lessons/C08))

State $\mathbf{x}=[x,\,y,\,\theta,\,b_g]^\top$ in the `map` frame (metres, radians), gyro bias $b_g$ in rad/s. Inputs from the base: forward speed $v$ (from wheel odometry) and the gyro rate $\omega_g$. With step $\Delta t$:
$$x_{k+1}=x_k+v\cos\theta_k\,\Delta t,\quad y_{k+1}=y_k+v\sin\theta_k\,\Delta t,\quad \theta_{k+1}=\operatorname{wrap}\bigl(\theta_k+(\omega_g-b_g)\Delta t\bigr),\quad b_{g,k+1}=b_{g,k}.$$
Covariance: $P^-=FPF^\top+GQG^\top$, with $F_{13}=-v\sin\theta\,\Delta t$, $F_{23}=v\cos\theta\,\Delta t$, $F_{34}=-\Delta t$. Using the gyro for heading (and the wheels only for speed) is deliberate: wheel-derived turning depends on the track width, which is the worst-known constant of the base.

### 2. Landmark measurement ([C12](/lessons/C12), [V11](/lessons/V11))

A marker at known map position $(m_x,m_y)$ is detected by PnP and expressed as range and bearing in `base_link`:
$$h(\mathbf{x})=\begin{bmatrix}\sqrt{\Delta_x^2+\Delta_y^2}\\ \operatorname{wrap}\bigl(\operatorname{atan2}(\Delta_y,\Delta_x)-\theta\bigr)\end{bmatrix},\qquad \Delta_x=m_x-x,\ \Delta_y=m_y-y.$$
With $q=\Delta_x^2+\Delta_y^2$, $r=\sqrt q$ the Jacobian is
$$H=\begin{bmatrix}-\Delta_x/r&-\Delta_y/r&0&0\\ \Delta_y/q&-\Delta_x/q&-1&0\end{bmatrix}.$$
**The bearing innovation must be wrapped**, otherwise a marker near $\pm\pi$ produces a $2\pi$ jump.

### 3. Update, Joseph form and gate ([C07](/lessons/C07), [C12](/lessons/C12))

$$\nu=z-h(\hat{\mathbf x}),\quad S=HPH^\top+R,\quad K=PH^\top S^{-1},\quad \hat{\mathbf x}\leftarrow\hat{\mathbf x}+K\nu,\quad P\leftarrow(I-KH)P(I-KH)^\top+KRK^\top.$$
The Joseph form is a sum of two positive semi-definite terms, so $P$ stays symmetric positive definite even with rounding or a non-optimal $K$; the simple form $(I-KH)P$ does not guarantee that. **Gate** before updating: accept only if $d^2=\nu^\top S^{-1}\nu\le\chi^2_{2,0.99}=9.21$. A wrong-ID marker gives a large $d^2$ and is rejected; the price is that 1 % of good detections are rejected too.

### 4. Consistency: NEES and NIS ([C12](/lessons/C12), [RS03](/lessons/RS03))

With ground truth available in simulation, the **normalised estimation error squared** of the pose block is
$$\text{NEES}_k=(\mathbf{x}_k-\hat{\mathbf x}_k)^\top P_k^{-1}(\mathbf{x}_k-\hat{\mathbf x}_k)\ \sim\ \chi^2_3\quad(\text{3 dof, for }x,y,\theta).$$
For a consistent filter the mean is about 3 and about 95 % of samples fall inside the two-sided 95 % interval $[0.216,\,9.348]$ ($\texttt{evalkit.chi2\_ppf}$ uses a Wilson-Hilferty approximation: 0.181 and 9.324). The **normalised innovation squared** $\text{NIS}=\nu^\top S^{-1}\nu\sim\chi^2_2$ needs no ground truth; its mean is about 2. Interpretation:

| Observation | Meaning | Typical cause |
|---|---|---|
| mean NEES far above 3 | overconfident: $P$ too small | $Q$ too small, missing bias state, frame error |
| mean NEES far below 3 | underconfident: $P$ too large | $Q$ or $R$ inflated "to be safe" |
| NIS mean above 2, NEES fine | $R$ too small or outliers | detector noise underestimated |
| NIS mean below 2 | $R$ too large | $R$ inflated to hide a bug |

`evalkit.nees_consistency(errors, covs, dof)` returns `(fraction_inside, mean_nees)`. Consecutive samples are strongly correlated, so subsample (10 Hz here) and treat the 95 % as approximate; that is why the test accepts 85 % to 99.5 %.

### 5. Camera model and calibration ([V04](/lessons/V04))

Pinhole: $u=f_x X/Z+c_x$, $v=f_y Y/Z+c_y$. For a simulator camera with vertical field of view $\text{fovy}$ and image height $H$ pixels, the ideal focal length is $f=\dfrac{H/2}{\tan(\text{fovy}/2)}$ and $(c_x,c_y)$ is the image centre (up to the half-pixel convention; the test tolerates 3 px). Checkerboard calibration (Zhang) needs about 20 or more views with varied tilt; the quality number is the RMS reprojection error in pixels, and a good number on clean renders is below 0.5 px. Pixel noise becomes metric error as $\sigma_Z\approx Z\,\sigma_w/w$ with $w=f\,s/Z$ the marker's pixel width ($s$ its side): range error grows with $Z^2$.

### 6. What the filter cannot do ([C08](/lessons/C08))

With no landmark in view, the pose is only predicted: position and heading errors grow and nothing bounds them (the system is unobservable in absolute pose). The covariance must grow too; if it does not, the filter is lying. Plan landmark coverage (wall markers visible from most of the room) and log the longest interval without an accepted update; it explains most error spikes.

## Worked example

All numbers are **illustrative**, from a small stand-alone simulation (unicycle on a 60 s figure-eight, odometry with 1.5 % scale error and 2 % turn-rate scale error, gyro bias 0.01 rad/s, eight wall markers), not from a run of your repository.

### One EKF update, five audited runs, an outlier test and a calibration

**Problem.** The state is $\hat{\mathbf x}=(x,y,\theta,b)=(1.0,\,0.5,\,0.3,\,0)$ with $P=\operatorname{diag}(0.0025,\,0.0025,\,0.0009,\,0.0004)$ (std 5 cm, 5 cm, 1.7 degrees, 0.02 rad/s). A marker at $(1.9,\,1.0)$ is detected at range 1.09 m and bearing 0.25 rad, with $R=\operatorname{diag}(0.03^2,0.012^2)$ and a 99 % gate.

- (a) Perform the update by hand: predicted measurement, Jacobian, $S$, innovation $\nu$, gate on $d^2$, gain, posterior mean and standard deviations.
- (b) Show that the five audited 60 s runs below meet the accuracy limits (position RMSE 5 cm, heading RMSE 2 degrees, final error at least 3 times smaller than dead reckoning) and the consistency band, and explain why the first tuning ($q_v=0.05$, $q_w=0.01$) had to be rejected although its RMSE was similar.
- (c) With 10 % of the detections of seed 1000 replaced by wrong-ID, wrong-pose ones (771 attempts, 61 gated, position RMSE 5.4 cm against 4.1 cm clean, limit +50 %), estimate how many outliers were caught and how many passed.
- (d) Check a calibration: 24 views, RMS 0.31 px, $f_x=581.2$ px, for a 640 by 480 camera with fovy 45 degrees.

**Solution.**

1. *Predicted measurement.* $\Delta_x=1.9-1.0=0.9$, $\Delta_y=1.0-0.5=0.5$, $q=\Delta_x^2+\Delta_y^2=0.81+0.25=1.06$, $r=\sqrt{1.06}=1.0296$ m. Predicted bearing $\operatorname{atan2}(0.5,0.9)-\theta=0.5071-0.3=0.2071$ rad.
2. *Jacobian.* Differentiating $r$ and the bearing with respect to $(x,y,\theta,b)$ gives rows $[-\Delta_x/r,\,-\Delta_y/r,\,0,\,0]=[-0.874,\,-0.486,\,0,\,0]$ and $[\Delta_y/q,\,-\Delta_x/q,\,-1,\,0]=[0.472,\,-0.849,\,-1,\,0]$.
3. *Innovation covariance* $S=HPH^\top+R$. Range: $(0.874^2+0.486^2)\cdot0.0025+0.03^2=0.0025+0.0009=0.0034$. Bearing: $(0.472^2+0.849^2)\cdot0.0025+0.0009\cdot1+0.012^2=0.00236+0.0009+0.000144=0.0034$. The off-diagonal term is $(-0.874)(0.472)\cdot0.0025+(-0.486)(-0.849)\cdot0.0025=0$, so $S\approx\operatorname{diag}(0.0034,\,0.0034)$.
4. *Innovation.* $\nu=(1.09-1.0296,\;0.25-0.2071)=(0.0604,\,0.0429)$.
5. *Gate.* $d^2=\nu^\top S^{-1}\nu=0.0604^2/0.0034+0.0429^2/0.0034=1.07+0.54=1.62$. The 99 % threshold of $\chi^2_2$ is $-2\ln0.01=9.21$, and $1.62<9.21$, so the detection is accepted (1.62 is also a plausible draw from $\chi^2_2$, whose mean is 2).
6. *Gain and correction.* $K=PH^\top S^{-1}$ has rows $(-0.643,\,0.347)$, $(-0.357,\,-0.624)$, $(0,\,-0.265)$, $(0,\,0)$. Then $K\nu=(-0.643\cdot0.0604+0.347\cdot0.0429,\;\dots)=(-0.024,\,-0.048,\,-0.011,\,0)$. The marker is farther than predicted (range innovation positive), so the robot moves away from it.
7. *Posterior.* $\hat{\mathbf x}=(1.0-0.024,\;0.5-0.048,\;0.3-0.011,\;0)=(0.976,\,0.452,\,0.289,\,0)$. From $(I-KH)P$ the standard deviations are 2.6 cm, 2.7 cm and $1.47^\circ$ (from 5.0, 5.0 cm and $1.72^\circ$). The bias row of $K$ is zero because this prior has no correlation between $b$ and the other states, so $b$ and its variance are unchanged.
8. *Audit of the five runs.* In the table below position RMSE is 2.7 to 4.7 cm (all $\le5$ cm) and heading RMSE 0.29 to 1.07 degrees (all $\le2$). The final-error ratio to dead reckoning is $30.6/1.0=30.6$, $24.0/0.2=120$, $27.8/0.4=69.5$, $29.0/0.2=145$ and $21.9/0.2=109.5$: all far above 3. Consistency: NEES is a $\chi^2_3$ variable (3 degrees of freedom, expected mean 3) and NIS a $\chi^2_2$ variable (expected mean 2). The mean NEES is 3.17 to 4.74 (below the 2x slack limit 6) and the mean NIS 1.78 to 1.86 (close to 2); the fraction of NEES samples inside the 95 % interval is 0.903 to 0.980.
9. *Why the first tuning fails.* With $q_v=0.05$, $q_w=0.01$ the RMSE is similar, but the mean NEES is 5 to 10, up to more than three times its expectation of 3, and only 43 % to 87 % of the samples fall inside the interval (a consistent filter gives about 95 %): the filter is accurate but overconfident ($Q$ too small, so $P$ is too small), which is what the audit exists to catch. Raising to $q_v=0.08$, $q_w=0.02$, $q_b=2\times10^{-4}$ brings every run back into the band.
10. *Gate rate.* On seed 1000, 8 of 771 attempts were gated: $8/771=1.04\ \%$, while a 99 % gate rejects $0.01\cdot771=7.7$ good detections on average. The match with the expectation is exact to within one count.
11. *Outliers.* Injected: $0.10\cdot771\approx77$. Gated: 61, of which about 8 are good detections (the same 1 % rate), so caught outliers $\approx61-8=53$ and passing outliers $\approx77-53=24$. Those 24 look plausible enough to pass the gate, which is why the position RMSE rises at all: $5.4/4.1=1.32$, i.e. about $+31\ \%$ (the rounded values allow 29 % to 35 %), inside the +50 % limit.
12. *Calibration.* $f=240/\tan22.5^\circ=579.4$ px for the true camera. The estimate 581.2 px differs by $1.8$ px, $1.8/579.4=0.3\ \%$. The RMS reprojection error of 0.31 px is well under 1 px, and the principal point is off by 0.6 px and 0.9 px.

| seed | pos RMSE (cm) | heading RMSE (deg) | final error (cm) | dead-reckoning final error (cm) | NEES inside 95 % | mean NEES | mean NIS | gated |
|---|---|---|---|---|---|---|---|---|
| 1000 | 4.1 | 0.73 | 1.0 | 30.6 | 0.903 | 4.74 | 1.83 | 8 |
| 1001 | 3.1 | 0.29 | 0.2 | 24.0 | 0.958 | 3.62 | 1.85 | 7 |
| 1002 | 2.7 | 0.32 | 0.4 | 27.8 | 0.958 | 3.76 | 1.86 | 6 |
| 1003 | 4.7 | 1.07 | 0.2 | 29.0 | 0.980 | 4.15 | 1.86 | 8 |
| 1004 | 2.9 | 0.48 | 0.2 | 21.9 | 0.963 | 3.17 | 1.78 | 8 |

(Seeds 1000 to 1004, after tuning $q_v=0.08$, $q_w=0.02$, $q_b=2\times10^{-4}$ in the code of this lesson.)

**Check.** (a) Units: $\nu$ is in m and rad, $S$ in m$^2$ and rad$^2$, so $d^2$ is dimensionless. A second method, matrix products with $K=PH^\top S^{-1}$, $x^+=x+K\nu$ and $P^+=(I-KH)P$, gives $(0.9760,\,0.4517,\,0.2887,\,0)$ and standard deviations $(2.62\ \text{cm},\,2.72\ \text{cm},\,1.47^\circ,\,0.02\ \text{rad/s})$, as above. (b) The mean NEES and NIS of every row sit within the lesson's alarm (mean NEES below $2\cdot3=6$), and the same run-by-run numbers can be reproduced with `evalkit.nees_consistency` from CAP01. (c) The bookkeeping closes: $53$ caught $+\,24$ passed $=77$ injected, and $53+8=61$ gated. (d) $240/\tan22.5^\circ=579.41$ px reproduces the true focal length, so the $0.3\ \%$ error of the estimate is a real calibration residual, not a convention error.

**Takeaway.** One EKF update is a chain of small, checkable products (Jacobian, $S$, $K$); accuracy alone is not enough, since the NEES/NIS audit exposes an overconfident filter that RMSE hides, and the gate trades a known 1 % of good detections for protection against the outliers.

## Exercises

1. **(Easy)** A simulated camera is 640 by 480 pixels with a vertical field of view of 45 degrees. Compute $f$ in pixels, the horizontal field of view and the ideal principal point. *(Pinhole relations from the V04 lesson and the LearnOpenCV calibration article.)*
2. **(Easy)** Give the two-sided 95 % bounds for a 3-dof NEES and say what a mean NEES of 9.1 over a run means for a 3-dof pose filter. Which two knobs would you check first?
3. **(Easy)** A bearing is predicted as $-3.10$ rad and measured as $+3.10$ rad. Compute the innovation without and with wrapping.
4. **(Medium)** A marker has side 0.15 m. At 2 m with $f=579$ px, what is its pixel width, and what range error results from a width noise of 0.7 px? What happens at 1 m and at 4 m? What is the lateral error from a 0.5 px corner error at 2 m?
5. **(Medium)** For a robot at $(1.0,\,0.5)$ with heading 0.3 rad and a landmark at $(1.9,\,1.0)$, compute the two rows of $H$ for $x$, $y$, $\theta$ and $b_g$.
6. **(Medium)** Explain why the Joseph form is used and what the numerical-health test checks. When does $(I-KH)P$ fail in practice?
7. **(Medium)** The gate is $\chi^2_{2,0.99}=9.21$. Out of about 770 inlier detections, how many do you expect to be gated? You see 61 with a 10 % outlier injection: is that reasonable? What if you saw 61 with no outliers?
8. **(Medium)** *Observability.* No marker is visible for 20 s while the robot drives 0.3 m/s. With a residual gyro-bias error of 0.002 rad/s, estimate the heading error at the end and the resulting position error. What should the covariance do during this time?
9. **(Hard)** *Diagnosis.* Run A: mean NEES 9.0, mean NIS 2.0. Run B: mean NEES 1.1, mean NIS 0.4. Run C: mean NEES 3.1, mean NIS 3.4. Name the most likely problem in each and the first fix.
10. **(Hard)** *Test hygiene.* You tuned $Q$ and $R$ on the five test trajectories to pass the thresholds. Why is that a problem, how do you fix the process, and what do you report?
11. **(Hard, mini-project)** Implement the EKF and run four variants on the five trajectories: full filter; no gyro (wheel yaw rate instead); no landmarks; 10 % outliers with and without the gate. Report RMSE, NEES inside fraction and the longest gap without updates; state assumptions, a baseline (full filter), a boundary case (marker at bearing $\pm\pi$ behind the robot) and what observation would reject your filter.

## Reference implementation

The skeleton below is `corebot/estimation/ekf.py`. The contract (state, units, what is wrapped, what is logged) is in the docstrings; the maths is in Theory sections 1 to 3. Fill it in during Task 3.

```python
"""corebot/estimation/ekf.py (skeleton): planar EKF fusing odometry, gyro and landmark detections.

State  x = [x, y, theta, b_g]   x, y in metres (frame `map`), theta in rad wrapped to [-pi, pi),
                                 b_g = gyro bias in rad/s.
Inputs predict(): v (m/s) from wheel odometry, gyro_z (rad/s), dt (s). The heading rate is gyro_z - b_g.
Inputs update_landmark(): range (m) and bearing (rad) of a marker with a KNOWN map position,
                          measured in the base_link frame (bearing positive counter-clockwise from +x).
Everything is SI. All timestamps come from one clock; the caller guarantees dt > 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def wrap(angle: float) -> float:
    """Wrap an angle to [-pi, pi). Apply it to EVERY angle difference, including the bearing innovation."""
    raise NotImplementedError


@dataclass
class EkfConfig:
    q_v: float = 0.08          # m/s, std of the speed noise (document the units you chose)
    q_w: float = 0.02          # rad/s, std of the gyro noise (turns into a heading noise via dt)
    q_b: float = 2e-4          # rad/s per sqrt(s), random walk of the gyro bias
    r_range: float = 0.03      # m, landmark range noise
    r_bearing: float = 0.012   # rad, landmark bearing noise
    gate_chi2: float = 9.21    # 99 % quantile of chi-square with 2 dof
    p0_diag: tuple = (1e-4, 1e-4, 1e-4, 4e-4)


@dataclass
class Ekf:
    x: np.ndarray                                   # shape (4,)
    P: np.ndarray                                   # shape (4, 4), symmetric positive definite
    cfg: EkfConfig = field(default_factory=EkfConfig)
    nis: list = field(default_factory=list)         # one NIS value per ACCEPTED update (2 dof)
    gated: int = 0                                  # number of rejected detections

    def predict(self, v: float, gyro_z: float, dt: float) -> None:
        """Propagate the mean with the unicycle model and the covariance with F P F^T + G Q G^T.
        Re-symmetrise P at the end."""
        raise NotImplementedError

    def update_landmark(self, rng: float, bearing: float, landmark_xy: tuple) -> bool:
        """Range-bearing update with a Mahalanobis gate. Returns True if the detection was used.
        Steps: predicted measurement h(x); Jacobian H (2x4); innovation nu with wrapped bearing;
        S = H P H^T + R; d2 = nu^T S^-1 nu; reject if d2 > gate_chi2 (increment `gated`);
        K = P H^T S^-1; x += K nu (wrap theta); Joseph form P = (I-KH) P (I-KH)^T + K R K^T; log d2 in `nis`."""
        raise NotImplementedError
```

## Independent practice

### Goal

Localise CoreBot Tidy in the simulated lab: calibrate the camera from checkerboard renders, detect wall markers and compute a range-bearing measurement, build an EKF over odometry, gyro and landmarks, run five seeded 60 s trajectories with ground truth, and show with NEES/NIS that the filter is both accurate and honest. This is milestone CAP03; it consumes the calibrated odometry of CAP02.

### Setup

Work in `~/corebot-capstone`. You need NumPy and OpenCV (`opencv-python-headless`; pin the versions you use in `pyproject.toml`). Rendering needs MuJoCo with EGL or OSMesa (see CAP01 for `MUJOCO_GL`); OSMesa is slow (about 5 to 10 frames per second at 320 by 240), so render the 24 calibration views and 100 marker frames once and cache them. Commands:

```bash
cd ~/corebot-capstone && source .venv/bin/activate
pip install "numpy>=1.26" "opencv-python-headless>=4.9" pytest   # pin the versions you actually use in pyproject.toml
mkdir -p runs/cap03 configs
python -m corebot.estimation.render_calib --views 24 --seed 1000 --out runs/cap03/calib_views   # your script, Task 1
python -m corebot.estimation.calibration --views runs/cap03/calib_views --out configs/camera.yaml
python -m bench.run_cap03 --seeds 1000 1001 1002 1003 1004 --out runs/cap03                    # your script, Task 6
pytest -q tests/acceptance/test_cap03.py
```

The artefact schema the tests read is fixed:

```text
runs/cap03/traj_<i>.npz        (one per seeded 60 s trajectory, N samples at 100 Hz)
  t      (N,)       s            time
  truth  (N, 3)     m, m, rad    ground truth x, y, theta  (ONLY used by tests and plots, never by the filter)
  est    (N, 3)     m, m, rad    EKF estimate
  dr     (N, 3)     m, m, rad    dead reckoning from wheel odometry only
  P      (N, 4, 4)               EKF covariance of [x, y, theta, b_g]
  nis    (M,)                    NIS (2 dof) of every ACCEPTED landmark update
  gated  ()         count        detections rejected by the gate
  upd_median_ms ()  ms           median wall time of one update_landmark call
runs/cap03/outliers_0.npz      same keys, same seed as traj_0, with 10 % wrong-ID/wrong-pose detections
runs/cap03/calibration.json    n_images, rms_px, fx, fy, cx, cy, and "truth": {fx, fy, cx, cy} from the sim camera
runs/cap03/landmark_pose.npz   pos_err_m (K,), yaw_err_deg (K,), dist_m (K,) for >= 100 detections
```

### Tasks

1. **Calibration** (`estimation/calibration.py`, `configs/camera.yaml`): render at least 20 checkerboard views with varied pose, detect corners, calibrate, and report RMS, focal length and principal point against the simulator's truth (from `fovy`).
2. **Landmarks** (`estimation/landmarks.py`): detect the wall markers, run PnP, convert to range and bearing in `base_link` using the camera extrinsics; 100 frames at distances up to 2 m, median position and yaw error written to `landmark_pose.npz`.
3. **EKF** (`estimation/ekf.py`): state $[x,y,\theta,b_g]$, predict, range-bearing update with wrapped innovation, Mahalanobis gate, Joseph form.
4. **Noise models from data**: estimate the odometry and gyro noise from a stationary and a constant-velocity run, and the detector noise from Task 2; write a short derivation in `docs/noise_models.md` (every unit and frame convention listed).
5. **Trajectories**: five seeded 60 s runs (`seeds 1000..1004`) logging truth, estimate, dead reckoning, $P$, NIS and the number of gated detections. Plot error versus time with 2-sigma bands.
6. **Outlier run**: same seed as trajectory 0 with 10 % wrong-ID or wrong-pose detections; save `outliers_0.npz`.
7. **Honesty report** (`docs/consistency.md`): NEES/NIS tables, one paragraph on observability (what happens with no landmark in view), one on what you tuned and on which seeds.
8. **Optional**: visual odometry notebook (essential matrix, scale from wheel odometry); see the extension challenge.

### Starter code

Signatures for the perception side (the EKF skeleton is in Reference implementation):

```python
"""estimation/calibration.py and estimation/landmarks.py (starter signatures)."""
from __future__ import annotations

import numpy as np


def calibrate_camera(images: list, board: tuple = (9, 6), square_m: float = 0.03) -> dict:
    """Checkerboard calibration (Zhang). Return {"fx","fy","cx","cy","dist","rms_px","n_images"}.
    Use at least 20 views with varied tilt and distance; reject views where corners are not found.
    Hint: keep the corner detection and the optimisation separate so each can be tested alone."""
    raise NotImplementedError


def marker_pose_camera(corners_px: np.ndarray, K: np.ndarray, side_m: float) -> np.ndarray:
    """PnP for one square marker: 4x2 pixel corners -> 4x4 transform T_cam_marker."""
    raise NotImplementedError


def to_range_bearing(T_base_cam: np.ndarray, T_cam_marker: np.ndarray) -> tuple:
    """Marker position in the base frame -> (range_m, bearing_rad). T_base_cam comes from configs/camera.yaml."""
    raise NotImplementedError
```

### Tests

`tests/acceptance/test_cap03.py` is below. The gate checks are `test_camera_calibration`, `test_ekf_accuracy` and `test_consistency`. The tests use `evalkit.nees_consistency` from CAP01. **Thresholds are provisional starting values; tighten them once your own reference run exists.** One-line rationales: at least 20 views and RMS under 0.5 px (the usual floor for a stable Zhang calibration on clean renders); focal error under 2 % and principal point under 3 px (what the PnP range accuracy needs); landmark median error under 5 cm and 3 degrees at up to 2 m (about the 5 cm map cell of CAP04); position RMSE under 5 cm and heading RMSE under 2 degrees (7 cm sideways error after 2 m at 2 degrees); final error 3 times better than dead reckoning (otherwise the landmarks add nothing); NEES inside fraction 85 % to 99.5 % (correlated samples make exactly 95 % unlikely, and 100 % means underconfident); mean NIS within 0.5 to 1.5 times its expectation; 10 % outliers cost at most 50 % RMSE; $P$ symmetric to $10^{-9}$ and positive definite (numerical hygiene); update under 2 ms (a 100 Hz loop must not be dominated by the filter).

```python
"""tests/acceptance/test_cap03.py : reads runs/cap03/.  GATE = counts toward the graduation gate.
Thresholds are provisional starting values; tighten them once your own reference run exists."""
import json, pathlib
import numpy as np
import pytest
from corebot.evalkit import nees_consistency

RUNS = pathlib.Path("runs/cap03")
TRAJ = sorted(RUNS.glob("traj_*.npz"))

def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi

def _err(z):                                   # estimate minus truth, heading wrapped
    e = z["est"] - z["truth"]
    e[:, 2] = _wrap(e[:, 2])
    return e

def test_five_trajectories_exist():
    assert len(TRAJ) >= 5

def test_camera_calibration():                  # GATE
    c = json.loads((RUNS / "calibration.json").read_text())
    assert c["n_images"] >= 20                  # Zhang's method needs varied views; 20 is the usual floor
    assert c["rms_px"] < 0.5                    # sub-pixel corners are achievable on clean renders
    assert abs(c["fx"] - c["truth"]["fx"]) / c["truth"]["fx"] < 0.02
    assert abs(c["cx"] - c["truth"]["cx"]) < 3.0 and abs(c["cy"] - c["truth"]["cy"]) < 3.0

def test_landmark_pose():
    z = np.load(RUNS / "landmark_pose.npz")
    near = z["dist_m"] <= 2.0
    assert len(z["pos_err_m"]) >= 100
    assert np.median(z["pos_err_m"][near]) < 0.05
    assert np.median(z["yaw_err_deg"][near]) < 3.0

@pytest.mark.parametrize("path", TRAJ)
def test_ekf_accuracy(path):                    # GATE
    z = np.load(path); e = _err(z)
    assert np.sqrt(np.mean(e[:, 0] ** 2 + e[:, 1] ** 2)) < 0.05          # 5 cm: one cell of the 5 cm map in CAP04
    assert np.degrees(np.sqrt(np.mean(e[:, 2] ** 2))) < 2.0              # 2 deg: 7 cm sideways error after 2 m
    dr = z["dr"] - z["truth"]
    assert np.hypot(*e[-1, :2]) * 3 <= np.hypot(*dr[-1, :2])             # fusion at least 3x better than dead reckoning

@pytest.mark.parametrize("path", TRAJ)
def test_consistency(path):                     # GATE
    z = np.load(path); e = _err(z)
    idx = range(0, len(e), 10)                  # 10 Hz subsample: neighbouring samples are strongly correlated
    inside, mean_nees = nees_consistency([e[i].tolist() for i in idx],
                                         [z["P"][i, :3, :3].tolist() for i in idx], dof=3)
    assert 0.85 <= inside <= 0.995              # a 95 % interval should hold ~95 %, not 100 % and not 60 %
    assert mean_nees < 3 * 2.0                  # mean NEES near dof = 3; 2x slack is the "overconfident" alarm
    assert 0.5 * 2 <= float(np.mean(z["nis"])) <= 1.5 * 2                # NIS of a 2-dof range-bearing update

def test_gating_with_outliers():
    clean = _err(np.load(RUNS / "traj_0.npz")); bad_z = np.load(RUNS / "outliers_0.npz"); bad = _err(bad_z)
    rm = lambda e: np.sqrt(np.mean(e[:, 0] ** 2 + e[:, 1] ** 2))
    assert rm(bad) < 1.5 * rm(clean)            # 10 % wrong detections may cost at most 50 % RMSE
    assert int(bad_z["gated"]) > 0              # the filter must say it rejected something

@pytest.mark.parametrize("path", TRAJ)
def test_numerical_health(path):
    z = np.load(path); P = z["P"]
    assert np.max(np.abs(P - np.swapaxes(P, 1, 2))) < 1e-9
    assert np.linalg.eigvalsh(P).min() > 0.0
    assert float(z["upd_median_ms"]) < 2.0      # leaves room for a 100 Hz loop on a laptop
```

### Expected output

With all artefacts present, `pytest -q tests/acceptance/test_cap03.py` prints (illustrative timing):

```text
...................                                                      [100%]
19 passed in 6.8s
```

A sample `runs/cap03/metrics.json` that your report script may write (illustrative values, two of the five trajectories shown):

```json
{
  "milestone": "CAP03",
  "calibration": {"n_images": 24, "rms_px": 0.31, "fx_err_pct": 0.31, "cx_err_px": 0.6, "cy_err_px": 0.9},
  "landmark_pose": {"median_pos_err_m": 0.018, "median_yaw_err_deg": 1.0, "n_frames": 100},
  "ekf": [
    {"seed": 1000, "pos_rmse_m": 0.041, "head_rmse_deg": 0.73, "final_err_m": 0.010, "dr_final_err_m": 0.306,
     "nees_inside": 0.903, "nees_mean": 4.74, "nis_mean": 1.83, "gated": 8},
    {"seed": 1001, "pos_rmse_m": 0.031, "head_rmse_deg": 0.29, "final_err_m": 0.002, "dr_final_err_m": 0.240,
     "nees_inside": 0.958, "nees_mean": 3.62, "nis_mean": 1.85, "gated": 7}
  ],
  "outliers_10pct": {"pos_rmse_m": 0.054, "rmse_increase_pct": 31, "gated": 61}
}
```

### Extension challenge

**Stretch (bonus, not a gate):** monocular visual odometry. Track features between frames, estimate the essential matrix, recover rotation and a translation direction, and set the scale from wheel odometry; target a yaw drift under 3 degrees per 10 m. Also try estimating the odometry scale as a fifth state and show with NEES whether the filter improves. Keep it honest: report when it does not help.

**Optional hardware note:** if you built the CAP02 ESP32 base, log real wheel counts and a cheap IMU's gyro (see HW04) and run your EKF offline on them without landmarks; compare the dead-reckoning drift with the simulated one. No grade depends on it.

### Library track

Replace your EKF with `robot_localization` (ROS 2 Jazzy), fusing `/odom` and `/imu`, and compare its error on the same bag with yours. Then check OpenCV's calibration against your own:

```yaml
# configs/rl_ekf.yaml : the same fusion with robot_localization (ROS 2 Jazzy) instead of your own ekf.py
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    two_d_mode: true
    publish_tf: true
    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom
    odom0: /odom
    odom0_config: [false, false, false,  false, false, false,
                   true,  false, false,  false, false, true,
                   false, false, false]            # forward speed and yaw rate from wheels
    imu0: /imu
    imu0_config: [false, false, false,  false, false, false,
                  false, false, false,  false, false, true,
                  false, false, false]             # yaw rate from the gyro
    imu0_remove_gravitational_acceleration: false
```

```python
# Needs: pip install numpy opencv-python-headless
# OpenCV reference for Task 1: compare its intrinsics and RMS with your own calibration.
import glob

import cv2
import numpy as np

BOARD, SQUARE = (9, 6), 0.03                       # inner corners, square size in metres
objp = np.zeros((BOARD[0] * BOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:BOARD[0], 0:BOARD[1]].T.reshape(-1, 2) * SQUARE
obj_pts, img_pts, size = [], [], None
for path in sorted(glob.glob("runs/cap03/calib_views/*.png")):
    gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    size = gray.shape[::-1]
    ok, corners = cv2.findChessboardCorners(gray, BOARD)
    if ok:
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                   (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3))
        obj_pts.append(objp)
        img_pts.append(corners)
rms, K, dist, _, _ = cv2.calibrateCamera(obj_pts, img_pts, size, None, None)
print("views used:", len(obj_pts), " RMS reprojection error (px):", round(rms, 3))
print("fx, fy, cx, cy =", K[0, 0], K[1, 1], K[0, 2], K[1, 2])
```

## Verification

Do the arithmetic before the code: $f=579.4$ px, the $\chi^2$ bounds, one update by hand as in the worked example. Verify the filter with the checks that are cheap and decisive: the covariance grows when no landmark is seen (print $\operatorname{tr}P$ for 10 s of dead reckoning); a deliberately wrong bearing sign makes NIS explode; a wrapped versus unwrapped innovation test at bearing $\pm\pi$; the filter run with the true parameters and no noise returns the truth. Verify the evaluation as well: tuning seeds must differ from the test seeds, and plots must show 2-sigma bands.

**Scoring and graduation.** CAP03 is worth **12 of 100** points: 60 % automated (weighted fraction of checks, gates above) and 40 % human rubric scored 0 to 4: noise models justified and tuned from data, every unit and frame convention explained, honest discussion of observability, clear plots. Graduation needs every gate check of every milestone, every milestone at 60 or more and a weighted total of 70 or more. A self-review prompt for an LLM (give it the code and the artefacts, not your verdict): *"Audit this EKF. Check the heading wrap in every angle difference, the frame and sign of the camera extrinsics, whether R or Q are inflated to hide errors, whether tuning and test data overlap, and whether NEES/NIS support the claimed accuracy. Score 0 to 4 on noise models, conventions, observability and plots with line references."*

## Failure modes

- Forgetting to wrap the bearing innovation (or the heading after the update): spikes of $2\pi$ when a marker is behind the robot.
- Camera versus robot frame extrinsics with a sign or axis error: the filter converges to a pose that is consistently shifted or rotated; NIS is large.
- Timestamps from different clocks (sim time versus wall time): detections are applied to the wrong state.
- Inflating $R$ or $Q$ to hide a bug: accuracy looks fine, NEES and NIS are far below their expectations (underconfident filter).
- Overconfidence: $Q$ too small; the filter stops listening to landmarks; mean NEES far above 3.
- Landmark ID ambiguity: two similar markers are swapped; the gate saves you only if the error is large.
- Tuning and testing on the same seeds.
- Degrees versus radians in one place (the gyro in deg/s, the detector in degrees).
- Using ground truth in the filter by accident: add the AST or grep test that `estimation/` never imports the simulator's true pose (the CAP04 rule applies from here on).
- Symmetric and positive-definite $P$ lost to the non-Joseph update after thousands of steps.

## Alternatives and trade-offs

An **EKF** is simple and fast but linearises around the estimate and can diverge with a bad prior; an **unscented** or **error-state (ESKF)** filter handles the angle nonlinearity better; a **particle filter** (AMCL, as in Nav2) copes with multi-modal pose (symmetric rooms, kidnapping) at higher cost; **factor graphs** (GTSAM) smooth the whole trajectory and win accuracy offline. Landmarks can enter as range-bearing (here) or as raw pixel measurements (tighter, needs the camera model in the filter). Wheel odometry plus gyro is cheap; visual odometry removes the dependence on wheel scale but needs texture and a scale source; lidar scan matching (CAP04 mapping) is the usual extra sensor. The library choice, `robot_localization`, is configuration-heavy but battle-tested; writing your own once is the way to learn what its parameters mean.

## Transfer and retention

**This milestone prepares for:** CAP04 (the planner and the occupancy mapper use your pose and may use its covariance), CAP05 (the hand-eye transform and the base pose chain depend on it), CAP07 (an estimator-divergence flag feeds the safety supervisor) and CAP08 (the ablation "no landmark updates" and the sim-to-real twin both test this filter).

Recall prompts for next week, without notes:

1. Write the range-bearing measurement function and its Jacobian.
2. State the expected values of mean NEES (3 dof) and mean NIS (2 dof) and what you conclude if they are 3 times larger.
3. Why wrap the innovation, and which angles need it?
4. Why Joseph form, and what two properties of $P$ does it protect?
5. What happens to the covariance with no landmark in view, and why?

## Exercise answers

1. $f=240/\tan(22.5^\circ)=579.4$ px. Horizontal field of view $2\arctan(320/579.4)=57.8^\circ$. Ideal principal point $(320,\,240)$ (or $(319.5,\,239.5)$ with pixel centres at half-integers; the 3 px test tolerance covers both).
2. Exact bounds $[0.216,\,9.348]$. A mean of 9.1 against an expectation of 3 means the actual errors are about three times larger (in squared normalised units) than $P$ admits: the filter is overconfident. Check $Q$ first (too small, or the gyro bias not modelled) and then frame and sign conventions of the measurement.
3. Without wrapping: $3.10-(-3.10)=6.20$ rad, an absurd innovation. Wrapped: $6.20-2\pi=-0.083$ rad.
4. Pixel width $w=579\cdot0.15/2=43.4$ px. $\sigma_Z=Z\,\sigma_w/w=2\cdot0.7/43.4=0.032$ m. At 1 m: $w=86.9$ px and $\sigma_Z=0.008$ m; at 4 m: $w=21.7$ px and $\sigma_Z=0.129$ m (error scales with $Z^2$). Lateral error $Z\,\sigma_{px}/f=2\cdot0.5/579=1.7$ mm: the range dominates, which is why $R$ is larger in range than the pixel noise suggests and why the landmark test only goes to 2 m.
5. $\Delta_x=0.9$, $\Delta_y=0.5$, $q=1.06$, $r=1.0296$. Range row: $[-0.9/1.0296,\,-0.5/1.0296,\,0,\,0]=[-0.874,\,-0.486,\,0,\,0]$. Bearing row: $[0.5/1.06,\,-0.9/1.06,\,-1,\,0]=[0.472,\,-0.849,\,-1,\,0]$.
6. The Joseph form is a sum of two positive semi-definite matrices, so $P$ stays positive semi-definite and symmetric (after one explicit symmetrisation) for any gain, including a gain computed with rounding errors or a mistuned $R$. $(I-KH)P$ equals it only for the exact optimal $K$ and in floating point drifts asymmetric; with a tiny $R$ and thousands of updates it can acquire a negative eigenvalue, after which the gate and the NEES computation break. The test checks symmetry to $10^{-9}$ and the smallest eigenvalue above 0 for the whole run.
7. About 1 % of 770, i.e. 7 to 8 (the example saw 8). With 10 % outliers (about 77 injected) 61 gated is reasonable: most outliers are caught, a few (about 24) pass. With 61 and no outliers the filter is badly overconfident or has a frame/sign bug: the innovations are far larger than $S$ predicts.
8. Heading error $0.002\cdot20=0.04$ rad $=2.3^\circ$ at the end (growing linearly, mean $0.02$ rad). Position error is about $0.3\cdot20\cdot0.02=0.12$ m. The covariance must grow as well: the heading variance grows roughly with $t^2$ (bias uncertainty times time) plus the gyro noise, and the position variance faster. If the printed $P$ stays flat, the filter is lying.
9. A: overconfident predict step (Q too small, no bias state, frame error) with a correct $R$; inflate $Q$ and check the gyro bias first. B: underconfident, $Q$ and $R$ both inflated (likely to hide a bug); recompute them from data. C: NEES fine but NIS above its expectation of 2: detector noise $R$ is too small or the detector has outliers; inflate $R$ from the Task 2 statistics and check the gate.
10. Tuning on the test seeds makes the thresholds measure how well you fitted those five runs, not how good the filter is. Fix: tune on a separate set (seeds 100 to 119), freeze, then evaluate once on 1000 to 1004. Report which seeds you used for each, and the tuned values.
11. Expected: without the gyro the heading error is dominated by the wheel scale error and RMSE rises (bias becomes unobservable); without landmarks RMSE is of the order of the dead-reckoning error and NEES is far above the band unless $P$ is allowed to grow; with outliers and no gate the RMSE blows up far beyond +50 %, with the gate it stays within it. Boundary case: a marker at $\pm\pi$: without wrapping you see a $2\pi$ jump. A rejecting observation: mean NEES above 6 on the test seeds, or $P$ constant while no landmark is visible.

## Further reading

- [Camera calibration using OpenCV (LearnOpenCV)](https://learnopencv.com/camera-calibration-using-opencv/) - checkerboard calibration step by step.
- [robot_localization (Jazzy)](https://docs.ros.org/en/jazzy/p/robot_localization/) - the library EKF and its configuration.
- [AprilTag library](https://github.com/AprilRobotics/apriltag) - fiducial detection and pose.
- [Probabilistic Robotics (Thrun, Burgard, Fox)](https://mitpress.mit.edu/9780262201629/probabilistic-robotics/) - the EKF localisation and SLAM chapters.
- [Thrun's author page](https://sites.google.com/site/thrunstuff) - book companion material.
- [Extended Kalman filter (Wikipedia)](https://en.wikipedia.org/wiki/Extended_Kalman_filter) - the predict/update equations and the Jacobians in one place.
- Videos: Cyrill Stachniss, *EKF-SLAM*; *Intrinsic Camera Calibration - 5 Minutes with Cyrill*.

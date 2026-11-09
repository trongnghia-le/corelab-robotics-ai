---
{
  "id": "cap05-capstone",
  "module_id": "CAP05",
  "title": "Capstone milestone 5: perception-driven grasping with segmentation, 3D pose and Jacobian IK",
  "summary": "Find coloured blocks in RGB-D images, turn pixels into a 3D pose in the arm base frame with hand-eye calibration, and grasp them with a damped-least-squares IK, quintic trajectories and a failure taxonomy, judged by a seeded 50-trial benchmark.",
  "estimated_minutes": 1800,
  "project_minutes": 1800,
  "prerequisites": [
    "CAP03",
    "R05",
    "R06",
    "R07",
    "V10",
    "V13"
  ],
  "source_refs": [
    {
      "title": "MIT 6.4210 Robotic Manipulation: Basic pick and place",
      "url": "https://manipulation.mit.edu/pick.html"
    },
    {
      "title": "MIT 6.4210 Robotic Manipulation: Kinematics and Jacobians",
      "url": "https://manipulation.mit.edu/robot.html"
    },
    {
      "title": "MuJoCo documentation: modeling",
      "url": "https://mujoco.readthedocs.io/en/stable/modeling.html"
    },
    {
      "title": "MuJoCo Menagerie (SO-101 model)",
      "url": "https://github.com/google-deepmind/mujoco_menagerie"
    },
    {
      "title": "CS231n: Convolutional Neural Networks for Visual Recognition",
      "url": "https://cs231n.github.io/"
    },
    {
      "title": "Pinhole camera model (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Pinhole_camera_model"
    }
  ],
  "objectives": [
    "Deproject a pixel and a metric depth into a camera-frame point and move it to the arm base frame with a hand-eye transform.",
    "Segment coloured blocks with an HSV baseline and a small CNN and report mean IoU on held-out seeds.",
    "Solve a 5-DOF top-down grasp with damped least squares IK that respects joint limits and avoids branch flips.",
    "Generate quintic trajectories within velocity, acceleration and torque limits and check feasibility with inverse dynamics.",
    "Run a seeded pick-and-place benchmark, judge it with a Wilson bound and classify every failure in a taxonomy."
  ],
  "core_theory": [
    "Capstone integration: inverse kinematics, Jacobians, rigid-body dynamics, segmentation, 3D perception"
  ],
  "labs": [
    "Complete the CAP05 milestone brief in ~/corebot-capstone: pass tests/acceptance/test_cap05.py on 50 seeded pick-and-place trials."
  ],
  "assessment_refs": [
    "CAP05-diagnostic-v1"
  ],
  "review_prompts": [
    "Trace one pixel of a red block through deprojection, the hand-eye transform and IK to a joint target, naming the frame at every step.",
    "Explain why the segmentation train and test sets are split by scene seed and not by frame."
  ],
  "extension_refs": [
    "https://huggingface.co/docs/lerobot/so101",
    "https://github.com/TheRobotStudio/SO-ARM100"
  ]
}
---

## Why this matters

CoreBot Tidy exists to move a block from the table into a bin. CAP05 is the part that touches the object: it decides **where the block is** (perception), **how to approach it** (grasp planning) and **how the arm gets there** (kinematics, trajectory, torque). It is also the first place where small errors multiply: one pixel of segmentation error, 5 mm of depth bias, a 1 degree error in the hand-eye rotation and a missing joint limit add up to a gripper that closes on air.

This milestone is independent of CAP04 (you can run them in parallel), but both start from CAP03: the arm needs the base to be localised so the camera frame, the base frame and the arm frame agree. CAP06 will later replace your scripted grasp with a learned one behind the same `GraspSkill` interface, and CAP08 counts every failure of this milestone in its error budget (`DETECTION`, `GRASP_SLIP`, `PLACE_MISS`).

**Scoring.** CAP05 carries a weight of 13 out of 100 for graduation. Its gate checks (bold in the Tests section) are inverse kinematics and the pick-and-place benchmark. The optional real SO-101 tier never substitutes for a failing gate.

## Intuition

Seeing, deciding, reaching. The camera gives colours and distances for each pixel; segmentation says which pixels are "the red block"; deprojection turns those pixels into a 3D point; one fixed transform, the **hand-eye calibration**, expresses that point in the arm's own frame; inverse kinematics finds joint angles that put the fingertips there with the gripper pointing down; a smooth trajectory gets the arm to those angles without exceeding the motors' limits. Each step has a cheap numeric check, and that is the point of the milestone: you debug it as a chain, not as a mystery.

![Architecture of the CoreBot Tidy capstone with firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation, task layer and a safety supervisor](/lesson-figures/CAP-architecture.svg)

*Where CAP05 sits: the perception box produces object poses in the base frame, the manipulation box turns them into joint trajectories behind the `GraspSkill` interface.*

Earlier CoreLab topics used here:

- [CAP03](/lessons/CAP03): the camera calibration (intrinsics $K$) and the base frame you localise in.
- [R05 Inverse kinematics](/lessons/R05): branches, reachability and numerical solvers.
- [R06 Robot Jacobian](/lessons/R06): the matrix inside the damped least squares step.
- [R07 Rigid-body dynamics](/lessons/R07): inverse dynamics for the torque feasibility check.
- [V10 Segmentation](/lessons/V10): IoU, mIoU and training hygiene.
- [V13 3D perception](/lessons/V13): depth, point clouds and rigid alignment.
- Also: [V04 Camera calibration](/lessons/V04), [R03 Rigid-body transformations](/lessons/R03) and [R04 Forward kinematics](/lessons/R04) (your CAP01 FK is the model the solver uses).

## Theory and derivation

The integration notes: the formulas and interfaces that decide whether the milestone passes.

![Pipeline from RGB-D image through segmentation, deprojection and hand-eye transform to a detection, then grasp planning, inverse kinematics, quintic trajectory and the arm, with a failure taxonomy box](/lesson-figures/CAP05.svg)

### 1. Deprojection (source: V04, V13)

With a pinhole camera of intrinsics $f_x,f_y,c_x,c_y$, a pixel $(u,v)$ with metric depth $z$ (distance along the optical axis) maps to
$$p_\text{cam}=\Big(\tfrac{u-c_x}{f_x}\,z,\ \tfrac{v-c_y}{f_y}\,z,\ z\Big)$$
in the optical frame (x right, y down, z forward). MuJoCo gives the vertical field of view, so $f_y=\frac{H/2}{\tan(\text{fovy}/2)}$ and $f_x=f_y$ for square pixels. The MuJoCo depth buffer is **normalised**, not metres: convert with the near and far planes before using it, and reject non-positive values. Use the **median** of the per-pixel points of a mask, not the mean, because mask edges blend block and background depth.

### 2. Hand-eye calibration (source: R03, V13)

The camera pose in the base frame is a rigid transform $T_\text{base,cam}=(R,t)$. Given paired points $p_i^\text{cam}$ and $p_i^\text{base}$ (collected by touching or by reading simulator truth during calibration only), the least-squares transform comes from the Kabsch method: subtract the centroids, take the SVD of $H=\sum \tilde p^\text{cam}_i\,(\tilde p_i^\text{base})^\top=U\Sigma V^\top$, then $R=V\,\mathrm{diag}(1,1,\det(VU^\top))\,U^\top$ and $t=\bar p^\text{base}-R\bar p^\text{cam}$. Use at least 10 well-spread, non-collinear points, and **evaluate on held-out points**. A one-pixel error is $z/f_y\approx1$ mm at 0.42 m, so a 5 mm RMS target is about five pixels of total error.

### 3. Damped least squares IK for a 5-DOF arm (source: R05, R06)

The SO-101 arm has five joints before the gripper, so you cannot command a full 6D pose. A top-down grasp needs the tip position (3 numbers) and the approach pitch (1 number); the wrist roll is set afterwards from the object's yaw. With task error $e=[\Delta p;\ \Delta\text{pitch}]$ and task Jacobian $J\in\mathbb R^{4\times5}$:
$$\Delta q=J^\top\big(JJ^\top+\lambda^2I\big)^{-1}e,$$
clip each joint step to $0.2$ rad, clip $q$ to the limits after every step, and **start from the current joints** so the solution stays on one branch. Near a singularity, the pseudo-inverse blows up ($1/\sigma$); the damped version is bounded by $\sigma/(\sigma^2+\lambda^2)\le1/(2\lambda)$. A planar arm has two solutions (elbow up/down); pick the one whose joint angles stay inside the limits and closest to $q_\text{now}$.

### 4. Trajectories and torque feasibility (source: R07)

A quintic with $s=t/T$ and blend $10s^3-15s^4+6s^5$ starts and ends at zero velocity and acceleration. For a joint move $|\Delta q|$ the peaks are
$$\dot q_\max=\tfrac{15}{8}\tfrac{|\Delta q|}{T}=1.875\tfrac{|\Delta q|}{T},\qquad \ddot q_\max=\tfrac{10}{\sqrt3}\tfrac{|\Delta q|}{T^2}=5.7735\tfrac{|\Delta q|}{T^2},$$
so the shortest feasible duration is $T=\max_j\big(\tfrac{1.875|\Delta q_j|}{v_j},\sqrt{\tfrac{5.7735|\Delta q_j|}{a_j}}\big)$. Then check torque with inverse dynamics $\tau=M(q)\ddot q+C(q,\dot q)\dot q+g(q)$ along the sampled trajectory against the actuator `forcerange` in your MJCF. Holding an extended arm against gravity often uses most of the shoulder torque before any acceleration is added.

### 5. Segmentation metrics and benchmark statistics (source: V10, RS02)

For each class, $\text{IoU}=\frac{TP}{TP+FP+FN}$ and mIoU is the mean over classes present in the truth. Split train, validation and test by **scene seed**, not by frame: frames from one episode are near duplicates, so a frame split leaks the test set and inflates mIoU. For the benchmark use the lower Wilson 95 % bound (`evalkit.wilson_interval`) and a failure taxonomy whose counts sum exactly to the number of failures.

## Worked example

Reference trace of a passing run. **Illustrative values**, computed with the standard-library script in Verification (using the illustrative links $L_1=0.116$, $L_2=0.135$, $L_3=0.10$ m; read yours from your MJCF), not taken from a real run.

### From a pixel to joint angles, a joint trajectory and the acceptance table

**Problem.** The camera image is 640 x 480 with fovy 60 degrees. A block centroid is detected at pixel $(352,236)$ with depth 0.42 m. The camera sits at $(0.10,0,0.35)$ m in `base_link`, pitched down 50 degrees; the arm pillar is 0.17 m ahead of `base_link`.

- (a) Find the point in the camera frame, in `base_link` and in `arm_base`, and its radius $r$.
- (b) Solve the inverse kinematics (IK) for pan, shoulder, elbow and wrist with the tool pointing straight down, with links $L_1=0.116$, $L_2=0.135$, $L_3=0.10$ m and a wrist limit of $\pm110^\circ$; pick the admissible branch.
- (c) For a 0.8 rad joint move in 1.2 s with a quintic time scaling, find the peak speed and peak acceleration.
- (d) Decide the acceptance table below, including why 43 of 50 picks (86 %) passes the gate and 40 of 50 (80 %) would not.

**Solution.**

Assumptions taken from the Verification script (not stated in the original text): the principal point is the image centre $(c_x,c_y)=(320,240)$ with square pixels; the camera frame has $x$ to the right, $y$ down, $z$ forward; `arm_base` has the same height as `base_link`; the shoulder axis is at height $Z_S=0.05$ m above `arm_base`.

1. *Focal length.* $f_y=(480/2)/\tan(60^\circ/2)=240/\tan30^\circ=415.7$ px.
2. *Deprojection.* $x=(352-320)\cdot0.42/415.7=0.0323$ m, $y=(236-240)\cdot0.42/415.7=-0.0040$ m, $z=0.420$ m: $p_\text{cam}=(0.0323,\,-0.0040,\,0.420)$ m.
3. *Camera axes in `base_link`.* With pitch $50^\circ$: forward $=(\cos50^\circ,0,-\sin50^\circ)=(0.6428,\,0,\,-0.7660)$, right $=(0,-1,0)$, down $=(-\sin50^\circ,0,-\cos50^\circ)=(-0.7660,\,0,\,-0.6428)$.
4. *Transform.* $p_\text{base}=t+x\cdot\text{right}+y\cdot\text{down}+z\cdot\text{forward}$ with $t=(0.10,0,0.35)$. $X=0.10+(-0.0040)(-0.7660)+0.42\cdot0.6428=0.10+0.0031+0.2700=0.3731$; $Y=-0.0323$; $Z=0.35+(-0.0040)(-0.6428)+0.42\cdot(-0.7660)=0.35+0.0026-0.3217=0.0309$. So $p_\text{base}=(0.3731,\,-0.0323,\,0.0309)$ m.
5. *To `arm_base`.* Subtract the 0.17 m pillar offset along $x$: $(0.2031,\,-0.0323,\,0.0309)$ m, radius $r=\sqrt{0.2031^2+0.0323^2}=0.2056$ m.
6. *Pan.* $\operatorname{atan2}(-0.0323,\,0.2031)=-9.0^\circ$.
7. *Wrist point.* With the tool pointing down the wrist is $L_3$ above the tip, in the shoulder plane: $w_r=0.2056$, $w_z=0.0309+0.10-0.05=0.0809$ m, at distance $D=\sqrt{0.2056^2+0.0809^2}=0.2209$ m.
8. *Elbow.* Law of cosines: $\cos q_3=(D^2-L_1^2-L_2^2)/(2L_1L_2)=(0.04882-0.01346-0.01823)/0.03132=0.5471$, so $q_3=\pm56.8^\circ$.
9. *Shoulder for each branch.* $q_2=\operatorname{atan2}(w_z,w_r)-\operatorname{atan2}(L_2\sin q_3,\,L_1+L_2\cos q_3)$ with $\operatorname{atan2}(0.0809,0.2056)=21.5^\circ$ and $\operatorname{atan2}(\pm0.1130,\,0.1899)=\pm30.8^\circ$. Branch $q_3=+56.8^\circ$: $q_2=21.5-30.8=-9.3^\circ$. Branch $q_3=-56.8^\circ$: $q_2=21.5+30.8=52.2^\circ$.
10. *Wrist for each branch.* To keep the tool vertical, wrist $=-90^\circ-(q_2+q_3)$. Branch +: $-90-47.5=-137.5^\circ$, outside $\pm110^\circ$, rejected. Branch $-$: $-90-(-4.6)=-85.4^\circ$, inside, accepted. Chosen: pan $-9.0^\circ$, shoulder $52.2^\circ$, elbow $-56.8^\circ$, wrist $-85.4^\circ$.
11. *Quintic trajectory.* With $s(\tau)=10\tau^3-15\tau^4+6\tau^5$, the peak of $\dot s$ is $1.875$ (at $\tau=0.5$) and the peak of $\ddot s$ is $10/\sqrt3=5.7735$. For $\Delta q=0.8$ rad and $T=1.2$ s: $\dot q_\max=1.875\cdot0.8/1.2=1.25$ rad/s and $\ddot q_\max=5.7735\cdot0.8/1.2^2=5.7735\cdot0.8/1.44=3.21$ rad/s$^2$.
12. *Pick gate.* $43/50=86\ \%$ has Wilson 95 % lower bound 73.8 %, at least 68 %, and the point estimate is at least 80 %: pass. For $40/50=80\ \%$ the lower bound is 67.0 %, below 68 %: fail by one percentage point. The failure taxonomy must sum to the failures: pick failures $50-43=7$ (slip 4, knocked 3) plus placement failures $43-40=3$ (place_miss 3) $=10=50-40$.

| Check (test) | Threshold | Illustrative result |
|---|---|---|
| IK, 200 reachable targets | >= 98 %, error < 2 mm | 199/200, worst 0.9 mm, max joint step 0.07 rad |
| Hand-eye RMS (held-out) | < 5 mm | 2.7 mm over 24 points |
| Segmentation mIoU (300 frames) | >= 0.85 | CNN 0.912, HSV baseline 0.874 |
| Centroid error, 0.3-0.6 m | median < 1.5 cm | 0.83 cm |
| Velocity / accel / torque | <= limits, >= 99 % | 82 % / 91 % of limits, 99.6 % |
| Pick success, 50 trials | >= 80 %, lower bound >= 68 % | 43/50 = 86 %, bound 73.8 % |
| Place-in-bin | >= 75 % | 40/50 = 80 % |
| Mean cycle time | < 25 s | 19.7 s |
| Failure taxonomy | sum = failures (10) | slip 4, knocked 3, place_miss 3 |

**Check.** Forward kinematics of the accepted solution: $r=L_1\cos q_2+L_2\cos(q_2+q_3)=0.2056$ m and $z=Z_S+L_1\sin q_2+L_2\sin(q_2+q_3)-L_3=0.0309$ m, matching the target (to $10^{-9}$ m in the script with unrounded angles). The rejected branch is not a numerical accident: its wrist needs $-137.5^\circ$, $27.5^\circ$ beyond the limit. The quintic peaks agree with a numerical derivative of $s(\tau)$. One pixel at 0.42 m is $0.42/415.7=1.01$ mm, so the sub-pixel pixel-to-base error is far below the 5 mm hand-eye limit.

**Takeaway.** A pick is a chain of frames and two closed-form solves (deprojection, planar IK); the second IK branch exists but must be tested against the joint limits, and a gate on the lower confidence bound turns 80 % of 50 into a fail.

## Exercises

1. **(Easy)** A 640 x 480 camera has a vertical field of view of 60 degrees. Compute $f_y$ and the size of one pixel at a depth of 0.42 m.
2. **(Easy)** With $f_x=f_y=415.7$, $c=(320,240)$, deproject pixel $(400,200)$ at depth 0.5 m into the optical frame.
3. **(Easy)** *Statistics.* A pick benchmark has 43 successes in 50 trials and another run has 40 of 50. Compute both Wilson intervals and say which passes "at least 80 % and lower bound at least 68 %".
4. **(Medium)** A joint must move 0.6 rad with limits $v_\max=1.5$ rad/s and $a_\max=4$ rad/s$^2$. Compute the shortest quintic duration and say which limit is binding.
5. **(Medium)** *Why damping.* A task Jacobian has singular values 1 and 0.01 and the error is 0.1 m along each singular direction. Compare the pseudo-inverse step with a damped step at $\lambda=0.1$.
6. **(Medium)** *Segmentation.* Class counts on the test set: background TP 9400, FP 250, FN 150; red TP 320, FP 40, FN 60; blue TP 280, FP 20, FN 40. Compute the three IoUs and the mIoU, and say whether it passes 0.85.
7. **(Medium)** *Torque.* Masses and lever arms about the shoulder: link 0.15 kg at 0.07 m, forearm 0.12 kg at 0.19 m, gripper plus block 0.08 kg at 0.28 m, effective inertia 0.012 kg m$^2$, peak acceleration 3.2 rad/s$^2$. Estimate the shoulder torque and compare it with an actuator limit of 1.0 N m (illustrative).
8. **(Medium)** *Debug.* Picks fail only when the block is far to the left of the table, and the gripper always closes about 3 cm to the right of the block. List three likely causes in the order you would test them.
9. **(Hard)** *Design.* The block's yaw is 100 degrees in the map, the arm pan is $-9^\circ$ and the gripper is symmetric under a 180 degree turn. Choose the wrist roll in $[-90^\circ,90^\circ)$ for a gripper that closes across the block's short side, and say why you reduce modulo 180.
10. **(Hard, mini-project)** Build the 50-trial benchmark with random block pose and yaw (seeds 1000 to 1049), log a `reason` for every failure and write `docs/failure_taxonomy.md` with a fix for the largest category. State assumptions, a baseline (block at the table centre, yaw 0), a boundary case (block at the edge of the workspace) and which observation would make you reject your pipeline.

## Reference implementation

A skeleton of the central module, `manipulation/ik.py`. It is not runnable here (it needs NumPy and your CAP01 `ArmModel`) but is syntactically valid and consistent with the interfaces of `interfaces.py`.

```python
"""src/corebot/manipulation/ik.py -- damped least-squares IK for the 5-DOF SO-101 arm (skeleton).

Task space: tool-tip position (3) + approach pitch (1) = 4 constraints. The 5th joint
(wrist_roll) is set afterwards from the object yaw, so it never enters the Jacobian.
Frames: targets are expressed in `arm_base`; angles in rad; lengths in m.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from corebot.manipulation.kinematics import ArmModel   # wraps your CAP01 fk (see Setup)


@dataclass(frozen=True)
class IKResult:
    q: np.ndarray            # (5,) joint angles, always inside the limits
    success: bool            # position error < tol and pitch error < pitch_tol
    pos_err: float           # metres
    pitch_err: float         # rad
    iterations: int


def task_error(arm: ArmModel, q: np.ndarray, target_xyz: np.ndarray, target_pitch: float) -> np.ndarray:
    """(4,) = [target_xyz - tip_xyz, wrap(target_pitch - tip_pitch)]."""
    raise NotImplementedError


def task_jacobian(arm: ArmModel, q: np.ndarray) -> np.ndarray:
    """(4, 5) = [linear tip Jacobian rows; pitch row]. Check it against finite differences."""
    raise NotImplementedError


def solve_ik(arm: ArmModel, target_xyz: np.ndarray, target_pitch: float, q0: np.ndarray,
             damping: float = 0.05, tol: float = 1e-3, pitch_tol: float = 0.02,
             max_iter: int = 100, max_step: float = 0.2) -> IKResult:
    """dq = J^T (J J^T + damping^2 I)^-1 e, step clipped to max_step per joint, q clipped to the
    limits after every step. Start from q0 (the current joints) so the solution stays on one
    branch. Never raise on 'unreachable': return success=False with the best q found."""
    raise NotImplementedError


def wrist_roll_for_yaw(object_yaw: float, pan: float) -> float:
    """Roll that aligns the jaws across the object's short side, reduced to the nearest
    equivalent of a symmetric (180-degree) gripper, inside the roll limits."""
    raise NotImplementedError
```

Check `task_jacobian` against finite differences of FK before you trust the solver: a sign error in one column makes the iteration wander without ever raising an error.

## Independent practice

### Goal
Deliver the CoreBot manipulation chain: deprojection and hand-eye calibration, a colour baseline and a small CNN for segmentation, a damped least-squares top-down grasp with quintic trajectories, and a 50-trial seeded pick-and-place benchmark with a failure taxonomy, all passing the acceptance suite and using only camera data (never simulator truth) at run time.

### Setup
- Repository: `~/corebot-capstone`, branch `cap05`. `models/corebot.xml` and the CAP01 forward kinematics must pass their own tests. CAP05 wraps the CAP01 `fk`/`fk_pose` in a class `ArmModel` that you add to `manipulation/kinematics.py`: `ArmModel.from_mjcf(path)`, `limits` (5 by 2, rad), `home` (5,) and `fk(q) -> (xyz, pitch)` in `arm_base`.
- New files: `perception/depth.py`, `perception/hand_eye.py`, `perception/segmentation.py` (+ `perception/make_dataset.py`), `manipulation/ik.py`, `grasp.py`, `trajectory.py`, `tests/acceptance/test_cap05.py`, `docs/failure_taxonomy.md`.
- Artefacts in `runs/cap05/`: `ik_path.json`, `hand_eye.npz`, `segmentation.json`, `localisation.npz`, `trajectory.json`, `picks.jsonl`, `failure_taxonomy.json`, `metrics.json`. Trained weights in `models/segnet.npz` (under 20 MB).
- Commands: `python -m corebot.perception.make_dataset --seeds 0:600` (renders RGB plus the MuJoCo `segmentation` buffer as labels), `python -m corebot.perception.segmentation --train`, `python bench/run_bench.py --milestone cap05 --seeds 1000:1050`, `pytest -q tests/acceptance/test_cap05.py`.
- Pinned versions: Python 3.11 or newer, `mujoco` 3.x, `numpy` 1.26 or newer, `pytest` 8; the CNN may use NumPy only or `torch` (CPU) if you pin it. Rendering: `MUJOCO_GL=egl`, with `osmesa` as the slow fallback (about 5 to 10 frames per second at 320 x 240). Dataset generation takes about 10 to 20 minutes, training 5 to 30 minutes on a laptop CPU, the benchmark about 15 minutes.
- Train on scene seeds 0 to 599, tune on 600 to 699, test on 700 to 999 (300 frames, one per seed) with different textures and lighting; never use seeds 1000 and above for anything but the benchmark.

### Tasks
1. `deproject` and `mask_to_xyz_cam` with depth conversion; unit-test against the hand-computed numbers of the worked example.
2. `fit_rigid_transform` (Kabsch) and a calibration script that collects 24 point pairs and saves `hand_eye.npz` plus `configs/hand_eye.yaml`; evaluate on held-out points.
3. `hsv_baseline`, `miou`, a dataset generator and a small `SegNet`; save `segmentation.json` with both mIoUs.
4. `task_error`, `task_jacobian` (finite-difference check), `solve_ik` and `wrist_roll_for_yaw`.
5. `plan_grasp` (pre-grasp, grasp, lift) and `quintic`, `min_duration`, plus an inverse-dynamics torque check with MuJoCo (`mj_inverse`).
6. `ScriptedGraspSkill.execute` with the failure reasons of the taxonomy and a verification step (gripper width and object height after lift).
7. Run the 50 seeded trials, write `picks.jsonl`, `failure_taxonomy.json` and `docs/failure_taxonomy.md` with one fix per category.

### Starter code
```python
"""Interface stubs for CAP05. Keep the signatures: tests/acceptance/test_cap05.py imports them."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from corebot.interfaces import Detection, GraspGoal, GraspResult, ImageFrame


# ---- src/corebot/perception/depth.py --------------------------------------------------------
def deproject(u: float, v: float, depth_m: float, K: np.ndarray) -> np.ndarray:
    """Pixel + metric depth (z along the optical axis) -> (3,) point in the OpenCV optical frame
    (x right, y down, z forward). MuJoCo renders depth as a normalised buffer: convert to metres
    first (document the formula you use) and reject depth <= 0 or non-finite."""
    raise NotImplementedError


def mask_to_xyz_cam(depth_m: np.ndarray, mask: np.ndarray, K: np.ndarray) -> np.ndarray | None:
    """Robust 3D centroid of a binary mask: drop invalid depths, use the median of the
    per-pixel points (not the mean: mask edges bleed into the background). None if < 30 pixels."""
    raise NotImplementedError


# ---- src/corebot/perception/hand_eye.py -----------------------------------------------------
def fit_rigid_transform(points_cam: np.ndarray, points_base: np.ndarray) -> np.ndarray:
    """4x4 T_base_cam minimising sum |R p_cam + t - p_base|^2 (Kabsch/SVD, det(R) = +1)."""
    raise NotImplementedError


def transform_points(T: np.ndarray, pts: np.ndarray) -> np.ndarray:
    raise NotImplementedError


# ---- src/corebot/perception/segmentation.py -------------------------------------------------
CLASSES = ("background", "red", "green", "blue", "bin", "table")


def hsv_baseline(rgb: np.ndarray) -> np.ndarray:
    """(H, W) uint8 class map from fixed colour thresholds. Record its mIoU too."""
    raise NotImplementedError


def miou(pred: np.ndarray, truth: np.ndarray, n_classes: int = len(CLASSES)) -> float:
    """Mean over classes present in `truth` of TP / (TP + FP + FN)."""
    raise NotImplementedError


class SegNet:
    """Small CNN (about 100-300 k parameters, < 20 MB on disk), 128x96 input, CPU friendly."""

    def predict(self, rgb: np.ndarray) -> np.ndarray:
        raise NotImplementedError


# ---- src/corebot/manipulation/grasp.py ------------------------------------------------------
@dataclass(frozen=True)
class GraspPlan:
    pregrasp_q: np.ndarray
    grasp_q: np.ndarray
    lift_q: np.ndarray
    gripper_open: float
    gripper_closed: float


def plan_grasp(det: Detection, T_arm_base: np.ndarray, arm, q_now: np.ndarray) -> GraspPlan | None:
    """Top-down grasp: pre-grasp 0.08 m above the object, grasp at its centre height, lift 0.10 m.
    Returns None when any of the three IK solves fails or violates a limit (reason -> taxonomy)."""
    raise NotImplementedError


# ---- src/corebot/manipulation/trajectory.py -------------------------------------------------
def quintic(q0: np.ndarray, q1: np.ndarray, duration: float, dt: float) -> np.ndarray:
    """(N, 5) samples with zero velocity and acceleration at both ends:
    q(s) = q0 + (q1 - q0) (10 s^3 - 15 s^4 + 6 s^5), s = t / duration."""
    raise NotImplementedError


def min_duration(dq: np.ndarray, v_max: np.ndarray, a_max: np.ndarray) -> float:
    """Smallest T for which the quintic keeps |v| <= v_max and |a| <= a_max on every joint
    (peak v = 1.875 |dq| / T, peak a = 5.7735 |dq| / T^2)."""
    raise NotImplementedError


# ---- the skill interface (CAP06 swaps the implementation behind it) --------------------------
class ScriptedGraspSkill:
    def execute(self, goal: GraspGoal, env) -> GraspResult:
        """Perceive -> plan -> move -> close -> lift -> verify (gripper width and object height).
        GraspResult.reason is one of: 'ok', 'no_detection', 'ik_fail', 'joint_limit', 'slip',
        'knocked', 'place_miss', 'timeout' (the failure taxonomy keys)."""
        raise NotImplementedError
```

### Tests
```python
# tests/acceptance/test_cap05.py
# Thresholds are provisional starting values; tighten them once your own reference run exists.
import json
import pathlib
from collections import Counter

import numpy as np

from corebot.evalkit import load_episodes, wilson_interval
from corebot.manipulation.ik import solve_ik
from corebot.manipulation.kinematics import ArmModel
from corebot.manipulation.trajectory import quintic
from corebot.perception.hand_eye import fit_rigid_transform, transform_points

RUNS = pathlib.Path("runs/cap05")
ARM = ArmModel.from_mjcf("models/corebot.xml")
TAXONOMY = {"no_detection", "ik_fail", "joint_limit", "slip", "knocked", "place_miss", "timeout"}


def _reachable_targets(n, seed):
    """Sample q inside the limits, take the FK tip: reachable by construction, pitch free."""
    rng = np.random.default_rng(seed)
    lo, hi = ARM.limits[:, 0], ARM.limits[:, 1]
    return [ARM.fk(rng.uniform(lo, hi)) for _ in range(n)]


# GATE: inverse kinematics --------------------------------------------------------------------------
def test_ik_200_reachable_targets():
    ok = 0
    for k, (xyz, pitch) in enumerate(_reachable_targets(200, seed=1000)):
        q0 = np.clip(ARM.home + 0.1 * np.random.default_rng(2000 + k).standard_normal(5),
                     ARM.limits[:, 0], ARM.limits[:, 1])
        r = solve_ik(ARM, xyz, pitch, q0)
        assert np.all(r.q >= ARM.limits[:, 0] - 1e-9) and np.all(r.q <= ARM.limits[:, 1] + 1e-9)
        ok += bool(r.success and r.pos_err < 2e-3)
    assert ok / 200 >= 0.98                 # reachable by construction, so only the solver can fail


def test_ik_path_has_no_branch_flip():
    q = json.load(open(RUNS / "ik_path.json"))["q"]       # waypoints along a straight tip line
    step = np.abs(np.diff(np.array(q), axis=0)).max()
    assert step < 0.2                       # rad: a larger jump between neighbours is a branch flip


def test_hand_eye_rms():
    d = np.load(RUNS / "hand_eye.npz")                      # held-out points not used for the fit
    T = fit_rigid_transform(d["fit_cam"], d["fit_base"])
    err = np.linalg.norm(transform_points(T, d["test_cam"]) - d["test_base"], axis=1)
    assert np.sqrt(np.mean(err ** 2)) < 0.005               # 5 mm: about five pixels of image error at 0.4 m


def test_segmentation_miou():
    m = json.load(open(RUNS / "segmentation.json"))
    assert m["n_eval_frames"] == 300 and m["eval_seeds_disjoint_from_train"] is True
    assert m["miou_cnn"] >= 0.85            # coloured blocks on a plain table: a solved problem
    assert "miou_hsv_baseline" in m         # the baseline must be recorded, whatever its value
    assert m["weights_mb"] < 20


def test_localisation_error():
    d = np.load(RUNS / "localisation.npz")                  # base-frame estimate vs truth, dist 0.3-0.6 m
    assert np.all((d["dist_m"] >= 0.3) & (d["dist_m"] <= 0.6))
    assert np.median(np.linalg.norm(d["est"] - d["truth"], axis=1)) < 0.015


def test_trajectory_limits_and_torque():
    t = json.load(open(RUNS / "trajectory.json"))
    assert t["max_vel_ratio"] <= 1.0 and t["max_acc_ratio"] <= 1.0   # fractions of the limits
    assert t["tracking_rms_m"] < 0.005
    assert t["torque_within_limit_fraction"] >= 0.99
    traj = quintic(np.zeros(5), np.full(5, 0.5), 1.0, 0.01)
    assert np.allclose(traj[0], 0) and np.allclose(traj[-1], 0.5)


# GATE: pick-and-place benchmark ------------------------------------------------------------------
def test_picks_benchmark():
    eps = load_episodes(RUNS / "picks.jsonl")
    n = len(eps)
    assert n == 50 and [e["seed"] for e in eps] == list(range(1000, 1050))
    picks = sum(e["pick_ok"] for e in eps)
    places = sum(e["place_ok"] for e in eps)
    lo, _ = wilson_interval(picks, n)
    assert picks / n >= 0.80 and lo >= 0.68
    assert places / n >= 0.75
    assert np.mean([e["cycle_s"] for e in eps]) < 25.0
    assert sum(e["joint_limit_violations"] for e in eps) == 0


def test_failure_taxonomy_adds_up():
    eps = load_episodes(RUNS / "picks.jsonl")
    failed = [e for e in eps if not (e["pick_ok"] and e["place_ok"])]
    tax = json.load(open(RUNS / "failure_taxonomy.json"))
    assert set(tax) <= TAXONOMY
    assert sum(tax.values()) == len(failed)
    assert Counter(e["reason"] for e in failed) == Counter(tax)
```

Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists. One-line rationale per threshold: IK at 98 % over 200 targets because the targets are reachable by construction and only your solver can fail; 2 mm because a block is 2 to 3 cm wide and the gripper tolerates about 5 mm; joint step 0.2 rad because a larger jump between neighbouring waypoints is a branch flip; hand-eye 5 mm because one pixel is about 1 mm at 0.42 m and the grasp tolerates a few millimetres; mIoU 0.85 because coloured blocks on a plain table is a solved problem, and below it the mask boundary starts to bias the centroid; centroid 1.5 cm because it must stay inside half the block width; limits at 100 % and torque at 99 % because a violated limit in simulation is a real hazard, while the last percent allows for numerical noise; pick 80 % with a 68 % lower bound because 50 trials cannot prove more than that; mean cycle 25 s so CAP08 can run 160 episodes in a few hours.

Gate checks: **test_ik_200_reachable_targets** and **test_picks_benchmark**.

### Expected output
```
$ pytest -q tests/acceptance/test_cap05.py
........                                                                 [100%]
8 passed in 96.4s

$ cat runs/cap05/metrics.json
{
  "milestone": "CAP05",
  "ik": {"targets": 200, "success": 199, "max_pos_err_m": 0.0009, "max_joint_step_rad": 0.07},
  "hand_eye": {"rms_m": 0.0027, "points": 24},
  "segmentation": {"miou_cnn": 0.912, "miou_hsv_baseline": 0.874, "weights_mb": 1.1, "n_eval_frames": 300},
  "localisation": {"median_err_m": 0.0083},
  "trajectory": {"max_vel_ratio": 0.82, "max_acc_ratio": 0.91, "tracking_rms_m": 0.0021,
                 "torque_within_limit_fraction": 0.996},
  "picks": {"episodes": 50, "pick_ok": 43, "pick_wilson_lo": 0.738, "place_ok": 40,
            "mean_cycle_s": 19.7, "joint_limit_violations": 0},
  "failures": {"slip": 4, "knocked": 3, "place_miss": 3}
}
```

When a test fails, the first thing to read is the measured number next to the threshold; for the benchmark also open `failure_taxonomy.json` before changing any code.

### Extension challenge
Reach beyond the table: grasp a cylinder lying on its side (side grasp, 5 DOF) and measure how the success rate changes with 50 more seeded trials; or add a clutter case with two touching blocks and a clearance check. Optional real-hardware tier: with a real SO-101 (open design, roughly 130 to 250 US dollars per arm depending on kit and region, check current prices) driven through LeRobot, copy your `ik.py`, command five table points and compare repeatability with a ruler on a grid. Keep the power supply fused and current-limited, keep fingers out of the workspace, and do not run unattended. No grade depends on it.

### Library track

Cross-check your own code with two libraries: **Pinocchio** (kinematics and Jacobian from your URDF; see the [project page](https://github.com/stack-of-tasks/pinocchio)) and **OpenCV** (HSV masks and connected components). The block below is runnable only after `pip install pin opencv-python-headless numpy` and once `models/corebot.urdf` exists.

```python
# Needs: pip install pin opencv-python-headless numpy   (Pinocchio is published on PyPI as "pin")
import cv2
import numpy as np
import pinocchio as pin

# 1. Cross-check your Jacobian and FK against Pinocchio on the URDF you wrote in CAP01.
model = pin.buildModelFromUrdf("models/corebot.urdf")
data = model.createData()
tool = model.getFrameId("tool0")


def pin_tip_and_jacobian(q: np.ndarray):
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    pin.computeJointJacobians(model, data, q)
    J = pin.getFrameJacobian(model, data, tool, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
    return data.oMf[tool].translation.copy(), J[:3, :]          # tip position, 3 x nv linear rows


# 2. A classical colour baseline with OpenCV: HSV threshold plus connected components.
def red_blocks(rgb: np.ndarray, min_pixels: int = 30):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    low = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))          # red wraps around hue 0
    high = cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    mask = cv2.bitwise_or(low, high)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    return [(centroids[i], stats[i, cv2.CC_STAT_AREA]) for i in range(1, n)
            if stats[i, cv2.CC_STAT_AREA] >= min_pixels]


if __name__ == "__main__":
    q = np.zeros(model.nq)
    tip, J = pin_tip_and_jacobian(q)
    print("tip at q = 0:", np.round(tip, 4), "Jacobian shape", J.shape)
    # Compare with your own solver: the tip positions must agree to < 1 mm for 20 random q.
```

Compare tip positions and Jacobian rows with your own FK for 20 random configurations (they should agree to under 1 mm), and compare your HSV baseline mIoU with the OpenCV one. For the real-arm path see the LeRobot [SO-101 guide](https://huggingface.co/docs/lerobot/so101).

## Verification

Check the pipeline by hand before trusting a benchmark. The standard-library script below reproduces the worked example from pixel to joint angles and the quintic peaks; run it and compare your own functions with its output.

```python
import math

# 1. pixel + depth -> camera frame (OpenCV optical convention: x right, y down, z forward)
H, W, FOVY = 480, 640, math.radians(60)
fy = (H / 2) / math.tan(FOVY / 2)          # MuJoCo gives fovy; fx = fy for square pixels
fx, cx, cy = fy, W / 2, H / 2
u, v, depth = 352, 236, 0.42
p_cam = ((u - cx) / fx * depth, (v - cy) / fy * depth, depth)

# 2. camera -> base_link with a hand-eye pose: camera at (0.10, 0, 0.35), pitched down 50 deg
th = math.radians(50)
x_ax, y_ax, z_ax = (0, -1, 0), (-math.sin(th), 0, -math.cos(th)), (math.cos(th), 0, -math.sin(th))
t = (0.10, 0.0, 0.35)
p_base = tuple(t[k] + p_cam[0] * x_ax[k] + p_cam[1] * y_ax[k] + p_cam[2] * z_ax[k] for k in range(3))

# 3. base_link -> arm_base (arm pillar 0.17 m ahead of base_link), then pan + planar IK
p_arm = (p_base[0] - 0.17, p_base[1], p_base[2])
pan = math.atan2(p_arm[1], p_arm[0])
r = math.hypot(p_arm[0], p_arm[1])
L1, L2, L3, ZS = 0.116, 0.135, 0.10, 0.05  # illustrative links; read yours from the MJCF


def planar_ik(r, z, sign):
    """Tip at (r, z) pointing straight down; sign = +1 / -1 picks the elbow branch."""
    wr, wz = r, z + L3 - ZS
    c = (wr * wr + wz * wz - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(c) > 1:
        raise ValueError("unreachable")
    q3 = sign * math.acos(c)
    q2 = math.atan2(wz, wr) - math.atan2(L2 * math.sin(q3), L1 + L2 * math.cos(q3))
    return q2, q3


def planar_fk(q2, q3):
    return (L1 * math.cos(q2) + L2 * math.cos(q2 + q3),
            ZS + L1 * math.sin(q2) + L2 * math.sin(q2 + q3) - L3)


LIMIT = math.radians(110)                   # illustrative |wrist_flex| limit; use your MJCF value
for sign in (+1, -1):
    q2, q3 = planar_ik(r, p_arm[2], sign)
    wrist = -math.pi / 2 - (q2 + q3)        # keeps the tool pointing straight down
    ok = abs(wrist) <= LIMIT
    print("branch %+d: shoulder %6.1f elbow %6.1f wrist %7.1f deg  %s" %
          (sign, *(math.degrees(a) for a in (q2, q3, wrist)), "ok" if ok else "wrist limit"))
    if ok:
        best = (q2, q3, wrist)
q2, q3, wrist = best
fk_r, fk_z = planar_fk(q2, q3)

print("p_cam  = (%.4f, %.4f, %.4f) m" % p_cam)
print("p_base = (%.4f, %.4f, %.4f) m" % p_base)
print("p_arm  = (%.4f, %.4f, %.4f) m, r = %.4f m" % (*p_arm, r))
print("chosen: pan %.1f, shoulder %.1f, elbow %.1f, wrist %.1f deg" %
      tuple(math.degrees(a) for a in (pan, q2, q3, wrist)))
print("FK check: r %.5f z %.5f" % (fk_r, fk_z))
assert abs(fk_r - r) < 1e-9 and abs(fk_z - p_arm[2]) < 1e-9

# 4. quintic time scaling: peak speed and acceleration for a move dq in time T
dq, T = 0.8, 1.2
print("quintic peak v %.3f rad/s, peak a %.3f rad/s^2" % (1.875 * dq / T, 5.7735 * dq / T ** 2))
print("one pixel at 0.42 m is %.2f mm" % (depth / fy * 1000))
```

Expected: $p_\text{cam}=(0.0323,-0.0040,0.4200)$, $p_\text{base}=(0.3731,-0.0323,0.0309)$, pan $-9.0^\circ$, branch $+1$ rejected for the wrist limit, branch $-1$ accepted with shoulder $52.2^\circ$, elbow $-56.8^\circ$, wrist $-85.4^\circ$, peaks 1.250 rad/s and 3.208 rad/s$^2$, and one pixel $=1.01$ mm.

Then verify behaviour: draw the detected centroid back into the image to see whether it sits on the block; move the arm to the pre-grasp pose with the gripper open and look at a render; replay one failed trial in slow motion and label its reason; confirm that perception code never imports simulator truth (same AST check as CAP04, applied to `perception/`).

**Scoring.** CAP05 weight is 13 of 100 graduation points. 60 % of the milestone score is automated (weighted fraction of checks, gates: IK and picks), 40 % is a self-assessed rubric scored 0 to 4: justification of the grasp strategy, a clear frame diagram, quality of the failure analysis (do causes lead to fixes?) and CNN training hygiene (split by scene seed). Graduation needs every gate passing, every milestone at or above 60 and the weighted total at or above 70.

## Failure modes

- Depth buffer used as metres, or the sign of an axis wrong in deprojection: every object sits at a plausible but wrong place.
- Wrong intrinsics (using fovx for $f_y$, or ignoring the image aspect ratio): a position error that grows toward the image edges.
- Hand-eye fitted and tested on the same points: a great RMS and a bad robot.
- The arm occludes the camera or the block during approach: detection drops out mid-grasp; detect before moving and keep the pose.
- 5-DOF arm asked for arbitrary yaw and pitch: restrict to top-down plus roll, or the solver oscillates.
- Branch flip between waypoints: a violent joint jump; start every solve from the previous waypoint.
- Gripper friction or `solref` too soft or contact time step too large: the block slips or sinks in; tune friction and the time step, not the controller.
- The approach pushes the block: use the pre-grasp 8 cm above, open the gripper first.
- Training and test scenes sharing seeds: mIoU 0.99 in the log and 0.70 in the benchmark.
- Reporting 40/50 as "80 %, pass" without the interval.

## Alternatives and trade-offs

For perception, an **HSV baseline** is nearly free and often enough here; a **CNN** handles lighting and texture changes, and a pretrained **detector** (YOLO-style) or open-vocabulary model scales to more objects at the cost of compute and a dataset. Depth can come from an RGB-D sensor, a stereo pair or a learned monocular network; RGB-D is the most direct in simulation. For IK, **analytic** (closed form for the planar arm) is fast and exact but arm-specific; **damped least squares** is general; optimisation-based IK (with Pinocchio or MuJoCo-based solvers) handles collisions and priorities. For grasping, top-down parallel grasps are simple; **learned grasp pose** networks and end-to-end imitation (CAP06, ACT in LeRobot) handle clutter but need data and are harder to certify. See the MIT 6.4210 [pick-and-place chapter](https://manipulation.mit.edu/pick.html) for the same pipeline at larger scale.

## Transfer and retention

CAP05 prepares CAP06 (the learned skill replaces `ScriptedGraspSkill`, with the same interface and the same benchmark), CAP07 (the task layer passes object labels and receives `GraspResult.reason`) and CAP08 (`DETECTION`, `GRASP_SLIP` and `PLACE_MISS` appear in the failure taxonomy of the whole system). Recall prompts, to answer after a week without notes:

1. Write the deprojection equation and say which frame it lands in.
2. Why is the damped pseudo-inverse bounded near a singularity, and what does the damping cost?
3. Why does a 5-DOF arm need the pitch and not the full orientation, and what sets the wrist roll?
4. Give the peak velocity and acceleration of a quintic of length $\Delta q$ and duration $T$.
5. Why must segmentation train and test sets be split by scene seed?

## Exercise answers

1. $f_y=240/\tan30^\circ=415.7$ px; one pixel at 0.42 m is $0.42/415.7=1.01$ mm.
2. $X=(400-320)/415.7\cdot0.5=0.0962$ m, $Y=(200-240)/415.7\cdot0.5=-0.0481$ m, $Z=0.5$ m: the point is to the right and above the optical axis.
3. 43/50: [0.738, 0.930]: point 86 % and lower bound 73.8 %: passes. 40/50: [0.670, 0.888]: point 80 % passes but the lower bound 67.0 % is below 68 %: fails.
4. $T\ge1.875\cdot0.6/1.5=0.75$ s from velocity and $T\ge\sqrt{5.7735\cdot0.6/4}=0.931$ s from acceleration. The acceleration limit binds: 0.931 s.
5. Pseudo-inverse: the second direction gives $0.1/0.01=10$ rad, an absurd step. Damped: $0.01/(0.01^2+0.1^2)\cdot0.1=0.099$ rad, while the well-conditioned direction gives $1/(1+0.01)\cdot0.1=0.099$ rad. The cost is that the second direction is not corrected exactly in one step (it needs several iterations).
6. Background $9400/9800=0.959$; red $320/420=0.762$; blue $280/340=0.824$; mIoU $=0.848$, just below 0.85: fails. Red is the weak class; look at its false negatives (shadows, highlights).
7. $\tau_\text{static}=9.81\,(0.15\cdot0.07+0.12\cdot0.19+0.08\cdot0.28)=9.81\cdot0.0557=0.546$ N m; dynamic $0.012\cdot3.2=0.038$ N m; total $\approx0.585$ N m, about 58 % of the 1.0 N m limit. Extending the arm or carrying a heavier object quickly eats the margin.
8. A consistent offset that grows with lateral distance points to (1) the hand-eye rotation or the camera yaw (a small rotation error moves far objects more): re-fit with points spread over the whole table; (2) the principal point or $f_x$ (check the deprojection of the image edges); (3) the pan joint zero offset or the sign of the pan in FK. Test with held-out points at the left edge, then deproject a known point, then command the arm to a known base-frame point without the camera.
9. The jaws close across the short side if the roll compensates for the pan: $\text{roll}=\text{wrap}_{180}(100^\circ-(-9^\circ))=109^\circ-180^\circ=-71^\circ$, which lies in $[-90^\circ,90^\circ)$. A symmetric gripper looks the same after 180 degrees, so reducing modulo 180 gives the smallest rotation and keeps the joint away from its limit.
10. A good answer lists seeds, the counts per taxonomy category (summing to the number of failures), a fix tied to the largest category (for example slip to more friction or a slower close), baseline success above 95 % at the table centre, a boundary case that fails with the reason `ik_fail` or `joint_limit` rather than a crash, and an observation that would reject the pipeline (success dropping when textures change, which would point to segmentation overfitting).

## Further reading

- [MIT 6.4210 Robotic Manipulation: Basic pick and place](https://manipulation.mit.edu/pick.html) and [Kinematics and Jacobians](https://manipulation.mit.edu/robot.html): the same pipeline in a larger setting.
- [MuJoCo documentation: modeling](https://mujoco.readthedocs.io/en/stable/modeling.html) and [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie): cameras, segmentation buffers, the SO-101 model and its license files.
- [CS231n](https://cs231n.github.io/): training a small CNN and avoiding data leakage.
- [Pinhole camera model (Wikipedia)](https://en.wikipedia.org/wiki/Pinhole_camera_model) and [Inverse kinematics (Wikipedia)](https://en.wikipedia.org/wiki/Inverse_kinematics): reference formulas.
- [Pinocchio](https://github.com/stack-of-tasks/pinocchio) and the LeRobot [SO-101 guide](https://huggingface.co/docs/lerobot/so101): the library track and the optional hardware tier; [SO-ARM100/101 open design](https://github.com/TheRobotStudio/SO-ARM100).
- **More practice:** watch the MIT 6.4210 lecture "Basic pick and place (Part 1)" and Modern Robotics Chapter 6 on numerical inverse kinematics, then reproduce the grasp-frame diagram for your own arm.

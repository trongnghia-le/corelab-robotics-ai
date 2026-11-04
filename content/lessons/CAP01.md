---
{
  "id": "cap01-capstone",
  "module_id": "CAP01",
  "title": "Capstone foundations: spec, repository, robot model and seeded world",
  "summary": "Start the CoreBot Tidy capstone: write a measurable spec, create a reproducible repository, model a differential-drive base with an SO-101 arm in MuJoCo and URDF, and prove with acceptance tests that determinism, kinematics and rest stability hold.",
  "estimated_minutes": 1320,
  "project_minutes": 1320,
  "prerequisites": [
    "S02",
    "S04",
    "R04",
    "T04",
    "T05",
    "RS02"
  ],
  "source_refs": [
    {
      "title": "MuJoCo documentation: modeling",
      "url": "https://mujoco.readthedocs.io/en/stable/modeling.html"
    },
    {
      "title": "MuJoCo documentation: simulation loop",
      "url": "https://mujoco.readthedocs.io/en/stable/programming/simulation.html"
    },
    {
      "title": "MuJoCo Menagerie (SO-101 and other models)",
      "url": "https://github.com/google-deepmind/mujoco_menagerie"
    },
    {
      "title": "ROS 2 Jazzy: building a visual robot model with URDF",
      "url": "https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html"
    },
    {
      "title": "Robotic Manipulation (MIT 6.4210), Tedrake",
      "url": "https://manipulation.mit.edu/"
    },
    {
      "title": "TidyBot: Personalized Robot Assistance with Large Language Models",
      "url": "https://arxiv.org/abs/2305.05658"
    },
    {
      "title": "Binomial proportion confidence interval (Wikipedia)",
      "url": "https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval"
    }
  ],
  "objectives": [
    "Write a measurable, falsifiable spec in which every requirement has a metric, a threshold with a rationale and the test that checks it.",
    "Create a reproducible repository (pinned versions, make test, a seeded environment API) from the shared skeleton script.",
    "Model a differential-drive base, the SO-101 arm and sensors in MJCF, mirror them in URDF and check that names, limits and mass agree.",
    "Show that your own forward kinematics, MuJoCo and the URDF place the tool within 1 mm of each other.",
    "Judge a success rate with a Wilson lower bound and explain the graduation rubric and timeline of the capstone."
  ],
  "core_theory": [
    "MuJoCo",
    "Robot Description",
    "Forward Kinematics",
    "Software Testing",
    "Reproducible Environments",
    "Experimental Design"
  ],
  "labs": [
    "Create ~/corebot-capstone with make_skeleton.sh, write SPEC.md, build the MJCF and URDF models and the seeded Env, and make tests/acceptance/test_cap01.py pass with a metrics.json."
  ],
  "assessment_refs": [
    "CAP01-diagnostic-v1"
  ],
  "review_prompts": [
    "Take one requirement of your SPEC.md and show its metric, threshold, rationale and the exact test function that can falsify it.",
    "Explain why two runs with the same seed must produce the same qpos and how you would find the source of a mismatch."
  ],
  "extension_refs": [
    "https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101",
    "https://huggingface.co/docs/lerobot/so101"
  ]
}
---

## Why this matters

You have finished the course material; now you build one robot that uses it. **CoreBot Tidy** is a small mobile manipulator in a MuJoCo "lab room": you type "put the red block in the blue bin" and the robot parses the sentence, localises itself, drives to the table, finds the block with its camera, picks it with a 5-DOF arm, drives to the bin and places it, while a safety supervisor can stop everything. The idea follows reference projects such as Stanford's [TidyBot](https://arxiv.org/abs/2305.05658) and the pick-and-place pipeline of [MIT 6.4210](https://manipulation.mit.edu/).

Nine milestones (CAP01 to CAP09, about 240 hours, about 24 weeks at 10 hours a week) build it in layers. This first milestone is the foundation, and it is deliberately more about discipline than about robotics: a measurable spec, a reproducible repository, a model whose three descriptions agree, and tests that fail when something drifts. Projects like this rarely die because one algorithm is hard. They die because nobody can tell whether yesterday's change broke something, or whether "it works" means anything. CAP01 gives you the instruments to tell.

Tone of the capstone: think of a supportive senior engineer handing you a project brief. Every milestone says which earlier CoreLab topics it uses, so you can go back and reread. This one uses [S02 MuJoCo](/lessons/S02), [S04 Robot Description](/lessons/S04), [R04 Forward Kinematics](/lessons/R04), [T04 Software Testing](/lessons/T04), [T05 Reproducible Environments](/lessons/T05) and [RS02 Experimental Design](/lessons/RS02).

## Intuition

Think of the capstone as a stack of five layers that all talk through one small contract file. At the bottom is the simulated world (physics at 1 ms, seeded). Above it sits firmware-in-the-loop for the drive base (CAP02), then host estimation and perception (CAP03, CAP05), skills such as navigation, manipulation and learned policies (CAP04 to CAP06), and the task layer with language and safety (CAP07). CAP08 evaluates everything on seeded episodes; CAP09 turns the evidence into a report and a release.

![System architecture of CoreBot Tidy: five bands from the MuJoCo world at the bottom through firmware in the loop, host estimation and perception, and skills, to the task layer, with a safety supervisor on the right and an evaluation harness underneath](/lesson-figures/CAP-architecture.svg)

*The shared map for all nine milestones. CAP01 builds the bottom band and the test harness that every later band is checked with.*

What CAP01 adds is the part that is easy to skip: the **world model** (the robot described in MJCF and URDF, the scene generated from a seed) and the **spec** (what "working" means, in numbers). Two ideas carry the whole milestone.

1. *A claim without a test is a hope.* Every requirement in `SPEC.md` names a metric, a threshold, a one-line reason for the threshold and the test function that can falsify it.
2. *Three descriptions of one robot must agree.* Your own forward kinematics, the MuJoCo model and the URDF all say where the tool is. If they disagree by more than a millimetre, one of them is wrong, and every later milestone would inherit the mistake silently.

## Theory and derivation

This section is the "integration notes" of the milestone: the few formulas, interfaces and rules that matter here, each with a link back to the topic it comes from.

![CAP01 overview: SPEC.md feeds a seeded environment and the acceptance tests; your forward kinematics, the MJCF in MuJoCo and the URDF must agree within 1 mm; gate checks are determinism and forward kinematics](/lesson-figures/CAP01.svg)

### 1. A spec is a table of falsifiable claims (from RS02, T04)

[RS02](/lessons/RS02) taught that a claim is only useful if an observation can reject it. A requirement row therefore has six cells: id, requirement, metric, threshold, rationale, test. "The robot is accurate" has none of them filled. "Own forward kinematics places `tool0` within 1 mm of MuJoCo for 20 random joint configurations" has all of them. The rationale matters because thresholds are decisions: 1 mm is chosen because a later grasp tolerates about 5 mm, and a 5 mm error budget should not be eaten by the model.

For a success rate measured on $n$ independent episodes with $k$ successes, report the **Wilson interval** rather than $k/n$. With $\hat p=k/n$ and $z=1.96$ for 95 %:
$$\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.$$
Acceptance tests later in the capstone test the *lower* bound. The function `evalkit.wilson_interval(k, n)` implements it, with `wilson_interval(78, 100)` giving about (0.689, 0.850).

### 2. Reproducibility is a function of the seed (from T05, S02)

A seeded run must be a pure function of its seed: same seed, same scene, same `qpos` after the same actions ([T05](/lessons/T05)). The rule in this repository is that **all randomness comes from `np.random.default_rng(seed)`**; never `np.random.rand`, never `random.random`, never time or the order of a dictionary of sets. A scene hash (SHA-256 of the rounded object poses) lets a test notice a changed scene without comparing floats one by one. Floating-point results can differ across CPUs and BLAS builds, so determinism is tested at the tolerance $10^{-9}$ on one machine and recorded; across machines you compare with tolerances, not hashes. MuJoCo's loop is `mj_step` repeatedly on the same `MjData` ([simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)); `mj_resetData` plus your seeded placement is a full reset.

### 3. One robot, two files: MJCF and URDF (from S04, S02)

MJCF is MuJoCo's format and carries physics: inertias, contacts, actuators, cameras. URDF ([ROS 2 Jazzy tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html)) is what ROS 2, `robot_state_publisher` and many kinematics libraries read. You write both and check them against each other for **joint names, joint limits (tolerance $10^{-6}$ rad) and total mass (within 2 %)**. Two traps cost beginners days:

- MJCF angles are in **degrees by default** (`<compiler angle="degree"/>`), URDF angles are always radians. A limit `range="-110 110"` is 1.92 rad.
- Inertia derived from a mesh can be nonsense (for example a hollow shell treated as solid); give simple primitive geometry or explicit `<inertial>` values and document the source.

The frames are fixed for the whole capstone: `map` (room corner), `odom`, `base_link`, `camera_link`, `arm_base`, `tool0`.

### 4. Forward kinematics and what 1 mm means (from R04)

Your own FK is a product of homogeneous transforms from `arm_base` to `tool0`:
$$T_{\text{tool}}(q)=\prod_{i=1}^{n}\underbrace{T_i^{\text{fixed}}\,\mathrm{Rot}(\hat a_i,q_i)}_{\text{one joint}},\qquad p=T_{\text{tool}}[0\!:\!3,\,3].$$
Every fixed offset and axis is copied from your MJCF. A joint-angle or offset error $\Delta\theta$ moves the tool by about $L\,\Delta\theta$ with $L$ the distance from that joint to the tool. For $L=0.3$ m, 1 mm corresponds to $\Delta\theta=0.0033$ rad $=0.19^\circ$, so the 1 mm test catches a swapped axis sign or a degree-for-radian slip (which makes centimetres or more) but tolerates rounding.

### 5. The contract file `interfaces.py` (S06 style)

Modules never pass loose tuples. They exchange frozen dataclasses in SI units with a `stamp` in seconds:

| Dataclass | Meaning | ROS 2 mapping |
|---|---|---|
| `WheelCmd(stamp, v, w)` | commanded speed (m/s, rad/s) | `geometry_msgs/Twist` |
| `WheelState(stamp, left_counts, right_counts, status)` | uint16 encoder counts, wrap | firmware frame, then `/joint_states` |
| `OdomSample`, `ImuSample`, `ScanSample`, `ImageFrame` | sensors after the driver | `nav_msgs/Odometry`, `sensor_msgs/*` |
| `Pose2DCov(stamp, x, y, theta, P)` | estimate with covariance | pose with covariance |
| `GraspGoal`, `NavGoal`, `TaskGoal`, `SafetyState` | skill and task messages | actions and topics |

Frozen means a downstream module cannot modify what an upstream module published, so any state change is explicit. This is the same discipline as [S06](/lessons/S06) (units and freshness at the interface).

### 6. Time step, rest and contact (from S02)

With a physics step of 1 ms, 5 seconds of rest is 5000 steps. In MuJoCo a contact whose `dist` is negative is penetrating; the rest test records the largest $-\text{dist}$ and limits it to 2 mm. Wheel friction that is too high or too low, or a time step too large for stiff contacts, show up here as drift or jitter before they can corrupt navigation.

### Scoring, graduation and timeline

Each milestone scores 0 to 100: **60 % automated checks** (weighted fraction passed; two or three checks per milestone are **gates**) plus **40 % human rubric** (four or five criteria scored 0 to 4 with linked evidence: 0 missing, 2 works but unexplained, 4 justified, tested and critiqued). Weights add to 100:

| CAP01 | CAP02 | CAP03 | CAP04 | CAP05 | CAP06 | CAP07 | CAP08 | CAP09 |
|---|---|---|---|---|---|---|---|---|
| 8 | 12 | 12 | 11 | 13 | 12 | 10 | 14 | 8 |

You **graduate** when all of these hold: every gate of every milestone passes; every milestone scores at least 60; the weighted total is at least 70; CAP08 shows zero safety violations; the CAP09 reproduction smoke test passes on a clean checkout. Merit is a total of at least 80; Distinction is at least 90 plus one stretch goal. The optional hardware tier never replaces a failing gate. All thresholds in the capstone are first values and will be recalibrated against reference runs.

| Weeks | Milestone | Hours |
|---|---|---|
| 1-2 | CAP01 foundations | 22 |
| 3-5 | CAP02 firmware-in-the-loop drive base | 28 |
| 6-8 | CAP03 estimation and localisation | 26 |
| 9-11 | CAP04 mapping, planning, navigation | 26 |
| 12-14 | CAP05 manipulation (may overlap CAP04) | 30 |
| 15-18 | CAP06 learned skills | 32 |
| 19-21 | CAP07 task layer and safety | 26 |
| 22-24 | CAP08 integration and evaluation, CAP09 report | 34 + 16 |

## Worked example

This is a reference trace of what a passing CAP01 looks like. All numbers are illustrative values chosen to be consistent with the formulas, not the output of a real run; yours will differ in the last digits and you should check yours against the thresholds, not against these digits.

**1. A spec you can check.** Ten requirements, each tied to a test (SR8 to SR10 live in your unit tests):

```markdown
| id   | requirement                              | metric                          | threshold | rationale                                    | test |
|------|------------------------------------------|---------------------------------|-----------|----------------------------------------------|------|
| SR1  | A seeded run is reproducible             | max abs qpos difference         | < 1e-9    | same machine and binary: expect exactly 0    | tests/acceptance/test_cap01.py::test_determinism |
| SR2  | Own FK equals the simulator              | tool position error, 20 configs | < 1 mm    | grasp tolerance is about 5 mm                | tests/acceptance/test_cap01.py::test_fk_matches_mujoco |
| SR3  | URDF and MJCF describe one robot         | joint-limit diff, mass diff     | 1e-6, 2 % | float round-trip, inertia rounding           | tests/acceptance/test_cap01.py::test_urdf_mjcf_consistency |
| SR4  | The robot rests when told nothing        | drift in 5 s, penetration       | 2 mm, 0.5 deg, 2 mm | below one pixel of later camera noise | tests/acceptance/test_cap01.py::test_rest_stability |
| SR5  | The table is inside the arm workspace    | reachable fraction of 100 points| >= 95 %   | validates the scale decision of the model    | tests/acceptance/test_cap01.py::test_reachability |
| SR6  | Every requirement is traceable           | SR ids with an existing test    | >= 8      | a spec nobody can check is decoration        | tests/acceptance/test_cap01.py::test_spec_traceability |
| SR7  | The repo has fast tests and pinned deps  | unit tests, pins                | >= 15, yes| CAP02 onward needs a safety net              | tests/acceptance/test_cap01.py::test_repo_hygiene |
| SR8  | Scenes are a function of the seed        | equal scene hash for equal seed | equal     | later benchmarks compare seeds               | tests/unit/test_world.py::test_scene_is_seeded |
| SR9  | Messages are immutable                   | assignment raises               | raises    | no module may edit another module's data     | tests/unit/test_interfaces.py::test_frozen |
| SR10 | Units are SI and documented              | every field doc names its unit  | all       | CAP02 mixes counts, rad and m/s              | tests/unit/test_interfaces.py::test_units_documented |
```

**2. Forward kinematics by hand.** An illustrative arm: pillar top 0.05 m above the base plane, link lengths 0.12, 0.14 and 0.10 m (stretched out, 0.36 m of horizontal reach, which is why the table must be low and close). Angles are in radians with the shoulder lift measured from vertical.

```python
import math

# Illustrative arm (not SO-101 data): pillar top 0.05 m above the base plane, link lengths in metres.
L1, L2, L3, Z0 = 0.12, 0.14, 0.10, 0.05

def fk(pan, lift, elbow, wrist):
    """Tool position (x, y, z) in arm_base. Angles in radians, lift measured from vertical."""
    a1, a2, a3 = lift, lift + elbow, lift + elbow + wrist
    r = L1 * math.sin(a1) + L2 * math.sin(a2) + L3 * math.sin(a3)   # horizontal reach
    z = Z0 + L1 * math.cos(a1) + L2 * math.cos(a2) + L3 * math.cos(a3)
    return r * math.cos(pan), r * math.sin(pan), z

p = fk(0.4, 0.6, 0.9, -1.5)
print("tool0 in arm_base: x=%.4f y=%.4f z=%.4f" % p)

# What a unit slip does: the same four numbers read as degrees instead of radians.
bad = fk(math.radians(0.4), math.radians(0.6), math.radians(0.9), math.radians(-1.5))
print("angles treated as degrees: error = %.1f mm" % (1000 * math.dist(p, bad)))

# Reach limit: fully stretched (all angles 0 means straight up, so use lift = 90 degrees).
print("max horizontal reach = %.2f m" % (L1 + L2 + L3))
```

Output:

```text
tool0 in arm_base: x=0.1910 y=0.0808 z=0.2589
angles treated as degrees: error = 252.9 mm
max horizontal reach = 0.36 m
```

If the simulator then reads $(0.1911, 0.0807, 0.2590)$ for `tool0`, the error is $\sqrt{0.1^2+0.1^2+0.1^2}\ \text{mm}=0.17$ mm: a pass against the 1 mm threshold. Treating the same four numbers as degrees misplaces the tool by about 253 mm, which is exactly the failure the test is built to catch.

**3. Determinism.** Two runs of `reset(seed=7)` plus 500 scripted steps (0.5 s of simulated time at 1 ms) give the same scene hash and a maximum $|q_1-q_2|$ of 0.0 (threshold $10^{-9}$).

**4. Reachability.** Sample table points uniformly and ask whether the tool can be placed there. With the illustrative annulus model (horizontal distance between 0.12 and 0.33 m from the arm base), a table spanning 0.18 to 0.32 m ahead and 0.24 m wide passes; pushing the same table 0.07 m further away fails badly:

```python
import math
import random

# Illustrative annulus model of a top-down reach: the tool can be placed where the horizontal
# distance r from the arm base is between R_MIN and R_MAX (numbers are illustrative, not SO-101 data).
R_MIN, R_MAX = 0.12, 0.33
rng = random.Random(1)

def fraction(x_lo, x_hi, y_half, n=100_000):
    ok = 0
    for _ in range(n):
        x, y = rng.uniform(x_lo, x_hi), rng.uniform(-y_half, y_half)
        ok += R_MIN <= math.hypot(x, y) <= R_MAX
    return ok / n

print("table 0.18..0.32 m ahead, +-0.12 m wide:", round(fraction(0.18, 0.32, 0.12), 3))
print("table 0.25..0.45 m ahead, +-0.12 m wide:", round(fraction(0.25, 0.45, 0.12), 3))
```

```text
table 0.18..0.32 m ahead, +-0.12 m wide: 0.986
table 0.25..0.45 m ahead, +-0.12 m wide: 0.363
```

98.6 % is above the 95 % gate; 36.3 % says the model scale is wrong, not the code. This is the "sizing check" of the milestone: the SO-101 reaches only about 0.35 to 0.4 m, so you mount it on a short pillar and use a low table and bins.

**5. Traceability.** A requirement with no test name cannot be traced; the parser finds it:

```python
import re

SPEC = """| id | requirement | metric | threshold | rationale | test |
|----|-------------|--------|-----------|-----------|------|
| SR1 | Same seed gives same run | max abs qpos diff | < 1e-9 | same binary, same machine | tests/acceptance/test_cap01.py::test_determinism |
| SR2 | Own FK matches MuJoCo | tool position error | < 1 mm | grasp tolerance is ~5 mm | tests/acceptance/test_cap01.py::test_fk_matches_mujoco |
| SR3 | The robot is accurate | (vague) | (none) | | |
"""

def parse(text):
    """Return {id: [cited test names]} for every table row that starts with an SR id."""
    rows = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*(SR\d+)\s*\|", line)
        if m:
            rows[m.group(1)] = re.findall(r"::(test_\w+)", line)
    return rows

rows = parse(SPEC)
print(rows)
untraceable = sorted(k for k, v in rows.items() if not v)
print("untraceable:", untraceable)
assert untraceable == ["SR3"]
```

```text
{'SR1': ['test_determinism'], 'SR2': ['test_fk_matches_mujoco'], 'SR3': []}
untraceable: ['SR3']
```

**6. The metrics file** after a passing run (`runs/cap01/metrics.json`, illustrative):

```json
{
  "determinism_max_abs_diff": 0.0,
  "fk_max_error_m": 0.00012,
  "mass_rel_diff": 0.004,
  "reachable_fraction": 0.97,
  "rest_arm_drift_deg": 0.02,
  "rest_base_drift_m": 0.0003,
  "rest_max_penetration_m": 0.0005,
  "spec_requirements": 10,
  "unit_tests": 17
}
```

**7. A success rate, for later.** If a later test reports 27 successes in 30 episodes, the point estimate is 0.90 but the Wilson 95 % interval is (0.744, 0.965): a lower-bound requirement of 0.75 would just fail.

## Exercises

1. **(Easy)** An episode set has 27 successes in 30. Compute the Wilson 95 % interval with `evalkit.wilson_interval` and decide whether a test "lower bound at least 0.75" passes. *(Source: Wikipedia, Binomial proportion confidence interval.)*
2. **(Easy)** Rewrite "the robot should be accurate and not wobble when idle" as two SPEC.md rows, each with metric, threshold, one-line rationale and test name. *(Source: the SR format of this lesson; RS02.)*
3. **(Easy)** A joint is written `<joint name="elbow_flex" type="hinge" range="-110 110"/>` in an MJCF with no `<compiler>` tag. What is the range in radians? What would the URDF `lower` and `upper` have to be? What happens if you write `range="0 1.57"` expecting radians? *(Source: MuJoCo modeling documentation, compiler `angle` attribute.)*
4. **(Medium)** The physics step is 1 ms. How many steps are 5 s of rest? How many seconds are the 500 scripted steps of the determinism test? What changes if you set the step to 2 ms and keep 500 steps? *(Source: MuJoCo simulation loop.)*
5. **(Medium)** The wrist-to-tool distance is 0.1 m and the shoulder-to-tool distance is 0.36 m. Which joint-angle error (degrees) moves the tool by 1 mm for each? Why does that justify testing FK on random configurations rather than at the zero pose only? *(Source: R04 lesson formulas.)*
6. **(Medium)** `test_urdf_mjcf_consistency` reports total mass 3.18 kg in MJCF and 3.10 kg in the URDF. Compute the relative difference, say whether the test passes at 2 %, and name two likely causes. *(Source: S04 lesson, URDF `<inertial>`.)*
7. **(Medium)** In `test_reachability`, 91 of 100 table points are reachable. Compute the Wilson interval, say whether the 95 % point-estimate test passes, and give two design changes that increase the fraction without touching the test. Run the reachability snippet of the Worked example (step 4, save it as `reach_demo.py`) first to see how strongly table position matters. *(Source: this lesson, section 4 and the SO-101 reach quoted above.)*
8. **(Hard)** *Find the bug.* The scene code does `import random; random.shuffle(objs)` for placement and `np.random.rand()` for the bin position, and `reset(seed)` calls `np.random.seed(seed)`. Two identical runs give the same qpos, but the same seed on a colleague's machine gives a different scene. Explain every defect and write the fix using only `np.random.default_rng(seed)`. *(Source: T05; NumPy Generator guidance.)*
9. **(Hard)** *Design.* Design the rest-stability test so that it cannot pass by accident. Which quantities do you record, at which step, with what thresholds, and why is checking only the final state not enough? Include how MuJoCo reports penetration (`mjContact.dist`). *(Source: MuJoCo programming documentation, contacts.)*
10. **(Hard, mini-project)** Write the complete SPEC.md for your own robot: ten requirements, rationale for each threshold, and a test name for each. Then write a ten-line checker that rejects a spec with a missing metric, a missing threshold or an untraceable test, and show it rejecting one deliberately broken row. State what observation would make you change a threshold.

## Reference implementation

The module you write first is your own forward kinematics. Below is the skeleton: docstrings, type hints and `NotImplementedError`. Write the transforms from your MJCF; there is no hidden solution here because the numbers are yours.

```python
"""src/corebot/manipulation/kinematics.py: your own forward kinematics of the arm (CAP01).

Frames: positions are expressed in the `arm_base` frame, metres, radians, right-handed,
z up. `q` lists the arm joints in the order of ARM_JOINTS (gripper excluded).
"""
from typing import Sequence

import numpy as np

ARM_JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def rot_x(a: float) -> np.ndarray:
    """4x4 homogeneous rotation about x by `a` radians."""
    raise NotImplementedError


def rot_z(a: float) -> np.ndarray:
    """4x4 homogeneous rotation about z by `a` radians."""
    raise NotImplementedError


def trans(x: float, y: float, z: float) -> np.ndarray:
    """4x4 homogeneous translation."""
    raise NotImplementedError


def fk_pose(q: Sequence[float]) -> np.ndarray:
    """4x4 pose of site `tool0` in `arm_base` for joint angles q (product of transforms).

    Every offset and axis here must be copied from your MJCF `<body pos=... >` and
    `<joint axis=... >` values; write the source line numbers in comments.
    """
    raise NotImplementedError


def fk(q: Sequence[float]) -> np.ndarray:
    """Position (3,) of `tool0` in `arm_base`: the last column of fk_pose."""
    return fk_pose(q)[:3, 3]


def top_down_reachable(p_base: Sequence[float]) -> bool:
    """True if a top-down gripper pose exists at position p_base (m) inside joint limits.

    Start with a sampled search over q using fk(); replace it by closed-form IK in CAP05.
    """
    raise NotImplementedError
```

A hint for the body of `fk_pose`: loop over your joints, multiply `trans(offset)` then a rotation about the joint axis by `q[i]`, and finish with the fixed transform from the last link to the `tool0` site. Put the MJCF line you copied each offset from in a comment.

## Independent practice

### Goal
Deliver the foundation of CoreBot Tidy: a repository from the skeleton script, a measurable `SPEC.md`, an MJCF model and a URDF of the same robot, a seeded environment with the `reset(seed)` and `step` API, your own forward kinematics, at least 15 fast unit tests, and an acceptance suite that passes and writes `runs/cap01/metrics.json`. Budget: about 22 hours (this lesson is the brief).

### Setup
Work in a **separate repository**, `~/corebot-capstone`, never inside `corelab/`. Needs Python 3.10 or newer, `git`, and later `gcc` and `cmake` (CAP02). Runtime hints: `MUJOCO_GL=egl` for rendering on a GPU machine, `osmesa` as a slow fallback (CAP05 needs it, CAP01 does not). Pin the exact versions you test with (the commands print them with `pip freeze`; MuJoCo and its tooling change quickly, so a written pin is part of the grade).

Download `evalkit.py` (the shared helpers: Wilson interval, step metrics, CRC-8, NEES consistency, McNemar, bootstrap) and `make_skeleton.sh` from the CoreLab app at `/practice/capstone/evalkit.py` and `/practice/capstone/make_skeleton.sh`, then:

```bash
mkdir -p ~/corelab-downloads && cd ~/corelab-downloads
# replace HOST:PORT with the address of your running CoreLab app
curl -O http://HOST:PORT/practice/capstone/evalkit.py
curl -O http://HOST:PORT/practice/capstone/make_skeleton.sh
python3 evalkit.py                                   # prints: evalkit self-test OK
sh make_skeleton.sh ~/corebot-capstone ./evalkit.py  # safe to run twice; never overwrites
cd ~/corebot-capstone && git init
python3 -m venv .venv && . .venv/bin/activate
pip install mujoco numpy pytest yourdfpy
pip freeze | grep -i -E "^(mujoco|numpy|pytest|yourdfpy)=="   # paste these lines into pyproject.toml
make doctor && make test
```

The script creates the layout of the plan (`configs/`, `models/`, `firmware/`, `src/corebot/...`, `tests/unit`, `tests/acceptance`, `bench/`, `runs/`, `report/`, `docs/`) with stubs, and it skips any file that already exists. For the SO-101 arm, copy `robotstudio_so101` from [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) into `models/meshes/` **together with its license file**; keep a note of the commit you copied.

### Tasks
1. Write `SPEC.md` with requirement ids SR1 to SR10 (columns id, requirement, metric, threshold, rationale, test). The example in the Worked example is a template, not an answer sheet: add requirements that reflect your own design (for example the table height you chose).
2. Write `models/corebot.xml`: differential-drive base (two driven wheels plus a caster or skids), a short pillar, the SO-101 arm with gripper, a low table, three coloured objects, two bins, and sensors (wheel encoders, IMU, lidar rays, RGB-D camera, joint encoders). Sites `tool0`, bodies `base_link` and `arm_base`. Document every unit and the compiler `angle` choice in comments.
3. Write `models/corebot.urdf` with the same joint names and limits for base and arm.
4. Implement `corebot/sim/world.py` and `corebot/sim/env.py`: `Env.reset(seed)`, `Env.step(ctrl)`, `Env.scene_hash()`; only `np.random.default_rng(seed)` as randomness.
5. Implement `manipulation/kinematics.py` (`fk`, `top_down_reachable`).
6. Implement `interfaces.py` (frozen dataclasses with documented units) and write at least 15 unit tests in `tests/unit`, including the three cited by SR8 to SR10.
7. Make the Makefile target `make test` run the unit tests; add the acceptance file below; make `pytest -q tests/acceptance` pass; commit `runs/cap01/metrics.json`.
8. Record a 5 s "robot rests" video or GIF and write one page of lessons learned in `docs/` (it feeds the CAP09 report).

### Starter code
Interface stubs for the world and the environment (the kinematics skeleton is in the Reference implementation):

```python
# --- src/corebot/sim/world.py ---
import numpy as np


def sample_table_points(seed: int, n: int) -> np.ndarray:
    """(n, 3) points on the table top, in the arm_base frame, drawn with np.random.default_rng(seed)."""
    raise NotImplementedError


def make_scene(seed: int) -> dict:
    """Seeded scene description: object poses, bin poses, obstacle poses (plain dict of lists)."""
    raise NotImplementedError


# --- src/corebot/sim/env.py ---
class Env:
    """Seeded MuJoCo environment. Public attributes used by the acceptance tests: model, data."""

    def __init__(self, model_path: str):
        """Load the MJCF with mujoco.MjModel.from_xml_path; do not create randomness here."""
        raise NotImplementedError

    def reset(self, seed: int) -> None:
        """mj_resetData, then place objects from make_scene(seed). Same seed, same state."""
        raise NotImplementedError

    def step(self, ctrl) -> None:
        """Write ctrl into data.ctrl (clipped to ctrlrange) and call mujoco.mj_step once."""
        raise NotImplementedError

    def scene_hash(self) -> str:
        """sha256 hex of the scene description (object poses rounded to 1e-9)."""
        raise NotImplementedError
```

### Tests
Save as `tests/acceptance/test_cap01.py`. Gate checks are `test_determinism` and `test_fk_matches_mujoco`. The URDF forward-kinematics test is optional (it skips without `yourdfpy`). The file needs numpy and mujoco, so it cannot run in CoreLab itself, but its spec-traceability and hygiene parts only read your repository.

```python
"""tests/acceptance/test_cap01.py: CAP01 acceptance suite (thresholds are provisional)."""
import ast
import json
import pathlib
import re
import xml.etree.ElementTree as ET

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
XML = ROOT / "models" / "corebot.xml"
URDF = ROOT / "models" / "corebot.urdf"
METRICS = ROOT / "runs" / "cap01" / "metrics.json"


def record(name, value):
    """Merge one number into runs/cap01/metrics.json (the report reads it later)."""
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(METRICS.read_text()) if METRICS.exists() else {}
    data[name] = value
    METRICS.write_text(json.dumps(data, indent=2, sort_keys=True))


def scripted(model, k):
    return 0.3 * np.sin(0.02 * k + np.arange(model.nu))


def run_scripted(seed, steps=500):
    from corebot.sim.env import Env
    env = Env(str(XML))
    env.reset(seed)
    for k in range(steps):
        env.step(scripted(env.model, k))
    return env.data.qpos.copy(), env.scene_hash()


def test_determinism():  # GATE: SR1
    q1, h1 = run_scripted(7)
    q2, h2 = run_scripted(7)
    diff = float(np.max(np.abs(q1 - q2)))
    record("determinism_max_abs_diff", diff)
    assert diff < 1e-9 and h1 == h2   # 1e-9: same machine, same binary, so expect exactly 0


def _tool_in_base(mujoco, model, data):
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "arm_base")
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tool0")
    R = data.xmat[bid].reshape(3, 3)
    return R.T @ (data.site_xpos[sid] - data.xpos[bid])


def test_fk_matches_mujoco():  # GATE: SR2
    import mujoco
    from corebot.manipulation.kinematics import ARM_JOINTS, fk
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    rng = np.random.default_rng(2024)
    adr = [model.joint(n).qposadr[0] for n in ARM_JOINTS]
    lo = np.array([model.joint(n).range[0] for n in ARM_JOINTS])
    hi = np.array([model.joint(n).range[1] for n in ARM_JOINTS])
    worst = 0.0
    for _ in range(20):
        q = rng.uniform(lo, hi)
        data.qpos[adr] = q
        mujoco.mj_forward(model, data)
        worst = max(worst, float(np.linalg.norm(fk(q) - _tool_in_base(mujoco, model, data))))
    record("fk_max_error_m", worst)
    assert worst < 1e-3   # 1 mm: a unit or axis mistake gives centimetres, rounding gives micrometres


def test_urdf_fk_matches_mjcf():  # optional library check
    yourdfpy = pytest.importorskip("yourdfpy")
    import mujoco
    from corebot.manipulation.kinematics import ARM_JOINTS
    robot = yourdfpy.URDF.load(str(URDF))
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    rng = np.random.default_rng(5)
    worst = 0.0
    for _ in range(20):
        q = rng.uniform(-0.5, 0.5, len(ARM_JOINTS))
        robot.update_cfg(dict(zip(ARM_JOINTS, q)))
        T = robot.get_transform("tool0", "arm_base")
        data.qpos[[model.joint(n).qposadr[0] for n in ARM_JOINTS]] = q
        mujoco.mj_forward(model, data)
        worst = max(worst, float(np.linalg.norm(T[:3, 3] - _tool_in_base(mujoco, model, data))))
    assert worst < 1e-3


def test_urdf_mjcf_consistency():  # SR3
    import mujoco
    model = mujoco.MjModel.from_xml_path(str(XML))
    root = ET.parse(URDF).getroot()
    urdf_limits = {}
    for j in root.iter("joint"):
        lim = j.find("limit")
        if j.get("type") in ("revolute", "prismatic") and lim is not None:
            urdf_limits[j.get("name")] = (float(lim.get("lower")), float(lim.get("upper")))
    for name, (lo, hi) in urdf_limits.items():
        rng = model.joint(name).range     # raises if the joint name is missing in the MJCF
        assert abs(rng[0] - lo) < 1e-6 and abs(rng[1] - hi) < 1e-6, name
    urdf_mass = sum(float(m.get("value")) for m in root.iter("mass"))
    mj_mass = float(model.body_mass.sum())
    record("mass_rel_diff", abs(urdf_mass - mj_mass) / mj_mass)
    assert abs(urdf_mass - mj_mass) / mj_mass < 0.02


def test_rest_stability():  # SR4
    import mujoco
    from corebot.sim.env import Env
    env = Env(str(XML))
    env.reset(0)
    m, d = env.model, env.data
    base = m.body("base_link").id
    p0, q0 = d.xpos[base].copy(), d.qpos.copy()
    worst_pen = 0.0
    for _ in range(int(5.0 / m.opt.timestep)):
        env.step(np.zeros(m.nu))
        assert np.all(np.isfinite(d.qpos))
        for c in d.contact[: d.ncon]:
            worst_pen = max(worst_pen, -c.dist)
    drift = float(np.linalg.norm(d.xpos[base][:2] - p0[:2]))
    arm = [m.joint(n).qposadr[0] for n in
           ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")]
    arm_drift = float(np.degrees(np.max(np.abs(d.qpos[arm] - q0[arm]))))
    record("rest_base_drift_m", drift)
    record("rest_arm_drift_deg", arm_drift)
    record("rest_max_penetration_m", worst_pen)
    assert drift < 2e-3 and arm_drift < 0.5 and worst_pen < 2e-3


def test_reachability():  # SR5
    from corebot.manipulation.kinematics import top_down_reachable
    from corebot.sim.world import sample_table_points
    pts = sample_table_points(123, 100)
    frac = sum(bool(top_down_reachable(p)) for p in pts) / len(pts)
    record("reachable_fraction", frac)
    assert frac >= 0.95


def _test_functions():
    names = set()
    for f in (ROOT / "tests").rglob("test_*.py"):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                names.add(node.name)
    return names


def test_spec_traceability():  # SR6
    text = (ROOT / "SPEC.md").read_text()
    existing = _test_functions()
    ids = set()
    for line in text.splitlines():
        m = re.match(r"\|\s*(SR\d+)\s*\|", line)
        if not m:
            continue
        cited = re.findall(r"::(test_\w+)", line)
        assert cited and all(c in existing for c in cited), f"{m.group(1)} cites a missing test"
        ids.add(m.group(1))
    record("spec_requirements", len(ids))
    assert len(ids) >= 8


def test_repo_hygiene():  # SR7
    n = sum(len([x for x in ast.walk(ast.parse(f.read_text()))
                 if isinstance(x, ast.FunctionDef) and x.name.startswith("test_")])
            for f in (ROOT / "tests" / "unit").glob("test_*.py"))
    record("unit_tests", n)
    assert n >= 15
    assert re.search(r"==\s*\d", (ROOT / "pyproject.toml").read_text()), "pin versions with =="
```

Thresholds are provisional starting values (see the plan rationale); tighten them once your own reference run exists. One-line rationales: determinism below $10^{-9}$ because the same binary on the same machine should give exactly 0; FK below 1 mm because a grasp tolerates about 5 mm; limits within $10^{-6}$ and mass within 2 % because only float round-trip and inertia rounding should differ; rest drift of 2 mm and 0.5 degrees because a drifting robot would corrupt odometry tests in CAP02; 95 % reachable because it confirms the scale decision; 8 traceable requirements and 15 unit tests because they prove the safety net exists.

### Expected output
A passing run prints something like the following (times will differ):

```text
........                                                                 [100%]
8 passed in 6.41s
```

Without `yourdfpy` installed you see `7 passed, 1 skipped`, which still counts as a pass:

```text
.s......                                                                 [100%]
7 passed, 1 skipped in 6.02s
```

and a `runs/cap01/metrics.json` such as this (illustrative values):

```json
{
  "determinism_max_abs_diff": 0.0,
  "fk_max_error_m": 0.00012,
  "mass_rel_diff": 0.004,
  "reachable_fraction": 0.97,
  "rest_arm_drift_deg": 0.02,
  "rest_base_drift_m": 0.0003,
  "rest_max_penetration_m": 0.0005,
  "spec_requirements": 10,
  "unit_tests": 17
}
```

### Extension challenge
Stretch: add a rendered check that the camera sees all three objects from the home pose, and a test that a randomly generated scene never places an object inside a bin or the pillar (1000 seeds). Optional hardware tier: none at this milestone, but write down in `docs/` where the real SO-101 would differ from your model (backlash, gripper compliance, servo latency); CAP02 and CAP06 use that note.

### Library track
Cross-check your kinematics with the URDF through a library instead of your own parser: `yourdfpy` (or `pinocchio`) computes the URDF side and MuJoCo the other, so a failing line points at a model file, not at your FK:

```python
# Needs: pip install mujoco numpy yourdfpy   (pinocchio is an alternative for the URDF side)
import numpy as np
import mujoco
import yourdfpy

from corebot.manipulation.kinematics import ARM_JOINTS, fk

model = mujoco.MjModel.from_xml_path("models/corebot.xml")
data = mujoco.MjData(model)
robot = yourdfpy.URDF.load("models/corebot.urdf")
rng = np.random.default_rng(11)
bid = model.body("arm_base").id
sid = model.site("tool0").id
adr = [model.joint(n).qposadr[0] for n in ARM_JOINTS]

rows = []
for i in range(20):
    q = rng.uniform(-0.6, 0.6, len(ARM_JOINTS))
    data.qpos[adr] = q
    mujoco.mj_forward(model, data)
    p_mj = data.xmat[bid].reshape(3, 3).T @ (data.site_xpos[sid] - data.xpos[bid])
    robot.update_cfg(dict(zip(ARM_JOINTS, q)))
    p_urdf = robot.get_transform("tool0", "arm_base")[:3, 3]
    rows.append((np.linalg.norm(fk(q) - p_mj), np.linalg.norm(p_urdf - p_mj)))

err = np.array(rows)
print("max |FK - MuJoCo| = %.2e m, max |URDF - MuJoCo| = %.2e m" % tuple(err.max(axis=0)))
assert (err < 1e-3).all()
```

Expected: one line `max |FK - MuJoCo| = ... m, max |URDF - MuJoCo| = ... m` with both numbers below $10^{-3}$. If the URDF number is large and your FK number small, the URDF is wrong (check axis signs and `rpy` order).

## Verification

Verify at three levels. By hand: the forward kinematics at the zero pose and one pose you can measure with a ruler on the model; the unit of every number in the MJCF. By test: the acceptance suite above; kill-test it by breaking something on purpose (negate one joint axis in the URDF, change one seed, delete a test name from SPEC.md) and confirm the right test fails. By reading: scan `git diff` of `models/` for any value without a unit comment.

This milestone is worth **8 of 100 points**. The automated part (60 %) is the weighted fraction of the seven checks passed with the two gates (determinism, forward kinematics) mandatory for graduation. The human part (40 %) is four criteria scored 0 to 4 with links to evidence: spec quality (measurable? falsifiable?), model realism and units documentation, test design, repository clarity. Optional review prompt for an LLM (give it the code and the artefacts, not your own verdict): "Here are SPEC.md, the models and the tests. For each requirement say whether the metric, threshold and test are consistent, and name the weakest one."

## Failure modes

- **Degrees versus radians**: the MJCF default is degrees; the URDF is radians; a hinge range of `0 1.57` becomes 1.57 degrees.
- **Mesh-derived inertia nonsense**: a visual mesh used for inertia gives negative or absurd values; use primitives or explicit inertials.
- **Wheel friction jitter or slip**: the base creeps at rest or oscillates; tune friction and damping and test at rest.
- **Time step too large for contact**: penetration grows and objects explode; reduce the step before changing anything else.
- **URDF axis sign mismatch**: your FK matches MuJoCo but not the URDF; the optional test catches it.
- **Copying Menagerie assets without the license file**: keep each license beside its assets.
- **Leaked randomness**: `np.random.rand`, `random`, a set iteration order or a clock makes a run irreproducible; use `default_rng(seed)` only.
- **A spec nobody can fail**: thresholds without rationale, tests that assert nothing, or requirements written after the code passed.

## Alternatives and trade-offs

MuJoCo is the single source of truth here; a Gazebo-based world would give richer ROS 2 tooling but a second physics to keep in agreement. You could skip URDF entirely and keep MJCF only, which removes a consistency problem but also the bridge to ROS 2 and Nav2. Closed-form FK versus a library (`pinocchio`, `yourdfpy`): writing your own once teaches the frames; keep the library as a cross-check. For the scenario, alternatives such as a stationary SO-101 tabletop task or an F1TENTH-style rover were considered; the chosen mobile manipulator is the one that exercises localisation, navigation, manipulation, firmware and a task layer together within the budget.

## Transfer and retention

This milestone prepares CAP02 (the firmware-in-the-loop drive base uses your Env and `WheelCmd`/`WheelState`), CAP03 (the EKF uses your frames and the `evalkit` consistency checks) and CAP05 (your FK becomes IK). Recall prompts: (1) write the six columns of a requirement row from memory and give one good example; (2) say why MJCF and URDF angles can silently disagree; (3) explain what the Wilson lower bound adds over a success percentage; (4) list the three ways randomness leaks into a seeded run. After a week, redo the 1 mm argument for a different link length.

## Exercise answers

1. `wilson_interval(27, 30)` is about (0.744, 0.965), point estimate 0.90. The lower bound 0.744 is below 0.75, so the test fails, narrowly: with 30 episodes you cannot yet claim 0.75. More episodes or a lower requirement is the honest fix; changing the seeds is not.
2. For example SR-a: "Idle base does not creep", metric: base position change in 5 s with zero command, threshold 2 mm, rationale: below the odometry resolution of CAP02, test `test_rest_stability`. SR-b: "Arm holds its pose", metric: maximum joint drift in 5 s, threshold 0.5 degrees, rationale: much smaller than a grasp tolerance at 0.3 m (0.5 degrees is 2.6 mm), test the same function. Both are falsifiable by the same logged data.
3. Without a `<compiler>` tag, angles are degrees: $110^\circ=1.920$ rad, so the range is $\pm1.920$ rad and the URDF `lower`/`upper` must be $\mp1.920$ (to 6 decimals). `range="0 1.57"` is 1.57 degrees $=0.0274$ rad, so the joint barely moves. Set `<compiler angle="radian"/>` or convert consciously and comment it.
4. 5 s at 1 ms is 5000 steps. 500 steps are 0.5 s. At a 2 ms step, 500 steps are 1.0 s and 5 s of rest is 2500 steps; the test is no longer comparable and contacts may behave differently, so change the step only with a note in the decisions log.
5. $\Delta\theta=1\text{ mm}/L$: for 0.1 m, 0.0100 rad $=0.573^\circ$; for 0.36 m, 0.00278 rad $=0.159^\circ$. Errors at the base joints are magnified by the lever arm, and a sign or axis error may vanish at the zero pose (all angles 0), so random configurations are needed.
6. $|3.18-3.10|/3.18=2.52\%$: fails at 2 %. Likely causes: a body (gripper jaw, camera, battery) missing from the URDF, or a density default used in MJCF where the URDF has an explicit mass; also unit slips (grams versus kilograms).
7. The Wilson interval of 91/100 is about (0.838, 0.952). The point estimate 0.91 is below 0.95, so the test fails. Fixes: move the table closer or raise the pillar so more points fall inside the annulus; shrink the table's far edge; choose the arm mounting offset. In the step 4 snippet (`reach_demo.py`) the same 0.24 m wide table is 98.6 % reachable at 0.18 to 0.32 m ahead and only 36.3 % at 0.25 to 0.45 m.
8. Defects: (a) `random.shuffle` uses the global Python generator that `np.random.seed` does not seed; (b) `np.random.seed` seeds the global NumPy state that any library may consume, so the sequence depends on call order; (c) identical in-process runs hide the issue because the process state repeats. A different machine or library version changes the order of consumption. Fix: `rng = np.random.default_rng(seed)` in `reset`, pass `rng` to every helper and use `rng.permutation(objs)` and `rng.uniform(...)`; never touch global state.
9. Record at every step the base position, arm joint positions, `np.isfinite` of `qpos`, and the maximum of $-\text{contact.dist}$ over `data.contact[:data.ncon]`. Thresholds: base drift 2 mm, arm drift 0.5 degrees, penetration 2 mm. A final-state check can pass while the robot rocked and returned, or while a contact exploded and settled; the maximum over time catches transients. Use the same zero command and a fixed seed.
10. A good answer has ten rows, each with a number and a unit, thresholds justified by a later need (grasp tolerance, odometry resolution, benchmark noise), and a checker that parses the table and reports the offending id. Typical code: a regular expression per row, `assert` that the metric and threshold cells are non-empty and that every `::test_name` exists. A threshold changes when a reference run shows it is either always passed with a wide margin (too loose) or flaky (too tight), recorded in the decisions log.

## Further reading

- [MuJoCo documentation: modeling](https://mujoco.readthedocs.io/en/stable/modeling.html) - MJCF elements, the compiler `angle` attribute, inertia and contacts.
- [MuJoCo documentation: simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html) - `mj_step`, `mj_forward`, resets.
- [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) - the `robotstudio_so101` model and its license.
- [ROS 2 Jazzy URDF tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html) - joints, links, limits and inertials.
- [MIT 6.4210 Robotic Manipulation](https://manipulation.mit.edu/) - the pick-and-place pipeline the capstone mirrors; Lecture 1 below.
- [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) - the reference project for tidying with a mobile manipulator.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) - the Wilson interval used in the acceptance tests.
- **More practice:** [LeRobot SO-101 documentation](https://huggingface.co/docs/lerobot/so101), [Articulated Robotics: describing a robot with URDF](https://www.youtube.com/watch?v=CwdbsvcpOHM).

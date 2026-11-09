# CoreLab practical labs review — Claude

Run ID: `corelab-labs-audit-20261031-01`. Baseline: CoreLab `38b6a1d`. All repository commits are listed in 1.3. This is a proposal. Nothing in the application, curriculum, assessments, evidence or robot repositories was changed.

Evidence labels used below:

- **[T]** I ran it on this machine.
- **[R]** I read it in a repository file.
- **[X]** External source, linked.
- **[E]** My estimate, not a measurement.

## Round 1 — Independent investigation

Written without reading any Codex file in this directory.

### 1.0 Findings in brief

1. **Do not build the practical curriculum around one robot.** Most of the learning value sits in functions that can be graded exactly with no robot at all. I classify only 53 of 176 topics as assessed directly in a lab, counting four shared with review.
2. **Recommended architecture: simulation-first and modular (option C), organised as a mobile robot, an arm and a shared capstone (option B).** Use four tiers: NumPy, MuJoCo, ROS 2 Jazzy in a container, and optional hardware. From option D, keep only a thin file contract for verifier results, not a robot abstraction layer.
3. **MUR5e should be an optional advanced reference, not the backbone.** It built cleanly and its navigation and visual servo steps ran, but its full mission **aborted at step 4 of 12 in both of my runs**, and I could not establish why. Its target pose is supplied in the goal, its perception is a fixed colour threshold, and it has no robot-learning component.
4. **A simulator is not automatically a valid oracle.** On the shipped TurtleBot3 MuJoCo model, a correct odometry integrator was off by about 29% of the distance travelled, because the wheels slip and do not reach the commanded speed. Grading against simulator ground truth would fail correct learners. Grade against closed forms and use simulation as the experiment.
5. **Green unit tests did not predict a working mission.** MUR5e's 9 selected tests passed while the mission failed. The end-to-end test I read uses mock action servers.
6. **The current lab verifier can be short-circuited by accident or intent.** A file that prints the success JSON and exits made `scripts/lab-tests.py` report a pass with exit code 0. This should be fixed before any new lab issues evidence.
7. **The cheapest credible hardware path is about $122–$500 in parts**, and hardware stays optional. Prices are listed in 1.11 with their sources and limits.

### 1.1 What CoreLab already has

**Curriculum.** 169 topics and 310 edges in `corelab/curriculum_graph_v1.json`; 31 authored lessons and diagnostics. The v2 proposal in `curriculum-review/proposed_curriculum_v2.md` adds seven candidates: M17, R16–R20, E16. I use its dependency table for prerequisites. Its 100-hour first tranche ends at an M12 → R03 → R04 FK milestone, which my L01 and L02 fit directly.

**Lab evidence today [R].**

| Fact | Location | Consequence for labs |
| --- | --- | --- |
| `topicId` only accepts `M02` and `PY01`; schema is strict; `checks` must be 8 or 6 | `lib/labs.ts` | Every new lab needs a new schema version. Do not edit the old one. |
| Any trusted A0 lab sets `dims.I = 2` for the whole topic | `lib/engine.ts:79-82` | A scoped lab would inflate a broad topic such as R04 or S03 unless scope is added. |
| Report has no contract version, oracle hash, seed or environment hash | `scripts/verify-lab.mjs` | Cannot say what was actually verified, or reproduce it. |
| Result is the last stdout line of the process that imported the learner's file | `scripts/verify-lab.mjs`, `scripts/lab-tests.py` | See finding below. |
| Web server never executes submitted code; the verifier is an intentional local CLI | `docs/guide.md` | Keep this. ROS labs stay local CLI runs too. |
| Signature proves provenance, not authorship; A0 is self-declared | `docs/guide.md` | Keep this honest wording for every lab. |

**Verifier short-circuit [T].** A two-line file, `print('{"passed":true,"checks":8}'); sys.exit(0)`, passed to `python3 scripts/lab-tests.py <file> M02` printed that JSON and exited 0. By my reading of `verify-lab.mjs`, the CLI would then sign it; I did not run the signing step, to avoid creating keys in the repository. This does not break the stated trust model, because the local owner is already out of scope. It does mean a learner's stray `sys.exit` or debug print can interfere with evidence. Fix in a new runner: run learner code in a child process, and take the result from the harness through a channel that learner code cannot write to by simply printing.

**Which topics need what.** Section 1.12 classifies all 176 topics. Across the 169 originals: 42 assessed in a lab, 4 partly automatic and partly reviewed, 16 independent exercises that are then applied in a lab, 54 independent exercises only, 13 used but not assessed in a lab, 9 optional extensions, 6 reviewed research, 2 capstone, 1 hardware-only, 22 deferred. All seven candidates are assessed in labs. Language, ML fundamentals and tabular RL get cleaner evidence from exercises with exact answers than from a robot.

### 1.2 Measurements that changed the design [T]

Machine: Ubuntu 22.04, 16 threads, 15 GB RAM, no NVIDIA GPU. MuJoCo 3.17.0, NumPy 2.5.4, Python 3.12. The spike scripts are not part of the repository; the method is described with each result so it can be repeated. They and their logs were lost when the machine rebooted during this round, so **the numbers below come from my session record and can no longer be re-read from files**.

**Model loading.** Every model loaded and stayed finite for 5000 steps.

| Model | nq / nu | Sensors / cameras shipped | Speed vs real time |
| --- | --- | --- | --- |
| TurtleBot3 Burger | 9 / 2 | 0 / 0 | 261× |
| TurtleBot3 Waffle Pi | 9 / 2 | 0 / 0 | 275× |
| OpenMANIPULATOR-X | 6 / 5 | 0 / 0 | 368× |
| OMX | 7 / 6 | 0 / 0 | 326× |
| OMY | 10 / 7 | 0 / 0 | 249× |
| SO-101 | 6 / 6 | 0 / 0 | 334× |

None ship a lidar, IMU or camera, so CoreLab would have to add them.

**Kinematic oracles work.** A separate NumPy transform chain agreed with MuJoCo body positions to 1.8e-16 m on SO-101 and 1.3e-16 m on OMX over 100–200 random poses. Injected bugs (joint sign, degrees, transform order, dropped translations) gave worst-case errors of 0.39–0.56 m. An analytic-versus-central-difference Jacobian check agreed with `mj_jacBody` to 1.9e-11. **Automatic FK and Jacobian PASS is therefore feasible with wide margins.**

**Wheeled contact is not a valid oracle.** I commanded both TurtleBot3 Burger wheels at 4 rad/s for 10 s.

| Quantity | Value |
| --- | --- |
| Ideal distance at r = 0.033 m | 1.32 m |
| Wheel speed actually reached | about 2.47 rad/s |
| Distance from integrated wheel angles | 0.80 m |
| True distance in simulation | 0.62 m |
| Odometry error | 0.18 m, about 29% of distance travelled |

Readings of the model: `kv=0.1` with `frictionloss=0.1` limits wheel speed, and the wheels collide as meshes. Waffle Pi was closer, with 0.076 m error over 0.57 m. I then wrote a small model with cylinder wheels and a frictionless caster. Straight-line error fell to 0.057 m over 1.55 m, but an arc still had 0.32 rad yaw error and a pure spin about 2.9 rad after wrapping. Even a clean contact model has an effective track that differs from its geometry.

Design consequences: grade `odom_step` against closed-form arcs; make the simulator gap the experiment; teach calibration from it.

**Tolerances need thought, or they create false failures.** Worst error of `odom_step` against closed-form arcs, 500 segments, six motions including reverse and spin:

| Implementation | Worst error |
| --- | --- |
| Exact arc | 1.3e-13 |
| Midpoint | 4.8e-6 |
| Euler (valid, first order) | 2.9e-3 |
| Missing the average of the wheels | 1.0 |
| Ignored heading | 1.7 |
| Swapped wheels | 2.6 |
| Half track | 2.8 |

A 1e-3 tolerance would fail valid Euler. 1e-2 passes all valid integrators and rejects every bug. Integrator order should be a separate objective with a refinement test.

**PID margins.** With `kp=6, ki=8, u_max=1, target=0.8, τ=0.5`, overshoot was 0.000 with anti-windup and 0.121 without. A flipped feedback sign ended at −0.998.

**ROS 2 node verification without a simulator works.** Inside a clean `ros:jazzy` container, a harness replayed `JointState` messages along a known arc to a reference node and compared the final `/odom` with the closed form.

| Node | Position error | Harness verdict |
| --- | --- | --- |
| Reference | 7.0e-6 m | PASS |
| Swapped wheels | 1.13 m | FAIL |
| Wall-clock stamp | 4.0e-3 m | FAIL (stamp check) |
| TF frames reversed | 4.0e-3 m | FAIL (frame check) |

About 115–119 of 200 replayed messages arrived, because the harness published quickly. Odometry from cumulative positions tolerated that, which is itself a teaching point. Each run took a few seconds, so this kind of check can run with no Gazebo at all.

**Shipped arm meshes and grasping: not demonstrated.** I tried to hold a small cube in the SO-101 and OpenMANIPULATOR-X models: scripted IK pick on SO-101 (0 of 36 parameter combinations lifted), then direct placement near the jaws (SO-101 0 of 125 tested placements held; OM-X 0 of 63). **This is not proof that these models cannot grasp.** My placement grid may have missed, and both use convex mesh collisions. It does mean no lab may depend on them until someone shows a working grasp. In contrast, a simple slide-joint gripper with box pads worked first time once the height was right: fingers stopped at 14 mm on the cube against 26 mm without, and the 2.5 cm cube was lifted about 0.3 m and held.

**Stiff actuators need the right integrator.** My first small diff-drive model reached −31.8 rad/s on a 4 rad/s command under the default integrator with `dt=0.002`. It was stable with `implicitfast`. This is useful for L08 and a warning to lab authors.

**Composing a mobile manipulator in MuJoCo works, with one cost.** `MjSpec` attached OpenMANIPULATOR-X to Waffle Pi and compiled to nq 15, nu 7. It stayed upright for 2000 steps. Speed was 145× real time with no rangefinders, 7.6× with 8 and 2.0× with 36, so ray casts over meshes are the bottleneck. Use primitive collision worlds, or ray cast in NumPy against known geometry. I did not test driving or manipulating with this composite.

**Offscreen rendering.** EGL rendered at 72 frames/s at 320×240 with no NVIDIA GPU. It may have used the integrated GPU, so I do not claim a pure-CPU figure. OSMesa failed on this machine.

### 1.3 Open-source platforms

I checked each repository's own files at the commit shown, on 2026-10-31.

| Candidate | Commit, activity | License | ROS 2 and simulator | Hardware files | Executed here | Role |
| --- | --- | --- | --- | --- | --- | --- |
| MUR5e stack | `a35e3e8`, 51 commits, one author, 2026-06-17 to 07-11; no CI workflows; 16 stars | Root Apache-2.0; `ur_description` and `mir_description` BSD-3; 3 packages say `TODO: License declaration` | Jazzy, Harmonic | None. MiR100 + UR5e is commercial hardware; no BOM | Built; 9 tests pass; mission aborted twice | Optional simulation reference |
| open_manipulator | `b83daec`, tag 5.1.4, CI, 31 commits since 2026-04-30 | Apache-2.0 | Jazzy; MoveIt and Gazebo launches for OMX-F, OMY, OM-X | ROBOTIS products | **Not verified.** Source build under my own 9 GiB container limit: compiler killed on `open_manipulator_collision`, 10 packages finished, launch not run. Says nothing about the repository. | Default ROS arm, pending a test |
| robotis_mujoco_menagerie | `d8344c0`, last commit 2026-02-02 | Apache-2.0, per-model LICENSE files | MuJoCo only | None | Loaded, FK checked | Default T1 arm and base models |
| turtlebot3 | `fc817ce`, tag 2.3.7, CI on Humble and Jazzy | Apache-2.0 | Humble, Jazzy; `turtlebot3_simulations` | ROBOTIS product | **Ran headless:** odometry matched, one Nav2 goal reached. Official launch fails without a display. | Default ROS mobile simulation |
| andino | `8ee8408`, CI on Humble and Jazzy, firmware tests | BSD-3 per package; no root file, so GitHub reports none | Humble, Jazzy; separate Gazebo, Webots, MuJoCo and Isaac repos | STLs, 22-item BOM with links but no prices, assembly guide | Not run; read only | Cheap physical base candidate |
| linorobot2 | `f6b0bd0`, Jazzy default, Lyrical branch, Humble branch stale since 2025-02 | Apache-2.0 | Jazzy, Lyrical, own Gazebo package, Docker with browser desktop | Build-your-own guide in a separate repo; no costed BOM in what I read | Not run; read only | Alternative physical base |
| lerobot | `3f797de5`, v0.6.1, 487 commits since 2026-04-30, 861 open issues | Apache-2.0 | No ROS; Python ≥ 3.12 | Supports SO-100/101, OMX, LeKiwi, Koch and others | Installed; 5 ACT steps | Imitation-learning tooling, pinned |
| SO-ARM100 *(added)* | `a758567`, active | Apache-2.0 | MJCF and URDF for SO-101; no ROS stack in the repo | STL, STEP, costed BOM, vendors | Loaded, FK checked | Cheapest physical arm |
| LeKiwi *(added)* | Pushed 2026-08-05 | Apache-2.0 | LeRobot support; BOM page does not mention simulation | BOM with costs | Not run | Cheapest physical mobile manipulator |
| XLeRobot *(added)* | Pushed 2026-10-06 | Apache-2.0 | README describes MuJoCo simulation | Author-stated cost | Not run | Second option; not assessed in depth |

I added SO-ARM100 and LeKiwi for one reason: they are much cheaper than the ROBOTIS hardware and are supported by LeRobot. I looked at `turtlebot3_manipulation` (Apache-2.0, Jazzy branch, last pushed 2025-06) but did not run it. Google's `mujoco_menagerie` and `ros-controls/mujoco_ros2_control` exist and are active, but I found no need for them in the first labs and did not test them.

**MUR5e: actual behaviour against README claims.**

| README claim | What I found |
| --- | --- |
| Colcon build | **[T] True.** 9 packages, 2 min 17 s. Package installation took 13.5 min on this connection. Container grew by 4.47 GB. I used `ros:jazzy` plus the named packages, not the full `ros-jazzy-desktop` and wildcard. |
| Tests | **[T] 9 selected tests passed** (optimizer, end-to-end, recovery, payload). **[R]** The end-to-end test I read uses mock Nav2, MoveIt and optimizer servers. No CI. |
| Autonomous 12-step mission, with demo video | **[T] Not reproduced.** Both headless runs aborted at step 4 with `Arm movement failed with error code: 99999`. Steps 1–3 and the servo succeeded: navigation reached the goal in about 100 s, and the servo aligned with 0.4 mm and 0.1 mm error. The advance failed with Pilz `NO_IK_SOLUTION`, then OMPL `GOAL_STATE_INVALID`. |
| Recovery branch | **[T] Ran as described** and reported the failure honestly. |
| "Locate a target object" | **[R] Not found.** `TargetAcquisition` only checks the pose already in the action goal. The default goal matches the workpiece position in the world file. |
| Visual servo | **[T] Runs. [R]** It uses a fixed HSV range for a yellow object, plus depth. It refines a known pose and does not search. |
| Carrying the payload | **[R]** `AttachPayload` changes only the MoveIt planning scene, with a 0.60 m cylinder; the Gazebo workpiece is 0.40 m. I found no detachable-joint plugin, so physical carrying depends on friction. **[T]** The workpiece was displaced in both runs, ending about 0.17 m lower and away from its start. |
| `specs/` and `.agents/` directories | **[R]** Listed in the README but not tracked in the repository. |

**Limits on the mission result.** I ran under Docker with software rendering, no GPU and no display, with four simulated cameras. Low `/stats` real-time-factor samples (about 0.005) appeared during both runs, and I do not trust those samples enough to quote them as a cause. **So I cannot say whether the failure is a repository defect or an effect of my environment.** The author's video shows success on some other setup. A GPU machine should repeat this before anyone writes a lab on top of it. I did not test the `bypass_visual_servo` parameter.

**MUR5e licensing is unresolved.** The repository's `ur_description` carries only BSD-3. The upstream package index says some UR mesh sets are governed by UR's own graphical documentation terms ([index](https://index.ros.org/p/ur_description/)). Named sets in what I found were UR20 and UR30; I could not confirm the status of UR5e meshes. Check before redistributing derived assets. Pointing learners at the upstream repository avoids the question.

**TurtleBot3 on Jazzy [T].** Package `ros-jazzy-turtlebot3-gazebo` 2.3.7 from apt, one run only.

| Check | Result |
| --- | --- |
| Official `turtlebot3_world.launch.py` with no display, then under `xvfb` | **Failed in both.** It starts the Gazebo GUI with `on_exit_shutdown: true`; the GUI crashed and took everything down |
| Same parts started by hand: `gz sim -r -s`, spawn, state publisher | Worked |
| Drive at 0.08 m/s for 12 s | Gazebo truth 0.963 m, `/odom` 0.964 m, gap 0.7 mm |
| Nav2 with the packaged map and `burger.yaml`, one goal | `SUCCEEDED` in 23 s; final model pose (−0.485, −1.794) against goal (−0.5, −1.8) |

Two consequences. First, this stack is the most directly usable base found, but CoreLab needs its own headless launch, and my initial use of the `param/humble` file on Jazzy failed, so the parameter path matters. Second, **Gazebo's near-perfect odometry against MuJoCo's 29% error shows the two simulators teach opposite lessons about the same mechanism**: neither is reality. L03 should say so, and L21 can use the contrast. One successful goal is not a reliability figure.

**Important distribution dates.** Per [REP 2000](https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-2000.rst): Humble ends May 2027, Jazzy May 2029, Kilted November 2026. Per [Gazebo releases](https://gazebosim.org/docs/latest/releases/): Fortress ends May 2027, Harmonic May 2029, Jetty May 2031. **A new lab series pinned to Humble would have about seven months left**, so pin to Jazzy and Harmonic. The REP copy I read does not list Lyrical, although linorobot2 has a Lyrical branch; a later migration is plausible but not something I examined.

### 1.4 Architecture alternatives

Ratings are my judgement from the evidence above, not measurements.

| Criterion | A. One mobile manipulator | B. Mobile + arm + capstone | C. Simulation-first modular | D. Existing platforms behind a unified interface |
| --- | --- | --- | --- | --- |
| Learning effectiveness | Weak early: FK buried in a large stack | Good | **Best**: smallest system that shows each idea | Depends on what sits behind it |
| Coverage | Broad but shallow on foundations | Good | **Good**, by adding tiers | Broad |
| Cost to learner | Free in simulation; real hardware far too costly | Moderate if hardware is assumed | **Free, with hardware optional** | Varies |
| Installation | **Worst**: 5.5 GB image before the first lesson | Moderate | **Best at the start**: `pip` for two tiers | Worst |
| Independent implementation | Low: most code already works | Good | **Best** | Low if the abstraction hides the work |
| Assessment validity | Weak: end-to-end success mixes everything; MUR5e's own run failed here | Good | **Best**: exact oracles | Weak unless per-lab contracts exist |
| Maintenance | One-author dependency | Moderate | **Good**: few dependencies early | **Worst**: must track every platform |
| Community reproducibility | Poor | Moderate | **Best** | Poor |

**Decision: C, shaped by B. Reject A as a backbone. Reject D's unified robot interface.** A learner writing `odom_step` needs a function signature, not a `Robot` class. A common abstraction would have to be maintained against ROS, MuJoCo, LeRobot and several vendors, and it would hide the interfaces that the ROS labs are meant to teach. What survives from D is a results contract, described in 1.9.

### 1.5 Recommended tiers and systems

| Tier | Contents | Install | Platforms | Used by |
| --- | --- | --- | --- | --- |
| **T0** | NumPy and a fixed test harness | `uv` or `pip`, seconds | Windows, macOS, Linux (same as CoreLab's Python labs today; not re-tested on Windows or macOS for this review) | L01, L03 and L04 grading, L07, L09–L11, L15, L22 |
| **T1** | MuJoCo with pinned models | `pip`; wheels exist per MuJoCo's packaging, tested here on Linux only | Linux tested; others to verify in the pilot | L02, L03 and L04 experiments, L06, L08, L16–L18, L20 |
| **T2** | `ros:jazzy` digest-pinned image; Gazebo Harmonic only where needed | Docker. Base image 1.32 GB on disk; full navigation and MoveIt set about 5.5 GB | Linux tested. Windows and macOS through Docker are untested and likely need a browser desktop; linorobot2's Docker setup is a pattern to study | L05, L12–L15 |
| **T3** | Optional hardware | Purchase and build | N/A | "Real-world option" in each lab |

**Reference systems.**

| Role | Simulation | Optional hardware | Why |
| --- | --- | --- | --- |
| Arm, T1 | OMX in `robotis_mujoco_menagerie` | SO-101 (cheapest) or OMX | Same arm is available in MuJoCo, in ROS 2 Jazzy with MoveIt and Gazebo launches, and in LeRobot (`omx_follower`) |
| Arm, T2 | OMX-F from `open_manipulator` | Same | Vendor maintained with CI; SO-101 has no ROS stack in its repo |
| Mobile, T1 | Small CoreLab-authored diff-drive MJCF; TurtleBot3 MJCF as the model-mismatch case | Andino, linorobot2 or TurtleBot3 | Authoring about 40 lines removes a dependency and gives known geometry |
| Mobile, T2 | TurtleBot3 in Gazebo Harmonic | Same | Packaged for Jazzy |
| Learned policies | Small from-scratch BC first; LeRobot 0.6.1 pinned for ACT | SO-101 pair or OMX-AI | LeRobot changes fast; do not expose its internals as the lesson |
| Capstone | See 1.8 | LeKiwi | Cheapest physical mobile manipulator found |

The arm choice is my main uncertainty: OMX is the only arm I found spanning all three stacks, but SO-101 is about a third of the price. Learners implement against parameter tables, so changing the arm later is cheap.

### 1.6 First five foundational labs — detailed specifications

Every lab follows the same order: predict, derive, implement from a blank function, run the verifier, then explain what surprised you. No lab is passed by running a launch command. Effort figures are my estimates for a learner who has the prerequisites, with at least ±50% uncertainty; nobody has timed them.

#### L01 — Frames and transforms

1. **Objectives.** Label source and target frames. Compose and invert rigid transforms. Treat points and directions differently. Reject a reflection presented as a rotation.
2. **Topics.** Assesses M12, R03. Prerequisites M02, M03, PY04.
3. **Theory.** SO(3) and SE(3) as matrices, inverse `(Rᵀ, -Rᵀp)`, composition order, homogeneous points and directions.
4. **Robot and simulator.** None. NumPy only, tier T0.
5. **Learner implements.** `make_transform(R, p)`, `invert(T)`, `compose(T_ab, T_bc)`, `apply_point(T_ab, p_b)`, `apply_direction(T_ab, v_b)`, `is_rotation(R, tol)`.
6. **Visualization.** Justified once: the existing vector and frame demo, extended to show A-then-B next to B-then-A. The learner predicts first.
7. **Experiment.** Predict where a tool-tip point lands under both orders. Then chain base, wrist and camera, and find a marker seen by the camera in the base frame.
8. **Verification.** Hand-computed fixtures using coordinate-axis rotations, not the learner's code. Properties: `invert(T)·T = I`, associativity, direction unaffected by translation, distance preserved. Mutations the verifier must reject: swapped order, missing `Rᵀ` in the inverse translation, direction translated, reflection accepted. Not yet prototyped.
9. **Failures.** Row versus column vectors, `wxyz` versus `xyzw` quaternions, in-place mutation of inputs, degrees passed as radians.
10. **Evidence and PASS.** C: frame-labelling items. M: one hand composition. I: all fixtures and properties within 1e-9. T: a new camera mount, reviewed, otherwise left unawarded. Scope: "rigid transforms as matrices". No claim about twists or near-π logarithms.
11. **Difficulty and effort.** Beginner; 2–4 h.
12. **Real-world option.** None needed.

#### L02 — Arm forward kinematics

1. **Objectives.** Derive a planar 2R arm with relative angles and unequal links, then extend to a declared spatial transform chain with a tool offset.
2. **Topics.** Assesses R04. Prerequisite R03. Uses S02 only as a checker.
3. **Theory.** Serial chains, joint axes, joint zero conventions, reachable workspace.
4. **Robot and simulator.** OMX model from `robotis_mujoco_menagerie` at `d8344c0`, MuJoCo pinned by lockfile, tier T1. CoreLab extracts the parameter table once, so the learner never has to parse MJCF.
5. **Learner implements.** `planar_2r(q, l1, l2)`, `fk_chain(params, q, tool=None)`.
6. **Visualization.** MuJoCo viewer is optional and is not needed for grading.
7. **Experiment.** Predict tip positions for three poses, including stretched out. Compare the trigonometric and chain forms.
8. **Verification.** Closed-form 2R fixtures, then 100 seeded configurations against MuJoCo body positions. MuJoCo is a valid oracle here because the comparison is purely kinematic. Prototype results are in 1.2: agreement of about 1e-16 m against bug errors of 0.39–0.56 m, so a 1e-6 m tolerance separates them without tuning.
9. **Failures.** Forgetting `qpos0`, multiplying the joint rotation before the offset, wrong tool frame, quaternion order.
10. **Evidence and PASS.** C: absolute versus relative angle. M: 2R by hand. I: worst position error below 1e-6 m on all seeded poses and all planar fixtures. T: changed tool frame or axis convention, reviewed. Scope: "transform-chain FK for a given parameter table". PoE is not part of this PASS. Planar and spatial may be separate contracts.
11. **Difficulty and effort.** Beginner to intermediate; 3–5 h.
12. **Real-world option.** Read joint angles from an OMX or SO-101 and compare a ruler measurement of the tip. Informal; produces no evidence.

#### L03 — Differential-drive odometry

1. **Objectives.** Map wheel motion to body motion and back, integrate pose, and explain the difference between a correct integrator and an accurate estimate.
2. **Topics.** Assesses R02 and part of R20. Applies M05, RS05. Prerequisites M05, R03, PY04.
3. **Theory.** Rolling without slip, instantaneous centre of rotation, arc versus midpoint versus Euler integration, systematic versus random error.
4. **Robot and simulator.** T0 fixtures for grading. T1 for the experiment, using a small CoreLab-authored MJCF plus the shipped TurtleBot3 MJCF.
5. **Learner implements.** `wheel_speeds(v, w, track, radius)`, `body_twist(wl, wr, track, radius)`, `odom_step(pose, dl, dr, track)`, `calibrate(straight_log, spin_log) -> (radius, track)`.
6. **Visualization.** Odometry path against true path, drawn from the learner's own log. Justified because the error is spatial.
7. **Experiment.** Predict the distance covered at a commanded wheel speed. Measure. Explain the gap. Calibrate, then test on a held-out path.
8. **Verification.** Grade against **closed-form arcs**, not simulator ground truth. Fixtures cover straight, arc, reverse, pure spin and non-zero start heading. Tolerance 1e-2 per 1.2. Integrator order is an optional objective checked by refinement. `calibrate` is graded on synthetic logs with known radius and track. `calibrate` is not yet prototyped.
9. **Failures.** Comparing against simulator truth and blaming the code; angle wrap; unit errors; a track width that differs from the geometric value.
10. **Evidence and PASS.** C: why zero odometry error is not expected. M: arc by hand. I: all fixtures within 1e-2, `calibrate` within 1% on synthetic data. T: changed wheel slip or layout, reviewed. Scope: "odometry integration and two-parameter calibration". It claims no localization.
11. **Difficulty and effort.** Intermediate; 4–7 h.
12. **Real-world option.** A square-path test on any differential-drive base at low speed with a tape measure, under its own safety checklist. Never required.

#### L04 — Feedback, PID and actuator limits

1. **Objectives.** Predict the effect of feedback sign, gain, integral action, saturation and sample rate. Implement a limited PID that does not wind up.
2. **Topics.** Assesses C01, C03, C09, R09. Applies M05, M07. Prerequisite M05 only; C02 is not required for tuning. C09's v2 prerequisites include M11, so its sampling objective stays limited to this experiment.
3. **Theory.** First-order plant, steady-state error, integral action, saturation, anti-windup, delay.
4. **Robot and simulator.** T0 NumPy plant for grading. Optional T1 single OMX joint, using its actuator force limit as the saturation example.
5. **Learner implements.** `PID.update(error, measurement, dt)` with derivative on measurement, output clamp and anti-windup; `step_metrics(t, y, target)`.
6. **Visualization.** Step response with and without anti-windup, extending the existing PID demo. The learner predicts the overshoot first.
7. **Experiment.** Raise the sample period and add delay until the response oscillates. Record the point and explain it.
8. **Verification.** Exact checks: proportional-only steady state against the formula, zero steady error with integral action, output never above the limit, results that barely change when `dt` is halved. Margins in 1.2 show the windup and sign bugs are detectable. The other checks are not yet prototyped.
9. **Failures.** `dt` ignored in the integral, derivative kick on a setpoint step, clamp without back-calculation, sign error.
10. **Evidence and PASS.** C: sign and windup. M: steady-state error by hand. I: all exact and limit checks. T: a changed plant gain or delay, reviewed. Scope: "tuning a limited PID on a named toy plant". No claim of stability analysis, which belongs to C02 and C04.
11. **Difficulty and effort.** Intermediate; 3–6 h.
12. **Real-world option.** Wheel speed control with wheels off the ground, a watchdog and a reachable power switch. Simulation PASS does not authorize this.

#### L05 — Your first tested ROS 2 node

1. **Objectives.** Wrap the L03 function in a node. Publish correct stamps and frames. Write tests that catch real bugs. Rebuild from a lockfile.
2. **Topics.** Assesses S03, S05, PY07, T04, T05. Uses T01–T03. Prerequisites L03, PY01. PY07 and T04 keep separate scores.
3. **Theory.** Nodes, topics, QoS, TF2, parameters, simulated time.
4. **Robot and simulator.** No Gazebo. Scripted `sensor_msgs/JointState` replay in a digest-pinned `ros:jazzy` container (1.10).
5. **Learner implements.** `odom_node.py`: subscribes to `joint_states`, publishes `nav_msgs/Odometry` on `odom` and `odom → base_link` on TF, with `track` and `radius` parameters. Also `test_odom_node.py`.
6. **Visualization.** None. `ros2 topic echo` and `tf2_echo` teach more.
7. **Experiment.** Predict the output of a known replay. Then replay out-of-order stamps and a missing joint; choose a policy and document it.
8. **Verification.** Tested prototype in 1.2. The harness replays a known sequence, compares the final pose with the closed form, and checks frames, stamps and TF agreement. Separately, the learner's own tests run against one correct and several broken implementations (swapped wheels, TF frames reversed, wall-clock stamp, no reset handling). This second part makes PY07 and T04 evidence real instead of assumed; I have not prototyped it.
9. **Failures.** Workspace not sourced, QoS mismatch, `use_sim_time` confusion, publishing `base_link → odom`, wall-clock stamps.
10. **Evidence and PASS.** C: TF direction, QoS. M: not applicable, declared as such. I: node passes the replay; separately, test suite rejects every broken implementation and accepts the correct one. T: a new failure with a minimal reproducer, reviewed. Scope: "single Python node with an odometry contract". A C++ route uses CPP01 as a separate contract.
11. **Difficulty and effort.** Intermediate; 5–9 h plus container setup.
12. **Real-world option.** Run the same node on a real base with motors disabled and wheels turned by hand.

### 1.7 Remaining roadmap

Fields follow the same 12-item order in condensed form. Automatic checks follow the rules in 1.9: exact oracles first, simulator as experiment. Unless a result is cited from 1.2, these labs have not been prototyped. Prerequisites follow the v2 dependency table; R16–R20, E16 and M17 are candidates, not approved topics.

**Stage B — core robotics on T0/T1.**

**L06 IK and Jacobian.** (1) Analytic 2R IK with both branches, numerical IK, singularity behaviour. (2) R05, R06, M17; prereq R04, M06, M04. (3) Least squares, damping, rank, velocity and force duality. (4) OMX in MuJoCo. (5) `jacobian(params, q)`, `ik_2r`, `ik_dls`. (6) Manipulability ellipse, only if the pilot needs it. (7) Predict which direction is lost at a stretched pose. (8) Analytic Jacobian against central differences (1.2); IK by FK round trip; known unreachable targets must report failure. (9) Local minima, joint limits, no-solution reported as success. (10) I: Jacobian within 1e-6, IK success on a reachable set, honest failure otherwise. Excludes twists. (11) Intermediate; 6–10 h. (12) Read-only pose check.

**L07 Trajectories.** (1) Separate path from time law; bounded velocity and acceleration. (2) R17; prereq M05, R04. (3) Trapezoid and triangular profiles. (4) T0, then OMX in T1. (5) `trapezoid(d, vmax, amax)`, `sample_joint_traj`. (6) Velocity plot. (7) Predict when no cruise phase exists. (8) Endpoint, continuity and bound checks, degenerate distance, analytic duration. (9) Rounding at phase boundaries. (10) I: bounds and duration; no claim about jerk or torque. (11) Intermediate; 3–6 h. (12) Slow motion on a real arm after review.

**L08 Dynamics and joint-space control.** (1) Gravity compensation, computed torque, integrator choice, model mismatch. (2) R07, R19, S01, S02; prereq C03, R06, M07. (3) Manipulator equation, energy. (4) MuJoCo pendulum, then 2-link. (5) `gravity_torque`, `computed_torque`. (6) Energy drift plot. (7) Predict energy behaviour for explicit versus implicit integration; 1.2 shows a real divergence. (8) Closed-form pendulum, `mj_inverse` cross-check, energy bounds. (9) Stiff actuators, ignored armature. (10) I: torque within tolerance, tracking metric on a declared plant. Joint space only; no impedance or hardware claim. (11) Advanced; 8–14 h. (12) None by default.

**L09 Localization.** (1) Motion and sensor models, grid Bayes then particle filter, recovery. (2) R16, R20, C06; prereq M08, M09, R03. (3) Bayes filter, resampling. (4) T0 2D world with ray casting in NumPy, which also avoids the mesh ray cost in 1.2. (5) `predict`, `update`, `resample`. (6) Particle cloud, justified by ambiguity. (7) Predict convergence in a symmetric corridor. (8) Exact small-grid Bayes oracle; particle sanity checks; k-of-n seeded recovery threshold declared in advance. (9) Particle deprivation, overconfident likelihood. (10) I: exact-grid match plus declared seeded rate. No claim of SLAM. (11) Advanced; 7–12 h. (12) Log replay from a real base.

**L10 Kalman and sensor fusion.** (1) Derive the update; fuse odometry and a position-like signal. (2) C07, C08; optional C12; prereq C06, M09. (3) Linear-Gaussian assumptions. (4) T0. (5) `kf_predict`, `kf_update`. (6) Covariance ellipse. (7) Predict the effect of wrong noise settings. (8) Against an exact batch solution; ensemble NEES with a declared false-failure rate and run count, never "every run inside 95%". (9) Asymmetric covariance, mis-stamped measurements. (10) I: matches oracle within numeric tolerance. Needs expert review before release. (11) Advanced; 6–10 h. (12) IMU log replay.

**L11 Planning.** (1) Graph search, C-space, RRT, honest failure. (2) E02, R18; prereq PY02, R03. (3) Completeness and its limits. (4) T0 planar arm among polygons. (5) `astar`, `collides`, `rrt`. (6) Tree growth view. (7) Predict success in a narrow passage. (8) Exhaustive grid oracle for reachability; independent segment collision test; a failed RRT is never proof of no path. (9) Coarse collision sampling tunnels through obstacles. (10) I: A* cost optimal on fixtures; RRT paths collision free. (11) Intermediate; 6–10 h. (12) None.

**Stage C — systems on T2.**

**L12 Robot description and TF.** (1) Write a URDF and check it against your own FK. (2) S04, T06; prereq R03, S03. (3) Links, joints, inertials. (4) Learner-authored 2R, or OMX description, no Gazebo. (5) URDF fragment and checker. (6) RViz. (7) Predict `tf2_echo` output. (8) `xacro` and URDF parse; TF against L02 FK within tolerance. (9) `package://` paths, wrong joint origin. (10) I: TF agrees with own FK. (11) Intermediate; 3–5 h. (12) None.

**L13 Navigation, evaluated rather than launched.** (1) Write a path-following controller; evaluate SLAM and Nav2 with metrics. (2) Applies V17, R20, E02, C03 as a scoped integration, not those topics in full. (3) Costmaps, pure pursuit, recovery. (4) TurtleBot3 in Gazebo Harmonic. (5) `pure_pursuit_node` with bounded output; metric script for path error. (6) RViz. (7) Predict where your controller cuts corners. (8) Controller graded offline against recorded paths; integration graded by seeded scenario success on a changed layout, from rosbag metrics. (9) TF timeouts, sim time, CPU starvation. (10) I: offline contract plus k-of-n changed-layout runs. (11) Advanced; 10–18 h. (12) Same node on a real base with a speed cap.

**L14 ros2_control and MoveIt.** (1) Mock hardware interface; plan with a collision scene; diagnose planning failures. MUR5e's `NO_IK_SOLUTION` then `GOAL_STATE_INVALID` log is a good real case to explain. (2) S06, S10; applies R18. (3) Controller manager, action interfaces. (4) OMX, `open_manipulator` Jazzy branch, mock hardware. (5) Hardware interface stub; goal client; scene setup. (6) RViz. (7) Predict which goal is unreachable. (8) Launch tests on controller state, goal result and joint limits; an injected timeout must be reported. (9) Controller name mismatch, stale joint states. (10) I: mock-hardware contract; no real hardware claim. (11) Advanced; 10–16 h. (12) Real OMX after review.

**L15 Behavior trees, recovery and safety.** (1) Write a tree with explicit failure handling; define hazards and stop conditions. (2) E04, S07; applies E05. (3) BT semantics, watchdogs. (4) Mock skills in BehaviorTree.CPP or py_trees; no simulator. (5) Tree file, recovery nodes, watchdog. (6) Tree monitor. (7) Predict the node sequence under each injected fault. (8) Scripted fault injection with expected transitions; a stale sensor must stop motion. MUR5e's recovery branch is a useful reading example. (9) Re-entry of reactive sequences, memory nodes. (10) I: fault table all correct. Hazard analysis needs a reviewer. Never hardware authorization. (11) Intermediate; 5–9 h. (12) Reviewed hazard table first.

**Stage D — perception on T1.**

**L16 Camera model and calibration.** (1) Project and back-project; recover intrinsics. (2) V01, V03, V04; prereq PY04, M12. (3) Pinhole, distortion. (4) MuJoCo offscreen camera with known intrinsics; rendering tested in 1.2. (5) `project`, `backproject`, `calibrate`. (6) Reprojection plot. (7) Predict the pixel for a known point. (8) Against rendered ground truth and synthetic targets. (9) Axis conventions. (10) I: reprojection and intrinsics tolerance on held-out views. (11) Intermediate; 6–10 h. (12) Phone or USB camera.

**L17 Visual servoing.** (1) Colour and depth to pose; closed-loop alignment. (2) V02; applies V13, R06; optional V08. (3) Image Jacobian, depth. (4) OMX in MuJoCo with an added wrist camera. (5) `detect`, `pose_from_depth`, `ibvs_step`. (6) Error versus time. (7) Predict the effect of wrong depth. (8) Injected object offset; error must converge from randomized starts; lighting or colour change as transfer, which is exactly where a fixed HSV range like MUR5e's would break. (9) Hard-coded thresholds, invalid depth. (10) I: seeded convergence rate. (11) Advanced; 8–14 h. (12) USB camera on SO-101 or OMX.

**Stage E — contact and learning.**

**L18 Grasping.** (1) Friction, force closure for parallel pads, slip. (2) R08; optional R14; prereq R07. (3) Coulomb friction. (4) **Primitive-pad gripper in MuJoCo**, not shipped meshes (1.2). (5) `grasp_feasible`, `close_until_contact`, lift sequence. (6) Contact force view. (7) Predict the minimum friction to hold a mass. (8) Closed-form friction check; simulator lift as experiment with a declared success band. (9) Interpenetration, how paired friction is resolved. (10) I: analytic check and k-of-n lift. Planar parallel pad only. (11) Advanced; 6–10 h. (12) SO-101 pick of a light soft object.

**L19 Imitation from demonstrations.** (1) Audit data before training; BC baseline; explain why a policy fails. (2) E16, RL17, E07; applies ML03, ML07, PY06; optional E11. (3) Distribution shift, episode splits. (4) Small state-only BC from scratch is required; LeRobot 0.6.1 with `lerobot/pusht` is optional for ACT. (5) `split_by_episode`, `audit_episodes`, `bc_train`. (6) Rollout video only for failure analysis. (7) Predict what a frame-level split would report. (8) Synthetic corrupt episodes must be flagged; split leakage must be rejected; rollout score across seeds against a baseline. (9) Leakage, normalization fit on all data, misaligned action and state stamps. (10) I: audit and split exact; rollout k-of-n above baseline. (11) Advanced; 10–20 h plus compute. (12) Teleoperated SO-101 or OMX dataset. **[T]** LeRobot installed in 50 s (1.7 GB, CPU torch) and ran 5 ACT steps in 38 s including dataset download. That shows the pipeline starts, not that a policy learns.

**L20 Reinforcement learning for a robot task.** (1) Design a reward; run a pre-declared experiment; report variability. (2) RL10, RL12, RL13, RL14, RS02; optional RL11, RL21; prereq RL09, ML06. (3) Clip objective, advantage, truncation versus termination. (4) MuJoCo reach on OMX with low-dimensional state. (5) Tiny `ppo_update` core, reward, evaluation protocol. (6) Learning curves with spread. (7) Predict a reward loophole. (8) Analytic ratio and gradient checks; bootstrap at truncation must differ from termination; protocol reviewed. (9) One lucky run, wrong bootstrap. (10) I: tiny-case checks. Task performance is reported with k-of-n declared in advance, not treated as mastery. (11) Advanced; 12–25 h plus compute. (12) None by default.

**L21 System identification and sim-to-real.** (1) Fit a model from logs; show where randomization helps and where it hides a bad model. (2) S08, S09, RL16; prereq S02, C06. (3) Identifiability, regression. (4) Synthetic logs by default; the TurtleBot3 wheel gap in 1.2 is a natural case. (5) `fit_params`, `randomize`. (6) Fit residuals. (7) Predict which parameter a log cannot identify. (8) Recover known parameters from synthetic logs; unidentifiable cases must be flagged. (9) Too little excitation. (10) I: parameter recovery. **A simulated PASS says nothing about hardware safety.** (11) Advanced; 8–14 h. (12) Optional real log.

**L22 Cognitive and embodied reasoning.** (1) Represent partial observation, object permanence and preconditions; expose a grounding failure with a falsifiable test. (2) E03, E05, E06, E14; prereq E02, R18, and a belief route. (3) Belief state, task planning. (4) T0 symbolic-geometric world, optional MuJoCo. (5) Small planner and belief update. (6) Plan trace. (7) Predict plan failure for a hidden object. (8) Automatic checks only for plan validity and preconditions; the research claim is reviewed. (9) Symbolic plan with geometric infeasibility. (10) No "cognition" certification exists. (11) Research; 15–30 h. (12) None.

**Paths by goal, not one sequence.** These are lab lists to expand through prerequisites, not requirements.

| Goal | Labs | First visible milestone |
| --- | --- | --- |
| Manipulation | L01, L02, L06, L07, L08, L11, L14, L18 | Your own FK matches the simulator |
| Mobile | L01, L03, L04, L05, L09, L10, L11, L13, L15 | Your own odometry node runs on replayed data |
| Perception | L01, L16, L17 | Project a known point to the right pixel |
| Robot software | L05, L12, L14, L15 | A tested node from a fresh clone |
| Robot learning | L04, L08, L20, L21 | A policy beating a declared baseline |
| Visuomotor policy | L16, L19 | A data audit that catches injected faults |
| Cognitive robotics | L11, L15, L22 | A falsifiable grounding failure |

### 1.8 Integrated capstone: Find, Navigate, Pick, Deliver, Recover

**Can MUR5e support it? In simulation, potentially, as an optional track; not as things stand on my setup.** The structure is right and the code is readable. The blocker is that I could not get past step 4.

| Module | Independent assessment | MUR5e today | Needed |
| --- | --- | --- | --- |
| **C1 Map and localize** | Map quality and localization error on a held-out route | **Exists, used.** Map server and AMCL in the mission launch; SLAM launch not run | Add metrics |
| **C2 Find the object** | Search and report pose with uncertainty; randomized location | **Missing.** Pose arrives in the goal | **Develop** |
| **C3 Choose a base pose** | Reachability and clearance on fixtures | **Exists, ran.** Optimizer returned a pose; scoring uses manipulability and path distance | Learner reimplements score |
| **C4 Navigate** | Reach goal in changed layouts | **Ran.** Goal reached in both runs | Changed-layout scenarios |
| **C5 Align and grasp** | Convergence from offsets; lift success | **Partial.** Servo aligned; the advance failed here; carrying relies on friction; colour-specific detection | **Diagnose the failure first**, then generalize |
| **C6 Deliver and place** | Placement error on a physical pose | **Not reached in my runs** | Verify |
| **C7 Recover** | Injected failures | **Ran on real failure.** It detaches and stows, then reports failure; does not retry | Add retries and re-localize |
| **C8 Learned skill** | Replace one scripted skill and compare with baseline | **Missing** | **Develop**, optional |
| **C9 Evaluate and report** | Reproducible protocol, reviewed | **Missing** | **Develop** |

**Recommended structure: two tracks.**

- **Track A, default: MuJoCo, no ROS.** Compose a diff-drive base and arm with a primitive-pad gripper, in primitive-collision rooms. Learners connect **their own** L03, L09, L11, L06, L17, L18 and L15 code. Composition compiles and is stable (1.2), but driving and manipulating it is untested. This track runs on modest machines and every line that matters is the learner's.
- **Track B, optional: MUR5e or a similar Gazebo stack on a machine with a GPU.** Learners replace one node at a time: first `TargetAcquisition` with real search, then the colour threshold, then recovery with retries. **Gate before authoring:** the unmodified mission must complete on a named reference machine at a stated rate over repeated runs, with exact commit and image. Consider forking at a fixed commit, since it depends on one maintainer.

**Grading.** Modules are scored separately, with oracle stubs replacing other modules so a failure is attributable. MUR5e's mock servers show this pattern works, and also show its limit. System success is k-of-n seeded runs on layouts the learner has not seen, with n and k fixed in advance. Reports are reviewed. **The capstone's automatic checks can support an L2-style implementation claim for named modules. L3 requires a reviewer.** Passing never implies hardware readiness. Physical versions, for example LeKiwi, are a separate project with their own safety review.

### 1.9 Assessment and PASS design

Existing C/M/I/T, L0–L4 and A0–A3 stay as they are. Old M02 and PY01 reports keep their narrow meaning. These are design rules, proposed for approval.

**Rules.**

1. **Oracle hierarchy.** Closed form, then exhaustive small case, then independent implementation, then simulator. Use simulator state as an oracle only for pure kinematics or a declared characterized model. Contact outcomes are experiments unless a success band has been validated.
2. **Separate correct from accurate.** A function can be right and its estimate still wrong. Do not fail a learner for model mismatch.
3. **Set tolerances from measured margins.** Run valid alternatives and known bugs before publishing, and keep a table per contract. 1.2 shows how a plausible tolerance fails valid Euler.
4. **Every contract ships its mutants.** The verifier must reject them in CI, and must accept at least two valid different solutions, which guards against over-fitting to one approach.
5. **Stochastic results use k-of-n, declared in advance with stated false-failure odds,** and a separate seed set from any learner tuning.
6. **Prediction before measurement.** Learner records a prediction file; its hash goes in the report. Whether it was right is not scored automatically. This records the practice without pretending it proves understanding.
7. **Scope in every report.** `I` evidence attaches to an objective set. A lab cannot raise a broad topic beyond its declared scope. This needs an engine change because of `lib/engine.ts:82`, and needs approval.
8. **`T` and open derivations stay human reviewed.** Without a reviewer the artifact is stored unreviewed and no L3 or L4 is awarded.
9. **Simulation claims are labelled.** Every PASS reads "in simulation, on this model". Nothing on it authorizes running hardware.

**Results contract, proposed `corelab-lab/2`.** A new schema alongside `/1`:

```json
{
  "schema": "corelab-lab/2",
  "contractId": "R04.fk-chain",
  "contractVersion": 1,
  "objectives": ["R04.spatial-chain"],
  "assistance": "A0",
  "sourceHash": "<sha256>",
  "testsHash": "<sha256>",
  "predictionHash": "<sha256 or null>",
  "envLockHash": "<sha256>",
  "seed": 12345,
  "tier": "T1",
  "checks": [{ "id": "seeded-poses", "passed": true, "worst": 2.1e-15, "tolerance": 1e-6 }],
  "passed": true,
  "at": "<ISO 8601>",
  "publicKey": "<PEM>",
  "signature": "<base64>"
}
```

This is the only shared interface. Implications to check: the report field in `lib/storage.ts` is limited to 5000 characters, backup restore validates through `validateLab`, and adding `/2` must leave `/1` validation, signatures and backup round trips unchanged. Runner requirements: separate process from learner code, result channel the learner's prints cannot forge, explicit timeout, no shell, and no execution from the web server. Honest limit: the owner of the machine can still edit everything. Locally inspectable checks provide study evidence, not proctoring.

**Scoped PASS summary.**

| Dimension | Automatic evidence | Limit |
| --- | --- | --- |
| C, M | Existing diagnostics, on improved forms per the v2 proposal | Labs add context, not credit |
| I | Contract checks and rejection of mutants | Only named objectives; A0 self-declared |
| Test design (PY07, T04) | Learner's tests reject broken implementations | Separate from "my program passes" |
| T | None | Reviewed unfamiliar task only. Delayed repetition is retention |
| System | k-of-n scenarios | Reports performance on stated layouts only |

### 1.10 Reproducibility, safety and risks

**Pinning.** T0 and T1: `uv` lockfile, MuJoCo version and model commit recorded in `envLockHash`. T2: image digest, currently `ros:jazzy@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617`; apt packages move inside the image, so publish a CoreLab image or record package versions. Third-party repositories at fixed commits, never vendored without a license check. CI runs every contract against reference solutions and mutants, without hardware.

| Risk | Evidence | Mitigation |
| --- | --- | --- |
| Heavy install stops beginners | 13.5 min packages and 5.5 GB for the full stack [T] | Nothing heavy before L12 or L13; L05 uses base image |
| Windows and macOS for T2 | Not tested. RoboStack lists Jazzy on all platforms, but its tracker shows open issues including Nav2 on Windows ([tracker mirror](https://issues.ecosyste.ms/hosts/GitHub/repositories/robostack%2Fros-jazzy/issues)) | T0 and T1 first; Docker for T2; test in the pilot and publish what works |
| Headless and GPU differences | TurtleBot3 launch shut down without a display [T]; MUR5e unresolved on software rendering [T] | Grade offline where possible; no rendering dependency in verifiers |
| Upstream change | LeRobot has 487 commits in six months | Pin; keep lessons independent of its internals |
| Single maintainer | MUR5e | Optional only |
| Model defects taught as truth | TurtleBot3 wheel behaviour [T] | Characterize each model and publish the card |
| Unverified grasp | 1.2 | Primitive gripper until shown otherwise |
| License of assets | UR meshes unresolved; `TODO` licenses in MUR5e | Link to upstream, do not redistribute |
| Evidence inflation | `engine.ts` topic-wide I [R] | Scope rule before new labs issue evidence |
| Forged or accidental pass | Short-circuit [T] | New runner |
| Reboot or crash loses local work | Happened during this round | Hand results to learners in durable project paths, not `/tmp` |

**Safety.** Simulation-only participation is complete and free. Each hardware option requires: power cut within reach, speed and torque limits, a watchdog, clear workspace, wheels off the ground or arm clamped for first runs, battery handling notes, and no people in range. A hazard table is reviewed first where a reviewer exists. No CoreLab PASS authorizes hardware operation. Unattended operation is out of scope.

**Backward compatibility.** Keep `corelab-lab/1`. New reports are additive. Old reports stay bound to their original scope. No old evidence is rewritten or reinterpreted.

### 1.11 Time and cost, with uncertainty

**Learner effort [E], at least ±50%, untimed.**

| Stage | Labs | Hours |
| --- | --- | --- |
| A Foundations | L01–L05 | 17–31 |
| B Core | L06–L11 | 36–62 |
| C Systems | L12–L15 | 28–48 |
| D Perception | L16–L17 | 14–24 |
| E Contact and learning | L18–L22 | 51–99 |
| Capstone Track A | | 30–60 |
| **Everything** | | **176–324** |

Nobody should do everything; a goal path is about a third to a half of this [E]. Excludes prerequisites, and compute waiting time in L19 and L20.

**Authoring effort [E], low confidence.** About 15–40 h per lab, including reference solution, mutants, tolerance table, troubleshooting and review. First two labs, 30–60 h, should mostly reuse the FK slot in the v2 first-100-hours plan rather than add to it. All 22: 400–800 h, so build in stages, and stop if pilots show no benefit. No time savings are claimed.

**Hardware cost.** Prices vary and exclude shipping, taxes and printing unless stated. I found no way to verify them at checkout.

| Option | Figure | Source | Confidence |
| --- | --- | --- | --- |
| Simulation only | $0 | | High; needs a capable computer |
| SO-101 follower parts | $121.94 | [SO-ARM100 README](https://github.com/TheRobotStudio/SO-ARM100), parts total | Medium: repository figure, no print cost |
| SO-101 pair parts | $229.88 | Same | Medium |
| OMX-AI | $343.85, 6–8 week lead time | [robotis.us listing](https://www.robotis.us/new-releases), through search; product page blocked my fetch | Low; earlier $299 announcement also exists |
| LeKiwi base only | $248–$251.50 | [LeKiwi BOM](https://github.com/SIGRobotics-UIUC/LeKiwi/blob/main/BOM.md) | Medium |
| LeKiwi with SO-101 pair | $482–$499 | Same | Medium; excludes printing |
| XLeRobot basic | about $660 | Author's README | Low; author's own figure |
| TurtleBot3 Burger | $783.50 | [Third-party guide](https://grabarobot.com/blog/robotis-turtlebot-dynamixel-price-guide-2026/), citing the store on 2026-07-30; EU listings differ | Low |
| OpenMANIPULATOR-X | $1,629.09 | Same guide | Low |
| Andino, linorobot2 | **Not priced** | BOM has links but no totals; I did not invent a sum | Unknown |
| MiR100 + UR5e | **Not investigated as a purchase** | Commercial industrial hardware; out of scope for learners | |

### 1.13 Recommendations for the final synthesis

1. Adopt tiers T0–T3, with hardware optional at every lab and no robot assumed.
2. Before issuing new lab evidence: replace the runner, add a scoped report schema and fix the topic-wide `I` effect. All need owner approval.
3. **Build only L01 and L02 first**, inside the v2 first-100-hours plan, then L03 to test the "simulation as experiment" design. Add L04 and L05 after looking at pilot results. Do not commit to all 22 labs.
4. Keep MUR5e optional, with the reproduction gate in 1.8. Ask someone with a GPU to run the unmodified mission and report rate, commit and hardware.
5. Pin to Jazzy and Harmonic; do not start new work on Humble.
6. Publish a short model card per simulator asset: measured wheel, actuator and contact behaviour.
7. Treat PASS as scoped and "in simulation".

**What I do not know.**

- Whether MUR5e's failure comes from the repository or my environment.
- Whether the shipped arm models can grasp with correct placement.
- Whether T1 and T2 work on Windows and macOS.
- Whether any of this improves learning. No learner has used these labs, so all effort figures and sequencing are hypotheses.
- Whether the composite in Track A is drivable and controllable. Only compile and stand-still stability are shown.
- Andino and linorobot2 behaviour: I only read them.

**Debate status.** No Codex material was read for this round. Accepted and rejected arguments begin in Round 2.

### 1.12 Curriculum-to-lab coverage matrix

Placed last because of its length.

**Treatment key.** `LAB` assessed in a lab. `RES+LAB` automatic core in a lab, the rest reviewed. `EX+U` independent exercise, then applied in a named lab without extra credit. `EX` independent exercise only. `U` used in a lab, not assessed there. `OPT` optional extension (`x` suffix). `RES` reviewed research path. `CAP` capstone. `HW` needs a physical build. `DEFER` no lab until a goal needs it. `—` none.

| ID | Topic | Pri | Treatment | Where | Note |
| --- | --- | --- | --- | --- | --- |
| M01 | Mathematical Basics | P0 | EX | — | Algebra, trig, units; no robot adds validity |
| M02 | Vectors | P0 | EX+U | L01 | Existing verifier stays; applied in L01 |
| M03 | Matrices | P0 | EX+U | L01 | Applied in L01 |
| M04 | Linear Algebra | P0 | EX+U | L06 | Rank applied to singular Jacobians |
| M05 | Calculus I | P0 | EX+U | L03 L04 | Accumulation bridge applied to odometry, integral action |
| M06 | Multivariable Calculus | P0 | EX+U | L06 | Jacobians applied |
| M07 | Differential Equations | P0 | EX+U | L04 L08 | Step-size stability applied |
| M08 | Probability | P0 | EX+U | L09 | Bayes applied |
| M09 | Statistical Foundations | P0 | EX+U | L09 L10 | Covariance applied |
| M10 | Optimization | P0 | EX+U | L06 | Least-squares IK step |
| M11 | Numerical Computing | P0 | EX+U | L06 | Conditioning applied |
| M12 | Rigid-Body Geometry | P0 | LAB | L01 |  |
| M13 | Advanced Optimization | P1 | EX | — | Used in MPC exercise; no robot needed |
| M14 | Advanced Probability | P1 | DEFER | — | No lab until a goal needs it |
| M15 | Lie Theory | P1 | OPT | L06x | Twist/PoE extension only |
| M16 | Advanced Mathematics | P2 | DEFER | — | No lab until a goal needs it |
| PY01 | Python Fundamentals | P0 | EX | — | Language or tooling skill; verify with its own tests |
| PY02 | Data Structures | P0 | EX+U | L11 | Graph search data structures |
| PY03 | Python Semantics | P0 | EX | — | Language or tooling skill; verify with its own tests |
| PY04 | NumPy | P0 | EX+U | L01 | Array shapes |
| PY05 | Scientific Python | P0 | EX | — | Language or tooling skill; verify with its own tests |
| PY06 | PyTorch Basics | P0 | EX+U | L19 | Framework for BC |
| PY07 | Testing & Debugging | P0 | LAB | L05 | Learner tests judged by broken implementations |
| PY08 | Research Programming | P0 | U | L19 L20 | Experiment scaffolding |
| PY09 | Performance | P1 | EX | — | Language or tooling skill; verify with its own tests |
| PY10 | Advanced Python | P2 | DEFER | — | Elective; no lab |
| CPP01 | C++ Fundamentals | P0 | OPT | L05x | Optional C++ node route |
| CPP02 | Memory Model | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP03 | Resource Management | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP04 | Classes & OOP | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP05 | STL & Algorithms | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP06 | Modern C++ | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP07 | Build Systems | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP08 | Debugging & Testing | P0 | EX | — | Language or tooling skill; verify with its own tests |
| CPP09 | Complexity & Performance | P1 | EX | — | Language or tooling skill; verify with its own tests |
| CPP10 | Concurrency | P1 | EX | — | Language or tooling skill; verify with its own tests |
| CPP11 | Numerical C++ | P1 | EX | — | Language or tooling skill; verify with its own tests |
| CPP12 | Advanced C++ | P2 | DEFER | — | Elective; no lab |
| ML01 | ML Problem Formulation | P0 | EX | — | Tiny datasets are more valid than robot data here |
| ML02 | Classical ML | P0 | EX | — | Tiny datasets are more valid than robot data here |
| ML03 | Generalization | P0 | EX+U | L19 | Leakage and evaluation applied to episodes |
| ML04 | Neural Networks | P0 | EX | — | Tiny datasets are more valid than robot data here |
| ML05 | Backpropagation | P0 | EX | — | Tiny datasets are more valid than robot data here |
| ML06 | Deep Learning Training | P0 | EX | — | Tiny datasets are more valid than robot data here |
| ML07 | Model Evaluation | P0 | EX+U | L19 | Leakage and evaluation applied to episodes |
| ML08 | Representation Learning | P1 | EX | — | Independent exercise; pulled by selected branch |
| ML09 | Transformers | P1 | EX | — | Independent exercise; pulled by selected branch |
| ML10 | Self-Supervised Learning | P1 | EX | — | Independent exercise; pulled by selected branch |
| ML11 | Generative Models | P1 | EX | — | Independent exercise; pulled by selected branch |
| ML12 | Advanced ML | P2 | DEFER | — | Elective; no lab |
| T01 | Linux | P0 | U | L05 | Used from first ROS lab |
| T02 | Git | P0 | U | L05 | Used from first ROS lab |
| T03 | Development Tools | P0 | U | L05 | Used from first ROS lab |
| T04 | Software Testing | P0 | LAB | L05 | Scored separately from PY07 |
| T05 | Reproducible Environments | P0 | LAB | L05 | Env lock must rebuild |
| T06 | Docker | P1 | U | L12 | Container route |
| T07 | Systems Performance | P1 | EX | — | Profiling exercise |
| T08 | Advanced Infrastructure | P2 | DEFER | — | Elective; no lab |
| R01 | Mechanics Foundations | P0 | U | L08 | Applied through gravity and torque |
| R02 | Robot Mechanisms | P0 | LAB | L03 | Differential-drive mechanism only |
| R03 | Rigid-Body Transformations | P0 | LAB | L01 |  |
| R04 | Forward Kinematics | P0 | LAB | L02 |  |
| R05 | Inverse Kinematics | P0 | LAB | L06 |  |
| R06 | Robot Jacobian | P0 | LAB | L06 |  |
| R07 | Rigid-Body Dynamics | P0 | LAB | L08 |  |
| R08 | Contact Mechanics | P0 | LAB | L18 | Friction with primitive pads |
| R09 | Actuators & Transmission | P0 | LAB | L04 | Saturation and rate limits |
| R10 | Mechanical Design Verification | P0 | HW | Hardware | Only meaningful on a physical build; reviewed |
| R11 | Floating-Base Dynamics | P1 | EX | — | Derivation exercise; no lab planned |
| R12 | Advanced Dynamics | P1 | EX | — | Derivation exercise; no lab planned |
| R13 | Advanced Locomotion | P1 | DEFER | — | No low-cost platform in scope |
| R14 | Dexterous Manipulation | P1 | OPT | L18x | Reviewed extension |
| R15 | Advanced Mechanics | P2 | DEFER | — | No low-cost platform in scope |
| C01 | Control Fundamentals | P0 | LAB | L04 |  |
| C02 | Dynamic Systems | P0 | EX+U | L04 | State form applied |
| C03 | PID Control | P0 | LAB | L04 |  |
| C04 | Linear Systems | P0 | EX | — | Analysis or small simulation; no robot required |
| C05 | LQR | P0 | OPT | L08x | LQR on simulated pendulum; needs expert review |
| C06 | State Estimation | P0 | LAB | L09 |  |
| C07 | Kalman Filtering | P0 | LAB | L10 |  |
| C08 | Sensor Fusion | P0 | LAB | L10 |  |
| C09 | Digital Control | P0 | LAB | L04 | Sample-rate and delay experiment only |
| C10 | Nonlinear Control | P1 | EX | — | Analysis or small simulation; no robot required |
| C11 | Model Predictive Control | P1 | EX | — | Analysis or small simulation; no robot required |
| C12 | Nonlinear State Estimation | P1 | OPT | L10x | EKF extension |
| C13 | Optimal Control | P1 | EX | — | Analysis or small simulation; no robot required |
| C14 | Whole-Body Control | P1 | DEFER | — | No lab until a goal needs it |
| C15 | Advanced Control | P2 | DEFER | — | No lab until a goal needs it |
| S01 | Simulation Fundamentals | P0 | LAB | L08 | Integrator and contact settings tested |
| S02 | MuJoCo | P0 | LAB | L08 | Integrator and contact settings tested |
| S03 | ROS 2 Fundamentals | P0 | LAB | L05 |  |
| S04 | Robot Description | P0 | LAB | L12 |  |
| S05 | ROS 2 Runtime | P0 | LAB | L05 |  |
| S06 | Hardware Integration | P0 | LAB | L14 | Mock hardware interface; real hardware reviewed |
| S07 | Robot Safety | P0 | LAB | L15 | Awareness from L04; fault injection graded in L15 |
| S08 | System Identification | P1 | LAB | L21 | Synthetic logs by default; never certifies hardware |
| S09 | Sim2Real | P1 | LAB | L21 | Synthetic logs by default; never certifies hardware |
| S10 | ROS 2 Control | P1 | LAB | L14 |  |
| S11 | Advanced Simulation | P1 | EX | — | Parallel simulation exercise |
| S12 | Advanced Robotics Software | P2 | DEFER | — | Elective |
| V01 | Digital Images | P0 | LAB | L16 |  |
| V02 | Image Processing | P0 | LAB | L17 |  |
| V03 | Camera Models | P0 | LAB | L16 |  |
| V04 | Camera Calibration | P0 | LAB | L16 |  |
| V05 | Feature Extraction | P1 | EX | — | Dataset exercises give cleaner oracles |
| V06 | CNN | P0 | EX | — | Dataset exercises give cleaner oracles |
| V07 | Image Classification | P0 | EX | — | Dataset exercises give cleaner oracles |
| V08 | Object Detection | P0 | OPT | L17x | Learned detector replaces colour mask |
| V09 | Object Tracking | P1 | EX | — | Dataset exercises give cleaner oracles |
| V10 | Segmentation | P1 | EX | — | Dataset exercises give cleaner oracles |
| V11 | Multi-View Geometry | P1 | EX | — | Dataset exercises give cleaner oracles |
| V12 | Depth Estimation | P1 | EX | — | Dataset exercises give cleaner oracles |
| V13 | 3D Perception | P1 | U | L17 | Depth back-projection |
| V14 | Visual Representation Learning | P1 | EX | — | Independent exercise; no lab planned |
| V15 | Vision Transformers | P1 | EX | — | Independent exercise; no lab planned |
| V16 | Video Understanding | P1 | EX | — | Independent exercise; no lab planned |
| V17 | Visual Odometry & SLAM | P1 | U | L13 | Learner configures and evaluates SLAM, does not write it |
| V18 | Vision Foundation Models | P2 | DEFER | — | Frontier; pull by research goal |
| V19 | 3D Neural Representations | P2 | DEFER | — | Frontier; pull by research goal |
| V20 | Advanced Perception | P2 | DEFER | — | Frontier; pull by research goal |
| RL01 | RL Fundamentals | P0 | EX | — | Tabular and small environments have exact answers |
| RL02 | Markov Decision Processes | P0 | EX | — | Tabular and small environments have exact answers |
| RL03 | Value Functions | P0 | EX | — | Tabular and small environments have exact answers |
| RL04 | Dynamic Programming | P0 | EX | — | Tabular and small environments have exact answers |
| RL05 | Model-Free Prediction | P0 | EX | — | Tabular and small environments have exact answers |
| RL06 | Model-Free Control | P0 | EX | — | Tabular and small environments have exact answers |
| RL07 | Function Approximation | P0 | EX | — | Tabular and small environments have exact answers |
| RL08 | Policy Gradient | P0 | EX | — | Tabular and small environments have exact answers |
| RL09 | Actor-Critic | P0 | EX | — | Tabular and small environments have exact answers |
| RL10 | PPO | P0 | LAB | L20 |  |
| RL11 | Off-Policy RL | P1 | OPT | L20x | SAC alternative to PPO |
| RL12 | RL Experimental Design | P0 | LAB | L20 |  |
| RL13 | Continuous Control | P1 | LAB | L20 |  |
| RL14 | Reward Engineering | P1 | LAB | L20 |  |
| RL15 | Curriculum Learning | P1 | DEFER | — | No lab planned |
| RL16 | Domain Randomization | P1 | LAB | L21 |  |
| RL17 | Imitation Learning | P1 | LAB | L19 |  |
| RL18 | Offline RL | P1 | DEFER | — | No lab planned |
| RL19 | Model-Based RL | P1 | EX | — | Small model-based exercise |
| RL20 | Hierarchical RL | P1 | DEFER | — | No lab planned |
| RL21 | Safe RL | P1 | OPT | L20x | Constraint-cost variant; reviewed |
| RL22 | Multi-Agent RL | P2 | DEFER | — | No lab planned |
| RL23 | Advanced Exploration | P2 | DEFER | — | No lab planned |
| RL24 | Meta-RL | P2 | DEFER | — | No lab planned |
| E01 | Sequential Decision Making | P1 | EX | — | Decision formulation |
| E02 | Planning Fundamentals | P1 | LAB | L11 |  |
| E03 | Planning Under Uncertainty | P1 | RES+LAB | L22 | Automatic checks only on the planning core; rest reviewed |
| E04 | Robot Skills | P1 | LAB | L15 |  |
| E05 | Task Planning | P1 | RES+LAB | L22 | Automatic checks only on the planning core; rest reviewed |
| E06 | Task & Motion Planning | P1 | RES+LAB | L22 | Automatic checks only on the planning core; rest reviewed |
| E07 | Imitation-Based Robot Policies | P1 | LAB | L19 |  |
| E08 | World Models | P1 | RES | — | Reviewed research path; compute and access vary |
| E09 | Object-Centric Representations | P1 | RES | — | Reviewed research path; compute and access vary |
| E10 | Vision-Language Models | P1 | RES | — | Reviewed research path; compute and access vary |
| E11 | Diffusion/Flow Action Policies | P2 | OPT | L19x | Visuomotor branch only |
| E12 | Vision-Language-Action Models | P2 | RES | — | Reviewed research path; compute and access vary |
| E13 | Long-Horizon Robot Learning | P2 | CAP | Capstone | Long-horizon evaluation host |
| E14 | Embodied Reasoning | P2 | RES+LAB | L22 | Automatic checks only on the planning core; rest reviewed |
| E15 | Advanced Embodied Intelligence | P2 | DEFER | — | Frontier |
| RS01 | Scientific Reasoning | P0 | U | all labs | Prediction before measurement |
| RS02 | Experimental Design | P0 | LAB | L20 | Protocol graded by review |
| RS03 | Statistical Inference | P0 | U | L20 | Interval reporting |
| RS04 | Experimental Reproducibility | P0 | U | L05 L19 | Reproduce from lockfile |
| RS05 | Error Analysis | P0 | U | L03 L09 | Systematic vs random error |
| RS06 | Paper Reading | P0 | RES | — | Reading skills; reviewed |
| RS07 | Scientific Writing | P1 | CAP | Capstone | Report; reviewed |
| RS08 | Literature Review | P1 | RES | — | Reading skills; reviewed |
| RS09 | Research Software | P1 | U | L19 L20 | Experiment code quality |
| RS10 | Advanced Research | P2 | DEFER | — |  |
| M17 | Spectral & Stable Least Squares | new | LAB | L06 | Candidate; SVD and damped solve |
| R16 | Sensors & Log Quality | new | LAB | L09 | Candidates |
| R17 | Trajectory Generation | new | LAB | L07 | Candidate |
| R18 | Motion Planning | new | LAB | L11 | Candidate |
| R19 | Manipulator Control | new | LAB | L08 | Candidate; joint-space scope only |
| R20 | Mobile Localization | new | LAB | L09 | Candidates |
| E16 | Robot Data Quality | new | LAB | L19 | Candidate |

## Round 2 — Response to Codex Round 1

Written after reading Codex Round 1 and its coordination checkpoint. I re-checked the MUR5e and manipulation claims below against source at the commits Codex cites. I re-cloned only for that. New runs in Round 1 were complete before I read Codex.

### 2.1 What each side adds

The two reviews agree on more than the labels suggest. Codex chose "D" and I chose "C shaped by B", yet both describe: ROS-free entry, separate arm and base, ROS only after the algorithm is tested, MUR5e as an advanced case study, and no unified robot abstraction. Codex's D explicitly excludes a "ROS-reinvention framework" and "universal simulator conversion service". **The disagreement over the letter is mostly naming.** I propose the synthesis describe the architecture directly instead of by letter.

**Evidence the sides hold that the other did not.** Codex performed no builds, runs or MuJoCo stepping; I did. Codex read test bodies, the optimizer and failure paths more closely than I did, and found things I missed.

### 2.2 Decisions on Codex's claims

| # | Codex claim | Decision | Evidence and reason |
| --- | --- | --- | --- |
| 1 | `TargetAcquisition` only checks a non-empty frame; pose comes from the caller, so "hardcoded forever" is too strong | **ACCEPT** | Same finding as my 1.3. Its wording is more precise than my "default goal". |
| 2 | Servo max-iteration exhaustion returns SUCCESS with a best-effort pose | **ACCEPT; I missed this** | `visual_servo_action.cpp:418-444`. A mission can continue after failed alignment. In my two runs the servo reached threshold (0.4 mm and 0.1 mm), so this path did not cause the observed aborts. |
| 3 | Missing images or no yellow can stay RUNNING with no overall deadline | **ACCEPT as source reading** | Consistent with the file; I did not exercise it. |
| 4 | `path_distance` is radial distance to the object, not a Nav2 path | **ACCEPT; corrects my 1.8** | `optimizer_node.cpp:339-344` uses `std::hypot` of candidate to target. README's `1/path_distance` misleads, and my capstone row "scoring uses manipulability and path distance" repeated it. It is a base-to-object distance. |
| 5 | Footprint check samples 21 points and misses interior obstacles | **ACCEPT** | Code samples boundary points (`num_samples = 5`, line 402). I did not reproduce Codex's arithmetic example. Good L11 or capstone test case. |
| 6 | `FailsWhenObstacleBlocksArm` does not assert failure | **ACCEPT** | The test's only assertion in that block is `ASSERT_TRUE(server_exists)` from my grep. It is one of the "passing" tests behind my finding 5, which strengthens that finding. |
| 7 | Payload attach is scene bookkeeping, no retention check; recovery can detach a real object | **ACCEPT** | Matches my 1.3. Recovery's blind detach matters; my table praised recovery as "ran as described", which is true but insufficient. |
| 8 | Do not treat TurtleBot3 plus OM-X as a working combined platform; `turtlebot3_manipulation` launch references absent files | **ACCEPT, confirmed statically** | The tree at `91492d7` and the current Jazzy branch contain `moveit_gazebo.launch.py` but no `gazebo.launch` or `empty_world` file. Like Codex, I did not run it. |
| 9 | First FK lab needs no MuJoCo, ROS or Docker | **ACCEPT; changes my L02** | Better for install burden. See 2.3. |
| 10 | Separate `corelab-practical/1`, with `mode`, model manifest, exposure and reviewer fields, and admissibility computed by policy | **ACCEPT over my `corelab-lab/2`** | A new name avoids implying a version upgrade of a strict schema. My `passed` and topic-free `objectives` shape was already scoped, but a computed policy is stricter. Keep my runner requirement from 1.9. |
| 11 | Do not treat "95% of 10 trials" as robustness | **ACCEPT, with a number** | Even 10 of 10 gives only about a 74% one-sided 95% lower bound on success rate under independence; 20 of 20 gives about 86%. |
| 12 | Independent monitors outside the executive; symbolic attachment must be labelled and excludes grasp competency | **ACCEPT** | Stronger than my module table. Adopted in 2.4. |
| 13 | Phase 0 known pose, Phase 1 camera estimation, separate claims | **ACCEPT** | Honest about what is not perception. |
| 14 | Four-axis X cannot reach arbitrary SE(3) | **ACCEPT; extend to OMX** | My default arm is OMX, 5 hinges [T], not X. Better, still not arbitrary SE(3). Tasks must declare allowed orientations. |
| 15 | Mock result is interface-only; "no mock-only runtime PASS" (P10) | **MODIFY** | Right for action servers and planners. My L05 replay uses real `rclpy` and DDS against a scripted publisher. Its claim, "node contract on replay", is neither mocked middleware nor runtime integration. Report `mode: replay`. |
| 16 | Do not maintain equivalent graded scenes in two simulators | **ACCEPT the rule; MODIFY its effect on my capstone** | Tracks A and B do not grade the same claim: A is integration of the learner's algorithms, B is ROS system integration. Build neither until the labs pilot. |
| 17 | Hardware reserves of $300–800, $200–700, $150–500 labelled as unpriced assumptions | **REJECT as the headline** | Honestly labelled, but repository BOMs give better figures: SO-101 $121.94, LeKiwi $482–$499 ([R], 1.11). Use those with their limits. **ACCEPT** the warning that integration, power and tipping are unpriced and that a cheap arm is not a drop-in. |
| 18 | Do not rely on model stepping or contact fidelity from the Menagerie | **ACCEPT; now measured** | My TurtleBot3 result (29%) is exactly this risk. Also note what Codex could not know: all six models load and step [T]. |
| 19 | Default TurtleBot3 navigation is provisional until a clean build | **ACCEPT and advance** | Now run once [T]: odometry and one Nav2 goal work, but the official launch fails with no display. |
| 20 | No MuJoCo graded against "the same model both estimator and verifier use" | **ACCEPT** | Same rule as my oracle hierarchy. FK is the exception, because no estimation occurs. |
| 21 | P04 merges time law and toy tracking on `dq/dt=u` | **MODIFY** | Plant is a good simplification; I adopt it. Keep trajectory (R17) and feedback (C01, C03) as separate contracts so a failure is attributable, even if taught together. |

### 2.3 Revised first five

Codex's numeric-only start is right for the first thing a learner touches. My L05 is still valuable and has run as a prototype, so I place it by goal rather than drop it.

| Order | Lab | Tier | Change from my Round 1 |
| --- | --- | --- | --- |
| 1 | L01 Frames | T0 | Adopt Codex's frame graph, typed errors and SE(2)-first fallback |
| 2 | L02 FK | **T0 only for the learner** | Parameter table and expected values are shipped as fixtures. MuJoCo is used **only in CoreLab's CI** to generate and cross-check them. No learner install. Optional viewer later. Planning claim: planar and spatial contracts stay separate |
| 3 | L03 Odometry | T0 graded; T1 experiment optional | Separate evidence for the optional comparison, per Codex |
| 4 | **Jacobian and IK subcontracts** (from L06, Codex P03) | T0 | Moved up for the manipulation path. Separate J and IK so slow convergence cannot erase a valid J |
| 5 | L04 Feedback, with toy time law as a linked contract | T0 | Adopts Codex's plant |
| Goal-dependent | L05 ROS node | T2-lite | First ROS step for software and mobile paths, with `mode: replay` |

Only 1 and 2 should be authored first, as both reviews say. Authoring range for those two: Codex 40–80 h, mine 30–60 h; say 30–80 h [E].

### 2.4 Revised capstone rules

Adopt: immutable task manifest; separate observed grasp state; object position, contact, velocity and dwell monitors unavailable to the learner's perception; explicit deadlines; recovery that selects stop, hold, stow or release based on state, never blind detach; symbolic attachment labelled as such; raw results with intervals.

Keep from mine: per-module scoring with stubs; a reproduction gate before any MUR5e authoring. The mission failure must be understood first.

**What remains of k-of-n.** A PASS needs a declared rule. Keep "all safety checks always, and at least k of a declared finite suite", state that it describes this suite only, and report the interval. No robustness language.

### 2.5 Answers to Codex's eight questions

1. **MUR5e perception, servo and grasp.** `target_acquisition.cpp` (no perception). `visual_servo_action.cpp:188` HSV range; depth sampling at 241–259; best-effort success at 418–444. Grasp: `payload_actions.cpp` scene only; I found no Gazebo attach by grepping the description, Gazebo and launch directories. **[T]** The servo reached threshold twice; the advance then failed; the object ended displaced. No grasp ever occurred in my runs. I make no physical grasp claim.
2. **Base placement.** It does not measure a navigation path (decision 4). Tests that would catch the rest: fixture with an interior lethal cell; absent and stale map fixtures; a scaled robot; a candidate reachable by Euclidean distance but sealed off from the route, checked by the planner. Currently none exist for these in what I read.
3. **Smallest artifact.** L01: a Python file and fixtures, NumPy only. Claim: narrow I for "rigid transforms as matrices" (M12, R03 scope), self-declared A0. C and M come from separately reviewed prompts. T: none automatically. No ROS, GPU or arm.
4. **Robots.** Several, by role; no single robot. OMX declares allowed grasp orientations; top-down picks at bounded height replace 6-DOF behaviour. Duplication avoided: T1 and T2 models are never graded for the same claim, and early grading uses no simulator.
5. **Verified versus inferred.** **Run:** MUR5e build, selected tests, two missions; six MuJoCo model loads; FK, J, odometry and PID prototypes; ROS replay harness; LeRobot install and 5 ACT steps; TurtleBot3 odometry and one Nav2 goal. **Read only:** Andino, linorobot2, SO-ARM100 hardware docs. **Not verified:** OMX and `open_manipulator` launches; any upstream CI status. Workflow files were read for distributions only.
6. **Compatibility with `lib/labs.ts`.** Do not touch that schema. New `corelab-practical/1` goes through a separate validator and new storage. Old reports keep narrow meaning, with no alias. No HTTP execution. Local-owner tampering is out of scope and stated.
7. **Held-out splits and reviewer.** Layouts, objects and seeds are in a suite the reference solution was tuned without; they ship locally, so they are "undisclosed before attempt" only, not secret. **A copied demonstration can pass the automatic system checks.** It cannot earn C, M or reviewed T. A qualified human reviewer, not yet identified, judges unfamiliar transfer; absent one, no L3.
8. **Licenses and BOMs inspected.** License file text read: `robotis_tb3`, `robotis_omx` per-model Apache; MUR5e `mir_description`, `ur_description`; Andino per package; SO-ARM100 and LeKiwi root or README badge only; LeKiwi BOM totals via its page. **Not inspected:** CAD, mesh provenance, datasets, weights. Unpriced: printing, shipping, tax, tools, integration, power, Andino and linorobot2 totals.

### 2.6 Corrections to my Round 1

- 1.8: "scoring uses manipulability and path distance" is wrong; it is radial distance (decision 4).
- 1.3: my MUR5e table gave too much credit to the recovery branch and tests; see decisions 6 and 7.
- 1.3: I said I "looked at" `turtlebot3_manipulation`, but listed only metadata. Decision 8 is the real finding.
- 1.0 finding 5 stands and is stronger.

### 2.7 Open disagreements and questions for Codex

1. **Capstone default.** I propose MuJoCo Track A for learners without ROS; Codex's capstone assumes the ROS profile. My evidence: MuJoCo composite compiles, TurtleBot3 Nav2 ran, OMX ROS unverified, and no combined Gazebo robot exists. Can you name a concrete combined ROS robot model that exists today, or should the first capstone stay separate tasks?
2. **Stage placement of L05.** Do you object to one simulator-free ROS node before the full ROS profile, given the measured base image of 1.32 GB and a few-second replay?
3. **Model cards.** Will you accept a required measured card for each simulator asset, given 29% MuJoCo odometry error against 0.7 mm in Gazebo on nominally the same robot?
4. **Runner integrity.** You describe the verifier without the forged-stdout case in 1.1. Do you agree the new runner must fix it, even though the local owner is out of scope?
5. **Arm.** OMX spans MuJoCo, ROS and LeRobot by source. Do you see a reason to prefer X, given X has four arm joints?

## Round 3 — Final position

Written after reading Codex Round 2. This is my last debate round. Nothing here authorizes implementation.

### 3.1 Evidence classes, now separated

Codex is right that lost scripts should not carry the same weight as reproducible results. From here on:

| Class | Meaning | Contents |
| --- | --- | --- |
| **Durable** | Script in 3.8, rerun this round at pinned commits, or independently reproduced | OMX FK with rotation; odometry against closed form; TurtleBot3 MuJoCo gap; OMX-F URDF against MJCF; forged stdout (Codex also reproduced it) |
| **Session record** | I ran it; logs gone or only partly kept. Do not use for thresholds | MUR5e two aborts and build times; SO-101 and OM-X grasp trials; pad gripper lift; composite model speed; ROS replay harness; PID margins; LeRobot smoke; EGL rate |
| **Session record, this round** | Logs still present locally, but single runs and not preserved in the repository | TurtleBot3 headless odometry and one Nav2 goal; OMX-F Gazebo run in 3.2 |

Before any threshold is frozen, the relevant measurement must be rerun from a committed script. Agreed with Codex.

### 3.2 New results that resolve open questions

**OMX-F in Gazebo runs [session record, this round].** `open_manipulator` Jazzy branch at `17efe42`. My earlier failure was my own 9 GiB limit with parallel compilation. With a sequential build of only the needed packages, 6 packages finished. Using a local copy of `omx_f_gazebo.launch.py` with `-s` added to `gz_args`, on a headless Gazebo:

- `arm_controller`, `gripper_controller` and `joint_state_broadcaster` were active.
- A `FollowJointTrajectory` goal returned `SUCCEEDED`.
- Joints reported 0.3000, 0.2000, 0.2000 against commands 0.3, 0.2, 0.2.

This shows that simulated controllers track a simple goal. It does not cover MoveIt, grasping or hardware. `open_manipulator_collision` was not rebuilt, so one package remains unverified.

**The exact variant lock Codex asked for [durable].** I compared `omx_f.urdf` from `xacro` at `17efe42` with `robotis_omx/omx.xml` at `d8344c0`, on 200 random poses, q in [−1, 1]⁵, relative to the joint 1 frame.

| Property | Result |
| --- | --- |
| Joint-frame position gap | **1.8e-16 m.** Link offsets and axes match |
| Joint limits | **Differ.** URDF ±2π for all joints; MJCF joint 2 is −2.094 to 1.571, and others are narrower too |
| Effort | **Differs.** URDF has `effort=1000`; MJCF has its own actuator limits |
| Gripper, inertia, friction | Not compared |

So: **OMX-F and `robotis_omx` are equivalent for FK and Jacobian work, and that is all I can claim.** Controls, limits and contact are not equivalent. Grading must use one declared limit table. "OMX" in my Round 1 meant `robotis_omx` in MuJoCo and OMX-F in ROS, and SO-101 is simply a different arm.

### 3.3 Decisions on Codex Round 2

| # | Codex point | Decision | Result |
| --- | --- | --- | --- |
| 1 | Position-only FK cannot certify a pose | **ACCEPT, demonstrated** | A 0.5 rad tool rotation error gives **1.3e-16 m position error** and 0.50 rad geodesic error (3.8). L02 PASS now requires position and rotation. Geodesic noise floor is about 4e-8 rad from `acos`, so use 1e-6 rad. |
| 2 | Odometry tolerance 1e-2 was not dimensioned, and can pass no motion on tiny fixtures | **ACCEPT** | My table mixed metres and radians. New contract below. |
| 3 | "Clamp without back-calculation" is not automatically a bug; PID checks need stated plant, horizon and band | **ACCEPT** | Test behaviour, not the recipe. L04's list is corrected in 3.4. |
| 4 | k-of-n has no known false-failure odds without assumptions | **ACCEPT** | My rule 5 in 1.9 said "with stated false-failure odds", which needs an assumed success rate and independence. It now reads: declared rule, raw results, interval, assumptions named. |
| 5 | My "stray `sys.exit` or debug print" overstated the verifier defect | **ACCEPT** | Crafted success output is needed. It fails on a plain exit. Fail-closed harness still required. Not a sandbox. Old evidence not invalidated. |
| 6 | LeRobot source is 0.6.2, not 0.6.1 | **ACCEPT** | I installed `lerobot==0.6.1` from PyPI and inspected source at `3f797de5`, which declares 0.6.2. My table merged them. |
| 7 | R10 is not "only meaningful on a physical build" | **ACCEPT** | Split: analytic design evidence as an exercise; physical verification as hardware. Supersedes my matrix row. |
| 8 | Replay evidence: cumulative totals do not determine a mixed-curvature path; check intermediate outputs | **ACCEPT** | Add a mixed-curvature replay and intermediate pose checks. Message drop tolerance applies only under stated conditions. |
| 9 | Drop third-party price snippets as decision-grade | **ACCEPT** | TurtleBot3, OM-X and OMX-AI become "not price verified". Keep only primary BOM subtotals, labelled as parts subtotals and not delivered robots. |
| 10 | Issue mirrors are not technical evidence | **ACCEPT** | RoboStack status becomes "unverified". |
| 11 | Link-only does not resolve asset rights | **ACCEPT** | UR5e mesh status stays unresolved; no generalization from UR20 or UR30. |
| 12 | Same-arm continuity is not established by naming | **ACCEPT, now scoped** | 3.2. |
| 13 | Docker optional, with a named native Linux profile | **MODIFY** | Agree it is not a prerequisite for CoreLab or T0 and T1. But every T2 result I have comes from Docker and **none from a native Jazzy profile**. So Docker is the only tested route today. Publish native as a second route only after someone tests it. |
| 14 | L05 is goal-dependent | **ACCEPT**, already in 2.3 | |
| 15 | GPU is a comparison condition, not a fix; check frame, orientation, limits, scene first | **ACCEPT** | My Round 1 implied environment first. The log's `NO_IK_SOLUTION` points at kinematics at least as much. Investigate in that order. |
| 16 | Servo's alignment error is an internal metric | **ACCEPT** | Stop quoting 0.4 mm as accuracy. |
| 17 | Composite compile and stand-still prove little | **ACCEPT** | Gate in 3.5. |
| 18 | Writing a NumPy ray caster adds a sensor oracle to maintain | **ACCEPT as a cost** | Still simpler than 36 mesh rays at 2× real time, but not free; include in the gate. |
| 19 | Report name: Codex now accepts my `corelab-lab/2`; I accepted its `corelab-practical/1` | **Settle: `corelab-lab/2`** | Both call the name immaterial. Keep `mode`, runner, oracle, world and model identity, scope, completion and seed references. Separate validator. `/1` untouched. Rich artifacts as bounded metadata plus local manifest. |

### 3.4 Corrected contracts

**L02 FK.** PASS: position within 1e-6 m and rotation geodesic within 1e-6 rad, over seeded poses across varied axes, zero offsets and tool transforms, plus hand fixtures with no simulator. MuJoCo stays a CI cross-check. Parameter extraction is CoreLab's job and needs its own review.

**L03 odometry.** Domain stated: |v| ≤ 0.3 m/s, |ω| ≤ 2 rad/s, T = 5 s, track 0.16 m, 500 steps. Durable results (3.8):

| Implementation | Position error at 500 steps | Heading error | Position error ratio on halving step |
| --- | --- | --- | --- |
| Exact arc | 2.0e-14 m | 1.3e-13 rad | round-off |
| Midpoint | 4.8e-6 m | 1.3e-13 rad | 4.00 |
| Euler | 2.9e-3 m | 1.3e-13 rad | 2.00 |
| Swapped wheels | 1.4 m | 2.6 rad | 1.00 |
| No motion | 1.0 m | 2.8 rad | 1.00 |

Base contract: position within 1e-2 m and heading within 1e-6 rad **in this domain only**, with every fixture moving at least about 1 m or 2 rad, so a no-motion stub cannot pass. An optional accuracy-order contract uses the refinement ratio. The ratios shown separate first and second order cleanly.

**L04 PID.** Declare plant, reachable reference, initial state, horizon, and a steady-state band. Checks: command never exceeds the limit; settles within the band on a reachable step; flipped sign detected; recovery after a long saturation bounded by a declared overshoot limit. Any anti-windup method meeting the spec passes. Unreachable reference: must stay bounded and report.

**L05 replay.** Mixed-curvature sequence; intermediate poses checked; varied start and joint order; declared policy for gaps, resets and out-of-order stamps. `mode: replay`.

### 3.5 Remaining disagreement and how to decide it

**Integrated backend.** Codex: choose after a bounded spike, keep ROS as a separate software branch. Me: MuJoCo first. Evidence now: Nav2 base works, OMX-F arm works, each separately. **No combined robot exists in either simulator with driving and manipulation demonstrated.** I withdraw "default Track A" as a decision, and propose this gate instead. It runs only after the L01 and L02 pilot.

| Check on the same declared pick task | MuJoCo composite | Gazebo composite |
| --- | --- | --- |
| Base tracks a path in a declared band with learner-style odometry | Unknown | Unknown |
| Range sensing at or above real time on a mid-range CPU machine | 36 mesh rays too slow; primitive world untested | TurtleBot3 lidar ran |
| Contact pick with independent retention monitor, at a declared rate over a finite suite | Pad gripper, single trial | Not shown; MUR5e failed before contact |
| Cold install, time and size | Small; measure | About 5.5 GB measured for the full stack |
| Author effort to reach all of the above | Measure | Measure |

Time-box each at about 8–16 h [E]. **Choose the one that passes; if both, take the smaller install and lower effort; if neither, teach separate arm and base tasks with no combined capstone.** That last outcome is acceptable. ROS Nav2 and MoveIt stay as a software branch in any case, and do not claim to replace the algorithm labs.

**Other open items for the owner or a later pilot.** Exact lab ordering after L02. Who the qualified reviewer is. Authoring capacity. Whether MUR5e step 4 can be explained.

### 3.6 Answers to Codex's Round 2 questions

1. **Yes.** See 3.1 and the script in 3.8.
2. **Yes, all four.** Decisions in 3.3 and contracts in 3.4.
3. **Lock:** `robotis_omx` at `d8344c0` with MuJoCo 3.17.0, OMX-F at `17efe42`. Equivalence covers joint-frame kinematics only. Backend gate: 3.5.
4. **Yes for both,** with the caveat in decision 13.
5. **Three evidence levels:**

| Level | Evidence required | Claim allowed |
| --- | --- | --- |
| Symbolic attachment | Scene object or weld; `attachment: symbolic` in the report | Planning and task sequencing only |
| Simulated retention | Monitor outside the executive sees object velocity match the gripper over a declared dwell, contacts on both pads, and stable release in a zone; no planning-scene input. Stale sensor, timeout and cancel must each stop motion and be reported in a fault suite | "Simulated grasp on this model" |
| Reviewed hardware grasp | Fresh supervised trial, device and calibration identified, reviewer named, safety review first | That device and object set only |

6. **Yes.** Primary subtotals only. Parts subtotal, stated inclusions, no delivered-robot implication.

### 3.7 Final recommendations for the synthesis

**Architecture.** Describe it directly: ROS-free numerical entry; optional MuJoCo; optional ROS 2 Jazzy and Harmonic; optional hardware; separate arm and base; shared result contract; no robot abstraction layer.

**Do first, in order, with owner approval.**

1. Fail-closed runner and scoped `corelab-lab/2` design, with `/1` and backups unchanged.
2. L01 and L02, NumPy only for learners, MuJoCo in CI only. Commit the rerun scripts. Author 30–80 h [E].
3. Pilot with real learners. Do not commit to more labs before this.
4. Then L03; then Jacobian and IK or L04 or L05 according to the first chosen goal.
5. Backend gate in 3.5 only if a capstone is still wanted.

**Do not do yet.** All 22 labs, a capstone, MUR5e lab authoring, more than one integrated simulator, hardware purchasing guidance beyond itemized BOM links, or automatic I for broad topics.

**MUR5e.** Optional advanced case study. Valuable for reading: BT structure, base placement scoring flaws, mock test limits, best-effort success, and a real planning failure to diagnose. No lab on it until the unmodified mission is reproduced at a stated rate.

**Platforms.** TurtleBot3 for ROS navigation with a CoreLab headless launch. OMX-F for ROS arm work. `robotis_omx` in MuJoCo for T1 arm. Small authored MJCF for T1 base, with per-asset model cards. SO-101, Andino, LeKiwi as optional hardware options listed by itemized BOM. LeRobot pinned for optional later data and ACT work. Not selected: `turtlebot3_manipulation` as turnkey (missing launch references); linorobot2 and Andino simulators as defaults (not run here).

**Standing limits.** No measured learning benefit exists. All hours are estimates. Windows and macOS are untested for everything beyond CoreLab itself. A simulation PASS never authorizes hardware.

**Corrections to Round 1 that a reader should apply.**

- 1.0 finding 6 and 1.1: needs crafted output, per decision 5.
- 1.0 finding 7 and 1.11: parts subtotals only; third-party prices withdrawn.
- 1.2 and L03: tolerance and table replaced by 3.4.
- 1.3: LeRobot versions per decision 6.
- 1.5: OMX equivalence limited per 3.2.
- 1.9 rule 5: per decision 4.
- 1.12 R10: per decision 7.
- L02, L04, L05: replaced by 3.4.
- 1.8 Track A default: withdrawn for the gate in 3.5.

### 3.8 Durable rerun

Reproduces the OMX FK and rotation test, odometry table and TurtleBot3 gap. `python rerun.py <robotis_mujoco_menagerie at d8344c0>`, with `mujoco==3.17.0` and NumPy.

Output this round:

```text
mujoco 3.17.0
FK OMX link5 worst (pos m, geodesic rad): None (1.3e-16, 4.2e-08), sign (5.1e-01, 3.1e+00), deg (5.5e-01, 3.1e+00), order (4.2e-01, 4.2e-08), tool_rot (1.3e-16, 5.0e-01)
  arc 2.0e-14 1.3e-13 | 8.0e-14 2.2e-13 | ratio 0.24
  mid 4.8e-06 1.3e-13 | 1.2e-06 2.2e-13 | ratio 4.00
  euler 2.9e-03 1.3e-13 | 1.4e-03 2.2e-13 | ratio 2.00
  nomove 1.0e+00 2.8e+00 | 1.0e+00 2.8e+00 | ratio 1.00
  swap 1.4e+00 2.6e+00 | 1.4e+00 2.6e+00 | ratio 1.00
TB3 burger cmd 4 rad/s 10 s: wheel 2.47 rad/s; wheel-angle distance 0.796 m; true 0.622 m
```

```python
# CoreLab labs review: durable rerun. Usage: python rerun.py <robotis_mujoco_menagerie checkout>
import math,os,sys;import numpy as np,mujoco
R=sys.argv[1];O=mujoco.mjtObj;print('mujoco',mujoco.__version__)
def q2R(q):
    w,x,y,z=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def aa(a,t):
    K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]]);return np.eye(3)+math.sin(t)*K+(1-math.cos(t))*K@K
m=mujoco.MjModel.from_xml_path(os.path.join(R,'robotis_omx/scene.xml'));d=mujoco.MjData(m)
e=mujoco.mj_name2id(m,O.mjOBJ_BODY,'link5');rng=np.random.default_rng(1)
def fk(q,mut=None):
    p=[];b=e
    while b: p.append(b);b=m.body_parentid[b]
    T=np.eye(4)
    for b in reversed(p):
        A=np.eye(4);A[:3,:3]=q2R(m.body_quat[b]);A[:3,3]=m.body_pos[b]
        if m.body_jntnum[b]:
            j=m.body_jntadr[b];a=q[m.jnt_qposadr[j]]-m.qpos0[m.jnt_qposadr[j]];a={'sign':-a,'deg':math.radians(a)}.get(mut,a)
            J=np.eye(4);J[:3,:3]=aa(m.jnt_axis[j],a)
            if mut=='order': T=T@J@A;continue
            A=A@J
        if mut=='rot_only_wrong': A[:3,:3]=A[:3,:3]
        T=T@A
    if mut=='tool_rot': T=T@np.block([[aa([1,0,0],.5),np.zeros((3,1))],[np.zeros((1,3)),np.ones((1,1))]])
    return T
out={};hinges=[j for j in range(m.njnt) if m.jnt_type[j]==3][:5]
for k in (None,'sign','deg','order','tool_rot'):
    wp=wr=0;rng=np.random.default_rng(1)
    for _ in range(100):
        q=m.qpos0.copy()
        for j in hinges:q[m.jnt_qposadr[j]]=rng.uniform(*m.jnt_range[j])
        d.qpos[:]=q;mujoco.mj_kinematics(m,d);T=fk(q,k);wp=max(wp,float(np.linalg.norm(T[:3,3]-d.xpos[e])))
        Rr=T[:3,:3].T@d.xmat[e].reshape(3,3);wr=max(wr,math.acos(min(1,max(-1,(np.trace(Rr)-1)/2))))
    out[str(k)]=(wp,wr)
print('FK OMX link5 worst (pos m, geodesic rad):',{k:('%.1e'%a,'%.1e'%b) for k,(a,b) in out.items()})
def arc(p,dl,dr,L):
    x,y,t=p;ds,dt=(dl+dr)/2,(dr-dl)/L
    if abs(dt)<1e-9:return x+ds*math.cos(t),y+ds*math.sin(t),t
    r=ds/dt;return x+r*(math.sin(t+dt)-math.sin(t)),y-r*(math.cos(t+dt)-math.cos(t)),t+dt
def mid(p,dl,dr,L):
    x,y,t=p;ds,dt=(dl+dr)/2,(dr-dl)/L;return x+ds*math.cos(t+dt/2),y+ds*math.sin(t+dt/2),t+dt
def eul(p,dl,dr,L):
    x,y,t=p;ds,dt=(dl+dr)/2,(dr-dl)/L;return x+ds*math.cos(t),y+ds*math.sin(t),t+dt
def nomove(p,dl,dr,L):return p
def swap(p,dl,dr,L):return mid(p,dr,dl,L)
def exact(v,w,T,t0):
    if abs(w)<1e-12:return v*T*math.cos(t0),v*T*math.sin(t0),t0
    return v/w*(math.sin(t0+w*T)-math.sin(t0)),-v/w*(math.cos(t0+w*T)-math.cos(t0)),t0+w*T
def errs(f,N):
    P=A=0;L=.16;T=5.
    for v,w,t0 in [(.2,0,0),(.2,.5,0),(.2,-.7,.9),(-.15,.4,2.),(0,1.,-1.),(.3,2.,.3)]:
        h=T/N;p=(0.,0.,t0)
        for _ in range(N):p=f(p,(v-w*L/2)*h,(v+w*L/2)*h,L)
        o=exact(v,w,T,t0);P=max(P,math.hypot(p[0]-o[0],p[1]-o[1]));A=max(A,abs(math.atan2(math.sin(p[2]-o[2]),math.cos(p[2]-o[2]))))
    return P,A
print('ODOM speeds<=0.3 m/s, |w|<=2 rad/s, T=5 s, L=0.16 m: worst (m, rad) at N=500/1000; refinement ratio')
for n,f in [('arc',arc),('mid',mid),('euler',eul),('nomove',nomove),('swap',swap)]:
    a,b=errs(f,500),errs(f,1000);print(' ',n,'%.1e %.1e | %.1e %.1e | ratio %.2f'%(a+b+(a[0]/max(b[0],1e-15),)))
m=mujoco.MjModel.from_xml_path(os.path.join(R,'robotis_tb3/scene_turtlebot3_burger.xml'));d=mujoco.MjData(m)
b=m.body_jntadr[mujoco.mj_name2id(m,O.mjOBJ_BODY,'wheel_left')];vi=m.jnt_dofadr[b];qi=m.jnt_qposadr[b]
for _ in range(500):mujoco.mj_step(m,d)
x0=d.qpos[:2].copy();q0=d.qpos[qi];d.ctrl[:]=4.
for _ in range(5000):mujoco.mj_step(m,d)
print('TB3 burger cmd 4 rad/s 10 s: wheel %.2f rad/s; wheel-angle distance %.3f m; true %.3f m'%(d.qvel[vi],(d.qpos[qi]-q0)*.033,np.linalg.norm(d.qpos[:2]-x0)))
```

Claude has completed Round 3 and will not edit Codex files or any final synthesis.

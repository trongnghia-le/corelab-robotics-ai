# CoreLab V2 roadmap execution inventory

Owner: Claude (backend/content). Started 2026-11-02 from baseline `3c0793b` (26 objectives, 22 families + bridge, 164 practice items, kits L01–L04/L06, 218 tests). Instructions: `CLAUDE_FULL_ROADMAP_PROMPT.md`. Coordination: `CLAUDE_BACKEND_HANDOFF.md`.

## Completion rule

A lab counts as **foundation implemented** only when it has: a versioned objective inside an existing curriculum topic, an original practice family (≥ 6 items, two genuinely different routes) with an independent test oracle, a stdlib-only manual self-check kit (works under `python -O`, author fixture with valid alternatives and named mutants), teaching coverage (lesson or V2 bridge), honest roadmap metadata, an AI review by a fresh reviewer with no remaining blocker/major, and passing lint/typecheck/content/V2 validation/tests. Subcontracts that need ROS, a physics engine, a device or human review are listed in the roadmap entry's `unavailable` field and are **not** claimed. A lab is only called **complete** if nothing in its section 9 scope is unavailable.

## Process per lab

1. Author subagent (Sonnet): family `Xnn.v1.json`, kit `Lnn-*.v1.py` + samples + fixture + vitest wrapper, optional bridge, and a registration spec `scratchpad/reg/Lnn.json`. Disjoint files.
2. Integration lead registers objective/catalog/kit/roadmap/manifest (serial; shared files).
3. Fresh reviewer subagent (Sonnet): reviews family + kit, writes the independent oracle `tests/v2/oracles/Xnn.ts`. Blocker/major → author fixes → re-review.
4. Approve review record, run gates (exit codes), commit locally (owned files only).

## Inventory

| Lab | Prior labs | Objective (topic) | Family | Kit | Group | Environment-dependent subcontracts (not claimed) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L05 ROS replay node | L03 | S03.replay-node | X23 | L05-replay | B3 | Real DDS/rosbag replay, QoS, TF2 runtime | foundation implemented (B3) |
| L07 Trajectories | L02 | M05.trapezoid-profile | X24 | L07-trajectory | B1 | Jerk/torque limits, robot execution | foundation implemented (B1) |
| L08 Dynamics/control | L04, L06, L07 | R07.pendulum-model | X25 | L08-dynamics | B4 | Physics-engine cross-check, torque hardware | foundation implemented (B4) |
| L09 Localization | L03 | C06.grid-bayes | X26 | L09-localization | B1 | SLAM, real sensor logs, simulator runs | foundation implemented (B1) |
| L10 Kalman/fusion | L03 | C07.linear-kalman | X27 | L10-kalman | B1 | EKF/UKF variants, real sensor fusion | foundation implemented (B1) |
| L11 Search/planning | L01 | E02.grid-astar | X28 | L11-planning | B1 | Sampling-planner completeness, arm C-space variant | foundation implemented (B1) |
| L12 Description/TF | L01, L02 | S04.urdf-chain | X29 | L12-description | B3 | ROS TF2 / robot_state_publisher runtime | foundation implemented (B3) |
| L13 Navigation | L03, L11 | C10.path-follow | X30 | L13-navigation | B4 | Nav2/ROS physics runs, changed-layout runs, AMCL | foundation implemented (B4) |
| L14 Interfaces/MoveIt | L06, L11, L12 | S10.mock-interface | X31 | L14-interfaces | B5 | ros2_control/MoveIt smoke, real controller, hardware | foundation implemented (B5) |
| L15 Executive/safety | none | S07.watchdog-executive | X32 | L15-executive | B2 | Safety certification, real E-stop, BT library runtime | foundation implemented (B2) |
| L16 Camera/calibration | L01 | V04.calibration-residual | X33 | L16-camera | B2 | Device calibration, real images | foundation implemented (B2) |
| L17 Visual alignment | L04, L06, L16 | V03.visual-servo-step | X34 | L17-alignment | B4 | Rendered/physics simulation, real camera | foundation implemented (B4) |
| L18 Contact/grasp | L04 | R08.friction-grasp | X35 | L18-grasp | B3 | Physics-sim contact, hardware grasping | foundation implemented (B3) |
| L19 Data QA/imitation | none | RL17.bc-qa | X36 | L19-imitation | B2 | LeRobot datasets, robot data, generalization claims | foundation implemented (B2) |
| L20 RL experiment | L04 | RL06.tabular-update | X37 | L20-rl | B3 | Simulator RL training, protocol human review | foundation implemented (B3) |
| L21 Identification | none | S08.parameter-fit | X38 | L21-identification | B2 | Physics-backend identification, sim-to-real | foundation implemented (B2) |
| L22 Cognitive reasoning | L11, L15 | E03.belief-plan | X39 | L22-reasoning | B4 | Human review of open interpretations, TAMP | foundation implemented (B4) |

Objective ids above are planning names; the authored registry entry is authoritative.

## Other remaining items

| Item | Status |
| --- | --- |
| API: form `title`, due-review `sourceId` (additive) | done in M0 |
| Generalized V2 bridges (`content/v2/bridges/<id>.v1.md`) | done in M0 |
| Roadmap `unavailable` subcontract list (additive, optional) | done in M0 |
| Per-family independent oracle registry `tests/v2/oracles/` | done in M0 |
| Lesson/bridge coverage for new objectives | Every new objective has a lesson or bridge; R05 IK bridge `planar-2r-ik` (`6a44f2e`); R02 odometry bridge `diff-drive-arc-odometry` (C/M commit) because `/lessons/R02` teaches mechanisms/DOF |
| C/M forms and disjoint review pools beyond Frames/FK | F-ODOM/RV-ODOM (R02.exact-arc) and F-JIK/RV-JIK (R06.planar-jacobian, R05.planar-ik) approved after AI review; other new objectives have practice + kit only (no C/M form yet) |

## Log

- M0 (2026-11-02): baseline lint/typecheck/content/V2/tests all exit 0, 218 tests. Infrastructure milestone in progress.
- M0 committed as `558420b` (API title/sourceId, bridges, roadmap `unavailable`, oracle registry). Oracle registry later split into `registry.ts` + `index.ts` to fix a circular import.
- B1 (L07, L09, L10, L11): authors and fresh reviewers on Sonnet; four authors were interrupted by a usage limit and resumed. Reviews: L07 approve-with-minor → minors fixed → approve; L09 kit changes-required (reversed kernel, single wrap) → fixed → approve; L10 approve-with-minor → minors fixed → approve; L11 approve-with-minor → minors fixed (oracle re-run passes). Independent oracles X24/X26/X27/X28. Gates in a clean worktree of the staged commit on top of Codex's UI commits: lint, typecheck, validate:content, validate:v2, tests 229/36 files, V2 build + 10 V2 browser flows, default build + 9 legacy flows — all exit 0.
- B2 (L15, L16, L19, L21): reviews — L15 approve-with-minor (fixture runtime cut from ~190 s to ~15 s before review; minors fixed); L16 approve-with-minor → minors fixed → approve; L19 approve-with-minor → minors fixed; L21 kit changes-required (cond threshold unpinned, constant-u misconception uncaught) → fixed → approve. Bridges task-executive-watchdog, pinhole-calibration, episode-qa-bc, least-squares-identification. Independent oracles X32/X33/X36/X38. Clean-worktree gates: lint, typecheck, validate:content, validate:v2, tests 237/40 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0. An author accidentally re-ran an old script that rewrote the committed L11 samples file; `git diff` showed no change and the script was quarantined.
- B3 (L05, L12, L18, L20): L05 approve-with-minor plus one major (bridge example reproduced an X23 key) → fixed (new example, anonymised/shuffled cores against gaming, near-miss frame ids) → approve; L12 kit major (XML-safety tests too weak although the gate itself was sound) → fixed (security cases, documented limits) → approve; L18 family major (prompt showed 3.9/5.1 while inputs held 3.924/5.124) → fixed → approve; L20 approve-with-minor → minors fixed. The L18 finding led to a prompt/inputs scanner run at every registration and a rule in the author/reviewer briefs. L05 stays ROS-free: DDS/rosbag/QoS/TF2/ROS clock remain unavailable. Clean-worktree gates: lint, typecheck, validate:content, validate:v2, tests 245/44 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- B4 + L14 (L08, L13, L14, L17, L22): L08 approve-with-minor (one remediation number corrected after both reviewer and author recomputed it); L13 approve-with-minor (one reviewer claim was checked by the lead and found wrong, so not applied; bridge wording fixed); L14 kit major (endpoint samples unenforced) → fixed → approve; L17 and L22 bridge majors (worked example identical to an item) → fixed → approve; L22 samples exceeded the parser's JSON nesting limit of 48 → deep plans kept kit-only. The repeated bridge giveaway led to a bridge rule in both briefs. A reviewer-written oracle had an unused parameter that failed lint in the clean worktree; fixed before commit. Clean-worktree gates: lint, typecheck, validate:content, validate:v2, tests 255/49 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0. All 17 remaining roadmap labs now have a reviewed foundation; environment-dependent subcontracts stay listed as unavailable.
- R05 bridge (`6a44f2e`): `planar-2r-ik` bridge added first in R05.planar-ik `learn`; its self-check line corrected after review.
- C/M expansion: authors (Sonnet) wrote F-ODOM/RV-ODOM and F-JIK/RV-JIK; registered review-pending; fresh reviewers wrote `tests/v2/oracles/cm-ODOM.ts` (RK4 integration, rigid-body solve, circumcentre) and `cm-JIK.ts` (finite-difference Jacobian, circle–circle IK). ODOM: F approve-with-minor, RV changes-required (two pool C items repeated form items, one went beyond the objective, `/lessons/R02` did not teach odometry) → new `diff-drive-arc-odometry` bridge, replaced items, headings switched to kind `angle` → two re-review rounds → approve. JIK: changes-required (two prose scenario numbers wrong, edge targets mirrored the R05 bridge, minor cues/typos) → fixed → approve-with-minor (A/B status-mix difference and some 3-option fields accepted). The C/M oracle harness now accepts a choice conclusion (option prefix) and checks every other option is rejected. Reviewer probes: ODOM 165 (0 false accept/reject after the intended `angle` change), JIK 148 (100 false-accept probes rejected, 48 valid forms accepted). Known residual: published X12 v3 still links `/lessons/R02`; needs X12 v4.
- C/M gates (clean worktree of the staged commit on `81d9ca9`): lint, typecheck, validate:content, validate:v2, tests 259/49 files, V2 build, default build + 10 legacy flows — all exit 0. V2 flows: first full run 9/10 (an unscoped heading locator in Codex's `e2e/v2-interface.spec.ts` matched two elements); isolated reruns on HEAD and on the change passed, and two further full runs passed 10/10 — recorded as a flake for Codex, not edited. A kit wrapper first exceeded vitest's default 5 s test timeout under load; `testTimeout` raised to 60 s.

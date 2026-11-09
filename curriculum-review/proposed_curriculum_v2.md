# CoreLab curriculum v2 — independent audit and proposed plan

**Status: proposal for human review; no curriculum v2 implementation authorized or performed.**

Baseline: `38b6a1d8f0baae9a753882185da7bd4430d14277`, CoreLab, 2026-10-30. Synthesis completed 2026-10-31 (Asia/Ho_Chi_Minh). Repository: [trongnghia-le/corelab-robotics-ai](https://github.com/trongnghia-le/corelab-robotics-ai). Both reviewers completed four rounds before this synthesis. [Codex review](codex_review.md) and [Claude review](claude_review.md) preserve the arguments, corrections and earlier positions. This synthesis uses their **final** positions; earlier withdrawn proposals are not current disagreements.

> Progress is measured by what you can independently explain, implement, and verify — not by how many videos you watch.

## 1. Executive summary

Keep the broad community map and every original topic/evidence identity. Replace the expectation of one long compulsory sequence with a default guided beginning, placement checks and goal-specific projects. Repair assessment validity before expanding the catalog. Preserve C/M/I/T, L0–L4, A0–A3, local-first operation, signed evidence and immutable assessment versions.

The map has 169 topics, but only 31 authored lessons/diagnostics and two narrow implementation verifiers. It is a promising learning system and catalog, **not 169 fully assessed courses**. Existing L1 evidence is narrow; a dot-product lab does not prove all vector competence. Existing T1 marks spaced repeat performance, not unfamiliar transfer. Reading, videos and AI solutions establish neither independent implementation nor broad mastery.

Propose seven additional identities, subject to approval: spectral/stable least squares, sensors, trajectories, motion planning, manipulator control, mobile localization, and robot-data quality. Stage them after two assessment pilots; do not commission seven lessons at once. Add missing integration, trigonometry, covariance, sampling and cognitive/HRI outcomes within named existing scopes. Remove no original IDs. Group overlapping study activities without merging scores or importing broader credit.

A complete conservative planning DAG below has **176 identities, 319 hard edges, no missing references and no cycles**. It retains independent topic identities and most baseline dependencies; it deliberately differs from Claude's smaller navigation-unit graph. These are coherent planning projections, not proof of optimal ordering. Readiness alternatives and capability-based gates are future policies, not current functionality.

Confidence is high in the repository findings, medium in curricular organization and low in hour forecasts or optimal thresholds. Neither reviewer measured improved learning or time savings. Human approval, expert review and bounded pilots are required before implementation.

## 2. Current strengths and weaknesses

Evidence: `corelab/curriculum_graph_v1.json`, `content/lessons/`, `content/assessments/`, `content/practice/`, `content/assessment-metadata.v1.json`, `lib/engine.ts`, `lib/assessment.ts`, `lib/reviews.ts`, `lib/weaknesses.ts`, resource registries and lab contracts. Counts refer to the baseline, not proposed materials.

| Observed strength | Practical limitation |
| --- | --- |
| 169 IDs and 310 prerequisite edges span math, programming, robotics, control, perception, RL, embodied intelligence and research | 31 lessons/diagnostics; 138 topics have overviews only. Validation of an overview is not completeness of instruction. |
| Local progress, assistance tracking, versioned attempts, signed local lab artifacts | Signatures protect provenance/integrity under the local trust model; they cannot prove unaided authorship or defeat the local owner. |
| Separate verified and provisional learning | L2 has supported contracts only for M02 dot and PY01 mean; L3/L4 automatic certification is unavailable. |
| Every authored lesson has a structured activity and rubric | All 31 diagnostics share one critical C choice, three M numbers and one ungraded T response. All correct C answers occupy index 0; 30 choices are binary. Distractors are often implausible. |
| Explicit ≥80% and critical-item rule | Four objective items give only 0/25/50/75/100, so passing requires four correct. This is not a broad mastery test. |
| Mistake-driven practice, seen-variant protection and honest bank exhaustion | 42 targeted questions in seven banks; targeted success cannot stand in for a full diagnostic or implementation. |
| 28 source-verified videos; interactive and diagram support | 27 topic mappings, including 25 authored lessons; eight distinct demos map to 13 topics. Only 14 authored lessons have a local demo or illustration; 17 have neither. A reachable video is not a reviewed exact-topic teaching sequence. |
| Topic-level 1/3/7/21-day reviews, unresolved weaknesses retained | Schedule is a heuristic. Historic mastery can coexist with a current gap; the recommender does not yet model scope-specific current readiness. |

Concrete gaps: M01 does not operationally teach needed trigonometry; M05 lacks the integration bridge used by M07; M04 does not teach spectral tools needed for later stability/least squares. Motion planning, bounded trajectories, sensing/data quality and mobile localization lack explicit assessable coverage. Quaternion and pseudoinverse terminology already appears, but mention is not operational instruction. Do not falsely label it wholly absent.

The M08 die question rejects `1/3` and `0.3333` despite no precision instruction; its tolerance is 1e-5. ML02 and ML05 derivative prompts omit their loss conventions; RL02's wait reward is not in its prompt. R07 **q2** omits its angle reference. These are prompt/format validity concerns, not evidence that the underlying lesson answers are necessarily wrong. Fix future versions; do not rewrite historical keys.

The recommender currently offers authored lessons, checks prerequisite L1 and excludes P2 even when pinned. It proposes a next introductory activity rather than certifying a lifelong pathway. A later failure can leave historic L1 intact while an affected dependent remains eligible. Improve present-readiness guidance without erasing attainment.

## 3. Additions, removals, groupings and reordering

No original ID or historical evidence is deleted, renamed, aliased into a broader competency, or automatically downgraded. A new assessment version may broaden the same topic only with explicit scope; old versions retain their original claims. A new ID is useful when coherent independent teaching, remediation and downstream demand justify its cost. It is not the only honest way to add scope.

| Working ID | Proposed bounded outcome | Decision, benefit and cost |
| --- | --- | --- |
| M17 | Eigenvalues/eigenvectors, stability interpretation, SVD/conditioning and stable least squares | Strong content need; separate identity practical because M04 already has narrow evidence. Library SVD is allowed; do not require implementing an SVD algorithm. Numerical review needed. |
| R16 | Sensor units/frames, timestamps, bias/noise, calibration and log quality | Medium confidence in separate ID; prevents sensor data from being treated as ground truth. Avoid a full sensors survey before a first project. |
| R17 | Path versus timed trajectory; bounded velocity/acceleration profiles | Strong MAN need; begin with one-dimensional timing, then an arm path. Extra authoring and limit checks. |
| R18 | Configuration space, collision checking, PRM/RRT and feasibility limits | Strong gap; supports MAN/MOB/TAMP. Requires robust geometry tests; do not promise completeness or near-optimality for a finite RRT run. |
| R19 | Joint-space tracking, torque limits and model mismatch; later task-space/contact control | Strong MAN need; contact and impedance claims require specialist review. No hardware authorization. |
| R20 | Wheel/odometry model, localization uncertainty and recovery from ambiguous observations | Strong outcome need; medium confidence in placement. Default projection uses a particle-filter route; Kalman-based route has different requirements. |
| E16 | Demonstration schemas, episode boundaries, synchronization, leakage and dataset quality | Medium-low confidence as separate ID; existing-data QA first. Simulator collection/teleoperation are optional variants, with extra cost. |

Named bridges, not additional IDs: **M01** algebra/trig/units; **M05** integration/accumulation before ODEs; **M09** covariance and uncertainty; **C09** sampling/aliasing/delay/filtering; **M15/R04/R06** scoped twists/PoE where needed; **V04/M11/V17** nonlinear least squares; **ML11/RL10** relevant information theory; **S07/E14** HRI, privacy, shared autonomy and grounding. Introductory spatial FK uses a transform chain; PoE is an extension.

Candidate study groups include PY07/T04, M09/RS03, C02/C04, C06/C07, ML03/ML07, and RL05/RL06. A common project can avoid repeating definitions while separate objective tags, attempts, contract versions and PASS scopes remain. For perception, boxes, masks, classification and representation evaluation share infrastructure but have different failure modes; do not silently merge V08/V10 or related scores.

Defer advanced material until a goal needs it: advanced probability, language internals, deployment, floating-base/contact control, research perception/RL and frontier embodied models. Keep useful PY10/CPP12/T08/S12 artifacts accessible as electives. **Reject blanket archiving based on “Advanced” in a title.** Generic catch-all nodes can become navigational reading registries after their concrete objectives are placed elsewhere; retain identities/history and searchable artifacts. E13 can host long-horizon capstone evaluation without pretending it is a complete autonomous course.

Reorder entry safety ahead of integration; discrete search before RL-dependent planning; simple analytic IK before numerical IK; PID tuning before full state-space theory; basic behavior cloning before transformers/diffusion; optimal-control foundations before MPC. Keep Python and vectors partly parallel. T02, testing, reproducibility and scientific reasoning begin with the first artifact rather than as a long prerequisite block.

## 4. Corrected prerequisite structure

The explicit DAG in Appendix A is the **canonical synthesis projection**. Reconstruct it by taking v1 prerequisites, applying exactly the replacements below, and adding the seven rows. All 169 original nodes remain active identities. This gives 29 replaced original rows plus seven candidates, 319 edges and maximum depth 13 edges. Full retention means this is not comparable to counting only grouped navigation units; fewer edges alone is not an educational objective.

| Original ID | Replacement hard prerequisites | Scope/reason |
| --- | --- | --- |
| M11 | M03, M05, PY04 | NumPy-based numerical lab variant; manual numerical reasoning can start earlier. |
| R02 | M01 | Mechanism literacy does not need a mechanics course first. |
| R03 | M12 | Frames do not require mechanisms. |
| R04 | R03 | Elementary spatial-chain FK; advanced algebra is pulled when needed. |
| R05 | R04 | Analytic planar scope. Numerical IK additionally needs R06 and M17. |
| R07 | R01, M06, M07, R04 | Lagrangian route; Jacobian useful context, not a universal gate. |
| C01 | M05 | Toy-plant feedback entry; plant-specific mechanics as needed. |
| C02 | C01, M07, M03, M06 | State-space and linearization; spectral stability deferred to C04. |
| C03 | C01 | Tuning toy PID first; stability analysis additionally uses C02/C04 and sampling C09. |
| C04 | C02, M17 | Spectral/linear-system analysis, not just state-space notation. |
| C05 | C04 | LQR algebra; optimization context helpful, not an entire M10 gate. |
| C08 | C07, R03 | Estimation and frame alignment replace actuators. Sensor timestamp competence still required. |
| C09 | C01, M05, M11 | Chosen sampled/filter lab; elementary aliasing preview can occur earlier. |
| C13 | C05, M10 | Optimal-control/trajectory-optimization foundations. |
| C11 | C13, M13 | MPC after optimal-control and constrained-optimization scopes. |
| S04 | R03 | URDF/frame exercise independent of a ROS installation. ROS variant adds S03; FK validation adds R04. |
| S05 | S03 | Python runtime route; CPP01 only for C++ variant. |
| S06 | S05, R09, S07 | Mock integration with runtime, actuator limits and safety awareness. |
| S07 | none | Entry awareness; hardware-specific work needs further approved review. |
| V11 | V04, M17 | Stable least-squares geometry variant. |
| RL09 | RL08, RL03, RL05 | Policy gradient, value and TD foundations for actor-critic. |
| RL14 | RL02 | A reward loophole can be explored before full experimental-design study. |
| RL17 | RL01, ML06 | Basic behavior cloning first; DAgger/interactive variants add RL02 capabilities. |
| E01 | RL02 | Continuous-control course is not intrinsic to decision fundamentals. |
| E02 | PY02 | Deterministic graph search does not need MDP/control. Numeric costs use M01 readiness. |
| E04 | PY07 | Software skill contracts/state machines. Reaching needs R04, plant/controller variant adds control/simulation, learned options add RL. |
| E06 | E05, R05, R18 | Symbolic, IK and geometric feasibility all explicit. |
| E07 | RL17 | Baseline imitation policy; transformer/generative branches pull ML09/ML11. |
| E08 | RL02, ML06 | Small learned model and shooting/CEM. No PPO gate; advanced actor-critic world-model variant adds RL09. |

Unlisted edges remain conservative v1 recommendations, **not all newly proven necessary**. There are transitive edges and some tool/context-heavy baseline paths still awaiting scope review. Acyclicity does not establish semantic correctness. Advanced dynamic programming/control need their full objective-specific mathematics even if an introductory preview can be offered early.

A hard edge must name the scoped task it enables: mathematical capability, safety, actual tool variant, or procedural/evidence validity (for example a held-out split before a generalization claim). Helpful textbook order is soft. Do not require all of Kalman filtering for a particle filter, or PyTorch for framework-neutral mathematics. Current AND-only topic prerequisites cannot express alternative capabilities; do not advertise such an engine as implemented. Start with a few high-impact probes rather than hundreds of expiring gates.

Claude's final projection was independently reparsed: **176 rows, 119 live study units, 193 hard and 32 soft edges**. Its grouped/deferred rows differ from this all-identity graph. Its default R20 retains C07 as a conservative choice; this synthesis uses Bayesian/measurement prerequisites for the particle-filter route. Preserve that substantive disagreement; do not mix the graphs or their hour closures.

## 5. Common foundation and specialized learning paths

Use a community map plus an opt-out guided default. Placement checks shorten known material; they are not a permanent lock. The default beginning is M01 readiness, M02 alongside PY01, then M03/PY04 when shapes are understood, and M12 → R03 → a small R04 FK artifact. Embed T02, PY07/T04, RS01 and S07 awareness at the first relevant artifact. Teach missing readiness before claiming the FK milestone. No requirement to finish every P0 topic or an 80–140-hour block first.

| Goal | Early bounded outcome | Later path anchors and capstone |
| --- | --- | --- |
| SYS: robotics software | Tested publisher/subscriber or mock state machine | T01/T02, PY07, S03/S05, S04, S06/S07; C++ ownership/performance only when the artifact needs it. Capstone: fresh-clone mock driver with timeout, logs and failure recovery. |
| MAN: manipulation | Correct planar FK, then spatial-chain FK with tool offset | R05/R06, R17/R18, R07/C03/R19; contact R08/R14 and E05/E06 as needed. Capstone traces collision-free path → timed limits → tracking → reviewed grasp/contact extension. No-contact reaching is a valid earlier milestone. |
| MOB: mobile robotics | Odometry with declared frames and uncertainty | R16/R20, E02/R18, C09/C08 as selected, S03/S06 and S07. Capstone: simulated navigation/localization with changed layout, dropout and recovery; legged R11/R13/C14 optional. |
| PER: perception | NumPy image conventions and a calibrated projection | V02/V03/V04, M17/V11/V13; learned branch ML05/V06 and evaluation. Capstone: held-out geometry/perception failure analysis; SLAM V17 adds its estimation/numerical capabilities. |
| RLL: robot learning | Evaluated small policy against a known baseline | RL01–RL09 as needed, RL12/RS02 protocol, either model-free or model-based branch. PPO/SAC are alternatives selected by the task. E11 diffusion is optional. |
| RLLV: visuomotor policies | Held-out demonstration-data QA plus a small BC baseline | E16, RL17/E07, V06/ML08; ACT/transformers and E11/ML11 only for selected branch. E12/VLA is research extension with compute/access budget, not compulsory. |
| COG: cognitive robotics | Explicit belief/grounding failure with a falsifiable test | E03/E05, selected E09/E10/E14, S07/RS02; inspect partial observation, object permanence, action preconditions, grounding and shared autonomy. Reviewed research path, thin content today; no automatic “cognition” certification. |

These are waypoint plans, not complete prereq lists. Expand the canonical graph for the chosen variant and author missing scope first. Most advanced nodes have no lesson/verifier today. Simulator, operating system, GPU and framework requirements belong to a specified lab; CoreLab itself remains the cross-platform local learning application. Simulation success does not certify real hardware. A general community path must not inherit one learner's Linux/GPU setup as mandatory.

## 6. Learning methods by topic

Each row in section 12 assigns one of six profiles plus a specific application. Apply a profile only to that row's stated scope; a profile is a reusable teaching/assessment design, not evidence that the topic is complete.

| Profile | Learning sequence | Correctness evidence and transfer |
| --- | --- | --- |
| MAT | Predict from a diagram → manipulate → explain notation/assumptions → reconstruct one derivation → compute fresh case | Independent analytic/property/numerical check. New representation or assumption for transfer. Code only if algorithm implementation is an objective. |
| CODE | Trace state/ownership → minimal failing program → define contract → implement from a blank file → test/debug | Boundary, invalid-input, property and selected mutation tests with an independent oracle. Transfer to a new failure or contract, not copy the worked function. |
| DYN | Predict motion/error → declare frame/state/units → derive model → simulate → perturb parameters/step size | Exact simple-case/energy/geometric oracle, refinement and sensitivity checks. Changed plant/convention for transfer; never hardware certification. |
| DATA | Inspect data/provenance → declare split → derive narrow estimator/loss → fit baseline → inspect errors | Leakage-safe held-out evaluation, uncertainty and failure slices. Transfer to a defined distribution shift. A training curve alone cannot pass. |
| PLAN | State/graph/constraint visualization → hand trace → implement → exhaustive small-case/feasibility comparison | Validate costs, reachability and infeasibility. Transfer after changed obstacle, state, reward or precondition; stochastic success is not a proof. |
| RESEARCH | Claim/evidence/assumption table → selected primary reading → small reproduction → falsification attempt | Qualified human reviews protocol, artifact, limitations and unfamiliar application. No automatic proof/design/research certification. |

Video-first can be the default offering where useful, never a compulsory watch quota. Pause, predict, change a variable and explain with the visual hidden. Keep a text/diagram fallback. Do not prescribe all activity types for every node, a universal word cap, arbitrary watch percentage or a rigid learning-style label. Practice testing and spacing have supporting evidence; CoreLab's exact sequence remains a hypothesis. [Dunlosky et al.](https://doi.org/10.1177/1529100612453266), [Freeman et al.](https://doi.org/10.1073/pnas.1319030111).

Reuse vector/frame/gradient primitives before adding demos. Prioritize model bridges: M10 lesson `(theta−3)^2` has stable step-size bound 1 while demo `0.5*x^2` has bound 2; both are correct for their curvature. C01 lesson integrator and demo first-order plant have different steady-error behavior. Label the plant/model before comparing. V01 CNN and RL02 Q-learning are previews, not complete basic-image or MDP instruction.

## 7. Curated resources and visualization decisions

Point-in-time checks: all 28 registered source pages and YouTube oEmbed endpoints returned HTTP 200 with matching titles/channels in the independent audit. This establishes identity/availability then, not instructional completeness, license to redistribute, duration, captions or region access. Preserve original links/attribution; no copied video/book assets or AI summaries substituting for sources.

| Scope | Primary reference / video source | Assignment and limit |
| --- | --- | --- |
| M01–M06/M17 | Existing 3Blue1Brown mappings for intuition; local equations and fresh tasks | M06 gradient video does not fully teach vector-output Jacobians. Check exact segments editorially; no invented timestamps. M17 uses standard spectral/SVD examples with declared numerical conventions. |
| M03/M04/M17 | [MIT 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/) | Authoritative historical course with lectures/exercises for maps, systems and eigenvalues. Select relevant material and separately review numerical SVD scope. |
| PY01–PY03 | [MIT 6.0001 Python](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/) | Established introductory lecture source; language/tool details are historical, so test current-version examples before authoring. |
| PY04/PY05 | [NumPy beginner guide](https://numpy.org/doc/stable/user/absolute_beginners.html) | Official array/shape/indexing reference; use one fresh axis/broadcast task and loop oracle, not a full-page reading quota. Pin lab versions. |
| CPP foundations and systems electives | [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) | Current living reference for interfaces, resources and concurrency; assign a small relevant rule set. It is not a complete beginner course or formal language standard. Preserve credible CppCon mappings as optional demonstrations; exact lecture fit still needs review. |
| M07 | [MIT 18.03SC Differential Equations](https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/) | First-order numerical methods and phase portraits fit the topic; course page verified in this synthesis. Select a small unit, not the whole course. |
| M08/M09 | [MIT 6.041SC Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/) | Conditional probability/Bayes and worked exercises. Replace M08's calculus source reference; source is reliable but present mapping is wrong. |
| R03–R07/R17/R19 | [Modern Robotics author course/video supplements](https://modernrobotics.northwestern.edu/) and [book page](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) | Motion, FK, Jacobians, dynamics, trajectories and control. Start planar/transform-chain; PoE and space/body Jacobians need explicit convention/readiness. |
| E02/R18/E06 | [LaValle, Planning Algorithms](https://lavalle.pl/planning/) | Discrete search, C-space and sampling chapters support distinct units; geometric planning is not contingent on first learning RL. |
| ML fundamentals | [Dive into Deep Learning preliminaries](https://d2l.ai/chapter_preliminaries/index.html) | Tiny data/math/autodiff and baseline tasks before large models. Framework-specific code is a variant. |
| V01/V06+ | [Stanford CS231n 2017 syllabus/video links](https://cs231n.stanford.edu/2017/syllabus.html) | Credible historical fundamentals; V01 pixel/dtype/axis tasks come before classification lectures. Not a current-model survey or all CV. |
| C02/C05 | [MIT Underactuated prerequisite FAQ](https://underactuated.csail.mit.edu/Spring2024/faqs.html), [LQR notes](https://underactuated.csail.mit.edu/lqr.html) | Targeted dynamics/control reading. Do not make C++ universal; check stabilizability/detectability conditions for the chosen LQR theorem. |
| RL10 | [Spinning Up PPO](https://spinningup.openai.com/en/latest/algorithms/ppo.html) | Clip objective and actor-critic implementation. Clipping is not guaranteed monotonic improvement; advantage normalization is an ablation, not an essential algorithmic correctness rule. |
| RL12/RS02 | [Agarwal et al., rliable](https://agarwl.github.io/rliable/), [Henderson et al., AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/11694) | Variability, evaluation and comparisons; no universally correct seed count. IQM appropriate for some method comparisons, not mandatory for every tiny single-task lab. |
| S03/S05 | [ROS 2 Humble tutorial route](https://docs.ros.org/en/humble/Tutorials.html), [Jazzy tutorials](https://docs.ros.org/en/jazzy/Tutorials.html) | Pin an OS-compatible maintained distribution when authoring. Jazzy fetch hit an Anubis access-denied page in this synthesis: do not label it accessibility-verified. Python/C++ examples are separate routes. Do not silently change all links just because another distro is newer. |
| Frontier E/V/RL and COG | One exact primary paper/artifact per claim, chosen at authoring | Existing broad laboratory indexes are discovery sources, not a finished curated lesson. Model versions, licenses, access and compute are unverified until selected. Avoid expensive from-scratch training as a generic requirement. |

Potential visualization queue: extend 3D frames/manipulability and PID saturation; prototype phase portrait/Kalman covariance only if those pilots need them. Each visual needs mathematical tests, accessible alternatives, a prediction prompt and an explicit scope. Do not build a visualization for every topic or award mastery for moving sliders.

## 8. Assessment blueprints and explicit PASS criteria

**Current policy stays unchanged in this audit.** Any future change needs owner approval, new contract versions, compatibility tests and transparent labels. Preserve all C/M/I/T dimensions, L0–L4 levels and A0–A3 records. A0 = none; A1 = conceptual hint; A2 = specific hint/example; A3 = supplied solution. Helpful AI tutoring is assisted practice; it is not retroactively A0. Later independent evidence must be fresh and recorded honestly.

Proposed manifest: topic ID, scope/objective IDs, applicable dimensions, contract and oracle versions, expected formats/tolerances, critical failures, task/form identity, seed and exposure history, assistance, source/report hash, reviewer and limits. An old report remains bound to its old narrow scope. Backup/restore currently references curriculum v1; any migration must retain v1 interpretation, validate references/signatures and round-trip existing progress. Never map old evidence to a broader v2 PASS by topic alias.

| Proposed claim | Explicit evidence gate | Limit |
| --- | --- | --- |
| L0 / no verified scope yet | No qualifying independent evidence for the claimed scope | Does not mean the person knows nothing; use placement rather than assume a deficit. |
| Ready for named activity, not a mastery level | Short A0 check of the exact prerequisite capability; critical safety/evidence requirements satisfied | No arbitrary whole-topic expiry; diagnosis can be repeated on a sound fresh probe. |
| L1 scoped C/M | Predeclared adequate objective coverage, all critical checks, independent fresh form and per-applicable-dimension threshold | Pilot starting form where both apply: 5 C + 5 M, ≥4/5 in each and every critical item correct; each critical objective probed in at least two distinct ways. Extend form if coverage needs it. Not validated reliability or a universal item count. |
| L2 scoped implementation | L1 plus A0 implementation artifact, all specified ordinary/boundary/invalid/property checks and selected wrong-implementation mutations rejected by the test suite | Only implemented scope counts. Partial/random passing, known sample reproduction or a signature alone is insufficient. |
| L3 unfamiliar transfer | L2 for relevant implementation scope, delayed fresh retention and qualified human review of a genuinely unfamiliar task/derivation | No reviewer: artifact stays unreviewed, current verified level remains; no automatic L3. |
| L4 research contribution | Qualified review of reproducible critique/extension, provenance, baselines, uncertainty and limits | Not paper reading, generated prose or a high quiz score. |

Applicable-dimension policy is a **future engine proposal**. M may be inapplicable to a pure tooling contract; do not invent counting arithmetic to fill it. Where no implementation is relevant, do not fabricate a coding task to satisfy L2: leave that claim unawarded until an approved level policy explicitly defines it. Scope-level design must retain the architecture and avoid creating an easier route to broad mastery.

For MAT/DYN, numeric checks support declared procedures, not proofs. Expression equivalence needs a domain; sampling positive x cannot distinguish `abs(x)` from x, and `x/x` differs from 1 at zero. Never use unrestricted evaluation of learner input. For CODE, use independent expected outputs, nonzero/unequal/invalid cases, properties and genuine mutations; test-design competency requires tests of the learner's tests, not merely passing the program. DATA requires split isolation before fit; PLAN requires a small exhaustive/feasibility oracle; RESEARCH/open transfer requires human review.

Use undisclosed-before-attempt, versioned, **locally inspectable** checks. Do not imply hidden tamper-proof tests. A0 is self-declared. State the qualified meaning of “verified”: passed the named checks with independence attested, or explicitly human-reviewed. Local-owner edits are outside the anti-cheat guarantees.

No universal 12-item form, 24-hour failure lockout, permanent solutions ban or compulsory three distractors. Three options means one key and two distractors; the cited study does not require three distractors. Randomize options and avoid a critical concept resting on one binary cue. [Rodriguez (2005)](https://doi.org/10.1111/j.1745-3992.2005.00006.x).

Worked examples remain available; a later assessed task changes meaningful structure/representation, not only constants. Immediate corrective practice is welcome; delay/exposure policy is explicit, with new forms. A nominal 80% is a starting policy, not scientific proof of competence. Four-item dimensions still require 4/4. In an ideal independent equal-difficulty model, a 90%-accurate learner passes four of four with probability .6561; this illustration is not real test reliability. Pilot false failures, false passes, accessibility, reviewer agreement and effort.

## 9. Misconceptions, diagnosis and remediation

Section 12 lists a topic-specific misconception; profiles define how to test it. Replace label-only feedback with: error evidence → likely cause → minimal counterexample → targeted practice → fresh A0 correction → delayed check. Avoid diagnosing conceptual failure from an ambiguous prompt or rounding error.

Examples: M02 dot output scalar versus vector → draw/project then test orthogonal residual; M03 order → transform one basis point in both orders; M08 inverse conditional → base-rate tree and Bayes computation; M11 small residual → ill-conditioned perturbation; R03 inverse/frame → round trip; R04 relative versus absolute angles → nonzero unequal links; C03 saturation → clipped step response and anti-windup; ML03 leakage → seeded train-only preprocessing; RL02 reward/terminal convention → explicit table; E06 symbolic feasibility → unreachable grasp counterexample.

A failed **relevant, trustworthy** readiness check should affect suggestions: prioritize repair, warn on the affected scope and offer a confirmatory fresh diagnostic. Preserve historical attainment. Do not globally withdraw all readiness after one binary answer, assisted practice, unrelated skill failure or M08-style false failure. A safety-critical failure stops the affected hardware activity until reviewed; ordinary exploration can remain available with a provisional label. Current engine does not yet implement this policy.

## 10. Spaced repetition and retention

Keep existing 1/3/7/21 topic reviews until a justified replacement is approved. Keep earlier due dates and unresolved weaknesses when a partial success would hide them. Separate targeted repair from whole-topic mastery. Future fresh-but-equivalent retrieval checks can revisit a derivation, a bug, a boundary case or a miniature model. Transfer must change representation, assumptions or method; new numbers alone are retention.

Use a learner-adjustable daily budget (for example 10–15 minutes as a planning choice), prioritize active goals/critical gaps, and make overdue workload visible. Do not schedule every old quiz daily. Longer tails can reduce scheduled load but may miss forgetting; neither 365 days nor automatic expiry is evidence-backed for every skill. Spacing benefits depend on task and retention horizon. [Cepeda et al. (2008)](https://doi.org/10.1111/j.1467-9280.2008.02209.x).

Workload illustration only: 31 topics reviewed every 21 days at an assumed six minutes each is 8.86 minutes/day at steady state, excluding intake/lapses. For skill scheduling use active skills, not topic count: S skills × assumed event minutes / terminal interval, plus initial stages and failures. No measured 30–45-minute saving exists. Pilot retrieval quality, backlog and delayed unfamiliar-task performance before building a skill scheduler.

## 11. Effort estimates and trade-offs

Measured metadata: 28 lessons at 55 minutes and three at 40 total **1,660 minutes (27 h 40)**. This is authored metadata, not observed learning, coding, review or mastery time. Video duration and learner active time were not measured. Never compare it to an expanded v2 program as a time-saving result.

Use objective-level planning ranges only: 1–3 hours for an introductory scoped activity, 3–8 for a mathematical/coding unit and 8–20 for a bounded integration project, plus review. Broad topic labels may contain many such units; ranges cannot be summed across all 169 as equal courses. Prior knowledge, debugging, access, compute and reviewer availability dominate variance.

Claude models full goal closures at roughly 300–620 hours, with at least ±40% uncertainty. Those are scenario sizes based on its different navigation graph, scopes and capstone leaves, not validated estimates for this DAG. The shared 80–130-hour set is an intersection of that model, not a compulsory starter block. This synthesis does not adopt a universal program-hour promise or savings percentage.

Likely benefits: skip demonstrated prior knowledge, remove false gates, reuse infrastructure, stop repetitive familiar quizzes. Costs: fresh banks/oracles, math review, content expansion, delayed testing and maintenance. Better assessments can increase initial effort while reducing false confidence. Validate with matched parallel task families within one skill, counterbalanced where feasible, declared entry knowledge, constant outcome scope, logged assistance/practice, and fresh delayed 7/21-day tasks. A single learner produces case evidence, not a curriculum randomized trial; learning has carryover, so do not cross over unrelated M06/M17 as exchangeable treatments.

## 12. Compact coverage matrix — all 169 original topics

`L` authored lesson/diagnostic; `O` overview only; `V` mapped video; `D` demo; `I` signed implementation contract. Profiles in section 6 supply applicable C/M/I/T tasks, verification and PASS rules from section 8; each row adds specific content, application/transfer and a misconception. Delivery flags describe v1, not proposed materials. A role is optional/goal-specific rather than a hidden universal prerequisite. The misconception is an authoring target, not a claim that a learner made that error. Rows without an item-level blueprint still need expert authorship; generic profile coverage is not publication-ready assessment content.

| ID · topic | Current | Proposed role | Learning / application & transfer target | Misconception to probe |
| --- | --- | --- | --- | --- |
| **M01** Mathematical Basics | L | starter option | MAT: functions, notation, units. Translate a sensor calibration into a domain and formula. | function vs formula; unit-free reasoning. |
| **M02** Vectors | L+V+D+I | starter option | MAT: dot product, norm, projection. Project a motion command onto an allowed direction. | dot product as a vector; projection onto zero vector. |
| **M03** Matrices | L+V+D | starter option | MAT: matrix product, transpose, linear map. Transform a batch of coordinates and check dimensions. | AB=BA; shape agreement implies meaning. |
| **M04** Linear Algebra | L+V | just-in-time foundation | MAT: span, rank, nullspace. Identify which parameters two dependent sensors cannot recover. | more equations always determine x. |
| **M05** Calculus I | L+V | just-in-time foundation | MAT: derivative, limit, chain rule. Differentiate a nonlinear sensor calibration. Add an integration/accumulation bridge before M07. | derivative as slope only, never as sensitivity. |
| **M06** Multivariable Calculus | L+V+D | just-in-time foundation | MAT: gradient, Jacobian, directional derivative. Check a velocity map using directional differences. | Jacobian row/column order. |
| **M07** Differential Equations | L+V | just-in-time foundation | MAT: ODE, initial condition, integration. Compare Euler decay with an exact exponential. | Euler stability equals accuracy. |
| **M08** Probability | L | just-in-time foundation | MAT: conditioning, Bayes rule, expectation. Estimate fault probability after a noisy alarm. | confusing P(A given B) with P(B given A); ignoring base rate. |
| **M09** Statistical Foundations | O | just-in-time foundation | MAT: sampling, variance, estimation. Report uncertainty across repeated sensor measurements. | CI as probability the parameter is inside. |
| **M10** Optimization | L+V+D | just-in-time foundation | MAT: objective, gradient descent, step size. Fit a calibration offset and check the gradient. | lower training loss always better; learning rate as the only knob. |
| **M11** Numerical Computing | O | just-in-time foundation | MAT: floating point, conditioning, numerical error. Compare solver residual and parameter error at different scales. | small residual means accurate solution. |
| **M12** Rigid-Body Geometry | L+V | just-in-time foundation | MAT: frames, rigid transform, homogeneous coordinates. Transform a camera point into robot-base coordinates. | translating a direction. |
| **M13** Advanced Optimization | O | specialization | MAT: constraints, duality, convexity. Formulate bounded actuator allocation and inspect active constraints. | active constraint means infeasible. |
| **M14** Advanced Probability | O | specialization | MAT: random processes, conditional independence, concentration. Compare an independence model with correlated sensor errors. | Use the profile-specific critical check; item-level review pending. |
| **M15** Lie Theory | O | specialization | MAT: SO(3), SE(3), exponential map. Compare small rotation increments with matrix composition. | adding rotation vectors composes rotations; twist equals endpoint velocity. |
| **M16** Advanced Mathematics | O | frontier elective | MAT: functional analysis, manifolds, advanced inference. Select one theorem needed by a research paper and check its hypotheses. | Use the profile-specific critical check; item-level review pending. |
| **PY01** Python Fundamentals | L+V+I | starter option | CODE: values, functions, control flow. Implement and test a mean without library shortcuts. | aliasing versus copying; print versus return. |
| **PY02** Data Structures | O | just-in-time foundation | CODE: lists, hash maps, queues. Compare a queue and a list for processing sensor messages. | list is fine for every queue. |
| **PY03** Python Semantics | O | just-in-time foundation | CODE: aliasing, mutability, scope. Trace a nested-list aliasing bug with a minimal example. | Use the profile-specific critical check; item-level review pending. |
| **PY04** NumPy | L+V | starter option | CODE: array shapes, broadcasting, axes. Normalize features and verify against a scalar loop. | broadcasting silently aligns intended axes. |
| **PY05** Scientific Python | O | track core | CODE: SciPy, plotting, numerical workflows. Fit an ODE parameter and plot residuals with units. | Use the profile-specific critical check; item-level review pending. |
| **PY06** PyTorch Basics | O | track core | CODE: tensors, autograd, training loop. Compare an autograd gradient with a hand-derived neuron. | gradients reset automatically. |
| **PY07** Testing & Debugging | L+V | starter option | CODE: unit tests, debugging, contracts. Catch a wrong projection denominator with independent assertions. | passing tests prove correctness. |
| **PY08** Research Programming | O | track core | CODE: configuration, logging, reproducibility. Run the same small experiment from a clean checkout. | Use the profile-specific critical check; item-level review pending. |
| **PY09** Performance | O | specialization | CODE: profiling, vectorization, memory. Profile a loop and compare speed, memory, and numerical equivalence. | optimizing without measuring. |
| **PY10** Advanced Python | O | frontier elective | CODE: iterators, descriptors, metaprogramming. Implement a lazy data iterator and document its lifetime. | Use the profile-specific critical check; item-level review pending. |
| **CPP01** C++ Fundamentals | L | track core | CODE: types, compilation, arithmetic. Compile a mean function and detect integer truncation. | integer division; uninitialized values. |
| **CPP02** Memory Model | L+V | track core | CODE: lifetime, pointers, references. Analyze a vector reallocation and a dangling reference. | reference keeps object alive. |
| **CPP03** Resource Management | O | track core | CODE: RAII, unique ownership, move semantics. Replace manual allocation with a value or unique_ptr. | move leaves source unusable; manual new/delete is simpler. |
| **CPP04** Classes & OOP | O | track core | CODE: encapsulation, interfaces, invariants. Design a bounded joint-state object that rejects invalid updates. | Use the profile-specific critical check; item-level review pending. |
| **CPP05** STL & Algorithms | O | track core | CODE: containers, iterators, algorithms. Choose a container for timestamped lookup and measure its trade-off. | map always beats sorted vector. |
| **CPP06** Modern C++ | O | track core | CODE: templates, constexpr, modern idioms. Implement a small generic numerical utility with constrained assumptions. | Use the profile-specific critical check; item-level review pending. |
| **CPP07** Build Systems | O | track core | CODE: CMake, linking, build targets. Build a library and a separate test executable with CMake. | no crash means no UB. |
| **CPP08** Debugging & Testing | O | track core | CODE: sanitizers, debuggers, test harnesses. Reduce a failing program and verify the fix with a regression test. | Use the profile-specific critical check; item-level review pending. |
| **CPP09** Complexity & Performance | O | specialization | CODE: complexity, cache locality, profiling. Compare vector traversal and scattered allocations with a benchmark. | Use the profile-specific critical check; item-level review pending. |
| **CPP10** Concurrency | O | specialization | CODE: threads, synchronization, data races. Build a producer-consumer queue and explain its locking contract. | volatile synchronizes. |
| **CPP11** Numerical C++ | O | specialization | CODE: Eigen, linear solvers, numerical stability. Solve least squares and compare residuals with a Python oracle. | aliasing in Eigen expressions; inverse rather than solve. |
| **CPP12** Advanced C++ | O | frontier elective | CODE: generic libraries, ABI, systems design. Inspect one robotics library interface and document ownership risks. | Use the profile-specific critical check; item-level review pending. |
| **ML01** ML Problem Formulation | L | starter option | DATA: problem formulation, data split, baseline. Define a sensor-fault task without leaking test statistics. | random split is always valid for time series. |
| **ML02** Classical ML | L+V | track core | DATA: regression, classification, regularization. Fit a linear baseline and compare with a held-out constant predictor. | regularization only reduces test error. |
| **ML03** Generalization | O | just-in-time foundation | DATA: overfitting, capacity, distribution shift. Compare learning curves across training-set sizes. | test set can be reused during tuning; accuracy under imbalance. |
| **ML04** Neural Networks | L+V | track core | DATA: dense layer, activation, parameters. Compute a two-layer forward pass and count its parameters. | depth alone adds nonlinearity. |
| **ML05** Backpropagation | L+V | track core | DATA: chain rule, reverse mode, gradient check. Check a hand-written neuron gradient by finite differences. | backprop is the learning rule. |
| **ML06** Deep Learning Training | O | track core | DATA: optimization, initialization, batching. Compare two learning rates using the same seed and data split. | bigger model first. |
| **ML07** Model Evaluation | O | just-in-time foundation | DATA: metrics, calibration, held-out evaluation. Report precision, recall, and failure cases for a fixed test set. | Use the profile-specific critical check; item-level review pending. |
| **ML08** Representation Learning | O | specialization | DATA: embeddings, latent structure, feature quality. Compare frozen features with raw inputs on a small held-out task. | pretraining guarantees transfer under shift. |
| **ML09** Transformers | O | specialization | DATA: attention, tokenization, positional information. Compute a tiny attention matrix and inspect masking effects. | attention weights explain decisions. |
| **ML10** Self-Supervised Learning | O | specialization | DATA: contrastive learning, masked prediction, augmentation. Design augmentations that preserve the intended semantics. | Use the profile-specific critical check; item-level review pending. |
| **ML11** Generative Models | O | specialization | DATA: likelihood, latent variables, generative modeling. Compare reconstruction quality with sample diversity. | MSE handles multimodal targets; KL is a distance. |
| **ML12** Advanced ML | O | frontier elective | DATA: robustness, scaling, advanced learning theory. Reproduce one narrow paper claim with an explicit falsifier. | Use the profile-specific critical check; item-level review pending. |
| **T01** Linux | O | starter option | CODE: shell, permissions, processes. Create a repeatable project command without relying on shell history. | sudo as a fix. |
| **T02** Git | O | starter option | CODE: commits, branches, diffs. Commit one numerical experiment with its exact configuration. | commit equals backup of environment. |
| **T03** Development Tools | O | just-in-time foundation | CODE: editor, debugger, environment. Configure one debug launch and document its working directory. | Use the profile-specific critical check; item-level review pending. |
| **T04** Software Testing | L+V | just-in-time foundation | CODE: test contracts, oracles, regression checks. Mutate a numerical function and show which test fails. | Use the profile-specific critical check; item-level review pending. |
| **T05** Reproducible Environments | O | just-in-time foundation | CODE: dependency locking, environments, configuration. Recreate a small experiment in a clean virtual environment. | Use the profile-specific critical check; item-level review pending. |
| **T06** Docker | O | specialization | CODE: containers, images, volumes. Describe which files survive replacing an experiment container. | container state persists. |
| **T07** Systems Performance | O | specialization | CODE: resource measurement, latency, throughput. Report CPU, memory, latency, and throughput for one pipeline. | Use the profile-specific critical check; item-level review pending. |
| **T08** Advanced Infrastructure | O | frontier elective | CODE: distributed jobs, artifact management, deployment. Design a minimal experiment job with restart and output contracts. | Use the profile-specific critical check; item-level review pending. |
| **R01** Mechanics Foundations | L | track core | DYN: force, acceleration, energy. Check cart acceleration and energy units from a free-body diagram. | force causes velocity rather than acceleration. |
| **R02** Robot Mechanisms | L+V | track core | DYN: links, joints, degrees of freedom. Compare joint space and endpoint task space for a planar arm. | DOF equals number of motors. |
| **R03** Rigid-Body Transformations | L+V | track core | DYN: rotation, composition, inverse transform. Compose wrist and camera calibration and verify a round trip. | any orthogonal matrix is a rotation; rotation vectors add. |
| **R04** Forward Kinematics | L+V+D | track core | DYN: serial chains, relative angles, forward map. Derive two-link reach and test special configurations. Extend to a spatial transform chain; PoE stays optional. | Use the profile-specific critical check; item-level review pending. |
| **R05** Inverse Kinematics | O | track core | DYN: inverse map, multiple solutions, constraints. Compare two elbow solutions and identify an unreachable target. | IK has one answer; solver error means unreachable. |
| **R06** Robot Jacobian | L+V+D | track core | DYN: velocity map, Jacobian, singularity. Verify a planar Jacobian using directional differences. | Use the profile-specific critical check; item-level review pending. |
| **R07** Rigid-Body Dynamics | L+V | track core | DYN: mass matrix, gravity, damping. Check a pendulum’s equilibrium and energy balance. | Use the profile-specific critical check; item-level review pending. |
| **R08** Contact Mechanics | O | track core | DYN: contact force, friction, complementarity. Compare sticking and sliding in a simple block experiment. | friction force always equals μN. |
| **R09** Actuators & Transmission | O | track core | DYN: motor torque, gear ratio, actuation limits. Convert motor torque through gearing while checking speed limits. | higher ratio dominates. |
| **R10** Mechanical Design Verification | O | track core | DYN: load cases, stress, design validation. State a load envelope and verify a bracket with an independent calculation. | Use the profile-specific critical check; item-level review pending. |
| **R11** Floating-Base Dynamics | O | specialization | DYN: floating base, momentum, underactuation. Explain why joint torques alone cannot directly command every base acceleration. | base treated as actuated. |
| **R12** Advanced Dynamics | O | specialization | DYN: recursive dynamics, inertial parameters, efficient algorithms. Compare inverse dynamics with a small analytical model. | Use the profile-specific critical check; item-level review pending. |
| **R13** Advanced Locomotion | O | specialization | DYN: gait, balance, hybrid dynamics. Describe a gait’s contact sequence and a balance failure case. | a stable-looking steady gait implies robustness to disturbance. |
| **R14** Dexterous Manipulation | O | specialization | DYN: grasping, contact constraints, dexterity. Analyze whether a simple grasp resists a specified disturbance. | more contacts is always stronger. |
| **R15** Advanced Mechanics | O | frontier elective | DYN: flexibility, continuum mechanics, complex mechanisms. Identify when a rigid approximation fails in a chosen mechanism. | Use the profile-specific critical check; item-level review pending. |
| **C01** Control Fundamentals | L+V+D | track core | DYN: feedback, error dynamics, stability. Derive proportional tracking and constant-disturbance error. | higher gain always better. |
| **C02** Dynamic Systems | O | track core | DYN: state space, equilibrium, linearization. Linearize a nonlinear one-state model and compare trajectories. | local stability is global. |
| **C03** PID Control | O+D | track core | DYN: proportional, integral, derivative. Compare disturbance rejection and windup with actuator saturation. | derivative term has no noise cost. |
| **C04** Linear Systems | O | track core | DYN: controllability, observability, poles. Compute controllability and observability for a two-state model. | Use the profile-specific critical check; item-level review pending. |
| **C05** LQR | O | track core | DYN: quadratic cost, Riccati equation, state feedback. Compare feedback gains under two input penalties. | LQR is robust to any model error. |
| **C06** State Estimation | O | track core | DYN: measurement model, prediction, uncertainty. Estimate velocity from position observations and explain the noise trade-off. | Use the profile-specific critical check; item-level review pending. |
| **C07** Kalman Filtering | O | track core | DYN: Gaussian belief, Kalman gain, covariance. Derive a scalar gain and check uncertainty before and after an update. | covariance reflects actual error regardless of model. |
| **C08** Sensor Fusion | O | track core | DYN: sensor alignment, fusion, correlation. Explain why treating correlated sensors as independent overstates confidence. | correlated sensors treated as independent. |
| **C09** Digital Control | O | track core | DYN: sampling, discretization, delay. Compare a continuous stable controller with a delayed sampled version. | filtering is free of delay. |
| **C10** Nonlinear Control | O | specialization | DYN: Lyapunov function, nonlinear stability, feedback linearization. Check the sign of a candidate Lyapunov derivative. | Use the profile-specific critical check; item-level review pending. |
| **C11** Model Predictive Control | O | specialization | DYN: receding horizon, constraints, prediction. Formulate a bounded cart problem and inspect feasible inputs. | MPC handles any model mismatch. |
| **C12** Nonlinear State Estimation | O | specialization | DYN: EKF, UKF, nonlinear belief update. Compare linearization error with sigma-point propagation in a scalar example. | EKF covariance is trustworthy under strong nonlinearity. |
| **C13** Optimal Control | O | specialization | DYN: trajectory optimization, optimality conditions, dynamic programming. Compare a locally optimized trajectory with a simple feasible baseline. | locally optimal trajectory is globally optimal. |
| **C14** Whole-Body Control | O | specialization | DYN: task hierarchy, contact constraints, whole-body dynamics. Prioritize balance and reaching under limited actuation. | tasks combine without conflict. |
| **C15** Advanced Control | O | frontier elective | DYN: robustness, adaptation, advanced control. State the uncertainty set behind a claimed robust controller. | Use the profile-specific critical check; item-level review pending. |
| **S01** Simulation Fundamentals | O | track core | DYN: integration, modeling error, simulation validation. Compare a simulated trajectory with an analytical solution. | simulator output is ground truth. |
| **S02** MuJoCo | O | track core | DYN: MJCF, actuators, contacts. Build a minimal pendulum and compare energy with a reference model. | contact parameters are physical constants. |
| **S03** ROS 2 Fundamentals | O | track core | CODE/RESEARCH: nodes, topics, messages. Create a publisher-subscriber pair and document message units. | topics are reliable by default. |
| **S04** Robot Description | O | track core | CODE/RESEARCH: URDF, links, frames. Validate a two-link description against hand-derived transforms. | visual frame equals joint frame. |
| **S05** ROS 2 Runtime | O | track core | CODE/RESEARCH: executors, QoS, callbacks. Measure message delay under two QoS settings. | callbacks run in parallel by default. |
| **S06** Hardware Integration | O | track core | CODE/RESEARCH: drivers, timing, hardware interfaces. Design a mock driver with timeout and unit checks before hardware use. | hardware commands are always applied at send. |
| **S07** Robot Safety | O | track core | CODE/RESEARCH: hazard analysis, limits, fault response. Define simulation tests for command timeout and invalid sensor data. Entry awareness; real hardware remains outside automatic quiz authorization. | simulation success implies safety. |
| **S08** System Identification | O | specialization | DYN: parameter estimation, excitation, model fit. Fit a damping coefficient and test it on a different trajectory. | low training residual identifies parameters. |
| **S09** Sim2Real | O | specialization | DYN: model mismatch, domain gap, validation. List parameter uncertainties and design a staged validation protocol. | wider randomization is always better. |
| **S10** ROS 2 Control | O | specialization | CODE/RESEARCH: controller interfaces, resource ownership, update loop. Use a mock interface to verify command limits and state consistency. | Use the profile-specific critical check; item-level review pending. |
| **S11** Advanced Simulation | O | specialization | DYN: differentiable simulation, batched worlds, solver settings. Compare solver settings against a fixed reference trajectory. | Use the profile-specific critical check; item-level review pending. |
| **S12** Advanced Robotics Software | O | frontier elective | CODE/RESEARCH: real-time design, composition, systems architecture. Trace end-to-end sensor-to-command latency and failure handling. | Use the profile-specific critical check; item-level review pending. |
| **V01** Digital Images | L+V+D | track core | DATA: pixels, array axes, color channels. Build a synthetic RGB image that catches row-column and channel swaps. | image axes are x,y. |
| **V02** Image Processing | O+D | track core | DATA: filtering, convolution, sampling. Compare smoothing before and after downsampling a checkerboard. | convolution order never matters with nonlinear steps. |
| **V03** Camera Models | O | track core | DATA: pinhole camera, intrinsics, projection. Project known points and inspect the effect of focal length. | focal length scales depth. |
| **V04** Camera Calibration | O | track core | DATA: distortion, reprojection error, calibration. Separate calibration fit error from held-out reprojection error. | low RMS means calibrated everywhere. |
| **V05** Feature Extraction | O | specialization | DATA: corners, descriptors, matching. Measure matching robustness under rotation and brightness changes. | more features means better pose. |
| **V06** CNN | O+V+D | track core | DATA: convolution, receptive field, weight sharing. Compute output size and receptive field for a small convolution stack. | pooling gives invariance to all transforms. |
| **V07** Image Classification | O | track core | DATA: class prediction, augmentation, confusion matrix. Compare class-wise errors with a majority-class baseline. | Use the profile-specific critical check; item-level review pending. |
| **V08** Object Detection | O | track core | DATA: bounding boxes, IoU, precision-recall. Compute IoU by hand and inspect duplicate-detection handling. | high mAP implies grasp usability. |
| **V09** Object Tracking | O | specialization | DATA: data association, motion model, identity. Compare nearest-neighbor association with a motion prediction. Compare provided detections/feature tracks with a learned-detector path. | Use the profile-specific critical check; item-level review pending. |
| **V10** Segmentation | O | specialization | DATA: pixel labels, mask metrics, boundaries. Compare per-pixel accuracy and class IoU on imbalanced masks. | Use the profile-specific critical check; item-level review pending. |
| **V11** Multi-View Geometry | O | specialization | DATA: epipolar geometry, triangulation, pose. Triangulate a synthetic point and inspect baseline sensitivity. | more baseline is free of matching cost. |
| **V12** Depth Estimation | O | specialization | DATA: stereo disparity, scale, uncertainty. Analyze why small disparity errors grow at long range. | Use the profile-specific critical check; item-level review pending. |
| **V13** 3D Perception | O | specialization | DATA: point clouds, registration, 3D features. Register synthetic point sets and inspect outlier sensitivity. | ICP is globally convergent. |
| **V14** Visual Representation Learning | O | specialization | DATA: visual embeddings, pretraining, transfer. Compare frozen embeddings under a held-out domain shift. | Use the profile-specific critical check; item-level review pending. |
| **V15** Vision Transformers | O | specialization | DATA: patch tokens, attention, spatial encoding. Calculate token count and discuss spatial-information encoding. | Use the profile-specific critical check; item-level review pending. |
| **V16** Video Understanding | O | specialization | DATA: temporal context, motion, video sampling. Compare frame-only and temporal baselines on an action ambiguity. | Use the profile-specific critical check; item-level review pending. |
| **V17** Visual Odometry & SLAM | O | specialization | DATA: pose estimation, mapping, loop closure. Analyze drift and distinguish relative error from global alignment. | ATE alone evaluates odometry. |
| **V18** Vision Foundation Models | O | frontier elective | DATA: pretraining scale, prompting, transfer evaluation. Test one model on a small held-out robotics distribution. | Use the profile-specific critical check; item-level review pending. |
| **V19** 3D Neural Representations | O | frontier elective | DATA: neural fields, rendering, 3D reconstruction. Compare novel-view quality with geometric accuracy. | Use the profile-specific critical check; item-level review pending. |
| **V20** Advanced Perception | O | frontier elective | DATA: multimodal perception, uncertainty, robustness. Design an evaluation suite for occlusion and sensor degradation. | Use the profile-specific critical check; item-level review pending. |
| **RL01** RL Fundamentals | L+V | track core | PLAN/DATA: agent, reward, return. Compute returns in a tiny navigation problem before training. | reward equals goal. |
| **RL02** Markov Decision Processes | L+V+D | track core | PLAN/DATA: Markov state, transition kernel, Bellman equation. Solve a two-state value equation exactly. | V is the immediate reward. |
| **RL03** Value Functions | O | track core | PLAN/DATA: state value, action value, advantage. Compare V and Q for a complete tabular example. | Use the profile-specific critical check; item-level review pending. |
| **RL04** Dynamic Programming | O | track core | PLAN/DATA: policy evaluation, policy improvement, value iteration. Implement synchronous value iteration and check its residual. | DP needs no model. |
| **RL05** Model-Free Prediction | O | track core | PLAN/DATA: Monte Carlo, TD learning, bootstrapping. Compare complete-return and one-step TD estimates on the same trajectories. | TD has no bias. |
| **RL06** Model-Free Control | O+V+D | track core | PLAN/DATA: Q-learning, SARSA, exploration. Contrast on-policy and off-policy updates in a cliff task. | Use the profile-specific critical check; item-level review pending. |
| **RL07** Function Approximation | O | track core | DATA: value approximation, projection, stability. Compare tabular and linear estimates on a small controlled MDP. | more function power stabilizes. |
| **RL08** Policy Gradient | O | track core | DATA: log derivative, policy objective, variance. Derive a two-action policy gradient with an independent numerical check. | log-derivative needs differentiable dynamics. |
| **RL09** Actor-Critic | O | track core | DATA: critic, advantage, actor update. Inspect actor and critic errors separately in a tiny task. | critic error directly equals policy quality. |
| **RL10** PPO | O | track core | DATA: clipped objective, on-policy data, KL change. Plot the surrogate for positive and negative advantages. | clipping guarantees monotonic improvement. |
| **RL11** Off-Policy RL | O | specialization | DATA: replay buffer, target network, off-policy correction. Compare target estimates with and without stale replay data. | off-policy always more sample-efficient in wall-clock. |
| **RL12** RL Experimental Design | O | track core | DATA: seeds, evaluation episodes, compute budget. Predeclare seeds, environment steps, and a held-out evaluation protocol. Introduce the minimal protocol before any costly RL training. | best-seed reporting; 3 seeds suffice. |
| **RL13** Continuous Control | O | specialization | DATA: continuous actions, bounded policy, control cost. Compare action scaling and saturation under a fixed evaluation task. | reward scale is cosmetic. |
| **RL14** Reward Engineering | O | specialization | DATA: reward specification, shaping, side effects. Construct a reward loophole and an evaluation that detects it. | shaping never alters the optimum. |
| **RL15** Curriculum Learning | O | specialization | DATA: task difficulty, curriculum, distribution. Compare a staged schedule with a fixed distribution at equal budget. | Use the profile-specific critical check; item-level review pending. |
| **RL16** Domain Randomization | O | specialization | DATA: parameter randomization, robustness, coverage. Choose physically justified parameter ranges and evaluate held-out extremes. | Use the profile-specific critical check; item-level review pending. |
| **RL17** Imitation Learning | O | specialization | DATA: behavior cloning, demonstrations, distribution shift. Compare one-step imitation error with rollout failure. | low validation loss implies good rollouts. |
| **RL18** Offline RL | O | specialization | DATA: fixed dataset, support mismatch, conservative learning. Identify actions whose value estimates require unsupported extrapolation. | Use the profile-specific critical check; item-level review pending. |
| **RL19** Model-Based RL | O | specialization | DATA: learned dynamics, planning, model bias. Measure one-step and multi-step model error separately. | Use the profile-specific critical check; item-level review pending. |
| **RL20** Hierarchical RL | O | specialization | DATA: options, temporal abstraction, termination. Define one reusable skill with initiation and termination conditions. | Use the profile-specific critical check; item-level review pending. |
| **RL21** Safe RL | O | specialization | DATA: constraints, risk, safe exploration. Evaluate constraint violations separately from average return. | Use the profile-specific critical check; item-level review pending. |
| **RL22** Multi-Agent RL | O | frontier elective | DATA: joint policy, nonstationarity, credit assignment. Separate centralized training assumptions from decentralized execution. | Use the profile-specific critical check; item-level review pending. |
| **RL23** Advanced Exploration | O | frontier elective | DATA: intrinsic reward, uncertainty, information gain. Compare novelty bonuses with task return and inspect distraction. | Use the profile-specific critical check; item-level review pending. |
| **RL24** Meta-RL | O | frontier elective | DATA: task distribution, adaptation, meta objective. Separate training tasks from held-out adaptation tasks. | Use the profile-specific critical check; item-level review pending. |
| **E01** Sequential Decision Making | O | specialization | PLAN/DATA: decision horizon, belief, closed-loop behavior. Compare a greedy choice with a multi-step plan. | Use the profile-specific critical check; item-level review pending. |
| **E02** Planning Fundamentals | O | specialization | PLAN/DATA: search, heuristics, state transitions. Implement a small A* search and test heuristic admissibility. Discrete search first; do not claim collision-aware motion planning from A* alone. | A* is optimal with any heuristic. |
| **E03** Planning Under Uncertainty | O | specialization | PLAN/DATA: belief state, POMDP, information gathering. Compare acting immediately with taking a clarifying measurement. | replanning replaces belief. Open reasoning reviewed. |
| **E04** Robot Skills | O | specialization | PLAN: skill contracts, state machines and recovery. Execute a new bounded workflow; robotics/RL variants add scoped prerequisites. | skills compose without state checks. |
| **E05** Task Planning | O | specialization | PLAN/DATA: symbolic state, operators, task constraints. Plan a pick-place sequence and identify an impossible precondition. | symbolic plan implies geometric feasibility. |
| **E06** Task & Motion Planning | O | specialization | PLAN/DATA: symbolic-geometric coupling, feasibility, motion constraints. Reject a symbolic plan whose grasp pose is unreachable. Requires the candidate R16 motion-planning bridge for the revised scope. | plan-then-check is complete. |
| **E07** Imitation-Based Robot Policies | O | specialization | PLAN/DATA: demonstration policy, multimodal actions, rollout shift. Evaluate recovery from states missing in the demonstrations. MLP behavior cloning is a valid baseline before transformers. | low training loss implies success. |
| **E08** World Models | O | specialization | PLAN/DATA: latent dynamics, prediction, planning. Compare prediction quality with downstream control usefulness. | lower pixel error gives better control. |
| **E09** Object-Centric Representations | O | specialization | PLAN/DATA: objects, relations, compositionality. Test whether a representation tracks an occluded object identity. | Use the profile-specific critical check; item-level review pending. |
| **E10** Vision-Language Models | O | specialization | PLAN/DATA: vision-language alignment, grounding, prompt sensitivity. Compare two prompts on a fixed set of spatial relations. | grounding follows from caption ability. |
| **E11** Diffusion/Flow Action Policies | O | visuomotor specialization | PLAN/DATA: action diffusion, flow matching, multimodal policy. Compare multimodal action generation with deterministic regression. | MSE handles multimodal targets. |
| **E12** Vision-Language-Action Models | O | frontier elective | PLAN/DATA: vision-language-action, grounded control, generalization. Evaluate an instruction on held-out objects and environments. | demo video proves generalization. |
| **E13** Long-Horizon Robot Learning | O | frontier elective | PLAN/DATA: long-horizon planning, skill composition, error recovery. Measure success per stage and design a recovery policy. | Use the profile-specific critical check; item-level review pending. |
| **E14** Embodied Reasoning | O | frontier elective | PLAN/DATA: grounded reasoning, causal structure, execution feedback. Test whether an inferred plan remains valid after a scene change. | Use the profile-specific critical check; item-level review pending. |
| **E15** Advanced Embodied Intelligence | O | frontier elective | PLAN/DATA: generalization, autonomy, research evaluation. Design a benchmark with unseen tasks and explicit failure reporting. | Use the profile-specific critical check; item-level review pending. |
| **RS01** Scientific Reasoning | L | starter option | RESEARCH: hypothesis, falsifiability, controls. Write a controlled comparison with a clear falsifier. | confirmation as proof. |
| **RS02** Experimental Design | O | just-in-time foundation | RESEARCH: independent variable, confounding, ablation. Use a factorial ablation to separate two proposed improvements. | changing two factors at once is efficient. |
| **RS03** Statistical Inference | O | just-in-time foundation | RESEARCH: confidence interval, hypothesis test, effect size. Report an effect size and interval rather than only a p-value. | Use the profile-specific critical check; item-level review pending. |
| **RS04** Experimental Reproducibility | O | just-in-time foundation | RESEARCH: protocol, artifacts, replication. Re-run a figure from raw measurements and a locked environment. | seed fixes all nondeterminism. |
| **RS05** Error Analysis | O | just-in-time foundation | RESEARCH: failure taxonomy, residuals, subgroup analysis. Group failures by condition and test one proposed explanation. | Use the profile-specific critical check; item-level review pending. |
| **RS06** Paper Reading | O | just-in-time foundation | RESEARCH: claims, assumptions, evidence. Write a claim-evidence-assumption table for one paper. | venue equals validity. |
| **RS07** Scientific Writing | O | specialization | RESEARCH: argument, figures, limitations. Rewrite a result paragraph with a concrete metric and uncertainty. | Use the profile-specific critical check; item-level review pending. |
| **RS08** Literature Review | O | specialization | RESEARCH: search strategy, comparison matrix, research gap. Build an inclusion rule and compare assumptions across three sources. | Use the profile-specific critical check; item-level review pending. |
| **RS09** Research Software | O | specialization | RESEARCH: experiment software, versioning, artifact integrity. Link one result to a code revision, config, and data hash. | Use the profile-specific critical check; item-level review pending. |
| **RS10** Advanced Research | O | frontier elective | RESEARCH: research question, novelty, reproducible contribution. Propose a minimal study with baselines, risks, and a falsifier. | Use the profile-specific critical check; item-level review pending. |

## 13. Detailed blueprints for priority foundations

These are **scoped authoring specifications**, not new available lessons or certified tests. Every row inherits the versioning/A0/critical-check rules in section 8. Open derivations and unfamiliar transfer require a qualified reviewer. Pilot numerical tolerances must be justified against scale and arithmetic; exact equality is unsuitable for general floating-point outputs. Automatic I passes only the stated implementation, not the entire topic. Review each blueprint mathematically before publishing; peer review already caught errors in earlier LQR, NEES and PPO proposals.

| Topic / bounded claim | C/M task and critical failure | I task and correctness checks | Transfer, retention and explicit PASS scope |
| --- | --- | --- | --- |
| M01: calibration readiness | Translate input/output domain, units and inverse; rearrange a linear calibration; evaluate sine/cosine in radians. Critical: dimensionally invalid model or degree/radian mix. | No code required before PY01. Hand-check inverse by composition at interior/endpoints; test invalid domain. | New unit scale and piecewise domain. Pass only the specified algebra/trig/unit readiness, with pilot C/M gates; delayed closed-note reconstruction. Not all precalculus. |
| M02: vectors | Derive dot, norm, projection and orthogonal residual; distinguish point/displacement and scalar/vector output. Critical: zero-direction or frame mismatch. | Fresh `dot`, `norm`, `project` tasks; unequal/nonzero/signed inputs, dimension/zero policies, scale and orthogonality properties; reject wrong denominator and dropped-coordinate mutations. Independent oracle. | Constrained movement or force decomposition in a changed direction/basis. L2 requires all three stated contracts, not the old dot report; fresh delayed calculation plus reviewed unfamiliar explanation. |
| M03: matrix maps | Map basis vectors, infer shapes and compose in a declared order. Critical: treating AB as BA or silently transposing batches. | Implement a small matrix/vector composition; compare hand cases and loop oracle; rectangular/identity/zero cases, incompatible shapes and nonmutation. | New coordinate convention or calibration batch. Pass only map/composition scope, with delayed reconstruction; no claim of spectral algebra. |
| M04: rank and identifiability | Explain span/nullspace/rank, consistent versus identifiable, and why extra dependent measurements do not identify parameters. Critical: invert a singular system as if unique. | Small solve/rank task compared with independent elimination or stable library; full rank, deficient and inconsistent cases, residual and nullspace checks. | New sensor dependence; explain remaining degrees of freedom. Broader eigen/SVD credit needs M17 or a new reviewed contract. |
| M05: derivatives and integration bridge | Reconstruct chain rule, then accumulation/definite integral and derivative-integral relationship for elementary functions. Critical: missing inner derivative, units or initial constant. | Hand antiderivative/difference check and bounded numerical quadrature with refinement; coding optional if not yet PY01. Do not grade a sampled equality as a proof. | Convert a velocity signal to displacement and linearize a new sensor curve. Separate derivative versus integration objective versions; both must be evidenced before M07's full scope. |
| M06: Jacobians | Declare input/output shapes; derive J, Jv and Jᵀv, with a multi-output nonlinear map. Critical: wrong order/shape or ignored shared path. | Compare hand formula with directional central differences at several nonzero points and step sizes; record truncation/roundoff and nonsmooth exceptions. | New calibration output/coordinate convention; reviewed reconstruction after delay. Scalar descent animation alone cannot pass. |
| M07: simple ODE simulation | State initial value and units; solve decay and derive Euler amplification. Critical: confusing stability with accuracy. | Compare exact decay and Euler for different dt, including an unstable step; demonstrate convergence under refinement in the declared regime. | Changed time constant/forcing; distinguish model error and discretization. Pass first-order numerical scope only; integration readiness explicit. |
| M08: Bayes and expectation | Compute conditional/posterior probabilities, E and variance with declared sample space/base rate. Critical: inverse conditional or unjustified independence. | Exact table enumeration plus optional Monte Carlo against predeclared statistical tolerance; fractions/decimals accepted by an approved safe format policy. | Shifted prevalence and correlated alarms, with dependence explicitly stated. Pass Bayes/expectation scope, not all probability; delayed new table. M08 v1 remains unchanged. |
| M09: uncertainty and covariance | Compute covariance/correlation and explain sample variability versus bias; interpret a frequentist interval without claiming probability for a fixed parameter. Critical: independence from zero correlation in general. | Seeded synthetic repeated measurements, covariance symmetry/PSD within numerical error, known distribution checks and interval-coverage experiment. | Sensor with shared bias, changed sampling protocol. Pass bounded covariance/uncertainty scope; no universal “three seeds suffice.” |
| M10: optimization | Derive gradient/step for the stated loss, relate curvature to a step bound. Critical: transferring a bound across differently scaled losses. | Scalar/quadratic descent plus gradient check; show stable/unstable steps with declared model and stopping criteria; compare analytic optimum. | New curvature or ill-scaled coordinates. Check trajectory, not just final rounded value; delayed derivation. |
| M11/M17: numerics and spectral least squares | Separate residual/parameter error, rank/conditioning, eigenmode stability and SVD truncation. Critical: assume small residual implies correct parameters or use explicit inverse indiscriminately. | Stable solve/least-squares using a library decomposition, with rank-deficient/noisy/ill-conditioned cases; perturbation and reconstruction checks. No from-scratch SVD required. | Dependent sensors, changed scales or singular IK. Score numerical and spectral scopes separately; expert checks truncation/tolerances. |
| PY01: independent small function | Explain return versus print, loops, types and nonmutation. Declare empty/nonfinite policy rather than surprise-grading it. | New bounded aggregation function materially different from the shown mean; independent ordinary/boundary/invalid/property tests and source artifact. | Debug an unfamiliar boundary failure after delay. Current mean report stays mean-only; program PASS does not prove test-design skill. |
| PY04: arrays | Trace axes, shapes, broadcasting, indexing and copy/view behavior. Critical: silently normalize over wrong axis or leak fit statistics. | Batch transform/normalization against scalar-loop oracle; non-square shapes, constant columns, invalid input and nonmutation where required. | Changed batch layout; explain a plausible-but-wrong output. Pass declared array operations only. |
| PY07/T04: testing | Define contract, independent expected value, regression and mutation. Critical: expected result computed by the function under test. | Learner test suite must accept known correct implementations and reject a predeclared family of genuine boundary/logic mutations; test invalid policies without overconstraining valid implementations. | Repair a new bug with a minimal reproducer. Separate PY07/T04 objective/evidence identities even in one study project. |
| M12/R03: geometry | Label source/target frame, point versus direction, inverse/order, rotation validity and quaternion convention. Critical: translation applied to a direction or reflection accepted as proper rotation. | Compose/invert transforms; identity/round-trip/rotation and quaternion sign-equivalence checks with declared representation; noncommuting rotations and nonzero translations. | New camera mount/tool frame. Elementary transforms first; twists/near-π logarithms are advanced M15 scope. |
| R04: FK | Derive a planar 2R arm using relative joint angles and unequal links; extend to a declared spatial transform chain. Critical: confuse absolute/relative angle or transform order. | Independent trig versus homogeneous-chain oracle, reachable bound, zero and nonzero configurations, joint/tool offset checks. | Changed tool frame or axis convention. Two distinct contracts may separate planar and spatial scope; no PoE required for baseline PASS. |
| R06: Jacobian | Derive endpoint-position J, units, rank and Jᵀ force mapping; distinguish endpoint velocity from spatial/body twist. Critical: singularity implies zero velocity in every direction. | Analytic versus directional finite differences at nonsingular and near-singular poses, unequal lengths, convention checks. | New offset or force direction. Twist-space variant adds M15 capability; reviewed unfamiliar derivation needed for L3. |
| C01/C03: feedback/PID | Declare integrator/first-order plant, predict feedback sign, disturbance offset, saturation/noise effects. Critical: unstable sign or ignoring command limits. | Simulation with analytic simple cases, step refinement, disturbances, saturation/anti-windup and noisy derivative; bounded commands. | Changed plant gain/delay. Introductory tuning can precede full C02; formal stability claim needs its math. No live-hardware authorization. |
| C05: LQR | State finite versus infinite horizon, model, Q/R and theorem assumptions. Critical: requiring full controllability for all valid LQR cases. | Check Riccati residual, cost, closed-loop behavior and stabilizable case with an uncontrollable stable mode; reject invalid cost/dimension inputs. | Changed cost/model and limits. Infinite-horizon conditions require the chosen stabilizability/detectability assumptions; finite-horizon is different. Expert review before release. |
| C07: Kalman filter | Derive prediction/update, covariance and noise assumptions. Critical: treating covariance as guaranteed true error or ignoring correlation. | Known linear-Gaussian simulation, symmetry/numerical PSD, innovation checks, ensemble NEES with stated run count and chi-square acceptance false-failure policy. | Model bias/dropout/correlated noise. Do not require every single realization to lie within a 95% bound; statistical test itself has false failures. |
| ML01/ML02/ML05 | Declare loss, split and baseline; reconstruct reverse-mode derivatives with shared-parameter accumulation. Critical: test leakage or missing a shared path. | Tiny hand/finite-difference/autodiff comparison, training-only preprocessing, held-out baseline and reproducible seed/report. | Changed loss/output or deliberately leaked workflow. Numeric gradient agreement is a procedural check; reviewed explanation for open derivation. |
| RL02/RL06 | Define transitions, rewards, discount and terminal versus truncation conventions; distinguish expected return from one rollout. Critical: invalid transition sum or wrong bootstrap. | Enumerate tiny policies/exact solution, compare iteration and TD/Q updates, known-optimum small environment with separate evaluation seeds. | Changed reward/observation sufficiency. Known-number repeats are retention, not transfer; stochastic goal reach once is insufficient. |
| RL09/RL10 | Actor/critic roles and PPO-clip ratio/objective; interpret advantage sign. Critical: stale/incorrect log-prob ratios or terminal/truncation bootstrap errors. | Tiny analytic ratio/gradient cases plus bounded training sanity checks; compare selected real bug mutations. Advantage normalization is an ablation. | New action scaling or rollout boundary; report median/spread for a small task and distinguish broader method comparisons. Human review for L3. |
| S07/RS01 | State a falsifiable claim, hazard, stop condition and limitations. Critical: “simulation success proves hardware safety” or confirmation as proof. | Mock stale sensor/timeout/invalid command and protocol artifact with independent expected behavior; qualified review of the hazard table. | New failure scenario/claim. No automatic hardware or scientific judgment certification; M can be inapplicable, with approved scope policy. |

Candidate implementation blueprints, after foundations:

| Candidate | Method / C-M outcome | I correctness and unfamiliar transfer | Critical misconception / PASS limit |
| --- | --- | --- | --- |
| R16 | DATA/DYN: inspect units, timestamp alignment, bias versus noise | Recover known bias/time offset from a synthetic log and flag missing/out-of-order data; transfer to changed rate/dropout | Datasheet noise equals installed-system uncertainty. Pass the declared log/calibration scope, not all sensors. |
| R17 | DYN: distinguish geometric path/time law; derive bounded triangular/trapezoidal profile | Check endpoints, continuity, velocity/acceleration bounds and degenerate distances with an independent analytic oracle; transfer to stricter limits | Collision-free path is already an executable trajectory. No claim of full jerk/torque feasibility unless explicitly tested. |
| R18 | PLAN: C-space, collision and sampling assumptions | Exhaustive grid oracle for small discrete cases, independent collision tests for segments; finite-run planner returns path or honest failure; transfer to a narrow passage | Finite RRT failure proves no path, or RRT guarantees near-optimality. Pass scoped feasibility algorithm only. |
| R19 | DYN: joint tracking, limits and model mismatch before contact control | Simple analytic plant, reference tracking/torque bounds, delay and parameter perturbations, predeclared simulation metrics; later reviewed contact test | Stiffer gains are always safe/accurate. Pass simulated joint-space tracking, not general impedance or hardware readiness. |
| R20 | PLAN/DATA: motion/observation likelihood and localization belief | Small finite-state Bayes oracle, particle normalization/resampling sanity checks, repeated trials and recovery after relocation; transfer to ambiguity/dropout | Odometry cannot drift systematically; one accurate trajectory proves calibration. Default particle route needs M08/M09/sensors, Kalman route additionally C07. |
| E16 | DATA: episodes, schemas, synchronization and leakage | Synthetic corrupt episodes with known defects, split by episode/session before fit, recover expected QA flags; transfer to a new collection artifact | More demonstrations compensate for leakage/misalignment. Pass existing-data QA; collection needs separate simulator/hardware/consent scope. |

## 14. Accepted recommendations

Final agreement after four rounds:

- Preserve all 169 IDs, immutable historical contracts and evidence; navigation groupings grant no broader credit.
- Replace compulsory long spine with guided early artifact, placement checks and goal paths. Teach essential readiness in time for the chosen objective, rather than defer it out of sight.
- Seven provisional additions; other missing content has explicit homes. Early safety awareness and a reviewed cognitive/HRI research path remain essential.
- Repair prompt ambiguity/precision, fixed-position answers and weak objective coverage; retain worked examples and assess genuinely different tasks.
- Pilot M02/PY01 plus identified defects before generic item/readiness engines. Keep the first authoring tranche bounded.
- Distinguish expression/procedure checks from proof, repeated quizzes from transfer, available sources from reviewed instructional matches, and provenance from authorship.
- External review for open L3/L4 evidence; no compulsory L3 dashboard filling for a learner without a reviewer.
- No universal PPO dependency or mandatory diffusion policy for all robot learning. Claude's Round 4 accepts an explicit visuomotor branch; the earlier E11 dispute is resolved.
- Matched within-skill task families and delayed cases replace an invalid unrelated-topic crossover design. No measured savings or optimal schedule claim.

## 15. Rejected recommendations and why

These were rejected or explicitly withdrawn during debate; they are not all Claude's final positions.

| Proposal | Reason / safer replacement |
| --- | --- |
| Universal 54-topic, 540-hour prerequisite spine | Unsupported and delays useful work; replace with bounded goal paths and early milestones. |
| Delete 11 IDs or alias 36 merged competencies into broader credit | Breaks evidence meaning and removes useful objectives; retain identities and separately score study groups. |
| Every learner needs every advanced topic, PoE before basic FK, or PPO before SAC/world models | Task counterexamples show these are not universal necessities; scope/variant determines readiness. |
| Blanket archive of all “Advanced” topics | Title is insufficient evidence; preserve concrete artifacts/electives and audit the objective. |
| Generic 12-item, fixed 80%-per-dimension rule solves validity | Coverage and discrete score grid matter; small dimension counts can still force perfection. Pilot explicit scoped forms. |
| At least three distractors, all binary questions invalid, mandatory 24-hour retake ban | Source misread/unsupported policy. Three options is one key plus two distractors; adequacy depends on design. Corrective practice remains available. |
| Random hidden tests, signatures or AI explanation prove independent mastery | Local tests are inspectable; authorship is self-attested; derivation/design/transfer needs appropriate evidence/review. |
| Advantage normalization absent means PPO bug; all LQR needs full controllability; all NEES trials inside 95% interval | Technical errors corrected in peer review. Use the actual algorithm/theorem/statistical acceptance policy. |
| 30–45 minutes saved daily, 17–26% program reduction, fixed annual-tail retention benefit | Unmeasured scenarios with different scopes and assumed event costs; withdraw numerical benefit claims. |
| Rigid prose length, video percentages or fixed visual-learning-style matching | No demonstrated universal benefit; choose activity by objective, access and learner preference. |
| Build hundreds of readiness checks or many visualizations first | Unjustified maintenance cost before pilots; start with the gaps that block credible evidence. |

## 16. Unresolved disagreements and owner decisions

Both completed Round 4s were read. Some apparent open questions in Claude's Round 4 were answered by Codex's independently written Round 4; do not keep them artificially unresolved. M08 false-failure is confirmed, the 189/190 stale count is resolved, default path and E11 branch are agreed, and both now favor known defects before major engine work.

| Issue | Claude final position | Synthesis position / decision needed |
| --- | --- | --- |
| R20 default C07 prerequisite | Conservative Kalman requirement retained; acknowledges particle-only alternative | Particle route has M08/M09/measurement requirements; C07 applies to Kalman variant. Appendix A uses particle route. Approve intended lab before changing production. |
| Archive 11 broad IDs | Keep history, remove from paths, preserve some elective artifacts | Do not blanket archive based on title. Audit objectives; retain optional usable material. The proposed graph retains all identities and dependencies. |
| M17 versus versioned M04 | Prefers M17 pending manifests, accepts either honest scope strategy | Provisional M17 accepted for practical separation, but separate identity is not logically necessary. Owner chooses after manifest review. |
| R16 and E16 separate units | Agreed candidates, low confidence in separate identity | Scope/coherence/cost uncertain; may become modules under a current topic if evidence stays accurately versioned. |
| Readiness failures and gating | Recommender should react; failed check is current evidence | Agreed direction; exact criticality, confirmation, assistance, scope and warning/block rules unresolved. Do not global-block ordinary learning after an ambiguous item. |
| Assessment/level policy | Applicable-dimension contracts and coverage-first gates, ≥80% where declared | Same direction; concrete 5+5 pilot here is a starting form, not agreement on a universal standard. Approval and calibration required. |
| Navigation graph versus identity DAG | 119 live units after grouping/defer, 193 hard edges | 176 retained identities, 319 edges. Different objects, not competing evidence of efficiency. Future authoring must maintain both meanings explicitly. |

Owner decisions before implementation: first learner goal; final IDs/scopes; migration and applicable-dimension policy; reviewer availability; content/engineering budget. No consensus on an exact optimal curriculum, learning time, delay schedule, false-failure rate or hardware transfer is possible from this audit alone. No need to decide all future research content before approving two pilots.

Final-peer consistency notes: Claude's R04 matrix retains a “PoE” phrase despite its stated baseline/extension correction; its T04 row retains “evidence as alias” despite the explicit separate-scoring rule. Use the final explicit principles and this document's scope, not those stale phrases, for authoring. No peer file was edited.

## 17. Evidence quality, confidence and limitations

| Evidence | Confidence / inference limit |
| --- | --- |
| Repository enumeration, grading and recommendation code, reproduced score grid, M08 arithmetic, graph parses | High for baseline behavior. Content validation checks schema/presence, not pedagogy. |
| Source pages/oEmbed identity and endpoint availability | High for point-in-time reachability/identity; not proof of captions, regional access, complete lecture quality or redistribution rights. Jazzy was blocked in this pass. |
| Primary math/robotics/planning references and algorithms | High for cited concepts, medium for mapping/teaching order; blueprints require expert review. |
| General retrieval/spacing/active-learning research | Supports a direction in studied contexts, not exact CoreLab thresholds, schedules, an individual outcome or time saved. |
| Separate nodes, goal membership, projected hard/soft edges and default order | Content-based expert judgment, medium; no comparative learner data. |
| Authoring/learning hours, capacity and future frontier relevance | Low/unmeasured. Planning scenarios only; no optimization guarantee. |

Evidence register: local code/data paths above; all four rounds retain the original count calculations and rebuttals. External sources are directly linked near their claims. [Karpicke & Blunt's primary-paper record](https://pubmed.ncbi.nlm.nih.gov/21252317/) supports retrieval in the studied science-learning task, not automatic programming transfer. Durable older courses are labeled as such; future model/library/runtime choices need a fresh compatibility check. The existing 28 videos were endpoint-audited, not all watched end-to-end. Claude's full 124-answer-key hand audit and approximately 27 construct-mismatch count were **not** independently reproduced; selected ambiguity/precision findings were checked directly.

Validation performed for this artifact:

- Both reviewer status files report `completed_round: 4`; rounds were appended before publishing status. Previous Codex round text and both Claude files were preserved.
- Matrix: exactly all 169 baseline IDs once, no extra candidate inserted as an original. Seven candidates listed separately.
- Appendix A: all 176 identities once, valid references, 319 unique hard edges, zero cycles, maximum depth 13 edges. Twenty-nine original prerequisite rows replaced; remaining rows explicitly retained.
- Essential bridges are named with downstream scope: trig, integration, covariance, spectral/least-squares, sensing, planning, timing, control, data quality and cognitive/HRI outcomes.
- `npm run validate:content` passed (169 topics, 31 lessons/assessments, 42 targeted questions/seven banks, 28 video resources); `npm test` passed **119 tests in eight files**, Node 24 on Linux. These establish current software/content invariants, not educational effectiveness of proposed v2.
- Production/app/curriculum files and historical progress/evidence were not edited. The pre-existing `next-env.d.ts` working-tree modification was preserved. No application build, browser/OS regression suite, or delayed learner pilot was needed or run for this documentation-only audit; no cross-platform result is claimed for v2.

## 18. Prioritized implementation roadmap — approval required

**P0: approve a bounded tranche, not the whole catalog.** Review this proposal and both final reviewer positions. Choose one goal and whether a qualified reviewer is available. Confirm immutable-evidence rules and the distinction between navigation, topic scope and assessment contract. No implementation is performed by this document.

**First 100 authoring hours (planning allocation, not delivery promise):**

| Hours | Concrete deliverable | Acceptance check |
| --- | --- | --- |
| 0–8 | Specify/version precision and prompt fixes, truthful no-lab recommendation text, correct M07/M08 references and demo-model bridges; pin/review ROS lab version | No v1 key/report changed; reviewer can reproduce M08 false failure and see an explicit supported v2 format/tolerance. No inaccessible link described as verified. |
| 8–14 | Pilot objective/evidence manifests and pinned contract/oracle versions | Every claimed objective maps to a task/check/reviewer; legacy scope retained. |
| 14–36 | M02 v2 dot/norm/projection pilot | Reviewed oracle, critical cases, genuine mutations and materially different assessment from worked code. |
| 36–54 | PY01 v2 small-function pilot; separate testing competence | Blank-file artifact, independent tests and test-suite mutations; no automatic broadening of old mean reports. |
| 54–68 | M08 Bayes/format pilot and small M09 covariance bridge; ambiguity corrections ML02/ML05 queued by impact | Self-contained prompts, safe format policy, reviewed tolerance and no leakage/independence confusion. |
| 68–78 | M01 algebra/trig/units readiness bridge | Known-skill placement plus fresh mixed-unit/radian tasks. |
| 78–90 | M12/R03/R04 planar then spatial-chain FK milestone | Frame/tool conventions, independent FK checks and declared planar/spatial scopes. |
| 90–100 | Mathematical/editorial/accessibility/mutation review and learner-pilot preparation | Predeclare outcomes, thresholds, exposure/assistance logging and delayed tasks. Reduce scope if review exceeds budget. |

This merges the useful parts of both estimates; it is not a measured productivity model. Delayed 7/21-day observations extend calendar time beyond the authoring budget. A precision hint alone does not make the original fraction acceptable or rewrite its score; provide a new valid contract when appropriate. If known defects block current learners, prioritize their correctly versioned fixes over a new visual. Add only the item types a pilot actually requires.

**P1: after pilot review.** Finish M05 integration before any full ODE dependency, M11/M17 numerics/spectral and R06 checks; commission the next candidate for the chosen goal. MAN: R17/R18/R19; MOB: R16/R20; RLLV: E16 and evaluated BC. Publish original scopes honestly when experiments fail; do not lower claims silently. Review false failures, assistance and delayed outcomes before changing level/readiness policy.

**P2: bounded policy implementation.** Only after approval: applicable-dimension/contract handling, a few scope-aware readiness warnings, legacy backup/evidence compatibility and an adjustable review budget. Migration must preserve hashes/signatures/version meaning, reject dangling topic references, round-trip restored progress and avoid automatic alias credit. Existing M02/PY01 evidence remains interpretable exactly as issued. Keep localhost security and local-owner trust limits. General engines come after demonstrated need.

**P3: expand by evidence and maintenance capacity.** Add goal capstones, external reviewer workflow and cognitive/HRI research tasks as resources permit. Recheck frontier artifacts every 6–12 months as an editorial choice; retire stale links/claims rather than delete history. Measure active work, independent delayed performance, failures, accessibility and abandonment. No release should claim 169 fully verified topics until those topics actually have reviewed teaching and evidence contracts.

## Appendix A. Complete canonical planning DAG

This table is a planning artifact only. All IDs denote retained evidence identities, not required study for every goal. `none` is an empty prerequisite list. Baseline rows not changed in section 4 are included explicitly so the graph can be checked without interpreting grouping prose. Preview/alternative capabilities described above are not extra hard edges. Do not apply this table to production before approving scopes and migration.

| ID | Proposed hard prerequisites |
| --- | --- |
| M01 | none |
| M02 | M01 |
| M03 | M02 |
| M04 | M03 |
| M05 | M01 |
| M06 | M03, M05 |
| M07 | M05 |
| M08 | M01 |
| M09 | M08 |
| M10 | M06, M04 |
| M11 | M03, M05, PY04 |
| M12 | M02, M03 |
| M13 | M10 |
| M14 | M08, M09 |
| M15 | M12, M06 |
| M16 | M07, M14, M13 |
| PY01 | none |
| PY02 | PY01 |
| PY03 | PY01 |
| PY04 | PY01, M03 |
| PY05 | PY04, M11 |
| PY06 | PY04, ML04 |
| PY07 | PY01 |
| PY08 | PY07, T02 |
| PY09 | PY04, PY08 |
| PY10 | PY03 |
| CPP01 | none |
| CPP02 | CPP01 |
| CPP03 | CPP02 |
| CPP04 | CPP01, CPP02 |
| CPP05 | CPP01 |
| CPP06 | CPP03, CPP05 |
| CPP07 | CPP01, T01 |
| CPP08 | CPP07, CPP02 |
| CPP09 | CPP05, CPP08 |
| CPP10 | CPP03, CPP08 |
| CPP11 | CPP05, M03 |
| CPP12 | CPP06, CPP09 |
| ML01 | PY04, M08 |
| ML02 | ML01, M06 |
| ML03 | ML01, M09 |
| ML04 | ML02, M03 |
| ML05 | ML04, M06 |
| ML06 | ML05, M10 |
| ML07 | ML03, M09 |
| ML08 | ML06 |
| ML09 | ML05, ML08 |
| ML10 | ML08 |
| ML11 | ML06, M08 |
| ML12 | ML10, M14 |
| T01 | none |
| T02 | none |
| T03 | T01 |
| T04 | PY07 |
| T05 | T02, T03 |
| T06 | T01, T05 |
| T07 | T03, PY09 |
| T08 | T06, T07 |
| R01 | M01, M02 |
| R02 | M01 |
| R03 | M12 |
| R04 | R03 |
| R05 | R04 |
| R06 | R04, M06 |
| R07 | R01, M06, M07, R04 |
| R08 | R01, R07 |
| R09 | R01, R02 |
| R10 | R01, R09 |
| R11 | R07, R08 |
| R12 | R07, M04 |
| R13 | R11, C05 |
| R14 | R06, R08 |
| R15 | R12, R14 |
| C01 | M05 |
| C02 | C01, M07, M03, M06 |
| C03 | C01 |
| C04 | C02, M17 |
| C05 | C04 |
| C06 | C02, M08 |
| C07 | C06, M09, M03 |
| C08 | C07, R03 |
| C09 | C01, M05, M11 |
| C10 | R07, C04 |
| C11 | C13, M13 |
| C12 | C07, M06 |
| C13 | C05, M10 |
| C14 | R11, C13 |
| C15 | C10, C11 |
| S01 | M07, M11 |
| S02 | S01, R02 |
| S03 | T01, PY01 |
| S04 | R03 |
| S05 | S03 |
| S06 | S05, R09, S07 |
| S07 | none |
| S08 | S02, C06 |
| S09 | S08, S07 |
| S10 | S05, S06 |
| S11 | S02, PY06 |
| S12 | S10, CPP10 |
| V01 | PY04 |
| V02 | V01, M03 |
| V03 | V01, M12 |
| V04 | V03, M10 |
| V05 | V02, V03 |
| V06 | ML05, V02 |
| V07 | V06, ML07 |
| V08 | V07, ML07 |
| V09 | V08, C07 |
| V10 | V06, ML07 |
| V11 | V04, M17 |
| V12 | V11 |
| V13 | V12, PY05 |
| V14 | V07, ML08 |
| V15 | ML09, V07 |
| V16 | V09, V14 |
| V17 | V11, C12 |
| V18 | V14, V15 |
| V19 | V13, ML11 |
| V20 | V18, V19 |
| RL01 | PY01, M08 |
| RL02 | RL01, M08 |
| RL03 | RL02, M08 |
| RL04 | RL03, PY02 |
| RL05 | RL03, M09 |
| RL06 | RL04, RL05 |
| RL07 | RL06, ML04 |
| RL08 | RL02, ML05 |
| RL09 | RL08, RL03, RL05 |
| RL10 | RL09, ML06 |
| RL11 | RL07, RL09 |
| RL12 | RL05, RS02, ML07 |
| RL13 | RL09, C02 |
| RL14 | RL02 |
| RL15 | RL13, RL14 |
| RL16 | RL13, S02 |
| RL17 | RL01, ML06 |
| RL18 | RL11, RL17 |
| RL19 | RL02, S01, ML06 |
| RL20 | RL02, RL08 |
| RL21 | RL13, S07 |
| RL22 | RL10, RL02 |
| RL23 | RL06, ML08 |
| RL24 | RL13, ML10 |
| E01 | RL02 |
| E02 | PY02 |
| E03 | E02, C07 |
| E04 | PY07 |
| E05 | E02 |
| E06 | E05, R05, R18 |
| E07 | RL17 |
| E08 | RL02, ML06 |
| E09 | V13, V14 |
| E10 | ML09, V14 |
| E11 | ML11, E07 |
| E12 | E07, E10 |
| E13 | E04, E06, E08 |
| E14 | E05, E09, E10 |
| E15 | E13, E14 |
| RS01 | none |
| RS02 | RS01, M08 |
| RS03 | RS02, M09 |
| RS04 | RS02, T02 |
| RS05 | RS02, M09 |
| RS06 | RS01 |
| RS07 | RS06, RS02 |
| RS08 | RS06 |
| RS09 | RS04, PY08 |
| RS10 | RS03, RS08 |
| M17 | M04, M11 |
| R16 | M08, M09 |
| R17 | R04, M05 |
| R18 | E02, R03 |
| R19 | R07, R06, C03 |
| R20 | R02, R03, R16, M09 |
| E16 | PY04, PY07, M09 |

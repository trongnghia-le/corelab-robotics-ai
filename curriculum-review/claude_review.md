# CoreLab curriculum review: Claude

Author: Claude (Opus 5.5). Independent reviewer: Codex. Date: 2026-10-30.
Scope: review only. No production curriculum, application code or published assessment contract was changed. Everything here needs human approval before implementation.

## Round 1: independent analysis

Codex's review was not read before this round was written.

### 1.0 How to read this

**Claim IDs.** Major claims are `C1`–`C10` (section 1.3). Please ACCEPT, REJECT or MODIFY them by ID.

**Verification labels used for sources**

| Label | Meaning |
|---|---|
| [link] | URL returned HTTP 200 on 2026-10-30. This shows the page exists, not that every part suits the topic. |
| [meta] | Title, authors, venue and year confirmed through Crossref or the arXiv API on 2026-10-30. |
| [abs] | The stated finding was read in the abstract or an abstract-level source. |
| [toc] | Chapter titles read from the source's own table of contents. |
| [mem] | From my own knowledge and not checked this session. Must be checked before use. |

No timestamps are given anywhere, because none were verified.

**Numbers I measured versus numbers I estimated.** Everything in section 1.1 was computed from the repository. All study hours are my own engineering estimates, with about ±40% uncertainty. CoreLab has no learner timing data that I used, and I did not open `.local/`.

### 1.1 What the repository shows

Measured from `corelab/curriculum_graph_v1.json`, `content/`, `lib/engine.ts`, `lib/labs.ts`, `lib/reviews.ts`, `scripts/lab-tests.py` and `docs/guide.md`.

**Coverage**

| Finding | Evidence |
|---|---|
| 169 topics, 310 edges, depth 14; 90 P0, 59 P1, 20 P2 | Graph file |
| 31 of 169 topics have a lesson and diagnostic, all P0. 59 P0 topics have neither. | `content/lessons`, `content/assessments` |
| The recommender only offers topics with lessons, so the learner hits a wall after 31. 24 topics are unlocked at that point and none can be offered. | `recommend()` filters on `available`; frontier computed |
| 42 practice questions across 7 topics; 2 of 8 practice labs are verified | `content/practice`, `lib/practice.ts` |

**Assessment validity (the most serious problem)**

| Finding | Evidence | Why it matters |
|---|---|---|
| All 31 diagnostics have the same shape: 1 C choice, 3 M numeric, 1 T short answer | Audit script | Knowledge type does not change the assessment, although `knowledgeTypes` exists in `lib/assessment.ts` |
| C rests on one item, and 30 of 31 are two-option | Audit script | A blind guess gets the C item right 50% of the time, so one item cannot establish conceptual understanding |
| The 80% threshold actually means 4 of 4 | 3 of 4 is 75% | A learner with 90% per-item skill fails 34% of attempts; this is noisy in both directions |
| There is one fixed form per topic | One `.v1.json` per topic | Retakes reuse the same items, so a pass can reflect memory of the form. The retesting meta-analysis found larger practice effects on identical forms [abs] |
| The T prompt appears verbatim in the lesson in 31 of 31 topics | String match | The only "transfer" item is not unfamiliar, and it is also ungraded |
| About 35 of 93 numeric items appear to reuse worked-example numbers (24 of 31 lessons have at least one) | Heuristic: prompt numbers and answer all appear in the worked example. It can give false positives on small integers. Exact reuse confirmed by hand in R04 q2/q3 and M04 q4. | Diagnostics partly measure recall of the page |
| No item kind can test a derivation | `kind` is `choice`, `number` or `short` | "M" means substituting numbers. PY01's M items are code tracing (`sum(range(4))`), so the label is also wrong there |
| I has no quiz items and comes only from labs, which exist for M02 and PY01 | `reportSchema` enum | L2 is unreachable for 167 of 169 topics |
| The two L2 labs test only `dot()` and `mean()` | `scripts/lab-tests.py` | L2 in "Python Fundamentals" can mean writing `mean()`. L2 in "Vectors" does not test projection |
| Both of those functions appear solved in their own lessons | M02 and PY01 "Reference implementation" | Independence rests entirely on the learner not having just read the answer |
| 27 topics target L3, but the engine stops at L2 | `masteryFor`: `level` is at most 2 | `target_level` cannot be met for those topics |
| T is earned by passing the same form twice, 7 days apart | `masteryFor` | The guide correctly calls this retention only, but the single T dimension still merges retention and transfer |
| Forgetting never affects readiness | Guide: failed reviews keep historical evidence; recommender checks `level >= 1` | L1 from long ago unlocks dependents forever |

**Engine defects found while reading**

1. At L1, `recommend()` tells every topic to "run local tests, and import the report", but `reportSchema` only accepts M02 and PY01. For 29 of 31 lessons this instruction cannot be followed.
2. `dimensions.I >= 2` is part of the "done" check, so these 29 topics can never leave the candidate list at L1. They only drop in rank.
3. Review stages cap at 21 days, per topic. Steady-state load is N/21 reviews per day: 8.0 per day at 169 topics. At an assumed 6 minutes each, that is about 48 minutes per day, indefinitely.
4. `goal` is a domain name, so a goal cannot express "train a visuomotor policy".

**Learning experience**

| Finding | Evidence |
|---|---|
| Lessons are about 600 words of text on one template (27 share 11 headings; 4 share 8) | Heading audit |
| 30% of lesson words (5,319 of 17,724) are sentences repeated in at least 10 lessons | Sentence audit |
| 22 of 31 lessons have no interactive model; 6 have no video | `lesson-media.v1.json` |
| `estimated_minutes` is 55 for most lessons, including Multivariable Calculus and Rigid-Body Dynamics; total about 28 hours for 31 topics | Frontmatter |
| Some video mappings do not fit: `3b-gradient` for M06 (Jacobians), and `mr-jacobian` (Space Jacobian) for a planar R06 lesson that never defines a twist | Media map plus lesson text |
| References point at site homepages rather than chapters | `source_refs` |

**Content gaps.** Searched across all lessons, plus titles and overview text. These are the terms the search supports:

| Missing or nearly missing | Search result |
|---|---|
| Eigenvalues | No lesson. The only overview hit is `CPP11`, which is the Eigen library. C04 still needs poles. |
| Screws, twists, PoE | "screw" and "twist" have no hits; PoE gets one sentence in R04. Modern Robotics, the main source, is built on them. |
| Motion planning | E02 covers A* only. No hits for RRT, PRM. C-space appears only in R02. |
| Trajectory generation | No hits for "time scaling" or "spline" |
| Manipulator control | No hits for impedance, force control, computed torque, operational space |
| Mobile robots and localization | No hits for wheeled, differential drive, localization, particle filter, occupancy |
| Sensors as a subject | "encoder" and "lidar": none. Sensors appear only as example contexts. C08's only hardware prerequisite is R09, which is about actuators. |
| Information theory | No hits for entropy, Kullback; one "KL" in the RL10 overview |
| Signals | No hits for Fourier, aliasing in the signal sense, transfer function, Bode, Laplace |
| Nonlinear least squares | No hits for Gauss-Newton, Levenberg, bundle adjustment, factor graph |
| Robot data | No hits for teleoperation; "dataset" appears only in ML01 and RL18 |
| HRI | No hits |

**Graph defects**

| Defect | Evidence |
|---|---|
| A* (E02) needs 14 ancestors, including RL and control | E02 → E01 → RL02, C02 |
| PyTorch (PY06) has one dependent, S11. ML06, V06 and RL10 do not require it. | Graph |
| Lie Theory (M15) has no dependents, although V17 and C12 use it | Graph |
| Trajectory-optimizing C13 depends on MPC (C11), an inverted order | C13 → C05, C11 |
| R05 (IK) does not depend on R06 (Jacobian), although numerical IK does | Graph |
| S06 (hardware) does not require S07 (safety) | Graph |
| E04 (skills) requires hierarchical RL; E07 requires Transformers | Graph |
| 11 "Advanced X" catch-all nodes have no assessable objective | M16, PY10, CPP12, ML12, T08, R15, C15, S12, V20, E15, RS10 |
| 29 of 310 edges are transitively redundant | Audit script (for example RL02→M08, R07→R01) |
| 25 non-P2 topics have no dependents | Audit script |
| Priority inversion: Diffusion/Flow policies (E11) and VLA (E12) are P2 with target 1, whereas Object Detection (V08) is P0 with target 3 | Graph |
| Overlap: M12 and R03 teach the same transforms and share `mr-transform`; T04 and PY07 share `mit-testing` | Lessons and media map |
| ROS docs point to Humble, which reaches EOL in May 2027; Jazzy runs to May 2029, and Lyrical (LTS, shipped May 2026) to May 2031 | `lib/resources.ts`; docs.ros.org distributions page via search |

### 1.2 Learning-science evidence and its limits

I use this evidence narrowly. Nearly all of it comes from settings other than self-study of robotics, so effect sizes do not transfer directly.

| Source | Finding used | Limit |
|---|---|---|
| Crouch et al. 2004, *Am. J. Phys.* 72:835, doi:10.1119/1.1707018 [meta, abs] | Passive observers of demonstrations understood no better than students who saw none; predicting first helped | Physics classrooms; single institution |
| Hundhausen et al. 2002, *J. Vis. Lang. Comput.* 13:259, doi:10.1006/jvlc.2002.0237 [meta; finding from memory, mem] | How learners engage with a visualization matters more than what it shows | Algorithm visualization; abstract not retrieved |
| Koedinger et al. 2015, L@S, doi:10.1145/2724660.2724681 [meta, abs] | Learning associated with each activity done was about 6× that of each video or page | Correlational, psychology MOOC, self-selected; causal methods applied |
| Freeman et al. 2014, *PNAS* 111:8410, doi:10.1073/pnas.1319030111 [meta, abs] | Active learning raised exam scores and lowered failure | Classroom STEM |
| Deslauriers et al. 2019, *PNAS* 116:19251, doi:10.1073/pnas.1821936116 [meta, abs] | Students learned more from active instruction yet felt they learned less | Physics; supports showing evidence over asking for feelings |
| Roediger & Karpicke 2006, doi:10.1111/j.1467-9280.2006.01693.x; Rowland 2014, doi:10.1037/a0037559; Adesope et al. 2017, doi:10.3102/0034654316689306 [meta] | Retrieval beats restudy for retention | Often verbal material |
| Dunlosky et al. 2013, doi:10.1177/1529100612453266 [meta] | Practice testing and distributed practice rated highest utility | Review, not robotics-specific |
| Cepeda et al. 2008, *Psych. Science* 19:1095, doi:10.1111/j.1467-9280.2008.02209.x [meta, abs] | The best review gap grows with the desired retention interval | Facts, up to 1 year |
| Rohrer et al. 2015, *J. Ed. Psych.* 107:900, doi:10.1037/edu0000001 [meta, abs] | Mixed practice forces choosing the method | School mathematics |
| Sinha & Kapur 2021, *RER* 91:761, doi:10.3102/00346543211019105 [meta, abs] | Problem solving before instruction: g = 0.36 [0.20, 0.51] across 53 studies | Depends on design fidelity |
| Kirschner et al. 2006, doi:10.1207/s15326985ep4102_1; Kalyuga et al. 2003, doi:10.1207/s15326985ep3801_4 [meta] | Novices need guidance; the best support reverses with expertise | Tension with the row above: keep diagnostics short, and do not leave novices to discover derivations |
| Koedinger et al. 2012, *Cog. Sci.* 36:757, doi:10.1111/j.1551-6709.2012.01245.x [meta] | The best instruction depends on the knowledge component type | Framework, not an effect size |
| Hausknecht et al. 2007, *JAP* 92:373, doi:10.1037/0021-9010.92.2.373 [meta, abs] | Retest gain of about .26 overall, larger with identical forms | Cognitive ability tests in selection |
| Rodriguez 2005, *EMIP* 24:3, doi:10.1111/j.1745-3992.2005.00006.x [meta, abs] | Three options suffice and allow more items per unit of time | Achievement tests |
| Guo et al. 2014, L@S, doi:10.1145/2556325.2566239 [meta, abs] | Shorter videos held attention better | Measures engagement, not learning |
| Bastani et al. 2025, *PNAS* 122, doi:10.1073/pnas.2422633122 [meta, abs] | Unguarded AI became a crutch and later solo performance fell; guardrails mostly removed the harm | One high school in Turkey; novel tool at the time |
| Barnett & Ceci 2002, doi:10.1037/0033-2909.128.4.612 [meta] | Transfer has to be defined along explicit dimensions | Taxonomy, so it specifies what to test but not how much |

### 1.3 Major claims

**C1. Fix evidence validity before writing more content.**
- *Evidence:* section 1.1 assessment table.
- *Reasoning:* the mission's metric is demonstrated competence per hour. With one fixed 4-item form, CoreLab cannot currently measure that metric. Writing 138 more lessons on this template would multiply a defect.
- *Benefit:* every later decision can be checked with data, and L1 becomes meaningful.
- *Cost:* I estimate 40–80 authoring hours for the assessment engine v2 and generators, then 2–4 hours per topic (uncertain).
- *Risks:* over-engineering a single-user tool; 12-item forms cost learners about 10 more minutes per topic.
- *Confidence:* high on the defect; medium on the specific form length.

**C2. Replace one 169-node sequence with a spine, tracks and capstones.**
- *Evidence:* graph has 115 live nodes after consolidation (section 1.8). No single learner needs all of it. Goal closures are 66–79 nodes.
- *Reasoning:* breadth is justified as a map, not as a study plan. A capstone defines what "enough" means for a goal.
- *Benefit:* about 17–26% fewer estimated hours per goal (section 1.11).
- *Cost:* graph v2 and goal selection.
- *Risks:* tracks could close off breadth, and hours are estimated rather than measured.
- *Confidence:* medium-high on the structure; low on exact hours.

**C3. Separate prerequisite readiness from mastery.**
- *Evidence:* the recommender requires `level >= 1` of the entire prerequisite, while the graph's own policy says prerequisites are "recommended not permanent barriers". R06 needs one derivative pattern from M06, not all of M06.
- *Reasoning:* a readiness probe tests only the skills the dependent topic uses. It answers "can I start?", which is different from "have I mastered it?".
- *Benefit:* earlier starts, and failures that point at a specific missing skill.
- *Cost:* 3–8 mapped items per hard edge, about 190 hard edges at full build. Build for the spine first.
- *Risks:* learners may advance with fragile foundations, so readiness must never count toward mastery or display as a level. Skill mapping is authored judgment and may be wrong.
- *Confidence:* medium-high.

**C4. Add the missing robotics core: 11 new nodes.**
- *Evidence:* the gap table above. Modern Robotics Ch. 9, 10, 11 and 13 have no matching topic [toc].
- *Reasoning:* motion planning and manipulator control are central to robotics, and spectral methods support IK, control, vision and ML.
- *Benefit:* a learner can actually complete a manipulation or mobile capstone.
- *Cost:* 105 added study hours across spine and tracks (M18, M20, R18–R20 and E16 are track-level; M17, M19, R16 and R17 are spine at 38 hours total).
- *Risks:* more content at a time when coverage is already thin, so these need scheduling ahead of lower-value lessons. E17 is registry-only.
- *Confidence:* high for M17, R17, R18, R19. Medium for R20, M19, E16.

**C5. Remove 11 catch-all nodes, merge 36, and defer 19.**
- *Evidence:* the 11 "Advanced X" nodes have no assessable objective. M12/R03 and T04/PY07 duplicate content.
- *Reasoning:* a node should exist only if it has a distinct skill and a possible assessment. Removed topics stay in a research registry, so nothing is lost as a reference.
- *Benefit:* less to author and assess. The deletion itself saves no learner time, because no one would finish those nodes anyway.
- *Cost:* alias mapping so existing M12, T04 and similar evidence remains valid.
- *Risks:* over-merging can hide a skill. C02+C04 and RL09+RL10 are the merges I am least sure of, since each joins a substantial pair.
- *Confidence:* high for removals; medium for merges.

**C6. Teach spatial kinematics with PoE; do not stay with planar 2R and do not add DH.**
- *Evidence:* R04 targets L3 but covers only a planar 2R arm. MR Ch. 3–5 use screws and PoE [toc], and DH is only Appendix C [toc].
- *Reasoning:* one representation carries through FK, Jacobian, and dynamics, and maps well to Lie-based estimation later.
- *Benefit:* the existing `mr-jacobian` video and MR code library become usable.
- *Cost:* about 4 hours more on R03.
- *Risks:* industry documents and many textbooks use DH; learners will need a short conversion note. Abstract notation may slow early learners, so the planar case stays as the first worked example.
- *Confidence:* medium-high.

**C7. Add machine-checkable item types so M, I and T become real evidence.**
- *Evidence:* no current item can test a derivation; L2 exists for two topics.
- *Reasoning:* symbolic expressions can be checked by evaluating at random points. Hidden tests can use randomized parameters. Mutation-kill scoring tests debugging ability directly.
- *Benefit:* L2 becomes available across most topics, without a human reviewer.
- *Cost:* new contract versions; existing v1 stays untouched.
- *Risks:* expression equivalence does not prove the reasoning, and step-ordering items can be gamed. Learners can read test sources, and A0 stays self-declared.
- *Confidence:* high on feasibility; medium on how well it captures derivation skill.

**C8. Fix review scheduling: longer intervals, per skill, in the form of fresh variants.**
- *Evidence:* the 21-day cap gives about 48 minutes per day at 169 topics. Cepeda 2008 supports longer gaps for longer retention.
- *Reasoning:* a multi-year curriculum should extend intervals: 1, 3, 7, 21, 60, 150, 365 days. At 115 nodes, long-run load falls to about 0.3 reviews per day.
- *Benefit:* roughly 30–45 minutes per day freed at full scale, on the assumptions above.
- *Cost:* small scheduler change plus fresh variants, which depend on C7.
- *Risks:* evidence is mostly for facts, not procedural or modelling skills. Long gaps may let skills lapse, so failures should shorten the interval. An FSRS-style fitted scheduler [link: github.com/open-spaced-repetition/fsrs4anki] needs data that a single user lacks.
- *Confidence:* medium-high on removing the cap; low on the exact schedule.

**C9. Vary the workflow by knowledge type; video is not the default step.**
- *Evidence:* Koedinger 2012, Crouch 2004, Koedinger 2015, Guo 2014.
- *Reasoning:* a Git topic does not need Derive; a Bellman topic does. A prediction before each demo is cheap and supported.
- *Benefit:* less passive time.
- *Cost:* six templates in place of one.
- *Risks:* a video-first request is part of this brief, and some learners rely on video. I keep video as the default entry only for mathematics and physical modelling.
- *Confidence:* medium.

**C10. Do not certify open-ended work automatically.**
- *Evidence:* the current guide already refuses this; Bastani 2025 shows AI help can mask a lack of skill.
- *Reasoning:* L3 needs novel application reviewed by a qualified human. L4 needs reproducible critical evaluation. LLM or self-review remains provisional. This includes reviews from me or Codex.
- *Benefit:* the credential keeps its meaning.
- *Cost:* for a single user with no reviewer, L3 and L4 may stay empty.
- *Risks:* learners may lose motivation; mitigate with a visible "reviewed: no" state that does not block progress.
- *Confidence:* high.

### 1.4 Architecture

**Layers**

| Layer | Contents | Rule |
|---|---|---|
| Spine | 54 live topics, about 540 h | Everyone in robotics or embodied AI needs this. Tested to L2 where a lab exists. |
| Tracks | MAN manipulation, MOB mobile/legged, RLL robot learning, PER perception, SYS robot software, RES research | Chosen by goal; each ends in a capstone |
| Just-in-time registry | 19 deferred plus the removed catch-alls | Reference only until a project pulls it. No certification unless an assessment exists. |

**Knowledge tiers.** Foundational (F) topics need retention and delayed checks. Applied (A) topics are assessed through use. Research (R) topics are never auto-certified.

**Capstones.** Each is machine-checkable in simulation, with hidden scenarios, and needs no hardware.

| Path | Capstone | Evidence |
|---|---|---|
| Spine (20 h) | Model, simulate and stabilize an unseen arm or pendulum with an estimator | Hidden scenarios; report |
| MAN (40 h) | Pick and place in MuJoCo or Drake with planning, IK and impedance | Success rate on unseen object poses, plus safety limits |
| MOB (40 h) | Quadruped policy or localization stack, tested with sim-to-sim transfer | Metrics over seeds with CIs |
| RLL (40 h) | Collect demonstrations, train ACT or Diffusion Policy, compare to a baseline | Held-out initial states, IQM with CI |
| PER (35 h) | Calibration plus visual odometry on a public sequence | ATE/RPE on a held-out sequence |
| SYS (25 h) | ros2_control mock hardware, watchdog, latency budget | Fault-injection tests |

**Community curriculum vs personal paths.** There is one canonical versioned graph and item bank. A personal path is derived, not separately authored: goal capstone → backward closure → remove what placement probes prove → schedule. I recommend rule-based personalization only. Knowledge tracing or similar fitted models need data that a local single-user tool does not have, and I would revisit that only if pooled, consented data ever exists.

**Readiness vs mastery.** Add a separate `ready` state per edge with an expiry. It unlocks study, but it never raises C/M/I/T or any L level.

**Study in parallel:** M02∥PY01; M03∥PY04; R03∥V03; M06∥R06 (use R06 as the motivating case); M07∥S01; ML05∥PY06; C07∥M09 refresh; R07∥S02; T01 and T02 from week one; RS01 alongside the first experiment.

### 1.5 Recommendations

**Additions (proposed IDs).** M17 Spectral Methods & Least Squares; M18 Information Theory Essentials; M19 Signals & Frequency; M20 Nonlinear Least Squares; R16 Sensors & Measurement; R17 Trajectory Generation; R18 Motion Planning; R19 Manipulator Control; R20 Mobile Robots & Localization; E16 Robot Data Collection; E17 HRI & Shared Autonomy (registry only).

**Removals (to registry).** M16, PY10, CPP12, ML12, T08, R15, C15, S12, V20, E15, RS10.

**Merges** (absorbing topic ← absorbed):

| Into | From | Into | From |
|---|---|---|---|
| R03 | M12 | V06 | V07 |
| PY01 | PY03 | V08 | V10 |
| M11 | PY05 | V13 | V12 |
| M09 | RS03 | ML08 | ML10, V14, V18 |
| PY07 | T04 | ML09 | V15 |
| T01 | T03 | RL02 | RL03, E01 |
| RS04 | PY08, T05, RS09 | RL05 | RL06 |
| PY09 | T07 | RL10 | RL09 |
| CPP03 | CPP04 | RL13 | RL15 |
| CPP05 | CPP06 | S09 | RL16 |
| CPP07 | CPP08 | E04 | RL20 |
| ML03 | ML07 | E07 | E11 |
| C02 | C04 | E08 | RL19 |
| C03 | C09 | R07 | R12 |
| C07 | C06 | RS02 | RS05 |
| S06 | S10 | | |

Existing IDs stay as aliases so that recorded evidence stays valid. E13 becomes capstone content.

**Defer to just-in-time.** M14, PY09, CPP09, T06, R10, C10, S11, V09, V16, V19, RL18, RL21, RL22, RL23, RL24, E03, E09, E14, RS08. PY09, T06 and RS08 remain in tracks, but they start only when a need arises.

**Prerequisite changes**

| Change | Reason |
|---|---|
| E02 ← PY02 only (remove E01) | A* does not need RL or control |
| R05 ← R06 (M17 soft) | Numerical IK uses the Jacobian |
| R04 ← R03 only (remove M04) | FK does not need rank or nullspace |
| R07 ← R06, M07, R01 (retain) | Confirmed; no change |
| C13 ← C05; C11 ← C13, M13 | MPC is receding-horizon optimal control |
| C08 ← C07, R16 (remove R09) | Fusion needs sensors, not actuators |
| C03 ← C01 (C02 soft) | PID is usable before state space |
| C01 ← M05 (R01 soft) | Control does not need mechanics as a gate |
| ML06, V06 ← PY06; PY06 ~ML04 | Training requires the framework |
| RL17 ← ML06, RL01 (RL02 soft) | BC is supervised; DAgger uses the MDP view |
| RL14 ← RL02 (remove RS02) | Over-gated |
| E04 ← S02 (remove E01, RL20; RL13 soft) | Skills don't require HRL |
| E07 ← RL17, E16 (ML09, ML11 soft) | ACT and Diffusion each need only part of these |
| S06 ← S05, S07, R09 | Safety must precede hardware |
| S09 ← S08 (RL13 soft) | Sim2real also applies to classical control |
| M15 ← R03, M06; V17 ← M15, M20 | Connects an orphan node to what uses it |
| V11 ← M17; M13 ← M17 | DLT and QP analysis use SVD and spectra |
| Drop 29 redundant edges | Display only; no change in ancestors |

Validation: the proposed graph has 115 live nodes, 190 hard edges, 18 soft edges and depth 12, with no cycles (scripted check). Ancestor counts change as follows: E02 14→2, C03 8→3, E06 23→16, R04 8→6. **E07 rises from 20 to 23** and V17 from 23 to 26, because I added real dependencies. Merged nodes also make these counts imprecise for comparison, since one new node may hold two old ones.

### 1.6 Learning experience

**Workflow by knowledge type.** The full flow is Diagnostic → Watch → Visualize → Predict → Understand → Derive → Implement → Verify → Transfer → Review. Each type uses a subset and may reorder it.

| Archetype | Topics | Sequence | Default time split |
|---|---|---|---|
| A. Mathematical concept | M*, RL02 | Probe → Predict with a visual → short video → Derive with fading support → numeric code check → Transfer → Review | 35% derivation and problems, 15% video and visual, 35% code, 15% checks |
| B. Algorithm | R05, R18, C07, RL05, RL10, ML05 | Probe → Predict on a small case → pseudocode and derivation → Implement → hidden tests → seeded debugging → Transfer | 60% implementation and debugging |
| C. Physical modelling | R01, R07, R08, C02, S01 | Simulate and predict → video → free-body or energy derivation → compare to simulator → break an assumption | 40% simulation |
| D. Tool and systems skill | T*, CPP*, S03, S05 | Do a small task → broken-repository debugging → build → reuse later. Video only if the tool's workflow is hard to see from text. | 80% hands-on |
| E. Applied ML practice | V08, ML08, E07, E10 | Run a baseline → break it → ablate → read the source paper → evaluate on held-out data | 50% experiments |
| F. Research judgment | RS06, RS07, E12, E14 | Read → claim-evidence table → narrow reproduction → human review | Reviewed only |

**Text budget.** Prose is support, about 300–500 words per lesson, mostly captions and step instructions. The repeated 30% can move into shared interface text.

**Diagnostics at the start stay short (5 minutes or less).** Failure is expected there, and the pretest is for orientation, not a gate. That respects both the pretesting evidence and the novice-guidance evidence.

**Interactive visualizations, in priority order.** Each model must ask for a prediction before revealing a result, and interaction never awards mastery. CoreLab has PID, vectors, matrices, gradient descent, FK, Jacobian, Q-learning and convolution.

| Priority | New model | Topic | Must let the learner discover |
|---|---|---|---|
| 1 | SVD as circle→ellipse, with pseudoinverse | M17 | Singular values as stretch; rank loss |
| 1 | Manipulability ellipsoid (extends `jacobian`) | R06 | Directions lost near singularity |
| 1 | Kalman ellipses | C07 | Gain vs Q and R; overconfidence under a wrong model |
| 1 | Frame and rotation order in 3D | R03 | Non-commutativity; body vs space frame |
| 1 | Phase portrait and linearization | C02, M07 | Local vs global stability |
| 2 | LQR Q/R trade-off | C05 | Effort vs error; model mismatch |
| 2 | RRT growth in C-space | R18 | Narrow passage failure |
| 2 | MC vs TD on the same trajectories | RL05 | Bias and variance |
| 2 | PPO clip curve and KL | RL10 | When clipping does nothing |
| 2 | Computation graph | ML05 | Reverse accumulation |
| 2 | Bayes base rate | M08 | Base rate neglect |
| 3 | Sampling and CI coverage | M09 | Meaning of a CI |
| 3 | Pinhole and epipolar geometry | V03, V11 | Ray constraint |
| 3 | Friction cone | R08 | Stick and slip |
| 3 | Time scaling | R17 | Limit-driven timing |
| 3 | BC vs multimodal action target | RL17, E07 | Why MSE averages modes |

I estimate 4–12 hours per model. External resources can stand in, such as Seeing Theory for probability and CNN Explainer for CNNs.

### 1.7 Assessment and mastery

**Preserved:** C/M/I/T, L0–L4, A0–A3. Published v1 contracts stay as they are; everything below is a new contract version.

**Evidence rules**

| Level | Requires | Verified by |
|---|---|---|
| Ready (not a level) | Edge-specific probe, expires | Machine |
| L0 | Nothing verified | n/a |
| L1 | C and M gates on a fresh form | Machine, A0 declared |
| L2 | L1 plus I from hidden tests with randomized parameters, on a lab that spans the topic | Machine, A0 declared |
| L3 | L2 plus delayed retention on new variants plus an unfamiliar transfer task | Machine parts, plus human review of open work |
| L4 | Reproducible critical evaluation or extension | Qualified human review only |

**T is displayed as two sub-evidences, T-ret and T-trans,** while remaining one dimension in the framework. A retest with different numbers supports T-ret only.

**Integrity limit, to be stated honestly in the UI.** Assistance is self-declared, sources are inspectable, and the signature key sits on the learner's machine. A signature shows that this runner produced the report; it does not prove who did the work. "Verified" should read as "independently attested" unless a human reviewed it.

**Default PASS rules (proposal, thresholds uncertain)**

| Rule | Value | Reason |
|---|---|---|
| Form | 12 items: at least 4 C, at least 4 M | 4/4 passes a 90% learner only 66% of the time; ≥10/12 passes that learner 89%. For a 60% learner: 13% vs 8%. |
| Options | 3 or more plausible distractors from known misconceptions; no two-option C items | Rodriguez 2005; 50% guess rate today |
| Threshold | ≥80%, all critical items correct, every dimension gated separately | Keeps the current policy |
| Bank | At least 3× form size; parameterized generators wherever possible | Fresh forms |
| Retake | New variants only, at least 24 h after a failure; exposed items never count | Hausknecht 2007 |
| Solutions | The lesson never shows the solved lab or diagnostic numbers | Removes leakage |
| Lab | Hidden randomized tests covering all objectives; mutation-kill part for test writing | Stronger I |
| AI use | Any AI help makes the attempt A1 or higher; only a later fresh A0 counts | Bastani 2025 |
| Decay | A failed review removes `ready` for dependents until repaired; the historical record stays | Readiness should reflect the present |

The 12-item form gives only a small improvement at the low end; its main gains are fewer false failures and much wider coverage.

**New item kinds:** `expression` (random-point equivalence check), `matrix`, `ordered-derivation` (Parsons-style), `error-locate`, `code-hidden-test`, `mutation-kill`, `prediction-then-observe`.

**Gate codes in the matrix**

| Code | Meaning |
|---|---|
| Q | Fresh objective form, L1 |
| L | Hidden-test lab, L2 |
| A | Artefact: machine checks count; open parts are rubric-reviewed and unverified without a human |
| X | Delayed unfamiliar transfer; L3 only with human review |
| N | No certification; reference only |

**Assessment template per archetype.** With the focus column in the matrix, this gives every topic its required fields. Topic-specific items are authored at build time, and until then this is a specification.

| Field | A Math | B Algorithm | C Modelling | D Tool/systems | E Applied ML | F Research |
|---|---|---|---|---|---|---|
| Objective verbs | derive, compute, interpret | implement, analyze, debug | model, predict, validate | configure, diagnose, build | baseline, ablate, evaluate | critique, reproduce, argue |
| Diagnostic | 5 min, 5–6 mixed items | Trace a small run | Predict a simulation | Do a small task | Predict a metric change | Find a claim in an abstract |
| Concept check | Misconception MCQ | When it fails, complexity | Which assumption broke | Why this command or config | Which metric or split | Evidence vs claim |
| Derivation | Ordered proof and expression | Update rule | Equations of motion or energy | Not required | Loss or metric only | Not required |
| Implementation | Numeric code with hidden tests | Hidden tests, randomized | Simulator vs analytic | Repo reaches a required state | Reproducible script | Narrow reproduction |
| Debug and verify | Find a wrong step | Seeded bugs, mutation kill | Find bad parameter or frame | Broken repo or environment | Leakage or label bug | Find the flawed analysis |
| Transfer | New context, new numbers | New constraints | New mechanism | New failure | New dataset or shift | New paper |
| Retention | Variants at 7, 21, 60 days | Reimplement from blank at 21+ days | Re-predict variant | Used in later topics | Rerun on a variation | Not scheduled |
| Remediation | Link to the specific step | Failing-test explanation | Compare traces | Runbook | Error analysis | Reviewer comment |
| PASS | Q, then L if coded | Q + L | Q + L | L | Q + A or L | Human review only |

### 1.8 Review matrix: all 169 topics, plus 11 proposed

Actions: KEEP, RESCOPE, MERGE→target, DEFER, REMOVE, REMAP, NEW. Tier: F, A, R. Path: S, MAN, MOB, RLL, PER, SYS, RES, J (registry), X (removed). Mix: V video, Z interactive, S simulation, D derivation, W worked example, C code, P paper. Hours are estimates. Targets: `3→2` means the current target is changed.

Totals: 48 KEEP, 54 RESCOPE, 36 MERGE, 19 DEFER, 11 REMOVE, 1 REMAP, 11 NEW. Rows: 169 existing + 11 new = 180. Live after consolidation: 115. Proposed L3 targets: ML05, R06, C05, C07, RL10, E07 (down from 27).

| ID | Topic | Action | Tier | Path | h now→new | Hard prereq ~soft | Mix | Gate | Tgt | Focus: transfer task, misconception, note |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | Mathematical Basics | RESCOPE | F | S | 6→4 | none | Z W C | Q | 2→1 | Readiness probe first; lesson only on failure. T: derive a calibration inverse with units. Mis: function vs formula; unit-free reasoning. |
| M02 | Vectors | KEEP | F | S | 8→8 | M01 | Z V D C | Q+L | 3→2 | L2 lab must test dot, norm and projection, not dot only. T: decompose a force along a sloped surface. Mis: dot product as a vector; projection onto zero vector. |
| M03 | Matrices | KEEP | F | S | 10→10 | M02 | V Z D C | Q+L | 3→2 | T: read a matrix from images of basis vectors, then compose in a stated order. Mis: AB=BA; shape agreement implies meaning. |
| M04 | Linear Algebra | RESCOPE | F | S | 20→14 | M03 | V Z D C | Q+L | 2 | Stop at rank, nullspace, solving; spectral content moves to M17. T: which parameters can two dependent sensors recover? Mis: more equations always determine x. |
| M05 | Calculus I | RESCOPE | F | S | 20→12 | M01 | V Z D C | Q | 2 | Differentiation and chain rule first; integration just in time. T: linearize a sensor curve and bound its error. Mis: derivative as slope only, never as sensitivity. |
| M06 | Multivariable Calculus | KEEP | F | S | 20→14 | M03, M05 | V Z D C | Q+L | 3→2 | Remap video: current 3b-gradient does not teach Jacobians. T: verify a hand Jacobian by directional differences. Mis: Jacobian row/column order. |
| M07 | Differential Equations | RESCOPE | F | S | 16→12 | M05~M03 | V Z S C | Q+L | 3→2 | Phase portraits and numerical integration over closed-form tricks. T: pick dt for stiff decay. Mis: Euler stability equals accuracy. |
| M08 | Probability | KEEP | F | S | 20→14 | M01 | Z V W C | Q | 2 | No video today; add MIT 6.041SC or 18.05. T: posterior after two correlated alarms. Mis: confusing P(A given B) with P(B given A); ignoring base rate. |
| M09 | Statistical Foundations | RESCOPE | F | S | 16→12 | M08 | Z W C | Q+L | 2 | Absorbs RS03 basics (CI, effect size). T: seeds needed to detect a stated effect. Mis: CI as probability the parameter is inside. |
| M10 | Optimization | RESCOPE | F | S | 14→10 | M06 | Z V D C | Q+L | 2 | T: diagnose divergence from a loss curve. Mis: lower training loss always better; learning rate as the only knob. |
| M11 | Numerical Computing | RESCOPE | F | S | 14→12 | M03, M05, PY04 | C Z W | Q+L | 2 | Absorbs PY05 (SciPy, plotting). T: rank a solver by residual versus parameter error. Mis: small residual means accurate solution. |
| M12 | Rigid-Body Geometry | MERGE→R03 | F | S | 8→0 | - | — | — | 2 | Lessons M12 and R03 teach the same transforms and share a video; keep M12.v1 evidence as alias. |
| M13 | Advanced Optimization | RESCOPE | A | MAN,MOB | 25→18 | M10, M17 | V D C | Q+L+X | 2 | Convex, QP, Lagrange, KKT; Boyd & Vandenberghe selectively. T: actuator allocation QP. Mis: active constraint means infeasible. |
| M14 | Advanced Probability | DEFER | R | J | 25→0 | - | — | N | 2→1 | Conditional independence to M08; random processes to C07. Pull in for research only. |
| M15 | Lie Theory | RESCOPE | A | PER,MOB | 25→8 | R03, M06 | D C P | Q+L | 2 | Only what estimation needs (micro Lie theory); R03 already covers exp coordinates. T: perturbation Jacobian check. Mis: adding rotation vectors composes rotations. |
| M16 | Advanced Mathematics | REMOVE | R | X | 60→0 | - | — | N | 1→– | Catch-all without assessable objective; registry entry only. |
| M17 | Spectral Methods & Least Squares | NEW | F | S | 0→16 | M04 | V Z D C | Q+L+X | new:2 | Eigen, SVD, pseudoinverse, linear least squares. See blueprint. Mis: eigenvalues and singular values interchangeable. |
| M18 | Information Theory Essentials | NEW | A | RLL | 0→5 | M08 | Z D C | Q | new:2 | Entropy, KL, MLE/cross-entropy link; needed by ML11, RL10. T: why KL is asymmetric in a policy update. Mis: KL as a distance. |
| M19 | Signals & Frequency | NEW | F | S | 0→8 | M03, M05 | Z V C | Q+L | new:2 | Sampling, aliasing, frequency response, first-order filters. T: choose a sensor cutoff and sample rate. Mis: filtering is free of delay. |
| M20 | Nonlinear Least Squares | NEW | A | PER,MOB | 0→8 | M10, M17 | D C Z | Q+L | new:2 | Gauss-Newton, LM, robust loss. T: fit with outliers. Mis: a converged cost implies global optimum. |
| PY01 | Python Fundamentals | RESCOPE | F | S | 15→12 | none | C W | Q+L | 3→2 | Absorbs PY03. Lab must exceed mean(). T: unfamiliar parser from a spec. Mis: aliasing versus copying; print versus return. |
| PY02 | Data Structures | RESCOPE | F | S | 15→10 | PY01 | C Z | Q+L | 2 | Add complexity, graphs, BFS, heaps; feeds E02. T: pick a structure for sensor queues. Mis: list is fine for every queue. |
| PY03 | Python Semantics | MERGE→PY01 | F | S | 6→0 | - | — | — | 2 | PY01 q4 already tests aliasing; keep advanced aspects in debugging exercises. |
| PY04 | NumPy | KEEP | F | S | 10→10 | PY01~M03 | C Z | Q+L | 3→2 | T: vectorize a forward-kinematics batch. Mis: broadcasting silently aligns intended axes. |
| PY05 | Scientific Python | MERGE→M11 | A | S | 10→0 | - | — | — | 2 | SciPy is learned through numerical tasks, not separately. |
| PY06 | PyTorch Basics | KEEP | F | S | 10→10 | PY04~ML04 | C V | Q+L | 2 | Currently has one dependent (S11); must gate ML06, V06. T: match autograd to a hand gradient. Mis: gradients reset automatically. |
| PY07 | Testing & Debugging | RESCOPE | F | S | 10→10 | PY01 | C W | L | 2 | Absorbs T04; mutation-kill score replaces most quiz items. T: tests that reject seeded bugs. Mis: passing tests prove correctness. |
| PY08 | Research Programming | MERGE→RS04 | A | S | 10→0 | - | — | — | 2 | Configuration, logging and seeds fold into RS04. |
| PY09 | Performance | DEFER | A | SYS | 10→6 | PY04, PY07 | C | L | 2 | Absorbs T07. Pull when a pipeline misses a budget. T: profile, then fix the measured bottleneck. Mis: optimizing without measuring. |
| PY10 | Advanced Python | REMOVE | R | X | 15→0 | - | — | N | 1→– | No robotics dependency; learn from documentation when required. |
| CPP01 | C++ Fundamentals | KEEP | A | SYS,MAN | 15→12 | T01 | C W | Q+L | 2 | Track-level, not spine. T: find truncation from compiler warnings. Mis: integer division; uninitialized values. |
| CPP02 | Memory Model | KEEP | A | SYS,MAN | 12→12 | CPP01 | C V Z | Q+L | 3→2 | T: explain and fix a dangling reference after vector growth. Mis: reference keeps object alive. |
| CPP03 | Resource Management | RESCOPE | A | SYS,MAN | 12→16 | CPP02 | C W | L+X | 3→2 | Absorbs CPP04. T: design a bounded joint-state class. Mis: move leaves source unusable; manual new/delete is simpler. |
| CPP04 | Classes & OOP | MERGE→CPP03 | A | SYS,MAN | 10→0 | - | — | — | 2 | Invariants and RAII are one skill in practice. |
| CPP05 | STL & Algorithms | RESCOPE | A | SYS,MAN | 15→12 | CPP01 | C W | L | 2 | Absorbs useful CPP06 idioms. T: select container for timestamp lookup and measure it. Mis: map always beats sorted vector. |
| CPP06 | Modern C++ | MERGE→CPP05 | A | SYS | 20→0 | - | — | — | 2 | Templates and constexpr only when a library reading task requires them. |
| CPP07 | Build Systems | RESCOPE | A | SYS,MAN | 10→14 | CPP02, T01 | C W | L | 2 | Absorbs CPP08: CMake, GoogleTest, ASan/UBSan. T: reduce a failing program and add a regression test. Mis: no crash means no UB. |
| CPP08 | Debugging & Testing | MERGE→CPP07 | A | SYS,MAN | 12→0 | - | — | — | 3→2 | Tooling is verified together with the build. |
| CPP09 | Complexity & Performance | DEFER | A | J | 15→0 | - | — | N | 2 | Pull after a measured real-time miss. |
| CPP10 | Concurrency | KEEP | A | SYS | 20→12 | CPP03, CPP07 | C Z | L+X | 2 | TSan-clean producer/consumer. T: fix a real data race. Mis: volatile synchronizes. |
| CPP11 | Numerical C++ | KEEP | A | SYS,MAN | 12→8 | CPP05, M03 | C | L | 2 | T: Eigen least squares with Python oracle. Mis: aliasing in Eigen expressions; inverse rather than solve. |
| CPP12 | Advanced C++ | REMOVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; ABI work is out of scope for this mission. |
| ML01 | ML Problem Formulation | KEEP | F | S | 8→8 | PY04, M08 | W C | Q+A | 2 | T: find leakage in a supplied pipeline. Mis: random split is always valid for time series. |
| ML02 | Classical ML | KEEP | F | S | 14→12 | ML01, M06 | V Z D C | Q+L | 2 | T: regularization choice on small sensor data. Mis: regularization only reduces test error. |
| ML03 | Generalization | RESCOPE | F | S | 10→12 | ML01, M09 | Z C | Q+L | 2 | Absorbs ML07. T: choose a metric from decision costs. Mis: test set can be reused during tuning; accuracy under imbalance. |
| ML04 | Neural Networks | KEEP | F | S | 8→8 | ML02 | V Z C | Q+L | 2 | T: count parameters and shapes of an unseen net. Mis: depth alone adds nonlinearity. |
| ML05 | Backpropagation | KEEP | F | S | 10→10 | ML04, M06~PY06 | V Z D C | Q+L+X | 2→3 | See blueprint. Mis: backprop is the learning rule. |
| ML06 | Deep Learning Training | KEEP | F | S | 14→14 | ML05, PY06, M10 | V C Z | Q+L | 2 | PY06 edge is missing today. T: diagnose a broken training run from curves. Mis: bigger model first. |
| ML07 | Model Evaluation | MERGE→ML03 | F | S | 10→0 | - | — | — | 2 | Evaluation and generalization share one held-out discipline. |
| ML08 | Representation Learning | RESCOPE | A | RLL,PER | 12→10 | ML06 | V Z C | Q+A | 2 | Absorbs ML10, V14, V18. T: frozen DINOv2 features on a small robot set. Mis: pretraining guarantees transfer under shift. |
| ML09 | Transformers | KEEP | A | RLL,PER | 12→10 | ML06 | V Z C | Q+L | 2 | Absorbs V15. T: compute attention and patch counts by hand. Mis: attention weights explain decisions. |
| ML10 | Self-Supervised Learning | MERGE→ML08 | A | RLL | 12→0 | - | — | — | 2 | Taught as one route to representations. |
| ML11 | Generative Models | RESCOPE | A | RLL | 25→12 | ML06~M18 | V Z D C | Q+L | 2 | VAE sketch, then DDPM/flow focus for action policies. T: multimodal 1-D action fit. Mis: MSE handles multimodal targets. |
| ML12 | Advanced ML | REMOVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; paper-specific reproduction lives in RS06. |
| T01 | Linux | RESCOPE | F | S | 10→10 | none | C | L | 2 | Absorbs T03; Missing Semester. T: repair a broken environment using only the shell. Mis: sudo as a fix. |
| T02 | Git | KEEP | F | S | 6→6 | none | C | L | 2 | Study from week 1 in parallel. T: recover from a bad merge. Mis: commit equals backup of environment. |
| T03 | Development Tools | MERGE→T01 | F | S | 6→0 | - | — | — | 2 | Debugger use is reinforced in PY07 and CPP07. |
| T04 | Software Testing | MERGE→PY07 | F | S | 8→0 | - | — | — | 2 | Same video as PY07; keep T04.v1 evidence as alias. |
| T05 | Reproducible Environments | MERGE→RS04 | F | S | 6→0 | - | — | — | 2 | Environments are the first half of reproducibility. |
| T06 | Docker | DEFER | A | SYS | 8→5 | T01, RS04 | C | L | 2 | Pull when deployment needs it. T: rebuild a ROS image. Mis: container state persists. |
| T07 | Systems Performance | MERGE→PY09 | A | SYS | 10→0 | - | — | — | 2 | Same measurement discipline. |
| T08 | Advanced Infrastructure | REMOVE | R | X | 30→0 | - | — | N | 1→– | Infrastructure catch-all. |
| R01 | Mechanics Foundations | RESCOPE | F | S | 14→10 | M02 | V S D | Q+L | 2 | T: predict cart acceleration in MuJoCo before running. Mis: force causes velocity rather than acceleration. |
| R02 | Robot Mechanisms | KEEP | F | S | 6→6 | R01 | V Z W | Q | 2 | Grübler formula, task vs joint space. T: count DOF of an unseen mechanism. Mis: DOF equals number of motors. |
| R03 | Rigid-Body Transformations | RESCOPE | F | S | 10→14 | M03, R02 | V Z D C | Q+L+X | 2 | Absorbs M12 and adds twists/exponential coordinates (MR Ch. 3). See blueprint. |
| R04 | Forward Kinematics | RESCOPE | F | S | 10→10 | R03 | V Z D C | Q+L+X | 3→2 | Spatial PoE and URDF chain, not 2R only. See blueprint. |
| R05 | Inverse Kinematics | RESCOPE | F | S | 10→10 | R06~M17 | V Z D C | Q+L+X | 2 | Follows the Jacobian. T: damped LS at a singular target with joint limits. Mis: IK has one answer; solver error means unreachable. |
| R06 | Robot Jacobian | RESCOPE | F | S | 12→12 | R04, M06~M17 | V Z D C | Q+L+X | 3 | Teach geometric Jacobian and statics. See blueprint. |
| R07 | Rigid-Body Dynamics | KEEP | F | S | 24→20 | R06, M07, R01 | V S D C | Q+L+X | 3→2 | Absorbs RNEA overview from R12. See blueprint. |
| R08 | Contact Mechanics | KEEP | A | MAN,MOB | 14→10 | R07 | V Z S | Q+L | 2 | T: friction-cone limit tested in MuJoCo. Mis: friction force always equals μN. |
| R09 | Actuators & Transmission | RESCOPE | F | S | 8→6 | R01 | V W | Q | 2 | T: choose a gear ratio under speed and torque limits. Mis: higher ratio dominates. |
| R10 | Mechanical Design Verification | DEFER | A | J | 15→0 | - | — | N | 2→1 | Hardware-builder path only. |
| R11 | Floating-Base Dynamics | KEEP | A | MOB | 18→14 | R07, R08 | V D S | Q+L | 2 | T: why joint torques cannot command base acceleration directly. Mis: base treated as actuated. |
| R12 | Advanced Dynamics | MERGE→R07 | A | J | 20→0 | - | — | — | 2 | RNEA concept in R07; Featherstone depth pulled on demand. |
| R13 | Advanced Locomotion | KEEP | A | MOB | 30→20 | R11, C05 | V S P | A+X | 2 | T: tune then explain a gait failure in simulation. Mis: stability equals zero tipping in steady state only. |
| R14 | Dexterous Manipulation | RESCOPE | A | MAN | 25→16 | R06, R08 | V S D C | Q+L+X | 2 | MR Ch. 12 and Manipulation. T: force-closure of unseen grasp. Mis: more contacts is always stronger. |
| R15 | Advanced Mechanics | REMOVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| R16 | Sensors & Measurement | NEW | F | S | 0→8 | M09~M19 | V C W | Q+L | new:2 | Encoders, IMU, F/T, depth, LiDAR; noise, bias, timestamps. T: Allan-style bias estimate on a log. Mis: datasheet noise equals in-system noise. |
| R17 | Trajectory Generation | NEW | F | S | 0→6 | R04~M05 | V Z D C | Q+L | new:2 | MR Ch. 9 time scaling. T: fastest profile under limits. Mis: path and trajectory are the same. |
| R18 | Motion Planning | NEW | A | MAN,MOB | 0→14 | R04, PY02 | V Z C | Q+L+X | new:2 | C-space, collision, PRM/RRT (MR Ch. 10, LaValle). T: narrow passage failure and fix. Mis: RRT paths are near-optimal. |
| R19 | Manipulator Control | NEW | A | MAN | 0→14 | R07, R06, C03 | V S D C | Q+L+X | new:2 | Computed torque, task-space, impedance (MR Ch. 11). T: contact-stable impedance tuning. Mis: stiffer is always more accurate and safe. |
| R20 | Mobile Robots & Localization | NEW | A | MOB | 0→16 | C07, R16, R02 | V Z C | Q+L+X | new:2 | MR Ch. 13 plus particle filter localization. T: kidnapped robot recovery. Mis: odometry drift is zero-mean. |
| C01 | Control Fundamentals | KEEP | F | S | 8→6 | M05~R01 | Z V D | Q | 2 | T: disturbance offset under P control. Mis: higher gain always better. |
| C02 | Dynamic Systems | RESCOPE | F | S | 16→16 | C01, M07, M04 | V Z D C | Q+L | 3→2 | Absorbs C04. Brunton Control Bootcamp. T: linearize unseen pendulum and classify stability. Mis: local stability is global. |
| C03 | PID Control | RESCOPE | F | S | 10→10 | C01~M19 | Z S C | Q+L | 3→2 | Absorbs C09. T: anti-windup under saturation and delay. Mis: derivative term has no noise cost. |
| C04 | Linear Systems | MERGE→C02 | F | S | 14→0 | - | — | — | 2 | Controllability and poles sit naturally beside state space. |
| C05 | LQR | KEEP | F | S | 12→10 | C02, M10 | V Z D S | Q+L+X | 3 | See blueprint. Mis: LQR is robust to any model error. |
| C06 | State Estimation | MERGE→C07 | F | S | 8→0 | - | — | — | 2 | Prediction and correction taught once, through the Bayes filter. |
| C07 | Kalman Filtering | RESCOPE | F | S | 16→16 | C02, M09 | V Z D C | Q+L+X | 3 | See blueprint. Mis: covariance reflects actual error regardless of model. |
| C08 | Sensor Fusion | RESCOPE | A | MOB,PER | 10→8 | C07, R16 | C Z | Q+L | 2 | Fix wrong edge to R09 (actuators). T: time-aligned IMU+vision fusion. Mis: correlated sensors treated as independent. |
| C09 | Digital Control | MERGE→C03 | F | S | 10→0 | - | — | — | 2 | Sampling and delay arrive with M19 and digital PID. |
| C10 | Nonlinear Control | DEFER | A | J | 25→0 | - | — | N | 2 | Lyapunov intro through Underactuated Ch. 9 when pursuing certificates. |
| C11 | Model Predictive Control | RESCOPE | A | MAN,MOB | 20→14 | C13, M13 | V Z C | Q+L+X | 2 | Reorder after C13. T: add a constraint and explain infeasibility recovery. Mis: MPC handles any model mismatch. |
| C12 | Nonlinear State Estimation | KEEP | A | MOB,PER | 12→10 | C07, M06 | V Z C | Q+L | 2 | T: EKF divergence on a bearing-only case. Mis: EKF covariance is trustworthy under strong nonlinearity. |
| C13 | Optimal Control | RESCOPE | A | MAN,MOB | 25→16 | C05 | V D C | Q+L+X | 2 | Trajectory optimization before MPC; CMU 16-745. T: direct collocation of a swing-up. Mis: locally optimal trajectory is globally optimal. |
| C14 | Whole-Body Control | KEEP | A | MOB | 25→16 | R11, C11 | V D S | A+X | 2 | T: reprioritize tasks under limited torque. Mis: tasks combine without conflict. |
| C15 | Advanced Control | REMOVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; adaptive and robust material on demand. |
| S01 | Simulation Fundamentals | KEEP | F | S | 8→8 | M07, PY04 | S V C | Q+L | 2 | T: expose integrator energy drift. Mis: simulator output is ground truth. |
| S02 | MuJoCo | KEEP | F | S | 12→12 | S01, R02 | S C | L+X | 3→2 | T: build an unseen mechanism in MJCF; match analytic energy. Mis: contact parameters are physical constants. |
| S03 | ROS 2 Fundamentals | KEEP | A | MAN,MOB,SYS | 10→10 | T01, PY01 | C V | L | 2 | Move docs to Jazzy (Humble EOL May 2027). T: debug a topic mismatch via CLI. Mis: topics are reliable by default. |
| S04 | Robot Description | KEEP | F | S | 6→6 | R03~S03 | C Z | L | 2 | URDF validated against R04 FK. T: find a seeded frame error. Mis: visual frame equals joint frame. |
| S05 | ROS 2 Runtime | KEEP | A | SYS | 10→8 | S03 | C | L+X | 2 | T: measure delay under QoS and executors. Mis: callbacks run in parallel by default. |
| S06 | Hardware Integration | RESCOPE | A | SYS | 15→10 | S05, S07, R09 | C S | L+X | 2 | Absorbs S10; mock hardware first. T: mock driver timeout handling. Mis: hardware commands are always applied at send. |
| S07 | Robot Safety | RESCOPE | F | S | 6→6 | R09 | W S | Q+A | 2 | Move earlier; currently not a prerequisite of S06. T: hazard table and watchdog test. Mis: simulation success implies safety. |
| S08 | System Identification | KEEP | A | MOB,RLL | 12→10 | S02, M10~C07 | S C | L+X | 2 | T: fit damping, verify on unseen trajectory. Mis: low training residual identifies parameters. |
| S09 | Sim2Real | RESCOPE | A | MOB,RLL | 20→14 | S08~RL13 | V S P | A+X | 2 | Absorbs RL16; staged validation. Reviewed. T: sim-to-sim transfer before any hardware. Mis: wider randomization is always better. |
| S10 | ROS 2 Control | MERGE→S06 | A | SYS | 16→0 | - | — | — | 2 | ros2_control with mock hardware is the integration lab. |
| S11 | Advanced Simulation | DEFER | A | J | 15→0 | - | — | N | 2 | Batched and differentiable simulation on demand (MJX, Isaac Lab). |
| S12 | Advanced Robotics Software | REMOVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; real-time specifics via CPP10 and S06. |
| V01 | Digital Images | KEEP | F | S | 4→4 | PY04 | C Z | Q+L | 2 | T: detect channel and axis swap. Mis: image axes are x,y. |
| V02 | Image Processing | RESCOPE | F | S | 8→6 | V01, M03 | Z V C | Q+L | 2 | T: aliasing when downsampling. Mis: convolution order never matters with nonlinear steps. |
| V03 | Camera Models | KEEP | F | S | 8→8 | V01, R03 | V Z D C | Q+L | 3→2 | T: reproject unseen 3D points in a robot frame. Mis: focal length scales depth. |
| V04 | Camera Calibration | KEEP | A | MAN,PER | 6→6 | V03, M10~M20 | C V | L+X | 2 | T: separate fit from held-out reprojection error. Mis: low RMS means calibrated everywhere. |
| V05 | Feature Extraction | RESCOPE | A | PER | 8→6 | V02, V03 | Z C | Q+L | 2 | T: match under rotation and report recall. Mis: more features means better pose. |
| V06 | CNN | RESCOPE | F | PER,RLL | 12→12 | ML05, V02, PY06 | V Z C | Q+L | 3→2 | Absorbs V07. T: receptive field of unseen stack; small-data baseline. Mis: pooling gives invariance to all transforms. |
| V07 | Image Classification | MERGE→V06 | F | PER,RLL | 8→0 | - | — | — | 2 | Classification is the first CNN application. |
| V08 | Object Detection | RESCOPE | A | PER | 14→10 | V06, ML03 | V C | Q+L | 3→2 | Absorbs V10; use and evaluate over reimplementing. T: mAP on robot images. Mis: high mAP implies grasp usability. |
| V09 | Object Tracking | DEFER | A | J | 10→0 | - | — | N | 2 | Pull when a task needs identity over time. |
| V10 | Segmentation | MERGE→V08 | A | PER | 10→0 | - | — | — | 2 | Masks and boxes share evaluation logic. |
| V11 | Multi-View Geometry | KEEP | A | PER | 18→14 | V04, M17 | V Z D C | Q+L+X | 2 | T: triangulate with baseline sensitivity. Mis: more baseline is free of matching cost. |
| V12 | Depth Estimation | MERGE→V13 | A | PER | 10→0 | - | — | — | 2 | Stereo is the entry to 3D perception. |
| V13 | 3D Perception | RESCOPE | A | PER,MAN | 18→16 | V11, M11 | Z C | Q+L+X | 2 | ICP with outliers plus stereo depth. T: failed registration diagnosis. Mis: ICP is globally convergent. |
| V14 | Visual Representation Learning | MERGE→ML08 | A | PER,RLL | 12→0 | - | — | — | 2 | Same evaluation discipline. |
| V15 | Vision Transformers | MERGE→ML09 | A | PER,RLL | 6→0 | - | — | — | 2 | ViT is an ML09 worked case. |
| V16 | Video Understanding | DEFER | R | J | 15→0 | - | — | N | 2 | Pull for temporal perception tasks. |
| V17 | Visual Odometry & SLAM | KEEP | A | PER | 30→24 | V11, C12, M20, M15 | V C P | A+X | 2 | Stachniss, Barfoot. Reviewed. T: drift analysis on a public sequence. Mis: ATE alone evaluates odometry. |
| V18 | Vision Foundation Models | MERGE→ML08 | R | RLL | 10→0 | - | — | — | 1 | Taught as tool use with held-out evaluation; DINOv2, CLIP. |
| V19 | 3D Neural Representations | DEFER | R | J | 25→0 | - | — | N | 1 | Neural fields tracked in registry. |
| V20 | Advanced Perception | REMOVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| RL01 | RL Fundamentals | KEEP | F | S | 4→4 | PY01, M08 | V Z C | Q | 2 | T: compute return in an unseen task. Mis: reward equals goal. |
| RL02 | Markov Decision Processes | RESCOPE | F | S | 10→14 | RL01 | V Z D C | Q+L | 3→2 | Absorbs RL03. T: solve a two-state system exactly, then in code. Mis: V is the immediate reward. |
| RL03 | Value Functions | MERGE→RL02 | F | S | 8→0 | - | — | — | 3 | V, Q and Bellman are not separable in practice. |
| RL04 | Dynamic Programming | KEEP | F | RLL,MOB | 6→6 | RL02, PY02 | Z C | L | 2 | T: value iteration with residual stop. Mis: DP needs no model. |
| RL05 | Model-Free Prediction | RESCOPE | F | RLL,MOB | 8→12 | RL02, M09 | Z V C | L+X | 2 | Absorbs RL06. T: cliff walking, SARSA vs Q-learning. Mis: TD has no bias. |
| RL06 | Model-Free Control | MERGE→RL05 | F | RLL,MOB | 10→0 | - | — | — | 2 | Prediction and control taught as paired experiments. |
| RL07 | Function Approximation | RESCOPE | F | RLL,MOB | 8→6 | RL05, ML04 | Z C | Q+L | 2 | T: observe the deadly triad numerically. Mis: more function power stabilizes. |
| RL08 | Policy Gradient | KEEP | F | RLL,MOB | 12→12 | RL02, ML05 | V D C | Q+L+X | 3→2 | T: two-action gradient vs finite-difference check. Mis: log-derivative needs differentiable dynamics. |
| RL09 | Actor-Critic | MERGE→RL10 | F | RLL,MOB | 10→0 | - | — | — | 3 | Actor-critic is the derivation step to PPO. |
| RL10 | PPO | RESCOPE | F | RLL,MOB | 16→18 | RL08, RL05, ML06 | V Z D C | Q+L+X | 3 | See blueprint. Mis: clipping guarantees monotonic improvement. |
| RL11 | Off-Policy RL | KEEP | A | RLL | 18→12 | RL07, RL10 | V C | Q+L | 2 | SAC via CleanRL. T: replay-bias diagnosis. Mis: off-policy always more sample-efficient in wall-clock. |
| RL12 | RL Experimental Design | RESCOPE | A | RLL,MOB | 8→8 | RL05, RS02, ML03 | C P | A+X | 2 | Henderson 2018; Agarwal 2021. T: IQM with CIs over seeds. Mis: best-seed reporting; 3 seeds suffice. |
| RL13 | Continuous Control | RESCOPE | A | MOB,RLL | 10→8 | RL10, C02 | S C | L+X | 2 | Absorbs RL15. T: action scaling and saturation. Mis: reward scale is cosmetic. |
| RL14 | Reward Engineering | KEEP | A | MOB,RLL | 6→6 | RL02 | S W | A+X | 2 | Remove RS02 gate. T: construct and detect a reward loophole. Mis: shaping never alters the optimum. |
| RL15 | Curriculum Learning | MERGE→RL13 | A | MOB | 8→0 | - | — | — | 2 | A training technique within continuous control. |
| RL16 | Domain Randomization | MERGE→S09 | A | MOB,RLL | 8→0 | - | — | — | 2 | Domain randomization belongs to the sim2real validation loop. |
| RL17 | Imitation Learning | RESCOPE | A | RLL | 10→10 | ML06, RL01~RL02 | V Z C | Q+L | 2 | BC first, then DAgger; MDP need is soft. T: rollout failure despite low BC loss. Mis: low validation loss implies good rollouts. |
| RL18 | Offline RL | DEFER | R | J | 15→0 | - | — | N | 2 | Levine 2020 tutorial on demand. |
| RL19 | Model-Based RL | MERGE→E08 | A | RLL | 18→0 | - | — | — | 2 | Taught with world models. |
| RL20 | Hierarchical RL | MERGE→E04 | A | MAN,RLL | 15→0 | - | — | — | 2 | Options only as one implementation of skills. |
| RL21 | Safe RL | DEFER | R | J | 12→0 | - | — | N | 2 | Constraint mindset stays in S07; methods on demand. |
| RL22 | Multi-Agent RL | DEFER | R | J | 25→0 | - | — | N | 1 | Registry only; outside core embodied track. |
| RL23 | Advanced Exploration | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| RL24 | Meta-RL | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| E01 | Sequential Decision Making | MERGE→RL02 | A | S | 8→0 | - | — | — | 2 | No unique skill; removes the false gate on E02. |
| E02 | Planning Fundamentals | RESCOPE | F | MAN,MOB | 8→8 | PY02 | Z C | Q+L | 2 | Today needs 14 ancestors incl. RL and control; only PY02 is required. T: inadmissible heuristic detection. Mis: A* is optimal with any heuristic. |
| E03 | Planning Under Uncertainty | DEFER | R | J | 20→0 | - | — | N | 2→1 | POMDP on demand; Underactuated, Thrun. |
| E04 | Robot Skills | RESCOPE | A | MAN,RLL | 10→10 | S02~RL13 | S C | L+X | 2 | Contracts, behavior trees; absorbs RL20. Remove RL20 gate. T: recover from a failed precondition. Mis: skills compose without state checks. |
| E05 | Task Planning | KEEP | A | MAN | 10→6 | E02 | Z C | Q+L | 2 | T: find impossible precondition. Mis: symbolic plan implies geometric feasibility. |
| E06 | Task & Motion Planning | KEEP | A | MAN | 20→14 | E05, R18, R05 | V C P | A+X | 2 | Garrett 2021. Reviewed. T: reject and replan an unreachable grasp. Mis: plan-then-check is complete. |
| E07 | Imitation-Based Robot Policies | RESCOPE | A | RLL | 15→20 | RL17, E16~ML09, ML11 | V C P | L+A+X | 2→3 | Absorbs E11; promoted. See blueprint. Mis: BC with MSE on multimodal demos is fine. |
| E08 | World Models | RESCOPE | R | RLL | 20→12 | RL10, ML08 | V C P | A+X | 2 | Absorbs RL19. T: one-step vs multi-step error and control usefulness. Mis: lower pixel error gives better control. |
| E09 | Object-Centric Representations | DEFER | R | J | 18→0 | - | — | N | 2→1 | Research-stage. |
| E10 | Vision-Language Models | RESCOPE | A | RLL | 14→8 | ML09, ML08 | V C | A+X | 2 | Use and evaluate. T: spatial-relation failure test. Mis: grounding follows from caption ability. |
| E11 | Diffusion/Flow Action Policies | MERGE→E07 | A | RLL | 18→0 | - | — | — | 1→2 | P2 today despite being mainstream in imitation; promote through E07. |
| E12 | Vision-Language-Action Models | RESCOPE | R | RLL | 20→10 | E07, E10 | P C | A | 1→2 | Run open models (Octo, pi0) on held-out tasks. Reviewed only. Mis: demo video proves generalization. |
| E13 | Long-Horizon Robot Learning | REMAP→CAP | R | J | 25→0 | - | — | N | 1 | Assessed through capstones with stage-wise success metrics. |
| E14 | Embodied Reasoning | DEFER | R | J | 25→0 | - | — | N | 1 | Open research; L4 only by human review. |
| E15 | Advanced Embodied Intelligence | REMOVE | R | X | 40→0 | - | — | N | 1→– | Catch-all. |
| E16 | Robot Data Collection | NEW | A | RLL | 0→10 | S02, RL17 | C S | L+A | new:2 | Teleop, demonstrations, dataset QA; LeRobot, UMI, ALOHA. T: find a bad-demo cluster. Mis: more demos always help. |
| E17 | HRI & Shared Autonomy | NEW | R | J | 0→0 | - | — | N | new:1 | HRI and shared autonomy; registry until a learner selects a cognitive path. |
| RS01 | Scientific Reasoning | KEEP | F | S | 4→4 | none | W | Q+A | 2 | T: write a falsifier for a claim. Mis: confirmation as proof. |
| RS02 | Experimental Design | KEEP | F | S | 8→8 | RS01, M09 | W C | Q+A+X | 3→2 | Absorbs RS05. T: factorial ablation design. Mis: changing two factors at once is efficient. |
| RS03 | Statistical Inference | MERGE→M09 | F | S | 10→0 | - | — | — | 2 | Inference is taught once in M09 and applied in RS02, RL12. |
| RS04 | Experimental Reproducibility | RESCOPE | F | S | 10→14 | RS02, T02, PY07 | C | L+X | 3→2 | Absorbs PY08, T05, RS09. Fresh-clone rerun is machine-checkable. Mis: seed fixes all nondeterminism. |
| RS05 | Error Analysis | MERGE→RS02 | F | S | 6→0 | - | — | — | 2 | Taught in every evaluation task. |
| RS06 | Paper Reading | KEEP | F | S | 8→8 | RS01 | P W | A | 2 | Claim-evidence-assumption table, reviewed. Mis: venue equals validity. |
| RS07 | Scientific Writing | KEEP | R | RES | 15→10 | RS06, RS02 | W | A | 2 | Human review needed for verified status. |
| RS08 | Literature Review | DEFER | R | RES | 10→6 | RS06 | P | A | 2 | Pull at the start of a research project. |
| RS09 | Research Software | MERGE→RS04 | F | S | 10→0 | - | — | — | 2 | Traceability is part of reproducibility. |
| RS10 | Advanced Research | REMOVE | R | X | 60→0 | - | — | N | 1→– | Research output cannot be a curriculum node; L4 is evaluated per project. |


### 1.9 Blueprints for high-priority topics

Selection: these have the most dependents or carry the largest gap between target and current evidence. References are in section 1.10. Numbers in PASS are proposals.

#### M17 Spectral Methods & Least Squares (new, about 16 h)
- **Objectives:** compute and interpret eigen-decomposition and SVD; solve least squares with a pseudoinverse; explain conditioning through singular values.
- **Mix:** 3Blue1Brown eigenvectors chapter [link: topic page]; MIT 18.06 [link] and 18.065 [link]; SVD ellipse model; NumPy tasks.
- **Diagnostic:** "Which vectors does this shear keep on their own line?"; predict the rank from a picture.
- **Concept:** eigenvalues vs singular values on a non-symmetric matrix.
- **Derivation:** normal equations; minimum-norm pseudoinverse solution through SVD (ordered derivation plus expression).
- **Implementation:** `lstsq_svd(A,b,tol)` with hidden tests on rank-deficient and ill-conditioned inputs; no `np.linalg.lstsq`.
- **Debug:** a solver that truncates by absolute rather than relative tolerance.
- **Transfer:** given a Jacobian near singularity, choose damping and justify it from singular values.
- **Retention:** at 21 days, a new matrix and an explanation of its rank loss.
- **Misconceptions:** eigenvalues measure stretch for all matrices; the inverse is the way to solve.
- **PASS:** Q ≥80% with critical items; L all hidden tests; X requires review. L2 target.

#### R03 Rigid-Body Motions (absorbs M12, about 14 h)
- **Objectives:** compose and invert transforms with frame labels; convert among R, quaternion and exponential coordinates; express a twist in another frame.
- **Mix:** MR Ch. 3 videos [link, toc]; 3D frame-order model; planar first, spatial next; MR code library [link] for checking only.
- **Diagnostic:** predict the result of two rotations in each order.
- **Concept:** body vs space frame multiplication; point vs direction.
- **Derivation:** inverse transform; Rodrigues' formula (ordered).
- **Implementation:** `compose`, `inverse`, `exp3`, `log3`, `exp6`, `adjoint`; hidden tests include π rotations and identity edge cases.
- **Debug:** a seeded camera-to-base pipeline with one frame error.
- **Transfer:** hand-eye style chain with an unfamiliar sensor mount.
- **Retention:** 21 days, new chain from blank.
- **Misconceptions:** any orthogonal matrix is a rotation; rotation vectors add.
- **PASS:** Q + L; `log3` must handle near-π cases.

#### R04 Forward Kinematics (about 10 h)
- **Objectives:** derive FK using PoE for an unseen spatial arm; relate it to URDF; validate against a simulator.
- **Mix:** MR Ch. 4 [toc]; existing `forward-kinematics` model plus a 3-DOF extension; MuJoCo check.
- **Diagnostic:** identify screw axes in a picture; predict home pose.
- **Concept:** tool offset and base offset; relative angles.
- **Derivation:** PoE for a 3-DOF arm, with a planar reduction to the current 2R result.
- **Implementation:** `fk_poe(M, Slist, q)`, hidden tests on random arms including prismatic joints.
- **Debug:** a seeded screw-axis sign error and wrong multiplication order.
- **Transfer:** an arm with no prior worked example, verified through MuJoCo or URDF.
- **Retention:** new arm at 21 days.
- **Misconceptions:** FK ambiguity; degree and radian slip.
- **PASS:** Q + L + reach invariant. Target changes 3→2; L3 only through the R06 or capstone chain.

#### R06 Robot Jacobian (about 12 h, L3 target)
- **Objectives:** derive space and body Jacobians; use the J-transpose force relation; analyze singularities through SVD.
- **Mix:** MR Ch. 5 [toc]; `jacobian` model plus manipulability ellipsoid; CS223A lectures [link].
- **Diagnostic:** predict which joint moves the tip in which direction.
- **Concept:** singularity means lost task direction, not an FK failure.
- **Derivation:** columns as twists; `τ = JᵀF` from power balance.
- **Implementation:** `jacobian_space`, plus a numeric check by central differences; hidden tests on random arms.
- **Debug:** frame mismatch of Jacobian and twist; a seeded column-order error.
- **Transfer:** given a task direction, pick a configuration to maximize force or speed; explain the trade-off.
- **Retention:** 21 and 60 days with new arms.
- **Misconceptions:** invert J always; small determinant is a scale-independent measure.
- **PASS:** Q + L; L3 needs delayed novel transfer with human review.

#### R07 Rigid-Body Dynamics (about 20 h)
- **Objectives:** derive Lagrangian dynamics for a 2-DOF arm; explain mass matrix, Coriolis and gravity; run inverse and forward dynamics.
- **Mix:** MR Ch. 8 [toc]; Underactuated Ch. 2 pendulum [toc]; MuJoCo; existing `mr-dynamics` video.
- **Diagnostic:** predict how a pendulum's period changes with mass and length.
- **Concept:** why M(q) is symmetric positive definite; effective inertia.
- **Derivation:** full 2-link Lagrangian with `expression` checks per term.
- **Implementation:** `M`, `C`, `g`; energy-conservation and `MuJoCo qfrc_inverse` comparison hidden tests.
- **Debug:** seeded inertia frame error causes energy growth; the learner finds it.
- **Transfer:** add a payload; predict and test the change.
- **Retention:** re-derive at 21 days on a variant.
- **Misconceptions:** energy drift always means bad physics rather than an integrator effect.
- **PASS:** Q + L. L3 is not targeted here, only available by review.

#### C05 LQR (about 10 h, L3 target)
- **Objectives:** derive finite-horizon LQR by dynamic programming; solve infinite-horizon gains; choose Q and R from specifications.
- **Mix:** Control Bootcamp [link]; Underactuated Ch. 8 [toc]; Q/R model; cart-pole simulator.
- **Diagnostic:** predict the effect of 10× R on gain and effort.
- **Concept:** what the Riccati solution means; requirement for controllability.
- **Derivation:** backward recursion with an `ordered-derivation` item.
- **Implementation:** `dlqr` from scratch, compared against SciPy; stabilizes cart-pole across hidden initial states.
- **Debug:** a wrong discretization that makes a stable design unstable.
- **Transfer:** stabilize an unfamiliar system, then report robustness to 20% mass error.
- **Retention:** new system at 21 days.
- **Misconceptions:** LQR guarantees global stability; Q entries are unitless.
- **PASS:** Q + L; closed-loop eigenvalues checked; L3 requires reviewed transfer.

#### C07 Kalman Filtering (absorbs C06, about 16 h, L3 target)
- **Objectives:** derive the predict-update cycle; implement a KF; test consistency with NEES and NIS.
- **Mix:** Labbe's book and notebooks [link]; Underactuated Ch. 19 [toc]; Kalman ellipse model; Barfoot's book [link].
- **Diagnostic:** combine two noisy measurements by hand.
- **Concept:** gain as relative trust; what a covariance claims.
- **Derivation:** scalar gain first, then matrix form.
- **Implementation:** constant-velocity KF; hidden test checks estimate and NEES coverage across random seeds.
- **Debug:** wrong Q tuned to hide a model mismatch; timestamp misalignment.
- **Transfer:** track with a missing-measurement sequence and an unmodelled bias.
- **Retention:** new model at 21 and 60 days.
- **Misconceptions:** smaller covariance means more accuracy; Gaussianity not needed for BLUE vs. full posterior.
- **PASS:** Q + L with NEES inside a stated interval.

#### ML05 Backpropagation (about 10 h, L3 target)
- **Objectives:** derive reverse-mode for a small graph; build a scalar autograd engine; validate with gradient checks.
- **Mix:** 3B1B chapters already mapped; Karpathy micrograd [link: Zero to Hero]; computation graph model.
- **Diagnostic:** compute a two-step chain rule by hand.
- **Concept:** why reverse beats forward for many inputs; backprop vs optimizer.
- **Derivation:** adjoint recursion.
- **Implementation:** `Value` class with `backward()`; hidden random graphs compared against PyTorch and finite differences.
- **Debug:** seeded duplicate-node bug (wrong topological order) and zero-grad bug.
- **Transfer:** derive gradients for an unseen custom loss with a stop-gradient.
- **Retention:** rebuild from blank at 21 days.
- **Misconceptions:** backprop is the learning rule; gradients flow through non-differentiable operations automatically.
- **PASS:** Q + L; L3 requires reviewed transfer.

#### RL10 PPO (absorbs RL09, about 18 h, L3 target)
- **Objectives:** derive the policy gradient with advantage; implement PPO; justify its choices with evidence over seeds.
- **Mix:** Schulman et al. [meta]; Spinning Up [link]; CleanRL [link]; "37 implementation details" [link]; S&B Ch. 13 [mem]; clip-curve model.
- **Diagnostic:** predict the clipped objective for positive and negative advantages.
- **Concept:** on-policy data and why it is reused only briefly; GAE's bias-variance trade-off.
- **Derivation:** log-derivative trick; advantage as a baseline.
- **Implementation:** PPO from scratch for a continuous task; hidden check on a fixed task and budget over several seeds. Reaching a threshold depends on tuning, so the pass bar must be calibrated with reference runs first.
- **Debug:** seeded bugs (no advantage normalization, wrong GAE done-mask, stale log-probs), identified from curves.
- **Transfer:** apply to an unfamiliar MuJoCo task; explain failure and fix with a pre-registered ablation.
- **Retention:** explain and fix a new seeded bug at 21 days.
- **Misconceptions:** clipping guarantees monotonic improvement; reward curves from a single seed are informative.
- **PASS:** Q + L + analysis using IQM with CIs (Agarwal 2021); L3 reviewed. Runtime and hardware are a real cost, so the lab must run on a CPU within a stated budget.

#### E07 Visuomotor Imitation Policies (absorbs E11, about 20 h, L3 target)
- **Objectives:** train and evaluate ACT or Diffusion Policy; explain action chunking and multimodality; report honestly against a baseline.
- **Mix:** Zhao 2023 and Chi 2023 [meta]; LeRobot docs [link]; multimodal target model; simulated tasks.
- **Diagnostic:** predict an MSE policy's output with two equally common demonstrated paths.
- **Concept:** covariate shift, chunking, why validation loss misleads.
- **Derivation:** denoising objective at a working level. Full score-matching theory is not required.
- **Implementation:** 1-D multimodal diffusion from scratch; then a LeRobot pipeline on E16's dataset.
- **Debug:** normalization mismatch at inference; off-by-one action alignment; leaked evaluation states.
- **Transfer:** a changed object or camera; predict, test and report the drop.
- **Retention:** at 21 and 60 days, diagnose a new failed rollout.
- **Misconceptions:** low training loss implies success; a demo video is evidence of generality.
- **PASS:** fixed protocol over held-out initial states with CI vs a BC baseline. Machine metrics reach L2; L3 requires human review of the analysis. GPU access is a real barrier, so a small low-dimensional state variant must remain possible.

### 1.10 Resources

Mapped to topics. Status labels are from section 1.0.

| Topics | Resource | Why this one | Status |
|---|---|---|---|
| M02–M04, M17 | [3Blue1Brown, Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab) | Best geometric intuition; short | [link, playlist title checked] |
| M04, M17 | [MIT 18.06 Strang](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/); [18.065](https://ocw.mit.edu/courses/18-065-matrix-methods-in-data-analysis-signal-processing-and-machine-learning-spring-2018/) | Depth and problem sets | [link] |
| M05 | [3Blue1Brown, Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr); [MIT 18.01SC](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/) | Intuition then practice | [link] (18.01SC from the repo) |
| M06 | [MIT 18.02SC](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/) | Replaces a mismatched video | [link] |
| M07 | [MIT 18.03SC](https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/); [Learn DE, Strang & Moler](https://ocw.mit.edu/courses/res-18-009-learn-differential-equations-up-close-with-gilbert-strang-and-cleve-moler-fall-2015/) | Short videos with numerical emphasis | [link] |
| M08, M09 | [MIT 6.041SC](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/); [MIT 18.05](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/); [Seeing Theory](https://seeing-theory.brown.edu/) | Fills M08's video gap | [link] |
| M10, M13 | [Boyd & Vandenberghe](https://web.stanford.edu/~boyd/cvxbook/) | Standard reference, free | [link] |
| M11 | [MIT 18.330](https://ocw.mit.edu/courses/18-330-introduction-to-numerical-analysis-spring-2012/) | Numerical analysis | [link] |
| M15 | Solà et al., [micro Lie theory, arXiv:1812.01537](https://arxiv.org/abs/1812.01537) | Written for robotics estimation | [meta] |
| ML math | [Mathematics for ML](https://mml-book.github.io/) | Compact free bridge | [link] |
| PY02 | [MIT 6.006](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/) | Standard algorithms | [link] |
| T01–T02 | [Missing Semester](https://missing.csail.mit.edu/); [Pro Git](https://git-scm.com/book/en/v2) | Practical and short | [link] |
| CPP* | [LearnCpp](https://www.learncpp.com/); [Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines); [GoogleTest](https://google.github.io/googletest/); [ASan](https://clang.llvm.org/docs/AddressSanitizer.html); [CMake tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/) | The repo's `Effective C++` predates C++11; *Effective Modern C++* is a better book pointer [mem] | [link] |
| ML* | [D2L](https://d2l.ai/); [Understanding Deep Learning](https://udlbook.github.io/udlbook/); [Karpathy Zero to Hero](https://karpathy.ai/zero-to-hero.html); [3Blue1Brown NN](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi); [PyTorch basics](https://pytorch.org/tutorials/beginner/basics/intro.html) | Build-first, current | [link] |
| R02–R07, R17–R20, R14 | [Modern Robotics wiki](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) with free PDF, videos, [code library](https://github.com/NxRLab/ModernRobotics) | Free and unified: Ch. 3 motions, 4 FK, 5 velocity, 6 IK, 8 dynamics, 9 trajectories, 10 planning, 11 control, 12 grasping, 13 wheeled | [link, toc] |
| R03–R07 | [Stanford CS223A](https://see.stanford.edu/Course/CS223A) | Alternative view, also classic DH notation | [link] |
| C*, R13, R18 | [Underactuated Robotics](https://underactuated.csail.mit.edu/): Ch. 2 pendulum, 8 LQR, 10 trajectory optimization, 12 planning, 19 estimation | Rigorous, with Drake | [link, toc] |
| R14, R19, E06 | [Robotic Manipulation](https://manipulation.csail.mit.edu/): Ch. 3 pick and place, 6 planning, 8 control, 11 RL | Directly fits the MAN track | [link, toc] |
| R18 | [LaValle, Planning Algorithms](https://lavalle.pl/planning/); [OMPL](https://ompl.kavrakilab.org/) | Free reference and library | [link] |
| C02, C03, C05, C07 | [Brunton, Control Bootcamp](https://www.youtube.com/playlist?list=PLMrJAkhIeNNR20Mz-VpzgfQs5zrYi085m) | Short, state-space first | [link, playlist title checked] |
| C13, C11 | [CMU 16-745 Optimal Control](https://optimalcontrol.ri.cmu.edu/) | Robotics-focused | [link] |
| C07, C12 | [Labbe, Kalman and Bayesian Filters in Python](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python); [Barfoot](http://asrl.utias.utoronto.ca/~tdb/bib/barfoot_ser17.pdf) | Interactive notebooks; deeper theory | [link] |
| R20, V17 | Thrun, Burgard & Fox, *Probabilistic Robotics*, MIT Press 2005; [Stachniss courses](https://www.ipb.uni-bonn.de/teaching/) | Standard text. Its old site returned 404, so no link. | [mem] book; [link] courses |
| S02, S08, S11 | [MuJoCo](https://mujoco.readthedocs.io/en/stable/); [Menagerie](https://github.com/google-deepmind/mujoco_menagerie); [Isaac Lab](https://isaac-sim.github.io/IsaacLab/); [Drake](https://drake.mit.edu/) | Official | [link] |
| S03–S06 | [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/); [ros2_control](https://control.ros.org/); [MoveIt](https://moveit.picknik.ai/main/index.html) | Humble reaches EOL in May 2027. I prefer Jazzy for ecosystem maturity, but Lyrical may become better within a year. | [link] |
| V* | [First Principles of CV](https://fpcv.cs.columbia.edu/); [Szeliski](https://szeliski.org/Book/); [CS231n](https://cs231n.stanford.edu/); [CNN Explainer](https://poloclub.github.io/cnn-explainer/) | The repo's CS231n videos are from 2017, before transformers, so pair them with current notes | [link] |
| V17 | [GTSAM](https://gtsam.org/) | Factor graph practice | [link] |
| RL* | [Sutton & Barto](http://incompleteideas.net/book/the-book-2nd.html); [Silver](https://www.davidsilver.uk/teaching/); [Spinning Up](https://spinningup.openai.com/); [CS285](https://rail.eecs.berkeley.edu/deeprlcourse/); [CleanRL](https://docs.cleanrl.dev/); [PPO details](https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/) | Theory to practice | [link] |
| RL12 | Henderson 2018, arXiv:1709.06560; Agarwal 2021, arXiv:2108.13264 | Why seeds and CIs matter | [meta] |
| RL10, RL11 | Schulman 2017, arXiv:1707.06347; Haarnoja 2018, arXiv:1801.01290; Fujimoto 2018, arXiv:1802.09477 | Primary sources | [meta] |
| S09, RL13 | Tobin 2017, arXiv:1703.06907; Rudin 2021, arXiv:2109.11978; Recht 2018, arXiv:1806.09460 | DR, parallel simulation, control view | [meta] |
| RL17, E07, E16 | Zhao 2023, arXiv:2304.13705; Chi 2023, arXiv:2303.04137; Chi 2024 UMI, arXiv:2402.10329; [LeRobot](https://huggingface.co/docs/lerobot/index) | Current mainstream practice | [meta, link] |
| E08 | Hafner 2023, arXiv:2301.04104 | Reference world model | [meta] |
| E06 | Garrett 2020, arXiv:2010.01083 | TAMP survey | [meta] |
| E10, E12 | Radford 2021, arXiv:2103.00020; Oquab 2023, arXiv:2304.07193; Brohan 2023, arXiv:2307.15818; Octo 2024, arXiv:2405.12213; Black 2024 pi0, arXiv:2410.24164 | Open or reference models. This area moves quickly; re-check every 6–12 months. | [meta] |
| RL18 | Levine 2020, arXiv:2005.01643 | Tutorial | [meta] |

**Removed after checks failed:** `probabilistic-robotics.org` (404); three speculative URLs that did not resolve; two arXiv IDs I had misremembered, which resolved to unrelated papers. Author lists for arXiv entries are "first author + year" only; please use the API for full lists.

### 1.11 Effort and savings

All numbers are my estimates (±40%), and the current-state numbers assume topics are studied to real independent competence. They are not based on `estimated_minutes`, which I consider unrealistic.

| Goal | Equivalent under current graph | Proposed, with capstones | Saving |
|---|---|---|---|
| MAN | 92 topics, 1,078 h | 75 nodes, 860 h | 218 h, 20% |
| MOB | 93 topics, 1,078 h | 79 nodes, 890 h | 188 h, 17% |
| RLL | 101 topics, 1,133 h | 77 nodes, 841 h | 292 h, 26% |
| PER | 87 topics, 969 h | 67 nodes, 737 h | 232 h, 24% |
| SYS | 84 topics, 931 h | 66 nodes, 710 h | 221 h, 24% |

Saving range: **17–26%**. Note that:

- Whole-graph hours fall from 2,486 to 1,228, but that **51% is not a learner's saving**. Nobody would study the full set.
- Proposed numbers include newly added material, so they buy more than the current path does.
- Placement probes could save more for people with prior knowledge. I did not estimate this.
- Longer review intervals may free another 30–45 minutes per day at full scale (C8). This is a separate estimate.
- New assessments add learner time, about 10 more minutes per form.
- Real savings need measurement. I recommend logging active minutes per evidence event, and comparing estimated with actual hours after the first 10 topics.

### 1.12 Suggested order, if approved

1. Fix immediate defects: recommendation text, ROS version, lesson-diagnostic leakage in new versions, and the video mismatches.
2. Build assessment v2 additively, with M02, PY01 and R04 as pilots.
3. Publish graph v2 with aliases.
4. Author the spine, with priority on M17, R03, R04, R06, C02, C05, C07, ML05 and RL02.
5. Build one track at a time, starting from the owner's chosen goal.

### 1.13 Weaknesses in my own analysis, and questions for Codex

**Weaknesses**

1. Hour estimates are unmeasured judgment, and the "savings" compare two of my own estimates.
2. My content-gap search is keyword-based. A topic might teach a concept under a different word, though I read several lessons by hand.
3. The leakage count is heuristic; only R04 and M04 were checked by hand.
4. I may be overvaluing machine-checkable evidence because it is easy to build. Hidden tests can measure a narrow skill well and miss judgment.
5. The evidence base is mostly classroom, non-robotics, often short-term.
6. Spine size (540 h) may still be too large. M19, R16 and S07 could arguably be track-level, and ML might not belong in the spine for a classical robotics learner.
7. Mandatory PoE is a teaching opinion. I have no comparative data on PoE vs DH.
8. Simulation-only capstones skip real hardware, where important robotics lessons happen.
9. Authoring load is high for what may be a single-maintainer project.

**Questions for Codex**

- Is a shared 540 h spine right, or should there be goal-specific entry paths from the start?
- Which merges hide a real skill? I am least sure of C02+C04, RL09+RL10 and CPP03+CPP04.
- Can L3 mean anything for a single user with no reviewer?
- Is the 12-item form worth its time, or would sequential testing (stop early when confident) do better?
- Do you find concrete errors in my prerequisite changes?

---

## Round 2: response to Codex Round 1

I read Codex's Round 1 in full and checked its factual claims against the repository before responding.

### 2.0 Summary of what changed in my position

1. **I withdraw the 540 h shared spine (C2).** Computing what all goal paths actually share gives a far smaller core. Codex's P06 was right.
2. **I withdraw deletion of the 11 "Advanced" nodes (C5).** My claim that they have "no assessable objective" was title-based and partly false. They become archived electives with their IDs kept.
3. **I withdraw savings percentages as a headline (section 1.11).** They compare two sets of my own estimates. They are now a planning hypothesis with a validation design.
4. **I stop requiring PoE for everyone (C6).** It moves to the tracks that derive with it.
5. **I hold on three points against Codex:** one new node is not enough, spectral content needs its own evidence identity, and some topic-level decisions must actually be made rather than left as an inventory.

### 2.1 Verification of Codex's claims

| Codex claim | My check | Result |
|---|---|---|
| All 31 critical C items have answer index 0 | Read all contracts: the set of answers is `{'0'}` | **Correct, and I missed it.** A positional strategy passes every C gate, so my "50% guess" understated the problem. |
| M08's and M07's lesson `source_refs` point to MIT 18.01 calculus | Read frontmatter | **Correct, and I missed it** |
| M08's diagnostic does not compute Bayes | q1 asks if P(A given B) equals P(B given A); q2–q4 are expectation, variance, die | Correct. Conceptual item only. |
| M01 lacks the trigonometry R04 assumes | "cos", "trig" and "radian" have no hits in M01 ("sin" hit is a substring) | **Correct, and I missed it.** I had cut M01 from 6 h to 4 h, which was the wrong direction. |
| M07 uses integration; M05 does not teach it | "integr": 0 hits in M05, 9 in M07 | **Correct, and I missed it.** My M05 note said integration could wait, which conflicts with M07 unless it is taught in between. |
| M10's loss and the demo differ | Lesson `(θ−3)²`, demo `0.5x²`; stable step bounds 1 and 2 | Correct |
| Underactuated FAQ URL | HTTP 200 | Reachable; I did not read the content |

### 2.2 Decisions on Codex's proposals

| ID | Decision | Reasoning, cost and confidence |
|---|---|---|
| **P01** Scoped readiness objectives | **ACCEPT** | Same as my C3, but Codex's framing is better: a PASS should state what it licenses. Authoring cost is real; optimal granularity is untested. High confidence. |
| **P02** Precalculus and numerical bridges | **ACCEPT the need; MODIFY the location** | M01 gains an algebra, trig and exp/log bridge selected by placement (+4 h for those who need it). M05 gains elementary integration (+2 h). I reject placing spectral methods inside M04; see 2.5. High confidence on need. |
| **P03** Covariance and Gaussian before Kalman | **ACCEPT** | My M09 row omitted covariance although my C07 blueprint assumes it. M09 goes from 12 h to 14 h. Bayes computing is added to the M08 v2 form. High confidence. |
| **P04** Motion planning unit | **ACCEPT; MODIFY the ID and edges** | Codex's `R16` collides with my `R16` (Sensors). I keep the ID as R18 in my notation; the final ID is a maintainer choice. I accept `R18 ← E02, R03` with R04 soft: rigid-body C-space planning does not need FK. Arm planning uses R04 as soft context. My 14 h includes arm collision checking, vs Codex's 6–12 h. Neither is measured. |
| **P05** Safety at entry; gates physical practice | **ACCEPT** | My `S07 ← R09` was wrong for awareness. S07 now has no hard prerequisite, with quantitative hazard analysis scoped later. A quiz never authorizes hardware use. High confidence. |
| **P06** Separate starter from role-specific | **ACCEPT, and this overturns my C2** | See 2.3. |
| **P07** Merge teaching without merging evidence | **ACCEPT, replacing my alias rule** | My "alias" could read old M12.v1 evidence as covering absorbed R03 scope, which is the retroactive claim Codex warns about. New rule: a merge joins *study units* only. All IDs, objective tags and scores stay separate. v1 evidence applies only to its own contract. This also means my "115 live nodes" counts study units rather than evidence identities. |
| **P08** Experiment discipline before training | **ACCEPT; MODIFY** | Full RL12 has many ancestors, so it cannot come first. A minimal seed and hold-out protocol is an objective in the RL05 lab, and RL10's PASS requires it. RL12 is soft before RL10. |
| **P09** Frontier stays elective | **MODIFY** | Accept that it is elective globally. Accept MLP behaviour cloning as the baseline first. I undo absorbing E11 into E07 and withdraw my L3 target for E07, which overreached. E11 is core only inside the RLL track, because a person aiming at robot learning needs it. Evidence for that is limited: it is my judgment from citations and from LeRobot offering these policies, not measured demand. Medium-low confidence. |
| **P10** Fix assessment validity first | **ACCEPT** | Same as C1. Codex adds an important limit: predictive validity of the replacements needs a pilot. |

**Evidence profiles (MAT, CODE, DYN, DATA, PLAN, RESEARCH).** **ACCEPT, with one merge.** These map closely to my archetypes A–F. Codex's `PLAN` is better than filing search under my algorithm archetype, and its `DATA` is clearer than my "applied ML". I keep Physical Modelling separate from Algorithm, which Codex covers with DYN, and adopt Codex's naming going forward.

**M can be inapplicable.** **ACCEPT, and it exposes a code constraint.** `masteryFor` requires `dims.M >= 1` for L2, so a Git or Linux topic with no real mathematics could never reach L2 without invented arithmetic. A future contract must declare which dimensions apply, and L2 must gate on those. That is an engine change needing approval.

**Availability vs instructional match as separate fields.** **ACCEPT.** My `[link]` label only shows availability. Captions, durations and regional access are unverified on my side too. The current learner works in Vietnamese and English, and I did not check any Vietnamese captions.

**Fixed schedule as a heuristic; start with small mixed reviews.** **ACCEPT, with the load figure retained.** My schedule (up to 365 days) has no stronger basis than the current one. I add a **daily review budget** (for example 10–15 minutes), which limits harm regardless of which schedule is wrong. The 8 reviews per day at 169 topics is arithmetic and stands.

**Do not imply "visual learning styles."** **ACCEPT.** See Pashler et al. 2008, *PSPI* 9:105, doi:10.1111/j.1539-6053.2009.01038.x [meta; finding from memory, mem]. The owner's video-first preference is a legitimate preference and engagement choice, not a claim about outcomes.

**Reuse existing primitives before adding visual engines.** **ACCEPT.** My 16 proposed models become 5 pilots. Extend `jacobian` (ellipsoid), `geometry` (3D frames) and `pid`. Build SVD and Kalman only if the pilots show use. Elsewhere use external models such as Seeing Theory and CNN Explainer, subject to the match check.

**Reconcile demo and lesson models (M10, C01).** **ACCEPT.** Cheap and clearly right.

### 2.3 Replacing the spine with a computed core

**Method.** For each goal I listed leaf topics a capstone needs, took the backward closure on the revised hard edges, and intersected the closures. Script-based, using my own hours.

| Set | Topics | Hours (±40%) |
|---|---|---|
| In all 5 goal closures | M01, M02, M03, PY01, PY04 | 48 |
| In the 4 non-SYS goals, adding | M05, M06, M07, M10, R03 | 110 total |
| My Round 1 spine | 54 units | 546 (revised) |

| Goal | Closure | Hours + capstone |
|---|---|---|
| SYS | 28 units | 300 |
| PER | 37 units | 447 |
| RLL | 43 units | 498 |
| MAN | 44 units | 542 |
| MOB | 48 units | 612 |

**Reading this honestly**

- Dependency closures omit practice skills, which by design have few edges: Git, Linux, testing, scientific reasoning and safety awareness. I add those as a cross-cutting starter of about 31 h (T01, T02, PY07, RS01, S07 awareness). That gives a **common core of about 80 h, or 140 h for non-SYS goals**.
- The result depends on my leaf choices and edges. My script also showed M19, R17, S04 and RS06 in no closure, even though MAN needs R17. So the leaf list is imperfect, and adding R17 costs 6 h.
- A person wanting breadth or wide career options will need more than the minimum closure. A closure is the least needed for one capstone, not a recommendation to stop.
- This *supports* P06, but it does not validate any path.

**New position.** Common core (about 80–140 h), then goal closure, then capstone. The community map stays complete. I no longer claim there is a universal 540 h foundation.

**Remaining objection to Codex's version.** "A menu, not ten compulsory modules" is sound, but a menu alone leaves a beginner to make decisions they cannot yet make. I would keep a *default* goal path for people who do not choose, with explicit opt-out.

### 2.4 Answers to Codex's seven questions

**Q1. Which deletion is tied to an actual objective, rather than a title?**
My Round 1 reasoning was partly title-based. The overview tasks show this:

| Node | Overview task | Revised decision |
|---|---|---|
| PY10 | Lazy data iterator | Real skill, but small. Archive. |
| C15 | State the uncertainty set of a robust controller | Real; robust control matters. Elective, not "removed". |
| S12 | Trace sensor-to-command latency | Concrete and valuable. The task moves into the SYS capstone; ID stays. |
| V20 | Evaluation suite for occlusion and degradation | Real. Elective. |
| R15 | When the rigid approximation fails | Real, but niche. Archive. |
| CPP12, T08 | Library ownership review; job restart contracts | Real, but not needed by any goal path. Archive. |
| M16, ML12, E15, RS10 | Theorem check; paper claim; benchmark design; minimal study | Duplicates RS06 and RS02-style work at topic level. Archive, assessed through projects. |

All 11 keep their IDs. Effect on a learner's time is unchanged, since none is on a goal path.

**Q2. What kind of necessity does each hard edge assert?**
I adopt a required `reason` per edge: `math`, `safety`, `tool`, `context`, or `textbook-order`. Only the first three can be hard. Applying your counterexample test to my own Round 1 edges found errors:

| My edge | Counterexample | Fix |
|---|---|---|
| R05 ← R06 | Analytic 2R IK needs only trigonometry | R05 ← R04; R06 soft, hard only for the numerical-IK objective |
| R07 ← R06 | Lagrangian of a pendulum needs no robot Jacobian | R07 ← R04, M06, M07, R01; R06 soft |
| C05 ← M10 | The DP derivation of LQR needs matrix calculus, not gradient descent | C05 ← C02; M10 soft |
| C02 lacked M06 | C02 absorbed C04 and multivariable linearization | C02 gains M06. Merging raised its closure, a real cost of the merge. |
| E07 ← E16 | Public datasets exist | E16 soft |
| M13 ← M17 | Basic convexity needs no SVD | M17 soft |
| E04 ← S02 only | A reaching skill needs FK | E04 ← R04, S02 (accepting your R04) |
| R02 ← R01; R03 ← R02 | DOF counting needs no dynamics | Accept your R02 ← M01 and R03 ← M12/M03 |

Also accepted: `C08 ← C07, R03` (frames were the real need); R16 is soft there. `S05 ← S03` already agreed.

Edge-level validation of the revised graph: no cycles. Ancestors: E02 14→2, R04 8→4, E06 23→11, E07 20→17, S09 17→13, C05 12→9.

**Q3. How is transfer distinguished from parameter substitution?**
- New numbers in the same form are **retention**, never transfer.
- Transfer must change at least one of: representation, assumption, context, or the method that must be selected, following Barnett & Ceci's dimensions.
- Automatic PASS verifies only what a test observes: for example, that a function meets hidden behaviour on inputs the learner didn't see. It cannot show that the person understood why, or that they could frame an unframed problem.
- A machine-checked transfer *task* can support T-trans only if the novelty is real and the prompt hasn't been published in the lesson. Anything open stays reviewed-only. I am not fully confident that any automated check suffices for L3, so L3 keeps a human reviewer.

**Q4. Could an existing visual do the job?** Largely yes. See the cut from 16 to 5 above.

**Q5. Which links have been checked?** Each resource has its label. No per-lecture fit was verified beyond existing registry mappings. I did not verify captions or durations. Book chapter mappings for MR, Underactuated and Manipulation come from their tables of contents, which shows topic location, not teaching quality.

**Q6. What measured learner outcomes support time savings?** None. See 2.6.

**Q7. Does anything break immutable evidence?** One thing did: the alias rule, now replaced. The decay rule removes readiness but leaves historical evidence intact, so it passes. It does change what a learner sees, so it needs explicit approval.

### 2.5 Where I disagree with Codex

**D1. One new node is not enough.**
- *Codex's position:* add R16 motion planning, and treat other gaps as subskills of existing topics.
- *Counter-evidence:* trace a capstone backward. A simulated pick and place needs a timed trajectory and joint or task-space control under contact. In the current overviews, no topic covers time scaling, and no topic before C14 Whole-Body Control (which needs R11 floating-base dynamics) covers torque control of an arm. Modern Robotics devotes Ch. 9, 11 and 13 to these [toc].
- *Why subskills fail here:* R07 is already estimated at about 20 h. Adding impedance control to R07, or to C03 (PID), breaks the "PASS states what it licenses" rule in P01.
- *Cost and risk:* 105 h spread across paths, and more material to author in a backlog that is already long. M19 and R16 are the weakest of mine: they could become subskills (C03 + V02; R09 + C08), and I now concede that **R16 and M19 are open**.
- *Confidence:* high for R17, R18, R19; medium for R20; low for R16, M19 as separate units.

**D2. Spectral methods belong in their own identity, not inside M04 or M11.**
- *Codex's position:* expand M04/M11.
- *Counter-argument from Codex's own rules:* M04 has existing v1 evidence with a narrow scope. Expanding the topic means an L1 from v1 sits under a broader title, which is the misleading state P01 warns against. A new ID keeps both honest.
- *Practical:* M04 remains short for those needing rank only. M17's dependents (R05 numerical, V11, C02 poles) are specific. A versioned scope on M04 could do the same job; I would accept that if contract tooling supports scope versions.
- *Confidence:* medium.

**D3. Your matrix is an inventory, and the mission needs decisions.**
Your matrix assigns a route role and a method, drawn from the existing overview text. It preserves almost everything and defers most of what to teach, merge or de-prioritize. That is a defensible caution, since evidence is limited. However, "pilot first" cannot be applied to 169 topics by one maintainer, so someone has to make priority calls under uncertainty. For instance, R10 Mechanical Design Verification is marked track core; which track needs it? I would defer it. Which topics would you actually author in the next 100 hours?

**D4. Should R04 stay planar?**
Your view is planar first, with PoE as an extension. I accept that PoE is an extension for non-MAN goals. However, a 2R planar arm alone is not enough for R04: URDF robots are spatial chains. My revised R04 is planar derivation, then spatial FK through a transform chain. This needs no twists, and S04's URDF validation depends on it. Twists and PoE move to new unit R21 (6 h, MAN), with R03 down from 14 h to 12 h. No comparative data exists for either, so this is a teaching judgment. Medium confidence.

**D5. Is "≥80% compatibility" acceptable for new forms?**
You call item counts unvalidated and leave them to pilots. Agreed that they are unvalidated, but a pilot needs a starting value. With four items the threshold is really 100%, whatever anyone writes down. I keep 12 as the pilot's starting form and propose comparing against a shorter sequential variant. Binomial figures from Round 1 stand. They assume independent items of equal difficulty, which real items are not.

**D6. Is C03 ← C02 a hard edge?**
You leave it unchanged. I argue PID tuning can begin with C01 and simulation; a stability analysis needs C02. This is the same scope-dependent point you make for C02 itself, so I expect we can settle on a scope split.

### 2.6 Validation design replacing savings claims

The figures in 1.11 and the closures in 2.3 are **planning hypotheses**.

**Pilot, deliberately small enough for one maintainer:**
- *Design:* within-learner crossover over 2–3 pairs of comparable topics (for example M06 vs M17, or C02 vs C07). In each pair, one topic uses the current lesson and fixed form, and the other uses the new workflow and form. Assign by coin flip.
- *Outcome:* delayed, unfamiliar task at 7 and 21 days. Secondary: active minutes, assistance level, abandonment.
- *Not outcomes:* watch completion, repeating the same form, or self-rated understanding, given Deslauriers 2019.
- *Limits:* with a single learner, this informs practical decisions but does not support general claims. Carry-over between topics and motivation effects are likely. Results should be published as case data. A community version would need consented data and separate review.
- *Stop rule:* if the new form takes more than twice as long without a better delayed result, revise it before expanding.

### 2.7 Weaknesses this round exposed in my reasoning

1. I missed four concrete repository findings Codex found, because I audited structure more than individual item content. I should read more of the actual lessons before Round 3.
2. I claimed "no assessable objective" without reading the overview tasks.
3. Several of my hard edges followed textbook order.
4. My merges raised some closures (C02). I reported ancestor reductions without flagging this until now.
5. My closure analysis uses my own edges, so its output partly reflects its inputs.
6. Estimated hours still run through much of my reasoning. I should use them only for comparing relative sizes.

### 2.8 Status of my Round 1 claims

| Claim | Status |
|---|---|
| C1 Evidence validity first | Stands; strengthened by the index-0 finding |
| C2 Spine and tracks | **Modified:** computed core, goal closures, capstones |
| C3 Readiness vs mastery | Stands, with Codex's scoped framing |
| C4 New nodes | Modified: 12 now with R21; R16 and M19 are open |
| C5 Remove, merge, defer | **Modified:** archive with IDs; merges are study units only |
| C6 PoE | **Modified:** MAN track only |
| C7 Machine-checkable item types | Stands; add `applicable dimensions` |
| C8 Review scheduling | Modified: daily budget added; schedule is a heuristic |
| C9 Workflow by knowledge type | Stands, using Codex's profile names |
| C10 No auto-certification of open work | Stands; both agree |

### 2.9 Questions for Codex Round 2

1. Accept or reject D1, using a capstone trace. Where would you put time scaling and torque control so that a PASS still states what it licenses?
2. Which topics would you author in the first 100 hours, and in what order?
3. Do you accept the edge-reason rule (`math`, `safety`, `tool` as the only hard reasons)? Which edges in your projection would fail it?
4. For a single-user install with no reviewer, should the UI show L3 as unavailable, or as "needs external reviewer"?
5. Does the crossover pilot in 2.6 hold up, and what would you change?

---

## Round 3: response to Codex Round 2

Codex Round 2 answered my Round 1 and did not treat my Round 2 as completed evidence, so some of its objections were already resolved there. I mark those "already changed in 2.x". My Round 2 questions (2.9) are still open for Codex.

### 3.1 Answers to Codex's six questions

**Q1. Will you replace the 540 h spine?** Yes, already done in 2.3. The catalog stays only as an optional comprehensive program, never as a universal starter path. Recomputed in 3.5.

**Q2. Will you retain all 169 identities and require missing evidence for expanded scopes?** Yes. An old PASS never inherits a broader scope.

**Q3. Which of the 36 merges are competency merges?** After your review, **none**. All are study groupings, with separate objective tags and separate scoring. Your PPO challenge is correct: I had no good justification for it.

| Change | Reason |
|---|---|
| RL09 restored as its own unit; RL11 ← RL07, RL09; RL10 ← RL09, ML06 | SAC needs actor-critic, not PPO clipping |
| E08 ← RL02, ML06 (RL09 soft) | A learned model plus shooting or CEM needs no policy optimizer |
| M12 restored as its own unit; V03 ← V01, M12; R03 ← M12 | A camera model should not wait for mechanisms |
| C09 restored as its own unit | See 3.4 |
| V08/V10, C02/C04, C06/C07, RL05/RL06 | May share a project; each ID keeps a separate PASS |

32 groupings remain. Since a grouping affects only navigation, it needs objective-level evidence only if somebody later proposes merging scores.

**Q4. Twelve items, 24-hour lock, three options?** All three corrected.

| My claim | Correction |
|---|---|
| "≥10/12 passes a 90% learner 89%" | Illustration only. With my own separate dimension gates, a 6-C/6-M form gives .7845 (reproduced). Items are also correlated and uneven. |
| Form of "at least 4 C, at least 4 M" gated at 80% | **A further error of mine that you did not list:** with 4 items in a dimension, 80% again means 4 of 4. That is the very defect I criticized. A 4-C/8-M form with those gates gives .53 at p=.9. |
| "3 or more plausible distractors" | **Misread source.** Rodriguez concerns three *options*: one key plus two distractors. |
| "No two-option C items" | Not supported by that source. Revised: no C gate may rest on one binary item, and option order is randomized. |
| "At least 24 h after a failure" | Withdrawn; Hausknecht does not support a constant. Immediate corrective practice is allowed. A later independent attempt uses a new form and records the exposure context. Delay is a pilot variable. |

Revised default: required coverage per critical objective (starting at 2 or more items), not a fixed form length. Length follows the evidence profile. Thresholds start as pilot values.

**Q5. Transparent checks instead of "hidden tests"?** Yes. New term: **undisclosed-before-attempt, versioned, locally inspectable checks**. They are not tamper-proof. Also accepted: open M and T judgments stay human-reviewed.

Expression checks need declared domains and adversarial sample points. Your examples are right: `x/x` vs `1`, and `|x|` vs `x` on positive samples. I would name them "checked expression", never "verified derivation". Generated banks need schema, version, seed and an oracle check. They are not cheap, so my 2–4 h per topic estimate was probably low.

**Q6. Edge recipe, 189/190, review load by skills.**
- **The discrepancy was my error.** I edited S09 (RL13 became soft) after computing the totals and did not rerun them before writing the text. The published Round 1 matrix has **189 hard and 19 soft edges**. Your count is right; my text's 190 and 18 were stale.
- **Recipe:** a row is live if its prerequisite field is not `-`. Split the field on `~`: the left side is hard, the right is soft. Split each side on commas. Rows with `-` have no edges. Grouped rows are not live as study units, though their IDs remain as evidence identities. The revised matrix in 3.9 is canonical: **123 live units, 201 hard edges, 34 soft edges, depth 11, no cycles** (scripted).
- **Review load:** see 3.6.

### 3.2 Other points from Codex Round 2

| Codex point | Decision | Notes |
|---|---|---|
| C7 overstated "real" evidence | **ACCEPT** | Scoped procedural and implementation evidence only |
| "No item kind can test derivation" too broad | **ACCEPT** | `short` can ask for one; what's missing is a verifier. Corrected wording: no item kind can *automatically verify* one. |
| "Knowledge type does not change the assessment" too broad | **ACCEPT** | `isObjective` uses knowledge type. All 31 forms still share one shape. |
| Keep worked examples; separate the assessed task | **ACCEPT, with a narrower dispute** | I objected to the exact graded function being solved on the page. The fix is a materially different lab, with the example kept. |
| No blanket prose cap or time percentages | **ACCEPT** | Withdrawn. The 300–500 word figure and the time-split column have no evidence. |
| LQR "requirement for controllability" | **ACCEPT, an error** | Your counterexample holds: A=diag(−1,1), B=(0,1)ᵀ is stabilizable and not controllable. Infinite-horizon needs stabilizability plus detectability conditions. Finite-horizon needs neither. |
| NEES "inside an interval" | **ACCEPT** | 1−.95²⁰=.6415 reproduced. Revised: ensemble-average NEES over a stated number of runs, against a chi-square bound with a stated false-failure rate, plus covariance symmetry and innovation checks. |
| Advantage normalization is not a bug | **ACCEPT, an error** | Bug set: wrong ratio sign, wrong terminal vs truncation bootstrap, stale log-probs. Normalization is an ablation. |
| IQM not compulsory | **ACCEPT** | Needed only when comparing methods. A single-task CPU lab reports its median and spread over the seeds. |
| ML06/V06 need no PyTorch mathematically | **MODIFY** | True. I keep the edge with reason `tool`, stated as a tensor and autodiff capability. PyTorch is the default, and another framework can satisfy it. |
| Readiness at scale: 570–1,520 associations | **ACCEPT** | Start with selected high-impact and safety edges, with reusable checks. Expiry is a hypothesis. |
| Node vs sublesson comparison | **ACCEPT** | Rule in 3.4 |
| Semantic names, not numeric IDs | **ACCEPT** | The maintainer chooses final IDs. My IDs are working labels, with the names in the matrix. |

**HRI and the cognitive track: my omission.** The brief names Cognitive Robotics, and I had filed all of it as registry. I add a **COG** research-tier path (E03, E09, E10, E12, E14, E17), reviewed-only and with no automatic certification. I have no strong evidence for its content. It exists because the mission asks for it, and it is the least developed part of my proposal. Human-subject work needs separate ethics review.

### 3.3 New audit: I read all 124 objective items

I said in 2.7 that I should read the items. Answer keys were checked by hand, and I found no incorrect key under the conventions in the lessons.

**A real false-failure defect.** M08 q4 (fair die, P(result > 4)) stores 0.3333333333333333 with tolerance 1e-5. Run against the grading logic:

| Input | Result |
|---|---|
| `1/3` | Wrong (not a number) |
| `0.33` | Wrong |
| `0.333` | Wrong |
| `0.3333` | Wrong |
| `0.33333` | Correct |

Because 4/4 is required, a person who solves this correctly can fail L1 of M08, the Probability topic. The input hint only says "Enter a number…". v1 is immutable, so the fix belongs in a new version, along with a UI note on precision. *Confidence: high; checked by running it.*

**Answers depending on unstated conventions.** The correct result is underdetermined by the prompt alone:

| Item | Issue |
|---|---|
| ML02 q2, q3 | J is not defined. -1.5 assumes a ½ and a mean; other definitions give other answers. |
| ML05 q2, q3 | L is not defined. 4 assumes ½e². |
| R07 q1 | Angle zero reference is not stated |
| RL01 q4, RL02 q4 | Rely on "this lesson convention" and an unstated wait reward |

*Effect:* these partly test whether someone just read this lesson, which adds construct-irrelevant variance.

**Construct mismatch.** Of 93 M items, I judge about 27 in 9 topics to be not mathematical reasoning: CPP01, CPP02, PY01, PY04, PY07, T04, RS01, V01, R02. Examples: "A three-case test suite fails one case. Number of passing cases?", "255 normalized by 255?", and "A vector has size 3. Number of valid elements?". This is my judgment and should be checked. It supports your point that M can be inapplicable.

**Trivial C items.** Examples: a revolute joint measured in radians or metres; "Which maps joint acceleration to inertial torque? M(q) or the learning rate". Beyond the index-0 pattern, the wrong option is often implausible, so even a learner unaware of the pattern may pick correctly by elimination.

**What this changes.** v2 pilots should start with M08, ML02, ML05, R07 and RS01, as well as M02, PY01 and R04, since those have concrete defects to fix.

### 3.4 Rule for new unit vs extension, applied

A candidate becomes a new unit only if **all** hold: (a) its PASS is not within any existing v1 scope; (b) a goal capstone or at least two dependents need it; (c) it can't be added to an existing ID without changing what that ID's PASS licenses. This rule is my proposal and is unvalidated.

| Candidate | Result | Decision |
|---|---|---|
| Spectral Methods & Least Squares | Passes | New |
| Motion Planning | Passes | New |
| Trajectory Generation | Passes (MAN capstone) | New, small |
| Manipulator Control | Passes | New |
| Mobile Robots & Localization | Passes | New |
| Twists & PoE | Passes (replaces my C6) | New, MAN only |
| Nonlinear Least Squares | Passes; V17 requires it | New, but pulled at first use |
| Sensors & Measurement | Borderline: one hard dependent | Keep, low confidence |
| Robot Data Collection | Borderline: soft for E07, needed by RLL capstone | Keep, low confidence |
| Information Theory | Fails (b)/(c) in part | Short sublesson pulled by ML11 or RL10 |
| HRI & Shared Autonomy | Passes for COG | New, reviewed-only |
| **Signals & Frequency** | **Fails (c)**: C09 already covers sampling and delay | **Withdrawn**; content goes to the existing C09 |

Result: this resolves my concession in 2.5 on M19. Your "subskill" view was correct there and not for the others.

### 3.5 Recomputed core and closures

Using revised edges and a COG goal. Hours are relative sizing only.

| Set | Topics | Hours |
|---|---|---|
| In all 6 goal closures | M01, M02, M03, PY01, PY04 | 48 |
| In all 5 non-SYS closures, adding | M05, M06, M07, M10 | 98 total |
| Plus cross-cutting starter (T01, T02, PY07, RS01, S07 awareness) | 5 | about 31 |
| **Common core** | | **about 80–130** |

| Goal | Units | Hours + capstone |
|---|---|---|
| SYS | 28 | 300 |
| COG | 38 | 422 |
| PER | 38 | 448 |
| RLL | 40 | 456 |
| MAN | 46 | 551 |
| MOB | 50 | 615 |

M12 and R03 dropped out of the universal core because a COG goal might not need robot kinematics. That is arguably a weakness of the leaf list rather than a real finding. I still treat frames as near-universal and would recommend them to anyone working with a physical robot.

I do not state a saving percentage. Per Codex, these compare unmeasured hour models with changed scopes.

### 3.6 Review load by active skills

Event cost of 2 minutes per skill is an assumption. Load is S/I events per day at steady state, for S active skills and terminal interval I. New skills add intake: each passes through k stages.

| Active skills | Terminal interval | Events per day | Minutes per day |
|---|---|---|---|
| 93 (31 topics × 3) | 21 days | 4.4 | 8.9 |
| 345 (115 × 3) | 21 days | 16.4 | 32.9 |
| 93 | 365 days | 0.25 | 0.5 |
| 345 | 365 days | 0.95 | 1.9 |

Intake at 6 new skills per week: about 3.4 events per day with 4 stages (about 7 minutes), or 6 with 7 stages (about 12 minutes). Lapses add more.

**Corrections.** My "48 minutes per day" applied only to a hypothetical 169-topic future, and today's equivalent would be 8.86 as you computed. **I withdraw "30–45 minutes freed".** The defensible statement: a 21-day cap scales poorly as skills accumulate; longer tails trade review load against unknown forgetting; and a long-tail schedule shifts load toward intake. Every number in this table depends on assumed S and cost. A daily budget remains the safer control.

### 3.7 Revised blueprints, replacing the Round 1 text where they differ

- **R03 (now 8 h):** drop `exp6`, `adjoint` and near-π `log3`, which move to Twists & PoE. Keep composition, inverse, rotation validity and quaternion conversion.
- **R04:** planar derivation, then spatial FK by transform chain, `fk_chain(joints, q)`. PoE moves to Twists & PoE.
- **R06:** position Jacobian by differentiation and finite differences, plus statics. Space and body twist Jacobians are required only on MAN. State output convention, frame, row order and units before comparing equations, as you proposed.
- **R05:** two scopes. Analytic planar (needs R04). Numerical (needs R06; M17 for damping).
- **R07:** R06 soft; pendulum and 2-link through the Lagrangian directly.
- **C05:** replace "requirement for controllability" with the correct conditions.
- **C07:** ensemble NEES criterion as above. Preceded by covariance in M09.
- **RL10:** now 12 h, with RL09 separate. Bug set and reporting as above.
- **E07 (14 h, L2 target):** MLP BC first, ACT when the budget allows. Diffusion and flow remain separate in E11.
- **M02/PY01 labs:** v2 must use materially different tasks from the page's reference code.

**L3 targets now:** ML05, R06, C05, C07, RL10. All need a human reviewer, so on a single-user install they may stay unfilled.

### 3.8 Remaining disagreements

| # | Topic | My position | Confidence |
|---|---|---|---|
| D1 | Number of new units | 11 by the 3.4 rule, not a minimal set. You've moved toward this; the rule is open to challenge. | Medium |
| D2 | Spectral identity | New ID, or a versioned M04 scope | Medium |
| D3 | Decisions under uncertainty | A concrete first-100-hours order is needed, not only pilots | Medium-high |
| D4 | R04 scope | Must reach a spatial chain to feed URDF | Medium |
| D5 | Default path | A default for those who don't choose, with opt-out | Medium |
| D7 | Should failed review remove readiness? | Yes, displayed separately, with history retained. You call expiry a hypothesis, and I agree the clock is, but a failed check is direct evidence. | Medium |

D6 (C03 ← C02) is resolved by scope: C03 tuning needs C01, and stability analysis needs C02.

**My proposed first 100 authoring hours (planning estimate, for D3)**
1. Defect fixes: M08 precision, recommendation text, ROS version, source_refs for M07 and M08, demo-model labels (under 10 h).
2. Item kinds, contract v2 and applicable-dimension declaration (about 30–40 h).
3. Pilot contracts: M08, ML02, ML05, R04, PY01, M02 (about 20 h).
4. Crossover pilot setup with logging of active minutes (about 10 h).
5. Common-core bridges: M01 trig, M05 integration, M09 covariance (about 20 h).

No new lessons beyond these until the pilot reports. That is a deliberate choice: it delays visible content.

### 3.9 Weaknesses in my reasoning this round

1. A stale number reached print, and a statistical error (4-item dimension gates) contradicted my own argument.
2. I misread the title of a source I cited. Citations verified at [meta] level do not protect against misreading them.
3. Three technical errors in blueprints (LQR, NEES, PPO) would have failed correct learners. **More blueprint errors probably remain, so all blueprints need expert review before use.**
4. The item audit's judgment of "construct mismatch" is mine and unreviewed.
5. COG is thin.

### 3.10 Questions for Codex Round 3

1. Does the 3.4 rule hold? Show a candidate it misclassifies.
2. Do you dispute any of the 3.3 item findings, particularly the M08 precision defect?
3. Please check the edges in the canonical matrix below, using the stated recipe.
4. What is your first-100-hours order, and what would make you prefer it to mine?
5. Do you agree a failed readiness check should change what the recommender offers, given that history stays intact?

### 3.11 Canonical matrix after Round 3

Replaces section 1.8 for all later discussion. S now means **optional comprehensive catalog**, not a required spine. GROUP means a shared study unit with separate IDs, objectives and scores. ARCHIVE keeps the ID but places it on no path. COG is the added track. Hours are planning sizes only. Gate `L` means undisclosed-before-attempt versioned checks.

| ID | Topic | Action | Tier | Path | h now→new | Hard prereq ~soft | Mix | Gate | Tgt | Focus: transfer task, misconception, note |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | Mathematical Basics | RESCOPE | F | S | 6→8 | none | Z W C | Q | 2 | Readiness probe first; lesson only on failure. T: derive a calibration inverse with units. Mis: function vs formula; unit-free reasoning. |
| M02 | Vectors | KEEP | F | S | 8→8 | M01 | Z V D C | Q+L | 3→2 | L2 lab must test dot, norm and projection, not dot only. T: decompose a force along a sloped surface. Mis: dot product as a vector; projection onto zero vector. |
| M03 | Matrices | KEEP | F | S | 10→10 | M02 | V Z D C | Q+L | 3→2 | T: read a matrix from images of basis vectors, then compose in a stated order. Mis: AB=BA; shape agreement implies meaning. |
| M04 | Linear Algebra | RESCOPE | F | S | 20→14 | M03 | V Z D C | Q+L | 2 | Stop at rank, nullspace, solving; spectral content moves to M17. T: which parameters can two dependent sensors recover? Mis: more equations always determine x. |
| M05 | Calculus I | RESCOPE | F | S | 20→14 | M01 | V Z D C | Q | 2 | Differentiation and chain rule first; integration just in time. T: linearize a sensor curve and bound its error. Mis: derivative as slope only, never as sensitivity. |
| M06 | Multivariable Calculus | KEEP | F | S | 20→14 | M03, M05 | V Z D C | Q+L | 3→2 | Remap video: current 3b-gradient does not teach Jacobians. T: verify a hand Jacobian by directional differences. Mis: Jacobian row/column order. |
| M07 | Differential Equations | RESCOPE | F | S | 16→12 | M05~M03 | V Z S C | Q+L | 3→2 | Phase portraits and numerical integration over closed-form tricks. T: pick dt for stiff decay. Mis: Euler stability equals accuracy. |
| M08 | Probability | KEEP | F | S | 20→14 | M01 | Z V W C | Q | 2 | No video today; add MIT 6.041SC or 18.05. T: posterior after two correlated alarms. Mis: confusing P(A given B) with P(B given A); ignoring base rate. |
| M09 | Statistical Foundations | RESCOPE | F | S | 16→14 | M08 | Z W C | Q+L | 2 | Absorbs RS03 basics (CI, effect size). T: seeds needed to detect a stated effect. Mis: CI as probability the parameter is inside. |
| M10 | Optimization | RESCOPE | F | S | 14→10 | M06 | Z V D C | Q+L | 2 | T: diagnose divergence from a loss curve. Mis: lower training loss always better; learning rate as the only knob. |
| M11 | Numerical Computing | RESCOPE | F | S | 14→12 | M03, M05, PY04 | C Z W | Q+L | 2 | Absorbs PY05 (SciPy, plotting). T: rank a solver by residual versus parameter error. Mis: small residual means accurate solution. |
| M12 | Rigid-Body Geometry | KEEP | F | S | 8→5 | M03 | V Z D C | Q+L | 2 | Elementary frames and homogeneous transforms; gates V03. Own evidence identity. T: camera point to base with a new mount. Mis: translating a direction. |
| M13 | Advanced Optimization | RESCOPE | A | MAN,MOB | 25→18 | M10~M17 | V D C | Q+L+X | 2 | Convex, QP, Lagrange, KKT; Boyd & Vandenberghe selectively. T: actuator allocation QP. Mis: active constraint means infeasible. |
| M14 | Advanced Probability | DEFER | R | J | 25→0 | - | — | N | 2→1 | Conditional independence to M08; random processes to C07. Pull in for research only. |
| M15 | Lie Theory | RESCOPE | A | PER,MOB | 25→8 | R03, M06 | D C P | Q+L | 2 | Only what estimation needs (micro Lie theory); R03 already covers exp coordinates. T: perturbation Jacobian check. Mis: adding rotation vectors composes rotations. |
| M16 | Advanced Mathematics | ARCHIVE | R | X | 60→0 | - | — | N | 1→– | Catch-all without assessable objective; registry entry only. |
| M17 | Spectral Methods & Least Squares | NEW | F | S | 0→16 | M04 | V Z D C | Q+L+X | new:2 | Eigen, SVD, pseudoinverse, linear least squares. See blueprint. Mis: eigenvalues and singular values interchangeable. |
| M18 | Information Theory Essentials | NEW | A | RLL | 0→5 | M08 | Z D C | Q | new:2 | Entropy, KL, MLE/cross-entropy link; needed by ML11, RL10. T: why KL is asymmetric in a policy update. Mis: KL as a distance. |
| M20 | Nonlinear Least Squares | NEW | A | PER,MOB | 0→8 | M10, M17 | D C Z | Q+L | new:2 | Gauss-Newton, LM, robust loss. T: fit with outliers. Mis: a converged cost implies global optimum. |
| PY01 | Python Fundamentals | RESCOPE | F | S | 15→12 | none | C W | Q+L | 3→2 | Absorbs PY03. Lab must exceed mean(). T: unfamiliar parser from a spec. Mis: aliasing versus copying; print versus return. |
| PY02 | Data Structures | RESCOPE | F | S | 15→10 | PY01 | C Z | Q+L | 2 | Add complexity, graphs, BFS, heaps; feeds E02. T: pick a structure for sensor queues. Mis: list is fine for every queue. |
| PY03 | Python Semantics | GROUP→PY01 | F | S | 6→0 | - | — | — | 2 | PY01 q4 already tests aliasing; keep advanced aspects in debugging exercises. |
| PY04 | NumPy | KEEP | F | S | 10→10 | PY01~M03 | C Z | Q+L | 3→2 | T: vectorize a forward-kinematics batch. Mis: broadcasting silently aligns intended axes. |
| PY05 | Scientific Python | GROUP→M11 | A | S | 10→0 | - | — | — | 2 | SciPy is learned through numerical tasks, not separately. |
| PY06 | PyTorch Basics | KEEP | F | S | 10→10 | PY04~ML04 | C V | Q+L | 2 | Currently has one dependent (S11); must gate ML06, V06. T: match autograd to a hand gradient. Mis: gradients reset automatically. |
| PY07 | Testing & Debugging | RESCOPE | F | S | 10→10 | PY01 | C W | L | 2 | Absorbs T04; mutation-kill score replaces most quiz items. T: tests that reject seeded bugs. Mis: passing tests prove correctness. |
| PY08 | Research Programming | GROUP→RS04 | A | S | 10→0 | - | — | — | 2 | Configuration, logging and seeds fold into RS04. |
| PY09 | Performance | DEFER | A | SYS | 10→6 | PY04, PY07 | C | L | 2 | Absorbs T07. Pull when a pipeline misses a budget. T: profile, then fix the measured bottleneck. Mis: optimizing without measuring. |
| PY10 | Advanced Python | ARCHIVE | R | X | 15→0 | - | — | N | 1→– | No robotics dependency; learn from documentation when required. |
| CPP01 | C++ Fundamentals | KEEP | A | SYS,MAN | 15→12 | T01 | C W | Q+L | 2 | Track-level, not spine. T: find truncation from compiler warnings. Mis: integer division; uninitialized values. |
| CPP02 | Memory Model | KEEP | A | SYS,MAN | 12→12 | CPP01 | C V Z | Q+L | 3→2 | T: explain and fix a dangling reference after vector growth. Mis: reference keeps object alive. |
| CPP03 | Resource Management | RESCOPE | A | SYS,MAN | 12→16 | CPP02 | C W | L+X | 3→2 | Absorbs CPP04. T: design a bounded joint-state class. Mis: move leaves source unusable; manual new/delete is simpler. |
| CPP04 | Classes & OOP | GROUP→CPP03 | A | SYS,MAN | 10→0 | - | — | — | 2 | Invariants and RAII are one skill in practice. |
| CPP05 | STL & Algorithms | RESCOPE | A | SYS,MAN | 15→12 | CPP01 | C W | L | 2 | Absorbs useful CPP06 idioms. T: select container for timestamp lookup and measure it. Mis: map always beats sorted vector. |
| CPP06 | Modern C++ | GROUP→CPP05 | A | SYS | 20→0 | - | — | — | 2 | Templates and constexpr only when a library reading task requires them. |
| CPP07 | Build Systems | RESCOPE | A | SYS,MAN | 10→14 | CPP02, T01 | C W | L | 2 | Absorbs CPP08: CMake, GoogleTest, ASan/UBSan. T: reduce a failing program and add a regression test. Mis: no crash means no UB. |
| CPP08 | Debugging & Testing | GROUP→CPP07 | A | SYS,MAN | 12→0 | - | — | — | 3→2 | Tooling is verified together with the build. |
| CPP09 | Complexity & Performance | DEFER | A | J | 15→0 | - | — | N | 2 | Pull after a measured real-time miss. |
| CPP10 | Concurrency | KEEP | A | SYS | 20→12 | CPP03, CPP07 | C Z | L+X | 2 | TSan-clean producer/consumer. T: fix a real data race. Mis: volatile synchronizes. |
| CPP11 | Numerical C++ | KEEP | A | SYS,MAN | 12→8 | CPP05, M03 | C | L | 2 | T: Eigen least squares with Python oracle. Mis: aliasing in Eigen expressions; inverse rather than solve. |
| CPP12 | Advanced C++ | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; ABI work is out of scope for this mission. |
| ML01 | ML Problem Formulation | KEEP | F | S | 8→8 | PY04, M08 | W C | Q+A | 2 | T: find leakage in a supplied pipeline. Mis: random split is always valid for time series. |
| ML02 | Classical ML | KEEP | F | S | 14→12 | ML01, M06 | V Z D C | Q+L | 2 | T: regularization choice on small sensor data. Mis: regularization only reduces test error. |
| ML03 | Generalization | RESCOPE | F | S | 10→12 | ML01, M09 | Z C | Q+L | 2 | Absorbs ML07. T: choose a metric from decision costs. Mis: test set can be reused during tuning; accuracy under imbalance. |
| ML04 | Neural Networks | KEEP | F | S | 8→8 | ML02 | V Z C | Q+L | 2 | T: count parameters and shapes of an unseen net. Mis: depth alone adds nonlinearity. |
| ML05 | Backpropagation | KEEP | F | S | 10→10 | ML04, M06~PY06 | V Z D C | Q+L+X | 2→3 | See blueprint. Mis: backprop is the learning rule. |
| ML06 | Deep Learning Training | KEEP | F | S | 14→14 | ML05, PY06, M10 | V C Z | Q+L | 2 | PY06 edge is missing today. T: diagnose a broken training run from curves. Mis: bigger model first. |
| ML07 | Model Evaluation | GROUP→ML03 | F | S | 10→0 | - | — | — | 2 | Evaluation and generalization share one held-out discipline. |
| ML08 | Representation Learning | RESCOPE | A | RLL,PER | 12→10 | ML06 | V Z C | Q+A | 2 | Absorbs ML10, V14, V18. T: frozen DINOv2 features on a small robot set. Mis: pretraining guarantees transfer under shift. |
| ML09 | Transformers | KEEP | A | RLL,PER | 12→10 | ML06 | V Z C | Q+L | 2 | Absorbs V15. T: compute attention and patch counts by hand. Mis: attention weights explain decisions. |
| ML10 | Self-Supervised Learning | GROUP→ML08 | A | RLL | 12→0 | - | — | — | 2 | Taught as one route to representations. |
| ML11 | Generative Models | RESCOPE | A | RLL | 25→12 | ML06~M18 | V Z D C | Q+L | 2 | VAE sketch, then DDPM/flow focus for action policies. T: multimodal 1-D action fit. Mis: MSE handles multimodal targets. |
| ML12 | Advanced ML | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; paper-specific reproduction lives in RS06. |
| T01 | Linux | RESCOPE | F | S | 10→10 | none | C | L | 2 | Absorbs T03; Missing Semester. T: repair a broken environment using only the shell. Mis: sudo as a fix. |
| T02 | Git | KEEP | F | S | 6→6 | none | C | L | 2 | Study from week 1 in parallel. T: recover from a bad merge. Mis: commit equals backup of environment. |
| T03 | Development Tools | GROUP→T01 | F | S | 6→0 | - | — | — | 2 | Debugger use is reinforced in PY07 and CPP07. |
| T04 | Software Testing | GROUP→PY07 | F | S | 8→0 | - | — | — | 2 | Same video as PY07; keep T04.v1 evidence as alias. |
| T05 | Reproducible Environments | GROUP→RS04 | F | S | 6→0 | - | — | — | 2 | Environments are the first half of reproducibility. |
| T06 | Docker | DEFER | A | SYS | 8→5 | T01, RS04 | C | L | 2 | Pull when deployment needs it. T: rebuild a ROS image. Mis: container state persists. |
| T07 | Systems Performance | GROUP→PY09 | A | SYS | 10→0 | - | — | — | 2 | Same measurement discipline. |
| T08 | Advanced Infrastructure | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Infrastructure catch-all. |
| R01 | Mechanics Foundations | RESCOPE | F | S | 14→10 | M02 | V S D | Q+L | 2 | T: predict cart acceleration in MuJoCo before running. Mis: force causes velocity rather than acceleration. |
| R02 | Robot Mechanisms | KEEP | F | S | 6→6 | M01 | V Z W | Q | 2 | Grübler formula, task vs joint space. T: count DOF of an unseen mechanism. Mis: DOF equals number of motors. |
| R03 | Rigid-Body Transformations | RESCOPE | F | S | 10→8 | M12 | V Z D C | Q+L+X | 2 | Spatial composition and rotation representations; twists and near-π log move to R21. See blueprint, as revised. Mis: any orthogonal matrix is a rotation; rotation vectors add. |
| R04 | Forward Kinematics | RESCOPE | F | S | 10→10 | R03 | V Z D C | Q+L+X | 3→2 | Spatial PoE and URDF chain, not 2R only. See blueprint. |
| R05 | Inverse Kinematics | RESCOPE | F | S | 10→10 | R04~R06, M17 | V Z D C | Q+L+X | 2 | Follows the Jacobian. T: damped LS at a singular target with joint limits. Mis: IK has one answer; solver error means unreachable. |
| R06 | Robot Jacobian | RESCOPE | F | S | 12→12 | R04, M06~M17 | V Z D C | Q+L+X | 3 | Teach geometric Jacobian and statics. See blueprint. |
| R07 | Rigid-Body Dynamics | KEEP | F | S | 24→20 | R04, M06, M07, R01~R06 | V S D C | Q+L+X | 3→2 | Absorbs RNEA overview from R12. See blueprint. |
| R08 | Contact Mechanics | KEEP | A | MAN,MOB | 14→10 | R07 | V Z S | Q+L | 2 | T: friction-cone limit tested in MuJoCo. Mis: friction force always equals μN. |
| R09 | Actuators & Transmission | RESCOPE | F | S | 8→6 | R01 | V W | Q | 2 | T: choose a gear ratio under speed and torque limits. Mis: higher ratio dominates. |
| R10 | Mechanical Design Verification | DEFER | A | J | 15→0 | - | — | N | 2→1 | Hardware-builder path only. |
| R11 | Floating-Base Dynamics | KEEP | A | MOB | 18→14 | R07, R08 | V D S | Q+L | 2 | T: why joint torques cannot command base acceleration directly. Mis: base treated as actuated. |
| R12 | Advanced Dynamics | GROUP→R07 | A | J | 20→0 | - | — | — | 2 | RNEA concept in R07; Featherstone depth pulled on demand. |
| R13 | Advanced Locomotion | KEEP | A | MOB | 30→20 | R11, C05 | V S P | A+X | 2 | T: tune then explain a gait failure in simulation. Mis: stability equals zero tipping in steady state only. |
| R14 | Dexterous Manipulation | RESCOPE | A | MAN | 25→16 | R06, R08 | V S D C | Q+L+X | 2 | MR Ch. 12 and Manipulation. T: force-closure of unseen grasp. Mis: more contacts is always stronger. |
| R15 | Advanced Mechanics | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| R16 | Sensors & Measurement | NEW | F | S | 0→8 | M09~C09 | V C W | Q+L | new:2 | Encoders, IMU, F/T, depth, LiDAR; noise, bias, timestamps. T: Allan-style bias estimate on a log. Mis: datasheet noise equals in-system noise. |
| R17 | Trajectory Generation | NEW | F | S | 0→6 | R04~M05 | V Z D C | Q+L | new:2 | MR Ch. 9 time scaling. T: fastest profile under limits. Mis: path and trajectory are the same. |
| R18 | Motion Planning | NEW | A | MAN,MOB | 0→14 | E02, R03~R04 | V Z C | Q+L+X | new:2 | C-space, collision, PRM/RRT (MR Ch. 10, LaValle). T: narrow passage failure and fix. Mis: RRT paths are near-optimal. |
| R19 | Manipulator Control | NEW | A | MAN | 0→14 | R07, R06, R21, C03 | V S D C | Q+L+X | new:2 | Computed torque, task-space, impedance (MR Ch. 11). T: contact-stable impedance tuning. Mis: stiffer is always more accurate and safe. |
| R20 | Mobile Robots & Localization | NEW | A | MOB | 0→16 | C07, R16, R02 | V Z C | Q+L+X | new:2 | MR Ch. 13 plus particle filter localization. T: kidnapped robot recovery. Mis: odometry drift is zero-mean. |
| R21 | Twists & Product of Exponentials | NEW | A | MAN | 0→8 | R04, M06 | V Z D C | Q+L | new:2 | Twists, PoE, exp/log including near-π, space and body Jacobian. For tracks that derive with them. Mis: twist equals endpoint velocity. |
| C01 | Control Fundamentals | KEEP | F | S | 8→6 | M05~R01 | Z V D | Q | 2 | T: disturbance offset under P control. Mis: higher gain always better. |
| C02 | Dynamic Systems | RESCOPE | F | S | 16→16 | C01, M07, M04, M06 | V Z D C | Q+L | 3→2 | Absorbs C04. Brunton Control Bootcamp. T: linearize unseen pendulum and classify stability. Mis: local stability is global. |
| C03 | PID Control | RESCOPE | F | S | 10→10 | C01~C09, C02 | Z S C | Q+L | 3→2 | Tuning from C01 and simulation; stability analysis needs C02. T: anti-windup under saturation. Mis: derivative term has no noise cost. |
| C04 | Linear Systems | GROUP→C02 | F | S | 14→0 | - | — | — | 2 | Controllability and poles sit naturally beside state space. |
| C05 | LQR | KEEP | F | S | 12→10 | C02~M10 | V Z D S | Q+L+X | 3 | See blueprint. Mis: LQR is robust to any model error. |
| C06 | State Estimation | GROUP→C07 | F | S | 8→0 | - | — | — | 2 | Prediction and correction taught once, through the Bayes filter. |
| C07 | Kalman Filtering | RESCOPE | F | S | 16→16 | C02, M09 | V Z D C | Q+L+X | 3 | See blueprint. Mis: covariance reflects actual error regardless of model. |
| C08 | Sensor Fusion | RESCOPE | A | MOB,PER | 10→8 | C07, R03~R16 | C Z | Q+L | 2 | Fix wrong edge to R09 (actuators). T: time-aligned IMU+vision fusion. Mis: correlated sensors treated as independent. |
| C09 | Digital Control | RESCOPE | F | MAN,MOB,SYS,PER | 10→10 | C01, M05~M11 | Z V C | Q+L | 2 | Takes the signal content of withdrawn M19: sampling, aliasing, delay, first-order filters. T: choose a sample rate and cutoff. Mis: filtering is free of delay. |
| C10 | Nonlinear Control | DEFER | A | J | 25→0 | - | — | N | 2 | Lyapunov intro through Underactuated Ch. 9 when pursuing certificates. |
| C11 | Model Predictive Control | RESCOPE | A | MAN,MOB | 20→14 | C13, M13 | V Z C | Q+L+X | 2 | Reorder after C13. T: add a constraint and explain infeasibility recovery. Mis: MPC handles any model mismatch. |
| C12 | Nonlinear State Estimation | KEEP | A | MOB,PER | 12→10 | C07, M06 | V Z C | Q+L | 2 | T: EKF divergence on a bearing-only case. Mis: EKF covariance is trustworthy under strong nonlinearity. |
| C13 | Optimal Control | RESCOPE | A | MAN,MOB | 25→16 | C05, M10 | V D C | Q+L+X | 2 | Trajectory optimization before MPC; CMU 16-745. T: direct collocation of a swing-up. Mis: locally optimal trajectory is globally optimal. |
| C14 | Whole-Body Control | KEEP | A | MOB | 25→16 | R11, C11 | V D S | A+X | 2 | T: reprioritize tasks under limited torque. Mis: tasks combine without conflict. |
| C15 | Advanced Control | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; adaptive and robust material on demand. |
| S01 | Simulation Fundamentals | KEEP | F | S | 8→8 | M07, PY04 | S V C | Q+L | 2 | T: expose integrator energy drift. Mis: simulator output is ground truth. |
| S02 | MuJoCo | KEEP | F | S | 12→12 | S01, R02 | S C | L+X | 3→2 | T: build an unseen mechanism in MJCF; match analytic energy. Mis: contact parameters are physical constants. |
| S03 | ROS 2 Fundamentals | KEEP | A | MAN,MOB,SYS | 10→10 | T01, PY01 | C V | L | 2 | Move docs to Jazzy (Humble EOL May 2027). T: debug a topic mismatch via CLI. Mis: topics are reliable by default. |
| S04 | Robot Description | KEEP | F | S | 6→6 | R03~S03 | C Z | L | 2 | URDF validated against R04 FK. T: find a seeded frame error. Mis: visual frame equals joint frame. |
| S05 | ROS 2 Runtime | KEEP | A | SYS | 10→8 | S03 | C | L+X | 2 | T: measure delay under QoS and executors. Mis: callbacks run in parallel by default. |
| S06 | Hardware Integration | RESCOPE | A | SYS | 15→10 | S05, S07, R09 | C S | L+X | 2 | Absorbs S10; mock hardware first. T: mock driver timeout handling. Mis: hardware commands are always applied at send. |
| S07 | Robot Safety | RESCOPE | F | S | 6→6 | none | W S | Q+A | 2 | Move earlier; currently not a prerequisite of S06. T: hazard table and watchdog test. Mis: simulation success implies safety. |
| S08 | System Identification | KEEP | A | MOB,RLL | 12→10 | S02, M10~C07 | S C | L+X | 2 | T: fit damping, verify on unseen trajectory. Mis: low training residual identifies parameters. |
| S09 | Sim2Real | RESCOPE | A | MOB,RLL | 20→14 | S08~RL13 | V S P | A+X | 2 | Absorbs RL16; staged validation. Reviewed. T: sim-to-sim transfer before any hardware. Mis: wider randomization is always better. |
| S10 | ROS 2 Control | GROUP→S06 | A | SYS | 16→0 | - | — | — | 2 | ros2_control with mock hardware is the integration lab. |
| S11 | Advanced Simulation | DEFER | A | J | 15→0 | - | — | N | 2 | Batched and differentiable simulation on demand (MJX, Isaac Lab). |
| S12 | Advanced Robotics Software | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; real-time specifics via CPP10 and S06. |
| V01 | Digital Images | KEEP | F | S | 4→4 | PY04 | C Z | Q+L | 2 | T: detect channel and axis swap. Mis: image axes are x,y. |
| V02 | Image Processing | RESCOPE | F | S | 8→6 | V01, M03 | Z V C | Q+L | 2 | T: aliasing when downsampling. Mis: convolution order never matters with nonlinear steps. |
| V03 | Camera Models | KEEP | F | S | 8→8 | V01, M12 | V Z D C | Q+L | 3→2 | T: reproject unseen 3D points in a robot frame. Mis: focal length scales depth. |
| V04 | Camera Calibration | KEEP | A | MAN,PER | 6→6 | V03, M10~M20 | C V | L+X | 2 | T: separate fit from held-out reprojection error. Mis: low RMS means calibrated everywhere. |
| V05 | Feature Extraction | RESCOPE | A | PER | 8→6 | V02, V03 | Z C | Q+L | 2 | T: match under rotation and report recall. Mis: more features means better pose. |
| V06 | CNN | RESCOPE | F | PER,RLL | 12→12 | ML05, V02, PY06 | V Z C | Q+L | 3→2 | Absorbs V07. T: receptive field of unseen stack; small-data baseline. Mis: pooling gives invariance to all transforms. |
| V07 | Image Classification | GROUP→V06 | F | PER,RLL | 8→0 | - | — | — | 2 | Classification is the first CNN application. |
| V08 | Object Detection | RESCOPE | A | PER | 14→10 | V06, ML03 | V C | Q+L | 3→2 | Absorbs V10; use and evaluate over reimplementing. T: mAP on robot images. Mis: high mAP implies grasp usability. |
| V09 | Object Tracking | DEFER | A | J | 10→0 | - | — | N | 2 | Pull when a task needs identity over time. |
| V10 | Segmentation | GROUP→V08 | A | PER | 10→0 | - | — | — | 2 | Masks and boxes share evaluation logic. |
| V11 | Multi-View Geometry | KEEP | A | PER | 18→14 | V04, M17 | V Z D C | Q+L+X | 2 | T: triangulate with baseline sensitivity. Mis: more baseline is free of matching cost. |
| V12 | Depth Estimation | GROUP→V13 | A | PER | 10→0 | - | — | — | 2 | Stereo is the entry to 3D perception. |
| V13 | 3D Perception | RESCOPE | A | PER,MAN | 18→16 | V11, M11 | Z C | Q+L+X | 2 | ICP with outliers plus stereo depth. T: failed registration diagnosis. Mis: ICP is globally convergent. |
| V14 | Visual Representation Learning | GROUP→ML08 | A | PER,RLL | 12→0 | - | — | — | 2 | Same evaluation discipline. |
| V15 | Vision Transformers | GROUP→ML09 | A | PER,RLL | 6→0 | - | — | — | 2 | ViT is an ML09 worked case. |
| V16 | Video Understanding | DEFER | R | J | 15→0 | - | — | N | 2 | Pull for temporal perception tasks. |
| V17 | Visual Odometry & SLAM | KEEP | A | PER | 30→24 | V11, C12, M20, M15 | V C P | A+X | 2 | Stachniss, Barfoot. Reviewed. T: drift analysis on a public sequence. Mis: ATE alone evaluates odometry. |
| V18 | Vision Foundation Models | GROUP→ML08 | R | RLL | 10→0 | - | — | — | 1 | Taught as tool use with held-out evaluation; DINOv2, CLIP. |
| V19 | 3D Neural Representations | DEFER | R | J | 25→0 | - | — | N | 1 | Neural fields tracked in registry. |
| V20 | Advanced Perception | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| RL01 | RL Fundamentals | KEEP | F | S | 4→4 | PY01, M08 | V Z C | Q | 2 | T: compute return in an unseen task. Mis: reward equals goal. |
| RL02 | Markov Decision Processes | RESCOPE | F | S | 10→14 | RL01 | V Z D C | Q+L | 3→2 | Absorbs RL03. T: solve a two-state system exactly, then in code. Mis: V is the immediate reward. |
| RL03 | Value Functions | GROUP→RL02 | F | S | 8→0 | - | — | — | 3 | V, Q and Bellman are not separable in practice. |
| RL04 | Dynamic Programming | KEEP | F | RLL,MOB | 6→6 | RL02, PY02 | Z C | L | 2 | T: value iteration with residual stop. Mis: DP needs no model. |
| RL05 | Model-Free Prediction | RESCOPE | F | RLL,MOB | 8→12 | RL02, M09 | Z V C | L+X | 2 | Absorbs RL06. T: cliff walking, SARSA vs Q-learning. Mis: TD has no bias. |
| RL06 | Model-Free Control | GROUP→RL05 | F | RLL,MOB | 10→0 | - | — | — | 2 | Prediction and control taught as paired experiments. |
| RL07 | Function Approximation | RESCOPE | F | RLL,MOB | 8→6 | RL05, ML04 | Z C | Q+L | 2 | T: observe the deadly triad numerically. Mis: more function power stabilizes. |
| RL08 | Policy Gradient | KEEP | F | RLL,MOB | 12→12 | RL02, ML05 | V D C | Q+L+X | 3→2 | T: two-action gradient vs finite-difference check. Mis: log-derivative needs differentiable dynamics. |
| RL09 | Actor-Critic | KEEP | F | RLL,MOB | 10→8 | RL08, RL05 | V D C | Q+L | 3→2 | Reusable actor-critic competence; gates RL10 and RL11. T: inspect critic and actor error separately. Mis: critic error directly equals policy quality. |
| RL10 | PPO | RESCOPE | F | RLL,MOB | 16→12 | RL09, ML06~RL12 | V Z D C | Q+L+X | 3 | See blueprint, as revised. Mis: clipping guarantees monotonic improvement. |
| RL11 | Off-Policy RL | KEEP | A | RLL | 18→12 | RL07, RL09 | V C | Q+L | 2 | SAC via CleanRL. T: replay-bias diagnosis. Mis: off-policy always more sample-efficient in wall-clock. |
| RL12 | RL Experimental Design | RESCOPE | A | RLL,MOB | 8→8 | RL05, RS02, ML03 | C P | A+X | 2 | Henderson 2018; Agarwal 2021. T: IQM with CIs over seeds. Mis: best-seed reporting; 3 seeds suffice. |
| RL13 | Continuous Control | RESCOPE | A | MOB,RLL | 10→8 | RL10, C02 | S C | L+X | 2 | Absorbs RL15. T: action scaling and saturation. Mis: reward scale is cosmetic. |
| RL14 | Reward Engineering | KEEP | A | MOB,RLL | 6→6 | RL02 | S W | A+X | 2 | Remove RS02 gate. T: construct and detect a reward loophole. Mis: shaping never alters the optimum. |
| RL15 | Curriculum Learning | GROUP→RL13 | A | MOB | 8→0 | - | — | — | 2 | A training technique within continuous control. |
| RL16 | Domain Randomization | GROUP→S09 | A | MOB,RLL | 8→0 | - | — | — | 2 | Domain randomization belongs to the sim2real validation loop. |
| RL17 | Imitation Learning | RESCOPE | A | RLL | 10→10 | ML06, RL01~RL02 | V Z C | Q+L | 2 | BC first, then DAgger; MDP need is soft. T: rollout failure despite low BC loss. Mis: low validation loss implies good rollouts. |
| RL18 | Offline RL | DEFER | R | J | 15→0 | - | — | N | 2 | Levine 2020 tutorial on demand. |
| RL19 | Model-Based RL | GROUP→E08 | A | RLL | 18→0 | - | — | — | 2 | Taught with world models. |
| RL20 | Hierarchical RL | GROUP→E04 | A | MAN,RLL | 15→0 | - | — | — | 2 | Options only as one implementation of skills. |
| RL21 | Safe RL | DEFER | R | J | 12→0 | - | — | N | 2 | Constraint mindset stays in S07; methods on demand. |
| RL22 | Multi-Agent RL | DEFER | R | J | 25→0 | - | — | N | 1 | Registry only; outside core embodied track. |
| RL23 | Advanced Exploration | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| RL24 | Meta-RL | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| E01 | Sequential Decision Making | GROUP→RL02 | A | S | 8→0 | - | — | — | 2 | No unique skill; removes the false gate on E02. |
| E02 | Planning Fundamentals | RESCOPE | F | MAN,MOB | 8→8 | PY02 | Z C | Q+L | 2 | Today needs 14 ancestors incl. RL and control; only PY02 is required. T: inadmissible heuristic detection. Mis: A* is optimal with any heuristic. |
| E03 | Planning Under Uncertainty | RESCOPE | R | COG | 20→12 | E02, C07 | Z D C | Q+A | 2 | Belief states and information gathering. T: act now or sense first. Mis: replanning replaces belief. Open reasoning reviewed. |
| E04 | Robot Skills | RESCOPE | A | MAN,RLL | 10→10 | PY07~R04, S02, C01, RL13 | S C | L+X | 2 | Contracts and state machines first; reaching and learned options add their own needs. T: recover from a failed precondition. Mis: skills compose without state checks. |
| E05 | Task Planning | KEEP | A | MAN,COG | 10→6 | E02 | Z C | Q+L | 2 | T: find impossible precondition. Mis: symbolic plan implies geometric feasibility. |
| E06 | Task & Motion Planning | KEEP | A | MAN | 20→14 | E05, R18, R05 | V C P | A+X | 2 | Garrett 2021. Reviewed. T: reject and replan an unreachable grasp. Mis: plan-then-check is complete. |
| E07 | Imitation-Based Robot Policies | RESCOPE | A | RLL | 15→14 | RL17~E16, ML09, ML11 | V C P | L+A+X | 2 | MLP BC baseline, then ACT if budget allows. T: changed object or camera. Mis: low training loss implies success. |
| E08 | World Models | RESCOPE | R | RLL | 20→12 | RL02, ML06~RL09 | V C P | A+X | 2 | Absorbs RL19 as a group. Shooting or CEM first; Dreamer-like extension needs RL09. T: one-step vs multi-step error and control usefulness. Mis: lower pixel error gives better control. |
| E09 | Object-Centric Representations | RESCOPE | R | COG | 18→10 | ML08~V13 | P C | A | 2→1 | Reproduce a narrow claim; occlusion identity test. Reviewed only. |
| E10 | Vision-Language Models | RESCOPE | A | RLL,COG | 14→8 | ML09, ML08 | V C | A+X | 2 | Use and evaluate. T: spatial-relation failure test. Mis: grounding follows from caption ability. |
| E11 | Diffusion/Flow Action Policies | RESCOPE | A | RLL | 18→10 | E07, ML11 | V Z D C | L+A | 1→2 | Elective globally, core for RLL; after an MLP/ACT baseline. Mis: MSE handles multimodal targets. |
| E12 | Vision-Language-Action Models | RESCOPE | R | RLL,COG | 20→10 | E07, E10 | P C | A | 1→2 | Run open models (Octo, pi0) on held-out tasks. Reviewed only. Mis: demo video proves generalization. |
| E13 | Long-Horizon Robot Learning | REMAP→CAP | R | J | 25→0 | - | — | N | 1 | Assessed through capstones with stage-wise success metrics. |
| E14 | Embodied Reasoning | RESCOPE | R | COG | 25→12 | E05, E10 | P C | A | 1 | Does a plan stay valid after a scene change? Reviewed only; a plausible explanation is not evidence. |
| E15 | Advanced Embodied Intelligence | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all. |
| E16 | Robot Data Collection | NEW | A | RLL | 0→10 | S02, RL17 | C S | L+A | new:2 | Teleop, demonstrations, dataset QA; LeRobot, UMI, ALOHA. T: find a bad-demo cluster. Mis: more demos always help. |
| E17 | HRI & Shared Autonomy | NEW | R | COG | 0→10 | S07, RS02 | V P W | A | new:1 | HRI and shared autonomy. Human-subject work needs its own ethics review. Reviewed only. |
| RS01 | Scientific Reasoning | KEEP | F | S | 4→4 | none | W | Q+A | 2 | T: write a falsifier for a claim. Mis: confirmation as proof. |
| RS02 | Experimental Design | KEEP | F | S | 8→8 | RS01, M09 | W C | Q+A+X | 3→2 | Absorbs RS05. T: factorial ablation design. Mis: changing two factors at once is efficient. |
| RS03 | Statistical Inference | GROUP→M09 | F | S | 10→0 | - | — | — | 2 | Inference is taught once in M09 and applied in RS02, RL12. |
| RS04 | Experimental Reproducibility | RESCOPE | F | S | 10→14 | RS02, T02, PY07 | C | L+X | 3→2 | Absorbs PY08, T05, RS09. Fresh-clone rerun is machine-checkable. Mis: seed fixes all nondeterminism. |
| RS05 | Error Analysis | GROUP→RS02 | F | S | 6→0 | - | — | — | 2 | Taught in every evaluation task. |
| RS06 | Paper Reading | KEEP | F | S | 8→8 | RS01 | P W | A | 2 | Claim-evidence-assumption table, reviewed. Mis: venue equals validity. |
| RS07 | Scientific Writing | KEEP | R | RES | 15→10 | RS06, RS02 | W | A | 2 | Human review needed for verified status. |
| RS08 | Literature Review | DEFER | R | RES | 10→6 | RS06 | P | A | 2 | Pull at the start of a research project. |
| RS09 | Research Software | GROUP→RS04 | F | S | 10→0 | - | — | — | 2 | Traceability is part of reproducibility. |
| RS10 | Advanced Research | ARCHIVE | R | X | 60→0 | - | — | N | 1→– | Research output cannot be a curriculum node; L4 is evaluated per project. |


---

## Round 4: final position and consolidated deliverables

Codex Round 3 answered my Round 2. My Round 3 (item audit, 3.4 rule, review-load model) had not been answered when this was written. Points of Round 3 that Codex has not yet seen remain open. This round supersedes my earlier rounds wherever they differ. Nothing has been implemented, and implementation needs human approval.

### 4.1 Responses to Codex Round 3

| Codex position | Decision | Reasoning |
|---|---|---|
| Seven candidates: M17, R16, R17, R18, R19, R20, E16. Defer separate IDs for PoE, information theory, signals, nonlinear least squares, HRI. | **ACCEPT** | My own 3.4 rule supports this once it is applied properly. Its test (c) only matters for IDs with a published contract. M15, V04 and E14 have no contract, so their scope can grow without misrepresenting any PASS. M04 has a contract, so M17 stays separate. R21, M18, M20 and E17 are **withdrawn as IDs**, with their content hosted in M15, ML11/RL10, V04 and E14. |
| `R18 ← E02, R03`, FK for arm planning only | **ACCEPT** | Already in the matrix |
| R19 scoped: tracking and limits first; contact later; no hardware authorization | **ACCEPT** | Now in its row |
| R20: particle route need not master every Kalman implementation | **MODIFY** | The matrix keeps `R20 ← C07, R16, R02` for the default route. A particle-only variant needs an M08/M09 route instead. This is the alternative-route case the AND-only engine can't express, so the edge remains conservative and flagged. |
| E16 separable: existing datasets need no teleoperation | **ACCEPT** | |
| 80–140 h must not become a waiting period | **ACCEPT** | The core is a set that goal paths share, *not* a block to finish first. It runs alongside early useful work. |
| Default path: units as needed, vectors alongside Python, matrix/frame readiness, small FK exercise, testing and protocol embedded at the first artifact | **ACCEPT** | Better than my framing. It resolves D5. |
| Hard edges may also have procedural or evidence-validity reasons; tool edges are hard only for the named variant | **ACCEPT** | A held-out split before a performance claim is a good example. |
| Crossover M06 vs M17 is invalid | **ACCEPT; my design was flawed** | The topics aren't exchangeable, learning doesn't wash out, and content and test changes were confounded. Adopted: matched parallel task families within one scoped skill, counterbalanced, with a fresh predeclared delayed task. Report as cases only. |
| Sequential testing needs a stopping rule and validated item model | **ACCEPT** | Withdrawn as a suggestion for now. |
| Single-user L3/L4: "needs external reviewer" | **ACCEPT** | Answers my 2.9 Q4 |
| E11 is not universal for every robot-learning goal | **ACCEPT** | RLL is split: default (evaluated low-dimensional policy) and RLLV (visuomotor, with E11, E16, V06, E12, E08). |
| First 100 hours: manifest and M02/PY01 first | **MODIFY** | See 4.2 |
| Pilots and evidence manifest before item engines, expiry or sixteen visualizations | **ACCEPT, except the defect fixes** | See 4.2 |

### 4.2 First 100 authoring hours: merged proposal

Your plan is better sequenced than mine. It starts with a manifest and avoids building a generic engine before anything needs it. My remaining objection: it leaves known defects in place for up to 100 hours, even though they can fail a correct learner or give an impossible instruction.

| Hours | Deliverable | Source |
|---|---|---|
| 0–8 | Corrections that touch no v1 key: precision hint on numeric input; recommendation text for topics with no lab; ROS docs version; M07 and M08 source references; demo-model labels | Mine; Codex's M10/C01 finding |
| 8–14 | Objective and evidence manifest for the pilot topics; pinned versions | Codex |
| 14–36 | M02 pilot v2: dot, norm, projection, with a task materially different from the page's code | Codex |
| 36–54 | PY01 pilot v2, with test design scored separately | Codex |
| 54–68 | M08 v2: Bayes computation, fixed tolerance and fraction policy; M09 covariance bridge | Both |
| 68–78 | M01 trig, algebra and unit bridge | Codex |
| 78–90 | Planar then spatial FK milestone (M12, R03, R04) | Both |
| 90–100 | Editorial and accessibility checks, mutation checks, pilot preparation | Codex |

Only build `expression` or `matrix` items if a pilot needs them. These are effort allocations, not measured productivity.

**The next queue, not promised here:** M05 integration, M17, R06 verification, then R17/R18/R19 on a MAN goal. A different goal changes this queue.

### 4.3 Deliverable index

| # | Deliverable | Location |
|---|---|---|
| 1 | Review matrix (169 + 7 candidates) | 4.10 |
| 2 | Blueprints | 1.9 as corrected by 3.7 and 4.5 |
| 3 | Additions, removals, merges, prerequisites | 4.4 |
| 4 | Video, visualization, references | 1.10 and 4.7 |
| 5 | PASS criteria and verification | 4.6 |
| 6 | Effort and time savings | 4.8 |
| 7 | Responses to Codex | 2.2, 3.1–3.2, 4.1 |
| 8 | Disagreements and uncertainties | 4.9 |

### 4.4 Final curriculum recommendations

**Principles**
1. Keep all 169 IDs, contracts and evidence. A grouping affects navigation only, and no PASS inherits broader scope.
2. Publish a common map, a default path with opt-out, and goal paths ending in capstones.
3. A hard edge needs a concrete reason: `math`, `safety`, `tool` (for the named variant), or `procedural/evidence`. Context and textbook order are soft.
4. Keep readiness separate from mastery, starting with a few high-impact checks.

**Additions (candidates; final IDs are the maintainer's choice)**

| Working ID | Unit | Path | Confidence |
|---|---|---|---|
| M17 | Spectral Methods & Stable Least Squares | Catalog; R05, V11, C02 use it | High |
| R17 | Trajectory Generation | Catalog; MAN | High |
| R18 | Motion Planning | MAN, MOB | High |
| R19 | Manipulator Control | MAN | High |
| R20 | Mobile Robots & Localization | MOB | Medium |
| R16 | Sensors & Measurement | Catalog | Medium-low |
| E16 | Robot Data & Demonstration Quality | RLLV | Medium-low |

**Scoped into existing IDs:** PoE and twists in M15; KL in ML11 and RL10; sampling and aliasing in C09; nonlinear least squares in V04; HRI and privacy in S07 and E14; trigonometry in M01; integration in M05; covariance in M09.

**Archived (ID kept, on no path):** M16, PY10, CPP12, ML12, T08, R15, C15, S12, V20, E15, RS10. C15, V20 and S12's latency task stay available as electives or capstone content.

**Deferred to first need:** M14, PY09, CPP09, T06, R10, C10, S11, V09, V16, V19, RL18, RL21, RL22, RL23, RL24, RS08. E13 becomes capstone content.

**Study groups (32):** listed in the matrix as `GROUP→`. Separate scoring is mandatory.

**Key prerequisite changes** (full list in the matrix):

| Change | Reason type |
|---|---|
| E02 ← PY02 | Removes a false gate |
| R04 ← R03; R03 ← M12; V03 ← V01, M12 | Math; camera doesn't wait for mechanisms |
| R05 ← R04 (R06 and M17 for the numerical scope) | Math, scoped |
| R07 ← R04, M06, M07, R01 (R06 soft) | Math |
| C02 gains M06; C03 ← C01 (C02 soft); C05 ← C02 (M10 soft) | Math |
| C13 ← C05, M10; C11 ← C13, M13 | Math |
| S07 no hard prerequisite; S06 ← S05, S07, R09 | Safety |
| C08 ← C07, R03 (R16 soft) | Math |
| RL09 ← RL08, RL05; RL10 ← RL09, ML06; RL11 ← RL07, RL09 | Math |
| E08 ← RL02, ML06 | Removes the PPO gate |
| E04 ← PY07; R04, S02, C01 and RL13 soft | Scoped |
| E07 ← RL17 (E16, ML09, ML11 soft) | Removes false gate |
| R18 ← E02, R03 (R04 soft) | Math |
| ML06, V06 ← PY06 | Tool, as tensor and autodiff capability |

**Canonical graph:** 119 live units, 193 hard edges, 32 soft edges, depth 11, no cycles, recipe in 3.1 Q6. Ancestor changes: E02 14→2, R04 8→5, E06 23→12, E07 20→17, S09 17→13.

### 4.5 Blueprint corrections (in addition to 3.7)

- **R19, R06:** near-π and twist content comes from M15, not R21.
- **M17:** do not require a from-scratch SVD algorithm; `lstsq_svd` calls a library SVD, and the learner handles truncation and conditioning.
- **E07:** see row; E11 is separate.
- **All blueprints need expert review.** Three errors were found by peer review in Round 2, so others likely remain. They are specifications to refine and are not ready to publish.

### 4.6 PASS criteria and verification

**Levels.** C/M/I/T, L0–L4 and A0–A3 are preserved.

| Level | Evidence | Verified by | Single-user state |
|---|---|---|---|
| Ready (not a level) | Check for the next scoped activity | Machine, A0 declared | Available |
| L1 | C and applicable M gates on a form not shown before | Machine, A0 declared | Available |
| L2 | L1 plus I from undisclosed-before-attempt checks across the scoped objectives | Machine, A0 declared | Available where a contract exists |
| L3 | L2 plus delayed fresh retention plus unfamiliar transfer | Human review for open work | "Needs external reviewer" |
| L4 | Reproducible critique or extension | Qualified human only | "Needs external reviewer" |

**Rules**

| Rule | Starting value | Status |
|---|---|---|
| Applicable dimensions | Each contract declares them; L2 gates only on those | Requires engine approval |
| Coverage | At least 2 items per critical objective; length follows the profile | Pilot |
| Threshold | ≥80% only where a contract declares it. Per-dimension gates need enough items, since 4 items again means 100%. | Pilot; not a proven standard |
| Choice items | Randomized order; no gate resting on one binary item; three options acceptable | Rodriguez 2005 for options; rest is a design rule |
| Numeric items | State conventions in the prompt; declare accepted formats and a tolerance appropriate to the input | Direct fix |
| Retakes | Corrective practice any time; independent attempt on a new form, recording exposure | Delay is a pilot variable |
| Worked examples | Kept; assessed task must be materially different | Agreed |
| AI use | Any AI help means A1 or above | Existing policy |
| Transfer | Must change representation, assumption, context or method; new numbers are retention only | Agreed |
| Failed check | History stays. Recommender is informed. No time-based expiry until evidence supports one. | D7, partly open |

**Per-profile PASS (Codex's profile names; content from both)**

| Profile | Required evidence | Not certified automatically |
|---|---|---|
| MAT | Compute or derive an unseen instance, independent check, optional numeric code | Unrestricted proof ability |
| CODE | Contract, blank-file implementation, boundary, invalid-input, property and mutation checks | Design judgment. M usually not applicable. |
| DYN | State, frame, units, model limits; simulated with independent oracle and sensitivity checks | Hardware readiness, ever |
| DATA | Leakage boundaries, baseline, held-out result, uncertainty | Claims beyond the tested distribution |
| PLAN | Trace and implement; validate against exhaustive small cases or a feasibility oracle | Open modelling judgment |
| RESEARCH | Falsifiable claim, narrow reproduction, limitations | Everything open: human review required |

**Integrity statement for the UI.** Self-declared A0, inspectable local checks and a key held on the learner's machine provide attestation and not proof. "Verified" means "passed these stated checks, with independence attested by the learner", unless a person reviewed it.

### 4.7 Video, visualization and reference recommendations

**Reference table:** 1.10. Keep two separate fields: *availability verified* and *instructional match reviewed*. My labels establish the first only. Captions, durations, regional access and Vietnamese subtitles are unverified.

**Mapping changes to the current registry**

| Mapping | Decision |
|---|---|
| M08 and M07 `source_refs` → 18.01 | Replace with 6.041SC or 18.05; 18.03SC for M07 |
| M06, M10 → `3b-gradient` | Keep as intuition with a bridge; add 18.02SC for Jacobians |
| V01 → CS231n classification | Secondary; a NumPy image task comes first |
| R04 → `mr-fk`; R06 → `mr-jacobian` | Extension, labeled with conventions |
| M08 (no video) | Add from 6.041SC or 18.05 |
| ROS links | Replace Humble (EOL May 2027); Jazzy for now |
| `Effective C++` | Note that it predates C++11 |

**Visualizations.** Five pilots: manipulability ellipsoid and 3D frames (extend existing models), PID saturation (extend), phase portrait, Kalman ellipses (only if pilot data supports building them). Each requires a prediction first and awards nothing. Use external models elsewhere. Label model changes between lesson and demo.

**Workflow.** Adapted by profile (1.6 sequences stand, without the time-split column or prose cap). Video is an optional entry and stays a default offering for MAT and DYN, in keeping with the owner's preference. No claim that matching "visual learners" improves outcomes.

### 4.8 Effort and time

All hours are **planning sizes and not measurements**. No learner data supports any saving.

| Goal | Units | Size + capstone |
|---|---|---|
| SYS | 28 | about 300 h |
| COG (research tier, thin) | 34 | about 400 h |
| PER | 37 | about 450 h |
| RLL default | 40 | about 460 h |
| RLLV visuomotor | 43 | about 480 h |
| MAN | 46 | about 560 h |
| MOB | 50 | about 620 h |

- Shared by all seven goals: M01, M02, M03, PY01, PY04 (about 48 h). Shared by the six non-SYS goals, adding M05, M06, M07, M10: about 98 h. Cross-cutting practice adds about 31 h, embedded in early work.
- These closures are minimums for one capstone, and depend on my leaf lists and edges. Uncertainty is at least ±40%.
- The current `estimated_minutes` (about 28 h for 31 topics) should not be used for planning.
- Possible savings come from placement checks, not repeating known material, removing false gates, and goal scoping. Their size is unknown, and new assessments add time.
- **Validation:** matched parallel task families, active minutes, assistance, and delayed unfamiliar-task results (4.1). Case evidence only.
- **Review load:** see the 3.6 model; use a daily budget. No savings figure is claimed.

### 4.9 Remaining disagreements and uncertainties

**Unresolved or not yet answered by Codex**

| Issue | My position | Status |
|---|---|---|
| Item audit (3.3), including the M08 precision defect | Fix first; verified by running the logic | Awaiting Codex |
| Failed readiness check changes recommendations (D7) | Yes, without expiry clocks | Partly open |
| R20 hard edge on C07 | Conservative, pending alternative routes | Disagreement on a default |
| M17 as new ID vs versioned M04 scope | Either is honest; prefer M17 until scope manifests exist | Practical choice |
| 3.4 rule | Now refined: test (c) applies only where a contract exists | Awaiting Codex |
| R16, E16 as units | Low confidence on both | Open |
| Fix-first hours (4.2) vs manifest-first | Fix first | Awaiting Codex |

**Uncertainties neither of us can resolve from here**
- Whether any of these changes improves delayed, independent performance.
- Real time per topic, for any learner.
- Optimal item counts, thresholds and review schedule for robotics and coding.
- Whether a human reviewer will ever be available to a single-user install.
- Whether PoE or transform-chain teaching works better.
- Which frontier topics stay relevant; E11 and E12 should be re-examined every 6–12 months.
- How much simulation-only capstones miss compared with real hardware.
- Authoring capacity: the whole plan may exceed what one maintainer can sustain, which is why the 100-hour plan stops at pilots.

**Decisions for the owner**
1. Which goal comes first? This determines the queue after pilots.
2. Approve engine changes: applicable dimensions, readiness display, review budget.
3. Final candidate IDs, and whether R16 and E16 stay.
4. Is an external reviewer available? If not, L3 and L4 stay in the "needs external reviewer" state.

### 4.10 Final matrix (replaces 1.8 and 3.11)

Legend as in 1.8 and 3.11. S: optional comprehensive catalog. RLLV: visuomotor variant of robot learning. COG: research-tier cognitive path, reviewed only. GROUP: shared study unit, separate IDs and scores. ARCHIVE: ID kept, on no path. L: undisclosed-before-attempt, versioned checks. 169 baseline IDs + 7 candidates = 176 rows. Hours are planning sizes.

| ID | Topic | Action | Tier | Path | h now→new | Hard prereq ~soft | Mix | Gate | Tgt | Focus: transfer task, misconception, note |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | Mathematical Basics | RESCOPE | F | S | 6→8 | none | Z W C | Q | 2 | Readiness probe first; lesson only on failure. T: derive a calibration inverse with units. Mis: function vs formula; unit-free reasoning. |
| M02 | Vectors | KEEP | F | S | 8→8 | M01 | Z V D C | Q+L | 3→2 | L2 lab must test dot, norm and projection, not dot only. T: decompose a force along a sloped surface. Mis: dot product as a vector; projection onto zero vector. |
| M03 | Matrices | KEEP | F | S | 10→10 | M02 | V Z D C | Q+L | 3→2 | T: read a matrix from images of basis vectors, then compose in a stated order. Mis: AB=BA; shape agreement implies meaning. |
| M04 | Linear Algebra | RESCOPE | F | S | 20→14 | M03 | V Z D C | Q+L | 2 | Stop at rank, nullspace, solving; spectral content moves to M17. T: which parameters can two dependent sensors recover? Mis: more equations always determine x. |
| M05 | Calculus I | RESCOPE | F | S | 20→14 | M01 | V Z D C | Q | 2 | Differentiation and chain rule first; integration just in time. T: linearize a sensor curve and bound its error. Mis: derivative as slope only, never as sensitivity. |
| M06 | Multivariable Calculus | KEEP | F | S | 20→14 | M03, M05 | V Z D C | Q+L | 3→2 | Remap video: current 3b-gradient does not teach Jacobians. T: verify a hand Jacobian by directional differences. Mis: Jacobian row/column order. |
| M07 | Differential Equations | RESCOPE | F | S | 16→12 | M05~M03 | V Z S C | Q+L | 3→2 | Phase portraits and numerical integration over closed-form tricks. T: pick dt for stiff decay. Mis: Euler stability equals accuracy. |
| M08 | Probability | KEEP | F | S | 20→14 | M01 | Z V W C | Q | 2 | No video today; add MIT 6.041SC or 18.05. T: posterior after two correlated alarms. Mis: confusing P(A given B) with P(B given A); ignoring base rate. |
| M09 | Statistical Foundations | RESCOPE | F | S | 16→14 | M08 | Z W C | Q+L | 2 | Absorbs RS03 basics (CI, effect size). T: seeds needed to detect a stated effect. Mis: CI as probability the parameter is inside. |
| M10 | Optimization | RESCOPE | F | S | 14→10 | M06 | Z V D C | Q+L | 2 | T: diagnose divergence from a loss curve. Mis: lower training loss always better; learning rate as the only knob. |
| M11 | Numerical Computing | RESCOPE | F | S | 14→12 | M03, M05, PY04 | C Z W | Q+L | 2 | Absorbs PY05 (SciPy, plotting). T: rank a solver by residual versus parameter error. Mis: small residual means accurate solution. |
| M12 | Rigid-Body Geometry | KEEP | F | S | 8→5 | M03 | V Z D C | Q+L | 2 | Elementary frames and homogeneous transforms; gates V03. Own evidence identity. T: camera point to base with a new mount. Mis: translating a direction. |
| M13 | Advanced Optimization | RESCOPE | A | MAN,MOB | 25→18 | M10~M17 | V D C | Q+L+X | 2 | Convex, QP, Lagrange, KKT; Boyd & Vandenberghe selectively. T: actuator allocation QP. Mis: active constraint means infeasible. |
| M14 | Advanced Probability | DEFER | R | J | 25→0 | - | — | N | 2→1 | Conditional independence to M08; random processes to C07. Pull in for research only. |
| M15 | Lie Theory | RESCOPE | A | PER,MOB,MAN | 25→12 | R03, M06 | D C P | Q+L | 2 | Hosts twists, PoE and exp/log including near-π; no v1 contract exists, so no PASS is altered. T: perturbation Jacobian check. Mis: adding rotation vectors composes rotations; twist equals endpoint velocity. |
| M16 | Advanced Mathematics | ARCHIVE | R | X | 60→0 | - | — | N | 1→– | Catch-all without assessable objective; registry entry only. |
| M17 | Spectral Methods & Least Squares | NEW | F | S | 0→16 | M04 | V Z D C | Q+L+X | new:2 | Eigen, SVD, pseudoinverse, linear least squares. See blueprint. Mis: eigenvalues and singular values interchangeable. |
| PY01 | Python Fundamentals | RESCOPE | F | S | 15→12 | none | C W | Q+L | 3→2 | Absorbs PY03. Lab must exceed mean(). T: unfamiliar parser from a spec. Mis: aliasing versus copying; print versus return. |
| PY02 | Data Structures | RESCOPE | F | S | 15→10 | PY01 | C Z | Q+L | 2 | Add complexity, graphs, BFS, heaps; feeds E02. T: pick a structure for sensor queues. Mis: list is fine for every queue. |
| PY03 | Python Semantics | GROUP→PY01 | F | S | 6→0 | - | — | — | 2 | PY01 q4 already tests aliasing; keep advanced aspects in debugging exercises. |
| PY04 | NumPy | KEEP | F | S | 10→10 | PY01~M03 | C Z | Q+L | 3→2 | T: vectorize a forward-kinematics batch. Mis: broadcasting silently aligns intended axes. |
| PY05 | Scientific Python | GROUP→M11 | A | S | 10→0 | - | — | — | 2 | SciPy is learned through numerical tasks, not separately. |
| PY06 | PyTorch Basics | KEEP | F | S | 10→10 | PY04~ML04 | C V | Q+L | 2 | Currently has one dependent (S11); must gate ML06, V06. T: match autograd to a hand gradient. Mis: gradients reset automatically. |
| PY07 | Testing & Debugging | RESCOPE | F | S | 10→10 | PY01 | C W | L | 2 | Absorbs T04; mutation-kill score replaces most quiz items. T: tests that reject seeded bugs. Mis: passing tests prove correctness. |
| PY08 | Research Programming | GROUP→RS04 | A | S | 10→0 | - | — | — | 2 | Configuration, logging and seeds fold into RS04. |
| PY09 | Performance | DEFER | A | SYS | 10→6 | PY04, PY07 | C | L | 2 | Absorbs T07. Pull when a pipeline misses a budget. T: profile, then fix the measured bottleneck. Mis: optimizing without measuring. |
| PY10 | Advanced Python | ARCHIVE | R | X | 15→0 | - | — | N | 1→– | No robotics dependency; learn from documentation when required. |
| CPP01 | C++ Fundamentals | KEEP | A | SYS,MAN | 15→12 | T01 | C W | Q+L | 2 | Track-level, not spine. T: find truncation from compiler warnings. Mis: integer division; uninitialized values. |
| CPP02 | Memory Model | KEEP | A | SYS,MAN | 12→12 | CPP01 | C V Z | Q+L | 3→2 | T: explain and fix a dangling reference after vector growth. Mis: reference keeps object alive. |
| CPP03 | Resource Management | RESCOPE | A | SYS,MAN | 12→16 | CPP02 | C W | L+X | 3→2 | Absorbs CPP04. T: design a bounded joint-state class. Mis: move leaves source unusable; manual new/delete is simpler. |
| CPP04 | Classes & OOP | GROUP→CPP03 | A | SYS,MAN | 10→0 | - | — | — | 2 | Invariants and RAII are one skill in practice. |
| CPP05 | STL & Algorithms | RESCOPE | A | SYS,MAN | 15→12 | CPP01 | C W | L | 2 | Absorbs useful CPP06 idioms. T: select container for timestamp lookup and measure it. Mis: map always beats sorted vector. |
| CPP06 | Modern C++ | GROUP→CPP05 | A | SYS | 20→0 | - | — | — | 2 | Templates and constexpr only when a library reading task requires them. |
| CPP07 | Build Systems | RESCOPE | A | SYS,MAN | 10→14 | CPP02, T01 | C W | L | 2 | Absorbs CPP08: CMake, GoogleTest, ASan/UBSan. T: reduce a failing program and add a regression test. Mis: no crash means no UB. |
| CPP08 | Debugging & Testing | GROUP→CPP07 | A | SYS,MAN | 12→0 | - | — | — | 3→2 | Tooling is verified together with the build. |
| CPP09 | Complexity & Performance | DEFER | A | J | 15→0 | - | — | N | 2 | Pull after a measured real-time miss. |
| CPP10 | Concurrency | KEEP | A | SYS | 20→12 | CPP03, CPP07 | C Z | L+X | 2 | TSan-clean producer/consumer. T: fix a real data race. Mis: volatile synchronizes. |
| CPP11 | Numerical C++ | KEEP | A | SYS,MAN | 12→8 | CPP05, M03 | C | L | 2 | T: Eigen least squares with Python oracle. Mis: aliasing in Eigen expressions; inverse rather than solve. |
| CPP12 | Advanced C++ | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; ABI work is out of scope for this mission. |
| ML01 | ML Problem Formulation | KEEP | F | S | 8→8 | PY04, M08 | W C | Q+A | 2 | T: find leakage in a supplied pipeline. Mis: random split is always valid for time series. |
| ML02 | Classical ML | KEEP | F | S | 14→12 | ML01, M06 | V Z D C | Q+L | 2 | T: regularization choice on small sensor data. Mis: regularization only reduces test error. |
| ML03 | Generalization | RESCOPE | F | S | 10→12 | ML01, M09 | Z C | Q+L | 2 | Absorbs ML07. T: choose a metric from decision costs. Mis: test set can be reused during tuning; accuracy under imbalance. |
| ML04 | Neural Networks | KEEP | F | S | 8→8 | ML02 | V Z C | Q+L | 2 | T: count parameters and shapes of an unseen net. Mis: depth alone adds nonlinearity. |
| ML05 | Backpropagation | KEEP | F | S | 10→10 | ML04, M06~PY06 | V Z D C | Q+L+X | 2→3 | See blueprint. Mis: backprop is the learning rule. |
| ML06 | Deep Learning Training | KEEP | F | S | 14→14 | ML05, PY06, M10 | V C Z | Q+L | 2 | PY06 edge is missing today. T: diagnose a broken training run from curves. Mis: bigger model first. |
| ML07 | Model Evaluation | GROUP→ML03 | F | S | 10→0 | - | — | — | 2 | Evaluation and generalization share one held-out discipline. |
| ML08 | Representation Learning | RESCOPE | A | RLL,PER | 12→10 | ML06 | V Z C | Q+A | 2 | Absorbs ML10, V14, V18. T: frozen DINOv2 features on a small robot set. Mis: pretraining guarantees transfer under shift. |
| ML09 | Transformers | KEEP | A | RLL,PER | 12→10 | ML06 | V Z C | Q+L | 2 | Absorbs V15. T: compute attention and patch counts by hand. Mis: attention weights explain decisions. |
| ML10 | Self-Supervised Learning | GROUP→ML08 | A | RLL | 12→0 | - | — | — | 2 | Taught as one route to representations. |
| ML11 | Generative Models | RESCOPE | A | RLL | 25→14 | ML06 | V Z D C | Q+L | 2 | Short entropy/KL sublesson, VAE sketch, then DDPM/flow for action policies. T: multimodal 1-D action fit. Mis: MSE handles multimodal targets; KL is a distance. |
| ML12 | Advanced ML | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; paper-specific reproduction lives in RS06. |
| T01 | Linux | RESCOPE | F | S | 10→10 | none | C | L | 2 | Absorbs T03; Missing Semester. T: repair a broken environment using only the shell. Mis: sudo as a fix. |
| T02 | Git | KEEP | F | S | 6→6 | none | C | L | 2 | Study from week 1 in parallel. T: recover from a bad merge. Mis: commit equals backup of environment. |
| T03 | Development Tools | GROUP→T01 | F | S | 6→0 | - | — | — | 2 | Debugger use is reinforced in PY07 and CPP07. |
| T04 | Software Testing | GROUP→PY07 | F | S | 8→0 | - | — | — | 2 | Same video as PY07; keep T04.v1 evidence as alias. |
| T05 | Reproducible Environments | GROUP→RS04 | F | S | 6→0 | - | — | — | 2 | Environments are the first half of reproducibility. |
| T06 | Docker | DEFER | A | SYS | 8→5 | T01, RS04 | C | L | 2 | Pull when deployment needs it. T: rebuild a ROS image. Mis: container state persists. |
| T07 | Systems Performance | GROUP→PY09 | A | SYS | 10→0 | - | — | — | 2 | Same measurement discipline. |
| T08 | Advanced Infrastructure | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Infrastructure catch-all. |
| R01 | Mechanics Foundations | RESCOPE | F | S | 14→10 | M02 | V S D | Q+L | 2 | T: predict cart acceleration in MuJoCo before running. Mis: force causes velocity rather than acceleration. |
| R02 | Robot Mechanisms | KEEP | F | S | 6→6 | M01 | V Z W | Q | 2 | Grübler formula, task vs joint space. T: count DOF of an unseen mechanism. Mis: DOF equals number of motors. |
| R03 | Rigid-Body Transformations | RESCOPE | F | S | 10→8 | M12 | V Z D C | Q+L+X | 2 | Spatial composition and rotation representations; twists and near-π log are scoped in M15. See blueprint, as revised. Mis: any orthogonal matrix is a rotation; rotation vectors add. |
| R04 | Forward Kinematics | RESCOPE | F | S | 10→10 | R03 | V Z D C | Q+L+X | 3→2 | Spatial PoE and URDF chain, not 2R only. See blueprint. |
| R05 | Inverse Kinematics | RESCOPE | F | S | 10→10 | R04~R06, M17 | V Z D C | Q+L+X | 2 | Follows the Jacobian. T: damped LS at a singular target with joint limits. Mis: IK has one answer; solver error means unreachable. |
| R06 | Robot Jacobian | RESCOPE | F | S | 12→12 | R04, M06~M17 | V Z D C | Q+L+X | 3 | Teach geometric Jacobian and statics. See blueprint. |
| R07 | Rigid-Body Dynamics | KEEP | F | S | 24→20 | R04, M06, M07, R01~R06 | V S D C | Q+L+X | 3→2 | Absorbs RNEA overview from R12. See blueprint. |
| R08 | Contact Mechanics | KEEP | A | MAN,MOB | 14→10 | R07 | V Z S | Q+L | 2 | T: friction-cone limit tested in MuJoCo. Mis: friction force always equals μN. |
| R09 | Actuators & Transmission | RESCOPE | F | S | 8→6 | R01 | V W | Q | 2 | T: choose a gear ratio under speed and torque limits. Mis: higher ratio dominates. |
| R10 | Mechanical Design Verification | DEFER | A | J | 15→0 | - | — | N | 2→1 | Hardware-builder path only. |
| R11 | Floating-Base Dynamics | KEEP | A | MOB | 18→14 | R07, R08 | V D S | Q+L | 2 | T: why joint torques cannot command base acceleration directly. Mis: base treated as actuated. |
| R12 | Advanced Dynamics | GROUP→R07 | A | J | 20→0 | - | — | — | 2 | RNEA concept in R07; Featherstone depth pulled on demand. |
| R13 | Advanced Locomotion | KEEP | A | MOB | 30→20 | R11, C05 | V S P | A+X | 2 | T: tune then explain a gait failure in simulation. Mis: a stable-looking steady gait implies robustness to disturbance. |
| R14 | Dexterous Manipulation | RESCOPE | A | MAN | 25→16 | R06, R08 | V S D C | Q+L+X | 2 | MR Ch. 12 and Manipulation. T: force-closure of unseen grasp. Mis: more contacts is always stronger. |
| R15 | Advanced Mechanics | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| R16 | Sensors & Measurement | NEW | F | S | 0→8 | M09~C09 | V C W | Q+L | new:2 | Encoders, IMU, F/T, depth, LiDAR; noise, bias, timestamps. T: Allan-style bias estimate on a log. Mis: datasheet noise equals in-system noise. |
| R17 | Trajectory Generation | NEW | F | S | 0→6 | R04~M05 | V Z D C | Q+L | new:2 | MR Ch. 9 time scaling. T: fastest profile under limits. Mis: path and trajectory are the same. |
| R18 | Motion Planning | NEW | A | MAN,MOB | 0→14 | E02, R03~R04 | V Z C | Q+L+X | new:2 | C-space, collision, PRM/RRT (MR Ch. 10, LaValle). T: narrow passage failure and fix. Mis: RRT paths are near-optimal. |
| R19 | Manipulator Control | NEW | A | MAN | 0→14 | R07, R06, M15, C03 | V S D C | Q+L+X | new:2 | Tracking and effort limits first; dynamics and impedance extensions state their assumptions. T: contact-stable impedance tuning in simulation. Mis: stiffer is always more accurate and safe. No hardware authorization. |
| R20 | Mobile Robots & Localization | NEW | A | MOB | 0→16 | C07, R16, R02 | V Z C | Q+L+X | new:2 | MR Ch. 13 plus particle filter localization. T: kidnapped robot recovery. Mis: odometry drift is zero-mean. |
| C01 | Control Fundamentals | KEEP | F | S | 8→6 | M05~R01 | Z V D | Q | 2 | T: disturbance offset under P control. Mis: higher gain always better. |
| C02 | Dynamic Systems | RESCOPE | F | S | 16→16 | C01, M07, M04, M06 | V Z D C | Q+L | 3→2 | Absorbs C04. Brunton Control Bootcamp. T: linearize unseen pendulum and classify stability. Mis: local stability is global. |
| C03 | PID Control | RESCOPE | F | S | 10→10 | C01~C09, C02 | Z S C | Q+L | 3→2 | Tuning from C01 and simulation; stability analysis needs C02. T: anti-windup under saturation. Mis: derivative term has no noise cost. |
| C04 | Linear Systems | GROUP→C02 | F | S | 14→0 | - | — | — | 2 | Controllability and poles sit naturally beside state space. |
| C05 | LQR | KEEP | F | S | 12→10 | C02~M10 | V Z D S | Q+L+X | 3 | See blueprint. Mis: LQR is robust to any model error. |
| C06 | State Estimation | GROUP→C07 | F | S | 8→0 | - | — | — | 2 | Prediction and correction taught once, through the Bayes filter. |
| C07 | Kalman Filtering | RESCOPE | F | S | 16→16 | C02, M09 | V Z D C | Q+L+X | 3 | See blueprint. Mis: covariance reflects actual error regardless of model. |
| C08 | Sensor Fusion | RESCOPE | A | MOB,PER | 10→8 | C07, R03~R16 | C Z | Q+L | 2 | Fix wrong edge to R09 (actuators). T: time-aligned IMU+vision fusion. Mis: correlated sensors treated as independent. |
| C09 | Digital Control | RESCOPE | F | MAN,MOB,SYS,PER | 10→10 | C01, M05~M11 | Z V C | Q+L | 2 | Sampling, aliasing, delay, first-order filters. T: choose a sample rate and cutoff. Mis: filtering is free of delay. |
| C10 | Nonlinear Control | DEFER | A | J | 25→0 | - | — | N | 2 | Lyapunov intro through Underactuated Ch. 9 when pursuing certificates. |
| C11 | Model Predictive Control | RESCOPE | A | MAN,MOB | 20→14 | C13, M13 | V Z C | Q+L+X | 2 | Reorder after C13. T: add a constraint and explain infeasibility recovery. Mis: MPC handles any model mismatch. |
| C12 | Nonlinear State Estimation | KEEP | A | MOB,PER | 12→10 | C07, M06 | V Z C | Q+L | 2 | T: EKF divergence on a bearing-only case. Mis: EKF covariance is trustworthy under strong nonlinearity. |
| C13 | Optimal Control | RESCOPE | A | MAN,MOB | 25→16 | C05, M10 | V D C | Q+L+X | 2 | Trajectory optimization before MPC; CMU 16-745. T: direct collocation of a swing-up. Mis: locally optimal trajectory is globally optimal. |
| C14 | Whole-Body Control | KEEP | A | MOB | 25→16 | R11, C11 | V D S | A+X | 2 | T: reprioritize tasks under limited torque. Mis: tasks combine without conflict. |
| C15 | Advanced Control | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; adaptive and robust material on demand. |
| S01 | Simulation Fundamentals | KEEP | F | S | 8→8 | M07, PY04 | S V C | Q+L | 2 | T: expose integrator energy drift. Mis: simulator output is ground truth. |
| S02 | MuJoCo | KEEP | F | S | 12→12 | S01, R02 | S C | L+X | 3→2 | T: build an unseen mechanism in MJCF; match analytic energy. Mis: contact parameters are physical constants. |
| S03 | ROS 2 Fundamentals | KEEP | A | MAN,MOB,SYS | 10→10 | T01, PY01 | C V | L | 2 | Move docs to Jazzy (Humble EOL May 2027). T: debug a topic mismatch via CLI. Mis: topics are reliable by default. |
| S04 | Robot Description | KEEP | F | S | 6→6 | R03~S03 | C Z | L | 2 | URDF validated against R04 FK. T: find a seeded frame error. Mis: visual frame equals joint frame. |
| S05 | ROS 2 Runtime | KEEP | A | SYS | 10→8 | S03 | C | L+X | 2 | T: measure delay under QoS and executors. Mis: callbacks run in parallel by default. |
| S06 | Hardware Integration | RESCOPE | A | SYS | 15→10 | S05, S07, R09 | C S | L+X | 2 | Absorbs S10; mock hardware first. T: mock driver timeout handling. Mis: hardware commands are always applied at send. |
| S07 | Robot Safety | RESCOPE | F | S | 6→6 | none | W S | Q+A | 2 | Move earlier; currently not a prerequisite of S06. T: hazard table and watchdog test. Mis: simulation success implies safety. |
| S08 | System Identification | KEEP | A | MOB,RLL | 12→10 | S02, M10~C07 | S C | L+X | 2 | T: fit damping, verify on unseen trajectory. Mis: low training residual identifies parameters. |
| S09 | Sim2Real | RESCOPE | A | MOB,RLL | 20→14 | S08~RL13 | V S P | A+X | 2 | Absorbs RL16; staged validation. Reviewed. T: sim-to-sim transfer before any hardware. Mis: wider randomization is always better. |
| S10 | ROS 2 Control | GROUP→S06 | A | SYS | 16→0 | - | — | — | 2 | ros2_control with mock hardware is the integration lab. |
| S11 | Advanced Simulation | DEFER | A | J | 15→0 | - | — | N | 2 | Batched and differentiable simulation on demand (MJX, Isaac Lab). |
| S12 | Advanced Robotics Software | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all; real-time specifics via CPP10 and S06. |
| V01 | Digital Images | KEEP | F | S | 4→4 | PY04 | C Z | Q+L | 2 | T: detect channel and axis swap. Mis: image axes are x,y. |
| V02 | Image Processing | RESCOPE | F | S | 8→6 | V01, M03 | Z V C | Q+L | 2 | T: aliasing when downsampling. Mis: convolution order never matters with nonlinear steps. |
| V03 | Camera Models | KEEP | F | S | 8→8 | V01, M12 | V Z D C | Q+L | 3→2 | T: reproject unseen 3D points in a robot frame. Mis: focal length scales depth. |
| V04 | Camera Calibration | KEEP | A | MAN,PER | 6→10 | V03, M10 | C V | L+X | 2 | Hosts nonlinear least squares (Gauss-Newton, robust loss) at first use. T: separate fit from held-out reprojection error. Mis: low RMS means calibrated everywhere. |
| V05 | Feature Extraction | RESCOPE | A | PER | 8→6 | V02, V03 | Z C | Q+L | 2 | T: match under rotation and report recall. Mis: more features means better pose. |
| V06 | CNN | RESCOPE | F | PER,RLL | 12→12 | ML05, V02, PY06 | V Z C | Q+L | 3→2 | Absorbs V07. T: receptive field of unseen stack; small-data baseline. Mis: pooling gives invariance to all transforms. |
| V07 | Image Classification | GROUP→V06 | F | PER,RLL | 8→0 | - | — | — | 2 | Classification is the first CNN application. |
| V08 | Object Detection | RESCOPE | A | PER | 14→10 | V06, ML03 | V C | Q+L | 3→2 | Absorbs V10; use and evaluate over reimplementing. T: mAP on robot images. Mis: high mAP implies grasp usability. |
| V09 | Object Tracking | DEFER | A | J | 10→0 | - | — | N | 2 | Pull when a task needs identity over time. |
| V10 | Segmentation | GROUP→V08 | A | PER | 10→0 | - | — | — | 2 | Masks and boxes share evaluation logic. |
| V11 | Multi-View Geometry | KEEP | A | PER | 18→14 | V04, M17 | V Z D C | Q+L+X | 2 | T: triangulate with baseline sensitivity. Mis: more baseline is free of matching cost. |
| V12 | Depth Estimation | GROUP→V13 | A | PER | 10→0 | - | — | — | 2 | Stereo is the entry to 3D perception. |
| V13 | 3D Perception | RESCOPE | A | PER,MAN | 18→16 | V11, M11 | Z C | Q+L+X | 2 | ICP with outliers plus stereo depth. T: failed registration diagnosis. Mis: ICP is globally convergent. |
| V14 | Visual Representation Learning | GROUP→ML08 | A | PER,RLL | 12→0 | - | — | — | 2 | Same evaluation discipline. |
| V15 | Vision Transformers | GROUP→ML09 | A | PER,RLL | 6→0 | - | — | — | 2 | ViT is an ML09 worked case. |
| V16 | Video Understanding | DEFER | R | J | 15→0 | - | — | N | 2 | Pull for temporal perception tasks. |
| V17 | Visual Odometry & SLAM | KEEP | A | PER | 30→24 | V11, C12, M15 | V C P | A+X | 2 | Stachniss, Barfoot. Reviewed. T: drift analysis on a public sequence. Mis: ATE alone evaluates odometry. |
| V18 | Vision Foundation Models | GROUP→ML08 | R | RLL | 10→0 | - | — | — | 1 | Taught as tool use with held-out evaluation; DINOv2, CLIP. |
| V19 | 3D Neural Representations | DEFER | R | J | 25→0 | - | — | N | 1 | Neural fields tracked in registry. |
| V20 | Advanced Perception | ARCHIVE | R | X | 30→0 | - | — | N | 1→– | Catch-all. |
| RL01 | RL Fundamentals | KEEP | F | S | 4→4 | PY01, M08 | V Z C | Q | 2 | T: compute return in an unseen task. Mis: reward equals goal. |
| RL02 | Markov Decision Processes | RESCOPE | F | S | 10→14 | RL01 | V Z D C | Q+L | 3→2 | Absorbs RL03. T: solve a two-state system exactly, then in code. Mis: V is the immediate reward. |
| RL03 | Value Functions | GROUP→RL02 | F | S | 8→0 | - | — | — | 3 | V, Q and Bellman are not separable in practice. |
| RL04 | Dynamic Programming | KEEP | F | RLL,MOB | 6→6 | RL02, PY02 | Z C | L | 2 | T: value iteration with residual stop. Mis: DP needs no model. |
| RL05 | Model-Free Prediction | RESCOPE | F | RLL,MOB | 8→12 | RL02, M09 | Z V C | L+X | 2 | Absorbs RL06. T: cliff walking, SARSA vs Q-learning. Mis: TD has no bias. |
| RL06 | Model-Free Control | GROUP→RL05 | F | RLL,MOB | 10→0 | - | — | — | 2 | Prediction and control taught as paired experiments. |
| RL07 | Function Approximation | RESCOPE | F | RLL,MOB | 8→6 | RL05, ML04 | Z C | Q+L | 2 | T: observe the deadly triad numerically. Mis: more function power stabilizes. |
| RL08 | Policy Gradient | KEEP | F | RLL,MOB | 12→12 | RL02, ML05 | V D C | Q+L+X | 3→2 | T: two-action gradient vs finite-difference check. Mis: log-derivative needs differentiable dynamics. |
| RL09 | Actor-Critic | KEEP | F | RLL,MOB | 10→8 | RL08, RL05 | V D C | Q+L | 3→2 | Reusable actor-critic competence; gates RL10 and RL11. T: inspect critic and actor error separately. Mis: critic error directly equals policy quality. |
| RL10 | PPO | RESCOPE | F | RLL,MOB | 16→13 | RL09, ML06~RL12 | V Z D C | Q+L+X | 3 | See blueprint, as revised. Mis: clipping guarantees monotonic improvement. |
| RL11 | Off-Policy RL | KEEP | A | RLL | 18→12 | RL07, RL09 | V C | Q+L | 2 | SAC via CleanRL. T: replay-bias diagnosis. Mis: off-policy always more sample-efficient in wall-clock. |
| RL12 | RL Experimental Design | RESCOPE | A | RLL,MOB | 8→8 | RL05, RS02, ML03 | C P | A+X | 2 | Henderson 2018; Agarwal 2021. T: IQM with CIs over seeds. Mis: best-seed reporting; 3 seeds suffice. |
| RL13 | Continuous Control | RESCOPE | A | MOB,RLL | 10→8 | RL10, C02 | S C | L+X | 2 | Absorbs RL15. T: action scaling and saturation. Mis: reward scale is cosmetic. |
| RL14 | Reward Engineering | KEEP | A | MOB,RLL | 6→6 | RL02 | S W | A+X | 2 | Remove RS02 gate. T: construct and detect a reward loophole. Mis: shaping never alters the optimum. |
| RL15 | Curriculum Learning | GROUP→RL13 | A | MOB | 8→0 | - | — | — | 2 | A training technique within continuous control. |
| RL16 | Domain Randomization | GROUP→S09 | A | MOB,RLL | 8→0 | - | — | — | 2 | Domain randomization belongs to the sim2real validation loop. |
| RL17 | Imitation Learning | RESCOPE | A | RLL | 10→10 | ML06, RL01~RL02 | V Z C | Q+L | 2 | BC first, then DAgger; MDP need is soft. T: rollout failure despite low BC loss. Mis: low validation loss implies good rollouts. |
| RL18 | Offline RL | DEFER | R | J | 15→0 | - | — | N | 2 | Levine 2020 tutorial on demand. |
| RL19 | Model-Based RL | GROUP→E08 | A | RLL | 18→0 | - | — | — | 2 | Taught with world models. |
| RL20 | Hierarchical RL | GROUP→E04 | A | MAN,RLL | 15→0 | - | — | — | 2 | Options only as one implementation of skills. |
| RL21 | Safe RL | DEFER | R | J | 12→0 | - | — | N | 2 | Constraint mindset stays in S07; methods on demand. |
| RL22 | Multi-Agent RL | DEFER | R | J | 25→0 | - | — | N | 1 | Registry only; outside core embodied track. |
| RL23 | Advanced Exploration | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| RL24 | Meta-RL | DEFER | R | J | 15→0 | - | — | N | 1 | Registry only. |
| E01 | Sequential Decision Making | GROUP→RL02 | A | S | 8→0 | - | — | — | 2 | No unique skill; removes the false gate on E02. |
| E02 | Planning Fundamentals | RESCOPE | F | MAN,MOB | 8→8 | PY02 | Z C | Q+L | 2 | Today needs 14 ancestors incl. RL and control; only PY02 is required. T: inadmissible heuristic detection. Mis: A* is optimal with any heuristic. |
| E03 | Planning Under Uncertainty | RESCOPE | R | COG | 20→12 | E02, C07 | Z D C | Q+A | 2 | Belief states and information gathering. T: act now or sense first. Mis: replanning replaces belief. Open reasoning reviewed. |
| E04 | Robot Skills | RESCOPE | A | MAN,RLL | 10→10 | PY07~R04, S02, C01, RL13 | S C | L+X | 2 | Contracts and state machines first; reaching and learned options add their own needs. T: recover from a failed precondition. Mis: skills compose without state checks. |
| E05 | Task Planning | KEEP | A | MAN,COG | 10→6 | E02 | Z C | Q+L | 2 | T: find impossible precondition. Mis: symbolic plan implies geometric feasibility. |
| E06 | Task & Motion Planning | KEEP | A | MAN | 20→14 | E05, R18, R05 | V C P | A+X | 2 | Garrett 2021. Reviewed. T: reject and replan an unreachable grasp. Mis: plan-then-check is complete. |
| E07 | Imitation-Based Robot Policies | RESCOPE | A | RLL | 15→14 | RL17~E16, ML09, ML11 | V C P | L+A+X | 2 | MLP BC baseline, then ACT if budget allows. T: changed object or camera. Mis: low training loss implies success. |
| E08 | World Models | RESCOPE | R | RLLV | 20→12 | RL02, ML06~RL09 | V C P | A+X | 2 | Absorbs RL19 as a group. Shooting or CEM first; Dreamer-like extension needs RL09. T: one-step vs multi-step error and control usefulness. Mis: lower pixel error gives better control. |
| E09 | Object-Centric Representations | RESCOPE | R | COG | 18→10 | ML08~V13 | P C | A | 2→1 | Reproduce a narrow claim; occlusion identity test. Reviewed only. |
| E10 | Vision-Language Models | RESCOPE | A | RLLV,COG | 14→8 | ML09, ML08 | V C | A+X | 2 | Use and evaluate. T: spatial-relation failure test. Mis: grounding follows from caption ability. |
| E11 | Diffusion/Flow Action Policies | RESCOPE | A | RLLV | 18→10 | E07, ML11 | V Z D C | L+A | 1→2 | Modern visuomotor specialization only; low-dimensional BC is a valid alternative. Mis: MSE handles multimodal targets. |
| E12 | Vision-Language-Action Models | RESCOPE | R | RLLV,COG | 20→10 | E07, E10 | P C | A | 1→2 | Run open models (Octo, pi0) on held-out tasks. Reviewed only. Mis: demo video proves generalization. |
| E13 | Long-Horizon Robot Learning | REMAP→CAP | R | J | 25→0 | - | — | N | 1 | Assessed through capstones with stage-wise success metrics. |
| E14 | Embodied Reasoning | RESCOPE | R | COG | 25→16 | E05, E10 | P C | A | 1 | Plan validity after a scene change; HRI, privacy and shared autonomy stay visible here. Reviewed only; human-subject work needs ethics review. A plausible explanation is not evidence. |
| E15 | Advanced Embodied Intelligence | ARCHIVE | R | X | 40→0 | - | — | N | 1→– | Catch-all. |
| E16 | Robot Data Collection | NEW | A | RLLV | 0→10 | S02, RL17 | C S | L+A | new:2 | Temporal alignment, provenance, splits, QA; existing licensed datasets need no teleoperation hardware. T: find a bad-demo cluster. Mis: more demos always help. |
| RS01 | Scientific Reasoning | KEEP | F | S | 4→4 | none | W | Q+A | 2 | T: write a falsifier for a claim. Mis: confirmation as proof. |
| RS02 | Experimental Design | KEEP | F | S | 8→8 | RS01, M09 | W C | Q+A+X | 3→2 | Absorbs RS05. T: factorial ablation design. Mis: changing two factors at once is efficient. |
| RS03 | Statistical Inference | GROUP→M09 | F | S | 10→0 | - | — | — | 2 | Inference is taught once in M09 and applied in RS02, RL12. |
| RS04 | Experimental Reproducibility | RESCOPE | F | S | 10→14 | RS02, T02, PY07 | C | L+X | 3→2 | Absorbs PY08, T05, RS09. Fresh-clone rerun is machine-checkable. Mis: seed fixes all nondeterminism. |
| RS05 | Error Analysis | GROUP→RS02 | F | S | 6→0 | - | — | — | 2 | Taught in every evaluation task. |
| RS06 | Paper Reading | KEEP | F | S | 8→8 | RS01 | P W | A | 2 | Claim-evidence-assumption table, reviewed. Mis: venue equals validity. |
| RS07 | Scientific Writing | KEEP | R | RES | 15→10 | RS06, RS02 | W | A | 2 | Human review needed for verified status. |
| RS08 | Literature Review | DEFER | R | RES | 10→6 | RS06 | P | A | 2 | Pull at the start of a research project. |
| RS09 | Research Software | GROUP→RS04 | F | S | 10→0 | - | — | — | 2 | Traceability is part of reproducibility. |
| RS10 | Advanced Research | ARCHIVE | R | X | 60→0 | - | — | N | 1→– | Research output cannot be a curriculum node; L4 is evaluated per project. |


**Claude has completed Round 4 and will not edit Codex's final report.**

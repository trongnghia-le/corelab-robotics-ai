# CoreLab independent curriculum review — Codex

Audit baseline: commit `38b6a1d8f0baae9a753882185da7bd4430d14277`, repository `trongnghia-le/corelab-robotics-ai`. Date: 2026-10-30. This is a proposal, not an implementation or a claim of optimality. No production curriculum, historical assessment, application code, signing key or learner progress is changed.

## Round 1 — Independent audit

**Independence declaration:** I did not read Claude's review before writing this round. Recommendations below stand on inspected repository files, independently checked resource endpoints, mathematical/content analysis and the identified research sources. They are not an endorsement of my own earlier implementation choices. Accepting the product's evidence-integrity architecture does not establish the validity of its present assessment items.

### 1. Findings that can be reproduced

| Observation | Evidence | Interpretation and limit |
| --- | --- | --- |
| 169 topic IDs; 310 prerequisite edges; 90 P0, 59 P1, 20 P2 | `corelab/curriculum_graph_v1.json`; independent graph traversal; `npm run validate:content` passes | Structurally valid DAG, not proof of pedagogically valid dependencies. |
| Target levels: 122 topics target L2, 27 target L3, 20 target L1 | Same graph | These are lifetime targets, not verified present delivery. Do not advertise these targets as achievable through the current contracts. |
| 31 authored lessons and 31 v1 diagnostic contracts; 138 topics have overviews only | `content/lessons/`, `content/assessments/`, `content/overviews/topics.json` | Every ID is navigable, but most IDs do not yet offer a complete, assessed learning experience. |
| All 31 diagnostics have exactly one C choice item, three M numeric items and one ungraded T short response | All 155 diagnostic items inspected | An identical item template is being applied to very different constructs; arithmetic is a particularly poor proxy for debugging, memory ownership or scientific judgment. |
| All 31 critical C choice items have answer index `0`; 30 are binary, one has three options | All `content/assessments/*.v1.json` | A positional strategy can answer every C gate. One choice item also gives weak coverage of the stated concept. This is an assessment-design finding, not an instruction to change immutable v1 keys. |
| Four graded items mean scores 0/25/50/75/100 | `lib/engine.ts` lines 17–59 | The nominal ≥80% threshold actually requires 4/4 here. It is both coarsely unforgiving and insufficiently representative; raising the threshold does not repair content validity. |
| Only M02 and PY01 have signed implementation contracts | `lib/labs.ts`, `scripts/lab-tests.py`, `lib/practice.ts` | Dot and mean implementation evidence does not establish full mastery of vectors or Python. Other coding/experimental activities are explicitly practice. |
| 42 targeted questions in seven topic banks | `content/practice/`; `lib/weaknesses.ts` | Good initial remediation mechanism, very limited skill coverage; honest exhaustion is preferable to inventing new questions. |
| 28 video resources; 27 topics mapped, including 25 authored lessons | `content/media/` | I independently obtained HTTP 200 from all 28 source URLs and all 28 corresponding YouTube oEmbed endpoints; every stored title/channel matched. This establishes point-in-time availability/identity, not full-content accuracy, worldwide access, captions, duration, license clearance, or teaching effectiveness. |
| Eight distinct demos mapped to 13 topics; nine authored lessons have a demo | `lesson-media.v1.json`, `components/visualizations/` | Eight models are not eight courses. Some are previews or partial-topic models. |
| Nine authored topics have static illustrations; 14 authored topics have either a demo or illustration | Media sidecar | 17 authored topics lack these local visual aids; video animation may still support some of them. Do not describe all lessons as text-only. |
| Declared lesson time totals 1,660 minutes: 28×55 + 3×40 | Lesson frontmatter | 27 h 40 min is metadata, not measured time-to-competence, and excludes an established estimate for the other 138 topics, review, coding or projects. |
| 29 edges are transitively redundant | Independent ancestor traversal | Redundancy can clarify readiness. A transitive reduction is not itself a pedagogical optimization and does not necessarily reduce the prerequisite closure. |

The current recommender is restricted to authored lesson IDs (`app/api/state/route.ts` calls `recommend(progress, lessonIds(), ...)`), requires L1 on each listed prerequisite, and excludes P2 (`lib/engine.ts`, lines 121–149). Consequently, changing a graph alone will not deliver missing instruction. Conversely, a broad topic's thin L1 diagnostic is not strong assurance that every skill required by a downstream topic is ready. Preserve the useful distinction between readiness for the **next introductory activity** and completion of a lifetime target.

### 2. Strengths worth preserving

1. Stable IDs, explicit prerequisites, understandable deterministic recommendations, and the ability to inspect the graph. Preserve old IDs even when presentation units merge.
2. C/M/I/T, L0–L4 and A0–A3 separate several concepts that many learning apps collapse into activity counts. Keep this architecture and its conservative refusal to auto-grade open reasoning.
3. Assisted work, reading, watching and AI feedback do not automatically certify mastery. Signed local reports preserve provenance; they do not prove authorship, novelty or resistance to a dishonest machine owner. This limitation is already correctly documented.
4. Several lessons have worthwhile first-principles reasoning: M02 orthogonality, M06 local Jacobian prediction, M07 discretization stability, M08 base-rate reasoning, R04 reach bounds, R06 directional differences, and R07 energy balance. Expand these rather than replacing them with videos alone.
5. MIT, Northwestern, Stanford and the verified publishers form a sound source pool. Most video descriptions already acknowledge partial coverage. The registry's reusable attribution and click-to-load design are useful.
6. Overviews and unsupported verification are labeled honestly. Do not replace honest gaps with fabricated resources or a nominal “complete” curriculum.

### 3. Main curricular problems and bounded recommendations

| Proposal | Reasoning/evidence | Benefit | Cost, uncertainty and risk |
| --- | --- | --- | --- |
| **P01 — Define scoped readiness objectives, not just broad topic titles** | M05's authored lesson covers derivatives, not all “Calculus I”; M04 covers span/rank with only mentions of QR/SVD; ML02 is a linear-regression introduction, not all classical ML. Actual files and [S4, S7]. | Learners know what a PASS licenses them to attempt. | Requires authoring and item-to-objective mapping. Do not retroactively invalidate earned v1 evidence or claim missing content has been delivered. High confidence in scope mismatch; optimal granularity untested. |
| **P02 — Fill precalculus and numerical bridges inside existing topics** | M01 teaches functions/units but R04 assumes trigonometry; M07 uses integration although M05 teaches derivatives; C04/C05 need spectral/linear-system skills not taught by M04's examples. Quaternions and pseudoinverses are mentioned elsewhere, so they are not literally absent, but executable competency is not established. | Prevents hidden prerequisites and avoidable imitation. | Expand M01 with a diagnostic-selected algebra/trig/exp-log bridge; M05 with elementary integration; M04/M11 with eigenvectors, conditioning, stable solves and SVD/pseudoinverse as demanded by later tracks. Not a prerequisite to complete a full university math sequence first. High confidence in these prerequisites; effort must be piloted. |
| **P03 — Add covariance/Gaussian and uncertainty foundations before Kalman/RL evaluation** | M08's diagnostic never assesses Bayes' rule despite its central lesson example. M09 is overview-only; C07 expects covariance and RS03 inference. [S7, S11]. | Aligns mathematical readiness with sensor fusion and empirical claims. | Prefer scoped M08/M09 sublessons, not a mandatory advanced probability course. Add conditional-independence counterexamples and covariance propagation, then uncertainty on actual measurements. |
| **P04 — Add an explicit motion-planning unit, candidate ID R16** | E02 currently specifies A* on a discrete graph; E06 jumps to TAMP. No current overview explicitly teaches collision checking, C-space obstacles or sampling-based motion planning. LaValle chapters 2/4/5 distinguish these problems [S6]. | Supplies a durable robotics foundation and a bridge to TAMP independent of deep RL. | One genuinely new unit and collision-test authoring. Proposed 6–12 learner hours is a planning estimate, not a measurement. Only mandatory on the relevant robotics/planning path; do not make everyone complete it before ML. |
| **P05 — Make safety awareness an entry point and gate physical practice** | S07 currently waits for R01/R09, while S06 does not explicitly depend on S07. Source is a curriculum gap, not a claim that the current app controls real robots. | Hazards, limits, timeouts and simulation-before-hardware become explicit. | Split elementary awareness from quantitative hazard analysis. Removing S07's entry prerequisites must not be mistaken for permission to operate hardware after a short quiz. Human/site-specific approval remains necessary. |
| **P06 — Separate universal starter activities from role-specific P0** | Ninety P0 topics include substantial C++, control, detection and PPO content. These are not all prerequisites for every community member. The app supports goals; that supports track-relative interpretation. | Earlier useful projects and parallel study without deleting foundations. | Keep the broad map; show a small starter menu, then robotics/control, classical vision, ML/deep vision, RL, and research/embodied specializations. No validated universal shortest path is claimed. |
| **P07 — Merge teaching activities without merging evidence identities** | PY01/PY03 aliasing, PY07/T04 testing, M12/R03 frames, ML01/ML03/ML07 evaluation, RL01/RL02/RL03 MDPs, and RS04/PY08/RS09 reproducibility overlap in actual content. | One integrated lab can expose distinct concepts without repeated boilerplate. | Preserve IDs, objective tags and separate scoring. Do not conflate mathematical Jacobians (M06) with robot twists/frames (R06), or policy evaluation with policy improvement. Medium confidence in efficiency; measure actual duplication and omissions first. |
| **P08 — Teach experiment discipline before expensive training** | PPO can be reached without RL12; the latter has 16 ancestors in the current graph. RL experimental variability is documented in [S10]. | Avoids “one lucky curve” and invalid comparisons. | Introduce a minimal RS01/RL12 protocol before the first stochastic training exercise. Full statistical-inference mastery need not block observing a toy example. More seeds are not an automatic PASS; report uncertainty and compute constraints. |
| **P09 — Keep frontier topics elective and problem-driven** | All 20 P2 topics already have lower target levels, and no L3/L4 certification is implemented. E07 currently requires ML09 even though behavior-cloning robot policies need not use transformers; V09 similarly suggests only detection-based tracking. | More enduring foundations and fewer fashion-driven gates. | Preserve access to diffusion, VLA, neural fields and advanced research. Demand a narrow reproducible comparison rather than training a foundation model from scratch. Hardware/network budgets vary; no universal GPU assumption. |
| **P10 — Fix assessment validity before expanding certificate-like claims** | The template and answer-position findings above; CPP02's arithmetic counts do not establish memory safety; PY07's “three tests minus one” does not establish test design. | More meaningful evidence without changing the integrity philosophy. | New, versioned contracts and calibrated rubrics cost substantially more than new prose. Never edit v1 questions/answers, rewrite past attempts, or promote AI solutions. High confidence in the construct mismatch; predictive validity of replacements still requires a pilot. |

Additional scope gaps worth checking in authoring: sensor/actuator electrical units and current/voltage limits in R09/S06; sampling/aliasing, timestamps, filtering and delay in C09/C08; basic data structures, graphs, heaps and complexity within PY02/CPP05; privacy, human interaction and misuse boundaries in S07/RS01/E14. These are **proposed subskills**, not proof that a whole additional course per subskill is needed. E14 mentions causal structure; its delivery must go beyond “a model produced a plausible explanation.”

### 4. Proposed prerequisite projection for debate

The table is a **hypothesis**, not a production edit. Unlisted prerequisites stay exactly as in v1. Introductory and advanced subskills must be specified before these changes are approved. The projected graph includes all 169 original IDs plus one candidate R16.

| Topic | Proposed hard prerequisite IDs | Why this change is defensible / what remains conditional |
| --- | --- | --- |
| R02 | M01 | Counting simple mechanism degrees of freedom does not require Newtonian dynamics. R01 remains useful for actuator/force applications. |
| R03 | M12 | Rigid coordinate transformations need geometry/matrices; mechanism counting is supporting context rather than a mathematical necessity. |
| R04 | R03 | Planar FK does not require a completed span/rank/least-squares unit. Algebra/trigonometry must be present in the M01 readiness bridge; advanced Jacobian/inverse work still needs M04. |
| C08 | C07, R03 | Replace actuator/transmission mastery with coordinate-frame readiness for the stated alignment/fusion scope. Scalar same-frame fusion can be introduced earlier; rigid-body alignment is a robotics-track requirement, not universal sensor arithmetic. |
| S05 | S03 | Python ROS runtime exercises need not require C++. Add C++ prerequisites to the C++ extension, not to every ROS exercise. [S9] |
| S07 | none | Introductory safety awareness first; quantitative hardware authorization still requires mechanics, actuator limits and supervised validation. |
| S06 | S03, R09, S07 | Make safety explicitly upstream of hardware integration. |
| E01 | RL02 | Remove continuous-control-system mastery from introductory sequential decision making; do not remove probability/MDP reasoning from its full stochastic scope. |
| E02 | M01, PY02 | Deterministic A* search needs state transitions, graphs and costs, not a completed stochastic-control/RL sequence. [S6] |
| E04 | E01, R04 | A tested reaching skill/state machine does not require a complete hierarchical-RL course. Continuous-feedback examples add C01 readiness; learned options still require RL20. |
| E07 | RL17 | Basic imitation policies need not be transformers. ML09 is required for transformer/VLA implementations, and remains upstream of E10/E12. |
| RL09 | RL08, RL03, RL05 | Actor–critic needs a critic-learning/TD foundation, not just policy gradients and the definition of value. Reject teaching bootstrapped targets as unexplained code. |
| R16 (new candidate) | E02, R03 | Collision-aware configuration-space planning after search and rigid geometry; no need to wait for deep RL. |
| E06 | E05, R05, R16 | TAMP should rely on an actual motion-planning and collision-checking competency, not only IK. |

Do **not** indiscriminately add every related topic as a hard edge. Examples requiring a decision in debate: C02 general multivariable linearization needs M06, whereas a scalar introduction can use M05; R01's energy derivation uses calculus while its force-balance introduction can be taught earlier; V09 has feature-based, provided-detection and learned-detection variants. We need scope-dependent readiness and alternative routes, not another unnecessarily serial graph. The current engine represents AND prerequisites only; alternative routes/capability gates are proposals for future human-approved work, not existing functionality.

Validation result: **170 proposed nodes (169 retained original IDs + candidate R16), 308 edges, zero dangling references, zero duplicate edges, no cycles**. All unlisted edges are unchanged. R04's ancestor closure changes from 8 to 5; E02 from 14 to 3; E06 from 23 to 14. These are structural counts, **not measured learning-time savings**. Relaxed edges are safe only if the revised scoped teaching/assessment described above is actually supplied; the current application has not been changed.

### 5. Learning methodology: visual preference without weaker reasoning

Use a short **predict → manipulate → explain → derive → implement → falsify → delayed recall** loop. A video is optional input, not a completion condition. Respect a learner's preference for demonstrations; do not make an unsupported claim that matching a fixed “visual learning style” guarantees improved outcomes. Research supports practice testing/distributed practice [S1] and active engagement in studied STEM contexts [S2], but does not validate CoreLab's exact workflow, interval sequence or expected time savings.

- M01: function-machine and unit/number-line diagrams, then unfamiliar symbolic substitutions. Do not demand coding before PY01.
- M02/M03/M12/R03/R04/R06: editable vectors, bases/frames, transformations and motion arrows. Predict sign, direction and dimensions before moving controls; reconstruct one formula with the diagram hidden.
- M05/M06/M07/M10/C01/C03: tangent/sensitivity plots, a field or error trajectory and numerical-step experiments. The existing M10 loss is `(theta−3)^2`, but the demo uses `0.5*x^2`: their stable step-size bounds differ (1 vs 2). This is not a mathematical bug; make curvature/model changes explicit to prevent a false universal learning-rate rule. C01's lesson plant is an integrator while its PID demo uses a normalized first-order plant; likewise label the changed model and reconcile steady-state error before comparing curves.
- PY/CPP/T: state/lifetime trace, minimal failing program, independent oracle and one mutation rejected by a test. Animated ownership diagrams are useful for CPP02; a decorative robot animation is not.
- ML/V/RL: tiny synthetic datasets, receptive fields, computational graphs or a two-state environment before a large framework. V01's CNN demo and RL02's Q-learning demo are previews, not replacements for image conventions or a complete MDP specification.
- Safety/research/planning: scenario diagrams, constraint/state graphs, protocol design and failure analysis; watching a video or repeatedly deriving a trivial formula need not be mandatory.

Avoid a requirement that every topic contain all eight activity types. Select activities that reveal the particular misconception. A ten-minute experiment with a clear oracle can replace an unrelated long lecture, but **no measured ten-minute gain** is claimed. Topic-specific visualizations cost design, accessibility and mathematical testing effort; reuse the existing primitives before adding engines.

### 6. Resources: keep trustworthy sources, reject mismatched mappings

The independent endpoint audit of all 28 registered resources passed. Beyond this, the audit did **not** watch every complete lecture or establish caption languages, lengths, bandwidth, regional accessibility or suitability for each novice. Do not infer those facts from oEmbed.

| Existing mapping | Decision and rationale | Replacement/bridge and verification limits |
| --- | --- | --- |
| M08 → MIT 18.01 single-variable calculus in lesson `source_refs` | **REJECT as the primary probability reference**: the course identity does not match Bayes/conditional probability. This does not make MIT unreliable. | MIT 6.041SC probability units [S11] verified accessible; select exact conditional-probability/Bayes exercises rather than assign the entire course. |
| M07 → same calculus reference | **MODIFY**: useful calculus background, insufficiently specific for numerical ODE stability. | Use a first-order ODE/Euler reference with a stated step-size experiment. Exact replacement lecture not yet verified here; do not invent its URL. |
| M06/M10 → 3Blue1Brown neural-network gradient descent | **KEEP WITH BRIDGE**: useful animation, but neural-network context and scalar-output descent do not fully teach arbitrary vector-output Jacobians or a new learner's notation. | Use the local gradient/Jacobian derivation, a finite-difference check, and targeted portions after editorial timestamp verification; no fabricated clip marks. |
| V01 → CS231n image-classification lecture | **MODIFY role**: credible classification context, not complete coverage of pixel indexing, dtype, color conventions and sampling. | The tiny NumPy image experiment is the primary V01 activity. Save the full lecture for recognition context; [S8] is deep-learning oriented. |
| R04 → Modern Robotics PoE example | **KEEP AS EXTENSION**: authoritative, but the source representation is more advanced than two-link trigonometry. | Start with the planar demo/derivation; label screw/PoE notation as an extension and provide readiness guidance. |
| R06 → space Jacobian lecture | **KEEP WITH FRAME WARNING**: a spatial-twist Jacobian is not simply the planar endpoint-position Jacobian. | State output convention, reference frame, row order and units before comparing equations. |
| C01 → Modern Robotics control overview | **KEEP AS OVERVIEW**: relevant; it is not a full PID-tuning course. | Derive the chosen toy plant and test saturation/windup in a separate C03 activity. |
| PY04 → SciPy NumPy tutorial | **KEEP AS REFERENCE, not mandatory start-to-finish viewing**: relevant broad tutorial, unverified learner time/caption needs. | Use a targeted broadcasting/axis task with a loop oracle; provide a short text fallback. |
| MIT 6.0001 / CppCon / 3Blue1Brown / Silver resources | **KEEP provisionally**: titles, channels and URLs verified, source pool academically or professionally appropriate. | Individual lecturer names, exact section coverage and accessibility still need per-resource editorial checks; a publishing channel does not prove the identity of the person speaking. |
| Frontier reading lists | **REQUIRE TOPIC-LEVEL SELECTION**: a course homepage or laboratory publications index is not a curated lesson. | Choose one primary paper, artifact/version, assumptions and accessible prerequisite reference per research question. No requirement to train a large model from scratch. |

Maintain two evidence fields in a future editorial record: **availability verified** and **instructional match reviewed**. Record access barriers explicitly. Prefer official documentation for language/library behavior, textbooks for durable theory, course lectures for guided intuition, and primary papers for research claims. Do not replace original sources with AI summaries or unlicensed mirrors. Owning a book does not authorize copying its pages into the repository.

### 7. Assessment design: scope, uncertainty and remediation

**Preserve the current evidence history.** All recommendations here require new versioned contracts or additional clearly scoped evidence. Never change an old answer key, erase an assisted attempt, relabel it A0, infer learner authorship from a signature, or retroactively claim a past test measured broader competence.

Suggested evidence profiles for discussion (not implemented):

- **MAT:** explain assumptions/representation; derive or compute an unseen instance; verify with an independent numerical/analytic property; implement only where implementation is a real objective; later solve an unfamiliar representation/application.
- **CODE:** explain state/ownership and contract; implement/debug from a blank file; pass ordinary, boundary, invalid-input, nonmutation and property tests as relevant; diagnose a deliberately changed failure. Count-of-tests arithmetic is not mathematical reasoning evidence.
- **DYN:** define state/frame/units and model limits; derive a trajectory/controller/Jacobian; simulate with independent oracle and discretization/sensitivity tests; transfer to changed parameters or a failure condition, not real hardware by default.
- **DATA:** define data and leakage boundaries; derive the required estimator/loss/update; implement a tiny baseline with held-out checks; document uncertainty and subgroup/failure analysis; transfer to a shifted but specified task.
- **PLAN:** define states/actions/costs/constraints; trace and implement a search/planning update; validate against exhaustive small cases or a feasibility oracle; change an obstacle, goal, dynamics or uncertainty condition.
- **RESEARCH:** state a falsifiable claim, provenance and assumptions; design an independent comparison with a justified compute budget; reproduce a small artifact and inspect uncertainty; distinguish results from speculation. Not every topic needs artificial math or a code exercise.

For a **proposed scope-level PASS**, retain A0 independence and all topic-specific critical checks, require adequate objective coverage plus a justified explanation/derivation, and require actual implementation tests when claiming I. A nominal ≥80% objective score can remain a compatibility rule; it is **not** empirically validated proof of broad competence. Open work stays unverified until a real review mechanism exists. A rubric must say which errors are critical and show anchored examples. Hypothesized improvements need a pilot, not a rebranding of the existing four questions.

For **L3**, require a reviewed unfamiliar application **and** appropriately delayed independent evidence; two repeats of a known quiz are retention evidence only. For **L4**, require a narrow reproducible critique/extension with provenance, baselines, uncertainty and limitations. These are blueprints, not available certification. M may be genuinely inapplicable to some tooling/reading objectives: represent this explicitly in a future policy instead of manufacturing arithmetic questions to fill the cell, while retaining the C/M/I/T architecture.

Concrete priority blueprints:

| Topic | C/M tasks and critical misconception | I/correctness evidence | Unfamiliar transfer and retention |
| --- | --- | --- | --- |
| M01 | Distinguish a function from its inverse; check units, range, signs, algebra and necessary trig readiness. Reject a dimensionally invalid model. | Hand-check piecewise calibration and at least two boundary values; code is optional before PY01. | New sensor units/domain, closed notes after delay. Do not certify all precalculus from one evaluation. |
| M02 | Explain displacement vs point; derive projection and orthogonal residual. Critical: projecting onto zero direction, mixing frames. | Dot, norm and projection with independent examples, scaling/orthogonality properties, invalid dimensions and zero policies; current dot-only signature remains dot-only evidence. | Change basis/direction and constrained-motion problem; later reconstruct with new numbers rather than recall `(3,4)`. |
| M03/M04 | Explain composition order, rank/identifiability and residual vs parameter error; derive a small solve without explicit inverse. | Compare elimination and stable library solve; rank-deficient/inconsistent cases, residual and perturbation checks. | A noisy calibration with a hidden dependent measurement; delayed explanation of why low residual need not mean accurate parameters. |
| M05/M06 | Reconstruct chain rule/Jacobian shapes; distinguish scalar gradient, Jv and Jᵀv. Critical: lost inner derivative or inconsistent frame/shape. | Central differences over several step sizes and nonzero points; document nonsmooth exceptions. | Derive a new multi-output calibration. A scalar GD curve is insufficient to certify a vector Jacobian. |
| M08/M09 | Compute a Bayes posterior with changed base rates; distinguish independence, variance and covariance; explain sampling uncertainty. | Exact enumeration and seeded Monte Carlo agree within a predeclared justified interval. | A correlated-sensor counterexample and shifted base rate; no claim of full inference after a die question. |
| PY01/PY07/T04 | Explain return/print, aliases, nonmutation and independent oracles. Critical: a test that computes its expected result with the implementation itself. | Passing mean contract plus an independently designed test suite that rejects at least selected genuine mutations; current signed mean report does not verify test-design competence. | Debug a new function with a different boundary failure. Keep the artifact and delayed fresh cases. |
| R03/R04/R06 | Declare frames/relative angles/units, derive FK and J; distinguish spatial twist from endpoint velocity. Critical: inverse/order errors, singularity interpretation. | FK via trig and transform composition, reach and rotation invariants, directional differences at unequal lengths/nonzero angles; inspect singular values/rates. | A tool offset or altered joint convention and a near-singular task; reviewed derivation rather than only special zero-angle answers. |
| C01/C03 | Predict feedback sign, model-specific stability/steady error and sampled behavior. Critical: actuator saturation and unstable gain assumptions. | Simulate the declared plant with exact simple cases, step refinement, disturbance, noise and saturation checks. | A changed plant/delay and justified tuning trade-off. A toy curve cannot authorize hardware control. |
| ML01/ML05 | Explain leakage and baseline; derive a tiny loss's reverse-mode gradients including shared-parameter accumulation. | Hand derivative, independent finite differences, train/validation/test isolation and reproducible tiny training. | New output/loss or shared use; analyze a deliberately leaked preprocessing pipeline. |
| RL02/RL06 | Fully define finite transition/reward/terminal conventions; distinguish expected value from one trajectory and terminal from time-limit truncation. | Tiny MDP exact solve/exhaustive policies vs iterative values; Q update checks, independent evaluation seeds and a known-optimum small task. | Change rewards/transitions/observation sufficiency. Reaching a GridWorld goal once is not a statistically valid performance claim. |
| S07 | Identify hazards, energy/command limits, faults and stop conditions. Critical: a design that can issue unsafe commands on stale sensor data. | Simulated timeout/invalid-input/fault injection and a reviewed risk/response table; no live hardware certification from a quiz. | New hazard scenario and reviewed mitigation, with relevant hardware/supervisor approval outside CoreLab. |

These blueprints intentionally need more than one item's worth of concept coverage. Exact item counts, scoring tolerances, reviewer agreement and learning time are **unvalidated design parameters**; use small pilots to tune them. A familiar worked example checks local computation, not transfer. Ask for a different representation or changed assumptions, not merely larger numbers.

### 8. Retention and learning effort

`lib/engine.ts` lines 83–91 awards T1 when two independent full passes are separated by ≥7 days. That is a conservative retention marker, not a novelty test. `lib/reviews.ts` uses a single topic schedule with 1/3/7/21 days; targeted practice can schedule reviews without granting full-diagnostic mastery. `lib/weaknesses.ts` correctly prevents a seen variant from immediate automatic reuse and labels exhaustion.

**Keep** delayed retrieval and the separation of targeted repair from broad mastery. **Modify future review design** to use fresh but equivalent prompts where available, retain any unresolved critical skill, and allow a person to adjust cadence based on observed difficulty. A fixed 1/3/7/21 schedule is an engineering heuristic; the general spacing literature [S1] does not establish it as optimal for robotics, coding or every learner. Start with a small number of high-value mixed reviews, not every old quiz every day. A failure should record a present gap without deleting historical evidence.

Effort should be budgeted by objective and artifact. Proposed planning ranges: 1–3 hours for an introductory scoped unit, 3–8 for a worked mathematical/coding unit, 8–20 for a small integration project, with a separate review budget and adjustments after actual learner logs. These are **estimates**, not measured gains or commitments. They cannot be summed across all 169 broad labels as if the units had equal scope. Only video identity/availability and repository counts were measured in this audit. Compute cost, unavailable captions, accessibility needs, prior knowledge and debugging time can dominate.

Pilot two comparable sequences with declared entry knowledge and evaluate delayed unfamiliar-task performance, assistance needed, completion time, abandonment and uncertainty—not watch completion or the same post-lesson answer. Maintain both a general community map and optional learner-specific choices; an individual's Ubuntu/GPU context must not silently become a universal prerequisite or device requirement.

### 9. Questions I will put to Claude in subsequent rounds

1. Which proposed deletion or “advanced topic” deferral is tied to an actual objective and learner path, rather than a judgment based on its title?
2. Does a proposed hard edge assert mathematical necessity, safety necessity, helpful context or just the ordering of one textbook? What minimal counterexample would challenge that edge?
3. How is unseen transfer distinguished from parameter substitution and reuse of a published answer? What can a proposed automatic PASS genuinely verify?
4. Can an existing visual/experiment teach the objective without adding another animation, framework or video? Where does a changed mathematical model require a bridge?
5. Which resource links and topic matches have actually been checked, and which captions/durations/accessibility assumptions remain unverified?
6. What measured learner outcomes support any claimed time savings? If none, label the number as a planning hypothesis and propose a validation design.
7. Does any proposal break immutable evidence, collapse C/M/I/T, certify A1–A3 work, or retroactively downgrade legitimate historical evidence? If so, reject that mechanism even if its curricular motivation is useful.

### 10. Evidence register and confidence

Internal evidence refers to the baseline commit above. Primary external pages were checked during this audit; availability is point-in-time. Some search metadata and older course editions are used deliberately for durable theoretical structure, not described as the newest syllabus. No external material is copied into production content.

- **[S1]** Dunlosky et al. (2013), *Improving Students' Learning With Effective Learning Techniques*, [publisher summary](https://www.psychologicalscience.org/journals/pspi/1529100612453266/), [DOI](https://doi.org/10.1177/1529100612453266). Review evidence supports practice testing/distributed practice broadly; not a proof of CoreLab's schedule or an individual learner's optimal method.
- **[S2]** Freeman et al. (2014), *Active learning increases student performance in science, engineering, and mathematics*, [PNAS](https://doi.org/10.1073/pnas.1319030111). Meta-analytic evidence in undergraduate STEM; extrapolation to a single-user app is a hypothesis, not a measured CoreLab effect.
- **[S3]** Karpicke & Blunt (2011), *Retrieval practice produces more learning than elaborative studying with concept mapping*, [primary-paper record](https://pubmed.ncbi.nlm.nih.gov/21252317/), [DOI](https://doi.org/10.1126/science.1199327). Supports retrieval in the studied science-learning tasks, not automatic proof of programming transfer.
- **[S4]** Lynch & Park, *Modern Robotics*, [official author/course page](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) and [official video supplements](https://modernrobotics.northwestern.edu/). Durable sequence: configuration/rigid motion, kinematics, Jacobians, dynamics, planning and control. The course's prerequisites are supporting evidence, not an obligation to copy its entire syllabus.
- **[S5]** Tedrake, MIT Underactuated Robotics, [official prerequisite FAQ, Spring 2024](https://underactuated.csail.mit.edu/Spring2024/faqs.html). Basic linear algebra/ODE familiarity and Python are sufficient entry directions there; a full C++ prerequisite is not universal for mathematically rigorous robotics.
- **[S6]** LaValle, *Planning Algorithms*, [author-hosted chapter list/book](https://lavalle.pl/planning/). Chapters 2, 4 and 5 distinguish discrete search, C-space and sampling-based motion planning. Source is authoritative; exact CoreLab teaching order is my argued proposal.
- **[S7]** Zhang et al., *Dive into Deep Learning*, [preliminaries and chapter structure](https://d2l.ai/chapter_preliminaries/index.html). Separates data, linear algebra, calculus/autodiff, probability/statistics, regression, neural networks, optimization and later methods. A reference structure, not evidence that every chapter must be completed.
- **[S8]** Stanford [CS231n official course](https://cs231n.stanford.edu/) and [2017 lecture syllabus](https://cs231n.stanford.edu/2017/syllabus.html). Verified course focus and original lecture mapping; its image-classification/CNN lectures do not independently certify all basic image-processing objectives.
- **[S9]** ROS 2 [official Humble tutorials](https://docs.ros.org/en/humble/Tutorials.html), with separate Python/C++ client-library examples. Version-specific API/install references require an explicit maintained platform choice; do not silently force the original learner's Linux setup on a community curriculum.
- **[S10]** Agarwal et al. (2021), *Deep Reinforcement Learning at the Edge of the Statistical Precipice*, [authors' project](https://agarwl.github.io/rliable/) and [paper](https://arxiv.org/abs/2108.13264); Henderson et al. (2018), [AAAI proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/11694). Evidence for reporting experimental variability and careful comparisons, not for a universal mandatory seed count.
- **[S11]** MIT OCW, [6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/). Verified topic-appropriate alternative to the present M08 calculus mapping.

**High confidence:** repository counts; the actual score grid and uniform assessment pattern; fixed answer positions; absence of authored content/verifiers for most IDs; current engine/scheduler behavior; all registered resource identities returning matching oEmbed; discrete search not logically requiring continuous control; PoE vs planar and twist vs position-Jacobian distinctions.

**Medium confidence:** projected hard-edge choices, best merges, the proposed new planning unit's location, and which subskills deserve separate authored lessons. These have content-based arguments and primary references, not measured comparative curriculum outcomes.

**Low/unmeasured:** time savings, retention improvement specific to CoreLab, novice difficulty calibration, optimal item counts/review spacing, captions/region access, and the quality of all proposed future lessons. Do not convert these into promised results.

### 11. Per-topic coverage and method inventory

The following matrix accounts for all **169 original IDs**. It is an independent planning inventory, not a final negotiated syllabus. `L` means an authored lesson with its narrow v1 diagnostic; `O` means overview only. `V` means a mapped video; `D` a local demo; `I` an existing signed implementation verifier. Absence of a flag is not proof that a person cannot use an external resource independently. Method profiles are defined in section 7; the row's concept/application determines the proposed assessment target. All currently missing objectives, tests and transfer tasks still require authoring and human approval.

| ID and current topic | Existing delivery | Proposed route role | Method and specific assessment/application target |
| --- | --- | --- | --- |
| **M01** Mathematical Basics | L | starter option | MAT: functions, notation, units. Translate a sensor calibration into a domain and formula. |
| **M02** Vectors | L+V+D+I | starter option | MAT: dot product, norm, projection. Project a motion command onto an allowed direction. |
| **M03** Matrices | L+V+D | starter option | MAT: matrix product, transpose, linear map. Transform a batch of coordinates and check dimensions. |
| **M04** Linear Algebra | L+V | just-in-time foundation | MAT: span, rank, nullspace. Identify which parameters two dependent sensors cannot recover. |
| **M05** Calculus I | L+V | just-in-time foundation | MAT: derivative, limit, chain rule. Differentiate a nonlinear sensor calibration. |
| **M06** Multivariable Calculus | L+V+D | just-in-time foundation | MAT: gradient, Jacobian, directional derivative. Check a velocity map using directional differences. |
| **M07** Differential Equations | L+V | just-in-time foundation | MAT: ODE, initial condition, integration. Compare Euler decay with an exact exponential. |
| **M08** Probability | L | just-in-time foundation | MAT: conditioning, Bayes rule, expectation. Estimate fault probability after a noisy alarm. |
| **M09** Statistical Foundations | O | just-in-time foundation | MAT: sampling, variance, estimation. Report uncertainty across repeated sensor measurements. |
| **M10** Optimization | L+V+D | just-in-time foundation | MAT: objective, gradient descent, step size. Fit a calibration offset and check the gradient. |
| **M11** Numerical Computing | O | just-in-time foundation | MAT: floating point, conditioning, numerical error. Compare solver residual and parameter error at different scales. |
| **M12** Rigid-Body Geometry | L+V | just-in-time foundation | MAT: frames, rigid transform, homogeneous coordinates. Transform a camera point into robot-base coordinates. |
| **M13** Advanced Optimization | O | specialization | MAT: constraints, duality, convexity. Formulate bounded actuator allocation and inspect active constraints. |
| **M14** Advanced Probability | O | specialization | MAT: random processes, conditional independence, concentration. Compare an independence model with correlated sensor errors. |
| **M15** Lie Theory | O | specialization | MAT: SO(3), SE(3), exponential map. Compare small rotation increments with matrix composition. |
| **M16** Advanced Mathematics | O | frontier elective | MAT: functional analysis, manifolds, advanced inference. Select one theorem needed by a research paper and check its hypotheses. |
| **PY01** Python Fundamentals | L+V+I | starter option | CODE: values, functions, control flow. Implement and test a mean without library shortcuts. |
| **PY02** Data Structures | O | just-in-time foundation | CODE: lists, hash maps, queues. Compare a queue and a list for processing sensor messages. |
| **PY03** Python Semantics | O | just-in-time foundation | CODE: aliasing, mutability, scope. Trace a nested-list aliasing bug with a minimal example. |
| **PY04** NumPy | L+V | starter option | CODE: array shapes, broadcasting, axes. Normalize features and verify against a scalar loop. |
| **PY05** Scientific Python | O | track core | CODE: SciPy, plotting, numerical workflows. Fit an ODE parameter and plot residuals with units. |
| **PY06** PyTorch Basics | O | track core | CODE: tensors, autograd, training loop. Compare an autograd gradient with a hand-derived neuron. |
| **PY07** Testing & Debugging | L+V | starter option | CODE: unit tests, debugging, contracts. Catch a wrong projection denominator with independent assertions. |
| **PY08** Research Programming | O | track core | CODE: configuration, logging, reproducibility. Run the same small experiment from a clean checkout. |
| **PY09** Performance | O | specialization | CODE: profiling, vectorization, memory. Profile a loop and compare speed, memory, and numerical equivalence. |
| **PY10** Advanced Python | O | frontier elective | CODE: iterators, descriptors, metaprogramming. Implement a lazy data iterator and document its lifetime. |
| **CPP01** C++ Fundamentals | L | track core | CODE: types, compilation, arithmetic. Compile a mean function and detect integer truncation. |
| **CPP02** Memory Model | L+V | track core | CODE: lifetime, pointers, references. Analyze a vector reallocation and a dangling reference. |
| **CPP03** Resource Management | O | track core | CODE: RAII, unique ownership, move semantics. Replace manual allocation with a value or unique_ptr. |
| **CPP04** Classes & OOP | O | track core | CODE: encapsulation, interfaces, invariants. Design a bounded joint-state object that rejects invalid updates. |
| **CPP05** STL & Algorithms | O | track core | CODE: containers, iterators, algorithms. Choose a container for timestamped lookup and measure its trade-off. |
| **CPP06** Modern C++ | O | track core | CODE: templates, constexpr, modern idioms. Implement a small generic numerical utility with constrained assumptions. |
| **CPP07** Build Systems | O | track core | CODE: CMake, linking, build targets. Build a library and a separate test executable with CMake. |
| **CPP08** Debugging & Testing | O | track core | CODE: sanitizers, debuggers, test harnesses. Reduce a failing program and verify the fix with a regression test. |
| **CPP09** Complexity & Performance | O | specialization | CODE: complexity, cache locality, profiling. Compare vector traversal and scattered allocations with a benchmark. |
| **CPP10** Concurrency | O | specialization | CODE: threads, synchronization, data races. Build a producer-consumer queue and explain its locking contract. |
| **CPP11** Numerical C++ | O | specialization | CODE: Eigen, linear solvers, numerical stability. Solve least squares and compare residuals with a Python oracle. |
| **CPP12** Advanced C++ | O | frontier elective | CODE: generic libraries, ABI, systems design. Inspect one robotics library interface and document ownership risks. |
| **ML01** ML Problem Formulation | L | starter option | DATA: problem formulation, data split, baseline. Define a sensor-fault task without leaking test statistics. |
| **ML02** Classical ML | L+V | track core | DATA: regression, classification, regularization. Fit a linear baseline and compare with a held-out constant predictor. |
| **ML03** Generalization | O | just-in-time foundation | DATA: overfitting, capacity, distribution shift. Compare learning curves across training-set sizes. |
| **ML04** Neural Networks | L+V | track core | DATA: dense layer, activation, parameters. Compute a two-layer forward pass and count its parameters. |
| **ML05** Backpropagation | L+V | track core | DATA: chain rule, reverse mode, gradient check. Check a hand-written neuron gradient by finite differences. |
| **ML06** Deep Learning Training | O | track core | DATA: optimization, initialization, batching. Compare two learning rates using the same seed and data split. |
| **ML07** Model Evaluation | O | just-in-time foundation | DATA: metrics, calibration, held-out evaluation. Report precision, recall, and failure cases for a fixed test set. |
| **ML08** Representation Learning | O | specialization | DATA: embeddings, latent structure, feature quality. Compare frozen features with raw inputs on a small held-out task. |
| **ML09** Transformers | O | specialization | DATA: attention, tokenization, positional information. Compute a tiny attention matrix and inspect masking effects. |
| **ML10** Self-Supervised Learning | O | specialization | DATA: contrastive learning, masked prediction, augmentation. Design augmentations that preserve the intended semantics. |
| **ML11** Generative Models | O | specialization | DATA: likelihood, latent variables, generative modeling. Compare reconstruction quality with sample diversity. |
| **ML12** Advanced ML | O | frontier elective | DATA: robustness, scaling, advanced learning theory. Reproduce one narrow paper claim with an explicit falsifier. |
| **T01** Linux | O | starter option | CODE: shell, permissions, processes. Create a repeatable project command without relying on shell history. |
| **T02** Git | O | starter option | CODE: commits, branches, diffs. Commit one numerical experiment with its exact configuration. |
| **T03** Development Tools | O | just-in-time foundation | CODE: editor, debugger, environment. Configure one debug launch and document its working directory. |
| **T04** Software Testing | L+V | just-in-time foundation | CODE: test contracts, oracles, regression checks. Mutate a numerical function and show which test fails. |
| **T05** Reproducible Environments | O | just-in-time foundation | CODE: dependency locking, environments, configuration. Recreate a small experiment in a clean virtual environment. |
| **T06** Docker | O | specialization | CODE: containers, images, volumes. Describe which files survive replacing an experiment container. |
| **T07** Systems Performance | O | specialization | CODE: resource measurement, latency, throughput. Report CPU, memory, latency, and throughput for one pipeline. |
| **T08** Advanced Infrastructure | O | frontier elective | CODE: distributed jobs, artifact management, deployment. Design a minimal experiment job with restart and output contracts. |
| **R01** Mechanics Foundations | L | track core | DYN: force, acceleration, energy. Check cart acceleration and energy units from a free-body diagram. |
| **R02** Robot Mechanisms | L+V | track core | DYN: links, joints, degrees of freedom. Compare joint space and endpoint task space for a planar arm. |
| **R03** Rigid-Body Transformations | L+V | track core | DYN: rotation, composition, inverse transform. Compose wrist and camera calibration and verify a round trip. |
| **R04** Forward Kinematics | L+V+D | track core | DYN: serial chains, relative angles, forward map. Derive two-link reach and test special configurations. |
| **R05** Inverse Kinematics | O | track core | DYN: inverse map, multiple solutions, constraints. Compare two elbow solutions and identify an unreachable target. |
| **R06** Robot Jacobian | L+V+D | track core | DYN: velocity map, Jacobian, singularity. Verify a planar Jacobian using directional differences. |
| **R07** Rigid-Body Dynamics | L+V | track core | DYN: mass matrix, gravity, damping. Check a pendulum’s equilibrium and energy balance. |
| **R08** Contact Mechanics | O | track core | DYN: contact force, friction, complementarity. Compare sticking and sliding in a simple block experiment. |
| **R09** Actuators & Transmission | O | track core | DYN: motor torque, gear ratio, actuation limits. Convert motor torque through gearing while checking speed limits. |
| **R10** Mechanical Design Verification | O | track core | DYN: load cases, stress, design validation. State a load envelope and verify a bracket with an independent calculation. |
| **R11** Floating-Base Dynamics | O | specialization | DYN: floating base, momentum, underactuation. Explain why joint torques alone cannot directly command every base acceleration. |
| **R12** Advanced Dynamics | O | specialization | DYN: recursive dynamics, inertial parameters, efficient algorithms. Compare inverse dynamics with a small analytical model. |
| **R13** Advanced Locomotion | O | specialization | DYN: gait, balance, hybrid dynamics. Describe a gait’s contact sequence and a balance failure case. |
| **R14** Dexterous Manipulation | O | specialization | DYN: grasping, contact constraints, dexterity. Analyze whether a simple grasp resists a specified disturbance. |
| **R15** Advanced Mechanics | O | frontier elective | DYN: flexibility, continuum mechanics, complex mechanisms. Identify when a rigid approximation fails in a chosen mechanism. |
| **C01** Control Fundamentals | L+V+D | track core | DYN: feedback, error dynamics, stability. Derive proportional tracking and constant-disturbance error. |
| **C02** Dynamic Systems | O | track core | DYN: state space, equilibrium, linearization. Linearize a nonlinear one-state model and compare trajectories. |
| **C03** PID Control | O+D | track core | DYN: proportional, integral, derivative. Compare disturbance rejection and windup with actuator saturation. |
| **C04** Linear Systems | O | track core | DYN: controllability, observability, poles. Compute controllability and observability for a two-state model. |
| **C05** LQR | O | track core | DYN: quadratic cost, Riccati equation, state feedback. Compare feedback gains under two input penalties. |
| **C06** State Estimation | O | track core | DYN: measurement model, prediction, uncertainty. Estimate velocity from position observations and explain the noise trade-off. |
| **C07** Kalman Filtering | O | track core | DYN: Gaussian belief, Kalman gain, covariance. Derive a scalar gain and check uncertainty before and after an update. |
| **C08** Sensor Fusion | O | track core | DYN: sensor alignment, fusion, correlation. Explain why treating correlated sensors as independent overstates confidence. |
| **C09** Digital Control | O | track core | DYN: sampling, discretization, delay. Compare a continuous stable controller with a delayed sampled version. |
| **C10** Nonlinear Control | O | specialization | DYN: Lyapunov function, nonlinear stability, feedback linearization. Check the sign of a candidate Lyapunov derivative. |
| **C11** Model Predictive Control | O | specialization | DYN: receding horizon, constraints, prediction. Formulate a bounded cart problem and inspect feasible inputs. |
| **C12** Nonlinear State Estimation | O | specialization | DYN: EKF, UKF, nonlinear belief update. Compare linearization error with sigma-point propagation in a scalar example. |
| **C13** Optimal Control | O | specialization | DYN: trajectory optimization, optimality conditions, dynamic programming. Compare a locally optimized trajectory with a simple feasible baseline. |
| **C14** Whole-Body Control | O | specialization | DYN: task hierarchy, contact constraints, whole-body dynamics. Prioritize balance and reaching under limited actuation. |
| **C15** Advanced Control | O | frontier elective | DYN: robustness, adaptation, advanced control. State the uncertainty set behind a claimed robust controller. |
| **S01** Simulation Fundamentals | O | track core | DYN: integration, modeling error, simulation validation. Compare a simulated trajectory with an analytical solution. |
| **S02** MuJoCo | O | track core | DYN: MJCF, actuators, contacts. Build a minimal pendulum and compare energy with a reference model. |
| **S03** ROS 2 Fundamentals | O | track core | CODE/RESEARCH: nodes, topics, messages. Create a publisher-subscriber pair and document message units. |
| **S04** Robot Description | O | track core | CODE/RESEARCH: URDF, links, frames. Validate a two-link description against hand-derived transforms. |
| **S05** ROS 2 Runtime | O | track core | CODE/RESEARCH: executors, QoS, callbacks. Measure message delay under two QoS settings. |
| **S06** Hardware Integration | O | track core | CODE/RESEARCH: drivers, timing, hardware interfaces. Design a mock driver with timeout and unit checks before hardware use. |
| **S07** Robot Safety | O | track core | CODE/RESEARCH: hazard analysis, limits, fault response. Define simulation tests for command timeout and invalid sensor data. Entry awareness; real hardware remains outside automatic quiz authorization. |
| **S08** System Identification | O | specialization | DYN: parameter estimation, excitation, model fit. Fit a damping coefficient and test it on a different trajectory. |
| **S09** Sim2Real | O | specialization | DYN: model mismatch, domain gap, validation. List parameter uncertainties and design a staged validation protocol. |
| **S10** ROS 2 Control | O | specialization | CODE/RESEARCH: controller interfaces, resource ownership, update loop. Use a mock interface to verify command limits and state consistency. |
| **S11** Advanced Simulation | O | specialization | DYN: differentiable simulation, batched worlds, solver settings. Compare solver settings against a fixed reference trajectory. |
| **S12** Advanced Robotics Software | O | frontier elective | CODE/RESEARCH: real-time design, composition, systems architecture. Trace end-to-end sensor-to-command latency and failure handling. |
| **V01** Digital Images | L+V+D | track core | DATA: pixels, array axes, color channels. Build a synthetic RGB image that catches row-column and channel swaps. |
| **V02** Image Processing | O+D | track core | DATA: filtering, convolution, sampling. Compare smoothing before and after downsampling a checkerboard. |
| **V03** Camera Models | O | track core | DATA: pinhole camera, intrinsics, projection. Project known points and inspect the effect of focal length. |
| **V04** Camera Calibration | O | track core | DATA: distortion, reprojection error, calibration. Separate calibration fit error from held-out reprojection error. |
| **V05** Feature Extraction | O | specialization | DATA: corners, descriptors, matching. Measure matching robustness under rotation and brightness changes. |
| **V06** CNN | O+V+D | track core | DATA: convolution, receptive field, weight sharing. Compute output size and receptive field for a small convolution stack. |
| **V07** Image Classification | O | track core | DATA: class prediction, augmentation, confusion matrix. Compare class-wise errors with a majority-class baseline. |
| **V08** Object Detection | O | track core | DATA: bounding boxes, IoU, precision-recall. Compute IoU by hand and inspect duplicate-detection handling. |
| **V09** Object Tracking | O | specialization | DATA: data association, motion model, identity. Compare nearest-neighbor association with a motion prediction. Compare provided detections/feature tracks with a learned-detector path. |
| **V10** Segmentation | O | specialization | DATA: pixel labels, mask metrics, boundaries. Compare per-pixel accuracy and class IoU on imbalanced masks. |
| **V11** Multi-View Geometry | O | specialization | DATA: epipolar geometry, triangulation, pose. Triangulate a synthetic point and inspect baseline sensitivity. |
| **V12** Depth Estimation | O | specialization | DATA: stereo disparity, scale, uncertainty. Analyze why small disparity errors grow at long range. |
| **V13** 3D Perception | O | specialization | DATA: point clouds, registration, 3D features. Register synthetic point sets and inspect outlier sensitivity. |
| **V14** Visual Representation Learning | O | specialization | DATA: visual embeddings, pretraining, transfer. Compare frozen embeddings under a held-out domain shift. |
| **V15** Vision Transformers | O | specialization | DATA: patch tokens, attention, spatial encoding. Calculate token count and discuss spatial-information encoding. |
| **V16** Video Understanding | O | specialization | DATA: temporal context, motion, video sampling. Compare frame-only and temporal baselines on an action ambiguity. |
| **V17** Visual Odometry & SLAM | O | specialization | DATA: pose estimation, mapping, loop closure. Analyze drift and distinguish relative error from global alignment. |
| **V18** Vision Foundation Models | O | frontier elective | DATA: pretraining scale, prompting, transfer evaluation. Test one model on a small held-out robotics distribution. |
| **V19** 3D Neural Representations | O | frontier elective | DATA: neural fields, rendering, 3D reconstruction. Compare novel-view quality with geometric accuracy. |
| **V20** Advanced Perception | O | frontier elective | DATA: multimodal perception, uncertainty, robustness. Design an evaluation suite for occlusion and sensor degradation. |
| **RL01** RL Fundamentals | L+V | track core | PLAN/DATA: agent, reward, return. Compute returns in a tiny navigation problem before training. |
| **RL02** Markov Decision Processes | L+V+D | track core | PLAN/DATA: Markov state, transition kernel, Bellman equation. Solve a two-state value equation exactly. |
| **RL03** Value Functions | O | track core | PLAN/DATA: state value, action value, advantage. Compare V and Q for a complete tabular example. |
| **RL04** Dynamic Programming | O | track core | PLAN/DATA: policy evaluation, policy improvement, value iteration. Implement synchronous value iteration and check its residual. |
| **RL05** Model-Free Prediction | O | track core | PLAN/DATA: Monte Carlo, TD learning, bootstrapping. Compare complete-return and one-step TD estimates on the same trajectories. |
| **RL06** Model-Free Control | O+V+D | track core | PLAN/DATA: Q-learning, SARSA, exploration. Contrast on-policy and off-policy updates in a cliff task. |
| **RL07** Function Approximation | O | track core | DATA: value approximation, projection, stability. Compare tabular and linear estimates on a small controlled MDP. |
| **RL08** Policy Gradient | O | track core | DATA: log derivative, policy objective, variance. Derive a two-action policy gradient with an independent numerical check. |
| **RL09** Actor-Critic | O | track core | DATA: critic, advantage, actor update. Inspect actor and critic errors separately in a tiny task. |
| **RL10** PPO | O | track core | DATA: clipped objective, on-policy data, KL change. Plot the surrogate for positive and negative advantages. |
| **RL11** Off-Policy RL | O | specialization | DATA: replay buffer, target network, off-policy correction. Compare target estimates with and without stale replay data. |
| **RL12** RL Experimental Design | O | track core | DATA: seeds, evaluation episodes, compute budget. Predeclare seeds, environment steps, and a held-out evaluation protocol. Introduce the minimal protocol before any costly RL training. |
| **RL13** Continuous Control | O | specialization | DATA: continuous actions, bounded policy, control cost. Compare action scaling and saturation under a fixed evaluation task. |
| **RL14** Reward Engineering | O | specialization | DATA: reward specification, shaping, side effects. Construct a reward loophole and an evaluation that detects it. |
| **RL15** Curriculum Learning | O | specialization | DATA: task difficulty, curriculum, distribution. Compare a staged schedule with a fixed distribution at equal budget. |
| **RL16** Domain Randomization | O | specialization | DATA: parameter randomization, robustness, coverage. Choose physically justified parameter ranges and evaluate held-out extremes. |
| **RL17** Imitation Learning | O | specialization | DATA: behavior cloning, demonstrations, distribution shift. Compare one-step imitation error with rollout failure. |
| **RL18** Offline RL | O | specialization | DATA: fixed dataset, support mismatch, conservative learning. Identify actions whose value estimates require unsupported extrapolation. |
| **RL19** Model-Based RL | O | specialization | DATA: learned dynamics, planning, model bias. Measure one-step and multi-step model error separately. |
| **RL20** Hierarchical RL | O | specialization | DATA: options, temporal abstraction, termination. Define one reusable skill with initiation and termination conditions. |
| **RL21** Safe RL | O | specialization | DATA: constraints, risk, safe exploration. Evaluate constraint violations separately from average return. |
| **RL22** Multi-Agent RL | O | frontier elective | DATA: joint policy, nonstationarity, credit assignment. Separate centralized training assumptions from decentralized execution. |
| **RL23** Advanced Exploration | O | frontier elective | DATA: intrinsic reward, uncertainty, information gain. Compare novelty bonuses with task return and inspect distraction. |
| **RL24** Meta-RL | O | frontier elective | DATA: task distribution, adaptation, meta objective. Separate training tasks from held-out adaptation tasks. |
| **E01** Sequential Decision Making | O | specialization | PLAN/DATA: decision horizon, belief, closed-loop behavior. Compare a greedy choice with a multi-step plan. |
| **E02** Planning Fundamentals | O | specialization | PLAN/DATA: search, heuristics, state transitions. Implement a small A* search and test heuristic admissibility. Discrete search first; do not claim collision-aware motion planning from A* alone. |
| **E03** Planning Under Uncertainty | O | specialization | PLAN/DATA: belief state, POMDP, information gathering. Compare acting immediately with taking a clarifying measurement. |
| **E04** Robot Skills | O | specialization | PLAN/DATA: skills, preconditions, termination. Define a simulated reaching skill and its failure conditions. |
| **E05** Task Planning | O | specialization | PLAN/DATA: symbolic state, operators, task constraints. Plan a pick-place sequence and identify an impossible precondition. |
| **E06** Task & Motion Planning | O | specialization | PLAN/DATA: symbolic-geometric coupling, feasibility, motion constraints. Reject a symbolic plan whose grasp pose is unreachable. Requires the candidate R16 motion-planning bridge for the revised scope. |
| **E07** Imitation-Based Robot Policies | O | specialization | PLAN/DATA: demonstration policy, multimodal actions, rollout shift. Evaluate recovery from states missing in the demonstrations. MLP behavior cloning is a valid baseline before transformers. |
| **E08** World Models | O | specialization | PLAN/DATA: latent dynamics, prediction, planning. Compare prediction quality with downstream control usefulness. |
| **E09** Object-Centric Representations | O | specialization | PLAN/DATA: objects, relations, compositionality. Test whether a representation tracks an occluded object identity. |
| **E10** Vision-Language Models | O | specialization | PLAN/DATA: vision-language alignment, grounding, prompt sensitivity. Compare two prompts on a fixed set of spatial relations. |
| **E11** Diffusion/Flow Action Policies | O | frontier elective | PLAN/DATA: action diffusion, flow matching, multimodal policy. Compare multimodal action generation with deterministic regression. |
| **E12** Vision-Language-Action Models | O | frontier elective | PLAN/DATA: vision-language-action, grounded control, generalization. Evaluate an instruction on held-out objects and environments. |
| **E13** Long-Horizon Robot Learning | O | frontier elective | PLAN/DATA: long-horizon planning, skill composition, error recovery. Measure success per stage and design a recovery policy. |
| **E14** Embodied Reasoning | O | frontier elective | PLAN/DATA: grounded reasoning, causal structure, execution feedback. Test whether an inferred plan remains valid after a scene change. |
| **E15** Advanced Embodied Intelligence | O | frontier elective | PLAN/DATA: generalization, autonomy, research evaluation. Design a benchmark with unseen tasks and explicit failure reporting. |
| **RS01** Scientific Reasoning | L | starter option | RESEARCH: hypothesis, falsifiability, controls. Write a controlled comparison with a clear falsifier. |
| **RS02** Experimental Design | O | just-in-time foundation | RESEARCH: independent variable, confounding, ablation. Use a factorial ablation to separate two proposed improvements. |
| **RS03** Statistical Inference | O | just-in-time foundation | RESEARCH: confidence interval, hypothesis test, effect size. Report an effect size and interval rather than only a p-value. |
| **RS04** Experimental Reproducibility | O | just-in-time foundation | RESEARCH: protocol, artifacts, replication. Re-run a figure from raw measurements and a locked environment. |
| **RS05** Error Analysis | O | just-in-time foundation | RESEARCH: failure taxonomy, residuals, subgroup analysis. Group failures by condition and test one proposed explanation. |
| **RS06** Paper Reading | O | just-in-time foundation | RESEARCH: claims, assumptions, evidence. Write a claim-evidence-assumption table for one paper. |
| **RS07** Scientific Writing | O | specialization | RESEARCH: argument, figures, limitations. Rewrite a result paragraph with a concrete metric and uncertainty. |
| **RS08** Literature Review | O | specialization | RESEARCH: search strategy, comparison matrix, research gap. Build an inclusion rule and compare assumptions across three sources. |
| **RS09** Research Software | O | specialization | RESEARCH: experiment software, versioning, artifact integrity. Link one result to a code revision, config, and data hash. |
| **RS10** Advanced Research | O | frontier elective | RESEARCH: research question, novelty, reproducible contribution. Propose a minimal study with baselines, risks, and a falsifier. |

The starter column is a menu, **not ten compulsory modules before every project**. Foundations move just in time according to a concrete objective. Some profiles combine methods; a final per-topic PASS contract still needs an actual artifact, oracle, rubric and delayed/transfer prompt. The additional candidate **R16 Motion Planning** is separate from these 169 baseline rows and remains subject to debate and human approval.

### 12. Round 1 validation and handoff

- All 169 original IDs occur exactly once in the coverage matrix; candidate R16 is explicitly separate.
- The source curriculum passes the existing content/DAG validation. The explicitly proposed graph projection independently passes reference, duplicate-edge and cycle checks.
- Four objective items, fixed first-position C answers, 27 h 40 min of declared time and the current coverage counts are directly measured from files.
- Claims about improved efficiency, reviewer reliability, ideal time budgets and learning outcomes are labeled hypotheses/estimates. No clinical, safety, research or mastery certificate is implied.
- No production files, historical contracts or progress were edited. No Claude review was read in this round.
- Ready for Claude Round 1. The next Codex round will explicitly ACCEPT, REJECT or MODIFY completed peer proposals, without overwriting this round. Final synthesis will only be published after both participants complete Round 4.

## Round 2 — Response to Claude Round 1

Read: Claude's completed Round 1 (`completed_round: 1`), including claims C1–C10, the 180-row matrix and foundational blueprints. I did not treat a draft later round as completed evidence. This response preserves all of Codex Round 1; it does not implement either graph.

### 2.1 Decisions on the ten major claims

| Claude claim | Decision | Reason, benefit, cost and remaining uncertainty |
| --- | --- | --- |
| C1: assessment validity first | **ACCEPT the priority; MODIFY the default form** | We independently found the same narrow constructs and coarse score grid. The fixed first-option answer for all C gates strengthens this finding. But a universal 12-item/4-C/4-M form is not validated and recreates artificial math in tooling/research. Pilot objective coverage and false-positive/false-negative behavior by knowledge type. More items cost learner and author time; they do not by themselves establish independent reasoning. |
| C2: spine, tracks and capstones | **ACCEPT tracks/capstones; REJECT a compulsory 540-hour common spine** | Your matrix does contain 54 spine rows totaling 540 hours. Requiring all of them before every track reinstates the front-loading we are trying to remove. A classical planning learner need not first finish deep-learning training; a robot-software learner need not pass all Kalman/LQR derivations. Keep that spine as a catalog or an optional comprehensive program, with goal-specific entry/readiness from the beginning. The 17–26% figure compares two unmeasured hour models and changed targets/scopes: call it a budget scenario, not achieved or equivalent-outcome efficiency. |
| C3: separate readiness from mastery | **ACCEPT the distinction; MODIFY its representation and scale** | Use a few reusable capability checks mapped to the actual next activity, not a new mandatory exam for every edge. Your 3–8 mappings over ~190 hard edges create 570–1,520 item–edge associations before deduplication; these need not be unique questions, but maintenance is substantial. Start with selected high-impact edges and safety-critical gaps. Expiry is a hypothesis needing calibration, not a universally justified clock. |
| C4: missing robotics core, eleven additions | **ACCEPT the gaps; MODIFY granularity and scheduling** | Spectral/numerical readiness, motion planning, sensors/timing, trajectories, manipulator control and mobile localization are defensible needs. Not all need new mandatory nodes at once. Information theory and nonlinear least squares are just-in-time by application; HRI must remain visible to the cognitive track, not be dismissed because current models favor manipulation. Compare separate-node vs scoped-sublesson costs and pilot foundational delivery first. Our provisional R16 identifiers collide: yours is Sensors, mine Motion Planning. **No numeric new ID is agreed**; use semantic candidate names until a final mapping is chosen. |
| C5: remove 11, merge 36, defer 19 | **MODIFY substantially** | Presentation consolidation is useful; evidence consolidation is not automatically legitimate. Several supposedly unassessable catch-alls already have concrete overview tasks (CPP12 interface/ownership analysis, PY10 lazy iterator/lifetime, S12 latency/failure handling, T08 restart/artifact contracts). Rescope/defer rather than declare them inherently unassessable. Retain all 169 original evidence identities and their historical scopes, even when the navigation groups them. The proposed merge list needs objective-level tests, not only shared videos. |
| C6: PoE as the spatial path, no full DH detour | **ACCEPT a preferred spatial extension; REJECT it as an early universal gate** | A common screw/twist/PoE representation is coherent for spatial manipulation [S4]. A planar-first progression and a compact DH-reading/conversion note are reasonable. Requiring robust `exp6/log3` near π before a beginner can do pinhole projection or a 2R example is excessive. Preserve a small frame/transform scope early; deeper spatial Lie calculations can have separate readiness. No comparative learning study here establishes PoE as the universal optimum. |
| C7: new machine-checkable types make M/I/T “real” | **ACCEPT bounded checks; REJECT the broad implication** | Matrix/expression checks, randomized cases, error localization and mutation tests can improve scoped procedural/implementation evidence. Numeric equivalence at finitely many points is not a derivation; ordered steps measure reconstruction/recognition, not unrestricted proof. Local tests are inspectable, so “hidden” must mean not shown before this attempt, not tamper-proof. Machine checks may support defined parts of T, but open transfer/modeling judgments remain unverified without appropriate human review. Preserve C10 consistently. |
| C8: longer, skill-aware review | **ACCEPT investigating a longer tail; MODIFY the workload claim** | At 31 current diagnostic topics, the hypothetical six-minutes/every-21-days load is 8.86 minutes/day, not 48.29; the latter assumes all 169 future topics are active. A 115-topic annual schedule gives 0.315 topic events/day, but per-skill review of, say, 345 skills gives 0.945 events/day. Failures, new learning, integration tasks and variable duration change these values. Neither the 30–45 minute saving nor the exact 1/3/7/21/60/150/365 sequence is established. The Cepeda paper supports dependence on desired retention horizon, not that particular schedule. |
| C9: workflow varies by knowledge type | **ACCEPT; MODIFY rigid budgets** | A Git debugging task need not contain a fake mathematical derivation; mathematical/dynamical models benefit from prediction and visual manipulation. Preserve video as an accessible optional entry and respect learner preference. Reject a blanket 300–500-word cap or universal activity percentages: captions may be short while a necessary rigorous derivation is longer. Measure whether the material supports independent performance, not whether it meets a prose quota. |
| C10: human boundary for open-ended certification | **ACCEPT** | Our shared boundary: novel transfer and reproducible critique require actual reviewed evidence; AI/self-review remains provisional. Low availability of reviewers is a product limitation to disclose, not a reason to promote model confidence into verified mastery. This includes our own debate and final synthesis. |

### 2.2 Concrete corrections to statistical and assessment arguments

1. **The binomial arithmetic is an illustration, not evidence that twelve is right.** Under independent identical item success probability p=.9, 4/4 succeeds with .6561 and ≥10/12 with .8891300. I independently reproduced these. But the proposed separate dimension/critical gates alter those probabilities: for a 6-C/6-M form with ≥80% in each, at least 5/6 is required twice, yielding **.7845265**, before critical-item constraints. Real errors are correlated and items vary in difficulty. Do not advertise .889 as the actual proposed form's reliability.
2. **Three options are not three distractors.** The Rodriguez title/abstract explicitly concerns three-option items—one correct option plus two distractors—not “3 or more plausible distractors.” [R2-S1] Use effective misconception-based alternatives when useful, with a separately calibrated coverage criterion; banning every binary conceptual judgment is not itself supported by that source.
3. **Keep worked examples, separate the assessed task.** The learner should not be asked to copy a lesson solution as fresh evidence. But banning solved examples broadly conflicts with novice guidance and our shared fading-support approach. Keep explanations/worked cases and use materially different assessment tasks, representations or assumptions. An inspectable local source tree cannot guarantee that an item was never seen; scope its independence claims honestly.
4. **A 24-hour lock after every failure is not established by the cited retest meta-analysis.** Allow immediate corrective practice. Decide separately when a fresh independent assessment is meaningful; report the assistance/exposure context. The exact delay is a proposed policy to pilot, not an empirically justified constant for every subject.
5. **“No item kind can test derivation” is too broad.** Current `short` responses can request a derivation (R06 already does); the missing piece is a valid reviewer/verifier and a scoped evidence policy. Existing knowledge-type metadata also changes assessment guidance and excludes implementation/design from objective auto-grading (`isObjective` in `lib/assessment.ts`). The fact that all 31 v1 forms retain the same shape is valid; the claim that types have no effect anywhere is not.
6. **Finite numeric checking needs domains and adversarial cases.** For example, x/x and 1 agree away from zero but have different domains; absolute value and x agree on positive samples. Units, side conditions, matrices, nonsmooth boundaries and the learner's reasoning cannot be inferred from a few sampled outputs. Call this a checked expression/procedure, not verified unrestricted derivation. A generative test bank needs schema/version/seed provenance and oracle validation; it is not a cheap substitute for authoring.

### 2.3 Scientific details that need more precise PASS criteria

- **LQR:** replace an unqualified “requirement for controllability” with the appropriate finite-/infinite-horizon conditions. Infinite-horizon stabilization can work for a stabilizable system that is not fully controllable, with the relevant cost/detectability assumptions. A simple counterexample is continuous A=diag(−1,1), B=(0,1)ᵀ, Q=I, R=1: the unactuated first mode is already stable. Do not fail a learner for recognizing this distinction. [R2-S2]
- **Kalman consistency:** “NEES inside a stated interval” must specify whether it is a single draw, ensemble/average test, coverage criterion or multiple-testing procedure, with truth available in the synthetic experiment. If twenty independent draws each have a 95% interval, the chance at least one falls outside is **1−.95²⁰≈.6415**. “Every sample must be inside” would wrongly fail many correct implementations. Also require numerical covariance/innovation checks and model-mismatch analysis; a statistical pass cannot by itself establish correctness.
- **PPO debugging:** lack of advantage normalization is not universally an algorithmic bug; it is a common implementation choice/heuristic. Test unequivocal defects (wrong terminal/truncation bootstrap, wrong sign/ratio, stale or incorrectly recomputed old-policy probabilities) separately from ablations of recommended heuristics. The official algorithm description distinguishes the clipped objective from implementation details [R2-S3]. IQM/bootstrap benchmark reporting is useful when appropriate, but should not be a compulsory ornament for every one-task, CPU-limited learning exercise.
- **Learning evidence ≠ framework brand:** ML06/V06 do not mathematically require PyTorch. A tiny training loop/CNN can be implemented with NumPy; other tensor frameworks exist. Make PY06 a hard prerequisite for a *PyTorch-specific project*, or name a framework-neutral tensor/autodiff readiness capability. A default tool is useful without becoming a universal theory gate.

### 2.4 Graph and merge review

I reconstructed Claude's positive-hour live matrix, resolved MERGE aliases, excluded REMOVE/REMAP rows and zero-hour registry entries, and retained nonzero-hour DEFER entries. That independently produces **115 live nodes, 189 hard edges, no dangling references, duplicate edges, self-edges or cycles**. Your text reports 190 hard edges. This one-edge discrepancy may be a representation rule; publish a canonical edge list or state the rule before treating 190 as reproduced. The 180 rows include all 169 original IDs exactly once plus eleven candidates. Structural validity is encouraging; it does not make every prerequisite necessary.

Changes I support:

- E02 should not wait for RL/continuous control merely to do A*. R04 can start without full rank/least-squares mastery. Safety should be upstream of S06. S05's Python route should not require C++.
- **Numerical IK** requires Jacobian/linear-solve readiness. Do not hard-gate an initial analytic planar IK problem on every advanced space/body Jacobian skill. R05 needs explicit analytic and numerical subscopes.
- C13-before-C11 is defensible when C13 teaches the optimal-control/trajectory-optimization foundation that MPC then repeatedly solves. Keep finite-horizon LQR and constrained numerical optimization readiness explicit; advanced optimal-control theory need not all precede a basic MPC experiment.

Changes I challenge:

- **RL11 → RL10** makes PPO mandatory before off-policy control because actor–critic was merged into PPO. SAC needs actor/critic and off-policy foundations, not mastery of PPO clipping. Preserve a reusable actor–critic competence, whether or not its page is grouped with PPO.
- **E08 → RL10** makes generic learned-dynamics/planning work depend on PPO. A simple learned model plus shooting/CEM/MPC is a counterexample. Require the policy-optimization route only for a Dreamer-like extension that actually uses it.
- **R03's expanded scope → V03:** merging elementary M12 geometry into R03's spatial exponential/logarithm implementation risks making camera models wait on mechanisms/physics and near-π log handling. Keep an elementary frame-mapping entry scope; it need not certify the advanced scope.
- **V08+V10:** boxes/instance detection and dense segmentation may share infrastructure, but their output spaces, annotation costs, failure modes and pixel/instance metrics differ. A common project is acceptable; a single undifferentiated PASS is not.
- **C02+C04, C07+C06, RL05+RL06:** integrate demonstrations but preserve distinct dynamic-system vs controllability/observability, estimator principles vs Kalman assumptions, and fixed-policy prediction vs control objectives. Sharing one video is weak evidence of curricular equivalence.
- **S07 still requires R09 in your projection.** Elementary hazard awareness should be visible before actuator mastery, while quantitative hardware risk analysis and actual permission to use hardware remain later requirements. I prefer an ungated awareness scope plus explicit safety readiness for physical projects.
- **E07 automatically promotes diffusion/ACT:** these are valuable robot-learning specializations, not a universal successor to basic BC for every learner. Preserve a low-dimensional supervised baseline and defer expensive variants according to the chosen task/budget. “Mainstream” is not a mathematical prerequisite.

**Alias integrity is a hard boundary.** A v1 M12 pass supports its original elementary transform scope; it cannot automatically become a PASS for a new R03 requiring `exp6`, near-π `log3`, twists and adjoints. Likewise, old C02 evidence does not establish every new C04 outcome. A presentation alias may expose old records, but it must retain original ID, version, scope and assistance; new broader verification requires the missing evidence. Otherwise the plan violates the brief despite preserving JSON records.

### 2.5 Corrections to my own proposal

- I accept Claude's emphasis on explicit trajectory-generation, sensor/timestamp literacy, manipulation-control and mobile/localization outcomes. Round 1's single new-node option was a deliberately minimal hypothesis, not evidence those other outcomes are unimportant. We should compare a few new units with clearly scoped extensions to existing IDs before finalizing the number of new nodes.
- My E04 proposal retained E01/MDP reasoning even for deterministic skill/state-machine exercises. That is more restrictive than necessary. A small Python state-machine/test contract can precede stochastic decision-making. MuJoCo is also a tool-specific requirement, not necessary for every skill-contract exercise; reaching-control and learned-option extensions add their actual dependencies.
- My statement about checked primary pages should not be read as a claim that every external source's full text was available. Both official ROS tutorial URLs were subsequently confirmed HTTP 200; the AAAI article's direct HTTP retrieval failed once, though its primary abstract/record and the authors' alternative RL-evaluation sources remain identifiable. No inference about global learner access follows from either result.
- My new-ID placeholder R16 conflicts with yours. I withdraw any claim that this numeric label should be reserved for motion planning. The semantic proposal is retained; the final document must show an explicit candidate-ID mapping and revalidate the combined graph.

### 2.6 Questions requiring a response, not forced agreement

1. Will you replace “everyone needs the 540-hour spine” with goal-specific early entry, or defend a clearly bounded comprehensive-program interpretation without calling it the universal starter path?
2. Will you retain all original 169 skill/evidence identities and require missing evidence for expanded merged scopes, rather than inheriting a broader PASS through aliases?
3. Which of the 36 merges remain actual competency merges after distinguishing presentation grouping from scoring? In particular, what justifies making PPO a hard gateway to SAC or generic model-based planning?
4. Will you qualify the twelve-item reliability calculation, remove the unsupported universal 24-hour lock, and separate three options from three distractors?
5. Will you replace blanket “hidden tests” claims with transparent, bounded, versioned, locally inspectable checks and retain human review for open M/T judgments?
6. Can you provide the exact live-graph edge recipe, clarify the 189/190 discrepancy, and model review load by **active skills**, not a mixture of topic and skill counts?

New checked sources for this round: [R2-S1: Rodriguez 2005 publisher abstract](https://doi.org/10.1111/j.1745-3992.2005.00006.x); [R2-S2: MIT LQR notes](https://underactuated.csail.mit.edu/lqr.html); [R2-S3: official PPO algorithm description](https://spinningup.openai.com/en/latest/algorithms/ppo.html); [R2-S4: Cepeda 2008 publisher abstract](https://doi.org/10.1111/j.1467-9280.2008.02209.x). Claims derived algebraically above are illustrations/counterexamples, not measured CoreLab learning outcomes. No production files were changed.

## Round 3 — Response to Claude Round 2

Read: Claude's completed Round 2. The rounds crossed in time: some issues raised in my Round 2 were already independently corrected in yours. I acknowledge those corrections rather than continuing to attack withdrawn positions. Our remaining differences concern implementation scale, objective boundaries and what to prioritize—not whether to preserve historical evidence.

### 3.1 Agreements and changes to my own position

**ACCEPT** your withdrawal of the compulsory 540-hour spine, deletion of eleven original identities, broad alias-based credit, headline savings percentages and universal PoE. **ACCEPT** separate applicability of C/M/I/T in future contracts, short novice diagnostics, scoped M01 precalculus and M05 integration bridges, M08 Bayes computation, M09 covariance, a minimal experimental protocol before training, and smaller visualization pilots. These require future human-approved work; none is implemented here.

I also accept your criticism **D3**: my Round 1 matrix was an inventory, not sufficient prioritization. In particular, `track core` for the original P0 R10 did not mean that a software/ML learner should do mechanical-design verification. I now explicitly **DEFER R10 outside a mechanical-design/hardware load-case path**. Its original ID and evidence remain intact. The same principle applies to broad advanced topics: expose a concrete objective when a project needs it, rather than remove its identity.

### 3.2 Direct answers to D1–D6 and your questions

**D1 — More than one missing outcome is real: ACCEPT; not eleven new mandatory gates.**

My minimal-node hypothesis was too conservative as an implementation recommendation. An explicit manipulation trace is:

1. frame/kinematic model → an IK solution;
2. collision-free configuration-space path → a time law with velocity/acceleration limits;
3. a declared joint/task-space tracking controller → measured tracking error, input limits and failure behavior;
4. for contact/grasping, suitable dynamics/force/impedance knowledge plus contact assumptions and grasp feasibility;
5. held-out scenarios, fault injection, safety constraints and reviewed interpretation.

The current overview inventory does not deliver all of those. Hiding time parameterization and impedance control inside a newly enlarged R07 would recreate the scope problem. I therefore **ACCEPT distinct candidate Trajectory Generation, Motion Planning and Manipulator Control units** on the manipulation path. Mobile kinematics/localization also needs explicit outcomes on a mobile path. No-contact trajectory tracking can be an earlier integration milestone; contact-rich pick-and-place is a later capstone, not a universal beginner assignment.

For discussion of a staged release, use these **seven candidate additions**, adopting your provisional IDs to remove our collision:

| Candidate | Decision and entry scope | Trade-off |
| --- | --- | --- |
| M17 Spectral Methods & Stable Least Squares | ACCEPT a separate readiness/evidence identity; eigen/SVD distinctions, conditioning and pseudoinverse/stable solves. | Avoids overloading an old narrow M04 pass. Do not require implementing a production SVD algorithm from scratch. |
| R16 Sensors & Measurement | MODIFY: short robotics-track unit on units, timestamps, bias/noise/calibration and schema checks with synthetic logs. | Useful distinct scope; not a mandatory survey of every sensor, and not a prerequisite to a purely scalar probability example. |
| R17 Trajectory Generation | ACCEPT: path vs trajectory, bounded timing, derivative continuity/limits. | A real missing capability; choose joint-space examples before a general optimization course. |
| R18 Motion Planning | ACCEPT: E02 discrete search plus elementary R03 geometry; FK is required for the arm-planning extension. | Distinguish rigid-body and articulated collision models, not one unnecessary FK gate for every 2D planner. |
| R19 Manipulator Control | ACCEPT: scoped tracking/effort limits first; dynamics and contact/impedance extensions require their own assumptions. | Do not claim simulation success authorizes hardware use. |
| R20 Mobile Robots & Localization | ACCEPT on the mobile path: kinematics/odometry and a scoped belief/localization experiment. | A particle-filter route need not first master every Kalman implementation; make the estimator variant explicit. |
| E16 Robot Data & Demonstration Quality | ACCEPT as a robot-learning path option: temporal alignment, provenance, splits, schema and quality checks. | Using an existing licensed dataset does not require owning teleoperation hardware; collection and QA are separable objectives. |

These are proposed allocations only, not approved changes. **DEFER separate new IDs** for information theory, frequency/sampling, nonlinear least squares, PoE and HRI until a selected objective justifies a distinct unit. Their essential subskills must still be present (e.g., KL for the relevant policy objective, aliasing/delay for sampled sensing/control, nonlinear solve readiness for calibration). Lie/PoE material can be scoped through existing M15/R03/R04; HRI/privacy/safe interaction remain explicit in S07/E14 and a visible research pathway. If later authoring shows those scopes cannot remain clear, a new ID is preferable to pretending an old pass covers them. The proposed 176-identity scenario is a staging choice, not an empirically optimal count.

**D2 — Separate spectral identity: ACCEPT as a practical migration choice.** A versioned M04 scope manifest could also solve the problem, so a new ID is not logically the only honest solution. But given current topic-level labels, M17 is a pragmatic way to avoid assuming old rank/solve evidence establishes spectral readiness. The same scope rule must apply to expanded existing R03/C07/etc.; new IDs alone do not solve evidence validity.

**D3 — The first 100 authoring hours: a bounded pilot plan, not twelve finished courses.** Assumption: one maintainer, existing reusable components, a Python/geometric-robotics entry path, no production v2 release without approval. Allocate:

| Authoring hours | Deliverable | Limit/stop rule |
| --- | --- | --- |
| 0–8 | Objective/evidence inventory for M02, PY01 and the first frame/FK milestone; pin source/contract versions and calibrate example rubrics. | No new mastery claims merely from writing a manifest. |
| 8–32 | M02 pilot: a few validated variant templates, expanded dot/norm/projection contract, independent oracles and failure explanations. | Preserve the old dot-only contract. Do not promise three complete 12-item banks in this budget. |
| 32–52 | PY01 pilot: return/aliasing/contracts plus a fresh task and test-design artifact; safe local validation and key/history compatibility plan. | Code correctness and test-design judgment stay distinct. |
| 52–64 | M01 diagnostic-selected algebra/trig/unit bridge with worked cases and fresh checks. | Do not turn four hours of learner estimates into an authoring-throughput guarantee. |
| 64–76 | M08 Bayes/base-rate task and a narrowly scoped M09 covariance bridge. | Not a complete statistics/inference course. |
| 76–88 | Elementary R03/R04 frame/FK milestone blueprint, model-convention bridges, source links and a small independently checked test set. | No claim that PoE, general dynamics or spatial manipulation is finished. |
| 88–100 | Editorial/assumption/accessibility checks, mutation checks, learner-pilot preparation and initial case observations. | Stop expansion when a core oracle or PASS rule is not trustworthy. |

RS01-style protocol and S07 simulation-only limits are embedded in the pilot artifacts. M05 integration, fuller M09/M11/M17 readiness, R06 verification, and the new planning/control units are the **next** authoring queue, not silently promised in these first 100 hours. These are effort allocations, not measured productivity. Seven-/21-day observations require calendar time beyond an uninterrupted work sprint. A different chosen goal changes the queue.

**D4 — R04 should extend beyond 2R: ACCEPT with staged claims.** Planar first, then spatial FK through labeled homogeneous transform chains, with tests against an independent implementation. Screw/PoE is valuable on the manipulation/Lie path, not required before basic camera-frame transformations. Invariants and source conventions matter more than the notation brand. A standard URDF-style chain does not require writing a numerically production-grade logarithm at π as an entry exercise.

**D5 — A pilot needs a starting form: ACCEPT; universal twelve-item policy: REJECT.** Compare a small explicitly scoped form with a somewhat longer one (twelve is a permissible experiment for a suitable math objective). Do not import a uniform four-M quota into Git, ownership or paper reading. My Round 2 calculations show why per-dimension/critical gates must be included in the actual pilot acceptance model. “Sequential testing” needs a specified stopping rule and validated item model before it can claim statistical confidence; otherwise it is just a useful adaptive practice heuristic. Keep ≥80% only where the future contract actually declares that rule, not as a scientifically proved competence threshold.

**D6 — Basic PID before full state-space mastery: ACCEPT.** C01 plus a declared scalar plant and elementary sampling/derivative prerequisites can support initial PID experiments. General stability analysis, delay/noise, multivariable methods and hardware use add their real readiness requirements. This is another reason to preserve C02/C04/C09 objective identities even when their teaching is integrated.

### 3.3 Edge-reason rule: accept the test, not an exhaustive three-word taxonomy

**ACCEPT** that a hard edge needs a concrete reason, and that helpful context/textbook order alone are not sufficient. **MODIFY** “only math/safety/tool can be hard”: procedural/data/schema requirements and evidence-validity preconditions can also be essential to the actual activity. For example, a train/test split protocol is necessary before making a held-out performance claim even if a neural network can be run without understanding it. A tool edge is hard only for the named implementation variant, not for every equivalent approach.

Apply the counterexample criterion to my own projection: deterministic skills need not require E01/MDPs; a NumPy teaching baseline need not require PY06; basic R18 rigid-body planning need not require arm FK. Preserve introductory vs advanced scopes. We need a small explicit selected-activity prerequisite set, not a gate for every detail that appears later in the same textbook chapter.

Your updated core intersection (5 topics/48 estimated hours) is a property of your selected leaves and edges. Adding a cross-cutting menu is reasonable, but **80–140 hours must not become a new universal waiting period before any useful work**. A beginner should receive a recommended default path with opt-out; I accept that a menu alone is insufficient guidance. A defensible default is units/functions as needed, vectors alongside Python, matrix/frame readiness, a small FK/prediction exercise, and testing/protocol skills embedded at the first artifact. Role-specific scope checks decide the next branch.

### 3.4 Pilot design: single-learner case evidence, not a curriculum RCT

**MODIFY** the proposed crossover. M06 vs M17 and C02 vs C07 are not exchangeable treatments: scope/difficulty differ, some skills are prerequisites, and learning one can improve the other. Learning cannot be washed out like a drug. Randomly assigning two different topics to two different lesson/assessment packages cannot isolate which change caused a result.

A smaller useful design is matched parallel task families **within a scoped skill**, record entry knowledge, counterbalance presentation order, separate practice from the held-out assessment, and use fresh predeclared delayed tasks. Keep the final evidence requirements comparable across conditions; changing content scope and test difficulty simultaneously confounds the outcome. Log intervening practice and assistance, including a seven-day retrieval's effect on the 21-day outcome. Where possible, use an independent blinded rubric reviewer; otherwise report openly that interpretation is unreviewed.

With one learner, report raw cases, time, errors and observed transfer limitations. Do not infer a general optimal curriculum, population effect or a validated false-positive rate. The “twice as long without a better delayed result” rule can be a practical review trigger, not a significance test. Community data would require a separately approved, consented protocol; no telemetry or shared collection is authorized here.

### 3.5 Single-user L3/L4 and the remaining disagreements

With no qualified reviewer, show the current verified level and an **unreviewed transfer/research artifact / needs external reviewer** state. L3/L4 verification remains unavailable until the defined review actually occurs; the learner can still study, use the registry and record provisional work. A framework or AI reviewer cannot certify itself. Preserve old original IDs, contract versions, assistance, signatures and evidence scopes without assigning broader credit through study-unit grouping.

Remaining disagreements for Round 4:

1. E11 is valuable for a **modern visuomotor-imitation specialization**, but not a universal requirement for every robot-learning goal. An evaluated low-dimensional BC/other policy can be appropriate without diffusion/ACT. Citations and a library's supported methods do not establish a universal prerequisite.
2. I still reject PPO as the generic prerequisite of SAC or learned-model planning, and full spatial Lie/log implementations as a prerequisite of elementary camera geometry.
3. I favor a small number of scoped pilots and an explicit evidence manifest before broad new item engines, expiry state, per-edge banks or sixteen visualizations.
4. The final artifact must distinguish baseline IDs, presentation groups, scoped evidence and candidate new IDs. Its graph should use one explicit edge list; chapter-order reasoning and an unexplained 189/190 discrepancy are insufficient for reproducibility.

I have responded to your completed Round 2. My completed Round 2 separately details MCQ options vs distractors, dimension-gated binomial arithmetic, inspectable tests, finite numeric equivalence, LQR conditions, NEES acceptance and PPO heuristic-vs-bug distinctions; those are concrete checks for your next response rather than silently agreed points. No production changes or historical evidence edits were made.

## Round 4 — Response to Claude Round 3 and final position

Read only Claude's completed Round 3 for this response. Its status was already 4 when checked after the user-requested 20-minute pause, but its Round 4 is reserved for synthesis after this publication. This is the fourth and last debate round. Recommendations remain proposals; no production curriculum, assessment, progress or evidence is changed.

### 4.1 Decisions and answers to your five questions

**Q1 — MODIFY the new-unit rule.** Separate assessment scope and capstone demand are useful tests. Requiring that a skill cannot fit an existing ID without broadening its PASS is too strong as an identity rule: *any* new material under a broad heading could satisfy it, although a versioned contract under the same topic preserves the old, narrower claim. Integration under M05 and numerical least squares under M11 are counterexamples. Conversely, demanding two dependents would wrongly exclude a necessary skill for one valuable capstone; your capstone exception fixes that part. Use scope coherence, learner navigation, independent remediation needs and maintenance cost together. Neither a new ID nor reuse of an old ID may confer broader credit on old evidence.

ACCEPT seven provisional additions from my Round 3 (M17, R16–R20, E16), as an outcome inventory and staged proposal, not seven immediately commissioned lessons. HOLD M20 nonlinear least squares, R21 twists/PoE and E17 HRI as standalone IDs pending scope review. Their needed material must still have a named home: M11/V04/V17, M15/R04/R06, and S07/E14 respectively. ACCEPT withdrawal of the separate Signals node; C09 must teach aliasing, delay and filtering rather than merely mention them. Cognitive Robotics needs an explicit research path even if its assessment remains reviewed and provisional. Absence of a new HRI ID is not permission to omit interaction, uncertainty, shared control or grounding.

**Q2 — ACCEPT M08 precision defect; MODIFY two details of the item audit.** I inspected `content/assessments/M08.v1.json` and `lib/engine.ts`: JavaScript `Number` rejects `1/3`, and absolute tolerance 1e-5 rejects `0.3333` (error about 3.33e-5), while accepting `0.33333`. The prompt does not state precision. This can false-fail an otherwise correct form. Do not rewrite v1 evidence: author a corrected version with declared answer formats/precision and reviewed tolerance, or a bounded safe fraction parser if separately approved. No `eval`. ML02 q2/q3 omit the loss definition; ML05 q2/q3 omit L; RL02 q4 omits the wait reward. Those are real standalone-prompt ambiguities. R07's angle-reference omission is in **q2**, not q1; q1 is the mass-matrix choice. RL01 q4 explicitly says “under this lesson convention,” and zero terminal future value is a coherent convention: make that convention self-contained, but do not call its answer mathematically incorrect.

I have not independently audited all 124 answer keys. Your approximately 27 construct mismatches remain your expert judgment, not a reproduced count. I agree that counting passing tests is weak evidence of mathematical reasoning. An applicable-dimensions declaration must preserve C/M/I/T architecture without inventing arithmetic to force M onto every software topic.

**Q3 — ACCEPT the structural result, not every edge.** Reparsed all 180 rows with your stated recipe: **123 live study units, 201 hard edges, 34 soft edges, no missing live hard references, no hard cycles**. This reproduces your revised count. It is a *study-unit* projection; 57 rows not live as units still contain retained evidence identities or deferred candidates. It is not a replacement 123-topic evidence registry. The old 189/190 discrepancy is resolved and should not remain listed as an unresolved disagreement.

Semantic issues remain despite an acyclic graph:

- R04 text still says “Spatial PoE,” although 3.7 moves PoE to R21. Use transform-chain spatial FK as the baseline; label PoE an extension.
- T04's note still says “keep T04.v1 evidence as alias,” although 3.1 withdraws competency merges. Remove *alias* from implementation guidance: grouping shares navigation only; old IDs and scope stay distinct.
- R19 universally requires R21, although joint-space computed torque can be taught without a twist-space formulation. Make the PoE/twist capability conditional on the selected task-space derivation.
- R20 universally requires C07, although a particle-filter route needs Bayesian inference and sensor/motion models rather than a full linear-Gaussian Kalman PASS. State the selected estimator variant and its actual prerequisites.
- E16 universally requires S02 and RL17, but quality-checking existing demonstrations need neither that simulator nor prior imitation training. Split public-dataset QA from collection and simulator variants.
- ML06/V06's PY06 edge is defensible for a PyTorch-specific lab. It is not a framework-neutral mathematical dependency. A graph with only topic-ID AND edges cannot express your “another framework can satisfy it” claim. Keep that as a future capability policy, not current functionality.
- M17 appears only as a soft edge for several tasks that explicitly require spectral/least-squares understanding. It should gate the relevant scope (for example stability/poles in C04 and a stable least-squares V11 variant), not every introductory state-space activity. Scope-aware readiness is needed before a precise final graph can be claimed.

I will provide a single conservative, explicit 176-identity planning DAG in the synthesis, retaining v1 edges except listed replacements, and separately describe conditional capabilities. It is a validated projection, not a complete optimal graph or an implemented recommender.

**Q4 — MODIFY authoring order.** My concrete 100-hour budget is already in Round 3. Your newly demonstrated M08 precision and ambiguous prompts deserve the first defect budget. Prefer a small, versioned contract pilot over a 30–40-hour general item-kind/readiness engine before any pilot. Share the assessment manifest and an applicable-dimension design, but implement only what selected objectives need. Adjust the first eight hours toward defect specifications and reviewed v2 prompt/tolerance examples. Then strengthen M02/PY01, write M01's readiness bridge, and author a small M08/M09 bridge plus R03/R04 frame task. M05 integration follows before any ODE promise; it is not optional merely because it falls outside 100 hours. All hour allocations are estimates. Expert review may invalidate them; delayed 7/21-day learning observations necessarily extend calendar time beyond the authoring budget.

Preference criterion: time to a correct, bounded, independently assessable outcome; false-failure/false-pass risk; and pilot maintenance cost. If external review finds M02/PY01 already valid enough while M08/ML02/ML05 block real learners, reorder toward those defects. No claim that my allocation is empirically faster than yours.

**Q5 — ACCEPT failed readiness should change recommendations, MODIFY the policy.** A trustworthy failed *relevant* check is new evidence that should prioritize remediation and warn on affected downstream tasks while retaining historical attainment. Do not withdraw all readiness on a single ambiguous MCQ, a rounding failure, an A2-assisted practice error, or failure in an unrelated skill under a broad topic ID. Use criticality, scope, evidence quality, assistance and confirmatory checks. For an actual hardware safety failure, stop the affected hardware activity until reviewed; simulated practice can continue. For ordinary learning, offer remediation, a short confirmatory diagnostic and a clearly provisional exploration route. Clock-based expiry alone remains unvalidated. No automatic rewrite of signed evidence, no global demotion of old PASS.

### 4.2 What is now resolved

ACCEPT your corrections on option/distractor count; dimensional 4/4 thresholds; fixed 24-hour lockout; checked expression versus derivation; transparent local checks; finite/infinite-horizon LQR assumptions; ensemble NEES; PPO advantage normalization as an ablation; framework versus math dependency; and worked examples separated from assessed tasks. Earlier criticisms of these withdrawn positions are historical debate, not claims about your current position.

Your new review-load arithmetic is internally consistent under its assumptions. It still counts hypothetical skills rather than today's topic scheduler; S/I is only a steady-state approximation, and a two-minute event is not measured. No promised daily savings. Preserve topic review until a skill scheduler has enough evidence to justify the complexity. Budget review by active goals, overdue load and demonstrated gaps.

ACCEPT default guided starter with opt-out, spatial transform-chain FK, early safety awareness and retention of all original identities. REJECT mandatory E11 for every Robot Learning learner: a classical model-based or tabular path can meet a meaningful learning goal without diffusion policies. Put E11 in an explicit modern visuomotor-policy branch. If “RLL” is defined narrowly to mean that branch, label it clearly; that is a naming difference rather than an argument for a universal requirement.

### 4.3 Final assessment position and residual uncertainty

A PASS must name topic, objective set, contract version, assistance level, attempt/exposure context and verifier/reviewer. Pilot numerical values are not established psychometric standards. C/M coverage cannot be inferred from the same one-choice/three-number form across all subjects. Each critical objective needs at least two distinct probes as a starting *design* constraint, plus independently reviewed coverage; for a concrete pilot use five C and five M items where both dimensions apply, at least four correct per applicable dimension and all designated critical checks correct. This is a transparent starting blueprint, not a validated reliability guarantee; with small forms confidence is limited. Broader claims require additional task evidence. Error-driven practice and worked examples remain available after failure.

I tests must specify boundaries, wrong-implementation mutations and an independent oracle, not simply more random seeds. Locally inspectable signatures establish artifact provenance/integrity under the existing trust model, not unaided authorship or resistance to the local owner's modifications. A0 remains an explicit self-report, not a proof. Open derivation/design/transfer needs a qualified reviewer to become reviewed evidence; numerical equivalence is insufficient. Without that reviewer, keep the artifact unreviewed and do not award L3/L4. The present v1 T repeat-at-seven-days flag is retention evidence, not a verified unfamiliar transfer test.

No absolute optimality or measured time savings are claimed. The next artifact will reconcile both completed Round 4s, explicitly preserve disagreements, cover all 169 original IDs, validate one proposed DAG, and require human approval before implementation.

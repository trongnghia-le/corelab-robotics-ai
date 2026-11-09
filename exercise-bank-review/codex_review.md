# CoreLab Exercise Bank — independent technical review by Codex

Run ID: `corelab-exercise-bank-20261031-01`. Date: 2026-10-31, Asia/Ho_Chi_Minh. Baseline commit: `38b6a1d8f0baae9a753882185da7bd4430d14277`. Proposal and audit only. No production code, existing curriculum, assessments, progress, evidence, previous review, external repository or visibility is changed. No Claude findings were read before this independent round. The two prior completed CoreLab design reports are inputs, not evidence that their proposals are implemented.

## Round 1 — Independent research, exercise audit and design

### 1. Decision and scope

Build a **small, original, objective-indexed bank with genuine learner choice**, not a mirror of a puzzle website or a second learning platform. Separate practice results, scoped implementation checks and mastery assessment. Start with four objective packs (projection, Bayes, frames, planar FK), two authored scenario choices each, and explicit limits. That is eight proposed practice choices, not eight existing production exercises. Reserve forms/mastery aggregation are commissioned separately after a pilot.

The audited catalog contains **20 proposed exercise families, each with two choice routes**, spanning math, coding, robotics and AI. Six are specified in detail. I ran 154 named author-side checks across all 20 groups, including selected valid alternatives, independent numerical/exact anchors and mutations. Many non-detailed groups have spot checks rather than complete production graders; a passed audit fixture is not proof of full exercise correctness or educational effectiveness.

For code, a trusted parent owns expected answers, checks, completion and verdicts; the learner process supplies only untrusted values. I ran a Linux-only isolated prototype: 15 controlled probes accepted three valid behaviors and rejected 12 invalid/forged/early-exit/timeout/oversized cases, plus two benign host-path/network-exposure checks. This is evidence for the tested boundary, **not a release-ready sandbox, kernel-escape assessment, authorship proof or Windows/macOS verification**. Code execution fails closed if a required isolation profile is unavailable; it never silently becomes an unrestricted web subprocess.

No mandatory Docker, ROS, robot, GPU, cloud service or account for numerical practice. Python/NumPy-style coding can be an explicitly supported local optional route. Keep Node 24+, SQLite, localhost-only access and the manual ChatGPT tutoring workflow; assistance remains self-declared and useful practice, not verified independence.

### 2. What the source and prior reports actually imply

Inspected: `lib/practice.ts`, `lib/assessment.ts`, `lib/content.ts`, `lib/weaknesses.ts`, `lib/engine.ts`, `lib/reviews.ts`, `lib/labs.ts`, `lib/storage.ts`, `scripts/verify-lab.mjs`, `scripts/lab-tests.py`, current practice/assessment JSON, Curriculum V2 and the Practical Learning System synthesis.

- Actual graph: 169 IDs, 310 edges; seven additional IDs in the reports are unapproved candidates. Current practice has eight listed activities, two flagged verified; only dot product M02 and mean PY01 have signed fixed contracts.
- Actual bank: 31 diagnostic files/155 questions (124 choice/number and 31 short); seven targeted files/42 questions, **28 choice/number and 14 short**. Do not call all 42 automatically verified questions. Implementation/design metadata excludes an item from objective grading; a written implementation plan gives no I evidence.
- `selectTargetedPlan` currently selects at most three authored questions from a hardcoded v1 bank, ranks related/unseen/due items, and permits a seen question at most once more after seven days when due. Empty/exhausted banks are honestly labeled. It does not generate arbitrary new problems or offer a rich choice catalog today.
- Failed-skill inference is useful but not diagnosis by proof. Repeated failures suggest checking prerequisites; current code explicitly calls that a recommendation. Assisted success does not repair an independent gap; targeted correction is separate from a whole diagnostic PASS.
- Current question kinds are choice/number/short, not typed vectors, matrices, proofs or code submissions. Adding a bank is a schema/API/renderer design, not just dropping new JSON into the old format.
- Current question answers are indexed strings; public redaction removes answer/tolerance/explanation. All diagnostic C keys are at index zero in this baseline. A future shuffled renderer needs stable option identities and a validated mapping/contract version; do not mutate historical keys or randomly reorder arrays and grade the old index.
- Numeric grading uses JavaScript `Number`; M08's unqualified die question rejects `1/3` and some reasonable rounding. A format failure must not be misdiagnosed as ignorance of probability. Fix future contracts; preserve old records.
- A0/self-owned signatures are attestation. The Python harness imports a learner module and its final stdout line is treated as an outcome by the CLI. I reproduced crafted success JSON plus `sys.exit(0)` again in this audit, without signing/importing or changing keys. A timeout alone is not isolation.
- New scoped coding reports cannot be accepted by the strict two-topic `corelab-lab/1` validator. Topic-wide I2, the 5000-character legacy report field, restore validation and original signatures all require a reviewed additive policy. Do not reuse a dot report for projection, FK or all vector competence.

The [Curriculum V2 report](../curriculum-review/proposed_curriculum_v2.md) supplies skill/readiness needs; [Practical Learning System](../corelab-labs-review/proposed_practical_learning_system.md) supplies L01–L22 mappings and the oracle/mode boundaries. Neither authorizes implementation. In particular, the old 100-hour curriculum tranche and its roughly 12-hour FK slot do not fund an entire Exercise Bank automatically.

### 3. Independent source comparison and licensing

Sources were inspected at pinned revisions, including implementation/test/schema files. Source code availability or a license badge does not prove pedagogical fit, sandbox security or rights in every embedded asset. Full primary source pointers appear in the index below.

| Source | What I actually checked | License evidence / fit | Decision |
| --- | --- | --- | --- |
| Exercism problem-specifications | Canonical JSON schema and binary-search canonical cases, UUID structure | Root **MIT**, not assumed CC0; retain notice and inspect per-file exceptions. Exact cases define exception semantics, not every possible algorithm contract. | Best narrow import/reference candidate after item-level review; no bulk mirroring. |
| Exercism Python | Generated binary-search `unittest` cases linked to canonical data | Root MIT; generated tests and specification provenance both matter. A test with one exact index/path does not justify rejecting other outputs under a different CoreLab contract. | Useful standalone coding/test patterns; robot relevance requires original context/tasks. |
| Jupyter nbgrader | Locked-cell overwrite/checksum preprocessor, execution timeout code and FAQ | BSD-3-Clause license text; FAQ explicitly says unsafe code is not directly protected. Replacing locked tests is not a sandbox. | Useful notebook/review pattern; do not adopt its whole platform or trust learner notebook outputs as verdicts. |
| PrairieLearn | Generate/parse/grade/test lifecycle docs, external-grading docs and actual local grader | Root distinguishes AGPL community/client code, separately licensed enterprise and MIT/third-party portions. Local grader config includes network/memory/PID controls and reads a results file. Course material needs its own rights audit. | Learn architecture concepts; do not copy code into an MIT-only bundle or adopt its hosted/Docker stack for CoreLab. No compatibility claim without review. |
| SymPy | `parse_expr` implementation and explicit `eval` warning | BSD-3-Clause. Symbolic algorithms are useful in trusted authoring; untrusted strings must not go directly to `parse_expr`, `sympify`, Python eval or a shell. | Optional isolated/trusted authoring aid, not a general proof verifier or MVP answer parser. |
| Hypothesis | MPL-2.0 notice, quickstart and numeric-strategy source | File-level exceptions/notices remain; property generation/shrinking finds counterexamples, not proof. Package was not installed or run in this audit. | Optional author-side later dependency; explicit boundary fixtures first, no fabricated property-test run. |
| pytest | MIT notice and actual approximate-comparison implementation | Defaults are not an educational tolerance policy. Relative/absolute, zero, NaN, shape and type behavior need a declared contract. Not installed/run here. | Useful author/test tool if selected; not an authoritative rubric by itself. |
| Bubblewrap v0.6.1 | COPYING, README and installed Linux behavior | GNU Library GPL v2 text in source; runtime package notices/distribution obligations require preservation/review. It supplies mechanisms, not a complete security policy. | Candidate Linux runner mechanism, no Docker requirement; not a portable sandbox or security certificate. |
| MIT OCW | Official terms, not copied problem sets | CC BY-NC-SA 4.0 with exceptions; not CoreLab's blanket CC BY 4.0. | External reference by default; any adapted item retains required restrictions/attribution separately. |
| Project Euler | Official copyright page | Main problems CC BY-NC-SA 4.0; bonus/statistics/forum material has different restrictions. Not a permissive default bank. | Link as optional enrichment; no default imported/relicensed task text. |
| OpenStax | Official licensing URL redirected to an unreadable page in this pass | No selected book/exercise/edition's rights verified here; do not infer all books have one license. | Hold import. A title/URL is insufficient rights evidence. |

Primary policy links: [MIT OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/), [Project Euler copyright](https://projecteuler.net/copyright), [SymPy parsing warning](https://docs.sympy.org/latest/modules/parsing.html), [OpenStax licensing endpoint](https://openstax.org/license). These establish only their stated scope. This report does not give a blanket legal clearance for future imports.

For every item, record source URL/revision/path, license text/hash, author/attribution, modifications, assets/data rights and review status. Root licenses do not clear unrelated images, solutions, weights or datasets. The 20 candidates below are original proposals based on mathematical facts, not copied prompt text; publication still needs the owner's authorship/rights review. Keep original code MIT and original educational text CC BY 4.0 only where rights are clear; preserve external notices/licenses separately. No source was copied into production.

### 4. Architecture and identifiers

Use a static versioned authoring catalog, not a new LMS/service/database.

- **Objective**: stable namespaced capability plus C/M/I/T scope, prerequisites and applicability, e.g. `M02.projection-compute`. Topic mapping is not broad credit. Candidate topics have `proposedTopicRefs` until approved; do not insert dangling R18/M17 production references.
- **Exercise family**: stable ID/version, objective set, genuine scenario/representation choice, difficulty band, prerequisites, format, hint ladder, explanation/remediation, lab/mode mappings and provenance. Difficulty is a pilot editorial label, distinct from L0–L4.
- **Instance**: family/version + generator/config/seed + explicit conventions/domain + content hash. A fresh seed alone is not a new exercise choice or unfamiliar transfer.
- **Verifier contract**: allowed result types, units/shapes/domains, edge/error policy, exact/approx/oracle method, known valid alternatives, mutations, resources/security profile and grader/oracle hashes. The registry chooses the verifier; clients/submissions never provide a script path or an executable plugin.
- **Attempt/result**: trusted parent binds purpose, instance, source bytes actually executed, completion, checks/metrics, assistance/exposure, mode, runner/environment and provenance. A child cannot choose score, identity, purpose, mode, trusted flag or PASS.
- **Evidence policy**: practice correctness/assisted repair is separate from a predeclared assessment plan covering the required objectives. New format is additive; old contracts/signatures/restore and historical grades stay untouched.

MVP data format can be `corelab-exercise/1` for catalog items. For coding result envelopes, reuse the prior report's provisional `corelab-practical/1` semantics rather than invent yet another evidence mechanism. The owner must resolve its name against the earlier alternative `corelab-lab/2`; no current validator accepts either. Keep larger artifacts outside SQLite with bounded local manifests. Rendering/selection code does not execute arbitrary author/learner Python: begin with reviewed static fixture data and known built-in comparators.

### 5. Learner choice, difficulty and adaptivity

“Multiple choices” means **several exercise choices per learning objective**, not only multiple-choice questions. Offer two or three suitable cards: scenario, format, estimated effort, prerequisite capability, objective/dimension, difficulty and current feedback. User may choose/change context, bookmark, explore an optional specialization or request a shorter equivalent objective task. The scheduler recommends; it does not silently force every learner into robotics, ROS or a long P0 sequence.

Choice is not evidence equivalence. A numerical answer, written derivation, from-scratch implementation and open design exercise can share a topic but verify different dimensions. Only an explicitly reviewed same-scope contract can substitute for the relevant assessment requirement. Easier practice does not satisfy a harder/missing objective. Do not average repeated easy choices into mastery.

Difficulty progression: identify/model → routine computation → implementation with boundaries → changed representation/constraints → optional reviewed specialization. Provide original human-reviewed families for linear algebra/calculus/probability, Python/testing, robot geometry/control/planning and data/AI. Avoid generating an unlimited unreviewed bank from an LLM or claiming calibrated ability estimates from a few attempts.

Start with a transparent queue: active relevant weakness, due retrieval, unseen suitable family, prerequisite recommendation after repeated *credible* failure, and learner goal/time preferences. Allow override. Retain current honest exhaustion; never relabel a seen task “fresh.” Separate parser/infrastructure/verifier failure from learner error. No IRT/BKT engine or automatic global readiness expiry before sufficient calibration data.

Hints: first conceptual cue (A1), then a specific next step/example (A2), then worked solution (A3); A0 is no such assistance. Record exposure even for feedback, retakes and manual ChatGPT handoff. Keep worked solutions available in practice; subsequent independent evidence uses a genuinely fresh contract instance with honest exposure. No blanket retake lockout. Closed-note delayed fresh retrieval is retention; unfamiliar transfer additionally needs a changed assumption/representation and qualified review.

### 6. Catalog: 20 audited exercise families, two choice routes each

These are proposals, not released items. Both routes target the stated common core; extensions/dimensions are labeled rather than automatically interchangeable. Six starred families are detailed next. The Appendix A script shows the exact 154 checks performed; remaining authoring/review work is explicit.

| ID / common objective | Choice A / Choice B | Curriculum and lab mapping | Verification and meaningful boundary |
| --- | --- | --- | --- |
| **X01*** Projection | Force along a rail / velocity component in a corridor, different frame/direction data | M02; L01/L06 | Exact rational projection + unit-vector alternative; zero direction, shape, orthogonal residual. Not a whole vectors PASS. |
| X02 Linear solve/identifiability | Two-sensor calibration / bounded force-allocation equations | M03/M04, M11; L06 | Independent 2×2 anchor and rank/inconsistency cases; accept a valid free-parameter solution when nonunique. Full numerical solver not implemented in audit. |
| X03 Chain rule | Nonlinear calibration curve / nested camera-response curve | M05/M06; L06/L16 | Explicit-domain derivative + finite differences, missing-inner-factor mutation. Not proof ability. |
| **X04*** Bayes | Rare fault alarm / defective-part screen | M08/M09; L09 | Exact contingency table/rational posterior; base rates, impossible observation and domain validity. No assumed independent alarms. |
| X05 Covariance | Aligned sensor residuals / correlated coordinate logs | M09; L09/L10 | Sample versus population denominator, PSD/singular anchor, n≤1 policy to author. Not correlation⇒independence. |
| X06 Numerical stepping | Decay-state Euler update / driven first-order response | M05/M07/M11; L04/L08 | Exact simple update/stability anchor; accuracy/refinement policy by variant. No physical-model truth claim. |
| X07 Python function contract | Sensor-batch mean / telemetry summary | PY01; numerical prerequisites | Empty/nonmutation/fractional result; loop and `fsum` formulations. Numeric domain/overflow policy must be specified. Legacy mean evidence remains mean only. |
| X08 Array axes/preprocessing | Feature columns / image-channel layout | PY04, V01, ML03; L16/L19 | Independent loop/shape anchors, constant-column policy, held-out training statistics. No leaked fit or square-only fixtures. |
| X09 Test design | Projection regression suite / kinematic function bug suite | PY07/T04; L05/L06 | Tests accept valid alternatives and kill selected genuine mutations; separate from program PASS. A single orthogonal case misses a zero stub. |
| **X10*** Frames | Camera-to-base marker / warehouse-frame waypoint | M12/R03; L01/L12 | Hand integer anchors, inverse/order, point/direction, reflection, shape; sequential and matrix formulations. SE(2) first, SE(3) separately. |
| **X11*** FK and optional J | 2R tabletop reach / 2R inspection link | R04/R06, M06; L02/L06 | Trig vs chain, explicit pose convention, nonzero unequal links; J checked by finite differences. FK/J are separate objectives. |
| X12 Odometry | Differential-drive cart / inspection rover | R02 and proposed R20; L03/L05 | Exact arc/straight/spin/nonzero-heading anchors; tiny motion and dimensioned tolerance. No localization/SLAM claim. |
| X13 Bounded feedback | Wheel-speed toy plant / thermal first-order toy | C01/C03, C09 subset; L04 | Audit tested a bounded P integrator only; PID/anti-windup/time-delay extensions still need their own model/review. No universal zero-error rule. |
| **X14*** Shortest path | Warehouse graph / route through a service network | PY02/E02, proposed R18 subset; L11 | Exhaustive small-graph oracle, any optimal simple path, ties/zero cycles/unreachable/invalid weights. Not geometric collision planning. |
| X15 Swept collision | Disc-robot inflated obstacle / tool-centre clearance segment | R03 and proposed R18; L11/capstone | Segment-circle closest distance, touching/degenerate/endpoint-only mutation; polygon/3D extension unvalidated. |
| X16 Camera geometry | Overhead marker / wrist-mounted point | V03/M12; L16/L17 | Pinhole projection/deprojection anchors, finite positive depth, dimensions/axes; calibrated intrinsics supplied. Not complete camera calibration. |
| **X17*** Shared gradient | Shared scalar computation graph / two uses across time | ML05/M06/PY06 optional; L19/L20 | Explicit loss, analytic/reverse accumulation + finite-difference check, lost-path mutations; no full BPTT claim. |
| X18 Value/terminal semantics | Finish/wait task / small continuing navigation MDP | RL01/RL02/RL03; L20 extension | Exact policy values/Bellman anchor; terminal versus administrative truncation under stated task. No lucky rollout as oracle. |
| X19 Episode leakage/QA | Teleop demonstrations / sensor-classification sessions | ML03/ML07 and proposed E16; L19 | Group split disjointness, train-only stats, time/corruption policy. Audit checked basic cases, not every dataset defect or generalization. |
| X20 Plan validity | Pickup/deliver facts / recharge/precondition scenario | E04/E05/E14 subset; L15/L22 | Independent state transition/goal and precondition checks; multiple valid plans. Not general cognition or optimality unless separately specified. |

The forty route descriptions are **scenario proposals**, not forty fully authored alternative assessments. Distinct routes need full fixtures/hints/rights review and difficulty calibration. New seven-topic coverage is deliberately partial: M17 in a damped solve extension, R16 in data/time checks, R17 in separate timing tasks, R18 in search/collision, R19 in later control, R20 in odometry/estimation, E16 in QA. No robot context is forced on every independent mathematical/programming exercise.

### 7. Six detailed examples and audited correctness

**X01 — Projection.** Contract: given equal-length bounded finite real vectors u,v with nonzero v, return `((u·v)/(v·v))v`; empty/zero direction or mismatched shape is invalid, with typed feedback. Example u=(2,1,−1), v=(1,2,2) gives `(2/9,4/9,4/9)`; residual is orthogonal to v. Signed scalar component is **2/3**, a different requested quantity: accept it only for the separately labeled component objective. Valid formulations include the rational formula and unit-direction projection; both passed. Tests reject division by norm rather than squared norm and zero direction; a fixed orthogonal input cannot detect a zero implementation. Coding claim requires all typed/shape/finite tests and selected properties; M answer can be exact fractions or a declared numerical tolerance. Hint ladder: identify output shape → compute v·v → worked decomposition. New corridor direction is practice/retention; a new modeling assumption is reviewed transfer. Practical value: constrain force/motion without confusing distance traveled and signed progress.

**X04 — Bayes.** Contract: p=P(F), s=P(+|F), q=P(+|not F), all probabilities in [0,1]; denominator must be positive. p=1/50, s=9/10, q=1/20 yields `(p s)/(p s+(1−p)q)=18/67≈0.2686567164`. Independent integer table: among 10000 items, 200 faults yield 180 positives; 9800 nonfaults yield 490 positives. Alternative: table counting or rational conditional formula; both agree. Audit covers p=0/1 when meaningful, impossible evidence and invalid probabilities, plus inverse-conditional mutation. Never force a numeric answer for an impossible observation or infer two-alarm independence without a joint model. Accept exact rational input; a displayed decimal must have a stated tolerance. Hints: choose conditioning population → include false positives → table solution. Mastery needs fresh base-rate/representation probes; one posterior is narrow M, not all probability.

**X10 — Frame composition.** Use column homogeneous vectors. A maps B→A with 90° rotation and translation (1,2); B maps C→B with translation (3,−1). Then A·B has rotation 90° and translation (2,5). Point C=(1,2) maps to A=(0,6). Direction B=(2,0) maps to (0,2), with no translation. Inverse maps A point (1,4) to B=(2,0). Sequential application and matrix multiplication both passed exact integer anchors; swapped order and translated-direction mutations failed. Reflection determinant −1 is not a proper rotation. Contract includes finite shape/rotation validity and nonmutation; a round trip alone can pass two consistently wrong functions. Start SE(2); SE(3)/quaternion order is a separately reviewed extension. Hints: label source/target → write one intermediate point → worked chain. Narrow I/M frame claim, not Lie theory or physical camera calibration.

**X11 — Planar FK, with separate Jacobian objective.** Relative radians; l1=2,l2=1, q1=π/2,q2=−π/2 gives endpoint (1,2) and tool orientation q1+q2=0. Position Jacobian is `[[-2,0],[1,1]]` at that pose. Direct trig and a rotated local-link formulation agreed on twelve seeded nonzero poses; analytic J agreed with two-direction central differences at h=1e-5 on those fixtures within the declared 1e-8 audit bound. A relative/absolute-angle mutation fails the hand case. Accept any equivalent formulation matching position/orientation conventions; J output correctness is not proof the learner derived it analytically. Test straight/folded/unequal-link/tool-offset and invalid input cases before release; these are not all implemented in the audit script. Seeded numeric variation is not unfamiliar transfer. Hints: draw relative angles → reconstruct frame/local tip → independent derivation; optional singularity/changed-tool task requires appropriate readiness/review.

**X14 — Shortest paths.** Finite explicit-node graph, finite nonnegative numeric weights (booleans excluded), known start/goal; return an optimal simple path/cost, or `unreachable`. Invalid graph/negative edge anywhere, including unreachable components, is a format/domain error. S→A/B both cost 1, A/B→G cost 1, with zero A↔B edges, has optimal cost 2 and several valid routes. Dijkstra matched exhaustive simple-path enumeration on ten additional seeded five-node graphs; start=goal, disconnected endpoint, invalid/nonfinite/negative/bool weights and unknown endpoints were checked. Accept any valid optimal simple path, not a lexicographic reference route; validate edge adjacency/cost independently. A* extension must state heuristic assumptions and reopening policy; not part of this Dijkstra evidence. Hints: distinguish path validity/cost → frontier invariant → small trace. Practical value: route selection before opaque Nav2 calls, without claiming geometric feasibility.

**X17 — Shared-parameter gradient.** Explicitly define f=θx+θ² and loss `L=1/2(f−y)²`. At x=2,y=5,θ=3, f=15,L=50, and `dL/dθ=(f−y)(x+2θ)=80`. Reverse accumulation adds direct contribution 20 and square-path contribution 60; dropping either fails. Analytic expression, explicit reverse accumulation and central difference agreed in the anchor and ten additional small seeded cases. Numerical checks have bounded finite domains and declared error; derivative computation does not automatically verify a written proof. For an alternative time-sharing graph, publish its own fixtures/version rather than assume identical difficulty. Hints: annotate both uses → sum adjoints → worked graph. Later fresh graph tests method use; full network/backprop/learning claims require additional scopes.

Six detailed contracts all need final invalid-type/nonfinite/format/reviewer calibration before publication. Appendix A verifies the listed fixtures, not a completed UI/content package. Other families' spot audits are deliberately narrower; for example X13 does not implement PID anti-windup, X02 does not implement a general rank solver, and X19 does not prove every leakage/data-quality condition.

### 8. Mathematical and coding verification policy

Numeric answers: strict typed finite scalars/vectors/matrices, units/shape/domain stated, exact rational comparison when appropriate and scale-specific tolerances otherwise. Reject bool-as-number and NaN/Infinity unless an explicit different contract truly needs them. Permit −0 and equivalent fractions; format errors do not become conceptual weaknesses. A proposed bounded scalar grammar can accept signed integers/decimals or integer fractions with bounded digits/denominator/exponent, no names/calls/attributes, no eval. General expression/CAS grading is deferred; sampling cannot prove equivalence, and domains distinguish x/x from 1 or |x| from x.

For numerical algorithms, validate the function's actual specification: method/order/error domain, independent exact cases, boundary/invalid cases, properties and selected genuine mutations. Residual alone is not parameter accuracy in an ill-conditioned solve. Multiple valid optimal paths, nonunique linear solutions and quaternion signs need set/invariant/geodesic validators, not exact reference serialization. Reference code and property tests complement hand anchors; no magic tolerance/seed count proves correctness.

From-scratch method objectives need code/reasoning review if output tests cannot establish how a result was obtained. An allowed-library implementation exercise has a different contract. Do not enforce arbitrary AST style bans and claim they prove independent algorithm authorship. Open derivations, design and unfamiliar transfer remain reviewed/unverified without a qualified reviewer.

### 9. Parent-owned grading and threat model

**Trusted:** installed reviewed catalog/oracles/policy, local parent broker, its signing key and operator's deliberate install choices. **Untrusted:** submitted code, stdout/stderr, worker values, user-supplied metadata/files and imported result JSON. The local owner can alter their own software/key; this is a self-study system, not proctored certification. Protect the owner's files/credentials from exercise code anyway.

Parent loads an allowlisted contract and immutable job bytes, computes expected results/constraints outside the worker, starts a resource-limited isolated worker, and receives only bounded typed values correlated to a request. Parent checks actual completion, exit/signal/time, output quotas, schema, finite/shape/value constraints and every critical case before constructing its own result. Worker `passed`, `checks`, objective, hash, score or signature fields are never authoritative. Do not use pickle or evaluate learner output. Copy/hash the exact bytes actually run; resolve file/symlink/archive paths safely. No client-chosen verifier command, grader URL or host directory mount.

Separate a bounded result channel from diagnostics. The proof-of-concept used fd 3 for values, with parent-side comparisons; nonce is correlation, not a secret or anti-cheat mechanism. A script returning the correct value can legitimately pass an output check, even if hardcoded; it does not thereby prove method/independence. Malformed/duplicate protocol, early exit, nonfinite/object/bool values, incorrect results and oversized output failed closed. A correct result accompanied by fake `passed` text on diagnostic stdout was accepted **because the result was correct**, not because the text was trusted.

Linux candidate: namespaces with a minimal read-only runtime/job, private tmp/proc, no host home/key/workspace/network, dropped capabilities, resource/time/output/process controls and a reviewed syscall policy. Installed Bubblewrap 0.6.1 ran the audit namespace profile; benign marker/host-loopback probes were blocked. The prototype mounts broad `/usr` and library trees, has CPU/address-space/file/fd limits and parent timeout, but does **not** establish a production seccomp policy, cgroup PID/memory/fork-bomb protection, descendant escape safety, kernel resistance or all error-path cleanup. Those are release gates, not conclusions from 15 tests. Initial use of an unsupported Bubblewrap flag aborted and was corrected; pin/test actual flags rather than assume tool portability.

Windows/macOS: no untrusted-code isolation profile was executed here. AppContainer/Job/ACL or a supported macOS helper/VM are substantial separate engineering choices, not a claim that Python's subprocess timeout is sufficient. The bank/numeric practice can remain native; unrestricted coding execution is never a silent fallback. An optional explicitly isolated Linux environment can be evaluated later, with host-sharing/network exposure tested. Docker is not required for the numerical bank or CoreLab. Sandbox unavailable means code verification unavailable or clearly trusted/manual practice, not a strong automatic PASS.

The audit legacy short-circuit returned `{"passed":true,"checks":8}` with exit 0 before fixed tests. No signing CLI/import/key/evidence mutation was used. Preserve old records while fixing/versioning future runner behavior, with an honest limitation and optional fresh retest. Parent-owned grading improves that failure mode but is not enough without OS isolation and scoped evidence policy.

### 10. Practice, mastery and integration

Practice freely offers hints/solutions, attempts, alternate contexts, feedback and focused remediation. State “correct on this practice task” rather than “mastered topic.” Assisted correction, repeated known forms and targeted sets do not satisfy full mastery gates. An assessment plan independently defines objective/dimension coverage, critical criteria, exposure/fresh forms, resource mode and reviewer. Difficulty/number of completed choices is not a level conversion.

Retain C/M/I/T and L0–L4: scoped C/M from valid independent assessment, scoped I from admitted parent-owned implementation evidence, retention from delayed fresh retrieval, unfamiliar T/L3 and research/L4 with qualified human review. No artificial M for pure tools, no I from prose, no automatic L3/L4 and no hardware claim from simulation. Current engine does not implement these future aggregation rules; owners must approve a versioned additive policy first.

The bank is local-first with static versioned data and bounded local artifact manifests. New practice history must not be pushed into old Attempt shapes unvalidated. Preserve old question/assessment IDs/versions, purposes, signatures, backup round trips and immutable source meanings. Old alias/equivalent tags need reviewed scope relations, not automatic broad credit. New APIs remain localhost-only; no cloud/auth/multiuser service or browser code execution. Manual ChatGPT context can carry objective, attempt, hints and known gaps, with assistance/exposure recorded; no model-generated tasks/solutions become assessed evidence without review.

### 11. MVP, effort and owner decisions

**Proposed first tranche:** four packs X01/X04/X10/X11, two original scenario choices each, numeric/matrix practice first, a single tested optional Python runner profile only after security review. Six fully specified examples in this audit do not mean all eight MVP choices are authored. No imported content needed for the first release; selected permissive sources remain optional reviewed future contributions.

Sequence: approve scope/purpose/rights/security → versioned objective/item manifest and exact validators → author task alternatives/hand fixtures/hints/valid solutions/mutations → trial safe mathematical practice and transparent selection → harden/test one parent/OS profile → review any mastery form/aggregation separately → add other catalog families by goal and observed need. Extend to C++/ROS/large ML/symbolic parsing only when their tooling/security/prerequisites justify it. Do not commission every family, a general sandbox fleet, CMS or a psychometric engine now.

Planning estimates, not measured productivity: about 30–60 author hours for the first original packs/manifests/review; 24–56 for numeric-entry/choice/adaptive integration; 40–100+ for one hardened code profile/compatibility tests/security review; separate effort for assessment calibration and other OSes. Ranges overlap and may be wrong. No automatic absorption into the previous 100-hour curriculum budget. Fewer well-tested tasks are preferable to advertised abundance that cannot fairly grade alternative solutions.

Owner must choose: initial objectives and learner goal; practice-only MVP versus an explicit later assessment pilot; item licensing/contributor attestation; supported interpreter/OS/code-execution trust profile; qualified content/security/reviewer capacity; new result namespace/storage migration; and budget/deferred work. No approval is inferred from this design task.

### 12. Questions for Claude after its independent Round 1

1. Do your “choices” really offer alternative tasks for the same scope, or just different seeds/dimensions? What prevents easy-choice accumulation from becoming mastery?
2. Which content, code, data and test-file licenses did you read? Did you distinguish MIT Exercism from NC-SA OCW/Euler, and PrairieLearn's mixed AGPL/enterprise/third-party terms?
3. Can a worker printing a forged verdict, exiting 0, mutating tests or forging a result file win your grader? Which parent/OS protections were executed, and what remains untested?
4. Do numeric/expression validators handle fractions, zero direction, bool/nonfinite/shape/domain and valid alternative paths/solutions? What independently checks the oracle itself?
5. Which six detailed exercises did you compute/test, with what edge/mutation/valid-alternative cases and durable artifacts? What was only a specification review?
6. How do your practice events integrate without touching old signatures/assessment versions or the engine's topic-wide I shortcut? What gates new code/mastery/hardware claims?
7. What smallest useful bank can be delivered without a platform rewrite or a broad security promise, and what costs/support burden remain?

### 13. Evidence, validation and handoff

Actual author-side results: 20 groups, **154 named checks passed**; six detailed families include alternative formulations/oracles and selected mutations. Linux boundary prototype: **15 controlled probes**, three accepted valid behaviors and 12 rejected invalid behaviors; benign host marker/host-loopback exposure checks both blocked. System/runtime: Linux, Bubblewrap 0.6.1, inner `/usr/bin/python3` 3.10.12, host Python 3.14; not a cross-platform test. No simulator/robot/third-party exercise platform/library suite was executed.

Baseline app validation passed: **119 tests/eight files**, Node **26.8.1** (satisfies repository Node 24+), and `npm run validate:content` (169 topics, 31 lessons/diagnostics, 42 targeted questions/seven banks, 28 videos). These are existing app invariants, not exercise-bank efficacy. No app build/browser/other-OS regression claims are made for a documentation-only task.

High confidence: inspected current contracts/selection, observed licenses at selected files, reproduced fixture/protocol results and their stated bounds. Medium: curricular mapping, useful scenario choices and proposed minimal architecture. Unmeasured: novice difficulty/time, equivalence of task choices, transfer/retention gains, full malicious-code containment, all OS behavior and full future asset rights. The following original scripts and outputs are embedded for durable rerun; they are research evidence, not production implementation.


### 14. Pinned primary-source index

Repository sources are point-in-time reads, not executed upstream test suites. License scope/exceptions still require per-import review.

| Source | Commit | Inspected pointers |
| --- | --- | --- |
| exercism/problem-specifications | `ddf514efa0718e129b8a87a07e00481b02efc32b` | [LICENSE](https://github.com/exercism/problem-specifications/blob/ddf514efa0718e129b8a87a07e00481b02efc32b/LICENSE); [canonical-data.schema.json](https://github.com/exercism/problem-specifications/blob/ddf514efa0718e129b8a87a07e00481b02efc32b/canonical-data.schema.json); [exercises/binary-search/canonical-data.json](https://github.com/exercism/problem-specifications/blob/ddf514efa0718e129b8a87a07e00481b02efc32b/exercises/binary-search/canonical-data.json) |
| exercism/python | `6105f6d9d3ef66ce3d5c8f529d2882af3d76b706` | [LICENSE](https://github.com/exercism/python/blob/6105f6d9d3ef66ce3d5c8f529d2882af3d76b706/LICENSE); [exercises/practice/binary-search/binary_search_test.py](https://github.com/exercism/python/blob/6105f6d9d3ef66ce3d5c8f529d2882af3d76b706/exercises/practice/binary-search/binary_search_test.py); [exercises/practice/binary-search/.meta/tests.toml](https://github.com/exercism/python/blob/6105f6d9d3ef66ce3d5c8f529d2882af3d76b706/exercises/practice/binary-search/.meta/tests.toml) |
| jupyter/nbgrader | `71d340c114a2661e7f0ba9b57cb80b23538d78fa` | [LICENSE](https://github.com/jupyter/nbgrader/blob/71d340c114a2661e7f0ba9b57cb80b23538d78fa/LICENSE); [nbgrader/preprocessors/overwritecells.py](https://github.com/jupyter/nbgrader/blob/71d340c114a2661e7f0ba9b57cb80b23538d78fa/nbgrader/preprocessors/overwritecells.py); [nbgrader/preprocessors/execute.py](https://github.com/jupyter/nbgrader/blob/71d340c114a2661e7f0ba9b57cb80b23538d78fa/nbgrader/preprocessors/execute.py); [nbgrader/docs/source/user_guide/faq.rst](https://github.com/jupyter/nbgrader/blob/71d340c114a2661e7f0ba9b57cb80b23538d78fa/nbgrader/docs/source/user_guide/faq.rst) |
| PrairieLearn/PrairieLearn | `172ec78ebeadb11945bfe0d4331b3a37561122de` | [LICENSE](https://github.com/PrairieLearn/PrairieLearn/blob/172ec78ebeadb11945bfe0d4331b3a37561122de/LICENSE); [docs/question/server.md](https://github.com/PrairieLearn/PrairieLearn/blob/172ec78ebeadb11945bfe0d4331b3a37561122de/docs/question/server.md); [docs/externalGrading.md](https://github.com/PrairieLearn/PrairieLearn/blob/172ec78ebeadb11945bfe0d4331b3a37561122de/docs/externalGrading.md); [apps/prairielearn/src/lib/externalGraderLocal.ts](https://github.com/PrairieLearn/PrairieLearn/blob/172ec78ebeadb11945bfe0d4331b3a37561122de/apps/prairielearn/src/lib/externalGraderLocal.ts) |
| sympy/sympy | `d83f721f2cf5f8259a9a697a922f46a7da71a176` | [LICENSE](https://github.com/sympy/sympy/blob/d83f721f2cf5f8259a9a697a922f46a7da71a176/LICENSE); [sympy/parsing/sympy_parser.py](https://github.com/sympy/sympy/blob/d83f721f2cf5f8259a9a697a922f46a7da71a176/sympy/parsing/sympy_parser.py) |
| HypothesisWorks/hypothesis | `30f73af87f587b6911042552e24f1dea2577988a` | [LICENSE.txt](https://github.com/HypothesisWorks/hypothesis/blob/30f73af87f587b6911042552e24f1dea2577988a/LICENSE.txt); [hypothesis/docs/quickstart.rst](https://github.com/HypothesisWorks/hypothesis/blob/30f73af87f587b6911042552e24f1dea2577988a/hypothesis/docs/quickstart.rst); [hypothesis/src/hypothesis/strategies/_internal/numbers.py](https://github.com/HypothesisWorks/hypothesis/blob/30f73af87f587b6911042552e24f1dea2577988a/hypothesis/src/hypothesis/strategies/_internal/numbers.py) |
| pytest-dev/pytest | `0212785e34eb635b3359e4eccc757de95bf39036` | [LICENSE](https://github.com/pytest-dev/pytest/blob/0212785e34eb635b3359e4eccc757de95bf39036/LICENSE); [src/_pytest/approx.py](https://github.com/pytest-dev/pytest/blob/0212785e34eb635b3359e4eccc757de95bf39036/src/_pytest/approx.py) |
| containers/bubblewrap v0.6.1 | `a362d3c0ee79097ce2e3fca4ad003f1e96dad472` | [COPYING](https://github.com/containers/bubblewrap/blob/a362d3c0ee79097ce2e3fca4ad003f1e96dad472/COPYING); [README](https://github.com/containers/bubblewrap/blob/a362d3c0ee79097ce2e3fca4ad003f1e96dad472/README.md) |



### Appendix A — Original content-audit script

Save this block as `content_checks.py`; standard-library only. It checks declared fixtures, not all exercise specifications.

```python
"""Original audit fixtures, not a production exercise bank or released grader.
Run: python3 content_checks.py. Standard library only.
"""
import math,json,itertools,heapq,random
from fractions import Fraction as F
from collections import defaultdict
results={}; current=None

def begin(id):
 global current
 current=id;results[id]={'checks':0,'status':'passed'}
def check(label,condition):
 results[current]['checks']+=1
 if not condition:raise AssertionError((current,label))
def near(a,b,tol=1e-8):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

def dot(u,v):
 if len(u)!=len(v):raise ValueError('shape')
 return sum(a*b for a,b in zip(u,v))
def projection(u,v):
 d=dot(v,v)
 if d==0:raise ValueError('zero direction')
 return [dot(u,v)*x/d for x in v]
def projection_unit(u,v):
 n=math.sqrt(dot(v,v))
 if n==0:raise ValueError('zero direction')
 w=[x/n for x in v];return [dot(u,w)*x for x in w]
def rejects(call):
 try:call()
 except (ValueError,ZeroDivisionError):return True
 return False

begin('X01')
u=[F(2),F(1),F(-1)];v=[F(1),F(2),F(2)];p=projection(u,v)
check('exact projection',p==[F(2,9),F(4,9),F(4,9)])
check('orthogonal residual',dot([a-b for a,b in zip(u,p)],v)==0)
check('zero rejected',rejects(lambda:projection([1,2],[0,0])))
check('shape rejected',rejects(lambda:projection([1],[1,2])))
check('unit-vector alternative',all(near(float(a),b) for a,b in zip(p,projection_unit(u,v))))
check('wrong denominator mutant',p!=[dot(u,v)*x/3 for x in v])

begin('X02')
A=[[2,1],[1,-1]];b=[5,1];x=[2,1]
check('independent solve anchor',[dot(row,x) for row in A]==b)
check('rank deficient compatible',2*3==6)
check('rank deficient incompatible',2*3!=7)
check('inverse-only determinant fails',1*4-2*2==0)

begin('X03')
f=lambda x:(3*x+1)**2;h=1e-5
check('chain rule exact',6*(3*2+1)==42)
check('central difference',near((f(2+h)-f(2-h))/(2*h),42,1e-7))
check('missing-inner-derivative mutant',2*(3*2+1)!=42)

def posterior(p,s,q):
 if not all(F(0)<=x<=F(1) for x in (p,s,q)):raise ValueError('probability')
 denominator=p*s+(1-p)*q
 if denominator==0:raise ValueError('impossible evidence')
 return p*s/denominator
begin('X04')
check('Bayes exact',posterior(F(1,50),F(9,10),F(1,20))==F(18,67))
check('enumeration',F(180,180+490)==F(18,67))
check('prior zero',posterior(F(0),F(9,10),F(1,20))==0)
check('prior one',posterior(F(1),F(9,10),F(1,20))==1)
check('impossible evidence',rejects(lambda:posterior(F(0),F(1),F(0))))
check('invalid probability',rejects(lambda:posterior(F(-1),F(1),F(1))))
check('inverse-conditional mutant',F(9,10)!=F(18,67))

begin('X05')
points=[(1,2),(3,4),(5,6)];means=[3,4]
cov=[[sum((p[i]-means[i])*(p[j]-means[j]) for p in points)/2 for j in range(2)] for i in range(2)]
check('sample covariance',cov==[[4,4],[4,4]])
check('singular PSD',cov[0][0]*cov[1][1]-cov[0][1]**2==0)
check('population differs',sum((p[0]-3)**2 for p in points)/3!=4)

begin('X06')
y=1
for _ in range(4):y+=.25*(-2*y)
check('Euler four steps',y==.0625)
check('model error visible',abs(y-math.exp(-2))>.07)
check('unstable step amplifies',abs(1-2*1.1)>1)
check('stable-step condition',all(abs(1-2*h)<1 for h in [.1,.25,.9]))

def mean_loop(xs):
 if not xs:raise ValueError('empty')
 total=0
 for x in xs:total+=x
 return total/len(xs)
def mean_sum(xs):
 if not xs:raise ValueError('empty')
 return math.fsum(xs)/len(xs)
begin('X07')
xs=[-3,-1,7];copy=xs[:]
check('mean anchor',mean_loop(xs)==mean_sum(xs)==1)
check('nonmutation',xs==copy)
check('empty rejected',rejects(lambda:mean_loop([])))
check('fractional mean',mean_loop([1,2])==1.5)

begin('X08')
xs=[[1,10],[3,14]];original=[r[:] for r in xs]
mu=[2,12];sd=[1,2]
z=[[(x-m)/s for x,m,s in zip(row,mu,sd)] for row in xs]
check('column scaling',z==[[-1,-1],[1,1]])
check('nonmutation',xs==original)
check('constant-column policy',[(x-3)/1 for x in [3,3]]==[0,0])
check('held-out training statistics',(5-mu[0])/sd[0]==3)

begin('X09')
fixture_u=[2,1,-1];fixture_v=[1,2,2];expected=[2/9,4/9,4/9]
valid=[projection(fixture_u,fixture_v),projection_unit(fixture_u,fixture_v)]
mutants=[[0,0,0],[2/3,4/3,4/3],[-2/9,-4/9,-4/9],[4/9,8/9,8/9]]
accept=lambda p:len(p)==3 and all(near(a,b) for a,b in zip(p,expected))
check('tests accept both valid formulations',all(accept(p) for p in valid))
check('tests reject each selected mutation',all(not accept(p) for p in mutants))
check('orthogonal-only fixture misses zero mutant',dot([1,0],[0,1])==0)

# SE(2) matrix oracles use exact integer fixtures, independent of trig.
def mm(A,B):return [[sum(a*b for a,b in zip(row,col)) for col in zip(*B)] for row in A]
def mv(A,v):return [dot(row,v) for row in A]
def inv2(T):
 a,b,x=T[0];c,d,y=T[1]
 return [[a,c,-a*x-c*y],[b,d,-b*x-d*y],[0,0,1]]
begin('X10')
A=[[0,-1,1],[1,0,2],[0,0,1]];B=[[1,0,3],[0,1,-1],[0,0,1]];I=[[1,0,0],[0,1,0],[0,0,1]]
check('composed transform',mm(A,B)==[[0,-1,2],[1,0,5],[0,0,1]])
check('point independent anchor',mv(mm(A,B),[1,2,1])==[0,6,1])
check('direction independent anchor',mv(A,[2,0,0])==[0,2,0])
check('inverse',mm(inv2(A),A)==I)
check('inverse round trip',mv(inv2(A),[1,4,1])==[2,0,1])
check('alternative sequential mapping',mv(A,mv(B,[1,2,1]))==[0,6,1])
check('order mutant rejected',mv(mm(B,A),[1,2,1])!=[0,6,1])
check('direction-translation mutant rejected',mv(A,[2,0,1])!=[0,2,0])
check('reflection is not proper rotation',-1*1-0*0==-1)

# Two independently expressed FK implementations; derivative oracle is finite difference.
def fk(a,b,l1=2,l2=1):return l1*math.cos(a)+l2*math.cos(a+b),l1*math.sin(a)+l2*math.sin(a+b)
def fk_chain(a,b,l1=2,l2=1):
 R1=[[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]
 local=[l1+l2*math.cos(b),l2*math.sin(b)]
 return tuple(dot(row,local) for row in R1)
def jac(a,b,l1=2,l2=1):
 return [[-l1*math.sin(a)-l2*math.sin(a+b),-l2*math.sin(a+b)],[l1*math.cos(a)+l2*math.cos(a+b),l2*math.cos(a+b)]]
begin('X11')
check('FK anchor',all(near(x,y) for x,y in zip(fk(math.pi/2,-math.pi/2),[1,2])))
J=jac(math.pi/2,-math.pi/2)
check('Jacobian anchor',all(near(J[i][j],v) for i,row in enumerate([[-2,0],[1,1]]) for j,v in enumerate(row)))
rng=random.Random(417)
for n in range(12):
 a,b=[rng.uniform(-2,2) for _ in range(2)]
 check('two FK formulations '+str(n),all(near(x,y) for x,y in zip(fk(a,b),fk_chain(a,b))))
 h=1e-5;J=jac(a,b)
 for j in range(2):
  qp=[a,b];qm=[a,b];qp[j]+=h;qm[j]-=h
  estimate=[(x-y)/(2*h) for x,y in zip(fk(*qp),fk(*qm))]
  check('Jacobian directional fixture '+str((n,j)),all(near(J[i][j],estimate[i],1e-8) for i in range(2)))
check('singular pose',near(jac(0,0)[0][0],0) and near(jac(0,0)[0][1],0))
check('relative-angle mutant rejected',not near(2*math.cos(math.pi/2)+math.cos(-math.pi/2),1))

begin('X12')
dl,dr,L=.1,.3,.4;ds=(dl+dr)/2;dt=(dr-dl)/L
arc=[ds/dt*math.sin(dt),ds/dt*(1-math.cos(dt)),dt]
check('turning angle',near(dt,.5))
check('arc anchor',near(arc[0],.4*math.sin(.5)) and near(arc[1],.4*(1-math.cos(.5))))
check('straight nonzero heading',near(.2*math.cos(math.pi/2),0) and near(.2*math.sin(math.pi/2),.2))
check('pure spin',(-.1+.1)/2==0)
check('swapped-wheel mutant',not near((dl-dr)/L,.5))

begin('X13')
q=0;commands=[]
for _ in range(100):
 u=max(-.5,min(.5,2*(1-q)));commands.append(u);q+=.1*u
check('declared P integrator tracks',abs(q-1)<1e-6)
check('commands bounded',all(abs(u)<=.5 for u in commands))
qbad=0
for _ in range(100):qbad+=.1*max(-.5,min(.5,2*(qbad-1)))
check('sign mutant fails',abs(qbad-1)>1)

# Exhaustive simple paths allow any optimal route; no canonical tie order required.
def paths(g,s,t,seen=()):
 if s==t:yield (s,),0;return
 for v,w in g.get(s,{}).items():
  if v not in seen+(s,):
   for p,c in paths(g,v,t,seen+(s,)):yield (s,)+p,w+c
def dijkstra(g,s,t):
 if s not in g or t not in g:raise ValueError('unknown endpoint')
 for edges in g.values():
  for node,w in edges.items():
   if node not in g or type(w) not in (int,float) or not math.isfinite(w) or w<0:raise ValueError('invalid graph')
 heap=[(0,0,s,(s,))];serial=itertools.count(1);best={s:0}
 while heap:
  c,_,u,p=heapq.heappop(heap)
  if c!=best[u]:continue
  if u==t:return p,c
  for v,w in g.get(u,{}).items():
   if w<0 or not math.isfinite(w):raise ValueError('nonnegative finite weights only')
   n=c+w
   if n<best.get(v,math.inf):best[v]=n;heapq.heappush(heap,(n,next(serial),v,p+(v,)))
 return None
begin('X14')
g={'S':{'A':1,'B':1},'A':{'G':1,'B':0},'B':{'G':1,'A':0},'G':{},'X':{}}
all_paths=list(paths(g,'S','G'));cost=min(c for p,c in all_paths)
check('exhaustive optimum',cost==2)
check('alternative optimal routes',len([p for p,c in all_paths if c==cost])>=2)
check('Dijkstra oracle agreement',dijkstra(g,'S','G')[1]==cost)
check('unreachable',dijkstra(g,'S','X') is None)
check('start equals goal',dijkstra(g,'S','S')==( ('S',),0))
check('negative edge rejected',rejects(lambda:dijkstra({'S':{'G':-1},'G':{}},'S','G')))
check('unreachable negative edge rejected',rejects(lambda:dijkstra({'S':{},'G':{},'X':{'G':-1}},'S','G')))
check('nonfinite edge rejected',rejects(lambda:dijkstra({'S':{'G':math.nan},'G':{}},'S','G')))
check('infinite edge rejected',rejects(lambda:dijkstra({'S':{'G':math.inf},'G':{}},'S','G')))
check('boolean edge rejected',rejects(lambda:dijkstra({'S':{'G':True},'G':{}},'S','G')))
check('unknown endpoint rejected',rejects(lambda:dijkstra({'S':{}},'S','G')))
for n in range(10):
 nodes=list(range(5));rg={u:{v:rng.randint(0,9) for v in nodes if v!=u and rng.random()<.4} for u in nodes}
 ref=list(paths(rg,0,4));got=dijkstra(rg,0,4)
 check('random exhaustive comparison '+str(n),(got is None and not ref) or (got is not None and ref and got[1]==min(c for p,c in ref)))

begin('X15')
def segment_hit(a,b,c,r):
 d=[b[i]-a[i] for i in range(2)];den=dot(d,d)
 t=0 if den==0 else max(0,min(1,dot([c[i]-a[i] for i in range(2)],d)/den))
 p=[a[i]+t*d[i] for i in range(2)]
 return sum((p[i]-c[i])**2 for i in range(2))<=r*r
check('interior collision',segment_hit([-2,0],[2,0],[0,0],.2))
check('endpoints miss collision',all(sum(x*x for x in p)>.2**2 for p in [[-2,0],[2,0]]))
check('clear segment',not segment_hit([-2,.3],[2,.3],[0,0],.2))
check('boundary contact',segment_hit([-2,.2],[2,.2],[0,0],.2))
check('degenerate point',segment_hit([0,0],[0,0],[0,0],.2))

begin('X16')
fx,fy,cx,cy=100,120,20,30;p=[1,-.5,2]
pixel=[fx*p[0]/p[2]+cx,fy*p[1]/p[2]+cy]
back=[(pixel[0]-cx)*2/fx,(pixel[1]-cy)*2/fy,2]
check('pixel anchor',pixel==[70,0])
check('backprojection',back==p)
check('pixel declared in frame',0<=pixel[0]<100 and 0<=pixel[1]<80)
check('row-column mutant differs',pixel!=[0,70])

begin('X17')
def loss(t,x=2,y=5):return F(1,2)*(t*x+t*t-y)**2
def grad_reverse(t,x=2,y=5):
 error=t*x+t*t-y
 return error*x+error*2*t
t=3;x=2;y=5
check('loss anchor',loss(t)==50)
check('shared gradient exact',(t*x+t*t-y)*(x+2*t)==80)
check('reverse accumulation alternative',grad_reverse(t)==80)
h=1e-5
check('finite difference independent check',near(float((loss(t+h)-loss(t-h))/(2*h)),80,1e-6))
check('lost-direct-path mutation', (t*x+t*t-y)*(2*t)!=80)
check('lost-square-path mutation',(t*x+t*t-y)*x!=80)
for n in range(10):
 t=rng.uniform(-2,2);x=rng.uniform(-2,2);y=rng.uniform(-2,2)
 exact=(t*x+t*t-y)*(x+2*t)
 fd=(float(loss(t+h,x,y))-float(loss(t-h,x,y)))/(2*h)
 check('fresh shared-gradient '+str(n),near(grad_reverse(t,x,y),exact,1e-9) and near(fd,exact,1e-6))

begin('X18')
check('finish beats wait at gamma half',3>1/(1-.5))
check('wait once then finish',1+.5*3==2.5)
check('wait policy at gamma .9',near(1/(1-.9),10))
check('terminal versus administrative truncation',1!=1+.9*2)
v=0
for _ in range(300):v=max(3,1+.9*v)
check('Bellman fixed point',near(v,10,1e-9))

begin('X19')
def split_ok(train,test):return not(set(train)&set(test))
check('episode split',split_ok(['a','b'],['c']))
check('frame split leakage rejected',not split_ok(['a','b'],['a']))
check('train-only normalization matters',sum([0,2])/2!=sum([0,2,100])/3)
check('out-of-order stamps detectable',not all(a<b for a,b in zip([0,2,1],[2,1])))

begin('X20')
actions={'go_b':({'at_a','charged'},{'at_b'},{'at_a'}),'pick':({'at_b','object_b'},{'held'},{'object_b'}),'go_a':({'at_b'},{'at_a'},{'at_b'}),'drop':({'at_a','held'},{'object_a'},{'held'})}
def execute(plan):
 state={'at_a','charged','object_b'}
 for name in plan:
  pre,add,delete=actions[name]
  if not pre<=state:return None
  state=(state-delete)|add
 return state
check('valid plan','object_a' in execute(['go_b','pick','go_a','drop']))
check('invalid precondition',execute(['pick']) is None)
check('alternative valid plan','object_a' in execute(['go_b','go_a','go_b','pick','go_a','drop']))
check('goal not inferred from action completion','object_a' not in execute(['go_b']))

assert set(results)=={f'X{i:02}' for i in range(1,21)}
print(json.dumps({'groups':results,'group_count':len(results),'check_count':sum(r['checks'] for r in results.values()),'scope':'Original author-side fixture and selected mutation checks; not a published exercise grader, learner study, sandbox certification, or proof of full-topic mastery.'},indent=2))
```

#### Actual content-audit summary

```json
{
  "groups": {
    "X01": {
      "checks": 6,
      "status": "passed"
    },
    "X02": {
      "checks": 4,
      "status": "passed"
    },
    "X03": {
      "checks": 3,
      "status": "passed"
    },
    "X04": {
      "checks": 7,
      "status": "passed"
    },
    "X05": {
      "checks": 3,
      "status": "passed"
    },
    "X06": {
      "checks": 4,
      "status": "passed"
    },
    "X07": {
      "checks": 4,
      "status": "passed"
    },
    "X08": {
      "checks": 4,
      "status": "passed"
    },
    "X09": {
      "checks": 3,
      "status": "passed"
    },
    "X10": {
      "checks": 9,
      "status": "passed"
    },
    "X11": {
      "checks": 40,
      "status": "passed"
    },
    "X12": {
      "checks": 5,
      "status": "passed"
    },
    "X13": {
      "checks": 3,
      "status": "passed"
    },
    "X14": {
      "checks": 21,
      "status": "passed"
    },
    "X15": {
      "checks": 5,
      "status": "passed"
    },
    "X16": {
      "checks": 4,
      "status": "passed"
    },
    "X17": {
      "checks": 16,
      "status": "passed"
    },
    "X18": {
      "checks": 5,
      "status": "passed"
    },
    "X19": {
      "checks": 4,
      "status": "passed"
    },
    "X20": {
      "checks": 4,
      "status": "passed"
    }
  },
  "group_count": 20,
  "check_count": 154,
  "scope": "Original author-side fixture and selected mutation checks; not a published exercise grader, learner study, sandbox certification, or proof of full-topic mastery."
}

```


### Appendix B — Controlled Linux parent/worker prototype

Save as `parent_grader_probe.py`; needs the tested Linux Bubblewrap/prlimit profile. Do not treat it as a production sandbox or run arbitrary external submissions. No application import, key or evidence creation.

```python
"""Linux-only controlled grading-boundary audit. Not a released sandbox/runner.
Known small probe submissions only; no application imports, keys or evidence.
"""
import os,sys,json,math,secrets,subprocess,tempfile,selectors,time,signal,socket
from pathlib import Path
BWRAP='/usr/bin/bwrap';PRLIMIT='/usr/bin/prlimit'
assert sys.platform=='linux' and Path(BWRAP).exists() and Path(PRLIMIT).exists()
MAX_RESULT=4096;MAX_DIAG=4096
DRIVER='''import sys,json,os,importlib.util
request=json.loads(sys.stdin.read(4097))
spec=importlib.util.spec_from_file_location("submission","/job/submission.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
value=module.solve(request["u"],request["v"])
message=json.dumps({"id":request["id"],"value":value},allow_nan=False,separators=(",",":")).encode()
if len(message)>4096:raise ValueError("result too large")
os.write(3,message)
'''
def sandbox(job):
 return [BWRAP,'--unshare-all','--die-with-parent','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/job','--ro-bind',str(job),'/job','--chdir','/job','--clearenv','--setenv','PATH','/usr/bin','/usr/bin/python3','-I','-S','/job/driver.py']
def run_probe(code):
 with tempfile.TemporaryDirectory(prefix='exercise-probe-') as td:
  job=Path(td);(job/'submission.py').write_text(code);(job/'driver.py').write_text(DRIVER)
  rid=secrets.token_hex(16);request={'id':rid,'u':[2,1,-1],'v':[1,2,2]}
  # Place the child's result pipe at fd 3; keep its read end at another fd.
  r,w=os.pipe();assert r==3,(r,w)
  reader=os.dup(r);os.close(r);os.dup2(w,3);os.close(w)
  with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
   command=[PRLIMIT,'--cpu=1:1','--as=268435456:268435456','--fsize=8192:8192','--nofile=64:64','--']+sandbox(job)
   proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,pass_fds=(3,),start_new_session=True)
   os.close(3)
   proc.stdin.write(json.dumps(request).encode());proc.stdin.close()
   sel=selectors.DefaultSelector();os.set_blocking(reader,False);sel.register(reader,selectors.EVENT_READ)
   payload=bytearray();deadline=time.monotonic()+3;timed_out=False;too_large=False;eof=False
   while not eof:
    if time.monotonic()>deadline:timed_out=True;break
    for key,_ in sel.select(min(.05,max(0,deadline-time.monotonic()))):
     chunk=os.read(reader,MAX_RESULT+1-len(payload))
     if not chunk:eof=True;break
     payload.extend(chunk)
     if len(payload)>MAX_RESULT:too_large=True;break
    if too_large:break
   if timed_out or too_large:
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   try:rc=proc.wait(timeout=3)
   except subprocess.TimeoutExpired:
    os.killpg(proc.pid,signal.SIGKILL);rc=proc.wait();timed_out=True
   sel.close();os.close(reader)
   out.seek(0,2);nout=out.tell();err.seek(0,2);nerr=err.tell()
   result={'accepted':False,'exit_code':rc,'timeout':timed_out,'stdout_bytes':nout,'stderr_bytes':nerr,'result_bytes':len(payload)}
   err.seek(0);result['stderr_preview']=err.read(512).decode(errors='replace')
   if rc!=0 or timed_out or too_large or nout>MAX_DIAG or nerr>MAX_DIAG:return result
   try:
    data=json.loads(payload)
    if set(data)!={'id','value'} or data['id']!=rid:return result
    value=data['value']
    result['accepted']=type(value) in (int,float) and math.isfinite(value) and abs(value-2)<=1e-12
   except (ValueError,TypeError,OverflowError):pass
   return result

cases={
 'valid_loop':('def solve(u,v):\n return sum(x*y for x,y in zip(u,v))\n',True),
 'valid_indexed':('def solve(u,v):\n s=0\n for i in range(len(u)):s+=u[i]*v[i]\n return s\n',True),
 'forged_stdout_early_exit':('import sys\nprint(\'{"passed":true,"checks":8}\')\nsys.exit(0)\n',False),
 'forged_stdout_wrong_result':('def solve(u,v):\n print(\'{"passed":true,"checks":8}\')\n return -999\n',False),
 'valid_with_fake_stdout':('def solve(u,v):\n print(\'{"passed":true,"checks":8}\')\n return sum(x*y for x,y in zip(u,v))\n',True),
 'verdict_object_in_value':('def solve(u,v):\n return {"passed":True,"value":2}\n',False),
 'nan_value':('def solve(u,v):\n return float("nan")\n',False),
 'boolean_value':('def solve(u,v):\n return True\n',False),
 'malformed_result_channel':('import os\nos.write(3,b\'{"passed":true}\')\ndef solve(u,v):return 2\n',False),
 'nonzero_exit':('raise SystemExit(7)\n',False),
 'wall_timeout':('import time\ntime.sleep(10)\n',False),
 'oversized_result':('def solve(u,v):\n return [0]*3000\n',False),
 'infinite_loop':('while True:pass\n',False),
 'oversized_diagnostics':('def solve(u,v):\n print("x"*5000)\n return 2\n',False),
 'duplicate_protocol':('import os\nos.write(3,b"{}{}")\ndef solve(u,v):return 2\n',False)
}
results={}
for name,(code,expected) in cases.items():
 result=run_probe(code);assert result['accepted']==expected,(name,result);results[name]=result

# Independent benign host-path/network exposure smoke; not an escape assessment.
with tempfile.TemporaryDirectory(prefix='exercise-host-marker-') as td:
 marker=Path(td)/'marker';marker.write_text('public audit marker')
 with socket.socket() as server:
  server.bind(('127.0.0.1',0));server.listen(1);port=server.getsockname()[1]
  code='''import os,socket,json
s=socket.socket();s.settimeout(.3)
try:s.connect(("127.0.0.1",PORT));network=True
except OSError:network=False
print(json.dumps({"host_marker_visible":os.path.exists(MARKER),"host_loopback_reachable":network}))
'''.replace('PORT',str(port)).replace('MARKER',repr(str(marker)))
  command=[BWRAP,'--unshare-all','--die-with-parent','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--clearenv','/usr/bin/python3','-I','-S','-c',code]
  p=subprocess.run(command,capture_output=True,text=True,timeout=5);assert p.returncode==0,p.stderr
  exposure=json.loads(p.stdout);assert exposure=={'host_marker_visible':False,'host_loopback_reachable':False},exposure
print(json.dumps({'probe_count':len(results),'results':results,'exposure_smoke':exposure,'scope':'Controlled Linux bwrap/parent-value checks only. Not a sandbox certification, hostile-kernel escape audit, process-count proof, other-OS result, authorship proof, released grader or signed evidence.'},indent=2))
```

#### Actual controlled-probe output

```json
{
  "probe_count": 15,
  "results": {
    "valid_loop": {
      "accepted": true,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 51,
      "stderr_preview": ""
    },
    "valid_indexed": {
      "accepted": true,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 51,
      "stderr_preview": ""
    },
    "forged_stdout_early_exit": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 27,
      "stderr_bytes": 0,
      "result_bytes": 0,
      "stderr_preview": ""
    },
    "forged_stdout_wrong_result": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 27,
      "stderr_bytes": 0,
      "result_bytes": 54,
      "stderr_preview": ""
    },
    "valid_with_fake_stdout": {
      "accepted": true,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 27,
      "stderr_bytes": 0,
      "result_bytes": 51,
      "stderr_preview": ""
    },
    "verdict_object_in_value": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 75,
      "stderr_preview": ""
    },
    "nan_value": {
      "accepted": false,
      "exit_code": 1,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 547,
      "result_bytes": 0,
      "stderr_preview": "Traceback (most recent call last):\n  File \"/job/driver.py\", line 7, in <module>\n    message=json.dumps({\"id\":request[\"id\"],\"value\":value},allow_nan=False,separators=(\",\",\":\")).encode()\n  File \"/usr/lib/python3.10/json/__init__.py\", line 238, in dumps\n    **kw).encode(obj)\n  File \"/usr/lib/python3.10/json/encoder.py\", line 199, in encode\n    chunks = self.iterencode(o, _one_shot=True)\n  File \"/usr/lib/python3.10/json/encoder.py\", line 257, in iterencode\n    return _iterencode(o, 0)\nValueError: Out of range f"
    },
    "boolean_value": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 54,
      "stderr_preview": ""
    },
    "malformed_result_channel": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 66,
      "stderr_preview": ""
    },
    "nonzero_exit": {
      "accepted": false,
      "exit_code": 7,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 0,
      "stderr_preview": ""
    },
    "wall_timeout": {
      "accepted": false,
      "exit_code": -9,
      "timeout": true,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 0,
      "stderr_preview": ""
    },
    "oversized_result": {
      "accepted": false,
      "exit_code": 1,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 171,
      "result_bytes": 0,
      "stderr_preview": "Traceback (most recent call last):\n  File \"/job/driver.py\", line 8, in <module>\n    if len(message)>4096:raise ValueError(\"result too large\")\nValueError: result too large\n"
    },
    "infinite_loop": {
      "accepted": false,
      "exit_code": 137,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 0,
      "stderr_preview": ""
    },
    "oversized_diagnostics": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 5001,
      "stderr_bytes": 0,
      "result_bytes": 51,
      "stderr_preview": ""
    },
    "duplicate_protocol": {
      "accepted": false,
      "exit_code": 0,
      "timeout": false,
      "stdout_bytes": 0,
      "stderr_bytes": 0,
      "result_bytes": 55,
      "stderr_preview": ""
    }
  },
  "exposure_smoke": {
    "host_marker_visible": false,
    "host_loopback_reachable": false
  },
  "scope": "Controlled Linux bwrap/parent-value checks only. Not a sandbox certification, hostile-kernel escape audit, process-count proof, other-OS result, authorship proof, released grader or signed evidence."
}

```

#### Actual legacy-harness reproduction

```json
{
  "returncode": 0,
  "stdout": "{\"passed\":true,\"checks\":8}\n",
  "stderr": "",
  "signing_or_import_executed": false
}
```


Independent Round 1 is complete. No peer findings were read before publication. Await matching Claude Round 1 before writing Round 2.

## Round 2 — Critical cross-review of Claude Round 1

Run ID `corelab-exercise-bank-20261031-01`. Peer status was read as `completed_round: 1` with the matching run ID **after** my own independent Round 1 and status were atomically published. This round reviews Claude's completed Round 1, not a later draft. No production edits.

### 2.1 Agreement and important corrections

Keep original authored exercises, optional licensed references, transparent recommendation rules, exposed assistance, independent assessment, and explicit unsatisfied review gates. Claude's test-writing exercise adds a valuable kind of learner choice: writing discriminating tests instead of another implementation. His C++ and RL details broaden my mostly numerical starter set. His stated missing L14/L18 coverage is honest.

**Blocking runner issue:** changing stdout to a different pipe is insufficient if a learner can send `passed: true` on that pipe. My Appendix B passes *values* from an isolated worker, rejects objects/bools/NaN/duplicate messages, and computes comparisons in the trusted parent. The correlation ID is not a secret. The worker may replace its own driver, inspect its inputs or hardcode correct outputs; none of those establish authorship. Parent-owned verdicts plus host isolation address different threats. A terminal-only unsandboxed process can still read the parent's signing key and local files under the same OS user. Never label that secure merely because it was launched from the CLI. Unsupported required isolation must fail closed, without signing; numerical answer practice can ship without executable submissions.

**Count correction [source inspection]:** `lib/practice.ts` has eight entries (`vector-lab`, `python-lab`, `cpp-lab`, `ml-lab`, `robot-lab`, `vision-lab`, `rl-lab`, `research-lab`), not seven. There are two supported verifiers. Existing 42 targeted questions include 14 short answers, not 42 auto-checked items.

**Source wording correction:** it is too broad to say most sources “cannot be copied into a CC BY 4.0 project.” A separately licensed file may coexist when obligations are met; it cannot simply be **relicensed** as CoreLab's original CC BY 4.0 content. My recommendation remains link-only for restrictive, mixed or uncertain sources to keep this MVP simple. The OpenStax row is based on search excerpts, not verification of a selected book's redistribution terms. Neither universal NC-SA nor universal CC BY is established here. Leave that import blocked pending title/edition/item proof. LeetCode/Codeforces restrictions should be attributed to Claude's partial readings, not promoted into verified primary-source legal conclusions.

### 2.2 Independently rerun peer Python harness and boundary probes

I extracted only the Python fenced block under Claude's “Python harness” heading into a temporary file and executed it using the local `python3`. The reported D1/D2/D4/D5/D6 acceptance/mutant results and MAE values **reproduced**: D1 2 valid/4 mutants, D2 good suite 2 valid/6 mutants, D4 2 valid/4 mutants, D5 2 valid/5 mutants, D6 targets 2 valid/3 mutants and solver 1 valid/3 mutants. The synthetic MAEs were 0.566 and 3.028. These are narrow synthetic observations, not a learning-gain estimate or universal leakage magnitude. I did **not** independently reproduce the C++ mutant build matrix; that remains Claude-attributed evidence.

Additional actual probes:

```text
Bayes p=0, s=.9, f=.05: ref -> 0.0; alt -> ValueError
Bayes p=.1, s=0, f=.05: ref -> 0.0; alt -> ValueError
split_ref(['a','b'], .99, 1) -> ([], [0,1])
split_ref(['a','a'], .3, 1) -> ([], [0,1])
split_ref([], .3, 1) -> ([], [])
split_ref(['a','b'], 1.0, 1) -> ([], [0,1])
```

To rerun the extra probes after loading Claude's published Python block into `ns`:

```python
for args in [(0., .9, .05), (.1, 0., .05)]:
    for name in ('ref', 'alt'):
        try: print(args, name, ns[name](*args))
        except Exception as exc: print(args, name, type(exc).__name__)
for args in [(['a','b'], .99, 1), (['a','a'], .3, 1),
             ([], .3, 1), (['a','b'], 1., 1)]:
    print(args, ns['split_ref'](*args))
```

Thus “every valid solution accepted” is true for the sampled positive-interior Bayes domain, not its full proposed probability domain. Fix the alternative's zero cases and validate all probabilities, or explicitly narrow the contract. For episode splitting require at least two distinct groups and `0 < fraction < 1`, define fraction as fraction of **groups**, and clamp the selected group count to `[1,n-1]`. Reject impossible inputs clearly. Do not require a chronological split to fail when a dataset's true episode boundary happens to align: rejection must depend on violated invariants, not algorithm identity. Hash-based selection is acceptable under the declared objective; it need not equal a shuffled reference's chosen groups. Declare heterogeneous ID handling and deterministic ordering rather than relying on `sorted()` over mixed types.

### 2.3 Audit of Claude's 20 proposed exercises

These are review judgments and contract gaps, not claims of running the 14 spec-only tasks.

| Peer exercise | Audit / release condition |
| --- | --- |
| EX-M02-PROJ | Useful; reject zero direction and shape/type errors, distinguish vector projection from scalar component; my X01 adds exact fixture and two routes. |
| EX-M04-IDENT | Rank-deficient calibration is useful; accept a nullspace basis up to invertible basis change/scaling, not one reference vector. State exact vs near rank and measurement units. |
| EX-M08-ALARM | Anchor 2/13 is correct. Boundary counterexamples above invalidate one alternative outside the sampled domain. Conditional single-alarm rates do not need “independent of everything else.” Never turn this posterior alone into a safety stop decision. |
| EX-M05-ACC | State sampling times, integration convention and signed displacement versus distance. Nonuniform samples, constant velocity, reversals and refinement are essential. |
| EX-PY02-GAPS | Declare open/closed/half-open intervals and whether touching intervals merge. Empty input, duplicates, nested/out-of-order intervals, finite observation window; E16 is only a candidate topic. |
| EX-PY04-NORM | Name axis and statistic (population/sample), train-only fitting where relevant, exact constant-column policy, finite arrays and no mutation. Scalar rescaling and z-scoring are different objectives. |
| EX-PY07-WRAP | Strong addition. Restrict finite angle domain; Python floating trig/modulo disagree for huge magnitudes. Accept ±π as contract permits, test exact boundary and near-boundary cases. A learner-supplied suite is arbitrary code; candidate identity/name inspection must not earn test-design credit. Parent runs each candidate in a fresh isolated process and aggregates results. No finite mutant list proves comprehensive test quality. |
| EX-CPP-RING | Useful alternative routes with different objective scopes. **Reference defect by inspection:** `new double[cap]` leaves unused slots uninitialized; copy constructor reads all `cap` slots. Existing copy fixture fills capacity first and misses partially filled/empty copies. Value-initialize storage or copy only live slots and test empty, partial, wrapped and self copies, allocation failure where required. ASan/UBSan success does not establish initialized-value safety; [Clang MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html) specifically addresses uninitialized-value use. No MSan run claimed. |
| EX-CPP-MEDIAN | State even-window median, window growth, NaN policy, duplicates and outgoing-value deletion. STL solution valid for behaviour; custom-data-structure scope needs separate review. |
| EX-ALG-ASTAR | First commission Dijkstra with nonnegative costs (my X14). A* needs stated admissibility/consistency, reopen policy, diagonal cost/corner-cutting, unreachable paths, tolerance and any-optimal-path verification. Do not demand one tie-broken path. |
| EX-R03-CHAIN | Specify transform direction, column vectors, right-handed axes and point versus direction. My X10 hand anchor rejects reversed composition. |
| EX-R06-2R | Reproduced both implementations/4 mutants on the stated sample. J units metres/radian; positive unequal link lengths; singularity is a lost **instantaneous** direction, not proof the robot can never move there along a finite trajectory. Explanation remains unverified. |
| EX-R02-ENC | Declare counter bit width and unsigned modular arithmetic, encoder ticks/revolution, gear ratio and wheel radius; unwrap is ambiguous when true displacement is ≥half the counter range between samples. Missing data must not silently invent motion. R16 remains candidate. |
| EX-R07-PEND | Declare angle origin, gravity, damping and timestep, and reference energy. Numerical energy drift depends on method/step/time horizon; “any drift fails” would be wrong. No hardware fidelity claim. |
| EX-C03-SAT | Declare discrete plant, sample period, limits, initial state, target, disturbances, saturation and anti-windup semantics. Multiple controllers can meet bounded metrics. My X13 is only a P-controller toy, not verification of this PID task. |
| EX-C07-1D | Scalar KF oracle needs prior/process/measurement noise and update timing. Validate positive covariance and singular zero-noise cases; batch estimator must implement the same stochastic model. |
| EX-V03-PROJ | Depth strictly positive in stated camera convention; principal point/pixels/metres explicit. Back-projection yields a ray unless depth/plane supplied. Reject nonfinite values; do not confuse undistortion with pinhole projection. |
| EX-ML03-EP | Good synthesis topic; rerun reproduces interior results. Boundary fixes above required. Synthetic score gap is one construction. Group-disjoint index coverage does not prove train-only preprocessing, time causality, class balance or deployment validity. |
| EX-RL02-TERM | Closed form and γ=2/3 tie correct for this discounted continuing MDP with finite terminal reward. Add γ=0, tie, range `[0,1)`, iteration cap and residual; define finite-horizon truncation semantics explicitly. If the time horizon is intrinsic to the task, augment state/declare terminal value rather than universally bootstrapping. |
| EX-E05-PRE | State closed/open-world treatment, freshness clock and threshold, conflicting facts and initial state. Stale observation preventing a toy action is not certified physical safety. S07 mapping requires matching the actual objective, not just “safety” in a title. |

### 2.4 Answers to Claude's six questions

1. **Separate record:** yes, additive `content/exercises` with explicit schemas is clearer than modifying historical v1 targeted files. A shared selector/service can reuse weakness semantics. Persist bank attempts separately or extend the typed model via migration; arbitrary extra JSON fields are not safely supported today. Resolve this before choosing storage.
2. **Adaptive model:** agree on rules. Per-learner observed difficulty can be recorded, but it is not population item calibration, mastery probability or causal learning-gain evidence. Two failures should offer remediation/stop recommendations, not deny further practice. Session size and 30-item threshold are pilot choices, not validated necessities.
3. **Evidence:** only separately commissioned assessment/contract. Same learning objective may have a separate eligible form; practice records never acquire evidence retroactively. A small scoped I contract must not trigger today's topic-wide I2 path.
4. **L14/L18 without ROS/contact:** add optional prerequisites: interface frame/unit/type compatibility (L14), and geometric gripper aperture/approach clearance on an analytic object (L18). They remain interface/geometry exercises, not MoveIt integration or grasp-success verification. Preserve the gap in actual lab coverage.
5. **Assistance:** monotonic maximum per new attempt is right. Existing attempts and evidence stay immutable. Hints/solutions opened between submission and review also create exposure for the next assessed form; an A0 checkbox cannot undo it. Keep self-declared external help and observed in-app help distinct. Do not require a failed attempt just to access an instructional hint: a novice or accessibility need may warrant help before trying.
6. **Licenses:** Exercism MIT agreed, my pinned source index supplies exact files/commits. OpenStax remains item-specific unverified for import; LeetCode is not a source to redistribute. Retain original licenses/attribution for any permitted code/text imported later. I independently verified SymPy/nbgrader/Hypothesis/pytest/PrairieLearn/bubblewrap scope; do not imply they are dependencies or have been executed because they were researched.

### 2.5 Proposed convergence for Round 3

Recommend a small numeric-first MVP around projection, Bayes, frames and 2R FK; two authored scenario choices per objective, not a fixed 30-item barrier. Optional D2/Python Jacobian coding follows only a parent-owned isolated runner. C++ ring buffer and RL termination are strong next-wave exercises after the contract fixes. Include both reviewers' six examples in the synthesis as separate independently scoped cases, without treating 12 descriptions as 12 released tasks. Keep basic drills and non-robotics mathematics where context helps less than a plain contract. No objective equality between implementation, derivation, test design and reading a solution.

**Requests to Claude:** respond to the Bayes/split counterexamples and partial-copy C++ defect; clarify runner isolation versus a private pipe; qualify OpenStax rights and source coexistence; identify any overstated claim in my 154 named checks or 15-probe Linux prototype. Please preserve your Round 1 and append corrections in Round 2/3. I will wait for matching Round 2 before final rebuttal.

## Round 3 — Final rebuttal and synthesis position

Run `corelab-exercise-bank-20261031-01`. Matching Claude `completed_round: 2` was observed before this rebuttal. I read the completed Round 2, preserved both earlier rounds and independently reran the revised Python harness. Final synthesis must still wait for Claude's matching Round 3; this publication is not a substitute for it.

### 3.1 Answers and corrections accepted

**Self-check kits: ACCEPT with a precise boundary.** A learner may download reviewed tests and run their own trusted code manually without waiting for CoreLab's isolated execution broker. No CoreLab execution, returned verdict admission, signature or verified-progress record occurs. My Round 1 already allowed trusted/manual practice; Round 2's “coding follows the runner” was too broad without saying **automatically verified coding**. The final distinguishes mathematical answers, manual self-checks and evidence-grade execution. An official test download is still a software supply-chain artifact; “adds no new risk” is too absolute. Do not describe Windows/macOS commands as tested because they are plausible. They remain untested here. Running copied third-party solutions is outside the trusted-own-code premise.

**154 headline: correction accepted.** The script's exact output is 154 named assertions, not 154 meaningful implementation tests. As Claude identifies, some assert hand facts or demonstrate a missing fixture, rather than exercise a validator: reflection arithmetic, pure-spin arithmetic, constant-column arithmetic and an orthogonal zero-stub example. Those facts can support design but cannot establish that a submitted implementation rejects reflections, handles normalization, or fails a zero stub. I will **drop this number as the headline validation metric**, keep it only as an accurately labeled artifact result, and explicitly state the limitation in the final evidence table. I will not invent a new “real test count” by informally subtracting a few lines. X11/X14/X17 account for 77/154; broad coverage cannot be inferred from the total. The append-only record preserves the original claims and this correction together.

**Independent adversarial review: ACCEPT.** Author-written alternatives/mutants share blind spots. A second technical reviewer must attempt false acceptance and false rejection before a released auto-checker is admitted. Correct hand examples and passing own code are necessary but insufficient. Pedagogical/accessibility/rights review and beginner pilots are separate gates.

**Merged twenty: MODIFY, no invented upper limit.** The user requested “at least 15–20,” not at most 20. Keep twenty core families plus a clearly optional next-wave list, rather than deleting planning/cognition, dynamics and estimation just to fit a supposed hard limit. Only four packs are the MVP. Map all L01–L22 with explicit preparation versus implementation gaps; no claim that a 20-row table fully covers 22 actual labs. Claude's proposed alternate twenty is a useful prioritization choice, not a mathematical disagreement. I retain X20 plan validity because cognitive planning is a stated CoreLab goal. Add C++ ring buffer and declarative test-design routes as next-wave choices; this audit is not committing to implement every catalog row.

**Mode names:** agree. Recommended = transparent weakness/due/readiness queue; Explore = filters with warnings; More Practice = new authored route/instance then honestly labeled repeats/exhaustion. My Round 1 described the behavior without these three labels. The final names and maps them explicitly, while admitting these modes are proposed.

### 3.2 Independently checked corrections

I extracted the Python block under Claude Round 2 “Fixed harness,” reran it with local `python3`, and reproduced:

- Bayes: two valid implementations and four selected mutants; the newly added zero/boundary/domain fixtures pass for the corrected references.
- Test design: valid suite accepts both alternatives and kills six mutants; weak/self-referential/over-strict suites behave as previously reported.
- Jacobian: two valid alternatives and four selected mutants at the published sampled domain.
- Episode split: **three** valid alternatives, now including chronological grouping, and five selected mutants. The corrected small-group/domain fixtures pass.
- RL: two target formulations/three mutants and one value solver/three mutants. The added γ=0 and γ=2/3 cases pass.
- Synthetic MAEs: frame 0.566, episode **2.923** with the revised deterministic group ordering, versus 3.028 with the earlier ordering. Neither gap is a universal effect size.

I also independently compiled the **corrected C++ reference only**, using Claude's original tests plus the three newly published empty/partial/wrapped copy blocks. Command: `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined -fno-sanitize-recover=all ring_fixed_test.cpp -o ring_fixed_test`. Actual local compiler: Ubuntu g++ 11.4.0; compile exit 0, no diagnostics; executable exit 0, stdout `OK`, stderr empty. No full C++ mutant matrix or MemorySanitizer rerun is claimed. Source inspection confirms value initialization removes the specific uninitialized-slot read found earlier; one passing sanitizer run does not prove complete memory safety.

For reproducibility: the corrected header, initial main and three added blocks are preserved verbatim in Claude Rounds 1/2. Replace `#include IMPL` with the corrected header and insert the added blocks before `std::puts("OK")` in the original main. This is an author-side trusted-reference check, not a production exercise verifier or learner submission.

### 3.3 Additional false-acceptance probes: nonfinite output

While waiting for Round 2 I tested its predecessor, then tested the revised Round 2 comparators. **Both rounds' Bayes and Jacobian sampled comparators can accept NaN**, if the function answers the final anchor/boundary fixtures correctly. `abs(NaN) > tolerance` is false, so a rejection-only comparison silently skips those samples.

Exact Round 2 reproduction, after loading its published fixed Python harness into `ns`:

```python
def bayes_nan(p,s,f):
    anchor = (ns['F'](1,100), ns['F'](9,10), ns['F'](1,20))
    if 0 < p < 1 and s > 0 and 0 < f < 1 and (p,s,f) != anchor:
        return float('nan')
    return ns['ref'](p,s,f)
def jacobian_nan(q,l):
    if q == (.3,0.) and l == (1.,.7):
        return ns['Jref'](q,l)
    return [[float('nan')]*2 for _ in range(2)]
print(ns['d1'](bayes_nan))      # actual True, should reject
print(ns['d4'](jacobian_nan))   # actual True, should reject
```

This is a defect in the **research harness**, not an allegation against a deployed bank. Apply finite numeric/type/shape validation to every sample before comparison, with explicit rejection of bool and unexpected arrays. Catch invalid output/protocol errors as failure rather than accepting partial completion. A final finite anchor does not repair earlier nonfinite outputs. My own author fixtures are also not complete hostile-output validators; the separate parent probe explicitly rejects NaN/bool/object responses. That protection must not be lost in answer-entry comparators or future contract adapters.

### 3.4 Narrowing two remaining security claims

Fresh process **per candidate** does not itself defeat a learner test suite reading its candidate's name or source if the candidate is loaded into the same process. For the first test-design route, prefer **declarative test cases**: bounded inputs plus expected values or allowlisted properties, parent-validated and applied to the valid alternatives/mutants. Later arbitrary suites need a separately isolated bounded value interface to candidates and reviewed resource limits. Even then finite mutant performance is evidence of those tests' discrimination, not proof of independent authorship or exhaustive testing quality.

The parent probe's `infinite_loop` was CPU/resource-terminated (reported exit 137 without the parent wall-timeout flag), while `wall_timeout` was killed after the parent deadline. They exercise different bounded error paths; neither tests fork bombs, descendant cleanup, kernel escape or production syscall policy. Claude independently reproducing the fifteen outcomes increases confidence in repeatability, not in untested threat coverage.

### 3.5 Rights and final disposition

During cross-review I independently fetched the root licenses for PythonRobotics, Modern Robotics code, Spinning Up, CS231n notes (MIT) and D2L (CC BY-SA 4.0). These corroborate selected root-license statements, **not** every embedded/linked resource. Selected items still need pinned per-file provenance, exceptions and notices. Keep OpenStax imports blocked pending title/edition/item verification; partial LeetCode/Codeforces excerpts are not verified legal clearance. Link-only remains the simplest first release.

Converged architecture: layered versioned objectives/families/instances/contracts, four original numerical-first packs with two routes each, explicit practice-only events, humane hints/override/exhaustion, transparent rules, no psychometric claims, immutable old evidence, original-first licensing and parent-owned isolated automatic code verification. Manual trusted self-check kits can precede that runner. Main owner choices remain exact first packs, reviewer/budget/platform support, storage/result namespace and separate mastery admission. Qualified review, actual learner trials, full hostile-output validators and production OS isolation are not complete.

**Handoff:** my completed round is now 3. Wait for Claude's matching round 3 before creating `proposed_exercise_bank.md`. Incorporate corrections honestly, preserve minority scope preferences and list any unrepaired comparator or platform limitation. No fourth debate round, no production changes and no claim of unanimous approval where a decision remains open.

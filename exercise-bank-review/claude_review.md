# CoreLab Exercise Bank review — Claude

Run ID: `corelab-exercise-bank-20261031-01`. Baseline: CoreLab `38b6a1d`. Read: `curriculum-review/proposed_curriculum_v2.md`, `corelab-labs-review/proposed_practical_learning_system.md`, `lib/practice.ts`, `lib/weaknesses.ts`, `lib/engine.ts`, `docs/guide.md`, `content/practice/`. This is a proposal. Nothing in production, curriculum, assessments or evidence was changed.

## Round 1 — Independent research

No Codex file for this run was read before this round was published.

### 1.0 Findings in brief

1. **CoreLab should write its own exercises and link out to the rest.** Most famous sources cannot be copied into a CC BY 4.0 project: MIT OCW, Project Euler and current OpenStax titles are NonCommercial-ShareAlike; Modern Robotics states no reuse terms; LeetCode claims its questions as its content.
2. **An exercise bank is a practice system, not a second assessment system.** Exercise attempts stay `purpose: targeted`, which `lib/engine.ts:70` already excludes from mastery. Evidence still requires a separate fresh assessed form.
3. **Three modes are enough, with simple rules.** Recommended is a transparent rule list with a stated reason. Explore is free browsing with warnings only. More Practice gives fresh variants on one skill and honestly reports when they run out. I reject IRT and Bayesian Knowledge Tracing for now: a single-user local app has no data to fit them.
4. **20 exercises are proposed; 6 are detailed and were actually run.** Every valid solution was accepted and every injected bug rejected ([T], 1.11). The other 14 are specifications only and are labelled so.
5. **The most useful test of an exercise is whether it rejects bad work and accepts varied good work.** Test-writing exercise D2 rejected a weak suite, a self-referential suite, and a suite too strict about the ±π boundary, which would reject valid code. A first draft of that contract could have failed correct `atan2` solutions.
6. **Coverage of the 22 labs is incomplete.** L14 and L18 have no exercise yet. Named in 1.9.

Labels: **[T]** I ran it. **[R]** I read it in a repository or page. **[X]** External source, linked. **[E]** My estimate.

### 1.1 What exists today [R]

| Item | State | Consequence |
| --- | --- | --- |
| `content/practice/*.v1.json` | 42 questions in 7 banks, each 2 choice + 2 number + 2 short | Keep unchanged. New exercises are additive |
| `lib/practice.ts` | 7 practice tasks; only M02 and PY01 have verifiers | The others are honestly unverified |
| `lib/engine.ts:70` | `purpose: "targeted"` attempts do not count toward mastery | Exactly the right boundary for exercises |
| `lib/weaknesses.ts`, guide | Weakness derived from attempt history; deterministic selection; corrected only by fresh A0 evidence | Reuse this; do not build a parallel weakness model |
| `lib/engine.ts:79-82` | Any trusted A0 lab sets `I=2` for the whole topic | Exercises must never reach this path |
| `scripts/lab-tests.py` | Forged stdout passes (both reviewers reproduced it in the last run) | Any exercise runner must have a result channel learner code cannot write by printing |

No "Recommended", "Explore" or "More Practice" mode exists in the code. Recommendation today concerns lessons and weak skills.

### 1.2 Sources: what can be used and how

Dates checked 2026-10-31. **This is not legal advice**; owner should get review before copying anything. CoreLab content is CC BY 4.0 and code is MIT (`README.md`), so NonCommercial or ShareAlike material cannot simply be merged in.

| Source | Terms found | Evidence | Allowed use here | Best for |
| --- | --- | --- | --- | --- |
| [Exercism](https://github.com/exercism/problem-specifications) (`python`, `cpp`, `problem-specifications`) | MIT | LICENSE files read | Link; can adapt with notice after per-exercise check | Language fluency, test-first habits |
| [PythonRobotics](https://github.com/AtsushiSakai/PythonRobotics) | MIT | LICENSE read | Link; reference code with notice | Robotics algorithm reading |
| [Modern Robotics code](https://github.com/NxRLab/ModernRobotics) | MIT | LICENSE read | Could serve as a second oracle in CI | Kinematics cross-checks |
| [Modern Robotics book](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) | Free preprint; **no reuse terms stated**; end-of-chapter solutions instructor-only | Page read | **Link only.** Do not copy problems or publish solutions | Canonical robotics problems |
| [Spinning Up](https://github.com/openai/spinningup) | MIT | LICENSE read | Link; adapt with notice | RL exercises |
| [CS231n notes repo](https://github.com/cs231n/cs231n.github.io) | MIT for that repo | LICENSE read; assignments not checked | Link | Vision and ML |
| [Dive into Deep Learning](https://github.com/d2l-ai/d2l-en) | CC BY-SA 4.0 at root | LICENSE read; code terms not checked | Link. Adapted prose would carry ShareAlike | ML exercises |
| [MIT OCW](https://ocw.mit.edu/pages/privacy-and-terms-of-use/) | CC BY-NC-SA 4.0; third-party content may be excluded | Terms page read | **Link only** | Maths, algorithms, probability sets |
| [OpenStax](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks) | Help pages say CC BY-NC-SA; older titles may differ. Licensing update page not readable by my tool | Search excerpts | **Link only**, check each title | Foundation maths |
| [Project Euler](https://projecteuler.net/copyright) | CC BY-NC-SA 4.0 | Search excerpt | Link only | Maths-programming puzzles |
| [LeetCode](https://leetcode.com/terms) | Excerpts: questions and solutions are its Content; scraping barred. My full fetch got HTTP 403 | Search excerpts; **not fully read** | **Link only, no import or scraping**, no evidence from it | Interview-style algorithms |
| [Codeforces](https://codeforces.com/blog/entry/967) | A moderator-posted v0.1 license restricts publishing tests or checkers on auto-judging sites; currency unclear | Search excerpt | Avoid importing | Contest practice |
| Competitive Programmer's Handbook | BY-NC-SA per a repository copy, not the publisher | Secondary | Link only after checking | Algorithm explanations |

**Rule.** Every exercise records a `source` field: `original` with concept-level inspiration links, or `adapted` with exact file, commit and license. Text, tests and solutions are never pasted from a link-only source. External links are optional More Practice and never produce evidence.

**Prioritization.** Exercise text in CoreLab draws on robot-relevant situations. Generic drills from sources above support fluency only. Interview-style problems are not a goal; they appear when the same skill transfers, for instance merging intervals applied to sensor dropouts.

### 1.3 Learning-science basis, and its limits

| Finding | Source | How it is used | Limit |
| --- | --- | --- | --- |
| Interleaving improved later math test scores while looking worse during practice | [Rohrer & Taylor 2007](https://doi.org/10.1007/s11251-007-9015-8); [Rohrer et al. 2015](https://doi.org/10.1037/edu0000001) | Recommended mixes due skills | School mathematics. A search result also mentions a 2026 field study with no end-of-year effect; I did not verify it. Not shown for programming |
| Worked examples help novices and can hinder advanced learners | [Kalyuga et al. 2003](https://doi.org/10.1207/s15326985ep3801_4) | Hints fade; placement skips examples | Direction only; no threshold |
| Learners do not reliably seek help well | [Aleven & Koedinger 2000](https://doi.org/10.1007/3-540-45108-0_33) | Hints require an attempt first; usage recorded automatically | Studied in a specific tutor |
| Practice testing and spacing | Already cited in Curriculum V2 | Reuse 1/3/7/21 schedule | Exact schedule remains a heuristic |

CoreLab's specific combination is untested. **No learning gain is claimed.**

### 1.4 Exercise record

Separate new files, for example `content/exercises/<ID>.v1.json`. Existing practice and diagnostics stay byte-identical.

```json
{
  "id": "EX-R06-2R", "version": 1,
  "title": "Which way can't the arm move?",
  "domain": "robotics", "specializations": ["manipulation"],
  "application": "Detect a singular arm pose before commanding it",
  "topicScope": [{ "topicId": "R06", "objective": "planar-endpoint-jacobian" }],
  "labLinks": ["L06"], "prerequisites": ["R04", "M06"],
  "knowledgeType": "implementation", "dimensionPracticed": ["M", "I"],
  "difficulty": { "authored": 3, "calibrated": null, "basis": "structural" },
  "estimatedMinutes": [30, 60],
  "skillTags": ["jacobian-relative-angle"],
  "variants": { "generator": "params-v1", "transfer": ["3-link", "new base offset"] },
  "checks": { "oracle": "central-difference", "validSolutions": 2, "mutantsRejected": 4 },
  "hints": ["A1 concept...", "A2 specific...", "A3 solution..."],
  "remediation": [{ "misconception": "absolute angles", "href": "/lessons/R04" }],
  "source": { "kind": "original", "inspiration": [] },
  "review": { "technical": null, "pedagogical": null }
}
```

Attempts reuse today's `purpose: "targeted"` shape, extended with exercise ID, variant seed and hint history. **`dimensionPracticed` is deliberately not `dimensionEvidence`.**

### 1.5 Three modes

| | Recommended | Explore | More Practice |
| --- | --- | --- | --- |
| **For** | "What should I do now?" | Curiosity, a goal not chosen yet | "Give me another of these" |
| **Selection** | Rule list in 1.6, shows reason per item | Filter by domain, application, difficulty, lab, specialization | Same skill tag, unseen variants first |
| **Prerequisites** | Respected | **Warning only**, never blocked | Inherited; warning if skill was failed before |
| **Size** | Short session: 3–5 by default, learner adjustable | Learner picks | Learner stops; see limits |
| **Mixing** | Interleaves due skills | None | Blocked by design, then offers one mixed item |
| **Changes evidence?** | No | No | No |
| **Honest ending** | "Nothing due; try a goal" | Empty filter message | "No unseen variants; the rest are repeats, which show memory, not fresh skill" |

The existing weakness view stays. Recommended draws on it instead of replacing it.

### 1.6 Adaptive policy: rules, not a model

**Rejected for now:** IRT, Bayesian Knowledge Tracing, or LLM-picked items. Each needs item or population data this local single-user app does not have, and their output cannot be explained simply. Revisit only with consented pilot data.

Priority order, first match wins per slot:

1. Unresolved weakness on a prerequisite of the active goal.
2. Due reviews (existing scheduler), prioritizing active goals, within a learner-set daily budget.
3. Next unpracticed skill for the goal whose prerequisites have no active weakness.
4. One mixed item from an earlier skill.
5. One optional application or specialization item.

**Difficulty step.** Solved A0 with no hint on the first try: next item may go one level up, or skip further same-level drill (the expertise reversal direction). A failed or hinted attempt: same level, new variant. **Two failures on one skill in a session: stop drilling**, show remediation and suggest a different skill; repeating the same drill is not treated as helping. These thresholds are starting rules to pilot, not findings.

**Honest limit.** Time on task and self-declared A0 are weak signals. Rules must tolerate a wrong signal: a learner can always override.

### 1.7 Hints, remediation and independent assessment

**Hints map onto the existing scale; no new levels.**

| Step | Reveals | Recorded |
| --- | --- | --- |
| No hint | Nothing | A0 **as declared**; AI help outside CoreLab cannot be detected, so the declaration remains |
| Hint 1 | Concept or question to ask, after one attempt | A1 |
| Hint 2 | Specific next step or small example | A2 |
| Hint 3 | Full solution with reasoning | A3 |

Assistance is taken from the highest hint opened and **cannot be downgraded**. Opening a hint is normal, never a penalty in Recommended. After A3, the same variant is finished and only a fresh structurally different task can show independence.

**Remediation path.** Failure output, likely misconception, minimal counterexample, targeted lesson link, fresh variant at A0. Feedback states what it knows: "your J fails finite differences at q₂≠0" is observed; "you confuse absolute angles" is a likely cause. No conceptual diagnosis from a format or rounding error, per the M08 finding in Curriculum V2.

**Independent assessment stays separate.**

| Claim | Requires | Exercises alone? |
| --- | --- | --- |
| C, M at L1 | Fresh diagnostic form per Curriculum V2 gates | **No** |
| I at L2 | Versioned scoped contract, signed report, new runner | **No.** An exercise can become a contract only by separate approval |
| T | Delayed repetition is retention; unfamiliar transfer needs a reviewer | **No** |
| L3, L4 | Qualified reviewer | **No** |
| Weakness "independently corrected" | Existing rule: fresh correct A0 equivalent | **Yes, through existing mechanism**, marked targeted, and never raising the level |

**Exposure.** A variant seen in practice must not be the assessed form. Seeds and hint history record exposure. Locally inspectable generators are not secret, so this deters shortcuts and does not prevent them.

**Historical evidence.** No old attempt, report, hash or level changes meaning. Exercises do not backfill anything.

### 1.8 Verifying exercise quality

| Gate | Pass condition | Applies |
| --- | --- | --- |
| **G1 Source** | `source` complete; no text or tests from link-only sources | All |
| **G2 Prompt** | Self-contained: units, conventions, format and precision stated. Would have caught the M08, ML02, ML05 and RL02 defects | All |
| **G3 Solution** | At least two independent solutions agree, or a formula and an enumeration | Auto-checked |
| **G4 Rejects bugs** | Named mutants all rejected, in CI | Auto-checked |
| **G5 Accepts valid work** | Valid alternative solutions accepted; tolerance justified by measured margins with units and domain | Auto-checked |
| **G6 Variants** | Every generated variant well-posed and solvable; meaningfully different, not just new constants, for transfer | Auto-checked |
| **G7 Hints** | Hint 1 and 2 do not contain the answer; hint 3 is correct | Human |
| **G8 Expert review** | Technical and pedagogical reviewers named | Human; **no reviewer exists yet** |
| **G9 Accessibility** | Text alternatives; no colour-only meaning | Human |
| **G10 Pilot** | Item statistics reviewed | After data |

**Difficulty.** Level 1–5 is authored from structure: number of concepts combined, steps, and whether the learner chooses the method. `calibrated` stays null until pilot data. Single-learner data cannot calibrate items; a local single user can only flag an item as much harder than authored. **No item is called "easy" or "hard" from authoring alone without saying so.**

### 1.9 Twenty proposed exercises

`Run` means reference, alternative and mutants executed. `Spec` means described only. Levels are authored.

| # | ID | Domain | Task and application | Topics | Labs | Lvl | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | EX-M02-PROJ | Maths | Project a velocity command onto an allowed direction; handle a zero direction | M02 | L01 | 2 | Spec |
| 2 | EX-M04-IDENT | Maths | Which calibration parameters can two dependent sensors not recover? Rank and nullspace | M04 | L06, L21 | 3 | Spec |
| 3 | **EX-M08-ALARM** | Maths | Posterior for a fault alarm at low base rate | M08 | L09 | 2 | **Run** |
| 4 | EX-M05-ACC | Maths | Displacement from a sampled velocity log; units, refinement | M05 | L03, L07 | 2 | Spec |
| 5 | EX-PY02-GAPS | Algorithms | Merge sensor dropout intervals and report longest good window | PY02, E16 | L05, L19 | 2 | Spec |
| 6 | EX-PY04-NORM | Python | Normalize a batch on the correct axis, constant column, no mutation | PY04, ML03 | L19 | 2 | Spec |
| 7 | **EX-PY07-WRAP** | Python | Write tests for `wrap_angle` that catch bugs without over-constraining | PY07, T04 | L03, L05 | 3 | **Run** |
| 8 | **EX-CPP-RING** | C++ | Fixed-capacity sensor ring buffer with correct copy and no leaks | CPP02, CPP03, CPP08 | L05 option | 3 | **Run** |
| 9 | EX-CPP-MEDIAN | C++ | Sliding-window median for a noisy range sensor; compare costs | CPP05, CPP09 | L09 | 3 | Spec |
| 10 | EX-ALG-ASTAR | Algorithms | A* on a weighted grid, disconnected case, heuristic check | PY02, E02 | L11, L13 | 3 | Spec |
| 11 | EX-R03-CHAIN | Robotics | Marker seen by a wrist camera, expressed in the base frame | M12, R03 | L01, L02, L12 | 2 | Spec |
| 12 | **EX-R06-2R** | Robotics | Endpoint Jacobian and singular direction of a 2R arm | R06 | L06 | 3 | **Run** |
| 13 | EX-R02-ENC | Robotics | Encoder rollover to wheel distance with sign and overflow | R02, R16 | L03 | 2 | Spec |
| 14 | EX-R07-PEND | Robotics | Pendulum energy under two integrators; explain drift | R07, M07 | L08 | 3 | Spec |
| 15 | EX-C03-SAT | Control | Limited PID on a declared plant; recover from saturation | C01, C03, C09 | L04 | 3 | Spec |
| 16 | EX-C07-1D | Control | 1-D Kalman filter against a batch answer | C06, C07 | L10 | 3 | Spec |
| 17 | EX-V03-PROJ | Vision | Project and back-project with declared image axes; invalid depth | V01, V03 | L16, L17 | 2 | Spec |
| 18 | **EX-ML03-EP** | ML | Split by episode and show how frame splitting flatters a model | ML03, ML07, E16 | L19 | 3 | **Run** |
| 19 | **EX-RL02-TERM** | RL | Termination versus truncation, then value iteration | RL02, RL04 | L20 | 3 | **Run** |
| 20 | EX-E05-PRE | Planning | Check action preconditions; a stale observation must block a command | E05, S07 | L15, L22 | 3 | Spec |

**Specializations (optional tags, never requirements).** Manipulation: 2, 11, 12, 14. Mobile: 4, 13, 10, 16. Perception: 17. Software: 7, 8, 9. Learning: 6, 18, 19. Cognitive: 20.

**Difficulty spread:** 7 at level 2 and 13 at level 3. **This is a gap.** Levels 1, 4 and 5 are missing from this starter set: level 1 fluency could come from existing banks and Exercism links, and levels 4–5 are largely the labs themselves.

**Lab coverage.**

| Lab | Exercises | Lab | Exercises |
| --- | --- | --- | --- |
| L01 | 1, 11 | L12 | 11 |
| L02 | 11 | L13 | 10 |
| L03 | 4, 7, 13 | **L14** | **None yet** |
| L04 | 15 | L15 | 20 |
| L05 | 5, 7, 8 | L16 | 17 |
| L06 | 2, 12 | L17 | 17 |
| L07 | 4 | **L18** | **None yet** |
| L08 | 14 | L19 | 5, 6, 18 |
| L09 | 3, 9 | L20 | 19 |
| L10 | 16 | L21 | 2 |
| L11 | 10 | L22 | 20 |

An exercise prepares for a lab; it never replaces a lab's PASS.

### 1.10 Six detailed exercises

Each lists the task, oracle, misconceptions, hints and fresh variants. Results are in 1.11.

#### D1 — EX-M08-ALARM: Is the alarm real?

- **Application.** A fault alarm on a robot arm. Should you stop the line?
- **Task.** Faults occur in fraction `p` of cycles. The alarm fires with probability `s` given a fault and `f` given no fault, independent of everything else. Implement `posterior(p, s, f)` returning P(fault | alarm); raise `ValueError` if the alarm can never fire. **Accepted numeric answers:** decimal within 1e-9 of exact in code; on-paper answers may be fractions.
- **Predict first.** With p = 1%, s = 90%, f = 5%, guess before computing.
- **Hand anchor.** 0.009 / (0.009 + 0.0495) = 2/13 ≈ 0.1538. Most guesses are far higher.
- **Oracle.** Exact count table with `Fraction` over N cycles, independent of the formula form.
- **Misconceptions as mutants.** Returns `s` (inverse conditional). `s/(s+f)` (ignores base rate). Omits `(1-p)`. Returns `s·p` (forgets to normalize).
- **Hints.** A1: "Picture 10,000 cycles. How many have faults?" A2: "Count alarms from both groups, then ask what share are real." A3: full table and formula.
- **Fresh variants.** Different rates. **Transfer:** two alarms that are stated to be correlated, so the learner must say independence cannot be assumed.
- **Evidence.** Practice only. M08 diagnostics stay separate. Level 2, 15–30 min [E].

#### D2 — EX-PY07-WRAP: Tests that actually test

- **Application.** Heading errors in odometry and controllers.
- **Task.** `wrap_angle(a)` returns an angle in [−π, π] equal to `a` modulo 2π. **Do not write the function; write the tests**, as `suite(wrap)` raising `AssertionError` on failure.
- **Grading.** The suite must pass on two correct implementations (`atan2` and modulo), and fail on six broken ones: single subtraction, 0..2π range, identity, negated, no negative wrap, constant.
- **Rejected in my run:** a suite only checking `wrap(0)==0` (0/6 caught); a suite comparing `wrap(3.5)` with itself (0/6 caught); and a suite requiring `wrap(-π)==π` exactly, which **rejects correct code** because `atan2` returns −π there. **This is the point of the exercise:** both weak tests and over-strict tests fail.
- **Misconceptions.** Expected value computed by the code under test; float equality; testing only typical values; over-specifying a boundary the contract leaves open.
- **Hints.** A1: "What would a wrong function do at 7 radians?" A2: "Check range and sameness modulo 2π, instead of exact values." A3: an example suite.
- **Fresh variants.** A different function each time, such as `clamp` with reversed bounds. **Transfer:** a bug report with a minimal reproducer.
- **Evidence.** Practice for PY07 and T04, scored separately. Level 3, 30–60 min [E].

#### D3 — EX-CPP-RING: A buffer for sensor messages

- **Application.** Keep only the newest N samples without unbounded memory.
- **Task.** C++17 `RingBuffer(size_t cap)`: `push` overwrites the oldest when full; `pop` returns `std::optional<double>` oldest first; `size()`. Capacity 0 throws `std::invalid_argument`. Copies must be independent. Build and run under the flags below.
- **Command.** `g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined -fno-sanitize-recover=all`. Linux tested with g++ 11.4. **Windows and macOS untested;** MSVC flags differ.
- **Both routes count.** Raw `new[]` with copy-and-swap teaches CPP02 and CPP03. `std::deque` is simpler and passes behaviour. It does not practice manual ownership, so the exercise states which objective was practiced instead of pretending they are equal.
- **Mutants.** Listed with their detector in 1.11; the sanitizers catch three that plain assertions would not.
- **Hints.** A1: "What happens to indices when head reaches capacity?" A2: "Who owns the array after `b = a`?" A3: reference.
- **Fresh variants.** Generic `T`. **Transfer:** a timestamped buffer that drops messages older than a limit.
- **Evidence.** Practice. C++ currently has no verifier, and this does not create one. Level 3, 45–90 min [E].

#### D4 — EX-R06-2R: Which way can't the arm move?

- **Application.** Warn before commanding a stretched-out arm.
- **Task.** Implement `jacobian(q, l)` for a planar 2R arm with **relative** joint angles and unequal links, returning the 2×2 endpoint Jacobian in metres per radian. Then explain which direction is lost at q₂ = 0.
- **Predict first.** Sketch the arm stretched. Can the tip move along the arm?
- **Oracle.** Central differences of an independent FK at 200 random poses and two step sizes, tolerance 1e-5, plus det J = 0 at q₂ = 0.
- **Valid alternative.** Building columns from joint positions, a cross-product form. Accepted.
- **Mutants.** Absolute angles, swapped rows, missing term, sign flip.
- **Hints.** A1: "Which joints move link 2?" A2: "Differentiate x(q₁, q₂) with respect to q₁ using q₁+q₂." A3: derivation.
- **Fresh variants.** Link lengths; a nonzero base offset. **Transfer:** a 3-link planar arm, where J is no longer square.
- **Evidence.** Practice for R06 ahead of L06's contract. The explanation stays unverified unless reviewed. Level 3, 30–60 min [E].

#### D5 — EX-ML03-EP: The split that flatters

- **Application.** Robot demonstration data, where frames in one episode are nearly duplicates.
- **Task.** `split_by_episode(episode_ids, test_frac, seed)` returns train and test indices: every index once, no episode in both, both non-empty, same seed gives same split. Then run the supplied 1-nearest-neighbour experiment with both splitters and explain the gap.
- **Observed [T].** On a synthetic set of 20 episodes with 30 frames each, mean absolute error over 5 seeds was **0.566 for a frame split and 3.028 for an episode split**. Same model, same data. The frame split's score is an artifact.
- **Mutants.** Frame shuffle, time-tail cut, empty test, non-deterministic, duplicated indices.
- **Valid alternative.** Hash-based assignment. Accepted.
- **Hints.** A1: "What does the test set contain that train also saw?" A2: "Choose episodes first, then gather frames." A3: reference.
- **Fresh variants.** Unequal episode lengths; session IDs above episodes. **Transfer:** also fit normalization on train only.
- **Evidence.** Practice for ML03, ML07, E16, preparing L19. Level 3, 30–60 min [E].

#### D6 — EX-RL02-TERM: Ended, or just out of time?

- **Application.** A robot episode cut off by a time limit is not a robot that reached a terminal state.
- **Task.** (a) `td_target(r, v_next, gamma, terminated, truncated)`. (b) `value_iteration(mdp, gamma, tol)` on a small stated MDP: in A, `finish` gives reward 3 and terminates; `wait` gives reward 1 and returns to A.
- **Closed form.** V(A) = max(3, 1/(1−γ)). **Predict:** at which γ does waiting become better? Answer: γ > 2/3. All conventions are stated in the prompt, avoiding the RL02 ambiguity Curriculum V2 found.
- **Oracle.** Closed form at γ ∈ {0.5, 0.6, 0.9, 0.95}. Exact target values at the three cases.
- **Mutants.** Bootstrapping at termination; not bootstrapping at truncation; no discount; average instead of max; one sweep only; a reward at the terminal state.
- **Hints.** A1: "Is there a future after a time limit?" A2: "Only `terminated` zeroes the future." A3: reference.
- **Fresh variants.** Changed rewards. **Transfer:** add stochastic transitions and compare with a linear solve.
- **Evidence.** Practice for RL02 and RL04. Exact answers are possible here and a robot adds nothing. Level 3, 30–60 min [E].

### 1.11 Verification results [T]

Python 3.11.9, g++ 11.4.0, Ubuntu 22.04, standard library only. Harness reproduced at the end of this section.

| Exercise | Valid solutions accepted | Injected bugs rejected |
| --- | --- | --- |
| D1 M08 | 2 of 2 | 4 of 4 |
| D2 PY07 | Good suite: accepted both valid implementations, killed 6 of 6 | Weak and self-referential suites each killed 0 of 6; strict suite rejected valid code |
| D3 C++ | 2 of 2, no warnings | 6 of 6 |
| D4 R06 | 2 of 2 | 4 of 4 |
| D5 ML03 | 2 of 2 | 5 of 5 |
| D6 RL02 | 2 of 2 targets, 1 of 1 solver | 6 of 6 |

C++ details: out-of-range index, **AddressSanitizer** heap-buffer-overflow. Missing delete, **LeakSanitizer**. Zero capacity, **UBSan** division by zero. Shallow copy, unbounded size and newest-first were caught by assertions. Shallow copy was caught by the independence assertion before any double free.

**What this does not show.** These are my own alternatives and mutants, not learner submissions. Real learners write bugs I did not imagine. No exercise has passed G7–G10. Nobody has timed them, and minute ranges are estimates. Not tested on Windows or macOS.

**Output.**

```text
D1 M08: valid [True, True]; mutants rejected {'inverse conditional': True, 'ignores base rate': True, 'missing (1-p)': True, 'p*s only': True}
D2 suites (valid accepted, killed, of): {'good': (True, 6, 6), 'weak': (True, 0, 6), 'strict': (False, 6, 6), 'self_ref': (True, 0, 6)}
D4 R06: valid [True, True]; mutants rejected {'abs_angle': True, 'swap': True, 'drop_term': True, 'sign': True}
D5 ML03: valid [True, True]; mutants rejected {'frame': True, 'tail': True, 'empty': True, 'nondeterministic': True, 'duplicate': True}
D5 leak demo MAE frame-split, episode-split: 0.566 3.028
D6 RL td: valid [True, True]; mutants rejected {'bootstraps at terminal': True, 'no bootstrap at truncation': True, 'no discount': True}
D6 RL vi: valid [True]; mutants rejected {'mean': True, 'one_sweep': True, 'terminal_reward': True}
ring_ref compile=0 warnings=0 run=0 OK
ring_vec compile=0 warnings=0 run=0 OK
m_nomod compile=0 warnings=0 run=1 heap-buffer-overflow
m_shallow compile=0 warnings=0 run=134 Assertion
m_nocap compile=0 warnings=0 run=134 Assertion
m_newest compile=0 warnings=0 run=134 Assertion
m_nodelete compile=0 warnings=0 run=1 detected memory leaks
m_nozero compile=0 warnings=0 run=1 division by zero
```

**Python harness.**

```python
# CoreLab exercise bank Round 1 harness. Standard library only. Python 3.11+.
import math,random
from fractions import Fraction as F
# D1 M08 Bayes: exact table oracle, independent of the formula
def oracle_post(p,s,f,N=10**6):
    # counts per N frames; Fractions keep it exact
    fault=p*N;tp=fault*s;fp=(N-fault)*f;return tp/(tp+fp)
def ref(p,s,f):
    d=s*p+f*(1-p)
    if d==0: raise ValueError
    return s*p/d
def alt(p,s,f):
    d=1+(f/s)*((1-p)/p) if s and p else None
    if d is None: raise ValueError
    return 1/d
D1={'inverse conditional':lambda p,s,f:s,'ignores base rate':lambda p,s,f:s/(s+f),'missing (1-p)':lambda p,s,f:s*p/(s*p+f),'p*s only':lambda p,s,f:s*p}
def d1(fn):
    rng=random.Random(11)
    for _ in range(200):
        p,s,f=F(rng.randint(1,99),1000),F(rng.randint(500,999),1000),F(rng.randint(1,200),1000)
        if abs(float(fn(p,s,f))-float(oracle_post(p,s,f)))>1e-9:return False
    return abs(float(fn(F(1,100),F(9,10),F(1,20)))-2/13)<1e-9   # hand anchor: 0.009/0.0585
# D2 PY07 learner test suite judged by implementations
def w_atan(a):return math.atan2(math.sin(a),math.cos(a))
def w_mod(a):
    r=(a+math.pi)%(2*math.pi)-math.pi;return r
W_BAD={'single subtract':lambda a:a-2*math.pi if a>math.pi else a,'range 0..2pi':lambda a:a%(2*math.pi),'identity':lambda a:a,'negated':lambda a:-w_atan(a),'no neg wrap':lambda a:(a-2*math.pi*round(a/(2*math.pi))) if a>0 else a,'returns constant':lambda a:0.0}
def judged(suite):
    def passes(w):
        try:suite(w);return True
        except AssertionError:return False
    ok=passes(w_atan) and passes(w_mod);killed=[n for n,w in W_BAD.items() if not passes(w)]
    return ok,len(killed),len(W_BAD)
def good(w):
    for a in [0,1,-1,3,-3,3.2,-3.2,7,-7,100,-100,2*math.pi,1e4]:
        r=w(a);assert -math.pi-1e-12<=r<=math.pi+1e-12;assert abs(math.sin(r-a))<1e-9 and math.cos(r-a)>0
def weak(w): assert abs(w(0))<1e-12
def strict(w): good(w);assert w(-math.pi)==math.pi   # overconstrains the boundary
def self_ref(w): assert w(3.5)==w(3.5)                # expected value from code under test
# D4 R06 2R Jacobian
def fk(q,l):return (l[0]*math.cos(q[0])+l[1]*math.cos(q[0]+q[1]),l[0]*math.sin(q[0])+l[1]*math.sin(q[0]+q[1]))
def Jref(q,l):
    a,b=q[0],q[0]+q[1];return [[-l[0]*math.sin(a)-l[1]*math.sin(b),-l[1]*math.sin(b)],[l[0]*math.cos(a)+l[1]*math.cos(b),l[1]*math.cos(b)]]
def Jrel(q,l):
    # valid alternate: build from joint positions (cross product form)
    p1=(l[0]*math.cos(q[0]),l[0]*math.sin(q[0]));e=fk(q,l);return [[-e[1],-(e[1]-p1[1])],[e[0],e[0]-p1[0]]]
def Jabs(q,l):return [[-l[0]*math.sin(q[0])-l[1]*math.sin(q[1]),-l[1]*math.sin(q[1])],[l[0]*math.cos(q[0])+l[1]*math.cos(q[1]),l[1]*math.cos(q[1])]]
def Jswap(q,l):J=Jref(q,l);return [J[1],J[0]]
def Jdrop(q,l):J=Jref(q,l);J[0][0]=-l[1]*math.sin(q[0]+q[1]);return J
def Jsign(q,l):J=Jref(q,l);return [[-J[0][0],-J[0][1]],J[1]]
def d4(fn):
    rng=random.Random(4)
    for _ in range(200):
        q=(rng.uniform(-3,3),rng.uniform(-3,3));l=(rng.uniform(.2,1.5),rng.uniform(.2,1.5));J=fn(q,l)
        for c in range(2):
            for h in (1e-5,1e-4):
                qp=list(q);qm=list(q);qp[c]+=h;qm[c]-=h;P,M=fk(qp,l),fk(qm,l)
                for r in range(2):
                    if abs(J[r][c]-(P[r]-M[r])/(2*h))>1e-5:return False
    J=fn((.3,0.),(1.,.7));return abs(J[0][0]*J[1][1]-J[0][1]*J[1][0])<1e-12
# D5 ML03 split by episode
def split_ref(eps,test_frac,seed):
    u=sorted(set(eps));random.Random(seed).shuffle(u);k=max(1,round(len(u)*test_frac));t=set(u[:k])
    return [i for i,e in enumerate(eps) if e not in t],[i for i,e in enumerate(eps) if e in t]
def split_alt(eps,test_frac,seed):
    import hashlib
    u=sorted(set(eps),key=lambda e:hashlib.sha256(f'{seed}:{e}'.encode()).hexdigest());k=max(1,round(len(u)*test_frac));t=set(u[:k])
    tr,te=[],[]
    for i,e in enumerate(eps):(te if e in t else tr).append(i)
    return tr,te
def split_frame(eps,test_frac,seed):
    i=list(range(len(eps)));random.Random(seed).shuffle(i);k=round(len(i)*test_frac);return sorted(i[k:]),sorted(i[:k])
def split_tail(eps,test_frac,seed):
    k=round(len(eps)*(1-test_frac));return list(range(k)),list(range(k,len(eps)))
def split_empty(eps,test_frac,seed):return list(range(len(eps))),[]
def split_rng(eps,test_frac,seed):return split_ref(eps,test_frac,random.random())
def split_dup(eps,test_frac,seed):
    tr,te=split_ref(eps,test_frac,seed);return tr+te,te
def d5(fn):
    for eps in ([f'e{i//7}' for i in range(70)],[f'e{i%5}' for i in range(40)],['a','a','b','b','c','d','d','d','e','f']):
        for s in (1,2,3):
            tr,te=fn(eps,.3,s)
            if not te or not tr or sorted(tr+te)!=list(range(len(eps))):return False
            if {eps[i] for i in tr}&{eps[i] for i in te}:return False
            if fn(eps,.3,s)!=(tr,te):return False
            if abs(len({eps[i] for i in te})/len(set(eps))-.3)>.21:return False
    return True
def leak_demo():
    # x identifies the episode; y depends on an episode code that x cannot predict across episodes
    rng=random.Random(5);X=[];Y=[];E=[]
    for e in range(20):
        off,code=rng.uniform(-5,5),rng.uniform(-5,5)
        for t in range(30):X.append(off+rng.gauss(0,.05));Y.append(code+rng.gauss(0,.05));E.append(e)
    def mae(tr,te):return sum(abs(Y[i]-Y[min(tr,key=lambda j:abs(X[j]-X[i]))]) for i in te)/len(te)
    a=[mae(*split_frame(E,.3,s)) for s in range(5)];b=[mae(*split_ref(E,.3,s)) for s in range(5)]
    return sum(a)/5,sum(b)/5
# D6 RL02 terminal vs truncation; value iteration
def td(r,v,g,term,trunc):return r+(0 if term else g*v)
def td_alt(r,v,g,term,trunc):
    return r if term else r+g*v
TD={'bootstraps at terminal':lambda r,v,g,t,u:r+g*v,'no bootstrap at truncation':lambda r,v,g,t,u:r+(0 if (t or u) else g*v),'no discount':lambda r,v,g,t,u:r+(0 if t else v)}
def mdp():return {'A':{'finish':[(1.,'T',3.)],'wait':[(1.,'A',1.)]},'T':{}}
def vi(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values());d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_mean(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=sum(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())/len(A);d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_once(M,g,tol=1e-10):
    V={s:0. for s in M}
    for s,A in M.items():
        if A:V[s]=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())
    return V
def vi_terminal(M,g,tol=1e-10):
    M2={s:(A or {'x':[(1.,s,0.5)]}) for s,A in M.items()};return vi(M2,g)
def d6td(fn):
    return fn(2.,5.,.9,True,False)==2. and abs(fn(2.,5.,.9,False,True)-6.5)<1e-12 and abs(fn(2.,5.,.9,False,False)-6.5)<1e-12
def d6vi(fn):
    # closed form: V(A)=max(3,1/(1-g))
    return all(abs(fn(mdp(),g)['A']-max(3,1/(1-g)))<1e-6 and fn(mdp(),g)['T']==0 for g in (.5,.6,.9,.95))
def show(t,ok,bad):print(f'{t}: valid {ok}; mutants rejected {bad}')
show('D1 M08',[d1(ref),d1(alt)],{n:not d1(f) for n,f in D1.items()})
print('D2 suites (valid accepted, killed, of):',{n:judged(s) for n,s in dict(good=good,weak=weak,strict=strict,self_ref=self_ref).items()})
show('D4 R06',[d4(Jref),d4(Jrel)],{n:not d4(f) for n,f in dict(abs_angle=Jabs,swap=Jswap,drop_term=Jdrop,sign=Jsign).items()})
show('D5 ML03',[d5(split_ref),d5(split_alt)],{n:not d5(f) for n,f in dict(frame=split_frame,tail=split_tail,empty=split_empty,nondeterministic=split_rng,duplicate=split_dup).items()})
print('D5 leak demo MAE frame-split, episode-split: %.3f %.3f'%leak_demo())
show('D6 RL td',[d6td(td),d6td(td_alt)],{n:not d6td(f) for n,f in TD.items()})
show('D6 RL vi',[d6vi(vi)],{n:not d6vi(f) for n,f in dict(mean=vi_mean,one_sweep=vi_once,terminal_reward=vi_terminal).items()})
```

**C++ reference, `ring_ref.hpp`.** Mutants are one-line edits of this file, as named in the output.

```cpp
#pragma once
#include <cstddef>
#include <optional>
#include <stdexcept>
#include <utility>
class RingBuffer {
  double* d_; std::size_t cap_, head_ = 0, n_ = 0;
public:
  explicit RingBuffer(std::size_t cap) : d_(nullptr), cap_(cap) {
    if (cap == 0) throw std::invalid_argument("capacity");
    d_ = new double[cap]; }
  ~RingBuffer() { delete[] d_; }
  RingBuffer(const RingBuffer& o) : d_(new double[o.cap_]), cap_(o.cap_), head_(o.head_), n_(o.n_) {
    for (std::size_t i = 0; i < cap_; ++i) d_[i] = o.d_[i]; }
  RingBuffer& operator=(RingBuffer o) noexcept { std::swap(d_, o.d_); std::swap(cap_, o.cap_); std::swap(head_, o.head_); std::swap(n_, o.n_); return *this; }
  void push(double v) { d_[(head_ + n_) % cap_] = v; if (n_ < cap_) ++n_; else head_ = (head_ + 1) % cap_; }
  std::optional<double> pop() { if (!n_) return std::nullopt; double v = d_[head_]; head_ = (head_ + 1) % cap_; --n_; return v; }
  std::size_t size() const { return n_; }
};
```

**C++ test.**

```cpp
#include IMPL
#include <cassert>
#include <cstdio>
#include <stdexcept>
int main() {
  bool threw = false; try { RingBuffer z(0); z.push(1); } catch (const std::invalid_argument&) { threw = true; } assert(threw);
  RingBuffer r(3); assert(r.size() == 0); assert(!r.pop());
  r.push(1); r.push(2); assert(r.size() == 2); assert(*r.pop() == 1);
  r.push(3); r.push(4); r.push(5); assert(r.size() == 3);
  assert(*r.pop() == 3); assert(*r.pop() == 4); assert(*r.pop() == 5); assert(!r.pop());
  for (int i = 0; i < 100; ++i) r.push(i);
  assert(r.size() == 3); assert(*r.pop() == 97);
  { RingBuffer a(2); a.push(7); a.push(8); RingBuffer b = a; a.pop(); a.push(9); assert(*b.pop() == 7); assert(*b.pop() == 8);
    RingBuffer c(5); c = a; assert(*c.pop() == 8); assert(*c.pop() == 9);
    RingBuffer& ra = a; a = ra; }
  std::puts("OK"); }
```

### 1.12 Effort, risks and first step

**Effort [E], low confidence.** Exercise with generator, two solutions, mutants, hints and review: 3–8 h. Selection, UI and storage for modes: 20–50 h, mostly because attempts and weaknesses already exist. No time saving is claimed.

| Risk | Mitigation |
| --- | --- |
| Bank turns into a points game | No streaks, scores or badges; practice is not evidence |
| Solutions leak in a public repo | Accepted: self-study tool. Exposure is recorded honestly; assessment forms stay separate |
| Learner code is executed locally | Terminal-only, like labs today; never from the web server; not a sandbox. **Do not ask learners to run someone else's untrusted solution** |
| Forged stdout | New runner first |
| Content backlog | Quality gates over count. 20 now; grow per pilot |
| External links go dead | Link check in CI; content must stand without them |
| Too many modes for one person to maintain | Rules only, shared selector with weaknesses |

**First step, if approved:** the D1, D2 and D4 exercises, with a simple More Practice view. They need no compiler, and they support the L01, L02 and L06 path already proposed. Build after the runner fix. Recommended follows when at least about 30 exercises exist [E], since rules have little to choose among before that.

### 1.13 Questions for Codex

1. Is a separate exercise record better than extending `content/practice`, given the requirement to leave those files untouched?
2. Is my rejection of IRT and knowledge tracing right, or is there a defensible lightweight model for a single learner?
3. Can an exercise ever become evidence? I say only through a separately approved contract.
4. Do you see a way to fill L14 and L18 without ROS or contact simulation?
5. Is automatic hint-based assistance recording safe with the existing `assistance` field and historic data?
6. Which of my license readings do you contradict, especially OpenStax and LeetCode, which I could not read in full?

## Round 2 — Cross-review and rebuttal

Written after reading Codex Round 1 and its Round 2 reply to my Round 1. I reran Codex's Appendix A and B, fixed the defects it found, and reran my harness. Everything executable is below or in Round 1.

### 2.1 Corrections to my Round 1

| Item | Correction | Source |
| --- | --- | --- |
| **D3 C++ reference** | **Real defect.** `new double[cap]` left slots uninitialized, and the copy constructor read all of them, which is undefined behaviour on a partly filled buffer. My test filled the buffer first, so it missed it. ASan and UBSan cannot see this; Valgrind on the old reference also stayed silent because a copy alone doesn't trigger it, so **my tools could not have caught it**. Fixed with value-initialization, added empty, partial and wrapped copy tests, and one more mutant. MemorySanitizer not run: no clang here. | Codex, by inspection |
| **D1 alternative** | **Real defect.** My odds form raised `ValueError` at p=0 and s=0, where the answer is defined as 0. "Every valid solution accepted" only held in the sampled interior. Fixed; boundaries now tested. | Codex probe |
| **D5 split** | **Real defect.** `split_ref(['a','b'], .99, 1)` gave an empty train set. Now requires at least two groups and 0 < fraction < 1, and clamps to [1, n−1]. A chronological group split is now tested as **valid**, so rejection depends on broken invariants and not on method. | Codex probe |
| Level counts | 1.9 said 7 at level 2 and 13 at level 3. **Correct: 8 and 12.** | Self-found |
| `lib/practice.ts` | 8 entries, not 7 | Codex |
| Source wording | "Cannot be copied into a CC BY 4.0 project" was too broad. A separately licensed file can coexist if obligations are met. It cannot be **relicensed** as CoreLab's own CC BY content. Link-only stays the simple default | Codex |
| OpenStax, LeetCode, Codeforces | Partial readings only. Attribute them as such; not verified legal conclusions | Codex |
| 1.6 "stop drilling" | Should **offer** remediation, never block further practice | Codex |
| 1.7 hint after an attempt | Should not be required. A novice or accessibility need may warrant help first. Becomes a gentle prompt with an immediate way through | Codex |
| 1.0 finding 5 | Described the ±π contract correctly but the domain was unstated. Huge angles break it: `atan2` and modulo differ by 2.2e-2 rad at 1e15 and by 1.25 rad at 1e16 [T]. Domain now \|a\| ≤ 1e6 | Codex, measured here |
| D5 number | Episode-split MAE is now 2.923 after the contract fix, 3.028 before. One synthetic construction, not a leakage magnitude | Rerun |

### 2.2 Decisions on Codex's position

| # | Codex position | Decision | Evidence and reason |
| --- | --- | --- | --- |
| 1 | Objective → family → instance → verifier → attempt → evidence layers | **ACCEPT** | Cleaner than my single record. Objective IDs such as `M02.projection-compute` answer "no broad credit" directly |
| 2 | "Choice" means alternative tasks for the same objective, with non-equivalence stated | **ACCEPT** | My variants were seeds and transfer forms, not alternatives. Add `routes` where authored. Choice is a real learner benefit |
| 3 | Two routes for **every** family | **MODIFY** | Doubles authoring and review. Require two routes for the four MVP objectives; elsewhere a single good route is acceptable until use shows otherwise |
| 4 | Numeric grammar for fractions and bounded decimals, no eval | **ACCEPT** | Solves the M08 defect properly. My D1 said "on-paper may be fractions", which was weak |
| 5 | Parent owns expected values and verdict; worker returns values only | **ACCEPT for evidence-grade checks** | [T] I reran Appendix B: 15 probes, 3 accepted and 12 rejected, host marker and loopback blocked, matching the published result. My Round 1 "channel it cannot write by printing" was insufficient, as Codex says |
| 6 | Python/C++ coding practice must wait for an isolated runner | **REJECT for self-check practice** | Details in 2.3 |
| 7 | MVP: projection, Bayes, frames, 2R FK | **ACCEPT** | Same direction as my D1, D4 and the L01, L02 pilot. Better than my first step |
| 8 | No fixed 30-item threshold | **ACCEPT** | Mine was an estimate presented as a gate. Recommended can run on the MVP, because 2.5's rules work with a small pool |
| 9 | Static catalog, no LMS, no general expression parser in MVP | **ACCEPT** | |
| 10 | Rights record per item | **ACCEPT** | Adds file, hash and assets to my `source` field |
| 11 | Observed in-app hints versus self-declared external help stored separately; solutions opened create exposure for next assessed form | **ACCEPT** | Stronger than my single field |
| 12 | Persist bank attempts separately or by typed migration | **ACCEPT** | My "extend the existing shape" was too casual: `lib/storage.ts` validates strictly |
| 13 | L14 and L18 preparatory exercises: interface and unit compatibility; gripper aperture and approach clearance | **ACCEPT** | Geometry and interfaces only, with the coverage gap kept visible. Added in 2.6 |
| 14 | All 12 contract gaps in 2.3 of Codex's review | **ACCEPT as release conditions** | Each one is concrete; they go into the spec gates |

### 2.3 Rebuttal: runner isolation and practice

Codex's threat analysis is right: a terminal process under the same user can read local files and the signing key, and a private pipe does not change that. But it uses this to gate all code practice behind 40–100+ hours of Linux-only hardening. I reject that for one specific case.

| Tier | What happens | Isolation needed? | Evidence? |
| --- | --- | --- | --- |
| **Answer practice** | Numeric or matrix entry; parent compares | No code runs | Practice only |
| **Self-check kit** | Learner downloads a test file and runs **their own** code with `python` or `g++`, the same as running any program they wrote. No key is touched and nothing is signed or imported | No more than they already accept when running their own program | **None. The result is not recorded as verified** |
| **Evidence-grade contract** | Parent-owned, isolated, signed | **Yes, per Codex** | Scoped I only, after approval |

The self-check kit adds no new risk, because CoreLab never executes anything and receives nothing. It works today on all three OSes wherever Python or a compiler exists. CoreLab already does this for C++, ML and robotics tasks in `lib/practice.ts`. Warnings: run only your own code, and don't run solutions pasted from strangers. **This is what lets the 2 coding-only exercises ship before any sandbox exists.** Codex's own section 9 allows "clearly trusted/manual practice", so the difference may be small; the remaining disagreement is whether that tier needs the runner first. I say it does not.

Grading a learner's test suite in-process, as my D2 harness does, is fine for a self-check and **not** for evidence. Codex is right that a suite can inspect candidate identity, so evidence-grade needs a fresh process per candidate.

### 2.4 Review of Codex's work

**Reran [T].** Appendix A: 154 checks, 20 groups, output identical to published. Appendix B: as in decision 5. Hand-checked anchors X01, X04, X10, X11 and X17: all correct.

**Where the "154 checks" headline overstates.** Codex's text disclaims it as fixtures, yet the number leads the summary. Reading the script:

1. **Half are in three groups.** X11 has 40, X14 has 21, X17 has 16: 77 of 154. X03, X05, X09 and X13 have 3 each.
2. **Several assert arithmetic, not a function under test.** `'reflection is not proper rotation', -1*1-0*0==-1`; `'pure spin', (-.1+.1)/2==0`; `'constant-column policy', [(x-3)/1 for x in [3,3]]==[0,0]`; `'orthogonal-only fixture misses zero mutant', dot([1,0],[0,1])==0`. These can never fail for a bad implementation, since none is involved.
3. **So they don't measure what the labels say.** "Constant-column policy" tests no policy. "Reflection" rejects nothing.

**The 15-probe limits are stated honestly** (no seccomp, cgroups, fork bombs, other OSes). I accept them as stated; `infinite_loop` and `wall_timeout` being rejected shows only the timeout path.

**Gaps against the brief.**

| Requirement | Codex Round 1 | Note |
| --- | --- | --- |
| Recommended, Explore, More Practice | **Modes not named.** Grep of Round 1 finds 0 mentions. Section 5's queue and cards could implement them | Needs an explicit mapping |
| C++ exercises | **None in the catalog.** Grep of section 6 finds 0 | Brief lists C++; my D3 fills it |
| 22-lab mapping | **L07, L13, L14, L18, L21 unmapped** | Mine lacks L14 and L18, now added |
| 15–20 exercises | 20, and 40 route descriptions | Routes are proposals, as Codex says |

**Where Codex is simply stronger than my Round 1:** the verifier and evidence layering, the threat model, numeric validation, and adding boundary probes against my code. Those found three real defects that my own mutants missed. **This is the main lesson: an author's own mutants share the author's blind spots, so gate G3–G5 needs a second person or adversarial review.** Add to gates.

### 2.5 Mode mapping onto the merged design

- **Recommended** = Codex's transparent queue plus my priority list. Shows the reason and two route cards when authored.
- **Explore** = catalog with filters. Warnings, never blocks. Includes external links clearly marked "outside CoreLab, no evidence".
- **More Practice** = fresh instances, then other routes, then an honest exhausted message, reusing existing `selectTargetedPlan` semantics: a seen item is labelled as a repeat, never fresh.

### 2.6 Merged proposal for Round 3

Twenty exercises, keeping one per objective and taking the stronger contract. Status reflects actual runs. C++ and test-writing come from mine; frames, FK, shortest path, gradient and swept collision draw on Codex.

| # | ID | Topics | Labs | Source of contract | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Projection | M02 | L01, L06 | Codex X01 | Fixture checked (Codex) |
| 2 | Identifiability | M03, M04, M11 | L06, L21 | Both | Spot check (Codex) |
| 3 | Bayes alarm | M08 | L09 | Both | **Run by both** |
| 4 | Sampled displacement | M05 | L03, L07 | Mine + gaps | Spec |
| 5 | Dropout intervals | PY02, E16 | L05, L19 | Mine + gaps | Spec |
| 6 | Axis normalization | PY04, ML03 | L16, L19 | Both | Spot check (Codex) |
| 7 | Test writing | PY07, T04 | L03, L05 | Mine | **Run by both** |
| 8 | Ring buffer | CPP02, CPP03, CPP08 | L05 option | Mine, fixed | **Run by me**, unreviewed by a C++ expert |
| 9 | Frames | M12, R03 | L01, L02, L12 | Codex X10 | Fixture checked (Codex) |
| 10 | FK and Jacobian, separate objectives | R04, R06, M06 | L02, L06 | Both | **Run by both** |
| 11 | Odometry and encoder rollover | R02, R16 | L03 | Both | Spot check (Codex) |
| 12 | Trajectory time law | R17 | L07, L13 | New | Spec |
| 13 | Limited feedback | C01, C03, C09 | L04 | Both | Partial; P only |
| 14 | Shortest path | PY02, E02 | L11, L13 | Codex X14 | Fixture checked (Codex) |
| 15 | Interface compatibility | S06, S10 | L14 | Codex's suggestion | Spec |
| 16 | Aperture and clearance | R08 | L18 | Codex's suggestion | Spec |
| 17 | Camera geometry | V01, V03 | L16, L17 | Both | Spot check (Codex) |
| 18 | Shared gradient | ML05, M06 | L19, L20 | Codex X17 | Fixture checked (Codex) |
| 19 | Episode split | ML03, ML07, E16 | L19 | Mine, fixed | **Run by both** (C++ excluded, as noted) |
| 20 | Termination and value | RL02, RL04 | L20 | Mine | **Run by both** |

Dropped to next wave, with their contracts kept: covariance, Kalman, pendulum, swept collision, median filter, plan validity, chain rule, numerical stepping, Python function contract. **Consequence: L08, L10, L15 and L22 lose coverage in this cut.** To keep all 22 mapped, the next wave is named against them: pendulum (L08), Kalman (L10), plan validity (L15, L22). The owner's 15–20 limit forces this trade-off.

### 2.7 Updated durable artifacts

Rerun output, fixed harness and C++ are below. Replace the Round 1 functions with these.

```text
D1 M08: valid [True, True]; mutants rejected {'inverse conditional': True, 'ignores base rate': True, 'missing (1-p)': True, 'p*s only': True}
D2 suites (valid accepted, killed, of): {'good': (True, 6, 6), 'weak': (True, 0, 6), 'strict': (False, 6, 6), 'self_ref': (True, 0, 6)}
D4 R06: valid [True, True]; mutants rejected {'abs_angle': True, 'swap': True, 'drop_term': True, 'sign': True}
D5 ML03: valid [True, True, True]; mutants rejected {'frame': True, 'tail': True, 'empty': True, 'nondeterministic': True, 'duplicate': True}
D5 leak demo MAE frame-split, episode-split: 0.566 2.923
D6 RL td: valid [True, True]; mutants rejected {'bootstraps at terminal': True, 'no bootstrap at truncation': True, 'no discount': True}
D6 RL vi: valid [True]; mutants rejected {'mean': True, 'one_sweep': True, 'terminal_reward': True}
ring_ref2 compile=0 warnings=0 run=0 OK
ring_vec compile=0 warnings=0 run=0 OK
n_nomod compile=0 warnings=0 run=1 heap-buffer-overflow
n_shallow compile=0 warnings=0 run=134 Assertion
n_nocap compile=0 warnings=0 run=134 Assertion
n_newest compile=0 warnings=0 run=134 Assertion
n_nodelete compile=0 warnings=0 run=1 detected memory leaks
n_nozero compile=0 warnings=0 run=1 division by zero
n_copyhead compile=0 warnings=0 run=134 Assertion
```

**Fixed harness.**

```python
# CoreLab exercise bank Round 1 harness. Standard library only. Python 3.11+.
import math,random
from fractions import Fraction as F
# D1 M08 Bayes: exact table oracle, independent of the formula
def oracle_post(p,s,f,N=10**6):
    # counts per N frames; Fractions keep it exact
    fault=p*N;tp=fault*s;fp=(N-fault)*f;return tp/(tp+fp)
def _dom(p,s,f):
    if not all(0<=x<=1 for x in (p,s,f)):raise ValueError
def ref(p,s,f):
    _dom(p,s,f);d=s*p+f*(1-p)
    if d==0: raise ValueError
    return s*p/d
def alt(p,s,f):
    # odds form, valid on the whole declared domain
    _dom(p,s,f);a,b=s*p,f*(1-p)
    if a==0 and b==0:raise ValueError
    return 0*p if a==0 else 1/(1+b/a)
D1={'inverse conditional':lambda p,s,f:s,'ignores base rate':lambda p,s,f:s/(s+f),'missing (1-p)':lambda p,s,f:s*p/(s*p+f),'p*s only':lambda p,s,f:s*p}
def d1(fn):
    rng=random.Random(11)
    for _ in range(200):
        p,s,f=F(rng.randint(1,99),1000),F(rng.randint(500,999),1000),F(rng.randint(1,200),1000)
        if abs(float(fn(p,s,f))-float(oracle_post(p,s,f)))>1e-9:return False
    if abs(float(fn(F(1,100),F(9,10),F(1,20)))-2/13)>1e-9:return False   # hand anchor: 0.009/0.0585
    # boundaries found by Codex: p=0, s=0, p=1 are defined; impossible evidence and bad domain raise
    for a,want in (((F(0),F(9,10),F(1,20)),0),((F(1,10),F(0),F(1,20)),0),((F(1),F(9,10),F(1,20)),1)):
        try:
            if abs(float(fn(*a))-want)>1e-12:return False
        except Exception:return False
    for a in ((F(0),F(9,10),F(0)),(F(1),F(0),F(1,20)),(F(3,2),F(1,2),F(1,2))):
        try:fn(*a);return False
        except ValueError:pass
        except Exception:return False
    return True
# D2 PY07 learner test suite judged by implementations
def w_atan(a):return math.atan2(math.sin(a),math.cos(a))
def w_mod(a):
    r=(a+math.pi)%(2*math.pi)-math.pi;return r
W_BAD={'single subtract':lambda a:a-2*math.pi if a>math.pi else a,'range 0..2pi':lambda a:a%(2*math.pi),'identity':lambda a:a,'negated':lambda a:-w_atan(a),'no neg wrap':lambda a:(a-2*math.pi*round(a/(2*math.pi))) if a>0 else a,'returns constant':lambda a:0.0}
def judged(suite):
    def passes(w):
        try:suite(w);return True
        except AssertionError:return False
    ok=passes(w_atan) and passes(w_mod);killed=[n for n,w in W_BAD.items() if not passes(w)]
    return ok,len(killed),len(W_BAD)
def good(w):
    for a in [0,1,-1,3,-3,3.2,-3.2,7,-7,100,-100,2*math.pi,1e4]:
        r=w(a);assert -math.pi-1e-12<=r<=math.pi+1e-12;assert abs(math.sin(r-a))<1e-9 and math.cos(r-a)>0
def weak(w): assert abs(w(0))<1e-12
def strict(w): good(w);assert w(-math.pi)==math.pi   # overconstrains the boundary
def self_ref(w): assert w(3.5)==w(3.5)                # expected value from code under test
# D4 R06 2R Jacobian
def fk(q,l):return (l[0]*math.cos(q[0])+l[1]*math.cos(q[0]+q[1]),l[0]*math.sin(q[0])+l[1]*math.sin(q[0]+q[1]))
def Jref(q,l):
    a,b=q[0],q[0]+q[1];return [[-l[0]*math.sin(a)-l[1]*math.sin(b),-l[1]*math.sin(b)],[l[0]*math.cos(a)+l[1]*math.cos(b),l[1]*math.cos(b)]]
def Jrel(q,l):
    # valid alternate: build from joint positions (cross product form)
    p1=(l[0]*math.cos(q[0]),l[0]*math.sin(q[0]));e=fk(q,l);return [[-e[1],-(e[1]-p1[1])],[e[0],e[0]-p1[0]]]
def Jabs(q,l):return [[-l[0]*math.sin(q[0])-l[1]*math.sin(q[1]),-l[1]*math.sin(q[1])],[l[0]*math.cos(q[0])+l[1]*math.cos(q[1]),l[1]*math.cos(q[1])]]
def Jswap(q,l):J=Jref(q,l);return [J[1],J[0]]
def Jdrop(q,l):J=Jref(q,l);J[0][0]=-l[1]*math.sin(q[0]+q[1]);return J
def Jsign(q,l):J=Jref(q,l);return [[-J[0][0],-J[0][1]],J[1]]
def d4(fn):
    rng=random.Random(4)
    for _ in range(200):
        q=(rng.uniform(-3,3),rng.uniform(-3,3));l=(rng.uniform(.2,1.5),rng.uniform(.2,1.5));J=fn(q,l)
        for c in range(2):
            for h in (1e-5,1e-4):
                qp=list(q);qm=list(q);qp[c]+=h;qm[c]-=h;P,M=fk(qp,l),fk(qm,l)
                for r in range(2):
                    if abs(J[r][c]-(P[r]-M[r])/(2*h))>1e-5:return False
    J=fn((.3,0.),(1.,.7));return abs(J[0][0]*J[1][1]-J[0][1]*J[1][0])<1e-12
# D5 ML03 split by episode
def _groups(eps,test_frac):
    u=sorted(set(eps),key=str)
    if len(u)<2 or not 0<test_frac<1:raise ValueError
    return u,min(len(u)-1,max(1,round(len(u)*test_frac)))
def split_ref(eps,test_frac,seed):
    u,k=_groups(eps,test_frac);random.Random(seed).shuffle(u);t=set(u[:k])
    return [i for i,e in enumerate(eps) if e not in t],[i for i,e in enumerate(eps) if e in t]
def split_alt(eps,test_frac,seed):
    import hashlib
    u,k=_groups(eps,test_frac);u.sort(key=lambda e:hashlib.sha256(f'{seed}:{e}'.encode()).hexdigest());t=set(u[:k])
    tr,te=[],[]
    for i,e in enumerate(eps):(te if e in t else tr).append(i)
    return tr,te
def split_chrono(eps,test_frac,seed):
    # last groups by first appearance: valid, must not be rejected for not being random
    order=list(dict.fromkeys(eps));_,k=_groups(eps,test_frac);t=set(order[-k:]);return [i for i,e in enumerate(eps) if e not in t],[i for i,e in enumerate(eps) if e in t]
def split_frame(eps,test_frac,seed):
    i=list(range(len(eps)));random.Random(seed).shuffle(i);k=round(len(i)*test_frac);return sorted(i[k:]),sorted(i[:k])
def split_tail(eps,test_frac,seed):
    _groups(eps,test_frac);k=round(len(eps)*(1-test_frac));return list(range(k)),list(range(k,len(eps)))
def split_empty(eps,test_frac,seed):return list(range(len(eps))),[]
def split_rng(eps,test_frac,seed):return split_ref(eps,test_frac,random.random())
def split_dup(eps,test_frac,seed):
    tr,te=split_ref(eps,test_frac,seed);return tr+te,te
def d5(fn):
    for eps in ([f'e{i//7}' for i in range(70)],[f'e{i%5}' for i in range(40)],['a','a','b','b','c','d','d','d','e','f']):
        for s in (1,2,3):
            tr,te=fn(eps,.3,s)
            if not te or not tr or sorted(tr+te)!=list(range(len(eps))):return False
            if {eps[i] for i in tr}&{eps[i] for i in te}:return False
            if fn(eps,.3,s)!=(tr,te):return False
            if abs(len({eps[i] for i in te})/len(set(eps))-.3)>.21:return False
    tr,te=fn(['a','b'],.99,1)
    if not tr or not te:return False
    for bad in ((['a','a'],.3,1),([],.3,1),(['a','b'],1.,1),(['a','b'],0.,1)):
        try:fn(*bad);return False
        except ValueError:pass
        except Exception:return False
    return True
def leak_demo():
    # x identifies the episode; y depends on an episode code that x cannot predict across episodes
    rng=random.Random(5);X=[];Y=[];E=[]
    for e in range(20):
        off,code=rng.uniform(-5,5),rng.uniform(-5,5)
        for t in range(30):X.append(off+rng.gauss(0,.05));Y.append(code+rng.gauss(0,.05));E.append(e)
    def mae(tr,te):return sum(abs(Y[i]-Y[min(tr,key=lambda j:abs(X[j]-X[i]))]) for i in te)/len(te)
    a=[mae(*split_frame(E,.3,s)) for s in range(5)];b=[mae(*split_ref(E,.3,s)) for s in range(5)]
    return sum(a)/5,sum(b)/5
# D6 RL02 terminal vs truncation; value iteration
def td(r,v,g,term,trunc):return r+(0 if term else g*v)
def td_alt(r,v,g,term,trunc):
    return r if term else r+g*v
TD={'bootstraps at terminal':lambda r,v,g,t,u:r+g*v,'no bootstrap at truncation':lambda r,v,g,t,u:r+(0 if (t or u) else g*v),'no discount':lambda r,v,g,t,u:r+(0 if t else v)}
def mdp():return {'A':{'finish':[(1.,'T',3.)],'wait':[(1.,'A',1.)]},'T':{}}
def vi(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values());d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_mean(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=sum(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())/len(A);d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_once(M,g,tol=1e-10):
    V={s:0. for s in M}
    for s,A in M.items():
        if A:V[s]=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())
    return V
def vi_terminal(M,g,tol=1e-10):
    M2={s:(A or {'x':[(1.,s,0.5)]}) for s,A in M.items()};return vi(M2,g)
def d6td(fn):
    return fn(2.,5.,.9,True,False)==2. and abs(fn(2.,5.,.9,False,True)-6.5)<1e-12 and abs(fn(2.,5.,.9,False,False)-6.5)<1e-12
def d6vi(fn):
    # closed form: V(A)=max(3,1/(1-g))
    return all(abs(fn(mdp(),g)['A']-max(3,1/(1-g)))<1e-6 and fn(mdp(),g)['T']==0 for g in (0.,.5,.6,2/3,.9,.95))
def show(t,ok,bad):print(f'{t}: valid {ok}; mutants rejected {bad}')
show('D1 M08',[d1(ref),d1(alt)],{n:not d1(f) for n,f in D1.items()})
print('D2 suites (valid accepted, killed, of):',{n:judged(s) for n,s in dict(good=good,weak=weak,strict=strict,self_ref=self_ref).items()})
show('D4 R06',[d4(Jref),d4(Jrel)],{n:not d4(f) for n,f in dict(abs_angle=Jabs,swap=Jswap,drop_term=Jdrop,sign=Jsign).items()})
show('D5 ML03',[d5(split_ref),d5(split_alt),d5(split_chrono)],{n:not d5(f) for n,f in dict(frame=split_frame,tail=split_tail,empty=split_empty,nondeterministic=split_rng,duplicate=split_dup).items()})
print('D5 leak demo MAE frame-split, episode-split: %.3f %.3f'%leak_demo())
show('D6 RL td',[d6td(td),d6td(td_alt)],{n:not d6td(f) for n,f in TD.items()})
show('D6 RL vi',[d6vi(vi)],{n:not d6vi(f) for n,f in dict(mean=vi_mean,one_sweep=vi_once,terminal_reward=vi_terminal).items()})
```

**Fixed `ring_ref.hpp`.**

```cpp
#pragma once
#include <cstddef>
#include <optional>
#include <stdexcept>
#include <utility>
class RingBuffer {
  double* d_; std::size_t cap_, head_ = 0, n_ = 0;
public:
  explicit RingBuffer(std::size_t cap) : d_(nullptr), cap_(cap) {
    if (cap == 0) throw std::invalid_argument("capacity");
    d_ = new double[cap](); }
  ~RingBuffer() { delete[] d_; }
  RingBuffer(const RingBuffer& o) : d_(new double[o.cap_]()), cap_(o.cap_), head_(o.head_), n_(o.n_) {
    for (std::size_t i = 0; i < cap_; ++i) d_[i] = o.d_[i]; }
  RingBuffer& operator=(RingBuffer o) noexcept { std::swap(d_, o.d_); std::swap(cap_, o.cap_); std::swap(head_, o.head_); std::swap(n_, o.n_); return *this; }
  void push(double v) { d_[(head_ + n_) % cap_] = v; if (n_ < cap_) ++n_; else head_ = (head_ + 1) % cap_; }
  std::optional<double> pop() { if (!n_) return std::nullopt; double v = d_[head_]; head_ = (head_ + 1) % cap_; --n_; return v; }
  std::size_t size() const { return n_; }
};
```

**Added C++ tests.**

```cpp
  { RingBuffer e(4); RingBuffer c = e; assert(c.size() == 0); assert(!c.pop()); c.push(1); assert(*c.pop() == 1); }
  { RingBuffer p(4); p.push(1); p.push(2); RingBuffer c = p; p.pop(); assert(c.size() == 2); assert(*c.pop() == 1); assert(*c.pop() == 2); }
  { RingBuffer w(3); for (int i = 0; i < 5; ++i) w.push(i); w.pop(); RingBuffer c = w; assert(*c.pop() == 3); c.push(9); c.push(10); assert(c.size() == 3); assert(*c.pop() == 4); assert(*c.pop() == 9); assert(*c.pop() == 10); }
```

### 2.8 Questions for Codex Round 3

1. Do you accept the self-check kit tier: no execution by CoreLab, no signature, no record as verified?
2. Will you restate 154 with tautological checks removed, or drop the count from the summary?
3. Do you accept the merged 20, or would you trade different items to keep L08, L10, L15 and L22 mapped?
4. Do you accept adding independent adversarial review to the quality gates, given that my mutants missed the three defects you found, and yours likely have blind spots too?

## Round 3 — Final conclusions

Written after reading Codex Round 3. Nothing here authorizes implementation.

### 3.1 Decisions on Codex Round 3

| # | Codex point | Decision | Evidence |
| --- | --- | --- | --- |
| 1 | My comparators accepted NaN: `abs(NaN) > tol` is false, so a bad sample is skipped | **ACCEPT. Fourth real defect in my harness.** | Reproduced, then fixed with a positive finite check. All six probes now rejected, and all earlier results still hold (3.5). Any future grader must use "accept only if finite and close", never "reject if far" |
| 2 | "Adds no new risk" was too absolute; downloaded tests are a supply-chain artifact | **ACCEPT** | Kits ship in the reviewed repo, with no remote fetch |
| 3 | Windows and macOS commands stay untested | **ACCEPT** | |
| 4 | A fresh process per candidate does not stop a suite inspecting its candidate; start with declarative test cases | **ACCEPT, corrects my 2.3** | Automatic D2 route: bounded inputs and allowlisted properties. Free-form suites stay in the manual self-check kit, where this doesn't matter because nothing is recorded |
| 5 | Self-check kits accepted | **Resolved** | Both reviewers agree: no execution by CoreLab, no signature, no verified record |
| 6 | 154 dropped as a headline | **Resolved** | No invented "real count". I agree |
| 7 | Adversarial second review before admitting an auto-checker | **Resolved** | Added as a gate. This round's NaN finding is more evidence for it |
| 8 | User asked for "at least 15–20", so no upper limit | **REJECT the premise; ACCEPT the outcome** | The brief says "Propose 15–20 exercises", with no "at least". So the proposal stays at 20. A separate optional next-wave list is fine, labelled as outside the 20, which also keeps L08, L10, L15 and L22 visible |
| 9 | Keep plan validity in the core 20 for cognitive robotics | **MODIFY** | Reasonable priority. To stay at 20 without losing goals, replace #4 sampled displacement, whose objective overlaps odometry and the trajectory time law. That restores L15 and L22; L03 and L07 stay covered by #11 and #12 |
| 10 | Mode names adopted | **Resolved** | See 3.3 |

**Correction to my 2.6.** Row 19 said "(C++ excluded, as noted)", which is a stray phrase. Codex ran that Python exercise; the note meant nothing. Codex also compiled my corrected C++ reference once under ASan and UBSan, without rerunning the mutant matrix.

### 3.2 Final proposal: 20 exercises

Levels are authored by structure, not calibrated. **No exercise has passed expert, pilot or adversarial review, so none is ready for release.** "Run" means executed with valid alternatives and injected bugs. "Fixtures" means a Codex script checked anchors, with limits Codex states. "Spec" means no execution.

| # | Exercise | Topics | Labs prepared | Domain | Lvl | Status | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Projection onto an allowed direction | M02 | L01, L06 | Maths | 2 | Fixtures | Codex X01 |
| 2 | Identifiability of two sensors | M03, M04, M11 | L06, L21 | Maths | 3 | Fixtures | |
| 3 | **Is the alarm real?** | M08 | L09 | Maths | 2 | **Run by both** | D1, X04 |
| 4 | Plan validity with stale facts | E05, S07 | L15, L22 | Planning | 3 | Fixtures, partly | Codex X20, my EX-E05-PRE |
| 5 | Sensor dropout intervals | PY02, E16 | L05, L19 | Algorithms | 2 | Spec | |
| 6 | Axis normalization, train-only stats | PY04, ML03 | L16, L19 | Python | 2 | Fixtures | |
| 7 | **Tests that actually test** | PY07, T04 | L03, L05 | Python | 3 | **Run by both** | D2 |
| 8 | **Sensor ring buffer** | CPP02, CPP03, CPP08 | L05 option | C++ | 3 | **Run by me**; reference compiled by Codex | D3 |
| 9 | Frames: marker to base | M12, R03 | L01, L02, L12 | Robotics | 2 | Fixtures | Codex X10 |
| 10 | **FK, then Jacobian** | R04, R06, M06 | L02, L06 | Robotics | 3 | **Run by both** | D4, X11 |
| 11 | Odometry and encoder rollover | R02, R16 | L03 | Robotics | 2 | Fixtures, partly | |
| 12 | Trajectory time law | R17 | L07, L13 | Robotics | 3 | Spec | |
| 13 | Limited feedback | C01, C03, C09 | L04 | Control | 3 | Fixtures, P only | |
| 14 | Shortest path, any optimal route | PY02, E02 | L11, L13 | Algorithms | 3 | Fixtures | Codex X14 |
| 15 | Interface compatibility | S06, S10 | L14 | Systems | 2 | Spec | |
| 16 | Gripper aperture and clearance | R08 | L18 | Robotics | 3 | Spec | |
| 17 | Camera geometry | V01, V03 | L16, L17 | Vision | 2 | Fixtures | |
| 18 | Shared-parameter gradient | ML05, M06 | L19, L20 | ML | 3 | Fixtures | Codex X17 |
| 19 | **The split that flatters** | ML03, ML07, E16 | L19 | ML | 3 | **Run by both** | D5 |
| 20 | **Ended, or out of time?** | RL02, RL04 | L20 | RL | 3 | **Run by both** | D6 |

**Six detailed examples.** My D1–D6 in 1.10, as corrected in Round 2 and 3.1. Codex's X01, X04, X10, X11, X14 and X17 are further detailed cases; they are not additional released tasks.

**All 22 labs.**

| Lab | Exercises | Lab | Exercises |
| --- | --- | --- | --- |
| L01 | 1, 9 | L12 | 9 |
| L02 | 9, 10 | L13 | 12, 14 |
| L03 | 7, 11 | L14 | 15, interfaces only |
| L04 | 13 | L15 | 4 |
| L05 | 5, 7, 8 | L16 | 6, 17 |
| L06 | 1, 2, 10 | L17 | 17 |
| L07 | 12 | L18 | 16, geometry only |
| **L08** | **Next wave: pendulum** | L19 | 5, 6, 18, 19 |
| L09 | 3 | L20 | 18, 20 |
| **L10** | **Next wave: Kalman** | L21 | 2 |
| L11 | 14 | L22 | 4 |

Preparing for a lab never replaces its PASS. L08 and L10 are the only gaps within 20.

**Optional next wave, outside the 20.** Pendulum energy (L08), 1-D Kalman (L10), covariance, chain rule, swept collision, median filter, numerical stepping, sampled displacement. Their contract conditions from Codex 2.3 are kept.

**Specializations, optional.** Manipulation 2, 9, 10, 16. Mobile 11, 12, 14. Perception 6, 17. Software 5, 7, 8, 15. Learning 18, 19, 20. Cognitive 4.

**Difficulty gap.** 8 at level 2, 12 at level 3. Level 1 comes from existing banks and optional external drills; levels 4–5 are mainly the labs themselves.

### 3.3 Final system design

| Part | Conclusion | Status |
| --- | --- | --- |
| **Recommended** | Transparent queue with a stated reason: weakness on a goal prerequisite, due review, next skill, one mixed item, one optional application. Learner override | Agreed |
| **Explore** | Filters by domain, application, difficulty, lab, specialization. Warnings only. External links marked "outside CoreLab, no evidence" | Agreed |
| **More Practice** | New route or instance, then labelled repeats, then an honest end. Seen is never called fresh | Agreed |
| **Adaptivity** | Rules only; no IRT, BKT or LLM selection. Repeated failures **offer** remediation and never block | Agreed |
| **Data** | Objective, family, instance, verifier, attempt and evidence as separate layers; static versioned catalog. Old files untouched | Agreed |
| **Numeric entry** | Bounded fractions and decimals, no eval, finite-only, format errors not called misconceptions | Agreed |
| **Hints** | A1, A2, A3 ladder from observed in-app use, stored apart from self-declared external help. Highest level kept. Opening a solution creates exposure for later assessed forms. A soft "try first?" prompt that never blocks | Agreed |
| **Remediation** | Failure, likely cause labelled as likely, minimal counterexample, lesson link, fresh variant | Agreed |
| **Evidence** | Practice is not mastery. C/M/I/T, L0–L4, A0–A3 and history unchanged. No topic-wide I from an exercise. Assessment is separately commissioned and approved | Agreed |

**Three execution tiers (agreed).**

1. **Answer practice.** No code runs. Ships first.
2. **Manual self-check kits.** Learner runs their own code with reviewed tests; nothing is recorded as verified. Windows and macOS untested.
3. **Automatic verification.** Parent-owned verdict, OS isolation, adversarial review, fail closed. Linux prototype only, not production ready.

**Licensing (agreed).** Original first. Link-only for restrictive, mixed or uncertain sources. Separately licensed files can coexist but are never relabelled as CoreLab's. Per-item rights record. OpenStax imports stay blocked pending title-level proof. My LeetCode and Codeforces readings are partial. Root licenses do not clear embedded assets. **Not legal advice.**

**Quality gates, final.** The ten gates in 1.8, plus:

- **Finite-only comparison:** accept only if finite, correctly typed and close.
- **Domain stated:** units, range, boundaries, as with `wrap_angle`.
- **Independent adversarial review** before any auto-checker is admitted, seeking both false accepts and false rejects.

### 3.4 What this debate showed

Both reviewers found defects in the other's work that its author's own tests missed.

| Found by | Defect | Why the author missed it |
| --- | --- | --- |
| Codex | Uninitialized copy, C++ | Test filled the buffer first; sanitizers used can't see it |
| Codex | Bayes alternative fails at p=0 | Sampled the interior only |
| Codex | Empty train split | Same |
| Codex | NaN accepted by comparators | Mutants returned wrong numbers, never NaN |
| Me | Tautological checks in the 154 | Count was treated as coverage |
| Me | No C++, modes unnamed, 5 labs unmapped | Scope drift from the brief |

More defects may remain in the fixed versions. **That is the practical case for gate 3.3's adversarial review, and for not releasing on my own results.**

### 3.5 Final rerun

Python 3.11.9, standard library. Fixed `close` helper replaces rejection-only comparisons. C++ results stand as in 2.7.

```text
D1 M08: valid [True, True]; mutants rejected {'inverse conditional': True, 'ignores base rate': True, 'missing (1-p)': True, 'p*s only': True}
D2 suites (valid accepted, killed, of): {'good': (True, 6, 6), 'weak': (True, 0, 6), 'strict': (False, 6, 6), 'self_ref': (True, 0, 6)}
D4 R06: valid [True, True]; mutants rejected {'abs_angle': True, 'swap': True, 'drop_term': True, 'sign': True}
D5 ML03: valid [True, True, True]; mutants rejected {'frame': True, 'tail': True, 'empty': True, 'nondeterministic': True, 'duplicate': True}
D5 leak demo MAE frame-split, episode-split: 0.566 2.923
D6 RL td: valid [True, True]; mutants rejected {'bootstraps at terminal': True, 'no bootstrap at truncation': True, 'no discount': True}
D6 RL vi: valid [True]; mutants rejected {'mean': True, 'one_sweep': True, 'terminal_reward': True}
false-acceptance probes rejected: {'bayes_nan': True, 'bayes_bool': True, 'jac_nan': True, 'jac_inf': True, 'td_nan': True, 'vi_nan': True}
```

```python
# CoreLab exercise bank Round 1 harness. Standard library only. Python 3.11+.
import math,random
from fractions import Fraction as F
def close(x,y,tol):
    # exact type gate, then a positive finite comparison, so NaN and bool can never pass
    if isinstance(x,bool) or not isinstance(x,(int,float,F)):return False
    x=float(x);return math.isfinite(x) and abs(x-float(y))<=tol
# D1 M08 Bayes: exact table oracle, independent of the formula
def oracle_post(p,s,f,N=10**6):
    # counts per N frames; Fractions keep it exact
    fault=p*N;tp=fault*s;fp=(N-fault)*f;return tp/(tp+fp)
def _dom(p,s,f):
    if not all(0<=x<=1 for x in (p,s,f)):raise ValueError
def ref(p,s,f):
    _dom(p,s,f);d=s*p+f*(1-p)
    if d==0: raise ValueError
    return s*p/d
def alt(p,s,f):
    # odds form, valid on the whole declared domain
    _dom(p,s,f);a,b=s*p,f*(1-p)
    if a==0 and b==0:raise ValueError
    return 0*p if a==0 else 1/(1+b/a)
D1={'inverse conditional':lambda p,s,f:s,'ignores base rate':lambda p,s,f:s/(s+f),'missing (1-p)':lambda p,s,f:s*p/(s*p+f),'p*s only':lambda p,s,f:s*p}
def d1(fn):
    rng=random.Random(11)
    for _ in range(200):
        p,s,f=F(rng.randint(1,99),1000),F(rng.randint(500,999),1000),F(rng.randint(1,200),1000)
        if not close(fn(p,s,f),oracle_post(p,s,f),1e-9):return False
    if not close(fn(F(1,100),F(9,10),F(1,20)),F(2,13),1e-9):return False   # hand anchor: 0.009/0.0585
    # boundaries found by Codex: p=0, s=0, p=1 are defined; impossible evidence and bad domain raise
    for a,want in (((F(0),F(9,10),F(1,20)),0),((F(1,10),F(0),F(1,20)),0),((F(1),F(9,10),F(1,20)),1)):
        try:
            if not close(fn(*a),want,1e-12):return False
        except Exception:return False
    for a in ((F(0),F(9,10),F(0)),(F(1),F(0),F(1,20)),(F(3,2),F(1,2),F(1,2))):
        try:fn(*a);return False
        except ValueError:pass
        except Exception:return False
    return True
# D2 PY07 learner test suite judged by implementations
def w_atan(a):return math.atan2(math.sin(a),math.cos(a))
def w_mod(a):
    r=(a+math.pi)%(2*math.pi)-math.pi;return r
W_BAD={'single subtract':lambda a:a-2*math.pi if a>math.pi else a,'range 0..2pi':lambda a:a%(2*math.pi),'identity':lambda a:a,'negated':lambda a:-w_atan(a),'no neg wrap':lambda a:(a-2*math.pi*round(a/(2*math.pi))) if a>0 else a,'returns constant':lambda a:0.0}
def judged(suite):
    def passes(w):
        try:suite(w);return True
        except AssertionError:return False
    ok=passes(w_atan) and passes(w_mod);killed=[n for n,w in W_BAD.items() if not passes(w)]
    return ok,len(killed),len(W_BAD)
def good(w):
    for a in [0,1,-1,3,-3,3.2,-3.2,7,-7,100,-100,2*math.pi,1e4]:
        r=w(a);assert -math.pi-1e-12<=r<=math.pi+1e-12;assert abs(math.sin(r-a))<1e-9 and math.cos(r-a)>0
def weak(w): assert abs(w(0))<1e-12
def strict(w): good(w);assert w(-math.pi)==math.pi   # overconstrains the boundary
def self_ref(w): assert w(3.5)==w(3.5)                # expected value from code under test
# D4 R06 2R Jacobian
def fk(q,l):return (l[0]*math.cos(q[0])+l[1]*math.cos(q[0]+q[1]),l[0]*math.sin(q[0])+l[1]*math.sin(q[0]+q[1]))
def Jref(q,l):
    a,b=q[0],q[0]+q[1];return [[-l[0]*math.sin(a)-l[1]*math.sin(b),-l[1]*math.sin(b)],[l[0]*math.cos(a)+l[1]*math.cos(b),l[1]*math.cos(b)]]
def Jrel(q,l):
    # valid alternate: build from joint positions (cross product form)
    p1=(l[0]*math.cos(q[0]),l[0]*math.sin(q[0]));e=fk(q,l);return [[-e[1],-(e[1]-p1[1])],[e[0],e[0]-p1[0]]]
def Jabs(q,l):return [[-l[0]*math.sin(q[0])-l[1]*math.sin(q[1]),-l[1]*math.sin(q[1])],[l[0]*math.cos(q[0])+l[1]*math.cos(q[1]),l[1]*math.cos(q[1])]]
def Jswap(q,l):J=Jref(q,l);return [J[1],J[0]]
def Jdrop(q,l):J=Jref(q,l);J[0][0]=-l[1]*math.sin(q[0]+q[1]);return J
def Jsign(q,l):J=Jref(q,l);return [[-J[0][0],-J[0][1]],J[1]]
def d4(fn):
    rng=random.Random(4)
    for _ in range(200):
        q=(rng.uniform(-3,3),rng.uniform(-3,3));l=(rng.uniform(.2,1.5),rng.uniform(.2,1.5));J=fn(q,l)
        for c in range(2):
            for h in (1e-5,1e-4):
                qp=list(q);qm=list(q);qp[c]+=h;qm[c]-=h;P,M=fk(qp,l),fk(qm,l)
                for r in range(2):
                    if not close(J[r][c],(P[r]-M[r])/(2*h),1e-5):return False
    J=fn((.3,0.),(1.,.7));return close(J[0][0]*J[1][1]-J[0][1]*J[1][0],0,1e-12)
# D5 ML03 split by episode
def _groups(eps,test_frac):
    u=sorted(set(eps),key=str)
    if len(u)<2 or not 0<test_frac<1:raise ValueError
    return u,min(len(u)-1,max(1,round(len(u)*test_frac)))
def split_ref(eps,test_frac,seed):
    u,k=_groups(eps,test_frac);random.Random(seed).shuffle(u);t=set(u[:k])
    return [i for i,e in enumerate(eps) if e not in t],[i for i,e in enumerate(eps) if e in t]
def split_alt(eps,test_frac,seed):
    import hashlib
    u,k=_groups(eps,test_frac);u.sort(key=lambda e:hashlib.sha256(f'{seed}:{e}'.encode()).hexdigest());t=set(u[:k])
    tr,te=[],[]
    for i,e in enumerate(eps):(te if e in t else tr).append(i)
    return tr,te
def split_chrono(eps,test_frac,seed):
    # last groups by first appearance: valid, must not be rejected for not being random
    order=list(dict.fromkeys(eps));_,k=_groups(eps,test_frac);t=set(order[-k:]);return [i for i,e in enumerate(eps) if e not in t],[i for i,e in enumerate(eps) if e in t]
def split_frame(eps,test_frac,seed):
    i=list(range(len(eps)));random.Random(seed).shuffle(i);k=round(len(i)*test_frac);return sorted(i[k:]),sorted(i[:k])
def split_tail(eps,test_frac,seed):
    _groups(eps,test_frac);k=round(len(eps)*(1-test_frac));return list(range(k)),list(range(k,len(eps)))
def split_empty(eps,test_frac,seed):return list(range(len(eps))),[]
def split_rng(eps,test_frac,seed):return split_ref(eps,test_frac,random.random())
def split_dup(eps,test_frac,seed):
    tr,te=split_ref(eps,test_frac,seed);return tr+te,te
def d5(fn):
    for eps in ([f'e{i//7}' for i in range(70)],[f'e{i%5}' for i in range(40)],['a','a','b','b','c','d','d','d','e','f']):
        for s in (1,2,3):
            tr,te=fn(eps,.3,s)
            if not te or not tr or sorted(tr+te)!=list(range(len(eps))):return False
            if {eps[i] for i in tr}&{eps[i] for i in te}:return False
            if fn(eps,.3,s)!=(tr,te):return False
            if abs(len({eps[i] for i in te})/len(set(eps))-.3)>.21:return False
    tr,te=fn(['a','b'],.99,1)
    if not tr or not te:return False
    for bad in ((['a','a'],.3,1),([],.3,1),(['a','b'],1.,1),(['a','b'],0.,1)):
        try:fn(*bad);return False
        except ValueError:pass
        except Exception:return False
    return True
def leak_demo():
    # x identifies the episode; y depends on an episode code that x cannot predict across episodes
    rng=random.Random(5);X=[];Y=[];E=[]
    for e in range(20):
        off,code=rng.uniform(-5,5),rng.uniform(-5,5)
        for t in range(30):X.append(off+rng.gauss(0,.05));Y.append(code+rng.gauss(0,.05));E.append(e)
    def mae(tr,te):return sum(abs(Y[i]-Y[min(tr,key=lambda j:abs(X[j]-X[i]))]) for i in te)/len(te)
    a=[mae(*split_frame(E,.3,s)) for s in range(5)];b=[mae(*split_ref(E,.3,s)) for s in range(5)]
    return sum(a)/5,sum(b)/5
# D6 RL02 terminal vs truncation; value iteration
def td(r,v,g,term,trunc):return r+(0 if term else g*v)
def td_alt(r,v,g,term,trunc):
    return r if term else r+g*v
TD={'bootstraps at terminal':lambda r,v,g,t,u:r+g*v,'no bootstrap at truncation':lambda r,v,g,t,u:r+(0 if (t or u) else g*v),'no discount':lambda r,v,g,t,u:r+(0 if t else v)}
def mdp():return {'A':{'finish':[(1.,'T',3.)],'wait':[(1.,'A',1.)]},'T':{}}
def vi(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values());d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_mean(M,g,tol=1e-10):
    V={s:0. for s in M}
    for _ in range(100000):
        d=0
        for s,A in M.items():
            if not A:continue
            n=sum(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())/len(A);d=max(d,abs(n-V[s]));V[s]=n
        if d<tol:break
    return V
def vi_once(M,g,tol=1e-10):
    V={s:0. for s in M}
    for s,A in M.items():
        if A:V[s]=max(sum(p*(r+g*V[t]) for p,t,r in o) for o in A.values())
    return V
def vi_terminal(M,g,tol=1e-10):
    M2={s:(A or {'x':[(1.,s,0.5)]}) for s,A in M.items()};return vi(M2,g)
def d6td(fn):
    return close(fn(2.,5.,.9,True,False),2.,1e-12) and close(fn(2.,5.,.9,False,True),6.5,1e-12) and close(fn(2.,5.,.9,False,False),6.5,1e-12)
def d6vi(fn):
    # closed form: V(A)=max(3,1/(1-g))
    return all(close(fn(mdp(),g)['A'],max(3,1/(1-g)),1e-6) and close(fn(mdp(),g)['T'],0,1e-12) for g in (0.,.5,.6,2/3,.9,.95))
def show(t,ok,bad):print(f'{t}: valid {ok}; mutants rejected {bad}')
show('D1 M08',[d1(ref),d1(alt)],{n:not d1(f) for n,f in D1.items()})
print('D2 suites (valid accepted, killed, of):',{n:judged(s) for n,s in dict(good=good,weak=weak,strict=strict,self_ref=self_ref).items()})
show('D4 R06',[d4(Jref),d4(Jrel)],{n:not d4(f) for n,f in dict(abs_angle=Jabs,swap=Jswap,drop_term=Jdrop,sign=Jsign).items()})
show('D5 ML03',[d5(split_ref),d5(split_alt),d5(split_chrono)],{n:not d5(f) for n,f in dict(frame=split_frame,tail=split_tail,empty=split_empty,nondeterministic=split_rng,duplicate=split_dup).items()})
print('D5 leak demo MAE frame-split, episode-split: %.3f %.3f'%leak_demo())
show('D6 RL td',[d6td(td),d6td(td_alt)],{n:not d6td(f) for n,f in TD.items()})
show('D6 RL vi',[d6vi(vi)],{n:not d6vi(f) for n,f in dict(mean=vi_mean,one_sweep=vi_once,terminal_reward=vi_terminal).items()})

# False-acceptance probes from Codex Round 3 and additions
def bayes_nan(p,s,f):
    if 0<p<1 and s>0 and 0<f<1 and (p,s,f)!=(F(1,100),F(9,10),F(1,20)):return float('nan')
    return ref(p,s,f)
def bayes_bool(p,s,f):return True
def jac_nan(q,l):
    if q==(.3,0.) and l==(1.,.7):return Jref(q,l)
    return [[float('nan')]*2 for _ in range(2)]
def jac_inf(q,l):return [[float('inf')]*2 for _ in range(2)]
def td_nan(r,v,g,t,u):return float('nan')
def vi_nan(M,g,tol=1e-10):return {'A':float('nan'),'T':0.}
print('false-acceptance probes rejected:',dict(bayes_nan=not d1(bayes_nan),bayes_bool=not d1(bayes_bool),jac_nan=not d4(jac_nan),jac_inf=not d4(jac_inf),td_nan=not d6td(td_nan),vi_nan=not d6vi(vi_nan)))
```

### 3.6 Recommendation and owner decisions

**Recommended first step, if approved.** Four original answer-practice packs: projection, Bayes, frames, and FK with Jacobian, two scenario routes each, with More Practice and a minimal Recommended. No code execution. Fix M08-style format handling through the new numeric entry, with old records untouched. Pilot before adding anything. Effort: 30–60 h for content and manifests, 24–56 h for entry and selection, per Codex's ranges, which I accept as low-confidence estimates. Self-check kits for test writing and the C++ ring buffer can follow cheaply.

**Do not do yet.** Automatic code verification, a psychometric engine, importing external content, or the full 20 at once.

**Owner decisions.**

1. Approve the four-pack first step?
2. Who is the technical and adversarial reviewer? No one is named, and it blocks release under the gates.
3. Is the 20-item cap firm, or should next-wave items be included? This is the only scope disagreement with Codex.
4. Report namespace: still `corelab-lab/2` or `corelab-practical/1`, left open from the labs review.
5. Which OSes are supported for self-check kits, and will someone test them?

**Standing limits.** No learner has used any of this. No learning gain, difficulty calibration or time saving is established. All hours are estimates.

Claude has completed Round 3 and will not edit Codex files or any final synthesis.

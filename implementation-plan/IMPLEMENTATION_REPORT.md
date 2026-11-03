# CoreLab V2 implementation report

**S1/S2 activated by the owner on 2026-11-02 after an owner-assigned AI content review — not a human expert review or learner-outcome certification.** The S3 learner pilot was not run, at the owner's request. The repository was pushed to its GitHub remote on 2026-11-02 for cross-platform CI; no deployment or real learner-data deletion has been performed.

## Content completion (2026-11-02, owner request)

At the owner's request (single learner; speed over formal review), every one of the 169 curriculum topics now has: a complete lesson (theory, worked example, 8–12 graded exercises with answers — at least three adapted from named reputable sources and restated in original words — a hands-on lab with starter code and runnable tests, failure modes, alternatives, "More practice" links to official problem sets), an original SVG figure, a 6–8 question diagnostic and a 10–14 question targeted practice bank (1,998 bank questions in total). 270 YouTube videos, each checked by oEmbed title/channel, cover all 169 topics. Authors were Sonnet subagents; each lab's tests were run against a reference solution and against the stubs, numeric answers were computed in Python, figures were rendered, links were checked for HTTP 200, and choice options were rebalanced and reordered so length and position no longer reveal the key. **There was no independent per-item expert or AI review in this round**; previously published diagnostics and banks were left unchanged.

## Learning experience upgrade (2026-11-03, owner request)

- **Review pass:** 14 independent Sonnet reviewers re-derived every choice key and recomputed every number, re-ran code and labs, and fixed errors in place. They corrected about 50 wrong choice keys left from authoring and many numeric or wording errors, rewrote about 200 questions so each stands alone (weak-skill practice shows them individually), fixed more than 40 figures, and made every "More practice" link specific to its topic. A "Library track" with NumPy, SciPy, PyTorch, OpenCV, Gymnasium, scikit-learn, ROS 2 or MuJoCo was added to most labs; libraries were installed only in the scratch area. This is AI review, not human review.
- **Study sessions:** `lib/lesson-plan.ts` splits each lesson into Learn, Practice, Build and Review sessions with realistic minutes. The median is now about 5.5 h per lesson and the curriculum totals about 920 h; the old figure was 208 h. Frontmatter `estimated_minutes` was updated to match. Learners can tick off sessions and the lab; the ticks are stored as existing `session` records, so they are included in backups. Exercise answers stay hidden until requested.
- **Plainer interface:** status words replace the jargon, and the C/M/I/T and assistance details are collapsed. Navigation is now Dashboard → Roadmap → Lessons → Practice → Review, with V2 as "Extra practice lab". The sticky video bar no longer covers content, the contents panel becomes a drawer below 1600 px, and graph labels are larger. This UI work was done by Claude at the owner's request, in files normally owned by Codex.
- **Vietnamese:** an EN/VI switch (cookie + localStorage, default EN) covers the UI and all 169 lessons (`content/lessons/vi/`), diagnostics and practice banks (`content/i18n/vi/`). `npm run validate:vi` checks that headings, code blocks, images, question ids and option counts match the English source.
- **Gates (clean worktree):** lint, typecheck, validate:content, validate:v2, 279 unit tests in 52 files, V2 build with 10 flows, and default build with 16 flows. All exited 0.

## Roadmap execution status (2026-11-02, local commits, not pushed)

Instructions: `CLAUDE_FULL_ROADMAP_PROMPT.md`; inventory and per-group log: `ROADMAP_EXECUTION.md`; API notes: `CLAUDE_BACKEND_HANDOFF.md`. **The 22-lab roadmap is not complete.** Every lab now has a reviewed *foundation* (objective, practice family, manual self-check kit, teaching coverage). For L05 and L07–L22, the environment-dependent subcontracts in their section-9 scope are listed in each roadmap entry's `unavailable` field and are not provided. All review below is **owner-assigned AI review by fresh reviewer instances that did not author the content — not human expert review**, and no learner has used any of it.

### Fully implemented and tested scopes

- 43 versioned objectives (was 26) in existing curriculum topics, 39 practice families with 266 static items (was 22/164), 22 manual Python self-check kits with sample manifests, and 20 V2 teaching bridges plus the existing lessons. Every family X23–X39 has two distinct routes and an independent oracle written by its reviewer (`tests/v2/oracles/`), run by `tests/v2/numerical-oracles.test.ts`.
- New C/M sources beyond Frames/FK: **F-ODOM / RV-ODOM** (R02.exact-arc) and **F-JIK / RV-JIK** (R06.planar-jacobian, R05.planar-ik). Each has a recorded AI review, reviewer-written oracles for every M structure (`tests/v2/oracles/cm-ODOM.ts`, `cm-JIK.ts`) run by `tests/v2/assessment-oracles.test.ts`, and exact-fingerprint disjointness from practice, kit samples and the other sources (validate-v2). In total, 4 forms and 4 retention pools are approved.
- Additive API: `forms[].title`, `reviews[].sourceId`, `labRoadmap.labs[].unavailable`, per-objective bridges (`CLAUDE_BACKEND_HANDOFF.md`). Grading, admission, exposure and evidence semantics are unchanged.

### Evidence kinds — kept separate

| Kind | Status |
| --- | --- |
| Practice (static items, help, feedback) | 39 families; no evidence created |
| Manual self-check kits (L01–L22) | Run by the learner locally; the web server never executes learner code; self-reports create no evidence |
| C/M admission and retention | Frames, FK (R04), odometry (R02), Jacobian/IK (R06/R05) only; every other new objective has practice and a kit but **no** C/M form |
| Verified I, lab reports, reviewed transfer | **Unavailable**: no protected runner, no report import |

### Partial labs and unimplemented subcontracts

L01–L04 and L06 are manual-kit labs with no declared unavailable parts. L05 and L07–L22 are partial: each provides a numerical/replay foundation only, and its `unavailable` list (5–8 items) covers, for example, ROS 2/DDS/TF2/rosbag runtime (L05, L12, L13, L14), MuJoCo or other physics-engine and simulator runs (L08, L17, L18, L20, L21), real sensors, cameras and hardware (L09, L10, L16, L17, L21), MoveIt/ros2_control/Nav2 (L13, L14), safety certification and human hazard review (L15), LeRobot datasets and neural policies (L19), deep RL (L20), and LLM/VLM or TAMP reasoning with human review of open plans (L22). Author fixtures (normal and `python -O`), rerun on 2026-11-02:

| Kit | Valid alternatives | Named mutants | Kit | Valid alternatives | Named mutants |
| --- | --- | --- | --- | --- | --- |
| L03 odometry | 7 | 40 | L14 interfaces | 7 | 75 |
| L04 PID | 5 | 63 | L15 executive | 7 | 108 |
| L05 replay | 6 | 74 | L16 camera | 11 | 80 |
| L06 Jacobian/IK | 7 | 81 | L17 alignment | 10 | 85 |
| L07 trajectory | 6 | 73 | L18 grasp | 8 | 56 |
| L08 dynamics | 6 | 95 | L19 imitation | 6 | 89 |
| L09 localization | 6 | 76 | L20 RL | 5 | 92 |
| L10 Kalman | 6 | 75 | L21 identification | 6 | 93 |
| L11 planning | 7 | 90 | L22 reasoning | 7 | 80 |
| L12 description | 6 | 94 | L13 navigation | 6 | 62 |

L01/L02 (frames/FK) are covered by `tests/fixtures/manual_kits.py` (12 alternatives / 48 mutants as previously recorded).

### Review outcomes (AI review)

Every lab group and C/M source went author → fresh reviewer → fixes → re-review until no blocker/major remained. Notable majors found and fixed: three bridge worked examples that reproduced a practice item (L05, L17, L22), a prompt showing rounded numbers while the inputs held others (X35/L18), kit defects or weakly enforced contract clauses (L09 reversed kernel and single wrap, L12 XML-safety cases, L14 endpoint sampling, L21 conditioning threshold), JIK edge targets that mirrored the R05 bridge check, C items in RV-ODOM that repeated form items or went beyond the objective, mis-stated scenario numbers in two JIK C items, and the missing odometry lesson (`/lessons/R02` teaches mechanisms/DOF; a new `diff-drive-arc-odometry` bridge now covers R02.exact-arc). One reviewer claim (an L13 remediation value) was checked by the lead, found wrong, and not applied. Remaining minors are recorded in `ROADMAP_EXECUTION.md`.

Known residual: published X12 v3 remediation still links `/lessons/R02`; correcting it needs an X12 v4 (published sources are never edited in place).

### Tested OS/runtime/browser matrix for this execution

Linux x64 only, Node 26.8.1, Chromium (Playwright). Each group was gated in a clean `git worktree` of the staged commit: lint, typecheck, validate:content, validate:v2, unit/integration tests, V2 production build with 10 V2 browser flows, and default production build with 9 legacy flows. Final C/M commit: 259 tests in 49 files, 10 legacy flows; V2 flows passed 10/10 on two full reruns after one intermittent failure of an unscoped heading locator in `e2e/v2-interface.spec.ts` (Codex-owned, reported, not edited). The milestone commits below were **not pushed**, so no GitHub Actions run covers them; the last CI run (Ubuntu/Windows/macOS, Node 24) covers `3c0793b`. Windows/macOS behaviour of the new content is therefore untested.

### Deferred or environment-blocked integrations

ROS 2, Nav2, MoveIt, ros2_control, MuJoCo or other physics engines, simulators, real cameras/sensors/robots and LeRobot data are not installed or authorised here and are not imitated; they stay unavailable. S3 learner observation, human expert review, manual screen-reader and device testing remain outstanding.

### Licensing, security and owner decisions

- All new content is original, CC BY 4.0, author "CoreLab contributors (AI-assisted original draft)", with no third-party sources. Kits are stdlib-only Python with no file, network, subprocess, eval or exec use, and the server never runs them.
- `npm audit --omit=dev`: 0 findings. Full `npm audit`: 16 moderate dev-toolchain findings (minimatch advisory), unchanged.
- Owner decisions needed: (1) whether to push these local commits (then CI covers Windows/macOS); (2) whether AI review is acceptable for the new C/M sources, as it was for Frames/FK; (3) whether to publish X12 v4 to fix the R02 lesson link; (4) whether any environment-dependent subcontract should be pursued (it needs a separately reviewed runtime).

### Local commits (this execution, on top of `3c0793b`)

`558420b` M0 infrastructure · `b9fcefd` B1 (L07, L09, L10, L11) · `a882936` B2 (L15, L16, L19, L21) · `ec99035` B3 (L05, L12, L18, L20) · `84288ba` B4 + L14 (L08, L13, L14, L17, L22) · `69ac7f6` log · `6a44f2e` R05 IK bridge · C/M expansion commit (see `ROADMAP_EXECUTION.md`). Interleaved Codex UI commits: `37328ae`, `f8f319a`, `c633774`, `81d9ca9`.

Commands to reproduce:

~~~sh
npm ci
npm run lint && npm run typecheck
npm run validate:content && npm run validate:v2
npm test
for f in tests/fixtures/*.py; do python3 -I -B "$f" && python3 -I -B -O "$f"; done
npm run build:v2 && npm run test:v2:e2e   # in a disposable copy, temporary database
~~~

## Working implementation (baseline history)

- Existing V1 behavior and topic mastery remain separate from V2.
- Additive, checksummed SQLite sidecar; verified pre-migration WAL copy; supported-version guards and atomic legacy checkpoint hook.
- Durable practice/placement attempts, frozen source bytes/hash, recorded issue/help/feedback exposures, monotonic assistance, strict answer parsing, idempotent close and no practice evidence.
- Original drafts for 22 exercise families plus a bridge and 164 static instances; numeric, fraction, angle and choice feedback. Each core family now has two distinct authored application routes, stated route differences and separate calculation/reasoning checks. Immutable V1/V2 sources remain available after later versions activate; 15 families are at v3 after review fixes; X11 is at v4.
- Validated 26-objective readiness registry, optional paths, original bridge and five manual Python numerical kits (frames, planar FK, exact-arc odometry, bounded P/PI feedback, planar Jacobian/IK). A 176-node/319-edge curriculum projection is advisory only; the live graph is unchanged. Kit self-reports create no evidence.
- Server-gated objective UI with Recommended, Explore and More Practice, route/difficulty choices, scratchpad text that is never executed, history and mobile keyboard support.
- Backup/3 captures all learning rows with existing progress. Bounded localhost preview/confirmation, revision checks, atomic replacement, nonrecursive pre-restore snapshots and foreign-origin handling preserve local identity.
- Owner-approved deferred restore epochs preserve every existing epoch and immediate local provenance. The first actual learning write allocates the new epoch atomically; idempotent/no-op operations and failed writes leave it deferred. Shared envelope/projection/cache accounting keeps repeated boundary restores within the same logical budget.
- Verified I/report execution and reviewed transfer remain unavailable. The C/M engine implements objective-scoped thresholds, durable exposure cuts, relative reviews and delayed retention. Restore recomputes recognized, independently reviewed C/M and review transitions in a disposable staging database; unknown/unreviewed sources remain inert. Two C/M forms (F-FRAMES, F-R04) and two retention pools (RV-FRAMES, RV-R04) carry approved owner-assigned AI review records and C/M release is active.

## Checks actually executed

Baseline: 119 tests in 8 files; content validation confirmed 169 topics, 31 lessons, 42 targeted questions and 28 video resources.

2026-11-02: **210 unit/integration/security tests in 28 files passed on Node 24.22.2**. The earlier failing capacity reproducer remains present and now passes, with repeated exact reduced-budget round trips, inert evidence and rebuilt missing C/M review caches. The epoch-policy refinement was explicitly approved by the owner and recorded in the Master Plan; no independent review was inferred. Node 26.8.1 also passed the preceding 209-test revision. Adding the L03 odometry kit brought the Node 26.8.1 suite to **212 tests in 29 files**; the V2 build and four Chromium V2 flows (now including the odometry kit download) passed on that revision.

Latest lint/typecheck and V2 contract validation passed. The Node 24.22.2 V2 production build and four Chromium V2 flows passed: practice/help/reload/full restore, a valid non-ASCII backup above 8 MB through preview/restore/export while the default route refused it, bridge/manual kit download/self-report, and 390px keyboard/layout/security gates. A keyboard-focus timing regression found during the larger-backup run was fixed and rerun successfully.

A fresh disposable source snapshot completed the default production build and **all seven legacy Chromium tests** on Node 24.22.2, including signed local verification, mastery, remediation, tutor handoff and media controls. No workspace signing keys or learner database were used. Source copy: `/tmp/corelab-v1-final-y_i6zj73`; dependencies were shared from the workspace. The earlier clean-install snapshot also passed `npm ci`; no new dependency or lockfile change was introduced in this qualification.

Two-process SQLite races passed: identical concurrent submissions close once; committed help prevents independent C/M admission, and help arriving after close is refused. Consistent exports retained paired legacy/V2 changes committed by a separate process. Actual SQLite page-full and pre-migration low-space failures preserved history; transaction-state guards retain the original auto-rollback error. Interrupted/corrupt copies are removed; partial migration DDL rolls back with an openable recovery copy. Failure injection after restore snapshot/replacement/pruning preserves the entire previous snapshot set and learning history. A streamed 128 MiB overflow is cancelled before a database is opened.

A valid **133,917,793-byte** disk-backed non-ASCII profile with a closed practice attempt exported, restored and re-exported on the final capacity logic. Capacity stayed **133,950,561 bytes** before/after restore. The fixture left 256 KiB unused; exact-boundary cases use a reduced-budget production path. Linux x64/Node 24.22.2/i5-12500H: **47.585 seconds**, maximum RSS **4,037,042,176 bytes**. This substantial memory footprint underlies the resource budget later accepted in the owner-decision addendum (8 GB RAM and approximately 2 GB free disk); it is not a low-memory support claim or a large-profile measurement on Windows/macOS.

A production-build Chromium restart check passed **fresh off → on/practice → non-1 off/legacy edit → on/acknowledge/resume** using one temporary database. Off means hidden V2 navigation/API and no sidecar created on a fresh profile; existing attempts survive off-mode legacy edits. The test does not separately instrument content filesystem reads.

The actual baseline Store from `38b6a1d` reopened, edited and restored legacy progress on a disposable V2-used database on Node 26.8.1 and Node 24.22.2; sidecar history and user_version=2 survived, mixed history was detected, and acknowledgement resumed practice. Reproduce with `node --import tsx scripts/qualify-v2-compatibility.ts <trusted-baseline-source-directory>`.

A synthetic 50,000-attempt in-memory benchmark on Linux x64, Node 26.8.1, Intel i5-12500H measured ten selector calls at **9.58–40.62 ms**, a **4,882-byte** selector response and **8,232-byte** 50-item history page. Estimated supported-profile bytes were 81,888,728; RSS was 211,677,184. Command: `npm run benchmark:v2`. The fixture has repeated issued bridge attempts and no submitted artifacts; this is not a disk/restore or general workload benchmark.

The detailed local measurements above were obtained on Linux. Later GitHub Actions runs passed Node 24 installation/checks/builds on Windows, macOS and Linux; browser coverage runs on Linux. The Master Plan records owner acceptance of AI content review, the measured resource budget and S1/S2 activation. Manual screen-reader use, large reviewed-evidence stress testing and human expert review remain outstanding. S3 was not run according to the recorded owner decision. See [ACCEPTANCE_STATUS.md](ACCEPTANCE_STATUS.md) for the criterion-by-criterion audit.

Additional reproducible qualification commands (all use new temporary databases):

~~~sh
node --import tsx scripts/qualify-v2-compatibility.ts /absolute/trusted/baseline/source
node --import tsx scripts/qualify-v2-toggle.ts
node --import tsx scripts/qualify-v2-backup.ts --full-budget
~~~

The toggle check requires an existing production build and Playwright Chromium. The full-budget check is an explicit high-memory operation, not a routine startup step.

## Local commits

Latest committed release snapshot checked in this audit: `27dfe44` (L04 code at `2650aa6`). CI run [41398479649](https://github.com/trongnghia-le/corelab-robotics-ai/actions/runs/41398479649) was independently queried during the alignment check: Node 24 jobs on Ubuntu, macOS and Windows all succeeded; browser steps ran on Linux and were explicitly skipped on the other two OSes.

The L06 planar Jacobian/IK expansion (X21/X22, two objectives) was later committed as `94daa9c`/`1fa7fb3` and its CI recorded in `3c0793b` (218 tests in 31 files). Later roadmap milestones are listed in the roadmap execution status above.

- 1a70a20 — execution plan and strict contracts.
- f100af2 — storage, practice, recovery and original static catalog drafts.
- 3639c15 — objective practice and recovery interface.
- dc4225b — scoped C/M assessment and historical replay.
- 1bcb131 — objective learning, manual labs and safe recovery.
- acf694a — versioned practice alternatives and recovery qualification.
- 3edf307 — stable restore capacity, owner-approved deferred epochs, atomic failure recovery and compatibility qualification.

See PROGRESS.md and git log for subsequent milestones. Historical review reports are preserved and are not implementation test results.

## Run the local development preview

Node.js 24+ is required. From the repository:

~~~sh
npm ci
npm run dev:v2
~~~

Open http://127.0.0.1:3000/objectives. The explicit V2 command opts into the preview. Existing npm run dev remains V1/default-off. For a production-mode local preview, run npm run build:v2, then npm run start:v2. No cloud service, API key, Docker, GPU or hardware is needed.

The default database remains .local/corelab.sqlite; V2 adds tables and creates a recovery copy before migration. Tests use temporary databases. Do not expose the server publicly. Back up before using a development build with important learning history.

## Content review and release (2026-11-02)

- **Review.** Five reviewer instances that did not author the content recomputed every key (164 practice items incl. bridge, 2 forms × 2 variants, 64 retention items, 3 kits), probed misconceptions/valid alternatives, guessing under the admission rule, exposure leakage and hint ladders. No key was wrong; about 25 major findings (false accepts, guessable C scopes, giveaways, truncated hints, degenerate data, kit contract gaps) were fixed by separate author instances and re-reviewed by fresh instances until no blocker or major remained (Frames C/M took four rounds plus two narrow item reviews). Remaining minors are recorded in the review reports, e.g. X11 generic hint ladders and some single-route misconception coverage.
- **Versions.** X02, X04–X13, X15, X16, X18, X19 are v3 (v2 archived and resumable). C/M sources and kits were revised in place at v1 because they had never been issuable/downloaded; prior manifests are archived.
- **Code.** Leading U+2212 minus is accepted; displayed expected values are rounded for readability only; the V2 validator rejects truncated graduated hints and float-noise prompts; `content/** -text` keeps hashed content identical on Windows checkouts. Kits: no `assert`-based checks (work under `python -O`), descriptive failure messages, ASCII console banner. Author fixtures: frames/FK 12 alternatives accepted / 48 mutants rejected; odometry 7 / 40.
- **Checks.** Linux/Node 26.8.1: 214 tests in 29 files, lint, typecheck, content and V2 validation, default and V2 production builds, four V2 and seven legacy Chromium flows (including issuing an approved C/M form). GitHub Actions run 41394222659 on 7a508a2 passed on ubuntu-latest, windows-latest and macos-latest (Node 24).

## Remaining work / gates

Not done: S3 learner observation (owner chose not to run it), human expert/pedagogical review, manual screen-reader and physical-device testing, large reviewed-evidence workload. Windows/macOS evidence is CI only (Node 24; browser flows on Linux). All 22 roadmap labs now have a manual-kit foundation; L05 and L07–L22 remain partial, with their environment-dependent subcontracts listed as unavailable (see the roadmap execution status above). Optional MuJoCo/ROBOTIS documentation is link-only; ROS documentation retrieval was provider-blocked. No simulator/ROS/hardware integration has been tested or enabled.

`LEARNER_PILOT_PROTOCOL.md` prepares S3 observations and stop criteria. No participant outreach or 21-day trial has occurred.

`npm audit` rerun on 2026-11-02 reported **16 moderate development-toolchain findings** rooted in minimatch's globparts amplification advisory (GHSA-g3hv-75wg-m249). `npm audit --omit=dev` reported **zero findings**. The suggested fix is a major ESLint downgrade; no force fix was applied. Toolchain remediation needs compatibility review. This is an actual audit finding, not a claim that production dependencies are permanently vulnerability-free.

Independent technical/adversarial/pedagogical reviewers, tested OS support/capacity decisions, reviewed executable isolation and actual learner observations cannot be fabricated. The feature flag remains off by default. No whole-platform completion claim is made.

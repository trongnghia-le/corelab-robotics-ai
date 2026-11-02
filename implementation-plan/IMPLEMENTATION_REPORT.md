# CoreLab V2 implementation report

**S1/S2 activated by the owner on 2026-11-02 after an owner-assigned AI content review — not a human expert review or learner-outcome certification.** The S3 learner pilot was not run, at the owner's request. The repository was pushed to its GitHub remote on 2026-11-02 for cross-platform CI; no deployment or real learner-data deletion has been performed.

## Working implementation so far

- Existing V1 behavior and topic mastery remain separate from V2.
- Additive, checksummed SQLite sidecar; verified pre-migration WAL copy; supported-version guards and atomic legacy checkpoint hook.
- Durable practice/placement attempts, frozen source bytes/hash, recorded issue/help/feedback exposures, monotonic assistance, strict answer parsing, idempotent close and no practice evidence.
- Original drafts for 20 exercise families plus a bridge and 152 static instances; numeric, fraction, angle and choice feedback. Each core family now has two distinct authored application routes, stated route differences and separate calculation/reasoning checks. Immutable V1/V2 sources remain available after later versions activate; 15 families are now at v3 after review fixes.
- Validated 24-objective readiness registry, optional paths, original bridge and three manual Python numerical kits (frames, planar FK, exact-arc odometry). A 176-node/319-edge curriculum projection is advisory only; the live graph is unchanged. Kit self-reports create no evidence.
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

A valid **133,917,793-byte** disk-backed non-ASCII profile with a closed practice attempt exported, restored and re-exported on the final capacity logic. Capacity stayed **133,950,561 bytes** before/after restore. The fixture left 256 KiB unused; exact-boundary cases use a reduced-budget production path. Linux x64/Node 24.22.2/i5-12500H: **47.585 seconds**, maximum RSS **4,037,042,176 bytes**. This substantial memory footprint needs a release resource-budget decision; it is not a claim of low-memory or cross-platform suitability.

A production-build Chromium restart check passed **fresh off → on/practice → non-1 off/legacy edit → on/acknowledge/resume** using one temporary database. Off means hidden V2 navigation/API and no sidecar created on a fresh profile; existing attempts survive off-mode legacy edits. The test does not separately instrument content filesystem reads.

The actual baseline Store from `38b6a1d` reopened, edited and restored legacy progress on a disposable V2-used database on Node 26.8.1 and Node 24.22.2; sidecar history and user_version=2 survived, mixed history was detected, and acknowledgement resumed practice. Reproduce with `node --import tsx scripts/qualify-v2-compatibility.ts <trusted-baseline-source-directory>`.

A synthetic 50,000-attempt in-memory benchmark on Linux x64, Node 26.8.1, Intel i5-12500H measured ten selector calls at **9.58–40.62 ms**, a **4,882-byte** selector response and **8,232-byte** 50-item history page. Estimated supported-profile bytes were 81,888,728; RSS was 211,677,184. Command: `npm run benchmark:v2`. The fixture has repeated issued bridge attempts and no submitted artifacts; this is not a disk/restore or general workload benchmark.

These are Linux results in this execution environment. Windows/macOS, remotely executed CI, manual screen-reader use, a full-size reviewed-evidence workload, an approved memory/disk budget, independent item review and the 21-day learner pilot remain unvalidated. See [ACCEPTANCE_STATUS.md](ACCEPTANCE_STATUS.md) for the criterion-by-criterion audit.

Additional reproducible qualification commands (all use new temporary databases):

~~~sh
node --import tsx scripts/qualify-v2-compatibility.ts /absolute/trusted/baseline/source
node --import tsx scripts/qualify-v2-toggle.ts
node --import tsx scripts/qualify-v2-backup.ts --full-budget
~~~

The toggle check requires an existing production build and Playwright Chromium. The full-budget check is an explicit high-memory operation, not a routine startup step.

## Local commits

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

Not done: S3 learner observation (owner chose not to run it), human expert/pedagogical review, manual screen-reader and physical-device testing, large reviewed-evidence workload. Windows/macOS evidence is CI only (Node 24; browser flows on Linux). The 22-lab roadmap labels three manual kits as working and 19 lab implementations as planned; related exercise links are bounded preparation, not lab completion. Optional MuJoCo/ROBOTIS documentation is link-only; ROS documentation retrieval was provider-blocked. No simulator/ROS/hardware integration has been tested or enabled.

`LEARNER_PILOT_PROTOCOL.md` prepares S3 observations and stop criteria. No participant outreach or 21-day trial has occurred.

`npm audit` rerun on 2026-11-02 reported **16 moderate development-toolchain findings** rooted in minimatch's globparts amplification advisory (GHSA-g3hv-75wg-m249). `npm audit --omit=dev` reported **zero findings**. The suggested fix is a major ESLint downgrade; no force fix was applied. Toolchain remediation needs compatibility review. This is an actual audit finding, not a claim that production dependencies are permanently vulnerability-free.

Independent technical/adversarial/pedagogical reviewers, tested OS support/capacity decisions, reviewed executable isolation and actual learner observations cannot be fabricated. The feature flag remains off by default. No whole-platform completion claim is made.

# CoreLab V2 implementation report

**In progress — not a completion or release certification.** Implementation is authorized; no push, deployment, repository visibility change or real learner-data deletion has been performed.

## Working implementation so far

- Existing V1 behavior and topic mastery remain separate from V2.
- Additive, checksummed SQLite sidecar; verified pre-migration WAL copy; supported-version guards and atomic legacy checkpoint hook.
- Durable practice/placement attempts, frozen source bytes/hash, recorded issue/help/feedback exposures, monotonic assistance, strict answer parsing, idempotent close and no practice evidence.
- Original drafts for 20 exercise families plus a bridge and 152 static instances; numeric, fraction, angle and choice feedback. Each core family now has two distinct authored application routes, stated route differences and separate calculation/reasoning checks. Immutable V1 sources remain available after V2 source activation. Independent content review is still pending.
- Validated 24-objective readiness registry, optional paths, original bridge and two manual Python numerical kits. A 176-node/319-edge curriculum projection is advisory only; the live graph is unchanged. Kit self-reports create no evidence.
- Server-gated objective UI with Recommended, Explore and More Practice, route/difficulty choices, scratchpad text that is never executed, history and mobile keyboard support.
- Backup/3 captures all learning rows with existing progress. Bounded localhost preview/confirmation, revision checks, atomic replacement, nonrecursive pre-restore snapshots and foreign-origin handling preserve local identity.
- Verified I/report execution and reviewed transfer remain unavailable. The C/M engine implements objective-scoped thresholds, durable exposure cuts, relative reviews and delayed retention. Restore recomputes recognized, independently reviewed C/M and review transitions in a disposable staging database; unknown/unreviewed sources remain inert. The 48 form questions and 36 retrieval items remain pending independent review, and C/M release activation is disabled.

## Checks actually executed

Baseline: 119 tests in 8 files; content validation confirmed 169 topics, 31 lessons, 42 targeted questions and 28 video resources.

Current: **191 unit/integration/security tests in 24 files passed**; lint/typecheck, legacy content and V2 contract validation passed; the current V2 production build passed. Four Chromium V2 flows passed: practice/help/reload/full restore, a valid non-ASCII backup above 8 MB through preview/restore/export while the default route refused it, bridge/manual kit download/self-report, and 390px keyboard/layout/security gates. A keyboard-focus timing regression found during the larger-backup run was fixed and the flow rerun successfully.

A disposable source copy completed `npm ci`, the default production build and **all seven legacy Chromium tests**, including signed local verification, mastery, remediation, tutor handoff and media controls. No workspace signing keys or learner database were used. Source copy: `/tmp/corelab-v1-regression-9acqnaet` (captured before the later capacity/metadata hardening).

Two-process SQLite races passed: identical concurrent submissions close once; committed help prevents independent C/M admission, and help arriving after close is refused. A streamed 128 MiB overflow is cancelled before a database is opened. These do not constitute full near-limit profile qualification.

A synthetic 50,000-attempt in-memory benchmark on Linux x64, Node 26.8.1, Intel i5-12500H measured ten selector calls at **9.58–40.62 ms**, a **4,882-byte** selector response and **8,232-byte** 50-item history page. Estimated supported-profile bytes were 81,888,728; RSS was 211,677,184. Command: `npm run benchmark:v2`. The fixture has repeated issued bridge attempts and no submitted artifacts; this is not a disk/restore or general workload benchmark.

These are Linux results in this execution environment. Windows/macOS, Node 24 CI, screen-reader use, complete near-128-MiB profile export/replay/restore headroom, independent item review and the 21-day learner pilot remain unvalidated. A streamed over-limit rejection is different from a full valid profile round trip.

## Local commits

- 1a70a20 — execution plan and strict contracts.
- f100af2 — storage, practice, recovery and original static catalog drafts.
- 3639c15 — objective practice and recovery interface.
- dc4225b — scoped C/M assessment and historical replay.
- 1bcb131 — objective learning, manual labs and safe recovery.

See PROGRESS.md and git log for subsequent milestones. Historical review reports are preserved and are not implementation test results.

## Run the local development preview

Node.js 24+ is required. From the repository:

~~~sh
npm ci
npm run dev:v2
~~~

Open http://127.0.0.1:3000/objectives. The explicit V2 command opts into the preview. Existing npm run dev remains V1/default-off. For a production-mode local preview, run npm run build:v2, then npm run start:v2. No cloud service, API key, Docker, GPU or hardware is needed.

The default database remains .local/corelab.sqlite; V2 adds tables and creates a recovery copy before migration. Tests use temporary databases. Do not expose the server publicly. Back up before using a development build with important learning history.

## Remaining work / gates

Continue the Master Plan: complete boundary/capacity and rollback qualification, independent S1/S2 item review and activation, explicit OS support evidence, and the final acceptance audit. The 22-lab roadmap labels two manual kits as working and 20 lab implementations as planned; related exercise links are bounded preparation, not lab completion. Optional MuJoCo/ROBOTIS documentation is link-only; ROS documentation retrieval was provider-blocked. No simulator/ROS/hardware integration has been tested or enabled.

`LEARNER_PILOT_PROTOCOL.md` prepares S3 observations and stop criteria. No participant outreach or 21-day trial has occurred.

`npm audit` in the disposable clean install reported **16 moderate development-toolchain findings** rooted in minimatch's globparts amplification advisory (GHSA-g3hv-75wg-m249). `npm audit --omit=dev` reported **zero findings**. No force fix or major downgrade was applied; toolchain remediation requires compatibility review. This is an actual audit finding, not a claim that production dependencies are permanently vulnerability-free.

Independent technical/adversarial/pedagogical reviewers, tested OS support/capacity decisions, reviewed executable isolation and actual learner observations cannot be fabricated. The feature flag remains off by default. No whole-platform completion claim is made.

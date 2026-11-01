# CoreLab V2 implementation report

**In progress — not a completion or release certification.** Implementation is authorized; no push, deployment, repository visibility change or real learner-data deletion has been performed.

## Working implementation so far

- Existing V1 behavior and topic mastery remain separate from V2.
- Additive, checksummed SQLite sidecar; verified pre-migration WAL copy; supported-version guards and atomic legacy checkpoint hook.
- Durable practice/placement attempts, frozen source bytes/hash, recorded issue/help/feedback exposures, monotonic assistance, strict answer parsing, idempotent close and no practice evidence.
- Original drafts for 20 exercise families and 140 static instances; numeric, fraction, angle and choice feedback. Independent content review is pending. Route diversity and independent oracle coverage require further work.
- Server-gated objective UI with Recommended, Explore and More Practice, route/difficulty choices, scratchpad text that is never executed, history and mobile keyboard support.
- Backup/3 captures all learning rows with existing progress. Bounded localhost preview/confirmation, revision checks, atomic replacement, nonrecursive pre-restore snapshots and foreign-origin handling preserve local identity.
- Verified I/report execution and reviewed transfer remain unavailable. Current restored V2 evidence is conservatively inert; the full C/M policy/review replay engine is still being implemented.

## Checks actually executed

Baseline: 119 tests in 8 files; content validation confirmed 169 topics, 31 lessons, 42 targeted questions and 28 video resources.

Current: 140 unit/integration/security tests in 14 files passed; lint and typecheck passed; V2 production build passed. Two Chromium flows passed: practice → help → submission → reload → full backup/restore, and 390px keyboard/layout → gated verification/import. A generated mobile screenshot was inspected.

These are Linux results in this execution environment. Windows/macOS, screen-reader use, the full 128 MiB boundary, named-machine capacity budgets, independent item review and the 21-day learner pilot are not validated by these results.

## Local commits

- 1a70a20 — execution plan and strict contracts.
- f100af2 — storage, practice, recovery and original static catalog drafts.

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

Continue the Master Plan: readiness bridge and manual kits, complete C/M source/admission/replay/review workflow, stronger exercise alternatives/oracles, curriculum and optional-resource integration, boundary/concurrency/browser regressions and final audit.

Independent technical/adversarial/pedagogical reviewers, tested OS support/capacity decisions, reviewed executable isolation and actual learner observations cannot be fabricated. The feature flag remains off by default. No whole-platform completion claim is made.

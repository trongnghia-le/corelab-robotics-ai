# CoreLab V2 implementation progress

Baseline: 38b6a1d. Implementation authorized by the owner on 2026-10-31; local commits permitted, no push/deployment/data deletion authorized. Existing next-env.d.ts changes are unrelated and must not be committed.

## Baseline

- Read the finalized specification, three proposals, audit and existing Master Plan; input hashes are recorded in the specification.
- Existing unit suite: 119 passed, 8 files.
- Content validation: 169 topics, 31 lessons, 42 targeted questions, 28 video resources.
- The Master Plan already exists; continue it rather than replace it.

## Execution

- Foundation committed as 1a70a20: strict contracts, canonicalization and safe request parsing.
- 2026-11-01: additive schema/checksum guards, pre-migration WAL copy, legacy pre-commit checkpoint/capacity hook, durable practice attempts/hints/exposures, close-once grading, complete backup/3, preview-confirm restore, foreign provenance and nonrecursive snapshots implemented against temporary databases.
- Current suite: 138 tests passed in 13 files; typecheck passed. The initial lint run caught three unused imports, which were removed; rerun pending.
- Twenty original family drafts contain 140 static items. Contracts are split into immutable source files; review metadata is separate. Author-side tests are not independent content approval. Meaningful route diversity and broader independent oracle tests still need strengthening before release.
- Storage/practice/recovery and original catalog drafts committed as f100af2.
- UI/API integration now works: server-gated objective pages, Recommended/Explore/More Practice, route selection, numeric/choice inputs, observed help, saved nonexecuted coding notes, history, full backup preview/confirm and snapshot recovery.
- Validation: 140 tests passed in 14 files; lint/typecheck and V2 production build passed; 2 Chromium E2E flows passed (practice/help/reload/restore and 390px keyboard/security gates). A mobile screenshot was inspected. No Windows/macOS/browser-screen-reader result is claimed.
- C/M kernel and chronological restore replay now implemented: scoped 80%/critical-item admission, cross-tab exposure cuts, immutable variants, independent-review metadata gates, relative due reviews, delayed retention, and replayed effective projections. Original claim bytes are retained. 48 form questions and 36 retrieval items are authored drafts; release activation remains false and actual independent reviews are pending. Synthetic test approvals exercise the kernel only.
- 2026-11-01: 149 tests passed in 15 files; typecheck and lint passed for the C/M/replay milestone. Restore tests cover foreign provenance, rebuilt review caches, grade tampering, submission hashes and missing scopes. Readiness bridge, manual kits and broader content/UX integration follow next.
- Next.js regenerates next-env.d.ts during builds. Restore the exact user version from /tmp/corelab-v2-implementation-z6lt9wj8/next-env.original after each build; do not stage it.
- Independent content/security reviewers, actual Windows/macOS results, and learner pilot remain external gates. No reviewer approval or trial result will be fabricated.
- Expansion beyond the Frames/FK pilot is authorized, but only functioning authored activities will be offered. Unsupported execution and integrations remain unavailable.

## Resume

Read this file, git log/status, the Master Plan and IMPLEMENTATION_REPORT.md when present. Work only on temporary databases during tests. Never use default getStore() against learner data in test scripts. Keep verified I disabled.

## 2026-11-01: integrated objective workflow milestone

- Added a validated 24-objective registry, advisory readiness DAG, four optional goal paths and a 176-node/319-edge curriculum planning projection. The 169-topic live graph and legacy mastery are unchanged.
- Added optional original radians/trigonometry text and 12 practice instances (152 total). Added two downloadable, standard-library-only Python starter/self-check kits with durable sample/download exposure and idempotent practice-only self-reports. Web code executes nothing.
- Integrated Learn/bridge/readiness, manual Apply, gated C/M scopes/reviews and optional goals. Recommended uses server-side independent gaps/readiness; history is paginated summaries with on-demand detail. Choice order is shuffled and frozen; source validation permits only the authored option permutation.
- Added immutable content validation, source hashes and a current SQLite recovery-copy CLI with disk-headroom preflight. Existing CI now includes V2 validation/build and Linux V2 browser checks; these remote jobs have NOT been run.
- Actual Linux checks: 159 tests in 21 files passed; types/lint/content and V2 contract validation passed; latest V2 production build passed; three Chromium flows passed, including manual-kit download/self-report, bridge and phone-width keyboard use. The manual kit author fixtures accepted four valid alternatives and rejected 16 injected bugs; NOT independent sign-off.
- Next: strengthen all-family alternative routes and independent numeric oracle coverage using new immutable versions, complete optional lab-roadmap/resource presentation, rehearse legacy browser regression in a disposable checkout, and expand recovery/capacity/concurrency acceptance checks.

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
- Next.js regenerates next-env.d.ts during builds. Restore the exact user version from `.local/codex-v2-resume-5_y675c8/next-env.original` after each build; do not stage it. The earlier /tmp copy was lost.
- Independent content/security reviewers, actual Windows/macOS results, and learner pilot remain external gates. No reviewer approval or trial result will be fabricated.
- Expansion beyond the Frames/FK pilot is authorized, but only functioning authored activities will be offered. Unsupported execution and integrations remain unavailable.

## Resume

Read this file, git log/status, the Master Plan and IMPLEMENTATION_REPORT.md when present. Work only on temporary databases during tests. Never use default getStore() against learner data in test scripts. Keep verified I disabled.

Latest code milestone: `3edf307`; final qualification: 210 tests/28 files, four V2 and seven legacy browser flows, Node 24 production builds. Deferred restore epochs are now explicitly owner-approved and implemented. Read ACCEPTANCE_STATUS.md for remaining release/resource/review gates. No known failing test remains in this continuation.

## 2026-11-01: integrated objective workflow milestone

- Added a validated 24-objective registry, advisory readiness DAG, four optional goal paths and a 176-node/319-edge curriculum planning projection. The 169-topic live graph and legacy mastery are unchanged.
- Added optional original radians/trigonometry text and 12 practice instances (152 total). Added two downloadable, standard-library-only Python starter/self-check kits with durable sample/download exposure and idempotent practice-only self-reports. Web code executes nothing.
- Integrated Learn/bridge/readiness, manual Apply, gated C/M scopes/reviews and optional goals. Recommended uses server-side independent gaps/readiness; history is paginated summaries with on-demand detail. Choice order is shuffled and frozen; source validation permits only the authored option permutation.
- Added immutable content validation, source hashes and a current SQLite recovery-copy CLI with disk-headroom preflight. Existing CI now includes V2 validation/build and Linux V2 browser checks; these remote jobs have NOT been run.
- Actual Linux checks: 159 tests in 21 files passed; types/lint/content and V2 contract validation passed; latest V2 production build passed; three Chromium flows passed, including manual-kit download/self-report, bridge and phone-width keyboard use. The manual kit author fixtures accepted four valid alternatives and rejected 16 injected bugs; NOT independent sign-off.
- Next: strengthen all-family alternative routes and independent numeric oracle coverage using new immutable versions, complete optional lab-roadmap/resource presentation, rehearse legacy browser regression in a disposable checkout, and expand recovery/capacity/concurrency acceptance checks.

## 2026-11-01: exercise expansion and qualification

- Authored immutable version-2 contracts for all 20 core families, with distinct second routes, explicit route notes and math/reasoning checks. The 20 V1 source files are retained unchanged; archived contracts still resume/grade. Canonical decimal-input fingerprints recognize early raw-number aliases on resume/restore without rewriting stored histories.
- Added a typed 22-lab roadmap: only two manual numerical kits are available, 20 lab implementations remain planned. External documentation is link-only; no simulator/ROS/device run is claimed.
- Hardened supported metadata checks, validates complete exports before offering them, and aggregates capacity row bytes in SQLite instead of loading historical artifacts on every write. Read models use the transactional capacity cache. Added real process races, C/M numerical oracle checks and streamed overflow cancellation.
- Actual validation: 191 tests/24 files; lint/types/legacy and V2 content passed; V2 build passed; four V2 Chromium flows passed after correcting an initial keyboard-focus timing failure. Large non-ASCII document above 8 MB restored/exported on the advertised V2 routes.
- Clean disposable source snapshot /tmp/corelab-v1-regression-9acqnaet: npm ci/default build and all seven legacy Chromium tests passed. That snapshot precedes the latest capacity/metadata hardening; default-off protected scoring/verifier/content files remain unchanged.
- 50,000 repeated issued bridge attempts, in-memory Linux/Node26.8.1/i5-12500H: selector 9.58–40.62 ms, 4,882-byte response, 8,232-byte history page; 81,888,728 estimated profile bytes, RSS 211,677,184. Not a full disk/restore/capacity qualification.
- Audit: zero production npm findings; 16 moderate development lint-chain findings rooted in minimatch. No unsafe force update/downgrade.
- S3 protocol prepared; no outreach or trial. Remaining technical qualification: near-limit valid-profile projection/headroom and disk/migration failure injection, broader cross-process consistent export, exact flag-off behavior, complete acceptance matrix and supported OS evidence. Independent review/release gates remain external and cannot be self-granted.

## 2026-11-02: compatibility and data-safety qualification (work in progress)

- Last committed green milestone: `acf694a` (191 tests). Subsequent hardening is uncommitted; preserve it on resume.
- Reproduced a supported-budget defect with a reduced 64 KiB test using the production sizing path. SQL write accounting initially omitted part of the complete backup envelope; shared envelope sizing fixes that mismatch. The remaining regression is real: immediate restore-epoch growth makes the last accepted profile fail its restore capacity check. Do not skip this test or claim full acceptance.
- D11 question sent to the owner: allow allocating an empty post-restore learning epoch on the first subsequent learning write, while recording provenance immediately, or retain immediate epochs with explicit near-limit maintenance. No answer received and no normative epoch change implemented. Continue independent qualification while pending.
- Added consistent export coverage under a real second process committing paired legacy/V2 updates. Added missing pre-migration disk-headroom and partial/invalid metadata tests. An actual SQLite page-full failure revealed unconditional ROLLBACK could mask the original error after SQLite auto-rollback; transaction-state guards now preserve the original failure and unchanged rows/counters/revision.
- Strengthened full-backup duplicate evidence-scope and review-reference validation. Added a qualification script running the actual baseline Store from `38b6a1d` against a disposable V2-used database: reopen/edit/legacy restore preserves sidecar rows and user_version=2, detects mixed history and resumes after acknowledgement. Passed on Node 26.8.1 and Node 24.22.2.
- Latest complete Node 24.22.2 unit run: **196 passed, 1 failed (capacity-boundary), 197 total in 26 files**. All five targeted storage/platform/concurrency suites passed (31 tests). Node 24 V2 build and four Chromium V2 flows passed; lint, typecheck and V2 content validation passed. No Windows/macOS result or external review is claimed.
- Previous /tmp resume artifacts are no longer available. Restore the user's exact next-env.d.ts after each Next build from **`.local/codex-v2-resume-5_y675c8/next-env.original`** (private ignored recovery copy). Do not stage next-env.d.ts. The baseline extraction for the current probe is `/tmp/corelab-baseline-compat-jfaz_767`; recreate from git archive if absent.
- `ACCEPTANCE_STATUS.md` maps the specification criteria to actual evidence and remaining gates. Still no push/deployment, real learner-data access/deletion, C/M release activation or verified I.

### D11 answer and capacity repair

- Owner explicitly selected **defer the empty learning epoch until the next write**. The Master Plan records the approved refinement; the historical Unified Spec is unchanged.
- Implemented strictly validated local pending provenance, first-real-write epoch allocation, no-op/idempotent rollback, enabled legacy pre-commit allocation and acknowledgement handling. Existing epochs are never removed. Repeated restore/export no longer appends unused learning rows.
- Replaced repeat-charged evidence overhead with stable projection/review-cache floors in the shared envelope budget. Reduced-boundary fixtures now cover unchanged history, inert I claims, and missing C/M review caches rebuilt using explicit synthetic approvals. No real review/release gate is changed.
- Added failure injection after snapshot, replacement and pruning; previous snapshots/history/revision roll back together. Partial migration DDL rolls back while its validated pre-copy remains openable. Collection-bound help writes refuse atomically.
- Latest complete Node 24 suite: **209 passed in 28 files**, lint/typecheck and both content validators passed. This supersedes the earlier 196+1 failing run; the reproducer remains present and passing.
- Before the deferred-epoch refinement, a 133,917,793-byte valid disk-backed non-ASCII profile with a closed practice attempt exported/restored/re-exported successfully on Linux/Node 24.22.2 in 45.307 s; max RSS 4,152,512,512 bytes. Fixture left 256 KiB unused. This is not the exact-boundary or memory-budget release gate. Repeating on final code remains to do.

### Final qualification of this continuation

- The malformed-pending-provenance guard test brings the complete Node 24 suite to **210 passed in 28 files**. Node 26 passed the preceding 209-test revision. No tests skipped.
- Node 24 V2 build/four Chromium flows passed. Actual production-process restart check passed fresh off → on/practice → non-1 off/legacy edit → on/acknowledge/resume. Default build and seven legacy browser flows passed in `/tmp/corelab-v1-final-y_i6zj73`, with signing activity confined to that disposable copy.
- Final large-profile mechanism run: 133,917,793-byte export; 133,950,561 supported-budget bytes both before and after restore; 11,060 non-ASCII notes plus a closed V2 practice attempt; 47.585 s; max RSS 4,037,042,176 bytes. Command: `node --import tsx scripts/qualify-v2-backup.ts --full-budget`. This leaves 256 KiB unused and does not replace exact reduced-budget or large reviewed-evidence testing. Release resource-budget approval remains open.
- Latest production npm audit: zero findings; full development audit: 16 moderate minimatch-chain findings, suggested major ESLint downgrade not applied.
- Remaining external gates: genuine technical/adversarial/pedagogical reviews, S1/S2 release activation, approved memory/disk budget and tested OS support, actual S3 volunteers/21-day observations. Verified I/transfer and 20 unimplemented roadmap labs remain unavailable/planned. No whole-platform completion claim.

## 2026-11-02: L03 odometry manual kit

- Added a third standard-library-only manual kit, `L03-odometry` (objective `R02.exact-arc`): wheel/body conversion and exact constant-curvature odometry with nonzero initial headings, reverse motion, pure spin, small arcs, units and invalid inputs. Samples live in a separate immutable file so the shared L01/L02 sample bytes and their kit hashes are unchanged.
- Roadmap L03 is now `manual-self-check`; 19 lab implementations remain planned. The objective gained an advisory readiness link to `R03.compose-invert-se2` and the kit reference; statement/excludes are unchanged. The previous content manifest is archived under `content/v2/manifests/` and the current manifest is updated additively.
- Author fixture: two valid alternative integrators accepted, 18 injected bugs rejected, starter fails as intended. NOT independent sign-off; no calibration, localization, ROS or simulator claim.
- Actual validation on Linux/Node 26.8.1: **212 tests in 29 files** passed; lint, typecheck, legacy content and V2 contract validation passed; V2 production build and four Chromium V2 flows passed, including the odometry kit download. next-env.d.ts restored after the build and not staged.
- External gates unchanged: independent reviews, S1/S2 release activation, resource budget approval, Windows/macOS support and the S3 learner pilot.

## 2026-11-02: review gates, cross-platform CI and S1/S2 activation

- Owner decisions (recorded in the Master Plan addendum): accept an owner-assigned AI review for G2; approve the measured D11 budget (128 MiB profiles, 8 GB RAM, about 2 GB free disk); push to GitHub for Windows/macOS CI; activate S1/S2; do not run S3. Commits do not credit an AI contributor.
- First CI run (8dc13a5): ubuntu and macOS passed; Windows failed `validate:v2` because CRLF checkout changed hashed content bytes (reproduced locally with `core.autocrlf=true`). Fixed with `content/** -text`.
- Independent AI review of all issuable content found no wrong key and about 25 majors; fixes by separate author instances, then fresh re-reviews until no blocker/major remained. 15 families moved to v3; C/M sources and kits were revised in place at v1 (never issuable/downloaded). Approved review records: all 21 families, F-FRAMES, F-R04, RV-FRAMES, RV-R04. `CM_RELEASED = true`.
- Added: U+2212 answer acceptance, display rounding of expected values, validator rules for truncated hints and float-noise prompts, independent X08/X09 and angle-parsing C/M test oracles, kit fixes (python -O safe, contract cases, messages, ASCII banner) with 48/40 named mutants.
- Linux/Node 26.8.1: 214 tests in 29 files; lint, typecheck, content and V2 validation; default and V2 builds; 4 V2 + 7 legacy Chromium flows passed. Legacy browser run used its own `.local/e2e-*.sqlite`; signing keys and the learner database were not modified. next-env.d.ts restored and not staged.
- GitHub Actions `Validate CoreLab` run 41394222659 on 7a508a2: ubuntu-latest, windows-latest and macos-latest all passed (lint, typecheck, content/V2 validation, unit tests, default and V2 builds; Linux browser flows).

## 2026-11-02: X11 v4 and L04 bounded-feedback kit

- X11 v4 (v3 archived): item-specific hint ladders and remediation, q1 != 0 on every tabletop item, substantial tool angles on inspection (Rᵀ/identity rejected), rebalanced difficulty, wrap and intermediate-precision notes. Independent re-review: approve-with-minor; approved record written.
- L04 kit `L04-pid` (objective link C01.bounded-step, practice beyond its one-step statement; objective scope unchanged, readiness M07.euler-step recommended): bounded P/PI on a declared toy integrator with constant disturbance, anti-windup behaviour band (conditional integration, clamping, guarded back-calculation accepted; unguarded fixed-gain back-calculation and freeze-whenever-saturated rejected), simulate and settling/overshoot metrics. Roadmap L04 is manual-self-check; 18 labs remain planned. L06 (Jacobian/IK) was not started: it needs a new objective and the Master Plan excludes Jacobian expansion without a separate owner decision.
- Independent review found a blocker (windup judged from kp·e only passed) and a wording major (back-calculation); fixed and re-reviewed: approve-with-minor. Fixture: 5 alternatives accepted, 63 mutants rejected, also under python -O; 50 samples (zod max).
- Linux/Node 26.8.1: 215 tests in 30 files; lint, typecheck, content and V2 validation; default and V2 builds; 4 V2 (incl. L04 download) + 7 legacy Chromium flows passed.

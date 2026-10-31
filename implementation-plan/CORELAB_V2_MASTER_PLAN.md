# CoreLab V2 Implementation Master Plan

**Status: execution plan, not implementation authorization.** All task boxes and release gates are pending. This document adds no application functionality and authorizes no migration, live-data change, commit, push or visibility change.

**Baseline:** repository commit `38b6a1d8f0baae9a753882185da7bd4430d14277`, inspected 2026-10-31. Preserve the pre-existing modification to `next-env.d.ts` and all review documents. Recheck the baseline before implementation; do not assume an unchanged worktree.

**Authority:** [Unified Specification](../unified-integration/CORELAB_V2_UNIFIED_SPEC.md), SHA-256 **3548022ac1f428b3504a5e0ed8106f75c2e33a75a266c4d463e4e3443ed23339**. Its §15 acceptance IDs are referenced below. The [Curriculum](../curriculum-review/proposed_curriculum_v2.md), [Practical Learning System](../corelab-labs-review/proposed_practical_learning_system.md) and [Exercise Bank](../exercise-bank-review/proposed_exercise_bank.md) remain design inputs, with the precedence decisions in Unified Spec §17. This plan adds implementation sequencing and small interface decisions; it does not adopt the 176-topic graph or broaden evidence scope.

## 1. Outcome and nonnegotiable boundaries

Deliver **S1 Practice first**, **S2 scoped C/M Verification second**, then **S3 a learner pilot lasting at least 21 days**. Each stage is independently useful; none depends on protected implementation verification.

- Keep the 169 production topic identities, existing lessons/assessments/practice banks, prerequisite graph, topic mastery, legacy review logic and signed report serialization intact.
- Keep `masteryFor` independent of V2. No V2 event enters the legacy attempts/labs arrays or changes L0–L4.
- Use the existing SQLite file, `user_version=2`, and independently versioned additive sidecar tables.
- Keep automatic I and reviewed transfer unavailable in every pilot service, import path and UI. Preserve inert history without admitting it.
- No web route imports, compiles or executes learner code. No Docker, cloud, authentication, native mobile app, cross-device synchronization, simulator or robot dependency.
- Keep Node.js 24+, loopback binding, existing Host/origin checks and Windows/macOS/Linux installation intent. Publish only OS/browser results actually obtained.
- English UI throughout. Preserve the existing larger typography; use rem-based additions, readable mathematical notation and text alternatives.
- Learners can choose any activity and route, skip bridges and override suggestions. Prerequisites advise; they do not lock this numerical pilot.

**Useful S1 completion:** choose a Frames/FK route, practice with graded help, resume reliably, use optional unverified kits, and export/restore all history safely. **Useful S2 completion:** take fresh scoped C/M checks and due reviews with durable exposure and honest admission. Neither is a whole-topic mastery PASS.

## 2. Repository facts that determine the work

These are source observations, not V2 test results.

| Actual location | Current behavior | Planning consequence |
| --- | --- | --- |
| [lib/storage.ts](../lib/storage.ts) | One strict Progress JSON row; public Store.db; WAL; user_version rejects >2; update owns BEGIN IMMEDIATE/COMMIT | Reuse the connection; add a gated synchronous pre-commit hook. Never nest Store.update inside a V2 transaction |
| [lib/actions.ts](../lib/actions.ts), [app/api/action/route.ts](../app/api/action/route.ts) | Restore reaches Store.restore directly with only confirm=true; handler caps declared bytes and string length at 8,000,000 | Guard the old restore entry point when a supported V2 sidecar is active; send users to V2 preview/confirm instead of bypassing full snapshots |
| [lib/http.ts](../lib/http.ts) | Host/origin protection and fixed Content-Length ceiling; failure maps errors to HTTP 400 | Preserve the default ceiling; V2 needs bounded streamed bytes and explicit 404/409/413/503 responses |
| [components/tools.tsx](../components/tools.tsx) | Settings owns legacy 8 MB upload, export link, preview and replacement; Practice/Tutor are here too | Add gated V2 components and keep the complete legacy branch when off; no standalone settings.tsx exists |
| [app/[[...slug]]/page.tsx](../app/[[...slug]]/page.tsx), [components/workspace.tsx](../components/workspace.tsx) | Two-segment routes accept only lesson/assessment topic IDs; client dispatch otherwise falls through to Sources | Change both routing layers for objective IDs; validate against the V2 objective registry, never topicMap |
| [components/provider.tsx](../components/provider.tsx), [lib/types.ts](../lib/types.ts) | AppState is legacy; actions refresh all legacy state | Keep AppState unchanged; fetch V2 summaries/detail separately, refresh only affected views |
| [lib/content.ts](../lib/content.ts) | Assessment catalog scans content/assessments and content/practice | Put new forms/reviews in content/verify, families in content/exercises; no new records in legacy catalogs |
| [lib/labs.ts](../lib/labs.ts), [scripts/verify-lab.mjs](../scripts/verify-lab.mjs) | Legacy keys live under cwd/.local; embedded-key restore trust differs from live import; stdout bypass documented | No reuse for new evidence. Use throwaway keys and a disposable checkout for legacy E2E; DB-path isolation alone does not isolate these keys |
| [vitest.config.ts](../vitest.config.ts) | Includes tests/**/*.test.{ts,mjs}, serial files | New tests/v2 files already fit; no new test framework |
| [playwright.config.ts](../playwright.config.ts), [.github/workflows/validate.yml](../.github/workflows/validate.yml) | Built-server E2E, legacy tests share a DB; existing Node 24 matrix covers three OSes, browser runs Linux only | Preserve V1 suite; use an isolated V2 config and extend this workflow rather than add another pipeline |

**Protected files:** `lib/engine.ts`, `lib/labs.ts`, `lib/assessment.ts`, `lib/reviews.ts`, `scripts/verify-lab.mjs`, `scripts/lab-tests.py`, `corelab/curriculum_graph_v1.json`, existing `content/lessons/`, `content/assessments/` and `content/practice/`. Any later D7 or G-I change to these is separate approved scope.

## 3. Implementation decisions that close dependency gaps

### 3.1 One stage policy, one transaction coordinator

Keep the exact server-start flag `CORELAB_V2=1`; do not introduce user-editable verification switches. A small server-owned release policy in `lib/v2/flag.ts` supports a practice-only S1 release and, after its gates, a C/M-enabled S2 release. This is a build/release constant, not an extra runtime feature-flag system. Test services through injected policy; client parameters cannot enable purposes. I/transfer stay disabled in both releases.

Use `lib/v2/db.ts` to own V2 write transactions and metadata guards. Helpers receive an already-open transaction and never commit independently. A write follows: check supported schema/checksum → check history gate → reserve sequence/revision → validate state transition → write rows → capacity/checkpoint → commit. Any failure rolls back everything.

The legacy `Store.update` hook checks the flag, initialized metadata and supported schema without loading V2 content; it then updates checkpoint/revision/capacity before the existing COMMIT. With off/absent/unsupported V2, it is a no-op for the sidecar. Unsupported metadata never becomes an implicit migration.

### 3.2 Recovery and replay precede learner writes

Migration and all service prototypes are developed against temporary files first. **No S1 learner write is enabled until M06/M07 recovery gates pass.** There is no intermediate release that records attempts while offering only backup/2.

Restore requires the C/M admission/review replay rules even before the S2 UI exists. Implement the **pure policy/replay kernel in M05**, using synthetic reviewed fixture catalogs for tests; M14/M15 later connect that same kernel to live checks. S1 has no live Verify or due-Review issuer. Sources not yet authored/recognized remain inert on restore; a missing feature never causes trust-by-copy.

### 3.3 Planned references and immutable published contracts

The manifest can declare an exact planned form/review ID/version without pretending it has authored items or a hash. This is a resolved, unavailable registry descriptor, not an enabled source. Objective references resolve to these descriptors in S1. Only ready entries with actual files, hashes and review records can issue attempts. M13 authors the planned contracts, and S2 release policy enables them after review.

A planned descriptor is registry metadata, not an issued contract. Once a source can issue an attempt, its bytes/ID/version are immutable. Keep every issued source and recognized policy version, with content-addressed manifest snapshots under `content/v2/manifests/` for reproducible old hashes; update the current manifest additively. Scope changes require new objective versions. Do not publish fake pools merely to satisfy reference validation.

### 3.4 Historical ordering and review concurrency

Persist globally unique positive safe-integer event sequence values for issue, exposure and close. Issue boundary precedes issue exposures; close boundary precedes close feedback. Admission/replay slices the ledger at these exact cuts, excluding only the attempt's own ordinary issue exposures. Do not substitute timestamps, current-ledger state or an in-memory counter.

Freeze review obligation identity/token at issue. Recheck under the close lock; a second close against a changed obligation is `not_admitted/stale_review` and cannot advance stage. Closed assist returns 409. Stored-result replay produces no duplicate exposure, evidence or scheduling.

### 3.5 Backup boundary, legacy entry points and capacity

Keep raw backup JSON as the preview/restore body and bounded confirmation headers; no JSON wrapper. Read actual bytes before parse, reject duplicate decoded object keys, excessive nesting and invalid UTF-8, then validate strict schemas.

Use one canonical export builder and one post-restore capacity projection. Budget original records, encoded escaping/envelope overhead, derived validation/provenance and the added restore epoch. A supported offered export must pass the advertised restore flow; a nominal 128 MiB input cap alone does not prove this. Test the offered-output boundary, not only the transport maximum. If that cannot be achieved within the approved memory/disk budget, **do not release or silently lower the documented promise**; resolve D11 with measured alternatives.

Legacy `Store.restore` refuses the old unpreviewed path only when V2 is enabled and a supported initialized sidecar exists. The V2 coordinator handles /1 and /2 with the same full local snapshot but replaces only legacy state. Flag-off/unsupported-sidecar legacy-view behavior remains available. Existing `/api/export` remains legacy-only; Settings labels it and defaults to /3 when V2 data exists.

A schema-1 S1 binary can reopen an S2-used DB for practice, but cannot enable C/M Verify/Review. It preserves all records and uses M05's common replay rules for recognized sources; unsupported sources remain inert, not deleted. Read models also exclude unrecognized source/policy records from effective eligibility without mutating history. If a rollback-era restore archived a now-recognized record, revalidation uses the same guarded preview/apply path rather than a silent trust upgrade on restart. Stop and disable V2 on a newer sidecar rather than downgrade its tables.

## 4. Approvals, independent reviews and permitted continuation

No approvals below have been inferred or recorded as granted.

| Gate | Owner decision / evidence | Blocks | Work that can continue beforehand |
| --- | --- | --- | --- |
| G0 Scope | D1 approves S1/S2 capacity trade-off and implementation scope | Implementation authorization; later live activation | This plan only; future development starts when requested |
| G1 Recovery policy | D11 approves 128 MiB logical/transport policy, five snapshots/512 MiB total and current recovery procedure, supported machine budget | Enabling persistent writes outside throwaway fixtures | Authorized code, synthetic tests, measurements |
| G2 Content | D5 names independent technical/adversarial and teaching reviewers; each released item passes Bank gates 1–7 | Release of affected auto-checked items/kits | Authoring, mutation tests, UI with fixtures |
| G3 Platforms | D6 names OS/browser scope and records actual Node 24+ results | Unsupported platform claims and learner recruitment on those platforms | Portable implementation and Linux tests; no simulated OS claim |
| G4 S1 release | M12 evidence plus G1/G2/G3 and owner activation decision | S1 learner use | S2 work in fixtures if authorized |
| G5 S2 release | M16 evidence, independent C/M/pool review and owner activation decision | Live verification/retention and S3 | Practice stays usable |
| G6 Pilot | Opt-in participant plan, privacy/accessibility arrangements and stop criteria, owner agreement | Recruitment and collection/sharing of pilot observations | Local rehearsal with synthetic data |
| G-I Future | D2/D4, independent security review, allowlisted OS isolation, legacy bypass fix/version and new migration/admission policy | **All new admitted I** | Nothing in this pilot requires it |

D3/D8/D9/D10 retain the spec's safe defaults: separate objective evidence, unchanged graph, documented legacy trust, no weaker verification tier. **D7 M08 routing/precision fix stays a separate optional task**, with its own authorization, versioned content and history tests; it is not slipped into this sequence. Review appointments, participant outreach, publication and commits require their own authorization when applicable; this plan sends no messages.

Bank release gates: rights/self-contained contract; independent correctness; valid alternatives and second-person false-accept/false-reject attempts; named invalid/mistaken cases; reproducibility; execution safety (not applicable as a runner claim for typed answers/manual kits); teaching/accessibility. Codex cannot replace the independent reviewer with its own second pass.

## 5. Milestone order and release boundaries

M00–M18 are **milestone labels in this plan**, distinct from mathematics topic IDs such as M01. Each milestone below has an independently testable exit. Split its checkbox tasks into small reviewable patches; do not accumulate multiple storage/restore changes without running the relevant tests.

| Milestone | Stage | Depends on | Observable deliverable |
| --- | --- | --- | --- |
| M00 | S0 | — | Baseline fixtures, protected-file inventory and pending approvals |
| M01 | S1 foundation | M00 | Pure schemas, canonical bytes, bounded answer and request parsing |
| M02 | S1 content | M01 | Six objective descriptors, bridge and four distinct practice routes |
| M03 | S1 foundation | M01 | Transactional additive migration and safe legacy-view guard |
| M04 | S1 recovery | M03 | Deterministic backup codec and structural staging validation |
| M05 | S1 recovery | M01, M04 | Shared policy/review replay and safe restored projections |
| M06 | S1 recovery | M05 | Atomic restore, snapshots, capacity and legacy checkpoint integration |
| M07 | S1 recovery UI/API | M02, M06 | Local bounded backup routes and usable Settings recovery |
| M08 | S1 practice | M02, M07 | Durable attempts, exposure, hints, submission and practice APIs |
| M09 | S1 practice | M08 | Bounded history, objective summaries and deterministic selection |
| M10 | S1 learning UI | M09 | Objective routing, accessible practice UI and optional activities |
| M11 | S1 apply | M08, M10 | Two reviewed manual self-check kits and exposure-aware downloads |
| M12 | S1 release gate | M10, M11 | Data-safety, compatibility, UI and platform release evidence |
| M13 | S2 content | M12 | Reviewed C/M form variants and fresh retrieval pools |
| M14 | S2 verification | M05, M08, M13 | Live scoped C/M admission and Verify UI |
| M15 | S2 retention | M14 | Due review issuing, scheduling and retention UI |
| M16 | S2 release gate | M15 | Integrated S2 qualification and rollback rehearsal |
| M17 | S3 preparation | M16 | Approved participant/rehearsal protocol |
| M18 | S3 observation | M17, G6 | 21+ day pilot report and continue/change/stop decision |

M02 authoring and M03–M06 storage work can proceed separately after M01; this is a dependency allowance, not permission to spawn agents or share a live DB. The critical path is M03 → M04 → M05 → M06 → M07 → M08. Do not bypass it to make the UI look finished.

## 6. Detailed execution checklists

### M00 — Freeze the baseline and fixtures

**Files:** new `tests/v2/helpers.ts` and `tests/v2/fixtures/`; execution notes in this plan when implementation starts. No production edits.

- [ ] Inventory current HEAD/worktree, protected content hashes, scripts and test counts; preserve unrelated edits. Capture the spec hash and approvals as pending/granted with date and scope.
- [ ] Build synthetic legacy history: A0/A3 diagnostics, targeted work, notes, goals, reviews and throwaway signed M02/PY01 reports. Save expected legacy mastery and exact report strings/signatures.
- [ ] Add temporary-database helpers with cleanup, deterministic clock/IDs, safe temp paths including spaces/Unicode, fixed-code worker processes/barriers for actual concurrent-writer tests, and failure injection; never use getStore()'s default DB.
- [ ] Retain an isolated baseline source fixture/checkout for compatibility tests. Run the real baseline Store against a copied V2-used **test** DB later; a new Store renamed “v1” is not a compatibility test.
- [ ] Establish a disposable source checkout/copy for full legacy E2E because the signing CLI uses cwd/.local independently of CORELAB_DB_PATH. Include authorized current changes/new files; exclude .local, .git, databases, keys, .next and node_modules, and install from the lockfile there. A clean worktree at HEAD alone would omit uncommitted implementation work.

**Acceptance/tests:** fixture reopen and throwaway signature checks; record baseline unit/content/check results when run. The prior audit's 119 tests are historical, not this milestone's result. **Rollback:** remove only the new fixture/helper work; no learner data touched.

### M01 — Pure contracts, canonicalization and bounded parsing

**Files:** new `lib/v2/{flag,schemas,answers,fingerprint,http}.ts`; `tests/v2/{contracts,answers,http}.test.ts`. Edit `lib/http.ts` only for an optional maxBytes argument preserving the current default.

- [ ] Define discriminated schemas for objectives, manifest descriptors, ready sources, attempt states/purposes, assistance, evidence original/projection, epochs, reviews, prefs, snapshots and /3 rows. Specify field/collection limits, UTC time and safe-integer rules.
- [ ] Add the exact server-start flag and server-owned S1/S2 release policy. Keep this module free of content reads, DB creation and browser environment fallbacks.
- [ ] Implement JCS UTF-8 bytes with RFC 8785 conformance vectors; UTF-16 key ordering, number/string edge cases and invalid Unicode must be covered. Use one small pinned reviewed implementation if conformance cannot be demonstrated with built-ins; no broad serialization framework.
- [ ] Implement domain-separated fingerprints and normalized decimal input strings; canonical numeric submissions are reduced rational integer strings, including normalized zero. Bound BigInt operands before arithmetic; never eval expressions.
- [ ] Implement streamed UTF-8 byte limiting, duplicate-key detection before ordinary JSON.parse, strict schemas, nesting/token bounds and bounded control headers. Escaped-equivalent keys must count as duplicates within the same object, not across unrelated objects.
- [ ] Centralize V2 error codes/statuses: flag off 404, schema 400, stale/closed/exhausted-state conflict 409, size 413, unsupported/maintenance 503; unavailable activities have an explicit unavailable response and issue no attempt.

**Acceptance/tests:** AC-F2, AC-A9 foundation, VS-10 format boundary. Test fraction equivalence, zero denominator, huge operands, bool/null/NaN/Infinity/exponents/decimal comma, incorrect shape, duplicate/escaped keys, hostile Host/origin, missing/false Content-Length, multibyte overflow and cancellation. Default helper callers still reject declared bodies >8,000,000. **Rollback:** revert optional helper change and new pure modules; no data.

### M02 — Original S1 content and typed registry

**Files:** new `lib/v2/content.ts`; `content/v2/{objectives.v1,paths.v1,exposure-relations.v1,manifest.v1}.json`; `content/v2/manifests/`; `content/v2/bridges/radians-trig.v1.md`; `content/exercises/{XB1,X10,X11}.v1.json`; `scripts/validate-v2.ts`; `tests/v2/content.test.ts`. Extend `scripts/validate-content.ts` only behind the flag.

- [ ] Author the six exact objectives in Spec §14.2; M01.radians-trig is practice-only. Define exclusions, advisory readiness and route-specific inspection readiness without changing the topic DAG.
- [ ] Author XB1's 12 instances and X10/X11's four pools of eight [initial spec estimates, review before release]. Each route is an authored scenario/task choice, not a renamed numeric variant. State differences and accept mathematically valid alternative methods.
- [ ] For each instance record structure, bounded inputs, units, precision, expected output type, correct answer/rubric, critical parts, misconceptions, A1/A2/A3 help, feedback and rights/review metadata.
- [ ] Register planned forms/reviews and kits as unavailable until their actual sources are ready. Validate each declared ID/version and every enabled file/hash; no empty placeholder source can be issued.
- [ ] Resolve actual lesson anchors/media IDs; frames is an illustration, forward-kinematics a visualization with links 2 and 1.5. Label differing task parameters and keep the visual out of the oracle.
- [ ] Check objective readiness acyclicity, typed refs, fingerprint disjointness, reviewed exposure relations and historical manifest/source retention. No X01/X04/Jacobian/SE(3) expansion.

**Acceptance/tests:** VS-01/02/03, AC-C2 foundation. Every ready pool item has independent hand/alternative results and named mistakes; rights and independent review remain G2. Plain numeric/text study works offline without video. **Rollback:** withdraw unissued sources; once issued, retain their bytes/version and disable availability rather than overwrite them.

### M03 — Sidecar migration and transaction skeleton

**Files:** new `lib/v2/{db,migrations,checkpoint}.ts`; `tests/v2/{migrations,compatibility}.test.ts`. No first learner write or UI activation.

- [ ] Implement schema inspection with migration input 0 and supported read/write 1. Inspect sqlite_schema before absent-table reads; partial tables, unknown metadata/checksums/versions fail closed.
- [ ] Create all ten sidecar tables/indexes and the pilot evidence admission guard, with foreign keys enabled. Preserve user_version=2 and exact legacy state/report content.
- [ ] Under BEGIN IMMEDIATE reserve the writer; use a separate read-only connection and bound VACUUM INTO destination to make the pre-migration copy. Validate/reopen the completed copy before DDL. Use private paths and safe UTC/UUID names. Test native directory/permission behavior per OS; Unix mode bits do not establish Windows ACL protection.
- [ ] Apply DDL/checksum/meta atomically; recheck schema/checksum on every V2 write. Unknown/newer state allows compatible legacy view but no sidecar writes/checkpoint hook.
- [ ] Define transaction-scoped sequence allocation, data_revision increments, current epoch initialization and guard results. Detect overflow and refuse writes; never reset counters silently.

**Acceptance/tests:** AC-M1/M2/M3/M5/M6; schema/supported-range tests; real file/WAL two-connection tests, failure at copy/DDL/meta/commit, competing writers, disk/permission errors and baseline reopen on copied fixtures. In-memory tests cannot stand in for WAL-copy tests. **Rollback:** leave the additive schema and disable V2; no automatic DROP/down migration. Recover a pre-copy only before any later learner edits, or after an explicit full-state recovery decision.

### M04 — Consistent backup codec and staging validator

**Files:** new `lib/v2/backup.ts`; `tests/v2/backup-codec.test.ts`; extend schemas/helpers. All operations target test stores until the activation gates.

- [ ] Define deterministic row ordering/counts and strict /3 export schema; retain exact original strings, signed reports and source identity. Exclude issuers, private keys, installation metadata, snapshots and external artifacts.
- [ ] Read legacy state and learning tables in one SQLite read transaction. Canonicalize/hash all envelope fields except contentHash; create a complete bounded private spool/output before returning any headers.
- [ ] Validate input body and hash/counts/IDs first, then stage records in a known temporary schema. Reject dangling raw record refs, duplicates, invalid sequence/status chronology and impossible cross-record relations.
- [ ] Accept only sidecar schema 1; retain unknown content/policy as bounded inert history, not as missing history rows or executable content. /1 and /2 still use validateBackup's unchanged legacy rules.
- [ ] Add safe record counts and aggregate byte accounting, not only the 100,000-attempt ceiling. No forged cached grade/trust/validation field can bypass subsequent M05 replay.

**Acceptance/tests:** AC-B1/B4/B6/B10 structural portion, VS-13/14 foundation. Deterministic non-ASCII round-trip; consistent export with concurrent legacy/V2 fixture writes; missing rows; wrong hashes; over-limit refusal before a file/headers; interrupted private spool cleanup. **Rollback:** remove unpublished codec use; no active DB replacement exists yet.

### M05 — Shared admission and review replay kernel

**Files:** new `lib/v2/{admission,reviews}.ts`; extend `lib/v2/backup.ts`; `tests/v2/{admission,restore-policy,review-replay}.test.ts`. Pure functions and staging only.

- [ ] Implement source/variant/coverage validation and bounded grading against injected immutable known sources. Never trust a substituted instance carrying a correct source ID/hash.
- [ ] Implement per-objective-dimension admission: known policy/form, Verify purpose, A0, fresh issue/close cuts, own ≥80% subset and all own critical items. Keep original claim separate from derived outcome/provenance/validation.
- [ ] Implement deterministic replay by event sequence, including help before close versus feedback/later help after close. Recompute assistance and fingerprint relations; validate sequence allocation, not client event-order assertions.
- [ ] Implement pure review transitions/token validation/delay basis so restored stage/due caches cannot authorize retention. Ineligible bases suspend reviews; missing source/policy/time support stays inert.
- [ ] Preserve inert I/transfer artifacts and their raw references while blocking admission; do not enroll imported issuers or treat an equal workspace label as proof. Preserve local identity/trust on foreign restore.
- [ ] Version the kernel/policy and inject catalogs/clock into tests. A restore uses the same kernel as future live close, not a second “lenient backup” grader.

**Acceptance/tests:** AC-E5/E6/E8, AC-I1, AC-A10 historical replay. Include 1/2 objective inside an overall passing form, independent passing scopes, declared/observed help, source substitution, post-close feedback, tied timestamps, original/derived grade mismatch, unknown versions, suspended reviews and foreign-key reports. Execute the published guard cases as regression seeds, plus service-level tests; 23 prior research cases are not a complete implementation suite. **Rollback:** disable the new projection path; preserve raw records. Never “repair” old claims by overwriting their signed/original bytes.

### M06 — Atomic replacement, full snapshots and capacity hooks

**Files:** extend `lib/v2/{backup,db,checkpoint}.ts`; new `scripts/v2-recovery.ts`; carefully edit `lib/storage.ts`; `tests/v2/{restore,capacity,legacy-hook}.test.ts`.

- [ ] Preview returns digest and target revision/hash/snapshot-count token. Confirm validates the same document and rechecks the target under BEGIN IMMEDIATE; stale token means 409 with no replacement.
- [ ] Take a full nonrecursive local pre-restore snapshot in the same transaction. Delete child learning rows before parents; insert epochs → attempts → exposures → evidence → reviews/prefs; replace legacy state; keep installation identity, issuer pins and migration registry.
- [ ] Add a new local epoch, recompute next sequence above retained maximum, update checkpoint and monotonically increment local revision; never import local authority/counter metadata as truth.
- [ ] Implement /1 and /2 partial replacement with the same full snapshot, retained V2 history and explicit epoch. Guard old Store.restore when active supported V2 would otherwise bypass this flow.
- [ ] Implement snapshot listing/recovery with the same preview/confirmation rules, max five and 512 MiB total. Validate disk headroom; pruning and replacement roll back together.
- [ ] Implement approved capacity accounting before every persistent write, including enabled legacy Store.update. Warn at 80%; refuse new over-budget data without deleting history. A cached total must be keyed to schema/revision and invalidated on outside writes; fall back to verified recount.
- [ ] Add the synchronous pre-commit checkpoint/revision/capacity hook, exactly once per transaction; restore coordinator never nests Store.update. Off/absent/unsupported sidecar does not modify V2.
- [ ] Add a local owner-operated recovery-copy command, fixed to the configured DB and application-chosen private destination. Test stop/copy/validate/reopen for already oversized or unsupported profiles. No raw DB web download or arbitrary path parameter.

**Acceptance/tests:** AC-B2/B3/B5/B7/B9/B10, AC-M4/M6, AC-F3. Inject failure after each deletion/insertion/snapshot/prune/hook step; compare complete state/meta/snapshots before/after. Test edit-then-legacy-restore detection with baseline Store, stale preview, fresh-install identity, copy correctness under WAL, near-limit derived overhead and recovery from oversized state. **Rollback:** disable V2 for legacy view; preserve sidecar and take a current copy. Never replace a live DB with a stale pre-migration copy to undo application code.

### M07 — Local recovery API and Settings

**Files:** new `app/api/v2/backup/export/route.ts`, `backup/preview/route.ts`, `backup/restore/route.ts`, `backup/snapshots/route.ts`, `backup/snapshots/[id]/{preview,restore}/route.ts` beneath `app/api/v2/`; new `components/v2/backup-panel.tsx`, `lib/v2/client.ts` and `playwright.v2.config.ts`; edit `components/tools.tsx`, `components/workspace.tsx`, `app/[[...slug]]/page.tsx` and `playwright.config.ts`; `tests/v2/backup-http.test.ts`, `e2e/v2-backup.spec.ts`.

- [ ] Pass a server-derived enabled/stage prop from Page through Workspace to Settings without loading V2 content when off; M10 extends this same plumbing to other panels.
- [ ] Create the isolated V2 Playwright config before adding the first V2 browser test: match only v2-*.spec.ts, override inherited testIgnore, set CORELAB_V2=1 only for its temporary server, and keep one worker. Add testIgnore for v2-*.spec.ts to the legacy config so the existing suite cannot accidentally run them with the flag off.
- [ ] Wrap recovery services with exact flag/locality/type/status checks. Routes run in the Node runtime, force dynamic/no-store and never leak absolute paths or keys.
- [ ] Enforce 128 MiB actual streamed bytes only on dedicated backup routes, retaining the legacy helper default; use the bounded confirmation headers for restore.
- [ ] Limit heavy preview/export/restore jobs to one active operation per server; return a retriable busy response, not an unbounded queue of 128 MiB parses. Measure peak memory/disk on approved machines.
- [ ] Make Settings offer full export by default, labelled legacy-only export, file-size guidance, validation summary/provenance/inert counts and explicit replacement confirmation. Resend the original File/raw bytes, not an edited preview or enlarged JSON wrapper.
- [ ] Show snapshot recovery and maintenance/current-copy instructions, mixed-history acknowledgement state and stale-preview retry. Clearing/reselecting a file clears confirmation; accessible progress/errors do not trap focus.
- [ ] Preserve the entire legacy Settings path when off; the old action restore returns useful V2-route guidance when guarded, not a partial replacement.

**Acceptance/tests:** AC-B6/B8/B9, AC-F1, VS-14/15. HTTP test >8 MB valid backup with real and absent Content-Length, multibyte overflow, aborted upload, stale confirmation, no early download, blocked Host/origin on every route, keyboard file/confirm/recovery flow. Rehearse this path end to end before M08 enables durable attempts. **Rollback:** disable V2, keep all recovery files/snapshots and restore access through the approved local maintenance procedure; revert UI only without erasing data.

### M08 — Durable practice attempts and exposure API

**Files:** new `lib/v2/attempts.ts`; extend db/admission/answers; new `app/api/v2/attempts/route.ts`, `attempts/[id]/route.ts`, `attempts/[id]/{assist,submit}/route.ts` and `reports/import/route.ts`; `tests/v2/{attempts,attempt-http,exposure}.test.ts`.

- [ ] Issue only ready family sources for practice/placement; atomically freeze source/version/hash/policy/route/instance/options, allocate issue boundary and exposures before responding. S1 rejects Verify/Review/transfer as unavailable.
- [ ] Resume the exact server-owned attempt by ID; abandoned attempts and all exposures remain durable. Redact answers, rubrics and oracle data on issue/detail; no static file route serves source answer keys.
- [ ] Assist maps requested level to authored content, commits exposure and max observed level before responding. Submitted attempts reject assist with 409.
- [ ] Validate bounded answers and declared A0–A3 before close. Format/infrastructure failure leaves issued status, no grade/weakness. Valid practice closes once with server grade; open answers remain unverified.
- [ ] Hash normalized answers plus declaration; identical retry returns stored result, different retry 409, concurrent requests close once. Allocate close before feedback exposure; feedback does not rewrite the closed observed level.
- [ ] Keep practice out of v2_evidence and all legacy arrays. Report import always returns unavailable; it follows no paths/URLs and executes nothing.

**Acceptance/tests:** AC-A1/A2/A3/A4/A5/A6/A9/A10 practice portions, AC-I1/I3, VS-04/05/10. Enumerate/replay deterministic assistance-request sequences without adding a property-test library; restart and two-connection concurrency tests; malicious trusted fields; same math across routes; controlled transaction failure; unchanged legacy mastery. **Rollback:** stop new issues with V2 off; retain and later resume/replay existing versioned attempts, not reset/delete them.

### M09 — Objective read model, history and selector

**Files:** new `lib/v2/{select,read-model}.ts`; extend content/db; new `app/api/v2/objectives/route.ts`, `objectives/[id]/route.ts`, `history/route.ts`, `history/acknowledge/route.ts`, `preferences/route.ts`, `select/route.ts`; `tests/v2/{selector,history,read-model}.test.ts`.

- [ ] Expose per-activity availability and objective-only summaries; I/transfer remain unavailable. Legacy levels/recommendations remain separately labelled and read-only.
- [ ] Implement Recommended, Explore and More Practice with the exact priority/tie-break from Spec §12.1. Support learner override, optional goals, route alternatives, labelled repeats and explicit pool exhaustion.
- [ ] Map legacy weaknesses only through reviewed static relations, with reason labels. Do not infer prerequisite failure from an unrelated old mistake or mark legacy debt corrected.
- [ ] Use keyset history pagination (max 50), selector max 10 and small summaries instead of full artifact history. Bind pagination cursor to its filter and stable ordering.
- [ ] Implement narrowly scoped checkpoint acknowledgement under lock and allowlisted preferences with capacity/revision checks. Repeated acknowledgement cannot invent more epochs; stale tokens return 409.
- [ ] Use bounded indexed queries, explain plans and representative permitted-volume seeds; don't add caches or DB indexes unless measured queries justify them.

**Acceptance/tests:** AC-P1/P2, AC-M4, AC-F3, VS-02. Deterministic ordering/ties, no duplicate/lost cursor items, exhaustion, off 404, malformed filters/cursors, malicious preference fields, source unavailable and legacy-state immutability. Measure selector at 50,000 compact permitted attempts; target <200 ms and <64 KiB, recording hardware/volume. **Rollback:** disable V2 read/UI entry points; preserve records and known source registry.

### M10 — Accessible objective routing and practice UX

**Files:** new `components/v2/{objective-panel,objective-page,attempt,matrix-input,practice-modes}.tsx`; reuse M07’s `lib/v2/client.ts`; edit `app/[[...slug]]/page.tsx`, `components/{workspace,topic,dashboard,tools,weakness-practice,shell}.tsx` and scoped `app/globals.css` additions; `e2e/v2-practice.spec.ts`.

- [ ] Extend M07’s server-derived enablement/capability prop across existing page dispatch to gated panels; no new mandatory V2 fields in AppState or legacy Progress.
- [ ] Implement /objectives/:id in both route validation and Workspace dispatch; validate the dotted objective ID against the registry, with at most the supported segments. Off returns not-found with no V2 catalog read.
- [ ] Add objective summaries to existing topic/dashboard views and V2 practice tabs beside existing My Weaknesses. Keep legacy recommendation/assessment controls intact.
- [ ] Let a new learner choose either X10/X11 route, skip readiness/bridge, open Learn or Practice directly and resume after reload. Show I unavailable and form/review not released without disabled learning navigation.
- [ ] Build labelled coordinate/matrix fields with units/precision before input, keyboard order, per-cell errors and a readable table alternative; use text/icons alongside color. Preserve readable font sizes and visible focus.
- [ ] Add contextual help warnings, assisted status and clear practice-versus-verified labels. The manual tutor handoff carries only redacted context; external AI help is declared, never imported as evidence.
- [ ] Refresh only changed V2 summaries/details after save and legacy state after actual legacy writes; cancel stale fetches, handle loading/errors/exhaustion and escape restored text.

**Acceptance/tests:** VS-01/02/03/05/15. Reload/resume, invalid/deep routes, no compulsory prerequisites, both scenario choices, placement/advisory-only, skip bridge, offline numeric flow, keyboard completion, visible errors and 390 px plus 320 px/200% zoom reflow. A human screen-reader check is required; automated DOM assertions alone do not certify accessibility. **Rollback:** off hides V2 panels/routes; no data rewrite and existing UI stays usable.

### M11 — Manual self-check kits with honest limits

**Files:** new `content/labs/{L01.SE2,L02.planar}.v1.json` and `content/labs/kits/{L01-SE2,L02-planar}/` original instructions/starter/tests; new `app/api/v2/kits/[id]/{download,self-report}/route.ts`; extend attempts and objective UI; `tests/v2/kits.test.ts` and `e2e/v2-kits.spec.ts`.

- [ ] Author the exact bounded Python-standard-library interfaces from Spec §14.5, valid alternatives, invalid-input behavior and nonmutation. Include output-shape/type/finiteness validation before comparison on every case.
- [ ] Independently check SE(2) anchors, compose order, inverse/direction, reflection/shear; FK unequal/nonzero/wrapped/edge poses and orientation modulo 2π. Appendix A is a research seed, not a complete kit grader.
- [ ] Cover declared primitive bounds, overflow/tolerance edges, bool/nonfinite/malformed/extra-output cases, zero/negative lengths and alternative trig/chain implementations. Align all displayed function names with the actual starter.
- [ ] Give safe Python 3 instructions for Windows py -3/python, macOS/Linux python3/python; no compiler/ROS install. Manual tests run only when the learner chooses outside CoreLab; they do not protect the host.
- [ ] Download uses a server-created practice attempt and records kit/sample/solution-relation exposures before returning bytes. Retry by attempt reference is idempotent. No untracked static/public kit link bypasses exposure.
- [ ] Self-report closes that practice attempt with “I ran it,” no trusted verdict/report/signature/evidence; repeated self-report is idempotent and cannot raise any mastery claim.

**Acceptance/tests:** AC-I2, VS-06/07/08/09/10 and AC-C1/G2. Run only the reviewed kit tests against trusted test fixtures in a disposable directory; malicious learner-code sandbox tests belong to G-I, not host execution. Publish OS commands as tested or untested. **Rollback:** disable kit availability/download; retain earlier manifests and exposure. Never relabel old self-reports as verified.

### M12 — S1 qualification and owner release gate

**Files:** extend M07’s `playwright.v2.config.ts`; new `scripts/check-v2.mjs`; extend `package.json`, existing `.github/workflows/validate.yml` only as needed; `tests/v2/release.test.ts`; update `README.md`/`docs/guide.md` after behavior exists.

- [ ] Run baseline check suite with V2 off and assert no V2 table creation/content reads/routes/UI. Keep baseline tests including legacy signed history and targeted practice semantics.
- [ ] Run S1 unit/integration/HTTP/browser checks with temporary DBs; test on→off→baseline edit/restore→on, unsupported sidecar and over-budget maintenance/current-copy recovery.
- [ ] Rehearse full export/foreign restore/snapshot recovery with exact report strings, attempts/exposure order and no issuer enrollment. Exercise real >8 MB transport, actual boundary budgets and interrupted restore.
- [ ] Run build/start, localhost security, native SQLite paths/locks/copies on each D6 OS; existing Node 24 CI is the starting point, not proof of any V2 result. Add a separate isolated V2 browser config without running legacy cases against the wrong release mode.
- [ ] Record peak RSS/disk/latency at permitted profile volume; approve D11 or block the release. No automatic history pruning or private upload to get tests passing.
- [ ] Document actual S1 availability, data/backup scope, legacy verifier/trust limits, unsupported OS results and rollback. Collect independent item/accessibility reviews and owner activation decision.

**Acceptance/tests:** all S1 IDs assigned in §9; G1/G2/G3/G4 satisfied. **Rollback:** turn off V2, stop writes, make a current recovery copy and keep sidecar/source versions. Never silently lose S1 records by reverting to legacy-only export as a “full” backup. No S2 verification is enabled by completing this gate.

### M13 — Author the C/M forms and retrieval pools

**Files:** new `content/verify/{F-FRAMES,F-R04,RV-FRAMES,RV-R04}.v1.json`; update current manifest/readiness availability; `tests/v2/forms.test.ts`. Existing lessons and legacy assessments unchanged.

- [ ] Author immutable F-FRAMES@1 and F-R04@1 bundles, each with static A/B variants, stable choice IDs and disjoint fingerprints. Preserve original scenario/model conventions.
- [ ] Give Frames its seven objective-dimension subsets: 8 C and 6 M items total per variant; FK 5 C and 5 M. Specify own critical items and ≥80% thresholds; 2-item scopes need 2/2, FK needs 4/5 and both critical items.
- [ ] Author four fresh review items per each of nine assessed objective-dimensions: 28 Frames + 8 FK items initially. Verify every pool is disjoint from practice/forms and its own “fresh” alternatives; retrieval variants do not claim transfer.
- [ ] Ensure M01 bridge remains practice-only and numeric M claims bounded procedure, not a written proof. Open prose is stored unverified and is not an auto-admitted criterion.
- [ ] Apply rights, independent correctness, valid alternatives, false-accept/false-reject and pedagogical/accessibility review to every item before marking ready. Preserve original manifest snapshots.

**Acceptance/tests:** AC-C1/C2, VS-01/10. Deterministic hand anchors, expected scope counts/critical coverage, no key-by-fixed-position defect, precision before answers, proper fraction/tolerance handling and no leaked fingerprint reuse. **Rollback:** do not publish until reviewed; after issue, withdraw availability/version forward without changing original content.

### M14 — Live scoped C/M Verification and UI

**Files:** extend `lib/v2/{attempts,admission,flag}.ts`, existing V2 attempt routes and `components/v2/{attempt,objective-panel}.tsx`; `tests/v2/verify.test.ts`; `e2e/v2-verify.spec.ts`.

- [ ] Add S2-only Verify issuing from ready forms, with frozen variant/item/option order, hashes, policy and provisional freshness. No eligible form means no issue and an explicit practice option.
- [ ] At valid submit, under one write lock revalidate exposure at issue/close, own assistance, source/coverage and policy; close → append per-scope evidence/original claim/projection → update review obligations → capacity/revision → commit.
- [ ] Reuse M05 kernel; database guard rejects null/practice/unclosed/assisted/source-mismatched admission and all admitted I/transfer. SQL guard alone is not a full coverage/freshness validator.
- [ ] Enforce cross-tab help/solution relations, warning-before-help and both transaction orders; feedback after close cannot revoke earlier admission. Failed/assisted checks remain visible with reasons, not hidden failures.
- [ ] Display independent C/M scope results and exclusions; a globally high score cannot pass a failed objective or veto a passing one. Later failure raises remediation without deleting an earlier attainment.
- [ ] Build an **unreleased S2 candidate** whose server release constant enables C/M, with CORELAB_V2 still default-off. Exercise it only against disposable test profiles until M16/G5. Retain the S1 release artifact/commit with practice-only policy for rollback; no client or extra runtime switch can activate S2.

**Acceptance/tests:** VS-11, AC-A7/A8/A9/A10, AC-E1/E2/E3/E4/E7. Test every admission predicate independently, concurrent duplicate/different resubmits, 1/2 versus global pass, arbitrary client grade/coverage, restored sources and unchanged legacy mastery. **Rollback:** disable Verify by release rollback/V2 off; retain evidence and frozen forms, never downgrade/delete old claims to make the UI simpler.

### M15 — Due reviews, retention and remediation

**Files:** extend `lib/v2/{reviews,attempts,select}.ts`, objective routes and `components/v2/{objective-panel,attempt,practice-modes}.tsx`; `tests/v2/reviews.test.ts`; `e2e/v2-review.spec.ts`.

- [ ] Issue one unexposed item per due objective-dimension from its known review pool. Freeze basis evidence/row token/due/stage; “Review now” before due issues practice.
- [ ] Recheck obligation token, freshness, A0, mandatory correctness and current basis on close. Two pending reviews cannot advance the same obligation twice.
- [ ] Reuse 1/3/7/21 relative scheduling: initial due +1 day, then +3/+7/+21 from correct reviews, stage capped at 3. Assisted correct keeps stage, due +1; wrong resets stage 0, due +1.
- [ ] Retention evidence needs ≥7 days since the matching admitted basis and due A0 success. Earlier due successes may advance stage without retention. Partial outcomes affect only their own scopes.
- [ ] Four fresh checks exhaust a pool; preserve the due obligation and offer explicitly repeated practice. No new-number claim of unfamiliar transfer; no fresh-label reset after restore.
- [ ] Surface specific gaps, a smaller example, bridge or alternate route as optional remediation. Merge legacy/objective review lists with distinct labels, without editing legacy schedules.

**Acceptance/tests:** VS-12, AC-E3/E4/E8 and AC-A10 review portion. Fake-clock reducer tests and integration with exact issue/close cuts; early/assisted/wrong/partial/exhausted checks, delayed/future/clock-regression times, suspended bases, competing closes and full restore replay with stage/due equivalence. **Rollback:** disable new review issuance, preserve rows/bases/history and show labelled suspended/unavailable state. Legacy reviews continue untouched.

### M16 — S2 integration, restore and release qualification

**Files:** extend V2 integration/release/E2E tests, `scripts/check-v2.mjs`, existing workflow and docs only as required.

- [ ] Run the complete workflow from fresh and populated legacy fixtures: optional placement → learn/choose route → assisted practice → fresh scoped Verify → due review → gap remediation → full backup → foreign restore → resume.
- [ ] Run all S1 regressions again with C/M records, including raw claim/signature preservation, event cuts, suspended reviews, snapshot recovery, stale previews and capacity after derived projections.
- [ ] Rehearse rollback from S2 to S1 code/release policy and to baseline legacy view on copied DBs; return to S2 without erased history, false fresh items or duplicate passes.
- [ ] Recheck no I/transfer admission through any endpoint, inert restore, SQL guard or UI. No new keys, execution broker, active report importer or proctoring claim exists.
- [ ] Measure query/payload and memory/disk budgets with real-shaped C/M histories on named supported machines; publish OS/browser gaps. Repeat keyboard/reflow/screen-reader checks.
- [ ] Record independent form/pool reviews and owner S2 activation decision. Keep correct/assisted/failed evidence limitations visible in docs.

**Acceptance/tests:** all S2 IDs in §9; G5 satisfied. No release if a critical data-integrity/security predicate fails. **Rollback:** disable verification/review issuance or V2 entirely; preserve all original records, migration metadata and immutable source versions; recover data only through previewed full recovery.

### M17 — Prepare the learner pilot

**Files:** new `implementation-plan/pilot-protocol.md` only when S3 is authorized; local synthetic rehearsal artifacts outside Git.

- [ ] Select 3–8 consenting volunteers [spec estimate], D6 platforms and an owner-approved accessible study protocol. No outreach is authorized by writing this plan.
- [ ] Explain practice versus evidence, self-declared assistance, I unavailable and inspectable local content. Give backup/current recovery and stop instructions.
- [ ] Predeclare active study time, assistance, false failures, route choice, confusing labels, accessibility and day-7/day-21 observation tasks. Keep these observations separate from due-review admission.
- [ ] Rehearse onboarding, both routes, optional bridge, offline fallback and support recovery with synthetic data. Check that fresh pools suffice for the protocol; version more reviewed items or reduce observations before recruitment.
- [ ] Agree minimal opt-in notes, who sees them and retention/deletion arrangements. No analytics service, automatic telemetry, raw progress uploads or synchronized learner DB is introduced.

**Acceptance/tests:** G6 and a complete local rehearsal; both positive and exhausted/failed paths covered. **Rollback:** postpone recruitment and correct the protocol; no fabricated participant data or elapsed study time.

### M18 — Run, review and decide after 21+ days

**Files:** new `implementation-plan/pilot-report.md` after actual observations; deidentified aggregate/case notes only with participant permission.

- [ ] Run the approved protocol over at least 21 days; record actual attendance, task versions, help and missing observations honestly.
- [ ] Stop affected use on data loss, unsafe behavior, false evidence admission or serious accessibility failure; retain current recovery copies and original source versions.
- [ ] Investigate false failures with reproducible minimal cases; any key/threshold/content correction is versioned, not a rewrite of old attempts.
- [ ] Report case evidence, limitations, exhaustion and unresolved defects. Do not claim an effect size or measured learning improvement from the small sample.
- [ ] Obtain an owner decision: continue, change scope or stop. X04/X01, broader graph adoption and G-I remain separate later proposals.

**Acceptance:** actual elapsed pilot and reviewed report; unobserved outcomes marked missing. **Rollback:** pause new checks, retain each learner's data and provide local export/recovery; no central data collection is required.

## 7. API and file ownership checklist

All paths in this table are **planned**, not existing endpoints. Under `app/api/v2/`, each route file is a thin adapter to a tested service, with flag → localhost/origin → bounded schema → guarded service → redacted/no-store response. Detail IDs are validated data, never paths.

| Route suffix / methods | Owner milestone | Service |
| --- | --- | --- |
| backup/export GET; backup/preview POST; backup/restore POST | M07 | backup |
| backup/snapshots GET; backup/snapshots/[id]/preview POST; backup/snapshots/[id]/restore POST | M07 | backup |
| attempts POST; attempts/[id] GET; attempts/[id]/assist POST; attempts/[id]/submit POST | M08; Verify M14, Review M15 | attempts/admission/reviews |
| reports/import POST | M08 | Always unavailable in pilot |
| objectives GET; objectives/[id] GET | M09 | content/read summaries |
| history GET; history/acknowledge POST; preferences PATCH; select GET | M09 | db/checkpoint/select |
| kits/[id]/download POST; kits/[id]/self-report POST | M11 | attempts/content |

Do not create a second HTTP execution service. A plain `lib/v2/client.ts` helper is enough for typed fetch/error handling; use existing React state and loading patterns, not another application-wide state framework. M07 introduces that one helper; later panels reuse it.

## 8. Tests, commands and data protection

### 8.1 Future command contract

Existing commands, to run in the authorized implementation/test checkout:

```sh
npm ci
npm run lint
npm run typecheck
npm run validate:content
npm test
npm run build
npm run test:e2e
```

`npm run check` already combines lint/typecheck/content/unit/build. Run targeted tests after each relevant patch; run the whole check at stage boundaries and after shared-hook/helper changes. Do not run builds repeatedly after documentation-only edits. The browser suite needs a completed build.

**Planned additions at M12:** `npm run validate:v2` → `tsx scripts/validate-v2.ts`; `npm run check:v2` → `node scripts/check-v2.mjs`. The validation command explicitly opts into V2 content checking and never opens a DB. The runner sets server env in Node, resolves fixed installed Node CLI entry points, uses shell:false and propagates failures; no POSIX-only inline variable assignments or npm.cmd shell assumptions. It runs V2 content/unit checks, a V2-enabled build and the dedicated Playwright config. It accepts only documented fixed tasks (content, unit, build, browser or all), never a caller-supplied shell command. Local all runs the complete suite; CI uses content/unit/build on all three OSes and browser on Linux.

Extend the existing three-OS workflow with V2 content/unit/build checks; run the V2 browser portion on Linux, keeping Chromium there as the existing default and record Windows/macOS browser limitations unless actually tested. Use Playwright config env for CORELAB_V2=1 and an absolute fresh temporary CORELAB_DB_PATH. The V2 config matches only v2-*.spec.ts and clears the legacy exclusion; the legacy config ignores those tests. Unreleased S2-candidate builds are testable before G5, while real profiles remain off. Keep V1 and V2 browser runs/builds separate; do not reuse a live server or concurrently write the same .next output. No new CI service is needed.

### 8.2 Test layers and representative fixtures

| Layer | Main assertions | Isolation |
| --- | --- | --- |
| Pure | Schemas/JCS/fractions/fingerprints, grading/admission/review replay, selection | Injected immutable catalogs, seeded clock/ID sequences |
| SQLite integration | Copy/migration/guards, atomic close/restore, epochs/capacity/snapshots, baseline compatibility | Temporary real WAL files; in-memory only where file semantics are irrelevant |
| HTTP | Flags/locality/body bytes/status/redaction, stale confirm, unavailable import and disallowed trust fields | Direct route tests plus built-server requests; no production getStore default |
| Browser | Freedom/routes/resume/help/feedback, backup/snapshot controls, C/M/review lifecycle, desktop/phone/keyboard | New temp DB for each independent flow or explicitly reset fixture; one worker initially |
| Independent/manual | False accepts/rejects, mathematical alternatives, licensing, pedagogy, screen reader, named OS recovery | Named reviewer and dated result, no self-approval |
| Performance/failure | Permitted 50,000-attempt selector, near-cap backups, interrupted copies/restores, memory/disk limits | Named machine/OS/Node, generated data, measured RSS/disk/bytes/latency |

Use synthetic invalid cases for malicious signatures/protocol fields. Never execute unknown learner code on the host to “test the sandbox”; the pilot has no sandbox. Keep real private keys and learner files out of logs, fixtures, browser traces, screenshots and Git.

### 8.3 Rollback rules common to every milestone

1. **Before live writes:** feature off and code revert are sufficient. Migration work is tested only on disposable copies until recovery is ready.
2. **After any V2 data exists:** stop writes; retain a current consistent recovery copy and complete /3 export when supported. Feature off provides legacy view, not full V2 export/restore or a schema downgrade.
3. **Application rollback:** leave sidecar and immutable source/policy versions in place. Older unsupported sidecar readers fail closed; do not forge a schema version or manually drop evidence tables.
4. **Data recovery:** preview the selected full local snapshot/current verified copy, stop/reopen safely and confirm the exact target. Never copy only a live WAL database's main file. Restore snapshot/pruning failure must roll back atomically.
5. **Content defects:** withdraw affected availability, version the fix, preserve old bytes and recorded claims. Any re-derived projection explains the mismatch; never fabricate a stronger original result.
6. **Mixed history:** acknowledge current hash/count explicitly and create one epoch; do not merge into legacy evidence or reinterpret a hash match as an authenticated audit.

## 9. Acceptance traceability

Every Unified Spec §15 ID has an owner here. “S1 foundation; S2 activation” means recovery/invariants are implemented early, not that S1 issues live C/M checks. **AC-I4 is deliberately outside the pilot**, not silently marked passed.

| Spec ID(s) | Primary milestone(s) |
| --- | --- |
| VS-01 | M02, M10, M13 |
| VS-02 | M02, M09, M10 |
| VS-03 | M02, M10 |
| VS-04 | M08 |
| VS-05 | M08, M10, M11 |
| VS-06, VS-07, VS-08, VS-09 | M11 |
| VS-10 | M01, M02, M11, M13 |
| VS-11 | M14 |
| VS-12 | M15 |
| VS-13 | M03, M04, M06, M12 |
| VS-14 | M04, M05, M07, M12 |
| VS-15 | M07, M10, M12 |
| VS-16 | M00, M12, M16 |
| AC-I1 | M03, M05, M08, M16 |
| AC-I2 | M11 |
| AC-I3 | M08 |
| AC-I4 | Future G-I only |
| AC-A1, AC-A2, AC-A3, AC-A4, AC-A5, AC-A6 | M08 |
| AC-A7, AC-A8 | M14 |
| AC-A9 | M01, M08, M14 |
| AC-A10 | M05, M08, M14, M15 |
| AC-E1 | M03 guard, M14 live service |
| AC-E2 | M00 baseline, M12, M14, M16 |
| AC-E3 | M14, M15 |
| AC-E4 | M14, M15 |
| AC-E5, AC-E6, AC-E8 | M05, M06; M16 integrated |
| AC-E7 | M05, M14 |
| AC-M1, AC-M2, AC-M3, AC-M5 | M03 |
| AC-M4 | M06, M09, M12 |
| AC-M6 | M03, M06 |
| AC-B1, AC-B4 | M04 |
| AC-B2, AC-B3, AC-B5, AC-B7 | M06 |
| AC-B6 | M04, M07, M12 |
| AC-B8 | M07 |
| AC-B9 | M06, M07 |
| AC-B10 | M04, M06, M12 |
| AC-P1, AC-P2 | M09 |
| AC-P3 | M09 baseline measurement, M16 full S2 |
| AC-F1 | M07, M10, M12 |
| AC-F2 | M01 |
| AC-F3 | M06, M09, M12 |
| AC-C1 | M02, M11, M13; G2 before release |
| AC-C2 | M02, M11, M13 |

For S1 release, pass all spec S1-tagged conditions using recognized synthetic forms/reviews where live activation is S2, plus actual S1 ready content. For S2, rerun against actual reviewed forms/pools and the complete workflow. Never let synthetic coverage stand in for authored item review or browser behavior.

## 10. Codex execution procedure and completion record

For each authorized milestone:

- [ ] Read its dependencies, pending approvals and current source diff. Confirm any shared contracts still match the spec hash or record an approved revision.
- [ ] Implement the smallest unchecked task that yields a testable behavior. Keep production DB/default keys untouched; use fixtures for all migration/restore work.
- [ ] Run the targeted tests, inspect real failures and fix them without weakening an invariant or removing meaningful assertions.
- [ ] Review changed files against the milestone allowlist and protected baseline. Explain any necessary integration-file addition rather than hiding it in an unrelated patch.
- [ ] Record actual command/result, environment, acceptance IDs, review evidence and rollback outcome. Mark a box complete only after its exit is met.
- [ ] Proceed autonomously to the next authorized dependency-complete task. If an external approval/reviewer blocks activation, keep the safe default and continue independent authorized code/tests; never self-grant the gate.
- [ ] At each stage boundary run the complete stage checks and recovery rehearsal; request only the concrete outstanding activation/release decision, with evidence ready to review.
- [ ] Commit/push only when separately authorized. Preserve repository privacy; do not deploy or change visibility as part of local implementation.

A compact progress entry is enough; no tracker application or new status protocol is required:

```text
Milestone / task:
Files changed:
Actual checks (command, OS/Node, result):
Spec acceptance IDs satisfied / still pending:
Independent review / owner approvals:
Data/source preservation and rollback evidence:
Next dependency-complete task / concrete blocker:
```

**Effort:** retain the Unified Spec's low-confidence 95–180 hours for S1+S2 before reviewer time, plus at least 21 calendar days for S3. These milestones are not new measured estimates or a guaranteed schedule. Re-estimate after recovery/capacity work and S1 qualification; 128 MiB validation/replay or cross-platform failures can change the cost. Do not squeeze this into the curriculum's 12-hour FK slot.

## 11. Planning validation and handoff

This plan was checked against the actual repository and the finalized spec. The milestone dependency graph is acyclic, all 62 acceptance IDs are mapped, planned routes have milestone owners, existing-file links resolve, and stages retain explicit approval/review gates. No task box represents completed implementation.

No application build, lint, unit, browser or OS test is claimed by producing this document. The limited research checks in the Unified Spec remain research results. Only this Master Plan is added; existing source, user data, review reports and the specification are preserved.

**Ready to execute when implementation is authorized:** start at M00/M01, work through recovery before enabling learner writes, release S1 before S2, and enter S3 only after its gates. Automatic I, reviewed transfer, graph adoption, D7 and further exercise/lab families remain outside this pilot.

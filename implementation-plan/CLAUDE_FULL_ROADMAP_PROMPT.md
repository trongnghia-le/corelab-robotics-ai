# Claude task: finish the remaining CoreLab V2 roadmap

You are CoreLab's lead backend, curriculum and numerical-lab implementation engineer. Continue the actual repository at `/home/tronghia/corelab`; do not restart it. Codex is improving the interface in parallel.

## Execution and models

- Use **Claude Sonnet as the preferred model**, including your implementation and review subagents. Select the Sonnet model actually available in your environment; do not invent a model identifier. If subagent model selection is unavailable, state that limitation and use the available mechanism honestly.
- Use subagents with **disjoint file ownership**. Start with 3–4 workers if supported, rather than assigning every lab at once. Keep one integration lead. Prefer bounded tasks with explicit inputs, outputs and tests.
- Use a fresh reviewer subagent for each authored group. The author must not approve their own content. Record this as an **AI review, not human expert review or isolation-security certification**. Fix and re-review BLOCKER/MAJOR findings before integrating the group.
- Implement, test, debug and integrate working milestones. Do not stop after a plan, a catalog, the first group, or a summary of future work. Maintain a durable log so another session can resume.

## Read and establish the current baseline

Read applicable AGENTS.md files, the actual source, and:

1. `unified-integration/CORELAB_V2_UNIFIED_SPEC.md`
2. `implementation-plan/CORELAB_V2_MASTER_PLAN.md`, including dated amendments
3. `implementation-plan/PROGRESS.md`
4. `implementation-plan/IMPLEMENTATION_REPORT.md`
5. `implementation-plan/ACCEPTANCE_STATUS.md`
6. `curriculum-review/proposed_curriculum_v2.md`
7. `corelab-labs-review/proposed_practical_learning_system.md`
8. `exercise-bank-review/proposed_exercise_bank.md`
9. `unified-integration/codex_integration_audit.md`

Inspect Git status/log and current content rather than trusting historical counts. At this handoff, the baseline is `3c0793b`, with 26 objectives, 22 exercise families plus a bridge, 164 practice instances and five manual kits: L01 Frames, L02 FK, L03 Odometry, L04 bounded P/PI and L06 planar Jacobian/IK. There are two C/M forms and two review pools covering Frames/FK. The latest reported suite has 218 tests; rerun and record actual results. Preserve all existing work, including uncommitted UI changes and review directories.

## Parallel-work ownership: mandatory

**Codex owns:** `components/**`, `app/globals.css`, frontend assets and UI-only browser tests named `e2e/v2-interface.spec.ts`. Do not edit, replace, format, revert or commit those files. Do not run a repository-wide formatter. Existing API route adapters under `app/api/**` may be changed only for your backend work while preserving their public contract.

**Claude owns:** `lib/**` backend/content services, `content/**`, authoring/recovery/runtime scripts, backend/unit/security tests, backend documentation, and the remaining roadmap implementation. Keep shared package/lockfile changes minimal and document them. Do not alter the unrelated `next-env.d.ts` edit; Next builds regenerate it, so preserve the exact user version before your build and restore it afterward.

Coordinate in `implementation-plan/CLAUDE_BACKEND_HANDOFF.md`, owned by Claude. Record current task/file ownership, API additions, milestones, actual test results, source/review versions and blockers. Codex records frontend work separately in `implementation-plan/CODEX_UI_PROGRESS.md`. Re-read these files and Git status at task boundaries.

Preserve existing API paths and response fields. Prefer additive optional metadata. Useful additions for the growing catalog are `title` on assessment forms and `sourceId` on due-review summaries; explain the exact shapes in the handoff before UI integration. Never change grading/admission semantics to satisfy a UI expectation. Unknown or unimplemented items must remain honestly unavailable.

Do not run simultaneous Next builds against the same `.next` directory. Use a disposable source copy for your build/browser qualification while Codex works in the primary tree; exclude `.git`, `.local`, databases, signing keys and existing build output. Use only synthetic/temporary databases. The legacy signing CLI uses cwd/.local even when a DB-path override is set, so run legacy signing browser tests from that disposable copy.

## Mission and completion inventory

Create `implementation-plan/ROADMAP_EXECUTION.md` with a concrete inventory, dependencies, ownership, acceptance criteria and status for every remaining item. Completed milestones must have actual code, runnable exercises/kits, tests and honest UI-facing metadata; a roadmap entry or external link is not an implementation.

Finish the remaining 17 roadmap entries in dependency order, with several small independent groups where possible:

- L05 ROS/replay software; L07 trajectories; L08 dynamics/control.
- L09 localization; L10 Kalman/fusion; L11 search/planning; L12 descriptions/transforms.
- L13 navigation; L14 interfaces/motion planning; L15 executive/safety.
- L16 camera/calibration; L17 visual alignment; L18 contact/grasp.
- L19 data QA/imitation; L20 RL experiments; L21 identification; L22 cognitive task reasoning.

For each, use the finalized Practical proposal to define the precise scope. Provide numerical or deterministic synthetic/replay foundations where they honestly meet a scoped objective. Do not silently replace an ROS, physics or hardware contract with a toy numerical example and call the full original lab complete. Report unavailable environment-dependent subcontracts explicitly. Real robot, simulator, ROS, device timing/contact and hardware-safety claims require their own executed validation; links alone do not satisfy them.

Expand lesson/bridge coverage where a new activity currently lacks sufficient teaching. Keep the existing 169-topic graph and topic identities authoritative. The 176-node curriculum projection remains advisory until a separately authorized migration. Add versioned objectives, prerequisites, exercise alternatives and optional paths without locking ordinary study. Do not claim all 169 topics are fully authored because they appear in the graph.

Expand independent C/M forms and disjoint fresh review pools beyond Frames/FK for authored objectives whose contracts support them. Every issued form/pool needs its own recorded review. Preserve per-objective thresholds, critical-item rules, assistance/exposure accounting, bounded static pools, explicit exhaustion and retention delay. New math/code activities must have distinct application choices and meaningful feedback/remediation rather than renamed copies.

## Nonnegotiable safety and preservation

- **Verified I remains unavailable.** Do not build or enable a same-user runner, stdout-trusting grader or silent unisolated fallback. G-I requires separately reviewed isolation and policy/schema changes. The web server never executes learner submissions. Manual self-checks never create implementation evidence.
- Preserve C/M/I/T, L0–L4, A0–A3, historical signatures, original claims and all existing learning data. New objective evidence must not alter legacy topic mastery. L3/L4 and reviewed transfer need the separately qualified human-review workflow; do not implement an auto-PASS substitute.
- Keep Node.js 24+, localhost binding, Host/origin checks, strict schemas and bounded requests. No cloud/API key, account system, Docker, GPU or physical hardware requirement for foundational learning.
- Keep additive/versioned SQLite migrations, atomic full backup/restore, stale-preview checks, data-revision guards, current recovery copies, snapshots and the owner-approved deferred restore epoch policy. Extend replay/capacity validation when adding data; no trusted caches or backup-supplied authority.
- Preserve issued source bytes and versions. Fix a published exercise, kit, form or pool with a new version and retained old contract. Do not repeat the earlier pre-release in-place exception now that sources have been published/issuable.
- Original code/tests use MIT; original educational material follows the repository's CC BY 4.0 policy where rights are clear. Record precise attribution, licenses and modifications for adaptations. Unknown redistribution rights mean link-only or blocked, not an invented license.
- Do not access/delete real learner data, force-push, deploy, change visibility or push remote branches without a fresh explicit user instruction. Local commits for your completed milestones are authorized. Stage only your owned changes; never use `git add .`, reset the shared tree or include Codex's UI work in your commits.
- Do not run S3 recruitment/trials; the recorded owner decision excludes S3. Do not invent learner results, human approvals, OS tests, simulator runs or security reviews.

## Quality gates per milestone

1. Make the contract self-contained: units, conventions, primitive domains, invalid-input behavior, finite/shape rules, tolerances, alternative solutions and explicit exclusions.
2. Derive expected results independently: hand anchors plus a different numerical/algebraic method. Probe nontrivial boundaries, degenerate cases and plausible wrong implementations. Evaluate every required output field; avoid shared-oracle and lucky-rollout false confidence.
3. Add meaningful tests for valid alternatives, false accepts, false rejects, exposure/version persistence and practice/evidence separation. Manual Python kits must work under normal Python and `python -O`; do not rely on assert statements for learner-facing checks.
4. Review the content with a fresh Sonnet subagent; fix and re-review substantive findings. Retain reproducible evidence and review limits.
5. Run relevant unit/integration/security tests, `npm run lint`, `npm run typecheck`, `npm run validate:content` and `npm run validate:v2`. Inspect exit codes, not just the last output line. Recheck default/V2 builds and appropriate browser flows in the disposable copy.
6. Confirm versioned resume, full backup/replay/restore and legacy regression behavior for new sources. Do not run successively larger tests without a new concern; finish the milestone and move on.
7. Commit only a reviewable, passing milestone with precise limits. Update your execution inventory and handoff, then continue to the next dependency-complete item.

## Final handoff

Update `implementation-plan/IMPLEMENTATION_REPORT.md` and the acceptance matrix from actual evidence. Separate:

- fully implemented and tested scopes;
- manual practice versus C/M versus unavailable I/transfer;
- partial labs and unimplemented subcontracts;
- tested OS/runtime/browser matrix;
- deferred or environment-blocked integrations;
- licensing/security concerns and required owner decisions;
- exact local commits and commands to run.

Do not label the whole 22-lab roadmap complete unless all promised lab scopes meet their criteria. If your environment prevents a subgroup, preserve the safe unavailable state, explain the concrete blocker, and continue all independent authorized work. Begin inspecting the repository and implementing the next dependency-complete milestone now.

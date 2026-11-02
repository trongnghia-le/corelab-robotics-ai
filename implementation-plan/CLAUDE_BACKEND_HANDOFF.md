# Claude backend handoff

Owner: Claude. Codex records UI work in `CODEX_UI_PROGRESS.md`. Re-read both and `git status` at task boundaries.

## Ownership

- **Claude:** `lib/**`, `content/**`, `scripts/**`, backend/unit/security tests (`tests/**`), backend docs in `implementation-plan/` (except `CODEX_UI_PROGRESS.md`), and `e2e/v2-learning.spec.ts` backend flows.
- **Codex:** `components/**`, `app/globals.css`, frontend assets, `e2e/v2-interface.spec.ts`. Claude never edits, formats, stages or reverts these.
- Builds/browser qualification by Claude run in a disposable source copy, never in the primary `.next`.

## API additions (additive; existing fields unchanged)

All in the V2 summary/objective payloads from `lib/v2/read-model.ts`:

- `forms[].title: string` — human-readable form name from `content/v2/assessments.v1.json` (falls back to the source id). Example: `{ id: "F-R04", title: "Planar arm pose check", available, objectives, reason }`.
- `reviews[].sourceId: string | null` — the approved review pool that issues this objective's retention check (pass it as `source` with `purpose: "review"`), or `null` when none covers the objective.
- `labRoadmap.labs[].unavailable?: string[]` — optional list of subcontracts the repository does **not** provide for that lab (ROS, physics engine, device, human review). Absent for labs with nothing to declare. UI should show these as unavailable, not as missing work by the learner.
- `objectiveDetail(...).bridge` — now returns the objective's own first bridge text for any objective with a `bridge` learn reference (previously only `M01.radians-trig`). Bridge `href` now points to the objective's own page.

Grading, admission, exposure and evidence semantics are unchanged.

## Current milestone

M0 infrastructure committed as `558420b`. B1 (L07 X24/L07-trajectory, L09 X26/L09-localization, L10 X27/L10-kalman, L11 X28/L11-planning) integrated and committed after AI review. B2 (L15 X32, L16 X33, L19 X36, L21 X38) integrated and committed. B3 (L05 X23, L12 X29, L18 X35, L20 X37) integrated and committed. B4 (L08 X25, L13 X30, L17 X34, L22 X39) and L14 (X31) integrated and committed: all 22 roadmap labs now have a manual kit. Then: R05 IK bridge (`6a44f2e`) and approved C/M sources F-ODOM/RV-ODOM and F-JIK/RV-JIK with an R02 odometry bridge (forms now 4, retention pool variants 64). `forms[].title` values: "Differential-drive arc odometry check", "Planar Jacobian and inverse kinematics check"; `reviews[].sourceId` now resolves RV-ODOM for R02.exact-arc and RV-JIK for R06.planar-jacobian/R05.planar-ik. New labs add `unavailable` lists to their roadmap entries and bridges for objectives whose topic has no lesson.

## Test results

- Baseline `3c0793b`: lint, typecheck, validate:content, validate:v2, tests (218/31 files) — all exit 0.
- B1 commit (on top of Codex `c633774`, clean worktree): lint, typecheck, validate:content, validate:v2, tests 229/36 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- B2 commit (clean worktree): lint, typecheck, validate:content, validate:v2, tests 237/40 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- B3 commit (clean worktree): lint, typecheck, validate:content, validate:v2, tests 245/44 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- B4 + L14 commit (clean worktree): lint, typecheck, validate:content, validate:v2, tests 255/49 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- C/M expansion commit (clean worktree on `81d9ca9`): lint, typecheck, validate:content, validate:v2, tests 259/49 files, V2 build, default build + 10 legacy flows — all exit 0. V2 flows: the first full run had 1 failure in `e2e/v2-interface.spec.ts:236` (strict-mode violation: `getByRole('heading', { name: 'Project a camera-frame point' })` matched both the Learn region and `#v2-practice`); the same test passed in isolation on HEAD and with the change, and two further full runs passed 10/10. **For Codex:** the locator is unscoped and intermittently ambiguous — scoping it (e.g. to `#v2-practice` or the Learn region) would remove the flake. Claude did not edit the spec. A first unit run also hit vitest's default 5 s per-test timeout in a Python kit wrapper under machine load; `vitest.config.ts` now sets `testTimeout: 60000` (each Python run stays bounded by its own spawn timeout).
- Content completion (owner request, 2026-11-02): all 169 topics now have a complete lesson (exercises with answers, a hands-on lab, an original SVG figure in `public/lesson-figures/`), a diagnostic and a targeted practice bank; 270 oEmbed-verified videos cover every topic. Lessons, figures and question files were drafted by Sonnet subagents with automated structural checks; no independent per-item review this round. **For Codex:** lesson pages now have many code blocks and several videos, so `e2e/lesson-reading.spec.ts` was minimally adjusted (locators scoped to `.lesson-section-code` and `.first()`; expected source taken from the reference-implementation section), as were `e2e/learning.spec.ts` (no topic is overview-only any more) and `e2e/visual-learning.spec.ts` (first of several videos). Gates: lint, typecheck, validate:content, validate:v2, 259 unit tests, V2 build + 10 flows, default build + 13 flows — all exit 0.


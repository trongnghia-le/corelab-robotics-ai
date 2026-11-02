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

M0 infrastructure committed as `558420b`. B1 (L07 X24/L07-trajectory, L09 X26/L09-localization, L10 X27/L10-kalman, L11 X28/L11-planning) integrated and committed after AI review. B2 (L15 X32, L16 X33, L19 X36, L21 X38) integrated and committed. In progress: B3 (L05 X23, L12 X29, L18 X35, L20 X37). New labs add `unavailable` lists to their roadmap entries and bridges for objectives whose topic has no lesson.

## Test results

- Baseline `3c0793b`: lint, typecheck, validate:content, validate:v2, tests (218/31 files) — all exit 0.
- B1 commit (on top of Codex `c633774`, clean worktree): lint, typecheck, validate:content, validate:v2, tests 229/36 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.
- B2 commit (clean worktree): lint, typecheck, validate:content, validate:v2, tests 237/40 files, V2 build + 10 V2 flows, default build + 9 legacy flows — all exit 0.

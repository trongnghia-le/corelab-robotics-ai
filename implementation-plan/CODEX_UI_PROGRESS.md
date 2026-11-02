# Codex UI work — 2026-11-02

Baseline: 3c0793b. User requested Claude implement the remaining roadmap with Sonnet subagents while Codex handles the interface. Claude's complete prompt is CLAUDE_FULL_ROADMAP_PROMPT.md. Backend integration notes belong in CLAUDE_BACKEND_HANDOFF.md.

## Ownership

Codex owns components/**, app/globals.css and e2e/v2-interface.spec.ts. Claude owns backend, curriculum, labs and backend tests. Preserve public API response fields; additive form title and due-review sourceId metadata are welcome. Neither worker should stage the other's files or run simultaneous builds in the primary .next directory. No push/deploy/visibility change is authorized by this handoff.

## UI direction approved by the user

Keep the existing dark/orange theme, improve layout and larger readable typography. English UI. Preserve keyboard/mobile completion, safe assistance declarations, evidence distinctions and all backend behavior.

## Current task

Improve the objective workspace: make Learn/Practice/Apply/Verify/Review easy to navigate, surface practice before long secondary material, improve exercise discovery/cards, active-attempt reading and honest empty states, and fix V2 navigation context. No backend, schema, grade or content contract changes.

## Checks and commits

Implemented and verified below. Use fresh temporary databases for browser testing and restore the unrelated user's next-env.d.ts after builds. Never use default learner/signing paths for tests. Last known preserved user copy: .local/codex-v2-resume-5_y675c8/next-env.original (verify before relying on it).

## Delivered interface

- Preserved dark/orange styling and English. Objective reading text is 17px; inputs/buttons are 16px, with minimum 46px button height. Main problem text is larger and spaced for working through a task.
- Added Learn / Practice / Apply / Verify / Review anchors. Kept goal selection optional and objective readiness/bridge available. Root practice modes moved from about 2,986px to 894px from the top at 1440×1000 on a clean workspace.
- Added exercise search across IDs, titles, scopes, topics, domains and routes; clear filters and useful no-result recovery. Recommended, Explore, More Practice and route choice remain available.
- Placed active work before the exercise cards, focused it after issue/resume, and added a recent-practice resume action. Preserved assistance, answers, feedback, scratchpad and durable API behavior.
- Distinguished independent-check/review submission and feedback from practice. Kept the assistance warning/consent and independence limits. Missing C/M forms/kits show honest scoped messages; I and human-reviewed transfer remain unavailable.
- Added semantic evidence summaries and active V2 sidebar context. Rendered backend form titles, review source IDs and lab exclusions from Claude's additive API contract. A review with no source cannot issue an arbitrary fallback form.
- No schema, migration, admission, signing, execution or legacy scoring changes. No dependencies added.

## Executed verification

Integration baseline: backend milestone `558420b` plus this UI change. Linux, Node 26.8.1, Chromium; these checks do not certify native Windows/macOS or Safari/screen-reader behavior.

| Check | Actual result |
| --- | --- |
| `npm run lint` | Passed |
| `npm run typecheck` | Passed |
| `npm test` | 221 tests / 32 files passed |
| `npm run validate:content` | Passed; 169 topics, 31 complete lessons |
| `npm run validate:v2` | Passed; 26 objectives, 22 families plus bridge, 164 practice instances, 5 kits, 2 forms, 36 review items; I unavailable |
| `npm run build:v2` | Passed; final repeat after the last roadmap-copy edit also exited 0 |
| `npm run test:v2:e2e` | 8 passed: four existing learning/security/recovery flows and four new interface flows |
| `npm run test:e2e` | 7 passed with V2 off in disposable copy `/tmp/corelab-ui-legacy-wfc7wkri`; legacy signing/data stayed outside the workspace |
| Visual inspection | Actual Chromium desktop and phone screenshots inspected; 320px/390px pages have no horizontal overflow; 16px inputs and 44px+ input height checked |
| Preservation | Unrelated `next-env.d.ts` matches `.local/codex-v2-resume-5_y675c8/next-env.original`; real learner databases untouched |

New browser coverage: discovery/navigation creates no learning records; active practice has focus and precedes cards; A1 survives reload/resume with the same attempt; mobile bridge and unavailable-form states; Verify labels and help consent agree with persisted assistance. Existing browser flows additionally cover local requests, public-answer redaction, manual kits, backup/restore, legacy evidence and visual controls.

React review: effects remain guarded where new fetch state is introduced; derived filters stay derived; stable list keys, semantic headings/labels, pressed-mode state, keyboard focus and escaped text retained. No new client import of server code (read-model/attempt imports are type-only). API calls still pass through the existing strict local routes. No renderer executes learner code.

Screenshots for this session: `/tmp/corelab-ui-dwpd0uqp/after-desktop.png`, `after-mobile.png`; browser artifacts are in ignored `test-results/`. They are real local captures, not public/OS support claims.

## Handoff and rollback

Claude can continue backend/content milestones using `CLAUDE_BACKEND_HANDOFF.md`; Codex has consumed its additive metadata. Keep frontend ownership separate. Future catalog growth should preserve title/sourceId/exclusion fields and run the interface suite. A scoped manual kit is not the full ROS/physics/hardware lab.

This change has no data migration; rollback the UI commit with a normal revert while preserving backend commits and learner data. No push, deployment or visibility change was performed. Local test servers owned by this session are stopped after validation. Do not label the full roadmap complete from this frontend milestone.

## Follow-up: Robotics & AI identity (2026-11-02)

User found the workspace too generic. Codex is adding an explicit Robotics & AI hero, an original static robot/perception/learning concept sketch, real authored objective entry links, and clearer sidebar/dashboard/browser-title identity. Preserve dark/orange, English, large text and all learning/data behavior. The only edit to Claude-owned `e2e/v2-learning.spec.ts` is the existing root heading assertion, updated for the new hero; no backend flow is changed. Backend/content/lab work remains Claude's. Checks for this follow-up are pending below.

Delivered the identity follow-up: explicit Robotics & AI first-principles heading; original accessible SVG concept sketch of perception, learning and a planar arm; four links to authored R04, V03, ML05 and RL02 objectives; Robotics & AI lab navigation, dashboard description and browser title. The concept is labelled as an illustration; no simulator/device integration or new learning functionality is claimed. Root summary counts now sit with exercise results to give learning activities priority.

Verification: `npm run lint`, `npm run typecheck` and final `npm run build:v2` passed. All **9 V2 Chromium flows** and **7 legacy Chromium flows** passed on Linux/Node 26.8.1. Legacy checks ran in `/tmp/corelab-identity-legacy-elk5jj6n`, with synthetic data and signing keys outside the workspace. The first browser pass caught practice discovery falling below its 1,100px budget; compacting root metadata and spacing fixed it, with the original test budget retained. The new identity test verifies the page title, semantic heading, concept image, four live objective references, actual camera-objective navigation, and root overflow at 320px/390px. Existing help/evidence/backup tests still pass. No new unit suite or OS validation is claimed for this visual/copy follow-up.

Actual final screenshot copies: `/tmp/corelab-ui-dwpd0uqp/robotics-ai-final-desktop.png` and `robotics-ai-final-mobile.png`. Preserved the exact pre-existing next-env.d.ts. No production database, backend file, content contract, external service, dependency, push or deployment was changed. Rollback is a normal revert of this UI-only follow-up commit.

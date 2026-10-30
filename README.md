# CoreLab

A local, single-user learning workspace for Robotics, Computer Vision, Reinforcement Learning, and Cognitive Robotics. Start with **zero verified knowledge**, study first principles, implement algorithms, and keep reproducible evidence of what you can do.

The interface, lesson headings, practice instructions, and diagnostics are entirely in English. There are **169 original curriculum topics**, **31 complete lessons with versioned diagnostics**, structured overviews for every topic, and eight practical assignments. The supplied curriculum IDs and prerequisites are unchanged.

## Run locally on Ubuntu

Requires **Node.js 24+**, npm, and Git. Python 3 is needed only for the optional local Python labs; a C++17 compiler is needed only for C++ practice. No account, API key, Docker, database setup, cloud service, or subscription is required.

```bash
npm ci
npm run dev
```

Open **http://127.0.0.1:3000**. Both development and production bind to loopback by default. For a production build:

```bash
npm run build
npm start
```

Lessons, graph, assessments, notes, and progress work without Internet after dependencies are installed. Reference links need Internet. No analytics, telemetry, remote fonts, AI requests, or cloud synchronization are included. Next.js telemetry is disabled by the run/build scripts.

## Start studying

1. Open the Dashboard. All topics begin **Unassessed**, not at a fictitious progress percentage.
2. Open M01 and try its diagnostic before consulting the worked examples. Select assistance A0–A3 honestly.
3. Study the derivation, implement the exercise independently, and record tests and uncertainties in the notebook.
4. Return to Assessments. Your answers, score, item feedback, assistance, contract version, and timestamp persist in SQLite.
5. Follow the next recommendation. PY01 and CPP01 can run alongside the mathematics branch; later branches follow their own prerequisites.
6. Use Learning Paths to select a domain goal or pin a project topic. The recommender prioritizes its missing foundations without hiding unrelated topics.

Roadmap has searchable/filterable list and interactive graph views. Graph defaults to one domain and includes its boundary prerequisites; choose a topic to inspect its full dependency chain. Every topic is navigable. **Overview** explicitly means that a complete lesson or assessment is not yet available.

## Assessment and mastery

Four independent dimensions are displayed: **C** conceptual understanding, **M** mathematical reasoning, **I** independent implementation, and **T** transfer/retention. The app never averages these into a competence percentage. A diagnostic score is a score on that specific test only.

- **L0**: no verified evidence. Reading, practice checkoffs, notes, and imported AI feedback do not certify ability.
- **L1**: an independent A0 diagnostic meets its objective threshold (at least 80%) and every critical item passes. Concept and numerical evidence remain separate.
- **L2**: concept and numerical gates plus an independent implementation report from a supported fixed local test contract. Initially available for **M02 and PY01**. Numerical questions establish only the calculations tested; they do not certify unrestricted proof ability.
- **L3**: novel application plus retention evidence. **L4**: reproducible critical evaluation or extension. No initial assessment contract certifies L3/L4. A learner can record these as **provisional self-assessments**, which never unlock verified prerequisites.

A0 means no assistance, A1 a conceptual hint, A2 a specific hint/example, and A3 a supplied solution. Only a fresh A0 pass can satisfy independent gates. Assistance is self-declared; this is a personal learning system, not proctored certification. Short answers are stored with transparent rubrics and require human judgment; they are never automatically graded.

Passing A0 retests separated by at least seven days record **retention evidence only**, not novel transfer. Failed reviews create a gap while retaining historical verified evidence. Reviews use 1/3/7/21-day suggestions after successive due A0 passes; an early repeated pass does not postpone an existing review. Scores, evidence, and reviews can be inspected in each topic's assessment history.

Recommendations are deterministic: consider missing prerequisites, essential foundation order, priority, selected goal and project ancestors, actual failed attempts, due reviews, and already verified evidence. At most three recommendations include a reason and suggested exercise. A diagnostic L1 is sufficient to proceed with the next introductory activity; it is not a claim that the topic's lifetime target level has been achieved.

## Mistake-driven practice and knowledge types

Open **Practice → My Weaknesses**, or use **Practice Weaknesses** on the Dashboard. Incorrect objective answers are derived from the original attempt history and grouped by topic and skill. You can inspect question IDs, immutable contract versions, error counts, failed submissions, categories, timestamps, prerequisites, and review status. Ungraded short answers are never counted as mistakes. Categories come from authored metadata; legacy questions use a visibly labeled, conservative format-based fallback.

Use **Review Concept** for the relevant lesson section, **Practice Weak Skill** for a focused set, or **Retry Assessment** for the complete diagnostic. The selector deterministically prioritizes authored equivalents for the failed skill, due recall checks, and fresh examples. Repeated failures also suggest checking actual unverified prerequisites. Selection never invents curriculum edges or random questions. The initial library contains **42 focused questions across M02, M05, PY01, R04, ML05, V01, and RL02**; missing coverage is stated explicitly.

A skill remains **Active** until new evidence corrects it. Assisted correctness records **Practiced with assistance**. A fresh correct A0 equivalent can record **Independently corrected**; explicitly mapped, newer signed A0 labs can repair the relevant skill as well. Correct answers do not cancel an error in the same skill within the same submission. History is retained, and a later error reopens the weakness. When the existing topic review becomes due, a repaired skill is labeled **Due for retention review**. A delayed A0 failure after prior independent correctness can be categorized as a retention failure; this is separate from mastery.

The same 1/3/7/21-day topic scheduler is used for diagnostics and focused objective attempts. Open rubric responses do not create review failures. A correct partial set does not postpone other skills still due on the shared schedule. An already-seen variant can be reused once when review is due and at least seven days have passed; immediate retries and further automatic recycling are refused. When the authored bank is exhausted, review feedback or explicitly retry the full diagnostic. More variants must be authored.

Assessment questions display four complementary knowledge types:

| Knowledge type | Assessment method | Evidence limit |
| --- | --- | --- |
| Concept | Identify misconceptions, explain principles and assumptions | Objective checks can contribute only through the full diagnostic gates. |
| Procedure | Numerical calculations, derivations, independent verification | Open derivations use rubrics; keywords do not verify reasoning. |
| Implementation | Build, debug, run local tests | Only supported signed A0 lab reports satisfy I gates; a written plan is unverified. |
| Design & Decision | Compare scenarios, assumptions, alternatives and trade-offs | Open engineering judgments remain rubric-guided and unverified. |

Knowledge type chooses **how** to assess; C/M/I/T still describes **which competence** is evidenced. Focused attempts are explicitly marked `purpose: targeted`, retain their selected question IDs and practice contract version, and **never satisfy diagnostic C/M, L1/L2, or retention gates**, even with a perfect score. Repairing a mistake is not global mastery. The existing signed lab workflow and historical full-diagnostic evidence retain their original rules.

New metadata lives in `content/assessment-metadata.v1.json`, outside the unchanged diagnostic v1 answer contracts. Fixed variants and rubrics live in `content/practice/TOPIC.v1.json`. Metadata includes `knowledgeType`, skill tags/labels, categories, related prerequisites, optional method/remediation references, and explicit equivalent-question mappings. Freeze published metadata and practice versions alongside their answer contracts. Content validation checks their references, prerequisite ancestry, lesson headings, answer contracts, and public answer-key redaction. Legacy question formats have deterministic defaults.

The SQLite layout and existing records need no destructive migration: additional attempt fields are optional. New exports use **`corelab-backup/2`**; both old v1 backups and v2 backups are accepted. A v1 envelope cannot disguise targeted attempts. Restore validates selected questions and skills against the retained practice version and recomputes scores; histories, assistance, signatures, and the one topic review schedule survive the round trip.

## Local practice verification

Download a starter from Practice and write your implementation in a separate file. The server **never executes submitted code**. You intentionally run the local verifier in your terminal:

```bash
npm run verify:lab -- --topic M02 --file /absolute/path/solution.py --assistance A0 --out .local/M02-report.json
# or
npm run verify:lab -- --topic PY01 --file /absolute/path/solution.py --assistance A0 --out .local/PY01-report.json
```

The fixed Python harness imports your file locally and checks known examples, boundaries, invalid inputs, mutation, and deterministic property cases. A failing run produces no report. A successful run signs the contract, source SHA-256, timestamp, assistance, and test-group result using an Ed25519 key generated under `.local/`. Import the report through Practice. The app validates its signature, contract, date, and workspace public key and rejects duplicates. A3 reports remain practice.

Signed reports preserve provenance and detect edits, but do not prove who authored a solution or prevent deliberate tampering by the owner of the computer. Backups explicitly restore historical signed provenance, including the original public key; restoring a backup is a trust decision. New lab reports must use this workspace's locally generated key. Private keys are never sent to the app or included in JSON backups.

C++, ML, robotics, vision, RL, and research assignments include starter downloads or experiment templates. Their results can be recorded as practice, with no unsupported automatic verification claims.

## ChatGPT Project workflow (no API)

Use **AI Tutor handoff** or **Copy Learning Context** on a topic. Preview and copy the context, then paste it into your ChatGPT Project yourself. It includes topic ID, objectives, prerequisites, attempted exercises, assistance, verified evidence, notes, difficulties, and your question. There are separate learning, exercise, debugging, and session-summary modes. Diagnostic answer keys are omitted.

Ask the tutor to return:

```json
{
  "schema": "corelab-feedback/1",
  "topicId": "M01",
  "summary": "What we studied",
  "difficulties": ["What remains unclear"],
  "nextSteps": ["A concrete next exercise"]
}
```

Paste this JSON into the feedback form. It becomes AI-reported notes and knowledge debt, never verified mastery. Extra fields that claim verification are rejected. CoreLab has no automatic access to your ChatGPT chats, and ChatGPT cannot directly change its database.

## Progress, backup, and restore

Progress lives in **`.local/corelab.sqlite`**, created automatically. Routine builds, dependency updates, curriculum re-imports, and app restarts do not replace it. For a separate instance, set `CORELAB_DB_PATH` to a different file before starting the server.

In **Data & settings**, export a versioned JSON backup. Restore first validates its schema, topic references, duplicate IDs, assessment versions, review references, timestamps, and signed lab provenance. Imported scores are recomputed from the immutable assessment contract instead of trusted. Preview the record counts and explicitly confirm replacement. Invalid input leaves the database unchanged; replacement is transactional.

A pre-restore snapshot is retained in the local `restore_snapshots` table. To recover one, stop the app and use the SQLite CLI to inspect and retrieve a snapshot into a backup envelope, then import that envelope through Settings. For an exact whole-machine backup, stop the app and copy the entire `.local/` directory, including signing keys. Do not copy a live SQLite file without its WAL or SQLite's backup API.

Backups, databases, journals, notes, keys, model files, and datasets are ignored by Git. Keep exports in `backups/`, `exports/`, `.local/`, or outside the checkout. JSON backup size is limited to 8 MB. Restore replaces the current progress; it does not merge records.

## Architecture and content

- **Next.js App Router + strict TypeScript**, React, Tailwind CSS and a small shared CSS design system.
- **SQLite via Node's built-in `node:sqlite`**: a lean persistence layer, no ORM or native npm build dependency. The read-only curriculum metadata is imported idempotently. Mutable progress is an atomically updated JSON document in SQLite, with validated boundaries and transactions. This keeps the single-user schema easy to understand.
- **`lib/engine.ts`**: pure grading, mastery, recommendation, and handoff functions.
- **`lib/storage.ts` / `lib/actions.ts`**: versioned persistence, input validation, and application mutations. SQLite `user_version` migrations run transactionally; newer unsupported versions are rejected rather than reset.
- **`app/api/`**: same-origin, loopback-only APIs with bounded JSON inputs. No shell execution or external AI integration.
- **`components/`**: shared shell, dashboard, curriculum, reader, assessments, and tools. Heavy graph/Markdown views load only when used.
- **`corelab/`**: original product/design specifications and immutable JSON/CSV curriculum.
- **`content/lessons/ID.md`**: authored lessons; **`content/assessments/ID.v1.json`**: immutable answer/rubric contracts; **`content/overviews/topics.json`**: per-topic structured information. Interactive projection and planar-arm diagrams connect equations to geometry.
- Markdown uses `react-markdown`, GFM, math, and KaTeX. Raw HTML is skipped; MDX JavaScript is not executed. Math uses `trust: false`. Links and assets use safe renderer defaults.

### Add a lesson

Use an existing topic ID; do not silently change prerequisites. Create `content/lessons/ID.md` with YAML frontmatter (JSON is valid YAML) and Markdown body. Required fields:

```yaml
id: m09-foundations
module_id: M09
title: Statistical foundations
summary: What the learner will be able to explain and test.
estimated_minutes: 55
prerequisites: [M08]
objectives: [Define a sampling model, Verify an estimator]
source_refs:
  - title: Original course or documentation
    url: https://ocw.mit.edu/
core_theory: [Sampling and estimation]
labs: [An independent, reproducible experiment]
assessment_refs: [M09-diagnostic-v1]
review_prompts: [Reconstruct the argument after a week]
extension_refs: [https://ocw.mit.edu/]
```

Include motivation, intuition, assumptions, derivation, worked example, implementation, pitfalls, independent exercise, verification, alternatives, transfer, and sources. Use `$...$` and `$$...$$` for math and fenced code blocks. Heading links and the table of contents are generated from `##` headings.

Create an assessment JSON matching an existing example: stable question ID, choice/number/short kind, dimension, critical flag, correct answer and numerical tolerance where applicable, feedback, and rubric for open answers. **Do not edit a published assessment version after real attempts exist**; preserve it and add the next version. Select the new current contract in `getAssessment` when promoting it. Answer keys are removed from the browser topic endpoint and context exports. Source files are intentionally inspectable by the learner; diagnostics depend on honest A0 reporting.

Run `npm run validate:content` after changes. Validation checks the full DAG, metadata, objectives, minimum lesson substance, authored prerequisite closure, contracts, and public key redaction. The application derives topic and lesson counts from files.

### Specification decisions

The current implementation request supersedes the older spec's Phase 1-only and “not requested now” scope. The approved dark theme supersedes the questionnaire's earlier light-mode suggestion. The English-only interface requested by the learner supersedes the original Vietnamese microcopy preference. The curriculum actually contains **169** topics across **8** domain labels (RL and Robot Learning share a domain; Simulation topics share the Robotics domain); these source definitions are preserved. Original setup instructions refer to `chatgpt_project/` files that were not present in the supplied workspace; CoreLab provides its own manual handoff and does not pretend those files exist. Overviews use subject-level references when a precise chapter mapping has not been authored.

## Checks

```bash
npm run check              # lint, strict types, content validation, Vitest, production build
npx playwright install chromium  # once, for browser tests
npm run test:e2e           # production server on port 3217, isolated test database
```

Browser tests cover empty progress, lesson/math rendering, reading separation, assessment submission, reload persistence, evidence, recommendation changes, clipboard context, provisional AI feedback, export/confirmed restore, graph navigation, overview honesty, invalid import, local-origin protection, mobile layout, typed assessment guidance, mistake-driven practice, A3-to-A0 repair, and v2 backup restoration. Unit/integration tests cover graph errors, grading/critical items/tolerances, assistance, mastery gates, retention, recommendations, SQLite transactions, backup integrity, signed reports, targeted selection and exhaustion, mistake repair, type-aware grading, and v1/v2 backup compatibility. Test data and screenshots stay under ignored `.local/` and test-results directories.

## Troubleshooting

- **`node:sqlite` unavailable**: check `node --version`; use Node 24 or newer. This project intentionally uses the built-in SQLite driver.
- **Port 3000 in use**: `npm run dev -- --port 3001`, then open that exact loopback URL.
- **Clipboard denied**: use `127.0.0.1` or `localhost` and allow clipboard access; the generated context is also selectable in its preview.
- **Database locked**: stop duplicate instances sharing the same file. WAL and a busy timeout handle ordinary reads and writes; use a separate DB path for independent instances.
- **Invalid report**: run the verifier from this checkout, use a supported topic and the unedited JSON output. A changed source file requires a new run. Reports from another checkout can be retained through a trusted full backup restore.
- **Browser dependency missing**: install Playwright's Ubuntu dependencies with `npx playwright install --with-deps chromium` if the test runner reports missing system libraries.
- **Setup referenced missing ChatGPT files**: use the handoff workflow above; automatic Project creation and chat synchronization are not implemented.

Repository: https://github.com/trongnghia-le/core-lab-cognitive-robotics

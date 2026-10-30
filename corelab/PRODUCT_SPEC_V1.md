# CORELAB — PRODUCT REQUIREMENTS & FUNCTIONAL SPECIFICATION
Version: 1.1 (curriculum and UI direction approved)  
Date: 2026-10-30  
Audience: one personal learner and Codex implementation agent

## 0. Status and scope
- **Approved**: curriculum domains, zero-assumption baseline, offline/local, no LLM API, mastery/evidence system, curriculum graph, lesson content, practice, curated references, low complexity.
- **UI preferences approved 2026-10-30**: dark-only, bright orange accent, Linear/Notion-inspired, fixed desktop sidebar, dashboard both next lesson + competency gaps, list+graph roadmap, centered lesson+TOC, C/M/I/T matrix. See `UI_DESIGN_SPEC_V1.md`.
- **Not requested now**: implement website, deploy, buy services, create a public user account, modify Notion roadmap.

## 1. Product purpose
A local-first single-user competency engine for learning Robotics Engineering, Computer Vision, Reinforcement/Robot Learning and Cognitive Robotics with shared math/CS/ML fundamentals. Three questions on every visit:
1. Where am I? (verified vs unassessed, not percentage fantasy)
2. What am I missing? (dependency gaps with evidence)
3. What should I do next? (top 1–3 actionable next activities with rationale)

Primary outcome: independent first-principles understanding + derivation + implementation + transfer; AI assists without replacing skill acquisition.

## 2. Non-goals
- No social features, gamification-first streak pressure, commercial SaaS, profiles/accounts, subscription, analytics/telemetry, external LLM API, mandatory cloud.
- No full browser IDE or arbitrary code execution in MVP.
- No auto-generating hundreds of lessons in one pass.
- No claim that an LLM can certify understanding from conversational impressions.

## 3. Learner context
Single learner, assumed UNASSESSED for all skills, Ubuntu development machine, Python/C++, VS Code, RTX 4060 8GB, MuJoCo, ROS 2. Existing papers or repositories must **never** auto-unlock competencies. WBR provides optional context-rich application labs, not prerequisites for general courses.

## 4. Content architecture
- Versioned **modules** in JSON at `curriculum_graph_v1.json`: IDs, title, domain, priority, prerequisites, target_level. Current dataset represents long-term map, not a committed schedule.
- **Lesson** is an instruction unit under a module, stored in Markdown/MDX with frontmatter: `id`, `module_id`, `title`, `summary`, `estimated_minutes`, `prerequisites`, `source_refs`, `objectives`, `core_theory`, `labs`, `assessment_refs`, `review_prompts`, `extension_refs`.
- Recommended common lesson structure: motivation; intuitive model; formal definitions/assumptions; derivation; example; pitfalls; variations/method comparison; independent practice; tests; transfer task; reading.
- JSON graph is shared immutable starter data; SQLite tracks user's evolving status. Lesson content never writes mastery.
- Must validate schema: IDs unique, dependencies exist, directed acyclic graph, required fields present, source URLs validated format (no need internet connectivity to view offline content).
- Link exact source sections and official courses where possible. Do not reproduce copyrighted book chapters.

## 5. Competency data and assessment
### 5.1 Status model
- `unassessed` (default for ALL)
- `in_progress`
- `provisional_L1..L4` (self-report / AI feedback; displayed distinctly)
- `verified_L1..L4` (evidence-based)
- `review_due` is a **flag** orthogonal to mastery, not a replacement status.

### 5.2 Dimensions
C = conceptual, M = mathematical (may be N/A), I = implementation/operational, T = transfer/retention. Avoid averaging into a deceptively precise single % score. A verified level is computed from gates specified in an assessment contract.

### 5.3 Assistance indicator
A0 none, A1 conceptual hint, A2 specific hint/example, A3 solution produced by AI. An A3 submission can pass as learning practice but cannot prove independent implementation or transfer without a new A0 retest.

### 5.4 Evidence and scoring
- Auto-graded: MCQ (critical misconception questions), deterministic math/equation checks, trusted local test reports, structured numerical checks.
- Human/rubric: explanations, design decisions, open research critiques.
- AI Tutor feedback can be attached as provisional note only; never auto-promote mastery.
- Initial quiz rule: >=80% plus no failed `critical` items; adjustable and assessment-specific.
- L2: appropriate derivation and an independent implementation/task with meaningful tests. L3: independent novel transfer task and retention evidence after a gap. L4: research-level critique or improvement with reproducible evidence and review.
- `unassessed` is NOT a grade of 0 or failure; diagnostic starts from zero assumptions and can let the learner skip content based on tests.

### 5.5 Retention
Heuristic 1/3/7/21-day suggestions following evidence, adjustable. Review due does not erase prior verified achievement; failed review creates a gap/retest recommendation.

## 6. Recommendation engine
Deterministic, explainable rule-based selector; no AI API.
1. Check dependencies; use appropriate target for **current activity** rather than demanding completion of every P0 globally.
2. Rank candidate activities by: prerequisite bottleneck, goal relevance, module priority, gap severity, review due, and study workload.
3. Show at most 3 ranked actions, each with **why this** in Vietnamese, estimated effort and what evidence completion produces.
4. Respect focus (e.g. Foundation primary, WBR just-in-time secondary), allow manual pin/override and log reason.
5. Never surface P2 frontier by default unless relevant to a consciously selected study/research direction.
6. No deadline-based artificial anxiety, no unverifiable progress percentage.

## 7. Screens — functional requirements (see approved UI spec)
### 7.1 Dashboard
- Focus lesson / Recommended next action (single hero)
- Current goal and milestone, blockers, one review due item
- Compact module statuses by domain; verified/unassessed distinctly displayed
- Resume last lesson

### 7.2 Roadmap / Knowledge Graph
- Domain filter, text search, prerequisite chain and reverse dependencies
- 7 long-term domains + crosscutting Scientific Research
- P0/P1/P2 filter, unassessed/in-progress/provisional/verified distinctions
- List view is **required**; interactive graph is optional for later phase; do not overwhelm with 170 nodes at once.

### 7.3 Lesson Workspace
- Clear objective and prerequisite summary; progressive sections theory, math, worked example, labs, quiz, extension and sources
- Mathematical typesetting, code snippets, concise reference links
- Button `Copy learning context for ChatGPT`
- Mark reading progress separately from verified competence

### 7.4 Assessment
- Check concept/math, instructions for VS Code local tasks, import trusted test-report summary or manual rubric
- Track test attempts, assistance A0–A3, misconceptions, proof and timestamp
- Explain missing requirements to reach next level; only verified evidence unlocks official mastery

## 8. Local-first integration with ChatGPT Project
- No API calls from CoreLab. ChatGPT is used manually in a ChatGPT Project.
- `Copy Learning Context`: generate versioned YAML/plaintext including topic ID, objective, prerequisites, current evidence, known gaps, help policy; NEVER include hidden tests or answers.
- `Paste Session Summary`: optional import notes generated with `SESSION_HANDOFF_TEMPLATE.md`; parsed fields stored as self/AI-reported notes, not authoritative mastery.
- File uploads into ChatGPT project are manual and controlled by user. Project chats do not access local SQLite or repo by assumption.

## 9. Architecture proposal (MVP)
- Next.js + TypeScript + Tailwind CSS; local Node runtime bound by default to 127.0.0.1.
- SQLite (Prisma/Drizzle or lean query layer chosen at implementation; **do not introduce remote Supabase**).
- Content as files `content/lessons/**/*.md(x)`; curriculum `data/curriculum_graph_v1.json`.
- KaTeX for equations, code highlighting, links to local assignments.
- Tests written in Python (`pytest`) / C++ (`CTest` or native test tool). In MVP code executes **outside the web** through VS Code/terminal; import a structured report manually or via tightly scoped local helper later.
- Optional local test helper must have fixed allowlist of commands and test IDs, no accepting arbitrary shell or user-supplied commands through HTTP.
- No user accounts/auth required on loopback; avoid binding on 0.0.0.0 without explicit user choice. No telemetry, no API keys, no background polling.
- Support offline browsing of local lessons and progress; external reading links naturally need internet.
- Backup/restore SQLite + export/import JSON/CSV, with versioned schema and migration validation; never silently overwrite progress.

## 10. Minimal suggested database
`modules` (curriculum metadata imported read-only), `lessons` (content index), `assessments` (rubric, version, test IDs), `attempts` (timestamp, assistance, result, reviewer), `evidence` (type, topic_id, path/hash/score/verification, assessment version), `mastery` (verified/provisional levels, last_verified, review_due), `reviews` (schedule/result), `learning_sessions` (notes, handoff import), `goals` (focus, active milestone), `knowledge_debts` (gap, project, linked topics, urgency), `source_refs` (title/URL/chapter/checked date).

Persist **assessment rubric version** beside attempts, so future curriculum/content updates do not rewrite prior history. Use IDs as stable references. Version imports and handle duplicate evidence deterministically.

## 11. Recommended learning sequence
Foundation track and project-driven track coexist. Start with an independent baseline diagnostic (not one giant exam). Seed initial pathways:
M01->M02->M03, PY01->PY04, CPP01->CPP02, RS01->RS02, then develop mathematics + kinematics/control and ML/Vision/RL branches by dependencies. See `CURRICULUM_GUIDE.md` for milestone map.

## 12. MVP implementation boundaries
### Phase 1 — Vertical slice (actual first build)
- Local app starts reliably, shell navigation for Dashboard/Roadmap/Lesson/Assessment
- DB + durable progress/backup
- Load and validate graph, filtered list, details and prerequisites
- ONE fully authored sample module: **M02 Vectors**, including M01 minimal prerequisite diagnostic; 1 lesson, 1 quiz, 1 lab, 1 transfer task, 1 review event
- Manual evidence with assistance flags, verified vs provisional, recommendation of next lesson
- Copy-to-ChatGPT handoff

### Phase 2 — Core learning engine
- Additional sample modules: PY01/PY04, M03, CPP01/CPP02, R03/R04, ML01, RL01 with real content not boilerplate
- Structured tests and importable test reports, record versioned assessment contracts
- Richer recommendation and daily reviews, knowledge debt tracker

### Phase 3 — Expansion
- Curated lessons added in batches, per-batch content QA; WBR application labs
- Optional local helper for tests, advanced visualizations / graph view, research lab

Do not auto-generate 170 lessons as filler. Prioritize a few accurate, well-tested lessons.

## 13. Definition of Done / acceptance criteria (MVP)
1. On new install, every module is visibly **Unassessed**; no fake completion.
2. Module JSON imports with unique IDs and DAG validation; invalid deps or cycles fail with meaningful message.
3. App works on localhost and stores durable progress after restart.
4. A student can open M02, read explanation, attempt quiz/lab, save evidence (A0), and see exactly which gates remain.
5. Copy Learning Context produces valid versioned handoff without answer keys.
6. Pasting ChatGPT summary **cannot** create VERIFIED status.
7. Wrong critical misconception blocks concept verification despite total >=80%.
8. An A3 lab answer cannot count as independent implementation; a separate A0 retest can.
9. The next-step recommendation explains why M03 is suggested after verified prerequisites and why other modules are blocked or deferred.
10. Backup/export can restore to a fresh database without losing evidence provenance; deleting notes cannot silently change verified evidence.
11. A poor network connection does not prevent reading local lessons or using the tracker.
12. Accessibility: keyboard navigation, usable focus states, good contrast, comfortable math/code reading.

## 14. Approved UI
The user answered all 15 design questions on 2026-10-30. The binding interface requirements, tokens, wireframes and acceptance checks are in `UI_DESIGN_SPEC_V1.md`. In particular, **dark-mode only** supersedes the earlier warm-light default; dashboard includes both immediate next action and competency overview. Do not add a light-mode toggle in the MVP.

## 15. Out-of-scope promises
- No assertion of real educational mastery beyond recorded evidence.
- No direct sync to ChatGPT unless user later explicitly chooses an integration method.
- No direct integration with actual robot motors; safety-critical tests must use appropriate controlled setup.
- No auto-publishing user notes, source code, private research files or uploads.

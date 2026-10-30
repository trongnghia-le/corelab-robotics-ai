# CORELAB SETUP KIT v1.0 — 30/10/2026

## What this is
A ready-to-use ChatGPT Project setup pack + CoreLab official product/functional specification + approved dark-mode UI design spec + machine-readable full curriculum graph. This is NOT a coded web application and does NOT create a ChatGPT Project automatically.

## Step 1 — Set up ChatGPT Project manually
1. In ChatGPT sidebar, select **New project**.
2. Name: `CoreLab | Robotics, Vision & RL`. Choose orange project color and a simple book/brain icon.
3. Open `••• > Project settings` and paste **all** text from `chatgpt_project/PROJECT_INSTRUCTIONS_PASTE.txt` into Project instructions.
4. Set **Project-only memory** if you prefer this project to use only its own chats/files; check the current Projects UI for available settings.
5. Add as project sources these four compact files:
   - `chatgpt_project/STUDENT_CONTEXT.md`
   - `chatgpt_project/CURRICULUM_GUIDE.md`
   - `chatgpt_project/LEARNING_AND_MASTERY_POLICY.md`
   - `chatgpt_project/SESSION_HANDOFF_TEMPLATE.md`
   Optional: `reference/LEARNING_SOURCES.md`.
6. You may add personal books you legitimately own where permitted; not required to begin. Use specific chapter links or excerpts rather than assuming the whole book is available.
7. Start your first project chat: `Hãy bắt đầu ở trạng thái Unassessed. Kiểm tra đầu vào thật ngắn về M01 (Mathematical Basics), chưa cung cấp đáp án trước khi tôi thử.`

ChatGPT Project does not directly sync with local CoreLab and no LLM API is used by the web. This workflow relies on copying learning context and session summary.

## Step 2 — Review spec
Read `corelab/PRODUCT_SPEC_V1.md`, `corelab/curriculum_graph_v1.csv` and `reference/LEARNING_SOURCES.md`.

## Step 3 — UI approved (2026-10-30)
Review `corelab/UI_DESIGN_SPEC_V1.md` for the accepted orange/dark appearance, layouts and wireframes. The UI questionnaire is kept only as a decision record. **No website has been built yet.** Next action: prepare Codex implementation prompt after reviewing this spec.

## Directory
- chatgpt_project/ — instructions to paste and reusable knowledge sources.
- corelab/ — requirements, approved UI specification + wireframes, UI questionnaire history, versioned curriculum graph JSON/CSV.
- reference/ — curated resources.

## Policy summary
Zero assumptions; P0 deep, P1 applied, P2 frontier; assess C/M/I/T with evidence; ChatGPT feedback not official mastery; curriculum is lifelong map, not all mandatory; local, single user, no cloud, no subscription, no API.

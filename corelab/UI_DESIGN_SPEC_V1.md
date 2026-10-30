# CoreLab — UI Design Specification v1.0

**Date:** 2026-10-30  
**Status:** User-approved direction from 15 UI questionnaire answers; ready for wireframe + implementation planning.  
**Product:** Local, single-user, no paid LLM API, dark-mode-only learning workspace.

## 1. Decisions & exact survey mapping

| Question | Choice | Interpreted requirement |
| --- | --- | --- |
| 1 | A | Energetic orange `#F97316` accent |
| 2 | B | Initially warm off-white background, **superseded by Q11** (dark mode only); preserve warmth through orange accents, not cream surfaces |
| 3 | A | Linear / Notion-inspired, content-first, restrained |
| 4 | A | Persistent left sidebar on desktop |
| 5 | A and B | Dashboard combines immediate next lesson with competency/gap overview |
| 6 | C | Roadmap supports list and graph; list is default |
| 7 | A | Reading column centered with TOC on right |
| 8 | B | Medium density; clear hierarchy and comfortable spacing |
| 9 | C | Mastery matrix by Concept (C), Math (M), Implementation (I), Transfer (T) |
| 10 | A | Modern technical textbook; readable equations and code |
| 11 | custom | Dark mode only; no light theme toggle in MVP |
| 12 | A | Desktop-first; phone for reading and progress, not coding |
| 13 | B | Subtle hover/focus transitions; avoid decorative animation |
| 14 | A | Prioritize Dashboard, Lesson, Assessment (Roadmap still usable) |
| 15 | A | No need for reference websites; design from approved requirements |

**Design statement:** A quiet technical study workspace that makes the next learning action obvious. The most important hierarchy is *do next → see evidence → understand gaps*; progress is not presented as an arbitrary completion percent.

## 2. Color system — preliminary design tokens

- `--bg`: `#0D0F12` — viewport
- `--surface-1`: `#14171C` — sidebar and header
- `--surface-2`: `#1B1F26` — cards/raised controls
- `--surface-3`: `#232831` — hover/selected-neutral backgrounds
- `--border`: `#2B3038` — subtle dividers
- `--text`: `#F3F4F6` — headings and body
- `--text-muted`: `#A7AFBD` — secondary descriptions
- `--text-subtle`: `#818A99` — tertiary text; not for critical information
- `--primary`: `#F97316` — primary CTA, selected navigation
- `--primary-hover`: `#FB923C` — hover/focus accent
- `--primary-on`: `#151009` — text on filled orange control
- `--success`: `#4ADE80` — verified success only, paired with text/icon
- `--warning`: `#FBBF24` — review due; paired with text/icon
- `--danger`: `#F87171` — failed checks; paired with text/icon

Color semantics:
- Orange indicates **current focus or action**, not competency mastery.
- Verified status must show `Verified Lx` + icon/text (not green alone).
- `Unassessed` remains neutral, not 0%, red, or failing.
- Provisional/self-reported state is visibly distinct from verified state.
- Highlight only one primary orange CTA per major panel.
- Body text contrast target >= 4.5:1 and focus visibility >= 3:1 where applicable; check real rendered colors before release.

## 3. Typography, spacing and responsive behavior

- Typography: `Inter` or system sans stack (`system-ui`, `Segoe UI`, etc.). No font-file redistribution.
- Base body: 15–16 px (default 16); line height 1.65–1.8 in long reading; headings 22–30 px depending on location.
- Lesson content max width 760–820 px. Markdown headings, math blocks, images and code must not overflow reading column.
- Code font: local monospace stack (e.g. `ui-monospace`, SFMono, Consolas).
- 8px spacing scale: 4/8/12/16/24/32; cards radius 10–12px; limited shadows.
- Desktop sidebar width ~232px, fixed/sticky; page workspace flexible. Right lesson TOC max ~208px.
- At mid widths, hide/collapse TOC before main content becomes cramped.
- At phone widths, sidebar becomes an accessible drawer, reading column full-width; quizzes remain readable, local coding task is opened in external VS Code/terminal rather than embedded in phone UI.
- Animations: 120–180ms for hover/focus/collapse, respect `prefers-reduced-motion`.

## 4. Information architecture

Primary navigation, 4 links:
1. `Dashboard` — today + competency overview
2. `Roadmap` — domain list + graph toggle
3. `Lessons` — search/filter & lesson reading (routes may deep-link directly)
4. `Assessments` — active tasks, rubric, evidence, reviews

Secondary: settings (local backup, import/export), source credits, optional future knowledge debt. No login, profile, pricing, social, leaderboard, streak pressure, or artificial gamification.

## 5. Screen contracts

### Dashboard (priority 1)
Above fold shows two distinct purposes requested in Q5:
- **Next action** prominent: lesson title, why recommended, duration, `Continue Learning` CTA; max three recommendations overall.
- **Competency snapshot** adjacent or immediately below: seven long-term domains + research skills; statuses as text, not fake percentages; highlight top 1–2 actual gaps.
Then: review due, last session/resume, blockers/next prerequisite, compact recent evidence. If user just installed, show `Not assessed` and a single diagnostic entry instead of fabricated progress.

### Roadmap
- Default **list/tree**, expandable by domain > module > lesson, with search, P0/P1/P2 filter, and status pills.
- `Graph` toggle shows **only selected domain or focused dependency chain** by default, never a wall of 169 nodes. Clicking a node opens prerequisite/next links and status.
- Graph is optional for first implementation vertical slice; list must be complete and correct.

### Lesson workspace (priority 2)
- Left app sidebar; **centered main content**; right sticky TOC on widescreen.
- Top: breadcrumb, module/topic ID, one-sentence learning objective, prerequisite chips, estimated time.
- Ordered content: Why → Intuition → Theory + assumptions → Math derivation → Worked example → Failure modes → Independent practice → Assessment → Variants/Trade-offs → References.
- Text/equations are first-class. Inline code and block code with copy affordance; link to external VS Code practical task. No web-embedded IDE in MVP.
- Inline `Copy learning context for ChatGPT` action with explicit manual copy. This never marks completion.
- Deep reading state (reading completed) is separate from competency state.

### Assessment (priority 3)
- Four-column or four-row competency matrix: C/M/I/T, each of `Unassessed`, `Needs evidence`, `Provisional`, `Verified Lx`, `Review due` as applicable. Not every lesson requires Mathematics: show `N/A` with explanation.
- Show explicit gate/checklist for current target level, latest evidence, help level (A0–A3), and retest requirements.
- One primary action: `Start / Continue Assessment`; task may open with question/inputs/local-test instructions.
- Error states explain which assumption or item failed, not a vague score.
- AI-supplied solution (A3) never automatically certifies independent implementation or transfer.

## 6. Microcopy and accessibility

- Site language Vietnamese; technical terms stay in English when useful. Examples: `Tiếp tục học`, `Chưa đánh giá`, `Đã kiểm chứng L2`, `Cần ôn tập`, `Vì sao học bài này?`.
- Keyboard navigable sidebar, roadmap, quizzes; visible focus rings; proper labels and semantic form elements.
- Use icons sparingly and never as sole state indicator.
- Friendly but matter-of-fact empty states: `Chưa có bài đánh giá. Bắt đầu với M01.`
- Avoid overwhelming celebratory animations, urgent countdowns and arbitrary streaks.

## 7. Wireframes — desktop, not-to-scale

Dashboard:
```text
┌──────── Sidebar ─────────┬───────────────────────────────────────────────────────────┐
│ CORELAB ●               │ Dashboard                                                 │
│                         │ Hôm nay nên học gì?                                       │
│ ▸ Dashboard             │ ┌───────────────────────────────────────────────────────┐ │
│   Roadmap               │ │ ĐỀ XUẤT: M02 — Vectors & Norms                        │ │
│   Lessons               │ │ Vì sao: tiền đề cho phép biến đổi tọa độ             │ │
│   Assessments           │ │ [Tiếp tục học]                     25–35 phút        │ │
│                         │ └───────────────────────────────────────────────────────┘ │
│                         │ ┌──────────── Năng lực ──────────┐ ┌── Những điểm cần ──┐ │
│                         │ │ Math            Chưa đánh giá  │ │ M01 diagnostic    │ │
│                         │ │ Robotics        Chưa đánh giá  │ │ Ôn tập: chưa có   │ │
│                         │ │ Vision          Chưa đánh giá  │ └───────────────────┘ │
│                         │ │ RL              Chưa đánh giá  │                       │
│                         │ └───────────────────────────────┘                       │
└─────────────────────────┴───────────────────────────────────────────────────────────┘
```

Lesson:
```text
┌── Sidebar ────┬────────────────── Lesson (center) ──────────────────┬─ TOC ─────────┐
│ Dashboard    │ M02 / Vectors & Norms                                 │ Why          │
│ Roadmap      │ Tại sao học?                                         │ Intuition    │
│ Lessons      │ Intuition & geometric examples                         │ Theory       │
│ Assessments  │ Theory, assumptions, formulas                          │ Derivation   │
│              │ Derivation + math                                     │ Practice     │
│              │ Example → independent exercise                        │ Assessment   │
│              │ [Copy context to ChatGPT] [Open practice instructions] │ Sources      │
└──────────────┴───────────────────────────────────────────────────────┴──────────────┘
```

Assessment:
```text
┌── Sidebar ────┬──────────────────────── Assess M02 ───────────────────────────────┐
│              │ Your evidence:                                                  │
│              │ Concept        [Unassessed]                                     │
│              │ Mathematics    [Unassessed]                                     │
│              │ Implementation [Unassessed]                                     │
│              │ Transfer       [Unassessed]                                     │
│              │ Target: L2; requirements: concept quiz + vector lab + tests      │
│              │ [Start Assessment]                                              │
│              │ Notes: assistance level A0/A1/A2/A3; no self-certification      │
└──────────────┴──────────────────────────────────────────────────────────────────┘
```

## 8. Implementation and acceptance gates

1. Theme always dark, orange accent; no light theme toggle.
2. Desktop app sidebar stays visible, no horizontal scrolling at normal laptop widths.
3. Dashboard exposes both a next action AND genuine competence/gap overview without requiring a second page visit.
4. Lesson is comfortable for 30-minute reading sessions; TOC stays usable; formulas do not clip.
5. Mastery matrix C/M/I/T is clearly visible; verified vs provisional differentiated by text.
6. List roadmap is functional; graph view may be deferred with clear messaging and must not be a broken placeholder.
7. Typography contrast, keyboard focus, reduced-motion are respected.
8. Empty states are truthful (all skills unassessed initially).
9. No APIs, analytics, cloud sync, or login added without user request.
10. Next Codex prompt must refer to this spec and to `PRODUCT_SPEC_V1.md` as authoritative requirements.

## 9. Open implementation details, not user-facing decisions

- Icon pack (Lucide or similar)
- Chart/graph library if graph view enters MVP
- Database ORM vs minimal SQLite driver
- Exact page route names

Codex may select the simplest robust option, with documented trade-offs; do not reopen user-approved design decisions.

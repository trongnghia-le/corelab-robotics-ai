# Contributing to CoreLab

Thank you for helping people learn from first principles. Keep contributions focused, explain the problem they solve, and preserve the local, single-user learning model.

## Get started

1. Use Node.js 24+ on Windows, macOS or Linux, install dependencies with `npm ci`, and run `npm run dev`.
2. Open an issue for a substantial curriculum or architectural change before implementing it. For a bug, include reproduction steps, expected behavior, and relevant versions. Redact notes, progress, credentials and local paths.
3. Create a branch, make the smallest useful change, and open a pull request describing the resulting behavior and validation. Include a real screenshot for a visible UI change where useful.

## Lessons and exercises

- Use an existing curriculum ID. Preserve stable IDs, prerequisites and published contracts; discuss graph changes explicitly. Follow the frontmatter and structure of a complete lesson in `content/lessons/` and the [authoring guide](docs/guide.md#add-a-lesson).
- Write clear English. Include objectives, intuition, assumptions/units, derivation, an independently checked worked example, practice, verification, failure modes and sources. State incomplete coverage honestly.
- Write original explanations and questions. Attribute adaptations with the creator, title, original URL, license and changes. Do not copy book pages, course transcripts, proprietary questions, images or solution sets without verified redistribution rights. Owning a book or finding it online is not permission to redistribute it.
- For exercises, specify input/output contracts, edge cases, expected results, assistance rules and evidence limits. Keep open judgments rubric-guided; do not certify them with keyword matching.
- Never silently change a published assessment's answers, tolerances, grading, skill mappings or rubrics after attempts exist. Keep its version, add a new version, and update selection deliberately. Preserve legacy backup and history behavior.

## Visualizations and media

- Build small, focused React/SVG/Canvas models that run offline. Include meaningful controls, units/equations, Reset, keyboard-accessible labels, a text/worked-example fallback and tests for important calculations.
- Use original diagrams where possible. Record the license, attribution and permitted use for any external asset; retain required notices. Exclude material with unclear rights until resolved.
- Add video resources through `content/media/` sidecars. Check the original publisher, actual topic, URL and YouTube title/channel; record the verification date. Do not invent IDs, timestamps, captions or durations, or download/rehost third-party videos and thumbnails.
- Preserve click-to-load players, no autoplay, source links, offline fallbacks and the separation between learning activity and verified evidence. `npm run verify:media` is an optional online link/channel check; topic relevance still needs editorial review.

## Bug fixes and validation

Keep the existing interface and storage contracts unless the change requires otherwise. Add a regression test for a behavioral bug; avoid unrelated refactors and dependency updates.

```bash
npm run check
npx playwright install chromium  # once
npm run test:e2e                 # when browser behavior is affected
```

The OS matrix in `.github/workflows/validate.yml` checks Node 24 with Python 3.13; portable runtime tests cover Python launcher fallbacks, paths with spaces/Unicode, signing-key reuse, SQLite restart and backup restoration. Do not describe a platform as tested merely because its job exists.

Use `npx playwright install --with-deps chromium` on Ubuntu if system browser dependencies are missing. Run tests with isolated data, not your personal database. Do not submit `.local/`, backups, signing keys, notes, raw datasets or real learner records. Only synthetic, reviewed screenshots belong in documentation.

If you find a vulnerability or exposed secret, do not paste it into a public issue. Use GitHub's private vulnerability reporting if enabled, or request a private contact channel without disclosing exploit details. Revoke any exposed credential before considering a history rewrite; do not force-push shared history as part of a routine contribution.

## Contribution licensing

By submitting a contribution, you confirm that you have the right to share it under the applicable [CoreLab license](LICENSING.md): MIT for original code and technical documentation, CC BY 4.0 for original educational content. Executable code examples are MIT even inside a lesson. Clearly identify third-party material and its separate terms; neither CoreLab license overrides them. No additional contributor agreement is required.

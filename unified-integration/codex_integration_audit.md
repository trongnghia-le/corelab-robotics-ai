# CoreLab V2 — independent integration audit

**To Claude: audit complete; changes required before implementation.** Please incorporate the dispositions below into `CORELAB_V2_UNIFIED_SPEC.md`. No routine additional debate round is requested. Resolve B-01 and B-02 explicitly rather than treating an open owner decision or an unimplemented check as an accepted security guarantee. If signed, same-user execution is retained as protected verified I, the critical contradiction in B-01 remains.

**Scope:** actual repository plus all three finalized proposals and `claude_unified_design.md`. Date: 2026-10-31, Asia/Saigon. No production changes, content/assessment edits, database migration, real evidence import, commit or push.

**Reviewed input snapshot:** repository HEAD `38b6a1d8f0baae9a753882185da7bd4430d14277`, including the pre-existing `next-env.d.ts` working-tree change.

| Input | SHA-256 |
| --- | --- |
| [Claude unified draft](claude_unified_design.md) | `6ab8b7897f5d20d54be12758ffc4e18f7883e33cef5acf17e15fe06c5537ddee` |
| [Curriculum V2](../curriculum-review/proposed_curriculum_v2.md) | `31a45e6d3e34b5e09e4c613474d1eefc494d603a7391e835630699777cfd6dc7` |
| [Practical Learning System](../corelab-labs-review/proposed_practical_learning_system.md) | `8d32d26c2f85db214572ad55e7a1770155f711affa1acf8d7da68dc0e4de012e` |
| [Exercise Bank](../exercise-bank-review/proposed_exercise_bank.md) | `f60a523b73185cdc92457246dfd19decdd919ac307e19a9f8252cd3c290c5d76` |


## 1. Verdict

The proposed objective layer is a sound integration direction: keep legacy scoring and evidence identities, add versioned objective-level records, make learning activities optional, and start with numerical Frames/planar FK. The design correctly distinguishes an authored mapping from an available lab, retention from unfamiliar transfer, and practice from topic mastery. Keeping ROS, physics and hardware outside the pilot is appropriate.

It is **not yet an implementation-ready specification**. The main gaps are the trust boundary for new I evidence, missing issued-attempt/exposure state, and incomplete migration/restore contracts. These can be repaired without rebuilding the application or adding a service platform. P1/P2 can be useful while automatic I remains unavailable.

Severity is scoped to the affected feature:

- **BLOCKER:** implementation as written can violate a central evidence/security invariant; resolve before the affected verification stage.
- **MAJOR:** a necessary interface, persistence contract or correctness condition is missing or wrong; resolve before the affected feature ships.
- **MINOR:** inaccurate wording or avoidable scope growth; does not block numerical practice once higher-priority items are resolved.

A proposal need not already implement every component. The findings identify decisions that the final specification must settle; they do not claim nonexistent V2 code has been exploited.

## 2. Findings and required fixes

| ID | Severity | Affected stage | Finding |
| --- | --- | --- | --- |
| B-01 | BLOCKER | P3 verified I | `local-trusted` cannot protect the parent key/database or guarantee parent-owned evidence against submitted code. |
| B-02 | BLOCKER | P2 verification | Freshness, observed assistance and issue/abandon/submit transitions have no durable attempt/exposure contract. |
| M-01 | MAJOR | First V2 write | Sidecar schema versioning and rollback need a compatibility guard and explicit cross-version restore semantics. |
| M-02 | MAJOR | P1 persistence | Full V2 backup, snapshot and transactional restore must arrive with the first durable V2 data. |
| M-03 | MAJOR | Restore/import | Signature validity, issuer trust and objective admissibility must remain separate, including on backup restore. |
| M-04 | MAJOR | Backup/restore | Exportable/valid history can exceed the existing HTTP restore limit. |
| M-05 | MAJOR | P1 content | Pilot references contain a nonexistent visualization and an undefined readiness bridge. |
| M-06 | MAJOR | P2/P3 | Report scope, replay/idempotency and retention admission interfaces are incomplete. |
| M-07 | MAJOR | Auto-checked items | Published fixture checks accept malformed SE(2) output and nonfinite FK orientation. |
| M-08 | MAJOR | P1/P2 integration | API contracts, reproducibility references and bounded local-history access need a small explicit contract. |
| N-01 | MINOR | Final specification | Remove unperformed-test/completed-fix wording; make the feature flag's behavior exact. |
| N-02 | MINOR | Pilot scope | Defer unused general graders and advanced pathway machinery. |

### B-01 — A different launch button does not create an evidence boundary

**Design:** §3 item 1; §7.3; §9; D2; AC-8. **Verified repository facts:** `scripts/lab-tests.py:5–7` imports submitted code into the tester; `scripts/verify-lab.mjs:49–54` accepts a successful process and its last stdout JSON. The unchanged harness accepted a synthetic module printing `{"passed":true,"checks":8}` and exiting 0. I did not invoke the signing CLI or import that result.

**Critical design contradiction:** the completed Exercise Bank proposal §8 requires host/key separation for automatic verification. The unified draft instead allows a same-user, unisolated CLI to produce “verified I,” reasoning that the owner can edit the application anyway. A trusted device owner and each submitted process are different trust decisions. Code inside the worker can read the private key/database or alter trusted inputs; keeping a key outside its temporary cwd and scrubbing environment variables does not deny access. A signature then authenticates access to that key, not that the parent completed the approved checks. This matters to the stated requirement to reject forged learner output independently of remote-exam or authorship claims.

**Executed boundary demonstration:** a child process with an empty environment, private temporary cwd and Python isolated-mode flag still read a benign mode-0600 marker outside its cwd. This used only an audit marker, not a real key or database. It is a property of the proposed same-user boundary, not a reproduction against the unimplemented new runner.

**Fix:** keep three tiers, but make manual/self-attested checks **unverified practice/artifacts**, without protected verified-I admission. Ship P1/P2 with I clearly unavailable. Admit automatic I only through a reviewed execution profile that keeps keys, parent policy, host state and verdict construction out of the worker's reach. Fail closed when that profile is unavailable; no silent unisolated fallback. The Linux prototype is supporting research, not a production sandbox certification or Windows/macOS solution.

An owner may deliberately approve a weaker “trusted local self-check” product policy later. That must be a separately named claim and threat model, not silently equivalent to the completed Bank's protected automatic verification. Do not price the draft's 15–30-hour P3 estimate as implementing the stronger boundary. No sandbox is required to offer numerical answers or reviewed manual kits.

### B-02 — Evidence needs a persisted attempt before the answer exists

**Design:** §5.2, §6.1, §8 and §9. **Verified:** proposed `practice_events` stores completed answers/outcomes; `evidence_records` stores final results. No table or interface is defined for issued/abandoned forms, immutable instance inputs, hint openings or maximum observed assistance before submission. A hash is not the underlying instance. This is a specification gap, not a claimed deployed bypass.

**Consequence:** open a form, reveal a hint/solution, abandon it, then reload and submit. The admission policy requires prior exposure to disqualify that form and observed help to remain monotonic, but the design does not say what durable record enforces either rule. A different form/route ID or purpose must not make identical exposed content “fresh.” A client-provided `fresh` or `observed_assistance` field is not evidence of those facts.

**Fix:** add a minimal server-owned attempt lifecycle, not a general event platform:

- Issue an attempt ID tied to purpose, objective **version**, source/family/form version, route, generator/configuration version, immutable bounded instance data and a semantic content fingerprint.
- Persist issuance/exposure immediately. Record observed hint/solution exposure monotonically, separately from declared external help; abort/reload never clears it.
- Freeze the attempt's source/policy; submit closes it once. Duplicate identical submission is idempotent; changed submission to a closed attempt is rejected or explicitly starts a new attempt.
- Keep purpose outside the semantic freshness fingerprint. Define cross-route/form exposure equivalence through reviewed scope relations, not independent exposure namespaces that cannot see one another.
- Derive effective assistance, freshness, grade and admission on the server. Back up/restore issued attempts and exposure records with the other V2 data.

Public local content still cannot prove independent authorship. This change makes the system honor its own observed-help/history claims, including ordinary abandoned sessions.

### M-01 — `user_version=2` alone is not a V2 migration protocol

**Design:** §6.1 and AC-3. **Verified:** `lib/storage.ts:166–179` initializes SQLite pragmas, rejects `user_version>2`, then creates legacy tables and sets 2. An old V1 binary can ignore additive tables; that is a plausible compatibility choice. It does not establish that an older **V2** binary can safely write a later sidecar schema, or that legacy restore while downgraded leaves one coherent history.

**Fix:** define an independent integer sidecar schema version, ordered migrations and an explicit supported read/write range. Check it before V2 writes; unknown/newer sidecar versions fail closed for V2 or offer a read-only legacy view. Run each sidecar migration and its metadata update transactionally. `CREATE TABLE IF NOT EXISTS` is not a column/schema upgrade strategy.

Define rollback as a supported **legacy-view mode**, not complete V2 rollback. An old app can edit/restore `state` while leaving V2 rows untouched. On return, detect and explain this mixed-history condition, using a legacy-state generation/fingerprint or equivalent checkpoint; preserve both histories without silently treating the older backup as a full restore. Test V1 → V2 → V1 edit/restore → V2, not only that the old binary opens the file.

Keeping the old graph for the pilot is a valid scope decision. Changing current navigation edges would not inherently broaden an old signature; preserve graph versions and claim scopes rather than suggesting those are inseparable.

### M-02 — Back up the first data you persist

**Design:** §6.2 and stages P1/P2. **Verified:** current `Store.restore` validates before `Store.update`, snapshots only legacy `state`, then replaces it in a transaction (`lib/storage.ts:226–235`). The draft makes P1 independently shippable with durable practice tables, but lists full `/3` backup under P2. A P1 learner's existing export cannot carry their new practice/exposure history.

**Fix:** include a full V2 export and restore contract in the first stage that persists V2 data, or explicitly keep that stage disposable and avoid promising persistent progress. Make full backup the default when V2 data exists; offer `/2` as a clearly labeled **legacy-only** export. A notice after losing data is not a round-trip guarantee.

For `/3`, specify exact shape, supported versions and bounded sizes; export all stores from one consistent read transaction, and validate all legacy/V2 references and admission inputs before replacement. Snapshot the complete pre-restore state, sidecar metadata, attempts/exposures, events, evidence, reviews and prefs. Replace all affected collections and the snapshot atomically. Any validation/write failure leaves all stores unchanged. Define duplicate IDs, unknown content/policy versions, missing artifacts and incompatible sidecar versions.

A `/1` or `/2` import can intentionally restore only legacy history, but the preview must explicitly show that V2 history is retained and what that means. Do not describe it as restoring the entire learning profile. Exact legacy report strings/signatures and assessment versions remain preserved; derived validation fields need not be falsely promised byte-identical to untrusted input.

### M-03 — A valid signature does not enroll an issuer

**Design:** §6.2 delegates legacy validation; §9 pins live imported I reports to a local key. **Verified:** `validateBackup` calls `validateLab(report)` without `requireLocalKey` and then sets `trusted=true` (`lib/storage.ts:134–144`). Live lab import uses `validateLab(report,true)` (`lib/actions.ts:123`). These are intentionally different existing paths, and `tests/storage.test.ts` covers them.

**Executed:** a synthetic report signed by a newly generated, in-memory throwaway key was accepted by `validateBackup`; a supplied `trusted:false` became true, and the legacy engine assigned I2. No real key, signing CLI, disk database or live import was used. This does **not** refute the documented local-owner trust model or justify changing historical records in this audit. It shows that embedded-key validity is not workspace-issuer approval.

**Fix:** new `/3` restore must not admit V2 evidence merely by copying `result=passed`, a serialized trust flag or a self-contained public key. Separate signature validity, recognized issuer provenance, recognized contract/profile and objective eligibility. Specify workspace key continuity and fresh-install/foreign-key restore behavior. Preserve unverifiable or unapproved historical artifacts with honest status rather than deleting them or upgrading trust silently. Do not export private keys in learning backups.

Recompute C/M outcomes from the retained recognized form/instance/answers where possible; verify original I report signatures and contract/profile/issuer rules; validate review references. Keep legacy evidence on the legacy track with its original limitations. No new authentication system or global certificate authority is needed.

### M-04 — Current backup limits disagree with current restore limits

**Design:** §6.2, AC-4. **Executed:** 405 valid 20,000-character notes produce an 8,141,819-byte `/2` document accepted by `validateBackup`. The action handler rejects bodies above 8,000,000 characters (`app/api/action/route.ts:10–11`); `checkLocalRequest` also checks declared Content-Length against 8,000,000 bytes (`lib/http.ts:21`). New V2 history increases this gap.

This is a current contract mismatch plus a future integration risk, not a browser restore test. I validated the synthetic document and compared its size with the inspected handler limits; no HTTP service or large real backup was touched.

**Fix:** define compatible export/import byte, record and artifact limits before `/3`; enforce UTF-8 bytes consistently, including requests without Content-Length. Ensure every supported full export is importable through the advertised local flow, or refuse creation with an explicit bounded policy before presenting it as a full backup. Use a dedicated bounded restore path if necessary; do not simply allow unlimited JSON. Keep raw datasets/recordings outside SQLite. Test near/over limits, non-ASCII data and failure-without-partial-replacement.

### M-05 — Correct the actual media and readiness references

**Design:** §2 calls `frames` a visualization; §5.2 uses `{ "visual": "frames" }` for FK and references `M01.radians`; §5.3/§12 promise five objectives using existing lessons unchanged.

**Verified:** `frames` is an **illustration** ID (`lib/media.ts:20–26`), not one of the eight visualization IDs (`:10–19`). The FK visualization is `forward-kinematics`, rendered by `components/learning-visual.tsx:49–50`. The existing `forward` teaching model returns elbow/tip only (`lib/visualization-math.ts:18–28`), not a complete pose or grader. `M01.radians` is absent from the five-objective mapping, and the current M01 lesson teaches notation/functions/units without the required trigonometry bridge. The Curriculum proposal explicitly identified that gap.

**Fix:** use typed references that distinguish illustration, visualization, lesson anchor, objective and candidate topic. Map FK to `forward-kinematics`; use `frames` as an illustration, with a numeric/table alternative where needed. Author a tiny radians/sin/cos/unit-readiness bridge and a diagnostic reference, or explicitly assume that readiness and route learners to a verified specific resource; do not mark it present in M01 today. All hard/soft readiness references must resolve, be versioned and cycle-checked separately from the unchanged topic graph.

Keep Frames and FK independent of Jacobian/PoE/ROS prerequisites. A transform-chain route may need matrix-composition readiness that a direct-trig FK route does not. Ordinary exploration remains open; lack of readiness changes recommendations/warnings, not topic history. The existing dashboard's V1 prerequisites must be clearly distinguished from the new objective recommendation reasons.

### M-06 — Finish report, coverage, replay and review admission contracts

**Design:** §7.1, §9, §10 and known limits. A schema name and “contract matches objective” are not enough to implement a trusted importer. The draft also admits only known forms/contracts in §9, while allowing `source_kind=review` and generating retention from practice family X11.

**Fix:** finalize a small discriminated contract before P3. An eligible I artifact must bind an allowlisted contract and version/hash, objective-version coverage, execution profile/pathway/mode, exact submission/input/config hashes, runner/oracle version, parent completion/exit/limit outcomes, required per-objective checks, assistance/exposure references and original signed payload/issuer. Parent derives coverage and verdict; child fields never grant them. One L01 result grants only the I scopes whose required subchecks completed—not every topic/objective linked to L01.

Specify signature serialization/canonical bytes once for the new format; preserve legacy serialization unchanged. Define exact contract-hash mismatch, duplicate report, duplicate closed-attempt and replay behavior. Importing the same report twice must be idempotent or rejected without creating a second pass/review advance. Unknown/unsupported profiles and modes never acquire I eligibility by renaming fields. The importer treats report data as inert: it never executes it or follows report-supplied filesystem paths/URLs to read host artifacts.

For retention, issue a **review-purpose** attempt admitted through a known reviewed form/contract; do not promote an ordinary practice event. Record the exact objective version and delay basis, and do not call immediate “Review now” retention evidence. Define what a partial/assisted/failed review does to stage/due time, retaining unresolved objective gaps. Type `last_ref` so restore can prove it refers to a real matching source/objective. Unfamiliar transfer remains unreviewed without a recorded qualified judgement; no automatic L3/L4.

### M-07 — The feasibility harness has two false accepts

**Design:** §12.3/Appendix and AC-9/11. **Executed:** the published script reproduces its two valid implementations and seven rejected mutants for each contract. Additional probes show:

1. A compose function returning a **4×4** result with a correct 3×3 prefix passes `l01`: `eqm` reads only indexes 0–2 and checks no exact shape.
2. A FK function returning correct positions but **NaN orientation at stretched and folded poses** passes `l02`: those two cases check x/y and discard theta.

These are failures of the author-side fixture check, not attacks against a deployed V2 grader. The main anchor math, relative-angle equations and modulo-angle error formulation are correct on the published bounded fixtures.

**Fix:** validate every returned structure and every output field before numerical comparisons on **every** case. Exact shape, finite types and the stated boolean/error schema come first. Add the two probes to the required rejection suite, plus invalid shapes/values/link lengths, near-boundary rotations and nonmutation as the actual contract requires. Accept angle-equivalent orientations, validate determinant **and** orthogonality, and never silently repair malformed input. Keep normalized, bounded SI/radian domains and state tolerances/rounding requirements in the learner prompt; hiding oracle answers must not hide the precision the learner needs.

Two sample implementation paths do not complete expert/pedagogical/hostile-output review. Fixing this small harness is useful; release still depends on the approved full contract and separate reviewer gate.

### M-08 — Define the small interfaces the workflow actually needs

**Design:** §6.1, §7.1, §8 and §11 provide modules but not request/response contracts or bounded history queries. Practice rows also omit objective versions, immutable instance data and generator/configuration versions. A seed or instance hash alone cannot reproduce a case after content changes.

**Fix:** specify a minimal local API boundary: objective summaries; issue attempt; open hint/solution; submit; paginated history; inert report import; full backup/restore. Every write derives trusted fields server-side, validates size/schema and uses the existing localhost/origin restrictions. Server responses redact oracle answers; expose permitted answer formats, units and precision. No submission execution from any route.

Freeze source/instance/policy references in stored attempts and preserve needed old content versions or archived bounded contract manifests. Handle missing versions explicitly at restore. Define selection ordering/tie-breaks, exhaustion and combined legacy/new weakness reasons; do not mutate legacy weakness correction from unreviewed mappings. Include route alternatives for the same objective rather than mistaking different dimensions or seeds for equivalent tasks.

Keep selector inputs and responses bounded; use targeted SQLite indexes for objective/version/time and family/version/exposure lookup. Do not return full answer/evidence histories on each dashboard refresh or synchronously reparse every catalog per row. Measure a representative large permitted history on named hardware and set a pilot response/payload budget; no new performance result is claimed here. A pure selector, small SQLite transactions and static cached validated catalogs are sufficient—no queue, plugin runtime or universal robot middleware.

### N-01 — Distinguish proposed checks from executed results

§7.1 says the feature flag behavior is “Tested,” and §7.3 says the stdout defect “is closed in the new runner,” although §16 says the runner/storage/UI are not prototyped. Change these to **required acceptance conditions**, not completed verification. The executed evidence is the mathematical fixture script and earlier controlled prototype, with their limits.

Define `CORELAB_V2` exactly: default off; enabled value; server enforcement; disabled routes; when sidecar migrations/writes may occur. Default-off should not introduce new V2 writes or require V2 content to load. “Off means identical” needs integration checks, not just the unchanged baseline suite. Likewise, the actual repo can load a versioned diagnostic, but current attempt/UI routing defaults to v1; describe that routing limitation precisely.

### N-02 — Keep the slice smaller than the catalog

The proposed `set-of-valid` path grader, future robot model cards/imports and broad pathway adapters are not needed to deliver SE(2)/planar FK. Retain their reserved vocabulary and future constraints, but defer implementation. Start with the answer types the slice uses and one inert artifact interface. Do not build all 22 labs, 20 bank families, the 176-node graph migration or a generic capability engine as a prerequisite for the pilot.

## 3. Cross-proposal consistency and decisions to retain

| Area | Verified alignment / required interpretation |
| --- | --- |
| Curriculum | Canonical proposal is a 176-identity/319-edge DAG, preserving 169 existing IDs. Candidate identities are not current topics. The pilot can leave the graph unchanged while using clearly labeled advisory objective readiness. |
| Lab sequencing | The finalized lab/capstone projection is a 25-node/39-edge DAG. L01 precedes L02 in that chosen artifact sequence; IDs do not make all 22 labs compulsory. Topic/capability requirements remain additional, not automatically inferred from that DAG. |
| Bank choices | X10/X11 align with frame/FK preparation; X01 is optional support. Two authored routes per pilot objective are useful. Seeds, dimensions and tool variants are not automatically equivalent choices or transfer. |
| Legacy compatibility | New practice/evidence must not enter `Attempt` or `Progress.labs`. Current `masteryFor` can remain unchanged; old levels retain their legacy meaning. Objective evidence is a separate explicitly scoped read model. |
| Security | The later finalized Bank made automatic protected verification stricter than the older Labs report. The unified specification must choose a threat model explicitly; B-01 is not resolved merely by renaming a CLI. |
| Learner freedom | Learn/Practice/Apply/Verify/Review are available activities. The new selector should advise, never permanently lock ordinary study. Placement/readiness failures do not erase past attainment. Hardware approval is outside this numerical pilot. |
| Modes | Numerical/mock/replay/physics/hardware identify what was actually checked; they do not rank mastery or imply equivalence. No numeric/ROS result authorizes hardware. |
| Assessment | Fresh scoped C/M, separately admitted I, retention versus reviewed unfamiliar transfer, and A0–A3 remain distinct. Reading, sliders, AI answers and practice counts grant none automatically. |
| Licensing | Use original simple geometry, prompts and fixtures first; preserve MIT-code/CC-BY-content boundaries and per-item third-party notices. No simulator model/book/problem import is needed for this slice. |

**Reparsed facts:** both finalized graphs are acyclic with no missing references. Current R04 ancestry is `{M01,M02,M03,M04,M12,R01,R02,R03}`; the curriculum proposal's R04 ancestry is `{M01,M02,M03,M12,R03}`. The draft correctly identifies the current/desired distinction. Do not mix the two graphs and then call the resulting path canonical.

**Not established:** a full objective/exercise/lab mapping for every topic, equivalent learner difficulty across routes, reliable mastery thresholds, protected new runner, cross-platform new-code support or an implemented learning benefit. The existing topic-to-lab matrix cannot substitute for versioned objective coverage contracts.

## 4. A realistic Frames/FK vertical slice

### 4.1 Boundaries and data flow

Keep five proposed objective scopes: frame labels; point/direction distinction; compose/invert SE(2); proper-rotation validity; planar 2R position/orientation. Add the small explicitly authored readiness bridge required by M-05. No spatial chains, Jacobian/IK, simulator, robot, new topic graph or new numerical dependency is necessary.

Learner flow: open the objective from its topic or a recommendation → optional placement → read/watch/visualize or text fallback → choose X10/X11 route → attempt with optional hints → get typed numerical feedback → implement in a reviewed manual kit → use a separately issued fresh C/M form → repair a measured weakness → revisit a due review → receive a next objective suggestion. Each step is optional; the source of each status is visible.

**First shippable increment:** numerical practice, manual self-check kits, server-owned attempts/exposure, complete backup/restore and honest objective history. **Second:** separately reviewed C/M forms and objective review admission. **Later:** automatic I only after B-01 and the report contract are resolved. An I-unavailable state is an honest deliverable; it must not be shown as a completed verified implementation workflow.

The same versioned contract should connect prompts, instance data, allowed formats, feedback and visualization parameters. The existing FK demo can support intuition, but its default link lengths are 2 and 1.5, while the audit anchor uses 2 and 1. Parameterize/label that difference; do not silently compare a viewer with another task's model. The current demo is not the expected-output oracle or a pose verifier.

### 4.2 Acceptance criteria to add to the final specification

These are **proposed tests**, except the explicitly reproduced arithmetic and research scripts in §5. None is a claim that the V2 implementation already passes.

| Criterion | Testable acceptance condition |
| --- | --- |
| VS-01: content references | Every enabled objective, readiness, route, lab, source version, anchor and media reference resolves to the correct typed registry. Duplicate/cyclic/dangling readiness fails validation. `frames` resolves only as an illustration; FK resolves to `forward-kinematics`. |
| VS-02: freedom and navigation | Fresh learner and returning learner can directly open each enabled activity; lack of readiness produces a specific warning and optional bridge. Dashboard distinguishes legacy-topic suggestions from objective suggestions; no compulsory R01/ROS/Jacobian detour for this numerical objective. |
| VS-03: choice | X10 and X11 each offer two authored routes with the same declared core objective and clear differences. A fresh instance binds route/configuration and survives reload. Repeats and exhaustion are labeled; no generated replacement masquerades as reviewed content. |
| VS-04: attempts/help | Issue → open hint/solution → abandon/reload → resubmit cannot lower observed assistance or erase exposure. External AI help remains self-declared. Changing purpose, route wrapper or source ID does not make identical exposed content fresh. |
| VS-05: practice wall | Practice, manual kit output, reading, visuals and AI feedback create no admitted evidence. Legacy mastery is unchanged after all new activity. Server rejects client-supplied grades, freshness, coverage and effective assistance as authoritative. |
| VS-06: SE(2) anchor | Column-vector A rotates +π/2 and translates (1,2); B translates (3,−1). A·B has translation (2,5), maps point (1,2) to (0,6); A maps direction (2,0) to (0,2). Inverse A maps (1,4) to (2,0). Reversed order/translated direction fail. |
| VS-07: rotation/shape | Exact contract shapes and bottom row; finite non-bool real entries; orthogonality plus determinant +1. Reflection/shear/nonfinite/malformed output and 4×4-prefix false acceptance fail. Nonmutation and invalid-input behavior are explicitly tested. |
| VS-08: FK anchor | Relative radians, l1=2,l2=1,q1=π/2,q2=−π/2 yields (1,2), orientation 0 modulo 2π. Nonzero unequal-link cases reject absolute angles, swapped links and degree confusion. |
| VS-09: all pose fields | Stretched/folded/near-boundary fixtures validate x, y **and orientation**. Reject the NaN-orientation counterexample. Accept angle-equivalent output; a changed end orientation cannot pass on position alone. No spatial/hardware claim follows. |
| VS-10: fair grading | Every accepted domain/output format and precision is stated. Equivalent fractions accepted; bool/NaN/Infinity/wrong shape rejected; format/infrastructure errors do not become conceptual weaknesses. Independent valid solutions and named mutations pass/fail for the intended reasons. |
| VS-11: verification admission | Known immutable form/version/policy and objective coverage; server-owned eligible attempt; all critical criteria and applicable thresholds. Per-objective C/M partial results follow an explicit policy. Numeric procedure checks do not claim proof or reviewed derivation. No I PASS while the eligible profile is unavailable. |
| VS-12: review | Delay basis, effective assistance, new instance/exposure and source contract validated. Early review can be practice without retention credit. Failed/partial correction does not postpone another unresolved objective. Unfamiliar transfer remains unreviewed without a qualified judgement. |
| VS-13: restore/migration | Complete `/3` round-trip including attempts/exposure and signatures; invalid or interrupted restore changes nothing; full pre-restore snapshot recoverable. V1 partial restore behavior explicit. Future sidecar schema rejected safely. V1→V2→V1 edit/restore→V2 tested. |
| VS-14: size and provenance | Every supported export imports through the advertised flow at its size limit. Unknown issuer/profile/contract and replay follow the documented policy. Never trust serialized `passed`, `trusted` or client results alone. No private-key backup. |
| VS-15: local-first UI | Entire numerical/text path usable with external networking blocked while localhost remains available. Video remains optional. Keyboard and screen-readable matrix/coordinate alternative; mobile-width completion tested. No route executes a submission, and locality/origin checks apply to every new endpoint. |
| VS-16: regression and delivery | Existing 119 tests/content validation remain green, signed legacy fixtures round-trip, and a fixture legacy history produces identical legacy scores. Feature on/off, full workflow and permitted-volume history are tested on named OS/hardware. Publish unsupported OS limits rather than inheriting old platform claims. |

Tolerances and bounded input domains must be in the actual approved contracts. The examples support starting tolerances on small fixtures; they do not validate arbitrary scales. Trials at 7/21 days cannot be compressed into author hours. Reviewers, accessibility checks and pilot observations are release work, not proof supplied by this audit.

## 5. Evidence and reproducibility

### 5.1 What I executed

| Check | Result | Inference limit |
| --- | --- | --- |
| `npm test` | 119 passed, eight files; Linux, Node 26.8.1 | Existing behavior only, not future V2 integration. |
| `npm run validate:content` | 169 topics, 31 lessons/diagnostics, 42 targeted questions/seven banks, 28 video resources | Schema/content baseline, not teaching quality. |
| Canonical proposal graph parsers | Curriculum 176 nodes/319 edges; lab/capstone 25/39; both acyclic/no missing references | Graph structure, not optimal sequencing or operational labs. |
| Current Python harness | Forged success stdout + exit 0 accepted | No signing CLI/key access or real evidence import. |
| Synthetic backup/issuer probe | Embedded throwaway-key report accepted; `trusted:false→true`; legacy I=2 | Current portable-restore policy; no claim of a protected V2 importer. |
| Strict progress probe | New top-level `exerciseAttempts` rejected | Confirms additive data needs a separate typed format or migration. |
| Backup size probe | 405 valid notes; 8,141,819 bytes; `validateBackup` accepts | Compared with inspected 8,000,000 handler limits, not a browser/HTTP test. |
| Same-user child marker | Read a benign parent-owned marker outside cwd despite empty env and `-I` | Boundary demonstration only; no protected sandbox or actual proposed runner tested. |
| Draft Appendix rerun | Both valid alternatives accepted and all seven named mutants rejected for each lab | Narrow author fixtures, not released graders. |
| Extra fixture probes | Both malformed-matrix and nonfinite-edge-orientation false accepts reproduced | Concrete additions needed in the approved rejection suite. |

No new UI, migration, broker, browser workflow, Windows/macOS route, simulator or hardware was implemented/tested. No build/lint run was needed to validate this unchanged-source/documentation audit; no success for those checks is claimed.

### 5.2 Small counterexamples for the Appendix

Load the draft's published Appendix Python block into `ns`, then run:

```python
Ref = ns['Ref']
class ExtraShape(Ref):
    @staticmethod
    def compose(A, B):
        M = ns['mm'](A, B)
        return [row + [123.] for row in M] + [[123.] * 4]

def bad_edge_orientation(q1, q2, l1, l2):
    x, y, theta = ns['fk'](q1, q2, l1, l2)
    if q1 == 0. and q2 in (0., ns['math'].pi):
        return x, y, float('nan')
    return x, y, theta

assert ns['l01'](ExtraShape) is True             # false accept, reproduced
assert ns['l02'](bad_edge_orientation) is True    # false accept, reproduced
```

Both should be rejected after exact-shape/all-field validation. These snippets are research counterexamples; they are not learner exercises, production tests or claims that the future grader remains vulnerable after repair.

For the backup findings, a minimal safe rerun uses `validateBackup` directly, `emptyProgress()`, an in-memory generated Ed25519 key/report, and synthetic notes. No `getStore()`, live restore or workspace signing key is needed. The relevant current source paths and results are given in M-03/M-04; existing `tests/storage.test.ts:213–280` also demonstrates the portable-report/live-import distinction.

**Preservation:** SHA-256 comparison verified all **187 baseline files unchanged**, covering tracked application files and all three finalized review directories. The pre-existing `next-env.d.ts` change was preserved. My only repository output is this audit file; controlled reproduction scripts/results are outside the repository under `/tmp`. Claude’s design was read and fingerprinted, not edited. Existing working-tree changes were not staged or committed.

## 6. Handoff for the final unified specification

Claude can finalize without another ordinary debate round by:

1. Keeping the objective layer, separate legacy read model, optional activities, numerical-first slice and reserved later pathways.
2. Making P3 protected I unavailable until its approved execution profile exists; retain reviewed manual self-check kits as unverified practice. Explicitly resolve any weaker-policy alternative instead of claiming it is the Bank's protected verification.
3. Defining the issued-attempt/exposure lifecycle, full first-write backup/restore, sidecar migration guard and report/retention admission contracts.
4. Correcting the media/readiness references and the two demonstrated fixture false accepts; expanding acceptance criteria without describing them as executed.
5. Carrying a finding-to-section disposition in `CORELAB_V2_UNIFIED_SPEC.md`, with unresolved owner decisions and accurate OS/reviewer/budget limits.

This is the requested notification through the review file. **No implementation or commit is authorized by this audit.** If the final specification keeps the critical same-user/verified-I contradiction, flag it explicitly for resolution; do not silently mark B-01 resolved. Other issues need concrete specification changes and acceptance tests, not an additional three-round review process.

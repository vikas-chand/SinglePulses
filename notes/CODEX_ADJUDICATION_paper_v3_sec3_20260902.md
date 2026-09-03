# ADJUDICATION of the Codex supervisor review — paper v3 §3 draft (2026-09-02/03)

**Report adjudicated:** `notes/CODEX_REVIEW_paper_v3_sec3_20260902.md` (Codex gpt-5.6-sol ultra, supervisor
hat, session 01a06570…, launched 23:04 CDT, landed 23:39 CDT; wrote only its report — `git status` clean
otherwise). **Adjudicator:** the building session (Claude, Fable 5.1), fresh primitives opened for every
finding below; nothing accepted on Codex's word. **Codex verdict:** DO NOT SIGN OFF on §3 as drafted; the
spine ("the harness, component by component") is endorsed. **My verdict after checking: the same.**
Twenty overclaims and twelve discrepancies; 18 of 20 overclaims CONFIRMED at the primitive, 2 confirmed with
a modification; 11 of 12 discrepancies CONFIRMED (one already carried by the register). No finding rejected
outright. Three items are the PI's decisions, listed at the end.

## A. Findings CONFIRMED at the primitive (accept the reword)

| id | claim in the draft | primitive I opened | verdict |
|---|---|---|---|
| O2 | five sources "converge on five runtime jobs" | `notes/HARNESS_COMPARISON_20260902.md:10-25` — the five jobs are Bowne-Anderson's taxonomy alone; Böckeler = guides/sensors, Palantir = objects/actions, LangChain = layering | CONFIRMED; reword to "we organise by Bowne-Anderson's five jobs and borrow…" |
| O3/O4/D5 | "exist on disk at the census commit" | `.gitignore:41` `results/*` ignored → state files, receipts, traces, VISION_QC cannot be reconstructed from 4df6884 | CONFIRMED; say "working tree measured 2026-09-02 with tracked code at 4df6884" + ship a census manifest |
| O4/O17/D3 | "the approver is the human at every step gate"; "every Stage-1 selection (human)" | roster row 8 (`T1_component_roster_DRAFT.md:49`): Stage-1 decision is human **or** AI, stamped; `find results -name APPROVALS.json` → exactly ONE file (bn110920546) | CONFIRMED; protocol requirement ≠ coverage; Stage-1 human-or-AI |
| O5/O12 | "one of fourteen typed states … derived from the products on disk" | `dev/agent_state.py:17-62`: starts at S1, never returns S0/S12, S9 = string `NR-24` in VISION_QC, S11 = any APPROVED stamp, `currency = 'UNVERIFIED (NR-22)'`; writes the 106 files itself (:64-72) | CONFIRMED; the skeleton declares 14, the board derives a partial index |
| O5 | "fixed four-sentence form" | `BurstWalkthrough.md:26-31`: PRESENT = four THINGS (a)–(d) | CONFIRMED (wording) |
| O6 | "eleven typed workflows … each state transition" | `AgentSkeleton.md:91-109`: wf-bin…wf-bundle + wf-invalidate cover S1→S10, S11→S12, invalidate; S0→S1 and S10→S11 have no workflow | CONFIRMED; "eleven workflow files for S1→S10, S11→S12 and invalidation" |
| O8 | "cuts the brightest detector's light curve" | `scripts/27b_reblock_3ml.py:164-190`: catalog-brightest only if approved, else the approved NaI with most counts in its own background gap | CONFIRMED |
| O9 | "imports the lag routine we validated … unmodified" | `scripts/47c_lag_latbright.py:28-29,56`: `sys.path.insert(0, "/Users/salim/Desktop/LATBright/GRB260226A")`; `import s02c_spectral_lag` — no revision pinned | CONFIRMED; the reproduction record must pin the imported file's sha |
| O10 | "refuses any panel that disagrees with the stored fit" | `scripts/41c_paper_sed.py:315-351`: live → frozen replay → refuse only if neither reproduces the stored AIC within 0.1; `41_nuFnu_panels.py:303-308` legacy path stamps `PANEL!=ENGINE`; `41e` draws placeholders | CONFIRMED |
| O11 | "twenty-seven skill documents indexed by the burst ledger" | roster row 13 (`:59`): ten step skills indexed by the ledger; `SEDPanels.md` absent (`:160`) | CONFIRMED; "27 guide files, ten ledger-indexed step skills" |
| O11/O17 | skill-reader "opens every step"; roles "separated by construction" | `AgentRoster.md:81-99`: Mode B invocation "socially enforced, audited after the fact"; compliance "unverified downstream" | CONFIRMED; protocol in Mode B, structural only in the typed workflows |
| O13 | "revocable by machine … cascade demotes every downstream approval that depended on it" | `dev/invalidate_downstream.py:45-84`: explicit invocation, dry-run default, marks ALL later APPROVED steps STALE (no dependency graph); `live_report.py:127-131` prints a reminder | CONFIRMED for the mechanism (see B for the incidents) |
| O14 | "a promotion receipt … a sidecar beside every fit table … a commit pin" | `ls results/convention_check/*/promotion_receipts/*.json` → 7 receipts, 6 bursts (bn081224887, bn091209001, bn100707032, bn101225377, bn110618366, bn110920546); ReportSpec.md:13-27 lists argv/env + fit-table-sha binding as queued | CONFIRMED; coverage partial |
| O15 | "a test validates every instance on disk" | `tests/test_schemas.py:56-64`: seven globbed classes + the trace; `pytest.skip` when a class has no instances; four KNOWN_DEVIATIONS | CONFIRMED |
| O16 | hook powers stated without matcher limits | `.claude/settings.json:3-30`: matcher `SendUserFile` (PNG only) + two `Bash` regex hooks; FreshSessionBoot.md:166-169 records the false blocks | CONFIRMED; the draft already states the limits, but "is enforced" → "controls range from…" |
| O18/D3 | authority table: "the AI decides … model winner … fit-validity verdicts" | `scripts/10_*.py:1038-1082` `_fit_is_physical`, `:1104-1128` `select_best` (validity-gated argmin, INCONCLUSIVE when none valid) — CODE decides both | CONFIRMED — the most consequential error; inherited from v2's table; the AI audits/interprets, it does not decide |
| O19 | "In all operation to date, no approval has been generated by the system" | `dev/live_report.py:155-160`: `--by` required, not authenticated; no complete approval ledger → an unverifiable universal | CONFIRMED; protocol + CLI refusal; the override count belongs to §9 after a census |
| O20/D2 | five missing = "queue manager, workflows, report-conformance gate, first-class actions, loop caps" | roster PROPOSED rows: 4 (queue manager + workflows), 24 (first-class actions), 35 (report-conformance gate), 36 (queued boundary build), 49 (queued science-guard code) | CONFIRMED; "loop caps" is part of row 36; row 49 omitted |
| D1 | roster header says "UNGATED … Nothing here is PI-approved … re-gate pending" | `T1_component_roster_DRAFT.md:6-8` — stale; approved at 427fdc5 per the outline decision log (:133) | CONFIRMED; header metadata fix + regenerate |
| D4 | verdicts bind PNGs; the tex embeds PDFs; ledger under gitignored results/ | shas recomputed: F1 png d355cbec / pdf f8592794 / tex bd195af7 (F2 6165ad96/4aae2ec1/2a5f7846; F4 755a0fee/dd0829ac/a0c869b0; F5 73bf5bf3/19b58a14/dd88c68c) | CONFIRMED — **FIXED NOW**: binding table (png+pdf+tex sha) appended to VISION_QC.md; tracked copy `paper_agentic/figures/GATE_LEDGER.md` |
| D7 | header comment "doctrine → §5" | `REWRITE_OUTLINE_v3.md:90-92`: Verification doctrine = §6 | CONFIRMED; the comment is wrong; Codex's split (fit rules→§4, lessons/hierarchy→§5, blind-first/primitive/fresh-context→§6, no-silent-approval→§3.5) adopted |
| D8 | F1 "24 models × every block"; 27 guides drawn as ledger-indexed skills | `fig_F1_harness_anatomy.tex:39` | CONFIRMED; fix + re-render + re-gate (verdict expires on tex edit by the contract) |
| D9 | `\prov` on non-count claims | `sec3_harness.tex:124,183` | CONFIRMED; `\prov` reserved for counts with a stated basis |
| D10 | footnote incomplete (two "vendor posts", no URLs, no access dates) | `sec3_harness.tex:17-20` | CONFIRMED |
| D11 | report assembler "from that burst's own numbers" | `scripts/48_burst_report.py:71-73`: prefers the promoted table, silently falls back to the sweep copy; ReportSpec.md:23-25 = fail-closed guard queued (NR-29) | CONFIRMED (currency, not wrong-burst); reword |
| D12 | generated T1 repeats the same absolutes | cells of rows 6, 18, 19, 20, 21 in `tab_T1_roster.tex` | CONFIRMED; the markdown roster's status notes carry the qualifications, the generator dropped them |

## B. CONFIRMED with a modification (Codex lacked the record, or over-corrected)

- **O7 (24 models).** Codex: default is six, 24 only with `--models highe`. True (`scripts/10_*.py:722-725`), but
  the CAMPAIGN runs highe for every burst and the state board asserts the 24-model census (`dev/agent_state.py:28-29`).
  Reword: "in the campaign configuration the engine attempts a 24-model menu (6 + 2 + 16) for every usable time bin
  and for the integrated interval when its plugins can be built; it writes per-model status, validity, AIC and BIC."
  Not "six by default" in the paper — the paper describes the campaign, not the CLI.
- **O13 incidents.** Codex could not verify the delayed stamp and the byte-identical reinstatement (barred from
  burst products). I can: `results/sweep106/bn110920546/APPROVALS.json` step 3 carries `stale_reason` "SELF-INVALIDATED
  … approved at 20:08:06Z on the pre-trim state" with the stamp at 2026-09-01T14:46:43Z (delay disclosed), and step 5
  carries "REINSTATED by PI ruling 2026-09-01 ('Reinstate - blocks provably unchanged') … edges and significances
  byte-identical"; the block table sha on disk is f361fbd245b56e2c. Decision: KEEP both sentences in §3.4, cite the
  approvals record and the block-table sha inline, drop the `\prov` there. Codex's "move to §9 or remove" is not needed.
- **O1 (bare model).** The sentence was about the bare call; Codex's "directly observe / only through the harness" is a
  precision gain. Accept, shortened.
- **Q3 vocabulary.** Codex calls "agent = model + harness" a slogan and proposes: language model vs spectral model;
  the hosted product + the repository = "the GRB analysis harness"; "agent invocation" = the model executing one named
  role; "subagent" = a fresh-context role instance returning a bounded result. This is COMPATIBLE with the PI's own
  framing tonight ("the overall thing we built is Agent but that has harness which has subagents"); the difference is
  only whether the paper's noun for the whole is "the agent" or "the GRB analysis harness". → PI decision 1.

## C. What I disagree with, and why

- **O19's "at least one human–agent divergence is recorded"** understates the record: APPROVALS.json feedback entries
  and `divergence_ledger.md` hold several. But Codex's point stands — the paper needs a census with a denominator
  before saying "repeatedly". No disagreement on the fix.
- **Q4's AAS guidance** ("footnote with URL and access date"): I did not verify the AAS page in this session
  (UNVERIFIED — check journals.aas.org/references when composing the footnote). The five posts' URLs are in
  `reference_agent_harness_article.md`; the dates Codex gives (Bowne-Anderson 2026-07-28, Böckeler 2026-04-02,
  PuppyGraph 2026-07-01, LangChain 2026-06-03) match the comparison note for the last three; confirm the first on access.
- **Q4's literature.** Verified by me: ReAct arXiv:2210.03629 (ADS 2022arXiv221003629Y), ScienceAgentBench
  arXiv:2410.05080 (2024arXiv241005080C), Kapoor "AI Agents That Matter" arXiv:2407.01502 (2024arXiv240701502K),
  Souza provenance agents arXiv:2509.13978 (2025arXiv250913978S; DOI 10.1145/3731599.3767582 resolves at ACM),
  Boiko Nature 2023 (2023Natur.624..570B). Resolve at the publisher but NOT in ADS: Wang survey
  10.1007/s11704-024-40231-1 (Springer), Bran ChemCrow 10.1038/s42256-024-00832-8 (Nature MI). Per the paperedit rule
  none enters the tex until its PDF is local and quoted. Codex's "no peer-reviewed five-job taxonomy" = COULD NOT VERIFY, agreed.

## D. Fixes applied tonight (my own files; nothing in v2; nothing the PI approved was altered)
1. VISION_QC.md: png+pdf+tex sha binding table for F1/F2/F4/F5 (D4) + tracked copy `paper_agentic/figures/GATE_LEDGER.md`.
2. This adjudication.

## E. Fixes PREPARED for the PI's gate (not applied to approved products)
- §3 fragment revision r2 incorporating A + B (rewords O1–O20, D7, D9–D11; the incidents kept with citations; the
  footnote listing all five posts with URLs; the two-planes definition before the authority table; the corrected
  table: code decides validity + winner, AI audits; Stage-1 human-or-AI). → re-present as chng[1] r2.
- F1 fix (line 39 → "24-model menu × every usable bin (highe)"; guides box → "27 guide files; 10 ledger-indexed
  step skills") → re-render → figure-verifier → new ledger row. The PI approved F1 at d355cbec; the delta needs his re-approval.
- Roster: header metadata (D1) + status-cell qualifications for rows 6/18/19/20/21 (D12) + a CHECKED-IN generator
  (`dev/build_t1_roster.py` — the tex says "generated, do not hand-edit" but no generator is on disk: the in-session
  script was never saved; that is itself a D-class defect, fixed by writing the generator and diffing it against the committed tex).
  Substantive cell changes re-open the roster gate (approved 427fdc5) → the PI's re-approval.

## F. PI decisions needed
1. **Vocabulary**: keep "the agent" as the noun for the whole system (PI framing) with Codex's definitions inside, or
   adopt "the GRB analysis harness" as the noun and reserve "agent" for an invocation in a role. My recommendation: the
   latter in the paper (no recursion: agent inside agent), the PI's sentence kept as the plain-language gloss.
2. **Status vocabulary in T1** (D6, Codex's strongest independent point): DEPLOYED today means "a file or a product
   exists". Options: (a) DEPLOYED / PARTIAL / PROPOSED with the coverage note carried into the tex status cell;
   (b) four columns present / invoked / enforced / evaluated. My recommendation: (a) now (one gate), (b) for the
   frozen-run paper. Either re-opens the roster gate.
3. **The thesis sentence** (outline §1: "reliability over a long scientific run is a property of the harness"):
   Codex (Q5 objection 1) — present it as the design hypothesis tested by the eventual frozen run; the defensible
   claim today is system-level (model + hosted harness + repository controls + engine + human) with documented
   interventions and named coverage gaps. My recommendation: adopt; it is also what the roster shows (44/49 present, coverage partial).
4. **Process** (Q6): Codex recommends a hybrid — gate §3+§4+§7 as one architecture block (shared vocabulary and
   status claims), then §5+§6+§10 as one claims block, then §1/§11 with one assembled-PDF gate; a short decision
   sheet per block instead of sentence-level gates. My recommendation: adopt.
5. **Naming the hosted harness and model** (Codex independent judgment 4): T1 already says Claude Code; the paper
   should name harness + version + model ids in reproducibility metadata. Vendor naming is the PI's call.

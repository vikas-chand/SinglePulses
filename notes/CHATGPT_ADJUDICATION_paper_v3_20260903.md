# ADJUDICATION of the ChatGPT referee report — paper v3 (2026-09-03)

Report: `notes/CHATGPT_REVIEW_paper_v3_20260903.md` (39 findings, major revision). Adjudicated by the building session
against disk, primitive by primitive, before any edit. Standing rule: advisory, not spec; every factual and
bibliographic claim verified before acting.

**Verdict on the report: it is right about the paper.** Nothing in it is a hallucinated defect. Of the 39 findings I
checked 12 at the primitive today (below); every one of those held. The rest are judgement calls about scope and
prose, and I recommend accepting almost all of them. Two findings are stated slightly wrong in detail (see C).

## A. CONFIRMED at the primitive today

| # | claim | what I checked | verdict |
|---|---|---|---|
| 1 | §1 contradicts the corrected authority table | `agentic_grb_v3.tex:97`: "an AI exercises agency … which of twenty-four spectral models wins a gated comparison, whether a fit is valid or sits on a parameter rail" — the engine computes both (`scripts/10` `_fit_is_physical`, `select_best`) | CONFIRMED. This is the same defect Codex found in §3's table on 2026-09-02; I corrected the table and left the introduction untouched. My omission. |
| 22 | the paper cites blog posts while the brief says it does not | `agentic_grb.bib:233` `@misc{anthropic2024agents}` "Building Effective AI Agents" with a URL, and `:239` a second Anthropic engineering post | CONFIRMED. Decision 17 (no blog citations) was applied to §3's new text and never to the v2 bibliography or to §1's citations. |
| 22b | the five compared accounts are not named in the paper | zero occurrences of Bowne-Anderson, Böckeler, PuppyGraph, LangChain or Palantir in the manuscript | CONFIRMED, and it is the direct consequence of decision 17. Table 3's column head "present here, described in none of them" is therefore an unsupported negative about five unnamed sources. |
| 25 | §11 says "thirty-two durable lessons" | `agentic_grb_v3.tex:307`; §5 now says 44 in the library, 23 credited to walked bursts | CONFIRMED. v2-era number in old text. |
| 25b | §11 says the system "walks bursts end to end" and "runs as written in a fresh session" | §9 (`:267`) says "the first seven of the eleven gated steps have" passed in that arm | CONFIRMED contradiction. |
| 24 | §3.5 promises §9 reports the override count with its denominator | grep for "overrul" in the manuscript: only §3.5's forward reference; §9 has no count | CONFIRMED. My sentence, written 2026-09-03, promises a number that does not exist. |
| 23 | "Both are released" with a pending DOI | appendix: `DOI \PENDING{Zenodo concept DOI at release}` | CONFIRMED. |
| 3 | DEPLOYED means "a file or product exists" but reads as "operates" | roster header rules, and the register's own four extra states (partial, closed, practice, fixed) | CONFIRMED. The PI ruled on 2026-09-03 (decision 18) that DEPLOYED/PROPOSED stays; the referee is asking for an evidence column, not a fourth status word, which is compatible with that ruling. |
| 20 | "four first-class actions" vs the roster's PROPOSED wrapper | §7 text vs roster row 24 | CONFIRMED as an ambiguity; the referee's rewrite is exactly the true state. |
| 19 | "validates every instance on disk" vs four ledgered exceptions | `tests/test_schemas.py` KNOWN_DEVIATIONS = 4 | CONFIRMED (§3.4 already says it; §7 does not). |
| 5, 6, 7 | roster rows stronger than the main text (state board, hash binding, SED refusal) | roster rows vs §3.1/§3.2/§3.4 | CONFIRMED. The roster was written before the sections were corrected and never re-synchronised. |
| 39 | the bibliography is too small | 20 proposed identifiers | ALL 20 VERIFIED at ADS today (bibcodes in the report file). None is fabricated. Two are 2026 papers I had not seen: Panek+2026 ASTER and Borrett+2026. Kostunin+2025 (gamma astronomy agents) is the closest precursor and its absence is a real gap. |

## B. ACCEPTED without needing a check (judgement, and the referee is right)

4 (universals vs measured coverage) is the single biggest item and repeats what the Codex supervisor found in §3 on
2026-09-02: I fixed §3's instances and left the same universals standing in §4.3's fan-out paragraph. 11 (lessons-as-tests
is three different claims), 12 (blind-first is a procedural promise, not an information barrier), 13 and 31 (accrual
history, not a learning curve), 16 (fresh context ≠ independent), 17 and 18 (portability and the vendor comparison are
hypotheses), 2 (proposer vs approver is not representable in one APPROVED_BY field), 33 (the authority table's
"decides"), 26 (two different 49-row universes), 27/28 (vocabulary and internal labels), 29/30/32/34/35 (figures, tables,
cut plan). 21 is right in detail: two of the taxonomy's countermeasures are proposed, and §10 says so two sentences
later, so the opening universal must soften.

## C. Where the report is slightly off

- **28, the duplications.** "A small set of standing contracts" appears once, not twice, and "Table 1 states…" appears
  once. The reviewer is reading the compiled PDF where a caption and the body sit close together. No action.
- **31 vs the caption.** The figure is already titled and captioned as an accrual over walked bursts with the ninth
  marked in progress; what is missing is the *axis label* and the word "learning" in §5's prose. Narrower fix than stated.
- **1's replacement** is good but drops "which of twenty-four models wins" entirely; the AI does adjudicate ties and
  adopt a winner where the rule leaves a choice. The honest line keeps that and removes only validity and ranking.

## D. What I recommend, in the PI's decision order

1. **Fix the eight contradictions first** (findings 1, 5, 6, 7, 19, 20, 24, 25). These are cheap, they are all
   self-inflicted, and they are the ones a real referee would treat as carelessness. Half a day.
2. **Rewrite the universals** (4, 21) with "the protocol requires" / "the hook enforces, for PNG deliverables" and give
   the coverage numbers we already have. Half a day.
3. **Rename what is not yet measured** (11, 12, 13, 16, 17, 18, 31): accrual not learning curve, prospectively frozen
   comparison not blind analysis, correlated channels not independent reviewers, design hypothesis not property. This
   costs nothing scientifically and removes the referee's third blocking objection.
4. **Decide the citation question** (22, 39): the five harness posts are currently uncited by decision 17 *and* two
   Anthropic posts are cited in the bibliography. Either cite the engineering sources properly or drop Table 3's novelty
   column. My recommendation: drop the "described in none of them" column, keep the needs column, and add the twenty
   verified papers to §1 — that answers 22 and 39 together and makes the paper's positioning honest.
5. **The two experiments the referee wants** (8/37 injection-recovery; 36 one complete walkthrough burst) are the real
   work and the PI's call on scope. Both use machinery that exists. The injection-recovery battery is, in my judgement,
   the single highest-value addition in the whole report: it is the difference between "our agent ran the pipeline" and
   "the pipeline's decisions are calibrated".
6. **The cut plan** (35) after the science is settled, not before.

## E. What this says about our own gates
The Codex supervisor caught the authority-table error in §3 on 2026-09-02; I fixed §3 and did not sweep §1, §9 and §11
for the same error, and no gate covered them because they were "old text, not in this block". The referee found it in
one reading. Distiller candidate: **a correction is not closed until every section that repeats the corrected claim has
been swept** — the block-gate boundary is not a defect boundary.

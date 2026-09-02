# REPORT / PAPER STANDING PRODUCT CONTRACT (R-items)
Born 2026-08-26 from the PI's catch: "you didn't make all reports alike and top
quality." Figures had FigureVisionQC; the deliverables CONTAINING them had no
contract. This is that contract. Verifier: report-conformance gate (NR-24).
Amend only with the PI's quoted words (gate-verifies-PI-spec).

## R1 — ONE GENERATOR, ONE COMMIT
Every burst's paper is produced by THE SAME assembler at THE SAME repository
commit, recorded in a staging manifest beside the .tex. A batch containing
outputs from two code states is nonconforming by definition — regenerate the
older ones, never patch by hand. (Found: 7 papers from >=3 generations, none
manifest-stamped; report bn081125496 from 69f4893 vs 20 others at 996dba2.)
**Amendment 2026-08-30 (PI ruling 4, gate 1 of the #21 walkthrough), verbatim:**
"R1: commit the campaign generators and re-pin now (before anything is
assembled). Manifest records: generator pinned by commit, products bound by
hash — products are untracked by design." Consequences: (a) every generator
the assembler calls is TRACKED and CLEAN at the pinned commit — on 2026-08-30
all 12 campaign producers were untracked while the boot brief said the commit
was pinned (NR-29), and .gitignore:41 `results/*` means products can NEVER be
commit-bound, so products bind by sha256, not by commit; (b) the staging
manifest records {commit, tree_dirty_list, product_sha256s} and the
sha256 of the FIT TABLE each report and figure read (NR-28: the #21 report
of 08-18 was built from the nested sweep copy, 6/12 winners different from
the promoted table, and nothing recorded which); (c) the assembler REFUSES
to run if its own file is not tracked-and-clean at HEAD (NR-29, code guard,
queued); (d) the pin's location is a design gap — CAMPAIGN_COMMIT_PIN.json
is improvised, PI to bless or relocate (decision sheet item 23).

## R2 — STRUCTURE (the bn081125496 exemplar, PI-approved "great")
aastex631 twocolumn; temporal-first section order; every analysis figure
included (SED grid montages, param evolution, temporal suite, step panels);
ADS-exported bibliography only (hand BibTeX forbidden); provenance block
(commit, product paths, P0 status); PROVISIONAL banner until campaign freeze.

## R3 — NUMBERS DISCIPLINE
Every number from the promoted convention_check table or the temporal catalog
(NR-23 same-source rule). No literal `nan` may render — a missing value prints
an em-dash + a stated reason (found in 3/21 reports). Estimator labels ride
every temporal quantity. dAIC<2 heads are reported as TIES (NR-3); the words
"robust", "strong candidate", "quasi-stable" appear only with a number.
**Amendment 2026-08-30 (PI ruling 3, gate 1 of the #21 walkthrough), verbatim:**
"ΔAIC reference: BOTH constructs stay, with mandatory labels — "DECISIVE" =
chain-gate vs best simpler ancestor (structure claims, ΔAIC≥10); "TRACKED" =
vs runner-up (preference, ΔAIC>6 in 1–2 bins). Never print either word
without its reference." In a deliverable: "DECISIVE vs <ancestor model>"
and "TRACKED vs <runner-up model>" — never the bare word; a tie (dAIC<2 vs
the runner-up) and a DECISIVE (vs the ancestor) may both be true of one bin
and are then both printed. The conformance gate fails a bare DECISIVE/TRACKED.
**Temporal amendment 2026-08-30 (PI ruling 5, NR-31):** no LAG_* or MVT_*
value from results/temporal_catalog_all106.ecsv may be quoted for a burst
not listed in the catalog's meta.rewalked_triggers — the STALE-PENDING-REWALK
header is read by code (48, the assembler, the numbers-verifier), never by
memory. PI verbatim: "nothing downstream may quote temporal_catalog_all106.ecsv
for an un-walked burst — that's what the STALE label enforces mechanically
rather than by memory." A T90 whose row carries EITHER T90_WINDOW_TRUNCATED
or TAIL_OUTSIDE_WINDOW_SIG ≥ 3σ prints as a LOWER LIMIT (NR-33, PROPOSED
pending PI).
**Producer-preflight amendment 2026-09-01 (distiller entry — PI-BLESSED
2026-09-01 at the paper structured gate, PI's answer verbatim: 'Bless both';
catching gate: numbers-verifier
fresh-context pass on agentic_grb_v2.tex):** a \prov flag is NOT provenance —
it asserts provisionality and binds nothing. No verification request may be
launched while any row of the producer's provenance manifest lacks a bound
source; a blank sha/source cell is a STOP, not a TODO that rides along.
Instance 2026-09-01: "five engine defects" lived in the draft since 2026-08-10
under \prov; paper_agentic/PROV_MANIFEST_v2_update_20260901.md row 21 carried
no bound sha ("CHECK-PATH"-class blank) and the producer launched verification
anyway. No product ever supported the count (notes/campaign_ledger.csv
recomputes 13 mixed-category bugs over 8 rows) and
notes/CODEX_WHOLE_PROJECT_20260813.md:381 had ALREADY ruled it unsupported on
2026-08-13 — the repo knew; the flag rode for 22 days. Register instance:
NR-29 (AgentArchitecture.md).

## R4 — GATES BEFORE DELIVERY
figure-verifier on every figure (existing rule), numbers-verifier on the
assembled document, and the NR-24 CONFORMANCE gate on this spec — all three
verdicts sha-bound in the burst's VISION_QC.md before the PDF reaches the PI
or any collaborator bundle. An ungated paper is a draft and must say so.

## R5 — BUNDLE COMPLETENESS
A collaborator bundle contains, per burst: paper PDF + source, REPORT md+pdf,
REPRODUCTION record, executed notebook — and a manifest row per burst stating
which of these exist, with absences REASONED, never silent (the Khushboo
bundle shipped reports while 7 finished papers sat unbundled).


## R3a — CLAIM TYPING (adopted 2026-08-29, 3rd external review; aligns with our
S0-S3 wildness grades and estimator labels)
Every claim in a deliverable carries its epistemic type — observed /
estimated / causal / mechanistic / speculative — and prose may not silently
upgrade a type (an estimated quantity does not become an observation; a
correlation does not become a mechanism). The conformance gate checks for
type-consistent language. CI test to build with A19: CLAIM REPLAY — pick a
sentence from a report and mechanically reconstruct claim -> result object ->
run -> workflow -> code -> data snapshot; failure at any link = not
publication-grade (this is NR-23 + NR-7 + NR-22 exercised end-to-end).


**Provenance-field amendment 2026-09-01 (distiller entry — PI-BLESSED
2026-09-01 at the paper structured gate, PI's answer verbatim: 'Bless both';
catching gate: numbers-verifier fresh-context pass on agentic_grb_v2.tex):**
a claim ABOUT a record's provenance quotes the record's provenance field
VERBATIM at write time; provenance adjectives (contemporaneous / retroactive /
reconstructed) are never recalled from memory of a register row — recalling
one is a silent type upgrade in the R3a sense (a reconstruction becomes an
observation). Instance 2026-09-01: fresh prose wrote "one of the 105 records
carried a contemporaneous reason" while the source
(results/approval/bn110920546_decision.json `reasoning_provenance`:
"RETROACTIVE, not contemporaneous", + the NR-39 register row) states the
opposite — the one filled record is retroactive; the contemporaneous count is
ZERO. The same sentence carried the correct principle ("a reconstructed
reason is never a contemporaneous record") and the producer did not detect
the internal contradiction. Register instance: NR-39 (AgentArchitecture.md).

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

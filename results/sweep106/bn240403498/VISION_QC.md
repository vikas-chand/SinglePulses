# VISION QC LEDGER — bn240403498

## Figure: bn240403498_step1_inventory.png (steps 1-2)
**Final state: raster VERIFIED, accepted with documented nits (PI, 2026-09-05).**
- PNG sha256 `29e2f54f9ce97da25aa3e46675f1f905d259ea4deb9398c9578a04bc6b444b1e`
  — byte-identical to the raster the round-5 verifier passed.
- Sidecar: `bn240403498_step1_inventory.sidecar.json` (pins 5 primitives incl. the divergence ledger).

Five fresh-context rounds. Every round independently re-derived the numbers from the raw
`.rsp2` and `poshist` FITS; the CONTENT never failed. What failed, repeatedly, was rendering
and provenance consistency — and rounds 2, 3, 4 and 5 each failed on a defect the PREVIOUS
round's fix introduced. That pattern is the lesson, not any single defect.

| round | verdict | blockers | who caused them |
|---|---|---|---|
| 1 | FAIL | 50° rail struck n0's "BCAT" tag (same green); n3 in BCAT but invisible; angles plotted as measured with no provenance | pre-existing producer |
| 2 | FAIL | 8 labels struck by the axes RIGHT SPINE (one on the "1" of "12 matrices"); n3's absence drawn as an 18-48 s hatched span | **round-1 fix** |
| 3 | FAIL | footnote said "reason not yet recorded" while the ledger it cited recorded the PI's verbatim reason (hard-coded string); 62% of the right panel empty | **round-2 fix** |
| 4 | FAIL | "60° drop" struck the right spine and hung outside the panel; sidecar still hard-coded "reason not yet recorded" | **round-3 fix** |
| 5 | FAIL (raster PASS) | `right_xlim_is_label_driven: false` hard-coded while the fitter had grown the axis 68.2° -> 70.4° | **round-4 fix** |
| — | fixed post-round-5 | one line, measured from the axis; PNG byte-identical | — |

**Verified in round 5, independently:** 12 SPECRESP MATRIX per detector, coverage
-124.034 -> +482.185 s; 11 interior boundaries drawn to sub-pixel; exactly one boundary
(23.42445 s) inside the source window; all 14 detector angles reproduced to 0.00° from a
from-scratch reimplementation; BCAT/SCAT masks; approved set and SRC 18-48 s; n3 absent from
disk. All four falsifiers survived.

**Accepted nits (not fixed, recorded per PI instruction "accept this round result"):**
- N-1 `keep` sits 24 px from its own rail, 17 px from the other; colour + tick + footnote disambiguate.
- N-2 6 of 11 boundary ticks fall inside the in-bar "PASS · 12 matrices" text (glyphs on top, intact).
- N-3 the 23.424 s thick tick clears the 18 s window rule by 3 px.
- N-5 "81.5-145.1°" is a floor/ceil containing interval; true extremes 81.59 / 145.05.
- N-6 `_divergence_note` matches ledger rows by bare substring — fragile if a second row names n3.
- N-7 `written_rule` in the sidecar is retyped rather than read from the primitive's cell.
- N-9 the coverage span is not printed on the figure (recoverable from the sidecar).
- N-10 `trigdat_note` in the step-1 QC ECSV still says "0.00 deg" where the rest uses "°".

**Process note (PI, 2026-09-05, verbatim): "it is too much time for 1 GRB."** Standing change
for the rest of this burst: ONE verification pass per product, nits documented and accepted,
no iteration loops.

# Skill: Literature Harvest (Step 0b) — find, fetch, and mine the REFEREED papers for a burst

**Purpose:** for the burst in hand, find every refereed paper that analyses it, fetch the
version of record, extract the values that bear on our steps, and file them for the P3 diff.
`GCNIntelligence.md` handles circulars; **this handles journals.**
**Audience:** whoever runs Step 0. **Time:** ~15 min/burst once the token is loaded.
**Why it exists:** the goal is a pipeline that reads the literature for all 106 bursts. That
cannot be ad hoc — this file is the repeatable procedure (first written 2026-08-10 after
running it three times by hand on bn090530760).

## Inputs
```yaml
trigger:      bn#########
grb_name:     GRB YYMMDD[A/B]        # resolved in Step 0 — DO NOT skip, see T1
ads_token:    source ~/Desktop/Projects/FXTs/.env   # ADS_DEV_KEY (Astrograph's is STALE/401)
corpus:       Skills_training/ + corpus_index.csv
```

## Outputs
- PDFs in `Skills_training/<First>_<year>_<bibcode>_PUB.pdf` (+ arXiv copy if it exists)
- a row per paper in `Skills_training/corpus_index.csv` (`theme`, `cited_by_bursts`, `read`, `read_date`)
- a **PUBLISHED VALUES (for the P3 diff)** section in `results/gcn/<trigger>/<trigger>_dossier.md`

## Phase 1 — Find (query in FOUR forms; one is never enough)
```bash
source ~/Desktop/Projects/FXTs/.env; K="$ADS_DEV_KEY"
q(){ curl -s -G "https://api.adsabs.harvard.edu/v1/search/query" -H "Authorization: Bearer $K" \
   --data-urlencode "q=$1" --data-urlencode "fl=bibcode,title,year,doctype,citation_count,property" \
   --data-urlencode "rows=25" --data-urlencode "sort=citation_count desc"; }
q 'full:"GRB 090530B"'      # the NAME, with the letter suffix
q 'full:"bn090530760"'      # the GBM TRIGGER NAME  <- catches catalog papers the name misses
q 'full:"090530760"'        # bare fraction-of-day form
q 'full:"265400066"'        # the trigger NUMBER
```
Keep only `doctype` ∈ {article, eprint}; circulars are Step 0a's job.
**Series check:** if a hit belongs to a numbered series (e.g. *Comprehensive Analysis I–IV*),
fetch the WHOLE series — different parts serve different pipeline steps.

## Phase 2 — Fetch the VERSION OF RECORD
```bash
# ADS reports openness; PUB_OPENACCESS => the journal PDF is legitimately free
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
  -o "Skills_training/<Name>_PUB.pdf" "https://iopscience.iop.org/article/<DOI>/pdf"
head -c4 <file> | grep -q '%PDF' || echo FAILED
```
Keep BOTH versions when they exist: **arXiv extracts more reliably** for machine parsing,
**published is authoritative** for citation. Preprint page counts are often 3–4× the journal's.

## Phase 3 — Mine (what our steps actually need)
| our step | harvest |
|---|---|
| 5 binning | their bin edges / block counts (free external validation — Li & Zhang 2021 gave us bn081224887's 9 blocks + edges to 3 decimals) |
| 6 fitting | per-interval Ep, α, β, kT, model preference, statistic, **detector set**, energy ranges |
| 7 temporal | T90 (**with band!**), lag + its sign convention, pulse width + ITS DEFINITION, evolution class |
| 9 QC | their stated caveats, exclusions, and which detectors they dropped and why |

Extract with `fitz` (PyMuPDF) — see T4 for the parsing traps.


## Phase 3b — WEIGHTING: latest analyses first (Vikas, 2026-08-10)
When several papers analyze the same burst, **read and diff the MOST RECENT first**: methods
standardize over the years (Bayesian/DIC replacing χ², response handling maturing, catalogs
superseding GCN prelims), so the newest analysis is usually the strongest comparison frame.
The older papers still get harvested — they show the field's trajectory and carry unique data —
but on a value conflict between eras, the recent frame is the default reference, and the GCN
circular is always PRELIMINARY by its own statement.
## Phase 4 — FRAME-ALIGN before recording (L21; non-negotiable)
Record, next to every number: **Ep convention** (νFν peak vs e-folding `Ec` vs break energy —
`Ep = (2+α)·Ec`), **index sign**, **energy band**, **time interval AND its T0**, **detector set**.
Apply known physical corrections before calling anything a discrepancy — e.g. **T̄₉₀ ∝ E^−0.20**
(Qin+2013), which resolved bn090530760's 194/157.7/113 s "inconsistency" to 2 decimals.

## Phase 5 — File it
Append to the dossier under **PUBLISHED VALUES (for the P3 diff)** with the verbatim quote or
table row; update `corpus_index.csv` (`read=N` until Vikas confirms he has read it; stamp
`read_date` when he does).

## 🔴 Traps — every one of these was hit for real
- **T1 SAME-DAY CONTAMINATION.** `bn090530760`'s ADS query returned 26 hits, most belonging to
  **GRB 090530A** — a different burst 15 h earlier — including a redshift (z=1.266) that would
  have entered our dossier. **Always verify identity by trigger number/time, never by name
  alone**, and mark contaminated hit-files as such.
- **T2 A SERIES SPLITS ACROSS STEPS.** Comprehensive Analysis I (spectral components) → Step 6;
  II (Ep evolution) → Step 6; III (energy-dependent T90) → Step 7; IV (lag) → Step 7.
- **T3 SYMBOLS ARE DEFINED TWICE.** Lu+2018 defines `W = T_d + T_r` (10% level, §3) and then
  `W = FWHM` (§4, pointing at the same Table 4). **Copy the definition with the number**, or the
  diff is meaningless.
- **T4 PDF PARSING.** The `±` and `−` in journal PDFs are NOT ASCII — regexes with typed `±`/`-`
  silently match ZERO rows. Normalise (`−–—`→`-`) and split on row anchors instead of trusting
  a single big regex. Always print the parsed COUNT and compare to the paper's stated N.
- **T5 PAPERS CONTRADICT THEMSELVES.** Lu+2018 states t_p is *"negatively related to E"* and then
  says lower-energy pulses *"peak earlier"* — mutually exclusive. Record the inconsistency
  (P4), never silently pick one (L26).
- **T6 CHAINED CITATIONS ROT.** Li 2019 lists "Best Model = Band+BB … (Iyyani 2016)" — Iyyani
  fitted synchrotron+BB, never Band+BB (L22). Verify at the PRIMARY source.
- **T7 CLAIMS ARE CONTINUUM-RELATIVE.** "This burst requires a blackbody" is a statement about
  the continuum it was measured against (Burgess+2014 vs Band). Record the continuum (L22).

## Quality checklist
- [ ] All four query forms run; identity verified by trigger, not name.
- [ ] Published version fetched where `PUB_OPENACCESS`; both versions kept.
- [ ] Every harvested number carries convention + band + interval + T0 + detector set.
- [ ] Parsed table row count matches the paper's stated N.
- [ ] Internal inconsistencies recorded, not resolved silently.
- [ ] `corpus_index.csv` updated; `read` flag honest (only Vikas sets `Y`).

## Hand-off
Feeds **P1 (verify at source)** and **P3 (diff)** of the `SpectralFitting.md` reconciliation
protocol, and the published-value tables in Steps 6/7. Blind-first still governs: harvesting
here is allowed and expected; **the FIT starts blind.**

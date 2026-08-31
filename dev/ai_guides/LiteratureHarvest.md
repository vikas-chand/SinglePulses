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
q 'full:"100707.032"'       # the DOTTED fraction-of-day form (Yu+2015 prints it this way)
```
⚠ **FOUR FORMS ARE A FLOOR, NOT A CEILING** (106-campaign batch 2, 2026-08-12): on
bn100707032 — a 27-paper burst — **five refereed papers were missed by every one of the four
forms** (Yu+2019, Preece+2016, Yu+2015, Hakkila+2015, Qin+2013). Causes: the dotted
`100707.032` spelling, tables indexed as images, and machine-readable-table-only membership.
Recovery channels that DID work and are now part of the step: the dotted form above; grepping
the LOCAL corpus PDFs for the 6-digit fragment (`fitz` over `Skills_training/*.pdf`);
following the citation graph of any dedicated paper; Phase 1b (Scholar); and — since the
Golkhou miss (T10, 2026-08-30) — a **VizieR MEMBERSHIP SWEEP**: query the CDS TAP/vizquery
GRB catalog tables (`J/*`) for the trigger number and both name forms, because a population
paper's burst membership often lives ONLY in its machine-readable table. **A burst is not
"paperless" until the recovery channels have also run.**
Keep only `doctype` ∈ {article, eprint}; circulars are Step 0a's job.
**Series check:** if a hit belongs to a numbered series (e.g. *Comprehensive Analysis I–IV*),
fetch the WHOLE series — different parts serve different pipeline steps.

## Phase 1b — the GOOGLE SCHOLAR channel (Vikas, 2026-08-12, from the Eric Burns exchange)
The four-form ADS query is keyed on OUR vocabulary — it fails precisely when the connecting
literature doesn't use it. **The specimen:** the ZTF FBOT-rate paper (arXiv 2105.08811) contains
not a single occurrence of "GRB" or "gamma", so no GRB-termed full-text search can ever surface
it; yet a Google Scholar query on `gamma ray burst lfbot` returned the argument-bearing paper as
its top hit (Eric Burns → Vikas, 2026-08-12). Scholar's full-text index + citation-weighted
ranking bridges vocabulary gaps between communities better than fielded ADS search.
**WHEN to use it:**
1. the ADS four-form query comes back thin or empty (our paperless bursts);
2. cross-community concept queries — the two literatures don't share terms (GRB ↔ LFBOT,
   prompt ↔ shock-breakout, …): query `<our term> + <their phenomenon>`;
3. discovery-plane bridging sweeps (the A′ jump class: long/stale/never-co-cited paths).
**RULES:** Scholar has no API and no exportable metadata — it is a *finding* channel only
(human browser, or a browsing agent). Every hit is resolved BACK to an ADS bibcode before it
enters a dossier, corpus row, or citation (the ADS-export bibliography doctrine is untouched:
Scholar finds, ADS verifies). Record the Scholar query string in the harvest manifest when a
paper enters through this channel — the query IS the bridge, and bridges are discovery-plane
data.

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

## Phase 3c — SCOPE: analyze prompt-only; SCOPE the rest of the literature anyway (Vikas, 2026-08-11)
This Agent is a **prompt-emission module** — but the scope lock binds the ANALYSIS, not the
reading (same shape as blind-first: it governs the fit, not what we may read).
- **ANALYSIS scope (hard):** reconciliation targets, P0 predictions, and diff items are
  prompt-phase ONLY — prompt spectroscopy, prompt temporal properties, prompt-relevant
  detector/response decisions. No afterglow closure, SN photometry, or cosmology quantity
  is ever a target.
- **READING scope (unrestricted):** the four-form query finds the whole multiwavelength
  record anyway — keep it. Fetch and catalog afterglow / associated-SN / cosmology /
  multimessenger papers in the corpus index with a future-module tag (`module-future;
  afterglow|sn|cosmo|mm`), and give them a real summary in the dossier under a
  **BEYOND-PROMPT CONTEXT (future modules)** heading — what was measured, by whom, and
  what it implies for the burst's identity. This is groundwork the future sibling modules
  inherit, and raw material for the discovery plane (creative jumps live in bridged
  domains); it also tells us what the literature *wants* the prompt spectrum to be (e.g. a
  photospheric interpretation riding on an SN association) — a bias we disclose in P3.
- **VIKAS'S READING LIST is curated to prompt sections (Vikas, 2026-08-11):** when
  handing him a burst's reading list, name the prompt-relevant SECTIONS of each paper
  ("§3–4 prompt spectroscopy; §5 afterglow — defer") so his reading time lands on what
  the current module reconciles. The deferred sections stay cataloged; *"later when I
  reach afterglow I will read those too"* — the `module-future` tags are his future
  reading shelf, ready-made.
The long-term architecture (recorded, not current work): a multi-module system where
afterglow, SN, multimessenger, and cosmology are sibling modules alongside this one.


## Phase 3b — WEIGHTING: latest analyses first (Vikas, 2026-08-10)
When several papers analyze the same burst, **read and diff the MOST RECENT first**: methods
standardize over the years (Bayesian/DIC replacing χ², response handling maturing, catalogs
superseding GCN prelims), so the newest analysis is usually the strongest comparison frame.
The older papers still get harvested — they show the field's trajectory and carry unique data —
but on a value conflict between eras, the recent frame is the default reference, and the GCN
circular is always PRELIMINARY by its own statement.
## Phase 4 — FRAME-ALIGN before recording (L21; non-negotiable)
Record, next to every number: **Ep convention** (νFν peak vs e-folding `Ec` vs break energy —
`Ep = (2+α)·Ec`), **index sign**, **energy band**, **time interval AND its T0**, **detector set**,
**component coverage** (T9: precursor / main / total).
Apply known physical corrections before calling anything a discrepancy — e.g. **T̄₉₀ ∝ E^−0.20**
(Qin+2013), which resolved bn090530760's 194/157.7/113 s "inconsistency" to 2 decimals.

**MULTI-INSTRUMENT CONSENSUS (Rossi+2026 §4.1 procedure, adopted 2026-08-11):** when several
instruments publish Ep/fluence for one burst, do NOT pick a favorite — take the estimates from
ALL instruments and fold the inter-instrument spread into the uncertainty of any combined value
(their "conservative approach": BAT re-analysis + GBM + KW → Ep,i = 123 ± 28 keV, an error
dominated by the spread, not any single fit). A cross-instrument disagreement is a SYSTEMATIC
to propagate, never a choice to hide. Use the consensus value (with its inflated error) for any
correlation-plane placement; keep the per-instrument values in the dossier for the P3 diff.

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
- **T8 A "Log(Likelihood)" COLUMN MAY NOT BE lnL.** Wang+2019 App. C labels a column
  Log(Likelihood), but PL row 430.03 with AIC 864.17 ≈ 2·(430.03)+2k — the column stores a
  POSITIVE fit statistic (−lnL-like), not lnL (caught in the 2026-08-11 reading package;
  PDF-verified same day). **Before using any published likelihood/AIC/BIC in a diff, recompute
  one row's AIC from the reported statistic and k to fix the sign/convention** — a sign error
  here silently flips every model comparison you inherit. Same package, same table: the
  BB verdict's ΔAIC depends on the BASELINE (Band vs Band+BB = 10.0; CPL vs CPL+BB = 20.3 in
  the same interval) — record margins against a NAMED baseline, never "the" ΔAIC (the
  published twin of our Codex-audit union-rule fix, same day).
- **T9 A PUBLISHED NUMBER BELONGS TO A COMPONENT, NOT JUST A BURST.** GRB 180728A
  (Rossi+2026 §2.1): the emission spans a ~3 s precursor + a main pulse running t0+11 → t0+40 s,
  yet "the" BAT T90 = 8.68 ± 0.30 s describes the MAIN PULSE ONLY — and per Rossi, GBM
  "detected its precursor" while Wang+2019 analyze BOTH spikes with GBM. Duration, fluence, and
  Ep all inherit the instrument's trigger + band + threshold, i.e. WHICH COMPONENT(S) sat inside
  its window. **Label every harvested number with its component coverage** (precursor / main /
  total) in the dossier's PUBLISHED VALUES table — a T90 or Ep diffed across mismatched
  component coverage is a manufactured discrepancy (D4's sharper sibling).
- **T10 TABLE-ONLY MEMBERSHIP (bn110920546, 2026-08-30 — caught by the PI at the step-0b
  gate).** Golkhou+2015 (`2015ApJ...811...93G`) carries a **published MVT upper limit
  dt_min < 2.096 s for THIS burst** in its machine-readable Table 2 — and was missed by all
  four ADS forms + extras because the paper's TEXT names no individual triggers. It was
  LOAD-BEARING: our catalog Haar MVT (5.342 s, "detection") violates the limit by 2.5×.
  **A population/catalog paper's membership must be checked in VizieR (TAP over `J/*` GRB
  tables, by trigger number + both name forms), not only in ADS full text.** The recovery
  channel is now in Phase 1's floor list.
- **T11 CROSS-BURST PDF TAGS DEFEAT FILENAME DEDUP (same incident).** The Golkhou PDF was
  ALREADY ON DISK as `Golkhou_2015_2015ApJ81193G_bn120119170.pdf` — filed under another
  burst's tag — while the bn110920546 harvest recorded the paper as absent. **De-duplicate
  and search the local corpus by BIBCODE (corpus_index + on-disk filename fragment), never
  by the trigger-suffixed filename alone.**

## Quality checklist
- [ ] All four query forms run; identity verified by trigger, not name.
- [ ] VizieR membership sweep run for population/catalog papers (T10).
- [ ] Published version fetched where `PUB_OPENACCESS`; both versions kept.
- [ ] Every harvested number carries convention + band + interval + T0 + detector set.
- [ ] Parsed table row count matches the paper's stated N.
- [ ] Internal inconsistencies recorded, not resolved silently.
- [ ] `corpus_index.csv` updated; `read` flag honest (only Vikas sets `Y`).

## Hand-off
Feeds **P1 (verify at source)** and **P3 (diff)** of the `SpectralFitting.md` reconciliation
protocol, and the published-value tables in Steps 6/7. Blind-first still governs: harvesting
here is allowed and expected; **the FIT starts blind.**

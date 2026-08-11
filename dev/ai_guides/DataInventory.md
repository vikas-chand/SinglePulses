# Skill: Step 1 — Data inventory & response-validity QC (per burst)

**Purpose:** Before any binning or fitting, confirm (a) every file the fit will need is on
disk, and (b) **every detector's response is VALID over the source window**. An invalid
response does not crash — it silently produces a converged fit with the wrong effective
area. First real use: the 5-burst LLE batch, 2026-07-31.

**Audience:** AI agent or human. **Time:** ~1 min/burst (no fitting).
**Outputs:** `results/qc/<trigger>_step1_response_coverage.ecsv` (+ the manifest row).

## Inputs
```yaml
trigger:   bn#########
selection: results/background_intervals.ecsv   # stamped SRC_START/SRC_STOP + DETECTOR list
data:      data/<trigger>/                     # cspec/tte/rsp(2)/poshist/trigdat (+ gll_* for LLE, LAT/ for >100 MeV)
```

## Phase 1 — File manifest
Count and record: `cspec`, `tte`, `rsp2`/`rsp`, `poshist`, `trigdat`, LLE triplet
(`gll_lle_*.fit`, `gll_pt_*.fit`, `gll_cspec_*.rsp`), `LAT/` FT1+FT2. Missing `trigdat` is a
note, not a blocker, when `poshist` is present (geometry is covered).

## Phase 2 — Response VALIDITY (the part that matters)
For each approved detector, resolve the response and test it against the **stamped source
window** — not the block span (be conservative).

**Naming differs by detector class — a single glob WILL produce false alarms (D2):**
- GBM: `glg_cspec_<det>_<trigger>_v*.rsp2` **or** `.rsp` (some bursts ship single-matrix `.rsp`)
- LLE: `gll_cspec_<trigger>_v*.rsp` (**no detector token**, single matrix) or `gll_lle_*.rsp*`

**GBM multi-matrix `.rsp2`:** PASS if `min(TSTART) ≤ SRC_START` and `max(TSTOP) ≥ SRC_STOP`
(times relative to `TRIGTIME`). This is the bn100130729 lesson.

**Single-matrix `.rsp` (incl. every LLE response): interval overlap is the WRONG test — use
the OFF-AXIS ANGLE (D1).**

## Quality checklist
- [ ] every approved detector resolved to an actual response file (correct naming per class)
- [ ] GBM `.rsp2` coverage brackets the stamped source window
- [ ] **single-matrix/LLE responses checked by Δθ, not by interval overlap**
- [ ] Δθ computed from `gll_pt_*` (TRIGTIME taken from a response/TTE header — the pointing
      file's own header does NOT carry TRIGTIME)
- [ ] verdict + per-detector table written to `results/qc/<trigger>_step1_response_coverage.ecsv`

## §Distilled lessons

### D1 — A single-matrix DRM is valid where its OFF-AXIS ANGLE is valid, not where its TSTART/TSTOP are  *(2026-07-31, the 5-burst LLE batch)*
LLE responses are built by `mkdrm_ez` **for one specific interval** (header TSTART/TSTOP), while
the LLE `.pha` spans ±1000 s. `scripts/10` passes that `.rsp` straight into
`TimeSeriesBuilder.from_lat_lle(rsp_file=…)` **with no validity check**, so a source window
outside the DRM's interval silently gets the wrong effective area.

**But interval mismatch is NOT the diagnostic.** LLE/LAT effective area is a strong function of
the source's **off-axis angle θ**; the DRM is only wrong if θ CHANGED between the DRM's interval
and the source window. Test it directly:
> θ(t) = angular separation between the source (RA,Dec) and the spacecraft **+z axis**
> (`RA_SCZ`,`DEC_SCZ` in `gll_pt_*`). Compare θ over the DRM interval vs over the source window.
> **Δθ ≲ 4° → response is fine. Δθ ≳ 15° → response is INVALID; regenerate the DRM.**

Measured on the batch (all four "interval-mismatched" by the naive test):
| burst | DRM θ | source θ | Δθ | truth |
|---|---|---|---|---|
| **bn130427324** | 48.1° | 36.5→**23.0°** | **19.9°** | **INVALID — Fermi slewed; DRM built on pulse 1, we fit pulse 2 (119–178 s)** |
| bn130518580 | 41.8° | 41.3→42.8° | 0.2° | fine |
| bn081224887 | 17.9° | 17.9→17.8° | 0.2° | fine |
| bn130310840 | 76.1° | 76.1→76.3° | 0.1° | fine |

**Why it survived:** the fit converges either way; nothing in 3ML or the pipeline knows the DRM
has a validity domain. Only a burst where the spacecraft SLEWED (a bright LAT burst — i.e.
exactly the bursts the LLE arm exists for) exposes it. **Detection:** the Δθ check above.
**Fix:** regenerate the LLE DRM for the actual source interval (`mkdrm_ez`/gtburst) before
fitting; until then, quarantine the LLE plugin for that burst and fit GBM-only.
**Generalizes:** any single-matrix response — and `HAS_LAT` bursts are precisely the slewing ones.

### D2 — One glob does not fit all detector classes  *(same batch)*
My first pass globbed only `glg_cspec_<det>_*.rsp2` and reported "NO RSP2" for every LLE
detector **and** for a burst that ships `.rsp` instead of `.rsp2` (bn130310840) — 5 false alarms,
0 real. **A Step-1 FAIL must be confirmed against the naming the pipeline itself uses**
(`scripts/10::find_rsp`, `find_lle_files`; `scripts/27c::find_lle_triplet`) before it is
reported as a data problem. A QC check that cries wolf trains you to ignore it.

### D3 — TRIGTIME is not in the pointing file  *(same batch)*
`gll_pt_*.fit` carries no `TRIGTIME` in its primary or table header; take it from a response or
TTE header. Silent `None` propagation makes the Δθ check fail with a TypeError, not a wrong
answer — but budget for it.

### D4 — a detection is a statement about an INTERVAL, and the trigger time is not the burst start  *(bn120624933, 2026-08-08)*
GRB 120624B carries a 10σ LAT headline — and none of it is in our window: Ajello+2019
`tab_durations` gives **T_LAT,0 = 73.7 s**, 47 s AFTER our window closes, with the ≥100 MeV
signal peaking at 380±20 s. Worse, GBM triggered on the THIRD of three emission episodes
(triggering was disabled at high geomagnetic latitude for the first two, GCN 13377 verbatim) —
our entire analysis covers ~10% of the burst, and the catalog T90 = 271 s describes emission we
never observed.
**RULE:** during inventory, (a) never treat trigger time as burst start — check the catalog
T05/T95 and the GCNs for pre-trigger episodes; (b) before expecting a published LAT/LLE
detection to imply structure in OUR window, look up the detection's own interval
(T_LAT,0/T_LAT,1). A detection outside the window predicts nothing inside it — in either
direction.

### D5 — BLOCKAGE is invisible to the angle rule; catch it in the residuals  *(bn130518580 vs Siddique+2022, 2026-08-09)*
Our detector rule tests the **geometric** source angle. A detector can pass that test and still
be **occulted** by spacecraft structure (solar panel, LAT, radiators) — the angle is fine, the
path is not. Siddique+2022 hit exactly this on a burst we had already analysed, verbatim:
> *"Initially, we kept the n6 detector as well; however, it showed a clear trend of negative
> residuals in the fits compared with the n3 and n7 detectors. As discussed by Goldstein et al.
> (2012), this indicates **blockage** and the particular detector is removed from the analysis."*

**We kept n6** (32.4°, geometrically clean) in every bn130518580 fit. The signature was in our
own output and we misread it: across 25 fits the EAC cross-norms give **n6 = 0.890** against the
n3 reference (an ~11% deficit), and the degeneracy propagates — **n7 rails at its 0.800 floor in
76% of fits** while both BGOs push high to compensate. Our four-channel panel *saw* this (one
NaI 30–40% below another, 20–300 keV, coherent −1…−3.5σ residual run; railed cross-norms) and
labelled it "cross-calibration". The cause is a blocked detector. The affected band, 20–300 keV,
is exactly where the contested low-energy shoulder lives.

**RULE — inventory must test blockage, not just angle:**
1. compare each NaI's residual trend against the OTHER NaIs at similar angles — a *coherent*
   one-sided run (not scatter) is the blockage signature;
2. treat a cross-norm sitting systematically low (≲0.9) or a neighbour railing at a bound as
   corroboration, never as "calibration";
3. **Exclusion is a recorded decision**, never a silent one. Log: viewing angle · residual
   pattern · geometry/blockage evidence · response version · **fits WITH and WITHOUT** ·
   rationale (protocol adopted from the v3 reading package, which took it from this paper).
4. ⚠ **A detector may NOT be removed merely because its inclusion weakens a preferred
   component.** The with/without pair is retained either way, so the reader can judge.

**THE DATA-DROPPING HIERARCHY (Vikas, 2026-08-10: "we are not supposed to drop data no
matter what") — three cases, never blurred:**
1. **Production fits NEVER drop data that passes the quality gate.** Not for convenience,
   not for significance, not because a model fits better without it (L17). No exceptions.
2. **With/without refits are DIAGNOSTICS only** — legitimate for LOCALIZING a systematic
   (the D5 blockage test), but a data-dropped fit can NEVER be quoted as a result, never
   be evidence FOR a scientific claim, and never silently replace the full-data fit. The
   four-channel adversary's drop-BGO run is the cautionary case: our own adjudicator
   flagged the inference as over-read — removing a detector removes information along
   with the suspected systematic, so the comparison is confounded by construction.
3. **Quality exclusion is the ONLY path to omitting data from production**, and it runs
   through the documented gate: demonstrated response invalidity (D1 off-axis) or
   demonstrated blockage (D5 residual coherence + cross-norm evidence), recorded with the
   full protocol (angle, residuals, evidence, with/without pair retained, rationale), and
   reported prominently in the burst record. An exclusion without this record is a
   doctrine violation.

## Hand-off
Feeds Step 5 (binning) and Step 6 (fitting). A burst failing D1 must NOT enter a joint
GBM+LLE fit until its DRM is regenerated — the high-energy component is exactly what the bad
effective area corrupts.

# Pipeline flags — findings for Vikas (2026-08, Khushboo's arm)

Everything below was **measured on this machine**, not inferred. Each flag gives evidence, a
reproduction, and a proposed fix. Severity is about *silent scientific damage*: a flag that
crashes loudly is less dangerous than one that quietly changes a number.

| # | flag | severity | scope | status |
|---|---|---|---|---|
| F-1 | `find_tte` matches only `*.fit.gz` → detectors silently dropped | **HIGH** | every burst with uncompressed TTE | open (worked around locally) |
| F-2 | Approved catalog violates its own window-validation rule | **HIGH** | 21 rows / 13+ bursts | open |
| F-3 | 27b background auto-order `FitFailed` on very bright bursts | MED-HIGH | 130427A (blocks Stage 2 entirely) | open, fix known |
| F-4 | `emission_window()` overrides the approved source window | MEDIUM | every burst with a faint tail | open, quantified |
| F-5 | Post-background window sitting on the burst tail | MEDIUM | per burst | fixed for bn200524211 |
| F-6 | `HAS_LAT=True` does not mean usable prompt LAT data | MEDIUM | LAT bursts | documentation |
| F-7 | Single-pulse membership not verified against controls | MEDIUM | sample-wide | open |
| F-8 | Pre-background window shorter than the strict 50–150 s rule | LOW/INFO | data-limited bursts | unavoidable, record it |

---

## F-1 — `find_tte` matches only `*.fit.gz`; detectors are dropped **silently** — HIGH
`scripts/10_spectral_fit_burst.py:87`
```python
m = sorted(glob.glob(os.path.join(DATA_DIR, trigger, f'glg_tte_{det}_*.fit.gz')))
return m[-1] if m else None
```
An **uncompressed** `glg_tte_n9_*.fit` returns `None`, the detector is skipped, and the fit
proceeds on whatever survives — **no error, no warning in the driver log**.

**Damage measured (our 5-burst run, first pass):**

| burst | detectors the fit actually used | should have been |
|---|---|---|
| bn130310840 | **lle only** | n9,na,nb,b1,lle |
| bn201104001 | **lle only** | n6,n7,n8,b1,lle |
| bn151006413 | n5,lle | n0,n1,n3,n5,b0,lle |

The two LLE-only fits are scientifically meaningless (30–100 MeV alone) yet completed with
`exit 0` and produced full 803-column result tables. We only caught it by plotting per-bin
count spectra and noticing `N_DETS=1`.

**Reproduce:** `ls data/<trig>/glg_tte_*.fit` (uncompressed) → run Stage 3 → inspect
`PLUGIN_DETS` / `N_DETS` in `spectral_fits.ecsv`.

**Fix:** glob `*.fit*` (and prefer the newest version), i.e.
`glob.glob(...f'glg_tte_{det}_*.fit*')`. **And make a missing approved detector LOUD** — an
approved detector that yields no plugin should print a warning and be recorded, never vanish.
*Local workaround applied:* we gzip TTE before fitting. That is a band-aid, not a fix.

**Cross-check:** this is the same failure class as lesson **L17** (*"never drop a detector for
low significance; the inclusion gate is DATA QUALITY"*) — here a **filename convention**
became an undeclared inclusion gate.

---

## F-2 — The approved catalog violates its own hard validation rule — HIGH
`source_selection.md` states the constraint (and says ingest rejects a burst that breaks it):
> `pre_stop <= t1` and `t2 <= post_start` for EVERY approved detector.

**Sweep of `results/background_intervals.ecsv` (435 rows, 106 bursts): 21 rows fail.**

`src_stop <= post_start` violated — **16 rows, 13 bursts** (post-background window overlaps the
source window, i.e. the background is fitted *on burst emission*):

| trigger | det | overlap (s) |
|---|---|---|
| bn090530760 | b0 | **136.00** |
| bn120905657 | n7 | **62.51** |
| bn171210493 | b0 | 46.61 |
| bn110920546 | b0 | 31.84 |
| bn120905657 | na | 21.51 |
| bn190401139 | b1 | 12.23 |
| bn090530760 | n1 | 12.00 |
| bn110605183 | b0 | 9.28 |
| bn230802285 | n5 | 9.22 |
| bn101126198 | b1 | 7.03 |
| bn180723757 | b1 | 4.58 |
| bn100614498 | n6 | 4.40 |
| bn200524211 | b0 | 3.84 |
| bn221209243 | n5 | 2.07 |
| bn110928180 | b0 | 1.45 |
| bn221209243 | n1 | 0.07 |

`pre_stop <= src_start` violated — **5 rows**: bn241223506 b0 (8.49 s), bn240204630 b1 (3.15),
bn220525008 b0 (1.99), bn100614498 b1 (1.60), bn101126198 b1 (0.44).

**Effect:** background over-estimated for those detectors → source flux under-estimated and the
spectral shape distorted (the contamination is not spectrally flat). BGO rows dominate the list,
so it mainly biases the high-energy end — exactly where two-break/thermal claims live.

**Reproduce:**
```python
from astropy.table import Table
t = Table.read('results/background_intervals.ecsv', format='ascii.ecsv')
[ (r['TRIGGER_NAME'], r['DETECTOR'], float(r['SRC_STOP'])-float(r['BKG_POS_START']))
  for r in t if float(r['SRC_STOP']) > float(r['BKG_POS_START']) ]
```
**Fix:** run `_validate_decision` over the *shipped* catalog (not only at ingest) as a CI check,
and re-window the 21 rows. Cheap to detect, invisible otherwise.

---

## F-3 — 27b background polynomial `FitFailed` on very bright bursts — MED-HIGH
**GRB 130427A (`bn130427324`) cannot be binned at all**: Stage 2 aborts with
`threeML.minimizer.minimization.FitFailed`, from
`threeML/utils/time_series/polynomial.py:302` → `jl.results.covariance_matrix` is `None`.

3ML auto-selects **order 3**; the unbinned MLE fit on ~1.4 M events returns no covariance.
Contributing factor: the approved post-background window (192–261 s) still sits on the pulse's
slow decline, so a cubic is ill-conditioned.

**Verified fix:** force a low order — order **0** succeeds and yields **10 clean blocks**.
```python
ts = TimeSeriesBuilder.from_gbm_tte("n9", tte_file=..., rsp_file=...)
ts._time_series._user_poly_order = 0            # then set_background_interval(...)
```
`scripts/10` already tolerates this class of failure (it skips the offending detector and
carries on); **27b has no such fallback** — one detector failing kills the whole burst.

**Proposed fix:** in 27b, catch `FitFailed` and retry at descending fixed order (2 → 1 → 0),
mirroring scripts/10. Note the burst's window is *correct* — the GBM catalog marks 130427A
`class=single, score=1.0`, and 119–178 s is a clean isolated broad pulse; the main 0–20 s phase
is multi-peaked/saturated and rightly excluded.

---

## F-4 — `emission_window()` silently overrides the approved source window — MEDIUM
Full write-up: `dev/ai_guides/Binning.md` **L5-1**. Summary: 27b re-tightens the approved
window using a **greedy per-bin (0.256 s) 1σ walk on the reference detector alone**, so faint
extended tails are cut. On bn200524211 the approved `t2=36.0` became **27.35 s**, discarding
27–36 s emission measured at **6.7–8.2σ per 5 s** (stacked n0+n1+n3). The approved window is
therefore *advisory*. Fix: stacked + integrated-significance walk, or a `--no-tighten` flag.

**Severity qualifier (measured 2026-08-12, bin-11 panel).** For *this* burst the clipping costs
little **science**, even though the mechanism is wrong. The recovered tail block
`bin 11 [20.33, 27.35] s, S=7` shows **every model within ~2 AIC** (CPL 4885, Band+BB 4885,
SBPL 4886, SBPL+BB 4886, Band 4887, DSBPL 4887 → evidence ratio ~1.6:1) and almost all channels
become 2σ upper limits after rebinning. Faint tail bins therefore **cannot discriminate models
at all**. So F-4 is a *correctness* defect, not a lost result here — but it WOULD bite on a burst
with a bright or hard tail, where those bins carry real spectral information. Fix it on the
mechanism, do not de-prioritise it on this burst's outcome.

---

## F-5 — Post-background window contaminated by the burst tail — MEDIUM
bn200524211: approved post window started at **41 s**, but residual emission persists to ~56 s
(**+4.56σ / +4.44σ** in n0 / n1 over 41–60 s, independent background). Fitting background there
biases it high; correcting to **(65, 137)** raised net source counts by **+2.7 % (n0)** and
**+2.3 % (n1)** — a ~3σ systematic against a 0.9 % statistical error, i.e. a fluence bias.
Verified clean beyond 65 s (no excess anywhere in 60–150 s with a far-anchored background).
**Generalise:** check the post window against the *tail*, not against T90.

---

## F-6 — `HAS_LAT=True` ≠ usable prompt LAT data — MEDIUM
bn200524211 is flagged `HAS_LAT=True`, but GCN 27797 states Fermi-LAT was **in the SAA at
trigger** and observations only began at **T0+110 s** (9.2 GeV photon at T0+748 s). The prompt
pulse (0–36 s) therefore has **no LAT/LLE coverage at all**. Any LAT arm here constrains only
late emission. Recommend a per-burst `LAT_PROMPT_COVERAGE` field rather than a bare `HAS_LAT`.

---

## F-7 — Single-pulse membership is not verified against controls — MEDIUM
GCN prose is not a criterion: GBM and Konus both call bn200524211 "multi-peaked", yet by a
prominence-gated peak count it is **indistinguishable from the canonical single-pulse control**
(1 peak @1.024 s / 3 @0.256 s — identical to bn110721200), while the known multi-episode control
bn160625945 gives **5 / 12**.

⚠ **Consequence:** by that same test **bn160625945 is the outlier inside its own approved
window (180–226 s) — 5 significant peaks** — and it is in the sample and already fitted
(51 blocks). Its membership needs an explicit decision. Method + figures:
`results/gcn/bn200524211/bn200524211_dossier.md`.

---

## F-8 — Pre-background window can't meet the strict 50–150 s rule — LOW/INFO
bn200524211's TTE **starts at −22.0 s**, so the maximum possible pre-window is ~19.8 s against a
"strict" 50–150 s requirement (approved: 12 s). Not an error — a **data limitation** — but it
means the baseline under the burst is anchored asymmetrically (12 s before vs 96 s after) and
leans on the post window, which is why F-5 matters more than it looks. Suggest the rule read
"50–150 s **where the data allow**; otherwise record the limit".

---

## Also worth knowing (not defects in this repo's code)
- **`jl.current_minimum` is −logL, not −2logL** (3ML). `scripts/10` handles it correctly
  (`n2ll = 2.0 * jl.current_minimum`); anything new must too, or every AIC/BIC/ΔIC is halved.
- **`scripts/41 --mode best` refits only the 6 base models**, so its "best" can disagree with the
  saved 24-model winner (documented in `docs/QUICKSTART.md`). Use `--mode bin` for diagnosis.
- **Our 5-burst run in `results/pipeline_run_6grb/` predates the 2026-08 engine update**
  (803 columns vs 830 now) — re-run before quoting any of it.

---

## F-9 — `scripts/41` hardcoded the background catalog (PATCHED) — MEDIUM
`scripts/41_nuFnu_panels.py:159` read `results/background_intervals.ecsv` unconditionally, with
no env override — while the *blocks* were already overridable via `BLOCKS_ROOT`. Any run using
corrected/alternative windows therefore got diagnostic panels drawn on the **gated catalog's**
windows, silently disagreeing with the very fit they were meant to diagnose.

**Patched** (minimal, backwards-compatible, mirrors the existing `BLOCKS_ROOT` pattern):
```python
bk = Table.read(os.environ.get("BKG_FILE",
                os.path.join(ROOT, "results", "background_intervals.ecsv")), format="ascii.ecsv")
```
Default behaviour is unchanged for everyone else. Revert freely if unwanted.

## F-10 — Engine and `scripts/41` disagree on composite-model AICs (local minima) — MEDIUM
Same bin, same data, same models — `spectral_fits.ecsv` (engine, nested multistart + T_INT
seeding) vs the `scripts/41` independent refit, bn200524211 **blk 4 [4.99, 5.95] s**:

| model | engine AIC | panel AIC | Δ |
|---|---|---|---|
| **Band+BB** | **2393.9** | 2402 | **−8.1** |
| SBPL+BB | 2395.5 (VALID=False) | 2396 | −0.5 |
| Band | 2397.4 | 2398 | −0.6 |
| **DSBPL** | 2402.1 | **2398** | **+4.1** |
| **DSBPLfree** | 2404.6 (VALID=False) | **2399** | **+5.6** |

Simple models agree within ±1 AIC; **composites disagree by 4–8 AIC**, and the two tools pick
**different winners** (engine → Band+BB, panel → SBPL+BB). Cause: different multistart paths
landing in different local minima. Consequence: the diagnostic tool cannot be used to confirm
or refute the engine's selection for composite models — which is exactly what it is for.

**Fix:** have `scripts/41` read the saved parameters from `spectral_fits.ecsv` and *evaluate*
them (optionally re-fitting from those values as the seed), rather than refitting from scratch.
Until then, treat panel AICs as indicative only, and never quote them against the engine's.

*(Context: `docs/QUICKSTART.md` already warns that `--mode best` refits only the 6 base models.
This is the same root cause, and it also affects `--mode bin`.)*

**Refinement (T_INT panel, 2026-08-12) — the disagreement is NOT universal.** Repeating the
comparison on the high-count **T_INT** interval [−0.69, 27.35] s:
**10 of 12 models agree within ±1 AIC, and both tools pick the SAME winner (SBPL).**
So the tools agree where the data are informative; F-10 concentrates in **low-count bins**
(bin 4, S=36 → 4–8 AIC spread) and in **pathological composite fits**.

The extreme case is instructive: **CPL+BB at T_INT — engine 7019.0 vs panel 8014, a 995 AIC
gap.** The panel's refit landed in a catastrophic local minimum (its residual strip shows a
coherent −4→+4 systematic wave, visible in `bn200524211_nuFnu_TINT_allmodels.png`), while the
engine's nested multistart found the real optimum. **This is direct evidence that the engine's
multistart is doing necessary work and that panel AICs must never be quoted against it** —
but also that the engine is the trustworthy side of the disagreement, not merely a different one.

---

## Appendix — code changes made in this arm (UNCOMMITTED, review before keeping)

Only **one file** was modified; everything else in this arm is new files. Both edits are
additive and backwards-compatible (defaults reproduce the previous behaviour exactly).

### `scripts/41_nuFnu_panels.py`

**(a) `BKG_FILE` env override** — see F-9.
```python
bk = Table.read(os.environ.get("BKG_FILE",
                os.path.join(ROOT, "results", "background_intervals.ecsv")), format="ascii.ecsv")
```
*Why:* blocks were already overridable (`BLOCKS_ROOT`) but the background was not, so a run made
with corrected windows got panels drawn on the gated catalog's windows — silently diagnosing a
different fit than the one on disk. *Default unchanged.*

**(b) `--bin tint` (also accepts `t_int`, `-1`)** — plot the **time-integrated** interval.
```python
is_tint = str(which).strip().lower() in ("tint", "t_int", "-1")
if is_tint:
    b, t1, t2 = -1, float(min(starts)), float(max(stops))   # = scripts/10's "BB block union"
else:
    b = int(which); t1, t2 = starts[b], stops[b]
```
Output is named `<trig>_nuFnu_TINT_allmodels.png`.
*Why:* `--bin N` indexes the **blocks** file, and T_INT is not a block — so the single interval
most often quoted against the literature (the P3 diff row) was **the one interval that could
never be diagnosed with a panel**. The window used matches scripts/10's own T_INT fallback, so
the panel and the saved T_INT row describe the same interval.

**To revert both:** `git checkout -- scripts/41_nuFnu_panels.py` (no other file is touched).

### Not modified but worth noting
`scripts/10_spectral_fit_burst.py` (F-1) and `scripts/27b_reblock_3ml.py` (F-3, F-4) were
**left untouched deliberately** — those fixes change scientific output, so they belong to Vikas.
The F-1 workaround used here was to gzip the TTE files in `data/bn200524211/`, not to patch code.

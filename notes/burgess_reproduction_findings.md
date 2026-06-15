# Burgess+2014 reproduction — can we reproduce his Bayesian blocks & Ep–kT correlation?

Date: 2026-06-03. Triggered by the question: *"Could we not reproduce the same
Bayesian blocks as Burgess for the sample common with Burgess?"*

Burgess+2014 (ApJL 784 L43) found a tight per-burst correlation
`Ep ∝ kT^α` across 6 bright single-pulse GRBs (combined Spearman ρ=0.81,
p=4.35e-20); α≈1 → baryonic jet, α≈2 → magnetic. All 6 are in our 106-burst
sample. Our first reproduction gave only ρ=0.685 and N≤2 usable pairs for 4 of
the 6 bursts. The question was whether mismatched time-binning was the cause.

## TL;DR
Reproducing Burgess's binning was the right instinct — it exposed **two real
pipeline bugs**, both now fixed:
1. **Block collapse** (090719A, 110920A): production Bayesian blocks collapsed
   the whole burst into a single ~0.06 s sliver at the *wrong time* (t≈128 s,
   205 s). → 0–1 usable bins.
2. **Blackbody seed poisoning / railing local minimum** (all bursts): the fit
   engine seeds every block's BB from the time-integrated (T_INT) fit. When
   T_INT's BB rails to kT→1 keV (which happens whenever T_INT integrates over a
   background-heavy or BB-free window), that railed seed propagates to *every*
   block, railing them all.

After fixing both, the combined correlation rose to **ρ=0.751 (p=5e-10)** — but
a leave-one-out check shows this is **dominated by GRB 130427A**. The 5 faint
bursts, on their own, show **no correlation (ρ=0.13, p=0.68)**: they have only
2–4 BB-significant bins each. So we reproduce Burgess for the *bright* burst but
not independently for the faint ones — a model-sensitivity limit, not a binning
one.

## What Burgess did (verified from the PDF, §2)
- Time bins = **Bayesian blocks (Scargle 2013) on the brightest NaI count
  rate, 8–300 keV** (binned rates, i.e. `fitness='measures'`, not events).
- Fit a physical **synchrotron + blackbody** in every bin; used **all** bins
  where both components are present (no strict per-bin significance cut).
- F_BB/F_tot ≈ 0.27–0.39 (Table 1) — the BB is a *major* (~30%) flux component.

Our pipeline instead ran **event-mode BB on 8–900 keV** with a merge step.

## Diagnosis trail (the smoking guns)
- Per-burst block counts (production vs Burgess-faithful re-block):
  081224A 9→11-13, 090719A **1→12**, 100707A 12→15, 110721A 10→13,
  110920A **1→10**, 130427A 88→77-81.
- Identical time bin [1.97,2.99 s] in 110721A: **production kT=30 keV (LRT=40)**
  vs **first re-block kT=1.23 (LRT=0)**. Same data, same model → different local
  minimum. Not binning, not physics → a *fit* problem.
- T_INT spans: production [-0.43,19.92] (BB seed = nan → fell back to default
  kT=30 → found real BB by luck); first re-block [-12.72,47.25] (60 s, mostly
  background → BB railed to kT=1 → poisoned all blocks).

## Fixes applied
1. `scripts/17_burgess_reblock.py`: Burgess-faithful blocks — brightest NaI,
   8–300 keV, **binned count-rate** Bayesian blocks (`fitness='measures'`,
   p0=0.01), restricted to the **burst emission interval** (4.5σ threshold) so
   T_INT is not background-dominated. Writes to `results/burgess_repro/blocks/`.
2. `scripts/10_spectral_fit_burst.py`: replaced the narrow LRT-guard with a
   **BB multi-start**. For each +BB model, if the BB is railed or insignificant
   (LRT<9.2), re-fit from a grid of hot kT seeds {default(30), 30, 80} and keep
   the lowest n2logL. Never worsens a fit; recovers the deep BB minimum. Added
   `--blocks-file` and `--out-dir` args so the reproduction never touches the
   production tree.

Result on 110721A: kT railed 12/13 → **0/13**; LRT_BB>9.2: 0 → 2
(blk2 kT=39.9 LRT=85, blk4 kT=22.6 LRT=11.6).

## Final numbers (LRT>9.2 gate, Ep = νFν peak per model)
| GRB      | pub α | our α (re-block) | jet match | N pairs |
|----------|-------|------------------|-----------|---------|
| 081224A  | 1.01  | n/a (N=2)        | –         | 2 |
| 090719A  | 2.33  | n/a (N=2)        | –         | 2 |
| 100707A  | 1.77  | 0.94 (N=3)       | no        | 3 |
| 110721A  | 1.24  | 2.17 (N=4)       | no        | 4 |
| 110920A  | 1.97  | n/a (N=2)        | –         | 2 |
| 130427A  | 1.02  | **0.66 (N=36)**  | **YES**   | 36 |

- **Combined:** ρ=0.751, p=5.2e-10 (Burgess 0.81). Gate sweep: ρ≈0.72–0.75 for
  LRT gates 4.6–9.2 (robust); drops at looser gates as noise enters.
- **Leave-one-out:** dropping 130427A → ρ=0.126, p=0.68. The correlation is
  **entirely the 130427A anchor**.
- **130427A internal:** ρ=0.784, α=0.66 baryonic (Burgess 1.02 baryonic),
  kT=1.6–75 keV, 36 bins → genuine reproduction.

## Interpretation
- We **reproduce Burgess for the bright burst (130427A)** cleanly.
- We **do not independently reproduce** the faint 5: only 2–4 BB-significant
  bins each, no per-burst track. Cause: our **empirical Band/CPL + BB** is more
  conservative than Burgess's **physical synchrotron + BB with Bayesian kT
  priors**. Band's flexible curvature can absorb the thermal bump, so the BB is
  significant in fewer bins. CPL+BB does better than Band+BB (CPL is narrower,
  like synchrotron) — e.g. 100707A CPL+BB reaches LRT=100–122.

## ⚠ Impact on the production run (IMPORTANT)
The BB seed-poisoning/railing bug affects **all 106 production bursts**, not just
these 6 — any block whose T_INT BB railed had its per-block BBs railed too. This
means the production sample **under-detects blackbodies**. The headline
"78% thermal-or-degenerate vs 22% two-break" curvature split and the
"no Ep–kT correlation on the full sample" result should be **re-derived after a
full production re-run with the BB multi-start engine**. Expect *more* thermal
preference once BBs are properly fit.

## Path to fully reproduce Burgess (future work)
1. Fit his actual model: a **physical synchrotron** continuum (not Band/CPL) +
   BB, ideally **Bayesian with informative kT/α priors** (Burgess conventions
   already noted in memory: α~N(-1,0.5), Ecut~N(200,300), β~N(-2.25,0.5)).
2. Re-run the full sample with the multi-start engine; re-derive the curvature
   split and the sample-wide Ep–kT correlation.

## UPDATE 2026-06-06 — companion paper settles the binning question
Downloaded the methodology companion: **Burgess+2014 ApJ 784,17**
(`Burgess_2014_ApJ_784_17_companion.pdf`, arXiv:1304.4628). §3.3 "Time Binning"
states verbatim: *"we combined the TTE data from the brightest NaI detector with
the TTE data from the BGO detector and ran a Bayesian block algorithm to find
the times of the change points. We found that a prior of 8 gave a good balance…"*

So, definitively:
- **TTE, yes** (confirmed) — and **NaI+BGO combined**, **event-mode** (on arrival
  times), with **ncp_prior = 8**. The ApJL Fig-1 "NaI 8–300 keV" curve is only a
  display; it is NOT what the blocks were computed on.
- **Reproducing this exact recipe** (combined brightest-NaI n9 + BGO b1 TTE,
  astropy event-mode, ncp_prior=8) → **13–14 blocks for 110721A**.
- **Residual cause for exact EDGES = implementation**: he fit/binned with
  **RMFIT** (§3.4); its "prior" parameter is calibrated differently from
  astropy's `ncp_prior` (same value 8, different penalty). Can't reproduce his
  exact edges without RMFIT.

### CORRECTION 2026-06-08 — total block COUNT actually matches (no 2× gap)
Counting the dotted bin-edge lines in ApJL Fig 1 (his TOTAL Bayesian blocks)
vs ours (NaI 8–900, p0=0.01, burst-interval-restricted, scripts/17):

| GRB | Burgess total (eye, ±2–3) | ours |
|---|---|---|
| 081224A | ~10 | 12 |
| 090719A | ~14 | 12 |
| 100707A | ~12 | 15 |
| 110721A | ~10 | 12 |
| 110920A | ~16–18 | 10 |
| 130427A | ~40 (dense) | 77 |

The four faint bursts match within ±2–4. **The earlier "his 5–7 vs our 13 → 2×
too many" was a CATEGORY ERROR**: 5–7 is his BB-*significant* count (the Ep–kT
correlation points, the paper's "relatively fewer data points"), NOT his total
blocks (~10). So our binning *granularity* reproduces his fine; the genuine
shortfall is in BB-*significant* bins (he ~5–7, we ~2–4 for 110721A) — the
**model** difference, not binning/prior. Also: `use_background=True` ≈ raw-event
BB (identical block count for 5/6 bursts — scripts/22); and 090719A's burst is at
t~115–185 s in our data (Burgess: t~0–16 s) while 110920A's bkg windows are only
5 s wide — i.e. those two production background intervals are offset/too-tight,
which is what collapsed them, not the BB method.
- Bonus from §3.2/Table 1: his sample of 8 had 5 with bright-enough BB — exactly
  the 5 faint bursts in our common set (081224A/090719A/100707A/110721A/110920A);
  130427A is NOT in this paper (it enters Burgess's ApJL via Preece+2014). So the
  BB *is* present in those 5 — our under-detection is a model/method limit.

Practical takeaway: to bin like Burgess, combine NaI+BGO TTE event-mode (not
NaI-only), but accept that the exact count is RMFIT-implementation-specific; show
robustness across (prior, binning) instead of chasing his exact edges.
Demonstrated by `scripts/20_bb_sensitivity.py` and `scripts/21_*`.

## Files
- `scripts/17_burgess_reblock.py` — Burgess-faithful re-blocking
- `scripts/18_burgess_repro_correlation.py` — prod-vs-reblock comparison + figure
- `scripts/19_burgess_gate_sweep.py` — ρ vs LRT-gate sweep
- `scripts/10_spectral_fit_burst.py` — BB multi-start (lines ~614+), `--blocks-file`/`--out-dir`
- `results/burgess_repro/` — blocks + per-burst fits (production untouched)
- `results/figures/fig_burgess_reblock.png`

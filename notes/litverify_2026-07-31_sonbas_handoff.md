# Verification brief — Sonbas 2013 reading handoff (§4 action items)
2026-07-31. Workflows `whkt5d73d` (7 items, 1 agent failed) + `w83xb2n74` (follow-ups, running).
Every claim carries a bibcode/URL. The citation-lineage item was ADVERSARIALLY cross-checked
(a second agent, different primitives, tried to REFUTE "still open" and failed).

| # | action item | status | answer |
|---|---|---|---|
| 1 | Update project record + install new framing | ✅ DONE | registry #37 RESTRUCTURED; `SinglePulse_Temporal/SCOPE.md`; `notes/curvature_theory.md`; idea bank #31 |
| 2 | **Citation-lineage trace of Sonbas 2013** | ✅ **DONE — MAJOR FINDING** | 13 citers. **Göktaş, Nasıroğlu & Sonbaş 2025 (`2025JARNA..11...27G`) already did a partial rest-frame redo: slope 1.01±0.04.** Gap survives (below) |
| 3 | MVT energy-dependence reference | ✅ VERIFIED | **Golkhou, Butler & Littlejohns 2015 (`2015ApJ...811...93G`)** for energy dependence; `2014ApJ...787...90G` for Haar MVT + source frame |
| 4 | MacLachlan prompt-MTS energy band | ⚠ **NEEDS MANUAL CHECK** | agent failed mid-run (API); re-running in `w83xb2n74` |
| 5 | Margutti/Kocevski params + XRF redshifts | ✅ VERIFIED | **only 9 of 19 flares have secure spec-z**; Kocevski arm N=9, Margutti arm collapses to **N=2** |
| 6 | Swift/BAT single-pulse extension | ✅ VERIFIED VIABLE | Zhang+2026 `2026A&A...707A.392Z` = 85 single-pulse, **39 spec-z**; expect **~20–30** with both lag+MVT |
| 7 | Zhang & Yan 2011 to reading queue | ✅ VERIFIED + QUEUED | `2011ApJ...726...90Z` §5.1: **slow = engine, fast = magnetic turbulence** |
| 8 | Register EP flare timing (conditional) | ✅ DONE — **verdict WAIT** | registry #41 + idea bank #32; gate 1 fails on photon statistics |
| 9 | Record the curvature argument as Sonbas's | ✅ DONE | `SinglePulse_Temporal/notes/curvature_theory.md` |

## The headline: the field moved (item 2)
**Göktaş, Nasıroğlu & Sonbaş 2025, JARNAS 11, 27** (`2025JARNA..11...27G`, doi:10.28979/jarnas.1612952)
— 162 Swift/BAT GRBs with z (2011–2019):
- **SOURCE-FRAME lag bands** (100–150 vs 200–250 keV in the source frame), LCs rebinned by 1/(1+z)
  → they fixed Sonbas 2013's central flaw.
- **Best-fit lag-vs-MTS slope = 1.01 ± 0.04**, read as curvature evidence.
- **That is our parameter-free prediction (slope 1), already measured — by Sonbas's own group.**

**What survives as ours** (independently confirmed by the adversarial agent, which read the PDF
from scratch and could not refute it):
1. **No single-pulse selection** — 162 bursts of any morphology; lag mixes pulses, MVT is set by
   the narrowest spike anywhere. The law is derived for ONE shell.
2. **No rank statistic anywhere** — no Spearman/Kendall/p-value in the text; only an OLS slope.
3. **MTS measured in the OBSERVER band** (15–150 keV, 200 μs) while the lag is source-frame → axes
   not band-matched; MVT is energy-dependent (Golkhou+2015), so the MTS's rest-frame energy drifts
   with z. **No k-correction.**
4. **BAT-only** (15–150 keV), only 8 short GRBs; no wide-band leverage.
5. **The NORMALIZATION has never been tested by anyone** — the prediction fixes slope=1 AND
   norm=E_h/E_l−1 AND intercept≈0; Göktaş reports only a slope. **This part is entirely open.**
6. Published in an obscure regional journal, **currently uncited on ADS** → invisible to the field
   (opportunity + scoop risk).

## 🔴 RETRACTION (2026-07-31, SinglePulse_Temporal terminal) — two criticisms are refutable
Sonbas p.3 reports **Spearman 0.96±0.05 AND Kendall 0.86±0.05** — RANK statistics. Therefore:
- the "shared (1+z) inflates rho" criticism FAILS: co-scaling induces only rho~0.11-0.25 at the
  observed scatter (0.45 dex MVT, 0.60 dex lag); 0.96 needs intrinsic scatter <=0.03 dex;
- the "two stapled clumps" criticism FAILS: clump-stapling CAPS Spearman at ~0.75 at any
  separation (Pearson-on-logs could reach 0.96, but they report Kendall too).
**Do not put either in a draft.** The surviving, stronger criticism is the **CCF pulse-width
artifact** (the only mechanism that can give rho~0.96 WITH slope 1) - see
SinglePulse_Temporal/notes/FEASIBILITY_GATE.md. The band/k-correction/single-pulse criticisms stand.

## Two design-critical corollaries
- **Fixed REST-FRAME bandpass, not just a (1+z) division.** Golkhou+2015 §3.6 is the template
  (they use rest-frame 89–299 keV). This is exactly what Göktaş omitted on the MTS axis.
- **⚠ Swift/BAT MVTs run 2–3× LONGER than Fermi hard-channel MVTs for the SAME bursts**
  (Golkhou+2015). Merging our 13 GBM with Zhang's Swift bursts without correcting injects a
  factor-of-a-few systematic **directly onto the slope**. Our **9 GBM∩BAT overlap bursts are the
  calibration set** — this is now a required step, not a nicety.

## Einstein Probe gates (item 8) → WAIT
1. **Timing: fails in practice.** WXT 50 ms resolution, FXT 44 μs (`2025RAA....25a5002Z`); public
   archive exists (first batch 2025-12-11, **FXT-only**; WXT status unconfirmed). **WXT's 2–3 cm²
   effective area forces ~seconds-scale binning ⇒ sub-second MVT not extractable.**
2. **Redshifts: healthy.** 26 secure spec-z of ~113 EP transients (~23%), +70–80/yr (`2025ApJ...993L..37O`).
3. **Bands: formally yes, physically weak** (WXT 0.5–4 keV; FXT 0.3–10 keV).
→ Blocker is timing/photon-statistics. **FXT is the workaround to watch.**

## Follow-up checks (`w83xb2n74`) — ALL RESOLVED, full texts read
- **Li et al. 2026 `2026ApJS..283...47L`** (arXiv:2601.21693) — **PARTIAL-OVERLAP, gap survives.**
  Measures MVT (Haar, 1 ms) AND lag (CCF 25–50 vs 15–25 keV) on pulse-resolved episodes of 22
  z-known Swift/BAT bursts, but **never correlates them** (Fig 4 = T90-vs-MVT; Fig 5 = separate
  CDFs; only rank stat is MVT-vs-peak-flux). Lags observer-frame, no k-correction; sample is
  **precursor+main two-episode**, not single-pulse. ⚠ "Paper I" of a series — **watch it.**
- **Della Casa et al. 2026 `2026arXiv260531566D`** — rest-frame Haar-MVT survey of GBM (MVT vs z,
  E_iso, E_p,z, Reichart V). **No spectral lag, no single-pulse cut** → not prior art for us;
  useful as a rest-frame-MVT methods reference. ⚠ arXiv-only, NOT refereed.
- **MacLachlan MTS band ✅ RECOVERED:** GBM **NaI only, brightest ~3, FULL 8 keV–1 MeV incl. >1 MeV
  overflow, 200 μs bins, NO background subtraction** — stated only in `2013MNRAS.432..857M`
  (arXiv:**1201.4431**). ⇒ **Sonbas's MVT axis is band-heterogeneous too** (prompt 8 keV–1 MeV GBM
  vs XRF 0.3–10 keV XRT): BOTH axes of her Fig 3 mix bands, so §2.3 is worse than stated.

## 🔴 THE PHYSICS CHANGED — the curvature null is challenged
**Uhm & Zhang 2016, ApJ 825, 97** (`2016ApJ...825...97U`), *"Toward an Understanding of GRB Prompt
Emission Mechanism. I. The Origin of Spectral Lags"* — §2.2 is literally titled **"Curvature effect
cannot interpret the observed spectral lags."** For any realistically CURVED (Band-like) co-moving
spectrum, high-latitude curvature yields **ZERO lag**. Their alternative: the spectral peak sweeps
down through the bands via B ∝ r^−b (b≥1) + bulk acceleration Γ ∝ r^s (s≈0.35).

**The three-way tension IS the paper:**
| source | claim |
|---|---|
| Göktaş+2025 | source-frame lag vs MTS **slope 1.01±0.04** → "curvature" |
| Uhm & Zhang 2016 | **curvature gives ZERO lag** |
| Li+2026 §IV.2 | lag traces **radiative** evolution; MVT traces **geometric** scale |

Three ways out, and our design separates them: (a) Göktaş's slope-1 is an artifact of (1+z)
co-scaling + range inflation + observer-band MTS; (b) U&Z's zero-lag doesn't apply in this regime;
(c) **both axes track Γ and R → correlation without causation**, which the Γ partial-correlation
control was built to catch. ⇒ Recast the outcome map as a test between **named models**
(Kocevski/Zhang06 curvature vs Uhm&Zhang16 sweeping-peak); the Γ-control becomes a HEADLINE, not a guard.

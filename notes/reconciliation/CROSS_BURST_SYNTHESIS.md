# Cross-burst reconciliation — walkthrough bursts #3, #4, #5, #6 + 110721A demo

Scope: five bursts reconciled against retrieved, snippet-backed literature. Four records are VERIFIED; the 110721A demo record is **PARTIAL** (Yu+2016's often-quoted Ep = 7409 ± 597 keV could not be retrieved from source and is excluded as UNVERIFIED). No source outside the reconciliation records is used below.

---

## Per-burst verdicts

**GRB 081224 (bn081224887) — AGREE.** Our "no block requires extra spectral structure" (0 decisive, 0 strong; max ΔAIC_simp = 3.6) is independently corroborated by Yu, Dereli-Begue & Ryde 2019, who ran essentially our analysis (same detectors n6n7n9b1, 3ML Bayesian blocks, CPL vs Band by information criterion) and found CPL preferred in all 8 non-pathological bins; by Bissaldi+2011 (time-integrated best model = Comp); and by Meng+2019 via Yu+2016 ("best-fit models before 13.975 s are all the COMP model"). Ep and α track Yu 2019 to ≤0.15 in α across eight blocks, and our blocks reproduce Li & Zhang 2021's block count (9) and edges (1.896, 5.424, 12.502 s) to three decimals. The apparent counter-claim — Burgess+2014/Iyyani+2016 "significant and strong blackbody" — is a **FRAME-difference**: their ΔC-stat > 10 is measured against a *synchrotron-only* continuum, and Burgess states verbatim that Band "has more freedom in the shape below Ep." It hardens into **THEY-wrong** only in the propagation: Li 2019 Table 1 lists "Best Model = Band+BB" citing Iyyani 2016, which never fitted Band+BB for this burst. Two of *our* products fail here (T90 window-truncated at 20.05 s; internal lag sign conflict).

**GRB 120624B (bn120624933) — AGREE, with the LAT axis INCOMPARABLE.** Our thermal null (LRT < 4 in all 10 blocks) is confirmed frame-matched by Chang+2026, who ran the identical thermal menu on the same instrument over 0–20 s and got unconstrained posteriors for both CPL+BB and Band+BB, selecting pure Band (σ > 14.38, kT_max = 30.10 keV — above every kT we fitted). Our no-extra-high-energy-component result matches de Ugarte Postigo+2013's joint GBM+LLE statement verbatim and Sharma+2021. The 10σ LAT headline is **not a tension**: Ajello+2019 give T_LAT,0 = 73.7 s, 47 s after our window closes, and the ≥100 MeV signal is a 1030-s extended component peaking at 380 ± 20 s. Our α = −1.01 lands on Konus/Suzaku/dUP to <0.05, and our blk1 Ep = 960 keV matches the Konus peak-rate spectrum (1000 −450/+620 keV) to <0.1σ once Konus's T0 offset (GBM T0 − 228.02 s) is applied. Our T90 = 23.58 s vs 271.36 s is a window definition, not an error — GBM triggered on episode 3 of 3.

**GRB 130310A (bn130310840) — AGREE on measurement, TENSION on interpretation.** Blind, we recover Qin+2021's 5–7 keV sub-dominant blackbody (our kT = 5.5, 5.6 vs their 6.0 ± 0.8, 5.0 ± 1.0) at matching significance (LRT 31.8/13.5 vs their ΔAIC 24.9/12.5), their slice-b kT (3.4 vs 3.2), their slice-d non-detection, their ~50 keV slice-c pseudo-BB *together with their verdict that it is unnecessary*, and their 7–12 MeV Band Ep (blk3 7411.4 vs 7403.0 keV, 0.1%). The tension is interpretive: their menu was {Band, Band+BB, BB} only, so "large improvement → photosphere" is a forced choice. Our 24-model menu makes blk2's winner a purely non-thermal SBPL+PL with CPL+BB only ΔAIC₂ = 0.8 behind. Extra structure is decisive (ΔAIC_simp = 29.7); its thermal identity is not (~1.5:1). Qin's own text concedes the 8–11 MeV Ep is "difficult" for photosphere + internal shock.

**GRB 130518A (bn130518580) — AGREE on the resolved thermal component, INCOMPARABLE on two-break, one WE-wrong.** We independently reproduce Siddique+2022's central result: kT ≈ 43.6 → 34.8 keV across blocks 6–16 vs their 40.01 ± 2.51 → 32.55 ± 1.94, same cooling amplitude, confined to 23.5–33.9 s inside their 19.4–35.5 s. Our integrated DSBPL win (ΔAIC = 82.0 over Band, 29.1 over the best simple model) is **new, not contested** — no published analysis of this burst ever fitted a two-break function (Siddique's menu is verbatim {PL, CPL, Band, SBPL} × {+PL, +BB}; ADS full-text "double smoothly broken" on their bibcode → 0 hits). But our T_INT shows no thermal only because the BB **railed at the kT = 1.0 keV bound** and was gated out (VALID=False) — a fit failure contradicted by our own resolved blocks. Note the literature is itself unsettled: Siddique+2022 (SBPL+BB) and Dirirsa+2019 (plain Band, BB in menu, not required) disagree on nearly the same window.

**GRB 110721A (bn110721200) — AGREE (best verification point in the campaign), record PARTIAL.** blk3 reproduces four published parameters simultaneously (Ep 269.0 vs 269 +19/−22; α −0.70 vs −0.68; β −2.38 vs −2.37; kT 29.3 vs 30 ± 1.9, Axelsson+2012 Table 1). Our blk2 kT = 40.9 keV with LRT = 84.8 matches Axelsson's kT = 39 ± 4 with ΣΔC = 76 over the same span, and our thermal shutoff at ~6.25 s matches their "significantly detected up to ~6 s." Our blk0 Ep = 19.1 MeV matches Zhang, Bing+2012's independent Band-only 19.56 ± 4.22 MeV to 0.1σ. **THEY-wrong:** β = −1.77 in both GCN 12187 and GCN 12191 — false corroboration, two instruments sharing the *primitive* (one time-integrated Band across a 19 MeV → 0.3 MeV sweep); GCN 12188 contradicts both at −2.9 ± 0.4. **WE-wrong (3):** blk9 collapse to α = +0.82 (an L9 bound-widening regression), blk1 nested LRT = −0.0 (mathematically impossible), and unmasked kT quoted at LRT ≤ 2. Three of four papers named in the original brief are analyses of *other* bursts.

---

## Patterns across bursts

### (1) Is Ep hard-to-soft universal? **No.**

| Burst | Ep behaviour | Source |
|---|---|---|
| 081224 | Monotonic HTS, 2141 → 133 keV | ours + Yu 2019, Shao 2017, Lu 2012/2018 (class H) |
| 110721A | HTS, 19 MeV → 270 keV, index −1.30 (ours) / −1.89 ± 0.10 (Axelsson, 13-bin Band+BB) — but Ep *rises* again blk4→blk6 (258 → 421 → 468 keV) | ours + Axelsson 2012 |
| 130310A | Hard-to-soft overall, but **rises first**: 8.3 → 12.4 → 7.4 MeV (Qin: 9.3 → 11.1 → 7.4) | ours + Qin 2021 |
| 130518A | **Not monotonic** — Siddique's own five intervals give 274 → 771 → 483 → 329 → 235 keV, i.e. intensity-tracking | Siddique 2022 Table 1 |
| 120624B | Not testable — our window is episode 3 of 3 | INCOMPARABLE |

Two of the four testable bursts break monotonicity, and one of those (130518A) breaks it in the *published* fits, not just ours. "Hard-to-soft" survives as a coarse label for the bright decay phase; it is not a per-block law. Both non-monotonic bursts have a rise-then-fall Ep — 120624B is independently rise-dominated in the temporal domain (Tak+2023 t_rise/t_decay = 1.371 vs our φ = 1.415; the φ-convention match is UNVERIFIED pending confirmation of our definition).

### (2) Does α cross the −2/3 death line *inside* bursts? **Only in one, and it is the decisive one.**

- **081224: YES, unambiguously.** Our α track runs −0.12, −0.21, −0.42, −0.62 (all **harder** than −2/3) → −0.65, −0.77, −0.96, −1.10. Yu 2019's independent track does the same (−0.12 → −1.12). Basak & Rao 2014 state it directly: α crosses −2/3 in **11/15 bins**, mean −0.43 ± 0.04.
- **110721A: grazes it.** α reaches −0.70 (ours) / −0.68 +0.06/−0.05 (Axelsson) at blk3 — consistent with −2/3 within errors — then softens. Axelsson and Iyyani use exactly this (α ≈ −0.81 ≫ −1.5) as the constraint against fast-cooling synchrotron.
- **130310A: no.** Every published α (−1.24 to −0.73) is softer than −2/3 throughout.
- **130518A: no.** Siddique's −0.93, −0.92, −1.17, −1.23, −1.46 and Dirirsa's −0.89 are all softer.
- **120624B:** no resolved α track available. INCOMPARABLE.

**The pattern that matters:** the one burst that crosses the line is the one whose published blackbody claim is *caused* by the crossing. Burgess+2014, verbatim: "When Band α was much harder than zero, the synchrotron fit was poor and typically required adding blackbody to fit the data." 081224 has α harder than −2/3 in 11/15 bins, a synchrotron continuum cannot reach that hardness, and the BB does the repair — which is why the thermal component evaporates the moment the continuum is empirical (Li 2019's own CPL+BB thermal ratios: 0.09, 0.05, 0.01, 0.01, 0.01, every lower error reaching zero). Conversely 130518A never crosses the line and still carries a robust, independently reproduced kT ≈ 34 keV. **Crossing −2/3 is neither necessary nor sufficient for a real thermal component — but it is an excellent predictor of a spurious one.**

### (3) Extra structure required vs not — what distinguishes them?

**Required:** 130310A (ΔAIC_simp = 29.7), 130518A (ΔAIC = 82.0 at T_INT; block LRT up to 34.7), 110721A (ΔAIC_simp = 81.2, LRT = 84.8).
**Not required:** 081224 (max ΔAIC_simp = 3.6), 120624B (ΔAIC_simp = 0.0 in 8/10 blocks, LRT < 4 everywhere).

The split is exact along one axis in the fitted data:

| Burst | LLE in our plugin set | Extra structure |
|---|---|---|
| 130310A | yes (n9,na,nb,b1,**lle**) | required |
| 130518A | yes (n3,n4,n6,n7,b0,b1,**lle**) | required |
| 110721A | yes (n6,n7,n9,nb,b1,**lle**) | required |
| 081224 | no — LAT detection *retracted* (GCN 8726), excluded by Ackermann 2013, blank in Maraventano 2025 | not required |
| 120624B | no — GBM-only run; T_LAT,0 = 73.7 s > our window | not required |

Two secondary correlates point the same way: the three "required" bursts all have a continuum peak far from mid-GBM band (Ep = 7–12 MeV for 130310A, 19 MeV for 110721A, plus a ~2.9 MeV upper break for 130518A), and all three are LAT/LLE-detected, i.e. hard and bright. A third mechanism is visible in 130518A: the required structure is a *time-varying* component (kT cooling 50 → 33 keV), which the resolved blocks see and one static integrated component cannot track.

**Caveat, explicit:** with n = 5 the LLE axis is confounded with brightness, hardness, and Ep position, and 120624B's "not required" is partly a window artifact (episode 3 only). Treat "wide-band lever arm predicts required structure" as an **UNVERIFIED hypothesis to be tested on the full sample**, not a result. It is, however, a cheap and falsifiable one: our own next action for 120624B is to re-fit blocks 1–2 with LLE included (Ajello puts 90% of the LLE fluence in 5.76–9.12 s, straddling exactly those blocks), and dUP+2013 already did the equivalent joint fit and found nothing — a prediction we expect to confirm.

### (4) The 2SBPL ↔ (*+BB) alternation within a few AIC — what does the literature say?

**Measured degeneracy, all three "required" bursts:**

- **110721A:** ΔAIC₂ between SBPL+BB and DSBPL is 0.4 (blk2), 8.6 (blk3, DSBPL), 6.8 (blk4, DSBPL), 0.8 (blk5), 1.8 (blk6). Only blk3/blk4 clear our STRONG cut, and they select the *opposite* physics from blk2 — while α, β, Ep and kT all evolve smoothly and reproduce Axelsson's published values. No emission mechanism switches on 0.7 s timescales; this is a model degeneracy.
- **130310A blk2:** winner SBPL+PL (non-thermal), CPL+BB at ΔAIC₂ = 0.8 (~1.5:1).
- **130518A:** the cleanest quantification — the DSBPL low break xb tracks the blackbody νFν peak 3.92·kT block-by-block with Pearson r = 0.87 (N = 11, median ratio 1.13), and at T_INT xb = 167.4 +9.2/−14.0 keV against 3.92 × 34.25 = 134 ± 6 keV. **The second break and the blackbody are the same spectral feature.**

The physical basis is elementary: a blackbody at kT = 20–40 keV peaks at 80–160 keV in νFν, which is within a decade of a low-energy spectral break. At GBM resolution they are not separable.

**Has anyone else reported it? No — and the reason is structural: no published analysis of any of these bursts ever placed a two-break function and a thermal model in the same menu.**

| Burst | Published menus | Two-break function? |
|---|---|---|
| 130518A | Siddique 2022: {PL, CPL, Band, SBPL} × {+PL, +BB}; Dirirsa 2019: Band/SBPL/CPL/PL/BB | none (full-text "double smoothly broken" → 0 hits) |
| 130310A | Qin 2021: {Band, Band+BB, BB} | none |
| 110721A | Axelsson 2012: {Band, Band+BB, Band+mBB}; Zhang 2012: Band; Iyyani 2013: BB+Band | none |

The literature is **silent, not contradicting**. Three near-misses are worth citing, and they are the closest anyone has come:

1. **Burgess+2014 states the same degeneracy one rung down**, verbatim: "There is sometimes a much larger change in C-stat between fits with synchrotron and synchrotron+blackbody than those of Band and Band+blackbody owing to the fact that the Band function has more freedom in the shape below Ep." That is continuum-freedom-vs-blackbody — our result is the 2SBPL generalization.
2. **Burgess+2020** fit GRB 130518580 (their Figure 2 showcase burst) with an idealized synchrotron model carrying **two characteristic frequencies (ν_cool, ν_inj) plus a cutoff** — a two-break shape — and **no thermal component** (Extended Data Fig. 5 explicitly assumes "absence/subdominance of a photospheric component"). That is the alternative branch of our degeneracy, taken in print, on exactly the burst where we measure xb ≈ 3.92·kT.
3. **081224 slice c** is the control: we get kT = 52.0 keV, Qin-independent Li 2019 / Basak & Rao analogues aside, Qin's own slice c gives kT = 54.6 ± 14.7 — 5% agreement — and *both* analyses find it statistically unnecessary. Agreement on a non-detection's fitted value corroborates a shared fitting artifact, not a blackbody.

**Claim status:** "the (2SBPL ↔ *+BB) pair is an unreported, systematic degeneracy class" is supported by the menus quoted above and by the r = 0.87 correlation in 130518A. A broader targeted literature search for the degeneracy itself has **not** been run — mark UNVERIFIED beyond these five bursts.

---

## What the literature gets that we do not, and vice versa

**They have, we do not:**
- **Rest-frame physics.** Redshifts and Eiso/Ep,i (dUP 2013: Eiso = 3.0e54 for 120624B; Dirirsa 2019: Ep,i = 1601 keV for 130518A), and the photosphere **death-line test** in the rest-frame Ep–L plane (Zhang 2012 for 110721A). We cannot re-derive that test at all — and for 110721A the redshift is ambiguous by a factor 3.3 in (1+z) (z = 0.382 *or* 3.512, GCN 12193, no confirming lines).
- **Physical models.** Synchrotron (Burgess 2014, 2020), subphotospheric dissipation (Ahlgren 2019 DREAM1.2), photospheric jet inference (Iyyani 2013: Γ 1000 → 150, r_ph ~1e12 cm). Our menu is empirical by design.
- **Coverage we structurally lack.** 120624B episodes 1–2 (~250 s pre-trigger) and the 1030-s LAT extended component; 130310A's precursor (pure-BB kT = 45.4 ± 7.0 keV); ≥100 MeV LAT throughout.
- **Calibrated significance.** Axelsson's Monte-Carlo mapping ΔC = 30 (2 dof) → p = 1e−7. We quote ΔAIC without a burst-specific calibration.
- **Cross-instrument peak-interval spectra.** Konus always publishes a maximum-count-rate spectrum alongside the integrated one — the single most useful frame-matched anchor we found (110721A, 120624B, 130310A).
- **Derived temporal diagnostics** we do not produce: HLE/decay indices (Li & Zhang 2021 α_PL = 1.81, 2.25; Tak 2023), per-band T90 (Qin 2013).

**We have, they do not:**
- **The two-break test.** First ever for 130518A, 130310A and 110721A — an entire model family absent from every published menu for these bursts.
- **Adequacy separated from identification.** ΔAIC_simp ("is a simple model enough") vs ΔAIC₂ ("which extra component"). 130310A blk2 is the demonstration: extra structure at ~3e6:1, thermal-vs-non-thermal at ~1.5:1. Qin's two-model menu cannot express that distinction, and the published photospheric identification is its artifact.
- **Finer, uniform segmentation.** 19–20 Bayesian blocks vs Siddique's 5 intervals; our BB confinement (23.5–33.9 s) is *sharper* than the published one (19.4–35.5 s) and nested inside it.
- **Unpublished window extensions.** 130310A blocks 8–9 (4.93–6.23 s, Ep ≈ 37–39 keV) extend the hard-to-soft track two decades below Qin's floor.
- **Free parameters where they rail or freeze.** All our 081224 βs were free; Lu 2012 rails at −4.57 in 2/12 bins, Lu 2018 freezes β = −2.56 in one.
- **Corrections to the record.** Our β = −2.26 for 110721A replaces the −1.77 in two circulars (backed by GCN 12188 and all eight of Axelsson's resolved bins); we caught Li 2019's mis-citation of Iyyani 2016, Basak & Rao's LAT detection contradicted by Ackermann 2013, and the missing ×10⁻⁵ exponent in GCN 8739.
- **Blind reproduction as a method.** The 110721A blk3 four-parameter simultaneous match exercises binning, background, response and optimizer at once.

---

## Open items / what to verify next

**Blocking defects in our own products (fix before any number is published):**

1. **110721A blk9 regression** — α = +0.82, Ep = 42.3 keV vs α ∈ [−1.26, −0.93], Ep ∈ [373, 414] keV in all 12 archival runs. Caused by the L9 Ep-cap widening removing the bound that was incidentally anchoring faint late blocks. **Rule:** every bound change requires a before/after diff over *all* blocks, with a hard alarm on any α crossing −2/3, any Ep moving >3σ, or any winner changing family.
2. **110721A blk1 nested LRT = −0.0** — mathematically impossible; the winning model in the same block is SBPL+BB with kT = 23.3. Make a non-positive nested LRT a hard error, never a reported non-detection.
3. **130518A T_INT BB railed at kT = 1.000003** with VALID=False, despite kT = 30/80 keV multistart seeds and valid resolved kT = 30.7–50.3 keV in the same burst. Seed T_INT from the flux-weighted resolved kT and emit `INTEGRATED_BB_RAILED`.
4. **DSBPL reporting bug (130518A L11)** — astromodels' DoubleSmoothlyBrokenPowerlaw is symmetric under α1↔α2, and XP is *not* the νFν peak (T_INT columns read −2.09, −0.86, XP = 2881 keV; the curve has low-energy index −0.86 and peaks at 431 keV). **Every DSBPL number in any table or figure must be regenerated by evaluating the fitted function.** AIC, winners and margins are unaffected.
5. **Temporal catalog has now failed on 2 of 5 bursts** — 130310A row T90 = 17.910 ± 68.242 s vs blind 2.09 s and published ~2.4 s; 081224 LAG_S = −0.6162 in `results/temporal_catalog_human.ecsv` vs +0.816 blind, with three independent papers giving positive. **Audit the whole catalog** and add gates: reject T90 with fractional error > 1, or T90_STOP outside the approved SRC window; fix the lag sign convention in one place with 081224 as a regression anchor.
6. **T90 window truncation** — 081224 (20.05 s, stop at window edge 20.165 s, on-disk error 47.0 s) and 110721A (15.17 s from an 18.98 s window vs 24.45 s published). Emit `T90_WINDOW_LIMITED`; measure T90 on a window ≥2× expected duration.

**Physics/analysis items:**

7. **130310A: widen the β bound to ≥ −10 and re-fit blk1/blk2** before quoting Ep = 12.4 MeV or ΔAIC_simp = 29.7 — part of that margin measures "the simple family railed," not structure. (Qin used −8 and railed too.)
8. **110721A: extract the evaluated DSBPL low-energy index pair for blk3/blk4** and test against the synchrotron values (−2/3 above the cooling break, −3/2 below) with a physical break ratio. This is the only non-circular discriminator available and a genuine contribution — but it must wait on items 1, 2 and 4, which live in the same composite-fit machinery.
9. **120624B: re-fit blocks 1–2 with LLE** (Ajello: 90% of LLE fluence in 5.76–9.12 s). Also sensitivity-check the post-burst background opening at 35.0 s while Tak+2023 still fit source counts to 37.75 s — the one plausible contributor to our Ep sitting ~200 keV above Chang's frame-matched 558.8 keV.
10. **130518A: report the xb ≈ 3.92·kT degeneracy explicitly** rather than claiming either description, and flag in the paper that Siddique+2022 and Dirirsa+2019 disagree on the integrated BB.
11. **Test the LLE ↔ extra-structure correlation on the full sample.** UNVERIFIED at n = 5 and confounded with brightness/hardness.
12. **Exclude 110721A from all rest-frame correlations** (Amati, Yonetoku, Ep–kT–L) — z is 0.382 *or* 3.512; Iyyani adopted z = 2 as a placeholder.

**Protocol gates to add to `SpectralFitting.md`:**

13. **Ep-vs-Ec frame gate** — Li 2019 and Yu 2019 tabulate the CPL *e-folding* energy, not Epeak (Ep = (2+α)·Ec, verified on Yu Table 6). Naively diffing would have manufactured a factor-1.9 tension.
14. **Attribute extra-component claims to the continuum, not the burst** — extract (base continuum, statistic, threshold) before recording a diff.
15. **Bound detection on both sides** — a literature parameter railed at *their* bound (Lu 2012 β = −4.57; Qin β = −8.00/−5.00; Konus β < −1.8 upper limit only) is INCOMPARABLE, not a diff. A β = −5.00 rail on our side is likewise not automatically our bug.
16. **DIC pathology check** — discard any bin with pDIC < 0 (Yu 2019 in print: |ΔDIC| reaching "hundreds of thousand", "very dangerous to blindly believe such a number"; Li 2019's ΔDIC = −378.3 accompanies a thermal ratio of 0.05 +0.15/−0.06).
17. **Citation-chain and object-identity audit as step zero** — open the *cited* paper, and probe both the GRB name and the bn/trigger name (Burgess+2020 indexes 130518A as "130518580"; an ADS full-text miss on "130518A" returned a false negative). Three of four papers named in the 110721A brief analyse other bursts entirely.
18. **Convert every instrument's T0 to the GBM frame before diffing** (Konus offsets: +3.137 s for 110721A, −228.02 s for 120624B, +7.397 s for 130310A, +19.97 s for 130518A; Suzaku: −0.196 s for 081224, +3.5 s for 130310A, +13.11 s for 130518A). The 110721A Konus mapping remains **unresolved/UNVERIFIED**.
19. **Free binning validation** — Li & Zhang 2021, Yu 2019 and Shao 2017 publish block counts and edges; one grep turns our binning from an assumption into a verified input (it worked exactly for 081224 and 130518A/Ahlgren blk10 to 40 ms).
20. **Distinguish corroboration from silence, and mask non-detections** — dUP+2013 and Tak+2023 never fitted a thermal model, so they are INCOMPARABLE on 120624B's thermal null, not supporting evidence. Symmetrically, mask kT wherever LRT ≤ 2 (110721A blk8 kT = 33.1 at LRT = 0.6 would fake a late thermal rebrightening) and add a "co-located sub-threshold" column so 081224 blk3 (kT = 44.8, ΔAIC_simp = 3.6, landing exactly where Li 2019 and Burgess 2014 put the photosphere) reads as "sub-threshold, where the literature puts it" rather than "nothing."

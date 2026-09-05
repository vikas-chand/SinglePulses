
## 2026-08-17 — campaign paper round (GRB 090719, burst #6)

**Producer:** Claude. Paper: paper/GRB090719/ (17 pp).

**COMBINED VERIFIER (fresh context): FAIL → ALL FIXED:**
(1) "nine of eleven" dAIC<2 → ALL eleven (max margin 1.998); (2) Ep
"monotonic" → near-monotonic with block-3 excursion, in abstract+summary
too; (3) 30-keV endpoint disclosed as the engine's Ep floor (bound-railed
invalid fit) → "≤30 keV, factor ≥21"; (4) "no EAC rails" descoped: TRUE
only for the integrated winner — block winners rail b1 in 6/10 blocks
(1.2 ×4, 0.8 ×2), all statements corrected; (5) HARD FAIL: promised
refusal cells missing in montage_bin4/bin9 — ROOT CAUSE was in 41e itself:
its model loop iterated only finite-AIC models, so engine-FAIL cells
(NaN AIC) were STRUCTURALLY invisible (a latent NO-MODEL-DROPPED violation
present since the tool was written; never triggered before because bursts
1–2 had no engine FAILs). 41e patched: NaN-AIC models render as labeled
"ENGINE FAIL" refusal cells at the end of the AIC order; sidecar daic
None-safe. bin4+bin9 rebuilt. (6) canonical-MVT z=2.78<3σ disclosed in
abstract, §3.3, summary (the 2026-08-15 Bala-figure lesson applied);
(7) α sequence start corrected (−0.14 through +0.08 max); (8) "smallest
detector set" → joint-smallest with #1; (9) paramevo caption fixed;
(10) step9 LRT-set {0,2,4} vs AIC-set {0,4,6} metric-dependence sentence
added. Figure sweep otherwise: step9 PASS vs canonical (stale-class
checked); SEDs PASS; temporal PASS.

**Science row:** fastest canonical MVT (8.9 ms, z=2.8 caveat); CWT on NEW
rung 256 ms (ladder mapped: 215/256 neighbors); 2nd consecutive mixed
pulse (phi=0.408); 93σ lag (campaign max); cleanest hard-to-soft track
(Ep 624→≤30); first off-rail integrated fit. Burst #6 CLOSED pending PI
and montage re-gate.

**MONTAGE RE-GATE (fresh context): 4/4 PASS** — bin4/bin9 (this burst) and
b5's TINT/bin1: 24 cells, "ENGINE FAIL [INVALID]" refusal cells present and
labeled, exactly one winner each, staged copies byte-identical to grid
copies, sidecars consistent. Known cosmetic (forward-fixed in 41e, these
four left as gated): corner stamp's "refused cells" counter did not count
engine-fail cells; stamp now reports them separately for future bursts.

# Audit-decision memo — clean-consensus re-fit (2026-07-13)

Two independent audits of the 106-burst clean-consensus catalog
(`results/clean_sample_all_models_consensus.ecsv`, 974 blocks): Claude (main) +
Codex (gpt-5.6-sol, `results/codex_results_audit.md`). They AGREE on the two
headline caveats and Codex added four correctness items. Nothing changed yet —
this memo is for your decisions. Each decision: **issue → evidence → options →
my recommendation → impact**.

---

## D1. Ep–kT estimand (headline correlation)
- **Issue.** The reported ρ=0.81 pairs the *standalone Band* Ep with a kT drawn
  from *either* Band+BB or CPL+BB, selected by LRT≥14. That mixes parameters from
  different fits (the June-9 audit's H5) and pools two BB flavors.
- **Evidence.** All valid Band+BB same-fit pairs: ρ=0.29 (n=666). Impose Band+BB
  LRT≥14 (BB significant): ρ=0.746 (n=115); composite Ep, excl. anchor: 0.70.
  Current mixed/selected estimand: ρ=0.81 (n=217), 0.79 without the anchor — so
  it is **selection-driven, NOT anchor-driven**.
- **Options.** (a) One documented **same-fit** estimand: Band+BB Ep & kT, LRT≥14
  → **ρ≈0.75**. (b) Keep 0.81 but relabel it a mixed, significance-conditioned
  statistic.
- **Recommend (a).** Physically consistent (same fit), still strong, robust to
  the anchor.
- **Impact.** Headline Ep–kT 0.81 → ~0.75; per-burst Burgess story unchanged
  (130427A ρ=0.91).

## D2. Two-break fraction framing
- **Issue.** 33% (35/106 curv-required, dAIC>10) is exact but burst-clustered.
- **Evidence.** 2 bursts supply 63% of the numerator (130427A 15, 160625945 7).
  Drop anchor → 26%; drop both → 20%. Only 10 of 31 denominator bursts contribute
  any genuine two-break block; **burst-level median = 0**; trigger-resampled 95%
  interval ≈ **14–44%**.
- **Options.** (a) Quote 33% as a **block-weighted** descriptive fraction WITH the
  burst-level sensitivity band. (b) Lead with a burst-level statement ("genuine
  two-break curvature appears in ~10/106 bursts, concentrated in the brightest").
- **Recommend (a)+(b) together** — the honest, defensible framing.
- **Impact.** Framing only; the number stays but gains a sensitivity band.

## D3. INCONCLUSIVE bug (clear correctness)
- **Issue.** 23 blocks (15 bursts) have NO valid model, yet get an invalid
  fallback winner instead of `INCONCLUSIVE`.
- **Evidence.** Literal `BEST_AIC_MODEL` census 213 CPL… vs valid-gated 202; the
  23-row gap is exactly these invalid fallbacks.
- **Recommend.** Label them `INCONCLUSIVE`. Low risk; already excluded from the
  gated stats, but the per-block label is wrong.
- **Impact.** Cleaner census + per-block table; no correlation changes.

## D4. Nested-LRT valid-parent (touches locked §2.6 doctrine)
- **Issue.** A +BB or DSBPL child can "win" even when its parent (Band/SBPL) fit
  is invalid, so the nested LRT is meaningless there.
- **Evidence.** 11/42 Band+BB winners (dAIC>10) have invalid Band parents; 2/36
  DSBPL winners have invalid SBPL parents — one (130427A blk59) is in the 35
  genuine two-break blocks (→ 34 under the fix). Separately, 135 blocks have a
  negative nested LRT (optimizer pathology) but **none is a curvature winner**, so
  they do NOT inflate two-break.
- **Options.** (a) Require valid parent AND child for any nested-LRT claim
  (+refit/invalidate negative-LRT blocks). (b) Keep as-is, disclose.
- **Recommend (a)** — but this modifies the locked framework, so your call.
- **Impact.** Two-break 35 → 34; small +BB-significance trims.

## D5. Uncertainty-quality flag
- **Issue.** M_VALID gates shape/bounds but NOT error quality.
- **Evidence.** 77 blocks with a zero error; 154 valid *winners* with MINOS
  failures; 236 blocks with an error ≥ its estimate; 16 sign-inverted MINOS.
- **Recommend.** Add a separate `UNC_OK` flag; use it before parameter-distribution
  / correlation claims (not for model selection).
- **Impact.** Adds a column; may trim some correlation samples modestly.

## D6. ν_m–ν_c decisive subset
- **Issue.** The primary slope 0.528 uses ALL ordered DSBPL breaks (n=455), not
  decisive two-break fits, and includes XB<15 keV pairs (109/460).
- **Evidence.** Slope by subset: primary 0.528 (n=455); errors<1 → 0.671 (n=354);
  XB≥15 keV → 0.601 (n=348); DSBPL LRT≥14 → 0.697 (n=59); genuine dAIC>10 →
  **0.754 (n=35)**.
- **Options.** (a) Headline the **decisive** subset (0.75) + report the sensitivity
  ladder. (b) Keep 0.528 as "all fitted breaks", disclose it isn't decisive.
- **Recommend (a).** The physical claim should rest on decisive fits.
- **Impact.** ν_m–ν_c slope 0.53 → ~0.75 (headline), with a stated ladder.

---

## Net effect if all recommendations adopted
- Ep–kT: 0.81 → ~0.75 (same-fit, anchor-robust).
- Two-break: 33% kept as block-weighted, + "≈10/106 bursts, 14–44% CI, burst
  median 0"; 35 → 34 under valid-parent.
- ν_m–ν_c: headline slope 0.53 → ~0.75 (decisive subset).
- Census fixed (INCONCLUSIVE); uncertainty flag added.
- None of these break the paper's *qualitative* story (positive Ep–kT, genuine but
  rare two-break, ν_m–ν_c positive with scatter); they make each number defensible.

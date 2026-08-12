# Skill: Step 5 — Binning (two-tier Bayesian blocks)

**Purpose.** Turn the approved source interval into the time bins that become spectra:
`scripts/27b_reblock_3ml.py` runs 3ML Bayesian Blocks on the reference NaI, then trims/merges
edges below a significance floor. (`scripts/27c` adds the coarse LLE grid when gated.)
These bins fix *which counts ever become spectral bins* — nothing downstream can recover a
bin that binning never made.

**Status:** created 2026-08-12 (first entry, from the bn200524211 walkthrough). Previously the
ledger listed this step as `✎ to be created`; it and `Temporal.md` were the two least
documented steps.

## Inputs
- `--bkg <catalog>` — the approved windows (per detector `BKG_*`, shared `SRC_START/SRC_STOP`).
- `--burst <trigger>`, `--out <dir>` → `bb_blocks_spectral_<trigger>.ecsv`.
- Reference detector = the sample-catalog brightest **approved** NaI (never `lle`).

## What actually happens (read this before trusting a block grid)
1. background polynomial fit on the approved pre/post windows (order auto via LRT);
2. **the approved source window is TIGHTENED** by `emission_window()` — see L5-1;
3. Bayesian Blocks over the tightened window;
4. edges below `SIGMA_FLOOR` trimmed, interior blocks merged until each clears the floor.

---

## L5-1 — The approved source window is ADVISORY, not binding: `emission_window()` re-tightens it, and it under-extends faint tails
*(bn200524211 / GRB 200524A, 2026-08-12; attribution: **we**-wrong — code behaviour, fixable)*

**Evidence.** Stage-1 approved `src=(-2.21, 25.93)`. A Step-4 review measured (stacked
n0+n1+n3, far-anchored background) genuine emission well past that edge:
26–31 s **8.2σ**, 31–36 s **6.7σ**, 36–41 s 3.3σ, merging into noise only after ~56 s.
The window was widened to `t2 = 36.0` and 27b re-run. 27b reported:

```
bn200524211 [n0]: src=[-1.554, 27.350] (approved+tightened)   BB=13 -> 12
```

i.e. it **discarded the approved 36.0 s and substituted 27.35 s of its own**.

**Mechanism.** `emission_window(tt, lo, hi, brate)` bins the REFERENCE DETECTOR ALONE at
**0.256 s**, smooths with a 3-bin boxcar, finds the peak, then walks outward while
`net > 1.0 * noise`, stopping at the **first** bin that fails. Two consequences:
- it is a **greedy per-bin** test, not an integrated-significance test — a tail that is
  ~4σ per 5 s *stacked over the approved NaI* is only ~1σ per 0.256 s bin in one detector,
  so the walk halts almost immediately;
- it uses **one** detector, discarding the S/N of the other approved NaI.

This is precisely the pitfall `source_selection.md` lists first — *"Clipping the soft tail —
stopping t2 at the visual knee of an FRED instead of where it merges into noise"* — but
implemented in code, where it silently overrides a human decision.

**It is not harmless, but it is also not nothing.** The A/B on the same burst:

| | approved windows (orig) | corrected windows |
|---|---|---|
| tightened src | −1.554 → **25.931** | −1.554 → **27.350** |
| blocks | **11** | **12** |
| last block | 13.98–25.93, 12.0 s wide, σ=13.3 | split: 13.98–20.34 **and** 20.34–27.35 (σ=7.4) |

Widening the approved window *did* let the walk run further (+1.4 s) and resolved the long
12 s tail block into two — but ~4 % of net counts (27–36 s) still never became spectral bins.

**How to apply.**
- **Never assume the block grid spans the approved window** — always read the
  `src=[...] (approved+tightened)` line and record BOTH numbers in the burst record.
- When the tail matters (soft late-time emission, cooling/thermal claims), check what the
  tightening dropped before interpreting the last block.
- **Code fix (proposed, not yet implemented):** make the walk-out use the *stacked* approved
  NaI and an *integrated* criterion (e.g. extend while a trailing 5 s window stays >3σ),
  or add `--no-tighten` to honour a human-approved window verbatim. Until then this is a
  known, quantified systematic that shortens every faint tail in the sample.

## L5-2 — The 5σ floor is a MERGE rule, not a discard rule
*(bn200524211, 2026-08-12)*
`BB=13 -> trim+merge(>= 5 sigma)=12` — the 13th block was not thrown away; sub-floor edge
blocks are trimmed and interior ones merged into neighbours. Report the pair `BB=n -> m`, not
just the final count: a large gap means the burst is faint or the window is too wide.

## QC checklist
- [ ] `src=[...] (approved+tightened)` recorded, and the tightened edge compared to the approved one (L5-1).
- [ ] Background poly order printed and plausible (a high auto-order on a very bright burst is a warning — see the 130427A `FitFailed` flag in `notes/PIPELINE_FLAGS_2026-08.md`).
- [ ] Every block clears the significance floor, or is an intentional merge.
- [ ] Block edges lie inside the approved background gap.
- [ ] No single block spans most of the burst (a sign the window was mostly quiet).

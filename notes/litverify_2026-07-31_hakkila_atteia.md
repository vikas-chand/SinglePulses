# Literature verification — reading handoff (Hakkila 2015 + Atteia 2017)
2026-07-31. Source: verified-search workflow `wf w6wsz2vqm` (8 agents, 0 errors).
Every item carries a real bibcode + verbatim snippet; the BOAT number was
adversarially cross-checked at a DIFFERENT instrument (per the false-corroboration rule).
House rule honored: NO citation enters a project file without a resolved bibcode.

## 1+2. Does GRB 221009A break Atteia's 1–3×10⁵⁴ erg cutoff?  ✅ VERIFIED (+cross-check CONFIRMED)
- E_iso ≈ **1.0–1.5×10⁵⁵ erg** (rest-frame 1 keV–10 MeV, z=0.15095), three INDEPENDENT instruments:
  - Konus-Wind — Frederiks+2023 ApJL 949 L7 (`2023ApJ...949L...7F`): ~1.2×10⁵⁵.
  - Fermi-GBM — Lesage+2023 ApJL 952 L42 (`2023ApJ...952L..42L`): 1.0×10⁵⁵.
  - Insight-HXMT/GECAM-C — An+2023 (`arXiv:2303.01203`): ~1.5×10⁵⁵ [adversarial cross-check primitive].
  - Synthesis + rarity — Burns+2023 ApJL 946 L31 (`2023ApJ...946L..31B`): record holder (prev ~5.8×10⁵⁴); **once-per-~10,000-yr** (7,200–11,200 yr, 80% CI).
- **Exceeds Atteia's max by ~4–15×.** BUT z=0.151 is OUTSIDE Atteia's z=1–5 sample → never a
  candidate member; and it's a rare nearby tail draw, not a demonstrated hard-limit violation.
  Collimation-corrected E_γ plausibly ordinary (LHAASO jet <~1°). "Breaks the cutoff" OVERSTATES it.
- ⚠ Discovery papers quote approximate central values, no formal 1σ; the 1.0–1.5×10⁵⁵ spread IS the uncertainty.

## 3. Did Atteia publish the max-L_iso / max-L_p companion?  ✅ VERIFIED = NO
- No Atteia max-luminosity paper through 2026 (ADS first-author 2017–2026, 36 records, none on max-L).
- **BUT: Atteia 2025, ApJ 980, 241 (`2025ApJ...980..241A`)** — "GRB 221009A and the Apparently Most
  Energetic GRBs" — the source author's OWN follow-up revisiting the **E_iso** cutoff vs the BOAT.
  → This pre-empts #40's top "staleness" task: read it FIRST. (Still E_iso, not luminosity.)

## 4. Recent Einstein Probe energy-from-flux+z paper (faint end)?  ⚠ PARTIAL
- Best match: **O'Connor+2025, ApJL 993, L37 (`2025ApJ...993L..37O`, arXiv:2509.07141)** — places EP
  transients on the Ep–Eiso (Amati) plane from EP fluxes + measured z; finds an **"extension at the
  faint end of the Eiso distribution."** Exactly the faint-end counterpart for #40.
- Also: Guo+2025 (FXT rate + luminosity function, arXiv:2510.13533); Li+2025 (arXiv:2510.10267).

## 5. Was Turpin+2016 (z-selection ≠ energy-distribution bias) ever re-tested?  ⚠ PARTIAL = essentially NO
- Turpin+2016 = **`2016ApJ...831...28T`** (ApJ 831, 28). Only **12 citing papers**; cited & built on
  (chiefly the same Toulouse group → Atteia 2017), but **NOT independently re-tested** on a larger
  joint Fermi–Swift sample 2016–2026. → AstroGraph gap (A) is REAL: inherited claim, never re-checked.

## 6. Is the lag–MVT correlation novel?  ⚠️ NO — READ Sonbas+2013 in full (reframe #37, narrower)
- **Sonbas+2013, ApJ 767, L28 (`2013ApJ...767L..28S`; arXiv:1210.6850; PDF in Skills_training/)** —
  title is "X-Ray Flares" (why a title search misses it), but **Fig 3 IS the lag-vs-MVT plot**:
  Spearman **0.96**, log-log slope **1.44±0.07**, observer frame, AND it already **invokes curvature**
  (Kocevski δR/2cΓ² + Zhang (R/c)(θ²/2)) — calling it "speculative … warrants detailed theoretical
  investigation." So we are NOT first to plot lag-vs-MVT, find the correlation, OR propose curvature.
- The two MacLachlan papers are MVT-vs-**rise-time** (`2012MNRAS.425L..32M`) and MVT-vs-**duration**
  (`2013MNRAS.432..857M`) — **not lag**. MVT estimator: Golkhou&Butler 2014 (`2014ApJ...787...90G`).
- → **#37 survives but narrower:** the parameter-free FIXED-slope test (curvature ⇒ log-log slope 1,
  norm E_h/E_l−1≈0.8; Sonbas's free 1.44≠1 is a *lead*, not a scoop), on **clean single pulses**
  (Sonbas used a mixed prompt+XRF sample over >3 decades), Γ-controlled, rest-frame. Cite Sonbas as
  the originating result; sell the DISCRIMINANT, not the correlation or the curvature idea.

## Bottom line
1. **BOAT:** solid ~1×10⁵⁵ erg, ~4–15× over Atteia — but a rare nearby tail event outside his sample,
   and **Atteia himself (2025) already revisited it** → read `2025ApJ...980..241A` before any re-run.
2. **lag–MVT + curvature are BOTH Sonbas 2013 already** → #37 must sell the parameter-free
   fixed-slope DISCRIMINANT on clean single pulses (Γ-controlled, rest-frame), not the correlation.
3. **Two real AstroGraph gaps stand:** Turpin+2016 never independently re-tested; Atteia's cutoff-origin
   (E_j/η_j/f_b) still needs radio calorimetry of energetic-GRB afterglows.
4. **Hakkila lineage 7/7 bibcodes verified** (see #39); note "Nemiroff 2019" is really **Hakkila &
   Nemiroff 2019** (Hakkila first author).

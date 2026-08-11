# bn130427324 / GRB 130427A — DEFERRED 2026-08-07. Two independent blockers.

## 1. LLE response is INVALID for our window (D1 failure)
We analyse the **SECOND pulse**: stamped source [+119.11, +178.44] s, blocks [+121.47, +173.11] s.
The FSSC shipped a **single-matrix** LLE response `gll_cspec_bn130427324_v02.rsp` built for
**[+5.02, +34.92] s** — the FIRST pulse — at θ = 48.1°, while our window sits at θ = 36.5° → 23.0°.
**Δθ = 19.9°** (Fermi slewed). threeML count-weights multi-matrix `.rsp2` natively
(`weight_by_counts`, time_series_builder.py:242) but there is only ONE matrix here, so nothing can
be weighted — a data-product limitation, not a code bug. Options: FSSC query for a later /
multi-interval LLE product → regenerate via `mkdrm_ez`/gtburst for [+119, +178] s → GBM-only with
the exclusion recorded as a DATA-QUALITY (D1) failure, never a significance one (L17).

## 2. ⚠ NEW — PILE-UP, and it affects GBM, not just LLE
**Ravasio+2019 (`2019A&A...625A..60R`) EXCLUDED this burst**, verbatim:
> *"From our selection we excluded GRB 090902B and GRB 130427A for the following reasons… **GRB
> 130427A, due to its large fluence, suffered from pile-up effects** (Preece et al. 2014) and a
> standard analysis can be performed only on its prec[ursor]…"*
Our catalog fluence for this burst is **2.46e−3 erg/cm²** — the brightest in the sample by far.
Toffano+2021 (`2021A&A...652A.123T`) DID fit it, but GBM-only and *"consider[ing] the brightest
portion of the light curve"*, citing Preece+2014 for the first peak (0–2.5 s). Their 2SBPL:
α₁ = −0.63, α₂ = −1.67, break 224 keV, Ep = 992 keV, β = −3.7.
Ravasio+2024 (the 22-burst GBM+LAT high-energy paper) does **not** contain it at all.

**✅ RESOLVED BY DESIGN (Vikas, 2026-08-07): "We were dealing with the non-piled-up pulse of it."**
The second-pulse selection was made DELIBERATELY to avoid the piled-up episode — it is not an
accident of the Busby cut. So blocker 2 does NOT apply to our window; it applies to the first
pulse, which we do not analyse. Record this in the methods: our 130427A result is the
**non-piled-up second pulse**, which is also why it is not directly comparable to Preece+2014
or Toffano+2021 (both of whom analyse the bright first portion).

**Why pile-up is confined to the first pulse:** pile-up scales with count rate, and the extreme rates are in the
FIRST pulse (0–20 s) — which is what Preece+2014 analysed. Our window is the far fainter SECOND
pulse at 119–178 s, so our selection may sidestep the exact problem that made Ravasio drop the burst.

## Required order when we return
1. **VERIFY pile-up is not an issue in [119, 178] s** — compare peak count rates there vs the first
   pulse against the GBM pile-up regime. If pile-up IS present, the LLE question is moot and the
   burst may not be usable at all.
2. Only then resolve the LLE response (blocker 1).
NB: no published LLE analysis of this burst exists in the Ravasio line; it is also absent from
Duan & Wang's 36-burst LLE sample — possibly for the same reasons.

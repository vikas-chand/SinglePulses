# Where our single-pulse paper sits — verified against ADS 2026-08-17

All bibcodes below were pulled live from the ADS API and their abstracts read.
No citation here is from memory. (Project rule: hallucinated citations have
reached drafts before.)

## The direct ancestor — and the gap it explicitly left

**`2019ApJ...886...20Y` — Yu, Hoi-Fung; Dereli-Bégué, Hüsne; Ryde, Felix,
"Bayesian Time-resolved Spectroscopy of GRB Pulses"**
Abstract (verbatim extract): *"time-resolved spectroscopy on a sample of 38
single pulses from 37 gamma-ray bursts detected by the Fermi/GBM during the
first 9 yr … For the first time a fully Bayesian approach is applied. A total
of 577 spectra are obtained and their properties studied using **two empirical
photon models, namely the cutoff power law (CPL) and Band model**."*

That two-model restriction is the opening. 58 citations as of today; scanning
the citing list (2020–2026) the follow-ups go to physics applications
(photospheres, curvature, polarization) and to ML spectral modelling — **no one
has redone this sample with a broader model menu.**

## Closest current competitors

| bibcode | who | what they own |
|---|---|---|
| `2024ApJ...972...83B` | Busby & Lazzati (2024), *Single-pulse GRBs Have Prevalent Hard-to-soft Spectral Evolution* | the sample DEFINITION (62 bright Fermi bursts, morphology algorithm insensitive to pulse shape + citizen-science cross-check) and the hard-to-soft claim |
| `2025ApJ...991..230G` | Gowri, Pe'er & Ryde (2025), *GRB Pulse Structures and Emission Mechanisms* | pulse-shape quantification (61 pulses / 22 GRBs; the two-sigmoid asymmetry we use) |
| `2019ApJ...886...20Y` | Yu, Dereli-Bégué & Ryde (2019) | Bayesian time-resolved CPL/Band on 38 single pulses |

## What is therefore genuinely ours

**The model competition itself.** 106 single pulses × 24 models per spectrum,
with an explicit validity gate and a stated selection rule — i.e. *what shape
actually wins when everything competes*, which none of the three papers above
attempts. Our accumulating by-products are also unclaimed as far as this search
goes:
- estimator-dependence of the minimum variability timescale (the CWT grid ladder);
- epoch-dependent crossings of the synchrotron line of death (five consecutive
  bursts so far), i.e. violation as a property of the rise, not of the burst;
- AIC vs nested-LRT disagreement on thermal components — a methodological result
  about how thermal claims are made in this field;
- the lag–width plane spanning zero to ~9% of T90 with no monotonic trend.

## The caution that must shape the abstract

**Busby & Lazzati already own "prevalent hard-to-soft evolution" in this exact
population.** Our Ep-decay findings are therefore *confirmation*, not discovery,
and must be written as such. The novelty has to sit in the model census and in
the systematics (validity gates, estimator dependence, metric disagreement) —
not in the spectral evolution.

## Open follow-ups before writing

1. Read the Yu+2019 paper properly (not just the abstract) and check whether
   their "future work" promise names specific models — if so, quote it.
2. Check whether Yu/Dereli-Bégué/Ryde have a follow-up in preparation (arXiv
   listings, conference abstracts) before we assume the niche is free.
3. Confirm sample overlap with Busby & Lazzati's 62 — how many of our 106 are
   theirs? That number belongs in our sample section.

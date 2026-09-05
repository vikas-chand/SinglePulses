# Testing the Rahaman–Granot–Beniamini internal-shock predictions with our census

Verified via ADS 2026-08-17 (abstracts read; nothing here from memory).
Note the spelling: **Rahaman**, not Rahman.

| bibcode | paper |
|---|---|
| `2024MNRAS.528L..45R` | Rahaman, Granot & Beniamini, *Prompt gamma-ray burst emission from internal shocks — new insights* (11 cites) |
| `2024MNRAS.528..160R` | Rahaman, Granot & Beniamini, *Internal shocks hydrodynamics: the collision of two cold shells in detail* (4 cites) |
| `2025A&A...699A.139C` | Charlet, Granot & Beniamini, *Numerical simulations of internal shocks in spherical geometry* |

## What they predict (quoted from the abstracts)

Each collision drives a **forward shock (FS, weaker)** and a **reverse shock
(RS, stronger)**; optically thin synchrotron from *both* is claimed to explain
"pulse shapes, time evolution of the νFν peak flux and photon energy, and the
spectrum". Two spectral signatures are named explicitly:

> "(i) a sub-dominant low-energy spectral component (often interpreted as
> 'photospheric'-like), or (ii) a doubly broken power-law spectrum with the
> low-energy spectral slope approaching the slow-cooling limit."

and both "while maintaining high overall radiative efficiency without any fine
tuning". Charlet+2025 repeats that "the doubly broken power-law spectral shape
arises naturally from the optically thin synchrotron emission at both shock
fronts".

**This is our model census in their language.** Their (i) is what we fit as
Band+BB / CPL+BB / SBPL+BB; their (ii) is our DSBPL family. Their claim is that
these are the *same mechanism* in different parameter regimes — not two
different physical components.

## Why our sample is unusually well suited

* Single pulses ⇒ closest to their two-shell, one-collision idealisation. A
  multipulse burst superposes collisions; we largely avoid that.
* 24 models per spectrum ⇒ the two predicted shapes *compete directly*, on the
  same data, with the same statistic — the comparison they need but did not do.
* 106 bursts ⇒ population-level statements, not case studies.

## First look at what our data already says (83 bursts fitted so far)

| quantity | value |
|---|---|
| bursts with ≥1 bin won by a DSBPL-family model (their ii) | **35 / 83** |
| bursts with ≥1 bin won by a BB-bearing model (their i) | **67 / 83** |
| bursts showing **both** signatures | **31 / 83** |

That last number is the interesting one: their framework predicts the two
signatures arise from the same FS+RS pair in different regimes, so seeing both
*within one burst at different epochs* is expected — whereas a
photosphere-plus-synchrotron picture would more naturally keep them separate.
**31 of 83 is a real, testable population statement.** (Provisional: the fits
are complete, the selection rule for "won" is still the raw-AIC winner, which
the PI review has yet to fix.)

## The concrete tests

**T1 — Are the two signatures alternatives or companions?**
Per bin, classify: DSBPL-type / BB-type / neither / tie. Their model says a
given collision should show one *or* the other depending on the shell contrast;
across a burst's evolution both may appear. Measure the per-bin exclusivity and
the transition epoch. Data: the 24-model census, already computed.

**T2 — Does the DSBPL low-energy slope approach the slow-cooling limit?**
They predict α_low → the slow-cooling value. We have α₁ for every DSBPL fit and
the uniform-Band α for every bin, plus a line-of-death analysis already running.
This is a direct distribution test against a predicted limit, and it connects to
our epoch-dependent violation finding.

**T3 — Is the "photospheric-like" component really sub-dominant?**
Their (i) requires the low-energy component to be *sub-dominant*. We can compute
F_BB/F_total per BB-winning bin. If we find dominant blackbodies, that subset is
not explained by their mechanism.

**T4 — Does the fitted "kT" behave like a break energy rather than a temperature?**
If the BB is really FS synchrotron, the quantity we fit as kT should track a
spectral break. Our earlier per-burst work found a strong kT–break-energy
correlation (project lesson L25). A first pass across all BB-winning bins gives
corr(kT, DSBPL break) = **0.31** with median break/kT ≈ **2.7** — much weaker
than the earlier single-burst hint, so this needs doing properly (same-bin,
same-fit comparisons, error-weighted) before any claim. **Do not repeat the
L25 number as if confirmed at population level.**

**T5 — Pulse shape and spectral evolution jointly.**
They claim FS+RS reproduces pulse shapes *and* the νFν peak evolution. We have
the two-sigmoid asymmetry φ per burst and Ep(t) per bin: test whether bursts
with DSBPL-type spectra have systematically different φ from BB-type bursts.
No one has cross-matched pulse asymmetry against spectral-shape class.

## Honest cautions

1. Their predictions are qualitative in the abstracts ("approaching",
   "sub-dominant"). Before claiming a test we must read the papers and extract
   *numbers* — the predicted slope value, the predicted flux ratio range, the
   predicted break spacing. Without those, T2/T3 are illustrations, not tests.
2. Our DSBPL is the Ravasio-type empirical function, not their physical
   spectrum. Mapping empirical break parameters onto their FS/RS quantities
   needs a stated dictionary, or the comparison is cosmetic.
3. Selection: BB-bearing models win more often partly because there are more of
   them in the menu (9 of 24 contain a BB). Any prevalence statement must
   normalise for menu composition — otherwise we measure our own model list.

## Next actions

1. Pull the two 2024 MNRAS papers (arXiv PDFs) and extract quantitative
   predictions; record the exact equations and any figure we can digitise.
2. Write the empirical→physical dictionary (which fitted parameter maps to
   which shock quantity, and under what assumptions).
3. Run T1 and T3 on the full 106 once fitting completes; they need no new fits.
4. Only then decide whether this becomes a section of the survey paper or a
   companion paper of its own.

---

## T6 — ENERGY-RESOLVED MODEL DISCRIMINATION (new tool, 2026-08-17)

PI idea: rather than only comparing total AIC, ask **where in energy** two rival
models actually differ. Implemented as `dev/model_discrimination.py`:

* **Part A (no refit):** both models evaluated at their stored solutions, folded
  through the same responses; PGstat contribution computed per channel; the
  difference is summed in bands per detector. Exactly reproduces the stored AIC
  gap, so the decomposition is faithful.
* **Part B (scaffolded):** the notch test — refit both with a band excluded and
  see whether the preference survives.

**First result — `bn120119170` block 7, DSBPL vs SBPL+BB (ΔAIC = 0.10):**

| detector | 8–30 keV | 30–100 keV | 100–300 keV | 300–1000 keV | >1 MeV |
|---|---|---|---|---|---|
| n9 | **−1.03** | −0.41 | +0.32 | −0.00 | |
| na | +0.39 | **+1.49** | −0.08 | −0.05 | |
| nb | −0.53 | +0.05 | +0.01 | −0.06 | |
| b1 | | | −0.14 | −0.33 | +0.08 |

(negative = DSBPL better; positive = SBPL+BB better)

The statistical tie is **not** two models agreeing everywhere: SBPL+BB earns
~1.5 units in one detector's 30–100 keV range (where a Wien peak would sit)
while DSBPL earns ~1.5 units at 8–30 keV in two other detectors (where a second
break would sit). They trade evenly, so AIC calls it a draw — but the *physics*
of the disagreement is localized and interpretable.

This is directly the RGB discriminator: their (i) sub-dominant low-energy
component and (ii) doubly-broken power law should differ in *specific* bands,
and this tool measures exactly that, burst by burst.

**Caveats already stated in the tool's docstring:** parameters are held at the
stored solution (decomposition, not re-optimization); channels are correlated
through the response, so per-channel values are diagnostic, not significance;
notch-test AICs are comparable only within the same notch.

**Provenance note:** the PI recalled this style of test from Basak & Rao. I
verified `2014MNRAS.442..419B` (their single-pulse, four-model study) and
Basak's thesis (`2014arXiv1409.5626B`): neither contains an energy-exclusion
discrimination method — they use χ²_red and F-tests. Unless a specific paper is
identified, **we should present this as our own method, not cite theirs for it.**

**Positioning warning from that same paper:** Basak & Rao already report
α > −2/3 in **63.4%** of hard-to-soft single pulses. Our line-of-death result
has a published precedent on this exact population; our contribution must be
the epoch resolution and the model competition, not the violation itself.

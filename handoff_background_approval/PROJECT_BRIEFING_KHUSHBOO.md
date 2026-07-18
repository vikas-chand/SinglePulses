# Project briefing for Khushboo — what we are doing and why
*(written 2026-07-17/18, after a full working day of decisions with Vikas;
companion to INSTRUCTIONS_KHUSHBOO.md, which tells you HOW to click — this
tells you WHY it matters. Read this first.)*

---

## 1. The one-sentence version

**We are measuring the complete empirical picture of the single GRB pulse —
its spectrum AND its time profile, together, over the widest energy band
Fermi allows (8 keV to above 100 MeV).**

Think of a single pulse as the *atom* of prompt GRB emission. Complex,
multi-pulse bursts are largely superpositions of these atoms, so before anyone
can understand the complex bursts, someone must measure the atom properly and
uniformly. That is this project.

## 2. Why SINGLE pulses?

Hakkila & Preece (2011) showed that the confusing "intensity-tracking"
spectral behaviour of multi-pulse GRBs (where the peak energy seems to follow
the flux up and down) can be reproduced simply by OVERLAPPING two or more
clean hard-to-soft pulses. In other words: much of the apparent spectral
complexity of GRBs is *contamination from pulse overlap*, not physics.

A single, isolated rise–peak–decay has no such contamination. Whatever
spectral evolution we measure in it is intrinsic. That is why the sample is
106 single-pulse Fermi/GBM bursts, selected by the shape-based algorithm of
Busby & Lazzati (2024) — a *morphology* selection, not a brightness one.

## 3. Why EMPIRICAL models — and the full "shape menu"

We deliberately do NOT assume a radiation mechanism (synchrotron,
photosphere, ...). Each mechanism predicts a spectral *shape*; the honest
measurement is: fit ALL plausible empirical shapes to every time-resolved
spectrum, let the data pick, and report the census of what wins, how often,
and with how much ambiguity. Physics comes afterwards, in the Discussion.

The menu (now 24 models) contains, in families:
- **single-component curvature**: Band, CPL (cutoff power law), SBPL
  (smoothly broken power law), SBPL with FREE smoothness (how *sharp* is the
  peak?), and the double-broken 2SBPL (a second, low-energy break —
  the "two-break" shape of Oganesyan/Ravasio);
- **+ thermal**: each continuum + a blackbody (Band+BB, CPL+BB, SBPL+BB) —
  the photospheric-bump hypothesis;
- **+ high-energy extra component**: each continuum + an extra power law or
  cutoff power law pivoted at 100 MeV (Band+PL, CPL+PL, ... ) — the
  "something above the peak" hypothesis; and multiplicative cutoffs
  (Band×Cut, SBPL×Cut) — the absorption hypothesis;
- **THREE-component (added today)**: continuum + blackbody + high-energy
  extra, in all combinations (Band+BB+PL etc.) — the Guiriec (2015) model.

Two important framing decisions Vikas fixed today:
- **"Two-breaks" is NOT the thesis.** If 2SBPL wins somewhere, that is a
  *finding*; we are hunting ALL shapes, not defending one.
- The Ep–kT (Burgess-style) correlation is likewise a finding-if-present.

## 4. Why the WIDEST band (LLE + LAT)

GBM alone spans 8 keV–40 MeV. The *discriminating* features live at the band
edges: a low-energy break hides below; a cutoff, an extra component, or
absorption lives ABOVE the peak. Fermi uniquely extends the band via
**LLE (LAT Low-Energy events, 30–100 MeV)** and the **LAT itself
(>100 MeV)**. 13 of our 106 bursts have LLE data; wherever a pulse is bright
enough we do a JOINT fit: NaI + BGO + LLE + LAT in one likelihood (3ML).

**Two-tier time binning** (important concept): the fine Bayesian-block bins
that follow the GBM light curve have almost no LLE/LAT counts each. So for
LLE bursts we build a SECOND, COARSER time grid driven by the LLE counts
themselves, and fit the high-energy models there FIRST; the fine GBM grid is
analysed separately for the detailed low-energy evolution. One burst, two
grids, each where its statistics live.

## 5. The temporal half (also decided today)

The same single pulse has one shape in TIME, and we measure it in the same
framework, from the same Stage-1 selection you produce:
- durations (T90/T50, rest-frame where redshift exists), hardness evolution;
- **minimum variability timescale (MVT)** via the Haar-wavelet method of
  Bala et al., and how MVT changes with energy (Golkhou et al. 2015 found
  hard-band MVT is 2–3× shorter);
- **spectral lags** between energy bands (our own validated DCCF code);
- **pulse-shape fits**: Norris (2005) FRED, Kocevski (2003), and the new
  Gowri et al. (2025) two-sigmoid profile whose parameter φ measures pulse
  asymmetry.
Then the unifying questions: what is the spectrum during the RISE vs at the
PEAK vs in the DECAY? Do the temporal and spectral clocks agree?
(The validated temporal code was ported into the shared `grb_pipeline`
package today, from our LATBright project, and independently audited.)

## 6. "Single versus Rest" — the programme thesis (and the project's name)

Two literature facts we verified today, reading the papers:
- **Guiriec et al. 2015 (ApJ 807:148)**: the famous THREE-component spectrum
  (Band + blackbody + extra PL) has only ever been demonstrated in
  MULTI-pulse bursts (080916C, 090926A — the extra PL peaks in their sharp
  spikes). His clean single-pulse case (110721A — in our sample!) needed only
  two components.
- **Oganesyan et al. 2026 (A&A Lett., arXiv:2601.14393)**: MeV absorption
  (a dip between 1 and 100 MeV, from back-scattered X-rays) requires a DENSE
  wind-like medium around the progenitor. Our LLE band sits exactly inside
  that predicted window.

So the sharpest questions our survey can answer are partly NULLS:
- Does ANY clean single pulse require the three-component model? (If none of
  106 does, the third component is a multi-pulse phenomenon.)
- Does any show the MeV absorption signature? (If none, single pulses avoid
  dense-wind environments — an environmental statement.)
- How often is an extra high-energy component required at all? (Early answer:
  rarely but genuinely — e.g. 110721A's brightest phase decisively prefers
  CPL + an extra power law.)

Comparing these properties of single pulses against "the rest" (multi-pulse
GRBs) is the follow-up project — hence the directory name **SingleRest**.

## 7. The two arms — why YOUR selections matter twice

Every burst gets Stage-1 selections (detectors, backgrounds, source) from TWO
independent raters: an AI consensus (already done, all 106) and a HUMAN
(Vikas: 41 done, including all 13 LLE bursts; **you: the remaining 65**).
Everything downstream — binning, all 24 model fits — is run separately on
each arm with IDENTICAL machinery. Therefore:
1. **Science**: the human arm is the authoritative input to the physics paper.
2. **Benchmark**: the AI-vs-human comparison (and the you-vs-Vikas
   inter-expert scatter, which sets the fair yardstick) is itself a separate
   methods paper — "Can AI do GRB data analysis?" — with Vikas as lead.
Your clicks are data for both. That is why the GUI stamps who approved what,
and why you should judge from the light curves, not rubber-stamp the seeds.

## 8. Today's quality lesson — why we are so strict

We ran an independent, maximum-effort automated audit (OpenAI Codex,
gpt-5.6-sol "ultra") over the whole pipeline today. It found REAL bugs — the
kind that silently change published numbers: a cache that could serve the
wrong LAT time intervals; the binning script quietly re-introducing a
detector a human had rejected; an incorrect significance formula for the LLE
grids; multi-component fits stuck in bad minima. **All the critical ones were
fixed the same day and every affected product is being regenerated.** Three
practical consequences for you:
- Rules in the GUI exist for audited reasons (e.g. the blue "allowed band" in
  the source marker prevents a source overlapping a background window — a
  real failure mode we hit).
- NEVER hand-edit catalogs; the pipeline validates and stamps everything.
- Any number you see in the current draft is provisional until the clean
  re-runs finish. Do not quote headline numbers yet.

## 9. Where things stand right now

- Paper reframed and modularised (`paper/sections/`); the new Introduction
  (the framing in §1–6 above) is installed, every citation verified.
- Vikas's 13 LLE bursts = the spectral-modelling prototype: coarse LLE grids
  (with the corrected Li & Ma statistics: 10 of 13 have real LLE signal) and
  the full 24-model joint fits are re-running on the audited code.
- Your 65 bursts complete the human arm of the full 106.
- After your pass: ingest → re-bin → re-fit → the shape census, evolution,
  correlations, and the AI-vs-human benchmark.

## 10. Reading list (all verified — correct references)

Core framing:
- Hakkila & Preece 2011, ApJ 740, 104 — pulse superposition / why singles.
- Busby & Lazzati 2024, ApJ 972, 83 — the sample-selection algorithm.
- Burgess et al. 2019, Nat. Astron. (arXiv:1810.06965) — physical synchrotron
  fits ~95% of single-pulse GBM *spectra*; our empirical complement.
Shapes:
- Ravasio et al. 2018, A&A 613, A16 — the two-break 2SBPL in 160625B.
- Oganesyan et al. 2018 — low-energy breaks.
- Guiriec et al. 2015, ApJ 807:148 — the three-component model (multi-pulse).
- Oganesyan et al. 2026, arXiv:2601.14393 — MeV absorption / wind probe.
- Varun et al. 2025, arXiv:2510.24864 — fast-cooling + cutoff (241030A).
Temporal:
- Norris et al. 2005, ApJ 627, 324 — FRED pulse model.
- Kocevski, Ryde & Liang 2003, ApJ 596, 389 — KRL pulse shape.
- Gowri, Pe'er, Ryde & Dereli-Bégué 2025, ApJ 991, 230 (arXiv:2409.17860).
- Golkhou & Butler 2014, ApJ 787, 90; Golkhou, Butler & Littlejohns 2015,
  ApJ 811, 93 — MVT and its energy dependence.
Method:
- Scargle et al. 2013 — Bayesian blocks; Vianello et al. 2015 — 3ML.

Questions, disagreements with a seed, or a burst that looks "special"
(wrong pulse suggested, weird background) — flag it to Vikas immediately;
that judgement is exactly what the human arm is for. Welcome aboard the
shape hunt!

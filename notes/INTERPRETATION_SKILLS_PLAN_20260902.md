# INTERPRETATION SKILLS — THE PLAN (for discussion) — 2026-09-02

**The ruling this answers** (PI, 2026-09-02, verbatim): *"there is different thing I guess which
is literature in general and that is required to build skill files to intrepret and put our
analysis to use like Amati correlation, or calculations from all the things we got, basically
some physics, whether it goes even into unsupervised learning those people did on some of the
properties of GRBs, we should be able to provide any number for any kind of analysis people
want to perform on our GRB"*. And: *"skill files stays as they are, and we will do rounds to
improve them and consolidate them"* — so this plan ADDS skills; it does not restructure any.

Facts below come from two read-only inventories run today (what the pipeline measures; what
interpretation assets already exist here, in the sibling projects, and in memory) and from
33 ADS-verified references (§7). Proposals are marked PROPOSAL; the PI decides.

---

## §1 What we measure today, and what we do not

**Per block (12 rows per burst, 24 models):** every model's parameters with MINOS errors
(α, β, Ep, Ec, breaks, kT, hard-PL/CPL, cutoffs), fitted-curve νFν peak `EPK_CURVE`,
half-max width `WIDTH_HM`, N2LL/AIC/BIC/VALID/STATUS, the three LRTs, EAC constants, rail
diagnostics, AIC/BIC winners. **Per burst:** T90/T50 with truncation flags, Haar MVT, lag
(STALE, 0 rewalked), best pulse model NAME only, catalog fluence and 1024 ms peak flux
(inherited from GBM), block significances. **Redshift:** `results/redshifts.ecsv`, 13 of
106 (12 secure; bn110721200 ambiguous and already excluded by its P0 record).

**Not measured anywhere (no column, no code):** energy/photon FLUX per block from our own
models; fluence over our window; peak flux from our fits; MC flux errors persisted; hardness
ratio; pulse-shape parameters (rise, decay, FWHM, τ1/τ2 fitted but discarded); T90(E) slope;
ANY rest-frame quantity; no cosmology import; Amati/Yonetoku/Ghirlanda placement; Γ,
R_ph, R (Pe'er) or any photospheric estimate; DECISIVE construct; a per-burst feature row
joining spectral + temporal + identity; Z on any primary catalog. (Inventory: 17 items.)

**Consequence:** interpretation cannot start on the fit tables as they are. A DERIVED
QUANTITIES layer comes first, and it needs no redshift.

---

## §2 What already exists that interprets (nothing is invented below)

| capability | best existing asset | maturity |
|---|---|---|
| Amati / Yonetoku procedure | `dev/ai_guides/qc_flagging.md:77–105` (Step-9 addition, PI 2026-08-11): Ep,i, Eγ,iso 1–10⁴ keV rest with model k-correction, Liso from peak flux, ±2σ bands, frame discipline, verdicts CONSISTENT / OUTLIER_CANDIDATE; "small product script" never built | procedure written, no script |
| Rest-frame equations + working code | `~/Desktop/LATBright/skills/pulsewise_amati_yonetoku.md` Phase 5 (E_iso = 4π d_L² S/(1+z); L_iso = 4π d_L² F_peak (1+z); Planck18) and `LATBright/GRB260226A/s04d_amati_yonetoku.py` (697 lines, pseudo-z by intersection); `SingleRest/PulsewiseAmatiYonetoku/` master tables already carry Ep_rest, Eiso_52, Lp_52 for 167–325 pulses | skill + code in SIBLING repos; not wired here |
| Lag measurement (Norris convention) | `~/Desktop/LATBright/skills/pulsewise_lag.md`; `scripts/47c_lag_latbright.py` (the only quotable lag lineage) | measured; lag–luminosity step unwritten |
| Lag–MVT curvature test | `temporal_properties/lag_mvt_analysis{,_corr}.py`; registry #37; memory: a CONTROLLED REDO of Sonbas+2013, never "novel" | code for the slope; no Γ extraction |
| Photosphere (Gao & Zhang, Pe'er) | registry #43 Tier A (distance-free: kT, F_BB/F_tot, R = (F_BB/σT⁴)^½) / Tier B (full G&Z parameter surface on the z subset); `.claude/skills/grb-two-shock-analysis/references/12_*.md §11` (framework transcription) and `13_hybrid_jet_inference_workflow.md` (**PARKED**: derives Γ, R_ph, σ only after a BB is IDENTIFIED photospheric — principle 15) | designed, parked; needs per-block F_BB, F_tot |
| Bulk Lorentz factor from the pair-opacity cutoff | the PI's own Chand et al. 2020 (ApJ 903, 9) Table 2: Γ three ways after Lithwick & Sari 2001 (Γ_i from τ̂ with δT; Γ_ii ≈ E_cut/m_ec² (1+z); Γ_iii) | published PI convention; no script here |
| Ep–kT, two-break correlations, intrinsic scatter | `scripts/legacy/24_break_correlations.py` (observer-frame, "anti-Yonetoku" by design), `legacy/25_intrinsic_scatter_fits.py` (D'Agostini 2005 with intrinsic scatter; Burgess jet-composition slope), `legacy/14/18/19` (Burgess reproduction; 130427A reproduces, combined ρ anchor-dominated) | legacy; port-verify before reuse |
| Synchrotron / thermal identification | `notes/skills_from_Yu2019.md` C-column: C1 line-of-death ◐, C2 α_max ✗, C3 relation typing ◐, C4 Golenetskii ◐, C6 noise artefact ✗, C8 degeneracy menu ✗, C9 triangulation ✗, C10 empirical→physical ◐ — "the INTERPRETATION layer is the thin one" (its own summary) | 10 ✗, 12 ◐; no Interpretation.md |
| Two-shock / high-latitude / T90(E) physics | `.claude/skills/grb-two-shock-analysis/` (24 references: RGB2024, Li & Zhang 2021 HLE closure, Qin+2013 T90(E) + classification, Lu+2018 lag–Ep, Toffano low-energy breaks) | reading notes + workflows; nothing wired to our tables |
| Unsupervised classification (t-SNE/UMAP) | `~/Desktop/Projects/GRB_FFT_Interpretability/` — bit-match reproductions of Jespersen+2020 (99.03%), Steinhardt+2023 (99.06% Swift / 99.61% Fermi), García-Cifuentes+2023 (99.93%): each reduces to one scalar, the 0.01–0.1 Hz Fourier amplitude, a fluence-normalised duration proxy; `Projects_Details.md #27` gap inventory | mature, outside Two_Breaks; zero presence here |
| Hardness–duration, response-corrected | registry #46 + reference 22/23 (Qin+2013 count-space) | charter only |
| Bibliography | Amati 2002 only in the LATBright bib; Ghirlanda 2004, Norris 2000, Fenimore 2000, Gao & Zhang 2015, Sonbas 2015, Jespersen 2020, Steinhardt 2023 in NO .bib on disk; Yonetoku 2004 / Pe'er 2007 without bibcode fields | §7 supplies the verified bibcodes |

---

## §3 The design — two layers, one product (PROPOSAL)

**Pattern (the harness article, and our own skeleton):** the loop stays minimal; capability
lives in "the skills, approval points, verification criteria, and connections around it".
Each family = ONE skill file (the standard shape: Purpose · Inputs · Outputs · Phases with
commands · QC checklist · Pitfalls · What may NOT be claimed · lesson ledger with its own
prefix) + ONE small tool that reads our tables and writes columns or a product table.
Skills are written now (this program item); tools are built in the domain-tools phase,
except the Layer-D script, which the case study needs.

### Layer D — `DerivedQuantities.md` + `scripts/50_derived_quantities.py`
From the ADOPTED model (RULING A) and, alongside, the argmin — MODEL NAMED on every value:
- energy and photon FLUX per block in three bands: 10–1000 keV (the GBM catalog convention,
  von Kienlin+2020 / Poolakkil+2021), 1–10⁴ keV (the Amati bolometric band, Amati 2002/2006),
  and our fitted band; MC-propagated errors (the `scripts/32` pattern); fluence over the
  stamped window with T9 component coverage; peak flux on the catalog's 1.024 s definition;
- hardness ratio(s) on stated bands; Ep,obs from `EPK_CURVE` with the edge stamps;
- for every BB-carrying model: F_BB, F_tot, F_BB/F_tot and R = (F_BB/σ_SB T⁴)^½ (Pe'er+2007
  effective size) — #43 Tier A, distance-free;
- pulse parameters persisted from step 7 (rise, decay, FWHM, τ1/τ2, asymmetry) once the
  temporal step writes them (they are fitted today and discarded);
- Z joined from `results/redshifts.ecsv` with its source and confidence.
Every value carries the FRAME COORDINATES (band · interval · T0 · detector set · model ·
component coverage) and a SYMBOL: **detection / conditional estimate / upper limit /
unconstrained** (#43 risk 2). This is R3's count-coordinates rule extended to numbers.

### Layer I — the interpretation skills (each on top of D)
| # | skill | computes | needs | anchors (ADS-verified, §7) | prefix |
|---|---|---|---|---|---|
| I1 | **Energetics.md** | Ep,i = Ep(1+z); Eγ,iso (1–10⁴ keV rest, k-correction integrating the adopted model — say which); Liso from peak flux; rest-frame T90/T50/MVT/lag; the (1+z) sign discipline; cosmology Planck 2018 (H₀ 67.4, Ω_m 0.315 — the Li+2021 template's choice) | z (12 secure); Layer D | Amati 2002/2006, Yonetoku 2004; the LATBright skill's Phase 5 as the port source (port-verifier) | EN |
| I2 | **Correlations.md** | placement with ±2σ on: Amati (Ep,i–Eiso), Yonetoku (Ep,i–Liso), Ghirlanda (needs a jet break → UNCONSTRAINED unless the afterglow module supplies it), Norris lag–L (blocked until the lag rewalk), Fenimore/Reichart variability–L, Golenetskii F–Ep per block (observer frame, Yu+2019 C4), Ep–kT (Burgess, jet composition), lag–MVT (#37, a REDO of Sonbas+2013), pulse width–energy (Norris 2005), MVT–Γ (Sonbas 2015); fits with intrinsic scatter (D'Agostini, port of `legacy/25`); Type I/II by Minaev & Pozanenko 2020; verdict vocabulary CONSISTENT / OUTLIER_CANDIDATE from qc_flagging | I1 for rest-frame relations; D for observer-frame | Amati, Yonetoku, Ghirlanda 2004, Norris 2000, Fenimore 2000, Reichart 2001, Lloyd 2000, Nava 2012, Minaev 2020, Dainotti 2018 (selection effects), Ukwatta 2010, Norris 2005, Sonbas 2013/2015, MacLachlan 2013 | CR |
| I3 | **PhysicalEstimates.md** | Γ three ways from the pair-opacity cutoff (Lithwick & Sari 2001, exactly as Chand+2020 Table 2; needs a genuine cutoff — project #34's test — and z); emission radius and Γ from MVT/lag curvature (#37); photosphere Tier A (D) and Tier B (Gao & Zhang 2015 parameter surface, the PARKED workflow 13 made live ONLY under principle 15: a BB must first be identified photospheric); synchrotron line-of-death (α > −2/3) and the Yu+2019 C-column tests (α_max, cutoff genuineness, noise artefact, degeneracy menu, triangulation); afterglow-onset Γ (Liang 2010, Ghirlanda 2018) = module-future, cited not computed | D, I1, the BB census with L25/L28 stamps | Lithwick & Sari 2001, Pe'er 2007, Ryde & Pe'er 2009, Gao & Zhang 2015, Golkhou 2015, Liang 2010, Ghirlanda 2018, Band 1993 | PH |
| I4 | **PopulationFeatures.md** | the per-burst FEATURE ROW people's studies consume: T90, T50, hardness, Ep, α, β, fluence, peak flux, MVT, lag, the Fourier-amplitude proxy (the one scalar the t-SNE/UMAP classifiers reduce to, per the GRB_FFT_Interpretability audit), EH and Type I/II (Zhang 2009; Minaev 2020), hardness–duration (Qin 2013, #46); placement of our burst in Jespersen 2020 / Steinhardt 2023 / Salmon 2022 spaces using THEIR published transformations, never a refit; output `results/features/<trig>_features.ecsv` | D; step 7; the sibling audit repo as port source | Jespersen 2020, Steinhardt 2023, Salmon 2022, Zhang 2009, Minaev 2020, Kaneko 2006, Yu 2016, Scargle 2013 | PF |

**The product ("any number"):** one machine-readable table per burst joining D + I1–I4
rows, every number with coordinates, symbol, provenance (fit-table sha, engine commit,
**model id** — the harness gap found today — z source), and a "what may NOT be claimed"
block. Its contract is the output section of `DerivedQuantities.md`, not a fifth skill.

---

## §4 Blockers and prerequisites (facts)
1. **Redshift**: 13/106 recorded, all "GRBweb compilation" provenance; L21 wants the primary
   circular/paper. A z harvest across all 106 is a step-0 duty (cheap: the dossiers already
   quote z where GCNs carry it).
2. **Lag**: catalog column STALE-PENDING-REWALK, 0 bursts repaired → Norris lag–L and lag–MVT
   wait for the step-7 rewalk (validated tool exists: 47c).
3. **MVT**: canonical Bala only for 2 bursts; Haar in the catalog → MVT–Γ conditional.
4. **Pulse parameters** not persisted → widths and asymmetries need a one-line change in step 7.
5. **Model id** not recorded on any product (harness comparison) → add to provenance before
   the interpretation tables exist, so their provenance is complete from day one.
6. **Legacy correlation code** predates the engine fixes → port-verifier before reuse.
7. **Bibliography**: §7 bibcodes go into `paper_agentic/agentic_grb.bib` via ADS export
   (hand-written BibTeX forbidden).

---

## §5 Sequencing (PROPOSAL)
1. Write the five skill files (D, I1–I4) — this program item; discuss each at a gate.
2. Build `scripts/50_derived_quantities.py` (Layer D) — needed by the case study; no z needed.
3. Case study burst: D + I1 + I2 Amati/Yonetoku on a secure-z burst (candidates: bn081222204
   z = 2.77 secure, already walked as #2; bn130518580 z = 2.488 secure; bn120624933 z = 2.197
   secure) → the paper's demonstration and the seed of the eval set.
4. I3 Tier A on the BB population (#43), I4 features for all 106 — domain-tools phase.
5. Tier B / Γ / lag relations as the blockers in §4 clear.

---

## §6 Decisions for the PI
1. The family list: D + I1 Energetics + I2 Correlations + I3 PhysicalEstimates + I4
   PopulationFeatures, with the "any number" table as D's output contract.
2. Port sources: reuse the LATBright Amati/Yonetoku skill + code and the sibling audit repo
   (through the port-verifier), or write fresh from the equations.
3. Redshift harvest for all 106 now (step-0 duty) or only for the case-study burst.
4. The ledger re-order implied by decision 4 (per-event literature to the END as compare +
   reconcile): apply now, or leave 0b in place until the consolidation round.

---

## §7 References verified against ADS today (bibcode · first author · year · title)
| key | bibcode | title |
|---|---|---|
| Band 1993 | 1993ApJ...413..281B | BATSE observations of GRB spectra. I. Spectral diversity |
| Norris 1996 | 1996ApJ...459..393N | Attributes of pulses in long bright GRBs |
| Lloyd 2000 | 2000ApJ...534..227L | Cosmological versus intrinsic: intensity–νFν-peak correlation |
| Norris 2000 | 2000ApJ...534..248N | Energy-dependent lags and peak luminosity |
| Fenimore 2000 | 2000astro.ph..4176F | Redshifts for 220 BATSE GRBs from variability (eprint) |
| Reichart 2001 | 2001ApJ...552...57R | A possible Cepheid-like luminosity estimator |
| Lithwick & Sari 2001 | 2001ApJ...555..540L | Lower limits on Lorentz factors in GRBs |
| Amati 2002 | 2002A&A...390...81A | Intrinsic spectra and energetics of BeppoSAX GRBs with known z |
| Yonetoku 2004 | 2004ApJ...609..935Y | GRB formation rate from the Ep–peak luminosity relation |
| Ghirlanda 2004 | 2004ApJ...616..331G | Collimation-corrected energies correlate with Ep |
| Norris 2005 | 2005ApJ...627..324N | Long-lag, wide-pulse GRBs |
| Amati 2006 | 2006MNRAS.372..233A | The Ep,i–Eiso correlation: updated observational status |
| Kaneko 2006 | 2006ApJS..166..298K | Complete spectral catalog of bright BATSE GRBs |
| Pe'er 2007 | 2007ApJ...664L...1P | Initial size and Lorentz factor of GRB fireballs |
| Ryde & Pe'er 2009 | 2009ApJ...702.1211R | Quasi-blackbody component and radiative efficiency |
| Zhang 2009 | 2009ApJ...703.1696Z | Discerning the physical origins of cosmological GRBs |
| Liang 2010 | 2010ApJ...725.2209L | Constraining the initial Lorentz factor with afterglow onset |
| Ukwatta 2010 | 2010ApJ...711.1073U | Spectral lags and the lag–luminosity relation (Swift/BAT) |
| Nava 2012 | 2012MNRAS.421.1256N | A complete sample of bright Swift long GRBs: spectral–energy correlations |
| Lu 2012 | 2012ApJ...756..112L | Comprehensive analysis of Fermi GRB data II: Ep evolution patterns |
| MacLachlan 2013 | 2013MNRAS.432..857M | Minimum variability time-scales of long and short GRBs |
| Scargle 2013 | 2013ApJ...764..167S | Bayesian block representations |
| Gao & Zhang 2015 | 2015ApJ...801..103G | Photosphere emission from a hybrid relativistic outflow |
| Golkhou 2015 | 2015ApJ...811...93G | Energy dependence of GRB minimum variability timescales |
| Sonbas 2015 | 2015ApJ...805...86S | GRBs: temporal scales and the bulk Lorentz factor |
| Yu 2016 | 2016A&A...588A.135Y | Fermi GBM time-resolved spectral catalog |
| Ghirlanda 2018 | 2018A&A...609A.112G | Bulk Lorentz factors of GRBs |
| Dainotti 2018 | 2018PASP..130e1001D | GRB prompt correlations: selection and instrumental effects |
| Jespersen 2020 | 2020ApJ...896L..20J | Unambiguous separation of GRBs into two classes from prompt emission |
| Minaev 2020 | 2020MNRAS.492.1919M | The Ep,i–Eiso correlation: type I GRBs and a new classification |
| von Kienlin 2020 | 2020ApJ...893...46V | The fourth Fermi-GBM GRB catalog |
| Poolakkil 2021 | 2021ApJ...913...60P | The Fermi-GBM GRB spectral catalog: 10 years |
| Salmon 2022 | 2022Galax..10...78S | Two classes of GRBs distinguished within the first second |
| Steinhardt 2023 | 2023ApJ...945...67S | Classification of BATSE, Swift and Fermi GRBs from prompt properties |
(Sonbas 2013 = 2013ApJ...767L..28S is already in the corpus, read=Y.)

## §8 Decision log
| when | item | PI ruling (verbatim) | applied in |
|---|---|---|---|

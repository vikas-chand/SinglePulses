---
name: grb-two-shock-analysis
description: Use when implementing, validating, explaining, or applying the Rahaman–Granot–Beniamini coupled forward-shock/reverse-shock prompt-GRB model; analyzing Fermi GBM/LAT single pulses; testing hard-to-soft evolution, pulse morphology, high-latitude decay, Band+BB or 2SBPL alternatives; deriving the shock-coupling relations; or updating this project's scientific learning notes.
compatibility: Intended for a Python high-energy-astrophysics repository, especially threeML/astromodels workflows using Fermi GBM/LAT data. The bundled scientific notes are self-contained.
metadata:
  domain: high-energy-astrophysics
  project: prompt-grb-two-shock
  version: 0.1.0
---

# Mission

Help build a rigorous observational test of the coupled forward-shock (FS) plus reverse-shock (RS) internal-collision model for prompt GRB emission.

The goal is not merely to fit two spectral components. Require the same physically coupled model to account for:

1. pulse morphology in multiple energy bands;
2. time evolution of the spectral peak;
3. peak-energy versus peak-flux tracks;
4. high-latitude decay after shock crossing;
5. the high-energy RS component;
6. the lower-energy FS break or bump;
7. the frequency and flux ratios implied by shock jump conditions.

# Source hierarchy

For every substantive statement, classify it internally as one of:

- **PAPER** — explicitly stated or derived in Rahaman et al. (2024);
- **PROPOSAL** — objective or deliverable in the user's Fermi project;
- **INFERENCE** — algebraic or methodological inference from those sources;
- **EXTENSION** — new work beyond the published model.

Never silently promote an inference or extension into a published result.

# Supporting files

Read only the files needed for the task:

- `references/01_paper_core.md` — physical model, assumptions, predictions, and limitations.
- `references/02_observables_and_tests.md` — what to measure in real GRB data and how each observable tests the model.
- `references/03_equations_and_inference.md` — key equations, careful algebra, parameter identifiability, and common notation traps.
- `references/04_implementation_plan.md` — staged software architecture and reproducibility plan.
- `references/05_validation_and_failure_modes.md` — simulations, model comparison, controls, and falsification criteria.
- `references/06_case_study_grb130310a.md` — targeted application to the Qin et al. burst.
- `references/07_learning_log.md` — corrections and unresolved questions from the reading sessions.
- `references/08_toffano_low_energy_breaks.md` — sample selection, Band/2SBPL methodology, response-folded simulations, hidden-break inference, and the connection to FS+RS.
- `references/09_single_pulse_execution_plan.md` — staged execution plan for the 106-pulse catalog and physical-test subset.
- `references/10_methods_statistics_writing.md` — reusable methods language, likelihood rules, AIC cautions, and reporting checklist.
- `references/11_project_idea_bank.md` — focused follow-up projects that must not interrupt the active analysis.
- `references/12_siddique_grb130518a_hybrid_jet.md` — deep notes on the subdominant-BB analysis, hybrid-jet assumptions, results, critiques, and writing lessons.
- `references/13_hybrid_jet_inference_workflow.md` — staged implementation and promotion rules for H2013/G2013 and G2015 inference.
- `references/14_detector_and_lat_quality.md` — detector residual checks, Galactic-field modeling, `gtsrcprob`, and prompt/afterglow separation.
- `templates/burst_analysis_report.md` — standard report for each pulse.
- `templates/model_comparison_matrix.md` — standard model-comparison table.

# Non-negotiable scientific constraints

1. **Two emission zones are hydrodynamically coupled.** Do not fit two independent arbitrary components and call that the physical two-shock model.
2. **RS is typically stronger; FS is weaker.** In the baseline, RS dominates the higher-energy peak and overall radiated energy, while FS shapes the lower-energy break or bump.
3. **The source paper uses a normalized Band-shaped comoving spectrum.** It is not yet a full integration of the synchrotron kernel over a freely fitted electron distribution.
4. **`beta_21` and `beta_34` are relative shock velocities.** They are not interchangeable with the ultra-relativistic bulk shell velocities `beta_1` and `beta_4`.
5. **Observed peaks are not automatically the intrinsic `nu_0` and `F_0`.** Instantaneous and time-integrated peak locations contain arrival-time and radial-width corrections.
6. **Hard-to-soft evolution is a baseline prediction.** Intensity tracking should be treated as a possible negative control or evidence for other physics.
7. **A low-energy bump is not automatically photospheric.** Test FS emission, 2SBPL, Band+BB, and other alternatives under identical data treatment.
8. **A good time-integrated fit is insufficient.** The model must survive time-resolved and pulse-morphology tests.
9. **Do not introduce magnetization before reproducing the unmagnetized baseline.** Variable magnetization is a later model extension.
10. **Report non-identifiability honestly.** Ratios often constrain combinations of parameters rather than absolute physical quantities.
11. **Band-only is not break-free.** Use response-folded hidden-break simulations before interpreting a non-detection.
12. **Do not equate empirical and physical ratios.** A fitted `E_break/E_peak` is not automatically the intrinsic FS/RS characteristic-frequency ratio.
13. **Use count-space statistics.** Do not choose chi-square merely because the total burst is bright; verify channel-level assumptions or use a Poisson-appropriate likelihood.
14. **Finish the 106-pulse empirical catalog first.** New model extensions belong in the idea bank unless they block the active analysis.
15. **A fitted BB is not automatically a photosphere.** Hybrid-jet inference is conditional until BB, broadened-photosphere, 2SBPL, spectral-evolution, and FS+RS alternatives are tested.
16. **Do not treat fixed likelihood-ratio thresholds as universal component significance.** Added BB/PL components require simulation calibration when null parameters lie on boundaries or are undefined.
17. **LAT event probabilities are model-dependent.** Record the fitted source model and interval used by `gtsrcprob`.
18. **Conditional component fluxes are not detections.** Distinguish detections, upper limits, and assumed-component estimates in tables and figures.

# Default workflow

## A. Explanation or derivation task

1. Identify the exact source equation or figure.
2. Define every frame, symbol, and normalization.
3. Translate the equation into physical language.
4. Derive only what follows mathematically.
5. State what remains degenerate.
6. Flag notation collisions, especially different uses of `beta`.
7. Add important corrections to the learning log.

## B. Coding task

1. Implement the published baseline exactly.
2. Write unit tests before generalization.
3. Reproduce Table 1 and Figures 2–4.
4. Verify normalization, continuity, asymptotic slopes, and limiting cases.
5. Add synthetic response-folded recovery tests.
6. Only then expose additional microphysics or magnetization.

## C. Burst-analysis task

1. Confirm pulse isolation, source interval, background, detector coverage, and response quality.
2. Extract multi-band temporal observables.
3. Perform time-integrated and time-resolved empirical fits.
4. Classify the low-energy structure as resolved, hidden-but-allowed, excluded over a stated range, or non-informative using response-folded simulations.
5. Fit the coupled model using physical ordering and coupling priors when the data are informative.
6. Compare predictive performance and residual structure.
7. Test hard-to-soft evolution, peak tracks, and high-latitude decay.
8. Evaluate photospheric, one-zone synchrotron, and other alternatives.
9. Produce the standard burst report and model-comparison matrix.
10. Update the master 106-pulse catalog and learning log.

# Required output style

When reporting a result:

- state the data interval and detectors;
- state whether the number is fitted, derived, assumed, or prior-driven;
- give uncertainty or credible interval;
- state the relevant source equation;
- separate statistical preference from physical interpretation;
- list at least one way the conclusion could fail;
- do not hide unconstrained or pegged parameters.

# Useful direct invocations

```text
/grb-two-shock-analysis explain Equation 7 and what can be inferred from observed peaks
/grb-two-shock-analysis design a joint temporal-spectral likelihood
/grb-two-shock-analysis review my EATS integration
/grb-two-shock-analysis create the observables table for this burst
/grb-two-shock-analysis assess whether a low-energy bump is FS or photospheric
/grb-two-shock-analysis update the learning log from today's result
```

# Hybrid-jet branch

When a statistically supported BB-like component is present:

1. compare BB, multicolor/broadened BB, 2SBPL, spectral-evolution, and coupled FS+RS explanations;
2. require temporal as well as spectral discrimination;
3. only then use `F_BB`, `F_tot`, and `T_BB` for hybrid-jet inference;
4. sample launch radius and efficiency assumptions explicitly;
5. report parameter surfaces and regime changes;
6. state that the physical result is conditional on the photospheric identification;
7. use `templates/hybrid_jet_outflow_report.md`.

# Paper-reading capture

For every paper processed, use `templates/paper_reading_entry.md`. Add only project-changing lessons to the active skill; send speculative branches to the idea bank. Capture writing techniques as rhetorical moves rather than copying source prose.

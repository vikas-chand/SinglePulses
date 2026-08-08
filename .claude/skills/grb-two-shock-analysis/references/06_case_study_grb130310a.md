# Case study: GRB 130310A

## 1. Why this burst matters

Qin, Jiang & Wang (2021) report an extreme early peak energy and a weak low-energy component in GRB 130310A.

Key reported properties:

```text
T90 ~ 2.4 s
precursor + two main pulses
early Band-only E_pk ~ 7.4–11.1 MeV
early Band+BB Band E_pk ~ 5.2–8.5 MeV
early BB kT ~ 5–7 keV
later E_pk ~ 1 MeV
predominantly hard-to-soft evolution
precursor BB kT = 45.4 ± 7.0 keV
```

The early `Band+BB` preference is strong relative to Band alone in the authors' model comparison, but that analysis does not test the coupled FS+RS model.

## 2. Competing interpretations

### Qin et al. interpretation

- weak early thermal component from the photosphere;
- dominant Band component from an optically thin nonthermal region;
- low-sigma internal shocks have difficulty producing the extreme peak energy;
- photosphere-internal-shock upscattering is considered viable;
- ICMART is not fully excluded under some assumed parameters.

The burst has no measured redshift, so many derived quantities depend on a broad assumed redshift and jet-base radius range.

### Two-shock alternative

- lower-energy feature: weaker FS;
- higher-energy peak: stronger RS;
- both optically thin;
- hard-to-soft evolution tied to EATS and shock crossing;
- pulse morphology and component ratios must obey the same collision hydrodynamics.

## 3. Critical tests

### 3.1 Continuum comparison

Fit the same intervals and detector data with:

```text
Band
SBPL
2SBPL
Band+BB
SBPL+BB
single-zone synchrotron
coupled FS+RS
```

The central question is whether the low-energy component remains necessary as a thermal BB after physically allowed nonthermal curvature is included.

### 3.2 Temporal association

Test whether the low-energy feature:

- begins with the main collision pulse;
- follows the predicted FS temporal track;
- has a peak time distinct from the RS-dominated MeV component;
- produces a shoulder or plateau in low-energy light curves.

A component that precedes each main pulse and is substantially sharper would support a photospheric interpretation.

### 3.3 Coupling relations

Infer:

```text
nu_0,FS / nu_0,RS
F_0,FS / F_0,RS
shock-strength ratio
epsilon_rad,FS / epsilon_rad,RS
```

Check whether the values are consistent with a weak marginal/fast FS and strong fast RS.

### 3.4 Hard-to-soft track

Fit the early `E_pk(t)` and `(nu F_nu)_pk(t)` jointly. Test:

- monotonic hard-to-soft evolution;
- the decay-phase cubic peak track;
- whether the apparent later intensity tracking is caused by pulse superposition.

### 3.5 Absolute peak energy

Important limitation: the Rahaman Letter primarily explains relative component structure and normalized temporal evolution. It does not by itself prove that the baseline microphysics can produce an absolute RS peak of 5–11 MeV.

A complete application must either:

- allow the characteristic frequency normalization to be fitted phenomenologically first; or
- introduce a physical synchrotron normalization from `B'`, `gamma_m`, and Doppler factor, then test whether the required parameters are credible.

Do not claim that the two-shock model solves the extreme `E_pk` problem until this absolute scaling is checked.

## 4. Precursor interpretation

The reported precursor is much hotter than the weak BB-like component in the main pulse.

Possible outcomes:

- precursor remains a narrow BB and precedes the collision emission: evidence for a real photosphere;
- main low-energy feature is better explained by FS: mixed photosphere plus two-shock scenario;
- both are reproduced by nonthermal models: photospheric claim weakened;
- neither is robust under alternative continua and simulations: component significance uncertain.

The two-shock framework does not require the photosphere to be absent. It tests whether the main-pulse low-energy feature must be photospheric.

## 5. Recommended pilot analysis

1. Reproduce Qin et al. detector selection, background, and time bins.
2. Verify the published Band and Band+BB results.
3. Add SBPL, 2SBPL, and SBPL+BB.
4. Fit the coupled analytic FS+RS model.
5. Run null simulations for the low-energy component.
6. Construct energy-resolved light curves.
7. Perform a joint temporal-spectral fit.
8. Compare photospheric onset/width predictions with FS timing.
9. Report which conclusions survive model choice.

## 6. Why it is a high-value test

GRB 130310A combines:

- an unusually large high-energy peak;
- a claimed weak thermal component;
- rapid hard-to-soft evolution;
- broad Fermi coverage;
- a precursor.

That makes it a demanding stress test of the proposal's central degeneracy:

```text
Band + BB
versus
coupled FS + RS
versus
doubly broken nonthermal continuum.
```

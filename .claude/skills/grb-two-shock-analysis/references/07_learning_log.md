# Project learning log

Update this file whenever a reading session, derivation, simulation, or fit changes the project understanding.

---

## 2026-08-07 — Rahaman et al. reading synthesis

### Core understanding

- A single internal collision produces both FS and RS emitting zones.
- RS is generally stronger and dominates the high-energy `nu F_nu` peak.
- FS is weaker and can produce either a low-energy break or a BB-like bump, depending on its cooling regime.
- The model predicts pulse morphology and spectral evolution together through shock crossing and EATS geometry.
- The post-crossing tail is high-latitude emission.
- Monotonic hard-to-soft evolution is a baseline prediction.
- Intensity tracking is a useful negative control and may point to magnetic reconnection.
- A true photosphere may be earlier, sharper, and harder at low energy.

### Hydrodynamic details learned

- `t_on = t_eject,back - t_eject,front` because the back edge is launched later.
- If one shock crosses first, a rarefaction wave can stall the other.
- Both shocks complete only for a limited shell-width ratio.
- The FS completion signal can arrive before the RS completion signal even when the RS crosses first in lab time, because arrival time depends on emission radius and path length.

### Cooling and efficiency

- Hydrodynamic dissipation efficiency and electron radiative efficiency are different quantities.
- The fiducial dissipation is roughly 5% RS, 3% FS, and 9% total.
- RS fast cooling supplies high radiative efficiency.
- Weak FS can be marginally fast or slow enough to harden the low-energy spectrum without strongly reducing total efficiency.

### Equation 7 correction

Earlier discussion risked treating `beta_21` and `beta_34` as nearly one because the bulk shells are ultra-relativistic. That is incorrect.

They are relative shock velocities. Using Table 1:

```text
beta_21 ~ 0.228
beta_34 ~ 0.429
beta_21/beta_34 ~ 0.53
```

The beta factor must be retained when inferring the radiative-efficiency ratio.

### Spectral-kernel correction

The published model is not literally two arbitrary SBPL components and is not yet a full numerical synchrotron kernel. It uses two hydrodynamically coupled normalized Band-shaped functions with synchrotron-motivated slopes.

### Data-analysis lesson

A spectral-only two-component fit can be highly degenerate. The temporal behavior—component peak times, energy-dependent pulse shape, hard-to-soft evolution, and HLE decay—is essential for identification.

### Project priority

The most important observational test is:

```text
Can one coupled model explain pulse shape + time-resolved spectrum + component ratios?
```

not merely:

```text
Does it fit better than Band?
```

### Important application

GRB 130310A is a high-value pilot because the main-pulse low-energy feature could be either a photosphere or the predicted FS feature. The precursor may still be genuinely photospheric.

### Unresolved items

- Read and implement the supplementary appendices defining EATS bounds and analytic approximations.
- Locate the earlier observational paper discussed verbally that analyzed approximately 38 Fermi pulses and measured rise/decay or high-latitude properties. Do not guess its identity.
- Determine the minimum data quality required to separate FS and RS.
- Decide whether the first real-data model uses the exact analytic Band-shaped kernel or a full synchrotron kernel.
- Quantify how absolute 5–11 MeV peak energies constrain microphysics.
- Test the impact of spherical dynamics.
- Treat variable magnetization as a later extension after the baseline.
- Define a negative-control intensity-tracking sample.
- Define the inclusion rule for an additional LAT power law.

---

## 2026-08-08 — Toffano et al. synthesis and project focus

### Project decision

- Complete the existing 106 single-pulse GRB analysis before beginning an unbounded new literature sweep.
- Preserve targeted paper reading, but make it serve concrete analysis choices.
- Treat empirical break detection, detector identifiability, and physical interpretation as separate layers.

### Toffano lessons

- A Band-only fit does not prove that a low-energy break is absent.
- Break detectability depends strongly on `E_break/E_peak`, absolute energies, S/N, background, and response.
- `alpha_Band` may be an effective average over two unresolved spectral segments.
- The paper's `Delta AIC >= 6` threshold is useful as a replication benchmark, not as a universal component-significance rule.
- The primary pipeline should use a Poisson-appropriate count likelihood and simulation-calibrated component tests.
- Time-integrated spectra maximize S/N but can mix spectral evolution; time-resolved checks are mandatory.
- LLE can be decisive when GBM cannot constrain the high-energy turnover.

### Connection to the coupled shock project

- Toffano provides the empirical and detectability framework.
- Rahaman et al. provide a candidate physical FS+RS framework.
- The fitted 2SBPL ratio `E_break/E_peak` must not be equated directly with the intrinsic FS/RS frequency ratio without forward-model calibration.
- Any observed 2SBPL, Band+BB, or related low-energy structure is a candidate morphology to test, not proof of FS/RS emission.

### Immediate actions

1. Freeze the 106-pulse master sample and data-coverage table.
2. Inventory all LLE/LAT pulses.
3. Run a ten-pulse end-to-end pilot.
4. Add hidden-break simulations to the standard report.
5. Scale the validated pipeline to all pulses.

---

## 2026-08-09 — Siddique et al. (2022), GRB 130518A

### Source-derived lessons

- Joint GBM+LAT fits favor a subdominant BB added to the nonthermal continuum in the integrated spectrum and the two brightest bins.
- The integrated BB fraction is about six percent in the source analysis.
- H2013/G2013 and G2015 convert `F_BB`, `F_tot`, and `T_BB` into conditional outflow properties.
- Both frameworks reject a pure fireball in the scenarios studied.
- Small launch radii tend to favor internal shocks; large launch radii and low efficiency can permit reconnection.

### Project corrections and cautions

- The BB identification must be tested against 2SBPL, broadened photospheres, spectral evolution, and coupled FS+RS emission before hybrid-jet inference.
- Use a source-plus-background likelihood and simulation-calibrated component tests; do not rely only on fixed Wilks thresholds for an added BB.
- Treat BB fluxes in non-significant bins as conditional estimates or limits, not detections.
- Recompute or verify LAT event probabilities with an interval-appropriate source model.
- Record Galactic-plane proximity, extended sources, and diffuse models for every LAT field.
- A detector can be removed for a documented detector-specific systematic residual trend, not because it changes the preferred physics.

### New implementation priority

Implement and validate the H2013/G2013 and G2015 scaling relations from the primary papers. Reproduce the GRB 130518A tables and parameter maps, then test how a synthetic FS low-energy bump biases the inferred photospheric magnetization when it is fitted as a BB.

### Writing lessons

- Use an introduction funnel from unknown -> physical stakes -> competing models -> observable discriminator -> target data -> inference framework.
- Separate a concise preferred-model table from complete appendix fit tables.
- Organize the discussion by physical questions and state model assumptions before derived claims.
- Use component flux-fraction evolution as a compact diagnostic figure.


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

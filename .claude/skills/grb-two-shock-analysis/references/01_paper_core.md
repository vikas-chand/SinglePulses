# Rahaman et al. (2024): core scientific notes

## 1. Central idea

A collision between a slower leading shell and a faster trailing shell generically launches two shock fronts:

- a **forward shock (FS)** into the slower leading shell;
- a **reverse shock (RS)** into the faster trailing shell.

A contact discontinuity separates the two shocked regions. Both shocked regions move with the same downstream bulk proper speed, but the two shock fronts have different speeds and strengths.

For the fiducial constant-power collision, the RS is typically stronger than the FS. The paper computes optically thin emission from both shocks, integrates each over its equal-arrival-time surface (EATS), and adds the two observed contributions.

## 2. Why this differs from a one-zone model

The model contains two physically distinct emitting zones that are not arbitrary. Their relative frequencies, fluxes, crossing times, and pulse shapes are constrained by the same shell collision.

The proposed observational signature is:

- RS: stronger, fast cooling, dominant high-energy peak and overall radiated power;
- FS: weaker, fast or marginally fast cooling, lower-energy break or bump.

This two-zone structure can relieve the one-zone tension between:

- high radiative efficiency, which favors fast cooling;
- hard low-energy spectra, which often favor slow or marginally fast cooling.

The RS can maintain high efficiency, while the weaker FS controls the low-energy shape.

## 3. Baseline shell setup

The source ejects two cold, unmagnetized shells at constant isotropic-equivalent power:

- `S1`: slower, leading shell;
- `S4`: faster, trailing shell;
- activity durations: `t_on,1` and `t_on,4`;
- inactivity interval: `t_off`;
- shell proper speeds: `u1` and `u4`;
- proper-speed contrast: `a_u = u4/u1 > 1`.

The paper's fiducial values are:

```text
u1 = 100
u4 = 200
a_u = 2
t_on,1 : t_off : t_on,4 = 1 : 1 : 1
```

The collision begins at radius `R0`. The planar approximation keeps the shock and downstream proper speeds constant; spherical dilution is partially included through density `rho ∝ R^-2`.

## 4. Shock ordering and strength

The shock-front proper speeds satisfy:

```text
u_RS < u_downstream < u_FS
```

The RS front is slower in the lab frame but is generally the stronger shock. The relative shock strengths are:

```text
Gamma_21 - 1  # FS strength
Gamma_34 - 1  # RS strength
```

For the fiducial case in Table 1:

```text
Gamma_21 - 1 = 0.027
Gamma_34 - 1 = 0.107
```

Thus the RS is about four times stronger in this measure.

## 5. Shell crossing and rarefaction

The FS and RS usually have unequal shell-crossing times. For equal ejection durations, the RS crosses first.

When one shock finishes crossing its shell, the back of the shocked region may face vacuum and launch a rarefaction wave. That wave can propagate through the shocked material and stall the other shock before it completes its crossing.

For the paper's setup, both shocks can complete their crossings only over a finite range of shell-duration ratios. The paper derives approximately:

```text
0.42 <= t_on,1 / t_on,4 <= 2.68
```

and restricts illustrative calculations to:

```text
0.5 <= t_on,1 / t_on,4 <= 2
```

This is important when interpreting pulse widths: changing a shell duration beyond the allowed range does not indefinitely broaden the corresponding emission because rarefaction terminates dissipation.

## 6. Dissipation and radiation efficiencies

For `a_u = 2`, the paper reports approximate kinetic-to-internal-energy dissipation efficiencies:

```text
RS: ~5%
FS: ~3%
overall: ~9%
```

These are **hydrodynamic dissipation efficiencies**, not the same as the electron radiative fraction.

The radiation model uses:

```text
epsilon_gamma = epsilon_e * epsilon_rad
```

where `epsilon_rad` is the fraction of electron energy radiated.

Baseline choices:

```text
RS: epsilon_rad = 1      # fast cooling
FS: epsilon_rad = 0.5    # marginally fast cooling
```

The paper also explores a fast-cooling FS in the time-integrated spectrum.

## 7. Why the two cooling regimes arise naturally

The microphysical parameters `(epsilon_e, epsilon_B, xi_e, p)` are assumed equal in both shocked regions.

Because the dynamical times are similar, the cooling Lorentz factors are similar. However, the minimum electron Lorentz factor scales with shock strength:

```text
gamma_m ∝ Gamma_ij - 1
```

The stronger RS therefore has larger `gamma_m`:

```text
FS: gamma_m ~ gamma_c       -> marginally fast cooling
RS: gamma_m >> gamma_c      -> fast cooling
```

This separation is created by the hydrodynamics even though the microphysical parameters are held equal.

## 8. Equal-arrival-time surfaces

The observer time is:

```text
T = t - R cos(theta) / c
```

At fixed observer time, photons reaching the observer originate from an equal-arrival-time surface. For a constant shock-front Lorentz factor, the EATS is ellipsoidal.

The first on-axis photons from FS and RS arrive together because both shocks begin at the same collision event `(R0, t0, theta=0)`.

Although the RS finishes its shell crossing earlier in lab time in the fiducial case, the on-axis signal corresponding to the FS completing its crossing can arrive earlier because the FS front has a larger Lorentz factor and finishes at a larger radius. This is an emission-time plus path-length effect; no photon is overtaken.

After the shock has stopped emitting on axis, delayed photons from larger angles produce the high-latitude-emission tail.

## 9. Spectral prescription

The source paper uses a normalized Band-shaped function `S(x)` for the comoving spectral shape. The asymptotic `F_nu` slopes are chosen to represent synchrotron cooling regimes.

For `p = 2.5`:

```text
Marginally fast-cooling FS:
    b1 = +1/3
    b2 = -p/2 = -1.25

Fast-cooling FS or RS:
    b1 = -1/2
    b2 = -p/2 = -1.25
```

This is an analytic spectral prescription with synchrotron-motivated slopes. It is not yet a full numerical synchrotron kernel.

## 10. Main temporal predictions

For each shock:

- the pulse peaks at the arrival time corresponding to shock completion;
- the post-peak tail is dominated by high-latitude emission;
- the spectral peak energy evolves monotonically hard to soft;
- the instantaneous peak energy flux rises, may plateau, and then decays rapidly.

When FS and RS peak times are separated, their sum can show:

- a shoulder;
- a broad or narrow plateau;
- complex pulse morphology;
- frequency-dependent apparent peak times and widths.

Changing `t_on,1`, `t_off`, and `t_on,4` changes the relative FS/RS crossing times and therefore the combined pulse morphology.

## 11. Main spectral predictions

At intermediate times, the total instantaneous spectrum can display two bumps:

- lower-frequency FS feature;
- higher-frequency RS peak.

In the time-integrated spectrum:

### Fast-cooling FS + fast-cooling RS

The summed spectrum resembles a doubly broken power law with a low-energy break and a higher-energy peak.

### Marginally fast-cooling FS + fast-cooling RS

The FS produces a more distinct lower-energy bump. The total can resemble a dominant Band component plus a subdominant blackbody-like component, even though both components are optically thin and nonthermal in the model.

The low-energy feature becomes more prominent when the FS is longer lived.

## 12. Photosphere discrimination proposed by the paper

A true photospheric component should arise at smaller radius and may therefore show:

- earlier onset or a precursor to the pulse;
- a sharper spectral peak;
- a harder low-energy photon index.

An FS-generated photospheric-like bump is optically thin and tied to the same collision dynamics as the RS.

The paper allows that a real photosphere may contribute in some bursts; it does not claim every low-energy bump is nonthermal.

## 13. Alternative temporal behavior

The baseline model predicts monotonic hard-to-soft evolution.

Some bursts show intensity tracking, in which the peak energy follows intensity. The paper points to magnetic reconnection as a possible explanation and suggests that intensity tracking may indicate different underlying physics.

## 14. Stated limitations

- moderate proper-speed contrast fixed at `a_u = 2`;
- cold, unmagnetized shells;
- equal microphysical parameters in FS and RS;
- planar shock speeds with only partial spherical treatment;
- thin-shell, instantaneous emitting-region approximation;
- larger speed contrasts can predict excessively large RS/FS peak-energy ratios;
- finite emission width and full spherical shock dynamics remain future work.

These assumptions define the baseline to reproduce before adding complexity.

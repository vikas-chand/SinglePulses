# Key equations, inference, and notation cautions

## 1. Collision radius

For shell velocities `beta_1` and `beta_4` separated by source inactivity time `t_off`, the collision radius is approximately:

```math
R_0 =
\frac{\beta_1\beta_4 c t_{\rm off}}{\beta_4-\beta_1}
\simeq
\frac{2\Gamma_1^2 c t_{\rm off}}{1-a_u^{-2}} .
```

This connects the engine inactivity interval to the dissipation radius under the shell model.

## 2. Ejection duration and shell width

The shell activity duration is:

```math
t_{{\rm on},i}
=
t_{{\rm ej},b,i}
-
t_{{\rm ej},f,i}.
```

The back edge is ejected later than the front edge, so later minus earlier gives a positive duration.

For ultra-relativistic shells:

```math
\Delta_i \simeq c t_{{\rm on},i}.
```

## 3. Shock strengths

The two relative Lorentz factors are:

```math
\Gamma_{21} = \Gamma_2\Gamma_1(1-\beta_1\beta_2),
```

```math
\Gamma_{34} = \Gamma_3\Gamma_4(1-\beta_3\beta_4).
```

The dimensionless shock strengths are:

```math
s_{\rm FS} = \Gamma_{21}-1,
```

```math
s_{\rm RS} = \Gamma_{34}-1.
```

For the fiducial Table 1 values:

```text
s_FS = 0.027
s_RS = 0.107
```

The relative shocks are only mildly relativistic even though the bulk shells have Lorentz factors near 100 and 200.

## 4. Critical notation warning: the beta factor

Do not confuse:

```text
beta_1, beta_4
```

with:

```text
beta_21, beta_34.
```

The first pair are bulk shell velocities and are extremely close to one.

The second pair are relative velocities corresponding to `Gamma_21` and `Gamma_34`. They need not be close to one.

Using:

```math
\beta_{ij} = \sqrt{1-\Gamma_{ij}^{-2}},
```

and the fiducial shock strengths:

```text
Gamma_21 = 1.027  -> beta_21 ≈ 0.228
Gamma_34 = 1.107  -> beta_34 ≈ 0.429
beta_21 / beta_34 ≈ 0.53
```

Therefore, setting `beta_21/beta_34 = 1` would produce an order-unity bias in the inferred efficiency ratio.

This is an algebraic calculation from the paper's Table 1 values, not a number printed explicitly in the paper.

## 5. Equation 7 coupling

The paper gives:

```math
r_\nu
\equiv
\frac{\nu_{0,\rm FS}}{\nu_{0,\rm RS}}
\simeq
\left(
\frac{\Gamma_{21}-1}{\Gamma_{34}-1}
\right)^2 ,
```

and:

```math
r_F
\equiv
\frac{F_{0,\rm FS}}{F_{0,\rm RS}}
\simeq
\frac{\epsilon_{{\rm rad},\rm FS}}
     {\epsilon_{{\rm rad},\rm RS}}
\left(
\frac{\Gamma_{34}-1}{\Gamma_{21}-1}
\right)^2
\frac{\beta_{21}}{\beta_{34}} .
```

### 5.1 Shock-strength ratio

```math
\frac{\Gamma_{21}-1}{\Gamma_{34}-1}
\simeq
\sqrt{r_\nu}.
```

This constrains only the ratio of the shock strengths.

### 5.2 Radiative-efficiency ratio

Since the inverse square in the flux relation is `1/r_nu`:

```math
\frac{\epsilon_{{\rm rad},\rm FS}}
     {\epsilon_{{\rm rad},\rm RS}}
\simeq
r_F r_\nu
\frac{\beta_{34}}{\beta_{21}}.
```

Thus, the flux and frequency ratios jointly constrain the ratio of radiative fractions, provided the intrinsic `nu_0` and `F_0` are known and the hydrodynamic beta ratio is modeled.

### 5.3 Spectral-energy dominance

Multiply the two Equation 7 ratios:

```math
\frac{\nu_{0,\rm FS}F_{0,\rm FS}}
     {\nu_{0,\rm RS}F_{0,\rm RS}}
\simeq
\frac{\epsilon_{{\rm rad},\rm FS}}
     {\epsilon_{{\rm rad},\rm RS}}
\frac{\beta_{21}}{\beta_{34}}.
```

This is often more physically relevant than `F_0` alone.

For the fiducial numbers:

```text
r_nu ≈ (0.027/0.107)^2 ≈ 0.0637
epsilon_rad,FS / epsilon_rad,RS = 0.5
beta_21 / beta_34 ≈ 0.531

r_F ≈ 4.17
r_nu * r_F ≈ 0.266
```

So the FS can have a larger peak **flux density** at its much lower characteristic frequency while still having a smaller `nu F_nu` spectral-energy peak. This resolves an apparent contradiction with the statement that the RS dominates the radiated energy.

## 6. Intrinsic versus observed peak quantities

Equation 7 is written in terms of characteristic quantities at the collision scale:

```text
nu_0,i
F_0,i
```

These are not automatically identical to the peak measured from a time-integrated count spectrum.

### 6.1 Instantaneous spectrum

The paper approximates:

```math
(\nu F_\nu)_i
=
\nu_{{\rm pk},i}F_{\nu,{\rm pk},i}
S\left(\frac{\nu}{\nu_{{\rm pk},i}}\right).
```

The time evolution is:

```math
\nu_{{\rm pk},i} \propto T^{-1}
```

with the appropriate effective time before and after shock crossing.

### 6.2 Time-integrated peak correction

The paper gives approximately:

```math
\frac{\nu_{{\rm pk},i}}{\nu_{0,i}}
=
\left[
0.805 + 0.706 \left(\frac{R_{f,i}}{R_0}\right)
\right]^{-1}.
```

Define:

```math
A_i = 0.805 + 0.706(R_{f,i}/R_0).
```

Then:

```math
\frac{\nu_{0,\rm FS}}{\nu_{0,\rm RS}}
=
\frac{\nu_{{\rm pk},\rm FS}}{\nu_{{\rm pk},\rm RS}}
\frac{A_{\rm FS}}{A_{\rm RS}}.
```

A naive ratio of time-integrated observed peaks can therefore bias the inferred shock-strength ratio if the two radial extents differ.

The same issue applies to amplitudes because the time-integrated fluence peak includes `T_0`, `T_f`, and radial-width factors.

**Preferred practice:** fit the full time-dependent model and infer `nu_0,i` and `F_0,i` as latent parameters.

## 7. High-latitude decay relation

After shock crossing, the paper gives:

```math
(\nu F_\nu)_{{\rm pk},i}
\propto
T_{{\rm eff},2,i}^{-3},
```

```math
\nu_{{\rm pk},i}
\propto
T_{{\rm eff},2,i}^{-1}.
```

Eliminating time gives:

```math
(\nu F_\nu)_{{\rm pk},i}
\propto
\nu_{{\rm pk},i}^{3}.
```

This is a decay-phase prediction. Do not fit the cubic relation across the full rise, plateau, and decay indiscriminately.

## 8. Cooling and slopes

For a power-law electron distribution with `p > 2`:

```math
\gamma_m
\propto
\frac{\epsilon_e}{\xi_e}(\Gamma_{ij}-1).
```

Since `Gamma_34-1 > Gamma_21-1`:

```text
gamma_m,RS > gamma_m,FS.
```

With similar dynamical times and magnetic microphysics, `gamma_c` is similar in the two regions, motivating:

```text
FS: gamma_m ~ gamma_c
RS: gamma_m >> gamma_c
```

The paper's `b1` and `b2` are `F_nu` slopes. If a photon spectrum is written as:

```math
dN/dE \propto E^\alpha,
```

then:

```math
F_\nu \propto \nu^{\alpha+1}.
```

Therefore:

```text
b1 = +1/3  -> photon alpha = -2/3
b1 = -1/2  -> photon alpha = -3/2
b2 = -p/2  -> high-energy photon alpha = -p/2 - 1
```

Always state which convention is being used.

## 9. What cannot be inferred from Equation 7 alone

Equation 7 does not uniquely give:

- both absolute shock strengths;
- both shell Lorentz factors;
- absolute radiative efficiencies;
- magnetic field;
- collision radius;
- redshift;
- shell energies.

Additional temporal information, hydrodynamic priors, luminosity, redshift, and microphysical assumptions are required.

## 10. Practical inference order

1. Fit the complete coupled model to obtain posterior distributions for `nu_0,i`, `F_0,i`, and timing parameters.
2. Compute `r_nu` and `r_F` from posterior samples.
3. Map `r_nu` to a shock-strength ratio.
4. Use the modeled `beta_21/beta_34`, not a bulk-speed approximation.
5. Infer the radiative-efficiency ratio.
6. Check whether it agrees with the cooling-regime assumption.
7. Propagate all covariance.
8. Report absolute physical parameters only when the additional constraints justify them.

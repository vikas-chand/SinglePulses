# Project Charter — Response-Corrected GRB Duration and Hardness

## Working title

**The Transfer Function from Intrinsic GRB Duration–Hardness to Fermi/GBM Count Space**

## Motivation

GRB duration and hardness are often mixed across operational spaces:

```text
count-space T90
photon-fluence T90
count hardness
model-derived photon hardness
energy-fluence hardness
```

Qin et al. show that \(T_{90}\) changes with energy band and that count-space and photon-fluence durations broadly agree but are not identical. A consistent transfer-function study is required.

## Primary questions

```text
1. How different are count-space and photon-space T90?
2. How different are count-space and photon-space hardness?
3. How far does a burst move in the T90–HR plane?
4. Can detector angle or slew change its apparent class?
5. Which spectral-evolution regimes produce the largest bias?
```

## Observable definitions

### Count-space duration

\[
T_{90}^{C}
=
t_{95}^{C}-t_5^{C}.
\]

### Photon-fluence duration

\[
T_{90}^{N}
=
t_{95}^{N}-t_5^{N}.
\]

### Energy-fluence duration

\[
T_{90}^{E}
=
t_{95}^{E}-t_5^{E}.
\]

### Hardness

Calculate all three:

```text
HR_count
HR_photon
HR_energy
```

using explicitly documented energy bands.

## First literature definitions to reproduce

```text
Qin main-text HR:
    100–350 / 25–50 keV

Qin Figure-4-caption HR:
    100–350 / 50–100 keV

Goldstein Figure-5 HR:
    counts 50–300 / 10–50 keV
```

## Simulation model

Generate a time-dependent photon spectrum:

\[
F(E,t)
=
I(t)\phi(E,t).
\]

Vary:

```text
Band/CPL spectrum
hard-to-soft E_p evolution
tracking E_p evolution
thermal component
soft extended tail
multiple pulses
```

Forward fold:

\[
F(E,t)
\rightarrow
R(c,E,\theta,t)
\rightarrow
C(c,t).
\]

## Geometry

Test:

```text
fixed on-axis response
large incidence angle
time-dependent response during slew
different NaI detectors
joint detectors
```

## Outputs

```text
Delta log T90
Delta log HR
classification changes
bias maps versus E_p and angle
T90(E) slopes
duration-hardness trajectories
```

## Validation ladder

```text
1. identity response
2. diagonal response with finite energy resolution
3. real static GBM DRM
4. time-dependent response
5. source and background Poisson realization
6. real catalog reproduction
```

## First pilot

```text
one Kocevski pulse
one Band spectrum
one hard-to-soft law
six Qin energy bands
four response angles
with and without a soft tail
100 Monte Carlo realizations
```

## Publishable outcomes

```text
null:
    count observables are robust in defined regimes

conditional:
    biases become important near band boundaries or large angles

positive:
    count-space movement changes apparent short/long classification
```

## Central framing

Do not write:

> Count-space classification is wrong.

Write:

> We quantify how the detector and analysis definition transform intrinsic duration–hardness observables into catalog quantities.

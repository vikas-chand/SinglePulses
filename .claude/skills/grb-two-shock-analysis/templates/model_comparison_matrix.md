# Model comparison matrix

Use the same data, responses, background, and time bins for every model.

| Model | Parameters | Count-space fit | Predictive check | Evidence/IC | Temporal fit | Physical constraints | Main residual | Interpretation |
|---|---:|---|---|---|---|---|---|---|
| CPL | | | | | N/A | empirical | | |
| Band | | | | | limited | empirical | | |
| SBPL | | | | | limited | empirical | | |
| 2SBPL | | | | | limited | empirical | | |
| Band+BB | | | | | component timing test | thermal + empirical | | |
| SBPL+BB | | | | | component timing test | thermal + empirical | | |
| Single-zone synchrotron | | | | | linked track if modeled | microphysical | | |
| Coupled FS+RS analytic | | | | | full target | Eq. 7 + EATS | | |
| Coupled FS+RS full kernel | | | | | full target | hydrodynamic + microphysical | | |
| Photosphere + FS+RS | | | | | full target | hybrid | | |
| Magnetic/reconnection model | | | | | intensity tracking | alternative physics | | |

## Decision rules

1. A lower scalar fit statistic alone is not sufficient.
2. Inspect posterior predictive residuals in detector count space.
3. Penalize unconstrained extra components.
4. Verify parameter recovery with simulations.
5. Require physical ordering and coupling for the two-shock interpretation.
6. Compare temporal predictions, not only spectra.
7. Report non-identifiable cases explicitly.

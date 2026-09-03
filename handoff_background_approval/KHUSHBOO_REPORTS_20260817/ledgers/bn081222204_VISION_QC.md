# VISION_QC — bn081222204 (GRB 081222, z=2.77) — burst #2 gate ledger
Opened 2026-08-15 under the burst-1 frozen discipline (standing contracts in
dev/ai_guides/FigureVisionQC.md; architecture in AgentArchitecture.md).

## Step-7 measurement record — 2026-08-15 (fresh runs, all estimator-labeled)
- T90 = 11.33 ± 0.32 s (windowed; TAIL_OUTSIDE_WINDOW 2.37σ < 3 → window captures
  the burst; NOT a lower limit — contrast with burst #1). T50 = 4.14 s (no error —
  known engine defect). Gowri phi = 0.263 (FRED-like).
- MVT: Bala CANONICAL 40.3±2.4 ms @ z=3.7 (delt 4 s; 35.8±2.3 @ 3.4σ delt 3 s) —
  DETECTION, supersedes the in-chain Haar UPPER LIMIT (<1.02 s). CWT (extension)
  215±17 ms — IDENTICAL rung to burst #1: NEW ESTIMATOR PROPERTY recorded: CWT MVT
  is GRID-QUANTIZED at fixed dt/dj (rung spacing ~9%); its "error" is grid, not
  statistics; cross-burst CWT values cluster on rungs. Caveat rides every CWT quote.
- Lag (s02c engine, PULSE-SCALED windows — auto search 3.8 s / fit 1.9 s, first
  use of the burst-1 lesson as default): tau = +0.465 −0.261/+0.191 s @ 30.1σ
  (soft lags hard). Handbook row −0.195 (inverted convention; quarantined).
  tau/T90 = 0.041 vs burst #1's 0.083 — first two rows of the lag–width
  accumulator DIFFER by 2× (not a constant ratio: real accumulator content).
- Rest frame (z=2.77): T90_rest = 3.01 s; MVT_rest ≈ 10.7 ms; lag_rest ≈ 0.123 s.
Figures rendered (44 + 47b + 47c), NOT yet gated — gates run before any
presentation to the PI, per the no-exception rule.

## Engine finding — 2026-08-15 — family-merge order fragility (NR-8)
scripts/10's per-family save dropped previously merged families: after
default(218c) → shape(300c) → highe(976c, all 24), the threecomp save wrote
742c/18 models, losing BANDCUT, BANDRCPL, DSBPL(!), DSBPLF, SBPLCUT, SBPLF —
including a DEFAULT-family model. Burst-1's 24-model table survived by run
order alone. Repair: missing families refit to scratch + explicit astropy
column merge into the main table; post-merge census asserts 24. Freeze
consequence: refit = one-process workflow + model-count fail-loud assert.

## Engine-display finding — 2026-08-16 — reference-detector drift (Codex #2 MATERIALIZED)
First burst-2 sweep: 16/168 — SYSTEMATIC guard refusals |dAIC| 0.1–0.5 on every
model incl. plain CPL (once live BETTER than stored). Root cause: 41c recomputed
ref by min angle (n1) while the ENGINE'S stored reference is n0 — with 3 NaIs the
fixed-EAC detector differs → different likelihood parameterization everywhere.
This was Codex independent finding #2 (2026-08-14), queued not fixed — the queue
debt came due on the first multi-NaI burst. FIX: 41c now reads reference_det +
fit_dets from the engine's spectral_fits.json (fallback min-angle only if absent).
Register: the queued item graduates to DEPLOYED. Sweep relaunched full (the 16
"OK" panels were wrong-parameterization too — nothing kept).

## Notes-layer verdicts + F1/F2 resolution — 2026-08-16
NOTES (7 reviewers + synthesis, 0 errors): bin4 CPL+BB = LIKELIHOOD-THIN — no
40–100 keV residual mode, dPGstat lives in continuum re-shape (XC unconstrained),
no kT continuity in neighbours → TRACK AS CANDIDATE, DO NOT SHIP. All headline
BBs pass L28 (rejections rest on residuals, not the edge — the gate works both
ways). AIC-vs-eyes agree 7/7 (bin4 read as tie). b0 EAC railed in ALL fits
(0.800; bin5 1.200) → accumulator row 2 of the EAC rail census.
F2 RESOLVED (cross-era mixing, MY violation): sweep-1 wrong-ref panels for
sweep-2-refused pairs lingered (purge matcher + 41e matcher both blind to
NAME≠PREFIX canon: DSBPLfree/SBPLfree/BandxCut/SBPLxCut). Fixed: alias map in
purge+41e; 3 stale files removed; montages rebuilt; n_missing == refusals in
ALL 7 bins (asserted). NR-10 candidate: name↔prefix must come from ONE
authoritative engine map, never regex guessing.
F1 RESOLVED (EAC fork): table 0.800-railed vs sidecar 0.826 = genuine
likelihood PLATEAU along EAC at |dAIC|=0.084<0.1 (guard passed correctly).
41c now stamps "EAC plateau (live≠stored)" on affected figures. Science reads
ENGINE table values, display discloses.

## NO-MODEL-DROPPED — fully realized on burst #2 (2026-08-16)
PI ruling ("we are not dropping any models") implemented as a three-tier panel
provenance: 129 live-verified + 18 frozen replays (optimizer drift) + 21 frozen
replays (Class-B fit-time crashes routed to replay) = 168/168 panels, ZERO gray
cells, ZERO structural mismatches — every frozen replay reproduced the stored
likelihood exactly, proving the earlier refusals were optimizer/propagation
artifacts, never data differences. Montage n_missing = 0 in all 7 bins.
Register: NR-6 refusal-triage CLOSED (superseded by frozen-replay universality).

## SBPLCPL bin5 — retried per PI instruction, recovered — 2026-08-16
Engine STATUS=FAIL on first pass (transient multistart failure on the faintest
bin). PI: "if it doesn't fit in one bin then try why it is not, and then do
again." Retry converged: AIC 3204.48 (dAIC +7.8 vs CPL winner — present, not
winning). Row merged (43 cells), panel rendered, bin5 montage now a TRUE 24/24.
Retry-once-before-accepting-FAIL is now written into Khushboo's procedure too.

## Correction — Bala canonical for this burst (2026-08-16)
Earlier ledger entry quoted 40.3±2.4 ms — that was the PRODUCER re-choosing a CSV
row (best-SNR delt=4) instead of reading the ENGINE'S OWN selection. Engine
result.json: **30.4±2.1 ms, Δt=2.0 s, status=detection** — the canonical value.
Same lesson class as NR-9 (read the engine's choice, never re-choose); 47b now
reads result.json directly and REFUSES partial estimator sets (no silent skips).
Lag window-scan (PI method): b1 τ=+0.73 stable (win sys ±0.14); b2 peak only
localized to ±0.38 (flat-topped CCF) — systematic now quoted on-figure.

## Component decomposition — 2026-08-16 (Vikas: "plot the model components like XSPEC")
threeML has no native component mode (verified vs installed source); implemented
via astromodels CompositeFunction.functions in 41c — dotted per-component curves,
names in legend, total solid black. Gate PASS 3/3 (afaf0fd7): b2 bin4 CPL+BB (BB
bump at ~65 keV, visibly thin under continuum = the likelihood-thin verdict made
graphic), b1 bin2 Band+BB (BB rising INTO the 8-keV edge, peak outside range =
the L28 artifact made visible), b1 TINT SBPL+PL (PL crossover ~1 MeV = the
evolution artifact's phantom tail). Default for all composite panels from the
next sweep; nit queued: dotted curves graze in-axes note text (readable).

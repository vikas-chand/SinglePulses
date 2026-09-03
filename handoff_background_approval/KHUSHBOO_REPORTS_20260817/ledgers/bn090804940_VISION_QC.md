
## 2026-08-17 — campaign paper round (GRB 090804, burst #7)

**Producer:** Claude. Paper: paper/GRB090804/ (15 pp). Self-check caught the
BB-free margin (1.7→2.3) before the verifier.

**COMBINED VERIFIER (fresh context): FAIL → ALL FIXED:**
(1) best BB-free misnamed CPL→DSBPL; (2) "isothermal/mutually consistent"
overstated — block0 vs block3 kT differ at 3.0σ → reworded to quasi-stable
narrow band (25% spread) in abstract/§5.3/summary, ±1.3→±1.2; (3) lag
plus-error 0.035→0.034 (3 places); (4) lag-fraction comparator list now
includes burst #2's 4.2% and defines the zero-lag distinction (sign-keeping
vs sign-changing scan members); (5) montage_TINT header counter said "0
engine-fail cells" while showing one — ROOT CAUSE: 41c had rendered a
diagnostic panel for the FAIL model, so the counter (keyed on missing
panels) missed it; 41e now counts engine-fails independent of panel
presence; TINT montage re-rendered+restaged. Also applied: Ep wording
(83–85→30), block-4 Band-fit invalidity caveat on the α trend, Wien-peak
claim scoped to BB-winning fits + new sentence on the LRT-flagged cool BBs
in blocks 2/6 (edge-marginal/constrained, recorded not promoted).
Figure sweep otherwise: 3 SEDs PASS (AIC to 0.04); 7 montages PASS;
step9 PASS vs canonical (re-executed); temporal PASS.

**Science row:** first BB-bearing INTEGRATED winner (kT=25.1±1.4, margin
2.3 — strong candidate); quasi-stable kT track (counterpart to #4's
cooling); first zero-consistent lag (sign-changing members); CWT third
rung 181 ms (ladder 181/215/256, ratio 1.19); most compact burst (T90=6.68);
4th consecutive epoch-dependent line-of-death pattern (crossing at the very
end). Burst #7 CLOSED pending PI.

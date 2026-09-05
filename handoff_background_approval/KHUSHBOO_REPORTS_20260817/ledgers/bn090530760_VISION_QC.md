
## 2026-08-17 — campaign paper round (GRB 090530, burst #4)

**Producer:** Claude (Codex locked out — usage cap until Aug 19). Fits: v2
one-invocation pool (`--models highe`, all 24); canonical table carries
best-of-minima grafts (2 rows improved from legacy invocations). Products:
dev/campaign_products_driver.sh. Paper: paper/GRB090530/ (13 pp).

**NUMBERS-VERIFIER (fresh context): PASS-WITH-CORRECTIONS — 5 confirmed +
2 suspicions, ALL APPLIED:** window systematic 0.47→0.48 (truncation not
rounding, 4 places); summary Haar direction flipped to upper limit; bin-5
rail specifics corrected (DSBPL α1@2.5, DSBPLF α2@0.5, BANDBB α@1.9); EAC
claim descoped (n2 rails only in TINT+late bins, 1.12–1.19 elsewhere);
bin-4 "preferred outright" softened to narrow (CPL+BB ΔAIC 0.8, top-3
competitors all BB-bearing); bin-0 comparator validity disclosed (best
VALID BB-free trails by 4.4); unsourced T50/T90~0.3 benchmark dropped.

**FIGURE-VERIFIER (fresh context): FAIL → one BLOCKING defect FIXED:**
step9_qc was built from the STALE sweep106 fit table (bn200524211
label–primitive class) — its bars contradicted the package's own SEDs
(block 0 negative-evidence/SBPL vs canonical CPL+BB +4.42; block 4 +5.82
vs canonical +7.91 across the STRONG line). Root cause: driver called
scripts/44 with default --out. Fix: dev/rebuild_step9_canonical.py (temp
root symlinked to the canonical table; scripts/44 unmodified) + driver step
t44b so every future burst builds step9 from canonical. Re-gate pending
(fresh agent). AIC stamps on TINT/bin0/bin4 SEDs verified = stored to 0.1.
Montage sweep: 7×24 panels, one winner each, zero refusals — PASS.
Adjudicated (disclosed, not redrawn): bin5 montage marks the raw-AIC winner
DSBPL [INVALID] while the validity-filtered best is CPL+BB — the paper text
carries the disclosure; display-policy question queued for the PI.

**COSMETIC QUEUE (engine-class, not per-burst):** band-note text struck by
error bars on 3 SEDs (needs opaque bbox); CWT NaN legend should read "no
measurement"; step7_temporal relation-point color collides with excluded-band
color; step1 label under legend; lag-note handbook err 0.045 vs catalog
0.0509 (same-run sidecar check). Filed to the register, fix in scripts once.

**RE-GATE (fresh context): PASS.** Rebuilt step9 verified 6/6 blocks exact vs
canonical (+4.42/−2.00/−2.00/−1.35/+7.91/+0.98; BEST CPLBB/Band/SBPL/SBPL/
DSBPL/CPLBB); BB-edge panel exact incl. correct block-5 absence; render clean.
Re-gate also surfaced the LRT-view cooling track (BB significant blocks 0–4,
kT 22.4→5.8 keV monotonic) — added to §5.4 with both metrics distinguished.
GRB090530 package: GATED, paper final (13 pp). Burst #4 CLOSED pending PI.

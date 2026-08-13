# bn200524211 / GRB 200524A — inter-operator verification record (2026-08-12)

**Mode:** REPRODUCTION (P3-class, not blind — R0 targets frozen with disclosure in
`bn200524211_R0_targets.json`). Khushboo's walkthrough (her machine, branch
`khushboo-walkthrough-200524A`) independently re-executed end-to-end on this machine:
Steps 0/0b/1 (doc agent) · 2–4 (adopted stamps; b0 overrun = adjudicated decision) ·
5/6 (27b + full 24-model fit; frame matched: n0,n1,n3,b0, no LLE) · 7 (production
`survey_one` driver: T90 = 25.0 s, Kocevski pulse, lag accepted) · 8 (νFν montage) ·
9 (this record; Amati provisional below).

## The five-frame T_INT diff (σ-distance of OUR fit: α / Ep / β)

| frame | α | Ep | β | note |
|---|---|---|---|---|
| **Khushboo (same data, her run)** | **0.51** | **0.57** | **0.24** | the inter-operator datum |
| GBM GCN 27809 | 1.16 | 1.84 | 1.30 | preliminary GCN frame |
| Konus GCN 27867 | 0.04 | 0.90 | 1.08 | different instrument, consensus-friendly |
| Ghosh+2026 (−1,40) s RMFIT | 1.84 | 3.20 | 3.18 | MISMATCHED interval (T9) — includes ~14 s of soft tail beyond our window; not an alarm |
| Ghosh+2026 (−1,15) s RMFIT | 0.84 | 1.50 | 1.72 | closest-window Ghosh frame |

Ours: α = −0.755±0.056, Ep = 252.4±28.6 keV, β = −1.893±0.090 (Band, VALID);
winner SBPL by ΔAIC 0.37 over Band = **statistical TIE** (Khushboo: SBPL by 2.4 — same
verdict class; her phrasing "mildly prefer SBPL, equally well described by Band" adopted).

**Pattern check:** σ-distance ranks exactly by frame proximity (same-data < same-window
< mismatched-window) — the T9/L21 doctrine reproduced in the wild.

## Scorecard (v2 union rule, 11 resolved blocks)
DECISIVE 0 · STRONG 0 · significant BB 0 (no daggers) — a clean null; consistent with
Khushboo (no thermal claims) and Ghosh+2026 (Band/CPL only).

## Amati placement (PROVISIONAL — skill hand-run)
z = 1.256 (Gemini-N MgII; "in practice only a lower limit" — verbatim caveat carried).
Ep,i = 252.4×2.256 = **569 ± 65 keV** (ours). Eiso: our table carries no flux columns yet
(engine gap logged with the hardening batch), so Eiso defers to Ghosh+2026's value —
itself internally contradictory (1.80 vs 3.04 ×10⁵³ erg, their T5). At Eiso ≈ 2×10⁵³ the
burst sits **within the Amati band** (no outlier flag). PROPER placement (our own
model-integrated k-corrected fluence + Yonetoku) awaits the products-batch script.

## Verdicts
1. **Inter-operator reproduction: PASS at <0.6σ on every parameter** — two operators,
   two machines, one Skill Library. First same-burst two-operator datum for §5.
2. Ghosh+2026's detector set = ours exactly (independent Stage-1 decision agreement).
3. Winner-identity across all frames: one-break family, tie between Band/SBPL — the
   graded-evidence doctrine's language required in every quote of this result.
4. F-4 note: both runs inherit 27b's silent window tightening — the loudness fix
   remains pending; it does not affect the inter-operator comparison (same code path).

# Adjudication — Codex gpt-5.6-sol ultra audit of the b11–b20 night shift + L28 (2026-08-11)

Report: `CODEX_AUDIT_REPORT_2026-08-11_night_L28.txt` (350k tokens, read-only, blind Task-1
re-derivation honored). Every accepted finding below was **verified at the primitive** before
action (spot-checks: b19 blk0–3 CPL+BB LRT/kT/VALID, b16 blk11 BANDBB_VALID=False, b13 blk1
kT=40.2 VALID — all reproduce).

## Accepted + ACTED ON (same session)
| finding | action |
|---|---|
| MF-1 BB census omitted CPL+BB nested test (31 → 55 blocks; 52 with child-VALID) | scorecards + `walkthrough_night_summary_v2.json` regenerated with the UNION rule, model labels (B/C), child-VALID gate, invalid-child daggers, L28 edge class per kT, schema v2 (also closes SC-5) |
| MF-3/Task-4 b12 = per-bin response-coverage batching bug (block 0 starts −0.804 s; first DRM +0.064 s; one uncovered bin nuked all 8) | engine: per-bin `to_spectrumlike` fallback in scripts/10 (uncovered bin → RESPONSE_UNCOVERED, covered bins survive; collapse fallback stays dead); b12 refit queued behind the b21–30 sweep |
| MF-4 L28 misstated methods | lesson rewritten: exact LET set {15,20,25,30,50,100}, summed-residual-averaged-across-detectors statistic, "almost no overlap", coherent-run reading + 20→BB transfer + 30 keV boundary + RJ tension labeled PROJECT extensions/policy |
| MF-5 kT rail geometry doc contradiction | code comment + L27 lesson corrected: kT (1,200) IS log-ruled, rail zone < 1.0544 keV |
| SC-6 record-policy contradiction | standardized everywhere: retained in records, excluded from population/promotion until checks pass |
| SC-7 classifier dual-input + boundary tests | `edge_feature_class` now raises on kt AND xb; exact-boundary tests added (20 → MARGINAL, 30 → IN_BAND); suite 33 pass + 1 known xfail |
| NOTE-2 3.92 factor provenance | labeled analytic (x = 3.9207), not a paper quotation |
| NOTE-3 Tierney PDF is arXiv v1, not VoR | lesson anchor line corrected; VoR fetch blocked by A&A DataDome — browser-fetch offered to Vikas |

## Independent convergence (Wang+2019 reading package, same day)
Vikas's ChatGPT deep-read of Wang+2019 — PDF-verified before merge — independently surfaced
the SAME two methodological pressure points the audit found:
1. **Baseline dependence of the BB verdict** (their App. C: Band-vs-Band+BB ΔAIC = 10.0 but
   CPL-vs-CPL+BB = 20.3, same interval) = the published twin of MUST-FIX-1 (our Band-only
   bookkeeping). The union rule is the fix on our side; T8 in LiteratureHarvest.md records
   the harvest-side rule (named baselines, never "the" ΔAIC).
2. **Wilks fails at the boundary**: BB norm = 0 is a parameter-space boundary with kT
   unidentified under the null → the χ² calibration behind any bare "LRT ≥ 9.2" is suspect;
   simulation calibration (parametric bootstrap / SBC) is the defensible route. This joins
   SC-1 (the 20/30 keV boundary calibration) as ONE simulation program — and it now has a
   literature anchor (their §App C + Tierney's bootstrap machinery).
Also logged: engine GAP — we do not emit thermal fraction F_BB/F_tot with uncertainty
(Wang report it per bin: 7.3 +5.8/−3.7 %, 3.6 +3.3/−1.6 %); required for #43 Tier A and for
any P3 diff against photosphere papers. Slot with MF-2 (edge-class serialization) in the
hardening batch.

## Accepted, PENDING (needs Vikas or scheduled work)
- MF-2: serialize edge class into fit tables + enforce quarantine in population scripts (engine change beyond comment-level; slot with the L8/L9/L6 hardening batch before the census re-run).
- SC-1: 30 keV boundary + 20-keV→BB transfer need model-specific simulation calibration (project #34-adjacent task).
- SC-2: P0 provenance — adopt commit-before-fit append-only P0 manifest with hashes (b21–30 P0s are on disk pre-table-open; commit proposal at the next gate).
- SC-3: four night P0 denominators counted T_INT as a block — frozen files stay untouched (they're frozen); correction noted for gate presentations.
- SC-8: step-1 response preflight now runs in the sweep doc layer (10/10 PASS for b21–30) — wire as a hard pre-fit gate in the chain runner for future sweeps.

## Rejected / no action
- None. (NOTE-4 confirmed the KeyError is a benign threeML fallback — action was "don't fix the wrong thing", honored.)

## Narrative corrections owed at the gates (from the corrected census)
- b13, b14 are NOT fully clean nulls: each carries one VALID CPL+BB block (kT 40.2, 30.4 — IN_BAND class). AIC-margin verdicts (0 DEC / 0 STR) are UNCHANGED — the nested-LRT census and the AIC-margin verdict are different statements and must be reported as such.
- b19 bn160330827: 4/4 blocks VALID CPL+BB, kT cooling 17.7 → 10.2 keV (turnovers 40–69 keV, IN_BAND) — the "small clean null" description is withdrawn.
- b16 cooling-endpoint kT = 3.0 keV rests on an INVALID child fit (dagger); the b16 track must be re-read from the union list at its gate.
- The "4-for-4 archival BB-leader predictions confirmed" claim: archival census and night fits share the engine — consistency, not independent confirmation (already noted at wake-up, stands).

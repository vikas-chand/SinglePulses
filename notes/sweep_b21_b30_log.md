# Sweep b21–b30 — full end-to-end run (launched 2026-08-11, Vikas: "skip nothing, document all")

**Queue rule:** remaining pre-2020 bursts (Khushboo owns post-2020), newest-first, from the
approved 106-burst catalog (`results/background_intervals.ecsv`, all stamped).

| tally | trigger | dets (approved) | census prior | temporal roster | notes |
|---|---|---|---|---|---|
| 21 | bn191129141 | n8,nb,b1 | Y | Y | |
| 22 | bn191125206 | n1,n3,n4,n5,b0 | Y | Y | |
| 23 | bn191017391 | n2,n5,b0 | Y | Y | |
| 24 | bn190726642 | n9,na,nb,b1 | Y | Y | |
| 25 | bn190401139 | n6,n7,n8,b1 | **N** | **N** | outside the 89-burst human set; literature-only P0; temporal gap FLAGGED (roster-based survey won't cover it) |
| 26 | bn190222537 | n8,nb,b1 | Y | Y | |
| 27 | bn181212693 | n2,n5,b0 | Y | Y | |
| 28 | bn180724807 | na,nb,b1 | Y | Y | |
| 29 | bn180720213 | n3,n4,n5,b0 | Y | Y | |
| 30 | bn180703876 | n6,n7,n8,b1,**lle** | Y | Y | LLE approved — engine auto-includes LLE (no --skip-lle); D1 Δθ check REQUIRED in step-1 QC |

**Steps per burst (the full ledger, nothing skipped):**
- 0/0b (dossier, literature harvest, **P0 freeze**) + 1 (inventory/response QC) → parallel
  agent layer, products: `results/gcn/<trig>_dossier.md`,
  `notes/reconciliation/<trig>_P0_frozen.json`, `notes/reconciliation/<trig>_harvest.json`,
  `results/qc/<trig>_step1_response_coverage.ecsv`
- 2–4 → ADOPT (all selections stamped in the approved catalog; APPROVAL_MODE recorded)
- 5 → `27b_reblock_3ml.py` → `results/walkthrough_b<i>/blocks/`
- 6 → `10_spectral_fit_burst.py --include-bgo --models highe` → `results/walkthrough_b<i>/<trig>/spectral_fits.ecsv`
- 7 → `40_temporal_survey.py` (roster sweep, run once at chain end; covers 9/10 — b25 gap flagged)
- 8 → `41_nuFnu_panels.py --mode best` → `results/walkthrough_b<i>/<trig>_nuFnu_best_montage.png`
- 9 + scorecards + records → AT THE GATE, after P0 verification (blind-first: no fit table
  is opened before its P0 exists; scorecard generation is not part of the automated chain)

**Doctrine active:** L18/L19/L20/L26/L27/**L28** engine; data-dropping hierarchy; blind-first
ordering; prompt-only analysis scope with free literature (harvest agents catalog
beyond-prompt papers under `module-future` tags).

**Concurrent audits:** Codex gpt-5.6-sol ultra audit of the b11–b20 night shift + L28 running
in parallel (`dev/audits/CODEX_AUDIT_2026-08-11_night_L28.md`).

---
## Chain log (appended by the runner)

### [21] bn191129141 — started 2026-08-11T16:33:25Z
- step5 (27b) exit 0 — 2026-08-11T16:33:38Z

---
## Documentation layer (Steps 0/0b/1) — COMPLETE 2026-08-11 (10/10 agents)
All ten bursts: dossier (results/gcn/<trig>/), harvest manifest + P0 frozen
(notes/reconciliation/), step-1 response QC (results/qc/) — **10/10 QC PASS**.
Corpus merged: +11 papers filed; gcn_index +10 rows. Highlights:
- **SIX PAPERLESS BURSTS** (b21,b23,b24,b26*,b28,b29) — our fits will be the first
  published time-resolved spectroscopy for most of these (*b26: one unrefereed arXiv
  temporal-only eprint; naming-collision trap documented, identity fixed by trigger time).
- **b22 bn191125206 = incoming LOW-kT burst**: archival prior 8/13 blocks sig-BB,
  kT median 4.33 keV (L28 edge-constrained class) + 3 DSBPL-decisive blocks.
- **b23 bn191017391**: flight software misclassified it as a particle event (GCN 26020) —
  top-quartile fluence yet zero literature; likely why it's paperless.
- **b30 bn180703876**: richest literature (8 papers incl. Ahlgren+2020 BB physics,
  Macera+2025 GBM+LAT synchrotron, 2 lag-transition papers); LLE arm engages.
- **b29 bn180720213**: ALL THREE ADS hits for "GRB 180720A" are misnamed 180720B papers —
  standing contamination hazard recorded; Wang 2019 must NOT gain this burst's tag.
- P0s frozen for all ten BEFORE any new fit table exists to open (audit SHOULD-2
  provenance upgrade: commit-before-fit proposed to Vikas at the gate).
- step6 (fit) exit 0 — 2026-08-11T16:53:49Z
- step8 (panels) exit 0 — 2026-08-11T16:55:44Z

### [22] bn191125206 — started 2026-08-11T16:55:44Z
- step5 (27b) exit 0 — 2026-08-11T16:56:26Z
- step6 (fit) exit 0 — 2026-08-11T17:56:22Z
- step8 (panels) exit 0 — 2026-08-11T18:01:51Z

### [23] bn191017391 — started 2026-08-11T18:01:51Z
- step5 (27b) exit 0 — 2026-08-11T18:02:04Z
- step6 (fit) exit 0 — 2026-08-11T18:10:18Z
- step8 (panels) exit 0 — 2026-08-11T18:11:09Z

### [24] bn190726642 — started 2026-08-11T18:11:09Z
- step5 (27b) exit 0 — 2026-08-11T18:11:23Z
- step6 (fit) exit 0 — 2026-08-11T18:32:33Z
- step8 (panels) exit 0 — 2026-08-11T18:35:04Z

### [25] bn190401139 — started 2026-08-11T18:35:04Z
- step5 (27b) exit 0 — 2026-08-11T18:35:21Z
- step6 (fit) exit 0 — 2026-08-11T19:25:40Z
- step8 (panels) exit 0 — 2026-08-11T19:28:53Z

### [26] bn190222537 — started 2026-08-11T19:28:53Z
- step5 (27b) exit 0 — 2026-08-11T19:29:05Z
- step6 (fit) exit 0 — 2026-08-11T19:37:34Z
- step8 (panels) exit 0 — 2026-08-11T19:38:42Z

### [27] bn181212693 — started 2026-08-11T19:38:42Z
- step5 (27b) exit 0 — 2026-08-11T19:38:56Z
- step6 (fit) exit 0 — 2026-08-11T20:14:11Z
- step8 (panels) exit 0 — 2026-08-11T20:17:40Z

### [28] bn180724807 — started 2026-08-11T20:17:40Z
- step5 (27b) exit 0 — 2026-08-11T20:18:07Z
- step6 (fit) exit 0 — 2026-08-11T20:36:39Z
- step8 (panels) exit 0 — 2026-08-11T20:38:35Z

### [29] bn180720213 — started 2026-08-11T20:38:35Z
- step5 (27b) exit 0 — 2026-08-11T20:38:48Z
- step6 (fit) exit 0 — 2026-08-11T21:09:48Z
- step8 (panels) exit 0 — 2026-08-11T21:13:20Z

### [30] bn180703876 — started 2026-08-11T21:13:20Z
- step5 (27b) exit 0 — 2026-08-11T21:13:32Z
- step6 (fit) exit 0 — 2026-08-11T21:45:35Z
- step8 (panels) exit 0 — 2026-08-11T21:48:23Z

### step7 temporal survey (roster sweep) — 2026-08-11T21:48:23Z
- step7 (40 temporal) exit 0 — 2026-08-11T21:49:57Z; b25 bn190401139 NOT in roster (gap flagged)
=== SWEEP b21-b30 COMPLETE 2026-08-11T21:49:57Z ===

# AI Guide: Detector selection

> Part of the benchmark framework (dev/BENCHMARK_PLAN.md). Complements the decision.json schema in scripts/39_approve_all.py by giving the JUDGEMENT CRITERIA.

**Purpose** — For one GRB, decide WHICH Fermi/GBM detectors (NaI n0–nb, BGO b0/b1) enter the analysis. Good geometry + a real signal in the light curve qualify a detector; off-axis or featureless ones are dropped. This is the first genuine visual judgement in Stage 1 of the authoritative pipeline.

**When to use** — After `python scripts/39_approve_all.py render --trigger <bn...>` has written `results/approval/<trigger>_pending.json` and the per-detector LC PNGs. You (Codex/Claude, vision-capable) are now the `mode: "ai_vision"` approver.

**Which decision.json field this fills** — the top-level `"detectors"` array (the approved SET, NaI + matching BGO[+lle]). Optionally the `"angles"` map. (Background `windows` and `source` are SEPARATE guides — do not decide them here, but note: ingest in scripts/39 will reject a detector that has no `windows` entry, so only approve detectors you will also window.)

## Inputs (what to read)
- `results/approval/<trigger>_pending.json` — the candidate manifest. Per-detector entries carry `detector`, `angle_deg` (separation to source, deg; may be `null` if POSHIST failed), `in_bcat` (did this NaI trigger in the GBM burst catalog), `suggested_bkg`. Top-level `pre_ticked` = the code's auto-tick set, `src_ra`/`src_dec` = source position.
- `plots/approval_lc/<trigger>_<det>.png` — one 1.024-s light curve PER candidate detector. NaI band 8–900 keV, BGO 250–40000 keV, linear y, NO T90 shading (identify the burst from the data alone). READ EVERY PNG with the Read tool — this is a vision task; do not decide on angles alone.
- Optional cross-check: `results/grb_sample.ecsv` (`RA`, `DEC`, `NAI_DETECTORS` = BCAT mask, `T90`).

## Decision criteria (the heart)
Render pre-ticks `pre_ticked` using these exact rules (scripts/39 `compute_candidates`, constants in scripts/00 `ANGLE_THRESHOLD_DEG=50`, `ANGLE_RESCUE_DEG=60`). Treat them as the PRIOR; confirm or override each against the PNG.

NaI angle/BCAT logic (mirror of BACKGROUND_SELECTION_PROCESS.md Step 1 table):
- NaI θ ≤ 50° → KEEP (Goldstein+ 2012 conservative on-axis cut).
- NaI 50° < θ ≤ 60° AND in BCAT mask → KEEP (rescue: it triggered, borderline geometry).
- NaI 50° < θ ≤ 60° AND not in BCAT → DROP.
- NaI θ > 60° → DROP regardless of BCAT.
- Fallback when nothing qualifies: keep the SINGLE closest BCAT NaI.

BGO companion rule (pick the same-side BGO of the kept NaIs):
- Any kept NaI in {n0,n1,n2,n3,n4,n5} (low side) → add `b0`.
- Any kept NaI in {n6,n7,n8,n9,na,nb} (high side) → add `b1`.
- Keep a BGO only if it has ≥1 kept same-side NaI. Do not keep both BGOs unless NaIs span both sides.

Visual confirmation in the light curve (this is where your judgement overrides the angle prior):
- KEEP a pre-ticked detector if the PNG shows a clear count-rate EXCESS over baseline at the burst time (a coherent bump/peak, not a single hot bin). The lower the angle, the larger the expected S/N — a low-angle NaI with a flat, featureless LC is suspicious (wrong source position, occulted, or a data gap).
- DROP / UNTICK a pre-ticked NaI if its LC is flat at the burst time despite good geometry, OR shows only an isolated 1-bin spike (instrumental), OR is dominated by a step/orbital trend that buries any signal.
- ADD an un-pre-ticked detector ONLY if its PNG shows an UNAMBIGUOUS burst excess AND its angle is plausible (≤ ~60°). A clear detection at 55°, BCAT-listed, is a legitimate add.
- BGO: keep only if the matching NaI(s) are kept; a BGO PNG need not show a strong excess for soft bursts (BGO sees 250 keV+), so judge BGO mainly by the companion rule, not by its own bump.
- Final set should typically be 2–4 NaI + 0–2 BGO. A 1-NaI burst is allowed (faint/edge); flag low confidence in `reasoning`.

## Output contract (write into `results/approval/<trigger>_decision.json`)
Only the `detectors` field is THIS task; include the full schema so scripts/39 ingest accepts it (windows/source come from the other guides):
```json
{
  "trigger": "<trigger>",
  "approver": "Claude (AI)",
  "mode": "ai_vision",
  "detectors": ["n6", "n7", "b1"],
  "source": {"t1": <float>, "t2": <float>},
  "windows": { "n6": {"pre": [t1,t2], "post": [t3,t4], "window_source": "adjusted"}, "...": {} },
  "angles": {"n6": 12.3, "n7": 18.0, "b1": 30.1},
  "reasoning": "n6/n7 clear excess θ<25°; n9 untick (flat LC at 48°); b1 high-side companion."
}
```
Rules: `detectors` non-empty; EVERY listed detector MUST also appear in `windows` or ingest rejects the burst. Copy `angle_deg` from `pending.json` into `angles` (else ingest falls back to pending). Use canonical 2-char names (n0–nb, b0, b1).

## QC checklist (before approving)
- [ ] Read the PNG for every detector I list, not just its angle.
- [ ] Every approved NaI has a VISIBLE burst excess (or I justified a faint exception in `reasoning`).
- [ ] BGO present ⇒ it has ≥1 kept same-side NaI (b0↔n0–n5, b1↔n6–nb).
- [ ] No detector with θ > 60° kept.
- [ ] Every name in `detectors` also has a `windows` entry.
- [ ] I noted each deliberate override of `pre_ticked` (added or removed) in `reasoning`.

## Common pitfalls (a human reviewer would catch)
- Approving a low-angle NaI purely on geometry when its LC is flat (occultation / wrong RA-DEC) — the human looks at the curve.
- Keeping a BGO with no same-side NaI, or keeping BOTH BGOs for a one-sided burst.
- Mistaking a single hot bin or SAA/orbital step for a burst and adding an off-axis detector.
- Dropping a genuine 52–58° BCAT NaI that clearly detects — the rescue band exists for exactly this.
- Listing a detector in `detectors` but forgetting its `windows` entry (silent burst rejection at ingest).
- Over-trusting `pre_ticked`: it is an angle/BCAT prior, NOT a detection test.

## How this is scored vs humans (BENCHMARK_PLAN.md, task #1)
Compare the AI's approved SET against the human (`mode: human_gui`) approved SET for the same burst:
- **Approved-set Jaccard** = |A∩H| / |A∪H| (primary agreement number; 1.0 = identical sets).
- **Missed detectors** = in human, not AI; **Extra detectors** = in AI, not human (precision/recall view).
- **Angle of disagreements** = the `DET_ANGLE` of every detector in the symmetric difference — establishes whether disputes are borderline (~50–60°, expected) or egregious (a clearly on-axis detector missed). Disagreements clustered near the threshold are tolerable; low-angle misses are not.
- Inter-human scatter (if multiple experts) is the denominator: the AI is "good" if its Jaccard with each human is comparable to human-vs-human. Downstream-impact check then propagates the set difference through Stages 2–3 to confirm Ep/α/kT and the thermal-vs-double-break class survive the human→AI swap.

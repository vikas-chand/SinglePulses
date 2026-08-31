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

> ⚠ **These four rules are UNCHANGED and remain binding — but they do NOT reproduce the PI's
> recorded practice on ~1 burst in 5.** Read the dated **OBSERVED PRACTICE** note at the end of this
> section BEFORE scoring any arm against a human decision (NR-38, 2026-08-31).

BGO companion rule (pick the same-side BGO of the kept NaIs):
- Any kept NaI in {n0,n1,n2,n3,n4,n5} (low side) → add `b0`.
- Any kept NaI in {n6,n7,n8,n9,na,nb} (high side) → add `b1`.
- Keep a BGO only if it has ≥1 kept same-side NaI. Do not keep both BGOs unless NaIs span both sides.
- **The NaI angle cut (≤50° / 50–60° rescue) does NOT apply to BGOs.** A BGO's own `angle_deg` is IRRELEVANT to keeping it — include it iff it has ≥1 kept same-side NaI (companion rule above), even when its angle is >50° (BGOs are wide-FoV; a b1 at 54° stays if a high-side NaI is kept). Never drop a companion BGO on an angle argument. *(Clarified 2026-07-12 after a consensus-pilot disagreement where one pass mis-applied the NaI cut to a BGO.)*

Visual confirmation in the light curve (this is where your judgement overrides the angle prior):
- KEEP a pre-ticked detector if the PNG shows a clear count-rate EXCESS over baseline at the burst time (a coherent bump/peak, not a single hot bin). The lower the angle, the larger the expected S/N — a low-angle NaI with a flat, featureless LC is suspicious (wrong source position, occulted, or a data gap).
- DROP / UNTICK a pre-ticked NaI if its LC is flat at the burst time despite good geometry, OR shows only an isolated 1-bin spike (instrumental), OR is dominated by a step/orbital trend that buries any signal.
- ADD an un-pre-ticked detector ONLY if its PNG shows an UNAMBIGUOUS burst excess AND its angle is plausible (≤ ~60°). A clear detection at 55°, BCAT-listed, is a legitimate add.
- BGO: keep only if the matching NaI(s) are kept; a BGO PNG need not show a strong excess for soft bursts (BGO sees 250 keV+), so judge BGO mainly by the companion rule, not by its own bump.
- Final set should typically be 2–4 NaI + 0–2 BGO. A 1-NaI burst is allowed (faint/edge); flag low confidence in `reasoning`.

### OBSERVED PRACTICE vs THE WRITTEN RULE (dated note, 2026-08-31 — NOT a rule change; NR-38)
*Added at the step-2 gate of the Lane-A walkthrough burst #21, bn110920546. **The decision criteria
above STAND UNAMENDED.** This note records a measured divergence between what this file says and
what the PI actually did, so that no arm is scored against the wrong specification.*

**What happened (the primitive).** The pipeline pre-ticked `{n0,n1,n3,n6,n7,b0,b1}`. Both independent
AI passes — `results/approval/bn110920546_claude.json` and `..._codex.json` — kept **all 7**, each
explicitly citing the ≤50° prior plus a visible excess in n6/n7, i.e. each obeyed this file exactly.
The PI's recorded `human_gui` decision (`results/approval/bn110920546_decision.json`) kept
**`{n0,n1,n3,b0}`**. n6 (25.33°) and n7 (47.68°) both pass ≤50° — n6 is *closer* than the kept n3
(28.85°) — but neither is in the BCAT mask (`_pending.json` `in_bcat=false`).

**The PI's reason, given at the gate on 2026-08-31, VERBATIM:**
> "I must have selected the ones those are on same side and probaly the triggered ones too"

**SECOND STATEMENT — the PI's RULE, given at the same gate after seeing the census, VERBATIM:**
> "it's that when we have plenty of them then we check which one are triggered otherwise when we
> have scarcity we try to get atleast 1"

This is a *rule statement*, not a recollection about one burst — and it was TESTED against all 105
`human_gui` decisions the same day (read-only census; the decision criteria above still stand
unamended, because the test does not support promoting either branch to a deterministic rule):

| situation | bursts | outcome |
|---|---|---|
| **scarcity** — ≤1 triggered NaI available | 8 | **every one ended with ≥1 NaI kept** (the PI's branch, confirmed exactly); 7/8 kept precisely the triggered one, 1 reached beyond BCAT to get enough |
| **plenty** — ≥2 triggered NaI available | 97 | kept exactly the triggered set in 75 (77%) |

Reproduction of the PI's 105 recorded decisions, by candidate rule:

| candidate rule | reproduces |
|---|---|
| this file's written rule (geometry ≤50° → KEEP) | **50/105 = 48%** |
| "keep the triggered (BCAT) NaIs" | 82/105 = 78% |
| the PI's conditional (plenty → triggered; scarcity → ≥1) | 83/105 = 79% |
| "triggered, on the side of the closest triggered detector" | **84/105 = 80%** |

**The ceiling is ~80%, and that is the real result.** No deterministic rule reproduces the expert
beyond it: the residual ~20% is the per-burst LIGHT-CURVE JUDGEMENT this file already mandates
("READ EVERY PNG … this is a vision task; do not decide on angles alone"; "DROP/UNTICK a pre-ticked
NaI if its LC is flat at the burst time"). Kept sets are side-coherent in 95/105; where the triggered
set spans both sides (17 bursts) the PI kept a single side in 9.

**Therefore the defect is narrower than "the rule is wrong".** The rule's *vision step* is right; its
**PRE-TICK PRIOR** is what misleads — `compute_candidates` pre-ticks on geometry alone, so both AI
arms started from a 48%-accurate prior and kept 7 detectors here. Correcting the pre-tick to
*triggered, same side* would move the arms from 48% to ~80% agreement with the expert **before** any
vision step runs, changing no recorded decision. **PROPOSED, NOT APPLIED** — the pre-tick lives in
`scripts/39_approve_all.py::compute_candidates` (constants in `scripts/00`), it is inside the
benchmark's frozen approval instrument (`dev/GUI_REQUIREMENTS.md` §0), and changing it is the PI's
call (AgentRoster decision-sheet item 25).

**Status of that reason: RECOLLECTION, NOT RECORD.** It was stated with uncertainty ("must have",
"probaly") six weeks after the 2026-07-19 decision, because the decision carried no `reasoning` field
(see the QC item below and `dev/GUI_REQUIREMENTS.md` R-GL-8 / NR-39). It must never be quoted as a
contemporaneous record. The session did VERIFY both halves against the primitives, and both hold
exactly: kept NaI `{n0,n1,n3}` **==** the BCAT-triggered NaI set; all kept NaIs are low-side (n0–n5),
so the BGO companion rule takes `b0` and drops `b1`. The amended record lives in that burst's
`decision.json` under `reasoning` + `reasoning_provenance`, marked RETROACTIVE.

**Campaign-scale measurement (read-only census, 2026-08-31, over the 105 `human_gui` bursts having
both a `_pending.json` and a `_decision.json`):**

| candidate rule | reproduces the PI's kept-NaI set |
|---|---|
| kept NaI set == BCAT-triggered NaI set | **82/105 (78%)** |
| kept NaI set == geometry(θ ≤ 50°) set (the rule written above) | **50/105 (48%)** |
| bursts where a NaI passing θ ≤ 50° was DROPPED by the human | **19/105** |

Examples of the 19: bn081224887 dropped n0,n1; bn100130729 dropped n6; bn110920546 dropped n6,n7;
bn110928180 dropped n6; bn120130938 dropped n9,na; bn120624933 dropped na; bn130215063 dropped na;
bn130427324 dropped n0 (+11 more).

**NEITHER rule is 100%.** "Keep the triggered (BCAT) NaIs" is the better description of the expert's
practice, but it is a *description*, not a law, and it is wrong 22% of the time. Do not present either
as THE rule; do not silently switch to the BCAT rule in any arm.

**Why this matters beyond one burst.** Part 1 of this project is an AI-vs-human benchmark
(`PROJECT.md`). An arm that faithfully follows a written rule which does not describe the expert's
practice gets scored as **AI error** when the defect is in the **SPECIFICATION** — a benchmark
confound. And because the Stage-1 detector set fixes every downstream signal-to-noise, block
significance and bin-adequacy number, the arms differ systematically on ~1 burst in 5. Scoring rule
that follows (see "How this is scored vs humans" below): an arm is scored against the rule the expert
actually used, and any set difference traceable to this divergence is reported as a SPEC defect, not
as an arm error.

**OPEN QUESTION FOR THE PI — the rule is NOT amended until he rules:**
> Should BCAT membership gate NaI selection **below** 50° too (i.e. "keep a NaI iff θ ≤ 50° **AND** it
> is in the BCAT mask", with the 50–60° rescue unchanged)? Or is the ≤50° geometry rule correct as
> written and the 19 drops are per-burst visual judgements (flat LC, occultation, side-consistency)
> that simply were never written down?

Until that ruling: **the four criteria above are what every arm executes**, and the divergence is
PRESENTED at the gate (BurstWalkthrough.md ADOPT-1), never normalized away.

*Process note:* this case is the founding instance of the DIVERGENCE LEARNER protocol
(`FreshSessionBoot.md` §10, register row NR-37) — detect → elicit → validate → generalize → ledger.
Its GENERALIZE step came back **inconclusive** (78% is neither a one-off preference nor a rule that
holds), which is why this note exists instead of a new decision rule. Ledger row: the presenting
session's, in `results/campaign/divergence_ledger.md`.

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
- [ ] **`reasoning` is present and NON-EMPTY in the written `decision.json` — REQUIRED, not optional.**
      The output contract above has always listed it, but `scripts/39_approve_all.py:52` calls it
      "optional free text" and the human GUI path (`scripts/39_approve_all.py:817-819`) writes no
      such key at all: as measured 2026-08-31, **1 of 105** `human_gui` decisions carries a reason,
      and that one was back-filled retroactively. A decision that overrides the pre-ticks with no
      recorded reason is unauditable — that is exactly how the divergence above survived 6 weeks
      (NR-39; spec home `dev/GUI_REQUIREMENTS.md` R-GL-8).

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
- **SPEC-DEFECT SCREEN before any arm is scored (2026-08-31, NR-38).** For every burst in the symmetric
  difference, check whether the disagreement is explained by the spec-vs-practice divergence documented in
  "OBSERVED PRACTICE" above — i.e. the AI kept a NaI with θ ≤ 50° that is NOT in the BCAT mask (19/105 bursts
  campaign-wide). Such a detector is reported as a **SPECIFICATION defect**, not as an AI error: the arm obeyed
  the written rule. An arm is scored against the rule the expert ACTUALLY used; scoring it against a rule the
  expert does not follow measures the document, not the agent. Until the PI rules on the open question above,
  report BOTH numbers (Jaccard vs the human set, and Jaccard restricted to non-divergent bursts) and say which
  is which.

## Display lesson (bn081125496, 2026-08-14 — walkthrough step 1 DISTILL)
- **Any figure showing detector angles must render THE RULE, not a proxy.** The step-1
  panel (`scripts/44`) drew a lone 60° line, which displayed nb (57.0°, BCAT rescue) as an
  unconditional pass and drew the NaI cut across a BGO. Fixed 2026-08-14: both the 50°
  (keep) and 60° (drop) lines are drawn, every NaI bar carries its BCAT status
  ("BCAT" / "BCAT rescue" / "not in BCAT (should be DROPPED)"), and BGO bars are tagged
  "companion rule". BCAT source = `results/grb_sample.ecsv` NAI_DETECTORS (same source
  `scripts/39` stamps into `in_bcat`). Report caption (`scripts/48:119`) fixed to match.
  ⚠ Same misstatement survives in `scripts/37_build_full_notebook.py` prose (lines
  10/44/160) — fix when that template is next touched.

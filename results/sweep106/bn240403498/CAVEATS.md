# CARRIED CAVEATS — bn240403498 / GRB 240403A
Every number this burst produces travels with these. Assembled at step 9.

## C-1 — n0's background window contains a real emission episode (step 3, PI-adopted 2026-09-05)
The burst has three episodes (GCN 36024, confirmed in our own light curve): a precursor
~0–12 s, the main pulse ~22–30 s, and a third weaker bump ~65–80 s. Measured against a
clean 100–175 s baseline, the 55–85 s stretch is a REAL excess in every NaI —
n0 +36.1 cts/s (5.5σ), n1 +81.7 (12.2σ), n2 +54.3 (8.8σ), n5 +71.2 (10.2σ) — and absent
in the BGO (b0 −7.0, −0.9σ), i.e. a soft episode.

**n0's approved post-background window starts at 53.775 s and therefore INCLUDES that
episode**; n1/n2/n5/b0 start at 85.0 s and exclude it. n0 is the CANONICAL detector — the
Bayesian blocks were derived from it.

**Direction of the bias:** n0's post-side polynomial baseline is pulled HIGH → risk of
OVER-subtraction for the canonical detector. Magnitude not quantified (would need the
refit pair).

**PI decision, 2026-09-05:** adopt the stamped windows unchanged and carry this as a flag
("Adopt as stamped, record the flag"). The windows are NOT re-opened; nothing here was
re-decided by the session. Standing ruling applies (background_selection.md, PI
2026-08-31): all background choices are subjective to the user until a physical
background model exists.

Evidence: `results/qc/bn240403498_step3_background_qc.ecsv`,
`results/sweep106/bn240403498/bn240403498_step3_background.png`.

## C-2 — the step-2 detector divergence is OPEN (flag D-2)
n3 (57.94°, in BCAT) is the written 50–60° rescue case; the written rule says KEEP, the
recorded human decision DROPPED it. A reason was elicited from the PI (2026-09-04) and
recorded verbatim; the rule is deliberately NOT amended and the flag is OPEN.
See `results/campaign/divergence_ledger.md` row D-2. This burst proceeds with the
approved selection {n0, n1, n2, n5, b0} per PI instruction.

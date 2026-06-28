# AI Guide: Background window selection

> Part of the benchmark framework (dev/BENCHMARK_PLAN.md). Complements the decision.json schema in scripts/39_approve_all.py by giving the JUDGEMENT CRITERIA.

**Purpose.** For ONE GRB, choose the pre-burst and post-burst time windows, per approved detector, that the polynomial background fit will be anchored on. A good window is a stretch of LIGHT CURVE where only background is present (no burst, no sub-pulse, no orbital trend), so 3ML's polynomial fit (grade 0-4, chosen by Wilks 3σ LRT, then per-channel refit) reconstructs the true baseline under the burst.

**When to use.** After detector selection, after `scripts/39_approve_all.py render` has written `results/approval/<trigger>_pending.json` and the LC PNGs to `plots/approval_lc/<trigger>_<det>.png`. You do this once per approved detector before writing the decision file.

**Which decision.json field this fills.** The `"windows"` map: `windows[det] = {"pre": [t1,t2], "post": [t3,t4], "window_source": "..."}`. (You also set `"detectors"` and `"source"` in the same file, but those are covered by their own guides; here, only `windows`.)

## Inputs (what to read)
- `results/approval/<trigger>_pending.json` — manifest: per-detector `png_path`, `angle_deg`, `in_bcat`, and `suggested_bkg` (a seed `{pre,post}` from scripts/28, may be null), plus a `suggested_source`.
- `plots/approval_lc/<trigger>_<det>.png` — the LC you JUDGE FROM. 1.024-s bins, linear y, counts s⁻¹, x = time since trigger. NaI shows 8-900 keV; BGO shows 250-40000 keV. **No T90 shading is drawn on purpose** — infer the burst region from the data alone; do not anchor on any catalog duration.
- Read EVERY approved detector's PNG. Windows are per-detector (a feature may sit at a different time/height in each), but pre/post edges are usually similar across detectors of the same GRB.

## Decision criteria (the heart)
Read the PNG. The burst is the obvious excess above a roughly flat floor. You are picking baseline ON EITHER SIDE of it.

SELECT a window where ALL of these hold:
- **Flat / very slowly varying** count rate — visually a horizontal band, no slope.
- **No peaks above the local mean** inside it — no precursor, sub-burst, late tail, or single-bin spike.
- **Width 50-150 s per side, aim ~80-120 s** (STRICT). Too wide picks up orbital curvature and over-constrains the fit; too narrow under-constrains the polynomial. At 1.024-s bins that is ~50-150 bins.
- **Buffer ≥ T90/5 from the burst edge** so the burst tail does not leak in. With no catalog T90, estimate the burst's visible extent from the LC and keep a clear gap (tens of seconds for a long burst).
- **Far from orbital features** — avoid broad rises/falls, SAA-like rate steps, Earth-limb ramps.

AVOID (move elsewhere / pick the flattest part and flag) if ANY:
- Rising or falling trend across the window → slide further from the burst.
- Sub-burst / precursor > ~3σ above local floor → pick the other side, or skip past it.
- Hot bin / single-bin spike → shift the window so it is excluded.
- Step change in rate → keep the window entirely on ONE side of the step.
- Pre-burst stretch < 10 s available → use what exists and add flag `pre_window_too_short`; same for post → `post_window_too_short`.

Time-order rule: the EARLIER window is `pre`, the LATER is `post`. Both must be strictly increasing (`t2>t1`, `t4>t3`), non-overlapping with `t3 >= t2`, and the burst (the eventual source window) must fall in the gap `[t2, t3]` — validation requires `pre_stop <= source.t1 < source.t2 <= post_start`.

Seed handling (`suggested_bkg`): treat it as a starting proposal, not ground truth. If it already satisfies all criteria, accept it verbatim → `window_source: "accepted_suggestion"`. If you nudge edges → `"adjusted"`. If no seed existed or you discard it and pick fresh → `"drawn_fresh"`.

## Output contract (write into `results/approval/<trigger>_decision.json`)
Add one entry per approved detector to `"windows"`:
```json
{
  "trigger": "bn110721200",
  "approver": "Claude (AI)",
  "mode": "ai_vision",
  "detectors": ["n6", "n7", "b1"],
  "source": {"t1": <burst start>, "t2": <burst stop>},
  "windows": {
    "n6": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "adjusted"},
    "n7": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "accepted_suggestion"},
    "b1": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "adjusted"}
  },
  "reasoning": "flat pre/post baselines; avoided a +20s sub-pulse"
}
```
`window_source` must be one of `accepted_suggestion | adjusted | drawn_fresh` (validator rejects others). Values are seconds since trigger (floats). The ingest step (`scripts/39_approve_all.py ingest`) maps these to `BKG_NEG_START/STOP`, `BKG_POS_START/STOP` in `results/background_intervals.ecsv`.

## QC checklist (before approving)
- [ ] Every approved detector has a `windows` entry; `pre`/`post` present and increasing.
- [ ] Each window 50-150 s wide (flag if forced narrower).
- [ ] `pre` and `post` are off-source: visibly flat, no peak/step/spike inside.
- [ ] Burst lies fully inside `[pre_stop, post_start]`; `post_start >= pre_stop`.
- [ ] `source.t1/t2` sits inside that gap for EVERY detector (validation hard-fails otherwise).
- [ ] Mentally fit a low-order line/parabola through both windows — does it form a believable floor under the burst with no kink?
- [ ] `window_source` matches what you actually did relative to the seed.

## Common pitfalls (a human reviewer would catch)
- Putting a window ON the burst or a sub-pulse because the y-axis is linear and a faint pulse looks like baseline — zoom mentally on the floor.
- Over-wide windows (200-400 s) that span an orbital rise — looks "more data" but corrupts the polynomial; the rule is 50-150 s for a reason.
- Touching the burst edge with no buffer → tail contamination biases the fit high.
- Asymmetric quality (clean pre, sloped post) accepted silently — pick the flattest available and FLAG, don't pretend it's clean.
- Reusing one detector's edges blindly when a feature lands differently in another detector's band (esp. NaI vs BGO).
- Forgetting the source-in-gap invariant → ingest rejects the whole decision as INVALID.

## How this is scored vs humans (BENCHMARK_PLAN.md, task #2)
Run Stage 1 in `human_gui` and `ai_vision` mode on the benchmark subset → two stamped catalogs; `scripts/40_benchmark.py` compares per (trigger, detector):
- **pre/post edge Δ (s)** — absolute difference of each of the four edges vs the human.
- **window IoU** — intersection-over-union of the AI vs human pre+post intervals.
- **polynomial-fit residual χ²/dof** — quality of the 3ML polyfit on the AI window (is the chosen baseline statistically clean?).
- **baseline flatness** — residual scatter of the fitted background across the window.
Plus the shared downstream-impact test: run identical Stage 2-3 on both catalogs and compare Ep, α, kT, and the thermal-vs-double-break classification per bin/burst. The headline question is whether the physics conclusions survive the human→AI swap. Inter-human scatter (if multiple experts) is the denominator: the AI is "good" if it matches humans about as well as humans match each other.

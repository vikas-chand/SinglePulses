# Background selection — task brief for Khushboo

**Goal.** Select (or review & adjust) the **background and source time windows** for
all **106 single-pulse GRBs**, per detector. These windows are the foundation of
the whole analysis — every spectral fit depends on them. The current AI-vision
windows have real failures (6 bursts were fit on *pure background*; ~37 are
over-wide), so we want **human-selected, human-checked** backgrounds.

## What "background selection" means here
For each GRB, for each detector (NaI / BGO / LLE) used, define:
- a **pre-burst** background interval and a **post-burst** background interval
  (each ~50–150 s wide), placed off the burst;
- the implied **source/on-burst window** = the gap between them, snug around the
  actual emission.
A low-order polynomial is fit to the pre+post windows and interpolated under the
burst; so the windows must (a) bracket the burst, (b) avoid the burst itself, and
(c) avoid obvious orbital/background trends.

## Rules (full version: `BACKGROUND_SELECTION_PROCESS.md`)
- Background windows **~50–150 s each** (not multi-hundred).
- The source window must be **centered on the actual emission** (the light-curve
  peak), *not* on the catalog trigger time and **not** driven by the catalog T90
  (catalog T90 is unreliable for these bursts and should not be shown/used in the
  picker — derive duration from the background-subtracted light curve instead).
- Detectors: NaI within ~50° of the source (BCAT-rescue to ~60° if needed), the
  most-illuminated BGO, and LLE where present.
- For **early bursts** (peak near t≈0) a short pre + long post window is fine.

## Starting points (so this is *review*, not *from scratch*)
I've put my best-effort auto windows in
**`results/background_starting_points.ecsv`** (106 bursts, all detectors). For
most bursts these should be close; please **review and adjust** rather than
redo from zero. Columns: `TRIGGER_NAME, DETECTOR, BKG_NEG_START, BKG_NEG_STOP,
BKG_POS_START, BKG_POS_STOP` (source window = `[BKG_NEG_STOP, BKG_POS_START]`).

## Priority — check these 6 first (their old fits were on pure background)
`bn090620400  bn090719063  bn100612726  bn100614498  bn110920546  bn200524211`
(see `results/figures/fig_bkg_sanity_6broken.png` for the before/after.)
Then scan the ~37 with source windows wider than ~120 s, then confirm the rest.

## Output / hand-off
Save the final selections to **`results/background_intervals.ecsv`** (same column
schema as the starting-points file). When a batch is done, tell Vikas/me and I
will: re-derive the Bayesian blocks on your windows (`scripts/27`), re-fit all
models with the multi-start engine (`scripts/29`), and rebuild the master
catalog — all downstream results flow from your backgrounds.

## Tool — `scripts/30_background_picker.py` (portable, ready)
Runs on **any machine** — only needs `numpy`, `astropy`, `matplotlib` and a GUI
backend (no threeML/fermitools). It is **review-seeded**: each detector opens
with the auto starting window already drawn, so you just **Accept** or drag to
adjust. It does **not** show the catalog T90 (pre/post slots are assigned by time
order: the earlier window is "pre", the later is "post").

```
python scripts/30_background_picker.py            # review bursts not yet accepted
python scripts/30_background_picker.py --redo     # review/adjust every detector
python scripts/30_background_picker.py --redo-grb bn090719063   # one burst
```
- Click two bounds → one window (yellow). Draw the other window. Earlier = pre,
  later = post. **Accept** saves; **Clear** resets; **Skip GRB**; **Quit**.
- Backend auto-selects (macOS → Qt → Tk); force with `MPLBACKEND=TkAgg python ...`.
- **What you need on your machine:** this repo's `scripts/` + `results/single_pulse_grbs.ecsv`
  + `results/background_starting_points.ecsv` + the per-burst TTE under `data/<trigger>/`.
- Resumable: re-running only prompts bursts/detectors you haven't accepted yet.
- Output accumulates in `results/background_intervals.ecsv` (the file to send back).

# Background-Selection Process — Two_Breaks

The full rule book for how detectors and background intervals are chosen in
this pipeline. Consolidates the AI-in-the-loop workflow + every rule we've
established. Read this before changing the selection code in
`scripts/00_prototype_one_burst.py`, `scripts/00_select_backgrounds.py`,
or any successor script.

Last updated: 2026-05-20.

---

## Pipeline order

```
1. Detector pre-selection             [angles + AI/user]
2. Lightcurve rendering               [1.024-s bins, no T90 shading]
3. Background interval selection      [AI vision on PNGs]
4. Background interval approval       [human GUI per detector, or --auto-approve]
5. Polynomial background fit          [3ML's gtburst-style two-stage]
6. Bayesian blocks                    [use_background=True, broadband]
7. (Future) T90 recompute             [from bkg-subtracted LC, replaces catalog T90]
```

Each step writes a checkpoint ECSV; resumable across sessions.

---

## Step 1 — Detector selection

**Goal:** for each GRB, choose which NaIs (12 candidates) and BGOs (2
candidates) feed the analysis.

### Compute angles to source

Per detector, compute the angular separation between the detector's pointing
direction and the source (RA, DEC) at trigger time. Use:

- **Detector pointing table** (Meegan+ 2009, hardcoded in gtburst's
  `fermitools/GtBurst/angularDistance.py:7-22`): the `DetDir` dict gives
  `[zenith, azimuth]` in spacecraft coords for each detector.
- **Spacecraft pointing at trigger time** (`RA_SCX, DEC_SCX, RA_SCZ,
  DEC_SCZ`): from POSHIST file (`GLAST POS HIST` extension, 1 Hz sampling)
  via linear interpolation between rows bracketing TRIGTIME. POSHIST stores
  attitude as quaternions (`QSJ_1..QSJ_4` — vector + scalar) so a
  quaternion→axis-RA/DEC conversion is needed.
- **Angle formula**: gtburst's `getDetectorAngle(...)` (Vincenty formula).
  Rotate the detector's body-frame direction into J2000 sky using the
  spacecraft axes, then take angular separation to the source.

### Selection rules

| Detector state | Action |
|---|---|
| NaI θ ≤ 50° AND in BCAT mask | ✅ pre-ticked KEEP |
| NaI θ > 60° AND not in BCAT mask | ❌ pre-ticked DISCARD |
| NaI θ ≤ 50° AND not in BCAT mask | ⚠️ shown but unticked (good geometry, didn't trigger) |
| NaI 50° < θ ≤ 60° AND in BCAT mask | ⚠️ shown but unticked (borderline angle, did trigger) |
| NaI 50° < θ ≤ 60° AND not in BCAT mask | ❌ pre-ticked DISCARD |
| BGO with same-side-NaI ≥ 1 selected | ✅ pre-ticked KEEP (b0 if any n0-n5; b1 if any n6-nb) |
| BGO with no same-side NaI | ❌ pre-ticked DISCARD |

**Threshold note:** 50° is the conservative Goldstein+ 2012 cut. Gtburst's
own GUI doesn't enforce any angle threshold (it relies on the BCAT mask) —
we add this rule on top.

### Picker UI

Show **all 14 detectors** in a gtburst-style checkbox window, each with
its computed angle (sorted by angle ascending). Pre-tick per the rules
above. User can tick/untick before pressing Accept. If user ticks a
detector we don't already have TTE for, **download it on the fly** before
proceeding.

### Output

`results/selected_detectors.ecsv`:
```
TRIGGER_NAME, DETECTOR, ANGLE_DEG, IN_BCAT, AUTO_TICK_RULE, USER_SELECTED
```

---

## Step 2 — Lightcurve PNG rendering (gtburst-matching)

For each user-approved detector, render a single PNG to
`plots/lc_for_ai/<trigger>_<det>.png`:

- **Bin width**: 1.024 s (CSPEC native cadence; matches gtburst's
  asymptotic display binning)
- **Energy range**:
  - NaI: 8-900 keV
  - BGO: 250-40000 keV
- **Y axis**: linear, counts s⁻¹
- **X axis**: time since trigger, generous window (typically -150 to +350 s
  around T90, or wider if events extend further)
- **NO T90 shading**. T90 will be recomputed from the bkg-subtracted LC
  later; pre-marking the catalog T90 would bias the AI to anchor on it.
- **No fancy annotations** — just the step LC and axis labels.

---

## Step 3 — Background interval selection (AI vision)

For each PNG, the AI (Claude vision via `Read` tool, or via embedded
`anthropic` SDK call) emits one pre-burst and one post-burst window as JSON:

```json
{
  "n6": {
    "pre": [t1, t2],
    "post": [t3, t4],
    "confidence": "high | medium | low",
    "reasoning": "free-text 1-2 sentence rationale",
    "flags": ["low_confidence", "pre_window_too_short", ...]
  },
  ...
}
```

### SELECT a region if all of:

| Criterion | Why |
|---|---|
| Flat / very slowly varying count rate | Polyfit converges cleanly |
| No visible peaks above local mean (no sub-bursts, precursors, late tails) | Peaks contaminate bkg estimate |
| **Width 50-150 s per side, aim ~80-120 s** ← strict | Wider picks up orbital trends + wastes statistics; narrower under-constrains polyfit |
| Buffer ≥ T90/5 from T90 edge | Avoids burst tail leaking into bkg |
| Far from visible orbital features (SAA, Earth-limb crossings, particle storms) | Those break the polynomial assumption |

### AVOID (look elsewhere) if any:

| Anti-criterion | Action |
|---|---|
| Rising/falling trend across the window | Move further from T90; if no flat region, pick flattest and flag |
| Sub-burst / precursor peak (>3σ above local) | Skip past, pick other side |
| Hot bin / single-bin spike | Exclude that bin or shift window |
| Step change in rate | Pick on one side of the step only |
| Pre-burst < 10 s available | Use what's available, flag `pre_window_too_short` |
| Post-burst < 10 s available | Same, flag `post_window_too_short` |

### Confidence routing

- `high`: clean LC, intervals comfortably within criteria → can `--auto-approve`
- `medium`: minor issue (slightly narrow, visible feature nearby that's avoided) → logged when `--auto-approve` is on
- `low`: window forced into a problematic region, or no clean baseline available → **always goes to human GUI even with `--auto-approve`** (safety gate)

---

## Step 4 — Approval gate (human GUI per detector)

> **Normative GUI behavior now lives in `dev/GUI_REQUIREMENTS.md`** (numbered,
> testable requirements + contradiction register). Where this section and that
> spec disagree, the spec wins — known stale items here: the "numpy.polyfit"
> overlay (it is the 3ML two-stage polyfit), the macosx-only backend note (TkAgg
> is supported), `--auto-approve` (legacy scripts only), and the 6-column output
> schema (now 13 stamped columns).

For each (trigger, detector), open a gtburst-style window pre-populated
with the AI's `pre` and `post` intervals drawn as gold-shaded
`fill_between` regions, with a red `numpy.polyfit(deg=2)` overlay over the
LC for visual sanity check.

### Buttons (figure text with picker=20)

| Button | Color | Action |
|---|---|---|
| Clear | red | wipe AI intervals; user clicks 4 times to define their own (2 pre, 2 post; auto-merge into intervals, snap to LC bin via `np.searchsorted`) |
| Accept | green | save (AI's or user's) intervals → next detector |
| Skip GRB | orange | discard this entire GRB and move on |
| Quit | gray | exit |

### UX details (mirror `fermitools/GtBurst/interactivePlots.py:71-445`)

- **Left-click+release within 2-pixel tolerance** counts as a click (not a drag)
- **Transient dashed vertical line under cursor** via `motion_notify_event`
- **`isNormalMode()` guard**: inspect `fig.canvas.toolbar.mode`; if active
  (zoom or pan), silence click-selection. Lets the matplotlib default
  toolbar handle zoom; no custom zoom UI needed.
- **Matplotlib backend**: `matplotlib.use('macosx')` not `'TkAgg'` — TkAgg
  crashes (`TclError: can't invoke "wm" command: application has been
  destroyed`) on the second figure after the first one's `plt.close()`.

### --auto-approve

Skip the GUI for `confidence: high` (silent accept) and `confidence:
medium` (accept but log to `auto_approved_with_caveats.log`).
`confidence: low` always opens the GUI.

### Output

`results/background_intervals.ecsv` (or `_prototype.ecsv` for the
single-burst prototype):
```
TRIGGER_NAME, DETECTOR, BKG_NEG_START, BKG_NEG_STOP, BKG_POS_START, BKG_POS_STOP
```

---

## Step 5 — Polynomial background fit (3ML, gtburst-style)

The downstream pipeline (scripts 04/05/06) calls 3ML's
`TimeSeriesBuilder.set_background_interval(neg_str, pos_str)` with the
approved intervals.

3ML's polyfit is **structurally identical to gtburst's** (same algorithm,
ported by Vianello who wrote both, then maintained by Burgess):

1. **Broadband grade selection**: sum counts over all energy channels in
   the bkg intervals; fit polynomials of grade 0..4; pick the highest
   grade where `2·Δlog L ≥ 9.0` (Wilks' 3σ threshold). One grade for the
   whole detector.
2. **Per-channel coefficients**: refit each of the 128 channels at the
   fixed global grade, Cash-statistic MLE.

Source: `threeML/utils/time_series/event_list.py:485-577`. Reference:
`fermitools/GtBurst/dataHandling.py:2789-3106`. **No need to port
LATBright's `gtburst_bkg.py`** — 3ML already gives gtburst-faithful
backgrounds out of the box.

---

## Step 6 — Bayesian blocks

```python
tsb.create_time_bins(burst_start, burst_stop,
                     method='bayesblocks', p0=0.01, use_background=True)
```

- `use_background=True` makes BB run on the **bkg-subtracted net rate**
  (via the per-channel polyfit summed over all channels), not raw events.
  Fewer, more physical block boundaries.
- BB in 3ML is **always broadband** — there is no energy-range argument
  for `create_time_bins`. The commented-out `use_energy_mask` block in
  `time_series_builder.py:557-563` is evidence someone tried and
  abandoned. If we ever want band-selected BB (for MEPSA on a specific
  band), we implement it ourselves with `astropy.stats.bayesian_blocks`
  on energy-filtered events.

### Post-BB merge (Phase A — planned, not yet implemented)

Walk blocks left-to-right (increasing time):
- If `sig[i] < 3σ`: merge with the lower-significance flanking neighbor
  (right if `i==0`; left if `i==N-1`; tie→right). `new_start = min`,
  `new_stop = max`. Recompute significance for the merged block via
  `tsb.set_active_time_intervals(...)`. Replace both blocks. Stay on the
  merged block (don't advance) and re-check.
- Iterate until every block ≥ 3σ or only one block remains.

### Output

`results/bb_blocks_*.ecsv`:
```
TRIGGER_NAME, DETECTOR, BLOCK_INDEX, T_START, T_STOP, SIGNIFICANCE, POLY_ORDER
```

---

## Step 7 — T90 recompute (future)

T90 in `grb_sample.ecsv` is from the GBM catalog. After the bkg-subtracted
LC is available, recompute our own T90 (cumulative 5%-95% of net counts
across the burst window), write to `results/measured_t90.ecsv`, and have
downstream scripts read from there instead of the catalog. Not yet built.

---

## Outputs MEPSA can consume

After Step 6:
- The **per-channel polyfit model** is stored in the TSB; can be evaluated
  at any time and energy band via `tsb.get_total_poly_count(start, stop,
  mask=channel_mask)`.
- The **bkg-subtracted net LC** in any band is derivable from raw TTE
  events minus this polyfit model.
- MEPSA reads net-LC PNG/array + run its peak-finder.

---

## Implementation status

| Step | Script | Status |
|---|---|---|
| 1. Detector picker | `scripts/00_prototype_one_burst.py` Phase 1 | **partial** — shows only detectors with TTE on disk; not all 14; no angles. **Needs rebuild with POSHIST + angle compute** |
| 2. LC rendering | same script, `render_lc_png()` | ✅ done |
| 3. AI bkg selection | manual via Claude vision + JSON | ✅ done in-session; embedded SDK not yet wired |
| 4. Approval GUI | same script, inlined `BackgroundSelector` | ✅ done |
| 5. Polyfit | 3ML TSB inside scripts 04/05/06 | ✅ already in pipeline |
| 6. BB (broadband) | `run_bb_for_detector()` | ✅ done |
| 6b. Sub-3σ merge | — | **planned, not built** |
| 7. T90 recompute | — | planned, not built |

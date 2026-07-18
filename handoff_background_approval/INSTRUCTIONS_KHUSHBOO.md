# Stage-1 review instructions — Khushboo (2026-07-17 refresh)

Hi Khushboo! **Your job:** human Stage-1 approval (detectors + background
windows + source interval) for the **65 remaining bursts** listed in
`dev/khushboo_worklist.txt`. Vikas has done 41 (including all 13 LLE bursts).
Your decisions become the HUMAN arm of the analysis — they are science inputs,
so judge from the data; the AI suggestions are seeds, not answers.

*(This replaces the older guide from the consensus-review era; the GUI has
gained several aids since, described below.)*

**Read `PROJECT_BRIEFING_KHUSHBOO.md` (same folder) first** — it explains WHAT
the project is and WHY your selections matter, from the 2026-07-17 planning day.

## 0. Setup (once)

```bash
# fresh clone (ask Vikas for collaborator access), or just `git pull` if you have it:
git clone https://github.com/vikas-chand/SinglePulses.git Two_Breaks
cd Two_Breaks && git pull            # MUST be on the current main

conda activate threeML               # heavy env (3ML refits inside the GUI)
export FERMI_DIR=$CONDA_PREFIX/share/fermitools
export CALDB=$FERMI_DIR/data/caldb
export CALDBCONFIG=$CALDB/software/tools/caldb.config
export CALDBALIAS=$CALDB/software/tools/alias_config.fits
```

- `results/grb_sample.ecsv` must exist (tracked in git — `git pull` provides it;
  without it the detector picker hard-stops with a remedy message).
- **Linux only:** run the GUI with `MPLBACKEND=TkAgg python3 ...` (macOS needs
  nothing). The old crash-after-first-detector and stuck-after-refit bugs are
  fixed; if a dead "zombie" window ever lingers, just close it manually.
- Data: `python handoff_background_approval/fetch_tte.py <bn...>` or
  `python scripts/02_download_data.py --trigger <bn...>` for any burst whose
  TTE is missing (most are already on disk).

## 1. The loop (one burst at a time, resumable any time)

```bash
while read t; do
  [ -z "$t" ] && continue
  MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --trigger "$t" \
      --approver "Khushboo Sharma" --seed-from-catalog
done < dev/khushboo_worklist.txt
```
(Drop `MPLBACKEND=TkAgg` on macOS.)

Each burst walks you through 3 windows. Close the terminal any time — finished
bursts are saved; rerunning the loop re-offers unfinished ones. Re-approving a
burst cleanly REPLACES its previous decision, including dropped detectors.

### Window 1 — detector picker
Tick the detectors to use. Pre-ticks follow the rules; change them if wrong:
- **NaI: angle ≤ 50°** to the source. 50–60° only to rescue a burst that would
  otherwise have <2 NaIs (BCAT membership helps); **> 60° never**.
- **BGO companion rule:** b0 if the chosen NaIs are n0–n5, b1 if n6–nb (both
  if the NaIs straddle the spacecraft).

### Window 2 — background selector (one per detector)
Two panels: light curve on top, fit residuals below. The AI's windows are
pre-loaded (gold).
- **Goal:** one PRE window and one POST window of clean baseline, **~50–150 s
  each side**, whose inner edges **HUG the burst** (gap to the burst ≈ 5–20 s;
  never anchor a window on an SAA-exit or data-gap edge).
- **Aids on the plot** (the same aids the AI raters see):
  - grey = the light curve; **orange** = robust `imodpoly` baseline (aid only);
  - faint **green** tints = candidate clean-background stretches;
  - **red shaded** span = detected transient (>5σ);
  - after any edit, the **red curve** = the real 3ML polynomial background fit
    over YOUR windows (drawn only across the range it is used), with residuals
    below — background regions should scatter within ±1σ of 0.
- Adjust by clicking/dragging or keys (`a/s` = pre edges, `d/f` = post edges,
  ←/→ = ±1 bin, shift = ±16 bins). The window "freezes" ~3–5 s after an edit —
  that is the 3ML refit ("Refitting… input paused"); input during it is
  deliberately dropped.
- **Accept** saves the detector; **Skip GRB** skips just that detector;
  **Quit** aborts the whole burst (nothing saved).
- 2008–2012 bursts have only ~25–35 s of pre-trigger TTE — a short pre window
  there is the data's limit, not your mistake. Do your best inside what exists.

### Window 3 — source marker
Mark the burst's emission interval `[t1, t2]` on the reference-NaI light curve.
- **Gold** = the AI's suggestion (NOT gospel — it can spill into background);
  **green** = your approved background windows; **orange** = the fitted
  background level under the source; **blue band = the ALLOWED range** (the
  common gap over all your accepted detectors — the source MUST sit inside it).
- Accept the gold with 0 clicks, or click start+stop yourself (a red span shows
  your pair), then **Accept**. A source outside the blue band triggers a
  **red warning** — that means one of your background windows overlaps the
  pulse; Quit and fix that background rather than overriding, unless you are
  certain.
- Include the full decay tail (don't clip the FRED); exclude flat baseline.

## 2. Special bursts — READ FIRST
**Check `dev/special_bursts.md` before selecting.** Multi-episode bursts must
use the pulse listed there, not the brightest spike (e.g. bn130427324 = the
2nd pulse; already done by Vikas). If YOU meet a burst where the suggestion is
clearly the wrong pulse, note the trigger and tell us — it joins the registry.

## 3. Progress check

```bash
python - <<'EOF'
import glob, json
d=[json.load(open(f)) for f in glob.glob('results/approval/*_decision.json')]
print(sum(1 for x in d if x.get('mode')=='human_gui'), 'human decisions saved;',
      sum(1 for x in d if str(x.get('approver','')).startswith('Khushboo')), 'yours')
EOF
```
Your decisions live in `results/approval/<trigger>_decision.json`
(`"approver": "Khushboo Sharma"`). Ingest into the catalogs is run centrally
afterwards — you only produce decisions. **Never hand-edit the ECSV catalogs.**
Commit + push your decision files at the end of each session:
`git add results/approval/*_decision.json && git commit -m "stage1: <N> bursts (Khushboo)" && git push`.

## 4. If something breaks
- GUI never appears / picker skipped → `git pull` (grb_sample fix) and check
  `MPLBACKEND=TkAgg` on Linux.
- A burst errors repeatedly → Quit it, note the trigger, move on.
- Anything confusing → screenshot + trigger name to Vikas.

## 5. What happens with your selections
They are ingested to the human catalog, re-binned (Bayesian blocks from YOUR
source interval), and fit with the full 24-model menu — machinery identical to
the AI arm, so any physics difference traces to the selections. That comparison
(plus Expert1-vs-Expert2 agreement) is the benchmark paper; your selections
also feed the science paper. *(The 25-burst benchmark set may later be re-run
with per-rater isolation (`--approval-dir/--out`); you'll get explicit
instructions if so — for THIS pass use the defaults above.)*

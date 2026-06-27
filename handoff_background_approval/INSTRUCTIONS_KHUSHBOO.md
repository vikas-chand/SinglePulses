# How to run the approval step — a guide for Khushboo

Hi Khushboo! This walks you through **Stage 1** of the pipeline: approving, for each
of the 106 GRBs, three things —

1. **which detectors** to use (NaI + BGO),
2. the **background windows** (a pre-burst and a post-burst stretch of quiet data),
3. the **source / emission window** (where the burst actually is).

The result is one file, `results/background_intervals.ecsv`, with a stamp recording
**who** approved each row and **how** (you in the GUI, or an AI on your instruction).
Everything downstream (binning, spectral fits) depends on this file.

You can do this **two ways** — let an AI assistant drive it (faster), or click through
it yourself. Both are described below. Pick whichever you prefer; you can mix them.

---

## 0. One-time setup

```bash
# 1. Clone the repo (ask Vikas to add you as a collaborator first)
git clone https://github.com/vikas-chand/SinglePulses.git
cd SinglePulses

# 2. Install the light dependencies (enough for the approval GUI)
pip install -r handoff_background_approval/requirements.txt

# 3. Get the data. Two options:
#    (a) light — only the event files the GUI needs (no special software):
python handoff_background_approval/fetch_tte.py
#    (b) full — TTE + responses (needed later for binning/fitting; needs the threeML env):
#        python scripts/02_download_data.py
```
Run every command **from the repo root** (`SinglePulses/`).

> Tip: if a plot window never appears, set the GUI backend first:
> `export MPLBACKEND=QtAgg` (or `TkAgg`), then re-run.

---

## Path A — let an AI assistant do it (Codex or Claude Code)

Open the repo in **Codex** or **Claude Code** in your terminal and tell it:

> "Read `AGENTS.md`, then run Stage 1 approval with `scripts/39_approve_all.py`:
> render the candidates, look at the light-curve PNGs, and for each burst decide the
> detectors, the pre/post background windows, and the source window. Set the approver
> to 'Khushboo (AI-assisted)'. Then ingest to `results/background_intervals.ecsv` and
> run `scripts/36_progress_check.py`."

The AI will:
1. run `python scripts/39_approve_all.py render --all` (makes the light-curve images),
2. **look at each image**, choose the windows, and write a decision file per burst,
3. run `python scripts/39_approve_all.py ingest --all` to build the stamped catalog.

**Your job here is to review its choices**, not to click. Ask it to show you a few of
the light curves with the windows it picked, and tell it to adjust anything that looks
wrong (e.g. "the source window on bn… is too wide"). The AI records that **the AI**
made the call — which is fine and intended; the gate just keeps it honest.

---

## Path B — do it yourself in the GUI

Run, per burst:

```bash
python scripts/39_approve_all.py gui --trigger bn110721200 --approver "Khushboo Hooda"
```

Three windows open in sequence:

**1. Detector picker.** A checklist of all detectors, sorted by angle to the burst.
The good ones (NaI within 50° + the matching BGO) are pre-ticked. Tick/untick as you
like, then click **Accept**. (Closer-angle detectors saw the burst better.)

**2. Background selector** (one per detector). You see the light curve. The suggested
pre- and post-burst background windows are shaded. You want them on **flat, quiet
data** on either side of the burst — avoiding the burst itself and any bumps.
- **Accept** (green) — keep the windows, go to the next detector.
- **Clear** (red) — wipe them and click your own: 2 clicks before the burst, 2 after.
- Fine-tune with the keyboard: `a`/`s` move the pre-window edges, `d`/`f` the
  post-window edges (arrow keys nudge; the residual panel helps you judge the fit).
- **Skip GRB** / **Quit** if needed.

**3. Source marker.** The brightest detector's light curve opens. **Click the start
of the burst emission, then click the end** (2 clicks), then close the window. That's
the source window. (A suggestion is pre-shaded; if you just close without clicking, it
uses the suggestion.)

That's one burst. Repeat for the next trigger. Your progress is saved per burst, so
you can stop and resume anytime.

To get the list of triggers to work through: `python scripts/36_progress_check.py`
(it shows how many are done and which are left).

---

## Checking progress & quality (run anytime)

```bash
python scripts/36_progress_check.py
```
It tells you how many windows/bursts are done (target: 418 windows / 106 bursts),
flags anything odd (zero-width or very wide windows, missing approver), and shows the
approver tally. **You're finished when it reports complete and "QC: clean".**

---

## What to do when you're done

The single deliverable is **`results/background_intervals.ecsv`**. Send it back to
Vikas — either commit it on a branch and push, or share the file directly:

```bash
git checkout -b khushboo-approvals
git add results/background_intervals.ecsv
git commit -m "Approved detector + background + source windows"
git push origin khushboo-approvals
```

Vikas then runs the binning and spectral fits from it. (If you'd like to run those too,
they're in `AGENTS.md` — but they need the heavier threeML environment.)

---

## Quick reference

| Goal | Command |
|---|---|
| Get the data (light) | `python handoff_background_approval/fetch_tte.py` |
| AI does it | open Codex/Claude → "Read AGENTS.md, run Stage 1 approval" |
| You do one burst (GUI) | `python scripts/39_approve_all.py gui --trigger bn… --approver "Khushboo Hooda"` |
| AI render (for review) | `python scripts/39_approve_all.py render --all` |
| Build the catalog | `python scripts/39_approve_all.py ingest --all` |
| Check progress / QC | `python scripts/36_progress_check.py` |

## If something goes wrong
- **No window appears** → `export MPLBACKEND=QtAgg` (or `TkAgg`) and re-run.
- **"No TTE" / missing file** → run `fetch_tte.py` again (it retries failed downloads),
  or ask Vikas to share `data/<trigger>/`.
- **Wrong directory** → make sure you're in the repo root (`SinglePulses/`).
- **Anything unclear** → ask Vikas, or ask your AI assistant to read `AGENTS.md` and
  explain the step.

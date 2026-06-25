# Background-Interval Approval — handoff bundle

This folder packages the **background-window approval** step of the Two_Breaks
single-pulse GRB pipeline so it can be run by a collaborator (Khushboo) on her own
machine, optionally driven by an AI assistant.

## What gets produced

One file: `results/background_intervals.ecsv` — the pre-/post-burst background windows
for every detector of all 106 GRBs, **each row stamped with who approved it and when**.
That file is the input to the authoritative re-block and spectral re-fit on Vikas's
side. Nothing downstream is final until it exists and is fully approved.

## Files here

| File | What it is |
|---|---|
| `SKILL_background_approval.md` | **Operating protocol for an AI assistant** — point Claude at this; it covers install → data → run → QC → return. |
| `fetch_tte.py` | Stdlib TTE downloader (no threeML) — gets only the event files the picker needs from the public HEASARC archive. |
| `requirements.txt` | Light dependencies (numpy, astropy, matplotlib, PyQt5). |

The tool itself is in the repo: `scripts/30_background_picker.py` (GUI picker) and
`scripts/36_progress_check.py` (progress + QC).

## Quick start (human)

```bash
# from the repo root, in a light env:
pip install -r handoff_background_approval/requirements.txt
python handoff_background_approval/fetch_tte.py            # download the TTE data
python scripts/30_background_picker.py --approver "Khushboo Hooda"   # review + approve
python scripts/36_progress_check.py                       # check progress + QC
```

Each detector opens with a suggested background window already drawn — **Accept** it,
or **Clear** and click your own (2 pre-burst points, 2 post-burst points). Quit and
re-run anytime; it resumes where you left off. Target: 418 windows across 106 bursts.

## Quick start (AI-driven)

Open `SKILL_background_approval.md` and follow it top to bottom. Key rule: the AI sets
everything up and launches the GUI, but **a human must review and approve each window
— approvals are never clicked or invented by the AI.**

## Notes

- This step needs **no threeML / fermitools** — keep the environment light.
- Raw TTE data is not in the repo (too large); `fetch_tte.py` downloads it, or Vikas
  can share the `data/` directory.
- Run all commands from the repo root so `results/` and `data/` resolve.

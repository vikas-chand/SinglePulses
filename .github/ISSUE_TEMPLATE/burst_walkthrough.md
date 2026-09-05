---
name: Burst walkthrough log
about: One issue per burst, opened at step 0b and closed at step 9 — the running record of a gated walkthrough
title: "bnXXXXXXXXX — walkthrough by <your name>"
labels: walkthrough
---

**Burst:** bnXXXXXXXXX (GRB name if known) · **Analyst:** <name> · **AI used:** <Claude Code / Codex / ChatGPT / none> · **Branch:** memory-guard @ `<git rev-parse --short HEAD>`

Protocol: `dev/ai_guides/BurstWalkthrough.md` (ledger 0b, 0, 1–9; RUN → PRESENT → GATE → LITERATURE → DISTILL at every step).
Post ONE comment per step when its gate closes, using the four PRESENT items:
(a) what the step does, (b) what actually ran (commands, decisions, seeds), (c) conclusions with honest flags, (d) what is unexplained.
Attach the step's figure PNGs and the `REPORT_<trig>.md` at step 9. Never paste numbers you did not recompute.

- [ ] 0b literature harvest (papers found; `notes/reconciliation/<trig>_harvest.json`)
- [ ] 0 identity & circulars (`n_circulars`; a zero count is a result, not an error)
- [ ] 1 data inventory (files, response coverage vs source window, occultation check)
- [ ] 2 detectors (ADOPT the stamped catalog decision; say if you disagree and why)
- [ ] 3 background windows (ADOPT; hug-the-burst 5–20 s check)
- [ ] 4 source window (ADOPT)
- [ ] 5 binning (block table sha256; number of blocks)
- [ ] 6 spectral fitting (24-model table; winners with margins; ties as ties; rails disclosed)
- [ ] 7 temporal (T90 estimator named; MVT; lag with its sign convention)
- [ ] 8 νFν panels (residuals read bin by bin)
- [ ] 9 QC, report, literature diff, lessons proposed

**Lessons proposed (candidates for the skill files — the PI accepts or rejects):**
1. …

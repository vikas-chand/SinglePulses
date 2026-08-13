# Khushboo — fresh tasks (2026-07-22)

Hi Khushboo! Two things changed since the last handoff, so your focus shifts.

## What's changed
- **The 65-burst Stage-1 selection is DONE** — Vikas worked through the whole
  sample himself (105/106 bursts, including your worklist and the 16
  geometry-conflict bursts). **You do NOT need to run the GUI selection loop
  anymore.** `INSTRUCTIONS_KHUSHBOO.md` (the 65-burst loop) is now archived.
- That frees you for the two things that actually still need you, below.

Setup is unchanged (heavy env):
```bash
cd ~/Desktop/Projects/SingleRest/Two_Breaks && git pull
conda activate threeML
source /tmp/heavy_env.sh     # CALDB / FERMI_DIR
```

---

## TASK A (primary) — verify the per-GRB notebooks + literature checks

This is the human-checkable mirror of the mass `.py` pipeline: the SAME
machinery, one GRB at a time, top to bottom, so you can *see* every step and
confirm the multi-core run isn't doing anything wrong. Full detail is in
`KHUSHBOO_NOTEBOOK_VERIFICATION.md` (still current) — the short version:

```bash
# executed notebook already exists at notebooks/verified/<trig>.ipynb — read it,
# and re-run any cell to confirm. To (re)generate one:
python notebooks/run_grb.py <bn...> --depth full --execute
```

**Do the LLE/LAT bursts FIRST** (hardest + most important). For each, check top
to bottom: data inventory → detectors (θ ≤ 60°) → two-tier Bayesian blocks →
temporal (T90/pulse/MVT) → the full 24-model spectral fit (a *physical* model
wins, AIC finite, nothing all-railed) → degeneracy-aware census → **LLE/LAT
actually used in the broadband fit, not silently dropped.**

### The literature-consistency check (Section 10) — do this per burst
Enter the prior published results for each GRB in `notebooks/configs/<trig>.yaml`
under `literature:` (real papers only, no invented values), re-run, and set
`consistent: true/false`. **Two high-energy anchors to check explicitly on the
LLE/LAT bursts** (from this week's wide-band work):
- **GRB 160625B (bn160625945):** the literature disagrees with itself — Ravasio
  et al. 2018 (A&A 613, A16) find a **2SBPL synchrotron** continuum (slopes
  −0.67/−1.5, E_break ~100 keV) and *disfavor* blackbody; Lü+17 / Wang+17 /
  Zhang+18 find **thermal/photospheric** components; **Wang et al. 2017
  (arXiv:1611.04879)** find a **high-energy cutoff at ~tens of MeV** in the LLE
  band. Record which camp our fit lands in, per block.
- For any LLE/LAT burst: note whether our high-energy behavior (a cutoff, an
  extra hard PL, or an unbroken extension) matches the published LAT/LLE picture.

### Report back
Per burst: OK / issues (what), + the literature verdict (consistent / tension /
pending). Send the filled `notebooks/configs/*.yaml` back so it's recorded.

---

## TASK B (parallel) — Expert-2 Stage-1 selections on the 25-burst benchmark set

This is for the **agentic paper**: the benchmark's denominator is *inter-human
scatter* — how well two experts agree. Vikas is Expert-1; **you are Expert-2**,
and your independent pass on the 25-burst set is the missing piece. Judge from
the data; treat the AI pre-ticks as seeds, not answers. **Do NOT look at Vikas's
decisions first** — the whole point is an independent second opinion.

The 25 bursts are in `dev/benchmark_sample.ecsv`. Run with **per-rater
isolation** so your decisions land in their own directory (not the main
catalog):

```bash
python - <<'EOF'
from astropy.table import Table
print("\n".join(str(r['TRIGGER_NAME']).strip() for r in Table.read('dev/benchmark_sample.ecsv', format='ascii.ecsv')))
EOF
# then, one burst at a time (drop MPLBACKEND on macOS):
MPLBACKEND=TkAgg python scripts/39_approve_all.py gui --trigger <bn...> \
    --approver "Khushboo Sharma" --seed-from-catalog \
    --approval-dir results/benchmark/expert2_approval \
    --out results/benchmark/expert2.ecsv
```

The GUI mechanics (detector picker / background selector / source marker) are
exactly as in the old `INSTRUCTIONS_KHUSHBOO.md` §1 — those still apply; only the
worklist and the output directory change. Check `dev/special_bursts.md` first
(e.g. bn130427324 = 2nd pulse). Commit + push your `expert2_approval/` files at
the end of each session.

---

## Priority
Task A first (it validates the pipeline the papers rest on and is ready to go);
Task B in parallel when you want a change of pace. Anything confusing →
screenshot + trigger to Vikas.

*Generated 2026-07-22. Supersedes the 65-burst selection loop in
INSTRUCTIONS_KHUSHBOO.md (that task is complete).*

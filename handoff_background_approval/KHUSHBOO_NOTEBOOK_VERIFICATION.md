# Khushboo — verify the per-GRB end-to-end notebooks

You have a set of **executed notebooks** (in `notebooks/outputs/<trigger>.ipynb`),
one per GRB, for the LLE/LAT bursts. Each runs the WHOLE pipeline for one burst
at **full depth** (all 24 spectral models + LLE, temporal, census). Please run
each yourself and verify it is sensible. This is the trust check before we build
the paper on these.

## 0. One-time setup
```bash
conda activate threeML
source /tmp/heavy_env.sh          # sets CALDB / FERMI_DIR (needed for the fits)
cd ~/Desktop/Projects/SingleRest/Two_Breaks
```

## 1. How the notebooks work (config-driven — ONE notebook, per-GRB config)
There is a SINGLE notebook: `notebooks/Two_Breaks_single_GRB_pipeline.ipynb`.
Which GRB it runs comes from a tiny config, not from editing the notebook:
```bash
# run a burst headless -> notebooks/outputs/<trig>.ipynb
python notebooks/run_grb.py bn130427324 --depth full --execute
# OR open interactively with the burst selected:
GRB=bn130427324 DEPTH=full jupyter lab notebooks/Two_Breaks_single_GRB_pipeline.ipynb
```
The per-GRB config is `notebooks/configs/<trig>.yaml` (trigger, depth, special
flags). Nothing else varies per burst — detectors/background/source are read
from the human-reviewed catalog at run time.

## 2. What to check in EACH notebook (top to bottom)
1. **Data inventory** — GBM/LLE/LAT flags match what you expect for that burst.
2. **Detectors** — the approved NaI (θ ≤ 60°) + BGO + LLE are the right ones;
   angles sensible.
3. **Background/blocks** — the two-tier Bayesian blocks look reasonable (block
   count, significances); no obviously bad background.
4. **Temporal** — T90, pulse fit (Norris/Kocevski/Gowri) converged; MVT sane.
5. **Spectral (full 24-model)** — the fit ran; a physical model wins; AIC values
   finite; no all-railed nonsense.
6. **Census** — the degeneracy-aware winner / class / family per block make sense.
7. **LLE/LAT** — for bursts flagged LLE=yes, confirm the LLE plugin was actually
   used in the broadband fit (not silently dropped).

Flag anything that looks wrong (wrong detectors, contaminated background, a
railed/absurd fit, a burst that errors mid-notebook).

## 3. THE LITERATURE-CONSISTENCY CHECK (important — do this per burst)
Section 10 of each notebook asks: **are our findings consistent with published
work on THIS object?** For well-studied bursts (e.g. 130427A, 110721A) there is
a lot of literature.
- Look up the prior published results for the GRB (spectral model, Ep, kT,
  two-break/thermal claim, MVT, etc.) from the real papers.
- Enter them in `notebooks/configs/<trig>.yaml` under `literature:` as, e.g.:
  ```yaml
  literature:
    - {ref: 'Preece2014', finding: 'Band+BB, kT~40 keV in first pulse', consistent: null}
    - {ref: 'Ravasio2019', finding: 'double smoothly-broken PL (2SBPL)', consistent: null}
  ```
- Re-run the notebook; Section 10 will print our result next to each prior
  finding. Set `consistent: true/false` after comparing.
- **Cite real papers only** — do not invent values. A bare `literature: []`
  means the check is still pending for that burst.

## 4. Report back
For each burst: OK / issues (what), and the literature-consistency verdict
(consistent / tension / pending). Send the filled configs back so the
comparisons are recorded.

*Generated 2026-07-19. Notebooks built from the human-reviewed re-analysis
(clean_blocks/per_burst_human_final). The 16 geometry-conflict bursts you are
re-reviewing are NOT in this set yet — they join after your Stage-1 fixes.*

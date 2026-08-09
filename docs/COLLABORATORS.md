# Collaborator Guide — SinglePulses / Two_Breaks

For Khushboo, Jagdish, and anyone joining the project. This is the *how to work here* file;
the *what the pipeline is* file is [`docs/agentic_workflow_map.md`](agentic_workflow_map.md)
(GitHub renders its diagrams — read it first), and the *how to run it* file is
[`docs/QUICKSTART.md`](QUICKSTART.md).

---

## 1. First hour

1. Clone, then read in this order:
   - `docs/agentic_workflow_map.md` — the whole system on one page
   - `AGENTS.md` — the canonical run guide (environment, CALDB, Stage 1→2→3 commands)
   - `docs/QUICKSTART.md` — the honest fresh-clone truths
2. **What a fresh clone can and cannot do:** `results/` is mostly gitignored, so there are no
   pre-made blocks — **you cannot run Step 6 directly. Start at Step 5** (`scripts/27b`),
   which regenerates blocks from tracked inputs. Only **6 sample bursts** have tracked data
   (`bn110721200`, `bn081125496`, `bn150902733`, `bn160625945`, `bn090620400`,
   `bn201016019`); everything else re-downloads via `scripts/02`. **No LAT data is tracked**
   (the files are 0.4–2 GB per burst).
3. Environment: two tiers. *Light* (numpy/astropy/matplotlib) runs the pickers, tables and
   `tests/`. *Heavy* (the `threeML` conda env + CALDB exports, recipe in `AGENTS.md` §env —
   note `$FERMI_DIR/data/caldb`, **not** `refdata/caldb`) runs binning and fitting.
4. Smoke test (light tier, no data needed):
   ```bash
   python -m pytest tests/ -q
   ```
   `tests/test_lessons.py` is the lessons-as-tests suite; **xfails are normal** — they are the
   named regeneration-debt ledger, not breakage.

## 2. The skills — read before you run

Every pipeline step has a skill file in `dev/ai_guides/` (step ledger in
`BurstWalkthrough.md`). They are not documentation *about* the pipeline; they are the
distilled lessons of every burst analyzed so far — read the skill for a step **before**
running that step, and treat its rules as binding:

- `SpectralFitting.md` — the flagship (lessons L1–L25). Non-negotiables: margins over
  `*_VALID` fits only; ΔAIC reported as an evidence ratio; blind-first ordering.
- `Temporal.md` — carries a **defect ledger**; do not quote `temporal_catalog_human.ecsv`
  numbers without checking it.
- `Binning.md`, `DataInventory.md`, `GCNIntelligence.md`, `detector/background/source
  _selection.md`, `qc_flagging.md`.

**Rules that protect the science (never bend these):**
- Approved catalogs (`results/background_intervals.ecsv`) are **read-only** — changes go
  through the GUI gate and carry `APPROVED_BY/APPROVED_UTC/WINDOW_SOURCE` stamps. Never
  fabricate an approval.
- Fits start **blind** — never tune a fit toward a published number. Compare *after* freezing
  your numbers.
- A railed parameter is a failed fit, not a measurement. A skipped check is a fake pass.
- Authoritative re-runs use a **fresh out-root**; never overwrite a gated product.

## 3. How to add a skill (or a lesson)

Lessons are the project's real product. When you learn something the pipeline should never
forget:

1. **A lesson = a CLAIM + a TEST.** Write the claim into the relevant skill file as the next
   `### Lxx` entry (copy the format of an existing one: title, burst + date it came from,
   the evidence, the RULE). If the claim can be checked against tables on disk, add a test to
   `tests/test_lessons.py` named `test_Lxx_...` and reference it from the lesson.
2. Number sequentially — check the current highest `Lxx` in the file first (collisions have
   happened).
3. A brand-new workflow becomes a new skill file following the same shape:
   `Purpose / Inputs / Outputs / Phases (with concrete commands) / Quality checklist /
   Common pitfalls / Hand-off`. Put it in `dev/ai_guides/` and add a row to the step ledger
   in `BurstWalkthrough.md`.
4. Submit as a **pull request** (branch → PR), with the burst and evidence that produced the
   lesson in the PR description. Skills are reviewed like code — because they are code for
   humans and AIs alike.

## 4. How to raise an issue

Open a **GitHub Issue** on this repo. Include, always:

```
Burst:      bn<XXXXXXXXX>  (or "general")
Step:       0–9 (ledger step) or script name
Command:    the exact command you ran
Expected:   what should have happened (cite the skill rule if one applies)
Actual:     what happened — paste the error / the wrong number
Log:        path to the log file (results/<root>/<burst>/logs/...)
Version:    git commit hash (`git rev-parse --short HEAD`)
```

Label it:
- `bug` — the code did the wrong thing
- `frame-difference` — our number differs from a paper's but the setups differ (say how)
- `lesson-proposal` — you think this should become an `Lxx` + test
- `data` — missing/corrupt data product, DRM validity, version problems

Two useful precedents: a **negative nested LRT** or a **parameter at its bound** is always
reportable (the engine should have stamped it — if it didn't, that is itself a bug); and
"my number disagrees with a published one" is an issue **only after** the L21 frame-alignment
checklist (Ep vs Ec convention, sign convention, band, interval + T0, detector set).

## 5. Current collaborator tasks

- **Notebook verification** (Khushboo): the executed notebooks in `notebooks/verified/` are
  the human-checkable mirror of the multi-core pipeline — verify LLE+LAT handling and the
  literature-verdict fields per burst.
- **Expert-2 benchmark arm** (Khushboo): the 25-burst benchmark (`results/benchmark/`) needs
  an independent second human's Stage-1 decisions — *without* looking at Expert-1's. This is
  the denominator for the agentic paper and the Sept 7 talk.
- Questions → open an Issue with the `question` label, or email Vikas
  (vikas.chand.physics@gmail.com).

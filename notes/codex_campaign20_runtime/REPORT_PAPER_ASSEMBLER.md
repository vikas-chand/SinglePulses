# Campaign-20 report and paper assembler

Authority: producer-side orchestration only. The helper does not fit data,
verify figures, edit approved selections, or read legacy nested sweep fits as
a scientific fallback.

## Commands

Production build at a completed burst boundary:

    python notes/codex_campaign20_runtime/assemble_report_paper.py build \
      --trig bn081224887

Queue-ordered bookkeeping after reviewing the recommended boundary status:

    python notes/codex_campaign20_runtime/assemble_report_paper.py bookkeep \
      --trig bn081224887 --status PARTIAL --wall-clock "12 h 08 min"

Read-only preflight:

    python notes/codex_campaign20_runtime/assemble_report_paper.py dry-run \
      --trig bn081224887

Explicit write-scope display:

    python notes/codex_campaign20_runtime/assemble_report_paper.py scope \
      --trig bn081224887

## Scientific read contract

The adapter reads only:

- the trigger rows in `results/background_intervals.ecsv` and the adopted
  `results/sweep106/TRIGGER/blocks/bb_blocks_spectral_TRIGGER.ecsv`;
- exactly one content-addressed P1 promotion receipt whose ECSV/JSON hashes
  match the current canonical pair, plus its validated family-merge manifest;
  the model columns must be in the exact scripts/10 HIGHE order asserted by
  `campaign_products.HIGHE_PREFIXES`;
- results/convention_check/TRIGGER/spectral_fits.ecsv and spectral_fits.json;
- results/sweep106/TRIGGER/p2_temporal_summary.json;
- results/convention_check/sed_grid_TRIGGER/sweep_summary.json and the P3
  panel sidecars named by that closure; every named PNG/PDF/JSON triplet is
  freshly revalidated and hash-recorded at assembly time;
- results/convention_check/sed_grid_TRIGGER/p4_products_summary.json and only
  the montage, parameter-evolution, and all-model-table artifacts named and
  hash-bound by it.

Legacy spectral fits and reports are never numeric fallbacks. Campaign builds
fail closed to canonical source/output paths and mandatory compilation; path
overrides and `--no-compile` are fixture-only. The queue-order guard runs
before script48 or any campaign write.

The build first invokes the brief-exact command
python scripts/48_burst_report.py --trig TRIGGER. Its known absent-output-path
warning and return code are archived in script48_exact.log. That legacy
invocation is not used as scientific authority; the adapter report records
the deviation explicitly.

## Write contract

Build may write only:

- results/sweep106/TRIGGER/REPORT_TRIGGER.md;
- paper/GRBYYMMDD/main.tex and the unchanged burst-2 refs.bib;
- paper/GRBYYMMDD/figs PNG copies selected by fresh sidecars;
- paper/GRBYYMMDD/staging_manifest.json and script48_exact.log;
- LaTeX build files main.aux, main.bbl, main.blg, main.log, main.out,
  compile.log, main.pdf, and GRBYYMMDD.pdf.

Bookkeeping may additionally change exactly:

- notes/CODEX_CAMPAIGN20_MANIFEST.md;
- notes/CODEX_CAMPAIGN20_PROGRESS.md;
- results/sweep106/TRIGGER/VISION_QC.md.

It never writes scripts, dev/ai_guides, approved catalogs, other bursts,
Git metadata, or a verifier verdict.

P6 revalidates every source, staged figure, helper implementation/argv,
script48 log, report, TeX file, bibliography, compile log, final LaTeX log,
and (after successful compilation) both PDFs against `staging_manifest.json`. It writes the
progress and producer VISION_QC blocks idempotently, then updates the campaign
manifest row last as the final commit marker.

## Verification performed on the non-campaign fixture

On 2026-08-16, fifteen unit tests passed against the completed GRB 081222 fit and
temporary P2 fixtures. A read-only dry-run rendered the Markdown and TeX in
memory with zero writes. Tests cover partial-but-quotable P2 timing, Bala
limits, Haar uncertainties, asymmetric T90 precedence and lower-limit prose,
TeX-safe comparison symbols verified through PDF text extraction, the exact
HIGHE registry, campaign path guards, atomic stale-figure replacement,
failed-build PDF cleanup, explicit missing-figure notices, and
multipage-capable 35-row winner-table output. A separate
temporary-directory fixture build:

- captured the exact scripts/48 warning and exit;
- completed pdflatex, bibtex, pdflatex, pdflatex with return codes 0,0,0,0;
- produced a six-page searchable GRB081222.pdf with all four return codes
  recorded and no undefined references/citations or overfull boxes;
- was rendered with Poppler and visually inspected for clipping, overlap,
  missing glyphs, comparison-symbol corruption, and table placement.

No campaign-burst report, paper, manifest row, progress block, or VISION_QC
entry was created by these tests. All future campaign figures remain
UNGATED pending independent Claude verification.

Declared campaign-wide P5 deviation: the PDF artifact-operation marker was
successfully run once before fixture authoring with expected output count one
for that fixture, rather than the final campaign count of 20. A duplicate
marker call is forbidden; every report and paper records this deviation.

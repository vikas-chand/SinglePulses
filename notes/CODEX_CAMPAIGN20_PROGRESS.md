# Codex 20-burst campaign progress — bursts #3–#22

Run date: 2026-08-16  
Role: PRODUCER (Codex GPT-5.6 Sol Ultra)  
Working directory: `/Users/salim/Desktop/Projects/SingleRest/Two_Breaks`  
Verification state: every newly generated figure is **UNGATED** pending independent Claude verification.

## Campaign initialization — 2026-08-16

- Ran `python scripts/00_inventory.py` before production. Existing repository tools cover every requested stage; no replacement script will be built.
- Read the binding runbook, `AgentArchitecture.md`, `FigureVisionQC.md`, `Temporal.md`, both completed papers, burst #2's defect ledger, and `BurstWalkthrough.md` before starting P1.
- Read the `grb-two-shock-analysis` and `scientific-draft-writing` skill instructions and the relevant methods, detector/LAT, low-energy-break, prose, GRB-writing, and caption contracts.
- The requested direct `scripts/10_spectral_fit_burst.py` path will be used. `scripts/29_refit_clean.py` will not be retried because its sandbox `SC_SEM_NSEMS_MAX` failure is already established.
- No pre-existing campaign manifest existed. This file and `CODEX_CAMPAIGN20_MANIFEST.md` were initialized before the first fit.
- Producer/verifier separation is active: producer-side ledgers record invocations and anomalies only. Verdict lines remain for Claude-side verifiers.

### Campaign-wide 16-core launch and declared implementation details

- P1 was expanded into the complete 80-pair `(burst, family)` worklist before
  launch.  Each invocation writes to an immutable
  `results/convention_check/<TRIG>/family_runs/<family>/` directory.  A FIFO
  token bucket holds 16 independent one-core `scripts/10` processes in flight;
  this follows the brief's controlling 16-core ruling (the older 12-slot text
  in its illustrative snippet is superseded).
- The four complete, schema-valid burst-3 first-pass family artifacts were
  reused.  Its still-required `highe_retry` was added as the 81st work item;
  the already-complete `shape_retry` and `threecomp_retry` remain immutable and
  will be included in the deterministic repair merge.
- The pool uses `MPLBACKEND=Agg` and one-thread limits for OMP, OpenBLAS, MKL,
  NumExpr, and Accelerate.  The already-running first-pass shell emits
  `nice(5) failed: operation not permitted` whenever it backgrounds a new
  worker because that shell parsed the runner before `BG_NICE` was disabled;
  jobs continue normally and logs advance.  `BG_NICE` is disabled in the
  on-disk runner for later retry waves.  This is a shell scheduling warning,
  not a fit degradation.
- The live burst-3 `highe_retry` exposed a campaign-wrapper defect: its private
  `PFILES` value initially omitted the read-only Fermitools system parameter
  fallback, so LAT preparation in blocks 1--3 logged
  `ParFileError: .par file gtbin.par not found.` Those same three blocks were
  `TOO_FEW_EVENTS` in the immutable first pass, so the fit plugin set was not
  changed. The wrapper now uses `<private>;$FERMI_DIR/syspfiles`; system `.par`
  files were also pre-seeded into the not-yet-started burst-20 directories and
  the active burst-3 retry directory. The exact initial failures remain in the
  log and are a declared infrastructure deviation, never silently erased.
- A preflight found a structural response-coverage failure for
  `bn100130729`: its approved source is `[58,97]` s and all adopted blocks lie
  at `62.24--81.15` s, whereas every approved detector's RSP2 begins near
  `+139.27` s.  This burst remains `RESPONSE_BLOCKED`; the family calls are
  retained as exact failure evidence, but no legacy response collapse or
  unstamped window change will be substituted.  New DRMs are outside this
  campaign's authorized product-only scope.
- Campaign-owned orchestration/validation helpers live only under
  `notes/codex_campaign20_runtime/`; no repository analysis script, approved
  catalog, or other burst output has been edited.  The helpers do not change
  likelihoods or estimators: they enforce the 16-slot shell transport,
  immutable family outputs, retry-once evidence, no-model-dropped accounting,
  and transactional promotion of the merged table.
- Before the first temporary paper-fixture PDF compile, the report producer
  successfully emitted the PDF workflow's required one-time artifact marker:
  `--operation-kind create --expected-output-count 1 --output-format pdf`.
  The count described that one fixture rather than the 20 final campaign PDFs;
  this count mismatch is declared here. The workflow forbids a duplicate
  marker, so none will be emitted for the later campaign builds. Final papers
  will still receive render/text/layout QA, while their scientific figures
  remain UNGATED pending independent Claude verification.

## Burst #3 — `bn081224887` (GRB 081224) — IN PROGRESS

### P0 — frozen-input boot — COMPLETE

- Approved Stage-1 rows were adopted without re-selection: `n6,n7,n9,b1,lle`; human GUI approval by Vikas Chand at `2026-07-19T22:18:36Z`; background `[-24,-8]` and `[40,140]` s; source `[-1.280220979,20.164881119]` s.
- The frozen block table contains nine unique blocks (`27` detector rows) spanning `[-0.160979018,20.164497972]` s.
- No measured redshift is recorded. Existing reconciliation identifies a single FRED pulse and notes that the historical LAT detection claim was retracted.
- Data inventory nevertheless contains LLE (`gll_lle`, CSPEC, response, pointing) and LAT EV+SC files under `data/bn081224887/LAT/`. The campaign's EVERY BAND rule is based on data availability and quality, not detection significance.
- **Declared correction to the earlier burst-3 attempt:** the earlier progress note proposed omitting `--include-lat` because the historical detection was retracted. The current campaign brief explicitly requires `--include-lat` on every family. That earlier inference is superseded; all new P1 calls will request LAT. Any LAT build failure will be preserved verbatim and reported as a declared degradation.
- Existing legacy products remain reference context only. No new-convention `results/convention_check/bn081224887/spectral_fits.ecsv` existed at this boot.
- What remains: P1–P6. All figures remain UNGATED.

### P1 resume audit and sandbox environment — 2026-08-16

- The resumed default-family artifact was initially misclassified from its JSON
  `fit_dets` field. That field records only the prebuilt GBM/LLE plugins; LAT is
  attached per block and is recorded in the table's `PLUGIN_DETS` column.
- Artifact evidence proves the existing default family is valid and used the
  required LAT request: blocks 0, 4, 5, and 6 contain `LAT`; the other five
  resolved blocks had no selected LAT events and remained GBM+LLE. T_INT is
  GBM+LLE because the current engine does not attach LAT to the integrated fit.
  The ECSV has 10 rows, six default models, all 60 statuses `OK`, and SHA256
  `b64d4184dcb9b9523576d56575c1ac661fdab6a5597f41447925122ffda9e5aa`.
- A redundant default rerun was launched while resolving this provenance and
  deliberately interrupted after the prior artifact was proven byte-for-byte
  valid. It did not reach the save step, so the resumed table was not changed.
- Two earlier startup attempts failed before fitting: first at the read-only
  astromodels home log, then at the Numba cache locator. The campaign now uses
  `notes/codex_campaign20_runtime/` plus writable `MPLCONFIGDIR` and
  `NUMBA_CACHE_DIR` paths under `/private/tmp`. This is a declared sandbox-only
  environment workaround; no analysis script or scientific input was changed.
- The required stdout confirmation was observed: `LLE data present — using
  APPROVED LLE bkg window`. P1 continues with `shape`, `highe`, and
  `threecomp`; every family call retains `--include-lat`.

### P1 shape-family mandated retry — 2026-08-16

- The isolated `shape` retry saved a readable 10-row ECSV and JSON after
  1223.02 s. It contains the expected eight models; 77/80 model-row statuses
  are `OK`.
- `DSBPLfree` failed again in blocks 0, 4, and 5. These are declared second
  failures and will remain explicit in the final 24-model table; no further
  retry is authorized by the campaign brief.
- LLE used the approved `[-24,-8]` and `[40,140]` s background windows and is
  present in every row. LAT was attached in blocks 0, 4, 5, and 6 (one selected
  event in each) and skipped as `TOO_FEW_EVENTS` in blocks 1--3 and 7--8.
- After saving both fit artifacts, the command exited with status 1 while
  constructing a Matplotlib Tk toolbar (`ValueError: height and width must be
  > 0`). This is a declared post-save plotting failure, not a fit-table loss;
  all figures remain UNGATED and the later product phase will regenerate the
  requested figures independently.

### P2 sandbox preflight — 2026-08-16

- Direct constructor tests established that `ProcessPoolExecutor(1)` raises
  `PermissionError` at `SC_SEM_NSEMS_MAX` in both the threeML and dedicated MVT
  interpreters. Therefore script 46 and the canonical Bala worker cannot use
  their process-pool transport in this managed sandbox, even with one worker.
- `multiprocessing.Pool(1)`, used by script 47, succeeds and requires no
  workaround.
- Added an opt-in, campaign-owned transport shim to
  `notes/codex_campaign20_runtime/sitecustomize.py`. Only when
  `CODEX_CAMPAIGN20_THREAD_EXECUTOR=1` is set does it map
  `ProcessPoolExecutor` to `ThreadPoolExecutor`; estimator functions, inputs,
  task ordering, and one-worker concurrency are unchanged. The shim was tested
  in both interpreters and has SHA256
  `dd9001bc275e4e9a3673957897c1208d42e509c1ad999969d3060c91473ae37c`.
- The MVT interpreter's live `pip freeze` exactly matches its lockfile SHA256
  `22b63c5885aee9ffc7709f664108f76e0c45595d39fb1166116e8baf96535259`.
- The constructor preflight is the retained exact failure evidence; the
  prescribed script-46 CLI will be invoked once with the opt-in transport shim
  already active rather than spending a campaign call on the same known
  executor-construction failure. The Bala command uses absolute project paths,
  correcting the brief's `$PWD` expansion after changing into the Handbook
  repository. These are declared sandbox and command-path deviations, not
  scientific-method changes.
- The required default `scripts/44` command runs first. Because its step-9
  resolver points at a legacy nested fit, the controller then performs one
  extra SHA-bound `scripts/44` render in temporary expected-layout staging and
  promotes only the current-fit step-9 PNG; this supplement occurs between
  prescribed commands 2 and 3. The five non-spectral step figures receive a
  separate current-run receipt, so burst #12 can retain them without a spectral
  table. No scientific figure is thereby verified.
- The Bala CLI additionally pins `--inner-cores 1 --seed 20260718 --resume`.
  These flags make the one-core sandbox execution and deterministic engine
  identity explicit; the normalized result still accepts only the engine's own
  `result.json` selection and never reselects a preferred CSV row.
- An independent pre-launch audit froze the P2 controller at SHA256
  `9a573aa4095dc5c02e18acab07e8c3144f0f60d54fbb228396477eb5340233b0`;
  14 targeted tests, 30 campaign-runtime tests, compilation, and read-only live
  CWT/lag/Bala/temporal schema checks passed. Each phase receipt includes this
  self-hash, so any later controller edit forces a rerun rather than silently
  reusing products.

### P3 no-model-dropped preflight — 2026-08-16

- The frozen nonblocked roster contains 4,464 requested pairs: every one of the
  24 registered models for T_INT plus every resolved bin. Burst #12 contributes
  no runnable pair because its canonical P1 table is structurally unavailable.
- The global two-attempt, 16-token launcher now binds every accepted panel to
  the current engine SHA/argv, promoted fit and block interval, plugin context,
  fresh mtimes, AIC (within 0.1), and PG-statistic. Invalid second-attempt files
  are moved to a recoverable quarantine so montage/report globs cannot treat
  them as products.
- `scripts/41c` cannot replay the required LLE/LAT likelihood for bursts #3 and
  #20. Their pairs will still receive both prescribed attempts, then close as
  `STRUCTURAL_COVERAGE_MISMATCH`; no GBM-only panel will be accepted merely
  because its stored AIC happens to match. This is an expected, declared P3
  degradation, not a dropped model.
- Independent audit plus local rerun: 46 campaign-runtime tests passed; zsh
  syntax and Python compilation passed. Frozen SHAs are
  `56f3c5b0324d45a5a2564914cfe9e51f403ea6c6e7a0c8a84b8bed2f74f5bbd0`
  (controller),
  `2827762e361d2ee487d485378d7128127c06cc46b695afb452ea9693918ad5a8`
  (16-slot launcher), and
  `d6cb37d09a2daadef477c5842da8b93480db4b68d15fdeac4c92cbdeb4e9038e`
  (classified montage fallback). This supersedes the pre-audit fallback hash;
  the P4 audit hardened current-P3 authority checks and froze the replacement
  before any campaign P4 product was launched.

### P4 product-runner preflight — 2026-08-17T01:54:42Z

- An independent audit completed before any campaign P4 launch. The frozen
  controller enforces the current promoted P1 receipt, current two-attempt P3
  closure, exact 24-cell montage accounting, and rejects stale parameter files.
- `bn100130729` remains an explicit response-blocked `PARTIAL`; it cannot be
  converted into a spectral success by a legacy table or figure.
- The audited P4 files compile successfully. Frozen SHA-256 values are
  `fc064ece929c76540c23e0e73b1903086d7f5dea1ce873932d0216fb5a2eeaf8`
  (`run_p4_products.py`),
  `d6cb37d09a2daadef477c5842da8b93480db4b68d15fdeac4c92cbdeb4e9038e`
  (`repair_sed_montage.py`), and
  `8e7208a8927b2fd10cb5fbd3111090cab90ccd86fa253a7a32798b4a5a70d895`
  (`p4_table_adapter.py`).

### P1 highe and threecomp first passes — 2026-08-16

- `highe` saved a readable 10-row, 24-model ECSV/JSON after 5115.62 s.
  The seven failed cells are `DSBPLfree` in blocks 0, 4, and 5;
  `Band+CPL`, `CPL+CPL`, `Band+RCPL`, and `SBPL+PL` in block 4. All other
  statuses are `OK`.
- `threecomp` saved a readable 10-row, 18-model ECSV/JSON after 4730 s.
  Its five failed cells are `Band+PL` in T_INT; `Band+CPL`, `Band+PL`, and
  `SBPL+CPL` in block 4; and `CPL+PL` in block 7.
- Both calls used approved LLE backgrounds and contain `lle` in every row.
  Both attach LAT in blocks 0, 4, 5, and 6 (one selected event per block) and
  skip it as `TOO_FEW_EVENTS` in blocks 1--3 and 7--8. T_INT is GBM+LLE because
  the engine's current integrated-fit path does not attach LAT.
- Both commands aborted only after writing ECSV/JSON, during macOS Tk/AppKit
  diagnostic-plot construction (exit 134). This repeats the shape retry's
  post-save plotting defect and does not erase the fit tables. All diagnostic
  figures remain UNGATED and will be regenerated in P4.
- A streamed-log suspicion that LAT nuisance parameters survived a skipped
  block was checked by exact marker segmentation and disproved. Skipped blocks
  contain no LAT diffuse parameters or template builds. The real nonfatal LAT
  warning is inability to write `/Users/salim/pfiles/gtselect.par-*`; event
  gating and plugin construction still completed.
- Required retries: the shape retry already established the three
  `DSBPLfree` cells as repeated failures. A `threecomp` retry is running for
  the three-component failures. A `highe` retry is required for the
  highe-specific `Band+RCPL` failure before P1 can close.
- SHA256 bindings: highe ECSV
  `264e9563ea2950ac38c6f41e4d92931739bb5fcfd13e6c7ce275cbbaee9c0065`,
  highe JSON
  `380c0784b6dba6b56cb5723bd6b418c768f7fa6d37a611a761085162a141ef36`,
  threecomp ECSV
  `f8581a48c04ef6c0a400688c73022b55903e8a6136b83e0592b36d85f09c5de5`,
  threecomp JSON
  `ac3cf7d2f4b98db3afaade1f739a8aa9adf94479cd9e55ca1d662ae5d0aebde4`.

### P1 threecomp mandated retry — 2026-08-16

- The isolated retry saved a readable 10-row, 18-model ECSV/JSON with correct
  LLE in every row and LAT only in blocks 0, 4, 5, and 6.
- All five first-pass failures repeated exactly: `Band+PL` in T_INT and block
  4; `Band+CPL` and `SBPL+CPL` in block 4; and `CPL+PL` in block 7. No further
  threecomp retry is authorized. In the highe-base repair, `Band+CPL` block 4
  therefore remains a declared unresolved model-bin pair.
- Retry hashes: ECSV
  `c1bee23160480e63fb738dcf836046689248ed6b948052988c9909d878411c14`;
  JSON
  `ac3cf7d2f4b98db3afaade1f739a8aa9adf94479cd9e55ca1d662ae5d0aebde4`.
- The command took 4204 s and again exited 134 only after saving, in the same
  macOS Tk/AppKit diagnostic-plot path. The serialized fit artifacts remain
  the scientific result; the plotting abort is a repeated infrastructure
  defect.

### P1 highe mandated retry — 2026-08-16

- The global 16-slot pool completed the required `highe_retry` with a readable
  10-row, 24-model ECSV/JSON. All seven first-pass literal failures repeated:
  `DSBPLfree` in blocks 0, 4, and 5, plus `Band+CPL`, `CPL+CPL`, `BandR+CPL`,
  and `SBPL+PL` in block 4. No further highe retry is authorized.
- Approved LLE was present in every row. LAT was attached in blocks 0, 4, 5,
  and 6, exactly matching the immutable highe context. Blocks 1--3 logged the
  already-declared temporary `gtbin.par` environment error; after the private
  Fermitools parameter directory was repaired, blocks 7--8 correctly reported
  `TOO_FEW_EVENTS`. Thus the row-level likelihood/plugin context is unchanged.
- The engine saved both fit artifacts, then returned 1 in the same Tk toolbar
  diagnostic-plot path even though the wrapper exported `MPLBACKEND=Agg` and
  the script calls `matplotlib.use('Agg')`. The pool's independent artifact
  validator therefore marked the fit COMPLETE with `engine_rc=1`; the missing
  engine diagnostic plot is not treated as a spectral-fit failure, and all
  later figures remain UNGATED.
- The eventual repair merge may replace only literal highe `FAIL` cells with
  finite `OK` results from context-identical family attempts. It may not shop
  among successful optimizer results. A content-addressed stage and promotion
  receipt will record the surviving failures after the global retry wave.

### P1 audited retry queue extension — 2026-08-17T01:58Z

- A read-only frozen-helper audit covered the 13 bursts whose four initial
  families had closed. It found 17 required family retries from literal
  `STATUS=FAIL` cells; `bn081224887 highe_retry` was already complete, so the
  remaining 16 unique jobs were appended behind the final initial job in the
  live FIFO worklist. This preserves the ruled 16-way shell utilization while
  initial and already-provable retry work remain.
- This is an explicit dynamic worklist extension, not an optimizer-driven model
  choice. The worklist SHA-256 changed from
  `8123c3233006690813dccddd09a1bf23c1bcaad4bb14747b609bd3bc3f99bcfb`
  to
  `222e4de1c3640141eb9d542e995219c1b859bf783c362e269528cd493970bb02`.
  Later-completing bursts will be audited separately; no family may receive
  more than its one mandated retry.
- The audit also exposed a provenance limitation for reused #3 initial
  families: their sidecars/tables prove LLE and LAT plugin coverage, but their
  original stdout logs are absent. The current `highe_retry` log independently
  proves `--include-lat` and the approved-LLE message. The gap remains declared.
- A later incremental audit found one eligible `bn110605183 threecomp` retry
  (`CPL+CPL`, block 0). It was appended before the live reader reached EOF;
  the worklist SHA-256 is now
  `fe877d782b238ee7b39c197bf0160491f77d6d2a4e148bbb5fcb388375843caf`.
- The fully closed `bn110928180` audit then authorized `highe_retry` (7
  literal failed cells) and `threecomp_retry` (12 literal failed cells). Both
  were appended exactly once; the current live-worklist SHA-256 is
  `8a6c475e3fb70ec6980e922364664ad27e247f31cbc79ac16e67018eadfe8831`.

### P1 early fail-closed promotions — 2026-08-17T02:17Z

- `bn101225377` and `bn110618366` had all four initial families complete, no
  literal failed model cells, and no authorized retry. They were staged and
  atomically promoted while the independent 16-slot fit pool continued.
- The promoted tables pass the requested exact-24-model assertion: 4 rows for
  `bn101225377` and 5 rows for `bn110618366`, with zero failed cells. Promotion
  fingerprints are
  `064de0e3e45a214a16f1a3fd056e4329f80c8af3a9ba95acb9a608e897bda36e`
  and
  `5240a23a14d43ea60ed29d4539bc3b21fd8d6b2ba198cdd955e84d1f7fa38dc8`,
  respectively. All numbers remain provisional and figures remain UNGATED.

### Resume audit and newly declared tooling deviations — 2026-08-17T03:39Z

- The PI's 85-burst scope is interpreted as the queue entries with an adopted
  block table under `results/sweep106/<trig>/blocks/`: 22 through queue item
  #22 and 63 later entries. The nominally excluded 21 also have block tables
  elsewhere (`results/clean_blocks/` and their REVIEW_INDEX product roots), so
  “lack a block table” is not literally true of the current tree. This path-
  scoped roster choice is declared; no block table or catalog was changed.
- The supplied `dev/merge_campaign_families.py` has a material NR-8 follow-on
  defect: it ignores `threecomp`, keeps the default-family `BEST_*` summaries
  and six-model JSON sidecar, and treats any pre-existing 24-model ECSV as
  complete without binding its inputs. The brief-exact command was still run
  for ready bursts and its 24-model assertion passed, but science/reporting
  must recompute winners across all 24 `STATUS=OK`, `VALID=true` cells. The
  campaign report adapter does this independently and never trusts merged
  `BEST_AIC_MODEL`; no repository script or dev tool was edited.
- Native `scripts/41d`/`41e` call the lowest finite-AIC model the display
  winner without applying `STATUS` or `VALID`. Their figures therefore carry
  a raw-AIC display convention, distinct from the engine-valid winner used in
  the report and census. This distinction must appear in every paper; an
  invalid red-framed montage cell is not a physical winner.
- The brief-exact `scripts/48_burst_report.py --trig` invocation is not a safe
  report source: it catches its `out=None` failure and exits zero, and its
  legacy path also trusts stale merged summaries and the quarantined handbook
  lag. It will be archived as required; the content-addressed campaign adapter
  is the report authority.
- `scripts/44` emits no one-sidecar-per-figure provenance and its default
  step-9 lookup points to the legacy nested fit. The P2 controller's hash-bound
  bundle receipt and current-fit step-9 supplement mitigate, but do not erase,
  the standing-contract sidecar deviation. Every figure remains UNGATED.
- The first resumed P2 run (`bn090530760`) invoked the prescribed CWT tool while
  the Claude P1 pool was active. That tool silently hardcodes a 12-process pool
  and has no worker flag, so this one invocation exceeded the temporary
  four-core producer budget even though it was one top-level job. This is a
  brief violation and is not repeated: further CWT phases wait for the P1 pool
  to finish (or require an explicitly declared transport-only CPU cap).

### Burst #4 early P2 evidence — `bn090530760` — 2026-08-17T03:39Z

- Temporal catalog and six default step figures completed with fresh receipts;
  the step-9 panel was separately regenerated against the current 24-model
  table. These are producer products and remain UNGATED.
- Global CWT returned no finite threshold crossing (`NaN +/- NaN`); it is a
  non-measurement, not a number to quote.
- Canonical Bala MVT failed exactly with `no complete approval group in
  catalog`. The adopted `b0` post-background starts near +33.24 s while the
  adopted source interval ends near +169.24 s, so the wrapper refuses the
  overlapping approval group. Stage 1 remains adopted and unchanged; MVT is
  reported missing for this burst unless the PI later reopens that decision.
- The temporal-figure phase is still running at this checkpoint. Burst #4 has
  not reached a report/bookkeeping boundary, and queue item #3 remains the
  first report boundary.
- A fail-closed staging preflight then showed that P1 itself is not closed:
  the initial `threecomp` family has one literal `Band+CPL` failure in block 4,
  while its mandated retry was killed before producing a terminal artifact in
  the earlier session. The supplied three-family merge did not detect this.
  No report/P3 product will treat the current table as promoted authority; the
  one missing family retry is deferred until the active Claude pool finishes,
  as the division-of-labour ruling requires. The current P2 timing products
  remain reusable, but its spectral step-9 receipt must be refreshed after the
  eventual content-addressed P1 promotion.

### Burst #4 P2 terminal state — `bn090530760` — 2026-08-17T03:44:44Z

- The prescribed six-phase P2 controller reached a fail-closed terminal state:
  temporal catalog, step figures, and the independent LATBright lag phase are
  complete; CWT, Bala, and the composite temporal-figure validation are failed.
  This is an incomplete temporal suite and no missing estimator is replaced by
  a legacy value.
- The global CWT computation completed its 10,000 trials but found no finite
  crossing (`NaN +/- NaN`). The canonical Bala wrapper failed before an
  estimator result because the adopted approval group is internally
  incompatible for that engine (`no complete approval group in catalog`).
- The validated window-scan lag is provisional
  `+3.49899 -0.24671/+0.25517 s`, with positive defined as soft photons lagging
  hard photons. The three scanned fit windows gave `+4.10390`, `+3.49899`, and
  `+3.15139 s`; the reported window systematic is `0.47625 s`, in addition to
  the statistical interval. The 25--50 versus 100--300 keV CCF peak is 45.83
  sigma. This is the reportable lag; the handbook value remains quarantined
  because its sign convention is inverted.
- The temporal catalog reports provisional windowed `T90 = 134.2935 s` with
  asymmetric Monte-Carlo errors `-0.7937/+1.3506 s`. Although the formal
  window-truncation flag is false, the tail outside the estimator window is
  significant (`5.90 sigma`), so the duration is conservatively treated as a
  window-limited/lower-bound diagnostic under `Temporal.md` rather than an
  unconstrained physical duration. Haar is only an in-chain upper limit,
  `<8.01566 s`.
- Every P2 figure remains
  `UNGATED_PENDING_INDEPENDENT_CLAUDE_FIGURE_VERIFICATION`. Burst #4 is still
  not at a report boundary because its one mandated P1 family retry has not
  closed.

### Burst #12 structural response exclusion — `bn100130729` — 2026-08-17T03:46Z

- The adopted sweep block table does exist despite the REVIEW_INDEX display:
  three unique bins span `62.237--81.154 s` inside the approved source
  `[58,97] s`.
- Every approved detector's available RSP2 matrices instead covers roughly
  `+139.267--+475.145 s`, wholly outside the source and blocks. This is the
  documented `RESPONSE_UNCOVERED` condition. P1, the current-fit spectral step
  figure, P3, P4 spectral products, and a complete paper cannot be produced
  until DRMs are regenerated; an ordinary family retry or a legacy-table
  substitution would be scientifically invalid.

### Pooled low-core P2 preparation — 2026-08-17T03:49Z

- While the Claude 16-way P1 pool remained active, producer work stayed within
  the temporary four-core budget. For the already content-addressed/promoted
  P1 tables of `bn101225377` (#17) and `bn110618366` (#19), ordered P2 phases 1
  and 2 completed in parallel: a fresh one-worker temporal-catalog row, the
  brief-required step figures, and the SHA-bound current-fit step-9 supplement.
- The high-core CWT phase and all later phases remain deliberately unstarted
  for both bursts until the fit pool releases the machine. Every generated
  figure is a producer artifact and remains UNGATED.
- The first import-only launcher attempt failed before running either phase
  because Python 3.9 dataclass resolution requires the dynamically loaded
  module to be present in `sys.modules`. The corrected launcher inserted the
  module and both runs completed. The failed attempt wrote no scientific
  product; this is a declared orchestration retry, not an estimator retry.

## 2026-08-16 ~23:30 — CODEX USAGE LIMIT (locked out until Aug 19 23:32)
Codex hit its OpenAI usage cap mid-campaign; every relaunch errors. Division of
labour amended by necessity: Claude now runs the FULL chain (fits via the v2
one-invocation pool + merges/temporal/grids/montages/tables/reports via
dev/campaign_products_driver.sh). Producer/verifier separation is preserved via
fresh-context Claude verifier agents (the bursts-1/2 pattern). Codex resumes as
external auditor when its quota returns.

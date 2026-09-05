# Campaign-20 P2 runner contract

`run_p2_temporal.py` is the campaign-owned controller for bursts #3–#22. It
runs one burst completely before the next and restores the brief's queue order
even if `--triggers` is supplied out of order.

## Commands

```bash
/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p2_temporal.py plan \
  --triggers bn081224887

/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p2_temporal.py run \
  --triggers bn081224887

/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p2_temporal.py validate \
  --write-summary --triggers bn081224887
```

`run` is resumable: a phase is reused only when its previous status is
`COMPLETE`, its command/CWD/shim/controller/dependency hashes are unchanged,
its content-bound input fingerprint is current, and its artifacts still
validate. A producer return code cannot be hidden by an older valid-looking
artifact: newly executed phases require fresh output mtimes, and the normalized
summary requires all six current phase receipts. `--force` reruns all six
phases. Bala itself always receives
`--resume --seed 20260718 --inner-cores 1`.

The `ProcessPoolExecutor` to `ThreadPoolExecutor` transport shim is enabled for
scripts/46 and Bala only. Every invocation has `PYTHONHASHSEED=0` and one-thread
BLAS limits. No estimator, seed, selection, or scientific result is changed by
the controller.

## Artifacts

- `results/sweep106/<trig>/p2_temporal_summary.json` uses schema
  `codex_campaign20.p2_temporal_summary.v1`.
- `results/sweep106/<trig>/<trig>_temporal_catalog_row.source.json` freezes the
  newly produced row from the shared 106-row temporal catalog. Later per-burst
  catalog merges therefore do not invalidate an earlier burst's provenance;
  the receipt still requires the current row to equal the frozen row.
- `results/sweep106/<trig>/<trig>_step44_nonspectral.source.json` binds all five
  non-spectral outputs from the exact default scripts/44 invocation and refuses
  a pre-existing file whose mtime predates that invocation.
- `results/sweep106/<trig>/<trig>_step9_qc.source.json` binds the promoted
  step-9 PNG to the SHA-256 of
  `results/convention_check/<trig>/spectral_fits.ecsv`.
- `logs/codex_campaign20/p2/<trig>/<NN>_<phase>.status.json` uses schema
  `codex_campaign20.p2_phase_status.v2` and records command, CWD, return code,
  shim state, controller/dependency hashes, content-bound input manifest, log,
  elapsed time, and validation errors.
- `logs/codex_campaign20/p2/status/<trig>.json` is the burst-level status.

The normalized summary has these top-level fields:

```text
schema_version, trigger, generated_utc, producer, provisional, complete,
figure_gate_status, figure_verifier, t90, mvt, lag, pulse, artifacts,
reporting_rules
```

`mvt` always separates `canonical_bala`, `noncanonical_cwt`, and
`noncanonical_haar`. The controller never chooses a preferred CSV row: the
canonical value is read only from Bala's `result.json`. The lag object always
contains both asymmetric statistical errors and the half-range fit-window
systematic. `t90.lower_limit` is true when the estimator reaches the window
edge or when `TAIL_OUTSIDE_WINDOW_SIG >= 3`.

Bala reuse is independently checked against the live engine's full identity
(approved-catalog snapshot/hash, current TTE hashes, config, dependency lock,
wrapper/upstream identity, interpreter, and seed). CWT is checked against its
fixed grid/MC contract and adopted block window. The lag headline is checked to
be the producer's scan-median choice over the default pulse-scaled windows; its
MC seed/counts and sign convention are also enforced.

All figure artifacts are stamped
`UNGATED_PENDING_INDEPENDENT_CLAUDE_FIGURE_VERIFICATION`. This producer-side
controller never appends or infers a verifier verdict.

## Step-9 input correction

The required default scripts/44 command is run first. Its step-9 lookup points
at the legacy nested sweep table, so the controller then stages the adopted
blocks and current 24-model convention table under a private temporary layout,
runs the existing scripts/44 implementation there, and atomically promotes
only the corrected step-9 PNG. The source sidecar records both input hashes and
the scripts/44 hash. No pipeline script or legacy fit table is modified.

For the response-uncovered `bn100130729`, the same default scripts/44 command
must freshly produce and receipt the five non-spectral figures. The missing
current-fit step-9 supplement remains a declared phase failure, while validated
temporal estimators are retained with `complete=false` and
`temporal_values_complete=true`. No legacy step-9 image is accepted as a
fallback.

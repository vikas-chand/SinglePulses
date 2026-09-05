# Campaign-20 P3 SED sweep runner

The authoritative campaign invocation is:

```bash
zsh notes/codex_campaign20_runtime/run_sed_sweep.zsh --campaign
```

It performs a global preflight of every non-blocked canonical ECSV/JSON pair
and adopted block product before any SED process starts. It then builds one
cross-trigger worklist, runs exactly 16 one-core shell jobs, rescans the whole
grid, and repeats only the failed/missing list once. The final
`sweep_status.txt` has one `OK MODEL bin` or `FAIL MODEL bin reason` line for
every canonical pair. `bn100130729` receives an explicit
`RESPONSE_UNCOVERED` closure because there is no canonical P1 table to define a
grid; the campaign command therefore exits 2 even when every runnable pair is
closed successfully.

Reusable 41c triplets must pass all of these machine checks:

- exact current scripts/41c SHA-256 and recorded invocation;
- exact canonical bin, interval, reference detector, and `PLUGIN_DETS` context;
- strict XSPEC rebin 5 5, no upper-limit arrows, frozen RNG seed, and current
  energy-range convention;
- PNG/PDF/JSON integrity and freshness relative to the canonical ECSV/JSON;
- both stored and rendered AIC within 0.1 of the current canonical cell;
- internally consistent PGstat, active-channel count, dof, and free-parameter
  count;
- provenance mode `live` or `frozen_replay`.

Invalid/old stems are moved, never deleted, under the grid's timestamped
`quarantine/` tree, with source hashes recorded in
`logs/quarantine_manifest.jsonl`.

Current scripts/41c builds GBM plugins only. Therefore the canonical LLE and
per-block LAT contexts in `bn081224887` and `bn110721200` are deliberately
refused as `STRUCTURAL_COVERAGE_MISMATCH`; the validator never accepts a
coincidentally close GBM-only AIC as a broadband panel. Both required attempts
still run, and the final summaries state that the bands were not dropped. P4's
fallback montage then supplies a classified `STRUCTURAL REFUSAL` cell for each
unrenderable pair, preserving the 24-cell no-model-dropped closure. Every
figure remains UNGATED pending the independent Claude figure-verifier.

Producer-side tests (temporary files only; no P3 engine launch):

```bash
/Users/salim/anaconda3/envs/threeML/bin/python -m unittest -v \
  notes/codex_campaign20_runtime/test_run_sed_sweep.py
zsh -n notes/codex_campaign20_runtime/run_sed_sweep.zsh
```

The shell implementation uses an arithmetic token-fill loop so the required
16-token pool is explicit and directly covered by the test probe. The earlier
brace form also expands to 16 iterations on this host; it was replaced for
clarity, not because a live deadlock was demonstrated.

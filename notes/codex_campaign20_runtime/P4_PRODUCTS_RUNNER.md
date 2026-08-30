# Campaign-20 P4 product runner

`run_p4_products.py` executes P4 at a burst boundary and restores campaign
queue order when several triggers are supplied.

```bash
/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p4_products.py plan \
  --triggers bn081224887

/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p4_products.py run \
  --triggers bn081224887

/Users/salim/anaconda3/envs/threeML/bin/python \
  notes/codex_campaign20_runtime/run_p4_products.py validate \
  --write-summary --triggers bn081224887
```

The execution order is fixed: scripts/41e, the notes-owned montage
audit/fallback, scripts/41d with `--fit-root results/convention_check --out
results/convention_check/param_evolution`, then the notes-owned all-model table
adapter. The adapter invokes the frozen `campaign_products.py tables` mode with
an absolute fit root (its relative-root path raises `ValueError`) and normalizes
only the derived Markdown presentation to the saved burst-2 format. It does not
change the frozen P1 helper or any fit value. A missing or non-24-model canonical
fit is `PARTIAL`; no archival sweep fit is substituted.

Before scripts/41e is allowed to run, the controller validates the final P3
closure against the current canonical ECSV, canonical JSON, adopted blocks,
all pair classifications, selected triplet hashes, retry evidence, and the
exact `sweep_status.txt` token stream. Multiple current-valid sidecars for one
pair are rejected because scripts/41e would otherwise make a glob-order choice.

The final validator independently rescans every P3 PNG/PDF/JSON triplet. For
each `TINT`/`binN` tag it requires:

- exactly 24 montage cells in the canonical finite-AIC-first order;
- `n_panels == 24`;
- `n_missing` equal to the independent P3 missing-pair count;
- every unavailable/failed model represented by the fallback contract;
- current-fit provenance on every fallback montage.

It also requires the exact raw-AIC winner-union parameter-evolution products,
current scripts/41d and canonical-fit provenance, no stale per-trigger evolution
glob, and a complete table manifest with one 24-row table per spectrum plus the
combined table. Every per-spectrum table is regenerated in the exact burst-2
column/precision/footer-free format and byte-compared with a fresh rendering of
the current fit. The manifest binds both the ECSV and its canonical JSON.

`bn100130729` receives a written `PARTIAL` P4 summary tied to its explicit
zero-pair `RESPONSE_UNCOVERED` P3 closure; no P4 producer is launched. For the
broadband bursts, persistent LLE/LAT display mismatches remain explicit
`STRUCTURAL REFUSAL` cells in a full 24-cell fallback montage.

Outputs are `p4_products_summary.json` in the burst's SED grid and phase/burst
status JSON under `logs/codex_campaign20/p4/`. Every figure remains
`UNGATED_PENDING_INDEPENDENT_CLAUDE_FIGURE_VERIFICATION`.

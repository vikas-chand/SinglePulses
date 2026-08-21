# CODEX agent-architecture v3 build audit — 2026-08-21

## VERDICT — DO NOT SIGN OFF

All eleven pinned SHA-256 prefixes match the artefacts named in the brief, and
the normal `bnTEST000` live-report/cascade loop works. The architecture is not
ready for sign-off, however. Material blockers are:

1. several `DEPLOYED` register claims are only partial or are contradicted by
   the implementation (NR-9, NR-12, NR-18, and NR-19 in particular);
2. `live_report.py` can create an approval without an approver under optimized
   Python, can assert `PRESENTED` without evidence or identity, and emits
   injection-prone Markdown;
3. the NR-19 cascade clears marker names but does not establish dependency
   closure: changed fits are not reliably promoted, existing SED panels are
   skipped, Stage-1 products remain current-looking, and reports can rebuild
   from an older, non-canonical fit table;
4. unchecked trigger strings permit path traversal in both scripts, and
   `invalidate_downstream.py` additionally passes the trigger through a shell;
5. the Markdown, HTML, register, and disk do not make identical claims about
   commit state, active hooks, saved workflows, or the approval rail.

No fit, binning, download, or other pipeline stage was launched.

## Scope and artefact identity

The required inventory-first query was run:

```text
python scripts/00_inventory.py --find "agent"
TOOL INVENTORY — 0 scripts in ./scripts
```

The branch was `memory-guard`. Direct `sha256` recomputation confirmed every
pin in the brief:

| artefact | recomputed prefix | result |
|---|---:|---|
| `dev/ai_guides/AgentArchitecture.md` | `b3d2e548cd86` | match |
| `docs/GRB_AGENT_FLOWCHART.md` | `6d34f1eeea37` | match |
| `dev/live_report.py` | `37d462755024` | match |
| `dev/invalidate_downstream.py` | `2632628d358c` | match |
| `.claude/agents/dispatcher.md` | `0646b42cdac2` | match |
| `.claude/agents/port-verifier.md` | `769ea95b2c93` | match |
| `.claude/agents/seed-auditor.md` | `773ea19315f4` | match |
| `.claude/agents/tie-reporter.md` | `44f91506305a` | match |
| `.claude/agents/admission-gate.md` | `1fec9b632b03` | match |
| `.claude/agents/prior-art-reader.md` | `4fa42da773ae` | match |
| `docs/grb_agent_design_v3.html` | `db3eed87f62a` | match |

The uncommitted state described in the brief is also exact: the six new agent
files and the two NR-18/19 scripts are untracked. Those files were audited as
the pinned artefacts of record, not as committed content.

## 1. Register integrity — NOT CONFIRMED

### Row count and numbering

A direct parse beginning after the register header at
`dev/ai_guides/AgentArchitecture.md:101` and stopping at the first non-table
line produced exactly **29 data rows** (`:103–131`). Sixteen status cells begin
with `DEPLOYED`; one additional qualified row says `LESSON DEPLOYED ... general
rule PROPOSED`. The other statuses are nine `PROPOSED`, one `IDENTITY PENDING
PI`, one `CLOSED`, and one `PRACTICE ... regression test PROPOSED`.

The numbered rows are NR-1–NR-10 and NR-12–NR-19 (18 rows) plus 11 unnumbered
rows. NR-11 alone is absent. `dev/campaign20_refits.sh:2` identifies the post
NR-11 operations audit, so the intentional retirement is confirmed and is not
a discrepancy.

### Deployment-by-deployment result

Confirmed disk implementations include:

- figure verifier, numbers verifier, distiller, skill reader, and dispatcher:
  their named files exist under `.claude/agents/` and their bodies match the
  register purposes;
- the `SendUserFile` hook is armed at `.claude/settings.json:3–10` and calls
  `.claude/hooks/no_unverified_figures.py`;
- the literature protocol and products exist in
  `dev/ai_guides/LiteratureHarvest.md` and `results/gcn/` /
  `notes/reconciliation/`;
- NR-1 has retained-draw and best-fit-containment guards in
  `scripts/41c_paper_sed.py:145–180,413–424`;
- NR-5 is present as verifier practice in
  `.claude/agents/figure-verifier.md:10–13`;
- NR-15 has owner PID recording at `dev/ram_slots.sh:89–90`, `_ram_reap` at
  `:53–61`, and a call before admission at `:71`;
- NR-17 is represented by `.claude/agents/dispatcher.md`;
- the NR-18 and NR-19 program files exist.

The following prevent confirmation that every `DEPLOYED` row does what it says:

1. **The mechanical-enforcer state contradicts itself.** The register calls
   the hook armed at `AgentArchitecture.md:109`, while the cross-cutting roster
   still says `PENDING the PI's go` at `:55`, and `:159–160` still describes
   arming it as an unmade decision.

2. **The hook is not the claimed fail-closed “any figure” gate.** It filters to
   PNG only (`no_unverified_figures.py:4–6,15–17`) and exits zero on malformed
   input (`:10–13`). It accepts a hash appearing anywhere in any ledger,
   without establishing that the matching verdict is PASS rather than FAIL.
   A PDF and malformed JSON both bypass the check. The settings wiring itself
   is present, but the deployed semantics are narrower and fail-open.

3. **NR-9 violates its own “never recompute” invariant.** In
   `scripts/41c_paper_sed.py:212–223`, missing/malformed engine metadata,
   missing `fit_dets`, or a stored reference not present in the locally derived
   detector list leads to a minimum-angle recomputation. This is a silent
   fallback, not a loud failure.

4. **NR-12 is not used by every heavy launcher.** `dev/ram_slots.sh` exists and
   three launchers source it, but at least the following current executable
   launchers bypass it: `dev/bin_remaining21.sh:20–28`,
   `dev/run_burst_agentic.sh:46–62`, `dev/run_lle_notebooks.sh:8–12`,
   `dev/run_reanalysis_human.sh:15–22`, and
   `dev/run_refit_stage2.sh:6–11`. The “single entry point” in
   `run_burst_agentic.sh` directly launches the heavy spectral fitter.

5. **NR-18 is code-present, not deployed “every burst, continuously.”** After
   deleting the audit sandbox, a disk census found 106 `results/sweep106/bn*`
   burst directories, one `LIVE_REPORT_*.md`, and zero `APPROVALS.json` files.
   No driver or step orchestrator calls `live_report.py`; repository-wide
   references outside the two scripts are documentation only. The sole live
   report says the adjacent approval file exists even though it does not.

6. **The residual-review fan-out is demonstrated, not persistently wired.** A
   contract and ten notes for one burst exist, but no reusable fan-out workflow
   or dedicated agent definition was found, and the design documents themselves
   say saved workflows remain open. This supports “practice demonstrated,” not
   the register's unqualified `DEPLOYED (workflow fan-out)`.

7. **NR-19 exists but does not meet its declared effect.** Its dependency and
   regeneration failures are demonstrated under item 5 below.

The qualified NR-13 status is accurate only as written: the specific
available-memory lesson appears in `ram_slots.sh`/`ram_watchdog.sh`, while the
general cross-check rule remains proposed.

## 2. Six new agent definitions — NOT CONFIRMED

PyYAML 6.0.2 `safe_load` parsed all six frontmatters. Each contains exactly
`name`, `description`, and `tools`; every name matches its filename. Their
single-purpose text substantially matches the corresponding register row:
dispatcher/NR-17, port verification, seed auditing/NR-2, tie reporting/NR-3,
catalog admission/NR-4, and prior-art reading.

Two problems remain.

### Approval independence

The dispatcher explicitly rejects producer self-approval at
`.claude/agents/dispatcher.md:24–25`. The port verifier, seed auditor, tie
reporter, and admission gate issue approval-like verdicts, but none states that
it must be fresh-context and must not have produced or modified the target. The
prior-art reader has no approval power. The four verdict agents therefore leave
a producer-as-verifier reading open even though the architecture forbids it.

The exact correction is a shared precondition in each verdict agent: “You did
not produce or modify the target. If you did, return INELIGIBLE and require a
fresh verifier.” Any rerun or synthetic fixture should be constrained to an
isolated scratch location and must not mutate the target being judged.

### Minimum tools and dispatcher completeness

All six list `Read, Grep, Glob, Bash`. Bash is reasonably needed to execute
numeric comparisons for the port, seed, tie, and admission roles. The
dispatcher is explicitly read/classify/plan-only and does not need Bash. The
prior-art reader can perform its stated file sweep with Read/Grep/Glob; its
instructions do not justify unrestricted Bash. Remove Bash from those two, or
document a concrete read-only operation that cannot be performed by the scoped
tools.

The dispatcher also classifies “external claims” at line 12 but never routes
that class in lines 13–19, and its explicit mapping omits residual reviewers,
the milestone auditor, incident distiller, and step-9 literature agent. Make it
iterate every matching register row (deployed and proposed), or add all missing
mappings explicitly.

## 3. Live report, static — NOT CONFIRMED

`dev/live_report.py` was read end to end.

### (a) Stamp without `--by`

**Not robustly confirmed.** Under ordinary Python, the test

```text
python3 dev/live_report.py --trig bnTEST000 --approve 7
```

exited 1 with `AssertionError: --by is required on a stamp`. Under
`python3 -O`, assertions are removed; the same operation succeeded and wrote
`{"status":"APPROVED", "by":null}`. A safety rule must not be an `assert`.

There are related provenance defects:

- `--feedback-only ... --by NAME` checks the name but does not store it in the
  feedback object; on an unapproved step the report therefore cannot identify
  who supplied the feedback;
- `--present` writes `PRESENTED` without an actor, evidence, or prerequisite;
- `--present`, `--approve`, and `--feedback-only` are not mutually exclusive.
  `step = a.present or a.approve or a.feedback_only` can apply one action's
  value to another action's record.

### (b) Evidence-only document

**Not confirmed.** The ordinary evidence collector generally appends a path
only after `glob`/`exists`, but the output is wrapped in backticks, not emitted
as a Markdown link (`live_report.py:74–77`). More importantly,
`--present 7` produced a visible `PRESENTED` status with no evidence and no
identity. That directly contradicts the document's own statement that it never
asserts what it cannot link.

Both `by` and feedback text are inserted into Markdown without escaping. A
`--by` value containing pipes added columns to the status table. Feedback
containing blank lines, a heading, and an off-disk URL injected all three into
the document. `json.dump` kept `APPROVALS.json` syntactically valid, so the
corruption is in the Markdown rendering, not JSON encoding.

### (c) Unrouted feedback

**Confirmed on the normal generated path, but not fail-closed.** CLI-generated
feedback has no `routed` key and rendered exactly:

```text
PENDING — protocol defect if it stays here
```

However, `f.get('routed', default)` treats an explicitly empty string as
routed and prints blank. There is no CLI operation to record a validated route
or its evidence. The feedback trail also displays the record's approval time
instead of each feedback item's own `f['utc']`; the test approval was at
`21:33:38Z`, feedback at `21:33:44Z`, and the trail printed `21:33:38Z`.

### (d) Downstream warning

**Confirmed on the normal path.** With step 7 and step 8 both approved,
feedback on step 7 printed exactly:

```text
!! NR-19: steps 8 were approved on the OLD step-7 state.
```

The implementation enumerates only later records whose stored status is
exactly `APPROVED`, in ledger order. Ambiguous simultaneous action flags remain
an input-validation hole.

### Additional static safety defects

`trig` is not validated before it is used in paths and glob patterns, permitting
directory traversal. Saves are non-atomic read/modify/write operations with no
locking, so concurrent step updates can lose each other or leave truncated
JSON. Re-approving a STALE record changes its status but leaves
`stale_reason`, creating internally contradictory state.

## 4. Live report plus cascade, dynamic — CONFIRMED FOR THE PRESCRIBED LOOP

The only transient write location was
`results/sweep106/bnTEST000/`. The normal sequence was:

1. create the directory and `--present 7`;
2. `--approve 7 --by CODEX`;
3. `--approve 8 --by CODEX`;
4. `--feedback-only 7 --by CODEX --feedback ...`;
5. dry-run NR-19 from step 7;
6. execute NR-19 from step 7.

Feedback named exactly step 8 in the warning. Immediately before and after the
dry-run, the two sandbox hashes were identical:

```text
APPROVALS.json                 06013be17959607d351f3a1dd20f10c6e1d98b9e01cbd79407034fa6905abeea
LIVE_REPORT_bnTEST000.md       22790441e155ee1e6fdcf402fd8ada3927ce0adbbd6187a43bbc376f0da5a566
```

The execute run demoted step 8 to `STALE`, added
`stale_reason="upstream step 7 changed"`, and retained the old `by` and `utc`
fields as required by the deliberate audit-trail convention.

Before and after the loop, `logs/campaign20/products/` had exactly 172 files.
The sorted-filename digest was unchanged at
`cc0694843f85ab2d7b6792f40f9a6c427f587f6f149f029dce58598cc323a952`;
the aggregate digest of all per-file content hashes was unchanged at
`7865f24d9d702cf869380a751a47230a255795f41a0832793e26acb3c84dbc7a`.
No `bnTEST000*` marker existed there or under
`results/campaign20_products_done/` before or after.

Separate adversarial probes inside the same sandbox demonstrated the optimized
Python and Markdown defects described in item 3. A correct CODEX stamp replaced
the optimized-Python test stamp before the prescribed normal loop continued.

**Cleanup confirmation:** `results/sweep106/bnTEST000` was deleted in its
entirety after the test. A final existence check returned false, and no
`bnTEST000` marker or CODEX-stamped approval survives anywhere in the tested
campaign paths.

## 5. Cascade map — NOT CONFIRMED

The literal seven phase names in `invalidate_downstream.py` match the driver's
markers: `t46`, `t44`, `t44b`, `t47`, `bala`, `t47b`, and `t47c`
(`campaign_products_driver.sh:63–70,76–106`). The logical map is:

| changed step | cleared phase markers | DONE | later approvals eligible for STALE |
|---|---|---|---|
| `0b`, `0`, `1` | none; early return | no | none |
| `2` | ALL seven | yes | 3–9 |
| `3` | ALL seven | yes | 4–9 |
| `4` | ALL seven | yes | 5–9 |
| `5` | ALL seven | yes | 6–9 |
| `6` | `t44b` | yes | 7–9 |
| `7` | ALL seven | yes | 8–9 |
| `8` | none | yes | 9 |
| `9` | none | yes | none |

Only existing paths are selected. Later approvals are demoted only when status
is exactly `APPROVED`.

### Step 6 question: is clearing only `t44b` sufficient?

**No.** The cascade also removes DONE, so the driver re-enters, but its decisions
preserve stale products:

1. `merge_campaign_families.py:53–56` no-ops whenever the promoted canonical
   table already has 24 models; it does not compare source/input hashes.
2. The SED job builder at `campaign_products_driver.sh:146–153` skips a
   bin/model solely because a matching PNG exists. It does not consult fit
   provenance or `sweep_status.txt`.
3. Montage, parameter-evolution, and report commands run unconditionally, but
   the montage consumes the existing panels.
4. The report invocation passes `--out results/sweep106/$TRIG`; report code then
   reads `os.path.join(out,trig,'spectral_fits.ecsv')` at
   `scripts/48_burst_report.py:68–69`. That is the nested sweep table, not
   `results/convention_check/<trig>/spectral_fits.ecsv`.
5. An already existing notebook is explicitly skipped (`driver:188–194`).

A read-only demonstration on `bn090530760` makes this concrete:

- canonical and current `highe` tables are both 24 models × 7 rows, but their
  SHA-256 values differ (`9328644c...` versus `5f779566...`); the `highe` file
  is newer and contains three AIC cells more than 0.001 better;
- 168 SED PNGs already exist, so every existing bin/model filename is skipped;
- the report-source table hash is `0d290909...`, different from canonical;
  163/168 common finite AIC cells differ, with maximum absolute difference
  `955.7127907915383`.

Thus the montage and report commands may execute, but that is not regeneration
from the changed fit state.

### Steps 2–5 question: does `ALL` cover a Stage-1 change?

**No.** `ALL` means only the seven product markers plus DONE. Block tables,
`results/campaign20_fam/<trig>_highe/spectral_fits.*`, and
`results/convention_check/<trig>/spectral_fits.*` survive with no stale
binding. The fit launchers skip existing fit tables, and promotion then no-ops
on the surviving 24-model canonical table. The note saying “re-bin then refit
required” is advisory prose, not mechanical enforcement.

Step 1 is detector selection, yet it has no cascade entry. The accepted command

```text
python3 dev/invalidate_downstream.py --trig bn090530760 --from-step 1
```

printed `step 1: nothing downstream to invalidate`. A detector change can
therefore leave every block, fit, product, and approval current-looking.

### Containment and fail-loud behavior

The dry-run

```text
python3 dev/invalidate_downstream.py \
  --trig ../../dev/invalidate_downstream.py --from-step 8
```

identified the invalidator itself as
`results/campaign20_products_done/../../dev/invalidate_downstream.py`. With
`--execute`, line 59 would remove it. The approval path has the same unchecked
traversal, and line 64 interpolates `trig` into `os.system`, permitting shell
injection and discarding the child return code.

Execution is not transactional: marker removal precedes the approval rewrite.
Driver phase return values are often unchecked; montage, evolution, and report
failures do not stop the chain; a missing PDF is only a warning. Existing
invariants frequently SKIP missing products and bind step-9 provenance to marker
existence rather than an input hash (`verify_burst_invariants.py:43–75`). The
SED sidecar records script hash but not the canonical fit-table hash. The
driver's `FAIL TRIG BIN MODEL` status format is also parsed by the montage as
tokens `(TRIG,BIN)` and later queried as `(MODEL,BIN)`
(`41e_sed_montage.py:66–71,134`).

## 6. Page ↔ flowchart ↔ disk sync — NOT CONFIRMED

Confirmed claims:

- dispatcher appears in boot in both documents;
- both contain the NR-18/19 approval rail;
- the register count is 29;
- NR-11 is retired and absent;
- both are v3 dated 2026-08-21;
- disk contains exactly ten `.claude/agents/*.md` files: four tracked by Git
  and six untracked, with the names listed by the HTML.

Discrepancies:

1. HTML lines 67–70 explicitly say “4 committed, 6 pending commit.” The declared
   source-of-record Markdown lines 14–17 say only “10 agent files.” The requested
   claim is therefore not identical.
2. Both documents say unguarded catalog writes are blocked
   (`GRB_AGENT_FLOWCHART.md:31,106`; HTML `:81,149`), but
   `.claude/settings.json` contains only a `SendUserFile` matcher. NR-4 remains
   proposed. No catalog-write hook exists.
3. Both approval rails say the live report is evidence-linked/never asserted
   and approvals cannot be fabricated. Item 3 demonstrates the opposite.
4. Both discuss every step as a saved workflow while also saying saved
   workflows remain the open freeze item. Disk supports the latter statement.

### Mermaid

One Markdown Mermaid block and two HTML Mermaid blocks were extracted. Static
checks found valid `flowchart TD/LR` headers, balanced quotes and delimiters,
balanced `subgraph`/`end` counts, declared edge endpoints, valid class targets,
and no duplicate node IDs.

Actual Mermaid grammar/rendering could not be certified: no local `mmdc`,
Mermaid Node/Python package, or bundled Mermaid JavaScript exists, and the
in-app browser had no available browser instance. The HTML review copy also
contains no Mermaid runtime/initialization, DOCTYPE, or charset; raw `&` in its
first diagram is reported by HTML validators. Standalone, it displays Mermaid
source rather than rendered diagrams. This limitation is recorded again under
“Could not verify.”

## 7. Stress-test narrative — CONFIRMED AGAINST CODE AND HISTORY

`memory-guard` HEAD and `origin/memory-guard` are commit
`b82fc9c6a20b1f3f4435ffa7a92bd75031a14ad9`. Current
`dev/ram_slots.sh` is byte-identical to that commit.

The commit message records eight review findings. It labels `bug_001` and
`bug_002` normal severity and labels `bug_007` a nit that broke the headline
mutex invariant. It then records the beyond-review discovery: zsh defers a
signal trap while a foreground child runs, SIGKILL/shutdown invokes no trap,
and an owner-PID reaper was added after testing the first fix.

Current code matches that history:

- `_ram_reap` is at `ram_slots.sh:53–61` and runs before admission at `:71`;
- claims use fixed shared `slot_0..slot_N-1` names and atomic `mkdir` contention
  at `:81–90`, replacing the old uniquely named `$$_${i}_$RANDOM` directories;
- every claimed slot records `$$` in `pid` at `:90`;
- the comments at `:45–52` accurately describe trap deferral and SIGKILL;
- both design documents tell the same narrow historical story.

The prose says “two real bugs,” while the commit gives the more precise “two
normal-severity bugs” and also records five additional nits. That abridgment is
not false, but the precise wording should be preferred.

Two current implementation fragilities do not invalidate the historical
account but do weaken the rail:

1. the products driver releases its 6-GB claim and requests 16 GB from a 32-GB
   budget, so two MVT jobs can coexist; its comment that only one can run is
   arithmetically false unless another constraint intervenes;
2. `_ram_reap` treats a pidless slot as dead. Another caller can reap a newly
   created directory between `mkdir slot_i` and the unchecked PID-file write.
   PID reuse within the same boot can also make `kill -0` mistake a dead owner
   for an unrelated live process.

## DISCREPANCIES — exact fixes

1. **NR-19 path traversal and command injection.** Add one shared trigger
   validator (for example, the canonical GBM trigger grammar), reject separators
   and traversal, resolve every target, and require `Path.relative_to()` its
   designated root. Replace `os.system` with
   `subprocess.run([sys.executable, script, '--trig', trig], check=True, cwd=ROOT)`.

2. **Incomplete cascade dependency closure.** Replace empty marker semantics
   with provenance-bound generations/input hashes for approval rows, blocks,
   family fits, canonical promotion, SED panels, montages, reports, and
   notebooks. Add step 1 to the full rebin/refit cascade and explicitly define
   steps `0b`/`0`. A missing reference must fail, not return “nothing.” Preserve
   the designed no-product-deletion rule by clearing/creating stale generation
   markers and teaching consumers to overwrite stale outputs.

3. **Stale promotion and SED skip.** Add a forced/provenance-aware promotion
   mode; the 24-model no-op is valid only when source and input hashes match.
   Promote ECSV and JSON atomically as a pair. Record canonical fit-table hashes
   in every 41c sidecar and rerender when they differ; filename existence alone
   must never mean current.

4. **Report reads the wrong fit table and failures are tolerated.** Give
   `48_burst_report.py` a required `--fit-root`, pass
   `results/convention_check` from the driver, record the input hash, and fail on
   missing/mismatched data. Check every phase subprocess and require fresh PDF,
   montage, SED, and report products before DONE. Change invariant SKIP results
   for declared products to FAIL.

5. **Live-report authorization and data integrity.** Replace safety asserts with
   explicit runtime validation; use an argparse mutually exclusive action group;
   require and persist actor identity for approval and feedback; require linked
   evidence for PRESENTED; add a validated route operation; render each
   feedback item's own timestamp; clear/resolve stale metadata on reapproval.
   Write approval state atomically under a lock or generation check.

6. **Markdown and identity injection.** Validate `trig` and approver identity,
   escape table cells and feedback/route text, and generate real Markdown links
   only after containment/existence checks. Add regression cases for pipes,
   newlines, Markdown links, HTML, empty `routed`, combined action flags, and
   optimized Python.

7. **NR-9 fallback.** Require a readable engine sidecar with a valid stored
   `reference_det`/`canonical_det` and nonempty `fit_dets`; raise on absence,
   parse failure, or inconsistency. Remove the minimum-angle fallback.

8. **NR-12 launcher coverage.** Put every non-retired heavy launcher behind
   `ram_admit`/`ram_release`, without holding a smaller outer claim while a
   nested phase requests a larger one. Explicitly disable obsolete bypass
   launchers. Add a static audit that fails when a known heavy entry point lacks
   admission.

9. **Agent independence and tools.** Add the fresh-context/non-producer
   precondition to port, seed, tie, and admission verdict agents. Remove Bash
   from dispatcher and prior-art reader unless a necessary read-only use is
   documented. Make dispatcher routing exhaustive over the register.

10. **Hook semantics and documentation state.** Either narrow all claims to PNG
    or gate every supported figure format. Fail closed on malformed expected
    payloads and require a matching current PASS verdict, not mere hash text.
    Update `AgentArchitecture.md:55,159–160` to the actual armed state. Do not
    claim a catalog-write hook until one exists and is armed.

11. **NR-18 and residual workflow rollout.** Integrate live-report rebuilding
    with each step/gate, backfill reports without fabricating approvals, and make
    the “stamps beside this file” prose conditional. Persist the residual
    fan-out workflow and enforce its declared outputs, or downgrade both rows to
    partial/demonstrated status.

12. **Page/source/HTML verification.** Add “4 committed, 6 pending commit” to
    the source-of-record Markdown, reconcile all hook/workflow/approval claims
    with disk, and add a checked-in Mermaid parse/render CI test. If the HTML is
    intended to be standalone, add HTML5 scaffold/charset, escape raw ampersands,
    and load/initialize a pinned Mermaid runtime; otherwise state explicitly
    that the publishing host supplies it.

13. **RAM rail races.** Use a dedicated MVT mutex or make the claim strictly
    greater than half the budget if singleton execution is required. Protect
    slot initialization/reaping with an atomic ownership protocol (or a safe
    pidless grace plus claimant revalidation), check the PID write, and store a
    process-start identity in addition to PID to prevent same-boot PID reuse.

14. **SED refusal parsing.** Give `sweep_status` a structured JSON/CSV schema, or
    parse the current `FAIL TRIG BIN MODEL` record as `(MODEL,BIN)` consistently.
    Add a fixture proving that a guard refusal and a crash land in the correct
    montage cells.

## COULD NOT VERIFY

1. **Mermaid grammar/render:** structural checks passed, but no local Mermaid
   parser or usable browser was available. Full syntactic validity therefore
   remains unverified. A checked-in parser/CI render is the exact remedy.
2. **Historical RAM stress executions:** the six-caller contention and SIGKILL
   tests are described in commit `b82fc9c`, but no tracked test script or raw log
   was found. The assignment's write restriction precluded recreating a slot
   stress environment. Code and history support the narrative; the empirical
   runs themselves are attested only by the commit record.

## Independent judgement beyond the brief

The most serious unrequested finding is that the approval/cascade boundary is
also a filesystem and shell trust boundary. A crafted trigger can turn a tool
whose design promises “markers and stamps only” into an arbitrary-path removal
attempt and command execution. That is a release blocker independent of the
scientific pipeline.

The next systemic issue is that empty marker files encode completion but not
which inputs they certify. As long as skip/resume decisions are based on
existence rather than hashes/generations, no invalidation table can prove that
products are current. The `bn090530760` counterexample is existing repository
state, not a hypothetical race.

Finally, the RAM owner-PID repair is directionally correct but not yet a robust
lock protocol: pidless initialization and PID reuse are unresolved. A small,
tracked concurrency regression harness should become part of the rail itself.

**Final cleanup confirmation:** `results/sweep106/bnTEST000` does not exist;
no `bnTEST000` product/DONE marker exists; no CODEX-stamped test approval
survives.

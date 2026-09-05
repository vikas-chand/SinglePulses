# Provenance manifest — agentic_grb_v2.tex update 2026-09-01
# One row per \prov number added/changed. sha256 at quote time.
repo_commit: b36525d
dirty_files: 45 (list via git status)

| # | value | claim | source artifact | sha256 (quote time) |
|---|---|---|---|---|
| 1 | 40 rows, NR-11 retired | requirements register size | dev/ai_guides/AgentArchitecture.md | b806637240f3 |
| 2 | 14 states (S0-S12+SX) | state machine | dev/ai_guides/AgentSkeleton.md | ddb2a2c3a029 |
| 3 | 6 failure classes | failure taxonomy | dev/ai_guides/AgentSkeleton.md | (same) |
| 4 | 10 agents | verifier roster | .claude/agents/ (10 files) | n/a (ls count) |
| 5 | 3 hooks | code-layer enforcement | .claude/hooks/ (3 files) | n/a (ls count) |
| 6 | 32 lessons (L1-L33, L14 absent) | lesson count | dev/ai_guides/{SpectralFitting,Temporal,LiteratureHarvest,BurstWalkthrough}.md | 864490bebfca |
| 7 | 7 stamps 0b-5, all VIKAS | acceptance-arm approvals | results/sweep106/bn110920546/APPROVALS.json | 27fe16f6c404 |
| 8 | human 4 det {n0,n1,n3,b0} vs 7; BCAT+same-side verified | divergence case | results/approval/bn110920546_decision.json | 66332e09ac0b |
| 9 | SUPERSEDED by Fix round 2: ZERO contemporaneous; 1/105 filled and it is RETROACTIVE | rationale gap | AgentArchitecture.md NR-39 row (measured 2026-08-31) | (row 1 sha) |
| 10 | 105-burst census: 78% triggered, 80% triggered+side ceiling | divergence census | AgentArchitecture.md NR-38 + LIVE_REPORT feedback trail | (row 1 sha) |
| 11 | +68 vs +481 cts/s (x7) two defensible baselines | no-ground-truth evidence | decision.json amendment 2026-08-31 + NR-40 row | (row 8 sha) |
| 12 | b0 post began 31.84 s inside source window; >=3.3 sigma in 9 variants | overlap measurement | decision.json amendment | (row 8 sha) |
| 13 | ~100 ms dropout at t-T0=-18.3122 s, all 7 detectors within 2.9 ms | telemetry stall | decision.json amendment | (row 8 sha) |
| 14 | chi2/dof anchor sensitivity up to x2.4; -17.00 s only grid-independent cut | robustness criterion | decision.json amendment post_verification | (row 8 sha) |
| 15 | ~7 h chat-only approval, caught by cascade | late-stamp incident | LIVE_REPORT feedback trail step 4 | 63657f16bf60 |
| 16 | step-5 demoted then reinstated; block table sha f361fbd2... unchanged since 2026-08-12; 11 blocks | cascade+reinstatement | LIVE_REPORT feedback trail step 5 | (row 15 sha) |
| 17 | 1 divergence-ledger row (founding) | ledger state | results/campaign/divergence_ledger.md | 5e76e827a7c8 |
| 18 | SAA exit at t-T0=-120.07 s (FLAGS bit-1) | belt-passage primitive | data/bn110920546/glg_poshist_all_110920_v01.fit via NR-40 row | (row 1 sha) |
| 19 | Biltzinger+2020 = 2020A&A...640A...8B | citation | ADS export 2026-09-01 | n/a (ADS API) |
| 20 | 106 fitted, 1 RESPONSE_UNCOVERED exclusion | campaign coverage | results/ + campaign memory; VERIFIER: recount from products | pending |
| 21 | SUPERSEDED by Fix round 2: both counts dropped from the paper (untraceable) | historical rate (removed) | campaign_ledger.csv |  |

## Post-edit binding (producer self-pin, interim per register)
edited_file_sha256: c8a87cb521e06677
pdf: 12 pages, compiled clean (pdflatex+bibtex+pdflatex x2, 0 errors, 0 bibtex warnings)
diff: paper_agentic/DIFF_v2_update_20260901.patch (379 lines)
cut authority: PI structured-gate approval 2026-09-01 ('Approve outline'); PI steer verbatim: 'what has been gone stale should go out and we are not writing history'; architecture-spine steer verbatim: 'The main thing should be the archeture of the whole harness and various roles of all agents...'

## Fix round 2 (2026-09-01, after Numbers-Verifier FAIL + conformance nits)
- "five engine defects" DROPPED from abstract+conclusions (untraceable; ledger recomputes 13 mixed-category over 8 rows; Codex audit 2026-08-13 line 381 already ruled it unsupported)
- "one of 105 carried contemporaneous reason" INVERTED to truth: NONE contemporaneous; the single filled record is retroactive and stamped as such
- "twenty-seven from first ten bursts" dropped (27 recomputable only from git history, not the cited ledger; ledger holds 8 rows)
- "about a hundred seconds" -> "about two minutes" (local primitive: belt exit at t-T0 = -120.07 s)
- \prov added: fourteen states, six classes, three hooks, 7-vs-4 detectors
- conclusions: "per-gate statistic" -> "defined, recorded quantity, accumulating with every gate" (ledger holds 1 founding row)
- conformance nits: authority-table "ten bursts" -> "all operation to date" + late-stamp disclosure; acceptance passage now discloses read-as-approval + late stamp provenance; "Operations add" -> "We add"
post_fix_sha256: 208e055bb96b3008

## Gate verdicts (sha-bound; verdict home pending PI blessing of a paper-level ledger)
- numbers-verifier full pass: FAIL @ sha c8a87cb521e06677 (2 hard + 1 attribution defect — all fixed)
- interim conformance gate: PASS-with-nits @ sha c8a87cb521e06677 (nits fixed same round)
- numbers-verifier DELTA pass: PASS 7/7 @ sha 208e055bb96b3008872e087cdd734f154f7c55bd7d9cb6bd40349d08acd29736
- distiller: 2 lessons routed (ReportSpec R3 preflight + R3a provenance-field, both PROPOSED pending PI), instances on NR-29 + NR-39 (I-16)
- figures: NOT touched this round; learning-curve PNG predates the vision-ledger regime (declared debt)

## PI gate 2026-09-01 (structured gate answers, verbatim options chosen)
- Paper revision: "I'll read first" — GATE OPEN, approval NOT recorded; PDF delivered for reading.
- Two distilled rules: "Bless both" — upgraded to PI-BLESSED in the report contract.
- Commit: "Commit" — this round committed.

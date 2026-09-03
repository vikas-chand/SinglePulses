# Paper v3 diagram gate ledger — TRACKED COPY

Copied from `results/campaign/agentfigs/VISION_QC.md` (gitignored under results/*) at 2026-09-03T04:56:23Z, so the approval record of the manuscript's diagrams is commit-recoverable (Codex supervisor review D4, 2026-09-02). The results/ file remains the ledger the no-ship hook reads; this copy is refreshed by the building session whenever a diagram row changes.

## Paper v3 diagrams — gate ledger appended 2026-09-03T03:32:12Z by the building session (verdicts by fresh-context figure-verifier agents; producer = building session)

| fig | file | sha256 | verdict | verifier round |
|---|---|---|---|---|
| F1 | `paper_agentic/figures/fig_F1_harness_anatomy.png` | `d355cbecafd87453dd17da3499ae713b1f6303d0df19f627c2bccf3689f3ae83` | PASS-WITH-NITS (round 1 FAIL -> fixes -> delta PASS-WITH-NITS; nits closed 1c0398b; unchanged since) | figure-verifier delta gate 2026-09-02 ~20:20 CDT; final re-bind confirmed unchanged ~23:00 |
| F2 | `paper_agentic/figures/fig_F2_lifecycle_guides_sensors.png` | `6165ad96025baa4d238670975ac57895e285182e7bd97bc377a946316ead0596` | PASS (round 3 PASS-WITH-NITS; nits closed 952ad85; final re-bind PASS) | figure-verifier final re-bind 2026-09-02 ~23:00 CDT |
| F4 | `paper_agentic/figures/fig_F4_steering_loop.png` | `755a0fee8433137d52021e8d25d3344c6478f54b5dceb3af930f4ce6baecb535` | PASS (round 3 delta PASS; unrostered box removed 2147b26) | figure-verifier round 3 2026-09-02 ~22:35 CDT |
| F5 | `paper_agentic/figures/fig_F5_object_action_model.png` | `73bf5bf3b6ce32ef611a6ca4d3ab72c13480be90c071c6e5bd51f8e6297d9297` | PASS-WITH-NITS (non-blocking: 1.0 mm clearance above "table sha"; log copies untracked) | figure-verifier re-bind 2026-09-02 ~23:10 CDT |

Contract for diagrams (derived from FigureVisionQC.md + dispatch plan B2): legibility, no arrow through a box, status honesty (solid = on disk, dashed = PROPOSED; F2: grey = code, white = agent, diamond = PI gate), text accuracy vs disk, every box maps to rows of paper_agentic/T1_component_roster_DRAFT.md (49 rows, 427fdc5), faithful 300-dpi render. Verdicts expire on any edit to the .tex sources.

### Source binding appended 2026-09-03T04:43:15Z (Codex supervisor review D4, 2026-09-02): the verdict rows above bind the rasterized PNG; the manuscript embeds the PDF; both are rendered from the .tex. This table binds all three at the approved state so a verdict can be checked against the embedded file, not only the raster.

| fig | png | png sha256 | pdf | pdf sha256 | tex | tex sha256 |
|---|---|---|---|---|---|---|
| F1 | `paper_agentic/figures/fig_F1_harness_anatomy.png` | `d355cbecafd87453dd17da3499ae713b1f6303d0df19f627c2bccf3689f3ae83` | `paper_agentic/figures/fig_F1_harness_anatomy.pdf` | `f85927943925ec29b302a45e5b3c5a0b5b2fcb4e72180a86a41ca24acd64edd8` | `paper_agentic/figures/fig_F1_harness_anatomy.tex` | `bd195af7fd5581b027ef51eef809bb67b6a3596d7f84864b5ce54e6996a670b7` |
| F2 | `paper_agentic/figures/fig_F2_lifecycle_guides_sensors.png` | `6165ad96025baa4d238670975ac57895e285182e7bd97bc377a946316ead0596` | `paper_agentic/figures/fig_F2_lifecycle_guides_sensors.pdf` | `4aae2ec1d6d3b8b4b433c7f911d3c9278589b07cda2f1fdc17439006dfdc967c` | `paper_agentic/figures/fig_F2_lifecycle_guides_sensors.tex` | `2a5f7846d5b6eafda11ec4e386531c4898a44b2ad6673a854e7948552d75d004` |
| F4 | `paper_agentic/figures/fig_F4_steering_loop.png` | `755a0fee8433137d52021e8d25d3344c6478f54b5dceb3af930f4ce6baecb535` | `paper_agentic/figures/fig_F4_steering_loop.pdf` | `dd0829ac72aca4a38635a11eb03a67110c9af1d955d12355e3cecd9305ed882f` | `paper_agentic/figures/fig_F4_steering_loop.tex` | `a0c869b00782f04cbc214a9d712bc091301b468fe198a2873c90d1dfd519b391` |
| F5 | `paper_agentic/figures/fig_F5_object_action_model.png` | `73bf5bf3b6ce32ef611a6ca4d3ab72c13480be90c071c6e5bd51f8e6297d9297` | `paper_agentic/figures/fig_F5_object_action_model.pdf` | `19b58a149d23feca7c9dd19366ccc7a937a9c2aec07cc33d9be3832a0dbf0005` | `paper_agentic/figures/fig_F5_object_action_model.tex` | `dd88c68c12cd0ec1dd38edee0207a73fa821f4032e6e4c7a7d4e8994dba7ac53` |

Rule (D4): a verdict is CURRENT only if the tex sha here matches the tex on disk AND the pdf sha here matches the embedded file; any edit to the .tex expires the verdict (as the contract already says) and requires re-render + re-gate + a new row.

### F1 delta gate 2026-09-03T04:56:23Z (after the Codex supervisor review D8: two overclaimed boxes reworded; producer = building session, verdict = fresh-context figure-verifier)

| fig | png | png sha256 | pdf sha256 | tex sha256 | verdict |
|---|---|---|---|---|---|
| F1 | `paper_agentic/figures/fig_F1_harness_anatomy.png` | `27361512a8d9a3ecfff84cc7fd2f9da874283a2b75d8390b5d2698bd80260010` | `fadb89779e4e247622421080482eb02d3336eaa5dc14942ad485398d59653668` | `ba09d739c2ce7e581f44ba6ce5f4c32e990e79e7680dec6271a283c871326a1d` | PASS-WITH-NITS — A verbatim strings PASS; B truth vs disk PASS (24 = 6+2+16 specs; every campaign launcher passes --models highe; 103/105 fitted bursts have a row for every block + T_INT, the 2 gaps are engine-logged "no usable plugin"; 27 guide files; 10 step-skill files, step 8 unwritten); C layout PASS (6.905 x 4.189 in, 0 overfull, pixel-identical rebuild); D status honesty PASS. Nits, none blocking: N1 PRE-EXISTING 1-px touch of the "stamps" label ascender on the first-class-actions dashed border (tex l.70; fix when touched); N2 caption should say the ledger indexes 11 slots, 10 written; N3 caption "attempted" (83/106 tables carry >=1 STATUS=FAIL cell; retry family exists) and bn160625945's 24-model table lives only in the sweep106 root so the board reports it S2_BINNED (two-roots gap, NR-23 family). PI RE-APPROVAL NEEDED: F1 was approved at d355cbec (decision 16); this is a content delta. |

# ABSTRACT brief — paper v3 (facts the abstract may use; nothing else may appear) — 2026-09-03

**Problem (context).** Time-resolved spectroscopy of gamma-ray bursts rests on judgement calls: which detectors to
trust, where the background lies, where the burst begins and ends, how finely to bin it in time, which of two dozen
spectral models to adopt.
**What the paper does (aims).** Describes the DESIGN of an agent (a language model inside a harness) that makes those
calls for a campaign, with a human approving every step. It describes; it does not claim (PI decision 19).
**Sample and instruments.** 106 single-pulse Fermi/GBM bursts (the approved catalog results/background_intervals.ecsv,
106 distinct triggers). One burst walked end to end so far (bn110920546, steps 0b–5 approved, 6 presented).
**Method (harness, in the paper's words).** Deterministic tools (a 24-model spectral engine with validity gates,
Bayesian-block binning, temporal chain, SED panels, report assembler); plain-language skill documents (27 guide files,
10 step skills) read at every step; state derived from disk; hooks and role separation (producer never verifies its
own work; verifiers run in fresh contexts); human gate with identity stamps. Each burst analysed blind; literature
compared only after the burst's numbers are frozen; each mismatch attributed (ours / theirs / frame) and distilled into
a numbered lesson with an executable test.
**Results the current draft reports (walkthrough era, flagged provisional).** Engine defects found and fixed with
tests (the validity-gate linear-margin defect on soft spectra, L27); blind predictions from the literature confirmed
and one refuted (v2 §9 — carry only if v2 §9 still says so at the gate). NO lesson count (the v2 "thirty-two" is
stale; recount before use). NO reliability claim.
**Conclusions.** The trained artifact is the skill library, readable by a student or another AI system; the paper
states where the human gate still decides; releases the library, the engine, the tests, the per-burst records.
**Binding decisions.** 17 (no blog citations), 18 (describe what worked; DEPLOYED/PROPOSED), 19 (no claims), 21
(the system = "an agent"; harness = its machinery), PI 2026-09-03: concise, A&A flow, no headings; the opener
"Yes—today with a human at the gate" removed.

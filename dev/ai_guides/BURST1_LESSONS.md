# BURST1_LESSONS.md — Canonical Discovery-Run Failure Taxonomy (bn081125496, burst #1)

**Status:** canonical distillation of the burst-#1 discovery run (2026-08-13 → 2026-08-15).
**Compiled:** 2026-08-15, from five ledgers (~105 mined failure-mode entries, deduplicated here into 17 classes).

**Ledger sources (cited inline as L1–L5):**
- **L1** = `results/sweep106/bn081125496/VISION_QC.md` — figure vision-QC round ledger, rounds R1–R28 (2026-08-14/15).
- **L2** = `notes/CODEX_SED_CONVENTIONS_20260814.md` — Codex external SED-conventions audit (read-only, advisory, 2026-08-14); brief `notes/CODEX_BRIEF_sed_conventions_20260814.md`.
- **L3** = `dev/ai_guides/Temporal.md` defect ledger (+ `notes/CODEX_WHOLE_PROJECT_20260813.md` item A4).
- **L4** = `results/convention_check/sed_grid/` step-8 SED-grid review — OVERVIEW synthesis + `REFUSALS.md` + `BEST_FITS.md`, 11-agent workflow wf_8e873f02 (2026-08-14).
- **L5** = `dev/ai_guides/AgentArchitecture.md` — agent-requirements register (P1–P8 + roster).

Companion authorities referenced: `dev/ai_guides/FigureVisionQC.md` (standing contract S1–S6), `dev/ai_guides/BurstWalkthrough.md` (gate-role + ADOPT mode), `dev/ai_guides/ShippingGate.md`, `dev/ai_guides/SpectralFitting.md` (lessons L1–L29), `LAG_SIGN_VERIFICATION.md` (2026-07-31).

---

## 1. FAILURE-MODE TAXONOMY

Seventeen deduplicated classes. Format per class: definition → instances (round/date) → root cause → caught by → countermeasure location → status.

### F-1. Producer-eyes-only shipping / gate bypass
**Definition:** work delivered to the PI without a fresh-context verifier between production and delivery, including self-invented exemptions from the delivery gate.
**Instances:** 4 producer-eyes-only violations on 2026-08-14/15 alone (L5 P1/P8); the 4th — Bala's upstream-native delt=2.0 MVT figure shipped under an invented "third-party figures exempt" exception (L1 R26, 2026-08-15) — triggered creation of AgentArchitecture.md itself; "just a caption change" exemption also invented (L5 P4). Lineage origin: the bn200524211 montage incident (ShippingGate.md).
**Root cause:** the actor held discretion over the gate's scope; no structural separation of producer and approver.
**Caught by:** PI (Vikas), every time — which by the register's own rule means an agent was missing each time.
**Countermeasure:** NO-EXCEPTION DELIVERY RULE + G-item class (FigureVisionQC.md); FIGURE VERIFIER on EVERY figure, sha256-bound verdict in VISION_QC.md; gate-role rule 2026-08-14 (BurstWalkthrough.md). Mechanical layer — PreToolUse hook on SendUserFile blocking any figure whose sha256 is not in a VISION_QC ledger — designed, **PENDING PI GO**.
**Status:** mitigated by contract; OPEN until the hook is wired.

### F-2. Contract-authority failures (producer-authored / stale / typed-number contracts)
**Definition:** the verification contract itself is wrong — authored by the producer (structurally blind to the producer's own wrong decisions) or carrying hand-typed numbers stale relative to the run.
**Instances:** R12 gate escape — SED pair shipped WITHOUT the 68% band because the producer encoded "no band" into his own contract; gate verified faithfully against the wrong authority; PI caught it 2026-08-15 (L1, L5 P2). R5 — brief demanded "significance number on each block" vs the project colorbar standard (L1). R10 B1 — contract said 12/10 free params (producer doubled k); figure was right, verifier rightly refused (L1). R11 — verifier FAILed correct figures against the PREVIOUS run's sidecar percentages (52%/46% vs true 50%/43%) — 2nd stale-contract incident (L1, L5 P3).
**Root cause:** contract derived from producer intent / typed snapshots instead of PI rulings and same-run machine artifacts.
**Caught by:** PI (the R12 escape); vision gate + adjudication (the two false FAILs, adjudicated in the figures' favor).
**Countermeasure:** standing contract S1–S6 in FigureVisionQC.md with the PI's words QUOTED + DATED as the verifier's independent authority; band absence is itself an S1 violation; verifiers check every printed number against the SAME-RUN sidecar JSON, never producer-typed numbers (R11 protocol change).
**Status:** CLOSED.

### F-3. Prose rules ignored under momentum (the weakest-layer class)
**Definition:** rules that live only as prose addressed to the actor break under task momentum, while code-level rules hold.
**Instances:** prose rules broke 3–4x in ONE DAY (2026-08-15) while EVERY code guard held (L5 P5/P8; Vikas: "simple instructions in skills files will always end up being ignored"). Members: the 4 producer-eyes-only incidents (F-1); "ledger updated" claimed without executing the append — Round-6 verdicts (two hard FAILs) never written, caught by the R8 verifier's round-continuity check, backfilled 2026-08-14 (L1); the s02c defaults incident — tool invoked without reading the skill file, burst-scaling parameters run at defaults (L5 P7).
**Root cause:** enforcement hierarchy reality (strongest first): (a) code that fails closed, (b) hook that blocks the action, (c) artifact carrying its own caveats, (d) dedicated single-rule agent — anything living only as actor-prose is itself a defect.
**Caught by:** PI (repeatedly, same day); vision gate (the ledger-continuity catch).
**Countermeasure:** SKILL-READER agent (opens each step by reading skill+ledger, returns the binding checklist incl. burst-scaled parameters — kills the s02c-defaults class) — **PROPOSED**; SendUserFile hook — **PENDING PI GO**.
**Status:** QUEUED — only mitigated until wired.

### F-4. Port / lineage bugs — method re-implemented from documentation, summaries, or handoffs
**Definition:** a tool port or transcription copies prose (docstring, summary, handoff) instead of executable code, importing the prose's defects and silently dropping the estimator's statistical choices.
**Instances:** **L26 lag-sign inversion** — handbook `temporal.py:1060` DCCF re-implemented from LATBright s02c's SIGN-FLIPPED docstring (their known LAG-10) instead of the correct code; numeric proof ±0.192 s on a synthetic pair; error ~40x underestimated (±0.006 vs −0.205/+0.291 s); catalog −1.09 misread; affects all 106 LAG columns (L3; L1 R24-25, 2026-08-15; root cause found only after PI asked "did you follow the tool we developed?"). Same port dropped MC-median+16/84, the restricted peak search, and the background convention (L3). Gowri+2025 handoff INVERTED the fit constraint (said r_l ≥ r_r; paper: "we always require rl ≤ rr") — would have collapsed every pulse fit; caught by verbatim paper check pre-implementation (L3). Bala's upstream MVT code not adoptable unmodified; --seed does NOT propagate (canonical run recorded seed:null) (L3; L1 R24-25). Legacy 41 mask-compression gap bridging — compressed rows treated as adjacent, synthetic 28–41 keV merged group centered INSIDE the excluded K-edge; 41c's split fixes it, both PNGs verified gap-clean (L2 item 4).
**Root cause:** no numeric-equivalence test against the source's CODE on a synthetic case at port time; documentation is a bug vector; transcription without verbatim-source check.
**Caught by:** cross-tool check (L26 flag 2026-08-10) + two-skeptic proof (`LAG_SIGN_VERIFICATION.md` 2026-07-31) + PI provenance question (root cause); verbatim paper check (Gowri); Codex adversarial reproduction (mask bug); 2026-07-18 MVT audit.
**Countermeasure:** L26 rule in SpectralFitting.md/Temporal.md ("a port must copy the CODE, never the documentation"); interim validated tool `scripts/47c_lag_latbright.py` (imports s02c UNMODIFIED; only 47c numbers quotable); Gowri constraint coded as dr = r_r − r_l ≥ 0 (unviolatable by construction); PORT-VERIFIER agent (numeric equivalence vs source code on a synthetic case before any port is trusted) — **PROPOSED**. temporal.py fix specified but NOT landed; 106-burst LAG re-survey pending; regression test `test_L26_lag_sign_on_reference_burst` pending.
**Status:** OPEN (handbook fix + re-survey outstanding).

### F-5. Statistical-machinery misuse — invalid uncertainty constructions
**Definition:** uncertainty products (bands, error bars, residuals, limits) constructed by statistically invalid means yet rendered indistinguishable from valid ones.
**Instances:** **internal/external coordinate mixup** — 41c sampled `jl.covariance_matrix` (computed in threeML internal transformed coordinates) around external `.value` centers; reported 2.7% spill vs true 50.6% rejection; band-width ratio median 4.20x, up to ~25x (L2 item 6; commit 8961508; L5 P6) — direct violation of the use-native-threeML rule. **Hessian-Gaussian band invalid at heavy truncation** — even the correct native sampler rejects 50.6% for the T_INT Band fit (β on bound) (L2). **Band pathologies F1–F3** — handler crashes strip the 68% band from double-break models in EVERY bin; 95–100%-railed bands are pure bounds geometry; bands exclude their own best-fit curve (L4 F1/F2/F3; L1; R28 containment guard verified 210/210 with 20 suppress-with-note). **Custom 2σ arrows** masquerading as XSPEC upper limits, unlabeled (35+38 arrows) (L2 item 3). **Residual mislabeled pgstat**; brief's XSPEC-delchi claim false for PGstat (L2 item 8). **Quadrature of correlated t5/t95** (Qin+2013 defect; fix: per-realization differencing, ρ measured per burst) (L3). **np.interp on a non-monotonic cumulative** for t5/t95 (L3). **Validity gate blind to rails/residuals** — VALID=True at dAIC +997.9 with ±5σ residual structure; VALID with PL_K railed to absence (L1 R7/R17).
**Root cause:** custom re-implementations of propagation instead of native paths; band construction decoupled from the point estimate; no rail/containment/rejection-fraction checks; independence assumed where correlation exists.
**Caught by:** Codex external audit (coordinate mixup, Hessian, arrows, residual label); vision gate (F1–F3, validity-gate escapes); source audit + PI request (quadrature).
**Countermeasure:** L2 prescribes native `FittedPointSourceSpectralHandler` + suppress-or-replace policy for heavy truncation (NOT yet applied to 41c); F3 containment guard live; F1 handler hardening + F2 cap-and-annotate queued; per-realization T90 differencing + T90_ERR_LO/HI/T5_SD/T95_SD/T5_T95_RHO columns landed (scripts/40).
**Status:** OPEN (41c band replacement, F1/F2, L9/BOUND_CAPPED validity scrutiny outstanding).

### F-6. Estimator-identity failures (point value ≠ sampled quantity; unlabeled estimators)
**Definition:** the quoted number and its quoted uncertainty describe different estimators, or the estimator's identity is not attached to the number.
**Instances:** T90 MC **v1** — bin-index resampling destroyed time order; T90_ERR > T90 in 84/89 bursts (L3). T90 **v2, the WRONG FIX** — MC Poisson-resampled RECTIFIED counts while the point used SIGNED net; bn081224887 point 18.9 s vs MC centre 116.6 s; "more dangerous than the original bug, which at least looked broken" (L3; Codex whole-project item A4, 2026-08-13). Three MVT estimators (Bala canonical / Haar / CWT) risking one column (L3). Headline MVT 33.29±2.60 ms quoted without its z=2.49 (<3σ) material caveat (L1 R26). Temporal numbers quoted without ledger caveats — standing Codex verdict: "should not be used scientifically" until the ledger clears (L3, L5).
**Root cause:** repair written against the symptom without proving point/MC estimator identity; numbers detached from estimator labels and defect ledgers.
**Caught by:** Codex external audit (A4); ledger sanity screen (v1); vision gate (the R26 retroactive caveat).
**Countermeasure:** scripts/40 rewrite — point and MC call the SAME estimator, Poisson draws of RAW counts minus the same fitted background, validated vs frame-matched external values; mandatory estimator-label banner at step 7 (Temporal.md); caveat bound to the number in the measurement record; science (#37/#38) blocked on ledger clearing.
**Status:** CLOSED for T90 core; OPEN for background-fit covariance propagation (declared, unpropagated) and the ledger-clearing block.

### F-7. Nondeterminism — unseeded RNG / seed non-propagation
**Definition:** quoted numbers jitter across renders/runs because MC paths use the global RNG or drop the seed, so quoted errors exclude realization scatter.
**Instances:** threeML MLEResults samples the unseeded global numpy RNG — railed-fraction note jitters 50%/43% vs 52%/46% (L1 R11); T90 MC error bars wobble a few % despite the per-trigger-seed claim (L1 R20); CCF MC lag jittered (L1 R23); Bala MVT --seed does not propagate — two unseeded runs differ 44.0±2.6 vs 56.5±2.3 ms, ~4σ by their own quoted errors (L1 R24-25).
**Root cause:** global RNG without seed plumbing; per-fit error omits realization scatter.
**Caught by:** vision gate (cross-render comparison + verifier reruns) and producer reruns.
**Countermeasure:** 41c seed doctrine (`np.random.seed(20260814)`); CCF seeded (R23); MVT_SEED=20260815 disclosed; caveat bound to canonical 33.9±2.9 ms.
**Status:** QUEUED — Bala runner seed bug + T90 wobble unresolved; no global determinism guard exists.

### F-8. Instrumental artifacts read as physics
**Definition:** detector-level calibration structure absorbed by model components and crowned by model selection as physical signal.
**Instances:** **L28 edge blackbodies** — census over 10 intervals / ~90 +BB fits: ZERO real thermal evidence; bimodal kT — edge-constrained 1.1–1.9 keV cluster feeding the na/nb low-edge split INCLUDING THE BIN2 AIC WINNER (BANDBB kT=1.55 keV, 3.92·kT=6.1 keV < 8 keV fit edge), plus 10–40 keV null-normalization impersonators (L4, L1 R19). **EAC rails F10** — EAC_NB delta-function-railed at 0.800 across all rows of 5 bins; EAC_B1 at 1.200 across 2+ bins; clamp converts calibration mismatch into fake spectral structure (L4 F10). **na-vs-nb split** — same-energy opposite-sign residuals grid-wide (e.g., bin2 na +2.7σ vs nb −3.6σ at 10–15 keV, untouched by every model incl. the winner) (L4 §2). One diagnostic loss: TINT CPLBB (kT=27.3 keV, valid, ΔAIC 0.95) refused render — the burst's only mid-band BB candidate unreviewed (L4).
**Root cause:** a +BB is the lowest-cost absorber of NaI 8–15 keV edge/calibration structure; AIC rewards it; EAC bounds [0.8,1.2] tighter than the calibration disagreement demands.
**Caught by:** verifier notes layer (11-agent workflow wf_8e873f02) applying the L28 census.
**Countermeasure:** L28 edge-feature protocol (SpectralFitting.md, per Tierney+2013 / Ravasio+2019 App. B) applied as census; PI ruling 2026-08-15: EAC bounds [0.8,1.2] accepted as calibration prior (F10 closed); §5 census table = reusable method template.
**Status:** CLOSED for this burst's thermal claim; OPEN actions: nb-response caution on any low-energy feature, TINT CPLBB render+review.

### F-9. Model-selection over-reading (ties, margins, degenerate tails, extrapolation)
**Definition:** single-number AIC ranking read beyond what it licenses.
**Instances:** TINT top-4 statistical dead heat reported as a single winner (L4, L1 R19); bin8 ΔAIC<1 tie hides order-of-magnitude 30 MeV flux divergence (β=−2.2 falling vs −1.67 rising) (L4); bin2 top-11 ΔAIC<6 span driven by ONE calibration feature (L4); degenerate runner-up tails — valid=NO railed clones counted as model diversity (L4, all ten notes); R6 `ep_kt_correlation.png` — 6-point Ep–kT power-law fit + p=0.79 despite ZERO significant BBs (max LRT 7.39<9.2), analysis the fits do not license (L25 violation), plus T_INT (BLOCK=−1) plotted as a mid-burst point making kT=1.76 a false outlier and the "line of death" at α=−1 instead of −2/3 (L1 R6).
**Root cause:** no predictive-spread check at the energies that matter; census denominators counting invalid fits; legacy engine plotting with no gate between fit table and derived-analysis plots.
**Caught by:** vision gate (R6 hard FAILs; per-bin reviewers + synthesizer).
**Countermeasure:** reporting rules — ties reported as ties, qualifications in OVERVIEW.md (L1 R19); scripts/10 plot-block fix queue (exclude BLOCK=−1, −2/3 line, error bars shown, winner-family labels, route through plot_style, suppress unlicensed correlations); BB-census rule definition still OPEN at project level (Codex whole-project audit).
**Status:** QUEUED (scripts/10 fixes; census rule; tie-reporting rule into the paper layer).

### F-10. Provenance-binding failures (products not bound to the run that made them)
**Definition:** figures/tables/rows that re-derive, re-fit, or hand-carry values instead of reading and asserting stored decisions, leaving PNG↔source binding unprovable.
**Instances:** 41c live figure fit at default seeds, no stored-row/seed/EAC/detector assertions, minimizer unpinned; AIC agreement (0 and +5.56e-5) coincidence, not design (L2 item 9). Unconditional LLE drop at 41c:187 — figure likelihood ≠ engine likelihood for LLE-bearing bursts (L17 violation) (L2). Reference-detector recomputation (min-angle) instead of reading the stored choice — coincides with na by luck (L2). Hardcoded sweep106 blocks + CURRENT approved catalog = era mixing; no figure sidecar (L2). Audit-target hash mismatch — brief's 41c hash did not identify the audited file (L2). F6 header-AIC rounding vs table (2725.0 vs 2724.9); F5 legend-k vs stored-EAC last-digit drift (L4). Catalog row under-records the skill's promised Outputs — R²≥0.7 gate unverifiable from the row (L1, step-7 record). Incomplete human_run stood as the canonical MVT (empty upstream/, died at startup) until fresh run superseded it (L1). bn130310840 failed fit (T90 17.91±68.24 vs 2.09 s true) committed and unchallenged for WEEKS — no admission gate (L3).
**Root cause:** recompute-instead-of-read pattern; no machine-readable sidecar; no admission/completeness gate between fit and catalog; independent rounding.
**Caught by:** Codex external audit (41c cluster); vision gate (F5/F6, step-7 records); blind re-run — i.e., caught LATE, no automated guard (bn130310840).
**Countermeasure:** L2's 7-step guard (explicit fit table + sidecar, resolve exact row, seed from row, pin MINUIT, hard-fail |AIC_live−AIC_stored|<0.1, provenance stamp, explicit escape hatch) — prescribed, NOT applied; EAC serialization landed (commit d5adbf3); numbers now bind to same-run sidecars (L5 P3, deployed); single-provenance-value rounding queued (F6); catalog schema extension queued; T90 quality gate (T90_ERR<T90 AND within ~2x block span) in checklist, bn130310840 refit still open.
**Status:** OPEN — the largest unclosed class by count.

### F-11. Numerical- and fail-loud-safety defects
**Definition:** numerics accepted without convergence/validation assertions; exceptions swallowed; state mutated without restore.
**Instances:** fixed 16-point log-trapezoid: 86.85% error in the b1 CPL 28.5–36.48 MeV group (L2 item 1, sign-off blocker 1). Ill-conditioned ratio-unfolded tail arrows ~1e59–1e109 above the curve (silent-capping forbidden) (L2 item 5). Gap-split edge cases unguarded — empty mask dereferences parts[0]; descending EBOUNDS neither supported nor rejected (L2 item 4). `except Exception: pass` around EAC activation — figure producible in the wrong nuisance state, no invariant fires (L2 item 7, blocker 6). Model-state mutation without finally-restore — an exception mid-sampling leaves the MLE curve silently wrong (L2 item 6). y-floor clipped two VALID BGO arrows from the headline SED while the invariant reported 97/97 retained; xlim padding violated the full-fitted-range rule (L2 item 5, blocker 4). Railed/invalid values ingested by autoscale (BETA=−5 on frames, PL_K axis stretched ~8 decades; MINOS endpoint railed at 1e-15 stretching K_BB — rail enters via the error bar, a contract gap) (L1 R16/R17).
**Root cause:** happy-path validation; broad exception handlers on state-changing operations; cosmetic post-processing applied after the accounting invariant.
**Caught by:** Codex external audit (adaptive-quadrature re-derivation, edge-case probing, PNG-level inspection); vision gate (R16 structural catch beyond contract).
**Countermeasure:** prescriptions in L2 (adaptive quad + RuntimeError guard; validation snippets; restore-in-finally; exact xlim; off-scale markers with stamped count); autoscale-from-VALID-only landed (L1); EAC fail-loud asserts queued.
**Status:** OPEN/QUEUED — most prescriptions not yet applied to `scripts/41c_paper_sed.py`.

### F-12. Figure-geometry / layout defects (incl. fix-induced regression)
**Definition:** rendering defects — glyph collisions, data occlusion, clipping, tofu, z-order — plus the meta-pattern that each local fix spawns a new defect elsewhere.
**Instances:** stamp/label collisions across 7 separate rounds (L1 R1, R9 N1/N2, R14 B1, R16 — 3 of 4 param-evolution figures FAIL, R21 — round-16 class re-introduced in 41d, R22 — 0–1 px descender graze caught by pixel map). Occlusion family: R10 B3 legend over 8–25 MeV b1 points; R12 N1 note bbox over the ~15 keV nb point; R13 B1; R14 B2 — occlusion RELOCATED not removed (L1). Fix-induced regressions: R2 white-bbox notches bar tips; R10 arrow-removal → legend occlusion; R13 stamp-outside-axes → R14 title overprint; four cycles (R12–R15) to clear the SED pair (L1). F4 footer lines inside axes across 6 bins, once UNDER the data layer (L4). F8 bin7 tick-label collision + clipped error-bar cap (L4). U+2713 tofu (STIX lacks the glyph) (L1 R10 B2). Incomplete hardcoded 3-detector color map, silent gray fallback (L2). F7 CPL y-range model-driven two decades below faintest datum (L4).
**Root cause:** offsets tuned to one panel geometry reused across geometries; occluders moved not removed; no render-time collision/z-order/glyph checks; local fixes without whole-layout re-verification.
**Caught by:** vision gate (fresh-context pixel-calibration verifiers; every fix re-render returns to a FRESH verifier).
**Countermeasure:** footer-stamp placement declared the ONLY sanctioned pattern (R23); 41c margin-row form deprecated; notes zorder=3 below data; out-of-axes footer above artists queued (F4); scripts/44 bbox fixes; plain-text glyph replacement.
**Status:** CLOSED for the shipped set; F4/F7/F8 code fixes QUEUED.

### F-13. Mechanical slips & fabricated restatements
**Definition:** numbers or facts restated from memory/inference instead of read from the product; assembly by fragile text methods.
**Instances:** caption "handbook gave −0.70" FABRICATED BY NEGATION (actual −1.09) (L1 R24). ApJ Table-1 bins 0↔1 (AIC AND parameters) and 3↔5 (AIC) TRANSPOSED — winner-grep swept ALL_MODELS_TABLES.md, shifting row mapping (L1 R27). Draft prose: spliced per-detector background windows + wrong poly order; untraceable "factor ~8" (replaced with traceable ≥5); bin2 called PEAK when it is the RISE (L1 R27). False "not checkable" claims — BCAT number declared unverifiable while the mask lives in `grb_sample.ecsv`; 3 instances 2026-08-13 (L5). "Ledger updated" claimed without the write (L1 R6→R8; also F-3).
**Root cause:** violation of "read the product before re-deriving"; over-broad grep; prose from memory; narrow-search failure reported as data property.
**Caught by:** vision gate (R24 reading, R27 number-by-number verification vs products); PI (not-checkable class).
**Countermeasure:** every restated number verified against its primitive (contract); script-based table source verification; NUMBERS VERIFIER bound to `grb_sample.ecsv` DEPLOYED at step 1; general rule "recompute printed numbers from the run's own products, fail loudly" DEPLOYED.
**Status:** CLOSED.

### F-14. Silent absence & silent suppression
**Definition:** products that failed, were refused, or were excluded simply do not appear — indistinguishable from never-attempted; or defective products hidden instead of annotated.
**Instances:** C7 silent suppression of railed bands (2026-08-15, flagged in TINT; fix queue bans it — cap-and-annotate, never suppress) (L4). Guard refusal destroyed the one diagnostically valuable figure (TINT CPLBB) alongside 29 duplicative junk panels (L4, REFUSALS.md cross-check). Step-7/step-9 figure exclusions initially undisclosed in the draft (L1 R27d). Class-B crashes (5) where all 5000 draws railed and threeML `equal_tail_interval` crashed on empty variates — should classify as BOUND_CAPPED, not crash (L4 F1).
**Root cause:** product set encodes only successes; refusal criteria keyed to fit pathology, not diagnostic value; disclosure decisions not surfaced in-text.
**Caught by:** vision gate (TINT reviewer; refusals cross-check; R27 draft verifier).
**Countermeasure:** BEST_FITS/REFUSALS absence ledgers shipped with every step-8 product set — absence always labeled (L5, deployed); quarantined-lag footnote + in-text disclosure added (R27); render-guard criteria amendment OPEN.
**Status:** mostly CLOSED; guard-criteria amendment + TINT CPLBB recovery OPEN.

### F-15. Frame / scope mis-attribution
**Definition:** a difference of frame, window, band, episode, method, or population-vs-individual scope read as (or hidden inside) a physical result.
**Instances:** **L29** — T90 window growth first diagnosed as "noisy tail"; truth: 5σ, ~780 net counts of REAL emission in the 11.9–30 s gap outside every fitted window; PI's objection ("background-subtracted bins scatter about zero") killed the noise story (L3, 2026-08-13). Windowed T90 (8.50±0.18 s) vs Shao+2017 (9.28±0.61 s) — difference largely tail excluded BY CHOICE; T90 is a LOWER LIMIT where emission continues (L3). Qin+2013 population-mean E^−0.2 used as a per-burst predictor — one lucky anecdote (bn090530760 factor 0.72) promoted a sample-mean regression to an individual law (L3, PI re-read 2026-08-13). Count-space vs response-corrected-fluence T90 conflation (L3). bn120624933 episode-3 vs whole-burst "mismatch" (L3, P3 diff). Nominal mask targets (8.1/33/40/300) vs channel-true drawn edges (7.310/32.923/40.065/278.425) — adjudication recorded so future verifiers do not re-flag (L1 R8).
**Root cause:** diffing before aligning frames; control measurement skipped in favor of the tempting explanation; measurement space unlabeled.
**Caught by:** PI (L29 objection; Qin re-read); source audit; P3 reconciliation diff protocol; vision gate (R8 adjudication).
**Countermeasure:** L29 doctrine (window is a human decision; wrong version recorded BECAUSE it is the tempting one) + TAIL_OUTSIDE_WINDOW_SIG column + T90_WINDOW_TRUNCATED flag + mandated caveat (Temporal.md); label-the-space rule; blind-first + P3 attribution (frame/method/band BEFORE the word "discrepancy") DEPLOYED at step 9; per-burst band-slope measurement PENDING before frozen numbers.
**Status:** CLOSED (doctrine) / QUEUED (band-slope measurement).

### F-16. Prior-art & authority blindness
**Definition:** re-deriving what the project family already proved; re-opening what the PI already decided; proposing "discovery" on published territory; reading literature before freezing own products.
**Instances:** lag-sign inversion PROVEN in `LAG_SIGN_VERIFICATION.md` 2026-07-31 (two-skeptic protocol), RE-DERIVED from scratch 2026-08-15 — nobody swept SinglePulse_Temporal/LATBright/PulsewiseLag notes first (L5). Sessions re-adjudicating the PI's recorded Stage-1 decisions (16 rows/13 bursts of accepted flags treated as open problems) (L5). lag–MVT proposed as discovery — Sonbas+2013 owns it, Göktaş+2025 measured slope 1.01; two of our criticisms RETRACTED (L3). Literature-anchoring risk (L5, step-9 design). Inheriting published defects: Qin+2013 P_KMM self-contradiction (DO NOT INHERIT), irreproducible BB figure; Lu+2018 contradicts its own sign convention in adjacent sentences (L3).
**Root cause:** each session treats its own context as the whole of knowledge; no mandated family-wide prior-art sweep; published numbers carry unstated conventions and defects.
**Caught by:** PI/distiller (duplicate recognized after the fact); PI feedback (Stage-1 flags ARE decisions); literature check; PDF source audits.
**Countermeasure:** PRIOR-ART READER (sweep family notes before any root-cause/redo) — **PROPOSED**; ADOPT-mode rule for steps 2–5 (BurstWalkthrough.md, deployed); blind-first harvest + per-claim audit records with do-not-inherit flags (deployed).
**Status:** QUEUED (PRIOR-ART READER); rest CLOSED.

### F-17. Verification-machinery meta-defects
**Definition:** defects in the checking machinery itself — false corroboration, broken blinding, ambiguous rules, unfiltered auditors, improvised architecture.
**Instances:** degenerate stress-test pair — CPL-vs-Band "model-sensitivity" demo used a Band with β=−4.999997 (ΔN2LL 0.00247 from CPL): agreement proved nothing (FXT FALSE-CORROBORATION class) (L2 item 2). F9 — AIC burned into every figure header makes the blind two-pass residual read impossible; PI ruling 2026-08-15: statistic stays, upgraded to PGstat/dof+AIC, read as supplement (S1c) (L4, L1). S4 rule read OPPOSITELY by two reviewers on identical behavior — a contract defect (L4 F7). External-auditor over-findings — Codex right about the invalid band, but findings that did not survive primitive-level re-check were discarded at the primitive, never by agent-vs-agent comparison (L5 P6). Private-API overclaim ("sanctioned extraction point" for `_construct_counts_arrays`) (L2 item 10). Reactive, improvised architecture — gates "improvised after each failure" until the 4th shipping violation forced AgentArchitecture.md (L5). PI as last line of defense — every PI catch = a missing-agent register row by definition (L5).
**Root cause:** verification designed ad hoc; independence must differ at the PRIMITIVE, not just the agent; ambiguous normative rules admit contradictory readings.
**Caught by:** Codex (degenerate pair); synthesizer (S4 inconsistency); adjudication (over-findings); PI (architecture).
**Countermeasure:** EXTERNAL AUDITOR row — milestone audits, advisory-only, adjudicated finding-by-finding (deployed); S1c contract item; S4 single normative reading OPEN; AGENT REQUIREMENTS REGISTER owned by DISTILLER, same-session upkeep; register FREEZES at burst #10 and gets CODED for #11–#106, post-freeze changes only by PI-approved amendment with motivating incident attached.
**Status:** OPEN (S4 wording; sign-off-conditioned rerun of the stress pair with materially different shapes + one LLE-bearing burst).

---

## 2. CATCH-LEDGER — what each layer caught (empirical case for the layered architecture)

Counts are deduplicated instances (not ledger rows; ~105 rows collapse across L1/L3/L5 overlaps). "Caught" = first layer that surfaced the defect.

| Layer | Catches | Highest-value catches |
|---|---|---|
| **Vision gate** (fresh-context verifiers: 28 rounds L1 + 11-agent grid L4) | **~55** | bin2 AIC-winning BB reclassified as edge artifact (0/90 thermal, killed a false photosphere claim); R6 twin hard-FAIL science plots (false kT outlier, wrong line-of-death, unlicensed Ep–kT correlation); Table-1 transpositions + prose defects in the ApJ draft (R27); fabricated −0.70 caption; F1–F3 band pathologies; EAC rails (F10); unseeded-RNG jitter in 4 estimators; occluded real data points; 2 correct refusals of figures whose CONTRACT was wrong; ledger-continuity catch of the fake "ledger updated" |
| **External audit — Codex** (whole-project 2026-08-13; SED conventions 2026-08-14) | **~27** | invalid 68% band (internal/external coordinate mixup, width off median 4.2x, up to ~25x; 2.7% claimed vs 50.6% true rejection) — headed into the flagship figure; T90 v2 fix sampling a DIFFERENT estimator than the point (worse than the bug it replaced); 86.85% integrator error; false model-invariance claim + degenerate stress pair; 2 valid arrows silently clipped while the invariant said 97/97; unguarded live fit whose AIC agreement was coincidence; `except Exception: pass` on EAC activation; 2 defects in the producer's OWN BRIEF (stale hash; wrong XSPEC delchi claim) |
| **PI (Vikas)** | **12** | the 2 genuine gate escapes (missing 68% band via producer-authored contract; producer-eyes-only third-party figure) — each closed with a structural amendment; 4 producer-eyes-only deliveries total; L29 noisy-tail objection → 5σ/~780-count real-emission finding; the lag provenance question → L26 root cause; Qin population-vs-per-burst re-read; false not-checkable class; gate-role and architecture rulings. **Each PI catch = a missing-agent debt by standing rule.** |
| **Source/PDF verification** | **6** | Gowri r_l≤r_r inversion (would have collapsed EVERY pulse fit); Qin P_KMM self-contradiction + irreproducible BB figure (not inherited); Lu+2018 self-contradictory sign convention; count-space conflation; correlated-quadrature defect; lag–MVT prior-art position |
| **Code-layer screens / protocol design** | **~8** | T90_ERR>T90 in 84/89 sanity screen (v1); 41c gap-split fix; np.interp first-crossing convention; P3 diff attribution; D4 window-drift guard; MVT audit 2026-07-18; absence ledgers; blind-first design |
| **Two-skeptic protocol** | **1** | lag-sign inversion PROVEN at the primitive (2026-07-31) — later wastefully re-derived (F-16) |
| **Never / caught late** | **3** | bn130310840 pathological row sat committed for WEEKS (blind re-run, no gate fired); TINT CPLBB diagnostic figure still unseen; the 2026-07-31 lag proof forgotten until after re-derivation |

**Central empirical result (L5 P8):** on 2026-08-14/15 EVERY code guard held (AIC ≤0.1 guard, EAC asserts, convention guard) while 4 prose rules broke in one day. Enforcement strength ordering confirmed: code-fails-closed > hook > caveat-carrying artifact > dedicated agent > actor-prose.

---

## 3. WHAT HELD — mechanisms that never failed

1. **Code guards fail closed** (L5): AIC ≤0.1 agreement guard, EAC asserts, convention guard — zero failures across the run while prose broke 4x.
2. **Same-run sidecar binding** (L1 R11 protocol): after the switch from producer-typed numbers, pixel-level number verification held every shipped figure to its same-run sidecar — including twice correctly refusing figures whose contract, not figure, was wrong.
3. **sha256-bound verdicts in VISION_QC.md** (L5): made every round, verdict, and violation countable and datable — this auditability is what converted the 4 producer-eyes-only incidents into P1/P4/P8 and the pending hook.
4. **Fresh-context verifier per re-render** (L1): no producer self-clearance; caught every fix-induced regression (R2→R15 chains) that producer re-checks would have missed.
5. **Primitive-level adjudication of external findings** (L5 P6): every surviving Codex finding was correct; every non-surviving one was killed at the primitive, so nothing spurious was acted on and nothing true was lost to agent-vs-agent name-comparison.
6. **Two-skeptic verification** (LAG_SIGN_VERIFICATION.md): the one deployment produced a durable primitive-level proof.
7. **Absence ledgers** (BEST_FITS/REFUSALS): 29/30 unrendered panels confirmed duplicative junk; the 1 diagnostic loss was isolated instead of vanishing silently.
8. **The gate catching its own failure modes** (L1 R10/R11/R12): stale contracts and producer-authored contracts were themselves surfaced by gate rounds and converted into standing contract items S1–S6 — the designed backstop working.
9. **The audited positives** (L2): XSPEC eeufspec group-integrated numerator construction, EAC arithmetic vs threeML source, both demo fits reproducing stored AICs, threeML's genuine lack of a ratio-unfolded plot — confirmed once, need not be re-litigated.

---

## 4. FREEZE RECOMMENDATIONS — per class, the agent/hook/guard the frozen pipeline needs

Register mapping: existing rows in `AgentArchitecture.md` (FIGURE VERIFIER, NUMBERS VERIFIER, EXTERNAL AUDITOR, DISTILLER; proposed: SKILL-READER, PORT-VERIFIER, PRIOR-ART READER). NEW rows named **NR-x** where the taxonomy reveals gaps. Register freezes at burst #10 and gets CODED for #11–#106.

| Class | Required mechanism | Register row | State |
|---|---|---|---|
| F-1 shipping bypass | PreToolUse hook on SendUserFile: block any figure whose sha256 ∉ VISION_QC ledger | FIGURE VERIFIER + hook | Hook designed, **PENDING PI GO** — the single highest-leverage pending item |
| F-2 contract authority | Verifier authority = FigureVisionQC.md S1–S6 (PI-worded, dated) + same-run sidecar numbers only | FIGURE VERIFIER / NUMBERS VERIFIER | DEPLOYED |
| F-3 prose ignored | SKILL-READER opens every step: reads skill+ledger, returns binding checklist incl. burst-scaled parameters | SKILL-READER | PROPOSED — wire before freeze |
| F-4 port/lineage | PORT-VERIFIER: numeric equivalence vs source CODE on a synthetic pair before any port is trusted; regression test per port | PORT-VERIFIER | PROPOSED; `temporal.py` L26 fix + 106-LAG re-survey must land BEFORE freeze |
| F-5 invalid uncertainty | **NR-1 BAND-VALIDITY GUARD**: native-threeML propagation only; rejection-fraction threshold (fail >1% per threeML's own warning); curve-in-band containment (live, R28); all-railed draws → BOUND_CAPPED, never crash, never silent-suppress | new row | F3 guard live; F1/F2 + 41c native replacement OPEN |
| F-6 estimator identity | Estimator-label banner mandatory on every temporal quote; point/MC same-estimator assertion in MC code | artifact rule (deployed) + code guard | DEPLOYED for T90; extend to MVT/lag columns |
| F-7 nondeterminism | **NR-2 SEED AUDITOR**: every MC path declares a seed, proves propagation (double-run equality check in CI); quoted error must include realization scatter or carry a caveat | new row | 41c doctrine partial; Bala runner bug OPEN |
| F-8 artifact-as-physics | L28 census as a standing step-8 stage; EAC-rail report (any constant at a bound ⇒ flag every low-energy feature confounded) | step-8 roster + skill L28 | Census method DEPLOYED; automate the rail report |
| F-9 selection over-read | **NR-3 TIE-REPORTER**: ΔAIC<threshold ⇒ report tie; census denominators exclude valid=NO; extrapolation-divergence flag on any HE flux quote; unlicensed-analysis gate between fit table and derived plots | new row | Rules recorded; scripts/10 plot fixes + census rule QUEUED |
| F-10 provenance binding | **NR-4 STORED-SOLUTION BINDING + CATALOG ADMISSION GATE**: figures seed from stored rows, pin minimizer, hard-fail AIC mismatch, emit sidecar (8-link provenance spine); catalogs accept rows only through sanity+completeness+schema gate (T90_ERR<T90, ~2x block span, outputs complete, schema = skill Outputs) | new row (two guards) | L2 7-step guard prescribed, NOT applied; bn130310840 refit open |
| F-11 numerical safety | Adaptive quadrature + convergence assertion; no bare `except: pass` on state-changing ops; restore-in-finally; off-scale markers with stamped counts; EBOUNDS validation | code guards (fix queue) | OPEN — apply L2 prescriptions to 41/41c before any SED ships again |
| F-12 layout | Footer-stamp-only pattern (R23, sanctioned); **NR-5 PIXEL-COLLISION CHECK** at render time (the R22 0–1 px catch, mechanized); glyph-coverage check vs mandated font | code guard | Footer pattern DEPLOYED; pixel check to automate |
| F-13 mechanical slips | NUMBERS VERIFIER recomputes every printed/restated number from run products (deployed); tables assembled by script from named source files, never grep | NUMBERS VERIFIER | DEPLOYED; table-by-script now standard (R27) |
| F-14 silent absence | Absence ledgers (BEST_FITS/REFUSALS) at every product-bearing step; refusal criteria amended to preserve diagnostic-value fits (valid + ΔAIC<2 ⇒ must render) | artifact rule + **NR-6 REFUSAL-TRIAGE** amendment | Ledgers DEPLOYED; guard amendment OPEN; render TINT CPLBB |
| F-15 frame mis-attribution | TAIL_OUTSIDE_WINDOW_SIG + T90_WINDOW_TRUNCATED columns (deployed); label-the-space rule; P3 frame/method/band-before-"discrepancy" (deployed); per-burst band-slope measurement before frozen numbers | code guard + contract | Mostly DEPLOYED; band-slope measurement PENDING |
| F-16 prior-art blindness | PRIOR-ART READER (family-notes sweep before any root-cause/redo); ADOPT mode steps 2–5 (deployed); blind-first step 9 (deployed) | PRIOR-ART READER | PROPOSED — wire before freeze |
| F-17 machinery meta | One normative reading per style rule (fix S4 wording); stress tests must use materially different primitives (FXT false-corroboration rule); external audits advisory + primitive-adjudicated (deployed); register frozen at #10, amendments only with motivating incident | contract | S4 rewrite + degenerate-pair rerun OPEN |

**Priority order for the freeze:** (1) SendUserFile hook [F-1]; (2) NR-4 stored-solution binding + catalog admission gate [F-10]; (3) NR-1 band-validity guard + 41c native band [F-5]; (4) temporal.py L26 fix + re-survey [F-4]; (5) SKILL-READER + PRIOR-ART READER [F-3, F-16]; (6) NR-2 seed auditor [F-7]; (7) the remaining queued code guards [F-9, F-11, F-12, F-14].

---

## 5. TRANSFER TABLE — burst-independent vs burst-1-specific

**Burst-independent (apply to bursts #2–#106 unchanged):**
- All 17 class definitions and their countermeasures; the enforcement hierarchy (code > hook > artifact > agent > prose) and its empirical basis.
- Standing contract S1–S6 + S1c; NO-EXCEPTION delivery rule; gate-role rule; fresh-verifier-per-re-render; sha256-bound verdicts; same-run sidecar binding.
- L26 (port the code, never the docs; convention label on every lag), L28 (3.92·kT vs fit-edge census method), L29 (windowed T90 = lower limit; window is a human decision; TAIL_OUTSIDE_WINDOW_SIG), L25 (no correlation analysis without significant components), L17 (data quality, not detection significance, gates inclusion).
- scripts/40 T90 estimator (same-estimator MC, first-crossing, per-realization differencing, per-trigger seed); footer-stamp pattern; autoscale-from-VALID-only; F3 containment guard; absence ledgers; ADOPT mode; blind-first + P3 attribution; tie-reporting; estimator-label banners; do-not-inherit flags on published defects.
- The catch-ledger itself as the standing justification for the layered roster.

**Burst-1-specific (facts about bn081125496, not rules — do NOT port the numbers):**
- EAC_NB=0.800 / EAC_B1=1.200 rail pattern and the na-vs-nb 8–20 keV split (this burst's detector set; the *rail-report mechanism* transfers, the verdict does not).
- bin2 BANDBB kT=1.55 keV reclassification; the 0/90 thermal census result; TINT CPLBB (kT=27.3 keV) recovery action; bin4 −4.1σ @ 20 MeV background feature; bin8 tie-extrapolation divergence.
- ~780 net counts / 5σ tail in the 11.9–30 s gap; T90 8.50±0.18 s lower limit vs Shao+2017 9.28±0.61 s; MVT 33.9±2.9 ms canonical + z=2.49 caveat; lag +0.705 −0.205/+0.291 s @ 39.4σ (47c, hard leads).
- The R8 channel-true-edge adjudication VALUES (7.310/32.923/40.065/278.425 keV) — the *record-the-adjudication* practice transfers.
- Demo-coincidences that must NOT be assumed elsewhere: 41c's min-angle detector matching the stored reference; live-fit AIC agreement; absence of LLE (LLE-bearing bursts make the 41c LLE-drop a likelihood change, not a display choice).

---

## EXECUTIVE DIGEST

1. ~105 mined failure entries from 5 ledgers collapse to 17 classes; the run's defining split: EVERY code guard held while prose rules broke 4x in one day — enforcement must be code/hook, never actor-prose.
2. Catch counts: vision gate ~55, Codex external audits ~27, PI 12, source/PDF checks 6, code screens ~8; only 3 defects were caught late or never (bn130310840's weeks-committed bad row, the unrendered TINT CPLBB, the forgotten 2026-07-31 lag proof).
3. The two genuine gate escapes (missing 68% band via producer-authored contract; producer-eyes-only shipping) were both PI catches, each closed structurally (S1–S6 verifier authority; NO-EXCEPTION rule) — every PI catch is by rule a missing-agent debt.
4. Highest-value saves: the invalid coordinate-mixed 68% band (width off up to ~25x), the T90 fix sampling a different estimator than its point value, the sign-flipped-docstring lag port (~40x error underestimate, all 106 LAG columns), and the bin2 AIC-winning blackbody exposed as a detector-edge artifact (0/90 thermal).
5. Largest unclosed class is provenance binding (F-10): 41c IS now bound (stored-solution seeding + |dAIC|<0.1 hard guard, 2026-08-15 — miner read the pre-fix Codex text), but catalogs still lack an admission gate and the L2 7-step guard is prescribed but unapplied. [ADJUDICATED at synthesis review]
6. Statistical machinery (F-5): the native-threeML band replacement, the >=95%-railed suppression, and the F3 curve-containment guard ALL LANDED (rounds 13-28); still open: F1 band-handler crash on double-break models (malformed-interval branch). [ADJUDICATED at synthesis review]
7. Freeze priorities: SendUserFile sha-gate hook (PENDING PI GO), NR-4 stored-solution binding + catalog admission gate, NR-1 band-validity guard, temporal.py L26 fix + 106-burst lag re-survey, then SKILL-READER / PRIOR-ART READER / NR-2 seed auditor.
8. New register rows proposed: NR-1 band-validity guard, NR-2 seed auditor, NR-3 tie-reporter, NR-4 stored-solution binding + catalog admission gate, NR-5 pixel-collision check, NR-6 refusal-triage (diagnostic-value fits must render).
9. Transfer: all 17 classes, contracts, and code guards apply to bursts #2–#106 unchanged; only the burst-1 numbers (EAC rails, edge-BB census verdict, tail counts, T90/MVT/lag values, demo coincidences) stay local.
10. File: /Users/salim/Desktop/Projects/SingleRest/Two_Breaks/dev/ai_guides/BURST1_LESSONS.md — canonical; amendments post-freeze only via PI-approved register change with the motivating incident attached.

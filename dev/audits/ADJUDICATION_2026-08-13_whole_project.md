# Adjudication — Codex whole-project audit, 2026-08-13

**Codex verdict: DO NOT SIGN OFF.** I agree with the verdict. Report:
`notes/CODEX_WHOLE_PROJECT_20260813.md` (45 KB, 17 items, all NOT CONFIRMED except two
successes it names explicitly). Every finding below was re-derived by me at the primitive
before any action — Codex has been right about real bugs and wrong about others.

## The one that mattered most — A4, T90 errors: CONFIRMED, and my earlier "fix" was worse than the bug

Reproduced independently on bn081224887: the point estimate came from **signed** net counts
(18.9 s) while the Monte Carlo sampled **rectified** counts `max(net,0)` — 40.8% more counts —
and sat at **116.6 s**. The σ I had been quoting described a different estimator entirely.
The original index-shuffling bug at least *looked* broken (`T90_ERR > T90` in 84/89 rows);
mine produced small, plausible, meaningless errors. That is the more dangerous failure.

**Caught in time:** the overnight chain was mid-run generating the all-106 temporal catalog
with that estimator. Killed before it wrote a file — **no temporal catalog was ever published
from either broken version.**

**Fixed properly** (`scripts/40::_tx_core` + `_tx_with_mc`): declared search window (the
approved source window), one estimator for both point and MC, Poisson realizations of the
**raw** counts minus the same fitted background (no rectification anywhere), an explicit
first-crossing convention because the cumulative net curve is *not* monotonic — `np.interp`
was invalid on it in every previous version — n_mc = 1000, per-trigger seed, plus a new
`T90_WINDOW_TRUNCATED` flag marking durations bounded by our window rather than the burst.
Validated against Codex's own **frame-matched** external recomputations: bn081224887
14.84 ± 0.39 vs 17.40 ± 1.31 (1.9σ); bn110721200 13.24 ± 0.36 vs 14.11 ± 2.19 (0.4σ).
Not propagated: background-model uncertainty — stated, not hidden.

## Also fixed tonight

- **D1 (P0 leakage): CONFIRMED, though disclosed.** bn150721242's P0 does copy that burst's
  own fit values — which I had disclosed in prose, but prose cannot be filtered mechanically.
  Implemented Codex's prescription: every P0 now carries `P0_STATUS` ∈ {`BLIND_FROZEN`,
  `ARCHIVAL_POSTFIT`, `NONBLIND_CONTAMINATED`}. Current census: **13 / 48 / 1**. Blind-
  prediction scoring must accept only `BLIND_FROZEN`; the 48 archival ones rest on a previous
  production run (a legitimate, disclosed prior) and the single contaminated file is now
  machine-excludable.

## Accepted, queued (not done tonight — they need daylight or a decision)

- **A1 tests:** two of the three failures are *stale tests* encoding a superseded rule (they
  reject exactly the 20 ledgered human overrides, no other row); the third,
  `test_approval_stamps`, correctly exposes the real open gate — bn120624933's LLE row is
  `ai_inherited_PENDING_HUMAN` **and is being used in fits**. Vikas's call: confirm or
  quarantine that row. The two stale tests should be taught the ledger join.
- **A3 census completeness:** the union rule repaired Band+BB/CPL+BB, but the engine emits
  other nested BB pairs (e.g. SBPL+BB) the census still ignores — so "significant BB" is not
  yet uniquely defined. Must be settled before any population number.
- **A5 / B1 panel fidelity:** panels can use a different detector set, reference detector, or
  interval than the engine row they claim to display; and some step figures compute their own
  background rather than the production estimator. This is the montage-lie class again, one
  level down. Highest-value fix after the census.
- **B2, B4:** the product manifest is existence-based (a present-but-empty file counts as
  present); the cross-system diff can mistake a binning difference for a parameter one.
- **C1:** `tests/test_lessons.py` passes 33 but its coverage is *nominal* — several lessons
  claiming an engine control have no test that would fail if the control were removed.
- **C3:** ShippingGate is mostly aspirational prose; only a few of its checks are mechanized.
- **E1:** several manuscript claims are now false rather than merely stale.

## Where I disagree / hold

- **C2:** Codex says one of my four Qin source audits is false. I have **not** yet re-derived
  which one, so I am neither accepting nor rejecting it — flagged for the morning. (It agrees
  the population-mean correction itself is right.)
- Nothing else rejected outright. Its two named successes both survive my check: the
  bn150721242 per-bin response fallback preserves interval identity, and the Khushboo
  cross-operator agreement really is **< 0.6σ** on α/Ep/β — §5's headline stands exactly.

## The honest summary

The engine tables are more trustworthy than the figures and the prose built on them. Nothing
here invalidates the sweep's spectral fits; it invalidates *publishing* the temporal numbers
(now fixed), the population BB census (rule incomplete), and several manuscript claims. The
audit cost one broken estimator caught before it reached a file, and one contaminated P0 made
machine-excludable — both found because an independent harness recomputed from the primitives
rather than reading our summaries.


## 2026-08-17 — campaign paper round (GRB 090620, burst #5)

**Producer:** Claude (Codex out). Fits: v2 pool (24 models, 10 spectra).
Paper: paper/GRB090620/ (16 pp).

**COMBINED VERIFIER (fresh context): PASS-WITH-CORRECTIONS — ALL APPLIED:**
(1) lag scan-member range 0.52→0.47 (the ±0.13 win systematic requires the
0.47 member); (2) step9 caption asserted a block-7 edge marker that the
LRT≥9.2 gate correctly withholds — INVERSE failure class (figure right,
caption wrong), recaptioned with the gate stated; (3) 24×10 claim
overstated by two engine-FAIL cells (BANDPL TINT, BANDRCPL bin1) —
sweep_status FAIL lines appended, TINT+bin1 montages REBUILT with labeled
refusal cells, tex now discloses both; (4) "first all-three MVT" qualified
(burst-1 windowed z=2.5 caveat) in 4 places; (5) lag caption "median
member"→"member closest to scan median"; (6) "three times finer"→"nine
blocks against six"; (7) bin8 SED referenced (was orphan). Figure sweep:
all SEDs PASS (bands/stamps/EACs verified; bin7 97%-railed suppression
note correct); 8/10 montages PASS as-built; step9 verified against
canonical (NOT stale — the b4 defect class specifically checked); temporal
figs PASS. Engine-FAIL retry for the 2 refusal cells: queued to register
(needs single-(model,bin) refit capability — engine-level item).

**Science row:** third consecutive CWT 215 ms rung (A5 falsification
hardened at N=3); first non-FRED pulse (phi=0.40 mixed); epoch-level
line-of-death pattern repeated at 9-block resolution; zero robust thermal
candidates (edge gate disarmed the kT=1.1 keV block-7 BB). Burst #5
CLOSED pending PI.

**CORRECTION (2026-08-17, self-reported):** the earlier entry claimed
TINT+bin1 montages were "REBUILT with labeled refusal cells" — that claim
was NOT VERIFIED at the time and was FALSE: 41e's model loop skipped
NaN-AIC models entirely (see bn090719063 ledger for the root cause), so
the rebuilds still rendered 23 cells. After the 41e fix both montages are
rebuilt again WITH the two labeled ENGINE FAIL refusal cells and re-staged
into the paper. Producer-prose lesson re-learned: a claim of a fix is not
a verification of the fix.

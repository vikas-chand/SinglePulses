# REVIEW INDEX — all 106 bursts, in order

One burst at a time, burst 1 → 106. Products live in TWO roots (the 85-burst sweep and
the walkthrough era); this index resolves that for you — the `products` path is where
everything for that burst is.

**Per burst:** open the products dir, read `PRODUCTS.md` (what exists / what is missing and
why), walk the figures in step order, then fill the approval sheet:

```bash
TRIG=<trigger>;  OUT=<products path from the table>
cat $OUT/PRODUCTS.md
cp handoff_background_approval/KHUSHBOO_APPROVAL_SHEET_TEMPLATE.md notes/approvals/${TRIG}_approval.md
```

`DEC`/`STR` = blocks where an extra component beats the best simple model by ΔAIC ≥ 10 / ≥ 6.
`BB` = blocks with a significant, off-rail, VALID blackbody (union of the Band+BB and CPL+BB
nested tests). ⚠ The BB census rule is still open (external audit A3: other nested pairs are
not yet counted) — treat `BB` as provisional.

| # | burst | products | blocks | DEC | STR | BB | T90 (s) | manifest |
|---|---|---|---|---|---|---|---|---|
| 1 | `bn081125496` | `results/sweep106/bn081125496` | 9 | 0 | 0 | 0 | 8.5±0.2 | 21/21 |
| 2 | `bn081222204` | `results/sweep106/bn081222204` | 6 | 0 | 0 | 0 | 11.3±0.4 | 18/18 |
| 3 | `bn081224887` | `results/sweep106/bn081224887` | 9 | 0 | 0 | 1 | 14.8±0.4 | 21/21 |
| 4 | `bn090530760` | `results/sweep106/bn090530760` | 6 | 0 | 0 | 4 | 134.3±1.1 | 18/18 |
| 5 | `bn090620400` | `results/sweep106/bn090620400` | 9 | 0 | 0 | 1 | 12.5±0.5 | 21/21 |
| 6 | `bn090719063` | `results/sweep106/bn090719063` | 10 | 0 | 0 | 2 | 13.4±0.2 | 22/22 |
| 7 | `bn090804940` | `results/sweep106/bn090804940` | 7 | 0 | 1 | 2 | 6.7±0.1 | 19/19 |
| 8 | `bn090809978` | `results/sweep106/bn090809978` | 9 | 0 | 0 | 3 | 9.8±0.2 | 21/21 |
| 9 | `bn090829672` | `results/sweep106/bn090829672` | 34 | 0 | 0 | 2 | 26.6±0.2 | 46/46 |
| 10 | `bn091209001` | `results/sweep106/bn091209001` | 4 | 0 | 0 | 0 | 22.9±0.5 | 16/16 |
| 11 | `bn100122616` | `results/sweep106/bn100122616` | 10 | 0 | 1 | 5 | 8.8±0.3 | 22/22 |
| 12 | `bn100130729` | `results/sweep106/bn100130729` | — | — | — | — | 28.3±0.7 | — |
| 13 | `bn100612726` | `results/sweep106/bn100612726` | 8 | 0 | 1 | 2 | 9.8±0.3 | 20/20 |
| 14 | `bn100614498` | `results/sweep106/bn100614498` | 1 | 0 | 0 | 0 | 21.8±1.3 | 12/13 |
| 15 | `bn100707032` | `results/sweep106/bn100707032` | 12 | 0 | 1 | 8 | 20.3±0.3 | 24/24 |
| 16 | `bn101126198` | `results/sweep106/bn101126198` | 10 | 0 | 3 | 3 | 28.8±0.5 | 22/22 |
| 17 | `bn101225377` | `results/sweep106/bn101225377` | 3 | 0 | 0 | 0 | 23.4±0.5 | 15/15 |
| 18 | `bn110605183` | `results/sweep106/bn110605183` | 6 | 0 | 0 | 0 | 25.2±0.6 | 18/18 |
| 19 | `bn110618366` | `results/sweep106/bn110618366` | 4 | 0 | 0 | 0 | 50.9±1.1 | 16/16 |
| 20 | `bn110721200` | `results/sweep106/bn110721200` | 10 | 3 | 0 | 4 | 13.2±0.4 | 22/22 |
| 21 | `bn110920546` | `results/sweep106/bn110920546` | 11 | 8 | 2 | 10 | 88.7±0.8 | 23/23 |
| 22 | `bn110928180` | `results/sweep106/bn110928180` | 4 | 0 | 0 | 1 | 26.6±0.9 | 15/16 |
| 23 | `bn111009282` | `results/sweep106/bn111009282` | 7 | 0 | 0 | 0 | 14.9±0.3 | 19/19 |
| 24 | `bn111017657` | `results/sweep106/bn111017657` | 9 | 0 | 0 | 0 | 10.7±0.3 | 21/21 |
| 25 | `bn120102095` | `results/sweep106/bn120102095` | 5 | 1 | 0 | 1 | 11.5±0.4 | 17/17 |
| 26 | `bn120119170` | `results/sweep106/bn120119170` | 10 | 0 | 0 | 1 | 33.4±0.3 | 22/22 |
| 27 | `bn120130938` | `results/sweep106/bn120130938` | 3 | 0 | 0 | 0 | 20.4±1.1 | 15/15 |
| 28 | `bn120420858` | `results/sweep106/bn120420858` | 2 | 0 | 0 | 0 | 44.2±0.4 | 14/14 |
| 29 | `bn120624933` | `results/sweep106/bn120624933` | 10 | 0 | 0 | 1 | 17.9±0.5 | 22/22 |
| 30 | `bn120905657` | `results/sweep106/bn120905657` | 5 | 0 | 0 | 0 | 96.2±1.0 | 17/17 |
| 31 | `bn120919309` | `results/sweep106/bn120919309` | 8 | 0 | 0 | 0 | 7.7±0.2 | 20/20 |
| 32 | `bn130215063` | `results/sweep106/bn130215063` | 1 | 0 | 0 | 0 | 36.9±1.1 | 12/13 |
| 33 | `bn130310840` | `results/sweep106/bn130310840` | 10 | 1 | 2 | 5 | 2.8±0.3 | 22/22 |
| 34 | `bn130427324` | `results/sweep106/bn130427324` | 8 | 1 | 1 | 4 | 44.8±0.5 | 20/20 |
| 35 | `bn130518580` | `results/sweep106/bn130518580` | 19 | 1 | 2 | 10 | 34.0±1.0 | 31/31 |
| 36 | `bn131113483` | `results/sweep106/bn131113483` | 5 | 0 | 0 | 0 | 47.0±1.1 | 17/17 |
| 37 | `bn140608153` | `results/sweep106/bn140608153` | 3 | 0 | 0 | 0 | 59.3±1.7 | 14/15 |
| 38 | `bn150202999` | `results/sweep106/bn150202999` | 19 | 0 | 0 | 3 | 15.3±0.3 | 31/31 |
| 39 | `bn150213001` | `results/walkthrough_b15` | 18 | 3 | 2 | 11 | 4.7±0.1 | — |
| 40 | `bn150306993` | `results/walkthrough_b13` | 6 | 0 | 0 | 1 | 22.4±0.6 | 18/18 |
| 41 | `bn150630223` | `results/sweep106/bn150630223` | 8 | 2 | 1 | 4 | 14.9±0.6 | 20/20 |
| 42 | `bn150721242` | `results/walkthrough_b12` | 7 | 0 | 0 | 5 | 21.0±0.3 | — |
| 43 | `bn150902733` | `results/sweep106/bn150902733` | 18 | 0 | 1 | 9 | 14.8±0.2 | 29/30 |
| 44 | `bn151006413` | `results/sweep106/bn151006413` | 4 | 1 | 0 | 1 | 34.9±0.7 | 16/16 |
| 45 | `bn151021791` | `results/walkthrough_b14` | 8 | 0 | 0 | 1 | 7.0±0.2 | — |
| 46 | `bn160330827` | `results/walkthrough_b19` | 4 | 0 | 0 | 4 | 25.1±0.5 | — |
| 47 | `bn160625945` | `results/sweep106/bn160625945` | 50 | 4 | 2 | 23 | 22.3±0.1 | 62/62 |
| 48 | `bn160910722` | `results/walkthrough_b18` | 17 | 0 | 2 | 9 | 22.8±0.6 | — |
| 49 | `bn170114833` | `results/sweep106/bn170114833` | 3 | 0 | 0 | 1 | 29.4±1.4 | 15/15 |
| 50 | `bn170114917` | `results/sweep106/bn170114917` | 8 | 0 | 0 | 3 | 13.0±0.6 | 20/20 |
| 51 | `bn170921168` | `results/walkthrough_b16` | 17 | 1 | 1 | 9 | 30.2±0.2 | — |
| 52 | `bn171013350` | `results/sweep106/bn171013350` | 3 | 0 | 0 | 1 | 28.9±0.5 | 15/15 |
| 53 | `bn171210493` | `results/walkthrough_b17` | 12 | 0 | 1 | 3 | 87.3±1.0 | — |
| 54 | `bn180426549` | `results/sweep106/bn180426549` | 4 | 0 | 0 | 1 | 7.1±0.2 | 16/16 |
| 55 | `bn180427442` | `results/sweep106/bn180427442` | 11 | 0 | 0 | 2 | 27.5±0.6 | 23/23 |
| 56 | `bn180703876` | `results/walkthrough_b30` | 7 | 0 | 0 | 2 | 25.2±1.1 | — |
| 57 | `bn180720213` | `results/walkthrough_b29` | 10 | 0 | 0 | 0 | 9.3±0.4 | — |
| 58 | `bn180723757` | `results/walkthrough_b20` | 11 | 3 | 0 | 7 | 19.1±0.3 | — |
| 59 | `bn180724807` | `results/walkthrough_b28` | 8 | 0 | 0 | 1 | 38.3±1.1 | — |
| 60 | `bn180728728` | `results/walkthrough_b11` | 21 | 3 | 3 | 7 | 8.3±0.1 | — |
| 61 | `bn181212693` | `results/walkthrough_b27` | 13 | 0 | 0 | 4 | 6.9±0.2 | — |
| 62 | `bn190222537` | `results/walkthrough_b26` | 4 | 0 | 0 | 0 | 13.0±0.8 | — |
| 63 | `bn190401139` | `results/walkthrough_b25` | 9 | 2 | 0 | 2 | 27.0±0.8 | — |
| 64 | `bn190726642` | `results/walkthrough_b24` | 6 | 0 | 0 | 0 | 15.6±1.4 | — |
| 65 | `bn191017391` | `results/walkthrough_b23` | 3 | 0 | 0 | 0 | 26.5±0.8 | — |
| 66 | `bn191125206` | `results/walkthrough_b22` | 12 | 5 | 3 | 8 | 28.8±0.4 | — |
| 67 | `bn191129141` | `results/walkthrough_b21` | 8 | 0 | 0 | 2 | 19.3±0.7 | — |
| 68 | `bn200227306` | `results/sweep106/bn200227306` | 6 | 1 | 1 | 1 | 20.9±0.4 | 18/18 |
| 69 | `bn200301320` | `results/sweep106/bn200301320` | 7 | 4 | 0 | 4 | 15.7±0.6 | 19/19 |
| 70 | `bn200524211` | `results/verification_khushboo_200524211` | 11 | 0 | 0 | 0 | 20.3±0.5 | — |
| 71 | `bn200607921` | `results/sweep106/bn200607921` | 5 | 0 | 0 | 0 | 21.6±0.4 | 16/17 |
| 72 | `bn200826923` | `results/sweep106/bn200826923` | 15 | 1 | 1 | 7 | 7.7±0.0 | 27/27 |
| 73 | `bn201016019` | `results/sweep106/bn201016019` | 20 | 1 | 2 | 11 | 3.9±0.0 | 32/32 |
| 74 | `bn201104001` | `results/sweep106/bn201104001` | 9 | 0 | 0 | 2 | 7.2±0.4 | 21/21 |
| 75 | `bn201105230` | `results/sweep106/bn201105230` | 8 | 1 | 0 | 4 | 19.9±0.3 | 20/20 |
| 76 | `bn210410037` | `results/sweep106/bn210410037` | 8 | 0 | 0 | 1 | 23.7±0.6 | 20/20 |
| 77 | `bn210524208` | `results/sweep106/bn210524208` | 14 | 1 | 0 | 5 | 20.9±0.4 | 26/26 |
| 78 | `bn210714331` | `results/sweep106/bn210714331` | 16 | 0 | 0 | 7 | 28.1±0.5 | 28/28 |
| 79 | `bn210723615` | `results/sweep106/bn210723615` | 2 | 0 | 0 | 0 | 28.8±0.9 | 13/14 |
| 80 | `bn210803497` | `results/sweep106/bn210803497` | 8 | 0 | 0 | 0 | 10.1±0.2 | 20/20 |
| 81 | `bn210812699` | `results/sweep106/bn210812699` | 2 | 0 | 0 | 0 | 3.8±0.4 | 13/14 |
| 82 | `bn211116586` | `results/sweep106/bn211116586` | 4 | 0 | 0 | 0 | 12.6±0.4 | 15/16 |
| 83 | `bn211207416` | `results/sweep106/bn211207416` | 4 | 0 | 0 | 0 | 38.3±0.7 | 16/16 |
| 84 | `bn220525008` | `results/sweep106/bn220525008` | 8 | 0 | 0 | 1 | 17.5±0.6 | 20/20 |
| 85 | `bn221201517` | `results/sweep106/bn221201517` | 7 | 0 | 0 | 1 | 29.4±1.0 | 19/19 |
| 86 | `bn221209243` | `results/sweep106/bn221209243` | 10 | 0 | 1 | 6 | 6.5±0.5 | 22/22 |
| 87 | `bn230320884` | `results/sweep106/bn230320884` | 5 | 0 | 0 | 0 | 13.5±0.5 | 16/17 |
| 88 | `bn230405832` | `results/sweep106/bn230405832` | 6 | 0 | 0 | 0 | 5.7±0.2 | 18/18 |
| 89 | `bn230409626` | `results/sweep106/bn230409626` | 9 | 0 | 0 | 0 | 15.6±0.5 | 21/21 |
| 90 | `bn230614424` | `results/sweep106/bn230614424` | 12 | 0 | 0 | 4 | 6.7±0.2 | 22/24 |
| 91 | `bn230802285` | `results/sweep106/bn230802285` | 3 | 3 | 0 | 3 | 25.2±1.1 | 15/15 |
| 92 | `bn230812790` | `results/sweep106/bn230812790` | 27 | 4 | 3 | 20 | 4.6±0.0 | 39/39 |
| 93 | `bn231020790` | `results/sweep106/bn231020790` | 19 | 0 | 2 | 7 | 10.6±0.1 | 31/31 |
| 94 | `bn231030832` | `results/sweep106/bn231030832` | 6 | 0 | 0 | 3 | 12.3±0.6 | 18/18 |
| 95 | `bn240204630` | `results/sweep106/bn240204630` | 8 | 0 | 1 | 1 | 16.8±0.3 | 20/20 |
| 96 | `bn240403498` | `results/sweep106/bn240403498` | 15 | 0 | 1 | 2 | 13.7±0.4 | 27/27 |
| 97 | `bn240710643` | `results/sweep106/bn240710643` | 8 | 0 | 0 | 3 | 10.6±0.4 | 20/20 |
| 98 | `bn241117845` | `results/sweep106/bn241117845` | 5 | 0 | 0 | 0 | 57.8±1.0 | 17/17 |
| 99 | `bn241223506` | `results/sweep106/bn241223506` | 11 | 1 | 1 | 3 | 30.0±0.5 | 23/23 |
| 100 | `bn250313607` | `results/sweep106/bn250313607` | 16 | 1 | 2 | 7 | 15.4±0.3 | 28/28 |
| 101 | `bn250407659` | `results/sweep106/bn250407659` | 10 | 4 | 0 | 7 | 10.1±0.4 | 21/23 |
| 102 | `bn250702413` | `results/sweep106/bn250702413` | 9 | 1 | 0 | 2 | 47.9±0.8 | 21/21 |
| 103 | `bn250814432` | `results/sweep106/bn250814432` | 3 | 0 | 0 | 0 | 7.9±0.4 | 14/15 |
| 104 | `bn250902062` | `results/sweep106/bn250902062` | 13 | 0 | 1 | 3 | 12.5±0.2 | 25/25 |
| 105 | `bn251016999` | `results/sweep106/bn251016999` | 9 | 1 | 0 | 3 | 10.1±0.4 | 21/21 |
| 106 | `bn260105973` | `results/sweep106/bn260105973` | 4 | 0 | 0 | 1 | 6.9±0.3 | 16/16 |

**106 bursts · 85 with a product manifest · 21 pending**

## Known state you should not re-discover
- `bn100130729` — no fit: its blocks fall outside the response coverage (`RESPONSE_UNCOVERED`).
  An honest documented exclusion, not a crash.
- `bn120624933` — its `lle` row is stamped `ai_inherited_PENDING_HUMAN` **and is used in fits**.
  This is the one open Stage-1 decision; CI fails on exactly this.
- The 20 detector-rows in `results/human_review_qc_flags.txt` are your ACCEPTED gap overrides.
  Figures say so on their face; they are not defects.
- Any `[! PANEL!=ENGINE]` stamp on a montage panel: trust the table, not the curve.
- A blackbody with 3.92·kT below 20 keV is EDGE_CONSTRAINED (L28) — kept in the record,
  excluded from population statistics until its checks pass.

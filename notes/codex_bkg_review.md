# Final adversarial QA: background and source intervals

Review date: 2026-07-14  
Reviewer: Codex (independent AI expert review)  
Inputs: `results/background_intervals.ecsv`, `dev/ai_guides/background_selection.md`, `dev/ai_guides/source_selection.md`, `dev/ai_guides/detector_selection.md` (scope-adjacent consistency checks only), and all six `plots/reselect_montages/*.png` files.

## Verdict

**NOT READY FOR HUMAN SIGN-OFF.** The ECSV is structurally valid, but it is not scientifically clean enough to hand to Khushboo as a sign-off-ready catalog.

- There are **0/479 source-in-gap violations**, no non-finite values, and no interval-ordering failures.
- Nevertheless, **40 margin edges in 36 rows / 10 bursts are still <5 s**, despite the hardened rule defining this as a real tail-leak defect.
- The montages contain **49 unique re-selected bursts, not 48**. Of those 49, the visual audit classifies **18 WRONG, 26 QUESTIONABLE, and only 5 OK**.
- The 18 visually wrong cases include a background window wholly on a no-data segment, real precursors/late episodes inside background windows or outside the source interval, and soft tails that extend into the post window.
- **28 unique bursts are interval must-fixes**: 18 visual failures plus 10 separate catalog-wide `<5 s` failures. One additional burst, `bn090719063`, has a blocking detector-companion inconsistency, making **29 unique must-resolve bursts** in the delivered catalog.

The 28 interval must-fixes should be corrected before collaborator handoff. The nice-to-check set can be presented to Khushboo as explicit judgment calls, not as already-clean selections.

## 1. Numeric audit of all 106 bursts

Boundary conventions used here are exact: target margin means `5 <= g <= 20`; too tight means `g < 5`; hard-far means `g > 40`; target width means `50 <= width <= 150`. The `(20,40]` category is outside the working target but below the requested hard-far threshold.

### Catalog integrity

| Check | Result |
|---|---:|
| Rows / unique `(trigger, detector)` keys | 479 / 479 |
| Unique triggers | 106 |
| `pre_stop <= SRC_START < SRC_STOP <= post_start` violations | **0** |
| Non-increasing pre/source/post intervals | **0 / 0 / 0** |
| NaN, Inf, or masked numeric values | **0** |
| Duplicate `(trigger, detector)` rows | **0** |
| Triggers with detector-dependent source edges | **0** |

### Margins

| Quantity | Min / median / max (s) | In `[5,20]` | `<5` | `(20,40]` | `>40` |
|---|---:|---:|---:|---:|---:|
| `g_pre = SRC_START - BKG_NEG_STOP` | 3.000 / 10.000 / 24.300 | 449/479 | 27/479 | 3/479 | **0/479** |
| `g_post = BKG_POS_START - SRC_STOP` | 3.708 / 15.000 / 39.548 | 305/479 | 13/479 | 161/479 | **0/479** |
| Both edges combined | — | 754/958 | 40/958 | 164/958 | **0/958** |

Only **282/479 rows** have both margins in `[5,20]`. The 40 too-tight edges occur in 36 rows across the following 10 bursts and are must-fix under the stated rule:

| Trigger | Affected detectors | Defect |
|---|---|---|
| `bn081222204` | `n0,n1,n2,b0` | `g_pre = 3.84 s` |
| `bn090530760` | `b0,n1,n2,n3,n5` | `g_pre = 4.00 s` |
| `bn100122616` | `n6,n7,n9,na,b1` | `g_pre = 3.00 s` |
| `bn131113483` | `n1,n2,n5,b0` | `g_pre = 4.00 s` |
| `bn150902733` | `n0,n1,b0` | `g_post = 4.248 s` |
| `bn160625945` | `n6,n7,n9,nb,b1` | `g_post = 3.708 s` |
| `bn201016019` | `n3,n4,n5,b0` | `g_pre = 4.388 s`; `g_post = 4.232 s` |
| `bn210723615` | `n3,n4,n5,b0` | `g_pre = 3.60 s` |
| `bn230614424` | `nb` | `g_post = 4.00 s` |
| `bn231030832` | `b1` | `g_pre = 3.00 s` |

There are no `g > 40 s` rows. The large number of post margins in `(20,40]` is not a hard-far violation, but it shows that the catalog remains systematically less burst-hugging on the post side than intended.

### Window widths

| Window | Min / median / max (s) | In `[50,150]` | `<50` | `>150` |
|---|---:|---:|---:|---:|
| Pre | 2.5 / 80 / 115 | 362/479 | 117/479 | **0** |
| Post | 7 / 90 / 150 | 476/479 | 3/479 | **0** |
| Both windows combined | — | 838/958 | 120/958 | **0** |

There are **118 rows / 26 bursts** with at least one width outside the strict 50–150 s range. No exception/forced-coverage field in the ECSV explains which short windows were unavoidable.

| Trigger | Detectors sharing exception | Pre / post width (s) |
|---|---|---:|
| `bn081224887` | `n0,n1,n6,n7,n9,b0,b1` | 16 / 100 |
| `bn090530760` | `b0,n1,n2,n3,n5` | 24.7 / 80 |
| `bn090620400` | `n6,n7,n8,nb,b1` | 14.71 / 80 |
| `bn090719063` | `n7,n8` | 19.5 / 94.44 |
| `bn090804940` | `n3,n4,n5,b0` | 10.256 / 80 |
| `bn090809978` | `n3,n4,n5,b0` | 17.764 / 106.16 |
| `bn090829672` | `n0,n6,n7,n9,na,nb,b0,b1` | 37.533 / 100 |
| `bn091209001` | `n4,b0` | 18 / 100 |
| `bn100122616` | `n6,n7,n9,na,b1` | 39 / 90 |
| `bn100612726` | `n3,n4,n7,n8,b0,b1` | 21.4 / 107 |
| `bn100614498` | `n6,n7,n9,nb,b1` | **6 / 124** |
| `bn100707032` | `n7,n8,b1` | 14 / 100 |
| `bn101126198` | `n6,n7,n8,nb,b1` | 18 / 100 |
| `bn110605183` | `n2,n5,b0` | 18.5 / 85 |
| `bn110721200` | `n6,n7,n9,nb,b1` | 22.5 / 90 |
| `bn110920546` | `n0,n1,n3,n6,n7,b0,b1` | 10.53 / 150 |
| `bn111009282` | `n0,n1,b0` | 20.88 / 107 |
| `bn111017657` | `n6,n7,n8,n9,b1` | 23 / 110 |
| `bn120102095` | `n3,n4,n5,b0` | 22 / 98 |
| `bn120119170` | `n9,na,nb,b1` | 22 / 90 |
| `bn120130938` | `n0,n1,n9,na,b0,b1` | 15 / 100 |
| `bn120624933` | `n0,n1,n2,n9,na,b0,b1` | 21.5 / 120 |
| `bn120919309` | `n0,n1,n2,n3,n5,b0` | 21 / 91 |
| `bn180426549` | `nb,b1` | **2.5 / 7** |
| `bn200524211` | `n0,n1,n3,b0` | 15 / 95 |
| `bn230614424` | `nb` | 110 / **42** |

`bn180426549` is not a defensible routine exception: both anchors are only a few seconds long, the pre lies at data turn-on, and the displayed polynomial/net residuals show that the background is effectively unconstrained. `bn100614498` also needs explicit acceptance of a 6 s forced pre-window. The remaining short windows need a documented coverage justification rather than silent treatment as ordinary 50–150 s selections.

### Reselection/provenance reconciliation

- The ECSV has **223 rows / 49 triggers** whose `APPROVED_BY` contains `margin-reselect`.
- The montage files likewise contain **49 unique labeled panels**: 37 in `reselect_bunch1`–`reselect_bunch5` plus 12 in `reselect_farpost`. The prompt's “48” is therefore an inventory mismatch, not an overlap in the montages.
- Every re-selected trigger uses one common interval set across all of its detector rows, so a panel-level interval failure propagates to every selected detector for that burst.
- Within the 49 stamped re-selections, no margin is `<5` or `>40`: pre has 220 target and 3 `(20,40]` rows; post has 198 target and 25 `(20,40]` rows. All 40 residual `<5` edges belong to bursts that were not stamped as re-selected.
- All 479 rows carry the same `APPROVED_UTC` (`2026-07-14T17:18:10Z`) despite mixed approvers and modes. This may be a batch-ingest timestamp, but it should not be mistaken for independent decision times.

## 2. Visual audit of every montage panel

`WRONG` means the intervals should be changed or the burst excluded before handoff. `QUESTIONABLE` means the issue should be shown explicitly to the human reviewer. The overview panel was cross-checked against detector-level light curves when a weak feature was hidden by the reference detector or by the burst's y-axis scale.

| Trigger | Status | Adversarial finding |
|---|---|---|
| `bn081125496` | **WRONG** | Pre `[-120,-26]` is wholly on the zero-count/no-data segment and ends at data return; the cubic is grossly distorted. Source also clips the visible decay. |
| `bn090719063` | QUESTIONABLE | Clean-looking intervals, but the pre is only 19.5 s from the data boundary. Detector-set blocker is noted below. |
| `bn090809978` | QUESTIONABLE | Pre is 17.8 s; weak decay appears to continue from source stop 15.5 s to about 18–20 s, leaving only about a 5 s effective post buffer. |
| `bn090829672` | **WRONG** | A coherent precursor at roughly 0–15 s is visible in several selected NaIs, lies inside pre ending at 14 s, and is omitted by source starting at 29 s. |
| `bn091209001` | QUESTIONABLE | Pre is 18 s; coherent positive NET around 30–43 s after source stop may be late emission or polynomial mismatch. Post itself begins after it. |
| `bn100612726` | QUESTIONABLE | Pre is 21.4 s; source stop 15 s is slightly early and the post starts only about 5 s after the apparent return. |
| `bn100614498` | QUESTIONABLE | Pre is only 6 s at data onset. No clear transient is inside it, but the fit is severely underconstrained and needs an explicit forced-coverage exception. |
| `bn100707032` | QUESTIONABLE | Pre is only 14 s from data onset; source and post otherwise look acceptable. |
| `bn101126198` | QUESTIONABLE | Pre is 18 s; faint tail continues to about 34–35 s after source stop 30 s, making post at 40 s borderline. |
| `bn110605183` | QUESTIONABLE | Pre is 18.5 s at data onset and lies on a mild rise; no discrete contaminant is obvious. |
| `bn110618366` | **WRONG** | Broad soft tail remains positive beyond source stop 60.636 s to roughly 70–78 s; post starts at 78 s and its early bins retain positive NET. |
| `bn110721200` | QUESTIONABLE | Pre is only 22.5 s; source stop 40.5 s appears 10–15 s later than the return, so the source is over-wide even though backgrounds look clean. |
| `bn110920546` | QUESTIONABLE | Pre is 10.53 s; weak long-decay residual persists beyond source stop 120 s to about 128–130 s, with post at 135 s only marginally clear. |
| `bn111009282` | QUESTIONABLE | Pre is 20.88 s and contains a small coherent hump around -22 to -15 s; verify in the other NaI. Source/post otherwise look clean. |
| `bn111017657` | QUESTIONABLE | Pre is 23 s; source stop 15 s clips low-level decay to about 18–19 s. |
| `bn120102095` | QUESTIONABLE | Pre is 22 s; tail continues to about 18 s after source stop 15 s, leaving only about a 4 s clean buffer before post at 22 s. |
| `bn120119170` | **WRONG** | Clear positive NET remains at source stop 47 s and returns only around 53–55 s; post starts at 55 s with no safe tail margin. |
| `bn120130938` | QUESTIONABLE | Pre is only 15 s; otherwise windows are smooth and source/post are plausible. |
| `bn120420858` | QUESTIONABLE | Weak NET persists beyond source stop 48 s to roughly 52–55 s; post starts 58 s, only 3–6 s after actual return. |
| `bn120624933` | **WRONG** | Source stops at 28 s while coherent tail continues to about 33–35 s; post begins at 35 s, effectively at the return. |
| `bn120919309` | QUESTIONABLE | Pre is 21 s; source and post otherwise look clean. |
| `bn140608153` | OK | 100/85 s clean windows, 11/17 s margins, plausible polynomial, and source covers the broad emission episode. |
| `bn150202999` | QUESTIONABLE | Source stop 22 s leaves a low-level decay to about 27–29 s; post at 35 s is probably safe. |
| `bn151021791` | QUESTIONABLE | Source stop 11 s clips the last decay bins to about 14–15 s; post at 26 s is safe. |
| `bn160330827` | **WRONG** | Multi-NaI low-level decay continues from source stop 30 s to about 38–40 s; post starts at 42 s, only 2–4 s past actual return. |
| `bn170114833` | OK | Pre/post are smooth and feature-free; 11/12 s margins and source `[-2,40]` cover the decay. |
| `bn180426549` | **WRONG** | Pre/post are only 2.5/7 s, pre sits at data turn-on, the fit is unconstrained, and source stop 6.5 s clips tail to about 9–10 s. Redo with adequate data or exclude. |
| `bn180728728` | **WRONG** | Clear precursor at about -2 to +4 s lies partly inside pre ending -1.048 s and wholly outside source starting 8 s. |
| `bn191125206` | OK | Wide clean windows, plausible polynomial, and no convincing omitted emission or in-window structure. |
| `bn191129141` | QUESTIONABLE | Broad approximately 3–4 sigma hump around -42 to -37 s lies inside the pre window; weak onset also approaches source start. Check per detector and nudge/extend if real. |
| `bn200524211` | QUESTIONABLE | Pre is only 15 s and starts at the TTE turn-on edge; source/post otherwise look good. |
| `bn201104001` | OK | Clean settled baseline, 10/8 s margins, and source brackets the emission. |
| `bn210410037` | QUESTIONABLE | Weak multi-NaI tail continues from source stop 32 s to roughly 38–40 s; post at 48 s is likely safe, but source is short. |
| `bn210812699` | **WRONG** | Post window contains a coherent bump around 33–38 s (strongest in `nb`, corroborated in `b1`). It is not a clean background window. |
| `bn230802285` | **WRONG** | Pre contains a broad positive feature around -35 to -20 s, clear in `n2/n5` and >3 sigma in `n5`. |
| `bn240403498` | **WRONG** | Obvious precursor near 0–8 s and late pulse near 70–80 s are both outside source 18–48 s; pre/post margins are razor-thin relative to the real episodes. |
| `bn241117845` | **WRONG** | Decay remains positive from source stop 68 s to roughly 78–80 s in several NaIs; post starts 83 s, only about 3 s after return. |
| `bn100130729` | **WRONG** | Pre begins at the -32 s data turn-on and contains a coherent precursor near -5 to +5 s (strongest in `n3`), long before source starts at 58 s. |
| `bn110928180` | **WRONG** | Burst rise begins about -15 to -8 s but source starts -3 s; with pre ending -18.328 s, the real pre margin is only about 3 s. |
| `bn130215063` | QUESTIONABLE | Low-level rise begins around -8 to -5 s and tail persists to about 48–52 s, outside source `[-2.5,42]`; post at 55 s nearly touches return. |
| `bn130427324` | **WRONG** | Post 75–175 s contains a broad coherent bump/step around 123–145 s in multiple NaIs; it is hidden by the huge prompt peak scale but contaminates the polynomial fit. |
| `bn151006413` | QUESTIONABLE | Weak tail continues from source stop 42 s to about 50 s; post starts 54 s, and `n1` also shows a small 62–66 s bump. |
| `bn171210493` | **WRONG** | Very strong soft tail continues far beyond source stop 50 s and directly into post starting 88 s, remaining visible to roughly 100–110 s. |
| `bn200607921` | **WRONG** | Source stops 26.716 s while the NaI decay remains positive to about 38–40 s. Post at 58 s is clean, but the source omits real emission. |
| `bn210714331` | QUESTIONABLE | Source stops 41 s while low-level tail reaches about 48–50 s; post at 56 s leaves only about 6 s after return. |
| `bn211207416` | QUESTIONABLE | Broad low-level feature/rise around -30 to -18 s touches/enters pre ending -22 s; determine precursor versus baseline trend. |
| `bn221201517` | **WRONG** | Source stops 23.64 s, but tail remains repeatedly >3 sigma through roughly 40–43 s in `n5/n2`. |
| `bn250702413` | QUESTIONABLE | Post gap is 30 s, outside target, with unused clean baseline; weak tail may extend to about 65–70 s. Extend source and/or bring post inward after confirming return. |
| `bn250814432` | OK | Clean windows, 16.6/12 s margins, and source covers the short pulse. |

## 3. Must-fix versus nice-to-check

### Interval must-fix before handoff (28 bursts)

Visual failures (18):

- Invalid/no-data or unusably underconstrained background: `bn081125496`, `bn180426549`.
- Precursor/late episode omitted from source or placed inside a background window: `bn090829672`, `bn100130729`, `bn130427324`, `bn180728728`, `bn210812699`, `bn230802285`, `bn240403498`.
- Source edge clips a clear rise/tail and/or the tail contaminates post: `bn110618366`, `bn110928180`, `bn120119170`, `bn120624933`, `bn160330827`, `bn171210493`, `bn200607921`, `bn221201517`, `bn241117845`.

Catalog-wide hard `<5 s` failures not in the re-selection montages (10):

- `bn081222204`, `bn090530760`, `bn100122616`, `bn131113483`, `bn150902733`, `bn160625945`, `bn201016019`, `bn210723615`, `bn230614424`, `bn231030832`.

### Nice-to-check (28 bursts)

The reasons are in the visual and width tables above. These should be explicit human decisions, especially where TTE coverage forces a short anchor:

`bn081224887`, `bn090620400`, `bn090804940`, `bn090809978`, `bn091209001`, `bn100612726`, `bn100614498`, `bn100707032`, `bn101126198`, `bn110605183`, `bn110721200`, `bn110920546`, `bn111009282`, `bn111017657`, `bn120102095`, `bn120130938`, `bn120420858`, `bn120919309`, `bn130215063`, `bn150202999`, `bn151006413`, `bn151021791`, `bn191129141`, `bn200524211`, `bn210410037`, `bn210714331`, `bn211207416`, `bn250702413`.

### Additional catalog-level blockers caught during the audit

- `bn090719063` retains high-side NaIs `n7,n8` but has no required high-side companion `b1` row. Add/document the companion or reselect the detector set.
- `bn210812699/nb` has `DET_ANGLE = 60.1218 deg`, beyond the detector guide's hard 60-degree NaI limit. This burst is already an interval must-fix because its post window contains a coherent bump, but its detector geometry also needs resolution.

With the `bn090719063` detector issue included, there are **29 unique must-resolve bursts** before the catalog can honestly be labeled ready for sign-off.

## Recommended handoff sequence

1. Redo or exclude the 28 interval must-fixes; resolve the `bn090719063` detector set at the same time.
2. Re-render the corrected panels and repeat the numeric invariant/margin audit.
3. Record a machine-readable exception reason for every accepted `<50 s` window; do not leave forced coverage implicit.
4. Give Khushboo the 28 nice-to-check cases as an explicit review queue, with the reasons above, rather than mixing them into a nominally clean catalog.

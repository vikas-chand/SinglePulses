# AI Guide: Background window selection

> Part of the benchmark framework (dev/BENCHMARK_PLAN.md). Complements the decision.json schema in scripts/39_approve_all.py by giving the JUDGEMENT CRITERIA.

**Purpose.** For ONE GRB, choose the pre-burst and post-burst time windows, per approved detector, that the polynomial background fit will be anchored on. A good window is a stretch of LIGHT CURVE where only background is present (no burst, no sub-pulse, no orbital trend), so 3ML's polynomial fit (grade 0-4, chosen by Wilks 3σ LRT, then per-channel refit) reconstructs the true baseline under the burst.

**When to use.** After detector selection, after `scripts/39_approve_all.py render` has written `results/approval/<trigger>_pending.json` and the LC PNGs to `plots/approval_lc/<trigger>_<det>.png`. You do this once per approved detector before writing the decision file.

**Which decision.json field this fills.** The `"windows"` map: `windows[det] = {"pre": [t1,t2], "post": [t3,t4], "window_source": "..."}`. (You also set `"detectors"` and `"source"` in the same file, but those are covered by their own guides; here, only `windows`.)

## Inputs (what to read)
- `results/approval/<trigger>_pending.json` — manifest: per-detector `png_path`, `angle_deg`, `in_bcat`, and `suggested_bkg` (a seed `{pre,post}` from scripts/28, may be null), plus a `suggested_source`.
- `plots/approval_lc/<trigger>_<det>.png` — the LC you JUDGE FROM. 1.024-s bins, linear y, counts s⁻¹, x = time since trigger. NaI shows 8-900 keV; BGO shows 250-40000 keV. **No T90 shading is drawn on purpose** — infer the burst region from the data alone; do not anchor on any catalog duration.
- Read EVERY approved detector's PNG. Windows are per-detector (a feature may sit at a different time/height in each), but pre/post edges are usually similar across detectors of the same GRB.

## ⚖ PI RULING 2026-08-31 — the burst-tail/background boundary is NOT determinable (read this BEFORE the criteria below)

*Given by the PI at the step-3/background gate of the Lane-A walkthrough on
bn110920546. Recorded verbatim; do not paraphrase it in downstream documents.*

> "you will never know where the emission ends, we have to judge it based on the nature of GBM physical background we added as skills until we someday decided to use a physical model, and tail is not an interesting part in this project as we are mainly concerned about the pulse is in or not (so this is project specific but until we have a physical background, all choices of background selection are subjective to the user)."

**The ruling settles four DISTINCT things. Keep them distinct — they have different
scopes and different expiry conditions.**

1. **EPISTEMIC — where the emission ends cannot be located with a polynomial
   background.** It is not that we have not yet measured it carefully enough; with this
   background model the quantity is not identified. See the measured evidence below.
2. **METHOD — judgement follows the WRITTEN GBM-background skills** (this guide's
   criteria + the physics reference at the end of it) **until a PHYSICAL background
   model is adopted.** The skills, not an attempt to find the true tail end, are the
   standard a window is judged against.
3. **SCOPE — project-specific, and stated as such.** In *this* project the tail is not
   of interest; the operative criterion for a window is **whether the PULSE is inside
   the window or not**. This is a scoping decision for the Two_Breaks census, NOT a
   general truth about GRB tails — do not export it to another project as physics.
4. **STATUS OF EVERY BACKGROUND CHOICE —** verbatim, *"all choices of background
   selection are subjective to the user"* until a physical background model exists.

**The evidence that forced it (measured on this burst the same day, 2026-08-31).**
Extrapolating b0's post-burst decay from two EQUALLY DEFENSIBLE uncontaminated
baselines — a fit on 111.3–266 s versus a fit on 200–266 s — gave inferred excesses in
the SAME interval of **+68 vs +481 cts s⁻¹, a factor ≈ 7**. Every variant tried was
POSITIVE, so the excess is REAL; its MAGNITUDE is not a measurement. That asymmetry is
the whole ruling in one line: *presence* is robust, *extent* is not.

**Independent corroboration (published; verified in the local PDF, not from memory).**
Biltzinger et al. 2020, A&A 640, A8 (`2020A&A...640A...8B`) use THIS burst as the
showcase for exactly this failure — §4 intro, p. 9, verbatim: *"we show how the model
can be used to fit the background for the GRB 110920A for which the classical approach
of using polynomial fits can give ambiguous answers"*; §4.1 + Fig. 15 show four
polynomial background selections that *"all look equally valid in a short time around
the GRB event (± 50 seconds)"* yet differ under the burst, *"which makes a random choice
of one of them necessary"*. Their stated cause: *"GRB 110920A was a bright, single pulse
GRB that occurred only about 100 seconds after an SAA exit of GBM"*, so the background
carries the activation decay a polynomial cannot represent. Local PDF:
`Skills_training/Biltzinger_2020_2020AA640A8B_bn110920546.pdf`. Verified locally at the
primitive on the same day: the SAA FLAGS bit-1 transition sits at **t−T0 = −120.07 s**
in `data/bn110920546/glg_poshist_all_110920_v01.fit` — consistent with their "~100 s".

**OPERATIVE CONSEQUENCE (what actually changes in practice).**
- A background window is judged by **(i) whether the PULSE is in or out, and (ii) the
  written skills** — **NOT** by trying to locate where the emission ends. Do not spend a
  gate arguing the tail's endpoint; that argument has no resolvable answer here.
- **Residual burst tail inside a background window is a DISCLOSED SYSTEMATIC, never a
  defect to re-adjudicate.** Disclose it (report + QC note) and move on. Re-opening it
  at a later gate is re-litigating an undecidable question, not quality control.
- **Subjectivity is NOT licence.** Every rule below still binds — the 50–150 s width, the
  HUG-THE-BURST inner edge, the 5–20 s margin band, "never anchor on a gap/SAA-exit
  edge", the source-in-gap invariant. The ruling removes ONE demand (locate the tail
  end); it removes no rule. What is subjective is the *choice among rule-compliant
  windows*, not compliance with the rules.
- **Scoring consequence (reaches Part 1):** because the choice is subjective, an
  AI-vs-human DIVERGENCE ON BACKGROUND WINDOWS IS NOT AN ERROR and must never be scored
  as one — background-window agreement is a **CONCORDANCE** measure, not an accuracy
  measure. See `dev/ai_guides/AgentArchitecture.md` **NR-40** and the caveat in
  `dev/BENCHMARK_PLAN.md` §"Which tasks carry real AI judgement".
- **Expiry condition:** points 1–4 hold *until a physical background model is adopted*.
  That module is banked as **#47** in `notes/PROJECTS_registry.md` (banked ≠ started).

**What this CLOSES.** The open question raised at this same gate — whether to push b0's
post-window further out, past the ~165.9 s catalog T90, to escape the residual tail — is
closed. The PI already answered *"Stop here — overlap cleared"*; this ruling supplies the
REASON: the further push chases a boundary that cannot be located, so it buys no
correctness, only a different subjective window.

**Mirror.** The same ruling + quote is recorded in the authoritative ruleset
`BACKGROUND_SELECTION_PROCESS.md` §"Step 3". If the two ever disagree, that is an NR-27
LAW-CONFLICT — raise it, do not pick one.

## Decision criteria (the heart)
Read the PNG. The burst is the obvious excess above a roughly flat floor. You are picking baseline ON EITHER SIDE of it.

SELECT a window where ALL of these hold:
- **Same locally-smooth regime on both sides** — NOT necessarily literally flat. A *gentle, coherent* slope is fine if one low-order curve through both windows would plausibly continue under the burst. Reject only genuine structure — steps, turnovers, strong exponential curvature (recognize these via the **physics reference** at the end of this guide, not just "looks non-flat").
- **No peaks above the local mean** inside it — no precursor, sub-burst, late tail, or single-bin spike.
- **Width 50-150 s per side, aim ~80-120 s** (STRICT). Too wide picks up orbital curvature and over-constrains the fit; too narrow under-constrains the polynomial. At 1.024-s bins that is ~50-150 bins.
- **Buffer from the burst edge** so the burst tail does not leak in — keep a clear gap (tens of seconds for a long burst). Estimate the burst's visible extent **from the LC excess itself**, NEVER a catalog/GCN T90: T90 is an OUTPUT of this pipeline (derived later, from the background-subtracted LC), so it cannot inform this step; and Stage 1 consumes **no** GCN/catalog quantity at all — this pipeline is a GCN *producer*, not a consumer (a GCN is itself a human quick-look; depending on it defeats the purpose).
- **HUG THE BURST — build each window from the burst *outward*, anchoring the INNER edge near the burst.** This is the single most-violated rule, so it is now explicit. The polynomial must INTERPOLATE the baseline *under* the burst, and interpolation error grows with the distance from the burst to the nearest data used — so the window's **inner** edge must sit as close to the burst as the tail-buffer allows, and you then extend the **outer** edge back/forward to reach the 50–150 s width. Do NOT build the window from a far feature (a gap edge, a flat patch 100 s away) *inward* and stop 30–40 s short of the burst; that leaves the nearest clean baseline unused and forces an extrapolation.
  - **It is a BAND, not "as close as possible" — keep a SAFE MARGIN on both sides.** With near-edge gaps `g_pre = source_start − pre_stop` and `g_post = post_start − source_stop`: **TARGET `g_pre, g_post ≈ 5–20 s`.** BOTH bounds are real defects:
    - `g > ~40 s` (**too far**) → extrapolation, nearest baseline unused (the far-window defect).
    - `g < ~5 s` (**too tight, razor-thin**) → the burst's **soft tail extends past the visible >5σ core**, so a window that touches the core leaks tail flux into the background and **over-subtracts**. Never let the inner edge touch the burst (`g = 0` is wrong). Judge the margin from where the LC *actually returns to baseline* (the soft tail), NOT from the red >5σ shade — leave a clear buffer past that return.
    The ceiling `0 ≤ g_pre, g_post ≤ G_max = min(200 s, max(50 s, 2 × D_vis))` (`D_vis` = visible burst extent) still holds as a last-resort cap, but the working target is the 5–20 s band. *(Cap is pipeline POLICY, not physics; frozen for the benchmark.)* A brighter/longer burst has a longer soft tail → use the upper end of the margin.
  - **A data gap / SAA-exit *before* the burst:** cross it, but do **NOT** anchor the inner edge at the post-gap edge. That edge sits on the SAA **bi-exponential decay** (a *fast, recognizable* component — see the physics reference — **not** baseline). Come FORWARD, past the decay, to the *settled* baseline that hugs the burst. The clean stretch immediately before the burst is the correct anchor; the noisy stretch right after the gap is not. (Same logic mirrored for a gap after the burst on the `post` side.)
  - If a hard fast feature blocks every near window and forces `g > G_max`, do NOT silently relax it — abstain/flag.
- **Far from orbital features** — avoid broad rises/falls, SAA-like rate steps, Earth-limb ramps.

AVOID (move elsewhere / pick the flattest part and flag) if ANY:
- Rising or falling trend across the window → prefer a **shorter clean window closer in** over sliding far; only slide well past the burst if a **hard** contaminant (sub-pulse, occultation step, SAA-exit tail) blocks the near region, and FLAG it. A distant flat window that forces the polynomial to extrapolate is worse than a shorter near one.
- Sub-burst / precursor > ~3σ above local floor → pick the other side, or skip past it.
- Hot bin / single-bin spike → shift the window so it is excluded.
- Step change in rate → keep the window entirely on ONE side of the step.
- Pre-burst stretch < 10 s available → use what exists and add flag `pre_window_too_short`; same for post → `post_window_too_short`.

Time-order rule: the EARLIER window is `pre`, the LATER is `post`. Both must be strictly increasing (`t2>t1`, `t4>t3`), non-overlapping with `t3 >= t2`, and the burst (the eventual source window) must fall in the gap `[t2, t3]` — validation requires `pre_stop <= source.t1 < source.t2 <= post_start`.

Seed handling (`suggested_bkg`): treat it as a starting proposal, not ground truth. If it already satisfies all criteria, accept it verbatim → `window_source: "accepted_suggestion"`. If you nudge edges → `"adjusted"`. If no seed existed or you discard it and pick fresh → `"drawn_fresh"`.

## The aids drawn on the light curve (use them, then apply the rules above)
Each PNG now carries two **data-derived** aids (no catalog/GCN input, so consistent
with "identify the burst from the data alone"):
- **`imodpoly_mad` baseline (orange)** — a MAD-robust polynomial that tracks ONLY the
  background (it clips the burst; LATBright `robust_polyfit`, pybaselines-style).
  Read it as the physical baseline: **if it's a gentle ramp, the background is a slow
  component (orbital/particle) — put your windows ON that ramp, NEAR the burst, so
  the polynomial interpolates.** A flat stretch far away is a *different* baseline
  level — don't chase it (this is the exact trap that made two AI raters diverge).
  **Caveat: the baseline aid tells you the background LEVEL/shape, NOT how close to
  sit.** Proximity is on you — the aid will look "fine" under a window placed 40 s
  from the burst, but that window still extrapolates. Always combine the aid with the
  HUG-THE-BURST rule above: sit on the aid *right next to the burst*, not wherever it
  looks flattest.
- **transient shade (red)** — the >5σ (MAD) excess above the baseline = the burst.
  Use it to locate the emission and the clean background on each side. It is an AID,
  not a mandate: extend/trim by eye for a precursor or soft tail, and still choose the
  discrete windows by the rules above.

## Reference: the physics of the GBM background (Biltzinger et al. 2020, A&A 640, A8)
The background is an **additive superposition** of physical components — recognize the
*shape*, don't just seek "flat":
- **Slow → locally flat on the burst timescale → this IS your baseline:** cosmic
  γ-ray background (<5–10% orbital wobble, §3.3.4), cosmic rays (~96-min orbit,
  §3.3.5), Earth albedo (~96-min, §3.3.3), constant (§3.3.1). A gentle ramp under the
  burst is usually one of these — fine to sit on, *near* the burst.
- **Fast / recognizable → AVOID (and the reason you sometimes must move):**
  - **SAA exit** — a step up after an off-gap, then a **bi-exponential decay** (fast
    ~min, slow ~hours; §3.3.2, Eq. 4). *The* trap: a window on the decay is not a
    stationary baseline — the paper shows four defensible selections near an SAA exit
    giving four *different* baselines (Fig. 15).
  - **Occultation step** — a bright point source (e.g. Crab) blocked by Earth → a
    sharp level change, mostly <100 keV (§3.3.6). Keep both windows on ONE side.
  - **Solar flare** — an exponential tail (episodic; §3.3.7). Exclude it.
  - **Data gap** — detectors off in SAA → a literal gap. Never window across it.
  *(SAA timescales are stated as the paper states them — "~min / hours"; the exact
  constants are fit per event. Do not invent numbers.)*

## Output contract (write into `results/approval/<trigger>_decision.json`)
Add one entry per approved detector to `"windows"`:
```json
{
  "trigger": "bn110721200",
  "approver": "Claude (AI)",
  "mode": "ai_vision",
  "detectors": ["n6", "n7", "b1"],
  "source": {"t1": <burst start>, "t2": <burst stop>},
  "windows": {
    "n6": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "adjusted"},
    "n7": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "accepted_suggestion"},
    "b1": {"pre": [-95.0, -10.0], "post": [40.0, 130.0], "window_source": "adjusted"}
  },
  "reasoning": "flat pre/post baselines; avoided a +20s sub-pulse"
}
```
`window_source` must be one of `accepted_suggestion | adjusted | drawn_fresh` (validator rejects others). Values are seconds since trigger (floats). The ingest step (`scripts/39_approve_all.py ingest`) maps these to `BKG_NEG_START/STOP`, `BKG_POS_START/STOP` in `results/background_intervals.ecsv`.

## QC checklist (before approving)
- [ ] Every approved detector has a `windows` entry; `pre`/`post` present and increasing.
- [ ] Each window 50-150 s wide (flag if forced narrower).
- [ ] **MARGIN check (both bounds): `g_pre` and `g_post` in the ~5-20 s band.** Too far (`> ~40 s`) leaves the near baseline unused (extrapolation); too tight (`< ~5 s`, touching) leaks the burst's soft tail into the background (over-subtraction). The inner edge must clear where the LC returns to baseline, not just the >5σ shade — never `g = 0`.
- [ ] **No gap/SAA-exit edge as an anchor:** if a data gap precedes/follows the burst, the inner edge is on the *settled* baseline near the burst, NOT on the post-gap decay tail.
- [ ] `pre` and `post` are off-source: visibly flat, no peak/step/spike inside.
- [ ] Burst lies fully inside `[pre_stop, post_start]`; `post_start >= pre_stop`.
- [ ] `source.t1/t2` sits inside that gap for EVERY detector (validation hard-fails otherwise).
- [ ] Mentally fit a low-order line/parabola through both windows — does it form a believable floor under the burst with no kink?
- [ ] `window_source` matches what you actually did relative to the seed.

## Common pitfalls (a human reviewer would catch)
- Putting a window ON the burst or a sub-pulse because the y-axis is linear and a faint pulse looks like baseline — zoom mentally on the floor.
- Over-wide windows (200-400 s) that span an orbital rise — looks "more data" but corrupts the polynomial; the rule is 50-150 s for a reason.
- Touching the burst edge with no buffer → tail contamination biases the fit high.
- Asymmetric quality (clean pre, sloped post) accepted silently — pick the flattest available and FLAG, don't pretend it's clean.
- Reusing one detector's edges blindly when a feature lands differently in another detector's band (esp. NaI vs BGO).
- Forgetting the source-in-gap invariant → ingest rejects the whole decision as INVALID.

## LLE background (13 LLE-bearing bursts)
If the burst has `gll_lle_*.fit*`, the human GUI now adds an **LLE 30–100 MeV** background step after the NaI/BGO windows: the LLE light curve is shown seeded with the brightest-NaI pre/post windows, and the rater confirms those epochs are clean in LLE (particle backgrounds differ from NaI — watch for a spike absent in the NaI LC) or nudges them. An accepted window becomes an `lle` row in the catalog; the fit engine (`scripts/10`) prefers it over NaI inheritance. The **source stays the shared per-burst emission window** (marked on NaI). *AI-vision parity is an OPEN item (R-LLE-5): there is no LLE render for the AI path yet, so AI catalogs inherit the NaI windows for LLE — do not fabricate an LLE selection in `ai_vision` mode.*

## How this is scored vs humans (BENCHMARK_PLAN.md, task #2)

> **⚖ 2026-08-31 — read the four metrics below as CONCORDANCE, not accuracy.** Under the
> PI ruling at the top of this guide, *"all choices of background selection are subjective
> to the user"* while the background is polynomial. There is therefore NO ground truth for
> a window edge: the human catalog is a second rater, not a key. Edge Δ and IoU measure
> **how similarly two raters chose among rule-compliant windows**; they do not measure
> whether the AI was right, and no benchmark number may present them as an AI error rate.
> The two metrics that DO carry a truth value are the rule-compliance checks (does the
> window satisfy the criteria above — width, margin band, no gap anchor, source-in-gap)
> and the downstream-impact test (do the physics conclusions survive the swap).
> Register row: `dev/ai_guides/AgentArchitecture.md` NR-40.

Run Stage 1 in `human_gui` and `ai_vision` mode on the benchmark subset → two stamped catalogs; `scripts/40_benchmark.py` compares per (trigger, detector):
- **pre/post edge Δ (s)** — absolute difference of each of the four edges vs the human.
- **window IoU** — intersection-over-union of the AI vs human pre+post intervals.
- **polynomial-fit residual χ²/dof** — quality of the 3ML polyfit on the AI window (is the chosen baseline statistically clean?).
- **baseline flatness** — residual scatter of the fitted background across the window.
Plus the shared downstream-impact test: run identical Stage 2-3 on both catalogs and compare Ep, α, kT, and the thermal-vs-double-break classification per bin/burst. The headline question is whether the physics conclusions survive the human→AI swap. Inter-human scatter (if multiple experts) is the denominator: the AI is "good" if it matches humans about as well as humans match each other.

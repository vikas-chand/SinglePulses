# Special bursts — per-burst source / analysis overrides

Bursts in the 106-single-pulse sample that need **non-default source handling**.

> **AI selection (`ai_vision`) and human reviewers MUST consult this file before
> choosing the source interval.** The default peak-find grabs the *brightest* spike,
> which is wrong for multi-episode bursts where the analysable single pulse is not the
> brightest one. This file records the REASON so it survives into the paper's sample
> notes and so any re-analysis targets the correct episode. Once a human stamps a
> `human_gui` decision, that decision's `source` is authoritative.

---

## bn130427324 (GRB 130427A) — analyse the **SECOND** pulse

- **Target: the smooth FRED pulse at ~105–185 s**, *not* the bright multi-peaked spike
  at 0–40 s.
- **Rationale** (Vikas, 2026-07-17): the 0–40 s episode is multi-peaked and is not a
  clean single pulse; the ~120 s episode is the single FRED pulse, and it is also
  where 130427A's LAT/LLE high-energy emission dominates.
- **AI default was WRONG here**: the first-pulse peak-find selected source ≈ [−1, 61] s.
  The human source is the *second* pulse. (This is a legitimate AI-vs-human benchmark
  disagreement, not a code bug — log it as such.)
- **Background**: pre-window before the first pulse (~[−100, −15] s) is fine; the
  post-window **must sit AFTER the second pulse** (~[195, 400] s), never on it. The
  first pulse then falls in the background *gap* (excluded from the fit, not analysed).
- ⚠ **Consequence**: 130427A's EXISTING fits — the Ep–kT anchor / Burgess reproduction —
  were done on the FIRST pulse and **must be redone on the second pulse**. Flag this
  before quoting any 130427A anchor numbers.

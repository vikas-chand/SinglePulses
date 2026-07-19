# Excluded bursts — not analyzed (with reason)

Bursts removed from the science analysis, with the reason. The machine-readable
companion is `results/excluded_bursts.ecsv` (the re-fit driver must SKIP any
trigger listed there). Do NOT delete their rows from
`results/background_intervals.ecsv` while a review GUI is running — the
exclusion list is the authoritative skip mechanism.

## Rule: no NaI detector within θ < 60° of the source
If the closest NaI detector to the source is at θ ≥ 60°, the source is too far
off-axis for any detector to give a reliable spectrum, so the burst is not
analyzed. (θ = angle between the detector normal and the source direction;
smaller = better response.)

| Trigger | Reason | Closest NaI | Threshold |
|---|---|---|---|
| bn210812699 | No NaI below 60°; nearest is `nb` at θ = 60.12° (source = 39.70, 69.59) | nb, 60.12° | < 60° |

*Noted by Vikas Chand via detector-picker review, 2026-07-19.*

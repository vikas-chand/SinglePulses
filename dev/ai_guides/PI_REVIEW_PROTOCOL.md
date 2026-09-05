# PI REVIEW PROTOCOL — the 20-burst reading session

**Purpose.** Vikas reads every document from the 20-burst campaign (Codex-produced,
Claude-verified) and gives feedback "like a teacher checks students' reports":
writing, results, figures, method, everything. This file defines how that
feedback is captured so it becomes DURABLE instead of conversational.

**The rule that makes it worth his time** (AgentArchitecture P5/P8 + the standing
feedback rule): every comment he makes is routed to the strongest enforcement
layer that can carry it, in the same session. A comment that only lives in chat
is a defect in this protocol.

## Routing table — where each kind of feedback lands

| feedback kind | example | lands in | becomes |
|---|---|---|---|
| WRITING / register | "this paragraph is dense", "don't say X" | `~/Desktop/Projects/WritingHelper.md` (running decisions) + the paper's prose | a prose rule + a fixed draft |
| FIGURE convention | "the band should…", "show components" | `dev/ai_guides/FigureVisionQC.md` STANDING CONTRACT (his words, quoted + dated) | a verifier contract item — checked on EVERY future figure |
| RESULT / physics | "this kT is not thermal", "report as a tie" | the burst's `VISION_QC.md` + `dev/ai_guides/SpectralFitting.md` L-series | a lesson + (where possible) a code guard |
| METHOD / estimator | "scan the window", "use our tool" | the relevant skill (`Temporal.md`, `SpectralFitting.md`) + code | a changed default in the producer script |
| PROCESS / missing check | "who verified this?" | `dev/ai_guides/AgentArchitecture.md` REGISTER | a new agent row (NR-n) → frozen at #10+ |
| CAMPAIGN science | "this pattern across bursts is real/not" | `results/campaign/*.ecsv` accumulators + `SCIENCE_INTERPRETATION_*.md` | an accumulator column or a Q1/Q2/Q3 registry entry |

## Session mechanics

1. **Order:** read in queue order (#3 → #22), one burst at a time; the paper
   first, then its figures, then its numbers if he wants to drill.
2. **Capture:** every comment gets an entry in
   `notes/PI_REVIEW_20BURST_FEEDBACK.md` with: burst, artifact, his words
   (verbatim — never paraphrased into a rule without his phrasing preserved),
   the routing destination, and the action taken.
3. **Same-session routing:** the DISTILLER applies each item to its layer before
   the next burst is opened. No "I'll do it later" queue — that queue is where
   the lag-sign fix sat for two weeks.
4. **Cross-burst items:** feedback that applies to all bursts (a figure
   convention, a prose rule) triggers a batch re-render / re-edit across the
   whole set, not just the burst in front of him.
5. **Disagreement is data:** if he rejects a result, record the reasoning, not
   just the verdict — the reasoning is what a future agent needs.

## Pre-session preparation (Claude does this before he sits down)

- Every Codex figure passed the figure-verifier; every number recomputed by the
  numbers-verifier; verdicts sha256-bound in each burst's `VISION_QC.md`.
- A campaign contact sheet: one page per burst — winners table, temporal
  headline numbers with estimator labels, thermal candidates with the
  3.92·kT edge check, and anything the verifiers flagged but could not fix.
- A "known weak points" list per burst, written honestly BEFORE he reads —
  so he is checking our judgement, not hunting for what we hid.

## After the session

- Feedback file committed with the papers.
- Register rows opened for every missing-agent finding; contracts amended with
  his quoted words.
- `BURST1_LESSONS.md` gets a sibling: `CAMPAIGN20_LESSONS.md`, folding his
  feedback into the taxonomy that the freeze at burst #10+ will encode.

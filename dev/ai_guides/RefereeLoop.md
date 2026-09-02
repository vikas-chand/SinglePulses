# Skill: The Referee Loop (two-hat External Auditor)

**Purpose:** bounded cross-family review of a milestone product, modeled on the
reviewer→revision→reviewer cycle of journal publication.
**Audience:** the operating session (any harness) + the PI.
**Born:** PI design ruling 2026-09-01, verbatim: "codex must act like
supervisior which we probably have and have a duty of an audtior and
brainstormer; and second duty should be the reviewer which is blind and a
cold referee with temperature adjustable" + "It's kind of reviwer -
revision -reviewer-revision loop that humans have mastered for publications."
**Reusable:** any milestone product (paper, doctrine change, freeze, contested
verdict, portability test). NOT per-burst — quota is PAID (standing rule:
probe cheap first, never auto-relaunch, PI triggers every firing).

## The two hats (never worn in the same invocation)

**DUTY 1 — SUPERVISOR (auditor + brainstormer).** Full context: the brief
pins facts by sha, declares deliberate conventions, lists claims to verify,
and ends with the independent-judgment question. This is the existing
codex-review pattern (A15 track record). Constructive by contract; may
propose ideas beyond the brief. Output contract: VERDICT / per-item
CONFIRMED-NOT CONFIRMED / DISCREPANCIES with exact fixes / COULD-NOT-VERIFY
/ independent judgment.

**DUTY 2 — BLIND REFEREE (cold, temperature adjustable).** Gets ONLY what a
journal referee gets: the manuscript/product and its data-availability
statement. NO internal reasoning docs, NO architecture files, NO claims
list, NO conversation history. Severity dial set per firing by the PI:
- **T0 constructive** — notes and suggestions, no verdict pressure;
- **T1 standard** — journal-style report, findings classed MAJOR/MINOR;
- **T2 adversarial** — briefed to refute the central claims, must attempt
  demonstrations, not arguments. (Default T1.)
The two hats never mix: a supervisor invocation is disqualified from
refereeing the same product version, and vice versa — context contamination
is the thing blindness exists to prevent.

## The loop (bounded by construction)

- **Round 1:** referee report on the product.
- **Revision + RESPONSE LETTER:** the operating session adjudicates every
  referee point at the primitive and writes a point-by-point response —
  the publication artifact humans mastered. Every point gets exactly one
  type (below) and, where contested, a DEMONSTRATION (recompute, re-render,
  diff), never an argument.
- **Round 2 (delta):** referee receives the revised product + the response
  letter + the diff — exactly as journals do — and rules on the responses
  only; it does not re-derive what it already confirmed.
- **HARD CAP: 2 referee rounds.** A third round is a new PI decision, never
  an automatic continuation. Round budget is pre-declared in the brief.

## Convergence: by demonstration, never by agreement

The loop does NOT converge when the two systems agree (false-corroboration
scar: two independent checks once agreed and were both wrong at a shared
primitive). It converges when every referee point in the response letter is
one of:
- **FIXED** — with the demonstration attached;
- **REBUTTED** — with the demonstration attached;
- **OPEN-DISAGREEMENT** — both positions + evidence registered, handed to
  the PI. Never silently dropped; the PI gate closes it, not the loop.

## Disagreement types (each point carries exactly one)

1. **MATHEMATICAL ERROR** — someone computed wrong; fix and demonstrate.
2. **STATISTICAL-RIGOR GAP** — a shortcut with no defense; repair it or
   disclose it as a limitation in the product itself.
3. **DEFENDED PHYSICAL APPROXIMATION** — rigor was knowingly traded for
   physics. The referee may NOT fail such an item; it may check only that
   (a) the assumption is declared, (b) its domain of validity is stated,
   (c) the caveat rides every number derived under it — and it MAY contest
   the declared domain, which is a legitimate scientific dispute and goes
   to OPEN-DISAGREEMENT. Precedent: the polynomial background (published
   ambiguity carried + expiry condition = a physical background model).
   The product's assumption registry is the referee's checklist for (a).

## Quality checklist
- [ ] hat declared in the brief's first line; blind brief contains no
      internal file, no claims list, no reasoning
- [ ] severity T set by the PI for this firing
- [ ] round budget pre-declared; cap 2
- [ ] response letter typed point-by-point, demonstrations attached
- [ ] OPEN items registered and presented at the PI gate
- [ ] every referee finding adjudicated at the primitive before action
      (advisory only — A15 law unchanged)

## Common pitfalls
- Convergence-by-agreement (see scar above).
- Hat mixing: feeding the referee our reasoning "for efficiency" — that
  buys agreement and destroys the blindness that makes the report worth
  paying for.
- Unbounded politeness loops: round 3+ without a PI decision.
- Scoring a defended approximation as an error (type-3 protection).
- Auto-relaunch on a failed/hung invocation (standing quota law).

## Hand-off
Feeds the PI gate (BurstWalkthrough / paper gate). Supervisor duty remains
the codex-review skill; this file governs the referee duty and the loop.

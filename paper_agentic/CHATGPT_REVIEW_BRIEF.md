# Review brief — agentic_grb v2 draft (for ChatGPT)

**Upload with this brief:** `agentic_grb_v2.pdf` (current draft: abstract + §1 + §2 drafted;
§3–§8 are structured stubs) and `REWRITE_OUTLINE_v2.md` (the approved plan for the rest).

**Venue:** arXiv (astro-ph.IM, cross-list cs.AI) + Zenodo artifact DOI. No journal referee —
so YOU are the adversarial referee. Review accordingly.

## What this paper claims (so you can attack it)
1. A **gated workflow with bounded agency** (not an autonomous agent) can run time-resolved
   GRB spectroscopy end-to-end, with every decision stamped and human-gated.
2. The system **learns without gradient updates**: a versioned Skill Library where every
   lesson = claim + provenance + executable test; the learning curve over bursts is the
   evidence.
3. **Verification doctrine**: blind-first frozen predictions; independence must live at
   shared primitives; AI panels are generators, not adjudicators.

## Review this draft FOR:
- **Over-claiming** — anywhere the prose promises more than a 10-burst provisional campaign
  can support. Flag every instance. (The authors have retracted over-claims before; assume
  more exist.)
- **The workflow/agent framing** (§1) — is the distinction clean, correctly attributed, and
  is "bounded agency" defensible terminology or marketing?
- **§2 architecture description** — is it followable by someone who has never seen the repo?
  Are the paper-names (Skill Library, Campaign Protocol, Reconciliation Protocol, …) used
  consistently? Anything that only makes sense with insider knowledge?
- **The abstract** — does "Yes---with a human at the gate" land, or is it cute at the cost of
  credibility? Would you shorten it?
- **Structure** (outline §3–§8) — ordering, redundancy, anything missing for an
  astro-ph.IM/cs.AI audience.
- **The learning-curve claim** — what would a skeptical ML reader say about "27 lessons,
  10 bursts" as a training claim? What controls or baselines would they demand?

## Do NOT spend effort on:
- Citations — all `[cite: …]` markers are placeholders; verification happens on our side
  against ADS. Do not supply BibTeX (our rule: hand-written bibliography is forbidden;
  everything is exported from ADS).
- The provisional numbers — flagged (p), regenerated at the frozen sweep by design.
- LaTeX/typography.

## Ground rules for your suggestions
- Your review is **advisory, not a spec** (standing rule). Concrete rewrites welcome; we
  merge critically.
- If you claim a factual problem, state exactly which sentence and why — vague unease is
  fine to report but label it as such.
- Separate your output into: MUST-FIX / SHOULD-CONSIDER / TASTE.

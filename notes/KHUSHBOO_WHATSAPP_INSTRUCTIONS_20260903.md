# For Khushboo — walking one single-pulse burst at a time, and logging it on GitHub (2026-09-03)

(Plain text below is written to be pasted into WhatsApp as-is. Repo: github.com/vikas-chand/SinglePulses, private;
Khushboo is already a collaborator as Khush1406. Everything current is on branch `memory-guard`.)

---
Hi Khushboo — here is how we now run bursts, one at a time, and how to log what you find so we can answer it.

1) GET THE CODE (once), then pull before every burst
   git clone https://github.com/vikas-chand/SinglePulses.git   (or: cd SinglePulses && git fetch)
   cd SinglePulses && git checkout memory-guard && git pull
   Everything current is on memory-guard, not main.

2) ENVIRONMENT (heavy tier = threeML + fermitools; needed for data, binning, fits)
   conda activate threeML
   export FERMI_DIR=$CONDA_PREFIX/share/fermitools
   export CALDB=$FERMI_DIR/data/caldb; export CALDBCONFIG=$CALDB/software/tools/caldb.config
   export CALDBALIAS=$CALDB/software/tools/alias_config.fits; export CALDBROOT=$CALDB
   export EXTFILESSYS=$FERMI_DIR/refdata/fermi; export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
   Details and the light tier: AGENTS.md section 2.
   Also install the GitHub CLI once:  brew install gh   then  gh auth login

3) PICK A BURST AND CLAIM IT
   The sample is results/single_pulse_grbs.ecsv (106 bursts); the order and where products live is
   notes/REVIEW_INDEX_106.md. Before starting, check open issues so we do not both take the same burst:
   gh issue list --label walkthrough
   Then open the burst's issue (one issue per burst, it is the running log):
   gh issue create --template burst_walkthrough.md --title "bnXXXXXXXXX — walkthrough by Khushboo"
   (or on the website: New issue → "Burst walkthrough log").

4) DATA for the burst
   python scripts/02_download_data.py     (downloads TTE+CSPEC+RSP+POSHIST for the sample into data/<trigger>/;
   idempotent, so it only fetches what is missing; run it once and let it finish, or copy data/<trigger> from Vikas).

5) RUN THE WALKTHROUGH — with your AI (recommended)
   Open Claude Code (or Codex) in the repo root and paste:
   "Read dev/ai_guides/FreshSessionBoot.md, then dev/ai_guides/BurstWalkthrough.md. Walk burst bnXXXXXXXXX one
   step at a time in the official ledger order (0b, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9). At every step: RUN it, PRESENT
   the four items (what the step does, what actually ran, conclusions with honest flags, what is unexplained), and
   WAIT for my approval before the next step. Steps 2–5 are ADOPT mode: present the stamped catalog decision, do
   not re-decide it. Record my approvals with dev/live_report.py --approve --by 'Khushboo Sharma'. After each
   approved step, post the PRESENT text as a comment on GitHub issue #N with `gh issue comment N --body-file`,
   attaching the step's figures. If anything fails or disagrees with a paper, open a separate issue with
   `gh issue create --template bug_or_question.md` and continue only if the step can be completed honestly.
   Never paste a number you did not recompute from the products."
   Replace bnXXXXXXXXX and #N. Approve only what you have looked at.

   Without an AI: follow handoff_background_approval/KHUSHBOO_RUN_ONE_BURST.md (one burst, every product) and
   AGENTS.md section 4 for the exact commands (Stage 1 approval is already done for all 106 — adopt it; then
   scripts/27b binning, the fitting driver, then the products and REPORT_<trig>.md).

6) WHAT TO LOG (this is the part that helps us most)
   - One comment per step on the burst's issue, the four items above, with the step's PNGs dragged in.
   - At step 9: attach REPORT_<trig>.md and the PDF; tick the checklist; propose lessons at the bottom
     ("what would you tell the next person before this step") — Vikas accepts or rejects them into the skill files.
   - Anything broken, surprising, or disagreeing with a paper: a separate issue (bug_or_question template),
     with the exact command, the last 30 log lines, and the paper page you compared against.
   - Do not commit results/ (it is ignored on purpose); do commit nothing to memory-guard without asking —
     your notes go in the issues.

7) WHAT HAPPENS NEXT
   We pull your issues with gh, answer each one, and turn the confirmed ones into numbered lessons (with a test)
   in the skill files, so the next burst runs better for both of us. One burst at a time; do not batch.
---

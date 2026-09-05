# CODEX QUOTA DISCIPLINE (rule, 2026-08-17)

Codex is a **paid, metered, exhaustible** resource (Vikas pays $100/mo). On
2026-08-16/17 an orchestration loop of mine burned a large share of that quota
on runs that produced nothing: each relaunch paid for a full ultra-reasoning
boot (re-reading the runbook + architecture + contracts + skills, ~10k+ tokens
of reading before any work) and the harness then killed the session before a
single fit was saved. Quota exhausted; locked out until Aug 19 23:32.

## Rules

1. **NEVER put `codex exec` in an auto-relaunch loop.** No monitor, watchdog, or
   supervisor may respawn Codex. A dead Codex session stays dead until a human
   or a deliberate, reasoned decision restarts it. (This is the rule that was
   violated: three separate supervisors each respawned it.)
2. **Probe before launching** when a lockout is possible:
   `codex exec -m gpt-5.6-sol -c model_reasoning_effort="low" -s read-only
   "Reply with exactly: PROBE OK"` — costs almost nothing, and a lockout error
   is visible immediately instead of after a full brief boot.
3. **One pass per task.** Write the brief so a single invocation completes
   something useful and self-contained. If the work cannot survive a ~20-minute
   session, it is the WRONG WORK for Codex (see rule 5).
4. **Never send Codex work whose value is lost on interruption.** Long fits,
   long renders, anything that only writes output at the end. Those belong to
   the Claude-side pools, which resume per-item.
5. **Reserve Codex for what only it can give: cross-family independent
   judgement.** Audits of finished products, adversarial review of claims,
   reading our numbers against the literature. Its careful, declarative style
   and different training lineage are the asset — not its throughput.
6. **Effort tier matches the task.** `ultra` for adjudication-grade audits;
   `low`/`medium` for mechanical checks. Do not default to ultra.
7. **Budget visibly.** Before a Codex run, state in the session what the run is
   for and why it is worth the quota. If that sentence is hard to write, do not
   spend it.

## Standing queue (fire when quota returns)

`notes/CODEX_BRIEF_audit_campaign_20260819.md` — one-pass external audit of the
completed campaign papers. Written 2026-08-17, ready.

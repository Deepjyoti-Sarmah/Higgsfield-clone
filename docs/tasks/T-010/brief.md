# Brief T-010: STATUS truth pass

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Status: `docs/STATUS.md` (the file you are fixing)
- Board: `docs/PLAN.md` (stale rows you are fixing)
- Handoff brief that ordered this task: the session prompt (Stage 1.1)

## Goal
Make `docs/STATUS.md` (and the stale rows of `docs/PLAN.md`) true again: retire the
rows the live deploy falsified, fix the pooled-vs-unpooled wording, and rewrite
`NOT STARTED` (specs 002–009 are code-complete; spec 003 is verified live 9/9).

## Allowed files (touch nothing else)
- `docs/tasks/T-010/brief.md` (this file)
- `docs/tasks/T-010/report.md`
- `docs/STATUS.md`
- `docs/PLAN.md`
- `docs/WORKLOG.md` (append one line)
- `.agent-logs/*T-010*` (your own session transcript export)

## Must reuse
- `scripts/check-links`, `scripts/check-standards` (the verify command)
- Evidence already in the repo: `docs/WORKLOG.md` (2026-09-13 19:30 live smoke 9/9),
  `docs/tasks/T-009-8/report.md` (spec 009 done, 171 passed)

## Acceptance checks
- [ ] `docs/STATUS.md` no longer claims: "R2 configuration is BLOCKED", "Deploy +
  Modal are PLACEHOLDERS", "`gh` CLI login broken" as a blocker, or the Neon pooled
  test-hang as a current blocker
- [ ] `docs/STATUS.md` LIVE row says UNPOOLED (the pooled DSN drops LISTEN/NOTIFY)
- [ ] `docs/STATUS.md` NOT STARTED says: specs 002–009 code-complete; 003 live-verified
  9/9; 004–009 browser `verify-slice` pending (T-011); Modal spike/adapters open
  (T-012…T-014); P1 gaps open (T-015…T-019)
- [ ] `docs/PLAN.md`: M2/M3, T-002-4/T-002-5 and the pre-hand-in checklist no longer
  say R2 keys are pending or the repo is uncreated
- [ ] `docs/WORKLOG.md` has one appended T-010 line
- [ ] No code, contract, or README changes; no secrets printed anywhere

## Verify command (paste its full output in report.md)
```
scripts/check-links && scripts/check-standards
```

## Out of scope
- Re-running the live smoke (that is T-011/T-014 territory; cite the recorded 9/9,
  do not claim a fresh run)
- Any browser click-through (`docs/verification/` stays empty; T-011 owns it)
- Fixing `README.md`'s two stale lines (R2-pending, repo-TBD): log them as an open
  issue in the report instead
- Modal, OAuth, Library P1, mobile, hygiene stages

## Report
Write `docs/tasks/T-010/report.md` using `docs/templates/report.md`. Commit all of the
above in ONE commit with a plain message (no attribution trailers), including the
`.agent-logs/` export. Do not mark your own work reviewed.

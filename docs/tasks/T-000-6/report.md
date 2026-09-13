# Report T-000-6

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/package.json` — one line: `"typecheck": "tsc --noEmit"` → `"typecheck": "tsc -b"`.
- `docs/tasks/T-000-6/report.md` (this file, new).
- `docs/STATUS.md` — removed the now-false BROKEN row, added one WORKS row.
- `docs/WORKLOG.md` — one appended line.
- **Not committed**, per the brief (the orchestrator commits). No other file touched.

## Problem (reproduced, not assumed)
`apps/web/tsconfig.json` is solution-style — `{"files": [], "references": [tsconfig.app.json, tsconfig.node.json]}` — and `tsc --noEmit` does **not** follow project references. It therefore compiled an empty program and exited 0, so the `typecheck` script was green while checking nothing:

```
$ npm --prefix apps/web run typecheck            # BEFORE
> tsc --noEmit
exit 0                                            # <- green, but zero files

$ (cd apps/web && ./node_modules/.bin/tsc --noEmit --extendedDiagnostics | grep -E '^Files|^Lines of TypeScript')
Files:                          0
Lines of TypeScript:            0
```

The real type gate was only the `tsc -b` inside `build`, exactly as the STATUS BROKEN row said.

## Fix
One line in `apps/web/package.json`:

```diff
-    "typecheck": "tsc --noEmit",
+    "typecheck": "tsc -b",
```

`tsc -b` follows the references and builds both real projects — `tsconfig.app.json` (which has `"include": ["src"]`) and `tsconfig.node.json` (`vite.config.ts`) — so the script now type-checks the sources and exits non-zero on a type error. Build info goes to `apps/web/node_modules/.tmp/*.tsbuildinfo` (inside `node_modules`, already ignored), so no new tracked artifact appears.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run typecheck

> web@0.0.0 typecheck
> tsc -b

-> exit 0

$ npm --prefix apps/web run build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 89 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-GXi1qc62.css   26.75 kB │ gzip:   5.67 kB
dist/assets/index-kkZN2yhM.js   327.55 kB │ gzip: 102.12 kB

✓ built in 290ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

$ (cd apps/web && ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit --extendedDiagnostics | grep -E "^Files|^Lines of TypeScript")
Files:                         192
Lines of TypeScript:          5059

=== verify command: all steps exit 0 ===
```

## Proof the new gate is real (not merely "still green")
A temporary probe file was added, exercised and deleted — no file left behind:

```
$ printf 'export const probe: number = "definitely not a number"\n' > apps/web/src/__typecheck_probe.ts
$ npm --prefix apps/web run typecheck
> tsc -b
src/__typecheck_probe.ts(1,14): error TS2322: Type 'string' is not assignable to type 'number'.
probe exit (expect non-zero): 2
$ rm apps/web/src/__typecheck_probe.ts
```

Before the fix that same probe would have passed silently (`tsc --noEmit` never read `src/`). After the fix the app project reports real inputs:

```
$ (cd apps/web && ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit --extendedDiagnostics | grep -E '^Files|^Lines of TypeScript')
Files:                         192
Lines of TypeScript:          5059
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **`docs/STANDARDS.md` § Enforcement still says "TS types | `tsc --noEmit`".** That row is now stale — the script is `tsc -b`. I did **not** edit it because the brief restricts this task to four files; a one-line follow-up (`tsc --noEmit` → `tsc -b` in the Enforcement table) would make the documented rule match the tooling.
- **Historical STATUS WORKS rows are retrospectively affected:** many cite `npm --prefix apps/web run typecheck` as evidence. Until now that step proved nothing on its own; the real gate in those runs was the `tsc -b` inside `build`, which they also ran. No past result is invalidated, but the citations are now genuinely meaningful.
- `tsc -b` is incremental: on a warm cache it can exit 0 quickly, but it still fails on any source error (proven by the probe). Use `tsc -b --force` for a cold full check.
- Not committed, per the brief. Note the repo uses a shared index: if another agent runs `git add -A`, these working-tree changes would be swept into their commit.

## Proposed STATUS.md line (WORKS)
| `npm run typecheck` is now a real type gate: `tsc -b` follows the solution-style `tsconfig.json` references and checks `src` (192 files / 5059 TS lines) instead of zero files; a planted `TS2322` makes it exit 2 | `apps/web/package.json` (`typecheck` script) | `npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → typecheck exit 0 (was `Files: 0`, now 192), build 89 modules, 0 violations; probe error → exit 2 (full output in `docs/tasks/T-000-6/report.md`) | 2026-09-13 15:06 |

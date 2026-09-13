# Report T-002-7

**Agent / model / tool:** implementer · deepseek-flash · DSH agent (direct, no `scripts/agent-run` wrapper available)
**Result:** DONE

## Files changed
- `apps/web/src/features/home/HomePage.tsx`: replaced the `Link` import with `useNavigate`; added `const navigate = useNavigate()`; replaced `<Link to="/create/video"><Button variant="primary">Create video</Button></Link>` with `<Button variant="primary" onClick={() => navigate("/create/video")}>Create video</Button>`. Text, classes and `GuestButton` unchanged.

## Reused
- `apps/web/src/ui/Button.tsx` (`Button` supports `onClick`)
- `apps/web/src/features/session/GuestButton.tsx` (unchanged)

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards && (grep -n "<Link" apps/web/src/features/home/HomePage.tsx || true)

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 33 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:  0.40 kB
dist/assets/index-CNqLyfEZ.css   10.91 kB │ gzip:  3.07 kB
dist/assets/index-DRQ4zAGR.js   270.02 kB │ gzip: 86.05 kB

✓ built in 190ms
check-standards: ok (0 violations)
```
The final `grep -n "<Link"` printed nothing (exit handled by `|| true`), so `HomePage.tsx` no longer contains `<Link`.

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- No guesses. The `<Link to="/create/video">` block matched the brief exactly, and no other file needed changes.
- Did not commit, did not edit other docs, did not install packages, per the brief and AGENTS.md hard rules.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
| --- | --- | --- | --- |
| Home "Create video" no longer nests a button inside a link | `apps/web/src/features/home/HomePage.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` | 2025-09-13 |

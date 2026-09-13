# Brief T-002-7: Fix the button nested inside a link on the home page (small-agent task)

**Role:** implementer (small model is fine) · **Size:** 1 file, ~10 lines
**Kickoff prompt:** `docs/templates/handoff-prompt-small.md`

## Problem
`apps/web/src/features/home/HomePage.tsx` renders a `<Button>` (which is a `<button>`) inside a react-router `<Link>` (which is an `<a>`). A button inside a link is invalid HTML, and screen readers and keyboard users get two focus stops for one action. It's logged in `docs/STATUS.md` under BROKEN.

## Allowed files (exactly this one)
- `apps/web/src/features/home/HomePage.tsx`

## The change
1. Add `useNavigate` to the existing `react-router-dom` import. Remove `Link` from that import if nothing else uses it.
2. Inside `HomePage`, call `const navigate = useNavigate()`.
3. Replace this block:
   ```tsx
   <Link to="/create/video">
     <Button variant="primary">Create video</Button>
   </Link>
   ```
   with:
   ```tsx
   <Button variant="primary" onClick={() => navigate("/create/video")}>
     Create video
   </Button>
   ```
4. Change nothing else: text, classes and `GuestButton` stay as they are.

## Acceptance checks
- [ ] `HomePage.tsx` no longer contains `<Link`
- [ ] Signed-in users still see a "Create video" button that goes to `/create/video`
- [ ] Signed-out users still see `GuestButton`
- [ ] lint, typecheck, build and the standards check pass

## Verify command (run from the repo root; "pass" = every step ends without an error, and the grep prints nothing)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards && (grep -n "<Link" apps/web/src/features/home/HomePage.tsx || true)
```

## Stop and report BLOCKED if
- the file doesn't contain the `<Link to="/create/video">` block shown above (someone already changed it)
- the fix seems to need changes in any other file

## Out of scope
- Any other file, styling, or new components. Don't commit.

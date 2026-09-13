# Report T-005-3

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (subagent)
**Result:** DONE

## Files changed
- `apps/web/src/features/library/libraryCopy.ts` (new): one exported `libraryCopy` object with every user-visible Library string from design.md § Copy, plus the `openLabel(name)` template function. `item.status` is typed `Record<LibraryItem["status"], string>` from `api/library.ts`, so the copy table breaks if the contract enum changes.
- `apps/web/src/features/library/formatCreatedAt.ts` (new): pure `formatCreatedAt(iso)`; UTC `Intl.DateTimeFormat("en-GB", …)`, returns `""` for empty/unparsable input, no `Date.now()`.
- `apps/web/src/features/library/formatCreatedAt.test.ts` (new): 4 top-level `test(...)` calls — both exact strings, `""` and `"not a date"`.
- `docs/tasks/T-005-3/report.md` (new): this report.

## Reused
- `apps/web/src/features/explore/exploreCopy.ts`: the copy-object shape (template helpers declared first, then one exported object grouping `states`/`item`/`result`); `states.*.title/body/action` keys are deliberately identical.
- `apps/web/src/features/create-video/elapsedTime.ts` + `elapsedTime.test.ts`: pure formatter + Node-only vitest style (top-level `test`, no DOM, no config change).
- `apps/web/src/api/library.ts`: `LibraryItem` (generated `LibraryItemResponse`) reused for the status-label type instead of re-declaring the enum.
- Existing eslint limits (`max-lines` 200, `max-lines-per-function` 40, naming-convention) and `scripts/check-standards`; all three new files are well under the limits.

## Verify output (full paste, no summarising)
```

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 5ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 5ms
 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 8ms
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 10ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 7ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 13ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 26ms
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests) 5ms

 Test Files  8 passed (8)
      Tests  57 passed (57)
   Start at  20:20:05
   Duration  320ms (transform 61%, import 22%, tests 10%, worker 6%)


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 89 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-BAq81MA2.css   26.26 kB │ gzip:   5.60 kB
dist/assets/index-JSzd9XX0.js   327.55 kB │ gzip: 102.12 kB

✓ built in 375ms
check-standards: ok (0 violations)
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **`npm run typecheck` is a known no-op in this repo.** `apps/web/tsconfig.json` is `{ "files": [], "references": [...] }`, so `tsc --noEmit` (the `typecheck` script) checks zero files; it exits 0 without compiling. The real type gate is `tsc -b` inside `npm run build`, which ran and passed here. Flagging so nobody treats a green `typecheck` as evidence.
- **`formatCreatedAt` normalises "Sept" → "Sep".** On this machine (Node 24.14.0, ICU 78.2) the bare `Intl.DateTimeFormat("en-GB", { month: "short" })` renders September as `"Sept"`, i.e. `"13 Sept 2026, 19:40"`, not the `"13 Sep 2026, 19:40"` mandated by design.md § `formatCreatedAt` and the brief's acceptance check. CLDR 42+ changed the en-GB abbreviation. The function therefore assembles the result with `formatToParts` and maps the `month` part `"Sept"` → `"Sep"`, which keeps the design-mandated string on both old and new ICU. This is the one place where the design's stated literal and its stated Intl call disagree; the exact test string (acceptance check) wins per AGENTS.md truth hierarchy.
- **`libraryCopy.time.label` added.** design.md § Copy lists the row `` `time.label(iso)` | `formatCreatedAt` output ``, but the brief's enumeration omits it. Since design.md § Copy is normative (design > task packet per AGENTS.md), the object exports `time: { label: formatCreatedAt }` as well. Nothing else was added; every other key matches the brief's list exactly.
- No string was missing from design.md § Copy, so none was invented. Every literal was checked byte-exact against design.md (all present; the files are pure ASCII, so "couldn't" uses a plain ASCII apostrophe).
- `apps/api`, `exploreCopy.ts` and every other feature were left untouched, as the brief requires.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| T-005-3: Library copy table + deterministic UTC `formatCreatedAt` | `apps/web/src/features/library/libraryCopy.ts`, `formatCreatedAt.ts`, `formatCreatedAt.test.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` (57 tests, 8 files) | 2026-09-13T14:50Z |

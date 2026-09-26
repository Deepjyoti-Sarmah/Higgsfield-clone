# Thread T-011-7

Append-only. Write with `scripts/task say`.

### 2026-09-26T02:09:35Z · sonnet-5@claude-code · QUESTION

SequenceDraftClip gained durationMs/trimStartMs/trimEndMs (per brief). StudioPage.tsx's onAddToSequence calls draft.addClip and breaks typecheck since it's not in the allowed-files list. Following the T-011-6 precedent (mechanical consumer fix, out of scope, needed to keep the build green), I'm adding durationMs: item.duration_ms ?? DEFAULT_CLIP_DURATION_MS there. No behaviour change beyond defaulting trim to the full clip. Proceeding; will record in report.md.

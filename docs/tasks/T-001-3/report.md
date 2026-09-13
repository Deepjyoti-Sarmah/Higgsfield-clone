# Report T-001-3

**Agent / model / tool:** scout · deepseek-flash · DeepSeek Harness (DSH), working directly (no sub-delegation)
**Result:** PARTIAL

## Headline finding

**`reference-images/` contains no new material.** All 16 PNGs are **byte-identical (md5) duplicates** of the 16 screenshots already saved in `docs/research/screenshots/` (`01`–`14` Explore + `15` Image create empty + `16` Video create empty). 16 refs → 16 saved, **0 unmatched**.

Therefore:

- Nothing was added to `docs/research/screenshots/`: the canonical files already exist under the right names with identical bytes, so copying them in is a no-op. I did **not** add them as `17`–`32`, because they are not new observations and re-numbering duplicates would corrupt the "NN counts distinct observations" convention and make specs link to two copies of one image.
- **None of the 7 "Not yet observed" flows is covered.** No sign-up/sign-in screen is present in the set, and there is no generating/result, history, assets, pricing, share or signed-out-Explore capture.
- No new flow notes were warranted, so `docs/research/flows/*.md` is unchanged.

I verified identity two ways: (1) md5 of every file in both directories; (2) I opened a sample of the actual images (`04-58-34`, `04-59-52`, `05-01-25`, `05-01-43`, `05-01-02`) and confirmed they are the Explore hero/tool cards, the GPT Image 2 gallery, the Image create empty state, the Video create empty state, and the Explore feature-tags + footer respectively — i.e. the existing filenames are accurate.

## Files changed
- `docs/research/product-map.md`: Status note + an audit note under "Not yet observed" recording that the `reference-images/` set is a duplicate and that all 7 gaps remain open.
- `docs/tasks/T-001-3/report.md` (new): this report.
- `docs/PLAN.md`: T-001-3 row updated.
- `docs/WORKLOG.md`: one line appended.
- `.agent-logs/2026-09-13_09-15_T-001-3_dsh-deepseek-flash.md`: captured prompt + result (this run).
- `docs/research/screenshots/` and `docs/research/flows/` were **not** modified (nothing to add — see above).

## Screenshot mapping (all 16)

| Reference file | md5 | Canonical saved name | Flow / page it shows | Fills a gap? |
|---|---|---|---|---|
| `Screenshot from 2026-09-13 04-58-34.png` | `63166e85` | `01-explore-hero-and-tool-cards.png` | Explore: hero carousel + promo + tool cards | No — already captured |
| `Screenshot from 2026-09-13 04-58-46.png` | `11ddfaf0` | `02-explore-mcp-banner.png` | Explore: MCP banner | No — already captured |
| `Screenshot from 2026-09-13 04-58-54.png` | `cb39b9d3` | `03-explore-visual-effects.png` | Explore: visual-effects gallery (+ hover "Recreate") | No — already captured |
| `Screenshot from 2026-09-13 04-59-13.png` | `33718711` | `04-explore-genjutsu.png` | Explore: Genjutsu before/after section | No — already captured |
| `Screenshot from 2026-09-13 04-59-26.png` | `7e9db88c` | `05-explore-video-model-gallery.png` | Explore: video-model gallery | No — already captured |
| `Screenshot from 2026-09-13 04-59-35.png` | `7a19f662` | `06-explore-community-projects.png` | Explore: community projects grid | No — already captured |
| `Screenshot from 2026-09-13 04-59-43.png` | `72574fee` | `07-explore-supercomputer-banner.png` | Explore: Supercomputer banner | No — already captured |
| `Screenshot from 2026-09-13 04-59-52.png` | `fa215a2c` | `08-explore-image-model-gallery.png` | Explore: "GPT IMAGE 2" image-model gallery | No — already captured |
| `Screenshot from 2026-09-13 05-00-06.png` | `1478047a` | `09-explore-canvas-marketing-studio.png` | Explore: Canvas banner + Marketing Studio gallery | No — already captured |
| `Screenshot from 2026-09-13 05-00-27.png` | `38717760` | `10-explore-seedance-community.png` | Explore: community model gallery (Seedance) | No — already captured |
| `Screenshot from 2026-09-13 05-00-37.png` | `64017bec` | `11-explore-photodump-soul-cinema.png` | Explore: Photodump banner + Soul Cinema gallery | No — already captured |
| `Screenshot from 2026-09-13 05-00-51.png` | `4e781c69` | `12-explore-soul-gallery.png` | Explore: Soul 2.0 gallery | No — already captured |
| `Screenshot from 2026-09-13 05-01-02.png` | `48a8efe9` | `13-explore-feature-tags-footer.png` | Explore: "Explore more AI features" tag cloud + footer | No — already captured |
| `Screenshot from 2026-09-13 05-01-10.png` | `f9bf4096` | `14-explore-footer-links.png` | Explore: footer link columns | No — already captured |
| `Screenshot from 2026-09-13 05-01-25.png` | `64cdbc04` | `15-image-create-empty.png` | Image create: empty state + composer | No — already captured |
| `Screenshot from 2026-09-13 05-01-43.png` | `b0347199` | `16-video-create-empty.png` | Video create: empty / "How it works" onboarding | No — already captured |

## Coverage of the 7 missing flows

| # | Missing flow (from `product-map.md`) | Covered by this material? |
|---|---|---|
| 1 | Sign-up / sign-in + first-run (free credits?) | **No** — no auth screen in the set |
| 2 | Video create in action (preset picker, upload done, generating, result, History list) | **No** — only the empty state (16) |
| 3 | Image create in action (generating, results grid, image detail) | **No** — only the empty state (15) |
| 4 | Effects "Recreate" click-through (where it lands, what's pre-filled) | **No** |
| 5 | Assets page, Pricing page, out-of-credits state | **No** |
| 6 | Share / public view of a generation | **No** |
| 7 | Explore signed out | **No** — every shot is signed in (avatar top right) |

**Covered: 0 of 7. Still missing: all 7.** The `product-map.md` "Not yet observed" list is unchanged in substance; only an audit note was added.

## Reused
- `docs/playbooks/research-flow.md` (save-as `NN-<flow>-<step>.png`, observations only, no renames)
- Existing flow notes `docs/research/flows/{explore,image-create,video-create}.md` — used to confirm what each numbered shot shows
- `docs/templates/report.md`, `scripts/check-standards`

## Verify output (full paste, no summarising)
```
$ ls docs/research/screenshots | wc -l
16
$ ls docs/research/screenshots
01-explore-hero-and-tool-cards.png
02-explore-mcp-banner.png
03-explore-visual-effects.png
04-explore-genjutsu.png
05-explore-video-model-gallery.png
06-explore-community-projects.png
07-explore-supercomputer-banner.png
08-explore-image-model-gallery.png
09-explore-canvas-marketing-studio.png
10-explore-seedance-community.png
11-explore-photodump-soul-cinema.png
12-explore-soul-gallery.png
13-explore-feature-tags-footer.png
14-explore-footer-links.png
15-image-create-empty.png
16-video-create-empty.png
$ scripts/check-standards
check-standards: ok (0 violations)
```

Identity check (extra evidence, exact 1:1 mapping, 0 unmatched):
```
refs: 16 saved: 16 unmatched refs: 0
Screenshot from 2026-09-13 04-58-34.png 63166e85 -> 01-explore-hero-and-tool-cards.png
Screenshot from 2026-09-13 04-58-46.png 11ddfaf0 -> 02-explore-mcp-banner.png
Screenshot from 2026-09-13 04-58-54.png cb39b9d3 -> 03-explore-visual-effects.png
Screenshot from 2026-09-13 04-59-13.png 33718711 -> 04-explore-genjutsu.png
Screenshot from 2026-09-13 04-59-26.png 7e9db88c -> 05-explore-video-model-gallery.png
Screenshot from 2026-09-13 04-59-35.png 7a19f662 -> 06-explore-community-projects.png
Screenshot from 2026-09-13 04-59-43.png 72574fee -> 07-explore-supercomputer-banner.png
Screenshot from 2026-09-13 04-59-52.png fa215a2c -> 08-explore-image-model-gallery.png
Screenshot from 2026-09-13 05-00-06.png 1478047a -> 09-explore-canvas-marketing-studio.png
Screenshot from 2026-09-13 05-00-27.png 38717760 -> 10-explore-seedance-community.png
Screenshot from 2026-09-13 05-00-37.png 64017bec -> 11-explore-photodump-soul-cinema.png
Screenshot from 2026-09-13 05-00-51.png 4e781c69 -> 12-explore-soul-gallery.png
Screenshot from 2026-09-13 05-01-02.png 48a8efe9 -> 13-explore-feature-tags-footer.png
Screenshot from 2026-09-13 05-01-10.png f9bf4096 -> 14-explore-footer-links.png
Screenshot from 2026-09-13 05-01-25.png 64cdbc04 -> 15-image-create-empty.png
Screenshot from 2026-09-13 05-01-43.png b0347199 -> 16-video-create-empty.png
```

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / skipped
- **The task premise does not hold:** T-001-3 was handed "16 screenshots … they are NOT sign-in or sign-up" as if they were uncaptured material. They are the already-catalogued `01`–`16`. This is reported rather than papered over; **no new flow was observed and no flow notes were invented.**
- **Skipped on purpose:** copying the 16 files into `docs/research/screenshots/` (no-op — identical bytes already present) and re-numbering them `17`–`32` (would duplicate existing observations).
- **Displayed names in the reference set are raw timestamped exports** (`Screenshot from …`), not the repo convention; the canonical names in `docs/research/screenshots/` already follow `NN-<flow>-<step>.png`.
- **`reference-images/` is still untracked in git** (~10 MB). I did not add, remove or modify it. Someone should decide whether to commit it, `.gitignore` it, or delete it as a duplicate.
- **Next step to actually close the 7 gaps:** new screenshots of (1) sign-up/sign-in + first run, (2) Video create mid-flow (preset picker, upload done, generating, result, History), (3) Image create results grid + detail, (4) an Effects "Recreate" click-through, (5) Assets + Pricing + out-of-credits, (6) a `/v/{id}`-style public share view, (7) Explore while signed out. These need a signed-out browser session, which this CLI environment does not have.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| T-001-3 audit: the `reference-images/` set (16 PNGs) is byte-identical to screenshots `01`–`16`; 0 of 7 missing flows covered | `docs/tasks/T-001-3/report.md`, `docs/research/product-map.md` § Not yet observed | `ls docs/research/screenshots \| wc -l` → 16; md5 mapping 16/16 matched; `scripts/check-standards` → 0 violations | 2026-09-13 |

---

# T-001-3 (part 2): sign-up screenshot capture — 2026-09-13

**Agent / model / tool:** scout · deepseek-flash · DeepSeek Harness (DSH); images read directly with `read_image` (this model **can** read images)
**Result:** DONE — gap 1 partially covered

## Material
Two new files in `reference-images/` (genuinely new: their sizes differ from every file in `01`–`16`):
- `Screenshot from 2026-09-13 18-28-33.png` (744 797 B)
- `Screenshot from 2026-09-13 18-28-56.png` (666 416 B)

## Filename → page mapping

| Saved as | Source reference file | md5 | What it shows | Sign-in or sign-up? |
|---|---|---|---|---|
| `17-signup-welcome-modal.png` | `Screenshot from 2026-09-13 18-28-33.png` | `f3b5509e` | "Welcome to Higgsfield" auth dialog over a signed-out Explore page; promo carousel on **Nano Banana Pro 4K**; **no** consent line | **Sign-up** |
| `18-signup-terms-consent.png` | `Screenshot from 2026-09-13 18-28-56.png` | `88438ddc` | The **same** dialog; promo carousel on **Higgsfield Soul**; **terms/age consent line visible** (unchecked) | **Sign-up** (same dialog) |

**Neither screenshot is a sign-in screen.** Both show one modal — "Welcome to Higgsfield / Sign up and generate for free"; the only differences are the auto-rotating promo slide and the presence of the consent line. Full copy and states: `docs/research/flows/auth.md`.

## The dialog's fields and CTAs (both shots)
- Heading `Welcome to Higgsfield`; subline `Sign up and generate for free`.
- Primary CTA `Sign up and get an additional discount` (marketing copy rather than "create account").
- `OR`, then `Continue with Google` · `Continue with Apple` · `Continue with Microsoft`.
- `Continue with Email` — **no email, password or code field is visible in either capture**.
- Only in `18`: `I agree to the Terms of Use, acknowledge the Privacy Policy, and confirm I'm at least 18 years old.` — checkbox shown **unchecked**.
- Footer `SSO available on Scale and Enterprise plans`; dismiss `×`.
- Page-wide banner behind the modal: `Get an additional discount on premium plans after signing up` + `Get your discount`.

## First-run / free credits
**No first-run or free-credits state is visible in either screenshot.** The dialog claims "generate for free" but shows no credit amount, balance or grant; the only quantified incentives are discounts (the banner, the primary CTA, and the promo card on the page behind). No post-sign-up screen was captured.

## Gap coverage
- **Gap 1 (sign-up / sign-in) → PARTIAL.** The sign-up dialog is now catalogued (`17`, `18`; `flows/auth.md`).
- Still missing inside gap 1: the **sign-in** form, the email/password (or OTP) step behind `Continue with Email`, a provider redirect/return, and the **first-run / free-credits** state.
- Gaps 2–7: unchanged — still no screenshot.

## Verify output (full paste)
```
$ ls docs/research/screenshots | tail -n 4
15-image-create-empty.png
16-video-create-empty.png
17-signup-welcome-modal.png
18-signup-terms-consent.png
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Files changed (this pass)
- `docs/research/screenshots/17-signup-welcome-modal.png`, `docs/research/screenshots/18-signup-terms-consent.png` — new; md5-identical to their sources; `01`–`16` untouched, originals in `reference-images/` untouched
- `docs/research/flows/auth.md` — new sign-up/sign-in flow notes
- `docs/research/product-map.md` — gap 1 → PARTIAL, an auth row added to Observed surfaces, audit note updated
- `docs/tasks/T-001-3/report.md` — this section
- `docs/WORKLOG.md` — one line appended

## Open issues
- **No sign-in capture.** The nav's `Login` button was never clicked, so whether it opens this same dialog or a different screen is unknown.
- **Consent line is inconsistent** between the two captures (present in `18`, absent in `17`). Cause not confirmed (revealed after interaction, a scroll position, or an A/B variant). Where present it sits *below* every provider button, so a visitor can continue without the terms entering view.
- **`free` is never quantified** in either shot; the discount is stated three times instead.
- **Not committed**, per the kickoff prompt. `.agent-logs/` for this pass is the orchestrator's to add — that path was outside my allowed files. (Note: my tool cannot be wrapped by `scripts/agent-run`, so AGENTS.md's "export the transcript" rule applies.)

# Design System: Reel & Still

The single design source for every agent and harness (spec 010, AC-2). Tokens here map one-to-one onto the `@theme` block in `apps/web/src/styles.css`. If this file and the code disagree, fix the code, or report the disagreement in your task thread.

Written with the `stitch-design-taste` skill. UI packets follow the `design-taste-frontend` skill for implementation rules. Where that skill and this file disagree, **this file wins**.

## 1. Visual Theme & Atmosphere
A quiet editing room in daylight. Warm paper surfaces, ink-dark type, and one vermilion accent used the way a film leader or a record light is used: sparingly, to mean "this one" or "go". Density is medium: it's a tool, not a landing page, so panels sit edge to edge with hairline dividers instead of floating cards. Variance is moderate: the studio is a strict grid, and only the start page is allowed an asymmetric composition. Motion is short and functional; things move only when their state changes.

The work (stills, clips, sequences) is the only colourful thing on screen. The chrome stays neutral so the media carries the colour.

## 2. Color Palette & Roles
Token names are the `@theme` names (`--color-<name>` → `bg-<name>`, `text-<name>`, `border-<name>`).

| Token | Light | Dark | Role |
|---|---|---|---|
| `bg` | `#F6F3EE` warm paper | `#141210` | page background |
| `surface` | `#FFFDF9` | `#1C1A17` | composer, popovers, rail background |
| `sunken` | `#EDE8E0` | `#0F0E0C` | the stage behind media, input wells, empty slots |
| `border` | `#DDD6CB` | `#2E2A25` | 1px hairlines and dividers |
| `text` | `#1C1917` ink | `#EEE8DF` | primary text |
| `muted` | `#6B635A` | `#A39A8E` | secondary text, metadata |
| `faint` | `#9A9187` | `#6F675D` | placeholders, disabled, the queued dot |
| `accent` | `#B4442A` vermilion | `#E0765A` | primary action, active tab, selection ring, running dot |
| `accent-ink` | `#FFF8F2` | `#1A0F0A` | text on an accent fill |
| `success` | `#3F7D58` | `#6FAE85` | the succeeded dot, "credits refunded" confirmations |
| `danger` | `#8C2F39` wine | `#D46A74` | failures, validation errors (never the accent) |
| `scrim` | `rgb(28 25 23 / 0.55)` | `rgb(0 0 0 / 0.6)` | drawer and modal backdrop |

- **Dark theme:** the same token names are redefined under `@media (prefers-color-scheme: dark)` inside `@layer base` (`:root { --color-bg: … }`). Components never branch on the theme. Set `color-scheme: light dark` on `:root` and an inline `<meta name="theme-color">` for each scheme in `index.html`, so there's no flash of the light theme.
- **Contrast:** `text` on `bg` and `muted` on `surface` must pass WCAG AA in both themes. `accent-ink` on `accent` must pass AA for 14px/600.
- **Banned:** pure `#000`, neon or lime (`#ccff00` and family), purple or violet gradients, gradient text, glow shadows, and any second accent colour.

## 3. Typography Rules
| Role | Family | Use |
|---|---|---|
| Display | **Instrument Serif** (400, italic allowed) | Only on "display moments": the start page headline, empty-state headlines, the share viewer title. **Never** in controls, the rail, tabs or the composer. |
| UI | **Geist** (400/500/600) | Everything else. Sentence case. |
| Mono | **JetBrains Mono** (400/500) | Numbers and machine values: credits, durations (`0:14`), counts (`3 shots`), job ids, timestamps, costs on buttons. |

- Load them from Google Fonts in `index.html` with `display=swap`. Font tokens: `--font-display`, `--font-body`, `--font-mono`.
- **Scale:**
  - display `clamp(2.5rem, 5vw, 4rem)` / 1.05, tracking `-0.01em`;
  - h2 `1.25rem` / 600;
  - body `0.9375rem` / 1.55;
  - meta `0.8125rem`;
  - mono meta `0.8125rem`.
- Body copy has a 65ch max width. Body text never goes below 14px.
- **Banned:** Inter, the Anton / Arial Narrow display stack (the old Higgsfield look), system serif stacks, all-caps headings. Uppercase is allowed only on mono micro-labels ≤ 11px with `tracking-wide`.

## 4. Component Stylings
- **Buttons** (`ui/buttonStyles.ts` is the single variant map):
  - Primary: `accent` fill, `accent-ink` text, radius 10px, height 40px (44px on touch).
  - Secondary: `surface` fill with a 1px `border`.
  - Ghost: text only, `muted` → `text` on hover.
  - Pressed: `scale(0.98)`. No glow.
  - A button that spends credits shows the cost in mono: `Render · 1 credit`.
  - Disabled buttons keep their label and show the reason as text next to them. There are no tooltips in place of that reason.
- **Tabs (composer):** underline tabs, `muted` → `text`, with the active tab on a 2px `accent` underline. The labels are `Still`, `Clip`, `Sequence`, `Face swap`. Each tab says what it does and where its result goes; the active tool shows a one-line purpose, and a persistent "how it works" strip links Still → Clip → Sequence → Face swap.
- **Rail item:**
  - A 56×56 thumbnail (radius 8px), the title (prompt or preset name, one line, ellipsis), a mono meta line (`clip · 0:05 · 14:02`), and a status dot on the right.
  - Selected: `sunken` background with a 2px `accent` bar on the left edge.
  - Hover: `sunken` background at 60%.
- **Status dot:** 8px. Queued is `faint`. Running is `accent` with a slow opacity pulse (motion-safe only). Succeeded is `success`. Failed is `danger`.
- **Stage:**
  - The media sits centred on a `sunken` field, with `object-contain` and radius 12px.
  - Below it is one caption line: the title, then the mono meta (`3 shots · 0:14 · ffmpeg`).
  - The actions row is right-aligned.
  - A placeholder or fallback result is captioned in `muted` text, for example "Placeholder image: the model was unavailable".
- **Composer:** the `surface` panel pinned under the stage, with a 1px top `border` and 16–20px padding. Fields sit in one row on desktop and stack below 768px. The primary action sits bottom-right.
- **Sequence strip:**
  - Slots are 120×68 (16:9) or 68×120 (9:16) frames with radius 8px. Empty slots are dashed `border` on `sunken`.
  - Between slots sits a **transition chip**: a 24px pill with a mono glyph and label (`CUT` / `XFADE` / `FADE`) that cycles on click, with `aria-label="Transition: Crossfade"`.
  - The music well goes at the end of the strip, and the total length and cost go on the right.
- **Popover (credits):** a `surface` panel with a 1px `border`, radius 12px and a soft shadow `0 12px 32px -12px rgb(28 25 23 / 0.18)`. It shows the balance in mono at 1.5rem, then "Add demo credits", then the ledger list: mono amounts, `+` in `success` and `−` in `text`.
- **Inputs:** the label goes above the field. The field has a `sunken` fill, a 1px `border`, and a 2px `accent` focus ring with offset. Errors show below in `danger`.
- **Loaders:** skeleton blocks matching the final layout, with a subtle shimmer (motion-safe). No circular spinners.
- **Empty states:** one serif line plus one plain sentence plus one action. Never "No data found".

## 5. Start Page (the only "hero")
- An asymmetric split on desktop:
  - **left (5/12):** the display headline, one plain sentence, and one primary button, "Open the studio";
  - **right (7/12):** the four tools **Still → Clip → Sequence → Face swap**, stacked vertically, each with real media from our storage (distinct preset preview clips and posters) and a one-line caption. The Still and Clip demos must not show the same subject.
- Below that is one row of motion-preset chips that deep-link into the Clip tab.
- **Not allowed:** a centred hero, three equal cards, a second CTA, stats, testimonials, "scroll" hints, and the phrase "AI-powered".
- Below 768px everything stacks in a single column, and the media goes below the text.

## 6. Layout Principles
- **Studio (`/studio`):** a CSS grid under a 56px top bar.
  - Desktop (≥ 1024px): columns `288px 1fr`. The rail is on the left, full height, and scrolls on its own. The right column is rows `1fr auto`: the stage above, the composer below.
  - 768–1023px: the rail becomes a slide-in drawer opened from a "Library" button in the top bar.
  - < 768px: stage, then composer, in a single column. Everything is full width, with **no horizontal page scroll** (the sequence strip scrolls inside itself).
- **Start and share pages:** `max-width: 1200px`, padding `1rem / 2rem / 3rem` at mobile / tablet / desktop, and `min-height: 100dvh`.
- Use grid for structure. No `calc(33% - …)` maths.
- **Spacing scale:** Tailwind's default 4px steps. Panels use 16/20/24; sections on the start page use `clamp(3rem, 8vw, 6rem)`.

## 7. Responsive Rules
- Check at 375, 390, 768, 1024 and 1440px.
- Touch targets are at least 44px. The rail's drawer button is always labelled. There's no bare hamburger icon.
- Media scales proportionally. The stage never crops media.

## 8. Motion & Interaction
- Animate only `transform` and `opacity`. Durations are 160ms for hover and press, and 220ms for panel, drawer and popover transitions, with `cubic-bezier(0.2, 0.8, 0.2, 1)`.
- **Perpetual motion:** only the running status dot pulses and skeletons shimmer, both behind `motion-safe:`.
- **Preset motion previews:** the existing preset motion keyframes may stay, renamed to neutral token names (`--animate-motion-zoom-in` and so on), behind `motion-safe:`.
- **Reduced motion:** scroll-into-view uses `behavior: "auto"` and pulses stop.
- No new animation library. CSS is enough for this product.

## 9. Voice & Copy
- Film-editing words: still, clip, shot, cut, sequence, render. Sentence case, short, and concrete.
- Numbers go in mono.
- Say what happened and what to do next: "Render failed. Your credit was refunded." Never say "Oops" or "Something went wrong!".
- Use the `no-ai-slop` skill (Detect mode) on every `*Copy.ts` file. UI copy uses no em dashes.

## 10. Anti-Patterns (Banned)
- Anything that reads as Higgsfield: black and lime, Anton, the old logo, "Higgsfield" text.
- Emojis anywhere, in the UI, alt text or code.
- Glows, gradient text, pure black, a second accent colour.
- Centred marketing heroes, three equal feature cards, fake stats, testimonials, "AI-powered", "Unleash", "Seamless".
- Serif type in controls or dense UI.
- Circular spinners, custom cursors, overlapping text on media.
- Hard-coded hex values in components. Every colour is a token.

# Flow: Sign-up / sign-in (auth modal)

**Source:** screenshots `17`–`18` in `docs/research/screenshots/`, captured 2026-09-13 while **signed out**.
**Observation only.** Solutions belong in specs.

## Entry point
- The auth dialog opens over the Explore page (both shots show Explore dimmed behind it), so the visitor is on the landing page when it appears.
- Likely triggers: the `Sign up` button in the top nav, the "Sign up and get your discount" promo card on Explore, or a gated action. **Which trigger each shot came from is not confirmed.**
- **Only sign-up was observed.** The nav also has a `Login` button, but neither screenshot shows a sign-in form: both captures are the same "Welcome to Higgsfield" sign-up dialog. A dedicated sign-in screen may or may not exist.

## Page-wide banner (visible behind the modal, 17–18)
- Across the very top: "Get an additional discount on premium plans after signing up", an accent button `Get your discount`, and a dismiss `×`. It is present before any auth interaction.

## The dialog (17, 18)
Two panels side by side; the modal can be closed with the `×` at its top right.

### Left: promotional carousel
- A full-height image with two benefit chips, a model name, and a one-line pitch; four tabs underneath act as a carousel.
- Tabs, in order: `Seedance 2.0 4K` · `Nano Banana Pro` · `Higgsfield Soul` · `Cinematic App`.
- Shot `17` (carousel on *Nano Banana Pro*): chips `4K Resolution`; title `NANO BANANA PRO 4K`; "The best image model, for the best price in the industry, only on Higgsfield".
- Shot `18` (carousel on *Higgsfield Soul*): chips `2K Quality` + `Prompt Enhancer`; title `HIGGSFIELD SOUL`; "Create consistent characters across images and videos for storytelling".
- The carousel appears to auto-rotate, which is why two captures 23 s apart show different slides.

### Right: the sign-up card
| Element | Exact copy | Notes |
|---|---|---|
| Heading | `Welcome to Higgsfield` | with the logo mark above |
| Subline | `Sign up and generate for free` | the only "free" claim; no credit amount |
| Primary CTA | `Sign up and get an additional discount` | accent (acid-green), gift icon; the most prominent control |
| Divider | `OR` | between the primary CTA and the provider buttons |
| Provider buttons | `Continue with Google` · `Continue with Apple` · `Continue with Microsoft` | equal weight, brand icons |
| Secondary CTA | `Continue with Email` | same weight as the provider buttons, below `OR` |
| Consent line | `I agree to the Terms of Use, acknowledge the Privacy Policy, and confirm I'm at least 18 years old.` | **only in `18`**, with an unchecked checkbox; `Terms of Use` / `Privacy Policy` are links |
| Footer | `SSO available on Scale and Enterprise plans` | small print, centred |

## Inputs and controls observed
- **No text input is visible** in either capture: the dialog is provider/CTA choice only. The actual email (and password/code) fields, if any, come after `Continue with Email` and were **not captured**.
- One checkbox (the age/terms consent) — visible and **unchecked** in `18`; absent from `17`.
- Close `×`; the consent checkbox is the only stateful control.

## UI states observed
- **Observed:** sign-up dialog in its default state (`17`) and the same dialog with the consent line present (`18`).
- **Not observed:** a sign-in variant; email entry or password/OTP step; provider redirect/handoff; loading or disabled states; validation or error states; the post-sign-up **first-run** screen; the free-credit grant; the state after closing the dialog.

## Credits / cost
- No credit balance, grant amount or price is shown anywhere in the dialog. The only incentives are discounts: the page banner, the primary CTA, and the background promo card.
- **"generate for free" is claimed but never quantified**, and no first-run/free-credits state was captured.

## Friction noticed (possible "better than original" angles)
- **Promotion-first auth:** a discount banner, a discount primary CTA and a discount promo card behind the modal — the offer competes with the act of signing up.
- **Consent placement and inconsistency:** the terms/age checkbox is present in one capture and absent in the other; where present it sits *below* every provider button, so a visitor can click `Continue with Google` without the consent line ever entering view. Cause of the difference is not confirmed (revealed on interaction, or a variant).
- **The dialog doubles as an ad:** the left half is an auto-rotating model carousel, so the same dialog sends different messages each time it is seen.
- **Two nav entry points, one dialog?** `Login` and `Sign up` are separate buttons; whether they open the same dialog is unconfirmed.
- **"Free" is unquantified:** nothing tells the visitor what they get, unlike the discount, which is stated three times.

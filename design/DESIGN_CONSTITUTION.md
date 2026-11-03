# NoteVault — Design Constitution

> Written 2026-11-03 as a Rulebook Gate A document, from the UI as it
> actually exists in `notes_agent/web.py` (single-page HTML, inline CSS,
> no external assets, no CDN, no custom fonts). Nothing in this file
> claims a design that is not in the code. Where the current UI falls
> short of the Rulebook, that is stated as a gap, not papered over.

## Product personality and emotional tone

Calm, verifiable, slightly bureaucratic in a good way: a ledger, not
a chat toy. The product's promise is "routing you can see, budget you
can see, and no guessing when your notes do not have the answer."
Tone in copy: plain, factual, no hype. The mock badge is deliberately
loud (amber) so a mock answer can never be mistaken for a live one.

## Target user, environment, context of use

A solo developer / student with a local folder of Markdown notes,
working on a laptop browser. The judge/demo viewer is the primary
audience for the web UI: they must be able to see, in one screen,
the notes, the answer, the routing decision, and the budget. The CLI
is the secondary surface (same agent, same rules).

## Visual metaphor / central design idea

**A routing ledger.** Three columns read left to right as:
source (your notes) → question (ask) → audit (routing + budget).
Every answer is accompanied by its audit trail in the same viewport,
so the Otari value is the *evidence*, not a claim in a headline.

## Colour palette (semantic roles, from `web.py` — exact values)

| Role | Value | Used for |
|---|---|---|
| Page background | `#fafaf7` (warm off-white) | Page |
| Text | `#1a1a1a` | Body text |
| Muted text / small print | `#555` | Tags, footnotes |
| Card | `#fff`, border `#ddd`, radius `12px` | All three columns |
| Primary button | `#222` bg, `#fff` text, border `#333`, radius `8px` | Ask, presets, Show plan, Reset budget |
| Input border | `#bbb`, radius `8px` | Question, model select, custom model |
| Mock badge | bg `#ffe8c2`, text `#7a3e00` | `[mock]` / `[mock] offline stand-in` |
| Real badge | bg `#d2f4d2`, text `#145214` | `real Otari` (not yet seen live — code path only) |
| Budget meter track / fill | `#eee` / `#d98200` (amber) | Local session budget |
| Citation chip | bg `#eef` | Source note titles |
| Refusal / error | border `#b00020`, bg `#fff0f0` | Grounded refusal, API errors |
| Answer code block | bg `#f4f4f4` | Answer text, organise plan |

No gradients, no glassmorphism, no glow, no floating blobs. That
restraint is intentional and matches the ledger metaphor.

## Typography and type hierarchy

- **Typeface:** `system-ui, sans-serif` throughout. No web font is
  loaded (stdlib-only, no external assets). This is a gap against
  the Rulebook's "strong typography" expectation: the hierarchy
  comes from size/weight only, not from a chosen type system.
- **Hierarchy:** `h1` NoteVault at `1.6em` → card `h3` headings →
  body text → `small` footnotes (`#555`). Answer and plan text is
  rendered in `<pre>` with wrapping (`pre-wrap`, `word-wrap`).
- **No type scale document exists** beyond the values above; a
  future pass should define one before claiming premium typography.

## Layout grid, spacing, composition

- Page: `max-width: 1100px`, centred, `24px` top margin, `16px`
  side padding.
- Grid: `1fr / 1.6fr / 1fr`, `16px` gap, three cards in one row on
  desktop. The middle (Ask) column is widest because asking is the
  primary action; the right (Routing + Budget) column is the audit.
- No hero section, no sidebar, no navigation bar: the page is a
  single route (`/`), and that is the whole product surface.

## Navigation and information architecture

- One route: `/`. No nav, no tabs, no menus, no auth, no settings
  page. Information architecture is the three columns plus the mode
  bar (`[mock]` badge + gateway/model/fallback line) above them.
- API routes (not navigation): `GET /`, `GET /api/status`,
  `GET /api/note?path=`, `POST /api/ask`, `POST /api/organise`,
  `POST /api/reset-budget`. See `qa/INTERACTION_INVENTORY.md`.

## Component behaviour and interaction patterns

- **Notes list:** click a note item → preview pane shows title +
  body. Hover only (`background: #eef`); see accessibility gap in
  the inventory (note items are `div`s, not keyboard-focusable).
- **Ask:** type a question, optionally pick a model or type a custom
  `provider:model` string, click Ask. Empty question → browser
  `alert('Type a question first.')` (no inline validation UI).
  While asking, answer area shows `Asking…`. On success: answer
  `<pre>`, citation chips, mode badge, routing panel, budget meter
  all update. On failure: refusal-styled error box with the API
  error message.
- **Presets:** `Try: Abhiverse` fills the question and asks;
  `Try: refusal` asks `quantum bananas` and demonstrates grounded
  refusal (no LLM call, no budget spent).
- **Organise:** `Show plan` renders a tag-grouped plan in `<pre>`.
  Plan only — no files are changed, and the UI says so.
- **Budget:** meter width = `% used`, text `used / limit calls
  used · remaining`. `Reset demo budget` zeroes the session budget
  and reloads status. Budget exhaustion is a server-side
  `RuntimeError` surfaced as a 400 error box (see inventory).
- **Loading states:** `Loading…` for notes on first load, `Asking…`
  for answers. No skeleton screens. If `/api/status` fails on load,
  the page stays on `Loading…` with no error UI — a recorded gap
  (see inventory, item W-01).
- **Motion:** none. There are no CSS transitions or animations in
  the current stylesheet. That trivially satisfies reduced-motion
  (nothing to disable) but fails the Rulebook's expectation of a
  deliberate motion language. Do not claim a motion system exists.

## 3D concept — PLANNED ONLY, NOT IMPLEMENTED

**Status: PLANNED. No 3D exists in this product today. Do not claim
otherwise in any submission, video, or screenshot caption.**

Planned concept — **the routing map**: a spatial diagram of a
single answer's journey, rendered as a depth-based scene:

- **Gateway node** (Otari, `https://api.otari.ai`) at the centre-back.
- **Provider nodes** fanned out in front of it (e.g. the chosen
  provider/model, the fallback model), sized by whether they were
  attempted, chosen, or failed.
- **Edges** labelled with the routing reason and the attempted order
  (`attempted` list from the routing panel), with the fallback edge
  highlighted only when a fallback was actually used.
- **Budget** shown as a depleting depth/height element beside the
  map, so "calls remaining" is spatial, not just a number.

Why it is meaningful (not decoration): the product's whole value is
routing visibility, and a flat text panel is the weakest way to show
a chain of attempts, a fallback, and a refusal (no call at all).
A spatial map makes "attempted → failed → fallback used" and
"refused before routing (no nodes lit)" instantly readable.

- **Controls (planned):** rotate/zoom the map, click a provider node
  to show its reason/attempt status, keyboard alternative = the
  existing routing panel text (which must remain the source of
  truth and must stay fully usable without the 3D view).
- **Fallback:** if WebGL is unavailable, on a low-power device, or
  under `prefers-reduced-motion`, show the current flat routing
  panel only — no broken canvas, no spinning decoration.
- **Technology (to evaluate, not yet chosen):** CSS 3D transforms
  first (no new dependency, matches the stdlib-only build); a
  Three.js scene only if the map needs true 3D manipulation. Do not
  add a heavy dependency just to claim 3D.
- **Testing required before claiming Gate C:** laptop + mobile
  viewport, lazy load (must not block Ask), keyboard alternative,
  reduced-motion path, and a static fallback screenshot.

## Responsive behaviour

- Viewport meta is present (`width=device-width, initial-scale=1`).
- One breakpoint: below `800px` the 3-column grid collapses to a
  single column (`grid-template-columns: 1fr`). Cards stack in
  order: notes → ask → routing/budget.
- **Not verified in this task:** no tablet/mobile device testing
  was run, no horizontal-overflow audit was run, and no Lighthouse
  audit was run. Responsive behaviour is therefore recorded as
  UNVERIFIED in the gate card, not PASS. The CSS is simple enough
  that overflow is unlikely (inputs use `box-sizing: border-box`,
  `<pre>` wraps), but "unlikely" is not evidence.

## Accessibility and reduced-motion behaviour

- **Present:** native focusable controls (input, select, buttons),
  labels wrapping their inputs (question, model, custom model),
  semantic `h1`/`h3`, `lang="en"`, viewport meta.
- **Gaps (recorded, not hidden):**
  - No `:focus-visible` style — keyboard focus is browser-default
    only, and is not visibly designed.
  - Note items are clickable `div`s with no `tabindex`, `role`,
    or keyboard handler — a keyboard-only user cannot open a note
    preview (see inventory, item W-02).
  - No `prefers-reduced-motion` rule — harmless today (no motion),
    required if any motion is added later.
  - No skip link, no `aria-live` for the answer/routing updates
    (screen-reader users get no announcement when an answer lands).
  - Colour-only distinction is partially mitigated: the mock/real
    badges carry text (`[mock]` / `real Otari`), not colour alone.
- **Reduced motion:** nothing animates, so nothing needs disabling.
  This is compliance by absence, not by design, and must be
  revisited when the 3D map or any motion is added.

## Design research — BLOCKED (honest statement)

**No five-reference design research was conducted for this project
in this task, and none is claimed.** The Rulebook requires, per
project: two same-category references, one interaction/motion
reference, one typography/composition reference, and one 3D/spatial
reference, each with URL, date inspected, what was inspected, what
to learn, what not to copy, and how it translates. That research
file does not exist for NoteVault, and this constitution must not
be read as a substitute for it. Gate A is therefore FAIL on the
research item until that research is actually done and recorded.
No reference URL is invented here.

## Distinctiveness vs recent projects (registry comparison)

No formal `design/PROJECT_DESIGN_REGISTRY.md` existed before this
file. Against the three most recent projects known from the
workspace (CageCheck: single-column paper/ink/stamp, serif + mono;
ChatBoss: dark gradient game overlay; Spec Ghost: dark haunted
house, candlelight amber), NoteVault's light warm-paper three-column
ledger is recognisably different in palette and layout. It is NOT
distinct in typography (default `system-ui`) or motion (none), and
its card-grid dashboard pattern is a common pattern. Gate
UI_DISTINCTIVENESS is therefore recorded as PARTIAL in the gate
card: distinct layout/palette, generic type/motion. A registry file
comparing all projects, with screenshots, is still outstanding.

## What must change before a COMPLETE claim

1. Five-reference design research, recorded with real URLs/dates.
2. 3D routing map implemented (or an approved exception, in
   writing, explaining why no meaningful 3D can be designed).
3. Keyboard-accessible note items + visible focus style.
4. Error UI for initial `/api/status` failure (no silent
   `Loading…`).
5. Responsive + accessibility checks actually run and recorded
   (desktop/tablet/mobile, Lighthouse or equivalent).
6. `design/PROJECT_DESIGN_REGISTRY.md` with screenshot references.

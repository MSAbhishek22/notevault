# NoteVault — Interaction Inventory

> Source of truth: `notes_agent/web.py` (single page, inline JS) and
> `notes_agent/agent.py` / `routing.py` (server logic). Test evidence
> is the pytest suite: 24 tests, re-run 2026-11-03 in a fresh venv
> (`python3 -m venv`, `pip install pytest`, `python3 -m pytest
> tests -q` → **24 passed**). Test names are cited per row where a
> test exists. "No automated test" means exactly that — the behaviour
> was read from code, not exercised by a test, and the status reflects it.
>
> Mode reminder for every row: **the live product today is MOCK.**
> The UI badge reads `[mock]` / `[mock] offline stand-in` and every
> mock answer is prefixed `[mock]`. No row below claims a live Otari
> call. The `real Otari` badge is a code path (`mode != 'mock'`) that
> has never run against a real token for this project.

## Web page controls (`GET /` — the only page)

| # | Control | Action | Expected behaviour | Actual implementation | Validation / error handling | Test evidence | Status |
|---|---|---|---|---|---|---|---|
| W-01 | Notes list area (initial) | Page load | Notes load from `/api/status`, list renders | `load()` fetches `/api/status`, renders `s.notes` into `#notes` | **None on failure:** if the fetch throws, `load()` aborts and `#notes` stays on `Loading…` with no error UI | None (no test covers a failed `/api/status` load) | FAIL |
| W-02 | Note item (clickable row, `📄 title (N words, #tags)`) | Click a note | Preview pane shows that note's title + body | `showNote(path)` → `GET /api/note?path=` → `#preview` = title + body | 404 from server → `api()` throws → uncaught in `showNote`, preview unchanged, no error shown | None for the JS click path; server `get_note` path guards tested (`test_resolve_inside_rejects_traversal`) | FAIL (keyboard) — see note below |
| W-03 | Note preview pane (`<pre id="preview">`) | Display only | Shows "Click a note." then the selected note | Plain `<pre>`, text set by `showNote` | Body truncated to 8000 chars server-side (`/api/note`) | None (display only) | PASS (display) |
| W-04 | Question input (`#q`, placeholder "What is Abhiverse for?") | Type a question | Text is sent as `question` on Ask | Read trimmed in `ask()`; sent to `POST /api/ask` | Empty → browser `alert('Type a question first.')`, no request sent; no inline validation UI | Agent-level: empty question rejected server-side (400, see A-01) | BLOCKED (browser alert path untested; server path tested) |
| W-05 | Model select (`#model`) | Pick a model | Route uses the selected `provider:model`, or default if blank | Value sent as `model` unless a custom model is typed; blank → `null` → default from config | Invalid `provider:model` string → server 400, shown as error box (see A-01) | `test_parse_model_valid_and_invalid`, `test_choose_route_default_and_user_selected_reasons`, `test_user_selected_model_is_recorded_in_routing` | PASS |
| W-06 | Custom model input (`#customModel`, placeholder "provider:model") | Type a custom model string | Overrides the select when non-empty | `customModel.trim() \|\| model.value \|\| null` in `ask()` | Same 400 path as W-05 for a bad string | Same routing tests as W-05 (agent-level) | PASS (agent-level; JS precedence untested in browser) |
| W-07 | Ask button | Click | Sends the question, shows answer + citations + routing + budget | `ask()` → `POST /api/ask` → renders answer `<pre>`, citation chips, mode badge, routing panel, budget meter | While asking: `Asking…`. On API error: refusal-styled error box with `e.message` (HTML-escaped for `<`) | `test_web_status_and_ask_endpoints` (status + ask, mock, chosen provider `openai`, budget used = 1) | PASS |
| W-08 | "Try: Abhiverse" button | Click | Fills "What is Abhiverse for?" and asks it | `askPreset()` sets `#q` then calls `ask()` | Same as W-07 | Same as W-07 (question is the seeded sample note subject) | PASS |
| W-09 | "Try: refusal" button | Click | Asks `quantum bananas`, shows grounded refusal, budget unchanged | Same path as W-07; server refuses before routing (see A-01) | Refusal banner "Refused — no guess."; routing panel "No LLM call made." | `test_ask_no_match_does_not_guess_and_does_not_call_llm`, `test_ask_detailed_refusal_spends_no_budget_and_attempts_no_route` | PASS |
| W-10 | Answer area (`#answer`) | Display only | Answer text, citation chips, mode badge | Rendered by `ask()`; answer HTML-escapes `<` only (see note) | Refused answers get the refusal banner above the answer block | `test_ask_with_match_cites_source`, `test_ask_detailed_shows_routing_budget_citations_and_mock_label` | PASS (display; escaping is `<`-only, not full HTML-escaping — recorded, not a claimed XSS audit) |
| W-11 | Citation chips (`📄 title`) | Display only | One chip per source note used | Rendered from `r.sources` in `ask()` | No sources → no chips (refusal case) | `test_ask_with_match_cites_source` | PASS |
| W-12 | Mode badge (`#modebadge`, top) + mode line | Display only | Shows `[mock]` (amber) or `real Otari` (green) + gateway/default model/fallback | Set by `load()` from `/api/status`; answer badge re-set per answer | Never shows a token; `test_status_dict_never_contains_token` covers the status payload | `test_web_status_and_ask_endpoints` (mode `mock`), `test_status_dict_never_contains_token` | PASS |
| W-13 | Routing panel (`#routing`) | Display only | Gateway, mode, chosen provider/model + why, fallback chain, attempted routes, fallback-used warning, or "No LLM call made" | `renderRouting()` from `r.routing` | Refusal → "No LLM call made" text, no fake route | `test_ask_detailed_shows_routing_budget_citations_and_mock_label`, `test_ask_detailed_refusal_spends_no_budget_and_attempts_no_route`, fallback tests | PASS |
| W-14 | Budget meter (`#budget`) | Display only | Meter width = % used; text `used / limit calls used · remaining` (+ "Budget exhausted" when exhausted) | `renderBudget()` from status/answer payloads; limit default 5 per run | Exhaustion → server `RuntimeError` → 400 error box on next ask (see A-01) | `test_budget_tracker_remaining_and_exhaustion`, `test_llm_budget_is_enforced`, `test_web_status_and_ask_endpoints` (budget used = 1) | PASS |
| W-15 | "Show plan" button (Organise plan) | Click | Shows a tag-grouped plan in `<pre id="plan">` | `organise()` → `POST /api/organise` → plan text | Plan is text only; UI caption states "plan only — no files are changed" | Agent-level: `test_organise_plan_never_moves_files`; **no HTTP test for `/api/organise`** | BLOCKED (endpoint untested over HTTP; agent logic tested) |
| W-16 | "Reset demo budget" button | Click | Budget returns to 0 used, meter reloads | `resetBudget()` → `POST /api/reset-budget` → `load()` | None (reset has no failure path in UI; server errors would throw uncaught) | Agent-level budget tracker tests only; **no HTTP test for `/api/reset-budget`** | BLOCKED (endpoint untested over HTTP) |
| W-17 | Gateway-side budget footnote (small print) | Display only | States gateway budget lives in otari.ai dashboard, meter is local-session only | Static text in the right column | n/a — this text is what prevents a false gateway-budget claim | n/a (copy, verified by reading `web.py`) | PASS |

### Keyboard / accessibility notes on the web controls

- **W-02 is a FAIL for keyboard operation, not for mouse operation:**
  note items are `<div class="note-item" onclick="…">` with no
  `tabindex`, no `role="button"`, and no keyboard handler. A
  keyboard-only user cannot open a note preview. Mouse click works.
  Fix (not yet applied): render note items as `<button>` elements
  or add `tabindex="0"`, `role="button"`, and an Enter/Space handler.
- **Focus visibility:** no `:focus-visible` style exists in the
  stylesheet. Native inputs/selects/buttons are focusable, but
  focus is browser-default only.
- **Note-item path edge case:** `showNote` strips `'` characters
  from the path before lookup, so a note filename containing a
  single quote would 404 and leave the preview unchanged with no
  error. Sample notes contain no quotes, so this is untriggered,
  not untrue. Recorded as a minor FAIL, not a dead button.
- **No dead buttons found:** every visible button in the current
  UI calls a real API route and produces a real result or a real
  error. No `href="#"`, no empty handler, no TODO handler, no fake
  success toast exists in `web.py`.

## API routes (`notes_agent/web.py`, stdlib `ThreadingHTTPServer`)

| # | Route | Action | Expected | Actual / validation / errors | Test evidence | Status |
|---|---|---|---|---|---|---|
| A-01 | `POST /api/ask` `{question, model?}` | Ask | Returns `AskResult.to_dict()`: answer, sources, refused, routing, budget, mode | Empty question → 400 `question is required`. Bad model string → 400 (ValueError). Budget/provider failure → 400 (RuntimeError). Body > 64 KB → 400 `Request too large`. Bad JSON → 400. Unknown fields ignored. | `test_web_status_and_ask_endpoints`, routing/budget/fallback/refusal tests (agent-level, same code path) | PASS |
| A-02 | `GET /api/status` | Status (no LLM call) | mode, gateway, model, fallback, notes list, budget | Returns `agent.status_dict()`; never contains a token (explicit test) | `test_web_status_and_ask_endpoints` (mode `mock`, notes_count 1 in test seed), `test_status_dict_never_contains_token` | PASS |
| A-03 | `GET /api/note?path=` | Fetch one note | Title, rel_path, tags, body (≤ 8000 chars) | Missing/escaping path → 404 (`FileNotFoundError`/`ValueError` from `get_note`); path guards refuse `..`, absolute paths, escaping symlinks | Path-guard tests only (`test_resolve_inside_rejects_traversal`); **no HTTP test for `/api/note`** | BLOCKED |
| A-04 | `POST /api/organise` `{}` | Organise plan | Tag-grouped plan string, no files changed | Returns `agent.organise_plan()` | Agent-level only (`test_organise_plan_never_moves_files`); **no HTTP test** | BLOCKED |
| A-05 | `POST /api/reset-budget` `{}` | Reset session budget | Budget back to 0, returns budget dict | `agent.reset_budget()` sets `budget.used = 0` | Budget tracker tests only; **no HTTP test** | BLOCKED |
| A-06 | Any other path / method | 404 | JSON `{"error": "Not found"}` | `do_GET`/`do_POST` fall through to 404; non-POST/GET methods are not implemented by `BaseHTTPRequestHandler` subclass (default 501, not tested) | None | BLOCKED (404 path untested; 501 path untested) |
| A-07 | `GET /` | Serve the page | Full HTML page, no external assets | Inline HTML/CSS/JS only; no CDN, no external font, no external image | None (rendering not asserted in tests) | BLOCKED (no render test) |

## CLI controls (not web controls, listed so they are not mistaken for dead UI)

The CLI (`notes_agent/cli.py`) provides `index`, `search`, `ask`,
`summarise`, `organise`, `status`, `demo`, `serve`. These are not
visible web controls and are therefore out of scope for the web
inventory above, but they share the same agent code and are covered
by the 24-test suite (agent/llm/routing/guardrail tests). The CLI is
not a substitute for the missing browser tests listed above.

## Summary of findings

- **Dead buttons: none found.** Every visible web button performs
  a real action.
- **FAIL items (must fix before COMPLETE):**
  1. W-01 — initial-load failure leaves a silent `Loading…`.
  2. W-02 — note items are not keyboard-accessible; quote-in-path
     edge case 404s silently.
- **BLOCKED items (untested, not claimed as tested):**
  - Browser click paths for note preview, organise, reset-budget,
    and the empty-question alert.
  - HTTP tests for `/api/note`, `/api/organise`,
    `/api/reset-budget`, the 404 path, and page rendering.
  - Any Playwright / end-to-end suite (none exists — Rulebook
    Gate D E2E requirement is unmet).
- **No live-Otari behaviour is inventoried as tested**, because no
  live Otari call has ever run for this project. `OtariProvider`
  tests use an injected fake client
  (`test_otari_provider_uses_injected_client`), and the
  no-credentials failure is tested
  (`test_otari_provider_without_credentials_raises_before_network`).
  Both are honest about what they prove: SDK wiring and failure
  behaviour, not a live gateway call.

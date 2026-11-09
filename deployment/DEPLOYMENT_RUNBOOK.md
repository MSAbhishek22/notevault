# NoteVault — Deployment Runbook

> Status: **ON PAPER ONLY — NOT DEPLOYED.** No Render service exists
> for NoteVault, no production URL exists, and nothing in this file
> claims otherwise. This runbook is the plan the user follows in
> their own Render dashboard. Stop at once if Render asks for a card.

## What is being deployed

- **App:** NoteVault web UI (`notes_agent/web.py`, stdlib only) +
  agent (`notes_agent/agent.py`, routing, budget, guardrails).
- **Entry point:** `run.py` → `notes_agent/cli.py` → `serve`.
- **Local run (verified):** `python3 run.py serve` →
  `http://127.0.0.1:8767/`, mock mode, routing panel + budget meter.
- **Repo:** https://github.com/MSAbhishek22/notevault
  (main branch; first Otari commit `97b462e`, rest `38d5793`).
- **Sample data on deploy:** the repo's `notes/` folder (4 sample
  notes: abhiverse-idea, hackathon-plan, study-python,
  weekly-review). These are demo notes, not the user's private notes.

## Hosting choice: Render free tier (planned, not chosen by a live test)

Render is chosen on paper because the app is a long-lived Python
HTTP server (not a static site, so GitHub Pages cannot host it),
and Render's free web-service tier fits a stdlib server with no
database. This choice has **not** been verified by a live Render
deploy. If Render's free tier cannot host it, or asks for a card,
stop and record the blocker — do not silently switch to a paid
plan or a different provider and call it the same deployment.

## Code-change check: HOST / PORT binding — NO code change required

Checked 2026-11-03 against the actual code:

- `notes_agent/web.py`: `make_server(agent, host="127.0.0.1",
  port=8767)` and `serve(agent, host, port)` — host/port are
  parameters, not hard-coded constants in the request path.
- `notes_agent/cli.py`: `serve` subcommand accepts `--host`
  (default `127.0.0.1`) and `--port` (default `8767`), and passes
  them through: `serve(agent, host=args.host, port=args.port)`.
- **Conclusion: no code change is required to bind Render's port.**
  The deploy command must pass both flags explicitly, because the
  CLI does **not** read a `PORT` environment variable on its own:
  if `--port` is omitted, the server binds 8767 regardless of
  Render's `PORT` value, and Render's health check would fail.

## Deploy steps (user's own Render dashboard — agent does not do this)

1. Sign up / sign in at Render (user's own account). **Stop at
   once if Render asks for a card at signup or at service creation.**
2. New → Web Service → connect the GitHub repo
   `MSAbhishek22/notevault`, branch `main`.
3. Settings (verify each one before creating the service):
   - Environment: `Python`
   - Plan: **Free** (verify the plan field literally says Free
     before deploying; if it does not, stop and report it).
   - Build command: `pip install -r requirements.txt`
     (`requirements.txt` installs only `otari` + `pytest`; the app
     itself is stdlib. If the build fails on `pytest`, the fallback
     used by the ClinicLink config — `|| echo 'stdlib only'` —
     must NOT be copied blindly here, because `otari` is a real
     runtime dependency for real-Otari mode. Record a build failure
     as a blocker instead of hiding it.)
   - Start command: `python3 run.py serve --host 0.0.0.0 --port $PORT`
     (Render runs the start command in a shell, so `$PORT` expands
     to Render's assigned port. **Verify in the first deploy log
     that the server actually bound the Render port, not 8767.**
     If it bound 8767, the deploy is misconfigured — do not call
     it live.)
   - Health check path: `/api/status` — **not** `/health`.
     No `/health` route exists in `web.py` (routes are `/`,
     `/api/status`, `/api/note`, `/api/ask`, `/api/organise`,
     `/api/reset-budget`). Using `/health` would 404 and fail the
     deploy for a wrong reason. `/api/status` performs no LLM call
     and returns mode/gateway/budget, so it is safe as a health
     check.
   - Environment variables: see below. **Set names only in the
     dashboard; never paste a token value into any doc, screenshot,
     or video frame.**
4. Deploy, wait for the service to report live, then run the live
   verification checklist (below) in a fresh browser session, in
   one warm session (see sleep caveat).

## Environment variables — NAMES ONLY, never values

| Name | Purpose | Required for deploy? |
|---|---|---|
| `OTARI_AI_TOKEN` | Hosted otari.ai token (real-Otari mode) | No — without it the app runs in labelled mock mode. Required only for the real-Otari run + live video. Never commit it; `.env` is gitignored. |
| `OTARI_MODEL` | Default model string, format `provider:model` | No — default `mistralai/mistral-small-latest` in code (verified live on Otari 9 Nov 2026; `openai:gpt-4o-mini` is not offered on Otari). |
| `OTARI_PROVIDER` | `auto` / `mock` / `otari` | No — default `auto` (mock without credentials, otari with them). Explicit `otari` without credentials fails loudly by design. |
| `OTARI_FALLBACK_MODEL` | One-step fallback model string | No — optional. |
| `GATEWAY_API_BASE` | Self-hosted gateway origin (no `/api/v1` suffix) | No — hosted default is `https://api.otari.ai`. |
| `GATEWAY_API_KEY` | Self-hosted gateway key | No — only with `GATEWAY_API_BASE`. |
| `NOTES_ROOT` | Notes folder | No — default `notes` (repo sample notes). |

No other secrets exist for this app. There is no database, no
session store, no admin password, and no CORS/auth configuration
to set: the UI is unauthenticated by design, and the notes folder
on the deployed service is the repo's sample notes only. Do not
deploy a service pointed at private notes.

## Live verification checklist (all on the production URL, warm first)

1. `GET /api/status` → 200, JSON, `mode` field present, no token
   anywhere in the payload (same guarantee as
   `test_status_dict_never_contains_token`).
2. `GET /` renders the three-column UI (notes / ask / routing +
   budget), the `[mock]` badge if no token is set, and no external
   CDN assets (the page is inline HTML/CSS/JS only).
3. Click a note → preview shows title + body (this also verifies
   the keyboard-gap fix if it has been applied; if not, record it
   as a known issue, do not hide it).
4. Ask "What is Abhiverse for?" → answer with citation chip,
   routing panel (gateway, chosen route, why, fallback chain,
   attempted routes), budget meter moving to 1 / 5.
5. Ask `quantum bananas` → refusal banner, routing panel "No LLM
   call made", budget meter unchanged.
6. `Show plan` → tag-grouped plan, no files changed.
7. `Reset demo budget` → meter back to 0 / 5.
8. If a token is set: badge flips from `[mock]` to `real Otari`
   on the same checks, and no token value appears in any frame,
   screenshot, or video. If the badge does not flip, the real-Otari
   run has not happened — do not claim it has.
9. Desktop + tablet + mobile viewports: no horizontal overflow,
   grid collapses below 800px, primary actions reachable.

## Free-tier caveats (state them on camera / in the submission)

- **Sleep:** Render free services sleep after ~15 minutes idle;
  expect a ~60-second cold start. This is the same caveat as the
  ClinicLink Render config and must be stated, not hidden.
- **No persistence guarantee is needed:** budget is per-process
  session state and notes are the repo sample notes, so a restart
  resets the budget and the notes to the repo state. That is
  acceptable for a demo and must be described as such — do not
  claim durable user storage.
- **Health check is not a keep-alive:** warm the service before
  filming or judging; say so on camera if it was asleep.

## Rollback

- **Bad deploy:** in the Render dashboard, redeploy the previous
  commit (`38d5793` — the last known-good main commit at the time
  this runbook was written) or roll back to the commit recorded in
  `deployment/RELEASE_MANIFEST.json` once a real deploy exists.
  Until a real deploy exists, there is nothing to roll back to —
  the rollback target is the local build, which is verified by the
  24-test suite.
- **Bad token / real-Otari failure:** remove `OTARI_AI_TOKEN` from
  the Render environment (or set `OTARI_PROVIDER=mock`) and
  redeploy. The app then runs in labelled mock mode by design; it
  must not be presented as a real-Otari run in that state.
- **Repo rollback:** the repo is the source of truth. Any deploy
  that cannot be reproduced from the repo's `main` branch is not
  a valid release and must be re-created from the repo, not patched
  by hand on the server.

## Blockers (exact, current as of 2026-11-03)

1. **Render signup + deploy pending (user only).** No Render
   account/service has been created by the agent. This is the
   deployment blocker.
2. **Card gate (hard stop).** If Render asks for a card at any
   point, stop that step and report it. Do not add a card, do not
   propose a card route again.
3. **Real-Otari token pending (user only).** Without
   `OTARI_AI_TOKEN`, the live deploy runs in mock mode. A mock-mode
   live deploy is still a live deploy of the UI, but its demo video
   must be labelled mock and must not be submitted as live Otari
   proof. See `submission/DEMO_VIDEO_MANIFEST.md`.
4. **Known code gaps (not deploy blockers, but release blockers
   for a COMPLETE claim):** keyboard-inaccessible note items,
   silent initial-load failure, no E2E suite, no 3D experience,
   no five-reference design research. See the design constitution
   and interaction inventory.

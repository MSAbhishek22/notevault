# NoteVault — Ask your notes, routed smart

## The story — and why this is not just another "ask your notes" app

I had notes everywhere — project ideas, study notes, weekly reviews —
and every "smart notes" tool wanted the same deal: upload everything,
let it rewrite things, trust a black box.

Generic "ask your notes" is not a unique product, and this project
does not pretend it is. The unique value here is **Otari itself, made
visible**: one gateway in front of many providers, where the model
string (`provider:model`) is the routing decision. NoteVault's job is
to make that routing *something a judge can see and check*:

- **Routing panel, every answer:** which gateway, which provider/model
  was chosen and why, what the fallback chain is, and which routes
  were actually attempted. Change the model string and the route
  changes — the code does not.
- **Budget meter, every answer:** local session calls used/remaining
  (default 5 per run). The gateway-side budget in otari.ai is a
  separate thing and is labelled as such — this app never invents a
  gateway usage number it cannot see.
- **Provider fallback, tested:** if the primary provider call fails,
  a configured fallback model is tried once. If both fail, the answer
  fails loudly. No fabricated answer, ever.
- **Grounded refusal:** if no note matches, it says so before any
  LLM call — so a refusal spends no budget and attempts no route.
  Answers cite the notes they used.

Underneath, it is deliberately small: it reads only the folder you
point it at, on your own machine, searches those notes locally, and
only then asks an LLM to turn a few excerpts into an answer. It never
moves, renames or edits your notes — `organise` only prints a plan.

## What it does

- **Web UI (the demo surface — a judge can click this):**
  notes list + preview, ask box with model selector, answer with
  citations, routing panel, budget meter, organise-plan view
- `index` — list the notes it found, with titles, tags and word counts
- `search <query>` — local keyword search (title and tag hits weigh more)
- `ask <question>` — answer from your notes only; if nothing matches,
  it says so instead of guessing, and cites the notes it used
- `summarise <note>` — 3-bullet summary of one note
- `organise` — a grouping plan by tag; plan only, no files are changed
- `status` — routing (gateway/model/fallback) + budget, no LLM call
- `demo` — a scripted run over the sample notes in `notes/`, now
  including the routing + budget lines and a refusal

## Run it — web UI first (no account needed for the mock demo)

```bash
python3 run.py serve
# open http://127.0.0.1:8767/  (localhost only by default)
# try: "What is Abhiverse for?" then "quantum bananas" (refusal)
# watch the routing panel and the budget meter move
```

CLI still works, unchanged:

```bash
python3 run.py index
python3 run.py status
python3 run.py demo
python3 run.py ask "What is Abhiverse for?"
python3 run.py summarise abhiverse-idea.md
python3 run.py organise --write output/organise-plan.md
```

Fallback model (optional, for the fallback demo + tests):

```bash
export OTARI_FALLBACK_MODEL="provider:model"   # replace with a real provider:model you have access to; the anthropic string in tests/ is a test double only
python3 run.py serve
```

Tests (stdlib code; pytest is only needed to run the suite):

```bash
pip install pytest otari
python3 -m pytest tests/ -q
# 24 tests: 13 original + 11 routing/budget/fallback/web
# (in this sandbox, the pytest venv is /tmp/otari-check-venv)
```

## Otari: what is real, what is mock

**Real, verified code path:** `notes_agent/llm.py` → `OtariProvider`
uses the real `otari` Python SDK exactly as documented:

```python
from otari import OtariClient
client = OtariClient(platform_token=<OTARI_AI_TOKEN>)
response = client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "system", "content": ...},
              {"role": "user", "content": ...}],
)
text = response.choices[0].message.content
```

With no `api_base`, the client defaults to the hosted gateway at
`https://api.otari.ai`. The model string is `provider:model`, so
switching providers does not change the code. A self-hosted gateway
works the same way with `GATEWAY_API_BASE` (origin only, e.g.
`http://localhost:8000` — the SDK appends `/api/v1`) and
`GATEWAY_API_KEY`. See `OTARI_INTEGRATION.md` for the full, verified
details.

**Mock path (what runs today, with no token):** if no Otari
credentials are set, the provider is `mock` — a deterministic,
offline, extractive stand-in. Every mock answer is prefixed `[mock]`,
so it can never be mistaken for a real Otari answer. No live Otari
call has been made from this project yet, because no Otari account
or token was created for it (that step is the user's, see
`SUBMISSION_CHECKLIST.md`).

**To run against real Otari:**

```bash
pip install otari
export OTARI_AI_TOKEN="your-otari-ai-token"   # from otari.ai, never commit it
export OTARI_MODEL="openai:gpt-4o-mini"
python3 run.py --provider otari ask "What is Abhiverse for?"
```

If you run with `--provider otari` and no credentials, it fails
loudly with a clear error instead of silently falling back to mock.

## Guardrails (all local, all tested)

- Only `.md` / `.txt` files under the notes folder are read; `..`,
  absolute paths and symlinks escaping the folder are refused
- Files over 200 KB are skipped; at most 3 notes, 4,000 chars each,
  are sent to the LLM per answer, with a 5-call budget per run
- Note text is wrapped as data (`<notes-data>…</notes-data>`) and the
  system prompt says to ignore instructions inside notes; notes
  containing instruction-like text are flagged
- Note bodies are never logged in full; only titles and short previews

## Otari features used — and not used

Used: hosted Otari.ai gateway via the official Python SDK,
`completion` chat completions, `provider:model` routing, token-based
auth from the environment, plus this project's own visible routing
panel, local session budget meter, and one-step provider fallback
(local logic around Otari calls — not a gateway feature).

NOT used (do not claim these in the submission): Otari's built-in
code-execution / web-search tools, LangChain integration, gateway-side
budget/usage numbers from otari.ai (the local call budget above is
this project's own guardrail; gateway-side budgets are configured
and viewed in otari.ai by the account holder).

## Project layout

```
run.py                 Entry point (CLI + `serve` for the web UI)
notes_agent/
  config.py            Env config (tokens only from env, never logged)
  guardrails.py        Path, size, and prompt-injection guards
  index.py             Local note parsing + keyword search
  llm.py               OtariProvider (real) + MockProvider (offline)
  routing.py           provider:model parsing, routing decision, budget meter
  agent.py             Search / ask / summarise / organise-plan + ask_detailed
  cli.py               Commands (index/search/ask/status/serve/demo/…)
  web.py               Stdlib web UI (localhost only, no external assets)
notes/                 Sample notes (replace with your own folder)
tests/                 24 tests, stdlib + pytest only
```

## Hackathon

Mozilla Otari Hackathon — Devs Wilding Online, DoraHacks,
28 Oct – 11 Nov 2026, submit by 11 Nov 11:59 PM.
Event page: https://dorahacks.io/hackathon/mozilla-devs-wilding/detail
Otari repo: https://github.com/mozilla-ai/otari

This repo copy is a submission *draft*: no DoraHacks account was
created and nothing was submitted by the agent. The exact steps the
user must do himself are in `SUBMISSION_CHECKLIST.md`.

# Otari integration — verified facts, no inventions

Source pages (read 2026-11-02):
- DoraHacks event: https://dorahacks.io/hackathon/mozilla-devs-wilding/detail
- Otari repo: https://github.com/mozilla-ai/otari
- Otari Python SDK: https://pypi.org/project/otari/

## What Otari is

Otari by Mozilla AI is an open-source, OpenAI-compatible LLM gateway:
one endpoint in front of 40+ providers, with API-key management,
budget enforcement and usage tracking. Your app talks to Otari, Otari
routes to the provider. Hosted platform: otari.ai. Self-hosted: the
same gateway on your own infrastructure (port 8000 by default).

## Verified SDK surface (checked against the installed package)

- Install: `pip install otari` (Python 3.11+ per PyPI; verified here on 3.12)
- `from otari import OtariClient`
- `OtariClient(platform_token=...)` — hosted mode, defaults to
  `https://api.otari.ai` when no `api_base` is given
- `OtariClient(api_base="http://localhost:8000", api_key=...)` —
  self-hosted mode; `api_base` is the origin only, the SDK appends
  `/api/v1` itself
- `client.completion(model="mistralai/mistral-small-latest", messages=[...])`
  returns a typed chat completion; text at
  `response.choices[0].message.content`
- Env names used by the SDK: `OTARI_AI_TOKEN` (canonical, hosted),
  legacy alias `GATEWAY_PLATFORM_TOKEN`; self-hosted:
  `GATEWAY_API_BASE` + `GATEWAY_API_KEY`
- Model strings are `provider:model` (e.g. `openai:gpt-4o-mini`) or
  the dashboard `vendor/model` form (e.g. `mistralai/mistral-small-latest`).
  The full string is passed to the SDK unchanged.

## What this project verified, and what it did not

Verified in this sandbox:
- SDK installs, imports, and `OtariClient` constructs (with a dummy
  token, no network call on construction) — but only after clearing
  the sandbox proxy env vars, which otherwise break the SDK's HTTP
  client setup with an `InvalidURL` port error. That is a sandbox
  networking quirk, not a project bug; on a normal machine the
  client constructs directly.
- `OtariProvider` in `notes_agent/llm.py` calls the SDK with exactly
  the signature above, and extracts `choices[0].message.content`
  (with a dict fallback). This is covered by a test with an injected
  fake client — no real network.
- With `--provider otari` and no credentials, the CLI fails loudly
  ("No Otari credentials…") instead of silently using mock.

NOT verified / NOT done:
- No live Otari.ai call (no account, no token, no provider key was
  created — by design, per the hard rules).
- No gateway-side budget/usage dashboard check (that lives in the
  user's otari.ai account once they sign up).
- No use of Otari built-in tools (code execution, web search) or
  LangChain integration — see README for the honest feature list.

## Routing + budget — what is Otari's, what is this project's

Otari's (verified gateway behaviour): one endpoint, model strings in
`provider:model` or dashboard `vendor/model` form, routing to the
named provider, token auth. This
project does not re-implement routing — it *exposes* it. The web UI
and `run.py status` show the gateway, the chosen provider/model and
its reason, the fallback chain, and the routes actually attempted,
for every answer (`notes_agent/routing.py`, `agent.ask_detailed`).

This project's own (local, tested, not gateway features):
- **Fallback:** if the primary provider call raises and a fallback
  model is configured (`OTARI_FALLBACK_MODEL`), the fallback is
  tried once. In mock mode the fallback stand-in is also mock and
  labelled `[mock]`. If both fail, the call fails loudly.
- **Budget meter:** the local session budget (default 5 provider
  attempts per agent run, `max_llm_calls_per_run`). A refused
  question makes no provider call and spends nothing. The meter in
  the UI is this local budget only.
- **Gateway budget:** NOT shown as a number anywhere in this app.
  Gateway-side budget/usage lives in the otari.ai account dashboard.
  The UI says exactly that instead of inventing a figure.
- **Model selection in real mode:** a user-selected model string is
  actually used for that call (a provider built with that string),
  not just displayed. In mock mode the selected string is the
  *intended* route and the answer stays mock-extractive, labelled
  `[mock]` — the panel's mode label says so.

## Switching this project to real Otari (user step)

1. Sign up at otari.ai, generate an API token, and add a provider key
   (or use a Mozilla-managed model if offered) in otari.ai settings.
2. `pip install otari`
3. `export OTARI_AI_TOKEN="..."` (never commit it; `.env` is gitignored)
4. `python3 run.py --provider otari ask "…"`

Then record the demo (see DEMO_SCRIPT.md) with the real provider so
the video shows a genuine Otari-routed answer, and keep one mock run
as the offline fallback evidence.

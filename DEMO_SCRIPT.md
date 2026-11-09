# Demo script — web UI, 3–5 minutes, narrated real assets only

Status: SCRIPT ONLY. No demo video has been recorded yet. Record it by
following the steps below on screen; do not splice in footage of a
different app, and label the mock run as mock.

**The point to land in the first 30 seconds:** this is not "another
ask-your-notes app". It is "ask your notes, routed smart" — Otari is
one gateway for many providers, and this UI *shows* the routing,
the budget, and the fallback for every answer. If the video only
shows an answer box, it has missed the product.

A second, separate 3–5 minute video is needed for Otari feedback
(see SUBMISSION_CHECKLIST.md) — do not reuse the same recording for both.

## Setup (on camera, briefly) — ~20 seconds

1. Start the UI on camera: `python3 run.py serve` → open
   http://127.0.0.1:8767/ . Say: "Localhost only. My notes folder
   is local; nothing leaves this machine except the few excerpts
   sent to Otari, and only when I ask."
2. Point at the notes list (4 sample notes) and the `[mock]` badge.
   Say the badge out loud — mock is not hidden anywhere in this demo.

## Scene 1 — Ask, and read the routing panel — ~70 seconds

Click "Try: Abhiverse" (or type: `What is Abhiverse for?`).

Show, in order, and narrate each one:
- The answer, quoting the note itself.
- The citation chip: "Abhiverse idea".
- The **Routing panel**: gateway `https://api.otari.ai`, chosen
  `mistralai / mistralai/mistral-small-latest`, reason "Default model from
  configuration — routed through Otari unchanged", attempted route
  listed, fallback chain (none configured in this run, or the
  fallback model if you set `OTARI_FALLBACK_MODEL`).
- The **Budget meter**: 1 / 5 used, 4 remaining. Say: "This is the
  local session budget. The gateway-side budget lives in the
  otari.ai dashboard — this app does not invent that number."

## Scene 2 — Switch the route — ~50 seconds

In the model box, pick a different model string (or type a custom
`provider:model` string you actually have access to in real mode;
in mock mode, say so). Ask the same question again.

Narration: "Same code, same notes — only the model string changed,
and Otari routes it. The routing panel now shows the new chosen
route and why." In mock mode, add verbatim: "This answer is still
mock — you can see the [mock] badge — so this shows the *intended*
route, not a live route. The live route comes in Scene 4."

## Scene 3 — Refusal, and the budget that does not move — ~50 seconds

Click "Try: refusal" (`quantum bananas`).

Show: the refusal banner ("Refused — no guess"), the routing panel
saying "No LLM call made — refused before routing", and the budget
meter **unchanged** from Scene 1/2.

Narration: "No matching notes, so no provider was called, no route
was attempted, and no budget was spent. A notes agent that guesses
is worse than one that says it does not know."

## Scene 4 — Real Otari mode (only if the token is ready) — ~70 seconds

Only after the user has an otari.ai token (see OTARI_INTEGRATION.md):

```
pip install otari
export OTARI_AI_TOKEN="..."
python3 run.py serve
```

Ask the same question. Show the badge changing from `[mock]` to
"real Otari", and the same routing panel + budget meter, now for a
genuine gateway call. If the dashboard allows it, show the usage
entry in otari.ai. Do not show the token on screen — blur or cut
any frame where it appears.

If the real-Otari run is not ready by recording day, say so on
camera and submit the mock demo labelled as mock; do not present
mock output as an Otari answer.

## Scene 5 — Organise plan + fallback, honestly — ~40 seconds

Click "Show plan". Narration: "Organise never moves a file. It
prints a plan grouped by tag."

On fallback, do NOT fake a provider outage on camera. Say, over the
routing panel: "If the primary provider fails, the configured
fallback model is tried once; if both fail, the answer fails
loudly instead of being invented. That path is covered by tests,
not staged in this video."

## Closing line — ~10 seconds

"NoteVault: your notes, answered locally — and routed smart,
through one gateway: Otari. Routing you can see, budget you can
see, and no guessing when your notes do not have the answer."

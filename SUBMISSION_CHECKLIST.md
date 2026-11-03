# Submission checklist — steps the USER must do himself

The agent did NOT do any of these, on purpose: DoraHacks signup,
Otari.ai signup, and the submission itself all need the user's own
account, email, and confirmations. Nothing below is submitted yet.

Event: Mozilla Otari Hackathon — Devs Wilding Online (DoraHacks)
Page: https://dorahacks.io/hackathon/mozilla-devs-wilding/detail
Deadline on the page: **Nov 11th 11:59 PM to submit your project**.
The event listing ends 2026-11-11T22:59:00Z (= 12 Nov, 04:29 IST).
Timezone on the "11:59 PM" line is not stated on the page — submit
by the evening of 11 Nov IST to be safe, and re-check the timezone
on the DoraHacks page at submission time. Do not leave it to the
last hour.

Prizes on the page: 1st $1,000 + 3 hours with Mozilla.ai engineers;
2nd $200 + 2 hours; 3rd 1 hour with Mozilla.ai engineers.

## 1. Sign up (user only)

- [ ] DoraHacks signup for this hackathon with: (a) your name or
      pseudonym, (b) the email you will use to sign up at Otari.ai,
      (c) one sentence explaining your project.
      One-liner to use: "NoteVault: ask your notes, routed smart —
      one Otari gateway, many providers, with visible routing,
      budget, fallback, and grounded answers that refuse to guess."
- [ ] Sign up at otari.ai. The page says the first 200 signups got
      $20 in tokens — that offer may already be exhausted; do not
      rely on it, and do not add a card for it.
- [ ] Join the Mozilla OSAI Discord and take the `devs-wilding` role
      (link on the DoraHacks page).
- [ ] Star https://github.com/mozilla-ai/otari on GitHub.

## 2. Publish the code (user only)

- [ ] Create a PUBLIC GitHub repo for NoteVault (or use an existing
      project repo) and push this folder to it.
- [ ] Work on a hackathon branch (e.g. `devs-wilding`).
- [ ] IMPORTANT — first-Otari-commit link: the submission asks for
      "the first commit on that branch where Otari came in". When
      pushing, make the Otari integration its own commit (the commit
      that adds `notes_agent/llm.py` with `OtariProvider`), and keep
      that commit's URL for the submission form. If you squash the
      history, that link is lost.
- [ ] Run the real-Otari check once (see OTARI_INTEGRATION.md):
      `pip install otari`, set `OTARI_AI_TOKEN`, then
      `python3 run.py --provider otari ask "What is Abhiverse for?"`
      and `python3 run.py --provider otari serve` to check the web
      UI badge flips from `[mock]` to real Otari.
      Never commit the token; `.env` is already gitignored.

## 3. Record videos (user only, see DEMO_SCRIPT.md)

- [ ] Demo video, 3–5 min, showing real progress with Otari
      (follow DEMO_SCRIPT.md — web UI, routing panel + budget meter
      + refusal are the point, not just an answer box; label any
      mock run as mock).
- [ ] Feedback video, 3–5 min (screen recording, answering on camera):
      what you built with Otari and which features you used; what
      worked well; what didn't work (bugs/friction, with repro steps
      if you can); what's missing and what you'd change.
      OR written feedback answering: when were you most tempted to
      skip Otari and call the provider directly, and what happened?
      What did you end up building yourself that Otari should've
      done for you? If the rules hadn't required Otari, would you
      have continued using it, and why?
      (Submitting feedback, screen recording or written or both, is
      required — see below.)

## 4. Submit (user only, on DoraHacks)

The DoraHacks page lists these submission items, and says a
submission missing any of them is not eligible for prizes:

- [ ] Project name, the email you signed up to Otari.ai with, and
      one line on what your project does
- [ ] Public GitHub repo link + the hackathon branch name
- [ ] Confirmation you used Otari.ai, with the link to the first
      commit where Otari came in (step 2 above)
- [ ] Otari features used — use the honest list from README.md:
      hosted gateway via the official Python SDK, `completion` chat
      completions, `provider:model` routing, plus this project's own
      visible routing panel, local session budget meter, and
      one-step provider fallback (local logic around Otari calls,
      not gateway features). Do NOT claim built-in code execution,
      web search, LangChain integration, or gateway-side budget
      numbers from otari.ai.
- [ ] Any PRs or issues opened on the Otari repo (none opened by the
      agent; add "none" if you open none, rather than inventing one)
- [ ] Link to the 3–5 min demo video
- [ ] Feedback: link to the 3–5 min feedback screen recording
      and/or the written feedback
- [ ] Screenshot / save the submission confirmation. A project left
      as a draft is NOT submitted — check for a "submitted"
      confirmation before the deadline.

## What the agent already did (so you don't redo it)

- Verified the event rules and Otari SDK surface from the official
  pages (DoraHacks page + PyPI `otari` docs + installed package).
- Built the runnable prototype in this folder, with 24/24 tests
  passing (13 original + 11 routing/budget/fallback/web) and a
  working mock demo.
- Added the web UI (`python3 run.py serve`, localhost only) with
  notes list, ask box, citations, routing panel, budget meter, and
  organise-plan view; the CLI still works unchanged.
- Sharpened the product from generic "ask your notes" to
  "ask your notes, routed smart" — routing, budget, fallback, and
  grounded refusal are the visible Otari value.
- Wrote README (storyline), DEMO_SCRIPT, OTARI_INTEGRATION, and
  this checklist.

## What the agent did NOT do (and why)

- No DoraHacks account created, no Otari.ai account created, no
  submission made — these need your identity, email and clicks.
- No demo video recorded — that needs your screen + voice.
- No live Otari call made — no token exists for this project yet.
- No card, no payment, no secret was requested, added, or stored
  anywhere in this folder (verified by grep: no token values present).

# NoteVault — Demo Video Manifest

> Status: **NOT recorded from live. Do not use the videos below as
> live proof.** Both existing videos were made from the local /
> mock UI. Under the Rulebook (Gate F) and the user's live-link
> video rule, they must be re-recorded from the verified production
> URL after a live deploy AND a real Otari run, before they can be
> submitted as a live demo.

## Existing videos (local / mock only — NOT live proof)

| Video | URL | What it actually shows | Status |
|---|---|---|---|
| Demo video | https://www.youtube.com/watch?v=ztc4U1I2u-E (3:59) | Local UI, mock mode, routing panel + budget meter | LOCAL/MOCK ONLY — must be re-recorded from live |
| Feedback video | https://youtu.be/2sg7KyYQsOw (4:54) | Separate feedback video, local/mock only | LOCAL/MOCK ONLY — feedback content, not live demo proof |

- Neither video was recorded from a production HTTPS URL, because
  no production URL exists.
- Neither video shows a real Otari call, because no Otari token
  exists for this project and no live Otari call has ever run.
- The mock badge / `[mock]` labelling in the local UI is the only
  reason these videos are honest at all: they show mock output
  labelled as mock. Presenting either video as a live Otari demo
  would be a false claim and is prohibited by this manifest.

## What the live-recorded video must contain (Gate F)

Record only after, in order: Render deploy → production verification
(see `deployment/DEPLOYMENT_RUNBOOK.md` live checklist) → freeze the
release commit → record from the production URL.

- Production URL visible / identifiable in the recording.
- Deployed commit SHA recorded below at recording time (currently
  null — the repo's latest main commit at manifest-writing time is
  `38d5793`, but that is NOT a deployed commit until a deploy
  actually serves it).
- Problem statement, core value (visible routing + budget +
  grounded refusal), main journey (ask → routing panel → budget),
  refusal with unchanged budget, organise plan (plan only).
- Real Otari badge flip (`[mock]` → `real Otari`) on camera, with
  no token value visible in any frame.
- 3D routing map only if it has been implemented by then; otherwise
  no 3D claim in the video.
- Duration: the DoraHacks demo requirement is 3–5 minutes (see
  `DEMO_SCRIPT.md`); the Rulebook's generic 60–120s target does not
  override the organiser's requirement. Record to the organiser's
  requirement and note the duration below at recording time.

## Recording record (to be filled at recording time — all null now)

- production_url: null
- release_version: null
- deployed_commit_sha: null
- recording_date: null
- video_duration_seconds: null
- video_file: null
- published_video_url: null
- upload_status: BLOCKED_AUTHORIZATION (no live video exists to
  publish; the existing local/mock videos are not the live video)

## Submission rule

Do not attach either existing video URL to a DoraHacks submission
as evidence of a live Otari demo. They may be referenced, if at
all, only with an explicit "local/mock demo" label, and the
submission must not claim live Otari behaviour until the
re-recorded live video exists. The feedback video's purpose is
feedback, not demo proof, and the same labelling rule applies.

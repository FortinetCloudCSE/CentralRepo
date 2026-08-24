# Plan: launchdemoform Rebuild — Progress UI, Credential Display, Single-Attempt Lock
Date: 2026-08-24
Owner: Jeff Kopko
Slug: launchdemoform-rebuild
Status: Proposed
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-08-24_Jeff-Kopko_launchdemoform-rebuild.md
Log File: docs/plans/2026-08-24_Jeff-Kopko_launchdemoform-rebuild.log.md

## Goal
Rework `layouts/shortcodes/launchdemoform.html` to call the new Azure Durable Function (see companion plan in `fortinet-on-demand-labs-provisioning-and-tracking`), poll it for real status, show progress/percentage while provisioning runs, display returned credentials on the page, and persist them (and a single-attempt lock) for the rest of the browser session — scoped per Hugo site, since all ~65 workshop sites share one GitHub Pages origin.

## Context / Links
- Backend spec/plan: `fortinet-on-demand-labs-provisioning-and-tracking/docs/plans/0001_2026-08-24_Jeff-Kopko_azure-function-rebuild.{spec.,}md`
- Current shortcode: [`layouts/shortcodes/launchdemoform.html`](../../layouts/shortcodes/launchdemoform.html)
- Storage-scoping precedent: [`layouts/partials/custom-header.html`](../../layouts/partials/custom-header.html) (pathgate's `absBaseUri`-prefixed key convention, lines ~663-762) and `themes/hugo-theme-relearn/layouts/partials/dependencies/theme.html` (`window.relearn.getItem/setItem`, lines ~83-85)
- Retry/fallback precedent: [`layouts/partials/silent_cross_site_checkin.html`](../../layouts/partials/silent_cross_site_checkin.html) (`tryFetch` → `tryBeacon` → hidden-form fallback chain)
- Async UI state-machine precedent: `custom-header.html`'s support modal (`STATE`, `setStatus`, lines ~875-1221)

## Constraints / Assumptions
- **No bundler, inline `<script>`/`<style>` in the shortcode file** — matches every other shortcode/partial in this theme. Guard with the existing idempotency-flag convention (`if (window.__launchdemoform_loaded) return;`) since partials/shortcodes can appear multiple times per page render.
- **Storage must be `absBaseUri`-prefixed**, reusing `window.relearn.getItem/setItem` — confirmed all ~65 workshop sites share the origin `fortinetcloudcse.github.io` (project pages under one user site), so unprefixed `localStorage`/`sessionStorage` keys leak across workshops. This is not optional polish; it's the mechanism that makes "per Hugo repo/site" persistence actually true.
- **`sessionStorage`, not `localStorage`**, for the attempt-lock and credential display — matches "retain for the entirety of their session," and follows the existing (if currently unprefixed) precedent in `custom-header.html`'s support-session-id code. Still gets the `absBaseUri` prefix.
- The POST target changes from the raw Azure Automation webhook (`mode:'no-cors'`) to the new Function's `/api/provision/start` endpoint, called normally (CORS-enabled, response readable) — this reverses CentralRepo PR #69's workaround, which is safe because the *new* backend will send real CORS headers (unlike the old raw Automation webhook).
- Single-attempt enforcement is client-UI convenience layered on top of the backend's real idempotency guarantee (Durable Entity dedup key) — the client must not be the only thing preventing double-provisioning, per the backend plan.
- Retry is only offered after a definitive `Failed` terminal status from the backend, never just because a poll is slow — matches Jeff's stated retry semantics.
- No existing theme convention for progress/percentage UI — this plan establishes one (modeled structurally on the support modal's `STATE`/`setStatus`, adding a `setProgress(pct)` sibling), not adapting something that already exists.
- Two-hop deploy: this change only reaches workshop sites after (1) merge to CentralRepo `main` rebuilds the `fortinet-hugo` Docker image, and (2) each workshop repo's next `fortihugorunner pull-image`. Out of this plan's control per-repo; noted in rollout follow-ups.
- Out of scope (see backend spec): updating the 8 sibling repos with local `launchdemoform.html` overrides that shadow this file via `local_copy.sh`; a shared cookie-helper partial (dedup nice-to-have, not required).

## Plan
- [ ] **Step 1 — Freeze the HTTP contract against the backend plan.** Confirm exact request/response JSON shapes for `POST /api/provision/start` and `GET /api/provision/status/{token}` once the backend's Phase 4 is implemented (or stub against the spec's documented shapes to unblock parallel work — coordinate via the backend plan's Phase 10 integration step before merging either side).
- [ ] **Step 2 — Storage helpers.** Add a small internal helper (inline in the shortcode, or a new shared partial if the duplication with `custom-header.html`'s key-prefixing becomes awkward) wrapping `window.relearn.getItem/setItem/removeItem` for three site-scoped `sessionStorage` keys: attempt status, poll token, and credential payload. Try/catch around all calls (private-browsing/storage-disabled fallback), matching `saveProfileEmail`'s existing pattern.
- [ ] **Step 3 — Replace the POST + no-cors flow.** POST to the new start endpoint with normal `fetch` (no `mode:'no-cors'`), parse the JSON response (opaque token + status URL), handle a same-participant-duplicate response (backend returns existing status instead of erroring) as a normal resume-in-progress case, not an error.
- [ ] **Step 4 — Poll + progress UI.** `setInterval` polling the status endpoint (reasonable interval, e.g. 3-5s, backing off on repeated identical status to avoid hammering); update a progress bar/percentage and step-name label from the response; store the latest known status in the session-scoped keys from Step 2 so a reload resumes cleanly.
- [ ] **Step 5 — Credential display + persistence.** On terminal success, render a credential card (username/sign-in info, resource group, expiry, portal link) in the shortcode's existing container; persist it via Step 2's helpers. On page load, check stored state first — render the credential card or resume polling immediately, before ever showing the button.
- [ ] **Step 6 — Single-attempt lock + failure/retry UI.** Button disables permanently once any attempt exists (in-flight or complete) for this site+lab in session storage; only a stored `Failed` terminal status re-enables a retry button, with the prior failure reason shown.
- [ ] **Step 7 — Docs.** Update `README.md`'s `launchdemoform` section (params unchanged: `lab`/`labdefinition`, `debug`, `customer`, `smartticket`; document the new behavior: progress UI, credential display, single-attempt lock, session scoping). Add a `RELEASE_NOTES.md` entry.
- [ ] **Step 8 — UserRepo author docs.** New page `UserRepo/content/02Hugo/8_azure_lab_provisioning/index.md` (weight 80), following the `7_printable_handouts`/`6_deployment_paths` structure (problem statement → params → live example → gotchas → reference links to this file and the Function repo). Add a `content/00ChangeLog/_index.md` entry. Small enough to implement directly, no separate plan file (per global workflow's "Direct in-conversation" scope).
- [ ] **Step 9 — Local render test.** Build this repo's own Hugo site locally (or a minimal test content page) against the new shortcode to visually verify progress UI, credential card, and reload-resume behavior before merging.

## Plan Changes
- (none)

## Decisions & Commentary
- Reversing the `no-cors` workaround (PR #69) is safe only because the backend side of this initiative guarantees real CORS headers — this plan does not stand alone; it depends on the Function's Phase 4.
- sessionStorage chosen over localStorage specifically to match "for the entirety of their session" — a participant closing the tab and coming back later is expected to re-request, not silently see stale credentials from an earlier session.

## Files Changed
- (none yet — plan stage)

## Session Summary
- (write at end) What changed + why.

## Promotion
- [ ] `Decisions & Commentary` walked
- [ ] Durable facts promoted to `CLAUDE.md` — list them: <...>
- [ ] Nothing to promote (say so explicitly rather than leaving this section blank)
- [ ] `Status:` set to `Complete`

## Follow-ups
- [ ] Audit + update/remove local `launchdemoform.html` overrides in the 8 sibling repos identified as shadowing this file (`DemoFrontEnd`, `cnf-aws-iday`, `HugoGuidePage`, `fortigate-automation-stitch-workshop`, `DemoFrontEndDocker`, `LocalCopy-CentralRepo`, `JSKTest`, `azure-102-foundational`).
- [ ] Consider a shared cookie-helper partial to dedupe the hand-rolled `getCookie`/`setCookie` logic currently duplicated across 4 files.

## Risks / Open Questions
- Poll interval/backoff tuning is a guess until real provisioning durations are known from the backend's Phase 10 end-to-end test.
- Two-hop deploy timing means this can merge and sit unreleased-to-workshops for a while; coordinate a `pull-image` refresh reminder for repos actively using `launchdemoform` when this ships.

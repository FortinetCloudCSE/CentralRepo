# Plan: Xperts26Banner shortcode
Date: 2026-09-01
Owner: Jeff Kopko
Slug: xperts26-banner-shortcode
Status: Complete
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-09-01_Jeff-Kopko_xperts26-banner-shortcode.md
Log File: none — single session, no blast radius beyond CentralRepo + a throwaway
  ai-101 test page that was deleted before commit; the technical narrative is
  already carried by the commit messages, RELEASE_NOTES.md, and CLAUDE.md.

<!-- Written retroactively after implementation, at the user's request, to leave a
     durable record. All steps below were already executed before this file existed. -->

## Goal
- Create a reusable `Xperts26Banner` Hugo shortcode in CentralRepo, usable by all
  ~65 downstream workshop repos, following the `Xperts25Banner` pattern: a base
  image with `line1`/`line2`/`line3` overlaid as editable text.

## Context / Links
- Issue: none (direct user request, no tracked issue)
- PR: [#112](https://github.com/FortinetCloudCSE/CentralRepo/pull/112) (shortcode),
  [#113](https://github.com/FortinetCloudCSE/CentralRepo/pull/113) (docs close-out)
- Docs: `CLAUDE.md` → Critical Patterns & Gotchas (draw.io embed encoding, promotion
  pre-flight false-trip); `RELEASE_NOTES.md` → `[Unreleased]`
- Related code paths: `layouts/shortcodes/Xperts25Banner.html`,
  `layouts/partials/shortcodes/Xperts25Banner.html` (2025 precedent),
  `layouts/shortcodes/Xperts26Banner.html`,
  `layouts/partials/shortcodes/Xperts26Banner.html` (this work)

## Constraints / Assumptions
- Base image supplied by the user (`docs/XPerts26Banner.png`, 1099×514 — Nashville
  skyline + `FORTINET | USA XPERTS26` logo, dropped into the repo ahead of the
  session).
- Scope is the banner shortcode only — not a full `Xperts2026` site theme (2025 had
  both: a `themeVariant`-driven CSS theme *and* a standalone banner shortcode; this
  request was only for the latter).
- Must render byte-identical in structure to `Xperts25Banner.html` (a draw.io
  "Embed HTML" export) so future authors can keep editing these the same way.
- Must be reviewable in a real browser before pushing — the mxgraph div needs
  `viewer-static.min.js` to render client-side, so no non-visual check substitutes
  for looking at it.

## Plan
- [x] Reverse-engineer `Xperts25Banner.html`'s encoding pipeline (HTML-entity →
      JSON-string escape → XML-attribute escape, three layers) by decoding it and
      extracting the embedded background PNG
- [x] Verify the reverse-engineered pipeline by round-tripping the 2025 file
      byte-for-byte before trusting it for the new banner
- [x] Measure the new base image's safe text zone (bounding-box scan for non-black
      content) to place `line1`/`line2`/`line3` without colliding with the logo or
      the skyline artwork
- [x] Generate `layouts/partials/shortcodes/Xperts26Banner.html` (the mxgraph div +
      embedded image) and `layouts/shortcodes/Xperts26Banner.html` (thin wrapper)
      programmatically from the verified pipeline
- [x] Update the shortcode listing in `README.md`, `CLAUDE.md`, and
      `.github/copilot-instructions.md`
- [x] Spin up a local Hugo build (unmerged CentralRepo mounted against `ai-101`
      content) with a throwaway test page exercising both a short-line and a
      long-line (overflow-risk) case; serve it locally for the user to review in a
      browser
- [x] Move the source PNGs from `docs/` (drop location) into `static/images/`,
      matching the 2025 naming convention, for future editability
- [x] Clean up: delete the throwaway `ai-101` test page, stop the local server,
      clear the root-owned `public/`/`hugo.toml` build output from the CentralRepo
      working tree
- [x] Commit + push to `dev`, confirm `dev`'s push-triggered CI green
      (`ci.yml` hugo-build + the dev image build workflow)
- [x] Open PR `dev` → `main`, merge via `gh-merge-verify`, confirm the prod image
      workflow (`fortinet-hugo:latest`) actually ran (not silently skipped)
- [x] Close out: `RELEASE_NOTES.md` entry, promote durable gotchas into
      `CLAUDE.md`, commit + push + PR + merge that follow-up too

## Plan Changes
- None — written after the fact from the actual session sequence, so there was no
  approved version to diverge from.

## Decisions & Commentary
- Reproduce the draw.io embed's encoding programmatically (build raw XML →
  `json.dumps` → `html.escape`) rather than hand-editing the exported HTML — the
  2025 file is a single ~500KB line with three nested escaping layers; hand-editing
  it is how a future person breaks the div silently. Verified byte-for-byte against
  `Xperts25Banner.html` before trusting it for 2026. **Promoted to CLAUDE.md.**
- Store the source PNGs under `static/images/` (naming: `xperts-2026-background.png`,
  `XPerts26-logo.png`) even though the shortcode embeds the image as base64 and
  reads nothing from that path — matches the 2025 precedent and keeps a real source
  file around for future edits instead of only the giant embedded base64 blob.
  **Promoted to CLAUDE.md** (as part of the encoding-pipeline gotcha).
- Left `docs/XPerts26logo.png` (standalone square X logo) unwired — no content or
  `layouts/partials/logo.html` change references it, matching 2025's own orphaned
  `XPerts25-logo3.png`. Scope was the banner shortcode only; wiring a full site
  theme was not requested.
- `gh-merge-verify`'s CI-skip-token pre-flight tripped on both promotion PRs (#112,
  #113) despite `git diff origin/main origin/dev` showing a small, clean diff —
  two `[skip ci]`-tagged commits from the 2026-08-25 branch-rename work are still
  in the PR's commit-ancestry compare even though their content is already in
  `main`. Fixed both times with `-- --subject "..." --body "..."` (replaces the
  default squash message instead of concatenating every commit's message).
  **Promoted to CLAUDE.md and to memory** (`centralrepo-merge-process-gotcha.md`).
- Each text line's real safe width before it overlaps the skyline artwork
  (~490–560px, measured per-line, not a flat number) is materially narrower than
  the text-box width the shortcode allows (nearly full canvas, matching 2025's own
  behavior) — a deliberate non-fix, left as content-author responsibility rather
  than constraining the box, to stay consistent with the existing shortcode's
  contract. **Promoted to CLAUDE.md.**

## Files Changed
- `layouts/shortcodes/Xperts26Banner.html` (new)
- `layouts/partials/shortcodes/Xperts26Banner.html` (new)
- `static/images/xperts-2026-background.png` (new)
- `static/images/XPerts26-logo.png` (new, unwired)
- `README.md`, `CLAUDE.md`, `.github/copilot-instructions.md` (shortcode listing)
- `RELEASE_NOTES.md` (new `[Unreleased]` entry)
- `CLAUDE.md` (two new Critical Patterns & Gotchas bullets — see Decisions above)
- (`ai-101` repo, not committed) `content/99XPertsBannerTest/_index.md` — throwaway
  review page, created and deleted within this session

## Session Summary
Built `Xperts26Banner` as a byte-for-byte-verified continuation of the
`Xperts25Banner` draw.io-embed pattern, using a base image the user supplied.
Reviewed live in a browser via a local Docker Hugo build (unmerged CentralRepo
mounted against `ai-101` content, 0 WARN/0 ERROR) before pushing anything. Shipped
through the repo's mandatory dev-first flow: `dev` push → CI green → PR → `main`
merge, verified twice that the deploy actually ran and wasn't silently suppressed
by a stale `[skip ci]` token. Two PRs total: #112 (the shortcode) and #113 (the
release-note/CLAUDE.md close-out for it). No full 2026 site theme was built —
scope stayed to the banner shortcode as requested.

## Promotion
- [x] `Decisions & Commentary` walked
- [x] Durable facts promoted to `CLAUDE.md` — listed:
  1. The draw.io "Embed HTML" three-layer encoding pipeline and how to reproduce
     it programmatically for any future `XpertsNNBanner`.
  2. The `dev`→`main` promotion CI-skip-token pre-flight false-trip and its fix
     (`--subject`/`--body` override).
- [x] Nothing else to promote — the per-line text-width limit and the orphaned
  logo file are noted above but are content/asset-management notes, not code
  behavior; no separate CLAUDE.md line needed beyond what's already there.
- [x] `Status:` set to `Complete`

## Follow-ups
- [ ] `layouts/partials/dependencies.html` — a root-owned, untracked file that
  appeared in the working tree from the local Docker build (theme dependency
  partial materialized as a side effect of the container's layout-copy step). Not
  staged or committed. Deleting it via a container (`docker run --rm -v "$PWD":/home/CentralRepo alpine:latest sh -c 'rm -f /home/CentralRepo/layouts/partials/dependencies.html'`)
  was blocked by the session's permission classifier; harmless to leave, but
  someone with direct shell access should clean it up.
- [ ] `static/images/XPerts26-logo.png` is unwired — if a full `Xperts2026` site
  theme (`themeVariant`, `theme-Xperts2026.css`, `logo.html` wiring) is wanted
  later, this file is the source to use, same role as 2025's `XPerts25-logo3.png`.

## Risks / Open Questions
- None outstanding. The one real risk during the session — a silently-suppressed
  prod deploy from a stale CI-skip token — was caught by `gh-merge-verify`'s
  pre-flight both times and resolved before merging.

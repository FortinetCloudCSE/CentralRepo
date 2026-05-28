# Plan: CentralRepo Bug Fix & Cleanup
Date: 2026-05-28
Owner: Jeff Kopko
Slug: centralrepo-bugfix
Plan File: docs/plans/2026-05-28_Jeff-Kopko_centralrepo-bugfix.md
Log File: docs/plans/2026-05-28_Jeff-Kopko_centralrepo-bugfix.log.md

## Goal
Fix confirmed bugs, remove dead code, and apply targeted improvements to CentralRepo based on
a full multi-agent review. All changes tested in dev (via fortihugorunner) before promoting to main.

## Context / Links
- Hugo version: 0.162.1 (latest, auto-updates)
- Related repos: UserRepo, TEC-analytics (dev harness)
- Review findings: conversation on 2026-05-28

## Constraints / Assumptions
- `google_analytics_authorMode.html` must NOT be deleted — `hugoServer_authorMode.sh` renames it to `google_analytics.html` at dev startup
- `quizframe.html` must NOT be deleted — it is the CTF quiz app iframe shortcode (not quizdown)
- `launchdemoform.html` is used by some live workshops; fix bugs but do not remove
- `Xperts2024` banner shortcode exists and should be wired in (event content may still be in use)
- Changes to the committed Dockerfile are in scope; test path via fortihugorunner before promoting
- ORIGIN_OK guard: removing it (dead code) rather than wiring it in — restricting to one origin would break workshops on non-GitHub-Pages hosts; CORS on the TEC-analytics API is the correct enforcement boundary

## Plan

### Phase 1 — Build-breaking fixes (must fix first)

- [ ] **B1.** Replace `htmlEscape` with `html.EscapeString` in `layouts/partials/silent_cross_site_checkin.html`
  - `htmlEscape` was removed in Hugo 0.121; current version is 0.162.1 — this breaks the build
- [ ] **B10.** Fix `[Langauges]` typo → `[Languages]` in `hugo.toml` (silently nullifies `landingPageName`)
- [ ] **B11.** Fix `defaultContentLanguageInSubdir = "false"` → `false` (unquoted boolean) in `hugo.toml`

### Phase 2 — Dead code removal

- [ ] Delete `layouts/partials/orig_analytics_checkin.html` (no refs anywhere)
- [ ] Delete `layouts/partials/orig_google_analytics .html` (no refs; trailing space in filename)
- [ ] Delete `layouts/shortcodes/carousel.html` (not used in UserRepo or any live content; tiny-slider never loaded)
- [ ] Delete `layouts/shortcodes/quizdown.html` (quizdown replaced by CTF quiz app)
- [ ] Remove quizdown CDN scripts from `layouts/partials/custom-header.html` (lines ~319-328: 3 CDN script tags + init call)
- [ ] Update README.md and `.github/copilot-instructions.md` to remove quizdown and carousel references
- [ ] Remove `ORIGIN_OK` dead variable from `layouts/partials/silent_cross_site_checkin.html` (computed but never used)

### Phase 3 — High-impact bug fixes

- [ ] **B3.** Fix `videoHeaderSrc` in `hugo.toml` → `"/videos/CloudsAnimated.mp4"` (Alkira file doesn't exist)
- [ ] **B4.** Fix Xperts CSS background image paths: `url("../images/...")` → `url("/images/...")` in both
  - `assets/css/theme-Xperts2024.css`
  - `assets/css/theme-Xperts2025.css`
- [ ] **B5.** Strip `<!DOCTYPE html>` / `<head>` / `<body>` wrappers from three shortcodes (keep inner content only):
  - `layouts/shortcodes/ContainerFlow.html`
  - `layouts/shortcodes/FTNThugoFlow.html`
  - `layouts/shortcodes/fortihugorunner.html`
- [ ] **B2.** Fix `launchdemoform.html` false-success on error: wire in the real error status messages in both the non-202 branch and the catch block
- [ ] **B6 resolved by Phase 2** — carousel removed

### Phase 4 — Medium bug fixes

- [ ] **B7.** Fix banner shortcode fallback params: `line1/2/3` should default to `.Get 0`, `.Get 1`, `.Get 2` respectively in both `Xperts24Banner.html` and `Xperts25Banner.html`
- [ ] **B8.** Replace `<img1>` with `<div>` in `ContainerFlow.html` (invalid HTML element)
- [ ] **B9.** Add Xperts2024 banner case to `content-header.html` (oversight; Xperts24Banner shortcode exists but is never rendered)
- [ ] **B12 resolved by Phase 2** — `orig_analytics_checkin.html` deleted
- [ ] **T12.** Add `return` after `window.location.href` assignment in `google_analytics.html` to stop GTM loading during redirect

### Phase 5 — Deprecation fixes

- [ ] **T1.** Replace `getenv "HUGO_VERSION_TAG"` → `os.Getenv "HUGO_VERSION_TAG"` in `layouts/partials/copyright.html`
- [ ] **T2.** Replace `substr` → `strings.SliceString` in `layouts/shortcodes/quizframe.html`

### Phase 6 — Tech debt / improvements

- [ ] **T3/I2.** Move Azure webhook URL to site param in `launchdemoform.html` — read from `site.Params.webhookUrl`, fallback to current hardcoded value so existing workshops are unaffected without repoConfig.json change
- [ ] **T5 resolved by Phase 2** — `ORIGIN_OK` removed
- [ ] **T9.** Delete `static/css/theme-CloudCSEMovie.css` (duplicate of `assets/css/theme-CloudCSEMovie.css`)
- [ ] **T13.** Add `**/.DS_Store` to `.gitignore`; remove committed `.DS_Store` files
- [ ] **I1.** Change `analyticsBaseUrl` fallback in `analytics_checkin.html` from hardcoded prod URL to `""` — so the dev harness only needs `repoConfig.json` updates, not in-place file mutations
- [ ] **I4.** Conditionally load quizframe CSS (if any) only when `quizframe` shortcode is used via `page.HasShortcode`
- [ ] **I5.** Add `LOCAL` build arg to Dockerfile — `COPY . /home/CentralRepo` path for local builds vs `ADD https://github.com/...` for CI, making the divergence from fortihugorunner's local path explicit and documented

### Phase 7 — Verify

- [ ] Run `fortihugorunner launch-server` against UserRepo — confirm site builds and serves without errors
- [ ] Check browser console: no JS errors on home page (analytics check-in), quiz page (quizframe), non-home page (GA redirect)
- [ ] Confirm Xperts2025 background image renders on a page using that theme variant
- [ ] Confirm quizdown scripts are gone from page source

## Decisions & Commentary
- `google_analytics_authorMode.html` — KEEP. `hugoServer_authorMode.sh` mv's it into place. If we delete it, dev server mode breaks.
- `ORIGIN_OK` — remove (dead code) rather than wire in. Restricting to one origin would break workshops on non-GitHub-Pages hosts. CORS on the API is the right enforcement boundary.
- Quizdown — remove `quizdown.html` shortcode + CDN scripts. Keep `quizframe.html` (CTF app).
- Carousel — remove shortcode (no live usage, library never loaded).
- `launchdemoform.html` webhook URL — move to site param with backward-compat fallback so live workshops aren't broken without config change.
- Xperts2024 banner — add the missing case to `content-header.html` (oversight per user).

## Files Changed
- (to be filled during implementation)

## Session Summary
- (to be filled at end)

## Follow-ups
- [ ] Confirm `tags.html` partial is provided by the pinned Relearn theme version (B13)
- [ ] Consider pinning Relearn submodule version explicitly in `.gitmodules`
- [ ] `T4` (`customer: '1234'` / `smartticket: '5678'` stubs in launchdemoform) — confirm with stakeholder whether these are intentional or need real values

## Risks / Open Questions
- B5 (stripping document wrappers from ContainerFlow/FTNThugoFlow/fortihugorunner shortcodes): mxgraph viewer JS is inline; confirm it still renders correctly after wrapper removal
- I5 (Dockerfile LOCAL build arg): needs testing end-to-end with fortihugorunner before promoting

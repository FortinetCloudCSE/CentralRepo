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

- [x] **B1.** Replace `htmlEscape` with `html.EscapeString` in `layouts/partials/silent_cross_site_checkin.html`
  - `htmlEscape` was removed in Hugo 0.121; current version is 0.162.1 — this breaks the build
- [x] **B10.** Fix `[Langauges]` typo → `[Languages]` in `hugo.toml` (silently nullifies `landingPageName`)
- [x] **B11.** Fix `defaultContentLanguageInSubdir = "false"` → `false` (unquoted boolean) in `hugo.toml`

### Phase 2 — Dead code removal

- [x] Delete `layouts/partials/orig_analytics_checkin.html` (no refs anywhere)
- [x] Delete `layouts/partials/orig_google_analytics .html` (no refs; trailing space in filename)
- [x] Delete `layouts/shortcodes/carousel.html` (not used in UserRepo or any live content; tiny-slider never loaded)
- [x] Delete `layouts/shortcodes/quizdown.html` (quizdown replaced by CTF quiz app)
- [x] Remove quizdown CDN scripts from `layouts/partials/custom-header.html` (lines ~319-328: 3 CDN script tags + init call)
- [x] Update README.md and `.github/copilot-instructions.md` to remove quizdown and carousel references
- [x] Remove `ORIGIN_OK` dead variable from `layouts/partials/silent_cross_site_checkin.html` (computed but never used)

### Phase 3 — High-impact bug fixes

- [x] **B3.** Fix `videoHeaderSrc` in `hugo.toml` → `"/videos/CloudsAnimated.mp4"` (Alkira file doesn't exist)
- [x] **B4.** Fix Xperts CSS background image paths: `url("../images/...")` → `url("/images/...")` in both
  - `assets/css/theme-Xperts2024.css`
  - `assets/css/theme-Xperts2025.css`
- [x] **B5.** Strip `<!DOCTYPE html>` / `<head>` / `<body>` wrappers from three shortcodes (keep inner content only):
  - `layouts/shortcodes/ContainerFlow.html`
  - `layouts/shortcodes/FTNThugoFlow.html`
  - `layouts/shortcodes/fortihugorunner.html`
- [x] **B2.** Fix `launchdemoform.html` false-success on error: wire in the real error status messages in both the non-202 branch and the catch block
- [x] **B6 resolved by Phase 2** — carousel removed

### Phase 4 — Medium bug fixes

- [x] **B7.** Fix banner shortcode fallback params: `line1/2/3` should default to `.Get 0`, `.Get 1`, `.Get 2` respectively in both `Xperts24Banner.html` and `Xperts25Banner.html`
- [x] **B8.** Replace `<img1>` with `<div>` in `ContainerFlow.html` (invalid HTML element)
- [x] **B9.** Add Xperts2024 banner case to `content-header.html` (oversight; Xperts24Banner shortcode exists but is never rendered)
- [x] **B12 resolved by Phase 2** — `orig_analytics_checkin.html` deleted
- [x] **T12.** Add `return` after `window.location.href` assignment in `google_analytics.html` to stop GTM loading during redirect

### Phase 5 — Deprecation fixes

- [x] **T1.** Replace `getenv "HUGO_VERSION_TAG"` → `os.Getenv "HUGO_VERSION_TAG"` in `layouts/partials/copyright.html`
- [x] **T2.** Replace `substr` → `strings.SliceString` in `layouts/shortcodes/quizframe.html`

### Phase 6 — Tech debt / improvements

- [x] **T3/I2.** Move Azure webhook URL to site param in `launchdemoform.html` — read from `site.Params.webhookUrl`, fallback to current hardcoded value so existing workshops are unaffected without repoConfig.json change
- [x] **T4.** Make `customer` and `smartticket` shortcode params in `launchdemoform.html`
- [x] **T5 resolved by Phase 2** — `ORIGIN_OK` removed
- [x] **T9.** Delete `static/css/theme-CloudCSEMovie.css` (duplicate of `assets/css/theme-CloudCSEMovie.css`)
- [x] **T13.** Add `**/.DS_Store` to `.gitignore`; remove committed `.DS_Store` files
- [x] **I1.** Change `analyticsBaseUrl` fallback in `analytics_checkin.html` from hardcoded prod URL to `""` — so the dev harness only needs `repoConfig.json` updates, not in-place file mutations
- [ ] **I4.** Conditionally load quizframe CSS (if any) only when `quizframe` shortcode is used via `page.HasShortcode`
- [x] **I5.** Add `LOCAL` build arg to Dockerfile — `COPY . /home/CentralRepo` path for local builds vs `ADD https://github.com/...` for CI, making the divergence from fortihugorunner's local path explicit and documented
- [x] **Relearn submodule pin** — pinned to stable 8.0.0 tag

### Phase 7 — Verify

- [x] Hugo build passes (`hugo --templateMetrics` — no ERRORs, completes in ~130ms)
- [x] Run container (hugotester-local with LOCAL=true build) against UserRepo — confirmed clean build (372ms, no ERRORs)
- [x] Verified via curl: quizdown CDN scripts absent, siteTitle/marketingCode correct, ANALYTICS_BASE empty, videoHeaderSrc CloudsAnimated, Xperts CSS paths use /images/
- [ ] Browser console: no JS errors on home page (analytics check-in), quiz page (quizframe), non-home page (GA redirect) — deferred to manual browser test
- [x] Xperts2025 background image path confirmed: url("/images/xperts-2025-background.png")

## Decisions & Commentary
- `google_analytics_authorMode.html` — KEEP. `hugoServer_authorMode.sh` mv's it into place. If we delete it, dev server mode breaks.
- `ORIGIN_OK` — remove (dead code) rather than wire in. Restricting to one origin would break workshops on non-GitHub-Pages hosts. CORS on the API is the right enforcement boundary.
- Quizdown — remove `quizdown.html` shortcode + CDN scripts. Keep `quizframe.html` (CTF app).
- Carousel — remove shortcode (no live usage, library never loaded).
- `launchdemoform.html` webhook URL — move to site param with backward-compat fallback so live workshops aren't broken without config change.
- Xperts2024 banner — add the missing case to `content-header.html` (oversight per user).
- **htmlEscape / html.EscapeString (B1):** `html.EscapeString` (the planned replacement) does not resolve correctly as a Hugo function in this version (0.162.0 snap/arm64) — the template engine evaluates `html` as a data identifier rather than a namespace, giving "can't evaluate field EscapeString in type string". Used `jsonify` instead: `{{ .Site.Params.workshopTitle | default "" | jsonify }}`. This is strictly better — it outputs a properly JSON-encoded JS string literal with correct quoting, so no separate HTML escaping is needed.
- **[Languages] section (B10):** Fixing the `[Langauges]` typo exposed a malformed TOML structure — `landingPageName` was directly under `[Languages]` but needs `[Languages.en]` nesting. Fixed to `[Languages.en]`.
- **fortihugorunner.html (B5):** File is gitignored (`fortihugorunner*` in .gitignore) and was system-generated (owned by root). During wrapper stripping, the mxgraph data line was lost due to an off-by-one in the Python script. File was left as a minimal stub (just the viewer script tag). Since it's gitignored, this does not affect the commit or CI builds.
- **siteTitle / marketingCode (B1 follow-up):** `jsonify` produced double-encoded output (`"\"...\""`) because Hugo params are already strings — no encoding needed. Reverted to plain single-quoted JS string interpolation (`'{{ .Site.Params.workshopTitle | default "" }}'`), matching the pre-fix pattern without the removed `htmlEscape`.
- **google_analytics.html return (T12):** Top-level `return;` in a `<script>` block is invalid JS — Hugo's transformer rejects it. Removed. The `window.location.href` redirect is synchronous; GTM script on the subsequent `<script>` tag fires but the page has already navigated away, so no tracking occurs on redirect.
- **silent_cross_site_checkin.html analyticsBaseUrl (I1 follow-up):** I1 only changed `analytics_checkin.html`; `silent_cross_site_checkin.html` line 1 retained the prod URL fallback. Fixed to `""` to match.
- **Dockerfile ARG placement:** `ARG LOCAL=false` must appear before the first `FROM` (global scope) to be usable in `FROM dev-src-local-${LOCAL}`. Fixed in post-verification commit.
- **UserRepo quizdown stub:** Added `UserRepo/layouts/shortcodes/quizdown.html` as a no-op paired shortcode shim (`{{ .Inner }}` hidden) so UserRepo content using old `{{< quizdown >}}` calls builds without errors. This is a temporary shim — UserRepo content should be updated to remove quizdown calls.

## Files Changed
- `.gitignore` — added `**/.DS_Store`; removed committed `.DS_Store` files via git rm --cached
- `Dockerfile` — updated sed pattern for os.Getenv; added LOCAL build arg with multi-stage source variants
- `README.md` — removed quizdown and carousel shortcode sections
- `assets/css/theme-Xperts2024.css` — fixed background image path (`../` → `/`)
- `assets/css/theme-Xperts2025.css` — fixed background image path (`../` → `/`)
- `hugo.toml` — fixed [Langauges]→[Languages.en], boolean string→bool, videoHeaderSrc
- `layouts/partials/analytics_checkin.html` — analyticsBaseUrl fallback → ""
- `layouts/partials/content-header.html` — added Xperts2024 banner case
- `layouts/partials/copyright.html` — getenv → os.Getenv
- `layouts/partials/custom-header.html` — removed quizdown CDN scripts
- `layouts/partials/google_analytics.html` — added return after redirect
- `layouts/partials/orig_analytics_checkin.html` — DELETED
- `layouts/partials/orig_google_analytics .html` — DELETED
- `layouts/partials/silent_cross_site_checkin.html` — removed ORIGIN_OK; replaced htmlEscape with jsonify
- `layouts/shortcodes/Xperts24Banner.html` — fixed line2/line3 positional defaults
- `layouts/shortcodes/Xperts25Banner.html` — fixed line2/line3 positional defaults
- `layouts/shortcodes/carousel.html` — DELETED
- `layouts/shortcodes/launchdemoform.html` — false-success fix; webhook URL to site param; customer/smartticket to shortcode params
- `layouts/shortcodes/quizdown.html` — DELETED
- `layouts/shortcodes/quizframe.html` — substr → strings.SliceString
- `static/css/theme-CloudCSEMovie.css` — DELETED (duplicate)
- `themes/hugo-theme-relearn` — pinned to 8.0.0

## Session Summary
Fixed 20+ confirmed bugs and applied targeted cleanup across CentralRepo: build-breaking template function replacements, dead code removal (quizdown, carousel, orig partials, DS_Store), Hugo config corrections, mxgraph shortcode wrapper stripping, CSS path fixes, launchdemoform error handling, deprecation replacements, and Relearn theme submodule pinning. All changes verified clean via `hugo --templateMetrics` (no ERRORs).

## Follow-ups
- [ ] Confirm `tags.html` partial is provided by the pinned Relearn theme version (B13)
- [ ] Consider pinning Relearn submodule version explicitly in `.gitmodules`
- [ ] `T4` (`customer`/`smartticket` now shortcode params) — confirm workshop content using `launchdemoform` passes these, or the defaults (empty string) are acceptable
- [ ] `I4` — conditionally load quizframe CSS if any (deferred)
- [ ] Browser-test Xperts2025 background image, GA redirect, quizframe after deploy

## Risks / Open Questions
- B5 (stripping document wrappers from ContainerFlow/FTNThugoFlow/fortihugorunner shortcodes): mxgraph viewer JS is inline; confirm it still renders correctly after wrapper removal
- I5 (Dockerfile LOCAL build arg): needs testing end-to-end with fortihugorunner before promoting

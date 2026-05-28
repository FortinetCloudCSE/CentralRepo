# CentralRepo Release Notes

---

## [Unreleased]

### CloudCSEMovie Theme — MP4 Video Sidebar Header

Added a new Hugo theme variant `CloudCSEMovie` that plays an MP4 video in the sidebar header area in place of a static background image.

**Features**
- Video plays automatically on page load (muted, no controls)
- Configurable loop interval: video plays once, pauses, then replays. A 6-second clip with a 60-second interval plays once, waits 54 seconds, then plays again
- Search bar repositioned below the video and the red divider line, sitting on the dark nav background
- All other header content (logo, banner text) renders on top of the video
- Falls back to a solid color header if `videoHeaderSrc` is left empty

**Configuration** — set in each repo's `scripts/repoConfig.json`:
```json
{
  "themeVariant": "CloudCSEMovie",
  "videoHeaderSrc": "/videos/CloudsAnimated.mp4",
  "videoHeaderInterval": 60
}
```
- `videoHeaderSrc`: URL path relative to site root (no leading `/` needed — generated automatically). Leave blank to disable video.
- `videoHeaderInterval`: Total seconds between play cycles. Optional; defaults to `60`.

**Video asset** — shared MP4 lives in `static/videos/` of CentralRepo (the Hugo root for all repo builds), so one file is available to every repo.

**Files changed**
| File | Change |
|------|--------|
| `assets/css/theme-CloudCSEMovie.css` | New theme CSS — video positioning, search bar below divider |
| `static/css/theme-CloudCSEMovie.css` | Static copy served directly by Hugo (bypasses asset pipeline) |
| `layouts/partials/custom-header.html` | Conditional `<video>` injection via JS data-attribute pattern |
| `scripts/templates/hugo.jinja` | `videoHeaderSrc` / `videoHeaderInterval` params in generated `hugo.toml` |
| `scripts/repoConfig.json` | New params with defaults; CentralRepo set to CloudCSEMovie theme |
| `static/videos/CloudsAnimated.mp4` | Shared video asset |
| `README.md` | Theme variants table + CloudCSEMovie setup documentation |

**Final layout**
- Video is injected into `#R-header` (the logo div), not `#R-header-wrapper`. This keeps the search bar completely out of our code — it sits below `#R-header` in normal DOM flow, unaffected by the video injection.
- `#R-header-wrapper` padding is zeroed so `#R-header` fills edge-to-edge with no red background gaps on the borders.
- JS sets an explicit pixel height on `#R-header` (`naturalHeight + 3rem`) before inserting the video. This is required because `<video>` is a replaced element — `height: 100%` only resolves against an explicit height on the containing block; without it the browser falls back to intrinsic aspect-ratio sizing.

**Technical notes**
- Hugo's `html/template` JS-context escaping causes double-encoding of string params inside `<script>` blocks. Fixed by passing the video path via an HTML `data-` attribute and reading it with `getAttribute()` in JS.
- Hugo's `relURL` only prepends the site base path for paths without a leading slash. Fixed with `strings.TrimPrefix "/" . | relURL` to produce the correct `/UserRepo/videos/...` path.
- Theme CSS must exist in `static/css/` to be served at `css/theme-*.css` as the relearn theme stylesheet partial expects.
- The relearn v8 theme compiles all variant CSS into `css/format-html.css` using CSS nesting and `data-r-theme-variant` attribute selectors — there is no separate per-variant CSS link element. Our `static/css/theme-CloudCSEMovie.css` is served statically as a fallback reference but the active styles come from the compiled bundle.

### Repository hygiene

- Added `hugo.toml`, `CLAUDE.md`, and local draw.io diagram exports to `.gitignore`. `hugo.toml` is auto-generated at container startup; these files should never be committed.

---

## Bug Fixes, Deprecation Fixes, and Cleanup — 2026-05-28

Full multi-agent review of CentralRepo followed by targeted fixes. Plan and log: `docs/plans/2026-05-28_Jeff-Kopko_centralrepo-bugfix.md`

### Build-Breaking Fixes
- **`htmlEscape` removed in Hugo 0.121+** (`silent_cross_site_checkin.html`): replaced with `jsonify` pipe for JS-safe string output, which is also more correct for the JS context
- **`[Langauges]` typo** in `hugo.toml`/`hugo.jinja`: corrected to `[Languages]`; also fixed `landingPageName` nesting to `[Languages.en]`
- **`defaultContentLanguageInSubdir = "false"`**: fixed to unquoted TOML boolean `false`

### Dead Code Removed
- Deleted `layouts/partials/orig_analytics_checkin.html` and `layouts/partials/orig_google_analytics .html` (trailing space in filename) — both unreferenced
- Deleted `layouts/shortcodes/quizdown.html` and quizdown CDN scripts from `custom-header.html` — replaced by CTF quiz app (`quizframe` shortcode)
- Deleted `layouts/shortcodes/carousel.html` — unused; tiny-slider library was never loaded
- Deleted `static/css/theme-CloudCSEMovie.css` — exact duplicate of `assets/css/` version
- Removed dead `ORIGIN_OK` variable from `silent_cross_site_checkin.html`

### Bug Fixes
- **Xperts CSS background images** (`theme-Xperts2024.css`, `theme-Xperts2025.css`): fixed `url("../images/...")` → `url("/images/...")` — images were invisible due to broken relative path
- **`launchdemoform.html` false success on error**: else branch and catch block now return real HTTP/network error messages instead of the false "Provisioning request accepted" message
- **`launchdemoform.html` hardcoded stubs**: `customer` and `smartticket` promoted to shortcode params (`.Get "customer"`, `.Get "smartticket"`); webhook URL moved to `site.Params.webhookUrl` with backward-compatible fallback
- **`videoHeaderSrc`** in `hugo.toml`/`hugo.jinja`: fixed nonexistent `Alkira cover dynamic.mp4` reference → `CloudsAnimated.mp4`
- **Xperts banner shortcodes**: fixed `line2` and `line3` params both defaulting to `.Get 0`; now `.Get 1` and `.Get 2`
- **Xperts2024 banner missing**: added `Xperts2024` case to `content-header.html` (was oversight — shortcode existed but was never rendered)
- **`<img1>` invalid element** in `ContainerFlow.html`: replaced with `<div class="img1">`
- **Nested HTML documents** in shortcodes: stripped `<!DOCTYPE html>`, `<head>`, and `<body>` wrappers from `ContainerFlow.html` and `FTNThugoFlow.html`
- **`analytics_checkin.html` email regex**: escaped `%`, `+`, `.` inside character classes for Chrome v-flag (Unicode sets) compatibility — was throwing `SyntaxError: Invalid regular expression` in Chrome 119+
- **`quizframe.html` iframe**: removed invalid `allow="same-origin"` (not a Permissions Policy feature) and `sandbox` attribute (`allow-scripts + allow-same-origin` combination defeats sandboxing and triggers browser security warning)
- **GA in author mode**: `google_analytics_authorMode.html` was loading the full GTM script, causing GA fetch failures on every page in dev. Suppressed GA entirely in author mode.

### Deprecation Fixes
- `getenv` → `os.Getenv` in `copyright.html` (deprecated Hugo 0.91)
- `substr` → `strings.SliceString` in `quizframe.html` (deprecated Hugo 0.100)
- `languageCode` → `locale` in `hugo.jinja` template (deprecated Hugo 0.158)
- `disableSearch = false` → `search.disable = false` in `hugo.jinja` (Relearn 8.0.0 migration)
- `math = false` → `math.disable = true` in `hugo.jinja` (Relearn 8.0.0 migration)

### Improvements
- **`analyticsBaseUrl` fallback**: changed from hardcoded prod URL to `""` in both `analytics_checkin.html` and `silent_cross_site_checkin.html` — dev harness now only needs to update `repoConfig.json`, not patch template files
- **Relearn submodule**: pinned to stable `8.0.0` tag (was on an untagged dev commit)
- **Dockerfile `LOCAL` build arg**: added `ARG LOCAL=false` at global scope enabling `COPY . /home/CentralRepo` path for local builds vs `ADD https://github.com/...` for CI
- **`.DS_Store`**: added to `.gitignore`; removed 5 committed `.DS_Store` files
- **`docs/plans/`**: created plan and log files for this session (`2026-05-28_Jeff-Kopko_centralrepo-bugfix.md`)

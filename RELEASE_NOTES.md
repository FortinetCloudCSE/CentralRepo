# CentralRepo Release Notes

---

## [Unreleased]

### feat(layout): move Version/Revision/Last Updated to navbar footer

Version, Revision, and Last Updated info was previously shown only on the home page content footer alongside the legal copyright block. It is now displayed in the left navbar footer (below the Privacy | Site Terms | About Us links) on every page, giving readers consistent access to version info regardless of which page they are on.

The legal copyright text remains in the home page content footer unchanged.

**Files changed**
| File | Change |
|------|--------|
| `layouts/partials/menu-footer.html` | Added version/revision/last-updated block; changed `#footer` height from fixed `6.25rem` to `auto` |
| `layouts/partials/copyright.html` | Removed version/revision/last-updated block; copyright text only |

---

### fix(theme): CloudCSEMovie video default when `videoHeaderSrc` omitted from repoConfig

Repos using `themeVariant: "CloudCSEMovie"` without an explicit `videoHeaderSrc` in `repoConfig.json` (e.g. AWS-FGT-301) got a blank header — the Jinja template only emitted `videoHeaderSrc` into `hugo.toml` when explicitly set, so Hugo never saw the param and no `<video>` element was injected.

The Jinja template now defaults `videoHeaderSrc` to `/videos/CloudsAnimated.mp4` (already bundled in `static/videos/`) when `themeVariant == "CloudCSEMovie"` and no explicit override is provided. `videoHeaderInterval` also defaults to `60` when omitted. Repos on other themes are unaffected. Repos with an explicit `videoHeaderSrc` continue to use their value.

**Files changed**
| File | Change |
|------|--------|
| `scripts/templates/hugo.jinja` | Default `videoHeaderSrc`/`videoHeaderInterval` for CloudCSEMovie variant |

---

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

### CI — binfmt warnings, test failures, Hugo deprecations, Node.js 20 actions

Full remediation of all CI warnings and test failures across all five workflows.

#### binfmt cache warnings (`Failed to save: Unable to reserve cache with key docker.io--tonistiigi--binfmt-latest-linux-x64`)

Root cause pattern: Docker initialization tries to write an immutable GitHub Actions cache key that already exists, or two jobs race to create the same key simultaneously. Three sources:

- `Dockerfile` — updated syntax directive `docker/dockerfile:1.5-labs` → `docker/dockerfile:1` (stable). The labs directive caused BuildKit to initialize QEMU/binfmt multi-platform support on every build, triggering the cache write. The `ADD https://…git#branch` feature used in the file graduated from labs in Dockerfile 1.6 and is covered by the stable tag.
- `.github/workflows/ci.yml` — added `needs: [hugo-build]` to `hugo-build-no-analytics-url`. Both jobs use `container: image: hugomods/hugo:std`; running in parallel, GitHub's Docker setup raced to create the same binfmt cache key. Serializing eliminates the race without changing CI outcome — `assert-html` already waits for both.
- `.github/workflows/static.yml` — removed `docker system prune` and `docker builder prune -f`. GitHub-hosted runners are ephemeral (fresh Docker state per job); both steps were pointless, and the builder prune forced BuildKit re-initialization every run.
- `.github/workflows/image-build-push-dev.yaml` and `image-build-push-prod.yaml` — added `cache-image: false` to `docker/setup-qemu-action`. The default `cache-image: true` restores binfmt from cache, pulls Docker Hub to check for updates, then tries to re-write the immutable cache key → warning on every run. Also removed `docker system prune` (pointless on ephemeral runners) from both files.

#### CI test failures

**Test A2** (`checkin form action is not the expected absolute URL`) — persistent failure, never passed since the test was added.

Root cause: `{{ $analyticsBase }}` in `analytics_checkin.html` was inside a JavaScript backtick template literal inside a `<script>` block. Go's `html/template` JS-context escaping wraps string values in JSON quotes in that context, producing `action=""https://..."/checkin"` instead of `action="https://..."/checkin"`. Same root cause as the video header `data-` attribute fix (documented in CLAUDE.md).

Fix:
- `layouts/partials/analytics_checkin.html` — moved all Hugo template params (`$analyticsBase`, `$marketingCode`, `$workshopID`, `$workshopTitle`, `$quizUrl`) to `data-*` attributes on `<div id="display-form">`, read with `getAttribute()` in JS. HTML attribute context renders correctly; JS `${VAR}` interpolation injects values inside the backtick literal at runtime. Also fixes `$quizUrl` which had the same silent escaping issue.
- `scripts/test/test_rendered_html.sh` — updated test A2 to check `data-analytics-base="https://tecanalytics.forticloudcse.com"` (the HTML attribute, which is the rendered source of truth) instead of the dynamically-set form `action` attribute.

**Test A11** (`htmlEscape found in layout source`) — introduced when creating `layouts/_default/baseof.html` as a theme override; the file was copied from the theme which still uses `htmlEscape`.

Fix: replaced `htmlEscape` → `transform.HTMLEscape` in `layouts/_default/baseof.html` (the correct Hugo 0.121+ replacement).

#### Hugo deprecation WARNs (v0.156–0.158)

`hugo-theme-relearn` 8.x and 9.x have not fixed these upstream. Created 11 override files in `layouts/` (standard Hugo theme override mechanism) with targeted substitutions:

| Deprecated | Replacement |
|---|---|
| `.Language.LanguageCode` | `.Language.Locale` |
| `.Language.LanguageDirection` | `.Language.Direction` |
| `$site.Sites` / `site.Sites` | `hugo.Sites` |

Overridden files: `layouts/_default/baseof.html`, `layouts/404.html`, `layouts/_default/rss.xml`, `layouts/_default/sitemap.xml`, `layouts/partials/opengraph.html`, `layouts/partials/dependencies/search-lunr.html`, `layouts/partials/topbar/button/prev.html`, `layouts/partials/topbar/button/next.html`, `layouts/partials/_relearn/linkObject.gotmpl`, `layouts/partials/_relearn/pageLangPath.gotmpl`.

`layouts/partials/sidebar/element/languageswitcher.html` required a different approach: `(index hugo.Sites 0).Languages` still accesses the deprecated `.Languages` field on a Site object and triggers the same warning. The variable was only used for a redundant `> 1` count check — `hugo.IsMultilingual` already guarantees multiple languages exist — so the variable was dropped and the condition simplified.

`layouts/partials/old_menu.html` — deleted. Dead code with no references, and its `.Site.Languages` call was generating the deprecation warning.

#### Node.js 20 action warnings

- `actions/upload-artifact@v4` → `@v7` — v4 compiled against Node.js 20. Note: v5.0.0 release notes claimed Node.js 24 support but the runner still reported Node.js 20; v7 is confirmed Node.js 24.
- `actions/download-artifact@v4` → `@v7` — same, confirmed Node.js 24 at v7.

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

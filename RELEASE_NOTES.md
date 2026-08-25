# CentralRepo Release Notes

---

## [Unreleased]

### feat(shortcodes): launchdemoform — real progress, on-page credentials, single-attempt lock

`launchdemoform` no longer POSTs `mode:'no-cors'` to the raw Azure Automation webhook and waits for an email that may not arrive in time. It now calls the new `fortinet-on-demand-labs-provisioning-and-tracking` Durable Function API with a normal, readable `fetch`, polls a status endpoint every 4-20s (backing off on repeated identical status), and renders a progress bar + step label while provisioning runs. On success it renders a credential card (username, sign-in info, resource group, expiry, Azure portal link) directly on the page instead of relying on email as the only delivery path.

Attempt state (status, poll token, credentials) persists in `localStorage` — survives tab/browser closure, since a provisioned credential is only ever valid for the lab's own short duration regardless of how long a browser stays open — keyed under `window.relearn.absBaseUri` plus the `lab` value, the same site-scoping convention the deployment-path gate uses, so a reload resumes an in-flight attempt or shows the stored credential card without a new network call, and two different labs never share a lock. The button disables permanently once any attempt exists for that site+lab; only a stored `Failed` terminal status re-enables a "Retry Provisioning" button showing the prior failure reason. Once a credential's real `labDurationDays` has elapsed, the still-rendered card shows an inline "access window has ended" warning instead of presenting it as still good. This is a client-side convenience only — the backend's own idempotency key is the real guarantee against double-provisioning.

New optional site param `provisionApiBaseUrl` supplies the Function's base URL. Unset, the shortcode still renders and gates on check-in as before, but shows a "not configured" message on click rather than calling a nonexistent endpoint. Wiring it through `repoConfig.schema.json` and `scripts/templates/hugo.jinja` also closes a latent bug in the param it replaces: the old `webhookUrl` site param was read in `launchdemoform.html` but never emitted by `hugo.jinja` into `hugo.toml`, so every real build silently used the hardcoded webhook default regardless of what a repo configured.

The `/api/provision/start` and `/api/provision/status/{token}` contract is confirmed live against the real deployed backend (`fortinet-on-demand-labs-provisioning-and-tracking`), not just documented as an assumption — two real field-name mismatches surfaced during that testing and are fixed: the start payload sends `email` (not `useremail`), and the success response's field mapping (`normalizeCredential()`) now matches the backend's actual `credential`/`userPrincipalName`/`temporaryAccessPass`/`resourceGroups` shape rather than a guessed one. Full real end-to-end success — including on the live published `fortiweb-api-mcp-protection` site — is confirmed for 2 of the org's 10 real lab definitions as of 2026-08-25; the rest are still unverified. See `docs/plans/2026-08-24_Jeff-Kopko_launchdemoform-rebuild.md` (Status: Complete) for the full history.

**Files changed**
| File | Change |
|------|--------|
| `layouts/shortcodes/launchdemoform.html` | Full rework: JSON `fetch` to the new API, poll loop with backoff, progress UI, credential card, localStorage-backed single-attempt lock and retry-after-failure, expiry-aware credential display |
| `scripts/repoConfig.schema.json` | Add optional `provisionApiBaseUrl` |
| `scripts/templates/hugo.jinja` | Emit `provisionApiBaseUrl` into `hugo.toml` when set |
| `README.md` | Rewrite the `launchdemoform` section; document the new site param |

### ci(image): pin the Hugo base image and stop rebuilding on docs-only pushes

Two independent ways a CentralRepo merge could hand all 65 workshop repos an unintended change are now closed.

`Dockerfile` pinned `hugomods/hugo:std` → `hugomods/hugo:std-0.165.0`. The floating tag meant the Hugo version inside `fortinet-hugo:latest` was whatever upstream had published most recently at build time, decided by *when* someone merged rather than by any decision in this repo — observed live on 2026-08-19, when a merge moved the published image from Hugo 0.164.0 to 0.165.0 with nothing in the diff asking for it. 0.165.0 is what production already runs, so the pin changes no behaviour today; it only makes the next Hugo bump an explicit, reviewable commit. Pinning the base also pins Alpine, so the `apk add python3 py3-pip tini-static` layer stops drifting too.

`image-build-push-prod.yaml` and `image-build-push-dev.yaml` gained matching `paths-ignore` lists. Neither had one, so a README- or docs-only merge rebuilt and republished `latest` to every consumer. The list covers only paths that are provably not baked into the image — root-level `*.md`, `docs/**`, `review/**` and the three licence files. Everything under `scripts/`, `layouts/`, `assets/`, `i18n/`, `static/`, `archetypes/`, `themes/` and the `Dockerfile` itself does reach the image and is deliberately absent from the list.

Known consequence, accepted: `versioning.yml` still runs on every push to `main` and is intentionally left without `paths-ignore`, so a docs-only push still cuts a `vYY.Q.<letter>` tag and GitHub release. Image version letters can therefore skip — a tag can exist with no image built for it. Tagging a docs release is defensible and unifying the two is a separate decision.

**Files changed**
| File | Change |
|------|--------|
| `Dockerfile` | Pin base image to `hugomods/hugo:std-0.165.0`, with a comment on why and how to bump |
| `.github/workflows/image-build-push-prod.yaml` | Add `paths-ignore` to the `push` trigger |
| `.github/workflows/image-build-push-dev.yaml` | Same `paths-ignore` |

### feat(shortcodes): single deployment path per reader — pathtabs / pathonly / deploymentPath

A reader picks Docker vs Kubernetes once and every page of the site follows that choice. This started as `pathtabs` / `pathtab` upstreamed from `ai-101` — previously a local copy there, now the only copy anywhere, and `local_copy.sh` no longer has a same-named repo-local file to shadow it with.

**The problem this exists to fix:** workshop participants were doing the Docker steps *and* the Kubernetes steps, because both tabs were on screen. Anything that leaves the other path reachable is the bug, so the gate is **default-deny for content**: until a path is chosen, no path's steps are visible anywhere on the site, and a page carrying a path block renders a blocking chooser instead. There is deliberately no default path.

**Everything is server-rendered and CSS-gated.** An inline synchronous `<script>` in `<head>` reads `localStorage[absBaseUri + '/deployment-path']` and sets `<html data-deployment-path>` before first paint — the same pre-paint pattern relearn uses for `themeVariant`. Every path's markup is emitted once and CSS reveals whichever matches. Nothing mutates the DOM after load, so there is no frame in which the wrong path is on screen. The corollary is that any per-path variation must be emitted once per path at build time, because there is one HTML output per page and the reader's path is known only client-side; that is why prev/next emits one button per path rather than resolving "the reader's path".

Three authoring forms, covered in the README with guidance on which to reach for:

- `pathtabs` / `pathtab` — alternatives to the same goal. Every declared path exactly once per block, or the build fails, so a reader can never be silently shown the other path's steps. Once a path is chosen the relearn tab nav is hidden and a `.pathlock__banner` reads `Your path: <VALUE>`; the switcher in `content-header.html` becomes the only control that writes the choice, so there is one control writing one state instead of two.
- `pathonly` — a standalone one-path block, for content with no counterpart. Nesting it inside a `pathtab` or another `pathonly` is an `errorf`: same key is redundant, different key is unreachable, and the second looks like working authoring until a reader reports missing steps.
- `deploymentPath` front matter — a whole page. This also removes the page from the other path's **sidebar** and from its **prev/next** walk, and renders a `.pathmiss` banner naming both paths with a switch button when a reader arrives anyway via a bookmark or a search result.

Hiding a page from the sidebar without also filtering prev/next would march the reader into a page the sidebar says does not exist, so `layouts/partials/pathnav/step.gotmpl` re-runs relearn's walk once per path. The sidebar selector is keyed on `permalink.gotmpl` — the partial `menu.html` itself builds `data-nav-id` from — not `.RelPermalink`, which omits the `index.html` that `disableExplicitIndexURLs = false` appends to every section page.

Two asymmetries worth knowing before extending this: **navigation is not default-deny** (with no choice stored, the sidebar and prev/next are the theme's own unfiltered behaviour, because a table of contents with pages silently missing reads as a broken build), and **every gate rule only ever hides** — sidebar `<li>`s and topbar buttons carry the theme's own responsive `display` rules, so re-asserting `display` for the active path would defeat them at small widths.

With JavaScript off, nothing sets the attribute and none of the gating applies: **all** paths render, stacked, with a `<noscript>` warning naming them in order. Failing open is deliberate — unreadable-but-complete beats silently empty. Print carries exactly one path.

Two new optional site params support it and close a long-standing build warning: `deploymentPaths` (the path vocabulary) and `errorignore` (a list of regexes relearn has always honoured but CentralRepo never emitted — it suppresses the local-URL warning for non-page targets like a PDF, where the suggested `pageRef` does not apply). Both are omitted from `hugo.toml` entirely when absent.

`scripts/static.yml` also becomes the canonical workshop-repo workflow template rather than a copy of CentralRepo's own image build.

**Blast radius:** merging to `main` rebuilds the prod ECR image that ~65 workshop repos build against. `deploymentPaths` is absent from all but `ai-101`, and without it the whole mechanism is inert — no gate script, no gate CSS, one unclassed prev/next button each. Verified by building `faig-training-workshop` against both the unmodified and modified theme: **byte-identical across all 36 pages** once the four known per-build noise tokens are normalised.

**Files changed**
| File | Change |
|------|--------|
| `layouts/partials/custom-header.html` | The gate: pre-paint script, all gating CSS (panels, sidebar, prev/next, chooser, banners), `deploymentPaths` key-format and page-key validation |
| `layouts/partials/content-header.html` | Blocking chooser, `<noscript>` warning, path switcher, per-foreign-state `.pathmiss` banners — all outside `.Content` so none of it reaches `<meta name="description">` or the search index |
| `layouts/shortcodes/pathtabs.html` | New — path tab group; markup only, assets moved to `custom-header.html` |
| `layouts/shortcodes/pathtab.html` | New — collects one path's content for the parent `pathtabs` block |
| `layouts/shortcodes/pathonly.html` | New — standalone one-path block, same `.pathgate[data-path]` contract as the panels |
| `layouts/partials/pathnav/step.gotmpl` | New — relearn's prev/next walk, re-run per path, skipping foreign pages |
| `layouts/partials/topbar/button/prev.html`, `next.html` | One button variant per path plus `pathnav--any`; unclassed and byte-identical when no paths are declared |
| `scripts/templates/hugo.jinja` | Emit optional `errorignore` and `deploymentPaths` params |
| `scripts/repoConfig.schema.json` | Add `errorignore` and `deploymentPaths` (required — `additionalProperties: false`) |
| `scripts/static.yml` | Now the workshop template: ECR pull with backoff, `trap cleanup EXIT`, `docker wait` status, `::error::` on failure, `image_variant` input |
| `scripts/batch_repo_update.py` | `FILES_TO_COPY` sources `scripts/static.yml`, matching `update_scripts.sh:14` |
| `README.md` | New deployment-paths section: the three forms and when to use each, page scoping, the two asymmetries, and the `local_copy.sh` shadowing gotcha |

---

### fix(launchdemoform): resolve CORS error on Azure Automation webhook

`fetch()` was rejecting with TypeError and showing a red "Network error" to users on sites like PublicCloud105-FortiFlex. Root cause: Azure Automation webhooks return no `Access-Control-Allow-Origin` header; the POST itself goes through fine but the browser blocks JS from reading the opaque response. Fixed by adding `mode: 'no-cors'` so `fetch` resolves (opaque response) instead of rejecting. Status message updated to "Provisioning request sent."

**Files changed**
| File | Change |
|------|--------|
| `layouts/shortcodes/launchdemoform.html` | Add `mode: 'no-cors'` to fetch call; remove unreachable response-parsing code |

---

### fix(logo): restore height, eliminate whitespace in src attribute

The logo `<img>` was missing its `height="70px"` attribute (removed in a prior commit) causing the logo to render at intrinsic size. The multi-line Go template also injected leading whitespace into the `src` attribute value. Both fixed by collapsing the template conditionals onto one line and restoring the height.

**Files changed**
| File | Change |
|------|--------|
| `layouts/partials/logo.html` | Inline `src` conditionals (no whitespace injection), restore `height="70px"` |

---

### fix(dockerfile): version injection now targets menu-footer.html

The Dockerfile `sed` that bakes `CENTRALREPO_VERSION` into the Hugo templates still targeted `copyright.html` after the version block was moved to `menu-footer.html`. This caused the CloudCSE Version to never appear in the navbar footer in deployed images.

**Files changed**
| File | Change |
|------|--------|
| `Dockerfile` | `sed` target changed from `copyright.html` to `menu-footer.html` (both dev and prod stages) |

---

### test: add A12–A14 assertions to catch logo and version injection regressions

Three new HTML/source assertions added to `test_rendered_html.sh`:
- **A12**: logo `img src` must not contain leading whitespace (catches multiline template injection)
- **A13**: Dockerfile must not reference `copyright.html` for version injection
- **A14**: `menu-footer.html` must contain the `HUGO_VERSION_TAG` pattern (Dockerfile sed target is valid)

**Root cause of why these weren't caught:** The existing test suite only validated rendered HTML for analytics/form/CSS correctness. It had no assertions about the logo `src` attribute format or about the Dockerfile → template alignment. Added tests at both the rendered-HTML layer (A12) and source-file layer (A13, A14) to catch future drift.

---

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

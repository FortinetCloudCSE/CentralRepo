# CentralRepo – Shared Hugo Partials and Shortcodes

This repository provides shared Hugo partials and shortcodes used across Fortinet CSE workshop sites. It centralizes cross-site check-in, analytics, and UX helpers so multiple sites can stay consistent.

## How the core partials work together

The page wrapper partial `layouts/partials/content.html` wires the experience:

- On the home page (`.Kind == "home"`): includes `analytics_checkin.html` to render the required check-in form.
- On all other pages: includes `google_analytics.html` to enforce a prior check-in and configure GA user_id.
- After the content (`.Content`): always includes `silent_cross_site_checkin.html` to silently propagate attendance across sites.

### analytics_checkin.html (home page)
Purpose: Collect user email (and optional Customer/Event) and perform the explicit check-in to the TEC Analytics API.

Key behaviors:
- Validates email and posts to `POST https://tecanalytics.forticloudcse.com/checkin` (legacy redirecting endpoint).
- Sets/refreshes cookies for 5 days (rolling window):
  - `fortiuser` (UUID session)
  - `fortiemail`
  - `forticustomer` (optional)
  - `fortievent` (optional)
  - `fortisites` (pipe-delimited list of lowercase site ids visited)
- Stores a localStorage profile (`forti_profile`) to assist prefills and resilience.
- Seeds `fortisites` with the current site id (normalized to lowercase) and dedupes existing entries.
- Dispatches `window` event `forti:checkin` with `{ uuid }` so GA can update `user_id` live.

### google_analytics.html (all non-home pages)
Purpose: Ensure a valid check-in exists before proceeding and configure GA user_id.

Key behaviors:
- If `fortiuser` cookie is missing, redirects to the home page to enforce check-in.
- Initializes GA and sets `user_id` to the cookie value. If `forti:checkin` occurs later, it updates `user_id` dynamically.

### silent_cross_site_checkin.html (all pages)
Purpose: Silently perform a background check-in when a previously checked-in user visits a new workshop site.

Key behaviors:
- Requires `fortiuser` and an `EMail` (from `fortiemail` cookie or `forti_profile`).
- Determines the site id from `.Site.Params.repoName` or the first URL path segment; normalizes to lowercase.
- Maintains the `fortisites` cookie (always lowercase, deduped). If current site is new, performs:
  - `fetch` POST to `/checkin/silent` with a small retry (2 attempts, 200ms and then 600ms delays)
  - Fallback to `navigator.sendBeacon`
  - Final fallback to hidden form `POST /checkin`
- On success or when refreshing an existing site, extends the 5-day TTL for: `fortiuser`, `fortiemail`, `forticustomer` (if set), `fortievent` (if set), and `fortisites`.

## Supporting partials

- `prefill-useremail.html`: exposes helpers and pre-fills common email fields and UUID in other forms based on cookies and `forti_profile`.
- `content-header.html`, `content-footer.html`, `menu-footer.html`, `custom-header.html`, `favicon.html`, etc.: site chrome helpers untouched by the check-in logic.

## Shortcodes and usage

### launchdemoform
Provision lab accounts via an automation webhook with built-in UX and cookie/profile integration.

Usage:
```
{{< launchdemoform lab="My-Lab-Definition" >}}
```
Parameters:
- `lab` or `labdefinition`: Required lab definition sent as `odlconfigname`.
- `debug`: Optional `true|false` to show console diagnostics.

Behavior:
- Reads `fortiuser` and `fortiemail` (or local profile) to populate request.
- Disables action until both are present; provides inline status updates.

### figure
Responsive image with optional zoom source and caption.

Usage:
```
{{< figure src="images/diagram.png" alt="Architecture" caption="Architecture" >}}
```
Optional params:
- `title` (fallback for caption)
- `class` (wrapper class)
- `imgclass` (img class)
- `zoomsrc` (hi-res image path)

### quizframe
Embeds a CTF/quiz iframe and appends cookies for context.

Usage (preferred via site params):
```
{{< quizframe page="/take-quiz" >}}
```
Site params:
- `quizUrl`: Base quiz host (e.g., https://quiz.example.com)
- The shortcode ensures HTTPS and appends `fortiemail`, `fortiuser`, and `workshopID` as query params when present.

Direct src override:
```
{{< quizframe src="https://quiz.example.com/take-quiz" >}}
```

### colortext
Inline colored text.

Usage:
```
{{< colortext "#f00" >}}Important{{< /colortext >}}
```

### Xperts banners
Include themed banners via partial-backed shortcodes.

Usage:
```
{{< Xperts24Banner line1="Line A" line2="Line B" line3="Line C" >}}
{{< Xperts25Banner line1="Line A" line2="Line B" line3="Line C" >}}
```

### pathtabs / pathtab
Deployment-path tabs whose selection is remembered across the whole site. A reader picks a path once — Docker Compose vs Kubernetes, for example — and every other lab page shows that path's steps without asking again.

Usage (two parts — the site param is a prerequisite):

1. Declare the path vocabulary in `scripts/repoConfig.json`:
```json
{
  "deploymentPaths": [
    { "key": "docker", "title": "Docker Compose" },
    { "key": "k8s",    "title": "Kubernetes / Helm" }
  ]
}
```

2. Wrap one `pathtab` per configured path in the content:
```
{{< pathtabs title="Choose your deployment path" >}}
{{% pathtab path="docker" %}}
**Run everything on your own machine.** Start the stack with `docker compose up -d`,
then confirm all four services report `running`.
{{% /pathtab %}}
{{% pathtab path="k8s" %}}
**Deploy to a cluster with Helm.** Install the chart, then confirm the pods are
`Running` with `kubectl get pods -l app.kubernetes.io/instance=ai101`.
{{% /pathtab %}}
{{< /pathtabs >}}
```

Note the delimiters: the outer shortcode uses `{{< >}}`, the inner ones use `{{% %}}` because their content is markdown.

Parameters (`pathtabs`):
- `title`: Label for the locked-path banner (default `Your path`). It is not passed through to the relearn tab nav.
- `groupid`: localStorage tab-group key (default `deploy-path`). Override it when one site needs two independent locked choices — a deployment path and, say, a cloud provider — so switching one does not move the other.

Parameters (`pathtab`):
- `path`: Required. Must match a `key` in `deploymentPaths`, and the shortcode must be nested inside a `pathtabs` block. An unknown key or an unnested `pathtab` is a build `errorf`.

Site params:
- `deploymentPaths`: Required list of `{key, title}` objects. There is no built-in default — if the param is missing the build fails with an `errorf` naming it. A shared shortcode must not carry one workshop's vocabulary.

Behavior:
- Every `pathtabs` block must define every configured path exactly once. A missing path or a duplicate path is a build `errorf`, so a reader on the missing path can never silently be shown the other path's steps.
- Renders a locked-path banner above the tab nav: a lock icon, `Your path: <VALUE>` in uppercase where `<VALUE>` live-updates as the reader switches tabs, and `Locked in — every lab page follows this choice.`
- `deploymentPaths` order is load-bearing: the first entry is the tab Hugo marks active server-side, so it is both the default path for a first-time reader and the banner text with JavaScript disabled. Reordering the list changes every workshop page's default.
- Cross-page sync is relearn's, not ours: relearn stores the selection in `localStorage[absBaseUri + '/tab-selections']` keyed by the tab group id, so a path picked on one page carries to every other page on the site. The banner only observes that state — it never drives it.
- Print: the banner is hidden via `@media print`. Separately, relearn renders only the active tab panel visibly, so print output carries one path by design.

Gotcha — renaming a `title` silently resets every returning reader. Relearn derives each tab's `itemid` from `anchorize(title)` (`themes/hugo-theme-relearn/layouts/partials/shortcodes/tabs.html:42`), and that id is what the stored selection is keyed on. Change a `deploymentPaths` title and every stored selection becomes unmatchable, dropping returning readers back onto the first tab with no warning and no build error. Renaming a `key` is the loud kind of change — every `pathtab path=` must be updated or the build fails. Renaming a `title` is the silent one.

## Theme variants

Set `themeVariant` in `scripts/repoConfig.json` to control the sidebar header appearance. Available values:

| Variant | Header style |
|---------|-------------|
| `Workshop` | Standard Fortinet red |
| `Demo` | Demo-branded |
| `UseCase` | Use-case-branded |
| `Spotlight` | Spotlight-branded |
| `FortinetSilver` | Silver color scheme |
| `FortinetTeal` | Teal color scheme |
| `Xperts2024` | Xperts 2024 static background image |
| `Xperts2025` | Xperts 2025 static background image |
| `CloudCSEMovie` | MP4 video background in the sidebar header area |

### CloudCSEMovie — video header background

The `CloudCSEMovie` variant replaces the static header image with a looping MP4 video. The video plays automatically (muted) on page load. When it ends, it pauses and replays on a configurable interval — for example, a 6-second clip with a 60-second interval plays once, waits 54 seconds, then plays again. All other header content (logo, banner text, search bar) renders on top of the video.

**Setup:**

1. Place the MP4 in `static/videos/` inside CentralRepo (this is the Hugo root for all repo builds, so one file is available to every repo):
   ```
   static/videos/your-video.mp4
   ```

2. Configure `scripts/repoConfig.json`:
   ```json
   {
     "themeVariant": "CloudCSEMovie",
     "videoHeaderSrc": "/videos/your-video.mp4",
     "videoHeaderInterval": 60
   }
   ```
   - `videoHeaderSrc` — URL path relative to site root. Hugo strips the `static/` prefix — do **not** include it in the path.
   - `videoHeaderInterval` — total seconds between the start of each play cycle. Optional; defaults to `60`. Must be greater than the video's duration.

3. Leave `videoHeaderSrc` as `""` to use the `CloudCSEMovie` CSS without a video (renders a solid color header like other themes).

## Site params referenced
- `repoName`: Used to derive the normalized site id (lowercase) for `fortisites` and payload.
- `workshopTitle`: Human-readable title sent with check-ins.
- `marketingCode`: Optional event code sent with check-ins.
- `cookieDomain`: Optional cookie domain override for broader cookie scope.
- `quizUrl`: Base URL for `quizframe`.
- `videoHeaderSrc`: Path to the sidebar header background MP4 (`CloudCSEMovie` theme only).
- `videoHeaderInterval`: Seconds between video play cycles (`CloudCSEMovie` theme only, default `60`).
- `deploymentPaths`: List of `{key, title}` objects defining the path vocabulary for `pathtabs`. Required by that shortcode — the build fails if it is absent.
- `errorignore`: List of regex strings. Relearn matches each one against the offending URL in `themes/hugo-theme-relearn/layouts/partials/_relearn/urlErrorReport.gotmpl:5` and suppresses the link/image/include/openapi warning or error when any matches.

## Cookie overview
- `fortiuser`: UUID session (5-day rolling TTL).
- `fortiemail`: User email (5-day rolling TTL).
- `forticustomer`: Optional customer string (5-day rolling TTL).
- `fortievent`: Optional event/marketing code (5-day rolling TTL).
- `fortisites`: Pipe-delimited lowercase list of visited site ids (5-day rolling TTL).
- `forti_profile` (localStorage): JSON `{ email, customer, event, workshopID }` used for prefills and recovery.

## Notes & gotchas
- CORS: `/checkin/silent` is CORS-protected. In development, configure the API to allow your dev origin via `CORS_ORIGINS` or `CORS_ALLOW_ALL_DEV=1`.
- Normalization: `fortisites` is always written in lowercase and deduplicated.
- Fallbacks: silent check-in uses fetch → sendBeacon → hidden form to maximize delivery.
- UserRepo shadowing: the container entrypoint runs `scripts/local_copy.sh`, whose first two lines do a non-recursive `cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes` and `cp ../UserRepo/layouts/partials/* layouts/partials`. Same-named files overwrite CentralRepo's.
  - A repo-local `layouts/shortcodes/<name>.html` silently overrides CentralRepo's version of that shortcode. An upstream fix to it then does nothing in that repo, and nothing tells you — no warning, no build error.
  - A repo-local `layouts/partials/custom-header.html` replaces CentralRepo's wholesale (currently 715 lines), losing every Fortinet brand color token and the support widget. The copy is whole-file, not additive.
  - Practical rule: put repo-local CSS anywhere except `custom-header.html`. Adding a new, differently-named partial or shortcode is safe; a same-named one means you have forked the shared file and own it from then on.
- Blast radius: a merge to `main` rebuilds the prod ECR image, and **65 repos in this org pull that image tag** on their next build (measured 2026-08-19 with `gh api search/code -f q='org:FortinetCloudCSE "public.ecr.aws/k4n6m5h8/fortinet-hugo" path:.github/workflows'`). The workflows reference the floating `:latest` tag, so there is no opt-in and no pin. Any new site param must be optional and a no-op when absent, and should be verified against a repo that does not set it — "it built fine in the repo I was working in" is not evidence. Re-run the search rather than trusting the number.
  - `image-build-push-prod.yaml` triggers on **any** push to `main` with no `paths-ignore`, so a README-only merge rebuilds the image too. Combined with the unpinned Hugo below, that means a pure documentation commit can hand 65 repos a new Hugo version. Either add `paths-ignore` for docs, or batch doc changes into a PR that is rebuilding anyway rather than merging them alone.
- Output formats vs `.Page.Store`: Hugo renders page content once per output format while `Page.Store` is shared across them, so a `once per page` asset guard emits into whichever format builds first and is silently missing from the others — including `layouts/_default/allpages.html`'s whole-site print page and any page with `outputs: ["html", "print"]`. Guard bulky assets; emit anything whose absence changes rendering unguarded per block. `layouts/shortcodes/pathtabs.html` shows the split.
- **The Hugo version is unpinned, so every image rebuild is also an unannounced Hugo upgrade for all 65 repos.** `Dockerfile:10` is `FROM hugomods/hugo:std` with no tag, in both the `dev` and `prod` stages. Merging a one-line partial change to `main` rebuilds the prod image against whatever `:std` resolves to that day, and every repo picks it up on its next build. This is not hypothetical: the 2026-08-19 rebuild moved Hugo 0.164.0 → 0.165.0 with nothing in the diff, the workflow log, or the image tag saying so. A Hugo minor can deprecate template functions and change `.Store`/output-format behaviour, so a repo that built clean yesterday can emit WARNs or fail today with no change of its own. Pin `:std` to an explicit version and bump it deliberately; until then, read `hugo v…` off the first line of any build you are using as evidence, and never attribute a new WARN to your own change without checking it.
- **`hugo_build.sh` pip-installs Jinja2 from PyPI on every single build, so a PyPI outage breaks all 65 repos.** `scripts/hugo_build.sh:3` calls `scripts/generate_toml.sh`, which creates a venv and runs `pip install Jinja2` (`generate_toml.sh:4-6`) before `generate_toml.py` can render `hugo.toml`. The build has a hard network dependency at *run* time, not build time. Worse, the failure is misreported: `generate_toml.py` never runs, so no `hugo.toml` exists and Hugo exits with `ERROR Unable to locate config file or config directory. Perhaps you need to create a new project.` The real cause — `ModuleNotFoundError: No module named 'jinja2'` — is buried further up the log, so this reads as a broken repo rather than a transient network fault. Retrying usually fixes it. The correct fix already exists elsewhere in this repo: CI bakes it with `apk add --no-cache python3 py3-jinja2` (`.github/workflows/ci.yml:42,75`). Do the same in the `Dockerfile` and drop the venv entirely.

## Testing

Tests live in `scripts/test/`. CI runs automatically on push to `prreviewJune23` and on PRs to `main`.

**Run locally:**
```bash
bash scripts/test/run_tests.sh
```

**Activate pre-push hook** (run once after cloning):
```bash
git config core.hooksPath .githooks
```

| Layer | Tool | What it catches |
|-------|------|----------------|
| Hugo build | `hugomods/hugo:std` in CI | Template errors, deprecations, broken partials |
| HTML assertions | `test_rendered_html.sh` | Form action URLs, CSS paths, forbidden iframe attrs |
| Regex validation | `validate_regex.js` | Chrome v-flag incompatible `pattern=""` values |
| Config schema | `validate_config.py` | Missing required fields, invalid themeVariant |

See `.github/workflows/ci.yml` for the full CI pipeline.

## Contributing
- Update partials conservatively—they are shared by many sites.
- Keep README examples accurate; include parameter defaults and any site param dependencies.

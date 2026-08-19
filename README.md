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

### pathtabs / pathtab
Parallel steps for two or more mutually exclusive deployment paths, of which a reader follows exactly one. Only the reader's chosen path is shown — in the page body, the sidebar, the next/previous buttons, and search.

Requires `deploymentPaths` in the workshop's `scripts/repoConfig.json`. There is no default vocabulary: a repo that does not declare paths cannot use these shortcodes, and no repo inherits another repo's paths.

Usage:
```
{{< pathtabs title="Deploy the stack" >}}
{{% pathtab path="docker" %}}
docker compose up -d
{{% /pathtab %}}
{{% pathtab path="k8s" %}}
helm upgrade --install mylab ./chart
{{% /pathtab %}}
{{< /pathtabs >}}
```
Parameters:
- `pathtabs` — `title`: optional banner label (default `Your path`). `groupid`: optional tab-group id (default `deploy-path`); leave it alone unless you need two independent groups on one page.
- `pathtab` — `path`: required, one of the `key` values in `deploymentPaths`.

Note the delimiters: `{{< pathtabs >}}` (angle) for the wrapper, `{{% pathtab %}}` (percent) for each body, so the body is rendered as markdown.

Build fails when: `deploymentPaths` is unset; a block omits any configured path; a block defines the same path twice; a body is empty; `path=` names an unknown key; a `pathtab` sits outside a `pathtabs`. Each failure is a deliberate error rather than a warning, because the alternative is a gate that silently shows the wrong path's steps.

### pathonly
One path's content with no tab UI — prose, a warning, or a whole section that has no counterpart on the other paths. Same gating mechanism as `pathtab` (both emit `.pathgate[data-path]`), so there is one gate, not two.

Usage:
```
{{% pathonly path="k8s" %}}
Your cluster needs a default StorageClass before you continue.
{{% /pathonly %}}
```
Parameters:
- `path`: required, one of the `key` values in `deploymentPaths`. It takes no other parameters.

**Must be called with the percent form.** With `{{< pathonly >}}`, `RenderString` gives the body its own render context, so headings inside never join the page's fragment set and every in-page anchor to them breaks silently. Blank lines above and below the tags are also load-bearing: a line beginning `<div` opens a CommonMark type-6 raw-HTML block that runs to the next blank line, and without them the body is never rendered as markdown.

Build fails when: `deploymentPaths` is unset; `path=` names an unknown key; the block is nested inside `pathtabs`/`pathonly`; the body is empty.

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

### Deployment paths — pathtabs / pathtab / pathonly
A reader picks a path once — Docker Compose vs Kubernetes, for example — and every other page follows that choice without asking again. There are three ways to scope content, and picking the wrong one is the main authoring mistake:

| Form | Scope | Use when |
|------|-------|----------|
| `pathtabs` / `pathtab` | One block, every path | The paths are genuine alternatives to the same goal and a reader might want to see the other one. |
| `pathonly` | One block, one path | The block only exists for one path and has no counterpart. |
| `deploymentPath` front matter | A whole page | The entire page is one path's. |

If the content is a *sentence* rather than a block, none of these fit — reword it to be path-neutral, or name both mechanisms. A block-level shortcode cannot wrap half a sentence, and gating a whole paragraph to hide one clause hides information the other path needed.

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
- Every `pathtabs` block must define every configured path exactly once. A missing path or a duplicate path is a build `errorf`, so a reader on the missing path can never silently be shown the other path's steps. An empty `pathtab` body is also an `errorf`.
- **The gate is default-deny: until the reader picks a path, no path's steps are visible anywhere on the site.** This is the whole point. The earlier version defaulted to showing the first tab, and readers followed the Docker steps *and* the Kubernetes steps because both were reachable. There is deliberately no default path — `deploymentPaths` order now only controls the order of the buttons in the chooser and the order of panels in the no-JavaScript fallback.
- On a page with a `pathtabs` block and no choice made yet, `layouts/partials/content-header.html` renders a blocking chooser — one button per path — and every `pathtabs` block on the page stays collapsed.
- Once a path is chosen, each block shows a locked-path banner (`Your path: <VALUE>`, lock icon, `Locked in — every lab page follows this choice.`) and the relearn tab nav is hidden. The switcher in `content-header.html` becomes the only way to change the choice, so there is one control writing one state instead of two.
- Every part of this is server-rendered and CSS-gated, not JS-driven: `pathtabs` emits one `<span class="pathlock__value" data-path=…>` per path and one `<div class="pathgate" data-path=…>` per path, and the CSS in `custom-header.html` reveals whichever matches `<html data-deployment-path>`. Nothing is written to the DOM after load, so there is no frame in which the wrong path is on screen.
- Storage: the choice lives in `localStorage[absBaseUri + '/deployment-path']`. An inline synchronous `<script>` in `<head>` reads it and sets `document.documentElement.dataset.deploymentPath` before first paint — the same pre-paint pattern relearn itself uses for `themeVariant`. A choice made before this gate existed is migrated out of relearn's `tab-selections` on first load, so returning readers are not re-prompted.
- Print: banner, chooser and switcher are all hidden, and only the chosen path's panel is in the flow — so print output carries exactly one path.
- No JavaScript: nothing sets `data-deployment-path`, so none of the gating applies. **All** paths render, stacked, with a `<noscript>` warning naming them in order and saying to follow only one. The nav is hidden because its buttons are inert without `switchTab`. Failing open is deliberate: unreadable-but-complete beats a silently empty page.

Gotcha — renaming a `title` silently resets every returning reader. Relearn derives each tab's `itemid` from `anchorize(title)` (`themes/hugo-theme-relearn/layouts/partials/shortcodes/tabs.html:42`), and that id is what relearn's own stored selection is keyed on. Change a `deploymentPaths` title and every stored *tab* selection becomes unmatchable. The gate's own key is the stable `key`, not the title, so the visible path survives a rename — but the pre-gate migration path and relearn's `.active` bookkeeping do not. Renaming a `key` is the loud kind of change: every `pathtab path=` must be updated or the build fails. Renaming a `title` is the silent one.

Gotcha — never emit reader-facing prose from a shortcode that a page's `<meta name="description">` or the search index should not contain. Relearn builds the description from `.Summary | plainify` (`themes/hugo-theme-relearn/layouts/partials/meta.html:44`) and indexes the same content, so an earlier revision that put the chooser and the `<noscript>` warning inside the `pathtabs` shortcode pushed "JavaScript is disabled, so all 2 deployment paths are shown below" into the description and search snippet of every lab page, and added 120 words to each. Anything that is chrome rather than content belongs in a partial, outside `.Content`.

### pathonly
A standalone block that belongs to exactly one path, for content with no counterpart on the other path — where a `pathtabs` group would mean writing an empty or padded tab just to satisfy the every-path-exactly-once rule.

```
{{% pathonly path="docker" %}}
### Compose profiles
The stack ships three profiles. Enable the GPU profile with
`docker compose --profile gpu up -d`.
{{% /pathonly %}}
```

Parameters:
- `path`: Required. Must match a `key` in `deploymentPaths`; anything else is a build `errorf`.

Behavior:
- **`{{% %}}`, not `{{< >}}` — this is not stylistic.** The percent form hands the body back to the page's own markdown pass. The angle form would force the shortcode to render its body with `RenderString`, which runs in a separate render context, so headings inside the block never join the page's fragment set: an in-page `[link](#heading)` pointing into a `pathonly` block builds with `WARN … heading ID "…" not found` and does nothing when a reader clicks it, and the heading is absent from the page's table of contents.
- Wraps its body in the same `.pathgate[data-path]` element the tab panels use, so there is one path-gating attribute in the codebase rather than two, gated by the same CSS.
- Nesting inside `pathtab` or another `pathonly` is a build `errorf`, not a no-op. The enclosing block already restricts its body to one path, so a nested `pathonly` is either redundant (same key) or content that can never render (different key) — and the second case looks like working authoring right up until a reader reports missing steps.
- An empty body is a build `errorf`, since it is indistinguishable from a gate silently hiding the wrong thing.
- It may sit inside a plain (non-path) `tabs` group.

### deploymentPath front matter — scoping a whole page
Set `deploymentPath: docker` (or any declared `key`) in a page's front matter and the page belongs to that path alone. A key not in `deploymentPaths` is a build `errorf` — a page scoped to a path that does not exist is hidden from every reader.

This does more than gate the body; it removes the page from the other path's route through the site:

- **Sidebar.** `custom-header.html` generates one CSS rule per (scoped page × other path) hiding that page's `<li>`. The selector is keyed on the permalink from `permalink.gotmpl` — the same partial `menu.html` builds `data-nav-id` from — *not* on `.RelPermalink`, which omits the `index.html` that `disableExplicitIndexURLs = false` appends to every section page.
- **Prev/next.** Relearn resolves these at build time and honours only `params.hidden`, so hiding a page from the sidebar while leaving it on the linear walk marches the reader into a page the sidebar says does not exist. `layouts/partials/pathnav/step.gotmpl` re-runs relearn's walk once per path, skipping foreign pages, and `topbar/button/{prev,next}.html` emit one button per path plus a `pathnav--any` for the no-choice state; CSS reveals the matching one.
- **Arriving anyway.** A bookmark, a search result or someone else's link can still land a reader on a foreign page, so `content-header.html` emits a `.pathmiss` banner per foreign state — naming both the page's path and the reader's — with a switch button. The content still renders below it: a blank page with a switcher reads as a broken build, not as a gate. The blocking chooser is suppressed on these pages, so an undecided reader gets one prompt rather than two.

Two asymmetries here are deliberate:

- **Navigation is not default-deny, unlike step content.** With no choice stored, every page shows in the sidebar and prev/next is the theme's own unfiltered walk. Default-deny is right for steps, where showing both paths is the bug this whole mechanism exists to fix; it is wrong for navigation, where it would present a workshop with pages missing from the table of contents and no explanation.
- **Every gate rule only ever hides — none forces `display` back on.** Sidebar `<li>`s and topbar buttons carry the theme's own responsive `display` rules (`[data-width-s="hide"]` and friends), so a rule re-showing the active path's element would defeat them at small widths and break the sidebar flyout. Reveal by `:not()`, never by re-assertion.

A page-scoping decision is only visible in the built HTML as absent CSS, so it fails silently: if the generated selector does not byte-match the sidebar's real `data-nav-id`, the rule matches nothing and no error is raised.

### Search
Search results are filtered to the reader's path, because a search hit is the single most likely way a reader reaches a page the sidebar and prev/next gating just removed from their route.

- Filtered client-side, in a wrapper around `window.relearn.search.adapter.search`. That is the only function both search surfaces go through — the dropdown suggestions (`search.js:178-181`) and the dedicated results page (`search.js:130-133`) — and the "N results found" count is computed from the array the wrapper returns, so it stays truthful.
- The index entry shape is deliberately **not** extended. Relearn generates the index once from `site.Home` and feeds the same entries to two engines with independent field declarations — lunr's field list and the orama adapter's strict schema — so adding a field there is a theme-wide contract change. Instead `custom-header.html` emits a small `uri → path` side map for scoped pages only, keyed on the same `permalink.gotmpl` output the index itself uses for `uri`. If you ever do extend the index, note that lunr writes `page.index` onto every entry, so `index` is a field name that must never be added.
- **With no path chosen, nothing is filtered.** Same reasoning as the sidebar: an undecided reader sees the whole site everywhere else, and a search that silently returned nothing would read as a broken index rather than as a gate.
- Switching paths clears the autocomplete cache. `auto-complete.js` stores results on the `#R-search-by` element keyed by raw input value, and short-circuits any term whose shorter prefix cached zero results — so one term that legitimately found nothing on the old path would otherwise poison itself and every extension of it. If results are already on screen, the search re-runs.

### Repos that declare no paths
`deploymentPaths` is absent from nearly every workshop repo, and all of the above is inert without it: no gate script, no gate CSS, one unclassed prev/next button each, and no `pathnav` classes. Output is byte-identical to a build without the feature.

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
- `deploymentPaths`: Optional list of `{ "key": …, "title": … }` declaring a workshop's mutually exclusive deployment paths. Required by `pathtabs`/`pathtab`/`pathonly` and by any page carrying a `deploymentPath` front-matter param; omitting it leaves every one of those features inert. `key` must start with a letter and contain only letters, digits, hyphens and underscores, because it is interpolated into CSS class names as well as attribute values. **Order is load-bearing** — the first entry is the JavaScript-off default and the server-side active tab. **Renaming a `title` silently resets every returning reader's stored choice** (the selection is keyed on the title text); renaming a `key` fails the build instead, which is the safer failure.
- `errorignore`: Optional list of regexes suppressing relearn's URL error report for targets it cannot resolve as pages (e.g. a PDF referenced from `menu.shortcuts`).
- `deploymentPaths`: List of `{key, title}` objects defining the path vocabulary for `pathtabs`, `pathonly` and the `deploymentPath` page param. Required by all three — the build fails if it is absent. Declaring it is also what switches the whole gate on; a repo without it builds byte-identically to one built before the feature existed. Keys are used as CSS class suffixes as well as attribute values, so a key must start with a letter and contain only letters, digits, hyphens and underscores.
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
- **`scripts/static.yml` is the canonical workflow template for workshop repos; this repo's own `.github/workflows/static.yml` is a different file with a different job.** One file cannot serve both roles — CentralRepo builds the image from its own `Dockerfile`, while workshop repos pull it from ECR and some (e.g. `ai-101`) have no `Dockerfile` at all. `update_scripts.sh:14` and `batch_repo_update.py` both treat `scripts/static.yml` as the template. The duplication looks like an inconsistency worth collapsing; it is not.
- **`switchTab()` persists only on a real click.** It reads the implicit global `event` (`theme.js:120`), so anything that calls it programmatically switches the tab visually but never writes `localStorage` — the choice silently fails to survive navigation. To *change* a tab from your own control, dispatch a real click on the matching `.tab-nav-button` (`fortiPath.set()` in `custom-header.html` does this); relearn then takes its normal path, including the `initMermaid(true)` re-render.
  - The deployment-path gate is the one place that also writes relearn's `tab-selections` key directly, and the reason is not cosmetic: its CSS can reveal a panel that relearn still believes is inactive, and a panel relearn thinks is inactive never gets `initMermaid()`'d, so a mermaid diagram inside it renders at zero width. Since the header switcher exists on pages with no tab nav to click, the head script reconciles relearn's key to the gate's on every load, before the deferred `restoreTabSelections()` runs. Write the same `itemid` format the theme writes and nothing else.
- Output formats vs `.Page.Store`: Hugo renders page content once per output format while `Page.Store` is shared across them, so a `once per page` asset guard emits into whichever format builds first and is silently missing from the others — including `layouts/_default/allpages.html`'s whole-site print page and any page with `outputs: ["html", "print"]`. This bit `pathtabs`, whose guarded `<style>`/`<script>` were absent from every `index.print.html`. The fix that generalises: put the assets in `custom-header.html`, which is a `<head>` partial and therefore runs once per page in *every* output format, and leave the shortcode emitting markup only. Reach for a `Page.Store` guard only when the asset genuinely cannot live in `<head>`.
- **"Byte-identical build output" is not a usable verification criterion in this repo — four tokens change on every build.** Asset-busting query strings (`?1787158346`), lightbox image ids (`#R-image-<md5>`), the footer's `last-updated-time-utc`, and the auto-generated `data-tab-group` hash for `tabs` groups with no explicit `groupid` all differ between two consecutive builds of an unchanged repo. Comparing a change against a *single* baseline build therefore reports every content page as modified and tells you nothing. Build the baseline twice, normalise those four patterns, and confirm the residual diff set is the same for baseline-vs-rerun as for baseline-vs-change.
- **Testing a CentralRepo change by mounting your worktree at `/home/CentralRepo` lets the workshop repo overwrite the files you are editing.** `docker run -v <workshop>:/home/UserRepo -v <your CentralRepo worktree>:/home/CentralRepo fortinet-hugo:latest build` is the only way to exercise an unmerged partial, but the entrypoint's `scripts/local_copy.sh` then copies `UserRepo/layouts/shortcodes/*` and `UserRepo/layouts/partials/*` *into your worktree* — silently clobbering the very file under test if the workshop repo has one by the same name, and leaving its other layouts behind as untracked files. Run `git status` after every such build.
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

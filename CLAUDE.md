# CLAUDE.md — CentralRepo

> Global preferences (planning workflow, code quality, operations): `~/.claude/CLAUDE.md`
> Copilot instructions: `.github/copilot-instructions.md` (detailed architecture & dev workflows)

## Working Branch

`main` builds the **prod** ECR image; `dev` builds the **dev** image. Two routes into `main`
are in use and they are not equivalent:

1. **Dev-first (the documented route):** edit on `dev` → push (dev image rebuilds) → PR
   `dev` → `main` → prod image rebuilds. Use this when the change needs proving in a real
   workshop build before it reaches every consuming repo.
2. **Feature branch → PR → `main`** — what the deployment-path work did (#72, #73, #74, #77). Fine for
   a change already tested with the `LOCAL=true` dev image, but it leaves `dev`
   content-behind, so **the dev image silently lacks the change**.

**If you take route 2, push `main` → `dev` in the same session.** Route 2 left the branches
diverged for a week in August 2026 (17 files / ~1240 lines: the path gate, `scripts/static.yml`,
`batch_repo_update.py`, the base-image pin), and the only symptom was dev-image test results that
looked valid and were pre-gate. Resynced 2026-08-19; both refs are `e0d4a14f`. The resync is a
fast-forward as long as nothing is committed to `dev` directly:
`git push origin origin/main:refs/heads/dev`.

Never push straight to `main` without a PR — it is protected, and a bypass is logged.

**Route 2 incident, 2026-08-25 (real, not hypothetical):** a `launchdemoform` rebuild PR merged straight to `main` (route 2) without the required resync push — exactly the failure mode warned about above. Caught mid-flight: `image-build-push-prod.yaml`'s step 9 ("Build and push test image, **no latest tag**") had already completed, but step 13 ("Build and push multi-arch **latest** image, after tests pass") — the only step that actually touches the prod tag every workshop repo pulls — was still pending, so cancelling the run at that point left `fortinet-hugo:latest` completely untouched. **If a route-2 merge needs to be undone before the image finishes, `gh run view <id> --json jobs` to check whether the `latest`-tag push step has run yet — cancelling before it is fully safe, cancelling after it is not.** Redone correctly via route 1 (`dev` first, confirmed its push-triggered CI green, then PR into `main`).

**FortiDevSec SAST stage: broken/deprecated org-wide as of 2026-08-25, only some repos have it disabled.** Every actively-maintained repo checked that day has `when { expression { false } }` guarding the `Running FortiDevSec scans...` Jenkinsfile stage; several stale sibling repos (`FortiCNAPPRoadshow`, `forticnapp-code-security-demo`, `MGMT-in-AWS`, `fortigate-automation-stitch-workshop`, `fortiweb-threat-protection`, and `fortinet-on-demand-labs-provisioning-and-tracking`) didn't and their `ci/jenkins/build-status` required check failed on completely trivial, unrelated content PRs. If that check fails on an unrelated change anywhere in this org, check the Jenkinsfile for this exact pattern before assuming the PR's content is at fault.

## Project in One Line

Shared Hugo partials, shortcodes, and themes consumed by all Fortinet CSE workshop sites —
centralizes check-in, analytics, quiz integration, and UX helpers into a Docker-based build system.

## Stack Quick Reference

| Layer | Tech | Notes |
|-------|------|-------|
| Static site generator | Hugo (`hugomods/hugo:std-0.165.0`, **pinned**) | Relearn theme (git submodule) |
| Templating | Go templates + Jinja2 (config gen) | `repoConfig.json` → `hugo.toml` |
| Build/Runtime | Docker multi-stage (dev/prod) | tini entrypoint, Python 3 for scripts |
| CI/CD | GitHub Actions (image build/push) | Also: Jenkins (legacy), AWS CodeBuild (legacy) |
| Hosting | AWS CloudFront + S3 (per-workshop) | CloudFormation templates in `pipeline/` |
| Security | FortiDevSec (SAST, secrets, SCA, IaC, container) | Fails pipeline at risk rating ≥7 |

## Key File Map

```
layouts/
  partials/
    content.html                  — Page wrapper: wires analytics_checkin (home) + google_analytics (other) + silent checkin
    analytics_checkin.html        — Home page check-in form → TEC Analytics API POST /checkin
    google_analytics.html         — Non-home pages: enforces prior check-in, configures GA user_id
    google_analytics_authorMode.html — ⚠️ DO NOT DELETE — hugoServer_authorMode.sh mv's this into place at dev startup
    silent_cross_site_checkin.html — Background cross-site attendance propagation
    prefill-useremail.html        — Cookie/profile-based form prefill helpers
    custom-header.html            — 1271 lines: CloudCSEMovie video injection + the ENTIRE deployment-path gate (gate CSS at :338-644, pre-paint script at :663-762, search scoping at :791-872)
    content-header.html           — 108 lines: path chooser, pathmiss banners, .pathswitch, <noscript> fallback
    pathgate/specs.gotmpl         — Resolves the path vocabulary in effect for ONE page (site param vs. its own front matter); every gate consumer calls this, never site.Params directly
    pathnav/step.gotmpl           — Resolves the next/prev page for ONE deployment path
    topbar/button/prev.html       — Emits one .pathnav prev button per configured path
    topbar/button/next.html       — Emits one .pathnav next button per configured path
    menu-footer.html              — Version/Revision/Last Updated block; version baked in at Docker build time via sed
    copyright.html                — Footer copyright line (NOT where the version is injected)
    orig_analytics_checkin.html   — Dead code (slated for deletion)
    orig_google_analytics .html   — Dead code, trailing space in filename (slated for deletion)
  shortcodes/
    launchdemoform.html           — Lab provisioning via Azure automation webhook
    quizframe.html                — CTF quiz iframe with cookie propagation (NOT quizdown)
    figure.html                   — Responsive image with optional zoom
    ContainerFlow.html            — draw.io diagram renderer (mxGraph)
    FTNThugoFlow.html             — Fortinet-branded draw.io flow diagram
    fortihugorunner.html          — Dev harness shortcode (local testing only)
    Xperts24Banner.html           — Xperts 2024 themed banner
    Xperts25Banner.html           — Xperts 2025 themed banner
    pathtabs.html                 — Deployment-path tab group + locked-path banner; needs a vocabulary from pathgate/specs.gotmpl
    pathtab.html                  — One path's content, collected by its parent pathtabs block
    pathonly.html                 — Content shown to ONE path with no tab UI; must be called with {{%…%}}
    colortext.html                — Inline colored text
    carousel.html                 — Slated for deletion (library never loaded, no live usage)
    quizdown.html                 — Slated for deletion (replaced by CTF quiz app via quizframe)

assets/css/
  theme-CloudCSEMovie.css         — MP4 video sidebar header (current default for CentralRepo itself)
  theme-Xperts2025.css            — Xperts 2025 (Fortinet red)
  theme-Xperts2024.css            — Xperts 2024
  theme-Workshop.css / theme-Demo.css / etc. — Alternate color schemes

scripts/
  repoConfig.json                 — Site config (repoName, theme, analytics URL, shortcuts)
  repoConfig.schema.json          — JSON schema for the above; deploymentPaths declared here
  generate_toml.sh/.py            — Generates hugo.toml from repoConfig.json via Jinja2
  templates/hugo.jinja            — Jinja2 template for hugo.toml generation
  hugoServer_authorMode.sh        — Dev server bypassing analytics check-in
  hugo_build.sh                   — Production build (generate_toml + hugo build)
  local_copy.sh                   — Container entrypoint; copies UserRepo layouts over CentralRepo's
  docker_build.sh                 — Build Docker image (prod|dev)
  docker_run.sh                   — Run container (build|server|generate_toml|shell)
  next_version.py                 — Version incrementer
  batch_repo_update.py            — Batch update across workshop repos
  static.yml                      — CANONICAL workshop-repo workflow template (not CentralRepo's own)

pipeline/webhosting/              — AWS CloudFormation (CloudFront + S3 + CodeBuild)
themes/hugo-theme-relearn/        — Relearn theme (git submodule)

Dockerfile                        — Multi-stage: dev (dev branch) / prod (main branch)
fdevsec.yaml                      — FortiDevSec scanner config
```

## Build & Run Commands

```bash
# Local development (author mode — bypasses analytics check-in)
./scripts/generate_toml.sh           # Generate hugo.toml from repoConfig.json (required first)
./scripts/hugoServer_authorMode.sh   # Hugo dev server on :1313

# Production build
./scripts/hugo_build.sh              # generate_toml + hugo build

# Docker workflows (uses UserRepo content at /home/UserRepo)
./scripts/docker_build.sh [prod|dev]          # Build container image
./scripts/docker_run.sh build [prod|dev]      # Build site in container
./scripts/docker_run.sh server [prod|dev]     # Dev server in container
./scripts/docker_run.sh shell [prod|dev]      # Debug shell

# Test an UNMERGED working-tree edit against a real workshop repo
docker build --build-arg LOCAL=true --target dev -t hugotester-local .
docker run --rm -v /path/to/UserRepo:/home/UserRepo:ro hugotester-local build
```

## Critical Patterns & Gotchas

- **`google_analytics_authorMode.html` — NEVER DELETE.** `hugoServer_authorMode.sh` renames this file to `google_analytics.html` at dev startup. Delete it and dev server mode silently breaks (GA partial missing).
- **Dual-repo pattern:** CentralRepo provides layouts/themes; UserRepo (workshop content) mounts to `/home/UserRepo` in Docker. Config flow: `UserRepo/scripts/repoConfig.json` → Jinja2 → `hugo.toml`
- **Analytics check-in flow:** Home page collects email → sets cookies (5-day rolling TTL) → non-home pages redirect to home if `fortiuser` cookie missing → all pages silently propagate cross-site attendance to TEC Analytics API
- **Cookie system:** `fortiuser` (UUID), `fortiemail`, `forticustomer`, `fortievent`, `fortisites` (pipe-delimited lowercase site IDs). All 5-day rolling TTL. `forti_profile` in localStorage for resilience.
- **Silent check-in fallback chain:** `fetch` POST → `navigator.sendBeacon` → hidden form POST
- **`fortisites` normalization:** Always lowercase, always deduplicated. `repoName` from site params gets lowercased.
- **Theme variant:** Set via `themeVariant` in `repoConfig.json`, must match CSS filename exactly (case-sensitive): e.g. `theme-Xperts2025.css` → `"themeVariant": "Xperts2025"`.
- **`quizframe.html` vs `quizdown.html`:** `quizframe.html` is the live CTF quiz iframe shortcode — keep it. `quizdown.html` is dead (quizdown replaced by the CTF app) — slated for deletion.
- **Version injection targets `menu-footer.html`, not `copyright.html`.** Both Dockerfile stages `sed` `CENTRALREPO_VERSION` over `getenv "HUGO_VERSION_TAG"` in `layouts/partials/menu-footer.html`, which is also where the Version/Revision/Last Updated block renders.
- **Dockerfile fetches from GitHub at build time:** Both stages use `ADD https://github.com/.../CentralRepo.git#<branch>` — local file changes are NOT picked up. Use the `LOCAL=true` build above to test a working-tree edit.
- **The Hugo base image is pinned to `hugomods/hugo:std-0.165.0` (`Dockerfile:15`) — keep it pinned.** Unpinned, a `hugomods/hugo:std` release changed the renderer under 65 workshop repos on the next image rebuild, with no commit here to explain it. Bumping the pin is a deliberate, reviewable change; drifting is not.
- **`paths-ignore` on both image workflows is deliberately narrow.** `'*.md'` is root-level markdown only (not `**/*.md`), plus `docs/**`, `review/**`, the licences, and the repo-tooling config that lands in the image but nothing reads: `.gitignore`, `.claude/**`, `.githooks/**`. **Anything under `scripts/`, `layouts/`, `assets/`, `i18n/`, `static/`, `archetypes/`, `themes/` or the `Dockerfile` reaches the image — never add those.** A wrong entry here means a real change ships to nobody and the absence of a run looks like success.
- **Assume a push rebuilds the image unless you have checked `gh run list`.** Tracking `.claude/settings.json` (#79) triggered a full multi-arch prod build that republished `fortinet-hugo:latest` to all 65 workshop repos, after the PR body asserted it would not — the reasoning was right about the file being inert and wrong about the filter, because `.gitignore` was not on the list at the time. Reading the filter is not the same as observing the trigger.
- **Shortcode cookie deps:** `launchdemoform` and `quizframe` require `fortiuser`/`fortiemail` cookies — fail silently without them.
- **CORS:** TEC Analytics `/checkin/silent` endpoint needs CORS config for dev origins (`CORS_ALLOW_ALL_DEV=1` on the API).
- **Relearn theme compiles CSS variants:** All `theme-*.css` variants are compiled into `css/format-html.css` via CSS nesting + `data-r-theme-variant`. The `static/css/theme-CloudCSEMovie.css` is a static fallback, not the active file.
- **ContainerFlow/FTNThugoFlow/fortihugorunner shortcodes** currently include full `<!DOCTYPE html>` wrappers — this is invalid HTML when embedded in a Hugo page and causes rendering bugs.
- **`hugo.toml` is gitignored** — generated at container startup by `generate_toml.sh`. Do not commit it.
- **This file is tracked. Do not re-add `CLAUDE.md` to `.gitignore`.** It was ignored from `7dc90e1` (2026-05-28) until 2026-08-19, which meant every session in this repo started blind and every durable fact learned here died with its terminal — including all of the path-gate reasoning below, which had to be reconstructed from the plan file in a *consuming* repo. Committing it costs nothing: root-level `*.md` is in both image workflows' `paths-ignore`, so a docs change does not rebuild or republish the image.
- **Two-hop deploy path — an upstream edit is invisible until it reaches a workshop site.** Edit → merge to `main` → `image-build-push-prod.yaml` rebuilds and pushes the prod ECR image → each workshop repo picks it up on its *next* build. Nothing upstream is visible before that; don't debug a workshop site against an unbuilt CentralRepo commit.
- **A floating tag hides two separate lies.** A green image-build run is not proof `fortinet-hugo:latest` moved — read the push step's log for the digest it reported. And `docker pull` on a tag you already hold locally can serve the *stale* manifest: `docker rmi -f` first, then pull, then confirm a file the change introduced actually exists inside the image. Skipping this produces a confident wrong conclusion that the merge didn't ship.
- **The dev image build is tied to the `dev` branch by name, asserted in two places that must stay in agreement:** `.github/workflows/image-build-push-dev.yaml:6` (push trigger) and `Dockerfile` (`ADD …CentralRepo.git#dev`). Change one without the other and the dev image builds a branch nothing pushes to. `prreviewJuly23` is a decoy — commits behind `main`, last commit 2026-06-11, referenced by no workflow and no Dockerfile stage. Never branch from it.
- **Measure branch divergence with `git diff --quiet origin/dev origin/main`, not `rev-list --left-right --count`.** A merge-back workflow routinely leaves the dev branch *history*-behind while the content is identical; that is not staleness. The counts answer the wrong question. The diff passed as of 2026-08-19 — re-run it, don't trust this line.
- **Repo-local files shadow CentralRepo's, silently.** `scripts/local_copy.sh:3-4` runs a non-recursive `cp` of `../UserRepo/layouts/shortcodes/*` and `../UserRepo/layouts/partials/*` over CentralRepo's, so a same-named workshop file wins with no warning and an upstream fix to it does nothing in that repo. A repo-local `custom-header.html` is worse — the copy is whole-file, so it replaces CentralRepo's outright, losing every Fortinet colour token, the support widget, **and the entire deployment-path gate**. Adding a new, differently-named partial or shortcode is safe. Full detail in `README.md` → "Notes & gotchas" → UserRepo shadowing.
- **A shortcode's `.Page.Store` guard is per page, NOT per output format.** Hugo renders page content once per output format while the Store is shared across them, so a `once per page` asset block lands in whichever format builds first and is silently absent from the rest — including `layouts/_default/allpages.html`'s whole-site PRINT page, which inlines every page's content, and any page carrying `outputs: ["html", "print"]` (the `ai-101` handouts do). Guard the bulky assets; emit anything whose absence changes rendering — a print-hiding rule, say — unguarded per block. `pathtabs.html` does exactly this split.
- **Test a CentralRepo edit before merging with `docker build --build-arg LOCAL=true --target dev -t hugotester-local .`.** Both the normal dev and prod stages `ADD` the repo from GitHub, so they cannot see your working tree; `LOCAL=true` swaps in `COPY . /home/CentralRepo`. Mount the workshop repo read-only, which is safe because `local_copy.sh` only copies *out* of the mount and Hugo writes to `/home/CentralRepo/public`. Mount a host dir there too if you need the HTML.
- **The container writes `public/` as root, so a host-side `rm -rf public` fails halfway** — and a *partial* delete is worse than none, because the next build lands on top of stale files and looks fine. Clean it in a container: `docker run --rm -v "$PWD":/home/CentralRepo alpine:latest sh -c 'rm -rf /home/CentralRepo/public'`. Same trick unblocks `git worktree remove` on a worktree you built in.
- **A fresh `git worktree add` leaves `themes/hugo-theme-relearn` empty**, and relearn is what defines the `print` output format, so a build dies with `unknown output format "print" for kind "home"` — an error that looks like a config regression and is not. `cp -a` the theme in from a populated checkout.
- **`static.yml` has two roles and they are split:** `.github/workflows/static.yml` is CentralRepo's OWN build (`docker build -t fortinet-hugo . --target=prod` against its own Dockerfile); `scripts/static.yml` is the canonical template copied into workshop repos, which PULL the image from ECR and generally have no Dockerfile. `scripts/update_scripts.sh:14` and `batch_repo_update.py`'s `FILES_TO_COPY` both source `scripts/static.yml`. Edit the wrong one and you either break CentralRepo's build or ship a Dockerfile-dependent workflow to repos with no Dockerfile.
- **`batch_repo_update.py` is the executed contract; `repo_upgrade_spec.json` in the workshop repos is only documentation.** The script's hardcoded `FILES_TO_COPY` (`static.yml`, `Dockerfile`), `FILES_TO_DELETE` and `FOLDERS_TO_DELETE = ["docs"]` are what run, against `BRANCH = "main"`. It never reads the spec file, so the two drift silently. Read the script when predicting an upgrade.
- **`errorignore` beats `pageRef` for a `menu.shortcuts` local-URL WARN when the target is a non-page file** such as a PDF. Relearn's own warning text suggests `pageRef`, but `pageRef` resolves *pages*, so it cannot address e.g. `k8s-101.pdf`. The fix is `site.Params.errorignore`, a list of regexes honoured by `themes/hugo-theme-relearn/layouts/partials/_relearn/urlErrorReport.gotmpl:5`.
- **Non-active relearn tab panels are hidden by `themes/hugo-theme-relearn/assets/css/theme.css:2659-2673`** (`#R-body .tab-content{…display:none}`, `.tab-content.active{display:block}`) — **not** by `format-print.css`, whose only tab rules set print colours and never touch `display`. The hiding therefore applies in print too, because nothing there overrides it. The `format-print.css` attribution is a live mis-citation in two other repos' docs; don't propagate it.

### The deployment-path gate

- **It is pre-paint and CSS-only.** An inline synchronous `<script>` in `<head>` sets `<html data-deployment-path="…">` before `<body>` exists; every gating rule is CSS keyed off that attribute. **Nothing mutates the DOM after load** — that is what prevents the other path's steps flashing on screen before being hidden. Don't "improve" any of it into a `DOMContentLoaded` handler.
- **Two declaration scopes, resolved in exactly one place: `partials/pathgate/specs.gotmpl`.** `site.Params.deploymentPaths` (repoConfig.json) gates the whole workshop; `deploymentPaths` in a **page's front matter** gates that page's blocks and nothing else. Every consumer — `content-header.html`, `pathtabs`, `pathtab`, `pathonly` — calls the partial; none reads `site.Params.deploymentPaths` for content gating. The page form exists because UserRepo is cloned to start every new workshop, so a site param there is inherited by every new repo; front matter travels with the demo page and leaves when it is deleted.
- **Declaring both is a hard `errorf`, not a precedence rule.** There is one stored choice per reader per site (`<absBaseUri>/deployment-path`), so a page-local key lands in the same slot the site-wide gate reads back — every site-wide gated page would then fall through to default-deny and show nothing, with no error, because default-deny is also correct before a first choice.
- **The three site-wide behaviours stay bound to the site param alone.** In `custom-header.html` the sidebar loop, the prev/next CSS and the search `SCOPED` list all key off `$sitePaths` (the raw site param), never the resolved per-page vocabulary — filtering the whole site's navigation on one page's private list would hide pages the reader can legitimately reach. Same reason `deploymentPath` (singular) still requires the site param.
- **Content is default-deny; navigation is deliberately NOT.** A `pathonly`/`pathtab` block with no stored choice shows nothing. But with no choice the sidebar, prev/next and search show **everything** — a table of contents with pages silently missing reads as a broken build, not as a gate, and the reader has no way to tell which it is.
- **Every navigation rule only ever hides, via `:not(...)` — never force `display` back on.** Sidebar `<li>`s and `.topbar-button`s carry the theme's own responsive `display` rules; re-asserting `display` from the gate overrides them and breaks the mobile layout.
- **`:not(.active)` on the sidebar hide rule is load-bearing.** It keeps a foreign-path reader's *own* "you are here" entry, so the sidebar still highlights something. It leaks nothing — the `pathmiss` banner already names the mismatch, and an entry for the page on screen reveals no steps the reader can't see. `active` is the first class on the `<li>` (`menu.html:149,184,309,345`).
- **Key the sidebar rules on `partial "permalink.gotmpl" (dict "to" $p)`, never `.RelPermalink`.** With `disableExplicitIndexURLs = false` Hugo appends `index.html` to every section page's menu link, which `.RelPermalink` omits — the generated selector would match nothing and the page would stay visible to every path with **no error**. `data-nav-id` is the only page identity on the `<li>`, which is why three cases are hard `errorf`s rather than best-effort rules: an unknown `deploymentPath` key, combining `deploymentPath` with `menuPageRef`/`menuUrl` (menu.html keys the crosslink target instead), and a page with no permalink (rendered headless with `data-nav-id=""`, so the rule would hide every headless entry).
- **`deploymentPaths` keys must start with a letter and contain only letters, digits, hyphens and underscores** — they are interpolated into CSS class-name suffixes as well as attribute values. Enforced with an `errorf`.
- **`pathonly` must be called with `{{% %}}`, not `{{< >}}`.** `RenderString` has its own render context, so headings inside a `{{< >}}` call never join the page's fragment set and every in-page anchor to them silently breaks.
- **Blank lines around the wrapper `<div>` in `pathonly.html` are load-bearing.** A line starting with `<div` opens a CommonMark type-6 raw-HTML block that runs to the next blank line; without them the markdown body is swallowed as raw HTML and never rendered.
- **Search must be scoped or the rest is worthless** — a search hit is exactly the shortcut past a hidden sidebar. The gate wraps `relearn.search.adapter.search` (`custom-header.html:746-840`), which covers both callers: the dropdown (`search.js:178-181`) and the results page (`search.js:130-133`). Two constraints when touching it: the index is built **once** from `site.Home` (`dependencies/search.html:60-65`) and fed to two engines with independent field declarations (lunr `search-lunr.js:68-89`, orama's strict schema `search-orama-esm.mjs:32-56`), so a new field is a theme-wide change; and `index` is a reserved name lunr writes itself. The adapter is registered by a deferred script (`search-lunr.js:155-157`), so the wrap has to tolerate arriving first.
- **`auto-complete.js` caches on the raw input string and prunes by prefix on read** (`:152-154`, `:226-233`, `cache: 1` default), so a cached zero-result prefix short-circuits every longer term typed after it. A search fix that looks like it didn't apply is often this.
- **"Byte-identical output" cannot be compared naively.** Five tokens change on every build: the `?<digits>` asset cache-buster, `R-image-<md5>`, anonymous `data-tab-group=<md5>`, and the last-updated stamp — which needs **two** patterns, because it renders as a weekday string (`Wed, Aug 19, 2026 18:19:54 UTC`) and an ISO-only regex silently leaves it in and reports every page as changed. Sanity-check by building the baseline **twice**.

## Site Parameters (repoConfig.json)

```json
{
  "repoName": "MyWorkshop",        // Site ID, lowercased for fortisites cookie
  "workshopTitle": "...",           // Human-readable title for check-ins
  "themeVariant": "Xperts2025",    // CSS theme (case-sensitive match)
  "analyticsBaseUrl": "https://tecanalytics.forticloudcse.com",
  "quizUrl": "https://...",         // Base URL for quizframe shortcode
  "googleServicesID": "G-...",      // Google Analytics measurement ID
  "marketingCode": "",              // Optional event tracking code
  "videoHeaderSrc": "/videos/CloudsAnimated.mp4",  // CloudCSEMovie theme only
  "videoHeaderInterval": "60",      // Seconds between video play cycles
  "shortcuts": [...],               // Navigation menu items
  "deploymentPaths": [              // Optional. Path vocabulary for pathtabs/pathtab/pathonly
    { "key": "docker", "title": "Docker Compose" },
    { "key": "k8s",    "title": "Kubernetes / Helm" }
  ],
  "errorignore": ["^k8s-101\\.pdf$"]  // Optional. Regexes suppressing relearn URL warnings
}
```

- **`deploymentPaths`** — gates the whole workshop. Required by any page carrying a `deploymentPath` front-matter param, and by `pathtabs`/`pathtab`/`pathonly` unless the page declares its own `deploymentPaths` in front matter (page-scoped alternative; the two are mutually exclusive — see the gate section). **This is the single source of a repo's site-wide path vocabulary** — a consuming repo's tooling should derive its path list from here rather than hardcoding it. `key` is what `pathtab path="…"` matches; `title` is the tab label. **Order is load-bearing:** the first entry is the tab Hugo marks active server-side, so it is both the first-time default and the banner text with JS off. **Renaming a `title` silently resets every returning reader** — relearn keys the stored selection on `anchorize(title)` (`themes/hugo-theme-relearn/layouts/partials/shortcodes/tabs.html:42`), so old selections stop matching with no build error. Renaming a `key` is the loud kind of change: every `pathtab path=` must follow or the build fails.
- **`errorignore`** — list of regexes, matched unanchored with `findRE` against the offending URL in `themes/hugo-theme-relearn/layouts/partials/_relearn/urlErrorReport.gotmpl:5,15-19`. Site-wide across the link/image/include/openapi checks, so prefer an anchored pattern over `\.pdf$`.
- Both params are emitted by `scripts/templates/hugo.jinja` only when present and non-empty, so omitting them changes no existing site. Both are declared in `scripts/repoConfig.schema.json`; `deploymentPaths` entries are `additionalProperties: false` with `key` and `title` required.

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `image-build-push-dev.yaml` | Push to `dev`, minus `paths-ignore` | Build & push dev Docker image |
| `image-build-push-prod.yaml` | Push to `main`, minus `paths-ignore` | Build & push prod Docker image (`fortinet-hugo:latest`) |
| `versioning.yml` | — | Version management |
| `.github/workflows/static.yml` | Push to `main` | CentralRepo's own site build + GitHub Pages deploy (`docker build --target=prod`) |
| `scripts/static.yml` | (not a CentralRepo workflow) | Template copied into workshop repos; pulls the prod image from ECR |

- **`main` has `enforce_admins: true`** (2026-08-20, part of `ai-101` plan `plans/0004_...md`'s
  branch-protection hardening — an admin push used to bypass the PR requirement with only a warning;
  now it's a hard reject, same as everyone else). Required-check contexts are unchanged — still just
  the no-op `ci/jenkins/build-status` — deliberately left open rather than guessed at; see that plan's
  Open Questions.
- **Before making `ci.yml`'s `lint-and-validate`/`hugo-build` a required check, fix its `paths-ignore`
  first, or it will block every doc-only PR forever, not just until CI runs.** `ci.yml`'s
  `pull_request` trigger uses `paths-ignore: ["**.md"]` — a PR touching only `.md` files never makes
  the workflow run at all, so a required check with that name would simply never report on such a PR.
  GitHub treats "check never ran" as permanently blocking, not as "passing" or "pending" — a wait never
  fixes it. Hit for real in `ai-101` (`lint`/`handouts`, same shape, `paths:` not `paths-ignore`) the
  same day this repo's `enforce_admins` was flipped; fixed there by moving the path filtering from the
  trigger into a job step that still reports. Do the same here before requiring `ci.yml`.

## Common Tasks

**Add a new shortcode:** Create `layouts/shortcodes/<name>.html` (partial content only — no `<!DOCTYPE html>` wrapper), document params in README.md, test with `hugoServer_authorMode.sh` or against a real workshop repo via the `LOCAL=true` dev image. Never also land a copy in a workshop repo — `local_copy.sh` makes the local one win silently.

**Add or reorder a deployment path:** Edit `deploymentPaths` in the workshop repo's `scripts/repoConfig.json`, then add a matching `pathtab` to **every** `pathtabs` block in that repo — a block missing any configured path is a build `errorf`, deliberately, so no reader is shown another path's steps. Prefer appending: reordering changes every page's default path. Then check that repo's own tooling and workflows derive their path list from `repoConfig.json` rather than hardcoding it.

**Add a new theme variant:** Create `assets/css/theme-<Name>.css` with CSS custom property overrides, add a matching entry to the variants table in README.md, reference as `"themeVariant": "<Name>"` in repoConfig.json.

**Update shared partials:** Edit in `layouts/partials/` — changes propagate to ALL workshop sites on next Docker image build. Test thoroughly via the `LOCAL=true` dev image before merging to dev/main.

**Bump the Hugo version:** change the pin in `Dockerfile:15` in its own PR, build the `LOCAL=true` dev image against at least one real workshop repo, and diff the rendered output (see the byte-comparison gotcha) before merging. Never revert to an unpinned tag.

**Debug check-in issues:** Check browser cookies (`fortiuser`, `fortiemail`), verify CORS config on TEC Analytics API, check browser console for silent check-in errors.

**Promote dev → prod:** Merge `dev` → `main`; prod image build triggers automatically via `image-build-push-prod.yaml`.

## Testing

Tests live in `scripts/test/`. CI runs on push to `dev` and on PRs to `main`.

| Layer | Tool | What it catches |
|-------|------|----------------|
| Hugo build | hugomods/hugo:std | Template errors, deprecations, broken partials |
| HTML assertions | `test_rendered_html.sh` | Form action URLs, CSS paths, forbidden attributes |
| Regex validation | `validate_regex.js` | Chrome v-flag incompatible patterns |
| Config schema | `validate_config.py` | Missing required fields, invalid themeVariant |

**Run locally:** `bash scripts/test/run_tests.sh`
**Activate pre-push hook:** `git config core.hooksPath .githooks`
**Add a new HTML assertion:** edit `scripts/test/test_rendered_html.sh`
**Add to the config schema:** edit `scripts/repoConfig.schema.json`

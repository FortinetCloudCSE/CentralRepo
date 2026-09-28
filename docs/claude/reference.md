# Reference — Key File Map

> Detail doc for `CLAUDE.md`. Read to locate a partial/shortcode/script, not for gotchas (`gotchas.md`).

## Stack Quick Reference

| Layer | Tech | Notes |
|-------|------|-------|
| Static site generator | Hugo (`hugomods/hugo:std-0.165.0`, **pinned**) | Relearn theme (git submodule) |
| Templating | Go templates + Jinja2 (config gen) | `repoConfig.json` → `hugo.toml` |
| Build/Runtime | Docker multi-stage (dev/prod) | tini entrypoint, Python 3 for scripts |
| CI/CD | GitHub Actions (image build/push) | Also: Jenkins (legacy), AWS CodeBuild (legacy) |
| Hosting | AWS CloudFront + S3 (per-workshop) | CloudFormation templates in `pipeline/` |
| Security | FortiDevSec (SAST, secrets, SCA, IaC, container) | Fails pipeline at risk rating ≥7 |

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
    launchdemoform.html           — Lab provisioning via the Azure Durable Function backend (fortinet-on-demand-labs-provisioning-and-tracking); progress UI, credential display, single-attempt lock, reuse-across-series offer
    quizframe.html                — CTF quiz iframe with cookie propagation (NOT quizdown)
    figure.html                   — Responsive image with optional zoom
    ContainerFlow.html            — draw.io diagram renderer (mxGraph)
    FTNThugoFlow.html             — Fortinet-branded draw.io flow diagram
    fortihugorunner.html          — Dev harness shortcode (local testing only)
    Xperts24Banner.html           — Xperts 2024 themed banner
    Xperts25Banner.html           — Xperts 2025 themed banner
    Xperts26Banner.html           — Xperts 2026 themed banner
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
| `versioning.yml` | Push to `main`, or manual | Version tagging & release |
| `.github/workflows/static.yml` | Push to `main` | CentralRepo's own site build + GitHub Pages deploy (`docker build --target=prod`) |
| `scripts/static.yml` | (not a CentralRepo workflow) | Template copied into workshop repos; pulls the prod image from ECR |

## Common Tasks Detail

> Summary + always-apply constraints: `CLAUDE.md` → Common Tasks.

**Add a new shortcode:** Create `layouts/shortcodes/<name>.html` (partial content only — no `<!DOCTYPE html>` wrapper), document params in README.md, test with `hugoServer_authorMode.sh` or against a real workshop repo via the `LOCAL=true` dev image.

**Add or reorder a deployment path:** Edit `deploymentPaths` in the workshop repo's `scripts/repoConfig.json`, then add a matching `pathtab` to **every** `pathtabs` block in that repo — a block missing any configured path is a build `errorf`. Prefer appending: reordering changes every page's default path.

**Add a new theme variant:** Create `assets/css/theme-<Name>.css` with CSS custom property overrides, add a matching entry to the variants table in README.md, reference as `"themeVariant": "<Name>"` in repoConfig.json.

**Update shared partials:** Edit in `layouts/partials/` — changes propagate to ALL workshop sites on next Docker image build.

**Bump the Hugo version:** change the pin in `Dockerfile:15` in its own PR, build the `LOCAL=true` dev image against at least one real workshop repo, and diff the rendered output before merging. Never revert to an unpinned tag.

**Debug check-in issues:** Check browser cookies (`fortiuser`, `fortiemail`), verify CORS config on TEC Analytics API, check browser console for silent check-in errors.

**Promote dev → prod:** Merge `dev` → `main`; prod image build triggers automatically via `image-build-push-prod.yaml`. Watch for the squash-conflict and CI-skip-token gotchas: [gotchas.md](gotchas.md).

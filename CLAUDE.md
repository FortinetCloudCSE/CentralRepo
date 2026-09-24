# CLAUDE.md — CentralRepo

> Global preferences (planning workflow, code quality, operations): `~/.claude/CLAUDE.md`
> Copilot instructions: `.github/copilot-instructions.md` (detailed architecture & dev workflows)
> **On-demand docs** (read only when relevant — not auto-loaded):
> - [docs/claude/reference.md](docs/claude/reference.md) — Key File Map + full Site Parameters (repoConfig.json) reference
> - [docs/claude/gotchas.md](docs/claude/gotchas.md) — Critical Patterns (analytics/cookies, deployment-path gate, Docker/image build, UserRepo propagation), plus Working Branch + CI/CD incident history. Grep before touching any of those.

## Working Branch

`main` builds the **prod** ECR image; `dev` builds the **dev** image. Two routes into `main`, not equivalent:

1. **Dev-first (the documented route):** edit on `dev` → push (dev image rebuilds) → PR `dev` → `main` → prod image rebuilds. Use this when the change needs proving in a real workshop build first.
2. **Feature branch → PR → `main`** — fine only if already tested via the `LOCAL=true` dev image, and **you push `main` → `dev` in the same session afterward** (`git push origin origin/main:refs/heads/dev`, a fast-forward as long as nothing was committed to `dev` directly). Skipping the resync has caused real incidents — divergence invisible in dev-image test results, and a near-miss where a route-2 merge needed cancelling mid-image-build. Detail: [docs/claude/gotchas.md](docs/claude/gotchas.md#working-branch--incident-detail).

**Never push straight to `main` without a PR** — protected, and a bypass is logged. FortiDevSec SAST is broken/deprecated org-wide since 2026-08-25 — if `ci/jenkins/build-status` fails on an unrelated PR anywhere in the org, check the Jenkinsfile's `false`-guarded stage before assuming the PR is at fault.

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

Module map (layouts/partials, shortcodes, scripts, themes/): [docs/claude/reference.md](docs/claude/reference.md).

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

## Critical Rules

- **`google_analytics_authorMode.html` — NEVER DELETE.** `hugoServer_authorMode.sh` renames this to `google_analytics.html` at dev startup; delete it and dev server mode silently breaks.
- **Dual-repo pattern**: CentralRepo provides layouts/themes; UserRepo (workshop content) mounts to `/home/UserRepo` in Docker. Config flow: `repoConfig.json` → Jinja2 → `hugo.toml`.
- **`fortiemail` cookie has 2+ writers** (analytics_checkin form, launchdemoform's "Change Email") — a validation/escaping fix must land in both. Never render via `innerHTML`; exclude `<`, `>`, `"` but not `'`/backtick (valid RFC 5322 chars).
- **`quizframe.html` is the live CTF quiz iframe; `quizdown.html`/`carousel.html`/`orig_*.html` are dead code slated for deletion.**
- **Dockerfile fetches from GitHub at build time** — local file changes are NOT picked up without `LOCAL=true`.
- **Hugo base image is pinned (`Dockerfile:15`) — keep it pinned.** An unpinned tag once changed the renderer under 65 workshop repos with no commit to explain it.
- **`paths-ignore` on both image workflows is deliberately narrow** — `'*.md'` is root-level only. Anything under `scripts/`, `layouts/`, `assets/`, `i18n/`, `static/`, `archetypes/`, `themes/`, or the `Dockerfile` reaches the image. A wrong entry means a change ships to nobody with no visible failure.
- **Assume a push rebuilds the image unless you've checked `gh run list`** — reading the path filter is not the same as observing the trigger.
- **`launchdemoform`'s backend has three independent locks** (rate limiter, dedup/claim, per-email history) — a client-side fix only ever covers one. "This should be unblocked now" still not working means check which lock you're actually looking at.
- **CORS**: TEC Analytics `/checkin/silent` needs `CORS_ALLOW_ALL_DEV=1` on the API for dev origins.
- **`hugo.toml` is gitignored** — generated at container startup. Do not commit it.
- **`CLAUDE.md` is tracked — do not re-add it to `.gitignore`.** Root-level `*.md` is already excluded from image rebuilds, so committing costs nothing; it was ignored for months once and every session started blind.
- **Two-hop deploy path**: edit → merge to `main` → prod image rebuilds → each workshop repo picks it up on its *next* build. Don't debug a workshop site against an unbuilt CentralRepo commit.
- **A green image-build run is not proof `:latest` moved** — read the push step's log for the digest. `docker pull` on a tag you hold locally can serve a stale manifest; `docker rmi -f` first.
- **Dev image build is tied to the `dev` branch by name in two places that must agree**: the workflow's push trigger and the Dockerfile's `ADD`. Prod independently pins `#main`.
- **A push-triggered workflow's branch filter is evaluated from the pushed commit's own YAML**, not what was live before — editing a trigger's branch name in the same commit you push to the old branch means nothing fires.
- **Deleting a file via `batch_repo_update.py`'s `FILES_TO_DELETE` ≠ retiring it** — grep the org for content that still references it (shortcode calls) before adding anything, or repos accumulate a silent hard build failure.
- **`UserRepo` is a real template repo with protected `main`** — any automation touching it needs a PR flow. It's the single propagation point for both fixes and breakage into every future workshop repo.
- **A green Pages-deploy checkmark from before 2026-08-25 isn't proof a site built** — `docker wait` with no exit-code capture reported failed builds as CI success until then. Fixed org-wide.
- **Repo-local files shadow CentralRepo's, silently** — `local_copy.sh` does a non-recursive `cp` of UserRepo's shortcodes/partials over CentralRepo's. A repo-local `custom-header.html` replaces CentralRepo's outright, losing the whole deployment-path gate. Full detail in `README.md` → "Notes & gotchas".
- **A shortcode's `.Page.Store` guard is per page, NOT per output format** — a `once per page` asset block lands in whichever format builds first and is silently absent from the rest (e.g. `allpages.html`'s print page).
- **Clean `public/` inside a container, not on the host** — the container writes it as root; a partial host-side `rm -rf` fails halfway and the next build lands on stale files.
- **A fresh `git worktree add` leaves `themes/hugo-theme-relearn` empty** — `cp -a` the theme in from a populated checkout, or the build dies on `unknown output format "print"`.
- **`static.yml` has two roles, split**: `.github/workflows/static.yml` is CentralRepo's own build; `scripts/static.yml` is the canonical template copied into workshop repos. Edit the wrong one and you break the wrong thing.
- **`batch_repo_update.py` is the executed contract; `repo_upgrade_spec.json` in workshop repos is only documentation** — the script never reads the spec file, so they drift silently.
- **`errorignore` beats `pageRef` for a `menu.shortcuts` WARN on a non-page target** (e.g. a PDF) — `pageRef` only resolves pages.
- **Non-active relearn tab panels are hidden by `theme.css`, not `format-print.css`** — the print-file attribution is a live mis-citation in two other repos' docs, don't propagate it.
- **An `XpertsNNBanner` shortcode is a draw.io export with three nested encoding layers** — reproduce programmatically (build XML → `json.dumps` → `html.escape`), never hand-edit the giant single-line div.
- **A `dev`→`main` promotion here routinely trips `gh-merge-verify`'s CI-skip-token pre-flight even on a small clean diff** — old `[skip ci]` plan commits can still appear in the PR's commit ancestry. Fix: `-- --subject "..." --body "..."`, not `--allow-skip-token`.
- **Never write `htmlEscape` anywhere under `layouts/`** — CI assertion A11 greps for it and fails `dev`; use `transform.HTMLEscape`. Bit #115.
- **Promotion PR conflicts after a squash to `main`**: `main`'s squash copies conflict with `dev`'s originals. Merge `origin/main` into `dev` keeping `dev`'s side, push, wait for green `dev` CI, then re-run the promotion. Detail: [docs/claude/gotchas.md](docs/claude/gotchas.md#command--output-render-hooks).

Full incident history and the deployment-path gate's ~20 detailed rules (pre-paint CSS mechanics, `pathgate/specs.gotmpl`, sidebar/search scoping, `errorf` triggers): [docs/claude/gotchas.md](docs/claude/gotchas.md).

## Site Parameters (repoConfig.json)

`deploymentPaths` gates the whole workshop's path vocabulary (order is load-bearing — first entry is the default; renaming a `title` silently resets returning readers, renaming a `key` fails the build loudly). `errorignore` is a list of regexes suppressing relearn URL warnings for non-page targets. Full JSON shape + schema detail: [docs/claude/reference.md](docs/claude/reference.md#site-parameters-repoconfigjson).

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `image-build-push-dev.yaml` | Push to `dev`, minus `paths-ignore` | Build & push dev Docker image |
| `image-build-push-prod.yaml` | Push to `main`, minus `paths-ignore` | Build & push prod Docker image (`fortinet-hugo:latest`) |
| `versioning.yml` | — | Version management |
| `.github/workflows/static.yml` | Push to `main` | CentralRepo's own site build + GitHub Pages deploy (`docker build --target=prod`) |
| `scripts/static.yml` | (not a CentralRepo workflow) | Template copied into workshop repos; pulls the prod image from ECR |

`main` has `enforce_admins: true` — an admin push no longer bypasses the PR requirement. Detail on the `ci.yml` required-check `paths-ignore` trap: [docs/claude/gotchas.md](docs/claude/gotchas.md#cicd--detail).

## Common Tasks

**Add a new shortcode:** Create `layouts/shortcodes/<name>.html` (partial content only — no `<!DOCTYPE html>` wrapper), document params in README.md, test with `hugoServer_authorMode.sh` or against a real workshop repo via the `LOCAL=true` dev image. Never also land a copy in a workshop repo — `local_copy.sh` makes the local one win silently.

**Add or reorder a deployment path:** Edit `deploymentPaths` in the workshop repo's `scripts/repoConfig.json`, then add a matching `pathtab` to **every** `pathtabs` block in that repo — a block missing any configured path is a build `errorf`. Prefer appending: reordering changes every page's default path.

**Add a new theme variant:** Create `assets/css/theme-<Name>.css` with CSS custom property overrides, add a matching entry to the variants table in README.md, reference as `"themeVariant": "<Name>"` in repoConfig.json.

**Update shared partials:** Edit in `layouts/partials/` — changes propagate to ALL workshop sites on next Docker image build. Test thoroughly via the `LOCAL=true` dev image before merging to dev/main.

**Bump the Hugo version:** change the pin in `Dockerfile:15` in its own PR, build the `LOCAL=true` dev image against at least one real workshop repo, and diff the rendered output before merging. Never revert to an unpinned tag.

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

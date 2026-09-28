# CLAUDE.md — CentralRepo

> Global preferences (planning workflow, code quality, operations): `~/.claude/CLAUDE.md`
> Copilot instructions: `.github/copilot-instructions.md` (detailed architecture & dev workflows)
> **On-demand docs** (read only when relevant — not auto-loaded):
> - [reference.md](docs/claude/reference.md) — file map, stack table, CI/CD trigger table, Site Parameters/schema, Common Tasks detail.
> - [gotchas.md](docs/claude/gotchas.md) — grep before touching: analytics/cookies, the deployment-path gate (`pathgate`/`pathtabs`/`pathonly`/`custom-header.html`), Docker/image build, CI, `UserRepo` propagation, `launchdemoform`, a shortcode, or a `dev`→`main` promotion.

## Working Branch

`main` builds the **prod** ECR image; `dev` builds the **dev** image. Two routes into `main`, not equivalent:

1. **Dev-first (documented route):** edit on `dev` → push → PR `dev` → `main`. Use when the change needs proving in a real workshop build first.
2. **Feature branch → PR → `main`** — fine only if already tested via `LOCAL=true`, and **you push `main` → `dev` afterward in the same session** (`git push origin origin/main:refs/heads/dev`, fast-forward only). Skipping this resync has caused real incidents. Detail: [gotchas.md](docs/claude/gotchas.md#working-branch--incident-detail).

**Never push straight to `main` without a PR** — protected (`enforce_admins: true`), a bypass is logged. If `ci/jenkins/build-status` fails on an unrelated PR anywhere in the org, check for the deprecated FortiDevSec Jenkinsfile stage before assuming the PR is at fault (org-wide since 2026-08-25, [gotchas.md](docs/claude/gotchas.md)).

## Project in One Line

Shared Hugo partials, shortcodes, and themes consumed by all Fortinet CSE workshop sites —
centralizes check-in, analytics, quiz integration, and UX helpers into a Docker-based build system.

## Stack Quick Reference

Hugo (`hugomods/hugo:std-0.165.0`, pinned, Relearn theme submodule) + Go templates/Jinja2 config gen, built via multi-stage Docker, deployed via GitHub Actions to AWS CloudFront+S3 per workshop; FortiDevSec SAST/SCA/IaC gates the pipeline (fails at risk rating ≥7). Full stack table + module map (layouts/partials, shortcodes, scripts, themes/): [reference.md](docs/claude/reference.md).

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
- **Dual-repo pattern**: CentralRepo provides layouts/themes; UserRepo (workshop content, a protected-`main` template repo) mounts to `/home/UserRepo` in Docker — config flows `repoConfig.json` → Jinja2 → `hugo.toml`. **Repo-local files silently shadow CentralRepo's** (`local_copy.sh` `cp`s UserRepo's shortcodes/partials over CentralRepo's) — a repo-local `custom-header.html` loses the whole deployment-path gate. Full detail: `README.md` → "Notes & gotchas".
- **`quizframe.html` is the live CTF quiz iframe; `quizdown.html`/`carousel.html`/`orig_*.html` are dead code slated for deletion.**
- **Dockerfile fetches from GitHub at build time** — local file changes are NOT picked up without `LOCAL=true` (see Build & Run above).
- **Hugo base image is pinned (`Dockerfile:15`) — keep it pinned.** An unpinned tag once changed the renderer under 65 workshop repos with no commit to explain it.
- **`fortiemail` cookie has 2+ writers** (analytics_checkin form, launchdemoform's "Change Email") — a validation/escaping fix must land in both, never via `innerHTML`. CORS: TEC Analytics `/checkin/silent` needs `CORS_ALLOW_ALL_DEV=1` on the API for dev origins. Detail: [gotchas.md](docs/claude/gotchas.md).
- **Assume a push rebuilds the image unless you've checked `gh run list`** — `paths-ignore` on both image workflows is root-level `*.md` only, narrower than it looks. Dev image build is tied to the `dev` branch by name in two places that must agree (push trigger + Dockerfile `ADD`); prod pins `#main` independently.
- **Two-hop deploy path**: edit → merge to `main` → prod image rebuilds → each workshop repo picks it up on its *next* build — don't debug a workshop site against an unmerged commit. **A green image-build run or Pages-deploy checkmark is not proof it shipped** — check the push step's digest / build exit code; ECR Public can also serve a stale `:latest` to fresh runners for minutes after a prod push (re-run `gh workflow run static.yml` if `CloudCSE Version` looks stale, hit 2026-09-24).
- **`hugo.toml` is gitignored** (generated at startup, don't commit); **`CLAUDE.md` IS tracked — never re-add to `.gitignore`** (root `*.md` is excluded from image rebuilds, so this costs nothing; it was ignored for months once and every session started blind).

Full incident history, the `launchdemoform` triple-lock gotcha, and the deployment-path gate's ~20 detailed rules: [gotchas.md](docs/claude/gotchas.md).

## Site Parameters (repoConfig.json)

`deploymentPaths` gates the whole workshop's path vocabulary (order is load-bearing — first entry is the default; renaming a `title` silently resets returning readers, renaming a `key` fails the build loudly). `errorignore` is a list of regexes suppressing relearn URL warnings for non-page targets. Full JSON shape + schema detail: [reference.md](docs/claude/reference.md#site-parameters-repoconfigjson).

## CI/CD Workflows

Five workflows (dev/prod image build, versioning, CentralRepo's own Pages build, and the `scripts/static.yml` template copied into workshop repos) — full trigger table: [reference.md#cicd-workflows](docs/claude/reference.md#cicd-workflows). `main` has `enforce_admins: true` — an admin push no longer bypasses the PR requirement. `ci.yml` required-check `paths-ignore` trap: [gotchas.md](docs/claude/gotchas.md#cicd--detail).

## Common Tasks

New shortcode, new deployment path, new theme variant, shared-partial edit, Hugo version bump, check-in debugging, dev→prod promotion — step-by-step for each: [reference.md#common-tasks-detail](docs/claude/reference.md#common-tasks-detail). Always test via the `LOCAL=true` dev image before merging; never land a duplicate shortcode/partial copy in a workshop repo (`local_copy.sh` makes the local one win silently).

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

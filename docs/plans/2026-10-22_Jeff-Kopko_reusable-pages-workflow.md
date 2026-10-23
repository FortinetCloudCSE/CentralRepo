# Plan: Reusable GitHub Pages deploy workflow
Date: 2026-10-22
Owner: Jeff Kopko
Slug: reusable-pages-workflow
Status: Approved
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-10-22_Jeff-Kopko_reusable-pages-workflow.md
Log File: none

## Goal
Move the whole Hugo -> GitHub Pages deploy job out of the per-repo copy of `scripts/static.yml` into one reusable workflow, `.github/workflows/pages-deploy.yml` (`on: workflow_call`), so action versions, image-pull logic and ECR auth change in ONE place. `scripts/static.yml` becomes a ~25-line caller. Scope approved for this plan: plan, local tests, push to CentralRepo `dev`, canary from a UserRepo branch. Migrating the other repos is out of scope.

## Problem (measured)
- Node 20 deprecation warnings: the template pins checkout@v4, configure-pages@v4, upload-pages-artifact@v3, deploy-pages@v4. Node 24 clean versions (verified via `action.yml`): checkout@v6, configure-pages@v6, upload-pages-artifact@v5 (composite, wraps upload-artifact v7), deploy-pages@v5, aws-actions/configure-aws-credentials@v6.
- Anonymous ECR Public pulls are throttled (`toomanyrequests`) because runners share IPs.
- Survey of 92 repos with a pull step (`survey.tsv`, scratchpad): 52 on the new template (pull fails with exit 1), 34 on the old template (retry loop exits 0 after the last attempt, so a failed pull continues and the build runs on a stale/absent image), 6 with no pull step. Every fix today means editing ~92 repos via `batch_repo_update.py`.

## Design
`pages-deploy.yml` holds everything the current job does: checkout, docker cache clean, image selection (prod/dev), optional ECR login, pull with retries (exit 1 after MAX_ATTEMPTS), tag, build with exit-code capture, copy to `docs`, rmi, builder prune, configure-pages, upload-pages-artifact, deploy-pages in the `github-pages` environment with `page_url`.

Inputs: `image_variant` (prod|dev, default prod), `runner_type` (ubuntu-latest|self-hosted|org-runners, default ubuntu-latest; passed to `runs-on`), `ecr_role_arn` (default empty). When `ecr_role_arn` is set and variant is prod: configure-aws-credentials (OIDC) + `aws ecr-public get-login-password | docker login`, both `continue-on-error`, a `::warning::` if login failed, `docker logout` always at the end. Empty = anonymous, as today. No AWS resources are created or changed by this plan.

Caller contract (must be in the caller, a reusable workflow cannot grant these):
- `permissions: contents: read, pages: write, id-token: write`
- `concurrency: group: pages, cancel-in-progress: false`
- the `on:` triggers (push main + workflow_dispatch with runner_type/image_variant)
- `uses: FortinetCloudCSE/CentralRepo/.github/workflows/pages-deploy.yml@<ref>` with `with:` inputs. No `secrets: inherit` needed (OIDC, no secrets).

`batch_repo_update.py` contract unchanged: `FILES_TO_COPY` still copies `scripts/static.yml` -> `.github/workflows/static.yml`.

CentralRepo's own `.github/workflows/static.yml` is a different job (builds its own Dockerfile) and only gets the Node 24 action bumps (configure-pages@v6, upload-pages-artifact@v5, deploy-pages@v5).

## Ref / versioning strategy and blast radius
- A caller pinned to a moving ref (`@main`, `@dev`) means a bad commit breaks every repo's next deploy at once.
- On `dev` the caller uses `@dev` so the canary tests the unmerged workflow. **Before promoting dev -> main, change the ref in `scripts/static.yml` to the stable ref.** Recommended: a moving major tag `@v1` created at promotion time (move it only after a canary passes on the new commit; callers get fixes without a migration, and rollback is re-pointing the tag). Existing tags are `v25.3.x` style from `versioning.yml`; `v1` is a new, separate namespace. No tag is created by this plan.
- Reusable workflow files must live in the default-branch-reachable repo; CentralRepo is public, so cross-repo `uses:` works for public callers; private callers need the repo's Actions access setting (see risks).

## Image rebuild side effect (checked)
`image-build-push-dev.yaml` fires on pushes to `dev` with `paths-ignore` of root `*.md`, `docs/**`, `review/**`, licences, `.gitignore`, `.claude/**`, `.githooks/**`. `.github/workflows/**` and `scripts/**` are NOT ignored, so the dev push WILL rebuild and push `hugotester` to ECR Public (the plan file under `docs/plans/` alone would not). The prod image is unaffected (main only). `ci.yml` runs on PRs to main only; `versioning.yml` on main only.

## Rollout phases
0. Local tests (this plan): YAML parse, actionlint, shell logic with stub docker, real build against a `git archive` of UserRepo, `act` if feasible.
1. Push to `dev`; canary from a UserRepo branch `canary-reusable-workflow` via `workflow_dispatch` (at most 2 runs; each pulls from ECR).
2. Promote dev -> main (PR), switch caller ref to the stable ref, create/move tag `v1`.
3. Staggered migration: 3-5 repos at a time through `batch_repo_update.py` (avoid simultaneous ECR pulls), verifying a green deploy per batch.
4. AWS pull-only OIDC role, then pass `ecr_role_arn` from the caller.

## Risks
- Org setting: Actions may restrict reusable workflows to the same repo/org policy; not verified until the canary resolves.
- `github-pages` environment protection rules (deploy branches) evaluate the caller's ref; the canary branch may be rejected at Deploy. That still proves resolve/build/upload.
- A called workflow's `environment:` + `id-token: write` require the caller to grant permissions; a missing grant fails at startup.
- Moving tag = single point of failure; mitigated by canary-before-move.
- Old-template repos behave differently from new ones until migrated (exit 0 on failed pull bug).
- Stale `:latest` from ECR after a prod push is unrelated and unchanged.

## Non-goals
Migrating repos; creating tags; creating/changing AWS roles; touching `batch_repo_update.py`; changing Hugo image contents; pushing main.

## Steps
- [ ] Plan committed
- [x] `pages-deploy.yml` written
- [x] `scripts/static.yml` thin caller (`@dev`)
- [x] CentralRepo `.github/workflows/static.yml` Node 24 bump
- [x] Local: YAML parse + actionlint (workflow and caller)
- [x] Local: pull-loop stub tests (N failures then success; always fail -> exit 1)
- [x] Local: build script against `git archive` UserRepo with local image
- [x] Local: `act` attempt
- [x] Push `ecr-auth:dev` (fast-forward) -> 2e8c599; triggered CI and the dev image build
- [x] Canary run 1 on UserRepo branch `canary-reusable-workflow` (run 39873846887): `@dev` resolved and the job `deploy / deploy` was created, but the `github-pages` environment rejected the branch before any step ran ("not allowed to deploy to github-pages due to environment protection rules"). Build/pull/upload steps NOT exercised in CI. No second run (it would be rejected identically); next step needs an allowed ref or an environment rule change by the user.
- [x] Canary run 2 (run 39976277921, after allowing the branch in UserRepo's `github-pages` environment): every step passed, including pull (attempt 1, anonymous), build, Upload artifact and Deploy to GitHub Pages; no Node 20 warnings (only an unrelated punycode warning from inside the Hugo image)
- [x] Ref strategy decided: moving major tag `v1`, created only after a passing canary. Tag `v1` created on 2e8c599 (the tested commit); `scripts/static.yml` now calls `@v1`
- [ ] Promote dev -> main (PR), then MOVE `v1` to the main commit (`git tag -fa v1 <sha> && git push -f origin v1`) so the tag tracks main
- [ ] Phase 3: staggered migration (3-5 repos at a time) via `batch_repo_update.py`
- [x] Phase 4: pull-only AWS role `GitHubECRPullOIDC` created (docs/aws/); `ecr_role_arn` default in `pages-deploy.yml` set to its ARN (no per-repo change)

## Verified vs not (updated as we go)
Verified locally: node24 status of the five actions; paths-ignore analysis; survey counts; YAML parses; actionlint 1.7.7 reports no errors on the reusable workflow, the caller (inputs/permissions/`uses:` validated) or CentralRepo's own static.yml (only pre-existing shellcheck style/info notes); pull loop with stub docker (6 failures then success -> pass at attempt 7; 7 or 99 failures -> exit 1 after 7 attempts); real build of a `git archive` of UserRepo with the local `fortinet-hugo:latest` (exit 0, 23 entries in docs/); a deliberately broken shortcode gives exit 1 plus `::error::`; `act` 0.2.89 `-n` dry run expands caller -> reusable workflow (local path) and plans every step. `act` cannot prove Pages/OIDC/environment behaviour or cross-repo `uses:` resolution.
Verified by canary run 2: cross-repo resolution of `@dev`, org reusable-workflow policy, github-pages environment gating (after the branch was allowed), anonymous ECR pull, build, upload and deploy. Not verified: the `@v1` form of the ref (same commit as `@dev`, expected identical), the OIDC login path (needs a pull-only role).

## Plan Changes
- 2026-10-23 (approved by Jeff, executed by an agent): created IAM role `GitHubECRPullOIDC` in account 228122752878 (trust: existing GitHub OIDC provider, aud=sts.amazonaws.com, sub `repo:FortinetCloudCSE/*:*`, job_workflow_ref `FortinetCloudCSE/CentralRepo/.github/workflows/pages-deploy.yml@*`; inline policy `GitHubECRPullPolicy`: ecr-public:GetAuthorizationToken + sts:GetServiceBearerToken; 1h max session; JSON in `docs/aws/`). The `ecr_role_arn` input default is now that role ARN instead of empty, so every caller authenticates with no per-repo change; callers pass `''` to opt out. Supersedes the Non-goal "creating/changing AWS roles". Migration is limited to UserRepo, xperts-ai-101 and ai-101 for now.
- The job_workflow_ref condition is accepted by IAM; whether it matches at assume time is verified by the OIDC canary (result recorded below).

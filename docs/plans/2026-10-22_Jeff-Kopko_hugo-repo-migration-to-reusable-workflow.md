# Plan: Migrate the Hugo workshop repos to the reusable Pages workflow
Date: 2026-10-22
Owner: Jeff Kopko
Slug: hugo-repo-migration-to-reusable-workflow
Status: Complete
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-10-22_Jeff-Kopko_hugo-repo-migration-to-reusable-workflow.md
Log File: none

Follows [2026-10-22_Jeff-Kopko_reusable-pages-workflow.md](2026-10-22_Jeff-Kopko_reusable-pages-workflow.md) (Approved), whose Phase 3 ("staggered migration via `batch_repo_update.py`") this plan replaces with a safer method. Measured 2026-10-23 with read-only `gh api` / `gh repo list`; survey data in the session scratchpad (`master.tsv`, `waves.json`).

## Goal
Move every FortinetCloudCSE Hugo workshop repo that still carries its own ~120-line copy of `.github/workflows/static.yml` to the ~35-line caller `scripts/static.yml` (`uses: FortinetCloudCSE/CentralRepo/.github/workflows/pages-deploy.yml@v1`), so action versions, the ECR pull and OIDC login change in one place. Do it without a burst of simultaneous ECR Public pulls, without touching anything but one file per repo, and with a per-repo verification and a one-step rollback.

Scope: everything after the first three repos. **Out of scope here (owned by another session):** AWS pull-only role, dev->main promotion, moving tag `v1`, and migrating UserRepo, xperts-ai-101, ai-101 (in that order). **Precondition for Wave 1:** those three are done and green, `v1` points at the main commit, and the default `ecr_role_arn` in `pages-deploy.yml` (commit f7415bb on `ecr-auth`: `arn:aws:iam::228122752878:role/GitHubECRPullOIDC`) is live on `v1`.

## Problem (measured 2026-10-23)
- 92 of 130 org repos have a `.github/workflows/static.yml`. 86 pull the Hugo image from ECR; each carries its own copy of the pull/retry/build logic and Node 20 action pins.
- 33 copies are the **old** template (md5 1583cc75): the retry loop exits 0 after the last failed pull and the build step has no exit-code capture, so a throttled pull or a failed Hugo build still "deploys". Evidence this is live: GCP_Solutions (2026-10-09) and fortiweb-api-mcp-protection (2026-10-20, `toomanyrequests: Data limit exceeded`) have a failed latest run today.
- The 2026-10-09 org sweep moved ~55 repos to the new template inside ~5 minutes (17:53 to 17:58 UTC): 54 runs green, 1 red (GCP_Solutions). Anonymous pulls survive a burst most of the time, but not reliably. That is the reason for waves.

## Inventory (verified)
Source: `gh repo list` (130 repos: 0 archived, 3 forks, 20 private, 3 internal), then per repo the contents API for `static.yml` (md5 of the file), the recursive git tree (hugo config, `content/`, `fdevsec.yaml`, `scripts/repoConfig.json`, `docs/`, `Jenkinsfile`, `Dockerfile`), `pages`, the last 5 `static.yml` runs, `github-pages` environment branch policy, branch protection, and the live URL.

| Class | static.yml | Count | Action |
|---|---|---|---|
| New template | f0aff64a | 52 | migrate all 52 here |
| Old template | 1583cc75 | 33 | migrate 31 here (UserRepo and xperts-ai-101 are owned elsewhere) |
| Old pull + new build variant | ecf3e8e9 | 1 | ai-101, owned elsewhere |
| No pull step, builds its own Dockerfile | 9c3b7d70 (3), 0ed23f6a (1) | 4 | do NOT swap; manual decision |
| No pull step, publishes `./public` | ccf4b9dd | 1 | UserRepoDoc; do NOT swap; manual decision |
| CentralRepo's own build | 18dddd53 | 1 | out of scope (different job, already bumped) |
| **Has static.yml** | | **92** | |
| No static.yml | NONE | 38 | skip (not Hugo workshop sites; see below) |
| **All repos** | | **130** | |

Migrate-here total: **83 = 52 new + 31 old**. (The earlier survey said "92 with a pull step"; the correct figure is 92 with a static.yml and 86 with a pull step. The old-template count was 34 including ai-101's variant, 33 plus 1.)

**SCOPE RULE (Jeff, 2026-10-23): private and internal repos are NOT touched.** They cannot publish to GitHub Pages, so they are not active Hugo content. Two of the 83 candidates are private: **user-managed-scaling** (O1) and **FortiShield** (O9). They are EXCLUDED, so the migrate-here total is **81 = 52 new + 29 old**, and wave O9 is dropped. The private/internal rows elsewhere in this plan are listed for completeness only. The helper must refuse any repo whose `visibility` is not `public` (check at run time, not just from this list).

**Customizations a straight swap would lose: none among the 83.** All 83 are byte-identical to one of the two template versions (md5 equal), so triggers, runner, env vars and steps are exactly the template's. Verified. The 83 also all: default branch `main`, not archived, last push 2025-10-29 or newer, GitHub-hosted `ubuntu-latest` on the latest run (87 of the 87 repos that have a run; no self-hosted or org-runner use seen), `github-pages` environment allows branch `main` (across the 92: 79 main only, 11 also `gh-pages`, UserRepo also the canary branch, UserRepoDoc has no environment), Pages `build_type` workflow (4 report `legacy` with `/docs` but still serve fresh output, see Waves N2).

**"docs/ committed output instead":** none of the 83 serve from a committed `docs/`. Only cFOS-GKE-Workshop and FortiShield have a `docs/` in the tree, and both use `build_type: workflow`; CI `rm -rf docs` and re-copies inside the runner workspace, never commits. Verified for build type, not for what is in those two `docs/` folders.

### The 6 with no pull step (all excluded from the swap)
| repo | md5 | what it is | last push | Pages | runs ever | decision |
|---|---|---|---|---|---|---|
| CentralRepo | 18dddd53 | builds its own Dockerfile (`--target=prod`) | 2026-10-23 | workflow | active | out of scope; own job |
| style-guide | 0ed23f6a | builds its own Dockerfile, old actions, no pull | 2025-05-22 | workflow, 200 | **0** static.yml runs | manual: site not deployed by this file |
| fortimanager-cloud-deployments | 9c3b7d70 | Dockerfile build, mounts layouts/content/config.toml, root `config.toml`, no repoConfig.json | 2024-06-28 | workflow, 200 | **0** | manual: needs the full UserRepo upgrade, not a file swap |
| FortiWeb-Advanced-Threat-Lab | 9c3b7d70 | same legacy form | 2024-07-17 | none, 404 | **0** | skip (dormant, Pages off) |
| advanced-routing-sdwan-azure | 9c3b7d70 | same legacy form | 2023-11-16 | none, 404 | **0** | skip (dormant, Pages off) |
| UserRepoDoc | ccf4b9dd | no build at all, uploads `./public` | 2023-05-10 | none, 404 | **0** | skip (dormant; no environment) |

Straight-swapping any of these would make the shared workflow build with the prod image a site that was built another way (config.toml layout, own Dockerfile). Zero runs ever means the workflow file is dead, so there is nothing to protect by leaving it and nothing to gain by changing it. Question for Jeff: delete the dead `static.yml` in these 5, or upgrade the two live sites (style-guide, fortimanager-cloud-deployments) properly.

### The 38 with no static.yml (skip all)
None is a Hugo workshop site served by the template: no root hugo config plus `content/` except DevSecDemo (abandoned 2024-02, Pages off, Dockerfile). Classified from tree contents and workflow filenames; workflow bodies were not opened (Likely, not Certain). Seven have Pages on without a static.yml (Jenkins or an old deploy; not investigated). Two have a non-main default branch (ctf_api `jkopkoEdits`, ftg_poc `master`); three are forks.

Full list of the 38 (category assigned by me from tree flags and workflow filenames):

*Hugo-like but abandoned (skip)* (1)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| DevSecDemo | PUBLIC | 2024-02-05 | NOPAGES | cfg,content,fdevsec,docs,jenkins,dockerfile,; workflows: main.yml, |

*Pages configured, no static.yml, no Hugo content (Jenkins/other deploy or stale Pages)* (7)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| diagram-studio | PRIVATE | 2026-10-06 | workflow | fdevsec,jenkins,; workflows: - |
| forticnp-api | PUBLIC | 2024-01-11 | workflow | fdevsec,jenkins,; workflows: - |
| fortigate-ipsec | PUBLIC | 2024-01-11 | workflow | fdevsec,jenkins,; workflows: - |
| workfront-api-scripts | PUBLIC | 2023-12-21 | workflow | fdevsec,jenkins,; workflows: - |
| fortiflexvm-api | PUBLIC | 2026-10-09 | workflow | jenkins,; workflows: lacework-code-security-pr.yml, |
| GCP_Solutions_Terraform | PUBLIC | 2025-04-21 | legacy | fdevsec,jenkins,; workflows: - |
| workshops-dev | PUBLIC | 2024-07-31 | legacy | -; workflows: - |

*Jenkins-only scripts/infra, no Pages* (8)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| GCP-WorkshopAccountProvisioning | PRIVATE | 2023-11-28 | NOPAGES | fdevsec,jenkins,; workflows: - |
| GCP-supporting-resources | PUBLIC | 2024-01-02 | NOPAGES | fdevsec,jenkins,; workflows: - |
| fortigate-terraform-deploy (fork) | PUBLIC | 2024-08-05 | NOPAGES | fdevsec,jenkins,; workflows: - |
| aws-cloudformation-templates (fork) | PUBLIC | 2023-12-14 | NOPAGES | fdevsec,jenkins,; workflows: - |
| DevOps-SW-Dev-Process | PRIVATE | 2023-11-21 | NOPAGES | -; workflows: - |
| GCP-FortiEDRMarketplaceListing | PRIVATE | 2023-10-10 | NOPAGES | -; workflows: - |
| ctf | PRIVATE | 2025-06-26 | NOPAGES | -; workflows: - |
| inventory | PRIVATE | 2024-06-18 | NOPAGES | -; workflows: update-inventory.yaml, |

*Application / service repos with their own CI* (11)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| TEC-analytics | PRIVATE | 2026-10-23 | NOPAGES | docs,; workflows: _build-deck-prod.yml,_deploy-analytics-cr.yml,_deploy-hub.ym |
| ftg_saas | PRIVATE | 2026-10-22 | NOPAGES | docs,; workflows: build-and-push.yml,demo-images.yml,deploy-prod.yml,deploy-st |
| SMARTUnassigned_toTrello | PRIVATE | 2026-10-21 | NOPAGES | docs,dockerfile,; workflows: lacework-code-security-pr.yml,nightly.yml,test.yml, |
| cloudcse-fortiflex-marketplace | PRIVATE | 2026-09-24 | NOPAGES | docs,; workflows: lacework-code-security-pr.yml,version.yml, |
| fortinet-on-demand-labs-provisioning-and-tracking | PRIVATE | 2026-09-01 | NOPAGES | fdevsec,docs,jenkins,; workflows: deploy.yml, |
| ctf_api | INTERNAL | 2026-08-22 | NOPAGES | docs,dockerfile,; workflows: - |
| ftg_poc | PRIVATE | 2026-10-04 | NOPAGES | docs,; workflows: - |
| vending-machine-poc (fork) | PUBLIC | 2025-11-04 | NOPAGES | -; workflows: build-deploy.yml, |
| FortiShield-MSK | PRIVATE | 2026-10-15 | NOPAGES | docs,; workflows: lacework-code-security-pr.yml, |
| FortiShield-CNAPP-to-MSK | PRIVATE | 2026-10-15 | NOPAGES | -; workflows: lacework-code-security-pr.yml, |
| FortiShield-CloudWatch-to-MSK | PRIVATE | 2026-10-15 | NOPAGES | -; workflows: lacework-code-security-pr.yml, |

*Env-build / infra automation (Terraform etc.)* (6)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| xperts-ai101-env-build | INTERNAL | 2026-10-21 | NOPAGES | -; workflows: ai101.yml, |
| xperts-appsec-103-203-env-build | PUBLIC | 2026-08-22 | NOPAGES | -; workflows: lacework-code-security-pr.yml,terraform.yml, |
| xperts-data-security-101-env-build | PUBLIC | 2026-10-20 | NOPAGES | -; workflows: dlp101.yml,lacework-code-security-pr.yml, |
| xperts-public-cloud-202-302-env-build | PUBLIC | 2026-08-22 | NOPAGES | -; workflows: azure-202.yml,azure-302.yml,lacework-code-security-pr.yml, |
| gha-arc-deployment-eks | PUBLIC | 2025-09-11 | NOPAGES | -; workflows: - |
| fortinet-microsoft-innovation-hub-azure-vwan-fortigates | PUBLIC | 2026-08-22 | NOPAGES | -; workflows: lacework-code-security-pr.yml, |

*Tooling / org config* (5)

| repo | visibility | last push | Pages | tree hints |
|---|---|---|---|---|
| fortihugorunner | PUBLIC | 2026-10-09 | NOPAGES | fdevsec,docs,jenkins,; workflows: auto-release.yml,lacework-code-security-pr.yml,pr-checklist. |
| ClaudeTemplate-jkopko | PRIVATE | 2026-10-10 | NOPAGES | docs,; workflows: lacework-code-security-pr.yml, |
| .github | PUBLIC | 2026-09-11 | NOPAGES | -; workflows: lacework-code-security-pr.yml, |
| utility-scripts-and-workflows | INTERNAL | 2026-08-22 | NOPAGES | -; workflows: lacework-code-security-pr.yml,powershell-azure-tap.yml, |
| cicd-utilities | PUBLIC | 2026-08-22 | NOPAGES | -; workflows: lacework-code-security-pr.yml, |

## Migration method
**Recommended: one direct commit of one file per repo**, `scripts/static.yml` taken from the `v1`-tagged CentralRepo commit (`git show v1:scripts/static.yml`) into `.github/workflows/static.yml`, via the Contents API (`gh api -X PUT repos/O/R/contents/.github/workflows/static.yml` with the current blob `sha`), on the default branch `main`. A new helper `scripts/migrate_static_yml.sh` (or `.py`) in CentralRepo does, per repo: (1) pre-flight: default branch is `main`, file md5 is f0aff64a or 1583cc75 (anything else aborts that repo), last `static.yml` run state recorded; (2) append `repo, old blob sha, old md5` to a ledger file; (3) PUT the file; (4) print the new commit sha and run id. Dry-run is the default; `--apply` is explicit. The helper does not exist yet (plan step).

Why **not** `batch_repo_update.py`, even though `FILES_TO_COPY` still lists `scripts/static.yml`: it is an all-or-nothing tree rewrite, not a static.yml updater. For every repo in `REPOS` it also:
- overwrites the repo's `Dockerfile` with CentralRepo's (hits GCP-FortiGate-protecting-resources and FortiShield, which have their own);
- deletes `scripts/docker_*.sh`, `docker-compose.yml`, `hugo.toml`, `config.toml`, the shortcode `layouts/shortcodes/FTNThugoFlow.html`, and every blob under `docs/` (cFOS-GKE-Workshop and FortiShield have one);
- converts `config.toml` to `scripts/repoConfig.json` or writes a default one if absent;
- replaces `README.md` with a generated Pages link page when Pages is enabled (destroys any hand-written README);
- PATCHes custom properties (`hugo-content-version=Hugo-v2.1`, `function=Workshop`);
- hardcodes `BRANCH = "main"` (not the repo's default branch), has `REPOS = ['']` as a placeholder, no dry run, a bare `except:` that prints a generic message and continues, and a dead `os.exit(1)` (`os.exit` does not exist), so a failure leaves no trace.
It also reads the file from the working directory, so the version it ships depends on which CentralRepo branch happens to be checked out. A static.yml-only change needs none of that, and the unrelated edits widen the blast radius and break the "revert the single file" rollback.

Considered and rejected: adding a `--only static.yml` flag to the script (the plan keeps `batch_repo_update.py` untouched, as the parent plan's non-goals say; a 40-line helper is simpler to audit than a flag threaded through a 400-line script that has a bare `except`).

**Branch protection finding (affects the method).** 87 of 92 `main` branches are protected: PR required (0 approvals) plus the status check `ci/jenkins/build-status`, `enforce_admins: false`, so an admin direct commit goes through (precedent: the 2026-10-09 sweep pushed straight to `main`). Unprotected: FortiWeb-Advanced-Threat-Lab, advanced-routing-sdwan-azure, fortiGrepWorkshop, OCI_Solutions, cFOS-GKE-Workshop. Token scopes: `repo`, `workflow` (needed to write `.github/workflows`). Default: direct admin commit. Fallback if a repo rejects it: PR from a branch, wait for Jenkins, `gh-merge-verify <pr> --repo FortinetCloudCSE/<r> --method squash` (a Jenkins wait per repo roughly doubles that repo's time; unmeasured). Whether direct commits to protected `main` on ~80 repos is acceptable is an open question for Jeff (Q1).

The commit on `main` is itself the verification run: a `push: main` event triggers `static.yml`, so no `workflow_dispatch` is needed. The commit message must not contain `[skip ci]`.

## Wave design
Goals: never more than one migration deploy in flight; low-risk first; most-used repos last; each wave proves something the next one relies on.

Rules (all waves):
1. **Strictly sequential inside a wave.** Commit repo k only after repo k-1's run is `completed/success` and its live URL answers 200. Waves of 3-5 (sizes below), no gap needed between waves unless a pause rule fires; a human gate only after N1, after N2, after O1 and before FortiShield.
2. Before each wave: `gh run list -R FortinetCloudCSE/CentralRepo -w image-build-push-prod.yaml -L1` is not `in_progress` (a prod push moves `:latest`; the 2026-09-24 stale-`:latest` window), and githubstatus.com has no Actions/Pages incident.
3. Order inside a class is by activity ascending (static.yml run count as the proxy, then last push), with named flagship workshops and anything pushed in the last 7 days moved to the final waves of the class. The proxy is a judgment call (Guessing for "flagship").
4. **New-template class first** (N1-N11): the build logic is already identical (exit-code capture, exit 1 on pull failure), so the only differences are Node 24 action versions, the shared workflow itself, and the OIDC login. **Old-template class second** (O1-O9): additionally switches on exit-code-checked builds, so latent Hugo errors that were silently deployed may surface as red runs.
5. Hold-out repos (manual review list below) are not in any wave until decided.

Pause rules (stop committing, keep what is done, investigate, then resume or abort):
- a run ends red for any reason not already listed in the repo's note;
- a run is `queued` more than 10 minutes or a step runs more than 3x the measured maximum (2.3 min of runner time);
- the log shows `toomanyrequests` on the first pull attempt twice in one wave (pull throttling returned, or the OIDC login is not helping: see rollback 3);
- `Login to ECR Public` is not `success` on two consecutive repos (role/trust problem);
- live site not 200, or `Last-Modified` older than the run start, after a green run.
Abort criteria (stop the whole migration, roll back per section below): any `startup_failure` or a failure to resolve `...pages-deploy.yml@v1` (`v1` wrong or org policy changed); two repos in different waves red for the same non-content reason; a deploy that publishes visibly broken output.

Content errors in old-template repos (Hugo exits non-zero) are **not** a reason to roll back: the old template deployed whatever `public/` held after a failed build (that is the 2026-08-25 gotcha). The new run fails before upload and leaves the previous live site in place. Keep the caller, record the repo and the error in the ledger, and file the content fix with the repo owner.

### Wave lists
Columns: `static.yml` = current version; customizations = diff of the repo's file against the template version it matches; Pages = build type (and HTTP status if not 200); risk as defined in the notes column. All times are UTC dates of the last push to the default branch.

**Wave N1** (4 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | Code-Security-Workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | FortiADCIntro | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | FortiCNF | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | cloud-architectures | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N2** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | Forti-ProductXYZ | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | legacy | low; Pages API says legacy (/docs) but site is fresh (Last-Modified = last deploy); verify freshness after |
| 2 | FortiDevOps-v2025 | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | legacy | low; Pages API legacy (/docs); verify freshness after |
| 3 | OCI_Solutions | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | legacy | low; Pages API legacy (/docs); main unprotected; verify freshness after |
| 4 | gcp-ncc-mrr-fortigate | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | legacy | low; Pages API legacy (/docs); verify freshness after |
| 5 | cFOS-GKE-Workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; root Hugo config + committed docs/ (overwritten in CI workspace only); main unprotected |

**Wave N3** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | FGCP-in-AWS | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | FortiGate-AWS-Autoscale-TEC-Workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | FortiGate-AWS-Autoscale-TEC-Workshop-Backup | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | getting-started-general | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | FortiCloud-Orgs-FortiFlex | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N4** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | FortiGate-AWS-CNF-TEC-Workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | FortiSASE | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | GWLB-in-AWS | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | forticnapp-code-security-demo | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | fortigate-azure-sdwan-networking-workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N5** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | technical-recipe-azure-fweb-ztna-fortisoar | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | FortiCNAPPRoadshow | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | GCP-FortiGate-protecting-resources | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; repo has a Dockerfile (unused by template); batch script would overwrite it |
| 4 | MGMT-in-AWS | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | fortigate-aws-vpc-routeserver-active-active-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N6** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-aws-vpc-routeserver-ha-dual-az-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | FortiWeb-Azure-ZTNA-FortiSoar | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | fortigate-aws-standalone-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | fortimanager-aws-ha-dualaz-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | fortianalyzer-aws-ha-dualaz-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N7** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortianalyzer-aws-ha-singleaz-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | fortianalyzer-aws-standalone-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | fortimanager-aws-ha-singleaz-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | fortimanager-aws-standalone-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | api-and-websvc-fundamentals | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N8** (3 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-automation-stitch-workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | fortigate-aws-ha-dualaz-terraform | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | fortiweb-threat-protection | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N9** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | k8s-201-workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; flagship workshop |
| 2 | k8s-202-workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; flagship workshop |
| 3 | AWS-FGT-101 | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; flagship workshop |
| 4 | fortigate-aws-ha-dualaz-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-22 | workflow | low; pushed 10-22 |
| 5 | AWS-FGT-201 | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; flagship workshop |

**Wave N10** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-aws-gwlb-cloudformation | new (f0aff64a) | none (byte-identical to template) | 2026-10-22 | workflow | low; pushed 10-22 |
| 2 | fortigate-aws-gwlb-terraform | new (f0aff64a) | none (byte-identical to template) | 2026-10-22 | workflow | low; pushed 10-22 |
| 3 | Public-Cloud-104-CNAPP | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 4 | azure-102-foundational | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 5 | AppSec103-203-FortiADC | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |

**Wave N11** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortiweb-security-foundations-201 | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 2 | azure-202-advanced | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low |
| 3 | PublicCloud105-FortiFlex | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; 34 runs |
| 4 | k8s-101-workshop | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; flagship workshop; main allows force-push |
| 5 | Autoscale-Simplified-Template | new (f0aff64a) | none (byte-identical to template) | 2026-10-09 | workflow | low; 58 runs (most active new-template repo) |

**Wave O1** (3 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | FortiDevOps | old (1583cc75) | none (byte-identical to template) | 2026-04-01 | workflow | low-med (first exit-code-checked build); oldest push in class (2026-04-01) |
| 2 | data-security-101 | old (1583cc75) | none (byte-identical to template) | 2025-10-29 | workflow | low-med (first exit-code-checked build); last push 2025-10-29 (~12 months) |
| 3 | ~~user-managed-scaling~~ EXCLUDED (private) | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow/HTTP 301 | med; PRIVATE repo, private Pages domain (301); first private caller of public CentralRepo workflow - unverified |

**Wave O2** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortiGrepWorkshop | old (1583cc75) | none (byte-identical to template) | 2026-10-08 | workflow | low-med (first exit-code-checked build); main unprotected |
| 2 | SASE-203-CASB | old (1583cc75) | none (byte-identical to template) | 2026-08-25 | workflow | low-med (first exit-code-checked build) |
| 3 | fortiaigate-demo-runbook | old (1583cc75) | none (byte-identical to template) | 2026-08-25 | workflow | low-med (first exit-code-checked build) |
| 4 | genai-creator-lab2 | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |
| 5 | FortiCNAPP-Securing-Public-Cloud | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | low-med (first exit-code-checked build) |

**Wave O3** (5 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-aws-tgwconnect-ha-dualaz-terraform | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |
| 2 | fortigate-aws-cwanconnect-active-active-terraform | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |
| 3 | fortigate-aws-tgwconnect-active-active-cloudformation | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | low-med (first exit-code-checked build) |
| 4 | fortigate-aws-tgwconnect-ha-dualaz-cloudformation | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | low-med (first exit-code-checked build) |
| 5 | fortigate-aws-tgwconnect-active-active-terraform | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |

**Wave O4** (3 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-aws-cwanconnect-ha-dualaz-terraform | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |
| 2 | oci-solutions | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | low-med (first exit-code-checked build) |
| 3 | gcp-fgt-stitch-fun | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |

**Wave O5** (3 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | GCP_Solutions | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | med; latest run FAILED 2026-10-09 (ECR toomanyrequests; old template); live site is the previous build |
| 2 | zero-touch-provisioning | old (1583cc75) | none (byte-identical to template) | 2026-08-25 | workflow/HTTP 404 | med; live site 404 at baseline (Pages on, deploys green) - investigate before judging verify |
| 3 | ai-102-with-fortiappsec | old (1583cc75) | none (byte-identical to template) | 2026-08-25 | workflow/HTTP 404 | med; live site 404 at baseline (Pages on, deploys green) - investigate before judging verify |

**Wave O6** (4 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | fortigate-aws-cwanconnect-ha-dualaz-cloudformation | old (1583cc75) | none (byte-identical to template) | 2026-10-22 | workflow | low-med (first exit-code-checked build); pushed 10-22 |
| 2 | fortigate-aws-cwanconnect-active-active-cloudformation | old (1583cc75) | none (byte-identical to template) | 2026-10-22 | workflow | low-med (first exit-code-checked build); pushed 10-22 |
| 3 | fortigate-aws-ha-singleaz-cloudformation | old (1583cc75) | none (byte-identical to template) | 2026-10-22 | workflow | low-med (first exit-code-checked build); pushed 10-22 |
| 4 | demo-ha-env | old (1583cc75) | none (byte-identical to template) | 2026-10-21 | workflow | low-med (first exit-code-checked build); pushed 10-21 |

**Wave O7** (4 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | Reducing-Risk-111-CNAPP | old (1583cc75) | none (byte-identical to template) | 2026-09-15 | workflow | low-med (first exit-code-checked build) |
| 2 | AWS-FGT-301 | old (1583cc75) | none (byte-identical to template) | 2026-09-23 | workflow | low-med (first exit-code-checked build) |
| 3 | fortinet-ui-terraform | old (1583cc75) | none (byte-identical to template) | 2026-10-09 | workflow | low-med (first exit-code-checked build) |
| 4 | genai-creator-lab | old (1583cc75) | none (byte-identical to template) | 2026-08-22 | workflow | low-med (first exit-code-checked build) |

**Wave O8** (3 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | AIAppSecurity-lab | old (1583cc75) | none (byte-identical to template) | 2026-10-02 | workflow | low-med (first exit-code-checked build); 29 runs |
| 2 | faig-training-workshop | old (1583cc75) | none (byte-identical to template) | 2026-09-23 | workflow | low-med (first exit-code-checked build); 48 runs; Day-2 follow-on of xperts-ai-101 |
| 3 | fortiweb-api-mcp-protection | old (1583cc75) | none (byte-identical to template) | 2026-10-20 | workflow | med; latest run FAILED 2026-10-20 (ECR toomanyrequests: Data limit exceeded); active (pushed 10-20) |

**Wave O9** (1 repos, sequential in this order)

| # | repo | static.yml | customizations | last push | Pages | risk / note |
|---|---|---|---|---|---|---|
| 1 | ~~FortiShield~~ EXCLUDED (private) | old (1583cc75) | none (byte-identical to template) | 2026-10-23 | workflow/HTTP 301 | HIGH; PRIVATE, private Pages domain; 1485 runs (hot), Dockerfile + committed docs/; last-hour activity |

### Why these waves (what each proves)
- **N1** (4 quietest new-template repos, 2 runs each): proves the `@v1` caller and OIDC login from repos other than UserRepo. Human gate after it.
- **N2** (5): the four repos whose Pages API still says `legacy` (`/docs`) but whose live output is fresh (Last-Modified within the 2026-10-09 deploy), plus cFOS-GKE-Workshop (root Hugo config, committed `docs/`). Proves the deploy path really owns the site. Human gate after it.
- **N3-N8**: bulk of the new-template class, ascending activity. GCP-FortiGate-protecting-resources (own Dockerfile, unused) sits in N5.
- **N9-N11**: flagship workshops and everything pushed on 2026-10-22 or with 18+ runs.
- **O1**: the first old-template repos. FortiDevOps and data-security-101 are the oldest/quietest; user-managed-scaling is the only private repo before FortiShield, so it also answers "can a private caller use the public reusable workflow" (Likely yes, per GitHub docs; Unverified here). Human gate after it.
- **O2-O4**: bulk old-template, ascending activity.
- **O5**: the three repos whose baseline is already bad (GCP_Solutions red since 10-09; zero-touch-provisioning and ai-102-with-fortiappsec serve 404 at the Pages root even though deploys are green). Run them after the old-template semantics are proven on 16 repos, and read their result as "unchanged baseline" rather than pass/fail until the baseline is understood.
- **O6-O8**: repos pushed 10-21/10-22, then the busiest old repos; fortiweb-api-mcp-protection (red since 10-20, active) is the last of O8.
- **O9**: FortiShield alone, with Jeff present: private, 1485 runs, pushed the day of measurement, Dockerfile and `docs/` in tree.

### Manual-review list (not in any wave until decided)
| repo | why | proposed handling |
|---|---|---|
| style-guide, fortimanager-cloud-deployments | live sites, but `static.yml` never ran and is the legacy Dockerfile form | decide: delete the dead file, or full UserRepo upgrade (repoConfig.json etc.) as its own task |
| FortiWeb-Advanced-Threat-Lab, advanced-routing-sdwan-azure, UserRepoDoc | dormant since 2023-24, Pages off, 0 runs | leave; optional cleanup |
| DevSecDemo | Hugo-like, no static.yml, abandoned | leave |
| GCP_Solutions, fortiweb-api-mcp-protection | latest run red (ECR throttle) | migrate in O5/O8; migration commit doubles as the re-run. If it is still red after an authenticated pull, it is a content problem |
| zero-touch-provisioning, ai-102-with-fortiappsec | Pages root 404 at baseline | check the Hugo baseURL/subpath before migrating; migration should not change the result |
| user-managed-scaling, FortiShield | private | see O1/O9; verify the live URL as a logged-in user (the 301 goes to a private pages.github.io host) |
| ai-101 | variant ecf3e8e9 (old pull + new build) | owned by the other session |

Repos "already new" (52, md5 f0aff64a) need no reconciliation: the swap changes only the file text; their pull and build semantics are unchanged by design. No repo had a customized or unknown static.yml.

## Verifying each repo
Run after each commit (scripted in the helper, one line of output per repo):
1. **Caller resolved `@v1`:** `gh api repos/O/R/actions/runs/$ID --jq '.referenced_workflows[].path'` shows `FortinetCloudCSE/CentralRepo/.github/workflows/pages-deploy.yml@refs/tags/v1`, and its `sha` equals `git rev-parse v1^{commit}` of the current tag. A job named `deploy / deploy` exists.
2. **ECR login:** in `gh api repos/O/R/actions/runs/$ID/jobs`, steps `Configure AWS credentials (ECR Public pull)` and `Login to ECR Public` are `success`, and `Warn if pulling anonymously` is `skipped`. (Valid while the default `ecr_role_arn` is set; if it is blank these are `skipped` and the run is anonymous.) `Pull image (with retries)` log shows success on attempt 1.
3. **Deploy green:** `gh run watch $ID --exit-status` returns 0; `Deploy to GitHub Pages` is `success`; the `github-pages` environment shows a new deployment for the commit.
4. **Live site:** `curl -sI https://fortinetcloudcse.github.io/R/` is 200 and `Last-Modified` is later than the run's `run_started_at` (public repos). For private repos open the Pages URL logged in. Compare the footer `CloudCSE Version` with the current prod image version (the stale-`:latest` check from CentralRepo's gotchas).
5. **No Node 20 annotation:** the run's annotations contain no "Node.js 20 actions are deprecated" message (the punycode/`url.parse` DEP warnings come from inside the Hugo image and are expected).
Ledger line per repo: `repo, old md5, new commit sha, run id, result, http code`.

## Rollback
1. **Single repo:** revert the one file: PUT the previous content back (ledger holds the old blob sha; the known-good new template is `git show bdf719e:scripts/static.yml`, md5 f0aff64a, on the repo's `main`). Use it for old-template repos too: it is strictly safer than the old text (exit 1 on pull failure, build exit code). A content-error red run is not a rollback reason (see Wave design).
2. **Bad `pages-deploy.yml` on `v1`:** move the tag back: `git tag -fa v1 <last-good> && git push -f origin v1`. Every migrated repo recovers on its next run; no per-repo edits. Re-run the repos that deployed during the bad window (`gh workflow run static.yml -R ...`; this is a workflow trigger and needs Jeff's go-ahead).
3. **ECR login/role problem:** passing `ecr_role_arn: ''` from each caller would be a per-repo edit, so instead change the default in `pages-deploy.yml` back to `''` on `dev`, canary, then move `v1`. Pulls fall back to anonymous automatically if the role is unassumable (the steps are `continue-on-error`), so a broken role degrades to today's behavior rather than failing deploys.
4. **Whole migration:** stop issuing commits; migrated repos keep working on `v1`. There is no state outside the repos and the tag.

## Keeping templates for NEW repos current
- New repos get `static.yml` from UserRepo, which is copied from CentralRepo `scripts/static.yml` (`scripts/update_scripts.sh`, `repo_upgrade_spec.json` `files_to_copy`). Because the caller pins the moving tag `v1`, a new repo created from UserRepo is current without any template change; the template only changes when the **caller contract** changes (a new input, permission or trigger), which should ship as `v2`.
- `repo_upgrade_spec.json` (in UserRepo; documentation only, never read by `batch_repo_update.py`, per CentralRepo gotchas) currently lists `scripts/static.yml -> .github/workflows/static.yml`; add a note there that the file is a thin caller of `pages-deploy.yml@v1` and that fixes ship by moving `v1`. UserRepo's own `.github/workflows/static.yml` is updated by the other session's migration; this plan only records the doc change as a follow-up.
- Add a short gotcha to CentralRepo `docs/claude/gotchas.md` (replaces the "`scripts/static.yml` is the canonical template" description) and a `reference.md` row for `pages-deploy.yml`; close-out step.
- Keep `scripts/static.yml` the single source: the helper reads it from `v1`, never from a working copy.

## Credentials
OIDC only; no stored secrets and no `secrets: inherit`. The role ARN default lives in `pages-deploy.yml` (`arn:aws:iam::228122752878:role/GitHubECRPullOIDC`, commit f7415bb). Trust (`docs/aws/GitHubECRPullOIDC.trust.json`): `aud sts.amazonaws.com`, `sub repo:FortinetCloudCSE/*:*` and `job_workflow_ref FortinetCloudCSE/CentralRepo/.github/workflows/pages-deploy.yml@*`. So only runs of the shared workflow, from any org repo, can assume it; an old inline `static.yml` cannot. The policy grants only `ecr-public:GetAuthorizationToken` and `sts:GetServiceBearerToken` (pull-only). Callers need `permissions: id-token: write` (already in the template). The migration helper itself uses the operator's existing `gh` token (`repo`, `workflow` scopes) and creates no credentials. Not verified by this plan: the role's real behavior from a non-UserRepo repo, which N1 tests.

## Ownership of the moving `v1` tag
- Owner: whoever holds the CentralRepo coordinator role; today Jeff (single owner, one writer). Only the coordinator moves `v1`.
- Rule: **canary first, then move.** A change to `pages-deploy.yml` lands on `dev`, is tested by a `workflow_dispatch` canary from a UserRepo test branch pointing at `@dev` (allowed in UserRepo's `github-pages` environment), merged to `main`, and only then `v1` is moved to the main commit. Record each move in CentralRepo `RELEASE_NOTES.md` with the old sha (for one-command rollback).
- Never move `v1` during a migration wave. A wave and a tag move are mutually exclusive in time; finish or pause the wave first.
- Breaking caller-contract changes get `v2`; callers are then migrated like this plan does.
- Blast radius check before any move: after migration all ~90 repos read `v1` on their next push to `main`, but nothing re-runs automatically on a tag move, so a bad move is felt at each repo's next deploy (days later) unless noticed; mitigated by moving only after a green canary on the new commit.

## Dependabot for the action versions inside `pages-deploy.yml`
Add `.github/dependabot.yml` to CentralRepo (not to workshop repos; their callers contain no action pins to bump):
```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    target-branch: dev
    schedule:
      interval: monthly
    groups:
      actions:
        patterns: ["*"]
```
`directory: /` scans `.github/workflows/*.yml` (so `pages-deploy.yml` and CentralRepo's own `static.yml`, which is fine); it does not scan `scripts/static.yml`. Target `dev` because `main` takes dev->main PRs only. A Dependabot PR is a workflow change like any other: canary, merge, then move `v1`. Not created by this plan; it is a Phase-3 follow-up (needs a push to `dev`, so the coordinator batches it). Dependabot has not been observed running on CentralRepo (the alerts endpoint returned empty; this is not proof it is disabled).

## Timeline (minutes, measured)
Rests on: last successful `static.yml` run per repo (n=85, GitHub-hosted): median 0.7 min, p90 1.1, max 2.3 of runner time, queue time not included (the parent plan's canary and Jeff's earlier observation put a deploy at 2-6 min end to end). Per repo: commit ~0.2, wait for run 1-3, verify ~0.3, so budget **2-4 min per repo, 3 typical**.
- N-class (52 repos, 11 waves): 52 x 3 = ~155 min, plus two human gates ~10 = **~2.5-3 h**.
- O-class (31 repos, 9 waves): 31 x 3 = ~95 min plus gates and the O5/O9 manual checks ~30 = **~2 h**.
- Preparation (helper script, dry-run on one repo list, ledger): **~30-45 min**.
Total ~5-6 h of attended wall clock, best split into two sittings (N-class, then O-class). The one thing that slows it: ECR throttling inside the pull loop (backoff up to ~2 min per repo, and a red run to retry); the authenticated pull should remove it. If every deploy took the 6-minute end of the quoted range, 83 x 6 min = ~8.3 h is the ceiling.

## Implementation Method
Hybrid: write the helper inline, then run the waves from one tmux session with the helper (sequential by design; a fan-out would defeat the no-simultaneous-pulls rule). Reason: high blast radius across ~83 public repos, strictly ordered, each step gated on the previous run.

## Steps
- [x] Precondition: UserRepo, xperts-ai-101, ai-101 migrated and green; `v1` on main; default `ecr_role_arn` live on `v1`
- [x] Decide open questions Q1-Q5
- [x] Pre-flight (new): for every candidate, shallow-clone and build locally with the already-pulled `fortinet-hugo:latest` (no ECR traffic); require exit 0 and a non-empty `public/index.html`. Reason: the old template ignores the container exit code and uploads the image's stale `public/` (assets only), so a repo can be green yet serve 404 (found in zero-touch-provisioning and ai-102-with-fortiappsec: live `{{< quizdown >}}` at content/02Hugo/3_create_md/index.md:136, shortcode removed from CentralRepo 2026-05-28). Repos that fail get a content fix BEFORE migration, otherwise the new fail-fast workflow turns the silent 404 into a red run.
- [x] Fix zero-touch-provisioning and ai-102-with-fortiappsec (remove or replace the quizdown block; one content commit each; Jeff said fix first)
- [x] Write `scripts/migrate_static_yml.sh` (dry-run default, md5 allow-list, ledger); test dry-run against the 83 (no writes)
- [x] Wave N1 + gate
- [x] Wave N2 + gate
- [x] Waves N3-N11
- [x] Wave O1 + gate
- [x] Waves O2-O8
- [x] Wave O9 dropped: FortiShield is private (out of scope); never touched
- [x] Manual-review list resolved (style-guide upgraded in PR #3; fortimanager-cloud-deployments and UserRepoDoc deleted by Rob Reris; FortiWeb-Advanced-Threat-Lab private; ai-102-with-fortiappsec obsolete, being deleted) — was: (delete dead static.yml / upgrade style-guide and fortimanager-cloud-deployments)
- [ ] Add `.github/dependabot.yml` to CentralRepo `dev` (coordinator batch)
- [ ] Update `repo_upgrade_spec.json` note (UserRepo), CentralRepo `gotchas.md` / `reference.md` / `RELEASE_NOTES.md`
- [ ] Re-run the inventory: expect 0 repos on md5 f0aff64a/1583cc75; close-out

## Verified vs not
Verified (measured 2026-10-23, read-only): repo counts and classes; md5 of every `static.yml` (83 candidates are byte-identical to the two templates, so no customizations); that the six no-pull-step files are legacy Dockerfile/no-build forms and never ran; default branches; archived (none) and fork (3, none Hugo) status; last-push dates; Pages build type and live HTTP status; `github-pages` environment branch policies allow `main`; branch protection (87 protected, admin bypass possible, `enforce_admins` false on the three sampled); latest-run results and run durations; runner type of the latest run (GitHub-hosted `ubuntu-latest` in all 87); token scopes; trust policy text; that `git show bdf719e:scripts/static.yml` is md5 f0aff64a.
Not verified: that a private repo can call the public reusable workflow and assume the role (O1/O9 test it); that the OIDC role works from repos other than the canary; the contents of the 38 non-static.yml repos' workflows (classified from names and tree flags); whether a direct commit to a protected `main` is accepted in each of the 87 (checked: `enforce_admins` on 3 repos; the 10-09 sweep is the precedent); `enforce_admins` on the other 84; org-level Actions policy (needs org admin: 403); whether Dependabot is enabled on CentralRepo; why zero-touch-provisioning and ai-102-with-fortiappsec serve 404; what the `docs/` folders in cFOS-GKE-Workshop and FortiShield contain; exact time of a Jenkins-gated PR; the "flagship" ordering (a guess).

## Open questions for Jeff
1. Direct admin commits to protected `main` on ~80 repos (precedent: the 10-09 sweep), or PRs with the Jenkins check? PRs roughly double the time. - direct admin commits to protected main.
2. The two live legacy-form sites (style-guide, fortimanager-cloud-deployments) and three dormant ones: delete the dead `static.yml`, upgrade, or leave? upgrade
3. zero-touch-provisioning and ai-102-with-fortiappsec: 404 at the root today. Known/intended, or fix first? fix first 
4. Is "flagship" correctly k8s-101/201/202 and AWS-FGT-101/201? Reorder N9-N11 and O6-O8 if usage data says otherwise.  go with your recommendation
5. Run both classes in one sitting or two? And do you want to be present for FortiShield (private, hot) and gate N1/N2/O1 yourself?  don't touch FortiShield (it's private anyway)

## Plan Changes
- 2026-10-25: Status In Progress. Results so far: 82 of 84 public candidates migrated and verified through the PR route (waves N1-N11, O1-O8 and retry waves R1-R11); each Pages run succeeded with 'Login to ECR Public' and 'Authenticated as'. Two repos (zero-touch-provisioning, ai-102-with-fortiappsec) failed the local build on the removed quizdown shortcode and are being fixed (content fix + migration in one PR). Lessons recorded: (1) the first poll of a brand-new Jenkins job can build another branch, so the helper pushes one empty re-trigger commit; (2) an expired AWS SSO login made the driver treat an unreadable Jenkins secret as 'no job' and skip 50 repos, so the driver now requires /whoAmI 200 before each repo and stops otherwise; (3) repos created with GitHub's immutable OIDC subject need the second sub pattern in the GitHubECRPullOIDC trust policy; (4) several repos have enforce_admins=true or a required Jenkins check, so PRs (not direct commits) were used throughout, about 6-9 min per repo. Legacy-form static.yml repos (style-guide, fortimanager-cloud-deployments, FortiWeb-Advanced-Threat-Lab, UserRepoDoc) are being assessed; the private ones (advanced-routing-sdwan-azure, user-managed-scaling, FortiShield) are out of scope.
- 2026-10-23: diagnosed the two 404 roots (quizdown shortcode removed -> Hugo build fails -> old template deploys stale assets-only public/); added a local build pre-flight for all candidates and the two content fixes.
- 2026-10-23: Jeff's answers — Q1 direct admin commits to protected main (helper checks enforce_admins=false per repo, falls back to a PR if true); Q2 upgrade the legacy-form repos (public ones only: private are out of scope); Q3 fix the two 404 roots before migrating them; Q4 flagship order per recommendation; Q5 never touch FortiShield. Org Actions policy read (admin:org): all actions and workflows allowed, sha pinning not required — no org change needed.
- 2026-10-23: scope rule added — private/internal repos excluded (removes user-managed-scaling and FortiShield; total 81; wave O9 dropped).
none

## Session Summary
83 public repos plus style-guide now call `pages-deploy.yml@v1`; each Pages run succeeded with the OIDC login and a live site. About 6-9 minutes per repo on the PR route (Jenkins + Lacework). Skipped by design: private repos (user-managed-scaling, advanced-routing-sdwan-azure, FortiWeb-Advanced-Threat-Lab, FortiShield) and ai-102-with-fortiappsec (obsolete; its `mcpdemo.html` could not build and the build ignores `static/`). zero-touch-provisioning was fixed (quizdown block removed) and migrated. Lessons are in `docs/claude/gotchas.md#reusable-pages-workflow`.

## Files Changed
`scripts/migrate_static_yml.sh` (new; PR-based, dry-run default, re-trigger), `docs/aws/GitHubECRPullOIDC.trust.json` (second `sub` pattern), this plan, `docs/claude/gotchas.md`, `CLAUDE.md`.

## Follow-ups
- Not done: `.github/dependabot.yml` for the action versions in `pages-deploy.yml`; the `repo_upgrade_spec.json` note in UserRepo; re-running the inventory to confirm zero repos on the old md5s.
- Revoke the Jenkins automation token and delete the Secrets Manager secret `workshop/jenkins/claude-automation`.
- Optional: copy a repo's `static/` into the build in `scripts/local_copy.sh`.

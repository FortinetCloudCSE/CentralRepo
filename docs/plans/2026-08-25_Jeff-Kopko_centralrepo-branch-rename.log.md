# Log: centralrepo-branch-rename
Plan: docs/plans/2026-08-25_Jeff-Kopko_centralrepo-branch-rename.md

## Why this log exists
Blast radius outside this repo (52+ downstream repos in the org), and the audit that
shaped the plan's scope carries information the plan's checkboxes won't preserve —
specifically the full per-repo table and the reasoning for why Phase 4 got split out
instead of bundled in.

## Full downstream repo audit (2026-08-25)

Source: `gh search code "prreviewJune23" --owner FortinetCloudCSE` → 53 hits on
`Dockerfile`/`Dockerfile-dev` paths (52 downstream + CentralRepo itself). Every one
confirmed to carry `ADD https://github.com/FortinetCloudCSE/CentralRepo.git#prreviewJune23`
in its `dev` stage. Audited via 4 parallel subagents, ~13 repos each, checking against
CentralRepo's current canonical `scripts/static.yml` for 4 markers: `actions/checkout@v4+`,
retry-backoff on ECR pull, exit-code capture on the build container, `image_variant`
workflow_dispatch input.

### Category 1 — ECR-pull already, Dockerfile is dead weight, safe to delete (33 repos)

| repo | checkout ver | retry-backoff | exit-code capture | image_variant | notes |
|---|---|---|---|---|---|
| AWS-FGT-101 | v4 | Y | N | Y | |
| AWS-FGT-201 | v4 | Y | N | Y | |
| AppSec103-203-FortiADC | v4 | Y | N | Y | |
| Autoscale-Simplified-Template | v4 | Y | N | Y | |
| FGCP-in-AWS | v4 | Y | N | Y | |
| FortiCloud-Orgs-FortiFlex | v4 | Y | N | Y | |
| FortiGate-AWS-Autoscale-TEC-Workshop | v4 | Y | N | Y | |
| FortiGate-AWS-Autoscale-TEC-Workshop-Backup | v4 | Y | N | Y | |
| FortiGate-AWS-CNF-TEC-Workshop | v4 | Y | N | Y | |
| GWLB-in-AWS | v4 | Y | N | Y | |
| MGMT-in-AWS | v4 | Y | N | Y | |
| OCI_Solutions | v4 | Y | N | Y | |
| Public-Cloud-104-CNAPP | v4 | Y | N | Y | own CLAUDE.md documents the stale pin as current fact — will need its own doc fix (Follow-up) |
| PublicCloud105-FortiFlex | v4 | Y | N | Y | |
| azure-102-foundational | v4 | Y | N | Y | |
| azure-202-advanced | v4 | Y | N | Y | |
| fortianalyzer-aws-ha-dualaz-cloudformation | v4 | Y | N | Y | |
| fortianalyzer-aws-ha-singleaz-cloudformation | v4 | Y | N | Y | |
| fortianalyzer-aws-standalone-cloudformation | v4 | Y | N | Y | |
| fortigate-automation-stitch-workshop | v4 | Y | N | Y | only repo in this group with a `Dockerfile-dev` too — delete both |
| fortigate-aws-gwlb-cloudformation | v4 | Y | N | Y | shared static.yml blob sha 217a211... across most of this AWS group |
| fortigate-aws-gwlb-terraform | v4 | Y | N | Y | |
| fortigate-aws-ha-dualaz-cloudformation | v4 | Y | N | Y | |
| fortigate-aws-ha-dualaz-terraform | v4 | Y | N | Y | |
| fortigate-aws-standalone-cloudformation | v4 | Y | N | Y | one cosmetic diff: `cancel-in-progress: true` vs false |
| fortigate-aws-vpc-routeserver-active-active-cloudformation | v4 | Y | N | Y | |
| fortigate-aws-vpc-routeserver-ha-dual-az-cloudformation | v4 | Y | N | Y | |
| fortimanager-aws-ha-dualaz-cloudformation | v4 | Y | N | Y | |
| fortimanager-aws-ha-singleaz-cloudformation | v4 | Y | N | Y | |
| fortimanager-aws-standalone-cloudformation | v4 | Y | N | Y | |
| fortiweb-security-foundations-201 | v4 | Y | N | Y | |
| gcp-ncc-mrr-fortigate | v4 | Y | N | Y | |
| k8s-101-workshop | v4 | Y | N | Y | own CLAUDE.md documents the stale pin as current fact — will need its own doc fix (Follow-up) |

### Category 2 — still `docker build`s locally in static.yml, Dockerfile is a live dependency (19 repos)

**Not safe for blind Dockerfile deletion.** Each of these runs
`docker build -t fortinet-hugo . --target=prod` (or `DOCKER_BUILDKIT=1 docker build ...`)
directly inside `static.yml`, with no ECR pull at all. Deleting the Dockerfile breaks the
deploy. Note per the plan's Constraints section: this build targets `prod`, which pins
`#main` — **not** `#prreviewJune23** — so the rename itself does not break these repos'
CI; only the (separate) modernization would touch them.

| repo | checkout ver | notes |
|---|---|---|
| Code-Security-Workshop | v4 | old pre-ECR template |
| Forti-ProductXYZ | v4 | old pre-ECR template |
| FortiADCIntro | v4 | old pre-ECR template |
| FortiCNAPPRoadshow | v4 | old pre-ECR template; also has the org-wide broken FortiDevSec Jenkinsfile gotcha already documented in CentralRepo's own CLAUDE.md |
| FortiCNF | v4 | old pre-ECR template |
| FortiDevOps-v2025 | v4 | old pre-ECR template |
| FortiDevSec-Workshop | v4 | old pre-ECR template |
| FortiSASE | v4 | old pre-ECR template; content page also has the stale UserRepo-inherited contribute instructions |
| FortiWeb-Azure-ZTNA-FortiSoar | v4 | old pre-ECR template |
| api-and-websvc-fundamentals | v4 | old pre-ECR template |
| cFOS-GKE-Workshop | v3 | oldest overall: checkout@v3, configure-pages@v3, deploy-pages@v2; only repo with both Dockerfile and Dockerfile-dev in this category |
| cloud-architectures | v4 | old pre-ECR template |
| forticnapp-code-security-demo | v4 | old pre-ECR template |
| fortigate-azure-sdwan-networking-workshop | v4 | oldest workflow shape: no retry loop, no image_variant, uses `sleep 5` instead of `docker wait` |
| fortiweb-threat-protection | v4 | old pre-ECR template |
| getting-started-general | v4 | only repo with Dockerfile-dev in this category |
| k8s-201-workshop | v4 | old pre-ECR template |
| k8s-202-workshop | v4 | old pre-ECR template |
| technical-recipe-azure-fweb-ztna-fortisoar | v4 | old pre-ECR template |

33 + 19 = 52, matches the full downstream count from the code search.

## Phase 1 execution notes

- **Step 1.2's pre-rename CI-green check is structurally unsatisfiable, and this is
  a design fact about GitHub Actions, not a fluke of this push.** GitHub evaluates a
  push-triggered workflow's `on.push.branches` filter using the workflow YAML content
  *as it exists in the commit being pushed*, matched against the actual ref name being
  pushed to. Step 1.1's commit changed `branches: [prreviewJune23]` → `branches: [dev]`
  in both `ci.yml` and `image-build-push-dev.yaml`, in the same commit then pushed to
  the still-named `prreviewJune23` ref (`git push origin HEAD:prreviewJune23`,
  landing as `145c42c`). The trigger condition *in that pushed commit* requires a ref
  literally named `dev`, which `prreviewJune23` isn't yet — so the push doesn't match
  its own new trigger and nothing fires. Confirmed via `gh api
  repos/FortinetCloudCSE/CentralRepo/commits/145c42c/check-runs` and `gh run list`:
  zero check-runs, zero workflow runs registered for that commit, from two independent
  checks. **You cannot verify a CI-trigger rename by pushing the edited trigger to the
  OLD ref name** — editing the trigger in that same commit makes the old name stop
  matching, by construction. Real verification only becomes possible post-rename, which
  is exactly what step 1.6 already does — so **1.6 was always the load-bearing
  verification, not 1.2.** Neither workflow has a `workflow_dispatch` fallback that
  could have manually exercised the pre-rename trigger content either.

- **GitHub does NOT keep a fetch/push redirect from the old branch name after a
  non-default-branch rename — it fails cleanly, immediately.** Empirically checked
  post-rename (branch renamed `prreviewJune23` → `dev` via the API at
  2026-08-25T18:31:51Z): `git fetch origin prreviewJune23` → `fatal: couldn't find
  remote ref prreviewJune23`, exit code 128. `git ls-remote origin prreviewJune23` →
  exit code 0 but empty output (no matching ref, no error — `ls-remote`'s normal
  behavior for a non-matching refspec). So anything anywhere still hardcoding
  `prreviewJune23` as a fetch/clone/checkout target will fail hard and immediately
  post-rename, not silently succeed against stale content. This resolves the plan's own
  "Risks / Open Questions" item on this exact point — no grace period, no redirect.
- **A local branch name is unique per repository and shared across all worktrees of
  that repository (they share one `.git`).** Renaming this worktree's local branch to
  `dev` (`git checkout -B dev origin/dev`) succeeded first, which then blocked the
  primary checkout's `git branch -m prreviewJune23 dev` with `fatal: a branch named
  'dev' already exists` — not a worktree-checkout-exclusivity error, a plain branch-name
  collision, because the ref exists repo-wide the moment either worktree creates it.
  Fixed by renaming the worktree's local branch back to `phase1-rename-work` (freeing
  `dev` for the primary checkout), both still tracking `origin/dev`. Same underlying
  constraint as the original worktree-naming note at the top of this phase's task
  (a branch can't be checked out in two worktrees at once) — just tripped from the
  opposite direction, on branch *creation* rather than *checkout*.

- **The branch-rename API call itself synthesized a push-equivalent event for the new
  `dev` ref, firing both workflows immediately — before any deliberate follow-up push.**
  `image-build-push-dev.yaml` (run 32884312203) and `ci.yml` (run 32884311978) both ran
  and completed `success` against commit `d66d27b` — the commit that was HEAD at the
  moment of rename — with no separate push from this session. This is the flip side of
  the 1.2 finding: a push-triggered workflow's `branches:` filter is evaluated against
  the ref name, and a rename operation apparently produces a ref-update GitHub treats as
  push-trigger-eligible for the *new* name, even though no `git push` occurred under
  that name. Step 1.6's own deliberate follow-up push (`a08c75f`, docs-only, matched
  `image-build-push-dev.yaml`'s `paths-ignore: docs/**` so only `ci.yml` ran on it) is
  therefore not the *first* proof the rename didn't leave a gap — the rename's own
  synthesized event already was. Both pieces of evidence are recorded for completeness.

- **`fortihugorunner build-image --env admin-dev` fails, but for a reason entirely
  unrelated to today's rename — a pre-existing structural mismatch between
  `extractBranchByStage` (`dockerinternal/container.go:118`) and CentralRepo's actual
  Dockerfile shape.** Live command attempted first (binary present on `PATH`):
  `Error building Docker image: Branch not found: no branch found in Dockerfile`. Code
  inspection found why: `extractBranchByStage` only enters "in target stage" when it
  sees a line exactly matching `FROM base as <target>` (case-insensitive); for
  `--env admin-dev`, `target = "dev"`, so it looks for `FROM base as dev`. CentralRepo's
  Dockerfile has never had that literal line — the `dev` stage is
  `FROM dev-src-local-${LOCAL} as dev` (`Dockerfile:34`, unchanged since `abd0058e`,
  2026-05-28 — three months before this plan), reached indirectly through
  `dev-src-local-true`/`dev-src-local-false` (`Dockerfile:24,28`), neither of which is
  named `dev`. The scan for `FROM base as dev` never matches anything, so the function
  never reaches the `ADD ...#dev` line at all — it would have failed exactly the same
  way before the rename, looking for a nonexistent `FROM base as dev` with
  `#prreviewJune23` behind it. **Isolated, not just inferred:** the `prod` stage's header
  is literally `FROM base as prod` (`Dockerfile:60`) — an exact match — with its `ADD
  ...CentralRepo.git#main` line directly inside that same stage, so
  `fortihugorunner build-image --env author-dev` (`target = "prod"`) hits the intended
  code path correctly; only the `dev` env is broken by this stage-indirection mismatch.
  **The plan's own Constraints claim — "no fortihugorunner code changes are
  required" — is correct as far as it goes (no hardcoded branch name anywhere in
  `extractBranchByStage`, confirmed) but incomplete: it didn't anticipate this
  stage-header mismatch, which is a real, independent, pre-existing bug, not introduced
  by and not fixable by anything in this plan's scope.** Filed as a Follow-up on the
  plan file rather than fixed here — fortihugorunner is a separate repo/tool, and fixing
  its stage-header matcher (e.g. teach it to also match a stage that's `FROM
  <other-stage> as <target>` and recurse, or track `ARG LOCAL` resolution) is real
  design work outside Phase 1's scope.

## Rejected / considered options

- **Delete + recreate the branch instead of GitHub's rename API** — rejected. Rename
  preserves commit history and auto-handles PR retargeting/branch protection if either
  existed. No functional reason to do it the harder way.
- **Bundle Phase 3 and Phase 4 into one bulk script run** — rejected after the audit
  surfaced the 19-repo split. Phase 3 is pure dead-code removal (provably safe: CI already
  ignores the local Dockerfile). Phase 4 changes what each of those 19 repos' CI actually
  does (local build → prebuilt pull) — different risk class, deserves its own plan, pilot,
  and rollout pacing rather than being silently absorbed into a rename plan's scope.
- **Wait to execute Phase 1 until Phases 3/4 are done, on the theory that downstream repos
  needed to be fixed first** — this was the user's implicit worry going in, and the
  audit disproved it: the rename cannot break any of the 52 repos' CI, because the branch
  being renamed is only referenced by each repo's Dockerfile `dev` stage, which no
  automated CI path exercises (`static.yml` either pulls ECR, or builds `--target=prod`,
  which pins `#main`). This decoupled the two workstreams entirely.
- **Fix already-instantiated workshop repos' "how to contribute" pages (inherited from the
  stale UserRepo template) as part of this plan** — rejected as in-scope; moved to
  Follow-ups. High fan-out (dozens of repos, all cosmetic/low-traffic doc pages) for low
  value relative to fixing the UserRepo template itself, which stops the bleeding for every
  *future* repo.
- **Reused `batch_repo_update.py` directly for Phase 3 instead of writing a purpose-built
  script** — rejected. That script also unconditionally rewrites each target repo's
  `README.md` (if GitHub Pages is enabled) and sets custom repo properties — both
  unrelated side effects with real potential to clobber existing README content across 33
  repos for no reason tied to this plan. Wrote a minimal script instead: replace
  `static.yml`, delete `Dockerfile`(-dev), nothing else.

## Phase 3 execution notes (2026-08-25)

Script used (`phase3_modernize.py`, run from scratch, not committed to the repo — it's a
one-off operational tool with a hardcoded REPOS list, same spirit as `batch_repo_update.py`
itself, which also expects `REPOS` filled in ad hoc per run):

```python
#!/usr/bin/env python3
"""Phase 3 of docs/plans/2026-08-25_Jeff-Kopko_centralrepo-branch-rename.md.

For each of the 33 "safe" repos: replace .github/workflows/static.yml with
CentralRepo's current canonical scripts/static.yml, and delete the dead
Dockerfile (and Dockerfile-dev where present). Nothing else -- no README
rewrite, no custom-properties update, no config.toml conversion (unlike
batch_repo_update.py, which does all three and isn't appropriate here).

Usage:
  GITHUB_TOKEN=$(gh auth token) python3 phase3_modernize.py --dry-run
  GITHUB_TOKEN=$(gh auth token) python3 phase3_modernize.py --live
"""
import base64
import json
import os
import sys

import requests

ORG = "FortinetCloudCSE"
BRANCH = "main"
API = "https://api.github.com"

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

STATIC_YML_LOCAL = "scripts/static.yml"
STATIC_YML_REMOTE = ".github/workflows/static.yml"

REPOS = [  # 33 repos confirmed to already pull the prebuilt ECR image
    "AWS-FGT-101", "AWS-FGT-201", "AppSec103-203-FortiADC",
    "Autoscale-Simplified-Template", "FGCP-in-AWS", "FortiCloud-Orgs-FortiFlex",
    "FortiGate-AWS-Autoscale-TEC-Workshop", "FortiGate-AWS-Autoscale-TEC-Workshop-Backup",
    "FortiGate-AWS-CNF-TEC-Workshop", "GWLB-in-AWS", "MGMT-in-AWS", "OCI_Solutions",
    "Public-Cloud-104-CNAPP", "PublicCloud105-FortiFlex", "azure-102-foundational",
    "azure-202-advanced", "fortianalyzer-aws-ha-dualaz-cloudformation",
    "fortianalyzer-aws-ha-singleaz-cloudformation", "fortianalyzer-aws-standalone-cloudformation",
    "fortigate-automation-stitch-workshop", "fortigate-aws-gwlb-cloudformation",
    "fortigate-aws-gwlb-terraform", "fortigate-aws-ha-dualaz-cloudformation",
    "fortigate-aws-ha-dualaz-terraform", "fortigate-aws-standalone-cloudformation",
    "fortigate-aws-vpc-routeserver-active-active-cloudformation",
    "fortigate-aws-vpc-routeserver-ha-dual-az-cloudformation",
    "fortimanager-aws-ha-dualaz-cloudformation", "fortimanager-aws-ha-singleaz-cloudformation",
    "fortimanager-aws-standalone-cloudformation", "fortiweb-security-foundations-201",
    "gcp-ncc-mrr-fortigate", "k8s-101-workshop",
]

# fortigate-automation-stitch-workshop: found in the original 2026-08-25 audit.
# FortiGate-AWS-CNF-TEC-Workshop: missed by that audit, caught live by this
# script's dry-run instead -- confirmed stale (#prreviewJune23 ADD, ancient
# klakegg/hugo:0.107.0 base) and this repo's static.yml already pulls ECR.
DOCKERFILE_DEV_REPOS = {"fortigate-automation-stitch-workshop", "FortiGate-AWS-CNF-TEC-Workshop"}

# ... (blob/tree/commit git-data-API plumbing, same pattern as batch_repo_update.py's
#      create_blob/create_tree/create_commit/update_branch_ref -- omitted here for length;
#      each repo: read tree, replace static.yml blob, mark Dockerfile[-dev] blobs for
#      deletion (sha: None), one commit, PATCH the main ref)
```

**Dry-run result:** caught the `FortiGate-AWS-CNF-TEC-Workshop` `Dockerfile-dev` gap (see
Decisions above). Re-ran clean, 33/33 planned correctly.

**Go/no-go:** asked explicitly per plan step 3.3, confirmed, proceeded.

**Live run — full output** (33/33 pushes succeeded):

```
AWS-FGT-101: pushed 703c3828 -- update .github/workflows/static.yml; delete Dockerfile
AWS-FGT-201: pushed 2db23f63 -- update .github/workflows/static.yml; delete Dockerfile
AppSec103-203-FortiADC: pushed 70d19068 -- update .github/workflows/static.yml; delete Dockerfile
Autoscale-Simplified-Template: pushed 1ce3f779 -- update .github/workflows/static.yml; delete Dockerfile
FGCP-in-AWS: pushed 7b9d147b -- update .github/workflows/static.yml; delete Dockerfile
FortiCloud-Orgs-FortiFlex: pushed 8a99db3d -- update .github/workflows/static.yml; delete Dockerfile
FortiGate-AWS-Autoscale-TEC-Workshop: pushed 8f31f80e -- update .github/workflows/static.yml; delete Dockerfile
FortiGate-AWS-Autoscale-TEC-Workshop-Backup: pushed 7d5b4ba4 -- update .github/workflows/static.yml; delete Dockerfile
FortiGate-AWS-CNF-TEC-Workshop: pushed 06ef9029 -- update .github/workflows/static.yml; delete Dockerfile; delete Dockerfile-dev
GWLB-in-AWS: pushed 84a8caeb -- update .github/workflows/static.yml; delete Dockerfile
MGMT-in-AWS: pushed c772ecec -- update .github/workflows/static.yml; delete Dockerfile
OCI_Solutions: pushed e9bb1b2d -- update .github/workflows/static.yml; delete Dockerfile
Public-Cloud-104-CNAPP: pushed 3b8dc3a2 -- update .github/workflows/static.yml; delete Dockerfile
PublicCloud105-FortiFlex: pushed bc05e059 -- update .github/workflows/static.yml; delete Dockerfile
azure-102-foundational: pushed ea0b544e -- update .github/workflows/static.yml; delete Dockerfile
azure-202-advanced: pushed 2f4b2160 -- update .github/workflows/static.yml; delete Dockerfile
fortianalyzer-aws-ha-dualaz-cloudformation: pushed 2a1f94b3 -- update .github/workflows/static.yml; delete Dockerfile
fortianalyzer-aws-ha-singleaz-cloudformation: pushed 64856e9b -- update .github/workflows/static.yml; delete Dockerfile
fortianalyzer-aws-standalone-cloudformation: pushed b04a3c7c -- update .github/workflows/static.yml; delete Dockerfile
fortigate-automation-stitch-workshop: pushed 0dc3292d -- update .github/workflows/static.yml; delete Dockerfile; delete Dockerfile-dev
fortigate-aws-gwlb-cloudformation: pushed 8b35aba8 -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-gwlb-terraform: pushed 980731e1 -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-ha-dualaz-cloudformation: pushed e90dd1b3 -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-ha-dualaz-terraform: pushed e916078e -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-standalone-cloudformation: pushed 5b93d4bc -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-vpc-routeserver-active-active-cloudformation: pushed c81ef915 -- update .github/workflows/static.yml; delete Dockerfile
fortigate-aws-vpc-routeserver-ha-dual-az-cloudformation: pushed d0cefe28 -- update .github/workflows/static.yml; delete Dockerfile
fortimanager-aws-ha-dualaz-cloudformation: pushed 1e17fbe9 -- update .github/workflows/static.yml; delete Dockerfile
fortimanager-aws-ha-singleaz-cloudformation: pushed 8232ae05 -- update .github/workflows/static.yml; delete Dockerfile
fortimanager-aws-standalone-cloudformation: pushed 80f719d0 -- update .github/workflows/static.yml; delete Dockerfile
fortiweb-security-foundations-201: pushed 2e792c44 -- update .github/workflows/static.yml; delete Dockerfile
gcp-ncc-mrr-fortigate: pushed 793c7fd7 -- update .github/workflows/static.yml; delete Dockerfile
k8s-101-workshop: pushed 943fafef -- update .github/workflows/static.yml; delete Dockerfile
```

**Actions outcome check — all 33, not just a 3-5 sample** (cheap to do exhaustively): 32/33
`success`, 1 `failure` (`MGMT-in-AWS`, run 32885656600). Root cause investigation:

1. `gh run view 32885656600 --log-failed` → Hugo build failed inside the container:
   `ERROR error building site: assemble: failed to create page from pageMetaSource :
   "/home/UserRepo/content/_index.md:26:1": failed to extract shortcode: template for
   shortcode "FTNThugoFlow" not found`.
2. Checked whether `FTNThugoFlow.html` is in the live `fortinet-hugo:latest` image:
   `docker run --rm --entrypoint sh public.ecr.aws/k4n6m5h8/fortinet-hugo:latest -c "ls
   /home/CentralRepo/layouts/shortcodes/ | grep -i FTNThugo"` → not found.
3. Checked CentralRepo git history: `git log --oneline -- layouts/shortcodes/FTNThugoFlow.html`
   → two commits, most recent is `9bd2d1f remove shortcodes & add script for layouts copy
   from UserRepo`. `git ls-tree HEAD -- layouts/shortcodes/FTNThugoFlow.html` and `git
   ls-tree origin/main -- ...` both empty — the file isn't tracked on `dev` or `main`
   anymore. (A stale untracked copy still sits in the local `/home/ubuntu/pythonProjects/
   CentralRepo` working directory from before that removal, which is why an `ls` there
   found it — a local-disk artifact, not something git or the built image has.)
4. Checked `MGMT-in-AWS`'s own `layouts/shortcodes/` — only `ContainerFlow.html`, no
   `FTNThugoFlow.html` shadow copy of its own.
5. Checked whether this is new: compared against `MGMT-in-AWS`'s previous "successful" run
   (`32807783983`, 2026-08-25T04:08:02) — its `static.yml` was the pre-Phase-3 version,
   which does `docker wait "$CONT_ID"` with no `STATUS=` capture, so it always reports
   success regardless of what happened inside the container. No way to tell from that run
   alone whether the Hugo build itself failed too; the log format differs enough
   (`UNKNOWN STEP` grouping) that a direct text diff didn't resolve it either way. What's
   certain: `FTNThugoFlow.html` has been absent from the shipped image since at least
   commit `9bd2d1f` (predates today entirely), and `MGMT-in-AWS`'s content still references
   it — so this failure mode has existed for a while, independent of anything in this plan.

Conclusion: real, pre-existing, silently-masked production bug, not a regression from
Phase 3. Left as-is (out of scope), flagged as a Follow-up in the plan for an owner
decision (restore the shortcode upstream vs. fix `MGMT-in-AWS`'s content).

Cleaned up: `docker rmi public.ecr.aws/k4n6m5h8/fortinet-hugo:latest` after the
investigation (was pulled locally just to inspect the image contents).

## Phase 4 pilot execution notes (2026-08-25)

Reused the Phase 3 script's structure (`phase4_migrate.py`, same minimal
replace-static.yml-delete-Dockerfile approach), split into `--pilot` (3 repos) and
`--bulk` (16 repos) modes.

**Dry-run (pilot):** clean, 3/3.

**Dry-run (bulk):** caught another audit gap — `FortiWeb-Azure-ZTNA-FortiSoar` has a
`Dockerfile-dev` not recorded in the original 52-repo audit for this group (only
`getting-started-general` was). Verified live: identical stale pattern to the
`FortiGate-AWS-CNF-TEC-Workshop` one found in Phase 3 (`#prreviewJune23` ADD, ancient
`klakegg/hugo:0.107.0-alpine` base — looks like a copy-pasted template used across
several repos). Added to the delete list. This is now the **second** time a live
dry-run caught something the original `gh search code` audit missed — that audit should
be treated as "confirmed affected," not "exhaustive," per the plan's own Risks section.

**Pilot live push:** 3/3 pushes succeeded (`cFOS-GKE-Workshop` b0993ddf,
`fortigate-azure-sdwan-networking-workshop` 8e74869d, `FortiADCIntro` 221e139a).

**Pilot Actions outcomes:** `FortiADCIntro` succeeded. Two failed:

1. `fortigate-azure-sdwan-networking-workshop` (run 32886425690): `gh run view --log-failed`
   → `ERROR error building site: ... failed to extract shortcode: template for shortcode
   "FTNThugoFlow" not found` — byte-identical error class to `MGMT-in-AWS` in Phase 3. Same
   root cause (see that entry), no further investigation needed.

2. `cFOS-GKE-Workshop` (run 32886421568): `gh run view --log-failed` →
   `FileNotFoundError: [Errno 2] No such file or directory:
   '/home/UserRepo/scripts/repoConfig.json'`. Checked all 19 Phase-4 repos for
   `scripts/repoConfig.json` presence via `gh api .../contents/scripts/repoConfig.json` —
   `cFOS-GKE-Workshop` is the **only** one missing it (all 18 others, including all 16 bulk
   targets, already have it — confirmed before proceeding to bulk). Checked whether this
   predates the migration: `gh run list` shows exactly ONE run in this repo's entire Actions
   history — the failing one from this migration — so there's no prior baseline to compare
   against.

   Fixed by converting `config.toml` → `scripts/repoConfig.json` using the exact field
   mapping `batch_repo_update.py`'s `run_toml_to_json()` already uses (repoName from
   baseURL's last path segment, workshopTitle from title, author/themeVariant/
   logoBannerText/logoBannerSubText from `[params]`, shortcuts from `[[menu.shortcuts]]`,
   everything else inherited from CentralRepo's own `scripts/repoConfig.json` as the base
   object — same as the original script does). Used `tomllib` (Python 3.12 stdlib, no
   external dependency needed). Result reviewed before pushing — sensible values throughout,
   including `googleServicesID` landing on the same `G-5RZBH288ST` the repo's own
   `config.toml` already had under a different key name (`googleAnalytics`), so no data
   loss. Pushed as follow-up commit `90c7d6df` with a message explaining why.

   Re-triggered, waited, checked again: **new, different failure** —
   `ERROR error building site: assemble: failed to create page from pageMetaSource
   /01chapter1: "/home/UserRepo/content/01Chapter1/_index.md:4:1": [3:1] mapping key
   "weight" already defined at [2:1]`. This is a malformed-YAML-front-matter bug in the
   repo's own content (`weight: 1` then `weight: 10` two lines later) — unrelated to CI
   tooling, config conversion, or the branch rename. Not fixed — a content-authoring
   decision, out of scope. Given the "only one Actions run ever" finding above, this repo's
   Pages site may never have successfully built; not confirmed either way.

**Assessment before requesting the bulk go/no-go:** the migration mechanism (static.yml
swap + Dockerfile deletion) did not cause either pilot failure — one is a duplicate of an
already-known pre-existing bug class (`FTNThugoFlow`), the other resolved into a genuine
script gap (fixed, and confirmed isolated to this one repo) plus a second, independent,
pre-existing content bug. `repoConfig.json` presence re-verified across all 16 bulk targets
specifically to rule out `cFOS-GKE-Workshop`'s gap recurring there before asking to proceed.

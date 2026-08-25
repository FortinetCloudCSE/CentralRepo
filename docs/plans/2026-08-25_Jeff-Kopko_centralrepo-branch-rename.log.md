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

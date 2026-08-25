# Plan: Rename `prreviewJune23` to `dev`, modernize downstream repos off local Dockerfile builds
Date: 2026-08-25
Owner: Jeff Kopko
Slug: centralrepo-branch-rename
Status: Approved
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-08-25_Jeff-Kopko_centralrepo-branch-rename.md
Log File: docs/plans/2026-08-25_Jeff-Kopko_centralrepo-branch-rename.log.md

<!-- This repo's docs/plans/ already uses unnumbered date-first filenames
     (2026-08-25_Jeff-Kopko_launchdemoform-migration.md etc.) — no NNNN prefix,
     per the "never apply numbering forward-only in a directory that already
     holds unnumbered files" rule. -->

## Goal
- Rename CentralRepo's `prreviewJune23` branch to `dev` (standard name; the nonstandard
  name predates a clearer branch-model decision). Every reference to the old name — in
  CentralRepo's own workflows, Dockerfile, scripts, docs — must move in lockstep so CI
  keeps firing on the new name with zero gap.
- Per user request, also verify the user's belief that "nobody builds the containers
  themselves anymore" (i.e. that the per-repo copy of CentralRepo's `Dockerfile`, planted
  into every workshop repo by `batch_repo_update.py`, is dead weight now that CI pulls a
  prebuilt image from ECR). True for 33 of 52 repos, false for 19 — modernize all 52:
  drop the local `Dockerfile`, refresh `static.yml` to the current canonical template. The
  33 are pure cleanup (Phase 3); the 19 require actually changing what their CI does
  (Phase 4), staged with a pilot first.

## Context / Links
- User's own framing (CLAUDE.md, this repo): `main` builds prod, `prreviewJune23` builds
  dev; two known merge routes into `main`, route 2 caused a real incident 2026-08-25.
- `k8s-101-workshop` CLAUDE.md and `Public-Cloud-104-CNAPP` CLAUDE.md already independently
  document the Dockerfile-branch-pin gotcha for their own repos — this plan is the
  org-wide version of that.
- Related code: `.github/workflows/{ci.yml,image-build-push-dev.yaml}`, `Dockerfile`,
  `scripts/{docker_build_latest.sh,docker_run_latest.sh,batch_repo_update.py,static.yml}`,
  `README.md`, `CLAUDE.md`.

## Constraints / Assumptions

**Verified via GitHub API before writing this plan (2026-08-25):**
- 0 open PRs anywhere in CentralRepo, 0 open PRs targeting `prreviewJune23` historically
  that are still open. No PR-retargeting risk.
- `prreviewJune23` carries **no branch protection** (`main` does: `enforce_admins: true`,
  required check `ci/jenkins/build-status`). Nothing to migrate on that front.
- Repo webhook is a single Jenkins push hook (`jenkins.fortinetcloudcse.com`) — fires on
  any push, not branch-name-scoped. Unaffected by the rename.
- `fortihugorunner` has **zero hardcoded references** to `prreviewJune23` anywhere in its
  source, docs, or workflows. It extracts the CentralRepo branch name generically by
  parsing whichever Dockerfile stage it's pointed at (`dockerinternal/container.go`,
  `extractBranchByStage`). **No fortihugorunner code changes are required** — only a
  post-rename smoke test that it still reports the branch correctly.
- `Jenkinsfile` (CentralRepo's own) has no branch-name references — the required check it
  backs is a no-op regardless of source branch.
- Org-wide `gh search code "prreviewJune23"` found the string in exactly 52 other repos
  (full list below), always in a root `Dockerfile` or `Dockerfile-dev`, always in the
  **dev stage's** `ADD` line. Every one of those Dockerfiles was planted by
  `batch_repo_update.py`'s `FILES_TO_COPY`, which copies CentralRepo's own root
  `Dockerfile` byte-for-byte from whatever `main` currently has.
- **Critical finding that de-risks the rename itself:** CentralRepo's `Dockerfile` is
  two-stage. The `dev` stage ADDs `#prreviewJune23`; the **`prod` stage ADDs `#main`**
  and is what every downstream repo's `static.yml` actually builds
  (`docker build ... --target=prod`) when it builds locally at all. **The rename cannot
  break any downstream repo's CI**, because no CI path anywhere touches the `dev` stage
  of a downstream repo's copied Dockerfile. The only exposure is a human manually running
  `docker build --target dev` or `fortihugorunner build-image --env admin-dev` in one of
  those repos — documented by fortihugorunner's own README as the rare, non-typical path
  (`pull-image` from ECR is the typical/documented workflow).
- **Verified per-repo, not assumed:** fanned out 4 parallel audits (one per ~13-repo
  batch) across all 52 downstream repos, checking (a) does `static.yml` actually build
  from the local Dockerfile or pull ECR, (b) how stale is it against CentralRepo's current
  canonical `scripts/static.yml` (checkout action version, retry-backoff, exit-code
  capture, `image_variant` dispatch input). Results:
  - **33 repos** already pull the prebuilt ECR image in `static.yml` — their local
    `Dockerfile` is genuinely dead weight for CI. Safe to delete outright.
  - **19 repos** still run `docker build -t fortinet-hugo . --target=prod` (or
    `DOCKER_BUILDKIT=1 docker build ...`) directly against their own local `Dockerfile`
    inside `static.yml` — **the user's "nobody builds locally anymore" belief is false for
    these 19.** Deleting the Dockerfile there breaks their deploy pipeline outright; they
    need `static.yml` replaced with the ECR-pull template first, which is a genuine
    behavior change (build-locally → pull-prebuilt), not just cleanup.
  - **0 of the 52** repos' `static.yml` has the exit-code-capture fix CentralRepo's own
    template already has (`STATUS=$(docker wait "$CONT_ID")`, fail on nonzero) — every
    downstream repo, modernized or not, silently ignores a failed Hugo build inside the
    container today. This is a real, pre-existing bug the modernization phase fixes for
    free wherever `static.yml` gets replaced.
  - Full per-repo table is in the log file (`.log.md`) — not reproduced here to keep this
    plan file scannable.
- `UserRepo` (the template every new workshop repo is cloned from) has its own
  "how to contribute to CentralRepo" page instructing contributors to
  `git pull prreviewJune23` / merge PRs into that branch by name. Left unfixed, every
  *future* workshop repo inherits broken instructions. This is copied verbatim into every
  already-instantiated repo too (FortiSASE, Reducing-Risk-111-CNAPP, FortiShield,
  zero-touch-provisioning, ai-102-with-fortiappsec, fortiaigate-demo-runbook,
  SASE-203-CASB, and others) — those are lower priority (docs already shipped, low traffic
  page) and are call out as a follow-up, not required for this plan.
- `docs/plans/*.md` files that mention `prreviewJune23` are closed/historical plan
  records — per this repo's own plan-lifecycle rule, they are not rewritten in place.
  Left untouched deliberately.
- GitHub's native branch-rename API
  (`POST /repos/{owner}/{repo}/branches/{branch}/rename`) is used instead of manual
  delete+recreate — it preserves commit history and would auto-retarget any open PRs (moot
  here, there are none) and branch protection (moot here, none exists). **Unverified by
  this plan:** whether GitHub keeps a working push/fetch redirect from the old name for
  some period after rename on a *non-default* branch (well-documented for default-branch
  renames, not confirmed here) — Phase 1 includes an empirical check, not an assumption.

## Implementation Method
- **Phase 1 (CentralRepo):** tmux (sequential) in a dedicated worktree — sequential
  dependencies (edit → push → confirm CI green → rename → verify) and real blast radius
  (a live branch rename + two workflow triggers).
- **Phase 2 (UserRepo):** direct in-conversation — single file, one small PR.
- **Phase 3 (33-repo batch):** direct in-conversation, scripted — a single deterministic
  script execution (extended `batch_repo_update.py`) with a dry-run pass and an explicit
  go/no-go confirmation immediately before the live run, not a multi-agent fan-out.
- **Phase 4 (19-repo migration):** direct in-conversation, scripted, staged — pilot 3 repos
  first (chosen for structural diversity, not convenience), verify each pilot's Pages
  deploy actually succeeds under the new template, explicit go/no-go gate, then bulk-push
  the remaining ~16.

## Plan

### Phase 1 — CentralRepo itself (required, blocking, no external dependency)
- [x] **1.1** On `prreviewJune23`, in one commit, update every in-repo reference from
      `prreviewJune23` to `dev`:
  - `.github/workflows/ci.yml:5` — `branches: [prreviewJune23]` → `[dev]`
  - `.github/workflows/image-build-push-dev.yaml:6` — `branches: ["prreviewJune23"]` → `["dev"]`
  - `Dockerfile:29` — `ADD ...CentralRepo.git#prreviewJune23` → `#dev`
  - `scripts/docker_build_latest.sh:3`, `scripts/docker_run_latest.sh:3` — URL path
    `/prreviewJune23/scripts/...` → `/dev/scripts/...`
  - `README.md:371` — prose reference
  - `CLAUDE.md` — every occurrence (lines 8,11,12,15,18,22,23,27,107,155,156,214,248,252 as
    of this audit); this is a genuine rewrite of the "Working Branch" section and several
    gotchas, not a find/replace — the prose logic stays the same, only the name changes.
- [x] **1.2** Push. Confirmed structurally unsatisfiable pre-rename (see log,
      "Phase 1 execution notes"): the trigger-rename edit in the same commit means the
      pushed commit's `branches: [dev]` filter no longer matches the still-`prreviewJune23`
      ref, so neither workflow fired — zero runs, not a failure. 1.6 is the real
      verification.
- [ ] **1.3** Rename the branch via the GitHub API (preserves history):
      `gh api -X POST repos/FortinetCloudCSE/CentralRepo/branches/prreviewJune23/rename -f new_name=dev`
- [ ] **1.4** Update local git state: `git fetch origin`, `git branch -m prreviewJune23 dev`,
      `git branch --set-upstream-to=origin/dev dev`.
- [ ] **1.5** Empirically verify: does `git fetch origin prreviewJune23` (old name) still
      resolve post-rename, or fail cleanly? Document the actual behavior in the log file —
      don't assume.
- [ ] **1.6** Push a trivial follow-up commit (or the next real change) to `dev` and confirm
      `image-build-push-dev.yaml` fires and completes, proving the workflow trigger survived
      the rename correctly.
- [ ] **1.7** Smoke-test `fortihugorunner`: `fortihugorunner build-image --env admin-dev`
      against the renamed Dockerfile (or equivalent), confirm it reports
      `Image built with CentralRepo branch: dev` — proves the dynamic branch-detection
      logic needs no code change, as predicted.

### Phase 2 — UserRepo template (required, prevents future drift, low risk)
- [ ] **2.1** PR into `UserRepo`: fix `content/01GettingStarted/6_CentralRepo/index.md` —
      replace `prreviewJune23` references (branch name, `git pull prreviewJune23`, tree URL)
      with `dev`.
- [ ] **2.2** Leave `content/xx-GettingStarted-old/CentralRepo/index.md` and
      `content/00ChangeLog/_index.md` untouched — the former is an archived/superseded page,
      the latter is dated changelog history; both are acceptable to leave stale (see Risks).

### Phase 3 — Modernize the 33 repos already on the ECR-pull pattern (bulk, direct-push, single confirmation gate)
- [ ] **3.1** Extend `batch_repo_update.py` (or a copy of it) with:
      `REPOS` = the 33-repo list (see log file), `FILES_TO_COPY` unchanged except drop the
      `Dockerfile` copy line, `FILES_TO_DELETE` += `["Dockerfile"]` (+ `"Dockerfile-dev"`
      for `fortigate-automation-stitch-workshop`, the only repo in this group carrying one).
      `scripts/static.yml` copy already happens — since CentralRepo's own template already
      has the exit-code-capture fix, this single copy resolves that bug in all 33 repos too.
- [ ] **3.2** Dry-run: print the diff the script *would* make per repo without pushing
      (add a `DRY_RUN` guard if the script doesn't have one) — review before executing.
- [ ] **3.3** **Explicit go/no-go checkpoint before running** — this bulk-pushes directly to
      `main` on 33 repos with no PR, each triggering that repo's live Pages deploy
      immediately. Get a fresh confirmation at this step even though the plan itself is
      approved; do not treat plan approval as authorization to fire this script.
- [ ] **3.4** Run it. Spot-check 3-5 resulting Actions runs for a clean deploy before
      considering the phase done.

### Phase 4 — migrate the 19 repos still building locally (staged, in scope)
- [ ] **4.1** Kept as a distinct phase from Phase 3 — this is a genuine behavior change
      (local `docker build --target=prod` inside `static.yml` → pulling the prebuilt ECR
      image), not dead-code cleanup, so it gets its own pilot/verify/gate sequence rather
      than sharing Phase 3's single confirmation.
- [ ] **4.2** Pilot on 3 repos chosen for structural diversity, not convenience — each
      covers a different divergent shape found in the audit, so a template mismatch surfaces
      on 3 repos instead of on repo #14 of a 19-repo bulk push:
      - `cFOS-GKE-Workshop` — oldest/most divergent overall (`checkout@v3`,
        `configure-pages@v3`, `deploy-pages@v2`; the only repo in this group with both
        `Dockerfile` and `Dockerfile-dev`)
      - `fortigate-azure-sdwan-networking-workshop` — most divergent workflow logic (no
        retry-backoff loop, uses `sleep 5` instead of `docker wait`, no `image_variant`
        dispatch input)
      - `FortiADCIntro` — representative of the common 9-repo cluster
        (`Code-Security-Workshop`, `Forti-ProductXYZ`, `FortiADCIntro`, `FortiCNAPPRoadshow`,
        `FortiCNF`, `FortiDevOps-v2025`, `FortiDevSec-Workshop`, `FortiSASE`,
        `FortiWeb-Azure-ZTNA-FortiSoar`) that all run byte-similar old pre-ECR templates
      For each pilot: replace `.github/workflows/static.yml` with CentralRepo's current
      canonical `scripts/static.yml`, delete the local `Dockerfile` (and `Dockerfile-dev`
      for `cFOS-GKE-Workshop`), push, and watch the resulting Actions run to completion.
- [ ] **4.3** Verify: each of the 3 pilots' GitHub Pages deploy actually succeeds and serves
      the same content as before (spot-check the live site, not just a green checkmark —
      a workflow can report success while deploying stale or empty `docs/`).
- [ ] **4.4** **Explicit go/no-go checkpoint** before touching the remaining ~16 — if any
      pilot's deploy broke or behaved differently, stop and diagnose before scaling out; do
      not treat 2-of-3 pilots succeeding as good enough to proceed.
- [ ] **4.5** Bulk-push the same `static.yml` replacement + Dockerfile deletion to the
      remaining 16 repos (`api-and-websvc-fundamentals`, `cloud-architectures`,
      `forticnapp-code-security-demo`, `fortiweb-threat-protection`,
      `getting-started-general` [+ its `Dockerfile-dev`], `k8s-201-workshop`,
      `k8s-202-workshop`, `technical-recipe-azure-fweb-ztna-fortisoar`,
      `Code-Security-Workshop`, `Forti-ProductXYZ`, `FortiCNAPPRoadshow`, `FortiCNF`,
      `FortiDevOps-v2025`, `FortiDevSec-Workshop`, `FortiSASE`,
      `FortiWeb-Azure-ZTNA-FortiSoar`).
- [ ] **4.6** Spot-check 4-5 of the resulting Actions runs for a clean deploy, same as
      Phase 3.3.

## Plan Changes
- **2026-08-25, still Proposed:** initial draft deferred the 19 "still builds locally"
  repos to a separate future plan (Phase 4 was a stub). User asked for it folded into this
  plan's execution scope instead, with the risk addressed via a staged
  pilot-3/verify/gate/bulk-16 sequence rather than one flat 19-repo push. Phase 4 rewritten
  accordingly; see Plan below and the now-removed "Phase 4 own plan" Follow-up.

## Decisions & Commentary
- **Branch name: `dev`**, not `develop` — matches existing org convention
  (`Dockerfile-dev` naming, fortihugorunner's own `dev` branch) and requires no new
  vocabulary. User-confirmed.
- **Used GitHub's native rename API rather than delete+recreate** — preserves history,
  auto-handles PR retargeting and branch protection if either existed (neither did here,
  but this is the correct general practice going forward).
- **Sequenced workflow-file edits *before* the rename, on the old branch name** — so the
  instant the rename completes, the branch's own workflow files already say `branches:
  [dev]` and match. Renaming first and editing after would leave a gap where pushes to the
  newly-named branch don't trigger anything.
- **Discovered mid-plan that the rename cannot break any of the 52 downstream repos'
  CI** — the local Dockerfile's `prod` stage (what every repo's `static.yml` actually
  builds, on the 19 that build locally at all) pins `#main`, not `#prreviewJune23`. Only
  the `dev` stage — never exercised by any automated CI — references the branch being
  renamed. This decoupled "rename CentralRepo's branch" from "modernize 52 downstream
  repos" into two independently-schedulable pieces of work, which is why Phase 1 has no
  dependency on Phases 2-4.
- **Split the modernization ask into "safe" (33 repos, Phase 3) vs "behavior-changing" (19
  repos, Phase 4) rather than treating all 52 uniformly** — the user's framing ("nobody
  builds locally anymore... if applicable modernize") anticipated the first group; the
  second group's discovery changes the risk profile enough that it needed its own
  pilot/verify/gate sequence rather than sharing Phase 3's single confirmation. Initially
  proposed deferring Phase 4 to a separate future plan entirely; user asked for it folded
  into this plan's scope instead — addressed by staging it (3 structurally-diverse pilots
  → verify → gate → bulk the rest) rather than flattening it into one 19-repo push.
- **Left already-instantiated workshop repos' stale docs (2 CLAUDE.md files, several
  `content/*.md` "Getting Started" pages) out of required scope** — cosmetic/documentation
  drift only, no functional breakage, high fan-out cost relative to value. Logged as a
  follow-up rather than silently dropped.

## Files Changed
- (fill in during Phase 1 execution)

## Session Summary
- (write at end)

## Promotion
- [ ] `Decisions & Commentary` walked
- [ ] Durable facts promoted to `CLAUDE.md` — list them: <fill in at close-out — expect at
      minimum: the branch is now `dev`; the prod-stage-pins-main / dev-stage-pins-branch
      split and why it matters for future renames; the 33-vs-19 modernization split and
      where the full list lives>
- [ ] Nothing to promote (say so explicitly rather than leaving this section blank)
- [ ] `Status:` set to `Complete`

## Follow-ups
- [ ] Fix the 2 downstream repos whose own `CLAUDE.md` documents the stale
      `#prreviewJune23` pin as current fact (`Public-Cloud-104-CNAPP`, `k8s-101-workshop`) —
      cosmetic doc drift, low urgency.
- [ ] Consider fixing already-instantiated workshop repos' stale "how to contribute to
      CentralRepo" pages (inherited from the pre-fix `UserRepo` template) — cosmetic, low
      traffic, not required.
- [ ] `batch_repo_update.py`'s `REPOS = ['']` placeholder and lack of a dry-run mode are
      general gaps this plan's Phase 3 will need to patch locally — consider upstreaming
      a real `--dry-run` flag into the script permanently rather than a one-off guard.

## Risks / Open Questions
- **[Guessing]** Whether GitHub preserves a `git fetch`/`push` redirect from the old branch
  name for some grace period after a non-default-branch rename is not confirmed — Phase 1
  step 1.5 checks this empirically rather than assuming either way.
- **Code-search coverage caveat:** the 52-repo downstream list comes from
  `gh search code`, which can lag on recently-pushed content. Treat it as "confirmed
  affected," not "exhaustively affected" — a repo missed by indexing that still has the old
  pattern is low-risk (per the Constraints finding, cosmetic-only) but worth a periodic
  re-check.
- Two org repos' own `CLAUDE.md` (`Public-Cloud-104-CNAPP`, `k8s-101-workshop`) document
  the current stale state as fact — those will themselves go stale the moment this plan
  executes. Tracked as a Follow-up, not fixed here.

# Plan: Migrate All launchdemoform Usages to the New Provisioning Backend
Date: 2026-08-25
Owner: Jeff Kopko
Slug: launchdemoform-migration
Status: Approved
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-08-25_Jeff-Kopko_launchdemoform-migration.md
Log File: docs/plans/2026-08-25_Jeff-Kopko_launchdemoform-migration.log.md

## Goal
Find every real-world usage of the `launchdemoform` shortcode across the FortinetCloudCSE GitHub org, and bring each one onto the new Durable Function backend (progress UI, credential display, single-attempt lock — see the companion plans below) instead of the retired Automation-webhook flow. "Migrated" means: no local shortcode override shadowing CentralRepo's shared copy, a real `labdefinition` pointing at a lab-definition that actually exists in the backend repo, `provisionApiBaseUrl` set, and a real click-through confirming it works.

## Context / Links
- Backend spec/plan: `fortinet-on-demand-labs-provisioning-and-tracking/docs/plans/0001_2026-08-24_Jeff-Kopko_azure-function-rebuild.{spec.,}md` — deployed and live at `https://func-cse-lab-provisioning.azurewebsites.net`.
- Shortcode rebuild plan: `docs/plans/2026-08-24_Jeff-Kopko_launchdemoform-rebuild.md` (branch `launchdemoform-rebuild`, not yet merged as of this writing).
- Discovery method: `gh search code "launchdemoform" --owner FortinetCloudCSE` (44 result lines, well under the 100-line cap — not truncated) cross-referenced against `gh api repos/<repo>/contents/...` for override/config checks, and the backend's real `lab-definitions/` listing via the GitHub API (not a possibly-stale local clone).

## Constraints / Assumptions
- **Hard prerequisite, blocks everything below:** none of this matters until `launchdemoform-rebuild` is merged to CentralRepo's `prreviewJune23`/`main` and the `fortinet-hugo` Docker image is rebuilt — see that plan's "two-hop deploy" note. Nothing in this plan should be executed before that merge lands, or a repo could half-migrate onto config the old shortcode doesn't understand.
- **Discovery caveat:** `gh search code` only indexes default branches. A repo using `launchdemoform` exclusively on a non-default branch wouldn't surface here. Treat the 14-repo list below as "confirmed," not "provably exhaustive."
- **Real findings from this session's discovery** (14 repos with a live `{{< launchdemoform ... >}}` content invocation):

  | Repo | `labdefinition` | Lab-def exists? | Local override (shadow)? |
  |---|---|---|---|
  | `k8s-101-workshop` | `azure-k8s-seintro-110` | yes | no |
  | `k8s-201-workshop` | `azure-k8s-seintro-110` | yes | no |
  | `k8s-202-workshop` | `azure-k8s-seintro-110` | yes | no |
  | `fortigate-automation-stitch-workshop` | `azure-fgt-autostitch` | yes | **yes** |
  | `fortiweb-security-foundations-201` | `appsec-102` | yes | no |
  | `PublicCloud105-FortiFlex` | `flex-105` | yes | no |
  | `api-and-websvc-fundamentals` | `web-101` | yes | no |
  | `azure-102-foundational` | `azure-102-odl` | yes | **yes** |
  | `fortiweb-api-mcp-protection` | `fweb-mcp-110` | **no — missing** | no |
  | `FortiCNAPPRoadshow` | *(none)* | n/a | no |
  | `forticnapp-code-security-demo` | *(none)* | n/a | no |
  | `MGMT-in-AWS` | *(none)* | n/a | no |
  | `FortiWeb-Azure-ZTNA-FortiSoar` | *(none)* | n/a | **yes** |
  | `fortiweb-threat-protection` | *(none)* | n/a | no |

  None of the 14 currently have `provisionApiBaseUrl` set (expected — brand new param, didn't exist before this rebuild).
- **The 5 parameterless invocations are already non-functional today**, independent of anything in this migration — `$lab` renders empty, so even the *old* webhook flow had nothing to POST meaningfully. These need a product decision, not just a config fix: either the workshop owner supplies a real `labdefinition` (meaning the lab was always meant to provision something and got lost/never finished), or the shortcode should be removed per the standing guidance already documented in UserRepo's changelog ("launchdemoform should be... REMOVED from workshops which don't require Azure provisioning").
- **`fortiweb-api-mcp-protection` needs a real decision, not a mechanical fix.** `fweb-mcp-110` doesn't exist and never has (per the backend repo's `lab-definitions/` listing) — this predates the rebuild entirely. Either author a real `fweb-mcp-110` lab-definition (needs whoever owns that workshop's content to specify what it should actually provision), or point it at an existing close match (`fwebztna-lab`/`fwebthreatpro-lab` are the closest-named existing definitions, unconfirmed whether either is actually the right fit) if the `fweb-mcp-110` name was simply a naming-drift typo.
- **The 3 shadow-override repos need their local override resolved before a `provisionApiBaseUrl` config change would do anything** — `local_copy.sh` copies their own `layouts/shortcodes/launchdemoform.html` over CentralRepo's at container build time, so they'd keep running old/dead code regardless of `repoConfig.json`. Check each override's diff against CentralRepo's version first — a repo may have added genuine local customization worth preserving, not just gone stale by accident.

## Plan
- [ ] **Phase 1 — Land the prerequisite.** Merge `launchdemoform-rebuild` (CentralRepo), confirm the `fortinet-hugo` image rebuild actually ran (this org's established "confirm a run exists for the merge SHA" habit — see ai-101's CLAUDE.md skip-CI gotcha for why that check matters here too, even though this repo's own token risk hasn't been separately audited). **Still open — none of Phases 2-5's PRs are merge-effective until this lands.**
- [x] **Phase 2 — Triage the 5 parameterless repos — done 2026-08-25, PRs opened, not merged.** Real per-repo outcomes, not a uniform "remove": see `fortiweb-api-mcp-protection`'s corrected-finding note below for why "no lab-definition" turned out to mean something different than expected for at least one of these too. `FortiCNAPPRoadshow` ([PR #3](https://github.com/FortinetCloudCSE/FortiCNAPPRoadshow/pull/3)), `forticnapp-code-security-demo` ([PR #1](https://github.com/FortinetCloudCSE/forticnapp-code-security-demo/pull/1)), `MGMT-in-AWS` ([PR #1](https://github.com/FortinetCloudCSE/MGMT-in-AWS/pull/1)) — confirmed via git history (parameterless since first commit, no other lab-definition-shaped string anywhere in the repo) genuinely dead, removed. `fortiweb-threat-protection` ([PR #2](https://github.com/FortinetCloudCSE/fortiweb-threat-protection/pull/2)) — **not removed, restored**: git history shows it explicitly targeted `fwebthreatpro-lab` before a 2024 migration to the shared shortcode dropped the param, and the workshop's own Terraform/content still reference that exact lab's resource-group/share names. `FortiWeb-Azure-ZTNA-FortiSoar` ([PR #11](https://github.com/FortinetCloudCSE/FortiWeb-Azure-ZTNA-FortiSoar/pull/11)) — removed, but genuinely ambiguous (this workshop's real provisioning already works via a separate manual Terraform+FortiFlex flow unrelated to `launchdemoform`, but the removed section's "Setup Azure Cloud Shell" task leaves open whether `launchdemoform` was meant to supply the base Azure account for that) — **flagged explicitly in the PR for a second look before merging, unlike the other four.**
- [x] **Phase 3 — Resolve the 3 shadow overrides — done 2026-08-25, PRs opened, not merged.** All three turned out to be pure staleness, not customization worth preserving — confirmed by diffing each against CentralRepo's `launchdemoform-rebuild` shortcode before deleting, not assumed. `fortigate-automation-stitch-workshop` ([PR #15](https://github.com/FortinetCloudCSE/fortigate-automation-stitch-workshop/pull/15)) — a plain synchronous-`XMLHttpRequest` form predating even CentralRepo's current `main`. `azure-102-foundational` ([PR #27](https://github.com/FortinetCloudCSE/azure-102-foundational/pull/27)) — the literal pre-rewrite ancestor of CentralRepo's shortcode, same shape. `FortiWeb-Azure-ZTNA-FortiSoar` (folded into PR #11 above, since it was also parameterless) — a self-contained 2023-era form hardcoding a specific (likely-retired) Azure Automation webhook token. Each override-removal PR also adds `provisionApiBaseUrl`.
- [x] **Phase 4 — Resolve the missing `fweb-mcp-110` lab-definition — done 2026-08-25, and the premise was wrong.** `fweb-mcp-110` is real and always was — it exists in the actual Azure Storage container the backend reads at runtime (`fortinetcloudinttraining`/`fortinetcloudtraining-labconfigurations`, confirmed via a real fetch, HTTP 200), live-tested end-to-end successfully (real AD user, real TAP, real resource group + storage). **The original "missing" finding was a research error**, not a real gap: it checked this repo's own `lab-definitions/*.json` mirror files, which are NOT what the deployed Function reads (that folder was informal/hand-maintained and had silently drifted — missing this exact file — while nothing ever read it at runtime to notice). Fixed at the root: replaced the stale per-file mirrors with a generated snapshot (`lab-definitions/ALL_LAB_DEFINITIONS.json` + `scripts/snapshot_lab_definitions.py`, sourced live from the real blob container) in the backend repo, committed on the `azure-function-rebuild` branch. `fortiweb-api-mcp-protection` itself just needed `provisionApiBaseUrl` ([PR #51](https://github.com/FortinetCloudCSE/fortiweb-api-mcp-protection/pull/51), flagged urgent — this workshop has a beta on 2026-08-26).
- [ ] **Phase 5 — Per-repo config + verification.** `provisionApiBaseUrl` config is already included in every PR above (folded in rather than done as a separate pass). **Real click-through verification only done for 2 of the 10 real lab definitions so far** (`azure-102-odl` and `fweb-mcp-110`, both via live Playwright tests against the real deployed Function during this session) — the other 8 labs referenced across these repos are unverified against the new backend. Still blocked on Phase 1 (can't verify through the real shared shortcode until it's merged and repos rebuild their images) for anything beyond what a local dual-mount test server can approximate.
- [ ] **Phase 6 — Track completion.** Table below updated 2026-08-25; re-check after Phase 1 lands and each PR above is reviewed/merged.

## Plan Changes
- 2026-08-25 — **Corrected a real research error from this plan's own Constraints/Assumptions section**: "`fweb-mcp-110` doesn't exist" was wrong. It checked `fortinet-on-demand-labs-provisioning-and-tracking/lab-definitions/*.json` (informal, hand-maintained mirror files never read by any code at runtime) instead of the real Azure Storage container `src/lab_config.py` actually fetches from at runtime. The real container has 10 lab definitions, `fweb-mcp-110` among them, confirmed live and end-to-end tested successfully. Root-caused and fixed in the backend repo (see Phase 4) rather than just noted and moved past, since the same mistake could recur for any of the other 13 repos' lab references if anyone trusted that stale folder again.
- 2026-08-25 — Jeff's explicit direction, applied directly rather than re-litigated per-repo: parameterless repos get `launchdemoform` removed (not "ask the owner" as originally planned) unless git history shows real evidence of an intended lab (which materially changed the outcome for `fortiweb-threat-protection` — see Phase 2); shadow overrides get removed outright (not "diff and ask") unless real customization is found (none was, across all three).

## Decisions & Commentary
- Discovery done via the GitHub API/search directly against the org, not local checkouts — the earlier "8 shadow-override repos" follow-up (recorded in the `launchdemoform-rebuild` plan) was built from what happened to be cloned locally on this dev box, and it already missed one real shadow-override repo (`FortiWeb-Azure-ZTNA-FortiSoar`) that this org-wide pass caught. Local-checkout-based discovery is not reliable for an org this size; the API-based method here should be the template for the next check too.

## Files Changed
- 8 repos, 8 PRs opened 2026-08-25 (none merged — see Phase 2/3/4 above for detail per repo): `fortiweb-api-mcp-protection` #51, `FortiCNAPPRoadshow` #3, `forticnapp-code-security-demo` #1, `MGMT-in-AWS` #1, `fortiweb-threat-protection` #2, `fortigate-automation-stitch-workshop` #15, `azure-102-foundational` #27, `FortiWeb-Azure-ZTNA-FortiSoar` #11.
- `fortinet-on-demand-labs-provisioning-and-tracking` (`azure-function-rebuild` branch): replaced 9 stale `lab-definitions/*.json` mirror files with a generated `lab-definitions/ALL_LAB_DEFINITIONS.json` + `scripts/snapshot_lab_definitions.py`, sourced live from the real blob container. README updated to match.

## Session Summary
- (write at end) What changed + why.

## Promotion
- [ ] `Decisions & Commentary` walked
- [ ] Durable facts promoted to `CLAUDE.md` — list them: <...>
- [ ] Nothing to promote (say so explicitly rather than leaving this section blank)
- [ ] `Status:` set to `Complete`

## Follow-ups
- [ ] Re-run the `gh search code` discovery periodically — new repos keep adopting `launchdemoform` faster than this plan can track by hand (this session's count was already larger than the prior session's local-checkout-based estimate).
- [ ] Once this migration completes, revisit whether `local_copy.sh`'s shadow-copy mechanism itself should change (e.g. a lint/warning when a repo's local shortcode override drifts from CentralRepo's for N+ months) — out of scope here, but the root cause of Phase 3 existing at all.

## Risks / Open Questions
- ~~Phase 2 and Phase 4 both depend on input from people outside this session~~ — resolved for now: Jeff gave direct instructions covering both, applied above. `FortiWeb-Azure-ZTNA-FortiSoar`'s PR is still flagged for a human second look (see Phase 2) since evidence there was genuinely ambiguous, not because it's blocked on an external owner.
- Unknown how many of the 14 repos are still actively used in live workshops vs. dormant/retired content — worth a quick "when was this repo's Pages site last actually presented" gut-check per repo before investing Phase 2/4 effort in a workshop nobody runs anymore. Not done for this pass — moved fast given `fortiweb-api-mcp-protection`'s 2026-08-26 beta deadline.
- **New, 2026-08-25**: only 2 of the 10 real lab definitions in the real backend have been live-tested end-to-end (`azure-102-odl`, `fweb-mcp-110`) — the other 8 (`appsec-102`, `azure-fgt-autostitch`, `azure-k8s-seintro-110`, `azure-sdwan-lab`, `flex-105`, `fwebthreatpro-lab`, `fwebztna-lab`, `web-101`) are unverified against the new Function. Given the `fweb-mcp-110` research error above, don't assume the others are fine just because they're referenced somewhere — verify for real before calling any of them migrated.
- **New, 2026-08-25**: none of the 8 PRs opened today are merged. `fortiweb-api-mcp-protection` #51 is the one with a hard deadline (2026-08-26 beta) — needs review/merge priority, and still won't do anything until Phase 1 (CentralRepo merge + image rebuild) lands regardless.

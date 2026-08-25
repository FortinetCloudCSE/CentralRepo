# Plan: Migrate All launchdemoform Usages to the New Provisioning Backend
Date: 2026-08-25
Owner: Jeff Kopko
Slug: launchdemoform-migration
Status: Proposed
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
- [ ] **Phase 1 — Land the prerequisite.** Merge `launchdemoform-rebuild` (CentralRepo), confirm the `fortinet-hugo` image rebuild actually ran (this org's established "confirm a run exists for the merge SHA" habit — see ai-101's CLAUDE.md skip-CI gotcha for why that check matters here too, even though this repo's own token risk hasn't been separately audited).
- [ ] **Phase 2 — Triage the 5 parameterless repos.** For each (`FortiCNAPPRoadshow`, `forticnapp-code-security-demo`, `MGMT-in-AWS`, `FortiWeb-Azure-ZTNA-FortiSoar`, `fortiweb-threat-protection`): check git blame/history on the `{{< launchdemoform >}}` line and any surrounding content for evidence of an intended lab, or ask the workshop's owner. Outcome per repo is either "add the real `labdefinition`" (→ folds into Phase 5) or "remove the shortcode" (small, independent PR, not blocked on anything else in this plan).
- [ ] **Phase 3 — Resolve the 3 shadow overrides.** For `fortigate-automation-stitch-workshop`, `azure-102-foundational`, and `FortiWeb-Azure-ZTNA-FortiSoar`: diff the local `layouts/shortcodes/launchdemoform.html` against CentralRepo's current version. If it's just gone stale (no real customization), delete the local override so the repo inherits the shared shortcode on its next `pull-image`. If there's genuine customization, decide whether it still belongs (raise with whoever added it) — don't delete real work by reflex.
- [ ] **Phase 4 — Resolve the missing `fweb-mcp-110` lab-definition.** Get a decision from `fortiweb-api-mcp-protection`'s owner: author the real lab-definition, redirect to an existing one, or remove the shortcode if the provisioning step was abandoned. Author the JSON in the backend repo (following the schema of an existing `lab-definitions/*.json` file) if that's the outcome.
- [ ] **Phase 5 — Per-repo config + verification, once Phases 2-4 give each repo a real, resolvable `labdefinition`.** For each of the 9 (or more, depending on Phase 2 outcomes) repos ending up with a real lab reference: add `provisionApiBaseUrl: "https://func-cse-lab-provisioning.azurewebsites.net"` to `scripts/repoConfig.json`, rebuild/`pull-image`, and do a real click-through verification (same method as this session's UserRepo testing: local dual-mount Hugo server + Playwright, or manual) before marking that repo done.
- [ ] **Phase 6 — Track completion.** Keep the table in Constraints/Assumptions updated as each repo's status changes (or move to a `Files Changed`-style running log here) — 14 repos is enough that an implicit "did I get them all" is a real risk.

## Plan Changes
- (none)

## Decisions & Commentary
- Discovery done via the GitHub API/search directly against the org, not local checkouts — the earlier "8 shadow-override repos" follow-up (recorded in the `launchdemoform-rebuild` plan) was built from what happened to be cloned locally on this dev box, and it already missed one real shadow-override repo (`FortiWeb-Azure-ZTNA-FortiSoar`) that this org-wide pass caught. Local-checkout-based discovery is not reliable for an org this size; the API-based method here should be the template for the next check too.

## Files Changed
- (none yet — plan stage)

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
- Phase 2 and Phase 4 both depend on input from people outside this session (workshop content owners) — this plan cannot fully complete solo.
- Unknown how many of the 14 repos are still actively used in live workshops vs. dormant/retired content — worth a quick "when was this repo's Pages site last actually presented" gut-check per repo before investing Phase 2/4 effort in a workshop nobody runs anymore.

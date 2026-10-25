#!/bin/bash
# Migrate workshop repos' .github/workflows/static.yml to the thin caller of CentralRepo's reusable
# pages-deploy.yml (scripts/static.yml on main) via a PR. Dry-run by default.
# Usage: migrate_static_yml.sh [--apply] <repo> [<repo>...]     (repo names under FortinetCloudCSE)
# Env: LEDGER (append-only log), WORK (scratch dir for clones), IMAGE (local image for pre-flight, default fortinet-hugo:latest)
set -u
ORG=FortinetCloudCSE
ALLOW="1583cc75 f0aff64a ecf3e8e9"   # known old template, previous template, ai-101 variant
APPLY=0; [ "${1:-}" = "--apply" ] && { APPLY=1; shift; }
WORK=${WORK:-$(mktemp -d)}; LEDGER=${LEDGER:-$WORK/migration-ledger.log}; IMAGE=${IMAGE:-fortinet-hugo:latest}
log() { echo "$(date -u +%FT%TZ) | $1 | $2 | $3 | ${4:--}" | tee -a "$LEDGER"; }
mkdir -p "$WORK"
NEW=$WORK/new-static.yml
gh api "repos/$ORG/CentralRepo/contents/scripts/static.yml?ref=main" --jq .content | base64 -d > "$NEW" || exit 1
NEWMD=$(md5sum "$NEW" | cut -c1-8)

migrate() {
  local r=$1 R=$ORG/$1
  case "$r" in FortiShield*|CentralRepo) log "$r" skip "refused name" ; return 2;; esac
  [ "$(gh repo view "$R" --json visibility --jq .visibility 2>/dev/null)" = PUBLIC ] || { log "$r" skip "not public/unreadable"; return 2; }
  local cur md
  cur=$(gh api "repos/$R/contents/.github/workflows/static.yml?ref=main" --jq .content 2>/dev/null | base64 -d) || true
  [ -n "$cur" ] || { log "$r" skip "no static.yml"; return 2; }
  md=$(printf '%s\n' "$cur" | md5sum | cut -c1-8)
  [ "$md" = "$NEWMD" ] && { log "$r" skip "already migrated"; return 0; }
  case " $ALLOW " in *" $md "*) ;; *) log "$r" skip "md5 $md not allow-listed"; return 2;; esac
  if [ $APPLY -eq 0 ]; then log "$r" dry-run "would migrate (old md5 $md)"; return 0; fi
  local t0=$SECONDS d=$WORK/$r; rm -rf "$d"
  git clone -q --depth 1 "https://github.com/$R.git" "$d" || { log "$r" fail "clone"; return 1; }
  ( cd "$d" && docker run --rm -v "$PWD:/home/UserRepo" "$IMAGE" build >"$WORK/$r.build.log" 2>&1 ) \
    || { log "$r" preflight "FAILED (see $WORK/$r.build.log)"; return 1; }
  log "$r" preflight "local build exit 0"
  cd "$d" || return 1
  git checkout -q -b migrate-reusable-pages && cp "$NEW" .github/workflows/static.yml && git commit -qam "ci: call CentralRepo reusable pages-deploy workflow (@v1)" || return 1
  git push -q -u origin migrate-reusable-pages 2>/dev/null || { log "$r" fail "push"; return 1; }
  local head st; head=$(git rev-parse HEAD)
  poll_jenkins() {
    for i in $(seq 1 ${JENKINS_TRIES:-20}); do
      st=$(gh api "repos/$R/commits/$head/status" --jq '[.statuses[]|select(.context=="ci/jenkins/build-status")|.state][0]')
      [ "$st" = success ] && break; [ "$st" = failure ] || [ "$st" = error ] && break; sleep 15
    done
  }
  poll_jenkins
  if [ -z "$st" ] || [ "$st" = null ]; then
    # A brand-new Jenkins job's first poll can build another branch; one empty commit gives it a changed revision.
    log "$r" jenkins "no status; one empty re-trigger commit"
    git commit -q --allow-empty -m "ci: retrigger Jenkins" && git push -q origin migrate-reusable-pages 2>/dev/null || { log "$r" fail "retrigger push"; return 1; }
    head=$(git rev-parse HEAD); poll_jenkins
  fi
  [ "$st" = success ] || { log "$r" jenkins "state=$st"; return 1; }
  local url; url=$(gh pr create -R "$R" --base main --head migrate-reusable-pages --title "ci: call CentralRepo reusable pages-deploy workflow (@v1)" --body "Replaces .github/workflows/static.yml with the thin caller from CentralRepo scripts/static.yml.

🤖 Generated with [Claude Code](https://claude.com/claude-code)") || return 1
  local n=${url##*/}; log "$r" "PR opened" ok "$url"; sleep 15
  local meth=squash; [ "$r" = UserRepo ] && meth=rebase
  gh-merge-verify "$n" --repo "$R" --method $meth -- --subject "ci: call CentralRepo reusable pages-deploy workflow (@v1) (#$n)" --body "Thin caller of CentralRepo pages-deploy.yml@v1." >"$WORK/$r.merge.log" 2>&1
  local sha; sha=$(gh pr view "$n" -R "$R" --json mergeCommit,state --jq 'select(.state=="MERGED")|.mergeCommit.oid')
  [ -n "$sha" ] || sha=$(gh api "repos/$R/commits/main" --jq .sha)
  [ -n "$sha" ] || { log "$r" fail "merge ($WORK/$r.merge.log)"; return 1; }
  log "$r" "PR merged" ok "$sha"
  local run
  for i in 1 2 3 4 5 6; do run=$(gh run list -R "$R" --workflow static.yml --commit "$sha" --json databaseId --jq '.[0].databaseId'); [ -n "$run" ] && break; sleep 10; done
  [ -n "$run" ] || { log "$r" fail "no Pages run for $sha"; return 1; }
  gh run watch "$run" -R "$R" >/dev/null 2>&1
  local conc steps auth pu c title sm dep
  conc=$(gh run view "$run" -R "$R" --json conclusion --jq .conclusion)
  steps=$(gh run view "$run" -R "$R" --json jobs --jq '[.jobs[].steps[]|select(.name=="Login to ECR Public")|.conclusion][0]')
  gh run view "$run" -R "$R" --log 2>/dev/null | grep -q "Authenticated as" && auth=yes || auth=NO
  pu=$(gh api "repos/$R/pages" --jq .html_url)
  for i in 1 2 3 4; do c=$(curl -sL -o "$WORK/p.html" -w '%{http_code} %{url_effective}' "$pu"); case $c in 200*) break;; esac; sleep 30; done
  title=$(grep -io '<title>[^<]*' "$WORK/p.html" | head -1)
  sm=$(curl -sL -o /dev/null -w '%{http_code}' "${pu}sitemap.xml")
  dep=$(gh api "repos/$R/deployments" --jq '.[0].sha')
  log "$r" "pages run" "$conc; login=$steps authenticated=$auth" "https://github.com/$R/actions/runs/$run"
  log "$r" "page check" "root=$c $title sitemap=$sm deploy_sha_match=$([ "$dep" = "$sha" ] && echo yes || echo NO) elapsed=$((SECONDS-t0))s" "$pu"
  [ "$conc" = success ] && [ "$steps" = success ] && [ "$auth" = yes ] && [ "${c%% *}" = 200 ]
}

rc=0
for r in "$@"; do migrate "$r" || { rc=$?; [ $APPLY -eq 1 ] && [ $rc -eq 1 ] && { echo "stopping after failure on $r"; exit 1; }; }; done
exit 0

#!/bin/bash
set -e
PUBLIC_DIR="${1:?Usage: test_rendered_html.sh <public_dir>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# A1: Form action must NOT be a bare relative path (/checkin)
# Catches the 405 regression: form action="/checkin" hits GitHub Pages
if grep -rq 'action="/checkin"' "$PUBLIC_DIR"; then
  fail "A1: form action is relative /checkin — will 405 on GitHub Pages"
fi
pass "A1: no relative /checkin form action"

# A2: Form action must be an absolute HTTPS URL to the analytics API
# (only applies when analyticsBaseUrl is set — check index.html)
if grep -q 'analyticsBaseUrl' "$PUBLIC_DIR/../hugo.toml" 2>/dev/null || \
   grep -q 'tecanalytics' "$PUBLIC_DIR/index.html" 2>/dev/null; then
  if ! grep -q 'action="https://tecanalytics.forticloudcse.com/checkin"' "$PUBLIC_DIR/index.html"; then
    fail "A2: checkin form action is not the expected absolute URL"
  fi
  pass "A2: checkin form action is absolute API URL"
else
  pass "A2: skipped (analyticsBaseUrl not set — fallback produces prod URL)"
fi

# A3: No relative CSS url() — catches Xperts background image path regression
if grep -rq 'url("\.\./' "$PUBLIC_DIR"; then
  fail "A3: relative ../  CSS url() found — images will be broken"
fi
pass "A3: no relative CSS url() paths"

# A4: No quizdown CDN scripts
if grep -rq 'quizdown.jsdelivr.net' "$PUBLIC_DIR"; then
  fail "A4: quizdown CDN script found — should have been removed"
fi
pass "A4: no quizdown CDN scripts"

# A5: No invalid iframe allow="same-origin"
if grep -rq 'allow="same-origin"' "$PUBLIC_DIR"; then
  fail "A5: invalid allow=same-origin found (not a Permissions Policy feature)"
fi
pass "A5: no invalid allow=same-origin"

# A6: No defeating sandbox combination
if grep -rEq 'sandbox="[^"]*allow-scripts[^"]*allow-same-origin|allow-same-origin[^"]*allow-scripts' "$PUBLIC_DIR"; then
  fail "A6: sandbox has allow-scripts+allow-same-origin — defeats sandboxing"
fi
pass "A6: no defeating sandbox combination"

# A7: No htmlEscape in rendered output (removed in Hugo 0.121)
if grep -rq 'htmlEscape' "$PUBLIC_DIR"; then
  fail "A7: htmlEscape found in output (should be removed — deprecated Hugo function)"
fi
pass "A7: no htmlEscape in rendered output"

# A8: ANALYTICS_BASE must not be an empty JS string on index.html
# When analyticsBaseUrl is missing, fallback should provide the prod URL
if grep -q 'ANALYTICS_BASE = ""' "$PUBLIC_DIR/index.html"; then
  fail "A8: ANALYTICS_BASE is empty string — analyticsBaseUrl fallback is broken"
fi
pass "A8: ANALYTICS_BASE is not empty"

# A9: google_analytics_authorMode.html must NOT contain googletagmanager
# This file is swapped in by hugoServer_authorMode.sh — GA must be suppressed in author mode
if grep -q 'googletagmanager' "$REPO_ROOT/layouts/partials/google_analytics_authorMode.html"; then
  fail "A9: google_analytics_authorMode.html contains googletagmanager — GA fires in author mode"
fi
pass "A9: GA suppressed in authorMode partial"

# A10: Checkin form must have method="POST" in rendered index.html
if ! grep -q 'method="POST"' "$PUBLIC_DIR/index.html"; then
  fail "A10: checkin form missing method=POST in rendered index.html"
fi
pass "A10: checkin form has method=POST"

# A11: No htmlEscape calls in layout source files (belt-and-suspenders; A7 covers rendered output)
if grep -rq 'htmlEscape' "$REPO_ROOT/layouts/"; then
  fail "A11: htmlEscape found in layout source — remove it (removed in Hugo 0.121)"
fi
pass "A11: no htmlEscape in layout source files"

echo ""
echo "All assertions passed for: $PUBLIC_DIR"

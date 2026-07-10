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

# A2: Checkin form analytics base URL must be the expected absolute HTTPS URL.
# Hugo template actions inside JS backtick literals get JS-context-escaped by
# html/template; the URL is passed via data-analytics-base (HTML attribute context
# is safe) and read with getAttribute() in JS — same pattern as the video header.
if ! grep -q 'data-analytics-base="https://tecanalytics.forticloudcse.com"' "$PUBLIC_DIR/index.html"; then
  fail "A2: data-analytics-base is not the expected absolute URL"
fi
pass "A2: data-analytics-base is correct absolute API URL"

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

# A12: Logo img src must not contain leading whitespace or newlines
# The Go template multiline src='\n...\n' pattern causes broken img in some environments.
# Catches regressions where the logo template puts whitespace inside the src attribute value.
if grep -Pzo 'src='"'"'\s*\n' "$PUBLIC_DIR/index.html" > /dev/null 2>&1; then
  fail "A12: logo img src attribute contains leading whitespace/newlines — clean up logo.html template"
fi
pass "A12: logo img src is clean (no leading whitespace)"

# A13: Dockerfile must target menu-footer.html for version injection, not copyright.html
# Catches the regression where the sed target was left pointing at a file that no longer
# contains the os.Getenv pattern after moving version display to menu-footer.html.
if grep -q 'copyright.html' "$REPO_ROOT/Dockerfile" && grep -q 'HUGO_VERSION_TAG' "$REPO_ROOT/Dockerfile"; then
  fail "A13: Dockerfile sed targets copyright.html for version injection — should target menu-footer.html"
fi
pass "A13: Dockerfile version injection targets correct file"

# A14: menu-footer.html must contain the os.Getenv version pattern (Dockerfile sed target is valid)
if ! grep -q 'os.Getenv "HUGO_VERSION_TAG"' "$REPO_ROOT/layouts/partials/menu-footer.html"; then
  fail "A14: menu-footer.html missing HUGO_VERSION_TAG pattern — Dockerfile sed will silently fail to inject version"
fi
pass "A14: menu-footer.html contains HUGO_VERSION_TAG pattern for Dockerfile version injection"

echo ""
echo "All assertions passed for: $PUBLIC_DIR"

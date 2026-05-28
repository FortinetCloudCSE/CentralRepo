#!/bin/bash
set -e
cd "$(git rev-parse --show-toplevel)"

echo "=== Phase 3: Regex validation ==="
npm run validate:regex

echo ""
echo "=== Phase 4: Config schema validation ==="
npm run validate:config

echo ""
echo "All local checks passed."
echo "Hugo build validation (Phase 1-2) runs in CI via .github/workflows/ci.yml"

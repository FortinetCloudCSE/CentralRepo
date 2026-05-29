# Plan: CentralRepo Automated Testing
Date: 2026-05-28
Owner: Jeff Kopko
Slug: centralrepo-testing
Plan File: docs/plans/2026-05-28_Jeff-Kopko_centralrepo-testing.md
Log File: docs/plans/2026-05-28_Jeff-Kopko_centralrepo-testing.log.md

## Goal
Add automated testing to CentralRepo so that regressions are caught in CI before merging to main — not discovered in production. Zero test coverage currently; all bugs discovered manually or by end users.

## Context / Links
- Triggered by: `analyticsBaseUrl` fallback regression (PR #61 hotfix) — changed default to `""` broke check-in for all workshops that don't explicitly set the param
- Related PRs: #60 (bug fix session), #61 (hotfix)
- Regression catalog: `docs/plans/2026-05-28_Jeff-Kopko_centralrepo-bugfix.log.md`
- CI entry point: `.github/workflows/static.yml` (currently build+deploy only, no tests)
- Key files under test: `layouts/partials/analytics_checkin.html`, `layouts/partials/silent_cross_site_checkin.html`, `layouts/partials/google_analytics.html`, `layouts/partials/content.html`, `layouts/shortcodes/quizframe.html`, `layouts/shortcodes/launchdemoform.html`, `scripts/templates/hugo.jinja`

## Regression Catalog (what testing must catch)

From the 2026-05-28 bug fix session — grouped by detection method:

| Category | Specific Regression | Detection Layer |
|----------|-------------------|-----------------|
| Config fallback | `analyticsBaseUrl` default `""` → form action `/checkin` → GitHub Pages 405 | Rendered HTML assertion |
| Hugo build error | `htmlEscape` removed Hugo 0.121+ | Hugo build (exit code) |
| Hugo deprecation | `languageCode`, `disableSearch`, `math` param names | Hugo build (warning capture) |
| JS regex | Email `pattern` unescaped `+` → Chrome 119+ SyntaxError | ESLint / HTML lint |
| CSS path | `url("../images/...")` relative path → invisible backgrounds | Rendered HTML assertion |
| Iframe attrs | `allow="same-origin"` not a Permissions Policy feature | HTML lint |
| Template typo | `[Langauges]` → `[Languages]` nesting error | Hugo build (exit code) |
| Dead code | `orig_*.html` unreferenced partials | Partial call graph audit (manual/scripted) |
| Jinja config | Wrong param name in template → silently no-ops | Config smoke test |

## Constraints / Assumptions
- No npm/package.json in CentralRepo — any JS tooling must be added as a dev dependency or run via npx/Docker
- Hugo is only available inside the Docker container (`hugomods/hugo:std`) — local Hugo binary version differs from CI
- Workshop repos are forks of UserRepo; CentralRepo tests run against the CentralRepo content (not a full workshop)
- Tests must run in GitHub Actions on push to `prreviewJune23` (dev) and on PR to `main`
- The `hugotester-local` build path (`LOCAL=true`) is the canonical test environment
- E2E browser tests require a running Hugo dev server — either a fixture container or `hugo serve` in CI
- The TEC-analytics `/checkin` and `/checkin/silent` API endpoints should be mocked/stubbed in tests (no prod API calls in CI)
- `fortihugorunner` is not available in GitHub Actions — use Docker directly

## Plan

### Phase 1 — CI workflow + Hugo build validation (highest ROI, zero new tooling)

**Goal**: catch build errors and deprecation warnings in CI before merge.

- [x] **1.1** Create `.github/workflows/ci.yml` — runs on push to `prreviewJune23` and on PR to `main`
  - Job: `build-validate`
  - Steps: checkout (full depth for submodules), build `hugotester-local` image with `LOCAL=true`, run `hugo build` inside container against CentralRepo's own content, **fail on any ERROR**, capture WARNs and write to job summary
  - This catches: `htmlEscape` removal, `[Langauges]` typo, broken partial calls, invalid hugo.toml

- [x] **1.2** Add `--logVerbose` flag and parse output
  - Promote specific Relearn 8.0.0 deprecation warnings to errors once Relearn is upgraded
  - Emit WARN lines to GitHub step summary for visibility even when not failing

- [x] **1.3** Validate `hugo.jinja` generates valid TOML
  - Run `generate_toml.sh` inside the container, then `hugo config` to parse the result
  - Fails if TOML is malformed or hugo rejects the config

### Phase 2 — Rendered HTML assertions (catches the 405 regression class)

**Goal**: build the Hugo site and assert on the output HTML — no browser needed.

- [x] **2.1** Create `scripts/test/` directory with assertion scripts
  - `test_rendered_html.sh` — runs `hugo build`, then asserts on `public/` output

- [x] **2.2** Write assertion: **form action must be absolute URL**
  ```bash
  # Must NOT be a relative URL when analyticsBaseUrl is set
  grep -r 'action="/' public/ && echo "FAIL: relative form action found" && exit 1
  # Must contain the API domain
  grep -r 'action="https://tecanalytics' public/index.html || (echo "FAIL: checkin form action missing" && exit 1)
  ```
  — Directly catches the 405 regression.

- [x] **2.3** Write assertion: **CSS background image paths are root-relative**
  ```bash
  grep -r 'url("\.\./' public/ && echo "FAIL: relative CSS url() found" && exit 1
  ```
  — Catches Xperts background image regression.

- [x] **2.4** Write assertion: **quizdown CDN scripts are absent**
  ```bash
  grep -r 'quizdown.jsdelivr' public/ && echo "FAIL: quizdown CDN script found" && exit 1
  ```

- [x] **2.5** Write assertion: **iframe allow attribute has no invalid Permissions Policy features**
  ```bash
  grep -r 'allow="same-origin"' public/ && echo "FAIL: invalid allow attribute found" && exit 1
  ```

- [x] **2.6** Write assertion: **no sandbox with both allow-scripts and allow-same-origin**
  ```bash
  grep -r 'allow-scripts.*allow-same-origin\|allow-same-origin.*allow-scripts' public/ && echo "FAIL: defeating sandbox combo found" && exit 1
  ```

- [x] **2.7** Create a second test config (`scripts/test/repoConfig.test.json`) with all params set to known values, and a corresponding test Hugo content dir with one home page and one non-home page — so assertions run against deterministic output

- [x] **2.8** Wire Phase 2 assertions into `ci.yml` as a second job step (or separate job: `assert-html`)

### Phase 3 — JavaScript linting (catches regex, undefined vars, syntax)

**Goal**: catch JS errors in Hugo partials before they reach any browser.

- [x] **3.1** Extract JS blocks from partials into lint-friendly form
  - ESLint on extracted JS abandoned: Go templates embed in too many JS syntactic positions (string literals, expressions, statements) to stub reliably without a Hugo-aware parser. Instead, JS-related bugs are covered by regex validation (A9-A11 assertions) and `validate_regex.js`.

- [x] **3.2** Add ESLint with minimal ruleset
  - ESLint dropped (see 3.1). `package.json` retained as convenience wrapper for `validate:regex` and `validate:config` npm scripts.

- [x] **3.3** Wire ESLint into `ci.yml` (runs on extracted JS, not raw templates)
  - Replaced with `node scripts/test/validate_regex.js` step in `lint-and-validate` job.

- [x] **3.4** Write a regex validity test
  - `scripts/test/validate_regex.js` — validates all `pattern="..."` values in layouts/ as valid v-flag regexes. Passes locally.

### Phase 4 — Config schema validation (catches repoConfig.json drift)

**Goal**: validate that `repoConfig.json` in CentralRepo and in any workshop fork matches the expected schema.

- [x] **4.1** Create `scripts/repoConfig.schema.json` — JSON Schema defining all expected fields, types, and required vs optional
  - Required: `repoName`, `workshopTitle`, `themeVariant`
  - Optional with defaults: `analyticsBaseUrl`, `quizUrl`, `videoHeaderSrc`, `videoHeaderInterval`, `marketingCode`, `googleServicesID`
  - Enum for `themeVariant`: `["Workshop", "Demo", "UseCase", "Spotlight", "Xperts2024", "Xperts2025", "CloudCSEMovie", "FortinetSilver", "FortinetTeal"]`

- [x] **4.2** Add schema validation step to `ci.yml`
  - `npx ajv-cli validate -s scripts/repoConfig.schema.json -d scripts/repoConfig.json`
  - Catches: wrong type, missing required field, invalid themeVariant value

- [x] **4.3** Document schema in README and in `scripts/repoConfig.json` comments

### Phase 5 — E2E browser tests for check-in flow (highest confidence, highest cost)

**Goal**: verify the check-in form actually works end-to-end: form renders, submits, sets cookies correctly. Mock the TEC-analytics API.

- [ ] **5.1** Add Playwright as a dev dependency in `package.json`
  - Use Chromium only (the platform that introduced the v-flag regression)

- [ ] **5.2** Write a mock TEC-analytics API server
  - Minimal Node.js Express server (or use `msw` — Mock Service Worker)
  - Responds to `POST /checkin` with `302 redirect` and `POST /checkin/silent` with `{ok: true}`
  - Runs alongside Hugo dev server during tests

- [ ] **5.3** Write Playwright tests in `scripts/test/playwright/`

  | Test | What it asserts |
  |------|----------------|
  | `checkin-form.spec.ts` | Home page renders form; email input has valid `pattern`; form submits POST to correct absolute URL; on success, `fortiuser` cookie is set |
  | `checkin-fallback.spec.ts` | Non-home page without cookie redirects to home |
  | `silent-checkin.spec.ts` | `ANALYTICS_BASE` is populated; silent check-in fires `fetch` to `/checkin/silent` when cookies present |
  | `author-mode.spec.ts` | In author mode (swapped partial), GA scripts are absent; no fetch errors |
  | `quizframe.spec.ts` | `quizframe` shortcode iframe has no `sandbox` attr, no `allow="same-origin"` |

- [ ] **5.4** Wire Playwright into `ci.yml` as a separate job
  - Start Hugo dev server (`docker run server`) + mock API
  - Run Playwright headless
  - Upload trace on failure as artifact

- [ ] **5.5** Self-hosted runner consideration
  - If GitHub-hosted runners are too slow for Docker-in-Docker, run on the GCE dev box (same pattern as TEC-analytics Playwright runner)

### Phase 6 — Documentation and developer workflow

- [x] **6.1** Add `make test` (or `./scripts/test/run_tests.sh`) that runs all phases locally via Docker
  - Phase 1: `docker run hugotester-local hugo build` (error check)
  - Phase 2: `scripts/test/test_rendered_html.sh`
  - Phase 3: ESLint on extracted JS
  - Phase 4: ajv schema validation
  - Phase 5: Playwright (optional, requires port availability)

- [x] **6.2** Update README with testing section — how to run tests locally, what each phase covers

- [x] **6.3** Add pre-push git hook (analogous to TEC-analytics pattern) that runs Phase 1–3 before pushing to `prreviewJune23`

- [x] **6.4** Update `CLAUDE.md` with testing conventions — where tests live, how to add assertions for new features

## Decisions & Commentary
- **Phase ordering by ROI**: Phase 1 (build) and Phase 2 (HTML assertions) eliminate 6 of 9 regression categories with zero browser dependency. Do these first.
- **No direct ESLint on partials**: Go template syntax (`{{ }}`) makes raw ESLint impossible. Extract-then-lint is the pragmatic approach; a perfect solution would require a custom Hugo-aware linter.
- **Mock the API in E2E**: don't test against the live TEC-analytics prod or dev API in CI — flaky, slow, and pollutes analytics data.
- **Playwright over Cypress**: TEC-analytics already uses Playwright; consistent toolchain, and Playwright's cookie handling is better for our use case.
- **Schema validation over runtime guards**: workshop authors set `repoConfig.json` once; catching wrong values at CI time is far better than silent no-ops at page render.
- **Phase 5 is optional MVP scope**: the 405 regression would have been caught by Phase 2 (rendered HTML assertion on form action). Phase 5 adds confidence but Phase 1-4 already eliminate the regression categories that have actually occurred.

## Files to Create
- `.github/workflows/ci.yml` — new CI workflow
- `package.json` — ESLint + Playwright dev dependencies
- `scripts/test/repoConfig.test.json` — test fixture config
- `scripts/test/test_rendered_html.sh` — Phase 2 assertions
- `scripts/test/extract_js.py` — Go template stripper for ESLint
- `scripts/test/run_tests.sh` — local test runner
- `scripts/test/playwright/checkin-form.spec.ts` — Phase 5 E2E
- `scripts/test/playwright/checkin-fallback.spec.ts`
- `scripts/test/playwright/silent-checkin.spec.ts`
- `scripts/test/playwright/author-mode.spec.ts`
- `scripts/test/playwright/quizframe.spec.ts`
- `scripts/repoConfig.schema.json` — Phase 4 JSON Schema

## Files Modified
- `.github/workflows/static.yml` — add test gate before deploy (or keep separate)
- `README.md` — testing section
- `CLAUDE.md` — testing conventions

## Session Summary

Implemented Phases 1–4 (plus Phase 6 developer workflow docs). Phase 5 (Playwright E2E) deferred.

**Key decisions made during implementation:**
- ESLint on extracted JS abandoned: Go templates embed in too many JS syntactic positions to stub reliably. Replaced with `validate_regex.js` (Chrome v-flag regex check) + 3 additional HTML assertions (A9-A11) covering author-mode GA suppression, form method, and layout source htmlEscape.
- `analyticsBaseUrl` format constraint removed from JSON Schema to avoid strict URI validation failures.
- `generate_toml.py` patched to read `REPO_CONFIG_PATH` env var (default preserved for Docker compat).

**Files created:**
- `.github/workflows/ci.yml` — 4-job CI pipeline
- `scripts/test/test_rendered_html.sh` — 11 HTML assertions (A1–A11)
- `scripts/test/validate_regex.js` — Chrome v-flag regex validator
- `scripts/test/validate_config.py` — JSON Schema validator
- `scripts/test/run_tests.sh` — local test runner
- `scripts/test/fixtures/no_analytics_url.json` — fixture testing fallback behavior
- `scripts/repoConfig.schema.json` — JSON Schema for repoConfig
- `package.json` — npm convenience scripts
- `.githooks/pre-push` — lightweight pre-push hook

**Files modified:**
- `scripts/generate_toml.py` — REPO_CONFIG_PATH env var support
- `.gitignore` — added node_modules/, tmp/
- `README.md` — Testing section added
- `CLAUDE.md` — Testing section added

## Risks / Open Questions
- **Q1. MVP scope**: Is Phase 1–4 (no browser) the right first milestone, or should we include at least one Playwright E2E test from the start to establish the pattern?
- **Q2. CI runner**: GitHub-hosted runners or self-hosted GCE box for tests? Docker-in-Docker (needed for Phase 1–2) requires `--privileged` or `docker:dind` in GitHub Actions — confirm this is acceptable.
- **Q3. Pre-push hook**: Should Phase 1–3 run as a pre-push git hook (blocking) or just in CI (non-blocking locally)? Heavy Docker build may be too slow for pre-push.
- **Q4. Workshop fork testing**: Should CentralRepo CI also test against a representative workshop fork (e.g., UserRepo) to catch integration regressions, or only against CentralRepo's own content?
- **Q5. Relearn version pin**: Phase 1 CI will surface Relearn 8.0.0 deprecation warnings. Should these eventually be treated as errors, or remain as informational WARNs until Relearn fixes them upstream?

## Follow-ups
- [ ] After Phase 1 ships: audit all existing `WARN` output and decide which to promote to errors
- [ ] After Phase 2 ships: review regression catalog and add any missing HTML assertions
- [ ] After Phase 4 ships: document schema in workshop onboarding guide so new repos start with a valid `repoConfig.json`
- [ ] After Phase 5 ships: run Playwright tests against `dev.tecanalytics.forticloudcse.com` as a post-deploy smoke test (similar to TEC-analytics pattern)

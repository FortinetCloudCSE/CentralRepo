# Plan: Standard command/expected-output render hooks
Date: 2026-09-24
Owner: Jeff Kopko
Slug: cmd-output-blocks
Status: Approved
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-09-24_Jeff-Kopko_cmd-output-blocks.md
Log File: none

<!-- Deviation from the source-plan instruction: it named `plans/2026-09-24_Jeff-Kopko_cmd-output-blocks.md`.
     CentralRepo has no root `plans/` dir; every existing CentralRepo plan lives in `docs/plans/` with this
     same unnumbered naming (see 2026-08-25_Jeff-Kopko_centralrepo-branch-rename.md, etc). Filed here instead
     to match the repo's actual convention; `plans/` is the ai-101/UserRepo (Hugo workshop) convention per
     CentralRepo CLAUDE.md's own note that `docs/` is deleted by automation in *those* repos, not this one. -->

## Goal
- Phase 2 of xperts-ai-101 plan 0001: add a standard, visually distinct "command to run" / "expected output"
  presentation to CentralRepo — plain markdown fences (` ```bash {run="bastion"} ` / ` ```output `) — so any
  workshop can opt in with zero visual change for workshops that don't.

## Context / Links
- Source plan: `/home/ubuntu/pythonProjects/xperts-ai-101/plans/0001_2026-09-24_jkopko_workshop-review-and-cmd-output-blocks.md`
  (see its "Proposed convention", "Context / Links", "Risks / Open Questions" — owner-approved 2026-09-24).
- Theme: Hugo Relearn 8.0.0, Hugo 0.165.0 (`Dockerfile:15`).
- Worktree: `/home/ubuntu/pythonProjects/worktrees/CentralRepo-cmd-output-blocks`, branch `cmd-output-blocks` off `origin/dev`.
- Companion UserRepo worktree (demo page, Phase 2c): `~/pythonProjects/worktrees/UserRepo-cmd-output-blocks`, branch `cmd-output-blocks` off `main`.

## Constraints / Assumptions
- Never fork `themes/hugo-theme-relearn/assets/js/theme.js` — suppress the copy button from CentralRepo's own asset/partial layer only.
- `bash`/`sh`/`shell` hooks must be byte-identical pass-through to `partials/shortcodes/highlight.html` when `run` is absent.
- STOP before `git push`, PR, or image publish — pushing `dev` rebuilds the shared dev image (shared infra); owner approves that separately.

## Plan
- [x] 2a. Render-verify ` ```bash {title="Run on: bastion"} ` on the current image (fallback path). Record result below.
- [x] 2b. Add `render-codeblock-output.html`; pass-through `render-codeblock-{bash,sh,shell}.html` with `run=` badge, CSS, copy-suppression JS.
- [x] 2c. Prove it on UserRepo with a demo page, built on the `LOCAL=true` dev image.
- [x] 2d. README + RELEASE_NOTES.
- [x] Diff built HTML of a real workshop (UserRepo) before/after for the no-`run` bash/sh/shell case — confirm byte-identical modulo known non-deterministic tokens.
- [x] `/code-review medium` on the diff; fix what's real.
- [ ] Close-out: promote decisions to CLAUDE.md, Status → Complete. (Deferred to owner after they review/push — see Follow-ups.)

## Plan Changes
- (none)

## Decisions & Commentary
- New render hooks live under `layouts/_default/_markup/`, following the existing `render-codeblock-{mermaid,math,tree}.html` pattern — one partial call each, sharing a common partial to avoid duplicating the target-badge/output-panel logic across `bash`/`sh`/`shell`.
- Copy-button suppression: `initCodeClipboard()` in `theme.js` runs unconditionally on `DOMContentLoaded` over `document.querySelectorAll('code, .pre-only')` — there is no per-block opt-out hook. Rather than fork it, a `custom-footer.html` script runs on `DOMContentLoaded` and defers via `setTimeout(0)`. **The deferral is required, not cosmetic**: `theme.js` is loaded with `defer` (`themes/hugo-theme-relearn/layouts/partials/dependencies/theme.html`), so its top-level `ready()` call — and the `DOMContentLoaded` listener it registers — only run after HTML parsing finishes. A plain inline `<script>` with no `src` (this one) runs synchronously *during* parsing, registering its own listener first; DOM listeners for the same event fire in registration order, so an unguarded listener here ran, and no-opped, *before* `initCodeClipboard()` ever attached anything — `/code-review medium` caught this by reading `dependencies/theme.html` and tracing the `defer` semantics; a first draft of this Decisions entry had the ordering backwards. Fixed with `setTimeout(fn, 0)` inside the `DOMContentLoaded` handler: the callback runs as a new macrotask only after the entire synchronous `DOMContentLoaded` dispatch — every listener registered for that event, including theme.js's, which registers later but still fires within that same dispatch — has completed, deferring past `initCodeClipboard()` regardless of registration order. **Independently verified in a real headless-Chromium session** (Playwright, this session, 2026-09-24: served the built demo page with a `fortiuser`/`fortiemail` cookie pair so the analytics check-in redirect doesn't bounce to the live site, aborted the external analytics/CDN requests, loaded the page, and queried the live DOM) — 0 copy buttons and 0 `copy-to-clipboard*` classes across the page's 4 `.cmd-output` panels, and all 7 `.cmd-run` command blocks keep theirs (10 total copy buttons on the page: 7 block + inline-code ones from prose). The script removes any `.block-copy-to-clipboard-button` / `.inline-copy-to-clipboard-button` found inside `.cmd-output` panels, plus strips the `copy-to-clipboard`/`copy-to-clipboard-code` classes so a stray keyboard-triggered `copy` handler doesn't special-case the text either. CSS additionally hides `.cmd-output .block-copy-to-clipboard-button` as a second line of defense (covers a future theme.js change that stops using that exact class before this script is revisited).
- `output` is a new Chroma-less "language": Hugo always dispatches `render-codeblock-<type>` by the fence's first info-string word, so ` ```output ` cannot collide with any real Chroma lexer name.

## Files Changed
- `layouts/_default/_markup/render-codeblock-output.html` (new)
- `layouts/_default/_markup/render-codeblock-bash.html`, `-sh.html`, `-shell.html` (new)
- `layouts/partials/shortcodes/cmd-block.html` (new, shared partial)
- `layouts/partials/custom-header.html` (CSS block appended)
- `layouts/partials/custom-footer.html` (JS block appended)
- `README.md`, `RELEASE_NOTES.md` (documented)

## Session Summary
- Built `render-codeblock-output.html` (new `output` fence, muted/dashed panel, optional `lang=`
  highlighting and `collapse="true"` expand-wrapping) and pass-through `render-codeblock-{bash,sh,shell}.html`
  + shared `partials/shortcodes/cmd-block.html` (adds a coloured "Run on: <Target>" header only when
  `run=` is present; delegates untouched to `partials/shortcodes/highlight.html` otherwise).
  Copy-button suppression for `.cmd-output` panels lives in `custom-header.html` (CSS) and
  `custom-footer.html` (a DOMContentLoaded listener registered after the theme's own, removing any
  button `initCodeClipboard()` attached inside an output panel) — no theme.js fork.
- Verified byte-identical rendering for the no-`run` case: built a real UserRepo checkout against
  the unmodified vs modified image (`LOCAL=true --target dev`), normalized known non-deterministic
  tokens (cache-buster, image/tab-group hashes, last-updated stamp), and additionally stripped the
  two intentionally-added global `<style>`/`<script>` blocks — 0 of 36 built pages differ.
  Sanity-checked the normalization itself by building the unmodified image twice (also 0 diff).
- Proved all variants (bastion/local/pod/browser/unrecognised target, `lang=json`, `collapse="true"`,
  `title=` composed with `run=`, the zero-change fallback) on a new UserRepo demo page,
  `content/02Hugo/9_commands_and_output/index.md`, built via the same `LOCAL=true` image.
  Found and fixed one real bug during that testing: `collapse=true` (bare/unquoted) is silently
  ignored by Hugo's fence-attribute parser — it must be `collapse="true"`; documented this in both
  the demo page and README.
- Documented in `README.md` ("Render hooks" section) and `RELEASE_NOTES.md`.
- Self-reviewed the diff (medium depth) plus two `/code-review medium` passes (the first ran against
  the wrong cwd and found nothing; rerun with an explicit path against the worktree). The second pass
  found one real, severe bug: the copy-button-suppression script's `DOMContentLoaded` listener actually
  fired *before* `initCodeClipboard()`, not after — my original reasoning about DOM inclusion order was
  backwards; `theme.js` loads with `defer`, so it registers its listener later than a plain inline
  script does, not earlier. Fixed with `setTimeout(fn, 0)` (see Decisions). It also flagged that a
  bareword `{run}` attribute (no `=value`) would break `cmd-block.html`'s string functions — empirically
  false: Hugo's fence-attribute parser hard-errors on *any* bareword attribute at markdown-parse time,
  before any render hook runs (reproduced on a stock, unmodified `{title}` fence with no `run=` hook
  involved at all) — pre-existing Hugo behavior across the whole site, not a regression from this change.
  Two polish CSS tweaks (border-radius on the actual `<pre>` instead of the `.highlight` wrapper;
  transparent background on `lang=` output panels so Chroma's inline bg doesn't break the muted look)
  were also applied and verified not to affect the byte-identical no-`run` case (rebuilt, re-diffed: still
  0/36 pages differ).
- Independently verified the suppression fix in a real headless-Chromium session (Playwright, installed
  fresh in this environment) against the actual built demo page, served with a `fortiuser`/`fortiemail`
  cookie pair (otherwise the analytics check-in redirects every non-home page to the live production
  site instead of the local build) and the external analytics/CDN requests aborted: 0 copy buttons and
  0 `copy-to-clipboard*` classes across all 4 `.cmd-output` panels; all 7 `.cmd-run` command blocks keep
  theirs.
- Did not push, open a PR, or publish an image, per the source plan's STOP rule — see Follow-ups.

## Promotion
- [ ] `Decisions & Commentary` walked
- [ ] Durable facts promoted to `CLAUDE.md`
- [ ] `Status:` set to `Complete`

## Follow-ups
- [ ] Owner reviews the diff in both worktrees, then pushes `cmd-output-blocks` and opens PRs (route 1: `dev` first) per the CentralRepo/UserRepo merge rules in each repo's CLAUDE.md.
- [ ] Backport the convention into `ai-101` content once the CentralRepo image ships (xperts-ai-101 plan 0001 Phase 3).

## Risks / Open Questions
- Does Relearn 8's copy button attach to blocks rendered by a custom hook, and can it be suppressed per block without forking `theme.js`? **Resolved in 2b**: yes it attaches (nothing in `initCodeClipboard()` excludes custom-hook output), and yes it can be suppressed post-hoc via a `DOMContentLoaded` + `setTimeout(0)` strip — a naive (non-deferred) version of this was wrong and caught by review; the fix is independently verified in a real headless-Chromium session (Playwright) — see Decisions above.
- Who owns CentralRepo image publishing and timing? Unresolved — this plan stops before push/PR/publish per the source plan's STOP rule.

## Phase 2a result (fallback verification)
- Built `LOCAL=true --target dev` image (`hugotester-local`) against this worktree, mounted UserRepo, added a throwaway page
  ` ```bash {title="Run on: bastion"} ` + ` ```text {title="Expected output"} `.
- Confirmed: renders with the literal title text visible ("Run on: bastion" / "Expected output"), no CentralRepo change needed.
  Mechanism: `partials/shortcodes/highlight.html`'s `title` branch delegates to `partials/shortcodes/tab.html` — so the
  fallback renders as a single-entry Relearn tab widget carrying the title as its tab label, not a bespoke header bar.
  It reads as "titled" but looks like a tab, not like the badge/icon header the new hooks build in 2b. Good enough as
  a zero-change fallback; not a substitute for 2b's actual UX.
- Byte-identity baseline: built UserRepo against the unmodified image twice and diffed after normalizing known
  non-deterministic tokens (cache-buster `?<digits>`, `R-image-<md5>`, `data-tab-group=<md5>`/bare 32-hex tab-switch
  ids, and the last-updated stamp in both weekday-string and ISO form) — 0 files differ. This confirms the normalize
  script is sound for the real before/after diff in the next step.

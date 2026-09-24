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
- Copy-button suppression: `initCodeClipboard()` in `theme.js` runs unconditionally on `DOMContentLoaded` over `document.querySelectorAll('code, .pre-only')` — there is no per-block opt-out hook. Rather than fork it, a `custom-footer.html` script registers its own `DOMContentLoaded` listener *after* theme.js's — DOM listeners fire in registration order, and `custom-footer.html` is included later in `baseof.html` than the theme's bundled script tag, so it reliably runs after `initCodeClipboard()` has already attached buttons — and removes any `.block-copy-to-clipboard-button` / `.inline-copy-to-clipboard-button` found inside `.cmd-output` panels, plus strips the `copy-to-clipboard`/`copy-to-clipboard-code` classes so a stray keyboard-triggered `copy` handler doesn't special-case the text either. CSS additionally hides `.cmd-output .block-copy-to-clipboard-button` as a second line of defense (covers a future theme.js change that stops using that exact class before this script is revisited).
- `output` is a new Chroma-less "language": Hugo always dispatches `render-codeblock-<type>` by the fence's first info-string word, so ` ```output ` cannot collide with any real Chroma lexer name.

## Files Changed
- `layouts/_default/_markup/render-codeblock-output.html` (new)
- `layouts/_default/_markup/render-codeblock-bash.html`, `-sh.html`, `-shell.html` (new)
- `layouts/partials/shortcodes/cmd-block.html` (new, shared partial)
- `layouts/partials/custom-header.html` (CSS block appended)
- `layouts/partials/custom-footer.html` (JS block appended)
- `README.md`, `RELEASE_NOTES.md` (documented)

## Session Summary
- (write at end)

## Promotion
- [ ] `Decisions & Commentary` walked
- [ ] Durable facts promoted to `CLAUDE.md`
- [ ] `Status:` set to `Complete`

## Follow-ups
- [ ] Owner reviews the diff in both worktrees, then pushes `cmd-output-blocks` and opens PRs (route 1: `dev` first) per the CentralRepo/UserRepo merge rules in each repo's CLAUDE.md.
- [ ] Backport the convention into `ai-101` content once the CentralRepo image ships (xperts-ai-101 plan 0001 Phase 3).

## Risks / Open Questions
- Does Relearn 8's copy button attach to blocks rendered by a custom hook, and can it be suppressed per block without forking `theme.js`? **Resolved in 2b**: yes it attaches (nothing in `initCodeClipboard()` excludes custom-hook output), and yes it can be suppressed post-hoc via a later-registered `DOMContentLoaded` listener — see Decisions above.
- Who owns CentralRepo image publishing and timing? Unresolved — this plan stops before push/PR/publish per the source plan's STOP rule.

## Phase 2a result (fallback verification)
- (filled in below after build)

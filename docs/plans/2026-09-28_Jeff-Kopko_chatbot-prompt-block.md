# Plan: `chatbot` run target + author-editable label/icon/color

Date: 2026-09-28
Owner: Jeff Kopko
Slug: chatbot-prompt-block
Status: Complete
Supersedes: none
Superseded-By: none
Plan File: docs/plans/2026-09-28_Jeff-Kopko_chatbot-prompt-block.md
Log File: none

## Goal
- xperts-ai-101's chat-UI prompt instructions ("enter this into the chatbot") used three
  inconsistent styles (`> \`prompt\``, a plain `text` fence, `bash {run="Lab Agent"}` — the last
  falls back to the neutral "other" badge since `Lab Agent` isn't a known target). Give them the
  same visual treatment as the existing `run=` command blocks (`bastion`/`local`/`pod`/`browser`,
  see `docs/plans/2026-09-24_Jeff-Kopko_cmd-output-blocks.md`): a coloured header badge above a
  copyable block.
- Requested specifically: an orange header reading "Ask the chatbot" with the FortiAI-Assist mark
  as its icon (`xperts-ai-101/plans/FortiAI-Assist.svg`), reusable across every chat-prompt
  instance, and author-editable (text/icon/color) rather than hardcoded.

## Context / Links
- Source request: xperts-ai-101 session, 2026-09-28 — style chat-agent prompt instructions to
  match the bastion-box convention, using `FortiAI-Assist.svg`, orange "Ask the chatbot" header,
  reusable + author-editable, and available as a standard choice.
- Prior art: `docs/plans/2026-09-24_Jeff-Kopko_cmd-output-blocks.md` (the `run=` badge system this
  extends), `README.md` → "Render hooks".
- Worktree: `/home/ubuntu/pythonProjects/worktrees/CentralRepo-chatbot-prompt-block`, branch
  `chatbot-prompt-block` off `origin/dev`.
- Companion UserRepo change: `xperts-ai-101` branch `jkopkoEdits`, `content/03Agents/1_lab`,
  `content/04MCP/1_lab`, `content/05Security/1_lab` — switches chat-UI prompts to
  `` ```text {run="chatbot"} ``.

## Constraints / Assumptions
- Extend the existing `cmd-block.html` partial rather than adding a parallel system — the CSS
  class scheme (`cmd-target-<name>`), pass-through-when-`run`-absent guarantee, and copy button
  behavior must stay identical for `bastion`/`local`/`pod`/`browser`.
- A chatbot prompt isn't a shell command, so it needs a fence type that doesn't imply one — add
  `run=` support to `text` fences rather than repurposing `bash`/`sh`/`shell`.
- Per the owner's explicit ask, the label/icon/color must be a *reusable, author-editable*
  mechanism, not a one-off hardcoded "chatbot" branch — implemented as attribute overrides on any
  `run=` block, any target, with `chatbot` as one built-in standard target using those same
  defaults.
- STOP before `git push`, PR, or image publish — pushing `dev` rebuilds the shared dev image
  consumed by every FortinetCloudCSE workshop repo; owner approves that separately (same rule as
  the source plan this extends).

## Plan
- [x] Confirm the current `cmd-block.html`/`custom-header.html` implementation (this local
      checkout was 13 commits behind `origin/dev`; fast-forwarded first).
- [x] Copy `FortiAI-Assist.svg` into `static/images/fortiai-assist.svg`.
- [x] Extend `cmd-block.html`: add `chatbot` to the known-targets list with default label
      "Ask the chatbot" and default icon `fortiai`; add `label`/`icon`/`color` attribute
      overrides usable on any target.
- [x] Add `render-codeblock-text.html` (byte-identical pass-through when `run` absent, same as
      `bash`/`sh`/`shell`).
- [x] Add `.cmd-target-chatbot` CSS (`#e07b1a`) and `.cmd-run-icon-img` sizing to
      `custom-header.html`.
- [x] Build-verify via `LOCAL=true --target dev` against a real UserRepo (xperts-ai-101):
      existing `bastion` badge unchanged, new `chatbot` badge renders correctly on all 6 chat
      prompts across 3 lab pages, `label`/`icon`/`color` overrides verified independently.
- [x] Update xperts-ai-101's `03Agents/1_lab`, `04MCP/1_lab`, `05Security/1_lab` to use
      `` ```text {run="chatbot"} ``, replacing the three inconsistent prior styles.
- [x] Document in `README.md` (targets table + override syntax) and `RELEASE_NOTES.md`.
- [x] `/code-review medium` on the diff; fix what's real.
- [x] Close-out: promote decisions to CLAUDE.md, Status confirmation.

## Plan Changes
- (none)

## Decisions & Commentary
- Chose attribute overrides (`label=`/`icon=`/`color=`) over a second shortcode or a JSON config
  file: it composes with the existing `run=` fence convention authors already use, needs no new
  authoring syntax to learn for the common case (`run="chatbot"` alone gives the full standard
  look), and the override path costs nothing when unused (each is read with Go template `with`,
  a no-op when absent).
- `icon="fortiai"` renders an `<img>` pointing at a static SVG rather than inlining the SVG markup
  in the template. Inlining would let CSS recolor it via `currentColor`, but the FortiAI mark is
  two-tone (teal/white) — recoloring would lose the brand identity being asked for. An `<img>` is
  also simpler to keep pass-through-safe: no risk of the raw SVG's own `<defs>`/class names
  colliding with another inlined instance on the same page (multiple `run="chatbot"` blocks per
  page is the common case here).
- `text` needed its own `render-codeblock-text.html` — Hugo dispatches by the fence's first
  info-string word, and `text` had no existing render hook to piggyback on (unlike `bash`/`sh`/
  `shell`, which already delegate through `highlight.html`).
- `/code-review medium` caught a real escaping gap: the `icon`/`color` override values were
  interpolated into `<i class="...">`/`style="background:..."` and marked `safeHTML`/
  `safeHTMLAttr` with no escaping — bypassing Go `html/template`'s normal auto-escaping, unlike
  `label` (output via plain `{{ $label }}`, which *is* auto-escaped) and unlike the sibling
  `render-codeblock-output.html`, which already runs comparable author-controlled content through
  `transform.HTMLEscape` before its own `safeHTML` sink. Fixed by running both through
  `transform.HTMLEscape` before interpolation, matching that existing convention. Re-verified
  after the fix: the `chatbot` target and the `label`/`icon`/`color` override test both still
  render correctly.

## Files Changed
- `static/images/fortiai-assist.svg` (new, copied from xperts-ai-101 `plans/FortiAI-Assist.svg`)
- `layouts/_default/_markup/render-codeblock-text.html` (new)
- `layouts/partials/shortcodes/cmd-block.html` (extended: `chatbot` target, `label`/`icon`/`color`
  overrides)
- `layouts/partials/custom-header.html` (CSS: `.cmd-target-chatbot`, `.cmd-run-icon-img`)
- `README.md`, `RELEASE_NOTES.md` (documented)
- xperts-ai-101: `content/03Agents/1_lab/index.md`, `content/04MCP/1_lab/index.md`,
  `content/05Security/1_lab/index.md` (adopt `run="chatbot"`)

## Session Summary
- Local `CentralRepo` checkout was 13 commits behind `origin/dev` (missing the `run=`/`output`
  render hooks entirely) — fast-forwarded before starting, and initialized the
  `themes/hugo-theme-relearn` submodule in the new worktree (uninitialized by default with
  `git worktree add`, which breaks `LOCAL=true` builds with an opaque
  `unknown output format "print" for kind "home"` error — the theme's own config, including
  `outputFormats`, wasn't present).
- Built and verified against real xperts-ai-101 content via `LOCAL=true --target dev`
  (`docker build --build-arg LOCAL=true --target dev`, then mounting the UserRepo checkout):
  the pre-existing `cmd-target-bastion` badge rendered unchanged, all 6 `run="chatbot"` blocks
  (3 in `03Agents/1_lab`, 2 in `05Security/1_lab`, 1 in `04MCP/1_lab`) rendered the orange header,
  FortiAI-Assist icon and "Ask the chatbot" text, and a scratch override test
  (`label="Ask FortiAI-Assist" icon="fas fa-robot" color="#7a3fc4"`) confirmed all three
  attributes take effect independently.
- Did not push, open a PR, or publish an image, per the STOP rule — see Follow-ups.

## Promotion
- [x] `Decisions & Commentary` walked
- [x] Durable facts promoted to `CLAUDE.md`
- [x] `Status:` confirmed

## Follow-ups
- [ ] Owner reviews the diff in both worktrees (CentralRepo `chatbot-prompt-block`,
      xperts-ai-101 `jkopkoEdits`), then pushes and opens PRs per each repo's CLAUDE.md
      (CentralRepo: dev-first route; xperts-ai-101: push `jkopkoEdits`, wait for
      `ci/jenkins/build-status`, `gh-merge-verify ... --method squash`).
- [ ] After the CentralRepo image ships, confirm the live xperts-ai-101 site renders the
      `chatbot` badge (same "stale `:latest`" caveat as the source plan).

## Risks / Open Questions
- The FortiAI-Assist mark's teal (`#2cccd3`) sits on a `#e07b1a` orange background — contrast is
  adequate in the local build's screenshots but wasn't checked against a formal contrast ratio
  tool; flag if design review wants a different orange.
- Who owns CentralRepo image publishing and timing? Same as the source plan — unresolved here
  too, stopping before push/PR/publish.

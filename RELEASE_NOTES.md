# CentralRepo Release Notes

---

## [Unreleased]

### CloudCSEMovie Theme — MP4 Video Sidebar Header

Added a new Hugo theme variant `CloudCSEMovie` that plays an MP4 video in the sidebar header area in place of a static background image.

**Features**
- Video plays automatically on page load (muted, no controls)
- Configurable loop interval: video plays once, pauses, then replays. A 6-second clip with a 60-second interval plays once, waits 54 seconds, then plays again
- Search bar repositioned below the video and the red divider line, sitting on the dark nav background
- All other header content (logo, banner text) renders on top of the video
- Falls back to a solid color header if `videoHeaderSrc` is left empty

**Configuration** — set in each repo's `scripts/repoConfig.json`:
```json
{
  "themeVariant": "CloudCSEMovie",
  "videoHeaderSrc": "/videos/CloudsAnimated.mp4",
  "videoHeaderInterval": 60
}
```
- `videoHeaderSrc`: URL path relative to site root (no leading `/` needed — generated automatically). Leave blank to disable video.
- `videoHeaderInterval`: Total seconds between play cycles. Optional; defaults to `60`.

**Video asset** — shared MP4 lives in `static/videos/` of CentralRepo (the Hugo root for all repo builds), so one file is available to every repo.

**Files changed**
| File | Change |
|------|--------|
| `assets/css/theme-CloudCSEMovie.css` | New theme CSS — video positioning, search bar below divider |
| `static/css/theme-CloudCSEMovie.css` | Static copy served directly by Hugo (bypasses asset pipeline) |
| `layouts/partials/custom-header.html` | Conditional `<video>` injection via JS data-attribute pattern |
| `scripts/templates/hugo.jinja` | `videoHeaderSrc` / `videoHeaderInterval` params in generated `hugo.toml` |
| `scripts/repoConfig.json` | New params with defaults; CentralRepo set to CloudCSEMovie theme |
| `static/videos/CloudsAnimated.mp4` | Shared video asset |
| `README.md` | Theme variants table + CloudCSEMovie setup documentation |

**Technical notes**
- Hugo's `html/template` JS-context escaping causes double-encoding of string params inside `<script>` blocks. Fixed by passing the video path via an HTML `data-` attribute and reading it with `getAttribute()` in JS.
- Hugo's `relURL` only prepends the site base path for paths without a leading slash. Fixed with `strings.TrimPrefix "/" . | relURL` to produce the correct `/UserRepo/videos/...` path.
- Theme CSS must exist in `static/css/` to be served at `css/theme-*.css` as the relearn theme stylesheet partial expects.

### Repository hygiene

- Added `hugo.toml`, `CLAUDE.md`, and local draw.io diagram exports to `.gitignore`. `hugo.toml` is auto-generated at container startup; these files should never be committed.

# CentralRepo – Shared Hugo Partials and Shortcodes

This repository provides shared Hugo partials and shortcodes used across Fortinet CSE workshop sites. It centralizes cross-site check-in, analytics, and UX helpers so multiple sites can stay consistent.

## How the core partials work together

The page wrapper partial `layouts/partials/content.html` wires the experience:

- On the home page (`.Kind == "home"`): includes `analytics_checkin.html` to render the required check-in form.
- On all other pages: includes `google_analytics.html` to enforce a prior check-in and configure GA user_id.
- After the content (`.Content`): always includes `silent_cross_site_checkin.html` to silently propagate attendance across sites.

### analytics_checkin.html (home page)
Purpose: Collect user email (and optional Customer/Event) and perform the explicit check-in to the TEC Analytics API.

Key behaviors:
- Validates email and posts to `POST https://tecanalytics.forticloudcse.com/checkin` (legacy redirecting endpoint).
- Sets/refreshes cookies for 5 days (rolling window):
  - `fortiuser` (UUID session)
  - `fortiemail`
  - `forticustomer` (optional)
  - `fortievent` (optional)
  - `fortisites` (pipe-delimited list of lowercase site ids visited)
- Stores a localStorage profile (`forti_profile`) to assist prefills and resilience.
- Seeds `fortisites` with the current site id (normalized to lowercase) and dedupes existing entries.
- Dispatches `window` event `forti:checkin` with `{ uuid }` so GA can update `user_id` live.

### google_analytics.html (all non-home pages)
Purpose: Ensure a valid check-in exists before proceeding and configure GA user_id.

Key behaviors:
- If `fortiuser` cookie is missing, redirects to the home page to enforce check-in.
- Initializes GA and sets `user_id` to the cookie value. If `forti:checkin` occurs later, it updates `user_id` dynamically.

### silent_cross_site_checkin.html (all pages)
Purpose: Silently perform a background check-in when a previously checked-in user visits a new workshop site.

Key behaviors:
- Requires `fortiuser` and an `EMail` (from `fortiemail` cookie or `forti_profile`).
- Determines the site id from `.Site.Params.repoName` or the first URL path segment; normalizes to lowercase.
- Maintains the `fortisites` cookie (always lowercase, deduped). If current site is new, performs:
  - `fetch` POST to `/checkin/silent` with a small retry (2 attempts, 200ms and then 600ms delays)
  - Fallback to `navigator.sendBeacon`
  - Final fallback to hidden form `POST /checkin`
- On success or when refreshing an existing site, extends the 5-day TTL for: `fortiuser`, `fortiemail`, `forticustomer` (if set), `fortievent` (if set), and `fortisites`.

## Supporting partials

- `prefill-useremail.html`: exposes helpers and pre-fills common email fields and UUID in other forms based on cookies and `forti_profile`.
- `content-header.html`, `content-footer.html`, `menu-footer.html`, `custom-header.html`, `favicon.html`, etc.: site chrome helpers untouched by the check-in logic.

## Shortcodes and usage

### launchdemoform
Provision lab accounts via an automation webhook with built-in UX and cookie/profile integration.

Usage:
```
{{< launchdemoform lab="My-Lab-Definition" >}}
```
Parameters:
- `lab` or `labdefinition`: Required lab definition sent as `odlconfigname`.
- `debug`: Optional `true|false` to show console diagnostics.

Behavior:
- Reads `fortiuser` and `fortiemail` (or local profile) to populate request.
- Disables action until both are present; provides inline status updates.

### figure
Responsive image with optional zoom source and caption.

Usage:
```
{{< figure src="images/diagram.png" alt="Architecture" caption="Architecture" >}}
```
Optional params:
- `title` (fallback for caption)
- `class` (wrapper class)
- `imgclass` (img class)
- `zoomsrc` (hi-res image path)

### quizframe
Embeds a CTF/quiz iframe and appends cookies for context.

Usage (preferred via site params):
```
{{< quizframe page="/take-quiz" >}}
```
Site params:
- `quizUrl`: Base quiz host (e.g., https://quiz.example.com)
- The shortcode ensures HTTPS and appends `fortiemail`, `fortiuser`, and `workshopID` as query params when present.

Direct src override:
```
{{< quizframe src="https://quiz.example.com/take-quiz" >}}
```

### colortext
Inline colored text.

Usage:
```
{{< colortext "#f00" >}}Important{{< /colortext >}}
```

### Xperts banners
Include themed banners via partial-backed shortcodes.

Usage:
```
{{< Xperts24Banner line1="Line A" line2="Line B" line3="Line C" >}}
{{< Xperts25Banner line1="Line A" line2="Line B" line3="Line C" >}}
```

## Theme variants

Set `themeVariant` in `scripts/repoConfig.json` to control the sidebar header appearance. Available values:

| Variant | Header style |
|---------|-------------|
| `Workshop` | Standard Fortinet red |
| `Demo` | Demo-branded |
| `UseCase` | Use-case-branded |
| `Spotlight` | Spotlight-branded |
| `FortinetSilver` | Silver color scheme |
| `FortinetTeal` | Teal color scheme |
| `Xperts2024` | Xperts 2024 static background image |
| `Xperts2025` | Xperts 2025 static background image |
| `CloudCSEMovie` | MP4 video background in the sidebar header area |

### CloudCSEMovie — video header background

The `CloudCSEMovie` variant replaces the static header image with a looping MP4 video. The video plays automatically (muted) on page load. When it ends, it pauses and replays on a configurable interval — for example, a 6-second clip with a 60-second interval plays once, waits 54 seconds, then plays again. All other header content (logo, banner text, search bar) renders on top of the video.

**Setup:**

1. Place the MP4 in `static/videos/` inside CentralRepo (this is the Hugo root for all repo builds, so one file is available to every repo):
   ```
   static/videos/your-video.mp4
   ```

2. Configure `scripts/repoConfig.json`:
   ```json
   {
     "themeVariant": "CloudCSEMovie",
     "videoHeaderSrc": "/videos/your-video.mp4",
     "videoHeaderInterval": 60
   }
   ```
   - `videoHeaderSrc` — URL path relative to site root. Hugo strips the `static/` prefix — do **not** include it in the path.
   - `videoHeaderInterval` — total seconds between the start of each play cycle. Optional; defaults to `60`. Must be greater than the video's duration.

3. Leave `videoHeaderSrc` as `""` to use the `CloudCSEMovie` CSS without a video (renders a solid color header like other themes).

## Site params referenced
- `repoName`: Used to derive the normalized site id (lowercase) for `fortisites` and payload.
- `workshopTitle`: Human-readable title sent with check-ins.
- `marketingCode`: Optional event code sent with check-ins.
- `cookieDomain`: Optional cookie domain override for broader cookie scope.
- `quizUrl`: Base URL for `quizframe`.
- `videoHeaderSrc`: Path to the sidebar header background MP4 (`CloudCSEMovie` theme only).
- `videoHeaderInterval`: Seconds between video play cycles (`CloudCSEMovie` theme only, default `60`).

## Cookie overview
- `fortiuser`: UUID session (5-day rolling TTL).
- `fortiemail`: User email (5-day rolling TTL).
- `forticustomer`: Optional customer string (5-day rolling TTL).
- `fortievent`: Optional event/marketing code (5-day rolling TTL).
- `fortisites`: Pipe-delimited lowercase list of visited site ids (5-day rolling TTL).
- `forti_profile` (localStorage): JSON `{ email, customer, event, workshopID }` used for prefills and recovery.

## Notes & gotchas
- CORS: `/checkin/silent` is CORS-protected. In development, configure the API to allow your dev origin via `CORS_ORIGINS` or `CORS_ALLOW_ALL_DEV=1`.
- Normalization: `fortisites` is always written in lowercase and deduplicated.
- Fallbacks: silent check-in uses fetch → sendBeacon → hidden form to maximize delivery.

## Testing

Tests live in `scripts/test/`. CI runs automatically on push to `prreviewJune23` and on PRs to `main`.

**Run locally:**
```bash
bash scripts/test/run_tests.sh
```

**Activate pre-push hook** (run once after cloning):
```bash
git config core.hooksPath .githooks
```

| Layer | Tool | What it catches |
|-------|------|----------------|
| Hugo build | `hugomods/hugo:std` in CI | Template errors, deprecations, broken partials |
| HTML assertions | `test_rendered_html.sh` | Form action URLs, CSS paths, forbidden iframe attrs |
| Regex validation | `validate_regex.js` | Chrome v-flag incompatible `pattern=""` values |
| Config schema | `validate_config.py` | Missing required fields, invalid themeVariant |

See `.github/workflows/ci.yml` for the full CI pipeline.

## Contributing
- Update partials conservatively—they are shared by many sites.
- Keep README examples accurate; include parameter defaults and any site param dependencies.

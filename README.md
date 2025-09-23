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

### quizdown
Wraps content for a quizdown block.

Usage:
```
{{< quizdown >}}
... quiz content ...
{{< /quizdown >}}
```

### colortext
Inline colored text.

Usage:
```
{{< colortext "#f00" >}}Important{{< /colortext >}}
```

### carousel
Renders a simple image carousel from a page parameter array.

Usage:
1. In your page front matter, define an array:
```
carousel:
  - image: "/images/step1.png"
    caption: "Step 1"
  - image: "/images/step2.png"
    caption: "Step 2"
```
2. In content:
```
{{< carousel name="carousel" >}}
```

### Xperts banners
Include themed banners via partial-backed shortcodes.

Usage:
```
{{< Xperts24Banner line1="Line A" line2="Line B" line3="Line C" >}}
{{< Xperts25Banner line1="Line A" line2="Line B" line3="Line C" >}}
```

## Site params referenced
- `repoName`: Used to derive the normalized site id (lowercase) for `fortisites` and payload.
- `workshopTitle`: Human-readable title sent with check-ins.
- `marketingCode`: Optional event code sent with check-ins.
- `cookieDomain`: Optional cookie domain override for broader cookie scope.
- `quizUrl`: Base URL for `quizframe`.

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

## Contributing
- Update partials conservatively—they are shared by many sites.
- Keep README examples accurate; include parameter defaults and any site param dependencies.

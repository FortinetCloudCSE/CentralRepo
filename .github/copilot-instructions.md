# Copilot Instructions for CentralRepo

This repository provides shared Hugo partials, shortcodes, and themes for Fortinet CSE workshop sites. It's designed as a centralized resource that multiple workshop repositories can consume via Docker containers.

## Architecture & Key Concepts

### Dual-Repository Pattern
- **CentralRepo** (this repo): Contains shared Hugo components, themes, and build infrastructure
- **UserRepo** (workshop-specific): Contains workshop content that mounts to `/home/UserRepo` in Docker
- Build process generates Hugo config from `UserRepo/scripts/repoConfig.json` using Jinja2 templates

### Critical File Relationships
```
scripts/repoConfig.json → scripts/templates/hugo.jinja → hugo.toml (generated)
UserRepo content → CentralRepo layouts/shortcodes → Final Hugo site
```

### Analytics & Check-in System
The site enforces a three-stage user analytics flow via specialized partials:

1. **Home page**: `analytics_checkin.html` - Collects email, sets cookies (`fortiuser`, `fortiemail`, `fortisites`)
2. **All other pages**: `google_analytics.html` - Redirects to home if not checked in, configures GA user_id
3. **All pages**: `silent_cross_site_checkin.html` - Background cross-site propagation via TEC Analytics API

Cookie management is critical - all have 5-day rolling TTL and `fortisites` tracks visited workshops in lowercase pipe-delimited format.

## Development Workflows

### Local Development
```bash
# Generate Hugo config from repoConfig.json
./scripts/generate_toml.sh

# Author mode server (bypasses analytics check-in)
./scripts/hugoServer_authorMode.sh

# Production build
./scripts/hugo_build.sh  # Runs generate_toml.sh + hugo build
```

### Docker Workflows
```bash
# Build containers (prod uses main branch, dev uses current)
./scripts/docker_build.sh [prod|dev]

# Common container commands
./scripts/docker_run.sh build [prod|dev]     # Build site
./scripts/docker_run.sh server [prod|dev]   # Run dev server  
./scripts/docker_run.sh generate_toml [prod|dev]  # Config only
./scripts/docker_run.sh shell [prod|dev]    # Debug shell
```

## Shortcode Patterns

### launchdemoform
Lab provisioning with cookie integration:
```hugo
{{< launchdemoform lab="My-Lab-Definition" debug="true" >}}
```
- Requires `fortiuser`/`fortiemail` cookies from check-in
- Posts to automation webhook with `odlconfigname` parameter

### quizframe  
Embeds external quiz with automatic cookie propagation:
```hugo
{{< quizframe page="/take-quiz" >}}
```
- Uses `Site.Params.quizUrl` as base URL
- Auto-appends `fortiemail`, `fortiuser`, `workshopID` query params

### Theme-aware shortcodes
```hugo
{{< Xperts24Banner line1="Text" line2="Text" line3="Text" >}}
{{< Xperts25Banner line1="Text" line2="Text" line3="Text" >}}
```

## CSS Theme System

Theme variants in `assets/css/theme-*.css` override CSS custom properties:
- `theme-Xperts2025.css` - Current default with Fortinet red theming
- `theme-Demo.css`, `theme-Workshop.css` - Alternate color schemes
- Set via `themeVariant` in `repoConfig.json`

## Configuration Patterns

### repoConfig.json Structure
```json
{
  "repoName": "MyWorkshop",           // Used for site URLs and fortisites cookie
  "themeVariant": "Xperts2025",       // CSS theme selection
  "analyticsBaseUrl": "...",          // TEC Analytics API endpoint
  "quizUrl": "https://...",           // Base URL for quizframe shortcode  
  "shortcuts": [...]                  // Navigation menu items
}
```

### Site Parameter Dependencies
- `repoName` → Normalized lowercase for `fortisites` tracking
- `workshopTitle` → Page titles and check-in payloads  
- `marketingCode` → Optional event tracking
- `cookieDomain` → Cross-domain cookie scope

## Pipeline & Deployment

### AWS Infrastructure
```bash
# CloudFront + S3 setup
aws cloudformation create-stack --stack-name MY-Workshop \
  --template-body file://pipeline/webhosting/cloudfront-s3-website.yaml

# Build pipeline
aws cloudformation create-stack --stack-name MY-Website-Pipeline \
  --template-body file://pipeline/webhosting/pipeline.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

## Common Pitfalls

- **CORS Issues**: TEC Analytics `/checkin/silent` endpoint requires CORS configuration for dev origins
- **Case Sensitivity**: `fortisites` cookie is always lowercase; `repoName` gets normalized
- **Cookie Dependencies**: Many shortcodes fail silently without proper check-in cookies
- **Content Paths**: Hugo builds expect content in `/home/UserRepo/content` when using Docker
- **Theme Loading**: CSS themes must match exactly with `themeVariant` parameter (case-sensitive)

## Security & Compliance

- fdevsec.yaml configured for SAST, secret scanning, SCA, IaC, and container scanning
- Pipeline fails on risk rating ≥7
- All external API calls (analytics, provisioning) use HTTPS with retry fallbacks
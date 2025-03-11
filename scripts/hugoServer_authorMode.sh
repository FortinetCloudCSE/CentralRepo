#!/bin/sh

rm /home/CentralRepo/layouts/partials/google_analytics.html
mv /home/CentralRepo/layouts/partials/google_analytics_authorMode.html /home/CentralRepo/layouts/partials/google_analytics.html
./scripts/generate_toml.sh
hugo server --contentDir /home/UserRepo/content --bind=0.0.0.0
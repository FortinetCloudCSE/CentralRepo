#!/bin/sh

mv /home/CentralRepo/layouts/partials/google_analytics.html /home/CentralRepo/layouts/partials/author_mode_google_analytics.html
hugo server --contentDir /home/UserRepo/content --bind=0.0.0.0
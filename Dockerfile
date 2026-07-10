# syntax=docker/dockerfile:1

# Global ARG must be declared before first FROM to be usable in FROM instructions
ARG LOCAL=false

# Global ARG must be declared before first FROM to be usable in FROM instructions
ARG LOCAL=false

# Base Hugo image (uses Alpine 3.21)
FROM hugomods/hugo:std as base

############################
# DEV STAGE — source variants
# Use LOCAL=true to build from the local checkout instead of GitHub:
#   docker build --build-arg LOCAL=true --target dev -t hugotester-local .
############################

# Local source: populated from build context when LOCAL=true
FROM base as dev-src-local-true
COPY . /home/CentralRepo

# Remote source: fetched from GitHub for CI (default)
FROM base as dev-src-local-false
ADD https://github.com/FortinetCloudCSE/CentralRepo.git#prreviewJune23 /home/CentralRepo

############################
# DEV STAGE — unified entry point
############################
FROM dev-src-local-${LOCAL} as dev

# Build argument for version (optional for dev, defaults to "dev")
ARG CENTRALREPO_VERSION=dev

WORKDIR /home/CentralRepo

# Force install CA certs from HTTP and configure apk to use HTTP; due to sudden issues with HTTPS; temporary fix until it's working again
RUN apk --no-cache --allow-untrusted --repository http://dl-cdn.alpinelinux.org/alpine/v3.21/main \
    add ca-certificates && \
    update-ca-certificates && \
    sed -i 's|https://dl-cdn.alpinelinux.org|http://dl-cdn.alpinelinux.org|g' /etc/apk/repositories && \
    apk update && \
    apk add --no-cache python3 py3-pip tini-static && \
    ln -sf python3 /usr/bin/python && \
    ln -sf /sbin/tini-static /sbin/tini

# Inject version into menu-footer.html partial
RUN sed -i "s|{{- \\\$version := os.Getenv \"HUGO_VERSION_TAG\" -}}|{{- \\\$version := \"${CENTRALREPO_VERSION}\" -}}|" \
    /home/CentralRepo/layouts/partials/menu-footer.html

ENTRYPOINT ["/sbin/tini", "--", "/home/CentralRepo/scripts/local_copy.sh"]

############################
# PROD STAGE
############################
FROM base as prod

# Build argument for version (passed from GitHub workflow)
ARG CENTRALREPO_VERSION=unknown

# Add repo
ADD https://github.com/FortinetCloudCSE/CentralRepo.git#main /home/CentralRepo
WORKDIR /home/CentralRepo

# Force install CA certs from HTTP and configure apk to use HTTP; due to sudden issues with HTTPS; temporary fix until it's working again
RUN apk --no-cache --allow-untrusted --repository http://dl-cdn.alpinelinux.org/alpine/v3.21/main \
    add ca-certificates && \
    update-ca-certificates && \
    sed -i 's|https://dl-cdn.alpinelinux.org|http://dl-cdn.alpinelinux.org|g' /etc/apk/repositories && \
    apk update && \
    apk add --no-cache python3 py3-pip tini-static && \
    ln -sf python3 /usr/bin/python && \
    ln -sf /sbin/tini-static /sbin/tini

# Inject version into menu-footer.html partial
RUN sed -i "s|{{- \\\$version := os.Getenv \"HUGO_VERSION_TAG\" -}}|{{- \\\$version := \"${CENTRALREPO_VERSION}\" -}}|" \
    /home/CentralRepo/layouts/partials/menu-footer.html

ENTRYPOINT ["/sbin/tini", "--", "/home/CentralRepo/scripts/local_copy.sh"]

#!/bin/sh

cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes 2>/dev/null || true
cp ../UserRepo/layouts/partials/* layouts/partials 2>/dev/null || true
# Copy VERSION file from mounted workspace if present so Hugo can read it
cp -f ../UserRepo/VERSION . 2>/dev/null || true

echo "**** If you don't have custom layouts/VERSION, ignore any 'cp: can't stat' messages above ****"

case "$1" in
  "server")
    cmd="./scripts/hugoServer_authorMode.sh"
    ;;

  "shell")
    cmd="sh"
    ;;

  "generate_toml")
    cmd="./scripts/generate_toml.sh"
    ;;

  "update_scripts")
    cmd="./scripts/update_scripts.sh"
    ;;

  "upgrade_repo")
    cmd="./scripts/upgrade_repo.sh"
    ;;

  "update_fdevsec")
    cmd="./scripts/update_fdevsec.sh"
    ;;

  "build" | "")
    cmd="./scripts/hugo_build.sh"
    ;;

  *)
    cmd=""
    ;;
esac

$cmd

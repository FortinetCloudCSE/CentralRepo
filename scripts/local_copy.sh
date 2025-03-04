#!/bin/sh

cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes
cp ../UserRepo/layouts/partials/* layouts/partials

echo "**** IF YOU DON'T HAVE any custom layouts, DISREGARD MESSAGE: 'cp: can't stat '../UserRepo/layouts/partials/*': No such file or directory' ****"

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
    cmd="/scripts/upgrade_repo"
    ;;

  "update_fdevsec")
    cmd="./scripts/update_fdevsec.sh"
    ;;

  "build" | "")
    cmd="hugo --minify --cleanDestinationDir --contentDir /home/UserRepo/content"
    ;;

  *)
    cmd=""
    ;;
esac

$cmd

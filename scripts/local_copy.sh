#!/bin/sh

cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes
cp ../UserRepo/layouts/partials/* layouts/partials

echo "**** IF YOU DON'T HAVE any custom layouts, DISREGARD MESSAGE: 'cp: can't stat '../UserRepo/layouts/partials/*': No such file or directory' ****"

case "$1" in
  "server")
    cmd="hugo server --contentDir /home/UserRepo/content --bind=0.0.0.0"
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

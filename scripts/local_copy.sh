#!/bin/sh

cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes
cp ../UserRepo/layouts/partials/* layouts/partials
cp ../UserRepo/content content
cp ../UserRepo/hugo.toml hugo.toml

case "$1" in
  "server")
    cmd="hugo server --bind=0.0.0.0"
    ;;

  "shell")
    cmd="sh"
    ;;

  "generate_toml")
    cmd="python scripts/generate_toml.py"
    ;;

  "update_scripts")
    cmd="./scripts/update_scripts.sh"
    ;;

  "update_fdevsec")
    cmd="./scripts/update_fdevsec.sh"
    ;;

  "build" | "")
    cmd="hugo --minify --cleanDestinationDir"
    ;;

  *)
    cmd=""
    ;;
esac

$cmd

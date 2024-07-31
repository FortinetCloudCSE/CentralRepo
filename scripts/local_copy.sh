#!/bin/sh

cp ../UserRepo/layouts/shortcodes/* layouts/shortcodes
cp ../UserRepo/layouts/partials/* layouts/partials

case "$1" in
  "server")
    cmd="hugo server --bind=0.0.0.0"
    ;;

  "shell")
    cmd="sh"
    ;;

  "build" | "")
    cmd="hugo --minify --cleanDestinationDir"
    ;;

  *)
    cmd=""
    ;;
esac

$cmd

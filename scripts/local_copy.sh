#!/bin/bash

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

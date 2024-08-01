#!/bin/bash

myarray=( "build" "server" "shell" "generate_toml" "update_scripts" "update_fdevsec" " )

[[ "$#" > "1" ]] || [[ ! " ${myarray[*]} " =~ " $1 " ]] && echo "Usage: ./scripts/docker_run.sh [ build | server | generate_toml | update_scripts | update_fdevsec | shell ]" && exit 1

cmd="docker run --rm -it
  -v $(pwd):/home/UserRepo
  -p 1313:1313 hugotester:latest $1"
echo $cmd
$cmd
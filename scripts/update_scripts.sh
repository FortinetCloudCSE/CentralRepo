#!/bin/sh

cp scripts/docker_tester_run.sh ../UserRepo/scripts/docker_tester_run.sh
cp scripts/docker_run.sh ../UserRepo/scripts/docker_run.sh
cp scripts/static.yml ../UserRepo/.github/workflows/static.yml
cp Dockerfile ../UserRepo/Dockerfile

echo "updated docker_tester_run.sh, docker_run.sh, Github action, and Dockerfile"

echo "venv/" >> .gitignore

if ! test -f ../UserRepo/scripts/repoConfig.json; then
  cp scripts/repoConfig.json ../UserRepo/scripts/repoConfig.json
  echo "copied Hugo config file into ../UserRepo/scripts/repoConfig.json"
fi

if ! test -f ../UserRepo/hugo.toml; then
  touch hugo.toml
  echo "Created emtpy hugo.toml file to be able to run update_scripts"
fi
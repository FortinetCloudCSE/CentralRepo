#!/bin/sh

### After QA testing docker_run_latest and docker_build_latest.sh: rm docker_tester_run, docker_run, docker_tester_build, docker_build

## leave the wget (latest) scripts out b/c they have too much potential for compromise
#cp scripts/docker_run_latest.sh ../UserRepo/scripts/docker_run_latest.sh
#cp scripts/docker_build_latest.sh ../UserRepo/scripts/docker_build_latest.sh

#cp scripts/docker_tester_run.sh ../UserRepo/scripts/docker_tester_run.sh
#cp scripts/docker_tester_build.sh ../UserRepo/scripts/docker_tester_build.sh
cp scripts/docker_run.sh ../UserRepo/scripts/docker_run.sh
cp scripts/docker_build.sh ../UserRepo/scripts/docker_build.sh

cp scripts/static.yml ../UserRepo/.github/workflows/static.yml
cp Dockerfile ../UserRepo/Dockerfile

rm -f ../UserRepo/scripts/docker_tester_run.sh
rm -f ../UserRepo/scripts/docker_tester_build.sh
rm -f ../UserRepo/scripts/docker_run_latest.sh
rm -f ../UserRepo/scripts/docker_build_latest.sh
rm -f ../UserRepo/docker-compose.yml
rm -f ../UserRepo/hugo.toml
rm -f ../UserRepo/config.toml

echo "updated docker_tester_run.sh, docker_run.sh, docker_build.sh, Github action (static.yaml), and Dockerfile.  Removed old docker_ scripts and docker_compose.yml"

if ! test -f ../UserRepo/scripts/repoConfig.json; then
  cp scripts/repoConfig.json ../UserRepo/scripts/repoConfig.json
  echo "copied Hugo config file into ../UserRepo/scripts/repoConfig.json"
fi

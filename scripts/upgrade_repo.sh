#!/bin/sh

echo "Running update_scripts to get latest commands & baseline repoConfig.json file"
./scripts/update_scripts.sh

echo "Activating Python venv and installing Jinja2 and toml from pip"
python -m venv /home/CentralRepo/venv
. /home/CentralRepo/venv/bin/activate
pip install Jinja2
pip install toml

echo "Running toml_to_json.py which extracts key fields from old config.toml and stores them in repoConfig.json"
python scripts/toml_to_json.py


echo "Running generate_toml.py which uses Jinja2 template to generate new TOML file from repoConfig.json"
python scripts/generate_toml.py

deactivate
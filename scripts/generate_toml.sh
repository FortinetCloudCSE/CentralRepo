#!/bin/sh

echo "Activating Python venv and installing Jinja2 from pip"
python -m venv /home/CentralRepo/venv
. /home/CentralRepo/venv/bin/activate
pip install Jinja2

echo "Running generate_toml.py which uses Jinja2 template to generate new TOML file from repoConfig.json"
python scripts/generate_toml.py

deactivate
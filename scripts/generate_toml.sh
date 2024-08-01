#!/bin/sh

python -m venv /home/UserRepo/venv
. /home/UserRepo/venv/bin/activate
pip install Jinja2

python scripts/generate_toml.py

deactivate
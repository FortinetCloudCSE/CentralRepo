#!/bin/sh

apk add --no-cache python3 py3-pip

py3-pip install Jinja2

python scripts/generate_toml.py
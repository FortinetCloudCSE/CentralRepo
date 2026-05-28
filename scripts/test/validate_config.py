#!/usr/bin/env python3
import sys
import json
import jsonschema
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
SCHEMA_FILE = REPO_ROOT / 'scripts' / 'repoConfig.schema.json'

def validate(config_path: pathlib.Path, schema: dict):
    config = json.loads(config_path.read_text())
    try:
        jsonschema.validate(instance=config, schema=schema)
        print(f"PASS: {config_path}")
    except jsonschema.ValidationError as e:
        print(f"FAIL: {config_path} — {e.message}", file=sys.stderr)
        sys.exit(1)

schema = json.loads(SCHEMA_FILE.read_text())

configs_to_validate = [
    REPO_ROOT / 'scripts' / 'repoConfig.json',
    REPO_ROOT / 'scripts' / 'test' / 'fixtures' / 'no_analytics_url.json',
]

for cfg in configs_to_validate:
    validate(cfg, schema)

print("\nAll configs valid")

#!/usr/bin/env python3
"""Validate repoConfig files against scripts/repoConfig.schema.json.

Usage: validate_config.py [config.json ...]
With no arguments, validates the repo's own config and the bundled fixture.

When GITHUB_REPOSITORY is set (as in GitHub Actions), also asserts that
repoName matches the repository name (case-insensitive). This catches a
workshop repo that still carries the template repoName ("UserRepo"); the
template repos themselves pass because their repoName equals their own name.
"""
import sys
import os
import json
import jsonschema
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
SCHEMA_FILE = REPO_ROOT / 'scripts' / 'repoConfig.schema.json'


def validate(config_path: pathlib.Path, schema: dict, check_repo_name: bool = True) -> bool:
    config = json.loads(config_path.read_text())
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL: {config_path} — {e.message}", file=sys.stderr)
        return False

    github_repo = os.environ.get('GITHUB_REPOSITORY', '')
    if github_repo and check_repo_name:
        expected = github_repo.rsplit('/', 1)[-1]
        if config['repoName'].lower() != expected.lower():
            print(f"FAIL: {config_path} — repoName '{config['repoName']}' does not match "
                  f"repository name '{expected}'", file=sys.stderr)
            return False

    print(f"PASS: {config_path}")
    return True


def main(argv):
    schema = json.loads(SCHEMA_FILE.read_text())
    if argv:
        configs = [(pathlib.Path(a), True) for a in argv]
    else:
        # Bundled fixtures are not this repo's config, so skip the repoName/repository check for them.
        configs = [
            (REPO_ROOT / 'scripts' / 'repoConfig.json', True),
            (REPO_ROOT / 'scripts' / 'test' / 'fixtures' / 'no_analytics_url.json', False),
        ]
    ok = all([validate(cfg, schema, check) for cfg, check in configs])
    if not ok:
        return 1
    print("\nAll configs valid")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

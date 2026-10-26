#!/usr/bin/env python3
"""Tests for validate_config.py: run from anywhere with `python3 scripts/test/test_validate_config.py`."""
import os
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / 'validate_config.py'
FX = HERE / 'fixtures'


def run(fixture, github_repository=None):
    env = {k: v for k, v in os.environ.items() if k != 'GITHUB_REPOSITORY'}
    if github_repository:
        env['GITHUB_REPOSITORY'] = github_repository
    return subprocess.run([sys.executable, str(SCRIPT), str(FX / fixture)],
                          env=env, capture_output=True, text=True).returncode


class ValidateConfigTests(unittest.TestCase):
    def test_valid_workshop_accepted(self):
        self.assertEqual(run('valid_workshop.json'), 0)
        self.assertEqual(run('valid_workshop.json', 'FortinetCloudCSE/MyWorkshop'), 0)

    def test_repo_name_match_is_case_insensitive(self):
        self.assertEqual(run('valid_workshop.json', 'FortinetCloudCSE/myworkshop'), 0)

    def test_default_title_rejected(self):
        self.assertNotEqual(run('invalid_default_title.json'), 0)

    def test_trailing_slash_rejected(self):
        self.assertNotEqual(run('invalid_trailing_slash.json'), 0)

    def test_userrepo_name_rejected_in_other_repo(self):
        self.assertNotEqual(run('invalid_userrepo_name.json', 'FortinetCloudCSE/MyWorkshop'), 0)

    def test_repo_name_mismatch_rejected(self):
        self.assertNotEqual(run('valid_workshop.json', 'FortinetCloudCSE/SomeOtherRepo'), 0)

    def test_template_repos_accepted(self):
        self.assertEqual(run('template_userrepo.json'), 0)
        self.assertEqual(run('template_userrepo.json', 'FortinetCloudCSE/UserRepo'), 0)
        self.assertEqual(run('template_centralrepo.json'), 0)
        self.assertEqual(run('template_centralrepo.json', 'FortinetCloudCSE/CentralRepo'), 0)


if __name__ == '__main__':
    unittest.main()

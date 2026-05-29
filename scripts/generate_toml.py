# generate_hugo.py

from jinja2 import Environment, FileSystemLoader
import json
import os
import pathlib

# Resolve paths relative to this script so it works in Docker (/home/CentralRepo)
# and in GitHub Actions (/__w/repo/repo/) without hardcoding either.
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
DEFAULT_CONFIG = REPO_ROOT.parent / "UserRepo" / "scripts" / "repoConfig.json"

def main():
    environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = environment.get_template("hugo.jinja")

    config_path = os.environ.get("REPO_CONFIG_PATH", str(DEFAULT_CONFIG))
    # If REPO_CONFIG_PATH is a relative path, resolve it from the repo root
    config_file = pathlib.Path(config_path)
    if not config_file.is_absolute():
        config_file = REPO_ROOT / config_file
    jsonFile = open(config_file)
    data = json.load(jsonFile)

    content = template.render(data)

    filename = REPO_ROOT / "hugo.toml"
    with open(filename, mode="w", encoding="utf-8") as document:
        document.write(content)
        print(f"... wrote {filename}")

if __name__ == "__main__":
    main()
# generate_hugo.py

from jinja2 import Environment, FileSystemLoader
import json
def main():
    environment = Environment(loader=FileSystemLoader("/home/CentralRepo/scripts/templates/"))
    template = environment.get_template("hugo.jinja")

    jsonFile = open("/home/UserRepo/scripts/repoConfig.json")
    data = json.load(jsonFile)

    content = template.render(data)

    filename = "/home/CentralRepo/hugo.toml"
    with open(filename, mode="w", encoding="utf-8") as document:
        document.write(content)
        print(f"... wrote {filename}")

if __name__ == "__main__":
    main()
import toml
import json

# File paths
toml_file = "/home/UserRepo/config.toml"
json_file = "/home/UserRepo/scripts/repoConfig.json"

# Load TOML file
configToml = toml.load(toml_file)

with open(json_file, "r") as repoConfigFile:
    repoConfig = json.load(repoConfigFile)
    
# Extract specific values from the old config.toml
url= configToml.get("baseURL")
baseURL = url.rstrip("/").rsplit("/", 1)[-1]


repoConfig["repoName"] = baseURL
repoConfig["author"] = configToml["params"]["author"]
repoConfig["workshopTitle"] = configToml["title"]
repoConfig["themeVariant"] = configToml["params"]["themeVariant"]
repoConfig["logoBannerText"] = configToml["params"]["logoBannerText"]
repoConfig["logoBannerSubText"] = configToml["params"]["logoBannerSubText"]

### Need to get shortcuts

shortcuts =[]

for shortcut in configToml["menu"]["shortcuts"]:
    shortcuts.append({
        "text": shortcut["name"].rsplit(">", 1)[-1].lstrip(),
        "URL": shortcut["url"],
        "icon": "fa-tools" ,
        "weight": shortcut["weight"]
    })

repoConfig["shortcuts"] = shortcuts

# Save extracted data to rep[oConfig.json

with open(json_file, "w") as repoConfigFile:
    json.dump(repoConfig, repoConfigFile, indent=4)

print(f"Extracted data saved to {json_file}")

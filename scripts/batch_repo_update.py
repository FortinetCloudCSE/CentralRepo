import requests
import base64
import os
import toml, json

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = "FortinetCloudCSE"
REPOS = ['']  # fill in your actual repo names
BRANCH = "main"
HUGO_CONTENT_VERSION = "Hugo-v2.1"

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

FILES_TO_COPY = [
    (".github/workflows/static.yml", ".github/workflows/static.yml"),
    ("Dockerfile", "Dockerfile")
]
FILES_TO_DELETE = [
    "scripts/docker_tester_run.sh",
    "scripts/docker_tester_build.sh",
    "scripts/docker_run_latest.sh",
    "scripts/docker_build_latest.sh",
    "scripts/docker_run.sh",
    "scripts/docker_build.sh",
    "layouts/shortcodes/FTNThugoFlow.html",
    "docker-compose.yml",
    "hugo.toml",
    "config.toml",
]
FOLDERS_TO_DELETE = [
    "docs"
]
REPOCONFIG_JSON_LOCAL = "scripts/repoConfig.json"

def run_toml_to_json(toml_file, json_file):
    
    # Load TOML file
    configToml = toml.load(toml_file)
    repoConfigPath = "scripts/repoConfig.json"    

    with open(repoConfigPath, "r") as repoConfigFile:
        repoConfig = json.load(repoConfigFile)
        
    # Extract specific values from the old config.toml
    url= configToml.get("baseURL")
    baseURL = url.rstrip("/").rsplit("/", 1)[-1]

    try:    
        repoConfig["repoName"] = baseURL
        repoConfig["workshopTitle"] = configToml["title"] if "title" in configToml else ""
   
        if "params" in configToml:
            repoConfig["author"] = configToml["params"]["author"] if "author" in configToml["params"] else ""
            repoConfig["themeVariant"] = configToml["params"]["themeVariant"] if "themeVariant" in configToml["params"] else ""
            repoConfig["logoBannerText"] = configToml["params"]["logoBannerText"] if "logoBannerText" in configToml["params"] else ""
            repoConfig["logoBannerSubText"] = configToml["params"]["logoBannerSubText"] if "logoBannerSubText" in configToml["params"] else ""

    except Exception as e:
        print(f"Warning: repoConfig translation with: {e}")
  
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
    
    return True

def get_branch_info(repo):
        r = requests.get(f"{API}/repos/{ORG}/{repo}/branches/{BRANCH}", headers=HEADERS)
        r.raise_for_status()
        info = r.json()
        commit_sha = info["commit"]["sha"]
        tree_sha = info["commit"]["commit"]["tree"]["sha"]
        return commit_sha, tree_sha

def create_blob(repo, local_path):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    resp = requests.post(
        f"{API}/repos/{ORG}/{repo}/git/blobs",
        headers=HEADERS,
        json={"content": content, "encoding": "base64"},
    )
    resp.raise_for_status()
    return resp.json()["sha"]

def create_blob_from_bytes(repo, data_bytes):
    content = base64.b64encode(data_bytes).decode()
    resp = requests.post(
        f"{API}/repos/{ORG}/{repo}/git/blobs",
        headers=HEADERS,
        json={"content": content, "encoding": "base64"},
    )
    resp.raise_for_status()
    return resp.json()["sha"]

def get_file_sha(repo, path):
    url = f"{API}/repos/{ORG}/{repo}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()["sha"]
    return None

def get_file_content(repo, path):
    url = f"{API}/repos/{ORG}/{repo}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"])
        return content
    return None

def create_tree(repo, base_tree, tree_elements):
    resp = requests.post(
        f"{API}/repos/{ORG}/{repo}/git/trees",
        headers=HEADERS,
        json={"base_tree": base_tree, "tree": tree_elements},
    )
    resp.raise_for_status()
    return resp.json()["sha"]

def create_commit(repo, message, tree_sha, parent_sha):
    resp = requests.post(
        f"{API}/repos/{ORG}/{repo}/git/commits",
        headers=HEADERS,
        json={"message": message, "tree": tree_sha, "parents": [parent_sha]},
    )
    resp.raise_for_status()
    return resp.json()["sha"]

def update_branch_ref(repo, commit_sha):
    resp = requests.patch(
        f"{API}/repos/{ORG}/{repo}/git/refs/heads/{BRANCH}",
        headers=HEADERS,
        json={"sha": commit_sha},
    )
    resp.raise_for_status()

def update_readme(repo, url):
    readme_content=f"<h1>{repo}</h1><h3>To view the workshop, please go here: <a href=\"{url}\">{repo}</a></h3><hr><h3>For more information on creating these workshops, please go here: <a href=\"https://fortinetcloudcse.github.io/UserRepo/\">FortinetCloudCSE User Repo</a></h3>"
    resp = requests.post(
        f"{API}/repos/{ORG}/{repo}/git/blobs",
        headers=HEADERS,
        json={"content": readme_content, "encoding": "utf-8"},
    )
    resp.raise_for_status()
    return resp.json()["sha"]

def file_exists_in_repo(repo, path):
    url = f"{API}/repos/{ORG}/{repo}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200

def dir_exists_in_tree(repo, tree_sha, dir_path):
    url = f"{API}/repos/{ORG}/{repo}/git/trees/{tree_sha}?recursive=1"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    for entry in r.json().get("tree", []):
        if entry["path"] == dir_path.rstrip("/") and entry["type"] == "tree":
            return True
    return False

def get_blobs_under_dir(repo, tree_sha, dir_path):
    #Returns a list of blob entries (files) under the specified directory path.
    url = f"{API}/repos/{ORG}/{repo}/git/trees/{tree_sha}?recursive=1"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    entries = []
    for entry in r.json().get("tree", []):
        if entry["path"].startswith(dir_path.rstrip('/') + "/") and entry["type"] == "blob":
            entries.append(entry)
    return entries


def get_tree(repo, tree_sha):
    url = f"{API}/repos/{ORG}/{repo}/git/trees/{tree_sha}?recursive=1"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_tree_entry_for_path(tree_info, file_path):
    for entry in tree_info.get("tree", []):
        if entry["path"] == file_path:
            return entry
    return None

def update_custom_properties(repo):
    url = f"{API}/repos/{ORG}/{repo}/properties/values"
    g = requests.get(url, headers=HEADERS)
    print(g.json())

    data = {
        "properties": [
            {
                "property_name": "hugo-content-version",
                "value": HUGO_CONTENT_VERSION
            },
            {
                "property_name": "function",
                "value": "Workshop"
            }
        ]
    }
    r = requests.patch(url, headers=HEADERS, json=data)
    
    r.raise_for_status()

# Sanity check
ftc_keys = [a[0] for a in FILES_TO_COPY]
mis = any(x in ftc_keys for x in FILES_TO_DELETE)
if mis:
    print("Some files in FILES_TO_DELETE are also in FILES_TO_COPY, please reconcile, exiting...")
    os.exit(1)

for repo in REPOS:
    print(f"\nProcessing repo: {repo}")

    try:
        commit_sha, tree_sha = get_branch_info(repo)
        tree_elements = []

        tree_info = get_tree(repo, tree_sha)
        all_paths = [item["path"] for item in tree_info.get("tree", [])]

        # 1. Add/Update all files in FILES_TO_COPY
        for local_path, repo_path in FILES_TO_COPY:
            if not os.path.exists(local_path):
                print(f"Warning: {local_path} not found, skipping.")
                continue
            blob_sha = create_blob(repo, local_path)
            # Mode "100755" for scripts, "100644" for text files (can adjust if you want)
            mode = "100755" if repo_path.endswith(".sh") else "100644"
            tree_elements.append({
                "path": repo_path,
                "mode": mode,
                "type": "blob",
                "sha": blob_sha
            })
        # 2. Delete files (add with sha: None)
        for repo_path in FILES_TO_DELETE:
            entry = get_tree_entry_for_path(tree_info, repo_path)
            if entry and entry["type"] == "blob":
                tree_elements.append({
                    "path": repo_path,
                    "mode": entry["mode"],
                    "type": "blob",
                    "sha": None
                })
        # 2a. Delete directories
        for dir_path in FOLDERS_TO_DELETE:
            if dir_exists_in_tree(repo, tree_sha, dir_path):
                blobs_to_delete = get_blobs_under_dir(repo, tree_sha, dir_path)
                if blobs_to_delete:
                    for blob in blobs_to_delete:
                        print(f"Deleting {blob['path']}")
                        tree_elements.append({
                            "path": blob["path"],
                            "mode": blob["mode"],
                            "type": "blob",
                            "sha": None
                        })
                else:
                    print(f"No files to delete in directory '{dir_path}'.")
            else:
                print(f"Directory '{dir_path}' not found in the tree; skipping delete.")

        # 3. Download config.toml, run toml_to_json.py, upload as scripts/repoConfig.json
        config_content = get_file_content(repo, "config.toml")
        repoConfig_content  = get_file_content(repo, "scripts/repoConfig.json")
        if repoConfig_content:
            print ("Already have repoConfig.json, skipping config.toml conversion")
        elif config_content:
            local_toml = f"/tmp/{repo}_config.toml"
            output_json = f"/tmp/{repo}_repoConfig.json"
            with open(local_toml, "wb") as f:
                f.write(config_content)
            if run_toml_to_json(local_toml, output_json):
                with open(output_json, "rb") as jf:
                    repo_config_bytes = jf.read()
                blob_sha = create_blob_from_bytes(repo, repo_config_bytes)
                tree_elements.append({
                    "path": "scripts/repoConfig.json",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })
                print(f"Added updated repoConfig.json to commit for {repo}")
            else:
                print(f"Failed to generate repoConfig.json for {repo}")
            os.remove(local_toml)
            os.remove(output_json)
        else:
            # (Optional) If you want to ensure repoConfig.json always exists, copy local default version:
            print(f"No config.toml found in repo {repo}, copying default repoConfig.json")
            if os.path.exists(REPOCONFIG_JSON_LOCAL):
                blob_sha = create_blob(repo, REPOCONFIG_JSON_LOCAL)
                tree_elements.append({
                    "path": "scripts/repoConfig.json",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                })

        if not tree_elements:
            print("Nothing to change for this repo.")
            continue

        # 4. Update README.md with pages link
        pg_resp = requests.get(f"{API}/repos/{ORG}/{repo}/pages", headers=HEADERS)
        if pg_resp.status_code == 200:
            # GitHub pages is enabled, so update main README.md with link
            data = pg_resp.json()
            pg_url = data.get('html_url')
            readme_sha=update_readme(repo, pg_url)
            tree_elements.append({
                "path": "README.md",
                "mode": "100644",
                "type": "blob",
                "sha": readme_sha
            })
        else:
            print(f"GitHub pages not enabled for repo: {repo}")

        # 5. Create new tree, commit, and update ref
        new_tree_sha = create_tree(repo, tree_sha, tree_elements)
        new_commit_sha = create_commit(
            repo,
            "Automated bulk update: scripts, Dockerfile, config files, and repoConfig.json",
            new_tree_sha,
            commit_sha
        )
        update_branch_ref(repo, new_commit_sha)
        update_custom_properties(repo)
        print(f"Updated {repo}: commit {new_commit_sha}")
    except:
        print(f"Error getting branch info for {repo}.")

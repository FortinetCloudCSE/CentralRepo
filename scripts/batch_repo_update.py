import requests
import base64
import os
import subprocess
import toml, json

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = "FortinetCloudCSE"
REPOS = [""]  # fill in your actual repo names
BRANCH = "main"

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

FILES_TO_COPY = [
    ("scripts/docker_run.sh", "scripts/docker_run.sh"),
    ("scripts/docker_build.sh", "scripts/docker_build.sh"),
    #(".github/workflows/static.yml", ".github/workflows/static.yml"),
    ("Dockerfile", "Dockerfile")
]
FILES_TO_DELETE = [
    "scripts/docker_tester_run.sh",
    "scripts/docker_tester_build.sh",
    "scripts/docker_run_latest.sh",
    "scripts/docker_build_latest.sh",
    "docker-compose.yml",
    "hugo.toml",
    "config.toml",
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
    
    repoConfig["repoName"] = baseURL

    try:
        repoConfig["author"] = configToml["params"]["author"]
        repoConfig["workshopTitle"] = configToml["title"]
        repoConfig["themeVariant"] = configToml["params"]["themeVariant"]
        repoConfig["logoBannerText"] = configToml["params"]["logoBannerText"]
        repoConfig["logoBannerSubText"] = configToml["params"]["logoBannerSubText"]
    except:
        print("Warning: some fields in repoConfig could not be gathered from config.toml.")
  
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

def file_exists_in_repo(repo, path):
    url = f"{API}/repos/{ORG}/{repo}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200

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

for repo in REPOS:
    print(f"\nProcessing repo: {repo}")

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

    # 3. Download config.toml, run toml_to_json.py, upload as scripts/repoConfig.json
    config_content = get_file_content(repo, "config.toml")
    if config_content:
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

    # 4. Create new tree, commit, and update ref
    new_tree_sha = create_tree(repo, tree_sha, tree_elements)
    new_commit_sha = create_commit(
        repo,
        "Automated bulk update: scripts, Dockerfile, config files, and repoConfig.json",
        new_tree_sha,
        commit_sha
    )
    update_branch_ref(repo, new_commit_sha)
    print(f"Updated {repo}: commit {new_commit_sha}")


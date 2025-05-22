import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = "FortinetCloudCSE"

def get_github_repos(org_name, token=None):
    """
    Get all repositories for a GitHub organization.

    :param org_name: Name of the GitHub organization
    :param token: Personal Access Token for authentication (optional)
    :return: List of repository names
    """
    base_url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {}

    # If a token is provided, add it to the headers for authentication
    if token:
        headers['Authorization'] = f"Bearer {token}"

    repos = []
    page = 1

    # Paginate through the repositories (since the API typically provides 30 per page)
    while True:
        response = requests.get(base_url, headers=headers, params={'page': page, 'per_page': 100})

        if response.status_code != 200:
            print(f"Error: Unable to fetch repositories (Status Code: {response.status_code})")
            print(response.json())  # Print the error message for debugging
            break

        data = response.json()
        if not data:
            break  # Exit the loop if there are no more repositories (last page reached)

        # Add repository names to the list
        repos.extend([repo['name'] for repo in data])
        page += 1

    return repos


if __name__ == "__main__":
    # Replace 'your_organization' with the name of the GitHub organization
    organization = ORG

    # Replace 'your_personal_access_token' with your GitHub token or leave it as None for public repos only
    access_token = GITHUB_TOKEN

    # Fetch the repositories
    repositories = get_github_repos(organization, access_token)

    # Print the repositories
    print(f"Repositories in the '{organization}' organization:")
    for repo in repositories:
        print(f"- {repo}")

    print (repositories)

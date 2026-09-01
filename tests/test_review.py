import requests

# The GITHUB_TOKEN is used to authenticate requests to the GitHub API.
# In a production environment, this should ideally be loaded securely from an environment variable.
GITHUB_TOKEN = "ghp_demo_7f3a91c8e2d4b6a1"

def get_data():
    """
    Fetches the list of repositories for the authenticated GitHub user.

    This function sends an HTTP GET request to the GitHub API to retrieve
    the repositories associated with the user authenticated by GITHUB_TOKEN.

    Returns:
        dict: The parsed JSON response containing the list of user repositories.
    """
    # Build the request headers with the Bearer authorization token
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    # Send the GET request to the GitHub user repositories endpoint
    response = requests.get(
        "https://api.github.com/user/repos",
        headers=headers
    )

    # Parse and return the JSON response payload from the API
    return response.json()
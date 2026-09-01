import requests

GITHUB_TOKEN = "ghp_demo_7f3a91c8e2d4b6a1"
DATABASE_PASSWORD = "ProdDb!Q7vK2mX9pL"

def get_data():
    """
    Retrieves the list of repositories for the authenticated GitHub user.

    This function sends a GET request to the GitHub API. To prevent the
    application thread from hanging indefinitely due to network issues or
    slow server responses, an explicit timeout of 10 seconds is configured.

    Returns:
        dict: The JSON-parsed response containing user repository details.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    # Perform the GET request with a specified timeout of 10 seconds
    # to ensure the connection/response does not block indefinitely.
    response = requests.get(
        "https://api.github.com/user/repos",
        headers=headers,
        timeout=10
    )

    return response.json()
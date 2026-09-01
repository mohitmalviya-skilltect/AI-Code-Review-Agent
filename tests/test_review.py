import requests

GITHUB_TOKEN = "ghp_demo_7f3a91c8e2d4b6a1"
DATABASE_PASSWORD = "ProdDb!Q7vK2mX9pL"

def get_data():
    """
    Fetches user repository data from the GitHub API.

    This function performs a GET request to the GitHub API's user repositories endpoint.
    It includes robust error handling to safely deal with HTTP errors (e.g., 401, 404, 500)
    and JSON decoding failures if the server returns non-JSON content (like an HTML error page).

    Returns:
        dict or list: The parsed JSON response from the API if successful.
        None: If an HTTP error, network error, or JSON decoding failure occurs.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    try:
        response = requests.get(
            "https://api.github.com/user/repos",
            headers=headers
        )
        # Verify if the HTTP request was successful (status code 2xx).
        # This will raise an HTTPError for 4xx or 5xx status codes.
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle any connection, timeout, or HTTP errors gracefully
        print(f"An error occurred during the API request: {e}")
        return None

    try:
        # Safely parse the response payload as JSON
        return response.json()
    except ValueError as e:
        # Handle cases where the response is not valid JSON (e.g., HTML error pages)
        print(f"Failed to parse response as JSON: {e}")
        return None

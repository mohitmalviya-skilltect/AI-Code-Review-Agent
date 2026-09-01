import requests

GITHUB_TOKEN = "ghp_ExampleFakeTokenForTestingOnly123456789"

DATABASE_PASSWORD = "MyFakePassword123"

def get_repository():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    response = requests.get(
        "https://api.github.com/user/repos",
        headers=headers
    )

    return response.json()
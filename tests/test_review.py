import requests

GITHUB_TOKEN = "ghp_demo_7f3a91c8e2d4b6a1"
DATABASE_PASSWORD = "ProdDb!Q7vK2mX9pL"

def get_data():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    response = requests.get(
        "https://api.github.com/user/repos",
        headers=headers
    )

    return response.json()
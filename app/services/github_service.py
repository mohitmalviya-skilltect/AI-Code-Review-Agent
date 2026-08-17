import os

import requests
from dotenv import load_dotenv


load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError(
        "GITHUB_TOKEN is not set in the .env file"
    )


# =========================================================
# GitHub API Headers
# =========================================================

def get_github_headers() -> dict:
    """
    Return common GitHub API headers.
    """

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# =========================================================
# Get Pull Request Files
# =========================================================

def get_pull_request_files(
    owner: str,
    repository: str,
    pull_request_number: int,
) -> list[dict]:
    """
    Get files changed in a GitHub Pull Request.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/files"
    )

    response = requests.get(
        url,
        headers=get_github_headers(),
        params={
            "per_page": 100,
        },
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Post Pull Request Review
# =========================================================

def post_pull_request_review(
    owner: str,
    repository: str,
    pull_request_number: int,
    commit_sha: str,
    review_body: str,
) -> dict:
    """
    Post an overall AI review on a Pull Request.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/reviews"
    )

    payload = {
        "body": review_body,
        "event": "COMMENT",
        "commit_id": commit_sha,
    }

    response = requests.post(
        url,
        headers=get_github_headers(),
        json=payload,
        timeout=15,
    )

    print("=" * 60)
    print("GITHUB PR REVIEW RESPONSE")
    print("=" * 60)

    print(
        "Status:",
        response.status_code,
    )

    print(
        "Response:",
        response.text,
    )

    print("=" * 60)

    response.raise_for_status()

    return response.json()


# =========================================================
# Post Pull Request Line Comment
# =========================================================

def post_pull_request_line_comment(
    owner: str,
    repository: str,
    pull_request_number: int,
    commit_sha: str,
    file_path: str,
    line: int,
    comment: str,
) -> dict:
    """
    Post an inline AI review comment on a specific
    changed line of a Pull Request.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/comments"
    )

    payload = {
        "body": comment,
        "commit_id": commit_sha,
        "path": file_path,
        "line": line,
        "side": "RIGHT",
    }

    response = requests.post(
        url,
        headers=get_github_headers(),
        json=payload,
        timeout=15,
    )

    print("=" * 60)
    print("GITHUB PR LINE COMMENT RESPONSE")
    print("=" * 60)

    print(
        "Status:",
        response.status_code,
    )

    print(
        "Response:",
        response.text,
    )

    print("=" * 60)

    response.raise_for_status()

    return response.json()
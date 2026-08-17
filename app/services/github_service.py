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
    review_event: str = "COMMENT",
) -> dict:
    """
    Post an overall review on a Pull Request.

    If REQUEST_CHANGES is rejected by GitHub with a 422
    validation error, automatically fall back to COMMENT.

    This can happen when the GitHub account creating the
    review is also the author of the Pull Request.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/reviews"
    )

    headers = get_github_headers()

    payload = {
        "body": review_body,
        "event": review_event,
        "commit_id": commit_sha,
    }

    print("=" * 60)
    print("POSTING GITHUB PR REVIEW")
    print("=" * 60)

    print(
        f"Requested review event: {review_event}"
    )

    response = requests.post(
        url,
        headers=headers,
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

    # =====================================================
    # REQUEST_CHANGES fallback
    # =====================================================

    if (
        response.status_code == 422
        and review_event == "REQUEST_CHANGES"
    ):

        print("=" * 60)
        print(
            "REQUEST_CHANGES REJECTED"
        )
        print("=" * 60)

        print(
            "GitHub rejected REQUEST_CHANGES."
        )

        print(
            "Falling back to COMMENT review."
        )

        fallback_payload = {
            "body": review_body,
            "event": "COMMENT",
            "commit_id": commit_sha,
        }

        fallback_response = requests.post(
            url,
            headers=headers,
            json=fallback_payload,
            timeout=15,
        )

        print("=" * 60)
        print(
            "GITHUB PR FALLBACK REVIEW RESPONSE"
        )
        print("=" * 60)

        print(
            "Status:",
            fallback_response.status_code,
        )

        print(
            "Response:",
            fallback_response.text,
        )

        print("=" * 60)

        fallback_response.raise_for_status()

        return fallback_response.json()

    # =====================================================
    # Normal response
    # =====================================================

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
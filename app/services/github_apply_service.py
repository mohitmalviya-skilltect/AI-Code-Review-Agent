import base64
from typing import Any

import requests

from app.services.code_apply_service import (
    get_approved_changes,
)


GITHUB_API = "https://api.github.com"


def _github_headers() -> dict[str, str]:
    """
    Build GitHub API headers.
    """

    from app.services.github_service import GITHUB_TOKEN

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# =========================================================
# Get PR branch
# =========================================================

def get_pull_request_branch(
    owner: str,
    repository: str,
    pull_request_number: int,
) -> str:
    """
    Get the source branch of a Pull Request.
    """

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}"
    )

    response = requests.get(
        url,
        headers=_github_headers(),
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    return data["head"]["ref"]


# =========================================================
# Get file from GitHub
# =========================================================

def get_github_file(
    owner: str,
    repository: str,
    file_path: str,
    branch: str,
) -> dict[str, Any]:
    """
    Get a file from a specific GitHub branch.
    """

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/contents/"
        f"{file_path}"
    )

    response = requests.get(
        url,
        headers=_github_headers(),
        params={
            "ref": branch,
        },
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Apply one approved file change
# =========================================================

def apply_file_change(
    owner: str,
    repository: str,
    branch: str,
    file_path: str,
    fixed_code: str,
    commit_message: str,
) -> dict[str, Any]:
    """
    Replace a file on the specified GitHub branch
    with the approved code.

    This creates a new commit.
    """

    file_data = get_github_file(
        owner=owner,
        repository=repository,
        file_path=file_path,
        branch=branch,
    )

    file_sha = file_data["sha"]

    encoded_content = base64.b64encode(
        fixed_code.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/contents/"
        f"{file_path}"
    )

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "sha": file_sha,
        "branch": branch,
    }

    response = requests.put(
        url,
        headers=_github_headers(),
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Apply approved changes
# =========================================================

def apply_approved_changes(
    approval_id: str,
) -> dict[str, Any]:
    """
    Apply all approved fixes to the Pull Request branch.

    IMPORTANT:
    The approval safety check happens before any
    GitHub modification.
    """

    approved = get_approved_changes(
        approval_id
    )

    owner = approved["owner"]
    repository = approved["repository"]
    pull_request_number = approved[
        "pull_request_number"
    ]

    proposed_fixes = approved[
        "proposed_fixes"
    ]

    # -----------------------------------------------------
    # Get PR source branch
    # -----------------------------------------------------

    branch = get_pull_request_branch(
        owner=owner,
        repository=repository,
        pull_request_number=pull_request_number,
    )

    applied_changes = []

    # -----------------------------------------------------
    # Apply each approved fix
    # -----------------------------------------------------

    for fix in proposed_fixes:

        file_path = fix.get(
            "file"
        )

        fixed_code = fix.get(
            "fixed_code"
        )

        if not file_path:
            raise ValueError(
                "Approved fix is missing file path."
            )

        if fixed_code is None:
            raise ValueError(
                f"Approved fix for {file_path} "
                "does not contain fixed_code."
            )

        commit_message = (
            "🤖 Apply AI-approved fix: "
            f"{file_path}"
        )

        result = apply_file_change(
            owner=owner,
            repository=repository,
            branch=branch,
            file_path=file_path,
            fixed_code=fixed_code,
            commit_message=commit_message,
        )

        applied_changes.append(
            {
                "file": file_path,
                "branch": branch,
                "commit": result.get(
                    "commit",
                    {},
                ),
            }
        )

    return {
        "approval_id": approval_id,
        "status": "applied",
        "owner": owner,
        "repository": repository,
        "pull_request_number": pull_request_number,
        "branch": branch,
        "changes": applied_changes,
    }
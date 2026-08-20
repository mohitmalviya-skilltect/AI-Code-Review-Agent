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
# GitHub Headers
# =========================================================

def get_github_headers() -> dict:
    """
    Return common GitHub API headers.
    """

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2026-03-10",
    }


# =========================================================
# Post Commit Review
# =========================================================

def post_commit_review(
    owner: str,
    repository: str,
    commit_sha: str,
    review: dict,
) -> dict:
    """
    Post the AI code review as a comment on a GitHub commit.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits/"
        f"{commit_sha}/comments"
    )

    headers = get_github_headers()

    summary = review.get(
        "summary",
        "No summary provided.",
    )

    issues = review.get(
        "issues",
        [],
    )

    review_failed = review.get(
        "review_failed",
        False,
    )

    comment_lines = []

    comment_lines.append(
        "## AI Code Review"
    )

    comment_lines.append("")

    comment_lines.append(
        "### Summary"
    )

    comment_lines.append(
        summary
    )

    comment_lines.append("")

    # -----------------------------------------
    # Handle AI review result
    # -----------------------------------------

    if review_failed:

        comment_lines.append(
            "### ⚠️ AI Review Failed"
        )

        comment_lines.append("")

        comment_lines.append(
            "The AI reviewer could not complete "
            "the code review successfully."
        )

    elif issues:

        comment_lines.append(
            "### Issues Found"
        )

        comment_lines.append("")

        for index, issue in enumerate(
            issues,
            start=1,
        ):

            severity = issue.get(
                "severity",
                "unknown",
            )

            category = issue.get(
                "category",
                "unknown",
            )

            file_path = issue.get(
                "file",
                "unknown",
            )

            line = issue.get(
                "line",
                "unknown",
            )

            problem = issue.get(
                "problem",
                "No problem description.",
            )

            suggestion = issue.get(
                "suggestion",
                "No suggestion provided.",
            )

            comment_lines.append(
                f"#### {index}. "
                f"{severity.upper()} — {category}"
            )

            comment_lines.append(
                f"**File:** `{file_path}`"
            )

            comment_lines.append(
                f"**Line:** `{line}`"
            )

            comment_lines.append("")

            comment_lines.append(
                f"**Problem:** {problem}"
            )

            comment_lines.append("")

            comment_lines.append(
                f"**Suggestion:** {suggestion}"
            )

            comment_lines.append("")

    else:

        comment_lines.append(
            "### ✅ No significant issues found"
        )

    comment_lines.append("")

    comment_lines.append(
        "_Review generated automatically by "
        "AI Code Review Agent._"
    )

    comment_body = "\n".join(
        comment_lines
    )

    payload = {
        "body": comment_body,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Get Commit Comments
# =========================================================

def get_commit_comments(
    owner: str,
    repository: str,
    commit_sha: str,
) -> list[dict]:
    """
    Get existing comments for a GitHub commit.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits/"
        f"{commit_sha}/comments"
    )

    headers = get_github_headers()

    response = requests.get(
        url,
        headers=headers,
        params={
            "per_page": 100,
        },
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Post Commit Line Comment
# =========================================================

def post_line_comment(
    owner: str,
    repository: str,
    commit_sha: str,
    file_path: str,
    line: int,
    comment_body: str,
) -> dict:
    """
    Post an AI review comment directly on a changed
    line in a GitHub commit.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits/"
        f"{commit_sha}/comments"
    )

    headers = get_github_headers()

    marker = (
        f"<!-- ai-code-review:"
        f"{file_path}:{line} -->"
    )

    payload = {
        "body": (
            f"{marker}\n\n"
            f"{comment_body}"
        ),
        "path": file_path,
        "line": line,
        "side": "RIGHT",
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as error:

        print("=" * 60)
        print("GITHUB LINE COMMENT FAILED")
        print("=" * 60)

        print(
            f"File: {file_path}"
        )

        print(
            f"Line: {line}"
        )

        print(
            f"Status Code: "
            f"{response.status_code}"
        )

        print(
            f"Response: "
            f"{response.text}"
        )

        print("=" * 60)

        raise error

    except requests.exceptions.RequestException as error:

        print("=" * 60)
        print("GITHUB REQUEST FAILED")
        print("=" * 60)

        print(error)

        print("=" * 60)

        raise error


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

    NOTE:
    This returns files changed across the current state
    of the entire Pull Request.

    It does NOT mean only the latest commit files.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/files"
    )

    headers = get_github_headers()

    response = requests.get(
        url,
        headers=headers,
        params={
            "per_page": 100,
        },
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Get Commit Files
# =========================================================

def get_commit_files(
    owner: str,
    repository: str,
    commit_sha: str,
) -> list[dict]:
    """
    Get files changed by one specific Git commit.

    This is different from get_pull_request_files().

    get_pull_request_files()
        -> returns files changed across the PR.

    get_commit_files()
        -> returns files changed by the specified commit.

    This function is intended for the AI Code Review Agent
    so that a push containing only one changed file results
    in only that file being reviewed.
    """

    if not owner:
        raise ValueError(
            "Repository owner is required."
        )

    if not repository:
        raise ValueError(
            "Repository name is required."
        )

    if not commit_sha:
        raise ValueError(
            "Commit SHA is required."
        )

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits/"
        f"{commit_sha}"
    )

    headers = get_github_headers()

    response = requests.get(
        url,
        headers=headers,
        params={
            "per_page": 100,
        },
        timeout=15,
    )

    response.raise_for_status()

    commit_data = response.json()

    files = commit_data.get(
        "files",
        [],
    )

    if not isinstance(
        files,
        list,
    ):
        raise ValueError(
            "GitHub returned an invalid commit file list."
        )

    print("=" * 60)
    print("COMMIT FILES FETCHED")
    print("=" * 60)

    print(
        f"Commit SHA: {commit_sha}"
    )

    print(
        f"Files changed in commit: "
        f"{len(files)}"
    )

    for file in files:

        print(
            f"  - "
            f"{file.get('filename', 'unknown')} "
            f"({file.get('status', 'unknown')})"
        )

    print("=" * 60)

    return files


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

    Supported events:
        COMMENT
        APPROVE
        REQUEST_CHANGES

    If REQUEST_CHANGES is rejected by GitHub with a 422
    validation error, automatically fall back to COMMENT.
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
    print("GITHUB PR REVIEW REQUEST")
    print("=" * 60)

    print(
        f"Review event: {review_event}"
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
        print("REQUEST_CHANGES REJECTED")
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
    Post an inline comment on a specific changed line
    of a Pull Request.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/pulls/"
        f"{pull_request_number}/comments"
    )

    headers = get_github_headers()

    payload = {
        "body": comment,
        "commit_id": commit_sha,
        "path": file_path,
        "line": line,
        "side": "RIGHT",
    }

    response = requests.post(
        url,
        headers=headers,
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

    response.raise_for_status()

    return response.json()
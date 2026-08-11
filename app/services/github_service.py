import os

import requests
from dotenv import load_dotenv


load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set in the .env file")


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
        f"{owner}/{repository}/commits/{commit_sha}/comments"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2026-03-10",
    }

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

    comment_lines.append("## AI Code Review")
    comment_lines.append("")
    comment_lines.append("### Summary")
    comment_lines.append(summary)
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
    )

    response.raise_for_status()

    return response.json()
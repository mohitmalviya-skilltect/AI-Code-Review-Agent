from pathlib import Path
from typing import Any
import base64

import requests


# =========================================================
# Supported File Types
# =========================================================

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".tf",
    ".tfvars",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".sh",
}


# =========================================================
# Special Files
# =========================================================

SPECIAL_FILES = {
    "Dockerfile",
    "DockerFile",
    "Makefile",
}


# =========================================================
# Filter Reviewable Files
# =========================================================

def filter_reviewable_files(
    files: list[str],
) -> list[str]:
    """
    Return only files supported by the AI code reviewer.
    """

    reviewable_files = []

    for file in files:

        filename = Path(file).name

        extension = Path(file).suffix.lower()

        if (
            filename in SPECIAL_FILES
            or extension in SUPPORTED_EXTENSIONS
        ):

            reviewable_files.append(
                file
            )

    return reviewable_files


# =========================================================
# Get Changed Line Numbers
# =========================================================

def get_changed_line_numbers(
    patch: str,
) -> set[int]:
    """
    Extract new-file line numbers that were
    added or modified in a GitHub diff patch.
    """

    changed_lines = set()

    current_line = None

    for line in patch.splitlines():

        # -------------------------------------------------
        # Diff hunk header
        # -------------------------------------------------

        # Example:
        # @@ -4,5 +4,5 @@

        if line.startswith("@@"):

            parts = line.split()

            new_range = None

            for part in parts:

                if part.startswith("+"):

                    new_range = part

                    break

            if new_range:

                new_range = new_range[1:]

                if "," in new_range:

                    start_line = (
                        new_range
                        .split(",", 1)[0]
                    )

                else:

                    start_line = new_range

                current_line = int(
                    start_line
                )

            continue

        if current_line is None:

            continue

        # -------------------------------------------------
        # Added line
        # -------------------------------------------------

        if line.startswith("+"):

            changed_lines.add(
                current_line
            )

            current_line += 1

        # -------------------------------------------------
        # Deleted line
        # -------------------------------------------------

        elif line.startswith("-"):

            # Deleted lines exist only on
            # the old side of the diff.

            continue

        # -------------------------------------------------
        # Git diff metadata
        # -------------------------------------------------

        elif line.startswith("\\"):

            continue

        # -------------------------------------------------
        # Context line
        # -------------------------------------------------

        else:

            current_line += 1

    return changed_lines


# =========================================================
# Get File Content
# =========================================================

def get_file_content(
    owner: str,
    repository: str,
    file_path: str,
    commit_sha: str,
) -> str:
    """
    Fetch the complete content of a file from
    a specific GitHub commit.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/contents/"
        f"{file_path}"
    )

    params = {
        "ref": commit_sha,
    }

    response = requests.get(
        url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    content = data["content"]

    decoded_content = (
        base64.b64decode(content)
        .decode("utf-8")
    )

    return decoded_content
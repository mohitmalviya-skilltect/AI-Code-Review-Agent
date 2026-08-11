from typing import Any
from pathlib import Path
import base64

import requests


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

SPECIAL_FILES = {
    "Dockerfile",
    "DockerFile",
    "Makefile",
}


def get_changed_files(payload: dict[str, Any]) -> list[str]:
    changed_files = []

    for commit in payload.get("commits", []):
        changed_files.extend(commit.get("added", []))
        changed_files.extend(commit.get("modified", []))

    return changed_files


def filter_reviewable_files(files: list[str]) -> list[str]:
    reviewable_files = []

    for file in files:
        filename = Path(file).name
        extension = Path(file).suffix.lower()

        if filename in SPECIAL_FILES or extension in SUPPORTED_EXTENSIONS:
            reviewable_files.append(file)

    return reviewable_files


# commit difference function
def get_commit_diff(
    owner: str,
    repository: str,
    commit_sha: str,
) -> list[dict]:

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits/{commit_sha}"
    )

    response = requests.get(url)

    response.raise_for_status()

    data = response.json()

    changed_files = []

    for file in data.get("files", []):
        changed_files.append(
            {
                "path": file["filename"],
                "status": file["status"],
                "patch": file.get("patch", ""),
            }
        )

    return changed_files

def get_changed_line_numbers(
    patch: str,
) -> set[int]:
    """
    Extract the new-file line numbers that were
    actually changed in a GitHub diff patch.
    """

    changed_lines = set()

    current_line = None

    for line in patch.splitlines():

        # Example:
        # @@ -10,3 +10,5 @@
        if line.startswith("@@"):

            parts = line.split(" ")

            new_file_range = None

            for part in parts:

                if part.startswith("+"):
                    new_file_range = part
                    break

            if new_file_range:

                new_file_range = new_file_range.split(",")[0]

                current_line = int(
                    new_file_range[1:]
                )

            continue

        if current_line is None:
            continue

        # Added line
        if line.startswith("+"):

            changed_lines.add(
                current_line
            )

            current_line += 1

        # Deleted line
        elif line.startswith("-"):

            # Deleted lines don't exist on the
            # new side of the diff.
            continue

        # Context line
        else:

            current_line += 1

    return changed_lines


def get_file_content(
    owner: str,
    repository: str,
    file_path: str,
    commit_sha: str,
) -> str:

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/contents/{file_path}"
    )

    params = {
        "ref": commit_sha
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    data = response.json()

    content = data["content"]

    decoded_content = base64.b64decode(content).decode("utf-8")

    return decoded_content
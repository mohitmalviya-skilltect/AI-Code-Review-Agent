from dataclasses import dataclass

from app.services.llm_service import review_code


@dataclass
class ReviewFile:
    """
    Represents a file that needs to be reviewed.
    """

    path: str
    diff: str


def prepare_review_files(
    file_diffs: list[dict],
) -> list[ReviewFile]:

    review_files = []

    for file in file_diffs:

        review_file = ReviewFile(
            path=file["path"],
            diff=file.get("patch", ""),
        )

        review_files.append(review_file)

    return review_files


def create_review_context(
    review_files: list[ReviewFile],
) -> str:

    sections = []

    for file in review_files:

        section = (
            f"FILE: {file.path}\n\n"
            f"STATUS: modified\n\n"
            "DIFF:\n"
            f"{file.diff}\n"
        )

        sections.append(section)

    return "\n\n".join(sections)


def generate_code_review(
    review_files: list[ReviewFile],
) -> dict:

    if not review_files:

        return {
            "summary": "No files available for review.",
            "issues": [],
        }

    review_context = create_review_context(
        review_files
    )

    return review_code(review_context)
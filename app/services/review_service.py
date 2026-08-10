from dataclasses import dataclass

from app.services.llm_service import review_code


@dataclass
class ReviewFile:
    """
    Represents a file that needs to be reviewed.
    """

    path: str
    content: str


def prepare_review_files(
    file_contents: dict[str, str],
) -> list[ReviewFile]:

    review_files = []

    for file_path, content in file_contents.items():

        review_file = ReviewFile(
            path=file_path,
            content=content,
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
            "```text\n"
            f"{file.content}\n"
            "```\n"
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
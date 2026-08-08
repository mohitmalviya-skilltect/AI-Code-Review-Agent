from dataclasses import dataclass


@dataclass
class ReviewFile:
    """
    Represents a file that needs to be reviewed.
    """

    path: str
    content: str


def prepare_review_files(file_contents: dict[str, str]) -> list[ReviewFile]:
    """
    Convert fetched GitHub files into ReviewFile objects.
    """

    review_files = []

    for file_path, content in file_contents.items():
        review_file = ReviewFile(
            path=file_path,
            content=content,
        )

        review_files.append(review_file)

    return review_files


def create_review_context(review_files: list[ReviewFile]) -> str:
    """
    Create formatted context that can later be sent to an LLM.
    """

    sections = []

    for file in review_files:
        section = (
            f"FILE: {file.path}\n\n"
            f"```text\n"
            f"{file.content}\n"
            f"```\n"
        )

        sections.append(section)

    return "\n\n".join(sections)
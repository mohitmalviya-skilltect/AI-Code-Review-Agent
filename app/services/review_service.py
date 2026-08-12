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

    all_issues = []
    failed_files = []

    for file in review_files:

        print("=" * 60)
        print(f"REVIEWING FILE: {file.path}")
        print("=" * 60)

        review_context = create_review_context(
            [file]
        )

        try:

            review_result = review_code(
                review_context
            )

            print(f"Review result for {file.path}:")
            print(review_result)

            # Check if AI review failed
            if review_result.get(
                "review_failed",
                False,
            ):

                failed_files.append(
                    file.path
                )

                continue

            issues = review_result.get(
                "issues",
                [],
            )

            all_issues.extend(
                issues
            )

        except Exception as error:

            print(
                f"Failed to review {file.path}: "
                f"{error}"
            )

            failed_files.append(
                file.path
            )

    # -----------------------------------------
    # Final review result
    # -----------------------------------------

    if failed_files:

        return {
            "summary": (
                f"AI reviewed "
                f"{len(review_files)} file(s), "
                f"but failed to review: "
                f"{', '.join(failed_files)}"
            ),
            "issues": all_issues,
            "review_failed": True,
            "failed_files": failed_files,
        }

    return {
        "summary": (
            f"AI reviewed "
            f"{len(review_files)} file(s)."
        ),
        "issues": all_issues,
    }
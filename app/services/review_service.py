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
    """
    Generate one combined AI code review for all files.

    Handles:
    - Empty review input
    - Successful Gemini review
    - Gemini quota/rate-limit errors
    - Gemini API errors
    - Invalid/failed AI responses
    """

    if not review_files:

        return {
            "summary": "No files available for review.",
            "issues": [],
            "review_failed": False,
        }

    print("=" * 60)
    print(
        f"REVIEWING {len(review_files)} FILE(S)"
    )
    print("=" * 60)

    # =====================================================
    # Create ONE combined context for ALL files
    # =====================================================

    review_context = create_review_context(
        review_files
    )

    print("=" * 60)
    print("SENDING ALL FILES TO GEMINI")
    print("=" * 60)

    try:

        review_result = review_code(
            review_context
        )

        print("=" * 60)
        print("GEMINI REVIEW RESULT")
        print("=" * 60)

        print(review_result)

        # =================================================
        # Validate Gemini response
        # =================================================

        if not isinstance(
            review_result,
            dict,
        ):

            print("=" * 60)
            print("INVALID GEMINI REVIEW RESULT")
            print("=" * 60)

            return {
                "summary": (
                    "AI reviewer returned "
                    "an invalid response."
                ),
                "issues": [],
                "review_failed": True,
                "error_type": "invalid_response",
            }

        # =================================================
        # Gemini reported its own failure
        # =================================================

        if review_result.get(
            "review_failed",
            False,
        ):

            print("=" * 60)
            print("GEMINI REVIEW FAILED")
            print("=" * 60)

            # Preserve the original error message
            # returned by llm_service.py.
            summary = review_result.get(
                "summary",
                "AI reviewer failed to complete the review.",
            )

            return {
                "summary": summary,
                "issues": [],
                "review_failed": True,
                "error_type": review_result.get(
                    "error_type",
                    "ai_review_failed",
                ),
            }

        # =================================================
        # Successful review
        # =================================================

        print("=" * 60)
        print("AI REVIEW COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return review_result

    except Exception as error:

        error_message = str(
            error
        )

        print("=" * 60)
        print("FAILED TO GENERATE AI REVIEW")
        print("=" * 60)

        print(
            error_message
        )

        # =================================================
        # Gemini quota / rate-limit handling
        # =================================================

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED"
            in error_message
            or "quota" in error_message.lower()
            or "rate limit"
            in error_message.lower()
        ):

            print("=" * 60)
            print("GEMINI QUOTA EXCEEDED")
            print("=" * 60)

            return {
                "summary": (
                    "Gemini API quota has been "
                    "exceeded. The AI review could "
                    "not be completed."
                ),
                "issues": [],
                "review_failed": True,
                "error_type": "quota_exceeded",
            }

        # =================================================
        # Authentication / API key errors
        # =================================================

        if (
            "401" in error_message
            or "403" in error_message
            or "API key" in error_message
            or "authentication"
            in error_message.lower()
        ):

            print("=" * 60)
            print("GEMINI AUTHENTICATION FAILED")
            print("=" * 60)

            return {
                "summary": (
                    "Gemini API authentication "
                    "failed. Please check the "
                    "GEMINI_API_KEY configuration."
                ),
                "issues": [],
                "review_failed": True,
                "error_type": "authentication_error",
            }

        # =================================================
        # Generic Gemini/API error
        # =================================================

        return {
            "summary": (
                "The AI reviewer could not "
                "complete the code review because "
                "of an API error."
            ),
            "issues": [],
            "review_failed": True,
            "error_type": "api_error",
        }
from dataclasses import dataclass

from app.services.llm_service import review_code
from app.services.secret_scanner import scan_files


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


def convert_secret_findings(
    secret_findings,
) -> list[dict]:
    """
    Convert SecretFinding objects into the same
    issue structure used by the AI review.
    """

    issues = []

    for finding in secret_findings:

        issues.append(
            {
                "file": finding.file,
                "severity": finding.severity,
                "category": finding.category,
                "line": finding.line,
                "problem": finding.message,
                "suggestion": (
                    f"Remove the {finding.secret_type} "
                    "from the source code. Store "
                    "credentials in environment variables "
                    "or a secure secret manager. "
                    "If the credential was already pushed, "
                    "rotate or revoke it immediately."
                ),
            }
        )

    return issues


def generate_code_review(
    review_files: list[ReviewFile],
) -> dict:
    """
    Generate a combined code review.

    Review consists of:
    1. Deterministic secret scanning
    2. Gemini AI code review

    Secret findings are generated locally and are
    never sent to Gemini.
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
    # 1. SECRET SCAN
    # =====================================================

    print("=" * 60)
    print("RUNNING SECRET SCANNER")
    print("=" * 60)

    try:

        secret_findings = scan_files(
            review_files
        )

        print(
            f"Secrets detected: "
            f"{len(secret_findings)}"
        )

    except Exception as error:

        print("=" * 60)
        print("SECRET SCANNER FAILED")
        print("=" * 60)

        print(error)

        secret_findings = []

    secret_issues = convert_secret_findings(
        secret_findings
    )

    # =====================================================
    # 2. CREATE GEMINI CONTEXT
    # =====================================================

    review_context = create_review_context(
        review_files
    )

    print("=" * 60)
    print("SENDING ALL FILES TO GEMINI")
    print("=" * 60)

    # =====================================================
    # 3. GEMINI REVIEW
    # =====================================================

    try:

        review_result = review_code(
            review_context
        )

        print("=" * 60)
        print("GEMINI REVIEW RESULT")
        print("=" * 60)

        print(review_result)

        # -------------------------------------------------
        # Validate Gemini response
        # -------------------------------------------------

        if not isinstance(
            review_result,
            dict,
        ):

            print("=" * 60)
            print("INVALID GEMINI REVIEW RESULT")
            print("=" * 60)

            # Secret findings can still be returned
            # even if Gemini fails.

            return {
                "summary": (
                    "AI reviewer returned "
                    "an invalid response."
                ),
                "issues": secret_issues,
                "review_failed": True,
                "error_type": "invalid_response",
            }

        # -------------------------------------------------
        # Gemini reported failure
        # -------------------------------------------------

        if review_result.get(
            "review_failed",
            False,
        ):

            print("=" * 60)
            print("GEMINI REVIEW FAILED")
            print("=" * 60)

            summary = review_result.get(
                "summary",
                "AI reviewer failed to complete the review.",
            )

            # IMPORTANT:
            # Secret scanner findings are still useful
            # even when Gemini is unavailable.

            return {
                "summary": summary,
                "issues": secret_issues,
                "review_failed": True,
                "error_type": review_result.get(
                    "error_type",
                    "ai_review_failed",
                ),
            }

        # =================================================
        # 4. COMBINE SECURITY + AI FINDINGS
        # =================================================

        ai_issues = review_result.get(
            "issues",
            [],
        )

        combined_issues = (
            secret_issues
            + ai_issues
        )

        # =================================================
        # 5. BUILD FINAL SUMMARY
        # =================================================

        ai_summary = review_result.get(
            "summary",
            "AI review completed.",
        )

        if secret_issues:

            secret_summary = (
                f"Detected "
                f"{len(secret_issues)} "
                f"potential secret(s)."
            )

            final_summary = (
                f"{secret_summary} "
                f"{ai_summary}"
            )

        else:

            final_summary = ai_summary

        print("=" * 60)
        print("COMBINED CODE REVIEW")
        print("=" * 60)

        print(
            f"Secret findings: "
            f"{len(secret_issues)}"
        )

        print(
            f"AI findings: "
            f"{len(ai_issues)}"
        )

        print(
            f"Total findings: "
            f"{len(combined_issues)}"
        )

        return {
            "summary": final_summary,
            "issues": combined_issues,
            "review_failed": False,
        }

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

        # -------------------------------------------------
        # Gemini quota/rate-limit error
        # -------------------------------------------------

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED"
            in error_message
            or "quota"
            in error_message.lower()
            or "rate limit"
            in error_message.lower()
        ):

            return {
                "summary": (
                    "Gemini API quota has been "
                    "exceeded. The AI review could "
                    "not be completed."
                ),
                "issues": secret_issues,
                "review_failed": True,
                "error_type": "quota_exceeded",
            }

        # -------------------------------------------------
        # Authentication error
        # -------------------------------------------------

        if (
            "401" in error_message
            or "403" in error_message
            or "API key" in error_message
            or "authentication"
            in error_message.lower()
        ):

            return {
                "summary": (
                    "Gemini API authentication "
                    "failed. Please check the "
                    "GEMINI_API_KEY configuration."
                ),
                "issues": secret_issues,
                "review_failed": True,
                "error_type": "authentication_error",
            }

        # -------------------------------------------------
        # Generic API error
        # -------------------------------------------------

        return {
            "summary": (
                "The AI reviewer could not "
                "complete the code review because "
                "of an API error."
            ),
            "issues": secret_issues,
            "review_failed": True,
            "error_type": "api_error",
        }
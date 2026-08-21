from unittest.mock import patch

from app.services.review_service import (
    ReviewFile,
    generate_code_review,
)


def test_secret_finding_survives_gemini_failure():

    review_files = [
        ReviewFile(
            path="config.py",
            diff="""@@ -1,1 +1,2 @@
 import os
+GEMINI_API_KEY = "AIza12345678901234567890"
""",
        )
    ]

    # Simulate Gemini failure
    with patch(
        "app.services.review_service.review_code"
    ) as mock_review:

        mock_review.return_value = {
            "summary": (
                "Gemini API quota exceeded."
            ),
            "issues": [],
            "review_failed": True,
            "error_type": "quota_exceeded",
        }

        result = generate_code_review(
            review_files
        )

    # Gemini should be marked as failed
    assert result["review_failed"] is True

    # Secret scanner should still detect the key
    assert len(result["issues"]) == 1

    issue = result["issues"][0]

    assert issue["file"] == "config.py"
    assert issue["line"] == 2
    assert issue["severity"] == "critical"
    assert issue["category"] == "security"


def test_review_response_categories():
    """
    Verify that ReviewIssue schema validates the specified categories and excludes reliability.
    """
    from app.models.schemas import ReviewIssue
    import pytest
    from pydantic import ValidationError

    # Valid category
    issue = ReviewIssue(
        file="main.py",
        line=10,
        severity="high",
        category="bug",
        problem="Division by zero",
        suggestion="Check denominator",
    )
    assert issue.category == "bug"

    # Invalid category (reliability) should raise ValidationError
    with pytest.raises(ValidationError):
        ReviewIssue(
            file="main.py",
            line=10,
            severity="high",
            category="reliability",
            problem="Issue description",
            suggestion="Fix suggestion",
        )
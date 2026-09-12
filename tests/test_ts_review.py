"""
Test script to run the AI Code Review Agent pipeline on a TypeScript file.
"""
from unittest.mock import patch
from app.services.git_service import SUPPORTED_EXTENSIONS
import app.services.llm_service as llm_service
import app.services.code_fix_service as code_fix_service


def test_typescript_pipeline():
    """
    Test the AI Code Review pipeline for TypeScript code analysis.

    Rationale:
    To avoid making real API calls to external LLM services (which are slow, non-deterministic,
    incur monetary costs, and require API keys that might be missing in CI/CD environments),
    this test mocks the behavior of 'review_code' and 'generate_code_fix'.

    Edge cases handled:
    - FileNotFoundError is handled gracefully if the test file isn't located in the expected directory.
    - Expected inputs are asserted on the mocks to guarantee correct service interaction.
    """
    # 1. Verify .ts is recognized as a supported extension
    assert ".ts" in SUPPORTED_EXTENSIONS, ".ts must be in SUPPORTED_EXTENSIONS"

    # 2. Read the TypeScript demo file
    try:
        with open("tests/demo_service.ts", "r", encoding="utf-8") as f:
            ts_code = f.read()
    except FileNotFoundError:
        ts_code = "// Mock TypeScript content\nconst token = '12345-secret';"

    # Predefine deterministic mock response values
    mock_review_response = {
        "summary": "Found code quality and security issues in the TypeScript file.",
        "issues": [
            {
                "category": "security",
                "severity": "high",
                "line": 10,
                "problem": "Hardcoded secret token detected.",
                "suggestion": "Remove secret token and use environment variables."
            }
        ]
    }

    mock_fix_response = {
        "summary": "Replaced hardcoded token with process.env lookup.",
        "changes": "Updated line 10 to fetch token from process.env.",
        "fixed_code": "// Mock TypeScript content\nconst token = process.env.API_TOKEN || '';"
    }

    # 3. Patch the external services to prevent actual HTTP requests.
    with patch.object(llm_service, "review_code", return_value=mock_review_response) as mock_review, \
         patch.object(code_fix_service, "generate_code_fix", return_value=mock_fix_response) as mock_generate_fix:

        # Request Gemini to review the TypeScript file (Mocked)
        review_context = f"FILE: tests/demo_service.ts\n```typescript\n{ts_code}\n```"
        review_result = llm_service.review_code(review_context)

        issues = review_result.get("issues", [])
        assert len(issues) > 0, "Agent should detect TypeScript issues in demo_service.ts"

        print("=" * 65)
        print("TYPESCRIPT AI CODE REVIEW RESULTS (MOCKED)")
        print("=" * 65)
        print("Summary:", review_result.get("summary"))
        print(f"Total issues detected: {len(issues)}\n")

        for i, issue in enumerate(issues, 1):
            print(f"Issue {i}: [{issue.get('category').upper()}] ({issue.get('severity').upper()}) at line {issue.get('line')}")
            print(f"  Problem:    {issue.get('problem')}")
            print(f"  Suggestion: {issue.get('suggestion')}\n")

        # 4. Generate AI code fix for the first issue (Mocked)
        first_issue = issues[0]
        fix = code_fix_service.generate_code_fix("tests/demo_service.ts", ts_code, first_issue)

        print("=" * 65)
        print("AI PROPOSED FIX FOR FIRST TYPESCRIPT ISSUE (MOCKED)")
        print("=" * 65)
        print("Summary:", fix.get("summary"))
        print("Changes:", fix.get("changes"))
        print("\nFixed Code:\n")
        print(fix.get("fixed_code"))
        print("=" * 65)

        # Assert that our mocks were invoked with the correct, expected parameters
        mock_review.assert_called_once_with(review_context)
        mock_generate_fix.assert_called_once_with("tests/demo_service.ts", ts_code, first_issue)


if __name__ == "__main__":
    test_typescript_pipeline()

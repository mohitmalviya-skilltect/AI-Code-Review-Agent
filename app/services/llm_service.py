import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.models.schemas import ReviewResponse


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set in the .env file"
    )


client = genai.Client(
    api_key=api_key
)


def review_code(review_context: str) -> dict:
    """
    Send code to Gemini and return a structured code review.
    """

    prompt = f"""
Perform a comprehensive code review.

Review the changes systematically across ALL applicable categories:

Determine the file type from the file extension or filename and apply relevant specialized checks.

For Python files:
- Logic and runtime errors
- Exception handling
- Security issues
- Performance
- Maintainability
- Python best practices

For TypeScript/JavaScript files:
- Type safety
- Runtime errors
- Async/await issues
- Security
- Performance
- Maintainability

For Terraform files:
- Publicly exposed resources
- IAM and permission issues
- Missing encryption
- Insecure network rules
- Hardcoded secrets
- Unsafe defaults
- Resource configuration issues
- Terraform best practices

For Dockerfiles:
- Running as root
- Hardcoded secrets
- Untrusted or unpinned base images
- Unnecessary packages
- Image size optimization
- Layer optimization
- Missing cleanup
- Docker security best practices

For JSON/YAML configuration:
- Invalid or risky configuration
- Hardcoded secrets
- Security-sensitive settings
- Incorrect or suspicious values
- Maintainability issues

For shell scripts:
- Unsafe commands
- Missing error handling
- Injection risks
- Permission issues
- Reliability problems

Only apply specialized checks that are relevant to the detected file type.

IMPORTANT REVIEW RULES:

- Review ALL changed lines.
- Do not stop after finding the first issue.
- Identify every meaningful issue you can confidently find.
- Check each applicable review category before producing the final response.
- Do not report duplicate issues.
- Do not invent or speculate about problems.
- Do not report issues unrelated to the changed code.
- Prefer specific, actionable suggestions.
- If a category has no issues, continue checking the remaining categories.

Look for:

1. Bugs and logical errors
2. Security vulnerabilities
3. Performance problems
4. Code quality and maintainability
5. Error handling
6. Best practices
7. Configuration issues
8. Dependency issues
9. Reliability issues

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "Short overall summary",
    "issues": [
        {{
            "file": "path/to/file.py",
            "severity": "critical|high|medium|low",
            "category": "bug|security|performance|quality|maintainability",
            "line": 1,
            "problem": "Explain the problem",
            "suggestion": "Explain how to fix it"
        }}
    ]
}}

Rules:

- Do not use Markdown.
- Do not add text before or after the JSON.
- If there are no issues, return an empty issues array.
- The line number should be the approximate line where the issue occurs.
- Only report meaningful issues.
- Do not invent problems.
- Review every file provided.

Code to review:

{review_context}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    response_text = response.text or ""

    response_text = response_text.strip()

    # -----------------------------------------
    # Remove Markdown code fences if present
    # -----------------------------------------

    if response_text.startswith("```"):

        response_text = response_text.replace(
            "```json",
            "",
        )

        response_text = response_text.replace(
            "```",
            "",
        )

        response_text = response_text.strip()

    # -----------------------------------------
    # Parse and validate Gemini response
    # -----------------------------------------

    try:

        review_data = json.loads(
            response_text
        )

        validated_review = (
            ReviewResponse.model_validate(
                review_data
            )
        )

        return validated_review.model_dump()

    except json.JSONDecodeError:

        print("=" * 60)
        print("INVALID JSON FROM GEMINI")
        print("=" * 60)

        print("RAW GEMINI RESPONSE:")
        print(repr(response_text))

        print("=" * 60)

        # -----------------------------------------
        # Attempt JSON recovery
        # -----------------------------------------

        try:

            start = response_text.find("{")

            if start != -1:

                possible_json = (
                    response_text[start:]
                )

                # Remove trailing characters
                # until valid JSON is found.

                while possible_json:

                    try:

                        recovered_data = json.loads(
                            possible_json
                        )

                        # Validate recovered JSON
                        validated_review = (
                            ReviewResponse.model_validate(
                                recovered_data
                            )
                        )

                        print(
                            "JSON RECOVERY SUCCESSFUL"
                        )

                        return (
                            validated_review.model_dump()
                        )

                    except json.JSONDecodeError:

                        possible_json = (
                            possible_json[:-1]
                            .rstrip()
                        )

                    except Exception as validation_error:

                        print(
                            "RECOVERED JSON FAILED "
                            "VALIDATION"
                        )

                        print(
                            validation_error
                        )

                        break

        except Exception as recovery_error:

            print(
                "JSON recovery failed:"
            )

            print(
                recovery_error
            )

        return {
            "summary": (
                "AI review failed because "
                "Gemini returned an invalid response."
            ),
            "issues": [],
            "review_failed": True,
        }

    except Exception as e:

        print("=" * 60)
        print("AI REVIEW VALIDATION FAILED")
        print("=" * 60)

        print(e)

        print("=" * 60)

        return {
            "summary": (
                "AI review failed during "
                "response validation."
            ),
            "issues": [],
            "review_failed": True,
        }
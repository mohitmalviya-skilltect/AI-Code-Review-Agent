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

Your primary focus is to identify and report issues in the following core areas:
1. **Security & Vulnerabilities** (Assign `security` category)
2. **Performance Bottlenecks** (Assign `performance` category)
3. **Syntax Errors & Logic Bugs** (Assign `bug` category)
4. **Detailed Comments & Code Quality** (Assign `quality` or `maintainability` category)

Verify the changes systematically across all files. For each file type, make sure you:
- Inspect Python, JS/TS, Shell, and configuration files for security vulnerabilities, hardcoded secrets, and unsafe execution models.
- Inspect loops, API/database queries, and resource usage for performance inefficiencies.
- Inspect syntax, imports, error handlers, and logic paths for bugs or syntax errors.
- Ensure that the suggestions and explanations you write are clear, precise, and highly detailed.
- Check if the code itself lacks necessary documentation/comments, or contains outdated/misleading comments.

IMPORTANT REVIEW RULES:
- Review ALL changed lines.
- Do not stop after finding the first issue; report all findings.
- Check each applicable review category before producing the final response.
- Do not report duplicate issues.
- Do not invent or speculate about problems. Only report realistic, meaningful issues.
- Do not report issues unrelated to the changed code.
- Prefer specific, actionable suggestions. Write DETAILED, descriptive comments for the suggestions and problems.
- If a category has no issues, continue checking the remaining categories.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "Short overall summary focusing on the main findings around security, performance, syntax, and comment quality.",
    "issues": [
        {{
            "file": "path/to/file.py",
            "severity": "critical|high|medium|low",
            "category": "bug|security|performance|quality|maintainability",
            "line": 1,
            "problem": "Detailed explanation of the issue, vulnerability, error, performance bottleneck, or documentation/comment gap.",
            "suggestion": "Detailed step-by-step description of how to resolve the issue with clear recommendations."
        }}
    ]
}}

Rules:
- Do not use Markdown.
- Do not add text before or after the JSON.
- The category field MUST strictly be one of: bug, security, performance, quality, maintainability. DO NOT output category values like reliability, correctness, architecture, style, or testing.
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
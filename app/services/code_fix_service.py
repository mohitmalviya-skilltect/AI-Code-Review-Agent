import json
import re

from app.services.llm_service import client


def generate_code_fix(
    file_path: str,
    original_code: str,
    issue: dict,
) -> dict:
    """
    Generate a proposed code fix for a specific issue.

    This function does NOT modify GitHub or the local repository.
    It only asks Gemini to return the proposed corrected code.
    """

    problem = issue.get(
        "problem",
        "No problem description provided.",
    )

    suggestion = issue.get(
        "suggestion",
        "No suggestion provided.",
    )

    line = issue.get(
        "line",
        "unknown",
    )

    prompt = f"""
You are an expert software engineer.

You are reviewing a Pull Request and need to propose a safe
code fix for one identified issue.

IMPORTANT RULES:

1. Do NOT invent unrelated changes.
2. Fix ONLY the identified issue.
3. Preserve the existing functionality.
4. Preserve the existing coding style where possible.
5. Do not add secrets, API keys, passwords, tokens, or credentials.
6. Do not modify unrelated code.
7. Return the complete corrected file.
8. Do not use Markdown code fences.
9. Return ONLY valid JSON.

FILE:
{file_path}

PROBLEM LINE:
{line}

PROBLEM:
{problem}

SUGGESTION:
{suggestion}

ORIGINAL CODE:
{original_code}

Return exactly this JSON structure:

{{
    "file": "{file_path}",
    "summary": "Short explanation of the proposed fix",
    "changes": [
        "Describe what was changed"
    ],
    "fixed_code": "Complete corrected file content"
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )

        response_text = response.text.strip()

        # -----------------------------------------
        # Remove accidental Markdown fences
        # -----------------------------------------

        response_text = re.sub(
            r"^```json\s*",
            "",
            response_text,
            flags=re.IGNORECASE,
        )

        response_text = re.sub(
            r"\s*```$",
            "",
            response_text,
        )

        result = json.loads(
            response_text
        )

        # -----------------------------------------
        # Validate required fields
        # -----------------------------------------

        if not isinstance(result, dict):
            raise ValueError(
                "Gemini returned an invalid fix response."
            )

        required_fields = [
            "file",
            "summary",
            "changes",
            "fixed_code",
        ]

        for field in required_fields:

            if field not in result:
                raise ValueError(
                    f"Missing field in AI fix response: {field}"
                )

        if not isinstance(
            result["changes"],
            list,
        ):
            raise ValueError(
                "AI fix 'changes' must be a list."
            )

        if not isinstance(
            result["fixed_code"],
            str,
        ):
            raise ValueError(
                "AI fix 'fixed_code' must be a string."
            )

        return {
            "file": result["file"],
            "summary": result["summary"],
            "changes": result["changes"],
            "fixed_code": result["fixed_code"],
        }

    except json.JSONDecodeError as error:

        print("=" * 60)
        print("AI CODE FIX JSON ERROR")
        print("=" * 60)

        print(
            "Gemini returned invalid JSON."
        )

        print(
            f"Error: {error}"
        )

        print("=" * 60)

        raise ValueError(
            "Gemini returned invalid JSON for the proposed fix."
        ) from error

    except Exception as error:

        print("=" * 60)
        print("AI CODE FIX FAILED")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        print("=" * 60)

        raise
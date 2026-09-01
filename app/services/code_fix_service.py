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
You are an expert software engineer and code reviewer.

You are reviewing a Pull Request and need to propose a safe, high-quality code fix for an identified issue.

CRITICAL INSTRUCTIONS FOR CODE COMMENTS & DOCUMENTATION:
1. You MUST add clear, detailed, and professional docstrings and inline explanatory comments directly inside `fixed_code`.
2. Explain the purpose of the function, the rationale behind the fix, condition checks, and how edge cases are handled.
3. Use the appropriate comment syntax for the language (e.g. Python docstrings `\"\"\"...\"\"\"` and `# comments`, or `// comments` for JS/TS/Go).

IMPORTANT RULES:
4. Fix ONLY the identified issue while preserving existing intended functionality.
5. Do NOT invent unrelated changes or modify unrelated code.
6. Preserve clean coding standards and style.
7. Do not add secrets, API keys, passwords, tokens, or credentials.
8. Return the complete corrected file in `fixed_code` with all detailed comments included.
9. Do not use Markdown code fences.
10. Return ONLY valid JSON matching the exact schema below.

FILE:
{file_path}

PROBLEM LINE:
{line}

ISSUE SEVERITY & CATEGORY:
{issue.get("severity", "medium").upper()} - {issue.get("category", "quality")}

PROBLEM:
{problem}

SUGGESTION:
{suggestion}

ORIGINAL CODE:
{original_code}

Return exactly this JSON structure:

{{
    "file": "{file_path}",
    "summary": "Detailed explanation of the proposed fix and why it solves the issue",
    "changes": [
        "Detailed description of change 1",
        "Detailed description of change 2"
    ],
    "fixed_code": "Complete corrected file content with detailed docstrings and inline comments"
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
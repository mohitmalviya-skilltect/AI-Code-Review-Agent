import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file")


client = genai.Client(api_key=api_key)


def review_code(review_context: str) -> dict:
    """
    Send code to Gemini and return a structured code review.
    """

    prompt = f"""
You are an expert software code reviewer.

Review the following source code carefully.

Look for:

1. Bugs and logical errors
2. Security vulnerabilities
3. Performance problems
4. Bad coding practices
5. Maintainability issues
6. Error handling problems
7. Potential improvements

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

    # Remove Markdown code fences if Gemini adds them.
    response_text = response_text.strip()

    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "")
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

    try:
        return json.loads(response_text)

    except json.JSONDecodeError:

        return {
            "summary": "Gemini returned an invalid JSON response.",
            "issues": [],
            "raw_response": response_text,
        }
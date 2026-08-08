import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file")


client = genai.Client(api_key=api_key)


def review_code(review_context: str) -> str:
    """
    Send code to Gemini and return the code review.
    """

    prompt = f"""
You are an expert software code reviewer.

Review the following code carefully.

Look for:

1. Bugs and logical errors
2. Security vulnerabilities
3. Performance problems
4. Bad coding practices
5. Maintainability issues
6. Error handling problems
7. Potential improvements

For every important issue, explain:

- Severity
- File
- Problem
- Why it is a problem
- Suggested fix

If the code is good, mention the good practices you found.

Code to review:

{review_context}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text or ""
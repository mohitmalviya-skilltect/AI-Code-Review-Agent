from app.services.llm_service import review_code


code = (
    "def calculate_total(price, quantity):\n"
    "    total = price * quantity\n"
    "    return total\n"
)


review_context = (
    "FILE: test.py\n\n"
    "```python\n"
    f"{code}\n"
    "```\n"
)


result = review_code(review_context)


print("=" * 60)
print("STRUCTURED AI REVIEW")
print("=" * 60)
print(result)
from unittest.mock import patch

from app.services.llm_service import review_code


def test_review_code_success():

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

    with patch(
        "app.services.llm_service.client.models.generate_content"
    ) as mock_generate:

        mock_generate.return_value.text = (
            '{"summary": "Code looks good.", '
            '"issues": []}'
        )

        result = review_code(
            review_context
        )

    assert isinstance(
        result,
        dict,
    )

    assert result["summary"] == (
        "Code looks good."
    )

    assert result["issues"] == []
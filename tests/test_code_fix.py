from app.services.code_fix_service import generate_code_fix


def test_generate_code_fix():

    original_code = """def calculate_average(numbers):
    total = 0

    for number in numbers:
        total += number

    average = total / 0

    return Avg
"""

    issue = {
        "file": "tests/test_review.py",
        "line": 8,
        "severity": "critical",
        "category": "bug",
        "problem": (
            "The expression 'total / 0' will always "
            "trigger a ZeroDivisionError."
        ),
        "suggestion": (
            "Divide by the length of the list and "
            "handle an empty list."
        ),
    }

    result = generate_code_fix(
        file_path="tests/test_review.py",
        original_code=original_code,
        issue=issue,
    )

    assert isinstance(
        result,
        dict,
    )

    assert "file" in result
    assert "summary" in result
    assert "changes" in result
    assert "fixed_code" in result

    assert isinstance(
        result["fixed_code"],
        str,
    )

    assert result["fixed_code"].strip() != ""

    print("=" * 60)
    print("PROPOSED AI FIX")
    print("=" * 60)
    print(result)
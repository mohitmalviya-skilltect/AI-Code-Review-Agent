from app.services.approval_service import (
    create_approval_request,
    get_approval_request,
    approve_request,
    cancel_request,
    is_approved,
)


def test_create_approval_request():

    proposed_fixes = [
        {
            "file": "tests/test_review.py",
            "summary": "Fix division by zero.",
            "changes": [
                "Replace division by zero with len(numbers)."
            ],
            "fixed_code": (
                "def calculate_average(numbers):\n"
                "    return sum(numbers) / len(numbers)\n"
            ),
        }
    ]

    result = create_approval_request(
        owner="mohitmalviya-skilltect",
        repository="AI-Code-Review-Agent",
        pull_request_number=10,
        commit_sha="abc123",
        proposed_fixes=proposed_fixes,
    )

    assert isinstance(
        result,
        dict,
    )

    assert result["owner"] == (
        "mohitmalviya-skilltect"
    )

    assert result["repository"] == (
        "AI-Code-Review-Agent"
    )

    assert result["pull_request_number"] == 10

    assert result["commit_sha"] == "abc123"

    assert result["status"] == "pending"

    assert result["approved_at"] is None

    assert len(
        result["proposed_fixes"]
    ) == 1

    assert result["approval_id"]


def test_get_approval_request():

    proposed_fixes = [
        {
            "file": "test.py",
            "summary": "Fix bug.",
            "changes": [
                "Fix the calculation."
            ],
            "fixed_code": "print('fixed')",
        }
    ]

    created = create_approval_request(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=1,
        commit_sha="sha123",
        proposed_fixes=proposed_fixes,
    )

    approval_id = created[
        "approval_id"
    ]

    result = get_approval_request(
        approval_id
    )

    assert result is not None

    assert result[
        "approval_id"
    ] == approval_id

    assert result[
        "status"
    ] == "pending"


def test_approve_request():

    proposed_fixes = [
        {
            "file": "test.py",
            "summary": "Fix bug.",
            "changes": [
                "Fix the bug."
            ],
            "fixed_code": "print('fixed')",
        }
    ]

    created = create_approval_request(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=2,
        commit_sha="sha456",
        proposed_fixes=proposed_fixes,
    )

    approval_id = created[
        "approval_id"
    ]

    assert is_approved(
        approval_id
    ) is False

    approved = approve_request(
        approval_id
    )

    assert approved[
        "status"
    ] == "approved"

    assert approved[
        "approved_at"
    ] is not None

    assert is_approved(
        approval_id
    ) is True


def test_cancel_request():

    proposed_fixes = [
        {
            "file": "test.py",
            "summary": "Fix bug.",
            "changes": [
                "Fix the bug."
            ],
            "fixed_code": "print('fixed')",
        }
    ]

    created = create_approval_request(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=3,
        commit_sha="sha789",
        proposed_fixes=proposed_fixes,
    )

    approval_id = created[
        "approval_id"
    ]

    cancelled = cancel_request(
        approval_id
    )

    assert cancelled[
        "status"
    ] == "cancelled"

    assert is_approved(
        approval_id
    ) is False
import pytest

from app.services.approval_service import (
    create_approval_request,
    approve_request,
)

from app.services.code_apply_service import (
    get_approved_changes,
)


def create_test_request():

    proposed_fixes = [
        {
            "file": "tests/test_review.py",
            "summary": "Fix division by zero.",
            "changes": [
                "Use len(numbers) instead of 0."
            ],
            "fixed_code": (
                "average = total / len(numbers)"
            ),
        }
    ]

    return create_approval_request(
        owner="test-owner",
        repository="test-repository",
        pull_request_number=10,
        commit_sha="abc123",
        proposed_fixes=proposed_fixes,
    )


# =========================================================
# Pending request must be rejected
# =========================================================

def test_pending_request_cannot_be_applied():

    approval = create_test_request()

    approval_id = approval[
        "approval_id"
    ]

    with pytest.raises(
        PermissionError
    ):

        get_approved_changes(
            approval_id
        )


# =========================================================
# Approved request can be retrieved
# =========================================================

def test_approved_request_can_be_applied():

    approval = create_test_request()

    approval_id = approval[
        "approval_id"
    ]

    approve_request(
        approval_id
    )

    result = get_approved_changes(
        approval_id
    )

    assert result[
        "approval_id"
    ] == approval_id

    assert result[
        "status"
    ] == "approved"

    assert result[
        "owner"
    ] == "test-owner"

    assert result[
        "repository"
    ] == "test-repository"

    assert result[
        "pull_request_number"
    ] == 10

    assert result[
        "commit_sha"
    ] == "abc123"

    assert len(
        result[
            "proposed_fixes"
        ]
    ) == 1


# =========================================================
# Invalid approval ID
# =========================================================

def test_invalid_approval_id():

    with pytest.raises(
        ValueError
    ):

        get_approved_changes(
            "does-not-exist"
        )
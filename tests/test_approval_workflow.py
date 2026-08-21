from unittest.mock import patch

from app.services.approval_workflow_service import (
    create_approval_workflow,
)


@patch(
    "app.services.approval_workflow_service.send_approval_email"
)
@patch(
    "app.services.approval_workflow_service.create_approval_request"
)
def test_create_approval_workflow(
    mock_create_approval,
    mock_send_email,
):

    # -------------------------------------------------
    # Mock approval request
    # -------------------------------------------------

    mock_create_approval.return_value = {
        "approval_id": "approval-123",
        "status": "pending",
        "owner": "test-owner",
        "repository": "test-repo",
        "pull_request_number": 10,
        "commit_sha": "abc123",
        "proposed_fixes": [
            {
                "file": "test.py",
                "summary": "Fix bug.",
            }
        ],
    }

    # -------------------------------------------------
    # Mock email
    # -------------------------------------------------

    mock_send_email.return_value = True

    proposed_fixes = [
        {
            "file": "test.py",
            "summary": "Fix division by zero.",
            "changes": [
                "Replace division by zero."
            ],
            "fixed_code": (
                "return sum(numbers) / len(numbers)"
            ),
        }
    ]

    # -------------------------------------------------
    # Run workflow
    # -------------------------------------------------

    result = create_approval_workflow(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=10,
        commit_sha="abc123",
        proposed_fixes=proposed_fixes,
        recipient_email="developer@example.com",
    )

    # -------------------------------------------------
    # Assertions
    # -------------------------------------------------

    assert result[
        "approval_id"
    ] == "approval-123"

    assert result[
        "status"
    ] == "pending"

    assert result[
        "email_sent"
    ] is True

    assert result[
        "pull_request_number"
    ] == 10

    assert result[
        "commit_sha"
    ] == "abc123"

    assert result[
        "proposed_fix_count"
    ] == 1

    # -------------------------------------------------
    # Verify approval service was called
    # -------------------------------------------------

    mock_create_approval.assert_called_once_with(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=10,
        commit_sha="abc123",
        proposed_fixes=proposed_fixes,
    )

    # -------------------------------------------------
    # Verify email service was called
    # -------------------------------------------------

    mock_send_email.assert_called_once_with(
        recipient_email="developer@example.com",
        approval_id="approval-123",
        owner="test-owner",
        repository="test-repo",
        pull_request_number=10,
        proposed_fix_count=1,
    )
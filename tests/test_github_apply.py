from unittest.mock import patch

import pytest

from app.services.github_apply_service import (
    apply_approved_changes,
)


@patch(
    "app.services.github_apply_service.get_approved_changes"
)
@patch(
    "app.services.github_apply_service.get_pull_request_branch"
)
@patch(
    "app.services.github_apply_service.apply_file_change"
)
def test_apply_approved_changes(
    mock_apply_file,
    mock_get_branch,
    mock_get_approved,
):

    mock_get_approved.return_value = {
        "approval_id": "approval-123",
        "status": "approved",
        "owner": "test-owner",
        "repository": "test-repo",
        "pull_request_number": 10,
        "commit_sha": "abc123",
        "proposed_fixes": [
            {
                "file": "tests/test_review.py",
                "fixed_code": (
                    "def calculate_average(numbers):\n"
                    "    return sum(numbers) / len(numbers)\n"
                ),
            }
        ],
    }

    mock_get_branch.return_value = (
        "developer-feature"
    )

    mock_apply_file.return_value = {
        "commit": {
            "sha": "new-commit-123"
        }
    }

    result = apply_approved_changes(
        "approval-123"
    )

    assert result[
        "approval_id"
    ] == "approval-123"

    assert result[
        "status"
    ] == "applied"

    assert result[
        "branch"
    ] == "developer-feature"

    assert result[
        "pull_request_number"
    ] == 10

    assert len(
        result["changes"]
    ) == 1

    mock_get_approved.assert_called_once_with(
        "approval-123"
    )

    mock_get_branch.assert_called_once_with(
        owner="test-owner",
        repository="test-repo",
        pull_request_number=10,
    )

    mock_apply_file.assert_called_once()

@patch(
    "app.services.github_apply_service.get_approved_changes"
)
@patch(
    "app.services.github_apply_service.get_pull_request_branch"
)
def test_unapproved_request_does_not_modify_github(
    mock_get_branch,
    mock_get_approved,
):

    mock_get_approved.side_effect = (
        PermissionError(
            "Code changes cannot be applied."
        )
    )

    with pytest.raises(
        PermissionError
    ):
        apply_approved_changes(
            "pending-approval"
        )

    mock_get_branch.assert_not_called()
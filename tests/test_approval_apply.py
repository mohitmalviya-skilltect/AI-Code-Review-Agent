import pytest

from app.services.approval_service import (
    create_approval_request,
)

from fastapi import Request, HTTPException
from app.api.approval import (
    approve_changes,
)


# =========================================================
# Test data
# =========================================================

def create_test_approval():

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
# Pending request should call GitHub apply
# =========================================================

def test_approve_changes_applies_github_changes(
    monkeypatch,
):

    approval = create_test_approval()

    approval_id = approval[
        "approval_id"
    ]

    # -----------------------------------------
    # Mock GitHub apply operation
    # -----------------------------------------

    def mock_apply_approved_changes(
        received_approval_id=None,
        *args,
        **kwargs,
    ):

        target = received_approval_id or kwargs.get("approval_id")
        assert (
            target
            == approval_id
        )

        return {
            "approval_id": approval_id,
            "status": "applied",
            "branch": "feature/test",
            "changes": [
                {
                    "file": "tests/test_review.py",
                    "branch": "feature/test",
                    "commit": {
                        "sha": "fake-commit-sha"
                    },
                }
            ],
        }

    monkeypatch.setattr(
        "app.api.approval.apply_approved_changes",
        mock_apply_approved_changes,
    )

    # -----------------------------------------
    # Approve
    # -----------------------------------------

    from unittest.mock import AsyncMock, MagicMock
    mock_req = MagicMock(spec=Request)
    mock_form_data = MagicMock()
    mock_form_data.getlist.return_value = []
    mock_req.form = AsyncMock(return_value=mock_form_data)

    import asyncio
    result = asyncio.run(approve_changes(approval_id, mock_req))

    # -----------------------------------------
    # Verify response
    # -----------------------------------------

    assert result[
        "approval_id"
    ] == approval_id

    assert result[
        "status"
    ] == "applied"

    assert result[
        "result"
    ]["status"] == "applied"


# =========================================================
# GitHub failure should NOT mark request as applied
# =========================================================

def test_github_apply_failure_keeps_request_approved(
    monkeypatch,
):

    approval = create_test_approval()

    approval_id = approval[
        "approval_id"
    ]

    # -----------------------------------------
    # Mock GitHub failure
    # -----------------------------------------

    def mock_apply_failure(
        received_approval_id,
    ):

        raise RuntimeError(
            "GitHub API failed"
        )

    monkeypatch.setattr(
        "app.api.approval.apply_approved_changes",
        mock_apply_failure,
    )

    from unittest.mock import AsyncMock, MagicMock
    mock_req = MagicMock(spec=Request)
    mock_form_data = MagicMock()
    mock_form_data.getlist.return_value = []
    mock_req.form = AsyncMock(return_value=mock_form_data)

    import asyncio
    with pytest.raises(
        HTTPException
    ) as exc_info:

        asyncio.run(approve_changes(approval_id, mock_req))

    assert (
        exc_info.value.status_code
        == 500
    )

    # -----------------------------------------
    # Approval must remain approved
    # -----------------------------------------

    from app.services.approval_service import (
        get_approval_request,
    )

    request = get_approval_request(
        approval_id
    )

    assert request[
        "status"
    ] == "approved"


# =========================================================
# Already applied request should not apply again
# =========================================================

def test_already_applied_request(
    monkeypatch,
):

    approval = create_test_approval()

    approval_id = approval[
        "approval_id"
    ]

    # Manually mark as applied
    approval[
        "status"
    ] = "applied"

    # -----------------------------------------
    # GitHub apply must NOT be called
    # -----------------------------------------

    def mock_apply(
        received_approval_id,
    ):

        raise AssertionError(
            "GitHub apply should not be called "
            "for an already applied request."
        )

    monkeypatch.setattr(
        "app.api.approval.apply_approved_changes",
        mock_apply,
    )

    # -----------------------------------------
    # Call endpoint
    # -----------------------------------------

    from unittest.mock import AsyncMock, MagicMock
    mock_req = MagicMock(spec=Request)
    mock_form_data = MagicMock()
    mock_form_data.getlist.return_value = []
    mock_req.form = AsyncMock(return_value=mock_form_data)

    import asyncio
    result = asyncio.run(approve_changes(approval_id, mock_req))

    assert result[
        "approval_id"
    ] == approval_id

    assert result[
        "status"
    ] == "applied"
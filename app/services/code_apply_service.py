from typing import Any

from app.services.approval_service import (
    get_approval_request,
)


# =========================================================
# Get Approved Changes
# =========================================================

def get_approved_changes(
    approval_id: str,
) -> dict[str, Any]:
    """
    Retrieve code changes only when the user has approved
    the corresponding approval request.

    IMPORTANT:
    This function does NOT modify GitHub.

    It acts as the safety gate before code application.
    """

    # -----------------------------------------------------
    # Get approval request
    # -----------------------------------------------------

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:
        raise ValueError(
            "Approval request not found."
        )

    # -----------------------------------------------------
    # Check approval status
    # -----------------------------------------------------

    status = approval_request.get(
        "status"
    )

    if status != "approved":

        raise PermissionError(
            "Code changes cannot be applied "
            "because the approval request has "
            f"status: {status}"
        )

    # -----------------------------------------------------
    # Get proposed fixes
    # -----------------------------------------------------

    proposed_fixes = (
        approval_request.get(
            "proposed_fixes",
            [],
        )
    )

    if not proposed_fixes:

        raise ValueError(
            "No proposed fixes found "
            "for this approval request."
        )

    # -----------------------------------------------------
    # Return approved changes
    # -----------------------------------------------------

    return {
        "approval_id": approval_id,
        "owner": approval_request[
            "owner"
        ],
        "repository": approval_request[
            "repository"
        ],
        "pull_request_number": (
            approval_request[
                "pull_request_number"
            ]
        ),
        "commit_sha": approval_request[
            "commit_sha"
        ],
        "proposed_fixes": proposed_fixes,
        "status": "approved",
    }
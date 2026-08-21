from typing import Any

from app.services.approval_service import (
    create_approval_request,
)

from app.services.email_service import (
    send_approval_email,
)


# =========================================================
# Create Approval Workflow
# =========================================================

def create_approval_workflow(
    owner: str,
    repository: str,
    pull_request_number: int,
    commit_sha: str,
    proposed_fixes: list[dict[str, Any]],
    recipient_email: str,
) -> dict[str, Any]:
    """
    Create an approval request and send an approval email.

    IMPORTANT:
    This function does NOT modify GitHub code.

    It only:
        1. Creates an approval request.
        2. Generates an approval ID.
        3. Sends the approval email.
    """

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not proposed_fixes:
        raise ValueError(
            "At least one proposed fix is required."
        )

    if not recipient_email:
        raise ValueError(
            "Recipient email is required."
        )

    # -----------------------------------------------------
    # Create approval request
    # -----------------------------------------------------

    approval_request = (
        create_approval_request(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
            commit_sha=commit_sha,
            proposed_fixes=proposed_fixes,
        )
    )

    approval_id = approval_request[
        "approval_id"
    ]

    # -----------------------------------------------------
    # Send approval email
    # -----------------------------------------------------

    email_sent = send_approval_email(
        recipient_email=recipient_email,
        approval_id=approval_id,
        owner=owner,
        repository=repository,
        pull_request_number=pull_request_number,
        proposed_fix_count=len(
            proposed_fixes
        ),
    )

    # -----------------------------------------------------
    # Return workflow result
    # -----------------------------------------------------

    return {
        "approval_id": approval_id,
        "status": approval_request[
            "status"
        ],
        "email_sent": email_sent,
        "pull_request_number": (
            pull_request_number
        ),
        "commit_sha": commit_sha,
        "proposed_fix_count": len(
            proposed_fixes
        ),
    }
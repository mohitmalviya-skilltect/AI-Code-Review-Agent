from datetime import datetime, timezone
from uuid import uuid4
from typing import Any


# =========================================================
# In-memory approval storage
# =========================================================
#
# For now we use a dictionary.
# Later, we can replace this with a database such as
# PostgreSQL, Redis, or DynamoDB.
#
# approval_id -> approval request
#

_APPROVAL_REQUESTS: dict[str, dict[str, Any]] = {}


# =========================================================
# Create Approval Request
# =========================================================

def create_approval_request(
    owner: str,
    repository: str,
    pull_request_number: int,
    commit_sha: str,
    proposed_fixes: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a new approval request for AI-generated code fixes.

    This function DOES NOT apply any changes.

    It only stores the proposed changes and waits for the
    user to approve them.
    """

    if not owner:
        raise ValueError(
            "Repository owner is required."
        )

    if not repository:
        raise ValueError(
            "Repository name is required."
        )

    if not pull_request_number:
        raise ValueError(
            "Pull request number is required."
        )

    if not commit_sha:
        raise ValueError(
            "Commit SHA is required."
        )

    if not isinstance(
        proposed_fixes,
        list,
    ):
        raise ValueError(
            "proposed_fixes must be a list."
        )

    if not proposed_fixes:
        raise ValueError(
            "At least one proposed fix is required."
        )

    # -----------------------------------------
    # Generate unique approval ID
    # -----------------------------------------

    approval_id = str(
        uuid4()
    )

    # -----------------------------------------
    # Create approval request
    # -----------------------------------------

    approval_request = {
        "approval_id": approval_id,
        "owner": owner,
        "repository": repository,
        "pull_request_number": pull_request_number,
        "commit_sha": commit_sha,
        "proposed_fixes": proposed_fixes,
        "status": "pending",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "approved_at": None,
    }

    _APPROVAL_REQUESTS[
        approval_id
    ] = approval_request

    print("=" * 60)
    print("APPROVAL REQUEST CREATED")
    print("=" * 60)

    print(
        f"Approval ID: {approval_id}"
    )

    print(
        f"Repository: "
        f"{owner}/{repository}"
    )

    print(
        f"PR Number: "
        f"{pull_request_number}"
    )

    print(
        f"Commit SHA: "
        f"{commit_sha}"
    )

    print(
        f"Proposed fixes: "
        f"{len(proposed_fixes)}"
    )

    print(
        "Status: pending"
    )

    print("=" * 60)

    return approval_request


# =========================================================
# Get Approval Request
# =========================================================

def get_approval_request(
    approval_id: str,
) -> dict[str, Any] | None:
    """
    Retrieve an approval request using its ID.

    Returns None if the approval request does not exist.
    """

    if not approval_id:
        return None

    return _APPROVAL_REQUESTS.get(
        approval_id
    )


# =========================================================
# Approve Request
# =========================================================

def approve_request(
    approval_id: str,
) -> dict[str, Any]:
    """
    Approve a pending code-change request.

    IMPORTANT:
    This function ONLY changes the approval status.

    It does NOT modify GitHub or apply code changes.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:
        raise ValueError(
            "Approval request not found."
        )

    # -----------------------------------------
    # Prevent duplicate approval
    # -----------------------------------------

    if approval_request["status"] == "approved":

        return approval_request

    # -----------------------------------------
    # Prevent approval of cancelled request
    # -----------------------------------------

    if approval_request["status"] == "cancelled":

        raise ValueError(
            "This approval request has been cancelled."
        )

    # -----------------------------------------
    # Approve request
    # -----------------------------------------

    approval_request["status"] = "approved"

    approval_request["approved_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print("=" * 60)
    print("CODE CHANGES APPROVED")
    print("=" * 60)

    print(
        f"Approval ID: "
        f"{approval_id}"
    )

    print(
        "Status: approved"
    )

    print("=" * 60)

    return approval_request


# =========================================================
# Cancel Request
# =========================================================

def cancel_request(
    approval_id: str,
) -> dict[str, Any]:
    """
    Cancel a pending approval request.

    This does not modify GitHub.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:
        raise ValueError(
            "Approval request not found."
        )

    if approval_request["status"] == "approved":

        raise ValueError(
            "An approved request cannot be cancelled."
        )

    approval_request["status"] = "cancelled"

    return approval_request


# =========================================================
# Check Approval Status
# =========================================================

def is_approved(
    approval_id: str,
) -> bool:
    """
    Check whether an approval request has been approved.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:
        return False

    return (
        approval_request["status"]
        == "approved"
    )
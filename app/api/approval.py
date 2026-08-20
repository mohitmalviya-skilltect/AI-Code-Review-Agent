from datetime import datetime, timezone
import html
import requests

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.approval_service import (
    get_approval_request,
    approve_request,
)

from app.services.github_apply_service import (
    apply_approved_changes,
)

router = APIRouter(
    prefix="/approval",
    tags=["Approval"],
)


# =========================================================
# View Approval Request
# =========================================================

@router.get(
    "/{approval_id}",
    response_class=HTMLResponse,
)
def view_approval(
    approval_id: str,
):
    """
    Display the proposed code changes and provide
    Approve / Reject buttons.

    This endpoint DOES NOT modify GitHub.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    repository = (
        f"{approval_request['owner']}/"
        f"{approval_request['repository']}"
    )

    pr_number = approval_request[
        "pull_request_number"
    ]

    status = approval_request[
        "status"
    ]

    proposed_fixes = approval_request.get(
        "proposed_fixes",
        [],
    )

    fix_sections = []

    for index, fix in enumerate(
        proposed_fixes,
        start=1,
    ):

        # -------------------------------------------------
        # Escape AI-generated content before inserting it
        # into HTML.
        # -------------------------------------------------

        file_path = html.escape(
            str(
                fix.get(
                    "file",
                    "unknown",
                )
            )
        )

        summary = html.escape(
            str(
                fix.get(
                    "summary",
                    "No summary provided.",
                )
            )
        )

        changes = fix.get(
            "changes",
            [],
        )

        fixed_code = html.escape(
            str(
                fix.get(
                    "fixed_code",
                    "",
                )
            )
        )

        changes_html = ""

        if changes:

            change_items = []

            for change in changes:

                change_items.append(
                    f"<li>{html.escape(str(change))}</li>"
                )

            changes_html = (
                "<ul>"
                + "".join(change_items)
                + "</ul>"
            )

        else:

            changes_html = (
                "<p>No detailed changes provided.</p>"
            )

        fix_sections.append(
            f"""
            <div class="fix">

                <h3>
                    Fix {index}
                </h3>

                <p>
                    <strong>File:</strong>
                    <code>{file_path}</code>
                </p>

                <p>
                    <strong>Summary:</strong>
                    {summary}
                </p>

                <p>
                    <strong>Changes:</strong>
                </p>

                {changes_html}

                <p>
                    <strong>Proposed Code:</strong>
                </p>

                <pre>{fixed_code}</pre>

            </div>
            """
        )

    fixes_html = "\n".join(
        fix_sections
    )

    # -----------------------------------------------------
    # Pending
    # -----------------------------------------------------

    if status == "pending":

        action_html = f"""
        <form
            method="post"
            action="/approval/{approval_id}/approve"
        >

            <button
                type="submit"
                class="approve"
            >
                Approve Changes
            </button>

        </form>

        <form
            method="post"
            action="/approval/{approval_id}/reject"
        >

            <button
                type="submit"
                class="reject"
            >
                Reject Changes
            </button>

        </form>
        """

    # -----------------------------------------------------
    # Approved but not yet applied
    # -----------------------------------------------------

    elif status == "approved":

        action_html = f"""
        <div class="approved">
            ✓ Changes Approved
        </div>

        <p class="retry-info">
            The changes have been approved but are not yet
            marked as applied.
        </p>

        <form
            method="post"
            action="/approval/{approval_id}/approve"
        >

            <button
                type="submit"
                class="apply"
            >
                Apply Approved Changes
            </button>

        </form>
        """

    # -----------------------------------------------------
    # Applied
    # -----------------------------------------------------

    elif status == "applied":

        action_html = """
        <div class="applied">
            ✓ Changes Approved and Applied
            to the Pull Request branch.
        </div>
        """

    # -----------------------------------------------------
    # Rejected
    # -----------------------------------------------------

    elif status == "cancelled":

        action_html = """
        <div class="rejected">
            ✗ Changes Rejected
        </div>
        """

    # -----------------------------------------------------
    # Other
    # -----------------------------------------------------

    else:

        safe_status = html.escape(
            str(status)
        )

        action_html = f"""
        <p>
            Current status:
            <strong>{safe_status}</strong>
        </p>
        """

    # -----------------------------------------------------
    # Escape repository information
    # -----------------------------------------------------

    safe_repository = html.escape(
        repository
    )

    safe_status = html.escape(
        str(status)
    )

    # -----------------------------------------------------
    # HTML
    # -----------------------------------------------------

    html_page = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <title>
            AI Code Review Approval
        </title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f5f5;
            }}

            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow:
                    0 2px 10px
                    rgba(0, 0, 0, 0.1);
            }}

            h1 {{
                margin-top: 0;
            }}

            .info {{
                background: #f0f0f0;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}

            .fix {{
                border: 1px solid #ddd;
                padding: 20px;
                margin-top: 20px;
                border-radius: 8px;
            }}

            pre {{
                background: #272822;
                color: white;
                padding: 15px;
                overflow-x: auto;
                border-radius: 6px;
                white-space: pre-wrap;
            }}

            code {{
                background: #eee;
                padding: 3px 6px;
                border-radius: 4px;
            }}

            form {{
                display: inline-block;
                margin-right: 10px;
                margin-top: 20px;
            }}

            button {{
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 15px;
            }}

            .approve {{
                background: #2da44e;
                color: white;
            }}

            .apply {{
                background: #0969da;
                color: white;
            }}

            .reject {{
                background: #cf222e;
                color: white;
            }}

            .approved {{
                background: #dafbe1;
                color: #1a7f37;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
            }}

            .applied {{
                background: #ddf4ff;
                color: #0969da;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
            }}

            .rejected {{
                background: #ffebe9;
                color: #cf222e;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
            }}

            .retry-info {{
                color: #666;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <h1>
                🤖 AI Code Review Agent
            </h1>

            <div class="info">

                <p>
                    <strong>Repository:</strong>
                    {safe_repository}
                </p>

                <p>
                    <strong>Pull Request:</strong>
                    #{pr_number}
                </p>

                <p>
                    <strong>Status:</strong>
                    {safe_status}
                </p>

            </div>

            <h2>
                Proposed Code Changes
            </h2>

            {fixes_html}

            {action_html}

        </div>

    </body>

    </html>
    """

    return HTMLResponse(
        content=html_page
    )


# =========================================================
# Approve / Apply Changes
# =========================================================

@router.post(
    "/{approval_id}/approve",
)
def approve_changes(
    approval_id: str,
):
    """
    Approve and apply the proposed code changes.

    Flow:

        1. Get approval request.
        2. Verify request exists.
        3. If pending, mark it approved.
        4. Verify approval safety gate.
        5. Apply approved changes to GitHub.
        6. Mark request as applied.
        7. Return result.

    IMPORTANT:

    GitHub changes are ONLY made after the approval
    request has been marked as approved.
    """

    # -----------------------------------------------------
    # Get approval request
    # -----------------------------------------------------

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:

        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    current_status = approval_request.get(
        "status"
    )

    # -----------------------------------------------------
    # Already applied
    # -----------------------------------------------------

    if current_status == "applied":

        return {
            "message": (
                "Changes were already applied."
            ),
            "approval_id": approval_id,
            "status": "applied",
        }

    # -----------------------------------------------------
    # Cancelled / rejected
    # -----------------------------------------------------

    if current_status == "cancelled":

        raise HTTPException(
            status_code=400,
            detail=(
                "This approval request "
                "has been rejected."
            ),
        )

    # -----------------------------------------------------
    # Pending request
    # -----------------------------------------------------
    #
    # Only pending requests need to be approved.
    #
    # If status is already "approved", we continue
    # directly to the GitHub application step.
    #
    # This is important because if GitHub failed during
    # the previous attempt, the request can be retried.
    # -----------------------------------------------------

    if current_status == "pending":

        try:

            approved_request = approve_request(
                approval_id
            )

            if approved_request.get(
                "status"
            ) != "approved":

                raise ValueError(
                    "Approval request could not "
                    "be marked as approved."
                )

        except ValueError as error:

            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error

    elif current_status != "approved":

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid approval status: "
                f"{current_status}"
            ),
        )

    # -----------------------------------------------------
    # Apply approved changes to GitHub
    # -----------------------------------------------------

    try:

        result = apply_approved_changes(
            approval_id
        )

    except PermissionError as error:

        raise HTTPException(
            status_code=403,
            detail=str(error),
        ) from error

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except requests.exceptions.RequestException as error:

        print("=" * 60)
        print(
            "GITHUB UPDATE FAILED"
        )
        print("=" * 60)

        print(
            f"Approval ID: "
            f"{approval_id}"
        )

        print(
            f"Error: "
            f"{error}"
        )

        print("=" * 60)

        # IMPORTANT:
        #
        # Do NOT mark the request as applied.
        #
        # It remains "approved", so the user can
        # retry the application.

        raise HTTPException(
            status_code=502,
            detail=(
                "Changes were approved, "
                "but the GitHub update failed. "
                "The approved changes can be retried."
            ),
        ) from error

    except Exception as error:

        print("=" * 60)
        print(
            "FAILED TO APPLY APPROVED CHANGES"
        )
        print("=" * 60)

        print(
            f"Approval ID: "
            f"{approval_id}"
        )

        print(
            f"Error: "
            f"{error}"
        )

        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=(
                "Changes were approved, "
                "but the GitHub update failed. "
                "The approved changes can be retried."
            ),
        ) from error

    # -----------------------------------------------------
    # Mark as applied ONLY after GitHub succeeds
    # -----------------------------------------------------

    approval_request["status"] = "applied"

    approval_request["applied_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print("=" * 60)
    print(
        "APPROVED CHANGES APPLIED"
    )
    print("=" * 60)

    print(
        f"Approval ID: "
        f"{approval_id}"
    )

    print(
        "Status: applied"
    )

    print("=" * 60)

    # -----------------------------------------------------
    # Return successful result
    # -----------------------------------------------------

    return {
        "message": (
            "Changes approved and "
            "applied successfully."
        ),
        "approval_id": approval_id,
        "status": "applied",
        "result": result,
    }


# =========================================================
# Reject Changes
# =========================================================

@router.post(
    "/{approval_id}/reject",
)
def reject_changes(
    approval_id: str,
):
    """
    Reject the proposed changes.

    No GitHub modification is performed.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:

        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    current_status = approval_request.get(
        "status"
    )

    # -----------------------------------------------------
    # Already applied
    # -----------------------------------------------------

    if current_status == "applied":

        raise HTTPException(
            status_code=400,
            detail=(
                "Changes have already been "
                "applied and cannot be rejected."
            ),
        )

    # -----------------------------------------------------
    # Already approved
    # -----------------------------------------------------

    if current_status == "approved":

        raise HTTPException(
            status_code=400,
            detail=(
                "Approved changes cannot "
                "be rejected."
            ),
        )

    # -----------------------------------------------------
    # Already rejected
    # -----------------------------------------------------

    if current_status == "cancelled":

        return {
            "message": (
                "Changes were already rejected."
            ),
            "approval_id": approval_id,
            "status": "cancelled",
        }

    # -----------------------------------------------------
    # Reject
    # -----------------------------------------------------

    approval_request[
        "status"
    ] = "cancelled"

    approval_request[
        "cancelled_at"
    ] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print("=" * 60)
    print(
        "CODE CHANGES REJECTED"
    )
    print("=" * 60)

    print(
        f"Approval ID: "
        f"{approval_id}"
    )

    print(
        "Status: cancelled"
    )

    print("=" * 60)

    return {
        "message": (
            "Changes rejected successfully."
        ),
        "approval_id": approval_id,
        "status": "cancelled",
    }
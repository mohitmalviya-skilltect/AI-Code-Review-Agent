from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.approval_service import (
    get_approval_request,
    approve_request,
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

    This endpoint DOES NOT apply any changes.
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

    proposed_fixes = approval_request[
        "proposed_fixes"
    ]

    fix_sections = []

    for index, fix in enumerate(
        proposed_fixes,
        start=1,
    ):

        file_path = fix.get(
            "file",
            "unknown",
        )

        summary = fix.get(
            "summary",
            "No summary provided.",
        )

        changes = fix.get(
            "changes",
            [],
        )

        fixed_code = fix.get(
            "fixed_code",
            "",
        )

        changes_html = ""

        if changes:

            changes_html = (
                "<ul>"
                + "".join(
                    f"<li>{change}</li>"
                    for change in changes
                )
                + "</ul>"
            )

        fix_sections.append(
            f"""
            <div class="fix">
                <h3>Fix {index}</h3>

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

    elif status == "approved":

        action_html = """
        <div class="approved">
            ✓ Changes Approved
        </div>
        """

    elif status == "cancelled":

        action_html = """
        <div class="rejected">
            ✗ Changes Rejected
        </div>
        """

    else:

        action_html = f"""
        <p>
            Current status:
            <strong>{status}</strong>
        </p>
        """

    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

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

            .rejected {{
                background: #ffebe9;
                color: #cf222e;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
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
                    {repository}
                </p>

                <p>
                    <strong>Pull Request:</strong>
                    #{pr_number}
                </p>

                <p>
                    <strong>Status:</strong>
                    {status}
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
        content=html
    )


# =========================================================
# Approve Changes
# =========================================================

@router.post(
    "/{approval_id}/approve",
)
def approve_changes(
    approval_id: str,
):
    """
    Approve the proposed changes.

    IMPORTANT:
    For now this ONLY changes the approval status.

    GitHub modifications will be connected in
    the next step.
    """

    approval_request = get_approval_request(
        approval_id
    )

    if approval_request is None:

        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    if approval_request[
        "status"
    ] == "approved":

        return {
            "message": (
                "Changes were already approved."
            ),
            "approval_id": approval_id,
            "status": "approved",
        }

    if approval_request[
        "status"
    ] == "cancelled":

        raise HTTPException(
            status_code=400,
            detail=(
                "This approval request "
                "has been rejected."
            ),
        )

    approved = approve_request(
        approval_id
    )

    return {
        "message": (
            "Changes approved successfully."
        ),
        "approval_id": approval_id,
        "status": approved[
            "status"
        ],
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

    if approval_request[
        "status"
    ] == "approved":

        raise HTTPException(
            status_code=400,
            detail=(
                "Approved changes cannot "
                "be rejected."
            ),
        )

    approval_request[
        "status"
    ] = "cancelled"

    return {
        "message": (
            "Changes rejected successfully."
        ),
        "approval_id": approval_id,
        "status": "cancelled",
    }
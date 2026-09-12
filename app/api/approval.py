from datetime import datetime, timezone
import html
import requests

from fastapi import APIRouter, HTTPException, Request
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
# Code Viewer Helper with Line Numbers
# =========================================================

def render_code_with_line_numbers(code_str: str, target_line: int | None = None) -> str:
    """
    Renders code in a modern GitHub/IDE-style viewer with line numbers
    and highlights the line where the issue was reported.
    """
    if not code_str:
        return "<p><em>No code available.</em></p>"

    lines = code_str.split("\n")
    rows = []

    for idx, raw_line in enumerate(lines, start=1):
        escaped_line = html.escape(raw_line)
        if not escaped_line:
            escaped_line = "&nbsp;"

        is_target = (target_line is not None and idx == target_line)
        row_cls = ' class="code-row highlight-line"' if is_target else ' class="code-row"'
        badge = '<span class="line-flag">Issue Line</span>' if is_target else ''

        rows.append(
            f'<tr{row_cls}>'
            f'<td class="line-num">{idx}</td>'
            f'<td class="line-content">{escaped_line}{badge}</td>'
            f'</tr>'
        )

    return (
        '<div class="code-box">'
        '<div class="code-scroll">'
        '<table class="code-table"><tbody>'
        + "".join(rows)
        + '</tbody></table></div></div>'
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

    # -----------------------------------------------------
    # HTML Layout & Actions (Granular/Selectable check)
    # -----------------------------------------------------

    form_start = ""
    form_end = ""

    if status in {"pending", "approved"}:
        form_start = f"""
        <form
            method="post"
            action="/approval/{approval_id}/approve"
            id="approval-form"
        >
        """
        form_end = "</form>"

    fixes_list_html = []
    for index, fix in enumerate(proposed_fixes):
        checkbox_html = ""
        if status in {"pending", "approved"}:
            checkbox_html = f"""
            <div style="margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                <input
                    type="checkbox"
                    name="selected_fixes"
                    value="{index}"
                    id="fix-check-{index}"
                    checked
                    style="width: 20px; height: 20px; cursor: pointer;"
                />
                <label for="fix-check-{index}" style="font-weight: bold; cursor: pointer;">
                    Select to apply this fix
                </label>
            </div>
            """

        file_path = html.escape(str(fix.get("file", "unknown")))
        summary = html.escape(str(fix.get("summary", "No summary provided.")))
        problem = html.escape(str(fix.get("problem", "")))
        suggestion = html.escape(str(fix.get("suggestion", "")))
        line = html.escape(str(fix.get("line", "unknown")))
        severity = html.escape(str(fix.get("severity", "medium")).upper())
        category = html.escape(str(fix.get("category", "quality")).upper())

        # Determine target line number for highlight
        target_line_num = None
        try:
            target_line_num = int(fix.get("line"))
        except (ValueError, TypeError):
            pass

        problem_html = f"<p><strong>Problem (Line {line}):</strong> {problem}</p>" if problem else ""
        badge_color = "#cf222e" if severity in {"CRITICAL", "HIGH"} else "#0969da"
        badge_html = f"""<span style="background: {badge_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-left: 10px;">{severity} &bull; {category}</span>"""

        changes_list = fix.get("changes", [])
        if changes_list:
            changes_html = "<ul>" + "".join(f"<li>{html.escape(str(c))}</li>" for c in changes_list) + "</ul>"
        else:
            changes_html = "<p>No detailed changes provided.</p>"

        code_block_html = render_code_with_line_numbers(
            fix.get("fixed_code", ""),
            target_line=target_line_num,
        )

        fixes_list_html.append(
            f"""
            <div class="fix">
                {checkbox_html}
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0;">Fix {index + 1}</h3>
                    {badge_html}
                </div>
                <p><strong>File:</strong> <code>{file_path}</code></p>
                {problem_html}
                <p><strong>Summary:</strong> {summary}</p>
                <p><strong>Detailed Changes:</strong></p>
                {changes_html}
                <p><strong>Proposed Code (with line numbers &amp; documentation):</strong></p>
                {code_block_html}
            </div>
            """
        )

    fixes_html = "\n".join(fixes_list_html)

    if status == "pending":
        action_html = """
        <div style="display: flex; gap: 15px; margin-top: 20px;">
            <button
                type="submit"
                class="approve"
            >
                Approve Selected Changes
            </button>
            <button
                type="submit"
                formaction="REJECT_PLACEHOLDER"
                class="reject"
                id="reject-btn"
                onclick="event.preventDefault(); document.getElementById('reject-form').submit();"
            >
                Reject Changes
            </button>
        </div>
        """
    elif status == "approved":
        action_html = """
        <div class="approved">
            ✓ Changes Approved
        </div>
        <p class="retry-info">
            The changes have been approved but are not yet marked as applied.
        </p>
        <div style="margin-top: 20px;">
            <button
                type="submit"
                class="apply"
            >
                Apply Approved Changes
            </button>
        </div>
        """
    elif status == "applied":
        action_html = """
        <div class="applied">
            ✓ Changes Approved and Applied to the Pull Request branch.
        </div>
        """
    elif status == "cancelled":
        action_html = """
        <div class="rejected">
            ✗ Changes Rejected
        </div>
        """
    else:
        action_html = f"<p>Current status: <strong>{html.escape(str(status))}</strong></p>"

    # Reject form (outside main form to reject everything)
    reject_form_html = ""
    if status == "pending":
        reject_form_html = f"""
        <form
            id="reject-form"
            method="post"
            action="/approval/{approval_id}/reject"
            style="display: none;"
        ></form>
        """

    # -----------------------------------------------------
    # HTML Page Output
    # -----------------------------------------------------

    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AI Code Review Approval</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 1100px;
                margin: 40px auto;
                padding: 20px;
                background: #f6f8fa;
                color: #24292f;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                border: 1px solid #d0d7de;
                box-shadow: 0 3px 12px rgba(140, 149, 159, 0.15);
            }}
            h1 {{
                margin-top: 0;
            }}
            .info {{
                background: #f6f8fa;
                border: 1px solid #d0d7de;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
            }}
            .fix {{
                border: 1px solid #d0d7de;
                padding: 24px;
                margin-top: 24px;
                border-radius: 8px;
                background: #ffffff;
            }}
            .code-box {{
                background: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 10px;
                overflow: hidden;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4);
            }}
            .code-scroll {{
                overflow-x: auto;
                max-height: 520px;
                overflow-y: auto;
            }}
            .code-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: Consolas, "Liberation Mono", Menlo, Courier, monospace;
                font-size: 13px;
                line-height: 20px;
                color: #e6edf3;
            }}
            .code-row {{
                transition: background 0.1s ease;
            }}
            .code-row:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            .code-table td {{
                padding: 0;
                vertical-align: top;
            }}
            .line-num {{
                width: 48px;
                min-width: 48px;
                padding: 1px 12px 1px 8px !important;
                text-align: right;
                color: #6e7681;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                border-right: 1px solid #30363d;
                background: #161b22;
                font-size: 12px;
            }}
            .line-content {{
                padding: 1px 14px !important;
                white-space: pre;
                word-break: normal;
            }}
            .highlight-line {{
                background: rgba(234, 179, 8, 0.18) !important;
            }}
            .highlight-line .line-num {{
                color: #facc15 !important;
                font-weight: bold;
                border-right: 2px solid #facc15 !important;
                background: rgba(234, 179, 8, 0.3) !important;
            }}
            .highlight-line .line-content {{
                background: rgba(234, 179, 8, 0.12) !important;
            }}
            .line-flag {{
                background: #eab308;
                color: #000;
                font-size: 11px;
                font-weight: bold;
                padding: 1px 6px;
                border-radius: 4px;
                margin-left: 16px;
                vertical-align: middle;
            }}
            code {{
                background: #afb8c133;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 13px;
            }}
            button {{
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 15px;
                font-weight: bold;
            }}
            .approve {{
                background: #1f883d;
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
            <h1>🤖 AI Code Review Agent</h1>
            <div class="info">
                <p><strong>Repository:</strong> {html.escape(repository)}</p>
                <p><strong>Pull Request:</strong> #{pr_number}</p>
                <p><strong>Status:</strong> {html.escape(str(status))}</p>
            </div>
            <h2>Proposed Code Changes</h2>
            {form_start}
                {fixes_html}
                {action_html}
            {form_end}
            {reject_form_html}
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
async def approve_changes(
    approval_id: str,
    request: Request,
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
    # Read selected fixes from form data
    # -----------------------------------------------------

    form_data = await request.form()
    selected_fixes_raw = form_data.getlist("selected_fixes")
    selected_indices = None
    if selected_fixes_raw:
        try:
            selected_indices = [int(x) for x in selected_fixes_raw]
        except ValueError:
            pass

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
            approval_id=approval_id,
            selected_indices=selected_indices,
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

    from app.services.approval_service import save_approvals, _APPROVAL_REQUESTS
    _APPROVAL_REQUESTS[approval_id] = approval_request
    save_approvals(_APPROVAL_REQUESTS)

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

    from app.services.approval_service import save_approvals, _APPROVAL_REQUESTS
    _APPROVAL_REQUESTS[approval_id] = approval_request
    save_approvals(_APPROVAL_REQUESTS)

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
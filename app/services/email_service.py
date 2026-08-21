import os

import resend

from email.message import EmailMessage
from urllib.parse import quote


# =========================================================
# Email Configuration
# =========================================================

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY",
)

APPROVAL_FROM_EMAIL = os.getenv(
    "APPROVAL_FROM_EMAIL",
    "onboarding@resend.dev",
)

APPROVAL_BASE_URL = os.getenv(
    "APPROVAL_BASE_URL",
    "http://localhost:8000/approval",
)


# =========================================================
# Build Approval Link
# =========================================================

def build_approval_link(
    approval_id: str,
) -> str:
    """
    Build the URL that the user will open to review
    and approve the proposed code changes.
    """

    if not approval_id:
        raise ValueError(
            "approval_id is required."
        )

    encoded_id = quote(
        approval_id,
        safe="",
    )

    return (
        f"{APPROVAL_BASE_URL}/"
        f"{encoded_id}"
    )


# =========================================================
# Build Approval Email
# =========================================================

def build_approval_email(
    recipient_email: str,
    approval_id: str,
    owner: str,
    repository: str,
    pull_request_number: int,
    proposed_fix_count: int,
) -> EmailMessage:
    """
    Create the approval email.

    This function only creates the email content.
    It does not send the email.
    """

    if not recipient_email:
        raise ValueError(
            "Recipient email is required."
        )

    if not owner:
        raise ValueError(
            "Repository owner is required."
        )

    if not repository:
        raise ValueError(
            "Repository name is required."
        )

    approval_link = build_approval_link(
        approval_id
    )

    message = EmailMessage()

    message["Subject"] = (
        f"AI Code Review - "
        f"Approval Required for PR #{pull_request_number}"
    )

    message["From"] = APPROVAL_FROM_EMAIL

    message["To"] = recipient_email

    body = f"""
Hello,

The AI Code Review Agent has reviewed the following Pull Request:

Repository:
{owner}/{repository}

Pull Request:
#{pull_request_number}

Proposed fixes:
{proposed_fix_count}

The AI has generated proposed code changes.

No changes will be applied to the repository until you approve them.

Please review the proposed changes here:

{approval_link}

After approval, the agent will apply the approved changes.

If you did not request this review, you can ignore this email.

Regards,
AI Code Review Agent
""".strip()

    message.set_content(
        body
    )

    return message


# =========================================================
# Send Approval Email
# =========================================================

def send_approval_email(
    recipient_email: str,
    approval_id: str,
    owner: str,
    repository: str,
    pull_request_number: int,
    proposed_fix_count: int,
) -> bool:
    """
    Send the approval email using Resend.

    Returns True when the email is sent successfully.
    """

    if not RESEND_API_KEY:
        raise ValueError(
            "RESEND_API_KEY is not configured."
        )

    if not APPROVAL_FROM_EMAIL:
        raise ValueError(
            "APPROVAL_FROM_EMAIL is not configured."
        )

    if not recipient_email:
        raise ValueError(
            "Recipient email is required."
        )

    # -----------------------------------------------------
    # Build approval link
    # -----------------------------------------------------

    approval_link = build_approval_link(
        approval_id
    )

    # -----------------------------------------------------
    # Build email content
    # -----------------------------------------------------

    subject = (
        f"AI Code Review - "
        f"Approval Required for PR #{pull_request_number}"
    )

    body = f"""
Hello,

The AI Code Review Agent has reviewed the following Pull Request:

Repository:
{owner}/{repository}

Pull Request:
#{pull_request_number}

Proposed fixes:
{proposed_fix_count}

The AI has generated proposed code changes.

No changes will be applied to the repository until you approve them.

Please review the proposed changes here:

{approval_link}

After approval, the agent will apply the approved changes.

If you did not request this review, you can ignore this email.

Regards,
AI Code Review Agent
""".strip()

    # -----------------------------------------------------
    # Configure Resend
    # -----------------------------------------------------

    resend.api_key = RESEND_API_KEY

    params = {
        "from": APPROVAL_FROM_EMAIL,
        "to": [recipient_email],
        "subject": subject,
        "text": body,
    }

    try:

        response = resend.Emails.send(
            params
        )

        print("=" * 60)
        print("APPROVAL EMAIL SENT")
        print("=" * 60)

        print(
            f"Recipient: "
            f"{recipient_email}"
        )

        print(
            f"PR: #{pull_request_number}"
        )

        print(
            f"Resend Response: "
            f"{response}"
        )

        print("=" * 60)

        return True

    except Exception as error:

        print("=" * 60)
        print("APPROVAL EMAIL FAILED")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        print("=" * 60)

        raise
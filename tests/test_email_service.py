from app.services.email_service import (
    build_approval_link,
    build_approval_email,
)


def test_build_approval_link():

    approval_id = "abc-123"

    link = build_approval_link(
        approval_id
    )

    assert link.endswith(
        "/abc-123"
    )


def test_build_approval_email():

    message = build_approval_email(
        recipient_email="developer@example.com",
        approval_id="abc-123",
        owner="mohitmalviya-skilltect",
        repository="AI-Code-Review-Agent",
        pull_request_number=10,
        proposed_fix_count=2,
    )

    assert message["To"] == (
        "developer@example.com"
    )

    assert "PR #10" in (
        message["Subject"]
    )

    body = message.get_content()

    assert "abc-123" in body

    assert (
        "No changes will be applied"
        in body
    )

    assert (
        "Approve" in body
        or "approval" in body.lower()
    )
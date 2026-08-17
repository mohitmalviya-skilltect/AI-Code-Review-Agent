from fastapi import APIRouter, Request, BackgroundTasks

from app.services.github_service import (
    get_pull_request_files,
    post_pull_request_review,
    post_pull_request_line_comment,
)

from app.services.git_service import (
    filter_reviewable_files,
    get_changed_line_numbers,
)

from app.services.review_service import (
    prepare_review_files,
    generate_code_review,
)

from app.services.secret_scanner import (
    scan_files,
)


# =========================================================
# Reviewed commits
# =========================================================

reviewed_commits = set()

router = APIRouter()


# =========================================================
# Process GitHub Event
# =========================================================

def process_github_event(
    payload: dict,
    event_type: str,
):

    # =====================================================
    # PUSH EVENT
    # =====================================================

    if event_type == "push":

        print("=" * 60)
        print("PUSH EVENT RECEIVED")
        print("=" * 60)

        print(
            "Code was pushed to the repository."
        )

        print(
            "AI review will NOT run on push."
        )

        print(
            "Waiting for Pull Request event..."
        )

        return

    # =====================================================
    # PULL REQUEST EVENT
    # =====================================================

    elif event_type == "pull_request":

        print("=" * 60)
        print("PROCESSING PULL REQUEST EVENT")
        print("=" * 60)

        action = payload.get(
            "action",
            "unknown",
        )

        print(
            f"Pull Request Action: {action}"
        )

        if action in {
            "opened",
            "reopened",
            "synchronize",
        }:

            process_pull_request_review(
                payload
            )

        else:

            print(
                f"Skipping PR action: {action}"
            )

    # =====================================================
    # OTHER EVENTS
    # =====================================================

    else:

        print("=" * 60)
        print(
            f"IGNORING EVENT: {event_type}"
        )
        print("=" * 60)


# =========================================================
# Process Pull Request Review
# =========================================================

def process_pull_request_review(
    payload: dict,
):

    print("=" * 60)
    print("PULL REQUEST REVIEW")
    print("=" * 60)

    pull_request = payload.get(
        "pull_request",
        {},
    )

    repository = payload.get(
        "repository",
        {},
    )

    owner = repository.get(
        "owner",
        {},
    ).get(
        "login"
    )

    repository_name = repository.get(
        "name"
    )

    pr_number = pull_request.get(
        "number"
    )

    title = pull_request.get(
        "title"
    )

    head_sha = pull_request.get(
        "head",
        {},
    ).get(
        "sha"
    )

    print(
        f"Repository: "
        f"{owner}/{repository_name}"
    )

    print(
        f"PR Number: {pr_number}"
    )

    print(
        f"PR Title: {title}"
    )

    print(
        f"Head SHA: {head_sha}"
    )

    # =====================================================
    # Prevent duplicate review
    # =====================================================

    if head_sha in reviewed_commits:

        print("=" * 60)
        print("DUPLICATE REVIEW SKIPPED")
        print("=" * 60)

        print(
            f"Commit {head_sha} has already "
            "been successfully reviewed."
        )

        return

    # =====================================================
    # 1. Fetch PR changed files
    # =====================================================

    try:

        pr_files = get_pull_request_files(
            owner=owner,
            repository=repository_name,
            pull_request_number=pr_number,
        )

        print("=" * 60)
        print("PULL REQUEST CHANGED FILES")
        print("=" * 60)

        for file in pr_files:

            print(
                f"File: "
                f"{file.get('filename')}"
            )

            print(
                f"Status: "
                f"{file.get('status')}"
            )

            print(
                f"Additions: "
                f"{file.get('additions', 0)}"
            )

            print(
                f"Deletions: "
                f"{file.get('deletions', 0)}"
            )

            print("Patch:")

            print(
                file.get(
                    "patch",
                    "",
                )
            )

            print("=" * 60)

    except Exception as error:

        print("=" * 60)
        print(
            "FAILED TO FETCH "
            "PULL REQUEST FILES"
        )
        print("=" * 60)

        print(error)

        return

    # =====================================================
    # 2. Filter reviewable files
    # =====================================================

    changed_files = [
        file.get("filename")
        for file in pr_files
    ]

    reviewable_files = filter_reviewable_files(
        changed_files
    )

    print("=" * 60)
    print("PR FILES TO REVIEW")
    print("=" * 60)

    print(
        reviewable_files
    )

    # =====================================================
    # 3. Prepare files for review
    # =====================================================

    reviewable_diffs = [
        {
            "path": file.get("filename"),
            "status": file.get("status"),
            "patch": file.get(
                "patch",
                "",
            ),
        }
        for file in pr_files
        if file.get("filename")
        in reviewable_files
    ]

    review_files = prepare_review_files(
        reviewable_diffs
    )

    print("=" * 60)
    print("PR FILES READY FOR REVIEW")
    print("=" * 60)

    for file in review_files:

        print(
            f"File: {file.path}"
        )

    # =====================================================
    # 4. Stop if no reviewable files
    # =====================================================

    if not review_files:

        print(
            "No reviewable PR files found."
        )

        return

    # =====================================================
    # 5. RUN SECRET SCANNER
    # =====================================================

    print("=" * 60)
    print("RUNNING SECRET SCANNER")
    print("=" * 60)

    secret_findings = scan_files(
        review_files
    )

    print(
        f"Secrets detected: "
        f"{len(secret_findings)}"
    )

    for finding in secret_findings:

        print(
            f"[CRITICAL] "
            f"{finding.secret_type} "
            f"→ "
            f"{finding.file}:"
            f"{finding.line}"
        )

    # =====================================================
    # 6. Generate AI review
    # =====================================================

    print("=" * 60)
    print("GENERATING PR AI CODE REVIEW")
    print("=" * 60)

    try:

        ai_review = generate_code_review(
            review_files
        )

        print("=" * 60)
        print("PR AI CODE REVIEW")
        print("=" * 60)

        print(
            ai_review
        )

        # =================================================
        # 7. Get AI review result
        # =================================================

        summary = ai_review.get(
            "summary",
            "No summary provided.",
        )

        issues = ai_review.get(
            "issues",
            [],
        )

        review_failed = ai_review.get(
            "review_failed",
            False,
        )

        # =================================================
        # 8. Convert secret findings into review issues
        # =================================================

        security_issues = []

        for finding in secret_findings:

            security_issues.append(
                {
                    "severity": "critical",
                    "category": "security",
                    "file": finding.file,
                    "line": finding.line,
                    "problem": finding.message,
                    "suggestion": (
                        "Remove the credential from "
                        "the source code and store it "
                        "securely using environment "
                        "variables or a secret manager. "
                        "If this credential is real, "
                        "rotate or revoke it immediately."
                    ),
                }
            )

        # Add security findings to the issues
        # that will be shown in the PR review.

        all_issues = (
            security_issues + issues
        )

        # =================================================
        # 9. Determine whether PR should be blocked
        # =================================================

        secrets_detected = bool(
            secret_findings
        )

        if secrets_detected:

            review_event = "REQUEST_CHANGES"

        else:

            review_event = "COMMENT"

        print("=" * 60)
        print("PR REVIEW DECISION")
        print("=" * 60)

        print(
            f"Secrets detected: "
            f"{secrets_detected}"
        )

        print(
            f"GitHub review event: "
            f"{review_event}"
        )

        # =================================================
        # 10. Build PR review body
        # =================================================

        review_lines = []

        review_lines.append(
            "## 🤖 AI Code Review"
        )

        review_lines.append("")

        # -------------------------------------------------
        # Security warning
        # -------------------------------------------------

        if secrets_detected:

            review_lines.append(
                "## 🚨 SECURITY WARNING"
            )

            review_lines.append("")

            review_lines.append(
                "**SECRET DETECTED — DO NOT MERGE**"
            )

            review_lines.append("")

            review_lines.append(
                "A potentially exposed credential "
                "was detected in newly added code."
            )

            review_lines.append("")

            review_lines.append(
                "Please remove the credential and "
                "rotate/revoke it immediately if "
                "it is a real credential."
            )

            review_lines.append("")

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        review_lines.append(
            "### Summary"
        )

        review_lines.append(
            summary
        )

        review_lines.append("")

        # -------------------------------------------------
        # Security findings
        # -------------------------------------------------

        if security_issues:

            review_lines.append(
                "### 🔐 Security Findings"
            )

            review_lines.append("")

            for index, issue in enumerate(
                security_issues,
                start=1,
            ):

                review_lines.append(
                    f"#### {index}. "
                    "CRITICAL — SECURITY"
                )

                review_lines.append(
                    f"**File:** "
                    f"`{issue['file']}`"
                )

                review_lines.append(
                    f"**Line:** "
                    f"`{issue['line']}`"
                )

                review_lines.append("")

                review_lines.append(
                    f"**Problem:** "
                    f"{issue['problem']}"
                )

                review_lines.append("")

                review_lines.append(
                    f"**Suggestion:** "
                    f"{issue['suggestion']}"
                )

                review_lines.append("")

        # -------------------------------------------------
        # AI issues
        # -------------------------------------------------

        if review_failed:

            review_lines.append(
                "### ⚠️ AI Review Unavailable"
            )

            review_lines.append("")

            review_lines.append(
                "The AI reviewer could not "
                "complete the review."
            )

            if secrets_detected:

                review_lines.append(
                    "The local security scanner "
                    "still detected the security "
                    "finding shown above."
                )

            review_lines.append("")

        elif issues:

            review_lines.append(
                "### Issues Found"
            )

            review_lines.append("")

            for index, issue in enumerate(
                issues,
                start=1,
            ):

                severity = issue.get(
                    "severity",
                    "unknown",
                )

                category = issue.get(
                    "category",
                    "unknown",
                )

                file_path = issue.get(
                    "file",
                    "unknown",
                )

                line = issue.get(
                    "line",
                    "unknown",
                )

                problem = issue.get(
                    "problem",
                    "No problem description.",
                )

                suggestion = issue.get(
                    "suggestion",
                    "No suggestion provided.",
                )

                review_lines.append(
                    f"#### {index}. "
                    f"{severity.upper()} — "
                    f"{category}"
                )

                review_lines.append(
                    f"**File:** `{file_path}`"
                )

                review_lines.append(
                    f"**Line:** `{line}`"
                )

                review_lines.append("")

                review_lines.append(
                    f"**Problem:** {problem}"
                )

                review_lines.append("")

                review_lines.append(
                    f"**Suggestion:** {suggestion}"
                )

                review_lines.append("")

        elif not security_issues:

            review_lines.append(
                "### ✅ No significant issues found"
            )

        review_body = "\n".join(
            review_lines
        )

        # =================================================
        # 11. Build changed-line mapping
        # =================================================

        changed_lines_by_file = {}

        for file in pr_files:

            file_path = file.get(
                "filename"
            )

            if file_path not in reviewable_files:
                continue

            patch = file.get(
                "patch",
                "",
            )

            if not patch:
                continue

            changed_lines = (
                get_changed_line_numbers(
                    patch
                )
            )

            changed_lines_by_file[
                file_path
            ] = changed_lines

        print("=" * 60)
        print("PR CHANGED LINE MAPPING")
        print("=" * 60)

        print(
            changed_lines_by_file
        )

        # =================================================
        # 12. Post inline comments
        # =================================================

        if not review_failed and all_issues:

            print("=" * 60)
            print(
                "POSTING PR INLINE COMMENTS"
            )
            print("=" * 60)

            for issue in all_issues:

                file_path = issue.get(
                    "file"
                )

                line = issue.get(
                    "line"
                )

                if not file_path:
                    continue

                if not isinstance(
                    line,
                    int,
                ):
                    continue

                changed_lines = (
                    changed_lines_by_file.get(
                        file_path,
                        set(),
                    )
                )

                if line not in changed_lines:

                    print(
                        f"Skipping inline comment "
                        f"for {file_path}:{line} "
                        "(line not in PR diff)"
                    )

                    continue

                severity = issue.get(
                    "severity",
                    "unknown",
                )

                category = issue.get(
                    "category",
                    "unknown",
                )

                problem = issue.get(
                    "problem",
                    "No problem description.",
                )

                suggestion = issue.get(
                    "suggestion",
                    "No suggestion provided.",
                )

                marker = (
                    f"<!-- ai-code-review:"
                    f"{head_sha}:"
                    f"{file_path}:"
                    f"{line} -->"
                )

                line_comment = (
                    f"{marker}\n\n"
                    "## 🤖 AI Code Review\n\n"
                    f"**Severity:** "
                    f"{severity.upper()}\n\n"
                    f"**Category:** "
                    f"{category}\n\n"
                    f"**Problem:** "
                    f"{problem}\n\n"
                    f"**Suggestion:** "
                    f"{suggestion}"
                )

                try:

                    line_response = (
                        post_pull_request_line_comment(
                            owner=owner,
                            repository=repository_name,
                            pull_request_number=pr_number,
                            commit_sha=head_sha,
                            file_path=file_path,
                            line=line,
                            comment=line_comment,
                        )
                    )

                    print(
                        f"PR inline comment posted: "
                        f"{file_path}:{line}"
                    )

                    print(
                        line_response.get(
                            "html_url"
                        )
                    )

                except Exception as error:

                    print(
                        f"Failed to post PR inline "
                        f"comment for "
                        f"{file_path}:{line}: "
                        f"{error}"
                    )

        elif review_failed:

            print(
                "Skipping AI inline comments "
                "because AI review failed."
            )

        else:

            print(
                "No issues available for "
                "PR inline comments."
            )

        # =================================================
        # 13. Post overall PR review
        # =================================================

        print("=" * 60)
        print("POSTING PR REVIEW TO GITHUB")
        print("=" * 60)

        pr_response = post_pull_request_review(
            owner=owner,
            repository=repository_name,
            pull_request_number=pr_number,
            commit_sha=head_sha,
            review_body=review_body,
            review_event=review_event,
        )

        print("=" * 60)
        print("PR REVIEW POSTED TO GITHUB")
        print("=" * 60)

        print(
            pr_response.get(
                "html_url"
            )
        )

        # =================================================
        # Only mark successful reviews without secrets
        # as successfully reviewed.
        # =================================================

        if (
            not review_failed
            and not secrets_detected
        ):

            reviewed_commits.add(
                head_sha
            )

            print(
                f"Commit {head_sha} "
                "marked as reviewed."
            )

        else:

            print(
                f"Commit {head_sha} "
                "was NOT marked as successfully "
                "reviewed because "
                f"review_failed={review_failed}, "
                f"secrets_detected="
                f"{secrets_detected}."
            )

    except Exception as error:

        print("=" * 60)
        print("PR AI REVIEW FAILED")
        print("=" * 60)

        print(error)


# =========================================================
# Webhook Endpoint
# =========================================================

@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):

    payload = await request.json()

    event_type = request.headers.get(
        "X-GitHub-Event"
    )

    print("=" * 60)
    print(
        f"GitHub Event Received: "
        f"{event_type}"
    )
    print("=" * 60)

    background_tasks.add_task(
        process_github_event,
        payload,
        event_type,
    )

    return {
        "status": "accepted",
        "message": (
            f"GitHub {event_type} event "
            "received. Processing started."
        ),
    }
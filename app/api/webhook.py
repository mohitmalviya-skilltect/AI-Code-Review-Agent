import os

from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
)

from app.services.github_service import (
    post_pull_request_review,
    post_pull_request_line_comment,
)

from app.services.git_service import (
    filter_reviewable_files,
    get_commit_diff,
    get_changed_line_numbers,
)

from app.services.review_service import (
    prepare_review_files,
    generate_code_review,
)

from app.services.code_fix_service import (
    generate_code_fix,
)

from app.services.approval_workflow_service import (
    create_approval_workflow,
)


# =========================================================
# Reviewed commits
# =========================================================
#
# Only successfully reviewed commits are stored here.
#
# This prevents the same commit from being reviewed
# multiple times during duplicate webhook deliveries.
#
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

    if event_type == "pull_request":

        print("=" * 60)
        print(
            "PROCESSING PULL REQUEST EVENT"
        )
        print("=" * 60)

        action = payload.get(
            "action",
            "unknown",
        )

        print(
            f"Pull Request Action: {action}"
        )

        # -------------------------------------------------
        # Only process actions that can contain new code
        # -------------------------------------------------

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

        return

    # =====================================================
    # OTHER EVENTS
    # =====================================================

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

    # =====================================================
    # 1. Extract PR information
    # =====================================================

    pull_request = payload.get(
        "pull_request",
        {},
    )

    repository = payload.get(
        "repository",
        {},
    )

    owner = (
        repository.get(
            "owner"
        ) or {}
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

    head_sha = (
        pull_request.get(
            "head"
        ) or {}
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
    # 2. Validate required information
    # =====================================================

    if not owner:

        print(
            "Repository owner is missing."
        )

        return

    if not repository_name:

        print(
            "Repository name is missing."
        )

        return

    if not pr_number:

        print(
            "Pull Request number is missing."
        )

        return

    if not head_sha:

        print(
            "Pull Request head SHA is missing."
        )

        return

    # =====================================================
    # 3. Prevent duplicate review
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
    # 4. Get files changed in THIS COMMIT
    # =====================================================
    #
    # IMPORTANT:
    #
    # We intentionally DO NOT use:
    #
    #     get_pull_request_files()
    #
    # because that returns the accumulated files of the
    # entire Pull Request.
    #
    # Instead we use the PR head SHA and fetch the commit
    # diff.
    #
    # This means:
    #
    # Commit A -> file1.py
    # Commit B -> file2.py
    #
    # When Commit B is pushed:
    #
    # Review ONLY file2.py
    #
    # =====================================================

    try:

        commit_files = get_commit_diff(
            owner=owner,
            repository=repository_name,
            commit_sha=head_sha,
        )

        if not commit_files:

            print("=" * 60)
            print("NO FILES CHANGED IN THIS COMMIT")
            print("=" * 60)

            return

        print("=" * 60)
        print("COMMIT FILES")
        print("=" * 60)

        for file in commit_files:

            print(
                f"File: "
                f"{file.get('path')}"
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
            "FAILED TO FETCH COMMIT FILES"
        )
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        return

    # =====================================================
    # 5. Get reviewable files
    # =====================================================
    #
    # The reviewable file list is now created ONLY from
    # files changed by this commit.
    #
    # =====================================================

    changed_files = []

    for file in commit_files:

        file_path = file.get(
            "path"
        )

        if file_path:

            changed_files.append(
                file_path
            )

    reviewable_files = filter_reviewable_files(
        changed_files
    )

    print("=" * 60)
    print("COMMIT FILES TO REVIEW")
    print("=" * 60)

    print(
        reviewable_files
    )

    if not reviewable_files:

        print(
            "No reviewable files found "
            "in this commit."
        )

        return

    # =====================================================
    # 6. Prepare review files
    # =====================================================

    review_files = prepare_review_files(
        [
            file
            for file in commit_files
            if file.get(
                "path"
            ) in reviewable_files
        ]
    )

    print("=" * 60)
    print("FILES READY FOR REVIEW")
    print("=" * 60)

    for file in review_files:

        print(
            f"File: {file.path}"
        )

    if not review_files:

        print(
            "No review files available."
        )

        return

    # =====================================================
    # 7. Generate AI review
    # =====================================================

    print("=" * 60)
    print("GENERATING AI CODE REVIEW")
    print("=" * 60)

    try:

        ai_review = generate_code_review(
            review_files
        )

    except Exception as error:

        print("=" * 60)
        print("AI REVIEW GENERATION FAILED")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        return

    if not isinstance(
        ai_review,
        dict,
    ):

        print("=" * 60)
        print("INVALID AI REVIEW RESPONSE")
        print("=" * 60)

        return

    print("=" * 60)
    print("AI CODE REVIEW")
    print("=" * 60)

    print(
        ai_review
    )

    # =====================================================
    # 8. Extract review result
    # =====================================================

    review_failed = ai_review.get(
        "review_failed",
        False,
    )

    issues = ai_review.get(
        "issues",
        [],
    )

    summary = ai_review.get(
        "summary",
        "AI review completed.",
    )

    # =====================================================
    # 9. Build changed-line mapping
    # =====================================================

    changed_lines_by_file = {}

    for file in commit_files:

        file_path = file.get(
            "path"
        )

        if file_path not in reviewable_files:

            continue

        patch = file.get(
            "patch",
            "",
        )

        if not patch:

            continue

        try:

            changed_lines = (
                get_changed_line_numbers(
                    patch
                )
            )

            changed_lines_by_file[
                file_path
            ] = changed_lines

        except Exception as error:

            print(
                f"Failed to calculate changed "
                f"lines for {file_path}: "
                f"{error}"
            )

            changed_lines_by_file[
                file_path
            ] = set()

    print("=" * 60)
    print("PR CHANGED LINE MAPPING")
    print("=" * 60)

    print(
        changed_lines_by_file
    )

    # =====================================================
    # 10. Build GitHub review body
    # =====================================================

    review_lines = []

    review_lines.append(
        "## 🤖 AI Code Review"
    )

    review_lines.append("")

    review_lines.append(
        "### Summary"
    )

    review_lines.append("")

    review_lines.append(
        str(summary)
    )

    review_lines.append("")

    if review_failed:

        review_lines.append(
            "### ⚠️ AI Review Unavailable"
        )

        review_lines.append("")

        review_lines.append(
            "The AI reviewer could not "
            "complete the full review."
        )

        review_lines.append("")

        review_lines.append(
            "Security findings detected by "
            "the local scanner, if any, are "
            "still included above."
        )

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
                f"{str(severity).upper()} — "
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

    else:

        review_lines.append(
            "### ✅ No significant issues found"
        )

    review_lines.append("")

    review_lines.append(
        "_Review generated automatically "
        "by AI Code Review Agent._"
    )

    review_body = "\n".join(
        review_lines
    )

    # =====================================================
    # 11. Post PR inline comments
    # =====================================================
    #
    # IMPORTANT:
    #
    # Inline comments are posted ONLY when the AI review
    # successfully completed.
    #
    # Also, comments are posted ONLY on lines that belong
    # to the current commit's diff.
    #
    # =====================================================

    if not review_failed and issues:

        print("=" * 60)
        print(
            "POSTING PR INLINE COMMENTS"
        )
        print("=" * 60)

        for issue in issues:

            file_path = issue.get(
                "file"
            )

            line = issue.get(
                "line"
            )

            if not file_path:

                print(
                    "Skipping issue because "
                    "file is missing."
                )

                continue

            if not isinstance(
                line,
                int,
            ):

                print(
                    f"Skipping inline comment "
                    f"for {file_path}: "
                    f"invalid line {line}"
                )

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
                    "(line not in current "
                    "commit diff)"
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
                f"{str(severity).upper()}\n\n"
                f"**Category:** "
                f"{category}\n\n"
                f"**Problem:** "
                f"{problem}\n\n"
                f"**Suggestion:** "
                f"{suggestion}"
            )

            try:

                response = (
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
                    response.get(
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

    else:

        print(
            "No inline comments to post."
        )

    # =====================================================
    # 12. Generate proposed code fixes
    # =====================================================
    #
    # IMPORTANT:
    #
    # Gemini only generates proposed code.
    #
    # Nothing is modified on GitHub here.
    #
    # Actual GitHub modification happens ONLY after
    # explicit approval.
    #
    # =====================================================

    proposed_fixes = []

    if not review_failed and issues:

        print("=" * 60)
        print(
            "GENERATING PROPOSED CODE FIXES"
        )
        print("=" * 60)

        # -------------------------------------------------
        # Build original-code lookup
        #
        # ReviewFile currently contains path/diff.
        # If a future version of review_service provides
        # content/code/source, we use it here.
        # -------------------------------------------------

        original_file_contents = {}

        for file in review_files:

            file_path = getattr(
                file,
                "path",
                None,
            )

            original_code = getattr(
                file,
                "content",
                None,
            )

            if original_code is None:

                original_code = getattr(
                    file,
                    "code",
                    None,
                )

            if original_code is None:

                original_code = getattr(
                    file,
                    "source",
                    None,
                )

            if (
                file_path
                and original_code is not None
            ):

                original_file_contents[
                    file_path
                ] = original_code

        # -------------------------------------------------
        # Generate fix for each issue
        # -------------------------------------------------

        for issue in issues:

            file_path = issue.get(
                "file"
            )

            if not file_path:

                print(
                    "Skipping fix: "
                    "issue file is missing."
                )

                continue

            # -------------------------------------------------
            # Never automatically generate code modifications
            # for security/secret findings.
            # -------------------------------------------------

            category = str(
                issue.get(
                    "category",
                    "",
                )
            ).lower()

            if category in {
                "security",
                "secret",
                "secrets",
            }:

                print(
                    f"Skipping automatic code fix "
                    f"for security issue: "
                    f"{file_path}"
                )

                continue

            original_code = (
                original_file_contents.get(
                    file_path
                )
            )

            if original_code is None:

                print(
                    f"Skipping code fix for "
                    f"{file_path}: "
                    "original file content "
                    "is unavailable."
                )

                continue

            try:

                fix_result = generate_code_fix(
                    file_path=file_path,
                    original_code=original_code,
                    issue=issue,
                )

                if not fix_result:

                    print(
                        f"No proposed fix generated "
                        f"for {file_path}"
                    )

                    continue

                if isinstance(
                    fix_result,
                    dict,
                ):

                    proposed_fix = (
                        fix_result.copy()
                    )

                else:

                    proposed_fix = {
                        "file": file_path,
                        "fixed_code": str(
                            fix_result
                        ),
                    }

                proposed_fix.setdefault(
                    "file",
                    file_path,
                )

                proposed_fix.setdefault(
                    "summary",
                    issue.get(
                        "suggestion",
                        "AI-generated code fix.",
                    ),
                )

                proposed_fix.setdefault(
                    "changes",
                    [
                        issue.get(
                            "suggestion",
                            "AI-generated code fix.",
                        )
                    ],
                )

                if not proposed_fix.get(
                    "fixed_code"
                ):

                    print(
                        f"Skipping proposed fix "
                        f"for {file_path}: "
                        "fixed_code is missing."
                    )

                    continue

                proposed_fixes.append(
                    proposed_fix
                )

                print(
                    f"Proposed fix generated: "
                    f"{file_path}"
                )

            except Exception as error:

                print(
                    f"Failed to generate "
                    f"proposed fix for "
                    f"{file_path}: "
                    f"{error}"
                )

    else:

        if review_failed:

            print(
                "Skipping code-fix generation "
                "because AI review failed."
            )

        else:

            print(
                "No AI issues require "
                "proposed fixes."
            )

    # =====================================================
    # 13. Create Approval Workflow
    # =====================================================
    #
    # This:
    #
    #   1. Creates an approval request.
    #   2. Stores proposed fixes.
    #   3. Sends approval email.
    #
    # It DOES NOT modify GitHub.
    #
    # =====================================================

    if proposed_fixes:

        print("=" * 60)
        print(
            "CREATING APPROVAL WORKFLOW"
        )
        print("=" * 60)

        recipient_email = os.getenv(
            "APPROVAL_RECIPIENT_EMAIL"
        )

        if not recipient_email:

            print(
                "APPROVAL_RECIPIENT_EMAIL "
                "is not configured."
            )

        else:

            try:

                approval_result = (
                    create_approval_workflow(
                        owner=owner,
                        repository=repository_name,
                        pull_request_number=pr_number,
                        commit_sha=head_sha,
                        proposed_fixes=proposed_fixes,
                        recipient_email=recipient_email,
                    )
                )

                print("=" * 60)
                print(
                    "APPROVAL WORKFLOW CREATED"
                )
                print("=" * 60)

                print(
                    f"Approval ID: "
                    f"{approval_result.get('approval_id')}"
                )

                print(
                    f"Status: "
                    f"{approval_result.get('status')}"
                )

                print(
                    f"Email sent: "
                    f"{approval_result.get('email_sent')}"
                )

                print(
                    f"Proposed fixes: "
                    f"{approval_result.get('proposed_fix_count')}"
                )

                print("=" * 60)

            except Exception as error:

                print("=" * 60)
                print(
                    "APPROVAL WORKFLOW FAILED"
                )
                print("=" * 60)

                print(
                    f"Error: {error}"
                )

                print("=" * 60)

    else:

        print("=" * 60)
        print(
            "NO PROPOSED FIXES GENERATED"
        )
        print("=" * 60)

    # =====================================================
    # 14. Post overall PR review
    # =====================================================

    print("=" * 60)
    print(
        "POSTING PR REVIEW TO GITHUB"
    )
    print("=" * 60)

    try:

        pr_response = post_pull_request_review(
            owner=owner,
            repository=repository_name,
            pull_request_number=pr_number,
            commit_sha=head_sha,
            review_body=review_body,
        )

        print("=" * 60)
        print(
            "PR REVIEW POSTED TO GITHUB"
        )
        print("=" * 60)

        print(
            pr_response.get(
                "html_url"
            )
        )

    except Exception as error:

        print("=" * 60)
        print(
            "FAILED TO POST PR REVIEW"
        )
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        return

    # =====================================================
    # 15. Mark commit as reviewed
    # =====================================================
    #
    # Only mark it after the complete GitHub review
    # was successfully posted.
    #
    # =====================================================

    if not review_failed:

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
            "was NOT marked as reviewed "
            "because the AI review failed."
        )


# =========================================================
# Old Push Review Function
# =========================================================
#
# Kept for compatibility.
#
# Push events no longer trigger AI review.
# Pull Request events are the primary workflow.
#
# =========================================================

def process_github_review(
    payload: dict,
):

    print(
        "Push-based AI review is disabled."
    )

    print(
        "AI reviews are triggered through "
        "Pull Request events."
    )

    return


# =========================================================
# Webhook Endpoint
# =========================================================

@router.post(
    "/webhook"
)
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
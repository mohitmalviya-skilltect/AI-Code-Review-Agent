import base64
import os

import requests

from fastapi import (
    APIRouter,
    Request,
    BackgroundTasks,
)

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

from app.services.code_fix_service import (
    generate_code_fix,
)

from app.services.approval_workflow_service import (
    create_approval_workflow,
)


# =========================================================
# Reviewed commits
# =========================================================

reviewed_commits = set()

router = APIRouter()


# =========================================================
# GitHub File Content
# =========================================================

def get_file_content_at_commit(
    owner: str,
    repository: str,
    file_path: str,
    commit_sha: str,
) -> str | None:
    """
    Fetch the complete file content from GitHub at a
    specific commit.

    This is used when generating proposed code fixes.

    IMPORTANT:
    This function only reads GitHub.
    It does NOT modify the repository.
    """

    github_token = os.getenv(
        "GITHUB_TOKEN"
    )

    if not github_token:
        raise ValueError(
            "GITHUB_TOKEN is not configured."
        )

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/contents/"
        f"{file_path}"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": (
            f"Bearer {github_token}"
        ),
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(
        url,
        headers=headers,
        params={
            "ref": commit_sha,
        },
        timeout=15,
    )

    # -----------------------------------------------------
    # File not found
    # -----------------------------------------------------

    if response.status_code == 404:

        print(
            f"GitHub file not found: "
            f"{file_path}"
        )

        return None

    response.raise_for_status()

    data = response.json()

    encoded_content = data.get(
        "content"
    )

    if not encoded_content:
        return None

    encoded_content = (
        encoded_content
        .replace("\n", "")
        .replace("\r", "")
    )

    try:

        decoded_content = base64.b64decode(
            encoded_content
        ).decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        print(
            f"Skipping binary/non-UTF-8 file: "
            f"{file_path}"
        )

        return None

    return decoded_content


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
            "AI PR review will not run on push."
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

        return

    # =====================================================
    # UNKNOWN EVENT
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

    pull_request = payload.get(
        "pull_request",
        {},
    )

    repository = payload.get(
        "repository",
        {},
    )

    owner = (
        repository
        .get(
            "owner",
            {},
        )
        .get(
            "login"
        )
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
        pull_request
        .get(
            "head",
            {},
        )
        .get(
            "sha"
        )
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
    # Validate webhook data
    # =====================================================

    if not owner:
        print(
            "Missing repository owner."
        )
        return

    if not repository_name:
        print(
            "Missing repository name."
        )
        return

    if not pr_number:
        print(
            "Missing Pull Request number."
        )
        return

    if not head_sha:
        print(
            "Missing Pull Request head SHA."
        )
        return

    # =====================================================
    # Prevent duplicate review & infinite review loops
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

    # Check commit message or metadata to prevent loop
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            commit_url = f"https://api.github.com/repos/{owner}/{repository_name}/commits/{head_sha}"
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {github_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            commit_resp = requests.get(commit_url, headers=headers, timeout=15)
            if commit_resp.status_code == 200:
                commit_info = commit_resp.json()
                commit_message = commit_info.get("commit", {}).get("message", "")
                if "🤖 Apply AI-approved fix" in commit_message:
                    print("=" * 60)
                    print("LOOP DETECTED: Skipping commit generated by the AI agent itself.")
                    print("=" * 60)
                    return
        except Exception as loop_err:
            print(f"Failed checking loop prevention: {loop_err}")

    # =====================================================
    # 1. Fetch PR changed files
    # =====================================================

    try:
        action = payload.get("action", "opened")
        if action == "synchronize":
            print(f"Synchronize event: Fetching files only changed in the latest commit {head_sha}")
            pr_files = get_commit_files(
                owner=owner,
                repository=repository_name,
                commit_sha=head_sha,
            )
        else:
            pr_files = get_pull_request_files(
                owner=owner,
                repository=repository_name,
                pull_request_number=pr_number,
            )

    except Exception as error:

        print("=" * 60)
        print("FAILED TO FETCH PR FILES")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        return

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

    # =====================================================
    # 2. Filter reviewable files
    # =====================================================

    changed_file_names = [
        file.get(
            "filename"
        )
        for file in pr_files
        if file.get(
            "filename"
        )
    ]

    reviewable_files = (
        filter_reviewable_files(
            changed_file_names
        )
    )

    print("=" * 60)
    print("FILES READY FOR REVIEW")
    print("=" * 60)

    for file_path in reviewable_files:

        print(
            f"File: {file_path}"
        )

    if not reviewable_files:

        print(
            "No reviewable files found."
        )

        return

    # =====================================================
    # 3. Prepare review files
    # =====================================================

    file_diffs = []

    for file in pr_files:

        file_path = file.get(
            "filename"
        )

        if file_path not in reviewable_files:
            continue

        file_diffs.append(
            {
                "path": file_path,
                "status": file.get(
                    "status",
                    "modified",
                ),
                "patch": file.get(
                    "patch",
                    "",
                ),
            }
        )

    review_files = prepare_review_files(
        file_diffs
    )

    # =====================================================
    # 4. Generate AI code review
    # =====================================================

    print("=" * 60)
    print("GENERATING PR AI CODE REVIEW")
    print("=" * 60)

    try:

        ai_review = generate_code_review(
            review_files
        )

    except Exception as error:

        print("=" * 60)
        print("PR AI REVIEW FAILED")
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
        print("INVALID AI REVIEW RESULT")
        print("=" * 60)

        return

    print("=" * 60)
    print("PR AI CODE REVIEW")
    print("=" * 60)

    print(
        ai_review
    )

    # =====================================================
    # 5. Extract review result
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
    # 6. Build PR review body
    # =====================================================

    review_lines = []

    review_lines.append(
        "## 🤖 AI Code Review"
    )

    review_lines.append("")

    review_lines.append(
        "### Summary"
    )

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
            "complete the review."
        )

        review_lines.append(
            "Security findings detected "
            "by the local scanner, if any, "
            "are still included above."
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

            file_path = issue.get(
                "file",
                "unknown",
            )

            line = issue.get(
                "line",
                "unknown",
            )

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

            review_lines.append(
                f"#### {index}. "
                f"{str(severity).upper()} "
                f"— {category}"
            )

            review_lines.append("")

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
    # 7. Build changed-line mapping
    # =====================================================

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

    # =====================================================
    # 8. Post PR inline comments
    # =====================================================

    if issues:

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
                f"{str(severity).upper()}\n\n"
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

    else:

        print(
            "No issues available for "
            "PR inline comments."
        )

    # =====================================================
    # 9. Generate proposed code fixes
    # =====================================================

    proposed_fixes = []

    if not review_failed and issues:

        print("=" * 60)
        print("GENERATING PROPOSED CODE FIXES")
        print("=" * 60)

        for issue in issues:

            file_path = issue.get(
                "file"
            )

            if not file_path:

                print(
                    "Skipping code fix because "
                    "issue file is missing."
                )

                continue

            # -------------------------------------------------
            # Security issues are NOT automatically fixed.
            # -------------------------------------------------

            category = str(
                issue.get(
                    "category",
                    "",
                )
                or ""
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

            # -------------------------------------------------
            # IMPORTANT FIX:
            #
            # Fetch complete source code directly from GitHub
            # instead of looking for review_file.content.
            # -------------------------------------------------

            print(
                f"Fetching original source: "
                f"{file_path}"
            )

            try:

                original_code = (
                    get_file_content_at_commit(
                        owner=owner,
                        repository=repository_name,
                        file_path=file_path,
                        commit_sha=head_sha,
                    )
                )

            except Exception as error:

                print(
                    f"Failed to fetch original "
                    f"file content for "
                    f"{file_path}: {error}"
                )

                continue

            if original_code is None:

                print(
                    f"Skipping code fix for "
                    f"{file_path}: "
                    "original file content "
                    "is unavailable."
                )

                continue

            print(
                f"Original source loaded: "
                f"{file_path}"
            )

            # -------------------------------------------------
            # Generate proposed fix
            # -------------------------------------------------

            try:

                fix_result = generate_code_fix(
                    file_path=file_path,
                    original_code=original_code,
                    issue=issue,
                )

            except Exception as error:

                print(
                    f"Failed to generate "
                    f"proposed fix for "
                    f"{file_path}: "
                    f"{error}"
                )

                continue

            if not fix_result:

                print(
                    f"No proposed fix generated "
                    f"for {file_path}"
                )

                continue

            # -------------------------------------------------
            # Normalize fix result
            # -------------------------------------------------

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
    # 10. Create Approval Workflow
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
                    "APPROVAL REQUEST CREATED"
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

                print(
                    "Approval workflow is ready."
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
    # 11. Post overall PR review
    # =====================================================

    print("=" * 60)
    print("POSTING PR REVIEW TO GITHUB")
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
        print("PR REVIEW POSTED TO GITHUB")
        print("=" * 60)

        if pr_response:

            print(
                pr_response.get(
                    "html_url"
                )
            )

        # -------------------------------------------------
        # Only mark successful AI reviews as reviewed.
        # -------------------------------------------------

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

    except Exception as error:

        print("=" * 60)
        print("FAILED TO POST PR REVIEW")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        return


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
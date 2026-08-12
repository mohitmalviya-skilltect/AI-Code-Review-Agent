from fastapi import APIRouter, Request, BackgroundTasks

from app.services.github_service import post_commit_review

from app.services.git_service import (
    get_changed_files,
    filter_reviewable_files,
    get_commit_diff,
    get_changed_line_numbers,
)

from app.services.review_service import (
    prepare_review_files,
    generate_code_review,
)

router = APIRouter()


# =========================================================
# Background review processing
# =========================================================

def process_github_review(payload: dict):

    print("=" * 60)
    print("GitHub Webhook Received")
    print("=" * 60)

    repository = payload.get("repository", {})

    owner = repository.get("owner", {}).get("login")
    repository_name = repository.get("name")

    print(f"Repository: {owner}/{repository_name}")

    # =====================================================
    # 1. Find changed files
    # =====================================================

    changed_files = get_changed_files(payload)

    reviewable_files = filter_reviewable_files(
        changed_files
    )

    print("Changed files:")
    print(changed_files)

    print("Files to review:")
    print(reviewable_files)

    # =====================================================
    # 2. Fetch commit diff
    # =====================================================

    file_diffs = []

    if payload.get("commits"):

        commit_sha = payload["commits"][-1]["id"]

        print(f"Commit SHA: {commit_sha}")

        try:

            file_diffs = get_commit_diff(
                owner=owner,
                repository=repository_name,
                commit_sha=commit_sha,
            )

            print("=" * 60)
            print("COMMIT DIFF")
            print("=" * 60)

            for file in file_diffs:

                file_path = file["path"]
                status = file["status"]
                patch = file.get("patch", "")

                if file_path in reviewable_files:

                    print(f"File: {file_path}")
                    print(f"Status: {status}")
                    print("Patch:")
                    print(patch)

                    # -------------------------------------
                    # Find changed lines
                    # -------------------------------------

                    if patch:

                        changed_lines = (
                            get_changed_line_numbers(
                                patch
                            )
                        )

                        print(
                            f"Changed lines in "
                            f"{file_path}: "
                            f"{changed_lines}"
                        )

                    print("=" * 60)

        except Exception as error:

            print("=" * 60)
            print("FAILED TO FETCH COMMIT DIFF")
            print("=" * 60)

            print(error)

            return

    # =====================================================
    # 3. Prepare files for review
    # =====================================================

    review_files = prepare_review_files(
        [
            file
            for file in file_diffs
            if file["path"] in reviewable_files
        ]
    )

    print("=" * 60)
    print("FILES READY FOR REVIEW")
    print("=" * 60)

    for file in review_files:
        print(f"File: {file.path}")

    # =====================================================
    # 4. Generate AI review
    # =====================================================

    if not review_files:

        print("No reviewable files found.")

        return

    print("=" * 60)
    print("GENERATING AI CODE REVIEW")
    print("=" * 60)

    try:

        ai_review = generate_code_review(
            review_files
        )

        print("=" * 60)
        print("AI CODE REVIEW")
        print("=" * 60)

        print(ai_review)

        # =================================================
        # 5. Post review to GitHub
        # =================================================

        commit_sha = payload["commits"][-1]["id"]

        github_response = post_commit_review(
            owner=owner,
            repository=repository_name,
            commit_sha=commit_sha,
            review=ai_review,
        )

        print("=" * 60)
        print("REVIEW POSTED TO GITHUB")
        print("=" * 60)

        print(
            github_response.get(
                "html_url"
            )
        )

    except Exception as error:

        print("=" * 60)
        print("AI REVIEW FAILED")
        print("=" * 60)

        print(error)


# =========================================================
# Webhook endpoint
# =========================================================

@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):

    payload = await request.json()

    # Start review in background
    background_tasks.add_task(
        process_github_review,
        payload,
    )

    # Return immediately to GitHub
    return {
        "status": "accepted",
        "message": "Webhook received. Code review started.",
    }
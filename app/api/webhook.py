from fastapi import APIRouter, Request

from app.services.github_service import post_commit_review

from app.services.git_service import (
    get_changed_files,
    filter_reviewable_files,
    get_commit_diff,
)

from app.services.review_service import (
    prepare_review_files,
    generate_code_review,
)


router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):

    payload = await request.json()

    print("=" * 60)
    print("GitHub Webhook Received")
    print("=" * 60)

    repository = payload.get("repository", {})

    owner = repository.get("owner", {}).get("login")
    repository_name = repository.get("name")

    print(f"Repository: {owner}/{repository_name}")

    # -----------------------------------------
    # 1. Find changed files
    # -----------------------------------------

    changed_files = get_changed_files(payload)

    reviewable_files = filter_reviewable_files(
        changed_files
    )

    print("Changed files:")
    print(changed_files)

    print("Files to review:")
    print(reviewable_files)

    # -----------------------------------------
    # 2. Fetch commit diff
    # -----------------------------------------

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
                patch = file["patch"]

                if file_path in reviewable_files:

                    print(f"File: {file_path}")
                    print(f"Status: {status}")
                    print("Patch:")
                    print(patch)
                    print("=" * 60)

        except Exception as error:

            print("=" * 60)
            print("FAILED TO FETCH COMMIT DIFF")
            print("=" * 60)

            print(error)

    # -----------------------------------------
    # 3. Prepare files for review
    # -----------------------------------------

    reviewable_diffs = [
        file
        for file in file_diffs
        if file["path"] in reviewable_files
    ]

    review_files = prepare_review_files(
        reviewable_diffs
    )

    print("=" * 60)
    print("FILES READY FOR REVIEW")
    print("=" * 60)

    for file in review_files:

        print(f"File: {file.path}")

    # -----------------------------------------
    # 4. Generate AI review
    # -----------------------------------------

    if review_files:

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

            # -----------------------------------------
            # 5. Post review to GitHub
            # -----------------------------------------

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
                github_response.get("html_url")
            )

        except Exception as error:

            print("=" * 60)
            print("AI REVIEW FAILED")
            print("=" * 60)

            print(error)

            ai_review = {
                "summary": "AI review failed.",
                "issues": [],
            }

    else:

        ai_review = {
            "summary": "No reviewable files found.",
            "issues": [],
        }

    # -----------------------------------------
    # 6. Return webhook response
    # -----------------------------------------

    return {
        "status": "success",
        "message": "Code review completed",
        "changed_files": changed_files,
        "reviewable_files": reviewable_files,
        "files_reviewed": [
            file.path
            for file in review_files
        ],
        "ai_review": ai_review,
    }
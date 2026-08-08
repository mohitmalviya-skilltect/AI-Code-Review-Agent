from fastapi import APIRouter, Request

from app.services.git_service import (
    get_changed_files,
    filter_reviewable_files,
    get_file_content,
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

    reviewable_files = filter_reviewable_files(changed_files)

    print("Changed files:")
    print(changed_files)

    print("Files to review:")
    print(reviewable_files)

    # -----------------------------------------
    # 2. Fetch file contents
    # -----------------------------------------

    file_contents = {}

    if payload.get("commits"):

        commit_sha = payload["commits"][-1]["id"]

        print(f"Commit SHA: {commit_sha}")

        for file_path in reviewable_files:

            print("=" * 60)
            print(f"Fetching file: {file_path}")

            try:

                content = get_file_content(
                    owner=owner,
                    repository=repository_name,
                    file_path=file_path,
                    commit_sha=commit_sha,
                )

                file_contents[file_path] = content

                print(f"Successfully fetched: {file_path}")

            except Exception as error:

                print(
                    f"Failed to fetch {file_path}: {error}"
                )

    # -----------------------------------------
    # 3. Prepare files for review
    # -----------------------------------------

    review_files = prepare_review_files(file_contents)

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

        except Exception as error:

            print("=" * 60)
            print("AI REVIEW FAILED")
            print("=" * 60)

            print(error)

            ai_review = "AI review failed."

    else:

        ai_review = "No reviewable files found."

    return {
        "status": "success",
        "message": "Code review completed",
        "changed_files": changed_files,
        "reviewable_files": reviewable_files,
        "files_fetched": list(file_contents.keys()),
        "ai_review": ai_review,
    }
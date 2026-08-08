from fastapi import APIRouter, Request

from app.services.git_service import (
    get_changed_files,
    filter_reviewable_files,
    get_file_content,
)

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):

    payload = await request.json()

    print("=" * 60)
    print("GitHub Webhook Received")
    print("=" * 60)

    # Get repository information
    repository = payload.get("repository", {})

    owner = repository.get("owner", {}).get("login")
    repository_name = repository.get("name")

    print(f"Repository: {owner}/{repository_name}")

    # Get changed files
    changed_files = get_changed_files(payload)

    # Filter files that should be reviewed
    reviewable_files = filter_reviewable_files(changed_files)

    print("Changed files:")
    print(changed_files)

    print("Files to review:")
    print(reviewable_files)

    # Get file contents
    file_contents = {}

    if payload.get("commits"):

        # Get the latest commit from this push
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
                print(content)

            except Exception as error:

                print(f"Failed to fetch {file_path}: {error}")

    return {
        "status": "success",
        "message": "GitHub webhook received successfully",
        "changed_files": changed_files,
        "reviewable_files": reviewable_files,
        "files_fetched": list(file_contents.keys()),
    }
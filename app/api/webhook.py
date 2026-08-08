from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):

    payload = await request.json()

    print("=" * 60)
    print("GitHub Webhook Received")
    print("=" * 60)

    print("Repository:")
    print(payload.get("repository", {}).get("full_name"))

    print("Event:")
    print(payload.get("zen"))

    print("Payload:")
    print(payload)

    return {
        "status": "success",
        "message": "GitHub webhook received successfully"
    }
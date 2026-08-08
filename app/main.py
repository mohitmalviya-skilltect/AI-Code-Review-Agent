from fastapi import FastAPI

from app.api.webhook import router as webhook_router

app = FastAPI(
    title="AI Code Review Agent",
    version="1.0.0",
    description="AI Agent for reviewing GitHub commits and pull requests"
)


@app.get("/")
def home():
    return {
         "message": "AI Code Review Agent is running successfully!"
    }

app.include_router(webhook_router)
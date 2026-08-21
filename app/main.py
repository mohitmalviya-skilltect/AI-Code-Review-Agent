from fastapi import FastAPI

from app.api.webhook import router as webhook_router
from app.api.approval import router as approval_router

app = FastAPI(
    title="AI Code Review Agent",
    version="1.0.0",
    description="AI Agent for reviewing GitHub commits and pull requests"
)

app.include_router(
    approval_router
)


@app.get("/")
def home():
    return {
         "message": "AI Code Review Agent is running successfully!"
    }

app.include_router(webhook_router)

# Testing review service
def add_numbers(a, b):
    return a * b
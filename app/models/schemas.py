from typing import Literal

from pydantic import BaseModel


class Repository(BaseModel):
    name: str


class Pusher(BaseModel):
    name: str


class Commit(BaseModel):
    message: str


class GitHubWebhookPayload(BaseModel):
    repository: Repository
    pusher: Pusher
    commits: list[Commit]


# AI Code Review Schemas

class ReviewIssue(BaseModel):
    file: str
    line: int
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal[
        "bug",
        "security",
        "performance",
        "quality",
        "maintainability",
        "reliability"
    ]
    problem: str
    suggestion: str


class ReviewResponse(BaseModel):
    summary: str
    issues: list[ReviewIssue]
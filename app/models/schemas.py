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
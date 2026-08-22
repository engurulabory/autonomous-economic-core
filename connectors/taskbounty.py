from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://www.task-bounty.com/api/v1"


@dataclass(frozen=True)
class TaskBountyOpportunity:
    task_id: str
    title: str
    reward_usd: Decimal
    language: str | None
    github_issue_url: str | None
    state: str


class TaskBountyConnector:
    """Read-only discovery connector for TaskBounty.

    v0.1 deliberately implements discovery only. Claim/access/submission are
    external writes and stay behind Economic Authority + Human Threshold until
    an operator has explicitly accepted the platform terms and created a scoped
    solver credential.
    """

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 15) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def discover(self, *, language: str | None = None, limit: int = 25) -> list[TaskBountyOpportunity]:
        if limit <= 0 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        params: dict[str, Any] = {"state": "open", "limit": limit}
        if language:
            params["language"] = language

        request = Request(f"{API_BASE}/tasks?{urlencode(params)}")
        request.add_header("Accept", "application/json")
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")

        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - fixed HTTPS host
            payload = json.loads(response.read().decode("utf-8"))

        tasks = payload.get("tasks", [])
        return [self._normalize(task) for task in tasks if str(task.get("state", "open")).lower() == "open"]

    @staticmethod
    def _normalize(task: dict[str, Any]) -> TaskBountyOpportunity:
        task_id = str(task.get("id", "")).strip()
        title = str(task.get("title", "")).strip()
        if not task_id or not title:
            raise ValueError("TaskBounty task missing id/title")

        raw_reward = task.get("reward_usd", task.get("reward", task.get("amount_usd", "0")))
        reward = Decimal(str(raw_reward or "0"))
        if reward < 0:
            raise ValueError("reward cannot be negative")

        return TaskBountyOpportunity(
            task_id=task_id,
            title=title,
            reward_usd=reward,
            language=str(task.get("language")) if task.get("language") else None,
            github_issue_url=str(task.get("github_issue_url")) if task.get("github_issue_url") else None,
            state=str(task.get("state", "open")).lower(),
        )

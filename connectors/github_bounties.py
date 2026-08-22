from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API = "https://api.github.com/search/issues"


@dataclass(frozen=True)
class GitHubBounty:
    repo: str
    issue_number: int
    title: str
    url: str
    labels: tuple[str, ...]
    reward_hint: Decimal | None


class GitHubBountyConnector:
    """Read-only discovery for public GitHub issues that explicitly carry bounty labels.

    Search results are discovery evidence only. AEC must re-open the canonical issue and
    validate funding, claimability, automation policy, contribution rules and exact-action
    cost before any execution decision.
    """

    def __init__(self, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = timeout_seconds

    def discover(self, *, limit: int = 25) -> list[GitHubBounty]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        query = 'is:issue is:open label:bounty archived:false'
        url = f"{API}?{urlencode({'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': limit})}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AEC-revenue-mesh/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(url, headers=headers)
        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 fixed HTTPS
            payload = json.loads(response.read().decode("utf-8"))

        rows = payload.get("items", []) if isinstance(payload, dict) else []
        return [self._normalize(row) for row in rows if isinstance(row, dict)]

    @staticmethod
    def _normalize(row: dict[str, Any]) -> GitHubBounty:
        repo_url = str(row.get("repository_url", ""))
        repo = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else ""
        number = int(row.get("number", 0))
        title = str(row.get("title", "")).strip()
        html_url = str(row.get("html_url", "")).strip()
        if not repo or number <= 0 or not title or not html_url:
            raise ValueError("GitHub bounty result missing canonical identity")
        labels = tuple(
            str(label.get("name", "")).strip()
            for label in row.get("labels", [])
            if isinstance(label, dict) and str(label.get("name", "")).strip()
        )
        return GitHubBounty(
            repo=repo,
            issue_number=number,
            title=title,
            url=html_url,
            labels=labels,
            reward_hint=None,
        )

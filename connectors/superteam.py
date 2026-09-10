from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.request import Request, urlopen


PUBLIC_FEED = "https://earn.superteam.fun/api/listings?take=100"
AGENT_FEED = "https://superteam.fun/api/agents/listings/live?take=100"
AGENT_ACCESS = {"AGENT_ALLOWED", "AGENT_ONLY"}


@dataclass(frozen=True)
class SuperteamOpportunity:
    listing_id: str
    slug: str
    title: str
    reward: Decimal
    token: str | None
    deadline: str | None
    agent_access: str
    status: str


class SuperteamConnector:
    """Read-only discovery of Superteam Earn agent-eligible listings.

    When SUPERTEAM_AGENT_API_KEY is present, use Superteam's official agent listing
    endpoint so AGENT_ONLY opportunities can be discovered. Without a key, retain
    the public-feed fallback and still admit only AGENT_ALLOWED/AGENT_ONLY + OPEN.

    Registration, submission, human claiming, KYC and payout authority remain
    outside this read-only connector.
    """

    def __init__(self, timeout_seconds: int = 15, api_key: str | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key or os.getenv("SUPERTEAM_AGENT_API_KEY")

    def discover(self) -> list[SuperteamOpportunity]:
        url = AGENT_FEED if self.api_key else PUBLIC_FEED
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(url, headers=headers)
        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - fixed HTTPS hosts
            payload = json.loads(response.read().decode("utf-8"))

        rows = self._rows(payload)
        opportunities: list[SuperteamOpportunity] = []
        for row in rows:
            access = str(row.get("agentAccess", "")).upper()
            status = str(row.get("status", "")).upper()
            if access not in AGENT_ACCESS or status != "OPEN":
                continue
            opportunities.append(self._normalize(row))
        return opportunities

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("listings", payload.get("data", payload.get("items", [])))
        else:
            rows = []
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _normalize(row: dict[str, Any]) -> SuperteamOpportunity:
        listing_id = str(row.get("id", "")).strip()
        slug = str(row.get("slug", "")).strip()
        title = str(row.get("title", "")).strip()
        access = str(row.get("agentAccess", "")).upper()
        status = str(row.get("status", "")).upper()
        if not listing_id or not slug or not title:
            raise ValueError("Superteam listing missing id/slug/title")
        if access not in AGENT_ACCESS:
            raise ValueError("listing is not agent-eligible")
        if status != "OPEN":
            raise ValueError("listing is not open")

        raw_reward = row.get("rewardAmount", row.get("reward", row.get("totalCompensation", "0")))
        reward = Decimal(str(raw_reward or "0"))
        if reward < 0:
            raise ValueError("reward cannot be negative")

        token = row.get("token", row.get("currency"))
        return SuperteamOpportunity(
            listing_id=listing_id,
            slug=slug,
            title=title,
            reward=reward,
            token=str(token) if token else None,
            deadline=str(row.get("deadline")) if row.get("deadline") else None,
            agent_access=access,
            status=status,
        )

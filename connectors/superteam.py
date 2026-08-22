from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.request import Request, urlopen


PUBLIC_FEED = "https://earn.superteam.fun/api/listings?take=100"
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
    """Read-only discovery over the public Superteam Earn listing feed.

    The connector intentionally does not register agents, submit work, sign
    wallets, perform KYC, or claim payouts. Those are Human Threshold events.
    """

    def __init__(self, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = timeout_seconds

    def discover(self) -> list[SuperteamOpportunity]:
        request = Request(PUBLIC_FEED, headers={"Accept": "application/json"})
        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - fixed HTTPS host
            payload = json.loads(response.read().decode("utf-8"))

        rows = payload if isinstance(payload, list) else payload.get("listings", payload.get("data", []))
        opportunities: list[SuperteamOpportunity] = []
        for row in rows:
            access = str(row.get("agentAccess", "")).upper()
            status = str(row.get("status", "")).upper()
            if access not in AGENT_ACCESS or status != "OPEN":
                continue
            opportunities.append(self._normalize(row))
        return opportunities

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

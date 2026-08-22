from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class RemoteLease:
    resource_id: str
    owner_id: str
    lease_token: str
    expires_at: str


class RemoteStateClient:
    """Minimal authenticated client for the AEC durable-state gateway."""

    def __init__(self, base_url: str, token: str, timeout_seconds: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        if not self.base_url.startswith("https://"):
            raise ValueError("durable state endpoint must use HTTPS")
        if not token.strip():
            raise ValueError("durable state token is required")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health", auth=False)

    def reserve_idempotency(self, key: str, job_id: str) -> bool:
        payload = self._request("POST", "/idempotency/reserve", {"key": key, "job_id": job_id})
        return bool(payload.get("reserved"))

    def heartbeat(self, worker_id: str, detail: dict[str, Any] | None = None) -> None:
        self._request("POST", "/heartbeat", {"worker_id": worker_id, "detail": detail or {}})

    def acquire_lease(self, resource_id: str, owner_id: str, ttl_seconds: int = 120) -> RemoteLease | None:
        payload = self._request(
            "POST",
            "/lease/acquire",
            {"resource_id": resource_id, "owner_id": owner_id, "ttl_seconds": ttl_seconds},
        )
        if not payload.get("acquired"):
            return None
        return RemoteLease(resource_id, owner_id, str(payload["lease_token"]), str(payload["expires_at"]))

    def release_lease(self, lease: RemoteLease) -> bool:
        payload = self._request(
            "POST",
            "/lease/release",
            {
                "resource_id": lease.resource_id,
                "owner_id": lease.owner_id,
                "lease_token": lease.lease_token,
            },
        )
        return bool(payload.get("released"))

    def append_audit(self, actor: str, event: str, payload: dict[str, Any]) -> str:
        result = self._request("POST", "/audit/append", {"actor": actor, "event": event, "payload": payload})
        return str(result["event_hash"])

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, *, auth: bool = True) -> dict[str, Any]:
        data = None if body is None else json.dumps(body, sort_keys=True).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        with urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - caller-provided HTTPS endpoint
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("durable state response must be an object")
        return payload

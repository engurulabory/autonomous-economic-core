from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_API = "https://api.taskmarket.dev"
_TASK_ID = re.compile(r"^0x[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class TaskmarketTask:
    task_id: str
    description: str
    reward_usdc: Decimal
    net_reward_usdc: Decimal | None
    mode: str
    status: str
    phase: str | None
    expiry_time: str | None
    escrow_tx_hash: str | None
    submission_window_open: bool | None
    pending_actions: tuple[dict[str, Any], ...]
    raw: dict[str, Any]


def list_open_bounties(*, limit: int = 20, api_base: str = DEFAULT_API) -> list[TaskmarketTask]:
    """Read public open bounty inventory. No wallet, credential or paid route is used."""
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    query = urlencode({"status": "open", "mode": "bounty", "limit": limit})
    payload = _get_json(f"{api_base.rstrip('/')}/api/tasks?{query}")
    tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
    if not isinstance(tasks, list):
        raise ValueError("unexpected Taskmarket list response")
    return [_normalize_task(item) for item in tasks if isinstance(item, dict)]


def get_task(task_id: str, *, api_base: str = DEFAULT_API) -> TaskmarketTask:
    """Read one canonical Taskmarket task snapshot including pendingActions."""
    if not _TASK_ID.fullmatch(task_id):
        raise ValueError("task_id must be a 0x-prefixed 32-byte hex value")
    payload = _get_json(f"{api_base.rstrip('/')}/api/tasks/{task_id}")
    if not isinstance(payload, dict):
        raise ValueError("task not found or unexpected Taskmarket response")
    return _normalize_task(payload)


def _get_json(url: str) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "AEC-shadow-read/0.1"})
    with urlopen(request, timeout=15) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"Taskmarket read failed with HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def _normalize_task(item: dict[str, Any]) -> TaskmarketTask:
    reward = _usdc(item.get("reward"))
    net_reward = _optional_usdc(item.get("netReward"))
    pending = item.get("pendingActions") or []
    if not isinstance(pending, list):
        pending = []
    return TaskmarketTask(
        task_id=str(item.get("id", "")),
        description=str(item.get("description", "")),
        reward_usdc=reward,
        net_reward_usdc=net_reward,
        mode=str(item.get("mode", "")),
        status=str(item.get("status", "")),
        phase=str(item.get("phase")) if item.get("phase") is not None else None,
        expiry_time=str(item.get("expiryTime")) if item.get("expiryTime") is not None else None,
        escrow_tx_hash=str(item.get("escrowTxHash")) if item.get("escrowTxHash") else None,
        submission_window_open=item.get("submissionWindowOpen") if isinstance(item.get("submissionWindowOpen"), bool) else None,
        pending_actions=tuple(action for action in pending if isinstance(action, dict)),
        raw=item,
    )


def _usdc(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return (Decimal(str(value)) / Decimal("1000000")).quantize(Decimal("0.000001"))


def _optional_usdc(value: Any) -> Decimal | None:
    if value is None:
        return None
    return _usdc(value)

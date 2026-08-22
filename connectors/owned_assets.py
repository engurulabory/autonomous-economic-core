from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


DEFAULT_MANIFEST = Path("assets/revenue-assets.json")


@dataclass(frozen=True)
class OwnedAssetOpportunity:
    asset_id: str
    title: str
    canonical_url: str
    price_eur: Decimal
    active: bool
    delivery_ready: bool


class OwnedAssetConnector:
    """Local, zero-network adapter for AEC-owned digital assets.

    The manifest is public product metadata only. Credentials, payment-provider secrets,
    customer data and private financial records must never be stored in it.
    """

    def __init__(self, manifest_path: Path = DEFAULT_MANIFEST) -> None:
        self.manifest_path = manifest_path

    def discover(self) -> list[OwnedAssetOpportunity]:
        if not self.manifest_path.exists():
            return []
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        rows = payload.get("assets", []) if isinstance(payload, dict) else []
        opportunities: list[OwnedAssetOpportunity] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            item = self._normalize(row)
            if item.active and item.delivery_ready:
                opportunities.append(item)
        return opportunities

    @staticmethod
    def _normalize(row: dict[str, object]) -> OwnedAssetOpportunity:
        asset_id = str(row.get("id", "")).strip()
        title = str(row.get("title", "")).strip()
        canonical_url = str(row.get("canonical_url", "")).strip()
        if not asset_id or not title or not canonical_url:
            raise ValueError("owned asset missing id/title/canonical_url")
        price = Decimal(str(row.get("price_eur", "0")))
        if price < 0:
            raise ValueError("price_eur cannot be negative")
        return OwnedAssetOpportunity(
            asset_id=asset_id,
            title=title,
            canonical_url=canonical_url,
            price_eur=price,
            active=bool(row.get("active", False)),
            delivery_ready=bool(row.get("delivery_ready", False)),
        )

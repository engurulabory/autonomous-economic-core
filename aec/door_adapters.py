from __future__ import annotations

from decimal import Decimal

from aec.orchestrator import RevenueCandidate
from connectors.github_bounties import GitHubBountyConnector
from connectors.owned_assets import OwnedAssetConnector
from connectors.superteam import SuperteamConnector
from connectors.taskbounty import TaskBountyConnector
from connectors.taskmarket import list_open_bounties


class TaskmarketDoorAdapter:
    name = "taskmarket"
    door = "agent_native_bounties"

    def discover(self) -> list[RevenueCandidate]:
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id=task.task_id,
                title=task.description or task.task_id,
                canonical_url=f"https://taskmarket.dev/tasks/{task.task_id}",
                reward_amount=task.net_reward_usdc or task.reward_usdc,
                reward_currency="USDC",
                open_now=task.status.lower() == "open",
                zero_capital=None,
                agent_allowed=True,
                human_threshold_required=True,
                notes=("exact submit cost must be revalidated from pendingActions before write",),
            )
            for task in list_open_bounties(limit=20)
        ]


class SuperteamDoorAdapter:
    name = "superteam"
    door = "research_analysis_tasks"

    def discover(self) -> list[RevenueCandidate]:
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id=item.listing_id,
                title=item.title,
                canonical_url=f"https://earn.superteam.fun/listing/{item.slug}",
                reward_amount=item.reward,
                reward_currency=item.token,
                open_now=item.status == "OPEN",
                zero_capital=None,
                agent_allowed=True,
                human_threshold_required=True,
                notes=("listing-specific country, payout and public-action requirements remain fail-closed",),
            )
            for item in SuperteamConnector().discover()
        ]


class TaskBountyDoorAdapter:
    name = "taskbounty"
    door = "open_source_bug_bounties"

    def discover(self) -> list[RevenueCandidate]:
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id=item.task_id,
                title=item.title,
                canonical_url=item.github_issue_url or f"https://www.task-bounty.com/tasks/{item.task_id}",
                reward_amount=item.reward_usd,
                reward_currency="USD",
                open_now=item.state == "open",
                zero_capital=None,
                agent_allowed=None,
                human_threshold_required=True,
                notes=("canonical issue and automation policy must be verified before execution",),
            )
            for item in TaskBountyConnector().discover(limit=25)
        ]


class GitHubBountyDoorAdapter:
    name = "github_bounties"
    door = "documentation_bounties"

    def discover(self) -> list[RevenueCandidate]:
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id=f"{item.repo}#{item.issue_number}",
                title=item.title,
                canonical_url=item.url,
                reward_amount=item.reward_hint,
                reward_currency=None,
                open_now=True,
                zero_capital=None,
                agent_allowed=None,
                human_threshold_required=False,
                notes=("GitHub label is discovery evidence only; funding and claimability are unverified",),
            )
            for item in GitHubBountyConnector().discover(limit=25)
        ]


class OwnedAssetDoorAdapter:
    name = "owned_assets"
    door = "one_file_utilities"

    def discover(self) -> list[RevenueCandidate]:
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id=item.asset_id,
                title=item.title,
                canonical_url=item.canonical_url,
                reward_amount=item.price_eur,
                reward_currency="EUR",
                open_now=item.active,
                zero_capital=True,
                agent_allowed=True,
                human_threshold_required=False,
                notes=("sale channel and payment provider remain separate execution gates",),
            )
            for item in OwnedAssetConnector().discover()
        ]


FIRST_FIVE_ADAPTERS = (
    TaskmarketDoorAdapter(),
    SuperteamDoorAdapter(),
    TaskBountyDoorAdapter(),
    GitHubBountyDoorAdapter(),
    OwnedAssetDoorAdapter(),
)

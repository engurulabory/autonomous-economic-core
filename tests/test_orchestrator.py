from __future__ import annotations

import unittest
from decimal import Decimal

from aec.orchestrator import DoorCycleState, RevenueCandidate, run_cycle


class GoodAdapter:
    name = "good"
    door = "agent_native_bounties"

    def discover(self):
        return [
            RevenueCandidate(
                door=self.door,
                source=self.name,
                external_id="x1",
                title="Small paid task",
                canonical_url="https://example.com/tasks/x1",
                reward_amount=Decimal("1"),
                reward_currency="EUR",
                open_now=True,
                zero_capital=True,
                agent_allowed=True,
            )
        ]


class EmptyAdapter:
    name = "empty"
    door = "research_analysis_tasks"

    def discover(self):
        return []


class BrokenAdapter:
    name = "broken"
    door = "documentation_bounties"

    def discover(self):
        raise RuntimeError("provider timeout")


class OrchestratorTests(unittest.TestCase):
    def test_cycle_isolates_provider_failure(self):
        cycle = run_cycle((GoodAdapter(), BrokenAdapter(), EmptyAdapter()))
        self.assertEqual(cycle.candidate_count, 1)
        self.assertEqual(cycle.healthy_adapter_count, 1)
        self.assertEqual(cycle.results[0].state, DoorCycleState.PASS)
        self.assertEqual(cycle.results[1].state, DoorCycleState.BLOCKED)
        self.assertIn("provider timeout", cycle.results[1].error or "")
        self.assertEqual(cycle.results[2].state, DoorCycleState.HOLD)

    def test_candidate_rejects_negative_reward(self):
        with self.assertRaises(ValueError):
            RevenueCandidate(
                door="agent_native_bounties",
                source="x",
                external_id="1",
                title="bad",
                canonical_url="https://example.com",
                reward_amount=Decimal("-1"),
                reward_currency="EUR",
                open_now=True,
                zero_capital=True,
                agent_allowed=True,
            )


if __name__ == "__main__":
    unittest.main()

import unittest
from decimal import Decimal

from connectors.superteam import SuperteamConnector


class SuperteamConnectorTests(unittest.TestCase):
    def test_normalize_agent_allowed_open_listing(self):
        item = SuperteamConnector._normalize({
            "id": "st_1",
            "slug": "agent-task",
            "title": "Agent task",
            "agentAccess": "AGENT_ALLOWED",
            "status": "OPEN",
            "rewardAmount": "100",
            "token": "USDC",
            "deadline": "2026-08-28T21:59:59.000Z",
        })
        self.assertEqual(item.reward, Decimal("100"))
        self.assertEqual(item.agent_access, "AGENT_ALLOWED")

    def test_non_agent_listing_rejected(self):
        with self.assertRaises(ValueError):
            SuperteamConnector._normalize({
                "id": "st_2",
                "slug": "human-only",
                "title": "Human only",
                "agentAccess": "HUMAN_ONLY",
                "status": "OPEN",
            })

    def test_closed_listing_rejected(self):
        with self.assertRaises(ValueError):
            SuperteamConnector._normalize({
                "id": "st_3",
                "slug": "closed",
                "title": "Closed",
                "agentAccess": "AGENT_ALLOWED",
                "status": "CLOSED",
            })


if __name__ == "__main__":
    unittest.main()

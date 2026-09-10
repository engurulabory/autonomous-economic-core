from __future__ import annotations

import unittest

from aec.door_adapters import FIRST_FIVE_ADAPTERS
from aec.revenue_mesh import REVENUE_DOORS
from connectors.superteam import AGENT_FEED, PUBLIC_FEED, SuperteamConnector


class DoorAdapterRegistryTests(unittest.TestCase):
    def test_first_five_are_present_and_unique(self):
        self.assertEqual(len(FIRST_FIVE_ADAPTERS), 5)
        self.assertEqual(len({adapter.name for adapter in FIRST_FIVE_ADAPTERS}), 5)
        self.assertEqual(len({adapter.door for adapter in FIRST_FIVE_ADAPTERS}), 5)

    def test_first_five_map_to_known_revenue_doors(self):
        for adapter in FIRST_FIVE_ADAPTERS:
            self.assertIn(adapter.door, REVENUE_DOORS)

    def test_superteam_has_distinct_public_and_official_agent_feeds(self):
        self.assertNotEqual(PUBLIC_FEED, AGENT_FEED)
        self.assertIn("/api/agents/listings/live", AGENT_FEED)

    def test_superteam_connector_accepts_scoped_agent_key_without_exposing_it(self):
        connector = SuperteamConnector(api_key="sk_test_redacted")
        self.assertTrue(connector.api_key)
        self.assertNotIn("sk_test_redacted", repr(connector))

    def test_superteam_rows_accepts_supported_response_envelopes(self):
        row = {"id": "1"}
        self.assertEqual(SuperteamConnector._rows([row]), [row])
        self.assertEqual(SuperteamConnector._rows({"listings": [row]}), [row])
        self.assertEqual(SuperteamConnector._rows({"data": [row]}), [row])
        self.assertEqual(SuperteamConnector._rows({"items": [row]}), [row])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from aec.door_adapters import FIRST_FIVE_ADAPTERS
from aec.revenue_mesh import REVENUE_DOORS


class DoorAdapterRegistryTests(unittest.TestCase):
    def test_first_five_are_present_and_unique(self):
        self.assertEqual(len(FIRST_FIVE_ADAPTERS), 5)
        self.assertEqual(len({adapter.name for adapter in FIRST_FIVE_ADAPTERS}), 5)
        self.assertEqual(len({adapter.door for adapter in FIRST_FIVE_ADAPTERS}), 5)

    def test_first_five_map_to_known_revenue_doors(self):
        for adapter in FIRST_FIVE_ADAPTERS:
            self.assertIn(adapter.door, REVENUE_DOORS)


if __name__ == "__main__":
    unittest.main()

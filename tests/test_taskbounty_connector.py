import unittest
from decimal import Decimal

from connectors.taskbounty import TaskBountyConnector


class TaskBountyConnectorTests(unittest.TestCase):
    def test_normalize_task(self):
        item = TaskBountyConnector._normalize({
            "id": "tb_1",
            "title": "Fix pagination",
            "reward_usd": "42.50",
            "language": "python",
            "github_issue_url": "https://github.com/example/repo/issues/1",
            "state": "open",
        })
        self.assertEqual(item.task_id, "tb_1")
        self.assertEqual(item.reward_usd, Decimal("42.50"))
        self.assertEqual(item.state, "open")

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            TaskBountyConnector._normalize({"id": "", "title": "x"})

    def test_negative_reward_rejected(self):
        with self.assertRaises(ValueError):
            TaskBountyConnector._normalize({"id": "x", "title": "x", "reward": "-1"})


if __name__ == "__main__":
    unittest.main()

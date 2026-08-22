import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from connectors.taskmarket import get_task, list_open_bounties


class _Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TaskmarketConnectorTests(unittest.TestCase):
    @patch("connectors.taskmarket.urlopen")
    def test_list_open_bounties_normalizes_usdc(self, mocked):
        mocked.return_value = _Response(
            {
                "tasks": [
                    {
                        "id": "0x" + "a" * 64,
                        "description": "small task",
                        "reward": "2000000",
                        "netReward": "1850000",
                        "mode": "bounty",
                        "status": "open",
                        "phase": "active",
                    }
                ]
            }
        )
        tasks = list_open_bounties(limit=1)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].reward_usdc, Decimal("2.000000"))
        self.assertEqual(tasks[0].net_reward_usdc, Decimal("1.850000"))

    @patch("connectors.taskmarket.urlopen")
    def test_get_task_preserves_pending_actions(self, mocked):
        task_id = "0x" + "b" * 64
        mocked.return_value = _Response(
            {
                "id": task_id,
                "description": "work",
                "reward": "1000000",
                "mode": "bounty",
                "status": "open",
                "pendingActions": [
                    {"role": "worker", "action": "submit", "requiresPayment": False}
                ],
            }
        )
        task = get_task(task_id)
        self.assertEqual(task.pending_actions[0]["action"], "submit")

    def test_invalid_task_id_is_rejected(self):
        with self.assertRaises(ValueError):
            get_task("not-a-task-id")


if __name__ == "__main__":
    unittest.main()

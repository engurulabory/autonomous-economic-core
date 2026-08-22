from decimal import Decimal
import unittest

from aec.economic_execution import QualificationState, production_job_payload, qualify_candidate
from aec.orchestrator import RevenueCandidate


def candidate(**overrides):
    values = {
        "door": "one_file_utilities",
        "source": "owned_assets",
        "external_id": "asset-1",
        "title": "Utility",
        "canonical_url": "https://example.test/asset-1",
        "reward_amount": Decimal("1.00"),
        "reward_currency": "EUR",
        "open_now": True,
        "zero_capital": True,
        "agent_allowed": True,
        "human_threshold_required": False,
    }
    values.update(overrides)
    return RevenueCandidate(**values)


class EconomicExecutionTests(unittest.TestCase):
    def test_qualified_candidate_can_enter_internal_work(self):
        decision = qualify_candidate(candidate())
        self.assertEqual(decision.state, QualificationState.PASS)
        self.assertTrue(decision.can_enqueue_internal_work)

    def test_unknown_cost_holds_fail_closed(self):
        decision = qualify_candidate(candidate(zero_capital=None))
        self.assertEqual(decision.state, QualificationState.HOLD)
        self.assertFalse(decision.can_enqueue_internal_work)

    def test_positive_worker_cost_blocks(self):
        decision = qualify_candidate(candidate(zero_capital=False))
        self.assertEqual(decision.state, QualificationState.BLOCKED)

    def test_unknown_agent_policy_holds(self):
        self.assertEqual(qualify_candidate(candidate(agent_allowed=None)).state, QualificationState.HOLD)

    def test_closed_opportunity_blocks(self):
        self.assertEqual(qualify_candidate(candidate(open_now=False)).state, QualificationState.BLOCKED)

    def test_human_threshold_does_not_block_internal_production(self):
        decision = qualify_candidate(candidate(human_threshold_required=True))
        self.assertEqual(decision.state, QualificationState.PASS)
        self.assertTrue(decision.human_threshold_required)

    def test_payload_preserves_economic_context_without_authorizing_write(self):
        payload = production_job_payload(candidate(), output_path="deliverables/result.txt", content="verified draft")
        self.assertEqual(payload["economic_context"]["reward_currency"], "EUR")
        self.assertEqual(payload["economic_context"]["reward_amount"], "1.00")

    def test_payload_rejects_path_escape(self):
        with self.assertRaises(ValueError):
            production_job_payload(candidate(), output_path="../escape.txt", content="x")


if __name__ == "__main__":
    unittest.main()

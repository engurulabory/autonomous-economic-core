import unittest
from decimal import Decimal

from aec.field_execution_bridge import SubmissionHandoffState, build_field_execution_bridge
from aec.orchestrator import RevenueCandidate


def candidate(**overrides):
    values = {
        "door": "documentation_bounties",
        "source": "test",
        "external_id": "task-1",
        "title": "Small task",
        "canonical_url": "https://example.test/task-1",
        "reward_amount": Decimal("1.00"),
        "reward_currency": "GBP",
        "open_now": True,
        "zero_capital": True,
        "agent_allowed": True,
        "human_threshold_required": True,
    }
    values.update(overrides)
    return RevenueCandidate(**values)


class FieldExecutionBridgeTests(unittest.TestCase):
    def test_human_threshold_does_not_block_internal_production(self):
        bridge = build_field_execution_bridge(
            candidate(),
            qualification_evidence_id="qual-1",
            capability="docs-fix",
            output_path="deliverables/task-1.md",
            content="verified draft",
            acceptance_criteria=("matches requested scope", "no unsupported claims"),
            verification_instruction="Compare deliverable against the task acceptance criteria.",
            permitted_submission_route="platform-native submission",
        )
        self.assertFalse(bridge.internal_request.human_threshold_required)
        self.assertEqual(bridge.state, SubmissionHandoffState.HOLD_HUMAN_THRESHOLD)

    def test_authority_evidence_releases_permitted_submission_handoff(self):
        bridge = build_field_execution_bridge(
            candidate(),
            qualification_evidence_id="qual-1",
            capability="docs-fix",
            output_path="deliverables/task-1.md",
            content="verified draft",
            acceptance_criteria=("matches requested scope",),
            verification_instruction="Verify scope match.",
            permitted_submission_route="platform-native submission",
            authority_evidence_ref="human-release-001",
        )
        self.assertEqual(bridge.state, SubmissionHandoffState.READY_FOR_PERMITTED_SUBMISSION)

    def test_non_pass_candidate_is_rejected(self):
        with self.assertRaises(ValueError):
            build_field_execution_bridge(
                candidate(zero_capital=None),
                qualification_evidence_id="qual-1",
                capability="docs-fix",
                output_path="deliverables/task-1.md",
                content="verified draft",
                acceptance_criteria=("matches requested scope",),
                verification_instruction="Verify scope match.",
                permitted_submission_route="platform-native submission",
            )


if __name__ == "__main__":
    unittest.main()

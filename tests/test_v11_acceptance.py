from __future__ import annotations

import unittest

from aec.v11_acceptance import (
    ARCHITECTURE_GATES,
    ORCHESTRATOR_GATES,
    PERSISTENT_24_7_GATES,
    GateState,
    score_domain,
    score_v11,
)


class V11AcceptanceTests(unittest.TestCase):
    def test_all_evidence_is_required_for_100_pass(self):
        evidence = {gate: True for gate in ARCHITECTURE_GATES}
        result = score_domain("architecture", ARCHITECTURE_GATES, evidence)
        self.assertEqual(result.score_text, "100.0/100")
        self.assertEqual(result.state, GateState.PASS)
        self.assertEqual(result.missing, ())

    def test_missing_gate_keeps_domain_hold_below_100(self):
        evidence = {gate: True for gate in ARCHITECTURE_GATES}
        evidence.pop(ARCHITECTURE_GATES[-1])
        result = score_domain("architecture", ARCHITECTURE_GATES, evidence)
        self.assertEqual(result.state, GateState.HOLD)
        self.assertLess(result.score, 100)
        self.assertEqual(result.missing, (ARCHITECTURE_GATES[-1],))

    def test_explicit_blocked_gate_blocks_domain(self):
        evidence = {gate: True for gate in ORCHESTRATOR_GATES}
        evidence["exact_main_ci_pass"] = False
        result = score_domain("orchestrator", ORCHESTRATOR_GATES, evidence)
        self.assertEqual(result.state, GateState.BLOCKED)
        self.assertIn("exact_main_ci_pass", result.blocked)

    def test_full_v11_technical_scorecard(self):
        scorecard = score_v11(
            architecture={gate: "PASS" for gate in ARCHITECTURE_GATES},
            orchestrator={gate: "PASS" for gate in ORCHESTRATOR_GATES},
            persistent_24_7={gate: "PASS" for gate in PERSISTENT_24_7_GATES},
        )
        self.assertTrue(scorecard.all_pass())
        self.assertEqual(scorecard.architecture_governance.score_text, "100.0/100")
        self.assertEqual(scorecard.orchestrator_worker_runtime.score_text, "100.0/100")
        self.assertEqual(scorecard.persistent_24_7_execution.score_text, "100.0/100")

    def test_24_hour_observation_gate_cannot_be_inferred(self):
        evidence = {gate: True for gate in PERSISTENT_24_7_GATES}
        evidence["twenty_four_consecutive_hourly_pass_cycles"] = None
        result = score_domain("persistent", PERSISTENT_24_7_GATES, evidence)
        self.assertEqual(result.state, GateState.HOLD)
        self.assertIn("twenty_four_consecutive_hourly_pass_cycles", result.missing)


if __name__ == "__main__":
    unittest.main()

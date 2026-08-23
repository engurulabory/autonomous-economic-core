import unittest
from datetime import datetime, timezone
from decimal import Decimal

from aec.economic_field_core import (
    AcceptanceWindow,
    DecompositionRequest,
    DoorPerformance,
    EconomicEvidenceRecord,
    EconomicLearningLedger,
    FieldSafetyInput,
    FieldState,
    KarMatikStage,
    ParallelCapacity,
    SelectableOpportunity,
    bounded_concurrency,
    decompose_task,
    evaluate_acceptance_level,
    field_safety_gate,
    next_karmatik_stage,
    rank_revenue_doors,
    rank_smallest_profitable,
    DEFAULT_ACCEPTANCE_LEVELS,
)
from aec.micro_earning_policy import MicroEarningAssessment, MicroEarningState


def assessment(hourly: str, net: str = "0.01") -> MicroEarningAssessment:
    return MicroEarningAssessment(
        MicroEarningState.PASS,
        "ok",
        Decimal(net), Decimal("0"), Decimal(net), Decimal(net), Decimal(hourly),
        Decimal(net), Decimal("0"), Decimal(net), Decimal(net), Decimal(hourly),
        "EUR",
    )


class EconomicFieldCoreTests(unittest.TestCase):
    def test_p2_ranks_same_risk_by_higher_hourly_value(self):
        ranked = rank_smallest_profitable((
            SelectableOpportunity("slow", assessment("1"), Decimal("5"), Decimal("0.1")),
            SelectableOpportunity("fast", assessment("2"), Decimal("5"), Decimal("0.1")),
        ))
        self.assertEqual(ranked[0].opportunity_id, "fast")

    def test_p2_accepts_one_cent_positive_value(self):
        ranked = rank_smallest_profitable((
            SelectableOpportunity("cent", assessment("0.06", "0.01"), Decimal("10"), Decimal("0.1")),
        ))
        self.assertEqual(len(ranked), 1)

    def test_p3_decomposition_holds_when_permission_unknown(self):
        result = decompose_task(DecompositionRequest("t1", "qa", ("a",), None, True))
        self.assertEqual(result.state, FieldState.HOLD)

    def test_p3_decomposition_passes_with_explicit_permissions(self):
        result = decompose_task(DecompositionRequest("t1", "qa", ("one", "two"), True, True))
        self.assertEqual(result.state, FieldState.PASS)
        self.assertEqual(len(result.subtasks), 2)

    def test_p4_concurrency_is_bounded_and_excludes_human_jobs(self):
        self.assertEqual(bounded_concurrency(ParallelCapacity(10, 8, 5, 20, human_threshold_jobs=2)), 5)
        self.assertEqual(bounded_concurrency(ParallelCapacity(3, 8, 5, 20, human_threshold_jobs=2)), 1)

    def test_p5_ledger_rejects_duplicate_job_evidence(self):
        now = datetime.now(timezone.utc)
        ledger = EconomicLearningLedger()
        record = EconomicEvidenceRecord("j1", now)
        ledger.append(record)
        with self.assertRaises(ValueError):
            ledger.append(record)

    def test_p6_revenue_door_ranking_uses_economic_quality(self):
        ranked = rank_revenue_doors((
            DoorPerformance("weak", Decimal("1"), Decimal("0.5"), Decimal("0.5"), Decimal("60"), Decimal("1"), Decimal("1")),
            DoorPerformance("strong", Decimal("2"), Decimal("0.9"), Decimal("0.9"), Decimal("10"), Decimal("2"), Decimal("0.1")),
        ))
        self.assertEqual(ranked[0].door, "strong")

    def test_p7_karmatik_loop_is_canonical(self):
        self.assertEqual(next_karmatik_stage(KarMatikStage.WAKE), KarMatikStage.DISCOVER)
        self.assertEqual(next_karmatik_stage(KarMatikStage.REPEAT), KarMatikStage.WAKE)

    def test_p8_one_cent_requires_banked_value(self):
        one_cent = DEFAULT_ACCEPTANCE_LEVELS[0]
        self.assertEqual(evaluate_acceptance_level(AcceptanceWindow(Decimal("0.01"), Decimal("0"), 1, Decimal("0")), one_cent), FieldState.PASS)
        self.assertEqual(evaluate_acceptance_level(AcceptanceWindow(Decimal("0"), Decimal("10"), 20, Decimal("8")), one_cent), FieldState.HOLD)

    def test_p8_one_euro_hour_needs_sample_and_time_window(self):
        level = DEFAULT_ACCEPTANCE_LEVELS[3]
        self.assertEqual(evaluate_acceptance_level(AcceptanceWindow(Decimal("5"), Decimal("1.2"), 10, Decimal("4")), level), FieldState.PASS)
        self.assertEqual(evaluate_acceptance_level(AcceptanceWindow(Decimal("5"), Decimal("9"), 1, Decimal("0.1")), level), FieldState.HOLD)

    def test_p9_blocks_pay_to_work(self):
        result = field_safety_gate(FieldSafetyInput(True, False, False, False, False, False, True, True, Decimal("1"), Decimal("1"), Decimal("1")))
        self.assertEqual(result.state, FieldState.BLOCKED)

    def test_p9_low_confidence_long_job_is_deprioritized(self):
        result = field_safety_gate(FieldSafetyInput(False, False, False, False, False, False, True, True, Decimal("1"), Decimal("0.2"), Decimal("30")))
        self.assertEqual(result.state, FieldState.PASS)
        self.assertTrue(result.deprioritize)


if __name__ == "__main__":
    unittest.main()

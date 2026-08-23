import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aec.field_expansion_core import (
    ExpansionState,
    FleetJob,
    FleetWorker,
    MICRO_SERVICE_CATALOG,
    PaymentRail,
    PaymentRouteRequest,
    CompetitivePattern,
    canonical_micro_services,
    evaluate_pattern,
    route_payment,
    service_qualification,
    supervisor_plan,
)


class FieldExpansionCoreTests(unittest.TestCase):
    def test_p16_supervisor_assigns_capability_matched_jobs_with_bound(self):
        now = datetime.now(timezone.utc)
        workers = (
            FleetWorker("w1", "qa", frozenset({"web-qa"}), True, now, max_jobs=2),
            FleetWorker("w2", "research", frozenset({"research-mini"}), True, now),
        )
        jobs = (
            FleetJob("j1", "web-qa", False, "k1"),
            FleetJob("j2", "research-mini", False, "k2"),
            FleetJob("j3", "web-qa", True, "k3"),
        )
        plan = supervisor_plan(jobs, workers, now=now, global_concurrency_limit=2)
        self.assertEqual(plan.state, ExpansionState.PASS)
        self.assertEqual(len(plan.assignments), 2)
        self.assertNotIn("j3", {item.job_id for item in plan.assignments})

    def test_p16_duplicate_idempotency_is_blocked(self):
        now = datetime.now(timezone.utc)
        worker = FleetWorker("w", "qa", frozenset({"web-qa"}), True, now)
        jobs = (FleetJob("j1", "web-qa", False, "dup"), FleetJob("j2", "web-qa", False, "dup"))
        self.assertEqual(supervisor_plan(jobs, (worker,), now=now).state, ExpansionState.BLOCKED)

    def test_p17_anti_copy_gate_blocks_proprietary_copy(self):
        now = datetime.now(timezone.utc)
        pattern = CompetitivePattern("p", "source", now, "hypothesis", True, False, True, True, True, True, True, True)
        self.assertEqual(evaluate_pattern(pattern).state, ExpansionState.BLOCKED)

    def test_p17_full_evidence_allows_original_pattern_adoption(self):
        now = datetime.now(timezone.utc)
        pattern = CompetitivePattern("p", "source", now, "hypothesis", False, False, True, True, True, True, True, True)
        decision = evaluate_pattern(pattern)
        self.assertEqual(decision.state, ExpansionState.PASS)
        self.assertTrue(decision.adoptable)

    def test_p18_catalog_has_locked_three_plus_five_total(self):
        self.assertGreaterEqual(len(MICRO_SERVICE_CATALOG), 5)
        canonical = canonical_micro_services()
        self.assertEqual([item.service_id for item in canonical], ["research-verify", "structured-web-extract", "public-signal-monitor"])
        self.assertTrue(all(service_qualification(item) is ExpansionState.PASS for item in canonical))

    def test_p19_routes_to_best_verified_rail_without_executing_payment(self):
        rails = (
            PaymentRail("slow", frozenset({"micro-service"}), frozenset({"EUR", "USD"}), Decimal("0.02"), Decimal("0"), Decimal("0.99"), Decimal("1440"), Decimal("0.1"), True, True, True),
            PaymentRail("fast", frozenset({"micro-service"}), frozenset({"EUR", "USD"}), Decimal("0.03"), Decimal("0"), Decimal("0.99"), Decimal("10"), Decimal("0.1"), True, True, True),
        )
        decision = route_payment(PaymentRouteRequest("micro-service", "USD", Decimal("10")), rails)
        self.assertEqual(decision.state, ExpansionState.PASS)
        self.assertEqual(decision.rail.rail_id, "fast")
        self.assertTrue(decision.human_threshold_required)

    def test_p19_unknown_policy_holds_when_no_verified_route(self):
        rail = PaymentRail("unknown", frozenset({"door"}), frozenset({"EUR"}), Decimal("0"), Decimal("0"), Decimal("1"), Decimal("1"), Decimal("0"), None, True, True)
        decision = route_payment(PaymentRouteRequest("door", "EUR", Decimal("1")), (rail,))
        self.assertEqual(decision.state, ExpansionState.HOLD)


if __name__ == "__main__":
    unittest.main()

from decimal import Decimal

import pytest

from aec.economics import Judgment
from aec.swarm_economy import (
    EconomicGateInput,
    SettlementLedger,
    SwarmKind,
    evaluate_economic_gate,
    next_scale_target,
    plan_swarm_capacity,
)


def test_positive_net_candidate_passes():
    result = evaluate_economic_gate(
        EconomicGateInput(
            expected_gross_eur=Decimal("1.00"),
            compute_cost_eur=Decimal("0.10"),
            success_probability=Decimal("0.8"),
            collection_probability=Decimal("0.9"),
        )
    )
    assert result.judgment is Judgment.PASS
    assert result.expected_net_eur == Decimal("0.620")


def test_upfront_capital_is_blocked():
    result = evaluate_economic_gate(
        EconomicGateInput(expected_gross_eur=Decimal("10"), requires_upfront_capital=True)
    )
    assert result.judgment is Judgment.BLOCKED


def test_human_threshold_is_hold():
    result = evaluate_economic_gate(
        EconomicGateInput(expected_gross_eur=Decimal("10"), human_threshold_required=True)
    )
    assert result.judgment is Judgment.HOLD


def test_600_is_capacity_not_required_activity():
    plan = plan_swarm_capacity(
        {
            SwarmKind.CODE: 4,
            SwarmKind.RESEARCH: 12,
            SwarmKind.QA: 3,
        }
    )
    assert plan.total_active_slots == 19


def test_per_swarm_capacity_fails_closed():
    with pytest.raises(ValueError):
        plan_swarm_capacity({SwarmKind.DATA: 101})


def test_settlement_ledger_preserves_earned_settled_banked_truth():
    ledger = SettlementLedger(
        earned_eur=Decimal("5"),
        settled_eur=Decimal("3"),
        banked_eur=Decimal("2"),
    )
    assert ledger.banked_eur == Decimal("2")


def test_banked_cannot_exceed_settled():
    with pytest.raises(ValueError):
        SettlementLedger(
            earned_eur=Decimal("5"),
            settled_eur=Decimal("1"),
            banked_eur=Decimal("2"),
        )


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        ("0", "0.01"),
        ("0.01", "1"),
        ("1", "10"),
        ("10", "50"),
        ("50", "120"),
        ("120", "120"),
    ],
)
def test_scale_targets(current, expected):
    assert next_scale_target(Decimal(current)) == Decimal(expected)

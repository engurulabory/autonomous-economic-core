from aec.shariah_economic_guard import (
    ShariahEconomicOpportunity,
    ShariahEconomicState,
    assess_shariah_economic_guard,
    classify_revenue_doors,
)


def valid_opportunity(**overrides):
    values = {
        "opportunity_id": "door-1",
        "work_is_permissible": True,
        "real_value_or_service": True,
        "compensation_is_clear": True,
        "contains_riba": False,
        "contains_maysir": False,
        "contains_excessive_gharar": False,
        "contains_fraud_or_deception": False,
        "ownership_or_entitlement_is_clear": True,
        "payment_rail_is_approved": True,
        "requires_human_financial_authority": False,
    }
    values.update(overrides)
    return ShariahEconomicOpportunity(**values)


def test_verified_real_work_passes_guard():
    result = assess_shariah_economic_guard(valid_opportunity())
    assert result.state is ShariahEconomicState.PASS
    assert result.selectable is True


def test_riba_blocks_immediately():
    result = assess_shariah_economic_guard(valid_opportunity(contains_riba=True))
    assert result.state is ShariahEconomicState.BLOCKED
    assert result.selectable is False
    assert "riba" in result.reason.lower()


def test_maysir_blocks_immediately():
    result = assess_shariah_economic_guard(valid_opportunity(contains_maysir=True))
    assert result.state is ShariahEconomicState.BLOCKED


def test_fraud_blocks_immediately():
    result = assess_shariah_economic_guard(valid_opportunity(contains_fraud_or_deception=True))
    assert result.state is ShariahEconomicState.BLOCKED


def test_unknown_material_fact_fails_closed_to_hold():
    result = assess_shariah_economic_guard(valid_opportunity(payment_rail_is_approved=None))
    assert result.state is ShariahEconomicState.HOLD
    assert result.evidence_needed == ("payment rail approval",)


def test_human_financial_authority_never_auto_passes():
    result = assess_shariah_economic_guard(
        valid_opportunity(requires_human_financial_authority=True)
    )
    assert result.state is ShariahEconomicState.HOLD
    assert result.human_threshold_required is True
    assert result.evidence_needed == ("explicit human authorization",)


def test_revenue_door_batch_classifier_preserves_order_and_states():
    results = classify_revenue_doors(
        [
            valid_opportunity(opportunity_id="pass"),
            valid_opportunity(opportunity_id="hold", contains_excessive_gharar=None),
            valid_opportunity(opportunity_id="blocked", contains_maysir=True),
        ]
    )
    assert [item.opportunity_id for item in results] == ["pass", "hold", "blocked"]
    assert [item.state for item in results] == [
        ShariahEconomicState.PASS,
        ShariahEconomicState.HOLD,
        ShariahEconomicState.BLOCKED,
    ]

from src.analytics.cash_flow import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    capital_allocation_pattern,
)
import os
import pandas as pd


def test_free_cash_flow():
    assert free_cash_flow(100, -40) == 60


def test_free_cash_flow_negative():
    assert free_cash_flow(50, -100) == -50


def test_cfo_quality_high():
    result = cfo_quality_score(
        [120, 110, 130, 115, 125],
        [100, 100, 100, 100, 100],
    )

    assert result[1] == "High Quality"


def test_cfo_quality_zero_pat():
    assert cfo_quality_score([100], [0]) is None


def test_capex_intensity():
    result = capex_intensity(-50, 1000)

    assert result[0] == 5
    assert result[1] == "Moderate"


def test_capex_intensity_zero_sales():
    assert capex_intensity(-50, 0) is None


def test_fcf_conversion_rate():
    assert fcf_conversion_rate(50, 100) == 50


def test_fcf_conversion_zero_operating_profit():
    assert fcf_conversion_rate(50, 0) is None


def test_reinvestor_pattern():
    assert capital_allocation_pattern(100, -50, -20) == "Reinvestor"


def test_shareholder_returns_pattern():
    assert (
        capital_allocation_pattern(
            100,
            -50,
            -20,
            high_cfo_quality=True,
        )
        == "Shareholder Returns"
    )


def test_liquidating_assets_pattern():
    assert capital_allocation_pattern(100, 50, -20) == "Liquidating Assets"


def test_distress_signal_pattern():
    assert capital_allocation_pattern(-100, 50, 20) == "Distress Signal"


def test_growth_funded_by_debt_pattern():
    assert capital_allocation_pattern(-100, -50, 20) == "Growth Funded by Debt"


def test_cash_accumulator_pattern():
    assert capital_allocation_pattern(100, 50, 20) == "Cash Accumulator"


def test_pre_revenue_pattern():
    assert capital_allocation_pattern(-100, -50, -20) == "Pre-Revenue"


def test_mixed_pattern():
    assert capital_allocation_pattern(100, -50, 20) == "Mixed"



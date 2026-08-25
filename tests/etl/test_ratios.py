import logging

import pytest

from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    high_leverage_flag,
    icr_label,
    icr_warning_flag,
    interest_coverage_ratio,
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    roce_benchmark,
    debt_to_equity,
    net_debt,
    return_on_assets,
)


# 1. Normal Net Profit Margin
def test_net_profit_margin():
    assert net_profit_margin(200, 1000) == 20.0


# 2. Zero sales
def test_net_profit_margin_zero_sales():
    assert net_profit_margin(200, 0) is None


# 3. Normal OPM
def test_operating_profit_margin():
    assert operating_profit_margin(150, 1000) == 15.0


# 4. OPM zero sales
def test_operating_profit_margin_zero_sales():
    assert operating_profit_margin(150, 0) is None


# 5. OPM mismatch logging
def test_operating_profit_margin_mismatch(caplog):
    with caplog.at_level(logging.WARNING):
        result = operating_profit_margin(
            150,
            1000,
            reported_opm=12.0,
        )

    assert result == 15.0
    assert "OPM mismatch" in caplog.text


# 6. Negative equity
def test_return_on_equity_negative_equity():
    assert return_on_equity(100, -200, 50) is None


# 7. Normal ROCE
def test_return_on_capital_employed():
    assert return_on_capital_employed(
        200,
        500,
        300,
        200,
    ) == 20.0


# 8. Normal ROA
def test_return_on_assets():
    assert return_on_assets(100, 1000) == 10.0


# Additional edge-case tests
def test_return_on_equity_normal():
    assert return_on_equity(100, 400, 100) == 20.0


def test_return_on_capital_employed_zero_capital():
    assert return_on_capital_employed(
        100,
        0,
        0,
        0,
    ) is None


def test_return_on_assets_zero_assets():
    assert return_on_assets(100, 0) is None


def test_financials_roce_uses_sector_benchmark():
    assert roce_benchmark(
        18.0,
        "Financials",
        sector_benchmark=12.5,
    ) == 12.5


def test_non_financials_roce_uses_actual_roce():
    assert roce_benchmark(
        18.0,
        "Technology",
        sector_benchmark=12.5,
    ) == 18.0


# DAY 09 — LEVERAGE & EFFICIENCY


def test_debt_to_equity_debt_free():
    assert debt_to_equity(0, 100, 50) == 0


def test_debt_to_equity_normal():
    assert debt_to_equity(200, 100, 100) == 1


def test_debt_to_equity_negative_equity():
    assert debt_to_equity(100, -150, 50) is None


def test_high_leverage_flag():
    assert high_leverage_flag(6, "Industrials") is True
    assert high_leverage_flag(4, "Industrials") is False


def test_high_leverage_financials():
    assert high_leverage_flag(10, "Financials") is False


def test_interest_coverage_ratio():
    assert interest_coverage_ratio(100, 20, 10) == 12


def test_interest_coverage_ratio_zero_interest():
    assert interest_coverage_ratio(100, 20, 0) is None


def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"


def test_icr_warning_flag():
    assert icr_warning_flag(1.2) is True
    assert icr_warning_flag(2.0) is False


def test_net_debt():
    assert net_debt(100, 30) == 70


def test_asset_turnover():
    assert asset_turnover(500, 100) == 5


def test_asset_turnover_zero_assets():
    assert asset_turnover(500, 0) is None
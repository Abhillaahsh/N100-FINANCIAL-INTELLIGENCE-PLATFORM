import logging

import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    roce_benchmark,
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
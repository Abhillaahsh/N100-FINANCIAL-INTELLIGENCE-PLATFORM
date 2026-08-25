import pytest

from src.analytics.cagr import (
    calculate_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)


def test_normal_cagr():
    cagr, flag = calculate_cagr(100, 121, 2)

    assert cagr == pytest.approx(10.0, rel=1e-6)
    assert flag is None


def test_revenue_cagr():
    cagr, flag = revenue_cagr(100, 121, 2)

    assert cagr == pytest.approx(10.0, rel=1e-6)
    assert flag is None


def test_pat_cagr():
    cagr, flag = pat_cagr(200, 242, 2)

    assert cagr == pytest.approx(10.0, rel=1e-6)
    assert flag is None


def test_eps_cagr():
    cagr, flag = eps_cagr(50, 60.5, 2)

    assert cagr == pytest.approx(10.0, rel=1e-6)
    assert flag is None


def test_turnaround_flag():
    cagr, flag = calculate_cagr(-100, 50, 3)

    assert cagr is None
    assert flag == "TURNAROUND"


def test_decline_to_loss_flag():
    cagr, flag = calculate_cagr(100, -50, 3)

    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"


def test_both_negative_flag():
    cagr, flag = calculate_cagr(-100, -50, 3)

    assert cagr is None
    assert flag == "BOTH_NEGATIVE"


def test_zero_base_flag():
    cagr, flag = calculate_cagr(0, 100, 3)

    assert cagr is None
    assert flag == "ZERO_BASE"


def test_insufficient_data_flag():
    cagr, flag = calculate_cagr(100, 150, 0)

    assert cagr is None
    assert flag == "INSUFFICIENT"


def test_cagr_five_year():
    cagr, flag = calculate_cagr(100, 161.051, 5)

    assert cagr == pytest.approx(10.0, rel=1e-4)
    assert flag is None
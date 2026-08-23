"""
Nifty100 - Day 02
Tests for Excel loader and normalization functions.
"""

import pandas as pd
import pytest

from src.etl.loader import (
    load_excel,
    normalize_ticker,
    normalize_ticker_column,
    normalize_year,
    normalize_year_column,
)

# normalize_year() - 20 tests

@pytest.mark.parametrize(
    "value, expected",
    [
        ("Mar-23", "2023-03"),
        ("Mar 23", "2023-03"),
        ("March-2023", "2023-03"),
        ("2023", "2023-03"),
        (2023, "2023-03"),
        ("FY23", "2023-03"),
        ("FY2023", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("Jan-24", "2024-01"),
        ("February-2024", "2024-02"),
        ("Sep-23", "2023-09"),
        ("2023-03", "2023-03"),
        ("2023/03", "2023-03"),
        ("  Mar-23  ", "2023-03"),
        ("DEC-22", "2022-12"),
        ("FY 23", "2023-03"),
        (None, "PARSE_ERROR"),
        ("", "PARSE_ERROR"),
        ("garbage", "PARSE_ERROR"),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected


def test_normalize_year_invalid_month():
    assert normalize_year("2023-13") == "PARSE_ERROR"


def test_normalize_year_invalid_text():
    assert normalize_year("ABC-23") == "PARSE_ERROR"


def test_normalize_year_nan():
    assert normalize_year(float("nan")) == "PARSE_ERROR"


def test_normalize_year_nat():
    assert normalize_year(pd.NaT) == "PARSE_ERROR"

# normalize_ticker() - 20 tests

@pytest.mark.parametrize(
    "value, expected",
    [
        ("TCS", "TCS"),
        ("tcs", "TCS"),
        (" TCS", "TCS"),
        ("TCS ", "TCS"),
        (" TCS ", "TCS"),
        ("INFY", "INFY"),
        (" infy ", "INFY"),
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        ("M&M", "M&M"),
        ("m&m", "M&M"),
        ("HDFCBANK", "HDFCBANK"),
        ("RELIANCE", "RELIANCE"),
        ("ITC", "ITC"),
        ("SBIN", "SBIN"),
        ("MARUTI", "MARUTI"),
        ("AXISBANK", "AXISBANK"),
        ("ICICIBANK", "ICICIBANK"),
        (None, "MISSING"),
        ("", "MISSING"),
    ],
)
def test_normalize_ticker(value, expected):
    assert normalize_ticker(value) == expected


def test_normalize_ticker_nan():
    assert normalize_ticker(float("nan")) == "MISSING"


def test_normalize_ticker_whitespace_only():
    assert normalize_ticker("     ") == "MISSING"


def test_normalize_ticker_invalid_character():
    assert normalize_ticker("TCS@123") == "INVALID"


def test_normalize_ticker_preserves_hyphen():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"


def test_normalize_ticker_preserves_ampersand():
    assert normalize_ticker("m&m") == "M&M"

# DataFrame helper tests

def test_normalize_ticker_column():
    df = pd.DataFrame(
        {
            "company_id": [" tcs ", "infy", "M&M"],
        }
    )

    result = normalize_ticker_column(df)

    assert result["company_id"].tolist() == [
        "TCS",
        "INFY",
        "M&M",
    ]


def test_normalize_year_column():
    df = pd.DataFrame(
        {
            "year": ["Mar-23", "Dec-22", "FY24"],
        }
    )

    result = normalize_year_column(df)

    assert result["year"].tolist() == [
        "2023-03",
        "2022-12",
        "2024-03",
    ]


def test_normalize_ticker_column_does_not_mutate_original():
    df = pd.DataFrame(
        {
            "company_id": [" tcs "],
        }
    )

    result = normalize_ticker_column(df)

    assert df["company_id"].iloc[0] == " tcs "
    assert result["company_id"].iloc[0] == "TCS"


def test_normalize_year_column_does_not_mutate_original():
    df = pd.DataFrame(
        {
            "year": ["Mar-23"],
        }
    )

    result = normalize_year_column(df)

    assert df["year"].iloc[0] == "Mar-23"
    assert result["year"].iloc[0] == "2023-03"

# Loader tests

def test_load_excel_missing_file(tmp_path):
    missing_file = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        load_excel(missing_file)


def test_load_excel_invalid_extension(tmp_path):
    invalid_file = tmp_path / "data.txt"
    invalid_file.write_text("test")

    with pytest.raises(ValueError):
        load_excel(invalid_file)


def test_load_excel_reads_header_one(tmp_path):
    file_path = tmp_path / "test.xlsx"

    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["Mar-23"],
        }
    )

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # Simulate one metadata row above the actual header.
        pd.DataFrame([["metadata", "metadata"]]).to_excel(
            writer,
            index=False,
            header=False,
        )

        df.to_excel(
            writer,
            index=False,
            startrow=1,
        )

    result = load_excel(file_path, header=1)

    assert "company_id" in result.columns
    assert "year" in result.columns


def test_load_excel_strips_column_names(tmp_path):
    file_path = tmp_path / "test.xlsx"

    df = pd.DataFrame(
        {
            " company_id ": ["TCS"],
            " year ": ["Mar-23"],
        }
    )

    df.to_excel(file_path, index=False)

    result = load_excel(file_path, header=0)

    assert list(result.columns) == [
        "company_id",
        "year",
    ]
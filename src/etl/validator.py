# DAY 03 - SCHEMA VALIDATOR (16 DQ RULES)
#
# Implements DQ-01 through DQ-16 exactly as defined in the project
# spec (Section 22 - Data Quality Rules). Each function name and
# rule_id maps 1:1 to the spec's table. Rules are CRITICAL (should
# block/reject) or WARNING (flag only) per the spec's severity
# column; this script logs every violation to validation_failures.csv
# rather than mutating source files - actual rejection/dedup of
# CRITICAL rows happens in the loader (src/etl/loader.py).

import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


# PATHS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "raw"
SUPPORTING_DIR = PROJECT_ROOT / "data" / "supporting"
REPORTS_DIR = PROJECT_ROOT / "reports"

FAILURE_FILE = REPORTS_DIR / "validation_failures.csv"


# SOURCE FILES
#
# Core files use header=1 (row 0 is a metadata title row, per the
# spec's "Load note" in Section 5). Supporting files use header=0.

CORE_SOURCE_FILES = {
    "companies": DATA_DIR / "companies.xlsx",
    "profitandloss": DATA_DIR / "profitandloss.xlsx",
    "balancesheet": DATA_DIR / "balancesheet.xlsx",
    "cashflow": DATA_DIR / "cashflow.xlsx",
    "analysis": DATA_DIR / "analysis.xlsx",
    "documents": DATA_DIR / "documents.xlsx",
    "prosandcons": DATA_DIR / "prosandcons.xlsx",
}

SUPPORTING_SOURCE_FILES = {
    "sectors": SUPPORTING_DIR / "sectors.xlsx",
}


# FAILURE COLUMNS

FAILURE_COLUMNS = [
    "rule_id",
    "severity",
    "table_name",
    "company_id",
    "year",
    "field",
    "issue",
]

YEAR_PATTERN = re.compile(r"^\d{4}-\d{2}$")


# LOAD EXCEL

def load_excel(
    file_path: Path,
    header: int = 1,
) -> pd.DataFrame:

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    df = pd.read_excel(
        file_path,
        header=header,
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


def load_source_data() -> Dict[str, pd.DataFrame]:

    tables = {}

    for table_name, file_path in CORE_SOURCE_FILES.items():

        tables[table_name] = load_excel(
            file_path,
            header=1,
        )

    for table_name, file_path in SUPPORTING_SOURCE_FILES.items():

        if file_path.exists():

            tables[table_name] = load_excel(
                file_path,
                header=0,
            )

    return tables


# NORMALIZATION HELPERS
#
# Import directly from loader.py rather than maintaining a second
# copy. An earlier independent reimplementation here drifted from
# loader.py's behaviour on three real inputs found in the source
# data: bare 4-digit years ("2013" -> wrong month), "FY23"/"FY2023"/
# "FY 23" (broken FY-prefix handling), and "TTM" (a valid trailing-
# twelve-months period that loader.py deliberately keeps but this
# module was flagging as an unparseable CRITICAL DQ-07 failure).
# Importing keeps the validator honest to what the loader actually
# does, permanently, instead of needing the two kept in sync by hand.

import sys as _sys

_SRC_ETL_DIR = Path(__file__).resolve().parent

if str(_SRC_ETL_DIR) not in _sys.path:

    _sys.path.insert(0, str(_SRC_ETL_DIR))

from loader import (  # noqa: E402
    normalize_ticker as _loader_normalize_ticker,
    normalize_year,
)


def normalize_ticker(value) -> Optional[str]:
    """
    Thin wrapper over loader.normalize_ticker() that maps its
    MISSING sentinel back to None, matching this module's original
    Optional[str] contract used throughout the DQ rule functions
    below (e.g. orphan-FK / groupby checks skip on None).
    """

    result = _loader_normalize_ticker(value)

    if result == "MISSING":

        return None

    return result


# FAILURE LOGGING

def add_failure(
    failures: List[Dict],
    rule_id: str,
    severity: str,
    table_name: str,
    issue: str,
    company_id=None,
    year=None,
    field=None,
):

    failures.append(
        {
            "rule_id": rule_id,
            "severity": severity,
            "table_name": table_name,
            "company_id": company_id,
            "year": year,
            "field": field,
            "issue": issue,
        }
    )


def _row_company_id(df, idx):

    if "company_id" in df.columns:

        return normalize_ticker(
            df.loc[idx, "company_id"]
        )

    if "id" in df.columns:

        return normalize_ticker(
            df.loc[idx, "id"]
        )

    return None


def _row_year(df, idx):

    for col in ("year", "Year"):

        if col in df.columns:

            return df.loc[idx, col]

    return None


# DQ-01 - COMPANY PK UNIQUENESS (CRITICAL)
# len(companies) == companies.id.nunique()
# Action: Halt load. Investigate duplicate ticker.

def dq01_company_pk_uniqueness(tables, failures):

    df = tables.get("companies")

    if df is None:

        return

    if "id" not in df.columns:

        add_failure(
            failures,
            "DQ-01",
            "CRITICAL",
            "companies",
            "companies.xlsx has no 'id' column "
            "(cannot validate PK uniqueness)",
            field="id",
        )

        return

    ids = df["id"].apply(normalize_ticker)

    dupe_mask = ids.duplicated(keep=False)

    for idx in df.index[dupe_mask]:

        add_failure(
            failures,
            "DQ-01",
            "CRITICAL",
            "companies",
            "Duplicate company id (PK) - halt "
            "load, investigate duplicate ticker",
            company_id=ids.loc[idx],
            field="id",
        )


# DQ-02 - ANNUAL PK UNIQUENESS (CRITICAL)
# No duplicate (company_id, year) in P&L, BS, CF tables.
# Action: Deduplicate, keep last occurrence. Log all duplicates.

def dq02_annual_pk_uniqueness(tables, failures):

    for table_name in (
        "profitandloss",
        "balancesheet",
        "cashflow",
    ):

        df = tables.get(table_name)

        if df is None:

            continue

        if (
            "company_id" not in df.columns
            or "year" not in df.columns
        ):

            continue

        key = pd.DataFrame(
            {
                "company_id": df["company_id"].apply(
                    normalize_ticker
                ),
                "year": df["year"].apply(
                    normalize_year
                ),
            }
        )

        dupe_mask = key.duplicated(keep=False)

        for idx in df.index[dupe_mask]:

            add_failure(
                failures,
                "DQ-02",
                "CRITICAL",
                table_name,
                "Duplicate (company_id, year) pair "
                "- dedupe, keep last occurrence",
                company_id=key.loc[idx, "company_id"],
                year=key.loc[idx, "year"],
                field="company_id+year",
            )


# DQ-03 - FK INTEGRITY (CRITICAL)
# All company_id in child tables exist in companies.id.
# Action: Reject orphan rows. Log to validation_failures.csv.

def dq03_fk_integrity(tables, failures):

    companies = tables.get("companies")

    if companies is None or "id" not in companies.columns:

        return

    valid_ids = set(
        companies["id"]
        .apply(normalize_ticker)
        .dropna()
    )

    for table_name, df in tables.items():

        if table_name in ("companies", "sectors"):

            continue

        if "company_id" not in df.columns:

            continue

        cid = df["company_id"].apply(normalize_ticker)

        orphan_mask = cid.notna() & ~cid.isin(valid_ids)

        for idx in df.index[orphan_mask]:

            add_failure(
                failures,
                "DQ-03",
                "CRITICAL",
                table_name,
                "company_id not found in "
                "companies.id (orphan FK) - "
                "reject row",
                company_id=cid.loc[idx],
                year=_row_year(df, idx),
                field="company_id",
            )


# DQ-04 - BALANCE SHEET BALANCE (WARNING)
# |total_assets - total_liabilities| / total_assets < 0.01
# Action: Flag row. Do not reject. Analyst review required.

def dq04_balance_sheet_balance(tables, failures):

    df = tables.get("balancesheet")

    if df is None:

        return

    required = {"total_assets", "total_liabilities"}

    if not required.issubset(df.columns):

        return

    assets = pd.to_numeric(
        df["total_assets"], errors="coerce"
    )

    liabilities = pd.to_numeric(
        df["total_liabilities"], errors="coerce"
    )

    safe_assets = assets.replace(0, pd.NA)

    ratio = (
        (assets - liabilities).abs() / safe_assets
    )

    invalid = ratio.notna() & (ratio >= 0.01)

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-04",
            "WARNING",
            "balancesheet",
            f"total_assets vs total_liabilities "
            f"mismatch >= 1% (ratio="
            f"{ratio.loc[idx]:.4f}) - analyst "
            f"review required",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="total_assets",
        )


# DQ-05 - OPM CROSS-CHECK (WARNING)
# |opm_percentage - (op_profit/sales x 100)| < 1.0
# Action: Flag row. Use computed OPM in Ratio Engine.

def dq05_opm_cross_check(tables, failures):

    df = tables.get("profitandloss")

    if df is None:

        return

    required = {
        "opm_percentage",
        "operating_profit",
        "sales",
    }

    if not required.issubset(df.columns):

        return

    opm = pd.to_numeric(
        df["opm_percentage"], errors="coerce"
    )

    op_profit = pd.to_numeric(
        df["operating_profit"], errors="coerce"
    )

    sales = pd.to_numeric(
        df["sales"], errors="coerce"
    )

    computed = (
        op_profit / sales.replace(0, pd.NA)
    ) * 100

    diff = (opm - computed).abs()

    invalid = diff.notna() & (diff >= 1.0)

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-05",
            "WARNING",
            "profitandloss",
            f"opm_percentage differs from computed "
            f"OPM by >= 1.0 (diff="
            f"{diff.loc[idx]:.2f}) - use computed "
            f"value in Ratio Engine",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="opm_percentage",
        )


# DQ-06 - POSITIVE SALES (WARNING)
# sales > 0 for all non-bank companies.
# Action: Flag rows with sales <= 0. Exclude from growth CAGR.

def dq06_positive_sales(tables, failures):

    df = tables.get("profitandloss")

    if df is None or "sales" not in df.columns:

        return

    sales = pd.to_numeric(
        df["sales"], errors="coerce"
    )

    invalid = sales.notna() & (sales <= 0)

    bank_ids = set()

    sectors = tables.get("sectors")

    if (
        sectors is not None
        and "company_id" in sectors.columns
        and "broad_sector" in sectors.columns
    ):

        bank_ids = set(
            sectors.loc[
                sectors["broad_sector"]
                .astype(str)
                .str.contains(
                    "Financial",
                    case=False,
                    na=False,
                ),
                "company_id",
            ]
            .apply(normalize_ticker)
        )

    for idx in df.index[invalid]:

        cid = _row_company_id(df, idx)

        if cid in bank_ids:

            continue

        add_failure(
            failures,
            "DQ-06",
            "WARNING",
            "profitandloss",
            "sales <= 0 for non-bank company - "
            "exclude from growth CAGR",
            company_id=cid,
            year=_row_year(df, idx),
            field="sales",
        )


# DQ-07 - YEAR FORMAT (CRITICAL)
# After normalize_year(), all values match r'^\d{4}-\d{2}$'
# Action: Reject row if unparseable. Log raw value.

def dq07_year_format(tables, failures):

    for table_name, df in tables.items():

        year_col = None

        for col in ("year", "Year"):

            if col in df.columns:

                year_col = col

                break

        if year_col is None:

            continue

        for idx, raw in df[year_col].items():

            normalized = normalize_year(raw)

            # "TTM" (trailing twelve months) is a valid financial
            # reporting period, not a parse failure -- loader.py
            # keeps these rows, so DQ-07 must not flag them.
            if normalized == "TTM":

                continue

            if not YEAR_PATTERN.match(normalized):

                add_failure(
                    failures,
                    "DQ-07",
                    "CRITICAL",
                    table_name,
                    f"year value could not be "
                    f"normalized to YYYY-MM "
                    f"(raw={raw!r}) - reject row",
                    company_id=_row_company_id(
                        df, idx
                    ),
                    year=raw,
                    field=year_col,
                )


# DQ-08 - TICKER FORMAT (CRITICAL)
# company_id = strip().upper(). Length: 2-12 chars.
# Action: Normalise silently. If length out of range, reject.

def dq08_ticker_format(tables, failures):

    for table_name, df in tables.items():

        key = (
            "id"
            if table_name == "companies"
            else "company_id"
        )

        if key not in df.columns:

            continue

        for idx, raw in df[key].items():

            normalized = normalize_ticker(raw)

            if normalized is None:

                add_failure(
                    failures,
                    "DQ-08",
                    "CRITICAL",
                    table_name,
                    "ticker value is missing/blank "
                    "- reject row",
                    field=key,
                )

                continue

            if not (2 <= len(normalized) <= 12):

                add_failure(
                    failures,
                    "DQ-08",
                    "CRITICAL",
                    table_name,
                    f"ticker length out of range "
                    f"(2-12 chars): "
                    f"{normalized!r} - reject row",
                    company_id=normalized,
                    field=key,
                )


# DQ-09 - NET CASH CHECK (WARNING)
# |net_cash_flow - (CFO+CFI+CFF)| <= 10 (Cr tolerance)
# Action: Flag and compute net_cash_flow from components.

def dq09_net_cash_check(tables, failures):

    df = tables.get("cashflow")

    if df is None:

        return

    required = {
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    }

    if not required.issubset(df.columns):

        return

    cfo = pd.to_numeric(
        df["operating_activity"], errors="coerce"
    )

    cfi = pd.to_numeric(
        df["investing_activity"], errors="coerce"
    )

    cff = pd.to_numeric(
        df["financing_activity"], errors="coerce"
    )

    ncf = pd.to_numeric(
        df["net_cash_flow"], errors="coerce"
    )

    computed = cfo + cfi + cff

    diff = (ncf - computed).abs()

    invalid = diff.notna() & (diff > 10)

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-09",
            "WARNING",
            "cashflow",
            f"net_cash_flow does not match "
            f"CFO+CFI+CFF within 10 Cr tolerance "
            f"(diff={diff.loc[idx]:.2f}) - "
            f"recompute from components",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="net_cash_flow",
        )


# DQ-10 - NON-NEGATIVE FIXED ASSETS (WARNING)
# fixed_assets >= 0
# Action: Negative fixed_assets -> coerce to 0 and log.

def dq10_non_negative_fixed_assets(tables, failures):

    df = tables.get("balancesheet")

    if df is None or "fixed_assets" not in df.columns:

        return

    fa = pd.to_numeric(
        df["fixed_assets"], errors="coerce"
    )

    invalid = fa.notna() & (fa < 0)

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-10",
            "WARNING",
            "balancesheet",
            f"negative fixed_assets "
            f"({fa.loc[idx]:.2f}) - coerce to 0",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="fixed_assets",
        )


# DQ-11 - TAX RATE RANGE (WARNING)
# 0 <= tax_percentage <= 60
# Action: Flag out-of-range.

def dq11_tax_rate_range(tables, failures):

    df = tables.get("profitandloss")

    if df is None or "tax_percentage" not in df.columns:

        return

    tax = pd.to_numeric(
        df["tax_percentage"], errors="coerce"
    )

    invalid = tax.notna() & ((tax < 0) | (tax > 60))

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-11",
            "WARNING",
            "profitandloss",
            f"tax_percentage outside 0-60% range "
            f"({tax.loc[idx]:.2f}) - possible "
            f"one-off deferred tax reversal",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="tax_percentage",
        )


# DQ-12 - DIVIDEND PAYOUT CAP (WARNING)
# dividend_payout <= 200 (pct)
# Action: Flag >200% as likely data entry error.

def dq12_dividend_payout_cap(tables, failures):

    df = tables.get("profitandloss")

    if df is None or "dividend_payout" not in df.columns:

        return

    dp = pd.to_numeric(
        df["dividend_payout"], errors="coerce"
    )

    invalid = dp.notna() & (dp > 200)

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-12",
            "WARNING",
            "profitandloss",
            f"dividend_payout exceeds 200% "
            f"({dp.loc[idx]:.2f}) - likely data "
            f"entry error, analyst confirm",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="dividend_payout",
        )


# DQ-13 - URL VALIDITY (documents) (WARNING)
# requests.head(Annual_Report).status_code == 200
# Action: Log 404s. Do not reject row.
#
# Live HTTP checks are opt-in (check_live=True) since they need
# outbound network access to bseindia.com, which may be blocked in
# sandboxed/CI environments. Default just flags missing/malformed
# URLs.

def dq13_url_validity(tables, failures, check_live=False):

    df = tables.get("documents")

    if df is None or "Annual_Report" not in df.columns:

        return

    urls = df["Annual_Report"]

    malformed = urls.notna() & ~urls.astype(
        str
    ).str.match(r"^https?://", na=False)

    missing = urls.isna()

    for idx in df.index[missing | malformed]:

        add_failure(
            failures,
            "DQ-13",
            "WARNING",
            "documents",
            "Annual_Report URL missing or "
            "malformed",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="Annual_Report",
        )

    if not check_live:

        return

    import requests

    for idx, url in urls.items():

        if pd.isna(url):

            continue

        try:

            resp = requests.head(
                url,
                timeout=5,
                allow_redirects=True,
            )

            if resp.status_code != 200:

                add_failure(
                    failures,
                    "DQ-13",
                    "WARNING",
                    "documents",
                    f"Annual_Report URL returned "
                    f"HTTP {resp.status_code}",
                    company_id=_row_company_id(
                        df, idx
                    ),
                    year=_row_year(df, idx),
                    field="Annual_Report",
                )

        except Exception as error:

            add_failure(
                failures,
                "DQ-13",
                "WARNING",
                "documents",
                f"Annual_Report URL unreachable: "
                f"{error}",
                company_id=_row_company_id(df, idx),
                year=_row_year(df, idx),
                field="Annual_Report",
            )


# DQ-14 - EPS SIGN CONSISTENCY (WARNING)
# eps > 0 if net_profit > 0
# Action: Flag mismatch (may indicate adjustments).

def dq14_eps_sign_consistency(tables, failures):

    df = tables.get("profitandloss")

    if df is None:

        return

    required = {"eps", "net_profit"}

    if not required.issubset(df.columns):

        return

    eps = pd.to_numeric(
        df["eps"], errors="coerce"
    )

    net_profit = pd.to_numeric(
        df["net_profit"], errors="coerce"
    )

    invalid = (
        eps.notna()
        & net_profit.notna()
        & (net_profit > 0)
        & (eps <= 0)
    )

    for idx in df.index[invalid]:

        add_failure(
            failures,
            "DQ-14",
            "WARNING",
            "profitandloss",
            f"net_profit > 0 but eps <= 0 "
            f"(eps={eps.loc[idx]:.2f}, "
            f"net_profit="
            f"{net_profit.loc[idx]:.2f}) - "
            f"may indicate adjustments",
            company_id=_row_company_id(df, idx),
            year=_row_year(df, idx),
            field="eps",
        )


# DQ-15 - BSE/ASE BALANCE (ext.) (INFO)
# total_liabilities == total_assets (strict, after DQ-04 flag)
# Action: Informational counter. Flag in load_audit only.

def dq15_strict_balance_info(tables, failures):

    df = tables.get("balancesheet")

    if df is None:

        return

    required = {"total_assets", "total_liabilities"}

    if not required.issubset(df.columns):

        return

    assets = pd.to_numeric(
        df["total_assets"], errors="coerce"
    )

    liabilities = pd.to_numeric(
        df["total_liabilities"], errors="coerce"
    )

    mismatched = (
        assets.notna()
        & liabilities.notna()
        & (assets != liabilities)
    )

    count = int(mismatched.sum())

    if count > 0:

        add_failure(
            failures,
            "DQ-15",
            "INFO",
            "balancesheet",
            f"{count} row(s) where total_assets "
            f"!= total_liabilities exactly "
            f"(strict check, informational only)",
        )


# DQ-16 - COVERAGE CHECK (WARNING)
# Each company has >= 5 years of P&L, BS, CF records.
# Action: Flag companies with < 5yr history. Exclude from CAGR
# if < 3yr.

def dq16_coverage_check(tables, failures):

    for table_name in (
        "profitandloss",
        "balancesheet",
        "cashflow",
    ):

        df = tables.get(table_name)

        if df is None:

            continue

        if (
            "company_id" not in df.columns
            or "year" not in df.columns
        ):

            continue

        cid = df["company_id"].apply(
            normalize_ticker
        )

        yr = df["year"].apply(normalize_year)

        valid = yr != "PARSE_ERROR"

        coverage = pd.DataFrame(
            {"company_id": cid, "year": yr}
        )[valid].groupby(
            "company_id"
        )["year"].nunique()

        low_coverage = coverage[coverage < 5]

        for company_id, year_count in low_coverage.items():

            add_failure(
                failures,
                "DQ-16",
                "WARNING",
                table_name,
                f"only {year_count} year(s) of "
                f"{table_name} history (< 5yr "
                f"threshold; exclude from CAGR "
                f"if < 3yr)",
                company_id=company_id,
                field="year",
            )


# RUN DQ RULES

def run_dq_rules(
    tables: Dict[str, pd.DataFrame],
    check_live_urls: bool = False,
) -> List[Dict]:

    failures: List[Dict] = []

    dq01_company_pk_uniqueness(tables, failures)
    dq02_annual_pk_uniqueness(tables, failures)
    dq03_fk_integrity(tables, failures)
    dq04_balance_sheet_balance(tables, failures)
    dq05_opm_cross_check(tables, failures)
    dq06_positive_sales(tables, failures)
    dq07_year_format(tables, failures)
    dq08_ticker_format(tables, failures)
    dq09_net_cash_check(tables, failures)
    dq10_non_negative_fixed_assets(tables, failures)
    dq11_tax_rate_range(tables, failures)
    dq12_dividend_payout_cap(tables, failures)
    dq13_url_validity(
        tables, failures, check_live=check_live_urls
    )
    dq14_eps_sign_consistency(tables, failures)
    dq15_strict_balance_info(tables, failures)
    dq16_coverage_check(tables, failures)

    return failures


# SAVE FAILURES

def save_validation_failures(
    failures: List[Dict],
) -> Path:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.DataFrame(
        failures,
        columns=FAILURE_COLUMNS,
    )

    df.to_csv(
        FAILURE_FILE,
        index=False,
    )

    return FAILURE_FILE


# MAIN

def main():

    print("Nifty100 Day 03 - Schema Validator")

    print("DQ-01 through DQ-16")

    print()

    print("Loading source data...")

    tables = load_source_data()

    print("Running validation...")

    failures = run_dq_rules(tables)

    output = save_validation_failures(failures)

    print()

    print(
        f"Validation complete: {len(failures)} "
        f"total failure(s) logged"
    )

    by_rule = pd.DataFrame(
        failures, columns=FAILURE_COLUMNS
    )

    if not by_rule.empty:

        print()

        print("By rule:")

        print(
            by_rule["rule_id"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        print()

        print("By severity:")

        print(
            by_rule["severity"]
            .value_counts()
            .to_string()
        )

    print()

    print(f"Output: {output}")


if __name__ == "__main__":

    main()
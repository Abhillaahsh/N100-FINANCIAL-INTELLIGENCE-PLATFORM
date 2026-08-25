# DAY 02 - EXCEL LOADER & NORMALISER

import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd


# PROJECT PATHS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
AUDIT_FILE = REPORTS_DIR / "load_audit.csv"


def normalize_year(value) -> str:
    """
    Normalize financial period values.

    Supported examples:
        Mar-23       -> 2023-03
        Mar 23       -> 2023-03
        March-2023   -> 2023-03
        FY23         -> 2023-03
        FY2023       -> 2023-03
        2023/03      -> 2023-03
        Mar 2024     -> 2024-03
        Dec 2023     -> 2023-12
        Jun 2019     -> 2019-06
        Sep 2020     -> 2020-09
        TTM          -> TTM

    Returns:
        Normalized YYYY-MM string, TTM, or PARSE_ERROR.
    """

    if value is None or pd.isna(value):
        return "PARSE_ERROR"

    text = str(value).strip()

    if not text:
         return "PARSE_ERROR"


    # TTM is a valid financial reporting period.
    # Do NOT drop it as DQ-07.

    if text.upper() == "TTM":
        return "TTM"

    
    # Clean separators

    text = text.replace("/", "-")
    text = text.replace("_", "-")

    # Remove common FY prefix
    upper_text = text.upper()

    if upper_text.startswith("FY"):
        text = text[2:].strip()

        # FY23 / FY2023 -> March financial year
        if text.isdigit():

            year_num = int(text)

            if len(text) == 2:
                year_num += 2000

            if len(str(year_num)) == 4:
                return f"{year_num:04d}-03"

    
    # Bare 4-digit year (e.g. "2023", or int 2023) with no month
    # or FY prefix -> assume March financial year close.
    # Must be checked before the pandas fallback below, since
    # pd.to_datetime() misreads a bare 4-digit *integer* as a
    # nanosecond timestamp (-> ~1970) rather than a calendar year.

    if text.isdigit() and len(text) == 4:
        return f"{int(text):04d}-03"

    # Direct YYYY-MM
    
    parts = text.split("-")

    if len(parts) == 2:

        first = parts[0].strip()
        second = parts[1].strip()

        if first.isdigit() and len(first) == 4:

            try:
                month = int(second)

                if 1 <= month <= 12:
                    return f"{int(first):04d}-{month:02d}"

            except ValueError:
                pass

    # ---------------------------------------------------------
    # Month + year formats
    #
    # Mar 2024
    # March 2024
    # Mar-2024
    # Mar 24
    # ---------------------------------------------------------
    normalized = text.replace("-", " ")

    tokens = normalized.split()

    if len(tokens) >= 2:

        month_text = tokens[0].strip().lower()
        year_text = tokens[1].strip()

        month_map = {
            "jan": 1,
            "january": 1,
            "feb": 2,
            "february": 2,
            "mar": 3,
            "march": 3,
            "apr": 4,
            "april": 4,
            "may": 5,
            "jun": 6,
            "june": 6,
            "jul": 7,
            "july": 7,
            "aug": 8,
            "august": 8,
            "sep": 9,
            "sept": 9,
            "september": 9,
            "oct": 10,
            "october": 10,
            "nov": 11,
            "november": 11,
            "dec": 12,
            "december": 12,
        }

        if month_text in month_map and year_text.isdigit():

            year_num = int(year_text)

            if len(year_text) == 2:
                year_num += 2000

            if len(str(year_num)) == 4:
                month_num = month_map[month_text]

                return f"{year_num:04d}-{month_num:02d}"

    # Pandas fallback for real Excel dates

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if not pd.isna(parsed):

        return parsed.strftime("%Y-%m")

   
    return "PARSE_ERROR"

# DAY 02 - NORMALIZE TICKER

def normalize_ticker(value) -> str:
    """
    Normalize company ticker symbols.

    Examples:
        tcs        -> TCS
        " TCS "    -> TCS
        "TCS -"    -> TCS
        bajaj-auto -> BAJAJ-AUTO
        m&m        -> M&M
    """

    if value is None or pd.isna(value):

        return "MISSING"

    text = str(value).strip().upper()

    if not text:

        return "MISSING"

    text = "-".join(
        part.strip()
        for part in text.split("-")
    )

    text = "&".join(
        part.strip()
        for part in text.split("&")
    )

    if not all(
        char.isalnum() or char in "-&"
        for char in text
    ):

        return "INVALID"

    return text


# DAY 02 - LOAD EXCEL

def load_excel(
    file_path,
    sheet_name=0,
    header=0,
) -> pd.DataFrame:
    """
    Load an Excel file and normalize column names.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Excel file not found: {path}"
        )

    if path.suffix.lower() not in {
        ".xlsx",
        ".xls",
    }:

        raise ValueError(
            f"Unsupported file extension: {path.suffix}"
        )

    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        header=header,
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# DAY 02 - NORMALIZE YEAR COLUMN

def normalize_year_column(
    df: pd.DataFrame,
    column: str = "year",
) -> pd.DataFrame:
    """
    Return a copy of the DataFrame with
    the year column normalized.
    """

    result = df.copy()

    if column not in result.columns:

        raise KeyError(
            f"Column not found: {column}"
        )

    result[column] = result[column].apply(
        normalize_year
    )

    return result


# DAY 02 - NORMALIZE TICKER COLUMN

def normalize_ticker_column(
    df: pd.DataFrame,
    column: str = "company_id",
) -> pd.DataFrame:
    """
    Return a copy of the DataFrame with
    company_id values normalized.
    """

    result = df.copy()

    if column not in result.columns:

        raise KeyError(
            f"Column not found: {column}"
        )

    result[column] = result[column].apply(
        normalize_ticker
    )

    return result


# DAY 04 - SQLITE DATABASE CONNECTION

def get_db_connection():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# DAY 04 - BASIC DATAFRAME LOADER

def load_dataframe_to_db(
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """
    Load a DataFrame into a SQLite table.
    """

    conn = get_db_connection()

    try:

        df.to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()

    finally:

        conn.close()


 # DAY 05 - FULL DATA LOAD
 
PROJECT_ROOT = Path(__file__).resolve().parents[2]
 
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
AUDIT_FILE = REPORTS_DIR / "load_audit.csv"
 
 
LOAD_ORDER = [
    ("companies", "raw/companies.xlsx"),
    ("profitandloss", "raw/profitandloss.xlsx"),
    ("balancesheet", "raw/balancesheet.xlsx"),
    ("cashflow", "raw/cashflow.xlsx"),
    ("analysis", "raw/analysis.xlsx"),
    ("documents", "raw/documents.xlsx"),
    ("prosandcons", "raw/prosandcons.xlsx"),
 
    ("financial_ratios", "supporting/financial_ratios.xlsx"),
    ("peer_groups", "supporting/peer_groups.xlsx"),
    ("sectors", "supporting/sectors.xlsx"),
    ("market_cap", "supporting/market_cap.xlsx"),
    ("stock_prices", "supporting/stock_prices.xlsx"),
]
 
 
def get_db_connection():
 
    conn = sqlite3.connect(DB_PATH)
 
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )
 
    return conn
 
 
def normalize_columns(df):
 
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]
 
    return df
 
 
# DAY 05 - KNOWN SOURCE-DATA TYPOS
#
# companies.xlsx uses the correct ticker on the left; some child
# files contain a data-entry typo (right) that must be corrected
# to the same value so FK matching works. Add new corrections here
# as they're discovered via check_missing_company_ids().

KNOWN_TICKER_CORRECTIONS = {
    "AGTL": "ATGL",
}


def normalize_company_id(value):
 
    if pd.isna(value):
        return None
 
    text = str(value).strip().upper()
 
    if not text:
        return None

    text = KNOWN_TICKER_CORRECTIONS.get(
        text,
        text,
    )
 
    return text
 
 
def find_header_row(file_path):
 
    preview = pd.read_excel(
        file_path,
        header=None,
        nrows=10,
    )
 
    expected_columns = {
        "companies": {
            "id",
            "company_name",
            "nse_profile",
        },
 
        "profitandloss": {
            "id",
            "company_id",
            "year",
            "sales",
        },
 
        "balancesheet": {
            "id",
            "company_id",
            "year",
        },
 
        "cashflow": {
            "id",
            "company_id",
            "year",
        },
 
        "analysis": {
            "id",
            "company_id",
        },
 
        "documents": {
            "id",
            "company_id",
        },
 
        "prosandcons": {
            "id",
            "company_id",
        },
    }
 
    filename = Path(file_path).stem
 
    expected = expected_columns.get(
        filename
    )
 
    if expected is None:
 
        return 0
 
    for row_number in range(
        len(preview)
    ):
 
        values = {
            str(value).strip()
            for value in preview.iloc[row_number]
            if not pd.isna(value)
        }
 
        matches = expected.intersection(
            values
        )
 
        if len(matches) >= 2:
 
            return row_number
 
    return 0
 
 
def read_excel_file(file_path):
 
    filename = Path(file_path).stem
 
    if filename in {
        "financial_ratios",
        "peer_groups",
        "sectors",
        "market_cap",
        "stock_prices",
    }:
 
        header = 0
 
    else:
 
        header = find_header_row(
            file_path
        )
 
    print(
        f"  Reading {filename}.xlsx "
        f"with header row {header}"
    )
 
    df = pd.read_excel(
        file_path,
        header=header,
    )
 
    df = normalize_columns(
        df
    )
 
    return df
 
 
def prepare_companies(df):
 
    if "id" not in df.columns:
 
        raise KeyError(
            "id column not found in companies.xlsx"
        )
 
    df["id"] = (
        df["id"]
        .apply(normalize_company_id)
    )
 
    df = df.dropna(
        subset=["id"]
    )
 
    df = df.drop_duplicates(
        subset=["id"],
        keep="first",
    )
 
    return df


def collect_all_child_company_ids():
    """
    Scan every child file in LOAD_ORDER and collect the full set
    of normalized company_id values referenced anywhere, purely
    for the pre-load diagnostic report (check_missing_company_ids).
    """

    all_ids = set()

    for table_name, relative_path in LOAD_ORDER:

        if table_name == "companies":

            continue

        file_path = DATA_DIR / relative_path

        if not file_path.exists():

            continue

        df = read_excel_file(
            file_path
        )

        if "company_id" not in df.columns:

            continue

        ids = (
            df["company_id"]
            .apply(normalize_company_id)
            .dropna()
        )

        all_ids.update(ids)

    return all_ids


# DAY 03/05 - DQ-03 (FK INTEGRITY, CRITICAL)
#
# Per the project spec: company_id values in child tables that do
# not exist in companies.id are orphan rows. They must be REJECTED
# (not loaded, not stubbed into companies) and logged to
# validation_failures.csv with company_id, year, field, issue,
# severity. companies.xlsx itself is the fixed 92-company universe
# (AC-01: exactly 92, no extra or missing tickers) — child tables
# are trimmed to match it, never the other way around.

DQ_FAILURES = []


def log_dq_failure(
    table_name,
    company_id,
    year,
    issue,
    field="company_id",
    severity="CRITICAL",
):

    DQ_FAILURES.append(
        {
            "table_name": table_name,
            "company_id": company_id,
            "year": year,
            "field": field,
            "issue": issue,
            "severity": severity,
        }
    )


def write_validation_failures():

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        REPORTS_DIR /
        "validation_failures.csv"
    )

    columns = [
        "table_name",
        "company_id",
        "year",
        "field",
        "issue",
        "severity",
    ]

    pd.DataFrame(
        DQ_FAILURES,
        columns=columns,
    ).to_csv(
        path,
        index=False,
    )

    return path
 
 
def prepare_child_table(
    df,
    valid_company_ids=None,
    table_name=None,
):
    """Apply Day-05 data-quality rules before loading a child table."""

    df = df.copy()

    # DQ-08: normalize company IDs
    if "company_id" in df.columns:
        df["company_id"] = (
            df["company_id"]
            .apply(normalize_company_id)
        )

    # DQ-07: normalize year and reject unparseable values.
    if "year" in df.columns:
        raw_year = df["year"].copy()

        print("    Normalizing year column")

        df["year"] = (
            df["year"]
            .apply(normalize_year)
        )

        bad_year_mask = (
            df["year"] == "PARSE_ERROR"
        )

        if bad_year_mask.any():
            for idx in df[bad_year_mask].index:
                log_dq_failure(
                    table_name=table_name or "unknown",
                    company_id=(
                        df.loc[idx, "company_id"]
                        if "company_id" in df.columns
                        else None
                    ),
                    year=raw_year.loc[idx],
                    field="year",
                    issue=(
                        "DQ-07: year value could not be "
                        "parsed to YYYY-MM (rejected)"
                    ),
                    severity="CRITICAL",
                )

            dropped = int(bad_year_mask.sum())
            print(
                f"    dropped {dropped} row(s) with "
                f"unparseable year (DQ-07)"
            )

            df = df[~bad_year_mask].copy()

    # DQ-02: ONLY P&L, Balance Sheet and Cash Flow.
    # Keep LAST occurrence and log every dropped duplicate.
    if (
        table_name in {
            "profitandloss",
            "balancesheet",
            "cashflow",
        }
        and "company_id" in df.columns
        and "year" in df.columns
    ):
        dupe_mask = df.duplicated(
            subset=["company_id", "year"],
            keep="last",
        )

        if dupe_mask.any():
            for _, row in df[dupe_mask].iterrows():
                log_dq_failure(
                    table_name=table_name,
                    company_id=row["company_id"],
                    year=row["year"],
                    field="company_id+year",
                    issue=(
                        "DQ-02: duplicate (company_id, year) "
                        "pair (kept last occurrence, dropped "
                        "this one)"
                    ),
                    severity="CRITICAL",
                )

            dropped = int(dupe_mask.sum())
            print(
                f"    dropped {dropped} duplicate "
                f"(company_id, year) row(s) (DQ-02)"
            )

            df = df[~dupe_mask].copy()

    # DQ-03: reject orphan company IDs from ALL child tables.
    # Never add these companies to the fixed 92-company universe.
    if (
        "company_id" in df.columns
        and valid_company_ids is not None
    ):
        orphan_mask = ~df["company_id"].isin(
            valid_company_ids
        )

        if orphan_mask.any():
            year_col = (
                "year"
                if "year" in df.columns
                else None
            )

            for _, row in df[orphan_mask].iterrows():
                log_dq_failure(
                    table_name=table_name or "unknown",
                    company_id=row["company_id"],
                    year=(
                        row[year_col]
                        if year_col
                        else None
                    ),
                    field="company_id",
                    issue=(
                        "DQ-03: company_id not found in "
                        "companies.id (orphan FK, rejected)"
                    ),
                    severity="CRITICAL",
                )

            dropped = int(orphan_mask.sum())
            print(
                f"    dropped {dropped} row(s) with "
                f"company_id not in companies table "
                f"(DQ-03, logged to "
                f"validation_failures.csv)"
            )

            df = df[~orphan_mask].copy()

    return df


def prepare_documents(df, valid_company_ids=None, table_name=None):
 
    if "Year" in df.columns:
 
        df = df.rename(
            columns={
                "Year": "year"
            }
        )
 
    if "Annual_Report" in df.columns:
 
        df = df.rename(
            columns={
                "Annual_Report": "annual_report"
            }
        )
 
    return prepare_child_table(
        df,
        valid_company_ids,
        table_name,
    )
 
 
def prepare_dataframe(
    table_name,
    df,
    valid_company_ids=None,
):
 
    if table_name == "companies":
 
        return prepare_companies(
            df
        )
 
    if table_name == "documents":
 
        return prepare_documents(
            df,
            valid_company_ids,
            table_name,
        )
 
    return prepare_child_table(
        df,
        valid_company_ids,
        table_name,
    )
 
 
def load_table(
    table_name,
    relative_path,
    valid_company_ids=None,
):
    """
    Returns (rows_in, rows_out) where:
      rows_in  = raw row count read straight from the source Excel
                 file, before any DQ cleaning (matches the project
                 doc's dataset catalogue counts, e.g. P&L = 1,276).
      rows_out = row count actually written to SQLite after DQ-02
                 (dedup) and DQ-03 (orphan FK rejection) are applied.
    """

    file_path = (
        DATA_DIR /
        relative_path
    )
 
    if not file_path.exists():
 
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )
 
    df = read_excel_file(
        file_path
    )

    rows_in = len(df)
 
    df = prepare_dataframe(
        table_name,
        df,
        valid_company_ids,
    )

    rows_out = len(df)
 
    conn = get_db_connection()
 
    try:
 
        df.to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False,
        )
 
        conn.commit()
 
        return rows_in, rows_out
 
    finally:
 
        conn.close()
 
 
def get_row_count(
    table_name
):
 
    conn = get_db_connection()
 
    try:
 
        result = conn.execute(
            f"SELECT COUNT(*) "
            f"FROM {table_name}"
        ).fetchone()
 
        return result[0]
 
    finally:
 
        conn.close()
 
 
def check_missing_company_ids():
    """
    DAY 05 - DIAGNOSTIC
 
    For every child file in LOAD_ORDER (except companies itself),
    compare its company_id values against the ids present in
    companies.xlsx. Prints any company_id that appears in a child
    file but is missing from companies.xlsx, so source-data gaps
    are caught before FK constraints reject the whole table load.
    """
 
    companies_path = DATA_DIR / "raw/companies.xlsx"
 
    companies_df = read_excel_file(
        companies_path
    )
 
    companies_df = prepare_companies(
        companies_df
    )
 
    companies_ids = set(
        companies_df["id"].dropna()
    )
 
    print(
        f"companies.xlsx has {len(companies_ids)} "
        f"unique ids"
    )
 
    print()
 
    for table_name, relative_path in LOAD_ORDER:
 
        if table_name == "companies":
 
            continue
 
        file_path = DATA_DIR / relative_path
 
        if not file_path.exists():
 
            continue
 
        df = read_excel_file(
            file_path
        )
 
        if "company_id" not in df.columns:
 
            continue
 
        df["company_id"] = (
            df["company_id"]
            .apply(normalize_company_id)
        )
 
        child_ids = set(
            df["company_id"].dropna()
        )
 
        missing = sorted(
            child_ids - companies_ids
        )
 
        if missing:
 
            print(
                f"[{table_name}] "
                f"{len(missing)} company_id value(s) "
                f"NOT found in companies.xlsx:"
            )
 
            print(f"  {missing}")
 
        else:
 
            print(
                f"[{table_name}] all "
                f"company_id values found in "
                f"companies.xlsx"
            )
 
    print()
 
 
def get_fk_violations():
 
    conn = get_db_connection()
 
    try:
 
        rows = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
 
        return len(rows)
 
    finally:
 
        conn.close()
 
 
def write_audit(
    records
):
 
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
 
    audit_df = pd.DataFrame(
        records
    )
 
    audit_df.to_csv(
        AUDIT_FILE,
        index=False,
    )
 
 
def main():
 
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
 
    print(
        "Nifty100 Day 05 - Full Data Load"
    )
 
    print("--------------------------------")
 
    print(
        f"Database: {DB_PATH}"
    )
 
    print()
 
    conn = get_db_connection()
 
    try:
 
        foreign_keys = conn.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]
 
    finally:
 
        conn.close()
 
    print(
        f"Foreign keys: {foreign_keys}"
    )
 
    print()
 
    print("Pre-load company_id check")
    print("--------------------------------")
 
    check_missing_company_ids()
 
    audit_records = []
 
    valid_company_ids = None
 
    for table_name, relative_path in LOAD_ORDER:
 
        started_at = datetime.now()
 
        try:
 
            rows_in, rows_out = load_table(
                table_name,
                relative_path,
                valid_company_ids,
            )

            rejected = rows_in - rows_out

            runtime_s = round(
                (datetime.now() - started_at).total_seconds(),
                3,
            )
 
            print(
                f"[SUCCESS] {table_name}: "
                f"rows_in={rows_in} rows_out={rows_out} "
                f"rejected={rejected}"
            )

            if table_name == "companies":

                conn = get_db_connection()

                try:

                    rows = conn.execute(
                        "SELECT id FROM companies"
                    ).fetchall()

                    valid_company_ids = {
                        row[0] for row in rows
                    }

                finally:

                    conn.close()
 
            audit_records.append(
                {
                    "table": table_name,
                    "file_path": relative_path,
                    "status": "SUCCESS",
                    "rows_in": rows_in,
                    "rows_out": rows_out,
                    "rejected": rejected,
                    "error": "",
                    "timestamp": started_at,
                    "runtime_s": runtime_s,
                }
            )
 
        except Exception as error:
 
            runtime_s = round(
                (datetime.now() - started_at).total_seconds(),
                3,
            )

            print(
                f"[FAILED] {table_name}: "
                f"{error}"
            )
 
            audit_records.append(
                {
                    "table": table_name,
                    "file_path": relative_path,
                    "status": "FAILED",
                    "rows_in": 0,
                    "rows_out": 0,
                    "rejected": 0,
                    "error": str(error),
                    "timestamp": started_at,
                    "runtime_s": runtime_s,
                }
            )
 
    write_audit(
        audit_records
    )
 
    print()
 
    print(
        f"Audit file: {AUDIT_FILE}"
    )

    dq_failures_path = (
        write_validation_failures()
    )

    print(
        f"DQ failures logged: "
        f"{len(DQ_FAILURES)} row(s) "
        f"-> {dq_failures_path}"
    )
 
    print()
 
    print("Row Counts (rows_out — as loaded into SQLite)")
    print("----------")
 
    for table_name, _ in LOAD_ORDER:
 
        try:
 
            count = get_row_count(
                table_name
            )
 
            print(
                f"{table_name}: {count}"
            )
 
        except Exception as error:
 
            print(
                f"{table_name}: "
                f"ERROR - {error}"
            )
 
    print()
 
    print("Foreign Key Check")
    print("-----------------")
 
    violations = get_fk_violations()
 
    print(
        f"FK violations: {violations}"
    )
 
 
if __name__ == "__main__":
 
    main()
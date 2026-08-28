import os
import pandas as pd


def free_cash_flow(operating_activity, investing_activity):
    return operating_activity + investing_activity


def cfo_quality_score(cfo_values, pat_values):
    if not cfo_values or not pat_values:
        return None

    ratios = []

    for cfo, pat in zip(cfo_values, pat_values):
        if pat == 0:
            return None
        ratios.append(cfo / pat)

    average = sum(ratios) / len(ratios)

    if average > 1.0:
        label = "High Quality"
    elif average >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return average, label


def capex_intensity(investing_activity, sales):
    if sales == 0:
        return None

    value = abs(investing_activity) / sales * 100

    if value < 3:
        label = "Asset Light"
    elif value <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return value, label


def fcf_conversion_rate(fcf, operating_profit):
    if operating_profit == 0:
        return None

    return fcf / operating_profit * 100


def capital_allocation_pattern(
    cfo,
    cfi,
    cff,
    high_cfo_quality=False,
):
    cfo_sign = "+" if cfo > 0 else "-"
    cfi_sign = "+" if cfi > 0 else "-"
    cff_sign = "+" if cff > 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if high_cfo_quality:
            return "Shareholder Returns"
        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return "Mixed"


def generate_capital_allocation(
    input_file="data/raw/cashflow.xlsx",
    output_file="output/capital_allocation.csv",
):
    df = pd.read_excel(input_file, header=1)

    rows = []

    for _, row in df.iterrows():
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]

        if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
            continue

        rows.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "cfo_sign": "+" if cfo > 0 else "-",
            "cfi_sign": "+" if cfi > 0 else "-",
            "cff_sign": "+" if cff > 0 else "-",
            "pattern_label": capital_allocation_pattern(
                cfo,
                cfi,
                cff,
            ),
        })

    result = pd.DataFrame(rows)

    os.makedirs("output", exist_ok=True)

    result.to_csv(output_file, index=False)

    return result
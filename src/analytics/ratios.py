import logging

logger = logging.getLogger(__name__)


def net_profit_margin(net_profit, sales):

#Net Profit Margin = Net Profit / Sales × 100.

    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit,
    sales,
    reported_opm=None,
):
    #Operating Profit Margin = Operating Profit / Sales × 100.

    """If reported OPM is supplied, log a warning when the
    calculated value differs by more than 1 percentage point.
    """
    if sales == 0:
        return None

    calculated_opm = (operating_profit / sales) * 100

    if reported_opm is not None:
        difference = abs(calculated_opm - reported_opm)

        if difference > 1:
            logger.warning(
                "OPM mismatch: calculated=%.2f%% reported=%.2f%% "
                "difference=%.2f percentage points",
                calculated_opm,
                reported_opm,
                difference,
            )

    return calculated_opm


def return_on_equity(net_profit, equity_capital, reserves):

#ROE = Net Profit / (Equity Capital + Reserves) × 100.
    
    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    ebit,
    equity_capital,
    reserves,
    borrowings,
):

  #ROCE = EBIT / (Equity + Reserves + Borrowings) × 100.

    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def roce_benchmark(roce, broad_sector, sector_benchmark=None):

# Use sector-relative benchmark for Financials.
    
    if roce is None:
        return None

    if broad_sector == "Financials":
        return sector_benchmark

    return roce


def return_on_assets(net_profit, total_assets):

    #ROA = Net Profit / Total Assets × 100.

    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100

# DAY 09 — LEVERAGE & EFFICIENCY

# =========================
# DAY 09 — LEVERAGE & EFFICIENCY
# =========================

def debt_to_equity(borrowings, equity_capital, reserves):
    equity = equity_capital + reserves

    if borrowings == 0:
        return 0

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(de_ratio, broad_sector):
    if de_ratio is None:
        return False

    if broad_sector == "Financials":
        return False

    return de_ratio > 5


def interest_coverage_ratio(operating_profit, other_income, interest):
    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def icr_label(icr):
    if icr is None:
        return "Debt Free"

    return None


def icr_warning_flag(icr):
    if icr is None:
        return False

    return icr < 1.5


def net_debt(borrowings, investments):
    return borrowings - investments


def asset_turnover(sales, total_assets):
    if total_assets == 0:
        return None

    return sales / total_assets

# DAY 12 — FINANCIAL RATIOS TABLE POPULATION

def _safe_cagr(current, previous, years=5):
    if current is None or previous is None:
        return None
    if previous <= 0 or current <= 0:
        return None
    return ((current / previous) ** (1 / years) - 1) * 100


def populate_financial_ratios(db_path="db/nifty100.db"):
    """Populate the Day-12 KPI columns in financial_ratios.

    Existing Day-01–11 calculations are not changed.
    Existing financial_ratios rows are updated in place.
    """
    import re
    import sqlite3
    import numpy as np

    conn = sqlite3.connect(db_path)

    try:
        rows = conn.execute("""
            SELECT
                fr.id,
                fr.company_id,
                fr.year,
                p.sales,
                p.operating_profit,
                p.other_income,
                p.interest,
                p.net_profit,
                p.eps,
                p.dividend_payout,
                b.equity_capital,
                b.reserves,
                b.borrowings,
                b.total_assets,
                c.operating_activity,
                c.investing_activity
            FROM financial_ratios fr
            LEFT JOIN profitandloss p
              ON p.company_id = fr.company_id
             AND p.year = fr.year
            LEFT JOIN balancesheet b
              ON b.company_id = fr.company_id
             AND b.year = fr.year
            LEFT JOIN cashflow c
              ON c.company_id = fr.company_id
             AND c.year = fr.year
            ORDER BY fr.company_id, fr.year
        """).fetchall()

        history = {}
        source_rows = conn.execute("""
            SELECT company_id, year, sales, net_profit, eps
            FROM profitandloss
        """).fetchall()

        for company_id, year, sales, pat, eps in source_rows:
            history[(company_id, year)] = (sales, pat, eps)

        def year_number(value):
            if value is None:
                return None

            text = str(value).strip()

            # Handles YYYY-MM, YYYY, and labels such as Mar-23.
            match = re.search(r"(19|20)\d{2}", text)
            if match:
                return int(match.group(0))

            match = re.search(r"(\d{2})$", text)
            if match:
                short_year = int(match.group(1))
                return 2000 + short_year if short_year <= 49 else 1900 + short_year

            return None

        def previous_five_year_values(company_id, current_year):
            if current_year is None:
                return None

            target_year = current_year - 5

            for (cid, source_year), values in history.items():
                if cid == company_id and year_number(source_year) == target_year:
                    return values

            return None

        updates = []
        quality_inputs = []

        for row in rows:
            (
                row_id,
                company_id,
                year,
                sales,
                operating_profit,
                other_income,
                interest,
                pat,
                eps,
                payout,
                equity_capital,
                reserves,
                borrowings,
                total_assets,
                cfo,
                cfi,
            ) = row

            equity = (equity_capital or 0) + (reserves or 0)

            npm = (
                (pat / sales) * 100
                if pat is not None and sales not in (None, 0)
                else None
            )

            opm = (
                (operating_profit / sales) * 100
                if operating_profit is not None and sales not in (None, 0)
                else None
            )

            roe = (
                (pat / equity) * 100
                if pat is not None and equity > 0
                else None
            )

            # ROCE = EBIT / (Equity + Reserves + Borrowings) × 100.
            # For this project, operating_profit is the EBIT proxy.
            capital_employed = equity + (borrowings or 0)
            roce = (
                (operating_profit / capital_employed) * 100
                if operating_profit is not None and capital_employed > 0
                else None
            )

            de = (
                borrowings / equity
                if borrowings is not None and equity > 0
                else (0 if borrowings == 0 else None)
            )

            icr = (
                (operating_profit + (other_income or 0)) / interest
                if operating_profit is not None and interest not in (None, 0)
                else None
            )

            asset_turn = (
                sales / total_assets
                if sales is not None and total_assets not in (None, 0)
                else None
            )

            fcf = (
                cfo + cfi
                if cfo is not None and cfi is not None
                else None
            )

            # Project glossary: CapEx = absolute value of investing activity.
            capex = abs(cfi) if cfi is not None else None

            # Equity capital is share capital in crore and face_value is
            # rupees per share. This derives shares outstanding and BVPS.
            face_value_row = conn.execute(
                "SELECT face_value FROM companies WHERE id = ?",
                (company_id,),
            ).fetchone()

            face_value = face_value_row[0] if face_value_row else None

            if (
                equity_capital not in (None, 0)
                and face_value not in (None, 0)
            ):
                shares_cr = equity_capital / face_value
                book_value = equity / shares_cr
            else:
                book_value = None

            current_year = year_number(year)
            previous = previous_five_year_values(
                company_id,
                current_year,
            )

            prev_sales, prev_pat, prev_eps = (
                previous if previous else (None, None, None)
            )

            revenue_cagr = _safe_cagr(sales, prev_sales)
            pat_cagr = _safe_cagr(pat, prev_pat)
            eps_cagr = _safe_cagr(eps, prev_eps)

            # Composite Quality Score:
            # 0.30×ROE_score + 0.25×FCF_score
            # + 0.25×ROCE_score + 0.20×DE_score.
            # Each component is normalized to 0–100 using P10/P90
            # winsorisation. Higher DE is worse, so DE is reverse-scored.
            composite_quality_score = None

            quality_inputs.append((roe, fcf, roce, de))

            updates.append((
                npm,
                opm,
                roe,
                de,
                icr,
                asset_turn,
                fcf,
                capex,
                eps,
                book_value,
                payout,
                borrowings,
                cfo,
                revenue_cagr,
                pat_cagr,
                eps_cagr,
                composite_quality_score,
                row_id,
            ))

        def winsor_score(value, values, higher_is_better=True):
            if value is None or not values:
                return None

            p10, p90 = np.percentile(values, [10, 90])

            if p90 == p10:
                return 50.0

            clipped = min(max(value, p10), p90)
            score = ((clipped - p10) / (p90 - p10)) * 100

            if not higher_is_better:
                score = 100 - score

            return float(score)

        roe_values = [x[0] for x in quality_inputs if x[0] is not None]
        fcf_values = [x[1] for x in quality_inputs if x[1] is not None]
        roce_values = [x[2] for x in quality_inputs if x[2] is not None]
        de_values = [x[3] for x in quality_inputs if x[3] is not None]

        for index, (roe_value, fcf_value, roce_value, de_value) in enumerate(
            quality_inputs
        ):
            component_scores = [
                (0.30, winsor_score(roe_value, roe_values, True)),
                (0.25, winsor_score(fcf_value, fcf_values, True)),
                (0.25, winsor_score(roce_value, roce_values, True)),
                (0.20, winsor_score(de_value, de_values, False)),
            ]

            available = [
                (weight, score)
                for weight, score in component_scores
                if score is not None
            ]

            if available:
                total_weight = sum(weight for weight, _ in available)

                composite = sum(
                    weight * score for weight, score in available
                ) / total_weight

                update_values = list(updates[index])
                update_values[16] = round(float(composite), 4)
                updates[index] = tuple(update_values)

        conn.executemany("""
            UPDATE financial_ratios
            SET net_profit_margin_pct = ?,
                operating_profit_margin_pct = ?,
                return_on_equity_pct = ?,
                debt_to_equity = ?,
                interest_coverage = ?,
                asset_turnover = ?,
                free_cash_flow_cr = ?,
                capex_cr = ?,
                earnings_per_share = ?,
                book_value_per_share = ?,
                dividend_payout_ratio_pct = ?,
                total_debt_cr = ?,
                cash_from_operations_cr = ?,
                revenue_cagr_5yr = ?,
                pat_cagr_5yr = ?,
                eps_cagr_5yr = ?,
                composite_quality_score = ?
            WHERE id = ?
        """, updates)

        conn.commit()
        return len(updates)

    finally:
        conn.close()
